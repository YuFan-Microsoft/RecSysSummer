# Amazon Reviews 2023 — Results of Papers Whose Data Processing Matches This Dataset

Scope: papers that run on the same Amazon-2023 categories as
[`yufan/amazon2023-user-interactions`](https://huggingface.co/datasets/yufan/amazon2023-user-interactions)
**and whose data processing matches** the dataset recipe
(official 5-core filtering → chronological order → **leave-one-out** split).
These are the ~15 papers cross-validated in the dataset README (their reported
`#users / #items / #interactions` match ours to the digit). Below, their *results*
are collected and organized.

> **The single most important caveat.** Identical data splits do **not** make the
> numbers directly comparable. The same baseline is re-implemented differently
> across papers, so its score swings 10–50 % even on byte-identical data. Example —
> **SASRec Recall@10 on Musical Instruments**: `0.0523` (RUCAIBox lineage) vs
> `0.0536` (LARES) vs `0.0525` (LLaDA-Rec) vs `0.0379` Hit@10 (Augment-or-Not).
> **TIGER Recall@10 on Musical Instruments**: `0.0501 → 0.0606` across papers.
> Numbers are therefore only comparable **within a shared-codebase lineage**.

---

## 1. Overview of the matching papers

| Paper | Venue / arXiv | Categories used (matching ones in **bold**) | maxlen | Split | Metric | Eval | Comparable group |
|---|---|---|---|---|---|---|---|
| **UTGRec** | Tencent·arXiv 2504.04405 | **Instrument, Scientific, Game**, Office (+5 pretrain) | 20 | LOO | R/N@5,10 | full rank | **A** |
| **MTGRec** | Huawei·SIGIR 2025 · 2504.04400 | **Instrument, Scientific, Game** | 20 | LOO | R/N@5,10 | full rank | **A** |
| **CCFRec** | KDD 2025 · 2503.12183 | **Instrument, Scientific, Game**, Baby | 20 | LOO | R/N@5,10 | full rank | **A** |
| **Pctx** | arXiv 2510.21276 | **Instrument, Scientific, Game** | 20 | LOO | R/N@5,10 | full rank | **A** |
| LARES | Meituan·arXiv 2505.16865 | **Instrument, Scientific, Game**, Baby | 20 | LOO | R/N@5,10,20 | full rank | B (own repro) |
| LLaDA-Rec | arXiv 2511.06254 | **Instrument, Scientific, Game** | seq | LOO | R@1,5,10 N@5,10 | full rank | B (own repro) |
| SID-MLP (MLPs) | Snap·arXiv 2605.12617 | **Instrument, Scientific, Game** | 20 | LOO | R/N@5,10 | full rank | B (own repro) |
| Token-Weighted | arXiv 2601.17787 | **Instrument, Scientific** | seq | LOO | H/N@5,10 | full rank | B (own repro) |
| Augment-or-Not | arXiv 2505.23053 | **Instrument, Scientific** | 20 | LOO* | Hit/N@5,10 | full rank | C (LLM-rec study) |
| GrIT | arXiv 2602.19728 | **Game, Scientific**, CDs&Vinyl | 50 | LOO | R/N@5,10,20 | full rank | D (maxlen 50) |
| HSTU-BLaIR | arXiv 2504.10545 | **Game, Instrument**, Office | ~50 | LOO | HR/N@10,50,200 | full rank | D (HSTU) |
| IntervalLLM | RecSys 2025 · 2507.23209 | **Game, Books**, CDs&Vinyl | seq | LOO | **HR@1** | re-rank 20 cand. | E |
| MARIUS | Criteo·arXiv 2508.14910 | **Beauty**, Office (+8 cats) | seq | LOO | R/N@5,10 (%) | full rank | F (large cats) |
| AlphaFree | WWW 2026 · 2603.02653 | **Video/Beauty/Baby** (+Movie,Book,Health) | — | **4:3:3 holdout** | R/N@20 | full rank | ✗ split differs |
| Hi-SAM | NetEase·KDD 2026 · 2602.11799 | **Books**, Movies&TV | 300 | **90/10 chrono** | **AUC/GAUC** | CTR | ✗ task differs |

\* Augment-or-Not explicitly downloads the *official* McAuley-Lab "5-Core
leave-one-out" preprocessed split — the closest possible match to this dataset.

`R=Recall, N=NDCG, H/HR=Hit Rate, LOO=leave-one-out`. For LOO with a single
test item, **HR@K = Recall@K** (same metric, different name).

---

## 2. Group A — directly comparable leaderboard (maxlen 20, full-ranking, RUCAIBox protocol)

**UTGRec, MTGRec, CCFRec and Pctx share byte-identical baseline rows** (same
RecBole/RUCAIBox codebase), so their *proposed* methods sit on one leaderboard.
Reference baselines (identical in all four): SASRec, FMLP-Rec, TIGER, LETTER.

### Musical Instruments — Recall@10 / NDCG@10
| Method | R@5 | R@10 | N@5 | N@10 |
|---|---:|---:|---:|---:|
| SASRec | 0.0333 | 0.0523 | 0.0213 | 0.0274 |
| TIGER | 0.0370 | 0.0564 | 0.0244 | 0.0306 |
| LETTER | 0.0372 | 0.0580 | 0.0246 | 0.0313 |
| UTGRec | 0.0398 | 0.0616 | 0.0263 | 0.0334 |
| MTGRec | 0.0413 | 0.0635 | 0.0275 | 0.0346 |
| Pctx | 0.0419 | 0.0655 | 0.0275 | 0.0350 |
| **CCFRec (PQ)** | **0.0432** | **0.0682** | **0.0281** | **0.0361** |

### Industrial & Scientific — Recall@10 / NDCG@10
| Method | R@5 | R@10 | N@5 | N@10 |
|---|---:|---:|---:|---:|
| SASRec | 0.0259 | 0.0412 | 0.0150 | 0.0199 |
| TIGER | 0.0264 | 0.0422 | 0.0175 | 0.0226 |
| LETTER | 0.0279 | 0.0435 | 0.0182 | 0.0232 |
| UTGRec | 0.0308 | 0.0481 | 0.0204 | 0.0255 |
| Pctx | 0.0323 | 0.0504 | 0.0205 | 0.0263 |
| MTGRec | 0.0322 | 0.0506 | 0.0212 | 0.0271 |
| **CCFRec (PQ)** | **0.0364** | **0.0555** | **0.0224** | **0.0285** |

### Video Games — Recall@10 / NDCG@10
| Method | R@5 | R@10 | N@5 | N@10 |
|---|---:|---:|---:|---:|
| SASRec | 0.0535 | 0.0847 | 0.0331 | 0.0438 |
| TIGER | 0.0559 | 0.0868 | 0.0366 | 0.0467 |
| LETTER | 0.0563 | 0.0877 | 0.0372 | 0.0473 |
| UTGRec | 0.0592 | 0.0909 | 0.0390 | 0.0491 |
| MTGRec | 0.0621 | 0.0956 | 0.0410 | 0.0517 |
| Pctx | 0.0638 | 0.0981 | 0.0416 | 0.0527 |
| **CCFRec (PQ)** | **0.0658** | **0.1042** | 0.0413 | **0.0536** |

**Group-A leaderboard (Recall@10): CCFRec > Pctx ≈ MTGRec > UTGRec > LETTER >
TIGER > SASRec**, consistently across all three categories. CCFRec's collaborative
tokenization gives the largest single jump over TIGER (+18–21 % Recall@10).

---

## 3. Group B — same protocol (LOO, maxlen 20, full-ranking) but each paper re-runs its own baselines

Compare **only within each block** (their SASRec/TIGER differ from Group A and from each other).

**LARES** (latent reasoning over SASRec-style backbone) — best baseline = DuoRec:
| Cat | SASRec R@10 | best baseline R@10 | **LARES R@10** | LARES N@10 |
|---|---:|---:|---:|---:|
| Instrument | 0.0536 | 0.0598 (DuoRec) | **0.0636** | 0.0336 |
| Scientific | 0.0385 | 0.0441 (PRL++) | **0.0464** | 0.0245 |
| Game | 0.0926 | 0.0932 (DuoRec) | **0.0972** | 0.0500 |

**LLaDA-Rec** (discrete-diffusion parallel semantic-ID) — best baseline = LC-Rec:
| Cat | SASRec R@10 | TIGER R@10 | best baseline R@10 | **LLaDA-Rec R@10** | N@10 |
|---|---:|---:|---:|---:|---:|
| Instrument | 0.0525 | 0.0566 | 0.0587 (LC-Rec) | **0.0623** | 0.0337 |
| Scientific | 0.0379 | 0.0446 | 0.0446 (TIGER) | **0.0474** | 0.0256 |
| Game | 0.0823 | 0.0823 | 0.0891 (LC-Rec) | **0.0942** | 0.0517 |

**SID-MLP (MLPs)** — efficiency story: *match TIGER at ~8.7× throughput*:
| Cat | TIGER R@10 | **SID-MLP R@10** | N@10 | speedup |
|---|---:|---:|---:|---:|
| Instrument | 0.0606 | 0.0620 | 0.0332 | 8.7× |
| Scientific | 0.0457 | 0.0472 | 0.0250 | 8.7× |
| Game | 0.0951 | 0.0953 | 0.0512 | 8.7× |

**Token-Weighted** (token-weighted multi-target loss on TIGER) — small gain over TIGER:
| Cat | TIGER H@10 / N@10 | **TIGER+Ours H@10 / N@10** |
|---|---:|---:|
| Instrument | 0.0501 / 0.0263 | **0.0512 / 0.0273** (+2.2 % / +3.8 %) |
| Scientific | 0.0393 / 0.0206 | **0.0398 / 0.0210** (+1.3 % / +2.0 %) |

---

## 4. Group C — Augment-or-Not (LLM-recommender comparative study)

A *study*, not a new model. Uses the official 5-core LOO split on Instrument &
Scientific. Headline finding: **semantic-ID generative recommenders (TIGER /
LETTER-TIGER) beat both pure-LLM recommenders (P5, POD, BIGRec, RDRec) and
classical SASRec** on these small categories.

| Method | Instrument Hit@10 / N@10 | Scientific Hit@10 / N@10 |
|---|---:|---:|
| SASRec | 0.0379 / 0.0167 | 0.0255 / 0.0120 |
| BIGRec (LLM) | 0.0420 / 0.0192 | 0.0280 / 0.0144 |
| TIGER | 0.0517 / 0.0276 | 0.0385 / 0.0204 |
| **LETTER-TIGER** | **0.0521 / 0.0282** | **0.0396 / 0.0210** |

---

## 5. Group D — maxlen 50 (longer history ⇒ higher absolute scores)

**GrIT** (group-informed transformer, maxlen 50) — own baselines (no SASRec/TIGER):
| Cat | best baseline R@10 | **GrIT R@10** | N@10 |
|---|---:|---:|---:|
| Video Games | 0.1042 (DuoRec) | **0.1047** | 0.0588 |
| Industrial & Scientific | 0.0476 (DuoRec) | **0.0482** | 0.0286 |

**HSTU-BLaIR** (HSTU + BLaIR text embeddings) — reports **HR**; HSTU ≫ SASRec,
BLaIR adds a small gain over plain HSTU:
| Cat | SASRec HR@10 | HSTU HR@10 | **HSTU-BLaIR HR@10 / N@10** |
|---|---:|---:|---:|
| Video Games | 0.1028 | 0.1315 | **0.1353 / 0.0760** |
| Musical Instruments | 0.0643 | 0.0700 | **0.0733 / 0.0406** |

> Note the maxlen-50 Video-Games HR@10 (~0.10–0.14) sits far above the maxlen-20
> Recall@10 (~0.085–0.104) of Groups A/B — almost entirely a history-length /
> backbone effect, not "better data".

---

## 6. Group E/F — different evaluation, still LOO

**IntervalLLM** (RecSys'25) — leave-one-out but **re-ranks 20 candidates**, so
HR@1 is high and not comparable to full-ranking numbers:
| Method | Video Games HR@1 | CDs&Vinyl HR@1 | Books HR@1 |
|---|---:|---:|---:|
| SASRec | 50.8 % | 50.9 % | 38.0 % |
| LLaMA+Interval | 56.3 % | 48.7 % | 61.1 % |
| **IntervalLLM** | **61.7 %** | **55.4 %** | **61.9 %** |

**MARIUS** (Criteo, "Closing the Gap") — large categories incl. **Beauty &
Personal Care**; scores in **%**. Key message: a **well-tuned SASRec (SASRec++)
matches or beats vanilla generative TIGER**, and MARIUS closes the remaining gap:
| Method | Beauty R@5 / R@10 | Beauty N@10 |
|---|---:|---:|
| TIGER | 0.98 % / 1.63 % | 0.84 % |
| SASRec++ | 2.68 % / 3.84 % | **2.25 %** |
| **MARIUS** | **2.71 % / 4.04 %** | 2.24 % |

> This is the opposite ordering to Groups A–C (where TIGER > SASRec). The
> difference is tuning: vanilla TIGER loses badly to a *tuned* SASRec on big,
> sparse categories. A reminder that "GR beats classical" depends on baseline effort.

---

## 7. Excluded — 5-core counts match, but the split / task does NOT

These match the dataset's 5-core `#users/#items/#interactions`, so the README
lists them, but their **data processing differs** from this dataset's leave-one-out
recipe — their results are **not** comparable to a LOO next-item benchmark:

- **AlphaFree** (WWW'26): random **user-wise 4:3:3 holdout**, not LOO; Recall@20.
  (Beauty R@20 0.0361, Video R@20 0.1111, Baby R@20 0.0412 — best baseline AlphaRec.)
- **Hi-SAM** (KDD'26): chronological **90 % / 10 % split**, ratings > 3 as positive,
  maxlen 300, and a **CTR task (AUC/GAUC)** rather than retrieval.
  (Books AUC 0.7149, Movies&TV AUC 0.7867.)

Also excluded (README "near-match"): **ReSID, Multimodal-GR, SPARC** apply one
*extra* filter on top of 5-core+LOO (drop items without side-info / images, or
keep only rating ≥ 4), so counts are ~2–6 % smaller and not strictly comparable.

---

## 8. Take-aways

1. **One clean leaderboard exists.** The RUCAIBox lineage (UTGRec, MTGRec, CCFRec,
   Pctx) is byte-identical on baselines, giving a directly usable maxlen-20,
   full-ranking benchmark on Instrument / Scientific / Game. **CCFRec leads**, then
   Pctx ≈ MTGRec > UTGRec > LETTER > TIGER > SASRec.
2. **Cross-paper numbers are not transferable.** The same SASRec/TIGER varies
   10–50 % across papers on identical data — always compare a method against the
   baselines *inside its own paper*.
3. **History length matters a lot.** maxlen-50 papers (GrIT, HSTU-BLaIR) post much
   higher absolute scores than maxlen-20 papers; this is protocol, not data.
4. **"Generative beats classical" is conditional.** On small categories vanilla
   TIGER > SASRec; on large Beauty, a *tuned* SASRec++ ≥ vanilla TIGER (MARIUS).
5. **Evaluation protocol is the real confounder**, not the data: full-ranking vs
   20-candidate re-ranking (IntervalLLM), Recall vs Hit vs AUC, and @5/@10 vs
   @20/@200 all change the headline.

*Reference numbers above are transcribed from each paper's main results table;
see the per-paper notes in `RecSys_EvaluationDataset/Freq_132_Amazon-2023/`.*
