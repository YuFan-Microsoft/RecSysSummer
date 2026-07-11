# ============================================================================
# SIDReasoner runtime image — built on the OFFICIAL verl 0.6 base image.
#
# Base tag: verlai/verl:base-verl0.6-cu128-cudnn9.8-torch2.8.0-fa2.7.4
#   (nvcr.io/nvidia/pytorch:25.03-py3 -> Ubuntu 24.04 + CUDA 12.8 + Python 3.12)
#
# The base image ALREADY ships the following — DO NOT reinstall them
# (reinstalling torch in particular would break the whole CUDA/vLLM stack):
#   - CUDA 12.8, cuDNN 9.8
#   - torch==2.8.0 (cu128), flash-attn==2.7.4.post1
#   - transformers[hf_xet]==4.55.4, accelerate, datasets, peft, hf-transfer
#   - numpy<2.0.0, pandas, pyarrow, tensordict, torchdata
#   - ray[default], hydra-core (+omegaconf), codetiming, pylatexenc,
#     qwen-vl-utils, wandb, dill, pybind11, liger-kernel, mathruler, xgrammar
#   - Apex, TransformerEngine 2.2.1, Megatron-LM core_v0.13.0, mbridge, DeepEP
#
# On top of the base we add ONLY what is missing for this project:
#   - vllm==0.10.2  (Stage-3 RL rollout). It pins torch==2.8.0 /
#     torchvision==0.23.0 / torchaudio==2.8.0, so torch is NOT downgraded.
#     It also transitively pulls the deps our code needs: openai (RecTool),
#     sentencepiece, einops, scipy, fastapi, pydantic, opencv-python-headless.
#   - deepspeed     (Stage-1/2 SFT: phase1/phase2 use an explicit DeepSpeed loop)
#   - fire          (evaluation + SFT launcher CLIs)
#   - pdsh + openssh (Stage-1/2 DeepSpeed MULTI-NODE launch over ssh; base has neither)
#
# NOTE: verl itself is NOT pip-installed. We run the vendored ./verl from
#       source (see phase3_rl/, which launches `python -m verl.trainer.main_ppo`).
# ============================================================================
FROM verlai/verl:base-verl0.6-cu128-cudnn9.8-torch2.8.0-fa2.7.4

# --- Fix pip index ----------------------------------------------------------
# The verl base image pins pip to an internal mirror (bytedpypi.byted.org),
# which is NOT reachable from a public build network (DNS "Name or service not
# known"). Override to public indexes so every pip install below works.
# ENV beats the inherited config/env; CLI --index-url would beat ENV in turn.
#   NOTE: if you build ON the ByteDance corp network, delete these two ENV
#         lines to keep the (faster) internal mirror.
ENV PIP_INDEX_URL=https://pypi.org/simple
ENV PIP_EXTRA_INDEX_URL=https://download.pytorch.org/whl/cu128

# git-lfs for pulling HuggingFace checkpoints + shell tools, PLUS the multi-node
# launch stack for Stage-1/2 DeepSpeed. phase1/phase2 use `deepspeed --hostfile`,
# which spawns workers on remote nodes over pdsh/ssh — NEITHER ships in the verl
# base image, so single-node runs work but multi-node launch would fail without these.
#   - pdsh                  : DeepSpeed's default multi-node launcher backend
#   - openssh-server/client : passwordless SSH between nodes (run sshd on each node)
# NOTE: we deliberately do NOT apt-install rdma-core / libibverbs / ibverbs-providers.
#   The NGC-derived verl base already ships the full MLNX OFED user-space + NCCL-IB
#   stack; layering distro rdma-core on top can shadow/break MLNX OFED and disable IB.
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
        git-lfs tmux vim \
        pdsh openssh-server openssh-client && \
    git lfs install && \
    rm -rf /var/lib/apt/lists/*

# DeepSpeed's pdsh launcher must use ssh (not the default rsh) to reach other nodes.
ENV PDSH_RCMD_TYPE=ssh

# --- Inference engine: vLLM 0.10.2 (exact match for the base torch 2.8.0) ---
# torch==2.8.0 is already present and stays untouched; torchvision/torchaudio
# (which the base did not install) come from the cu128 extra index set above.
RUN pip install --no-cache-dir \
        vllm==0.10.2 \
        torch==2.8.0 torchvision==0.23.0 torchaudio==2.8.0

# --- Project deps NOT covered by the base image or by vLLM ---
#   deepspeed : Stage-1/2 SFT (phase1_alignment_sft / phase2_reasoning_activation)
#   fire      : evaluation scripts + SFT launchers
RUN pip install --no-cache-dir deepspeed fire
RUN pip uninstall -y nvtx || true

# --- Sanity check: torch must remain 2.8.0 and vllm must be 0.10.2 ---
RUN python -c "from importlib.metadata import version as v; \
print('torch', v('torch'), '| vllm', v('vllm'), '| deepspeed', v('deepspeed'), '| transformers', v('transformers')); \
assert v('torch').startswith('2.8'), 'torch got overridden: ' + v('torch'); \
assert v('vllm') == '0.10.2', 'unexpected vllm: ' + v('vllm')"
