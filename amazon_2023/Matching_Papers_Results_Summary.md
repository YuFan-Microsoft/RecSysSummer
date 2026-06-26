# Amazon Reviews 2023 — Results of Papers Whose Statistics & Processing EXACTLY Match This Dataset

**Strict inclusion rule.** A paper's result on a category is reported here **only if**
it satisfies *both*:

1. **Statistics match exactly** — the paper's reported `#users / #items / #interactions`
   for that category are **identical** to
   [`yufan/amazon2023-user-interactions`](https://huggingface.co/datasets/yufan/amazon2023-user-interactions); and
2. **Processing matches** — official 5-core filtering → chronological order →
   **leave-one-out** split (the dataset's recipe).

Anything that fails either test is **excluded** — different counts, a different split
(e.g. random holdout), a different task (CTR), or a category not in this dataset
(Office, CDs & Vinyl, Baby, Health, Movie, …) — because its numbers are not produced
on the same data and are therefore **not meaningful** to compare.

This dataset's target statistics (after 5-core):

| Category | #Users | #Items | #Interactions |
|---|---:|---:|---:|
| `Musical_Instruments` | 57,439 | 24,587 | 511,836 |
| `Video_Games` | 94,762 | 25,612 | 814,586 |
| `Industrial_and_Scientific` | 50,985 | 25,848 | 412,947 |
| `Beauty_and_Personal_Care` | 729,576 | 207,649 | 6,624,441 |
| `Books` | 776,370 | 495,063 | 9,488,297 |

---

## 1. Statistics-match verification (the gate)

`✅` = reported `#users/#items/#inter` identical to target · `−1` = off by one ·
`✗` = different · `=cnt` = counts identical but **processing differs** · blank = category not used.

| Paper (venue) | M.Instr. | V.Games | Ind.&Sci. | Beauty | Books | Split / task | Verdict |
|---|:--:|:--:|:--:|:--:|:--:|---|---|
| **UTGRec** (arXiv 2504.04405) | ✅ | ✅ | ✅ | | | 5-core + LOO | **INCLUDE** |
| **MTGRec** (SIGIR'25) | ✅ | ✅ | ✅ | | | 5-core + LOO | **INCLUDE** |
| **CCFRec** (KDD'25) | ✅ | ✅ | ✅ | | | 5-core + LOO | **INCLUDE** |
| **Pctx** (arXiv 2510.21276) | ✅ | ✅ | ✅ | | | 5-core + LOO | **INCLUDE** |
| **LARES** (arXiv 2505.16865) | ✅ | ✅ | ✅ | | | 5-core + LOO | **INCLUDE** |
| **LLaDA-Rec** (arXiv 2511.06254) | ✅ | ✅ | ✅ | | | 5-core + LOO | **INCLUDE** |
| **SID-MLP** (arXiv 2605.12617) | ✅ | ✅ | ✅ | | | 5-core + LOO (official `last_out`) | **INCLUDE** |
| **GrIT** (arXiv 2602.19728) | | ✅ | ✅ | | | 5-core + LOO (maxlen 50) | **INCLUDE** |
| **IntervalLLM** (RecSys'25) | | ✅ | | | ✅ | 5-core + LOO (re-ranks 20 cand.) | **INCLUDE** |
| **MARIUS** (arXiv 2508.14910) | | | | ✅ | | 5-core + LOO | **INCLUDE** |
| **Augment-or-Not** (arXiv 2505.23053) | ✅ᵘⁱ | | ✅ᵘⁱ | | | 5-core + LOO (official split) | **INCLUDE** |
| Token-Weighted (arXiv 2601.17787) | ✅ | | −1 item | | | 5-core + LOO | **PARTIAL** → Instrument only |
| HSTU-BLaIR (arXiv 2504.10545) | −1 | −1 | | | | 5-core + LOO | **BORDERLINE** (off by 1) |
| AlphaFree (WWW'26) | | =cnt | | =cnt | | **4:3:3 random holdout** | **EXCLUDE** (split) |
| Hi-SAM (KDD'26) | | | | | ≈ | **90/10 chrono + CTR/AUC** | **EXCLUDE** (task) |

ᵘⁱ Augment-or-Not prints `#users` & `#items` (both exact) and `avg-len` (8.91 / 8.10,
exact); it does not print `#interactions`, but explicitly downloads the *official*
McAuley-Lab "5-Core leave-one-out" preprocessed split, so the data is the same artifact.

> **Reminder that still applies to everything below.** Even on byte-identical data, each
> paper re-implements baselines differently, so the *same* baseline varies across papers
> (e.g. TIGER Recall@10 on Instrument = 0.0564 / 0.0566 / 0.0606 in different papers).
> **Compare a method only against the baselines inside its own paper / lineage.**

---

## 2. The one directly-comparable leaderboard — UTGRec · MTGRec · CCFRec · Pctx

These four are **all exact-match on Instrument / Scientific / Game** *and* share a
byte-identical baseline implementation (same RecBole/RUCAIBox codebase), so their
proposed methods sit on a single leaderboard. Protocol: maxlen 20, full ranking.

### Musical Instruments — Recall@10 / NDCG@10
| Method | R@5 | R@10 | N@5 | N@10 |
|---|---:|---:|---:|---:|
| SASRec (shared baseline) | 0.0333 | 0.0523 | 0.0213 | 0.0274 |
| TIGER (shared baseline) | 0.0370 | 0.0564 | 0.0244 | 0.0306 |
| LETTER (shared baseline) | 0.0372 | 0.0580 | 0.0246 | 0.0313 |
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

**Ranking (Recall@10), consistent across all three exact-match categories:**
`CCFRec > Pctx ≈ MTGRec > UTGRec > LETTER > TIGER > SASRec`.

---

## 3. Other exact-match papers (each compared only to its own baselines)

All numbers below are on **exact-match data**, but each paper re-runs its own
baselines, so do **not** cross-compare with §2.

**LARES** (maxlen 20, full ranking) — best baseline = DuoRec:
| Cat | SASRec R@10 | best baseline R@10 | **LARES R@10 / N@10** |
|---|---:|---:|---:|
| Instrument | 0.0536 | 0.0598 (DuoRec) | **0.0636 / 0.0336** |
| Scientific | 0.0385 | 0.0441 (PRL++) | **0.0464 / 0.0245** |
| Video Games | 0.0926 | 0.0932 (DuoRec) | **0.0972 / 0.0500** |

**LLaDA-Rec** (discrete diffusion, full ranking) — best baseline = LC-Rec:
| Cat | SASRec R@10 | TIGER R@10 | best baseline R@10 | **LLaDA-Rec R@10 / N@10** |
|---|---:|---:|---:|---:|
| Instrument | 0.0525 | 0.0566 | 0.0587 (LC-Rec) | **0.0623 / 0.0337** |
| Scientific | 0.0379 | 0.0446 | 0.0446 (TIGER) | **0.0474 / 0.0256** |
| Video Games | 0.0823 | 0.0823 | 0.0891 (LC-Rec) | **0.0942 / 0.0517** |

**SID-MLP** (efficiency — match TIGER at ~8.7× throughput; official `last_out` split):
| Cat | TIGER R@10 / N@10 | **SID-MLP R@10 / N@10** |
|---|---:|---:|
| Instrument | 0.0606 / 0.0323 | **0.0620 / 0.0332** |
| Scientific | 0.0457 / 0.0243 | **0.0472 / 0.0250** |
| Video Games | 0.0951 / 0.0512 | **0.0953 / 0.0512** |

**GrIT** (maxlen **50** ⇒ higher absolute scores; own baselines, no SASRec/TIGER):
| Cat | best baseline R@10 | **GrIT R@10 / N@10** |
|---|---:|---:|
| Video Games | 0.1042 (DuoRec) | **0.1047 / 0.0588** |
| Industrial & Scientific | 0.0476 (DuoRec) | **0.0482 / 0.0286** |

**Augment-or-Not** (LLM-recommender *study*; reports Hit@10 = Recall@10). Finding:
semantic-ID GR (TIGER / LETTER-TIGER) beats pure-LLM recommenders and SASRec here:
| Cat | SASRec | BIGRec (LLM) | TIGER | **LETTER-TIGER (best)** |
|---|---:|---:|---:|---:|
| Instrument H@10 / N@10 | 0.0379 / 0.0167 | 0.0420 / 0.0192 | 0.0517 / 0.0276 | **0.0521 / 0.0282** |
| Scientific H@10 / N@10 | 0.0255 / 0.0120 | 0.0280 / 0.0144 | 0.0385 / 0.0204 | **0.0396 / 0.0210** |

**Token-Weighted** — **Musical Instruments only** (its Scientific is off by 1 item, see §5):
| Cat | TIGER H@10 / N@10 | **TIGER+Ours H@10 / N@10** |
|---|---:|---:|
| Instrument | 0.0501 / 0.0263 | **0.0512 / 0.0273** (+2.2 % / +3.8 %) |

**IntervalLLM** — leave-one-out but **re-ranks 20 candidates**, so `HR@1` is high and
not comparable to the full-ranking numbers above:
| Method | Video Games HR@1 | Books HR@1 |
|---|---:|---:|
| SASRec | 50.8 % | 38.0 % |
| LLaMA + Interval | 56.3 % | 61.1 % |
| **IntervalLLM** | **61.7 %** | **61.9 %** |

**MARIUS** ("Closing the Gap") — the **only** exact-match + LOO paper on **Beauty**
(scores in %). Message: a *well-tuned* SASRec++ ≥ vanilla generative TIGER; MARIUS edges ahead:
| Method | Beauty R@5 / R@10 | Beauty N@10 |
|---|---:|---:|
| TIGER | 0.98 % / 1.63 % | 0.84 % |
| SASRec++ | 2.68 % / 3.84 % | **2.25 %** |
| **MARIUS** | **2.71 % / 4.04 %** | 2.24 % |

---

## 4. Coverage summary (exact-match results only)

| Category | # usable papers | Methods with exact-match results |
|---|:--:|---|
| `Musical_Instruments` | 9 | UTGRec, MTGRec, CCFRec, Pctx, LARES, LLaDA-Rec, SID-MLP, Augment-or-Not, Token-Weighted |
| `Industrial_and_Scientific` | 8 | UTGRec, MTGRec, CCFRec, Pctx, LARES, LLaDA-Rec, SID-MLP, GrIT, Augment-or-Not |
| `Video_Games` | 9 | UTGRec, MTGRec, CCFRec, Pctx, LARES, LLaDA-Rec, SID-MLP, GrIT, IntervalLLM |
| `Beauty_and_Personal_Care` | 1 | MARIUS |
| `Books` | 1 | IntervalLLM |

Most comparable evidence concentrates on **Instrument / Scientific / Video Games**.
**Beauty** and **Books** each have only a single exact-match + LOO paper, and each uses
a non-standard metric (MARIUS in %, IntervalLLM HR@1) — so there is essentially no
cross-method comparison available for those two categories.

---

## 5. Borderline — off by exactly one (your call)

Counts differ from the target by 1; almost certainly the same data with a trivial
boundary/typo difference, but **not byte-identical**, so kept out of §2–§3:

- **HSTU-BLaIR** — Musical Instruments `511,835` (target 511,836) and Video Games
  `814,585` (target 814,586): both **−1 interaction** (same users/items). If accepted,
  it reports HR/NDCG with a longer (HSTU) history: VG HR@10 0.1353/N@10 0.0760,
  Instrument HR@10 0.0733/N@10 0.0406 (HSTU 0.1315 / 0.0700; SASRec 0.1028 / 0.0643).
- **Token-Weighted (Industrial & Scientific)** — items `25,847` (target 25,848); users
  and interactions exact, so likely a typo. Its Musical Instruments entry *is* exact and
  is included in §3.

---

## 6. Excluded — statistics match but processing/task differs

These reproduce the 5-core counts on some of our categories, but **do not use the same
processing**, so their numbers are not comparable and are not reported:

- **AlphaFree** (WWW'26) — Video & Beauty 5-core counts are exact, **but the split is a
  random user-wise 4:3:3 holdout, not leave-one-out** (and it evaluates Recall@20). A
  different train/test construction ⇒ different task.
- **Hi-SAM** (KDD'26) — Books counts ≈ match (rounded), **but it uses a 90 %/10 %
  chronological split, treats rating > 3 as positive, and evaluates a CTR task
  (AUC/GAUC)** — a fundamentally different setup.

Also excluded by the statistics gate (README "near-match", extra filter on top of
5-core ⇒ counts ~2–6 % smaller): **ReSID** (drops items without side-info),
**Multimodal-GR** (drops items without images), **SPARC** (keeps only rating ≥ 4).

---

*Numbers transcribed from each paper's main results table; per-paper notes (data
processing, full baseline lists, GPU usage, code links) are in
`RecSys_EvaluationDataset/Freq_132_Amazon-2023/`.*
