# CLAUDE_Distributed_Training.md

**Purpose.** A reproducible, step-by-step playbook to take SIDReasoner **Phase-1
Alignment SFT** from a single 8-GPU node to a **multi-node, InfiniBand-backed**
run (here: **5 nodes × 8 A100-80GB = 40 GPUs**) on an **AzureML / Singularity**
job. Follow this top-to-bottom on a fresh job with the same initial image and you
will end up with all 3 domains training over IB, one domain at a time.

> TL;DR — once the 3 helper files are in place (see §4), the whole thing is:
> ```bash
> cd .../SIDReasoner && mkdir -p logs
> nohup bash phase1_alignment_sft/sft_Qwen3_enrich_distributed.sh \
>      > logs/phase1_distributed_launch.out 2>&1 &
> ```

---

## 0. What "the same initial environment" means

- AzureML/Singularity job, **N nodes** each with **8× A100/H100 80 GB**.
- Entry point (your shell) runs on **node-0 only**
  (`SINGULARITY_START_ENTRYPOINT_ON_ALL_NODES=false`).
- The SIDReasoner repo already laid down on every node at the **same path**
  under `.../exe/wd/SIDReasoner` (AzureML copies `exe/wd` to all nodes at start).
- Phase-1 training entry point `phase1_alignment_sft/sft_Qwen3.py` is already
  multi-node-safe (global-rank wandb/checkpointing, `DistributedSampler`, the
  save-checkpoint `barrier()` sits **outside** the rank-0 guard → no deadlock).
  **You do not edit it.**

Everything below adds 3 small helper files and a launch procedure. No change to
the model/training code is required.

---

## 1. Probe the cluster FIRST (do not skip)

Run these on node-0. Record the outputs — later steps depend on them.

```bash
# 1a. Topology from the platform env + hostfile
env | grep -E "MASTER_ADDR|MASTER_PORT|AZUREML_NODE_COUNT|AZ_BATCH_HOST_LIST|NODE_RANK"
cat ~/hostfile            # deepspeed-style: "node-0 slots=8" ... one line per node
```
Expected: `MASTER_ADDR=node-0`, a host list `node-0,...,node-4`, and a hostfile
with `slots=8` per node.

```bash
# 1b. Passwordless ssh to a worker + confirm it's a DIFFERENT filesystem
MARK=".../exe/wd/__fs_marker_$$"; echo hi > "$MARK"
ssh -o BatchMode=yes -o StrictHostKeyChecking=no node-1 \
    "hostname; ls $MARK 2>&1; nvidia-smi -L | head -1"
rm -f "$MARK"
```
Expected: ssh works **without a password**, `nvidia-smi` lists an A100, **and the
marker file is NOT found on node-1**. ⇒ **`exe/wd` is per-node, NOT shared.**
This single fact drives the whole design (§3, §4a).

```bash
# 1c. Launcher tooling + InfiniBand presence
which deepspeed pdsh ssh torchrun uv python rsync
ls /dev/infiniband                      # expect uverbs0..7 (8 IB NICs)
for d in /sys/class/infiniband/mlx5_ib*/; do \
  echo "$(basename $d): $(cat ${d}ports/1/state) $(cat ${d}ports/1/rate)"; done
```
Expected findings on this image (all verified):
- `deepspeed`, `ssh`, `torchrun`, `pdsh` and either `uv` or `python` present;
  **`rsync` MISSING**.
- 8× `mlx5_ib0..7` ports **ACTIVE @ 200 Gb/sec (4X HDR)**.

```bash
# 1d. Is pdsh usable? (It is NOT on this image.)
PDSH_RCMD_TYPE=ssh pdsh -w node-1 hostname
```
Expected: **pdsh fails** with `module path "/usr/lib" insecure ... Owner not root`.
Reason: `/usr/lib` is owned by `ubuntu`, not `root`. **Do not try to chown system
dirs on 5 nodes.** We bypass pdsh entirely (§3).

```bash
# 1e. HF dataset reachable and public?
uv run python -c "from datasets import get_dataset_config_names as g; \
print(g('yufan/recsys-genrec-dataset')[:6])"
```
Expected: prints config names (`Video_Games_seqrec`, ...). **Public → no HF token
needed.** `HF_HUB_ENABLE_HF_TRANSFER=1` is already set.

---

## 2. The five hard problems (and the fixes) — learned the hard way

| # | Problem (symptom) | Root cause | Fix |
|---|---|---|---|
| A | Your edits on node-0 don't take effect on workers; workers silently run **stale code** | `exe/wd` is **per-node**, not shared | Push code to every node before launch (`sync_code_to_nodes.sh`, §4a). `rsync` missing ⇒ use tar-over-ssh |
| B | Training **crashes ~immediately** with `FileNotFoundError: .../Video_Games_reasoning/train.parquet` and `"couldn't be found on the Hugging Face Hub"` | **40 processes hammer the HF Hub at once → rate-limited**; datasets' cache-fallback is buggy for some configs | **Prefetch once per node ONLINE**, then run **training fully OFFLINE** (`HF_HUB_OFFLINE=1`). Also **pre-cache the base model** so offline can load it (§4b, §4c) |
| C | Multi-node NCCL slow / not using the fast fabric | Single-node launcher **disables IB** (`NCCL_IB_DISABLE=1`, `NCCL_P2P_DISABLE=1`) | In the multi-node launcher **do NOT disable IB/P2P**; let NCCL use the 8 HDR NICs + NVLink (§3, §6) |
| D | A domain **finishes all N epochs** (all `epoch_*` + `final_checkpoint` written), yet the job is marked **FAILED** and the **next domain never starts**. Workers die with `Watchdog caught collective operation timeout ... ALLREDUCE` after a ~30-min hang, `return code = -6` (SIGABRT); node-0's log says every rank `exits successfully` | **A per-node filesystem check gating a collective.** The old `sft_Qwen3.py` ended with `if not os.path.isdir(final_dir): save_hf_checkpoint(...)`, and `save_hf_checkpoint` runs `barrier()`. On the **non-shared FS**, `final_checkpoint` exists only on node-0 ⇒ node-0 skips the barrier while the 32 worker ranks enter it ⇒ rank-0 never joins ⇒ NCCL timeout | **Never branch a collective on a per-node path.** Gate it on a **rank-consistent** value instead — current code uses `if best_epoch == 0:` (derived from the all-reduced `eval_loss`, so every rank agrees). Early-stop is safe for the same reason (all ranks break on the same all-reduced loss). Belt-and-braces: judge domain success by **artifacts** (`epoch_${NUM_EPOCHS}` + `final_checkpoint` present), not exit code |
| E | The launcher **dies during `prepare_workers`** right after code-sync with `bash: line 1: /home/aiscuser/hostfile: Permission denied` — before any prefetch/training | The platform provisions an **identical, root-owned, READ-ONLY** `~/hostfile` on every node. The launcher tried to overwrite it (`cat > $HOSTFILE`) → `EACCES`; under `set -e` that one non-zero ssh kills the whole script | **Only *seed* the hostfile where it is missing**, never overwrite: `ssh $host "test -r $HOSTFILE" || ssh $host "... cat > $HOSTFILE" <"$HOSTFILE"`. The platform copy is already correct on every node, so normally nothing is written |

Secondary lessons baked into the launcher:
- **Master port:** the platform's `MASTER_PORT=9500` is taken → use a separate
  rendezvous port (`29500`).
- **LR scaling — use SQRT, not linear, for Adam.** Baseline: global batch 64 ⇔
  `LR 2e-5` (single node, best eval ppl ≈ 13.89). Scaling to global batch 320 (40
  GPUs) with the **linear** rule (`2e-5 × 320/64 = 9e-5`) *overshot* → best ppl
  regressed to ≈ 14.60 and the model overfit after epoch ~5. The **sqrt** rule
  (`2e-5 × √(320/64) ≈ 4.5e-5`) is the right one for Adam-style optimizers; treat
  `9e-5` as ~2× too hot. Change **one** knob (LR) at a time — batch and LR were
  confounded in the first attempt, which is why the sqrt-vs-linear cause took a
  run to isolate.
- **Don't burn a 2-day run on epoch count.** Every epoch is checkpointed and the
  best is chosen post-hoc; `--num_epochs 10 --early_stopping_patience 2` lets the
  run stop itself (~epoch 6–7) without wasting compute.
- **NCCL log noise:** 40 ranks of `NCCL_DEBUG=INFO` is unreadable → default `WARN`.

---

## 3. The launch model — why ssh fan-out with `--no_ssh`

Constraints: entry point runs on **node-0 only**, and **pdsh is broken**. So
node-0 must orchestrate the other nodes itself over plain ssh (which works).

DeepSpeed supports exactly this: `deepspeed --no_ssh --node_rank R`.

- node-0 starts **one `deepspeed` per node**, over ssh, each with its own
  `--node_rank` (`0` locally, `1..N-1` on workers).
- Every node reads the **same `~/hostfile`**, so each builds an **identical global
  world map** (`world_size = N×8 = 40`); `--node_rank` selects that node's rank
  slice. **Global rank 0 lands on node-0** → wandb + checkpoints stay on node-0
  (where you also run evaluation).
- **hostfile order == node_rank order** (node-0→0, node-1→1, …). The launcher maps
  by hostfile index so physical node and rank always agree.

Validated with a 5-node NCCL all-reduce: `world_size=5`, `allreduce_sum=10.0`
(=0+1+2+3+4) ✅.

---

## 4. The three helper files

All three live in the repo (`scripts/` and `phase1_alignment_sft/`). If you need to
recreate them on a fresh clone, the essential content/flags are below.

### 4a. `scripts/sync_code_to_nodes.sh` — push code to every worker

Solves Problem A. `rsync` is missing → stream a tar over ssh. Idempotent; run it
after **every** local edit. The main launcher calls it automatically at start.

Key points:
- Read hostnames from `~/hostfile`; skip `self` (`hostname`).
- `tar czf - -C <parent> --exclude=SIDReasoner/{output_dir,logs,temp,results,.git,__pycache__} SIDReasoner | ssh <host> "tar xzf - -C <parent>"`.
- Fan out to all workers in parallel; fail if any node fails.

```bash
bash scripts/sync_code_to_nodes.sh     # run after any code change
```

### 4b. `scripts/prefetch_hf.py` — warm each node's cache ONLINE (data + model)

Solves Problem B (half). HF cache is per-node; run **one** process per node to
pull everything **before** training, so the 8 ranks per node (and offline mode)
read straight from cache.

It caches, for a given `--category`:
- dataset configs `<cat>_seqrec`, `<cat>_catalog`, `<cat>_reasoning`,
  `general_reasoning` (all splits), and
- the **base model** (`--base_model Qwen/Qwen3-1.7B`) via
  `huggingface_hub.snapshot_download` — required because training runs offline.

Standalone runs are best-effort: missing pieces are logged as `SKIP`. The
distributed launcher adds `--strict`, so it stops before offline training if any
node is missing a required cache entry.

```bash
# one process per node — the launcher fans this out over ssh, ONLINE:
uv run python scripts/prefetch_hf.py \
  --category Video_Games --base_model Qwen/Qwen3-1.7B
```

The launcher prefers `uv run python` and falls back to `python` when the target
image does not provide `uv`.

### 4c. `phase1_alignment_sft/sft_Qwen3_enrich_distributed.sh` — the launcher

Ties it together, per domain, sequentially:
1. **Sync code** to all nodes (§4a).
2. Copy node-0's hostfile to every worker and preflight the remote repo,
   `deepspeed`, and Python launcher so every node builds the same world map.
3. **Prefetch** data+model on all nodes, **ONLINE** (§4b).
4. **Train** across all 40 GPUs via ssh fan-out of `deepspeed --no_ssh --node_rank R`,
   **OFFLINE** (`HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1`) to dodge Hub rate-limits.

The launcher monitors every node process concurrently. If any prefetch or
DeepSpeed launcher exits non-zero, it terminates the remaining node launchers
instead of leaving healthy ranks blocked at rendezvous or a collective.

Critical settings inside it:
```text
HOSTFILE            = ~/hostfile            # node_rank = line index
MASTER_ADDR         = node-0
DIST_MASTER_PORT    = 29500                 # NOT the platform's 9500
GPUS_PER_NODE       = 8
world               = NUM_NODES × 8 = 40
MICRO_BATCH_SIZE    = 8    → GLOBAL_BATCH = 320
LR                  = 4.5e-5 (sqrt rule: 2e-5 × √(320/64); linear 9e-5 overshoots — see §2)
NUM_EPOCHS          = 10
EARLY_STOP_PATIENCE = 2    → next domain after 2 consecutive non-improving eval epochs
NCCL_DEBUG          = WARN
# IB is NOT disabled (unlike the single-node script) → uses 8× HDR + NVLink
# Prefetch env: ONLINE.  Training env: + HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1
wandb_project = SIDReasoner_Phase1_Distributed_Training     # groups the 3 runs
wandb_run     = <Category>_Stage1_SFT_Qwen3-1.7B           # Title-cased
```

Env propagation detail: worker ssh shells are non-login and **don't inherit** the
platform env, so the launcher re-exports what NCCL-over-IB and training need
(`PYTHONPATH`, `PYTORCH_CUDA_ALLOC_CONF`, `HF_HUB_ENABLE_HF_TRANSFER`,
`NCCL_SOCKET_IFNAME`, `NCCL_IB_*`, `NCCL_TOPO_FILE`, …) into each ssh command.
Offline flags are added to the **training** command only (never to prefetch).

---

## 5. Run it

```bash
cd .../SIDReasoner
mkdir -p logs

# All 3 domains, 10 epochs each, one domain at a time (Video_Games first).
# ALWAYS nohup so the multi-hour run survives disconnects.
nohup bash phase1_alignment_sft/sft_Qwen3_enrich_distributed.sh \
     > logs/phase1_distributed_launch.out 2>&1 &

# Subset / overrides:
NUM_EPOCHS=5 LR=6e-5 MICRO_BATCH_SIZE=12 \
  nohup bash phase1_alignment_sft/sft_Qwen3_enrich_distributed.sh Video_Games \
     > logs/phase1_distributed_launch.out 2>&1 &
```

Overridable env vars: `NUM_EPOCHS`, `LR`, `MICRO_BATCH_SIZE`, `DIST_MASTER_PORT`,
`GPUS_PER_NODE`, `NCCL_DEBUG`, `HOSTFILE`, `MASTER_ADDR`, `BASE_MODEL`,
`SIDR_HF_REPO`, and `NCCL_SOCKET_IFNAME`. If `NCCL_SOCKET_IFNAME` is unset,
NCCL selects the bootstrap interface automatically.

Before the first real launch, render the exact per-node prefetch and DeepSpeed
commands without using ssh, downloading data, or starting GPUs:

```bash
DRY_RUN=1 bash phase1_alignment_sft/sft_Qwen3_enrich_distributed.sh Video_Games
```

---

## 6. Verify InfiniBand is actually used (and read the "dashboard shows 0" trap)

Cross-node NCCL **must** ride IB, not TCP. Check the node-0 training log:

```bash
L=logs/Video_Games_stage1_sft_Qwen3-1.7B_distributed.txt
grep -c 'NET/Socket'        "$L"   # want 0  (no socket fallback)
grep    'NET/IB'            "$L" | head -1   # want: Using [0]mlx5_ib0 ... [7]mlx5_ib7  IB/SHARP  RDMA
grep    'NCCL RDMA Plugin'  "$L" | head -1
```
Good output means all 8 HDR NICs are bound via RDMA and **no channel fell back to
sockets**. You should also see NVLink intra-node (`P2P/CUMEM`) and
`NCCL INFO Connected all trees`.

**Trap:** the platform's InfiniBand throughput metric may read **0** even while IB
works. Reason: this container **does not expose IB byte counters** —
`/sys/class/infiniband/mlx5_ib0/ports/1/counters/` and `hw_counters/` are absent
and there's no `perfquery`/`rdma` tool, so the telemetry agent has nothing to read.
The port **state/rate** are still visible and healthy:

```bash
for d in /sys/class/infiniband/mlx5_ib*/; do \
  echo "$(basename $d): $(cat ${d}ports/1/state) $(cat ${d}ports/1/rate)"; done
# expect: ACTIVE  200 Gb/sec (4X HDR)  for ib0..ib7
```
So **"IB = 0" on a dashboard is a telemetry artifact, not a fabric failure.** Trust
the NCCL log (`NET/IB ... RDMA Plugin`, `NET/Socket` count = 0).

---

## 7. Monitor, timing, outputs

```bash
# live training (node-0 == global rank 0)
tail -f logs/Video_Games_stage1_sft_Qwen3-1.7B_distributed.txt
# per-worker logs (stdout streamed back to node-0 over ssh)
tail -f logs/Video_Games_stage1_sft_Qwen3-1.7B_distributed.node1.txt
```

Per-step line: `epoch E | micro-step i/992 | opt-step k | loss .. | lr .. | <ms>`.

**Timing (measured on this cluster):** ~**992 steps/epoch**, ~**4.0 s/step** ⇒
- 1 epoch ≈ **~1.1 h** (train) + a few min (per-epoch eval ×3 + checkpoint save).
- At most 10 epochs / domain ≈ **~11–12 h**; early stopping may move to the next
  domain sooner after 2 consecutive non-improving `sid_pred` eval losses.

Speed levers: raise `MICRO_BATCH_SIZE` (80 GB has headroom; bump `LR` ~linearly) to
cut steps/epoch, or lower `NUM_EPOCHS`.

**Outputs (all on node-0 — rank 0 saves):**
- per-epoch checkpoints → `output_dir/<CAT>_stage1_sft_Qwen3-1.7B_distributed/epoch_<N>`
- loss-best pointer → `.../final_checkpoint`
- Final checkpoint is chosen by **recsys metrics** (NDCG@10/HR@10) per domain, by
  scoring each `epoch_<N>` — see `phase1_alignment_sft/CLAUDE.md §7`. Evaluation
  runs single-node on node-0 (8 GPUs), which is why keeping rank 0 on node-0 matters.

---

## 8. Troubleshooting quick table

| Symptom | Likely cause | Action |
|---|---|---|
| Workers run old code / weird stale behaviour | forgot to sync after an edit | `bash scripts/sync_code_to_nodes.sh` |
| `FileNotFoundError ...train.parquet` / `couldn't be found on the Hugging Face Hub` | Hub rate-limit + offline not set / prefetch missed | ensure prefetch ran on every node; training must have `HF_HUB_OFFLINE=1` |
| Offline load can't find base model | model not pre-cached on a worker | `prefetch_hf.py --base_model ...` on all nodes (launcher does this) |
| Hangs at rendezvous | wrong/blocked port, or `MASTER_ADDR` wrong | use `DIST_MASTER_PORT=29500`, `MASTER_ADDR=node-0` |
| `pdsh ... module path insecure` | pdsh broken (system dir not root-owned) | expected — we don't use pdsh; ignore |
| Slow multi-node / `NET/Socket` in log | IB got disabled | ensure launcher does **not** set `NCCL_IB_DISABLE`/`NCCL_P2P_DISABLE` |
| Dashboard shows InfiniBand = 0 | container doesn't expose IB counters | telemetry artifact; verify via NCCL log + port `state/rate` (§6) |
| `bash: line 1: ~/hostfile: Permission denied`, launcher dies during `prepare_workers` | platform's `~/hostfile` is root-owned & **read-only**; launcher tried to overwrite it and `set -e` aborted | seed the hostfile only when missing (`test -r $HOSTFILE || cat > $HOSTFILE`); never overwrite (Problem E, §2) |
| Workers `Watchdog ... collective ... timeout`/`return code = -6`, but all `epoch_*` on disk | a **per-node FS check gated a collective** (ranks diverged on `barrier()`) | branch collectives on a **rank-consistent** value (e.g. `best_epoch`), never `os.path.isdir` of a per-node path (Problem D, §2) |
| One domain finished all epochs but run stops before the next | fail-fast on exit code; a tail-end desync gave non-zero exit | judge success by artifacts (`epoch_N` + `final_checkpoint`); re-launch remaining domains as args |
| Distributed eval ppl worse than single node | LR **linear**-scaled for a big batch (overshoot) | use **sqrt** scaling (`2e-5 × √(batch/64)`); change only LR per experiment (§2 secondary) |
| One domain fails, run stops | launcher is fail-fast per domain | fix cause, re-launch that domain as an arg |

---

## 9. One-screen recap

1. Probe: per-node FS, ssh OK, pdsh broken, rsync missing, IB HDR up, HF public (§1).
2. Sync code to all nodes (tar-over-ssh) — per-node FS (§4a).
3. Prefetch data **+ base model** online, once per node (§4b).
4. Launch `deepspeed --no_ssh --node_rank R` per node over ssh; rank 0 on node-0 (§3).
5. Train **offline** (`HF_HUB_OFFLINE=1`) to dodge Hub rate-limits (§2B).
6. Keep IB **enabled**; verify `NET/IB ... RDMA Plugin`, `NET/Socket`=0 (§6).
7. 40 GPUs → global batch 320. **LR by the sqrt rule ≈ 4.5e-5** (linear 9e-5 overshoots);
   wandb project `SIDReasoner_Phase1_Distributed_Training` with the 3 domain runs;
   `--num_epochs 10 --early_stopping_patience 2`, one domain at a time (§4c, §5).
8. Two multi-node traps that abort the whole job: (a) never overwrite the read-only
   platform `~/hostfile` — seed only if missing (§2E); (b) never gate a collective
   (`barrier()`) on a per-node filesystem check — branch on a rank-consistent value
   like `best_epoch` (§2D).
