# SIDReasoner Baseline · Video_Games · First 500 — Per-Item Analysis

> Source: HF `yufan/rec_inference_results/baseline_Video_Games.json` (official-endpoint decoding). Thinking mode + constrained beam-10; `native` = greedy single-shot after `</think>`.

## Method
Each item is analyzed on four axes: **(1) Rec↔GT gap** SID prefix-depth a>b>c(0–3) + platform mismatch; **(2) Beam diversity** unique a/(a,b)/platform/title & collapse; **(3) Reasoning quality** restatement/novel-candidate/genre/pivot; **(4) Target sensibility (ceiling)** — is the user's true target a continuation of, or an exploration away from, history, and is the *user's actual click* or *our recommendation* more history-consistent. Relatedness uses SID-prefix (SID itself is a semantic quantization) + platform + title-word overlap, in four tiers: SUBCLASS-continuation(3)/CLASS-continuation(2)/DRIFT(1)/EXPLORATION(0).

## ★ Target sensibility & performance ceiling (core)

**Distribution of the user's true target by relatedness to history** (governs whether history *can* predict it):
| Tier | Meaning | Count | Share | beam@10 HR | native HR |
|---|---|---:|---:|---:|---:|
| 3 SUBCLASS-continuation | repurchase/same-series | 19 | 3.8% | 47.4% | 42.1% |
| 2 CLASS-continuation | same big-class diff SKU | 114 | 22.8% | 16.7% | 6.1% |
| 1 DRIFT (platform/word-linked) | platform/word related | 218 | 43.6% | 5.0% | 0.5% |
| 0 EXPLORATION (unrelated) | brand-new domain | 149 | 29.8% | 1.3% | 0.0% |

- **Hard ceiling**: **EXPLORATION targets = 29.8%** (zero link to history), beam@10 HR only 1.3% → a history-based model basically cannot catch these; plus DRIFT 43.6% (HR 5.0%), **73.4% of targets are only weakly related or unrelated**.
- **Little catchable signal**: clear 'continuation' (class+subclass) is only **26.6%**; nearly all model gains come from here (subclass HR 47.4%, class HR 16.7%).
- **Who is more sensible (conservativeness)**: mean relatedness target=1.01 vs our pred[0]=1.83 vs native=2.07. Our recommendation is **more history-consistent than the user's actual click** in **299 (60%)** items, more divergent in 40 (8%), same tier in 161. → **the model is systematically more conservative than the user**: it bets on 'history continuation' while ~half of users explore, and this mismatch is the main ceiling driver.
- **Implication**: on the exploration/drift subset any pure history-sequence model has a low ceiling; real headroom is (a) raising HR within the **26.6% continuation** tier, and (b) injecting **non-history signals** (content/collaborative/temporal/context) to attack the exploration tier.

---

## Per-item analysis (#0–#499)

### #0 — Category-OK·item wrong · BEAM-COLLAPSE (<a_245×9/10)
- **History** (6 items; platforms PS3×4,PS×2): PlayStation Eye | PlayStation Eye | Angry Birds Star Wars - Pl… | DuckTales - Remastered PS3… | Minecraft - PlayStation 3 | LEGO Jurassic World - Play…
- **GT**: `<a_111><b_158><c_21>` Just Dance 2017 - PlayStation 3 _(platform PS3)_ ｜ **native**: `<a_245><b_232><c_5>` LEGO Jurassic World - PlayStat… ✗
- **beam top5**: `<a_245><b_91><c_144>`PS3, `<a_245><b_232><c_39>`PSV, `<a_245><b_86><c_8>`PS3, `<a_245><b_232><c_5>`PS3, `<a_245><b_91><c_188>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS3); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_245 family 9/10); unique(a,b)=6/10, platforms=5, unique titles=10/10.
- **Reasoning quality**: cites 4/5 history items (coverage 80%), anchored on: Angry Birds Star Wars …, LEGO Jurassic World - …, DuckTales - Remastered…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #1 — Category-miss·even top-class (a) wrong
- **History** (4 items; platforms PS4×4): Metro Redux - PlayStation … | Dark Souls III - PlayStati… | Madden NFL 17 - Standard E… | Titanfall 2 - PlayStation …
- **GT**: `<a_194><b_97><c_127>` Demon's Souls _(platform ?)_ ｜ **native**: `<a_39><b_51><c_21>` Titanfall 2 - Xbox One ✗
- **beam top5**: `<a_39><b_77><c_105>`Xbo, `<a_201><b_56><c_74>`PS4, `<a_39><b_51><c_21>`Xbo, `<a_39><b_78><c_54>`PS4, `<a_39><b_77><c_69>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=7/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Metro Redux - PlayStat…, Dark Souls III - PlayS…, Madden NFL 17 - Standa…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,multiplayer,immersive.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item. Note: target shares word(s) ['souls'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #2 — Category-OK·item wrong
- **History** (5 items; platforms PS4×5): Watch Dogs 2 - PlayStation… | Ratchet & Clank - PlayStat… | Horizon Zero Dawn - PlaySt… | CorpCo 6ft AC Power Cord f… | Deadpool - PlayStation 4
- **GT**: `<a_61><b_251><c_51>` DualShock 4 Wireless Controller for PlayStatio… _(platform PS4)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_24><b_86><c_14>`PS4, `<a_201><b_31><c_107>`PS4, `<a_201><b_18><c_56>`PS4, `<a_123><b_58><c_78>`PS4, `<a_24><b_96><c_27>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=10/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 5/5 history items (coverage 100%), anchored on: Watch Dogs 2 - PlaySta…, Ratchet & Clank - Play…, Horizon Zero Dawn - Pl…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #3 — Hit@2 · RERANK-HARM
- **History** (6 items; platforms PS4×6): Watch Dogs 2 - PlayStation… | Ratchet & Clank - PlayStat… | Horizon Zero Dawn - PlaySt… | CorpCo 6ft AC Power Cord f… | Deadpool - PlayStation 4 | DualShock 4 Wireless Contr…
- **GT**: `<a_201><b_31><c_107>` Uncharted 4: A Thief's End - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_201><b_31><c_107>` Uncharted 4: A Thief's End - P… ✓
- **beam top5**: `<a_61><b_251><c_144>`PS4, `<a_201><b_31><c_107>`PS4, `<a_201><b_213><c_242>`PS4, `<a_123><b_58><c_78>`PS4, `<a_201><b_151><c_255>`PS
- **Rec↔GT gap**: correct item at beam rank 2, pred[0] prefix-depth only 0/3; platform consistent(PS4); in beam: share-a=4/10, share-(a,b)=1/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/6 history items (coverage 67%), anchored on: Watch Dogs 2 - PlaySta…, Horizon Zero Dawn - Pl…, CorpCo 6ft AC Power Co…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=SUBCLASS-continuation (score3). target is a sensible DRIFT and **was caught**.

### #4 — Category-OK·item wrong
- **History** (7 items; platforms PS4×7): Ratchet & Clank - PlayStat… | Horizon Zero Dawn - PlaySt… | CorpCo 6ft AC Power Cord f… | Deadpool - PlayStation 4 | DualShock 4 Wireless Contr… | Uncharted 4: A Thief's End…
- **GT**: `<a_189><b_243><c_254>` Limited Edition Vertical Stand for Glacier Whi… _(platform PS4)_ ｜ **native**: `<a_201><b_213><c_242>` The Last of Us Remastered - Pl… ✗
- **beam top5**: `<a_123><b_58><c_78>`PS4, `<a_24><b_86><c_14>`PS4, `<a_201><b_18><c_56>`PS4, `<a_201><b_56><c_74>`PS4, `<a_201><b_213><c_242>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=10/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 6/7 history items (coverage 86%), anchored on: Watch Dogs 2 - PlaySta…, Horizon Zero Dawn - Pl…, CorpCo 6ft AC Power Co…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item.

### #5 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_61×9/10)
- **History** (1 items; platforms Xbox360×1): JINHEZO Sensor TV Mount Cl…
- **GT**: `<a_118><b_162><c_110>` Batman: Arkham Origins - Playstation 3 _(platform PS3)_ ｜ **native**: `<a_61><b_181><c_195>` Xbox 360 Wireless Controller -… ✗
- **beam top5**: `<a_61><b_181><c_195>`Xbo, `<a_61><b_137><c_255>`Xbo, `<a_189><b_45><c_10>`Xbo, `<a_61><b_56><c_2>`Xbo, `<a_61><b_181><c_175>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS3 vs rec=Xbox360); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_61 family 9/10); unique(a,b)=6/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 1/1 history items (coverage 100%), anchored on: JINHEZO Sensor TV Moun…; novel candidates=0 (**pure history restatement**); genre: accessor.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=DRIFT (platform/word-linked) (score1). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #6 — Category-miss·even top-class (a) wrong
- **History** (2 items; platforms Xbox360×1,PS3×1): JINHEZO Sensor TV Mount Cl… | Batman: Arkham Origins - P…
- **GT**: `<a_49><b_218><c_81>` LEGO Marvel Super Heroes - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_61><b_181><c_195>` Xbox 360 Wireless Controller -… ✗
- **beam top5**: `<a_61><b_181><c_195>`Xbo, `<a_61><b_214><c_252>`Xbo, `<a_118><b_41><c_55>`?, `<a_118><b_1><c_224>`Xbo, `<a_118><b_162><c_110>`PS3
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS4 vs rec=Xbox360); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=10/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: JINHEZO Sensor TV Moun…, Batman: Arkham Origins…; novel candidates=0 (**pure history restatement**); genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=DRIFT (platform/word-linked) (score1). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #7 — Category-OK·item wrong
- **History** (3 items; platforms Xbox360×1,PS3×1,PS4×1): JINHEZO Sensor TV Mount Cl… | Batman: Arkham Origins - P… | LEGO Marvel Super Heroes -…
- **GT**: `<a_49><b_236><c_171>` LEGO Marvel's Avengers - Xbox 360 _(platform Xbox360)_ ｜ **native**: `<a_201><b_213><c_242>` The Last of Us Remastered - Pl… ✗
- **beam top5**: `<a_123><b_72><c_7>`PS4, `<a_201><b_31><c_107>`PS4, `<a_245><b_185><c_59>`PS4, `<a_201><b_213><c_242>`PS4, `<a_49><b_47><c_60>`PSV
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform mismatch(GT=Xbox360 vs rec=PS4); in beam: share-a=1/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=10/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Batman: Arkham Origins…, LEGO Marvel Super Hero…, JINHEZO Sensor TV Moun…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=DRIFT (platform/word-linked) (score1). user's pick is **more history-consistent** than our top-1 (target2>rec1) → we **drifted off** a catchable continuation. Note: target shares word(s) ['lego'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #8 — Category-OK·item wrong
- **History** (4 items; platforms Xbox360×2,PS3×1,PS4×1): JINHEZO Sensor TV Mount Cl… | Batman: Arkham Origins - P… | LEGO Marvel Super Heroes -… | LEGO Marvel's Avengers - X…
- **GT**: `<a_131><b_210><c_0>` Fallout 4 - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_49><b_47><c_60>` LEGO Marvel Super Heroes - PS … ✗
- **beam top5**: `<a_123><b_72><c_7>`PS4, `<a_49><b_47><c_60>`PSV, `<a_123><b_72><c_191>`Xbo, `<a_245><b_185><c_59>`PS4, `<a_217><b_121><c_56>`PSV
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=9/10, platforms=5, unique titles=10/10.
- **Reasoning quality**: cites 3/4 history items (coverage 75%), anchored on: LEGO Marvel Super Hero…, LEGO Marvel's Avengers…, Batman: Arkham Origins…; novel candidates=0 (**pure history restatement**); genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item.

### #9 — Category-OK·item wrong
- **History** (5 items; platforms Xbox360×2,PS4×2,PS3×1): JINHEZO Sensor TV Mount Cl… | Batman: Arkham Origins - P… | LEGO Marvel Super Heroes -… | LEGO Marvel's Avengers - X… | Fallout 4 - PlayStation 4
- **GT**: `<a_74><b_218><c_206>` Ratchet & Clank - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_118><b_185><c_102>` Batman: Arkham Knight - PlaySt… ✗
- **beam top5**: `<a_123><b_72><c_7>`PS4, `<a_118><b_185><c_102>`PS4, `<a_201><b_31><c_107>`PS4, `<a_201><b_145><c_9>`PS4, `<a_118><b_95><c_6>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=10/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/5 history items (coverage 80%), anchored on: Batman: Arkham Origins…, Fallout 4 - PlayStatio…, LEGO Marvel Super Hero…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item.

### #10 — Category-OK·item wrong
- **History** (6 items; platforms PS4×3,Xbox360×2,PS3×1): JINHEZO Sensor TV Mount Cl… | Batman: Arkham Origins - P… | LEGO Marvel Super Heroes -… | LEGO Marvel's Avengers - X… | Fallout 4 - PlayStation 4 | Ratchet & Clank - PlayStat…
- **GT**: `<a_13><b_1><c_233>` Plants vs. Zombies Garden Warfare 2 - PlayStat… _(platform PS4)_ ｜ **native**: `<a_118><b_185><c_102>` Batman: Arkham Knight - PlaySt… ✗
- **beam top5**: `<a_123><b_72><c_7>`PS4, `<a_141><b_73><c_216>`PS4, `<a_118><b_185><c_102>`PS4, `<a_141><b_73><c_7>`PS4, `<a_201><b_31><c_107>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/6 history items (coverage 67%), anchored on: Batman: Arkham Origins…, Fallout 4 - PlayStatio…, LEGO Marvel Super Hero…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item.

### #11 — Category-OK·item wrong
- **History** (7 items; platforms PS4×4,Xbox360×2,PS3×1): Batman: Arkham Origins - P… | LEGO Marvel Super Heroes -… | LEGO Marvel's Avengers - X… | Fallout 4 - PlayStation 4 | Ratchet & Clank - PlayStat… | Plants vs. Zombies Garden …
- **GT**: `<a_24><b_72><c_142>` Horizon Zero Dawn - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_123><b_72><c_7>` Far Cry 4 - PlayStation 4 ✗
- **beam top5**: `<a_123><b_72><c_7>`PS4, `<a_74><b_128><c_20>`PS4, `<a_201><b_31><c_107>`PS4, `<a_141><b_73><c_216>`PS4, `<a_141><b_73><c_7>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (7 distinct a top-classes); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 5/7 history items (coverage 71%), anchored on: Batman: Arkham Origins…, Fallout 4 - PlayStatio…, LEGO Marvel Super Hero…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item.

### #12 — Category-miss·even top-class (a) wrong
- **History** (8 items; platforms PS4×5,Xbox360×2,PS3×1): LEGO Marvel Super Heroes -… | LEGO Marvel's Avengers - X… | Fallout 4 - PlayStation 4 | Ratchet & Clank - PlayStat… | Plants vs. Zombies Garden … | Horizon Zero Dawn - PlaySt…
- **GT**: `<a_217><b_148><c_123>` The Amazing Spider-Man 2 - Xbox 360 _(platform Xbox360)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_123><b_100><c_33>`PS4, `<a_201><b_18><c_56>`PS4, `<a_24><b_86><c_14>`PS4, `<a_123><b_58><c_78>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=Xbox360 vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=10/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 5/8 history items (coverage 62%), anchored on: Batman: Arkham Origins…, Fallout 4 - PlayStatio…, LEGO Marvel Super Hero…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item.

### #13 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_123×7/10)
- **History** (9 items; platforms PS4×5,Xbox360×3,PS3×1): LEGO Marvel's Avengers - X… | Fallout 4 - PlayStation 4 | Ratchet & Clank - PlayStat… | Plants vs. Zombies Garden … | Horizon Zero Dawn - PlaySt… | The Amazing Spider-Man 2 -…
- **GT**: `<a_217><b_176><c_0>` Teenage Mutant Ninja Turtles: Mutants in Manha… _(platform Xbox360)_ ｜ **native**: `<a_123><b_100><c_33>` Tom Clancy&rsquo;s Ghost Recon… ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_123><b_100><c_33>`PS4, `<a_123><b_76><c_232>`PS4, `<a_123><b_100><c_0>`Xbo, `<a_123><b_58><c_78>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=Xbox360 vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_123 family 7/10); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/9 history items (coverage 44%), anchored on: Batman: Arkham Origins…, Fallout 4 - PlayStatio…, LEGO Marvel Super Hero…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=DRIFT (platform/word-linked) (score1). user's pick is **more history-consistent** than our top-1 (target2>rec1) → we **drifted off** a catchable continuation.

### #14 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_123×7/10)
- **History** (6 items; platforms Xbox360×4,?×2): Guitar Hero 2 - Xbox 360 | Thief - Xbox 360 | The Amazing Spider-Man | Watch Dogs - Xbox 360 | Minecraft | Far Cry 4 - Xbox 360
- **GT**: `<a_39><b_51><c_188>` Titanfall 2 - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_123><b_72><c_191>` Far Cry 4 - Xbox One ✗
- **beam top5**: `<a_123><b_72><c_191>`Xbo, `<a_123><b_102><c_217>`Xbo, `<a_123><b_72><c_33>`PC, `<a_123><b_233><c_44>`?, `<a_123><b_246><c_254>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS4 vs rec=XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_123 family 7/10); unique(a,b)=7/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 5/6 history items (coverage 83%), anchored on: Guitar Hero 2 - Xbox 3…, Thief - Xbox 360, Far Cry 4 - Xbox 360; novel candidates=0 (**pure history restatement**); genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=SUBCLASS-continuation (score3). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #15 — Hit@6
- **History** (1 items; platforms PS4×1): PlayStation 4 Camera (Old …
- **GT**: `<a_61><b_251><c_51>` DualShock 4 Wireless Controller for PlayStatio… _(platform PS4)_ ｜ **native**: `<a_201><b_213><c_242>` The Last of Us Remastered - Pl… ✗
- **beam top5**: `<a_231><b_28><c_63>`PS4, `<a_201><b_31><c_107>`PS4, `<a_201><b_213><c_242>`PS4, `<a_8><b_4><c_188>`PS4, `<a_39><b_182><c_247>`PS4
- **Rec↔GT gap**: correct item at beam rank 6, pred[0] prefix-depth only 0/3; platform consistent(PS4); in beam: share-a=1/10, share-(a,b)=1/10.
- **Beam diversity**: **High** (6 distinct a top-classes); unique(a,b)=10/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 0/1 history items (coverage 0%); novel candidates=0 (**pure history restatement**); genre: peripheral,accessor.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). target is a sensible DRIFT and **was caught**.

### #16 — Category-OK·item wrong
- **History** (2 items; platforms PS4×2): PlayStation 4 Camera (Old … | DualShock 4 Wireless Contr…
- **GT**: `<a_140><b_50><c_3>` Call of Duty: Ghosts - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_201><b_213><c_242>` The Last of Us Remastered - Pl… ✗
- **beam top5**: `<a_231><b_28><c_63>`PS4, `<a_201><b_2><c_102>`PS4, `<a_201><b_201><c_84>`PS4, `<a_201><b_213><c_242>`PS4, `<a_201><b_36><c_181>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (6 distinct a top-classes); unique(a,b)=10/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 0/2 history items (coverage 0%); novel candidates=0 (**pure history restatement**); genre: action,immersive,accessor.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item.

### #17 — Category-miss·even top-class (a) wrong
- **History** (3 items; platforms PS4×3): PlayStation 4 Camera (Old … | DualShock 4 Wireless Contr… | Call of Duty: Ghosts - Pla…
- **GT**: `<a_21><b_19><c_204>` Nyko Net Connect for Wii _(platform Wii)_ ｜ **native**: `<a_201><b_213><c_242>` The Last of Us Remastered - Pl… ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_201><b_36><c_195>`PS4, `<a_39><b_204><c_65>`PS4, `<a_201><b_213><c_242>`PS4, `<a_201><b_2><c_102>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=Wii vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=10/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 0/3 history items (coverage 0%); novel candidates=0 (**pure history restatement**); templated opening; genre: action,shooter,immersive.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=DRIFT (platform/word-linked) (score1). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #18 — Category-OK·item wrong
- **History** (4 items; platforms PS4×3,Wii×1): PlayStation 4 Camera (Old … | DualShock 4 Wireless Contr… | Call of Duty: Ghosts - Pla… | Nyko Net Connect for Wii
- **GT**: `<a_140><b_164><c_230>` PlayStation 4 Battlefield 4 Launch Day Bundle _(platform PS4)_ ｜ **native**: `<a_21><b_19><c_204>` Nyko Net Connect for Wii ✗
- **beam top5**: `<a_61><b_47><c_32>`PS3, `<a_61><b_47><c_60>`PS, `<a_61><b_47><c_8>`PS3, `<a_21><b_19><c_204>`Wii, `<a_140><b_220><c_113>`PS
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform mismatch(GT=PS4 vs rec=PS3); in beam: share-a=4/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=6/10, platforms=6, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: PlayStation 4 Camera (…, DualShock 4 Wireless C…, Call of Duty: Ghosts -…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,shooter,immersive.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item.

### #19 — Category-OK·item wrong · BEAM-COLLAPSE (<a_61×8/10)
- **History** (3 items; platforms WiiU×1,PSVita×1,PS×1): Super Smash Bros. - Ninten… | Corpse Party: Blood Drive … | USPRO&reg; PlayStation 2 W…
- **GT**: `<a_61><b_248><c_151>` Steam Controller _(platform ?)_ ｜ **native**: `<a_61><b_247><c_90>` USPRO&reg; PlayStation 2 Wired… ✗
- **beam top5**: `<a_61><b_44><c_172>`PS4, `<a_61><b_247><c_172>`PS4, `<a_113><b_35><c_14>`Gam, `<a_61><b_35><c_122>`PS, `<a_61><b_228><c_90>`?
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; in beam: share-a=8/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_61 family 8/10); unique(a,b)=8/10, platforms=6, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Super Smash Bros. - Ni…, Corpse Party: Blood Dr…, USPRO&reg; PlayStation…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,horror,multiplayer.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item. Note: target shares word(s) ['controller'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #20 — Category-OK·item wrong
- **History** (4 items; platforms XboxOne×3,?×1): Wolfenstein: The New Order | Grand Theft Auto V - Xbox … | Doom - Xbox One | Naruto Shippuden: Ultimate…
- **GT**: `<a_86><b_105><c_118>` South Park: The Fractured but Whole - Xbox One _(platform XboxOne)_ ｜ **native**: `<a_131><b_155><c_206>` Fallout 4 - Xbox One ✗
- **beam top5**: `<a_131><b_155><c_206>`Xbo, `<a_39><b_69><c_69>`Xbo, `<a_39><b_77><c_69>`Xbo, `<a_131><b_55><c_86>`Xbo, `<a_39><b_77><c_105>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (2 a top-classes); unique(a,b)=9/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Wolfenstein: The New O…, Grand Theft Auto V - X…, Doom - Xbox One; novel candidates=0 (**pure history restatement**); templated opening; genre: action,shooter,fighting.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item.

### #21 — Category-miss·even top-class (a) wrong
- **History** (3 items; platforms PS4×2,PSVita×1): Transformers Devastation -… | PlayStation 4 500GB Consol… | Sony PlayStation Vita WiFi
- **GT**: `<a_7><b_36><c_217>` Xbox One X 1TB Limited Edition Console - Proje… _(platform XboxOne)_ ｜ **native**: `<a_201><b_213><c_242>` The Last of Us Remastered - Pl… ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_208><b_175><c_0>`PS4, `<a_131><b_210><c_0>`PS4, `<a_201><b_36><c_181>`PS4, `<a_201><b_213><c_242>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=XboxOne vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=10/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Transformers Devastati…, PlayStation 4 500GB Co…, Sony PlayStation Vita …; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**. Note: target shares word(s) ['discontinued', 'limited'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #22 — Category-OK·item wrong
- **History** (4 items; platforms PS4×2,WiiU×1,3DS×1): Gravity Rush Remastered - … | Valkyria Chronicles Remast… | Tokyo Mirage Sessions #FE … | Nintendo - New 3DS XL Lege…
- **GT**: `<a_30><b_92><c_0>` Persona 5 - Standard Edition - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_1><b_150><c_189>` Legend of Heroes: Trails of Co… ✗
- **beam top5**: `<a_121><b_35><c_0>`PS4, `<a_1><b_25><c_254>`3DS, `<a_1><b_150><c_189>`PS3, `<a_1><b_177><c_184>`PS4, `<a_1><b_68><c_121>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (2 a top-classes); unique(a,b)=10/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Gravity Rush Remastere…, Valkyria Chronicles Re…, Tokyo Mirage Sessions …; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,strategy.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #23 — Category-miss·even top-class (a) wrong
- **History** (10 items; platforms ?×3,Wii×2,PS×2): Mercenaries: Playground of… | Donkey Kong Country Return… | PS3 500 GB Grand Theft Aut… | The Legend of Zelda: Twili… | Black - PlayStation 2 | Tomb Raider Game of the Ye…
- **GT**: `<a_240><b_157><c_13>` Manhunt - PlayStation 2 _(platform PS2)_ ｜ **native**: `<a_239><b_39><c_242>` Kirby Nightmare in Dream Land ✗
- **beam top5**: `<a_71><b_66><c_11>`?, `<a_239><b_236><c_95>`Wii, `<a_24><b_156><c_78>`PS3, `<a_239><b_196><c_173>`?, `<a_175><b_83><c_0>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=9/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 6/10 history items (coverage 60%), anchored on: Kirby's Return to Drea…, Donkey Kong Country Re…, Ghostbusters: The Vide…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item.

### #24 — Category-OK·item wrong · BEAM-COLLAPSE (<a_80×7/10)
- **History** (7 items; platforms GameCube×3,PS4×2,?×2): Resident Evil 2 - Gamecube | The Evil Within - PlayStat… | Resident Evil 3: Nemesis | Resident Evil - Gamecube | Resident Evil 4 - PlayStat… | Resident Evil Code Veronic…
- **GT**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - PS4 Digital Code _(platform PS4)_ ｜ **native**: `<a_80><b_59><c_0>` Resident Evil 2 ✗
- **beam top5**: `<a_80><b_59><c_248>`Xbo, `<a_80><b_59><c_0>`?, `<a_80><b_59><c_29>`PS3, `<a_80><b_59><c_159>`PS, `<a_123><b_67><c_103>`Gam
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform mismatch(GT=PS4 vs rec=Xbox360); in beam: share-a=3/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_80 family 7/10); unique(a,b)=3/10, platforms=5, unique titles=10/10.
- **Reasoning quality**: cites 4/7 history items (coverage 57%), anchored on: Resident Evil 4 - Game…, Resident Evil 2 - Game…, The Evil Within - Play…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=SUBCLASS-continuation (score3). we recommended something **more history-consistent** than the user's actual pick (rec3>target2) → **model too conservative / user more exploratory**. Note: target shares word(s) ['code', 'evil', 'resident'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #25 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_21×10/10)
- **History** (9 items; platforms ?×2,PS2×2,PS3×1): PS2 Controller Extension C… | PS2 Controller Extension C… | Retro Bit Universal 3 in 1… | 4x Wii/Gamecube Extension … | GBA SP Gameboy Game boy Ad… | Buffalo iBuffalo Classic U…
- **GT**: `<a_13><b_87><c_62>` Time Crisis: Razing Storm - Playstation 3 _(platform PS3)_ ｜ **native**: `<a_21><b_44><c_75>` PS2 Controller Extension Cable… ✗
- **beam top5**: `<a_21><b_44><c_75>`PS2, `<a_21><b_138><c_81>`Gam, `<a_21><b_144><c_105>`?, `<a_21><b_18><c_85>`PS3, `<a_21><b_117><c_122>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS3 vs rec=PS2); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_21 family 10/10); unique(a,b)=10/10, platforms=6, unique titles=10/10.
- **Reasoning quality**: cites 7/8 history items (coverage 88%), anchored on: Sega Saturn System - V…, PS3 Optical Digital Ca…, PS2 Controller Extensi…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,nostalg,retro.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=SUBCLASS-continuation (score3). we recommended something **more history-consistent** than the user's actual pick (rec3>target1) → **model too conservative / user more exploratory**.

### #26 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_113×7/10)
- **History** (4 items; platforms ?×1,PS×1,DS×1): Street Fighter Anniversary… | Buyee 128MB Memory Card fo… | Nintendo 2DS - Electric Bl… | HORI Compact PlayStand - Z…
- **GT**: `<a_250><b_55><c_95>` Mario Kart 7 _(platform ?)_ ｜ **native**: `<a_113><b_232><c_97>` Redesigned REPLACEMENT Joystic… ✗
- **beam top5**: `<a_113><b_232><c_97>`?, `<a_208><b_196><c_65>`PS, `<a_113><b_91><c_165>`?, `<a_61><b_228><c_90>`?, `<a_113><b_235><c_2>`3DS
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_113 family 7/10); unique(a,b)=8/10, platforms=5, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Street Fighter Anniver…, Buyee 128MB Memory Car…, Nintendo 2DS - Electri…; novel candidates=0 (**pure history restatement**); genre: action,fighting,nostalg.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #27 — Category-miss·even top-class (a) wrong
- **History** (5 items; platforms ?×2,PS×1,DS×1): Street Fighter Anniversary… | Buyee 128MB Memory Card fo… | Nintendo 2DS - Electric Bl… | HORI Compact PlayStand - Z… | Mario Kart 7
- **GT**: `<a_119><b_109><c_15>` Lilyy Protective Soft Silicone Rubber Gel Skin… _(platform ?)_ ｜ **native**: `<a_113><b_232><c_97>` Redesigned REPLACEMENT Joystic… ✗
- **beam top5**: `<a_113><b_232><c_97>`?, `<a_250><b_21><c_158>`?, `<a_113><b_235><c_2>`3DS, `<a_113><b_35><c_14>`Gam, `<a_193><b_104><c_221>`PC
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=9/10, platforms=5, unique titles=10/10.
- **Reasoning quality**: cites 5/5 history items (coverage 100%), anchored on: Street Fighter Anniver…, Nintendo 2DS - Electri…, Mario Kart 7; novel candidates=0 (**pure history restatement**); templated opening; genre: action,fighting,racing.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**. Note: target shares word(s) ['2ds'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #28 — Category-OK·item wrong · BEAM-COLLAPSE (<a_113×9/10)
- **History** (6 items; platforms ?×2,DS×2,PS×1): Street Fighter Anniversary… | Buyee 128MB Memory Card fo… | Nintendo 2DS - Electric Bl… | HORI Compact PlayStand - Z… | Mario Kart 7 | Lilyy Protective Soft Sili…
- **GT**: `<a_119><b_178><c_139>` Mudder Protective Travel Carrying Case Cover f… _(platform ?)_ ｜ **native**: `<a_113><b_104><c_28>` Nintendo 3DS Compatible with 3… ✗
- **beam top5**: `<a_113><b_104><c_28>`3DS, `<a_113><b_232><c_97>`?, `<a_113><b_230><c_103>`3DS, `<a_113><b_174><c_101>`?, `<a_113><b_235><c_2>`3DS
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; in beam: share-a=1/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_113 family 9/10); unique(a,b)=9/10, platforms=6, unique titles=10/10.
- **Reasoning quality**: cites 4/6 history items (coverage 67%), anchored on: Street Fighter Anniver…, Mario Kart 7, Nintendo 2DS - Electri…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,nostalg,retro.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item. Note: target shares word(s) ['2ds', 'case', 'cover', 'protective'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #29 — Category-miss·even top-class (a) wrong
- **History** (10 items; platforms PS4×7,XboxOne×2,PC×1): Mass Effect Andromeda - Pr… | Grand Theft Auto V - Xbox … | Horizon Zero Dawn - PlaySt… | Watch Dogs 2 - PlayStation… | Watch Dogs 2: Deluxe Editi… | Persona 5 - Standard Editi…
- **GT**: `<a_201><b_151><c_255>` Playstation Plus: 3 Month Membership [Digital … _(platform PS-generic)_ ｜ **native**: `<a_30><b_92><c_146>` Persona 5 - SteelBook Edition … ✗
- **beam top5**: `<a_24><b_185><c_47>`Xbo, `<a_30><b_92><c_146>`PS4, `<a_24><b_38><c_11>`PS4, `<a_30><b_92><c_0>`PS4, `<a_191><b_76><c_188>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS-generic vs rec=XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=9/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 6/10 history items (coverage 60%), anchored on: Dishonored 2 - PlaySta…, Horizon Zero Dawn - Pl…, The Witness - PS4 [Dig…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item. Note: target shares word(s) ['code', 'digital'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #30 — Category-miss·even top-class (a) wrong
- **History** (2 items; platforms PS×2): Shin Megami Tensei: Person… | Shin Megami Tensei: Person…
- **GT**: `<a_201><b_239><c_3>` Resident Evil Origins Collection - PlayStation… _(platform PS4)_ ｜ **native**: `<a_30><b_104><c_169>` Shin Megami Tensei: Persona 3 … ✗
- **beam top5**: `<a_30><b_104><c_169>`PS, `<a_195><b_171><c_31>`PSP, `<a_30><b_128><c_164>`PS3, `<a_216><b_92><c_163>`3DS, `<a_30><b_106><c_179>`PSV
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS4 vs rec=PS2); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=9/10, platforms=6, unique titles=10/10.
- **Reasoning quality**: cites 1/1 history items (coverage 100%), anchored on: Shin Megami Tensei: Pe…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,immersive.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=SUBCLASS-continuation (score3). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #31 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_113×9/10)
- **History** (5 items; platforms Wii×2,?×1,PC×1): Mayflash W010 Wireless Sen… | Logitech G27 Racing Wheel | Buffalo iBuffalo Classic U… | New Super Mario Bros. Wii | Super Mario Maker - Ninten…
- **GT**: `<a_202><b_115><c_229>` AULA LED Backlit Gaming Keyboard (3 Colorways) _(platform ?)_ ｜ **native**: `<a_113><b_35><c_14>` Nintendo Super Smash Bros. Bla… ✗
- **beam top5**: `<a_113><b_9><c_63>`Wii, `<a_113><b_147><c_140>`Wii, `<a_113><b_104><c_28>`3DS, `<a_113><b_240><c_225>`Wii, `<a_113><b_35><c_14>`Gam
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_113 family 9/10); unique(a,b)=8/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 5/5 history items (coverage 100%), anchored on: Mayflash W010 Wireless…, Buffalo iBuffalo Class…, New Super Mario Bros. …; novel candidates=0 (**pure history restatement**); genre: platformer,multiplayer,nostalg.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=DRIFT (platform/word-linked) (score1). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #32 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_216×10/10)
- **History** (10 items; platforms 3DS×4,?×3,PSVita×2): Theatrhythm Final Fantasy:… | Nintendo NFC Reader/Writer… | Animal Crossing Card amiib… | Mario & Sonic at the Londo… | Tearaway | The Legend of Zelda: Major…
- **GT**: `<a_10><b_86><c_68>` The Elder Scrolls V: Skyrim Legendary Edition … _(platform ?)_ ｜ **native**: `<a_216><b_51><c_130>` Xenoblade Chronicles 3D - New … ✗
- **beam top5**: `<a_216><b_93><c_101>`DS, `<a_216><b_112><c_114>`Wii, `<a_216><b_219><c_158>`3DS, `<a_216><b_51><c_130>`3DS, `<a_216><b_122><c_148>`3DS
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_216 family 10/10); unique(a,b)=9/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 8/10 history items (coverage 80%), anchored on: DanganRonpa: Trigger H…, The Legend of Zelda: M…, Bejeweled 3 - Nintendo…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,adventure,puzzle.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #33 — Category-OK·item wrong · BEAM-COLLAPSE (<a_205×10/10)
- **History** (3 items; platforms Xbox360×2,XboxOne×1): Forza Horizon - Xbox 360 | Forza Horizon 3 - Xbox One | Forza Motorsport 4 - Xbox …
- **GT**: `<a_245><b_155><c_254>` Middle Earth: Shadow of Mordor - Xbox One _(platform XboxOne)_ ｜ **native**: `<a_205><b_136><c_51>` Forza Horizon 2 for Xbox One ✗
- **beam top5**: `<a_205><b_136><c_51>`Xbo, `<a_205><b_40><c_3>`?, `<a_205><b_40><c_83>`?, `<a_205><b_136><c_234>`Xbo, `<a_205><b_60><c_111>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_205 family 10/10); unique(a,b)=7/10, platforms=4, unique titles=9/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Forza Horizon - Xbox 3…, Forza Horizon 3 - Xbox…, Forza Motorsport 4 - X…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,racing,multiplayer.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #34 — Category-miss·even top-class (a) wrong
- **History** (5 items; platforms DS×1,PC×1,?×1): SteelSeries Flux Gaming He… | Dark Souls II: Collector's… | Halo 5: Guardians | Fallout 4: Contraptions Wo… | HORI Compact PlayStand - Z…
- **GT**: `<a_89><b_221><c_81>` $20 Battle.net Store Gift Card Balance - Blizz… _(platform ?)_ ｜ **native**: `<a_131><b_137><c_58>` Fallout 4: Contraptions Worksh… ✗
- **beam top5**: `<a_61><b_44><c_172>`PS4, `<a_61><b_131><c_197>`Xbo, `<a_7><b_248><c_16>`Xbo, `<a_131><b_155><c_206>`Xbo, `<a_7><b_248><c_2>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=9/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 5/5 history items (coverage 100%), anchored on: Dark Souls II: Collect…, Fallout 4: Contraption…, HORI Compact PlayStand…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,immersive.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=EXPLORATION (unrelated) (score0). user's pick is **more history-consistent** than our top-1 (target1>rec0) → we **drifted off** a catchable continuation. Note: target shares word(s) ['code', 'digital'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #35 — Category-OK·item wrong · BEAM-COLLAPSE (<a_39×8/10)
- **History** (7 items; platforms XboxOne×3,?×2,Xbox360×2): Call of Duty: Black Ops II… | Titanfall - Xbox One | R.C. Pro-Am | Borderlands Triple Pack - … | Destiny: The Taken King - … | Forza Motorsport 6 - Xbox …
- **GT**: `<a_123><b_33><c_95>` Resident Evil 5 - Standard Edition - Xbox One _(platform XboxOne)_ ｜ **native**: `<a_39><b_151><c_9>` Halo 5: Guardians ✗
- **beam top5**: `<a_39><b_114><c_237>`Xbo, `<a_39><b_77><c_69>`Xbo, `<a_39><b_114><c_209>`Xbo, `<a_39><b_77><c_105>`Xbo, `<a_39><b_151><c_9>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_39 family 8/10); unique(a,b)=8/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 6/7 history items (coverage 86%), anchored on: Call of Duty: Black Op…, Titanfall - Xbox One, R.C. Pro-Am; novel candidates=0 (**pure history restatement**); templated opening; genre: action,shooter,racing.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #36 — Category-miss·even top-class (a) wrong
- **History** (3 items; platforms PS4×2,PS3×1): Sony Computer Entertainmen… | Tom Clancy's The Division … | Mega Man Legacy Collection…
- **GT**: `<a_249><b_180><c_74>` PlayStation Vita Memory Card 64GB (PCH-Z641J) _(platform PSVita)_ ｜ **native**: `<a_201><b_31><c_107>` Uncharted 4: A Thief's End - P… ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_131><b_210><c_0>`PS4, `<a_201><b_2><c_102>`PS4, `<a_131><b_209><c_151>`PS4, `<a_201><b_213><c_242>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PSVita vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (6 distinct a top-classes); unique(a,b)=10/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Tom Clancy's The Divis…, Mega Man Legacy Collec…, Sony Computer Entertai…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=DRIFT (platform/word-linked) (score1). user's pick is **more history-consistent** than our top-1 (target2>rec1) → we **drifted off** a catchable continuation.

### #37 — Category-OK·item wrong
- **History** (1 items; platforms PS4×1): Star Wars: Battlefront - S…
- **GT**: `<a_45><b_226><c_3>` NHL 17 - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_131><b_210><c_0>` Fallout 4 - PlayStation 4 ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_131><b_210><c_0>`PS4, `<a_201><b_36><c_195>`PS4, `<a_141><b_73><c_7>`PS4, `<a_201><b_213><c_242>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=9/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 0/1 history items (coverage 0%); novel candidates=0 (**pure history restatement**); genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item.

### #38 — Category-OK·item wrong
- **History** (5 items; platforms PS4×3,?×2): Doom - PlayStation 4 | Rise of the Tomb Raider: 2… | Atari Flashback Classics: … | Atari Flashback Classics: … | Dragon Quest Builders - Pl…
- **GT**: `<a_205><b_208><c_148>` Gran Turismo Sport - Limited Edition - PlaySta… _(platform PS4)_ ｜ **native**: `<a_1><b_43><c_207>` The Last Guardian - PlayStatio… ✗
- **beam top5**: `<a_123><b_58><c_78>`PS4, `<a_1><b_43><c_207>`PS4, `<a_1><b_173><c_4>`PS4, `<a_24><b_72><c_142>`PS4, `<a_131><b_209><c_151>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (7 distinct a top-classes); unique(a,b)=10/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Doom - PlayStation 4, Rise of the Tomb Raide…, Atari Flashback Classi…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item.

### #39 — Category-OK·item wrong · BEAM-COLLAPSE (<a_162×7/10)
- **History** (6 items; platforms ?×3,3DS×2,WiiU×1): Yoshi amiibo (Super Smash … | PDP New Nintendo 3DS XL Cl… | Ganondorf amiibo - Japan I… | Wolf Link Amiibo Jp Model … | Kirby amiibo - Nintendo 3D… | Nintendo Diddy Kong amiibo…
- **GT**: `<a_162><b_134><c_221>` Donkey Kong amiibo - Japan Import (Super Smash… _(platform ?)_ ｜ **native**: `<a_162><b_147><c_226>` Nintendo Diddy Kong amiibo (SM… ✗
- **beam top5**: `<a_162><b_12><c_210>`Wii, `<a_162><b_130><c_2>`Wii, `<a_162><b_130><c_1>`Wii, `<a_162><b_130><c_72>`Wii, `<a_162><b_130><c_51>`Wii
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; in beam: share-a=7/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_162 family 7/10); unique(a,b)=7/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 0/6 history items (coverage 0%); novel candidates=0 (**pure history restatement**); templated opening; genre: action,accessor.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item. Note: target shares word(s) ['amiibo', 'bros', 'import', 'japan', 'kong'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #40 — Category-OK·item wrong · BEAM-COLLAPSE (<a_162×10/10)
- **History** (7 items; platforms ?×4,3DS×2,WiiU×1): PDP New Nintendo 3DS XL Cl… | Ganondorf amiibo - Japan I… | Wolf Link Amiibo Jp Model … | Kirby amiibo - Nintendo 3D… | Nintendo Diddy Kong amiibo… | Donkey Kong amiibo - Japan…
- **GT**: `<a_162><b_45><c_208>` Bowser Jr. amiibo - Japan Import (Super Smash … _(platform ?)_ ｜ **native**: `<a_162><b_130><c_72>` Nintendo Boo amiibo (SM Series… ✗
- **beam top5**: `<a_162><b_130><c_1>`Wii, `<a_162><b_130><c_2>`Wii, `<a_162><b_130><c_72>`Wii, `<a_162><b_12><c_210>`Wii, `<a_162><b_97><c_155>`?
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; in beam: share-a=10/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_162 family 10/10); unique(a,b)=7/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 2/7 history items (coverage 29%), anchored on: Donkey Kong amiibo - J…, Kirby amiibo - Nintend…; novel candidates=0 (**pure history restatement**); templated opening; genre: action.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item. Note: target shares word(s) ['amiibo', 'bros', 'import', 'japan', 'series'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #41 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_175×9/10)
- **History** (6 items; platforms PS3×2,PS4×1,WiiU×1): Final Fantasy XIII - Plays… | Doom - PlayStation 4 | Street Fighter X Tekken - … | Yoshi's Woolly World -  Wi… | Wii | Nintendo Selects: Donkey K…
- **GT**: `<a_191><b_204><c_225>` Just Cause 3 - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_175><b_24><c_4>` New Super Mario Bros. Wii ✗
- **beam top5**: `<a_175><b_24><c_4>`Wii, `<a_175><b_24><c_11>`?, `<a_175><b_24><c_254>`?, `<a_175><b_113><c_76>`?, `<a_175><b_73><c_7>`PS3
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS4 vs rec=Wii); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_175 family 9/10); unique(a,b)=5/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 4/6 history items (coverage 67%), anchored on: Final Fantasy XIII - P…, Doom - PlayStation 4, Nintendo Selects: Donk…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,fighting,multiplayer.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item.

### #42 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_250×10/10)
- **History** (8 items; platforms Xbox360×3,WiiU×2,Wii×1): Nintendo 3DS Midnight Purp… | SpongeBob SquarePants: Pla… | Guitar Hero III: Legends o… | Yoshi's Woolly World -  Wi… | Yoshi's Story | Donkey Kong Country Tropic…
- **GT**: `<a_84><b_92><c_101>` Carnival Games - Nintendo Wii _(platform Wii)_ ｜ **native**: `<a_250><b_57><c_233>` Super Mario 3D World - Nintend… ✗
- **beam top5**: `<a_250><b_57><c_233>`Wii, `<a_250><b_116><c_22>`Wii, `<a_250><b_219><c_103>`?, `<a_250><b_92><c_0>`?, `<a_250><b_112><c_111>`Wii
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=Wii vs rec=WiiU); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_250 family 10/10); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/8 history items (coverage 50%), anchored on: Yoshi's Woolly World -…, Donkey Kong Country Tr…, Nintendo 3DS Midnight …; novel candidates=0 (**pure history restatement**); templated opening; genre: action,adventure,narrative.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item.

### #43 — Category-miss·even top-class (a) wrong
- **History** (9 items; platforms Xbox360×3,Wii×2,WiiU×2): SpongeBob SquarePants: Pla… | Guitar Hero III: Legends o… | Yoshi's Woolly World -  Wi… | Yoshi's Story | Donkey Kong Country Tropic… | Carnival Games - Nintendo …
- **GT**: `<a_80><b_216><c_246>` Sonic Ultimate Genesis Collection - Xbox 360 _(platform Xbox360)_ ｜ **native**: `<a_84><b_222><c_22>` Mario Kart 8 - Nintendo Wii U ✗
- **beam top5**: `<a_84><b_222><c_135>`Wii, `<a_84><b_222><c_22>`Wii, `<a_84><b_109><c_95>`Wii, `<a_250><b_92><c_0>`?, `<a_84><b_222><c_164>`Wii
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=Xbox360 vs rec=Wii); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (2 a top-classes); unique(a,b)=8/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 5/9 history items (coverage 56%), anchored on: Wii, Yoshi's Woolly World -…, Donkey Kong Country Tr…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,adventure,multiplayer.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #44 — Category-miss·even top-class (a) wrong
- **History** (10 items; platforms Xbox360×4,Wii×2,WiiU×2): Guitar Hero III: Legends o… | Yoshi's Woolly World -  Wi… | Yoshi's Story | Donkey Kong Country Tropic… | Carnival Games - Nintendo … | Sonic Ultimate Genesis Col…
- **GT**: `<a_235><b_30><c_137>` Scooby Doo First Frights - Nintendo Wii _(platform Wii)_ ｜ **native**: `<a_250><b_57><c_233>` Super Mario 3D World - Nintend… ✗
- **beam top5**: `<a_84><b_222><c_22>`Wii, `<a_250><b_57><c_233>`Wii, `<a_84><b_222><c_135>`Wii, `<a_250><b_92><c_0>`?, `<a_84><b_222><c_164>`Wii
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=Wii vs rec=WiiU); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (2 a top-classes); unique(a,b)=7/10, platforms=3, unique titles=9/10.
- **Reasoning quality**: cites 5/10 history items (coverage 50%), anchored on: Wii, Yoshi's Woolly World -…, Donkey Kong Country Tr…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,adventure,multiplayer.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #45 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_250×9/10)
- **History** (10 items; platforms Xbox360×4,WiiU×2,Wii×2): Yoshi's Woolly World -  Wi… | Yoshi's Story | Donkey Kong Country Tropic… | Carnival Games - Nintendo … | Sonic Ultimate Genesis Col… | Scooby Doo First Frights -…
- **GT**: `<a_193><b_185><c_114>` Sonic Gems Collection - Gamecube _(platform GameCube)_ ｜ **native**: `<a_250><b_57><c_233>` Super Mario 3D World - Nintend… ✗
- **beam top5**: `<a_250><b_219><c_103>`?, `<a_250><b_57><c_233>`Wii, `<a_250><b_238><c_106>`DS, `<a_250><b_92><c_0>`?, `<a_250><b_120><c_101>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_250 family 9/10); unique(a,b)=10/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 5/10 history items (coverage 50%), anchored on: Yoshi's Woolly World -…, Donkey Kong Country Tr…, SpongeBob SquarePants:…; novel candidates=0 (**pure history restatement**); templated opening; genre: adventure,racing,puzzle.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**. Note: target shares word(s) ['collection', 'sonic'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #46 — Category-miss·even top-class (a) wrong
- **History** (3 items; platforms ?×2,Xbox360×1): Halo 3 - Xbox 360 | Call of Duty 4: Modern War… | Call of Duty 4: Modern War…
- **GT**: `<a_206><b_156><c_152>` Fortune Street _(platform ?)_ ｜ **native**: `<a_39><b_40><c_248>` Call of Duty: Modern Warfare 3… ✗
- **beam top5**: `<a_39><b_40><c_248>`Xbo, `<a_140><b_161><c_25>`Xbo, `<a_140><b_176><c_37>`Xbo, `<a_140><b_242><c_55>`?, `<a_140><b_212><c_79>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (2 a top-classes); unique(a,b)=8/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: Halo 3 - Xbox 360, Call of Duty 4: Modern…; novel candidates=0 (**pure history restatement**); genre: action,shooter,multiplayer.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #47 — Category-OK·item wrong
- **History** (7 items; platforms PS3×3,XboxOne×3,Xbox360×1): Assassin's Creed IV Black … | Assassin's Creed Rogue- Pl… | Battlefield Bad Company 2 … | Assassin's Creed Unity - X… | Far Cry Primal - Xbox One … | Watch Dogs xbox one
- **GT**: `<a_194><b_15><c_156>` Dishonored 2 - Xbox One _(platform XboxOne)_ ｜ **native**: `<a_123><b_72><c_191>` Far Cry 4 - Xbox One ✗
- **beam top5**: `<a_123><b_72><c_191>`Xbo, `<a_123><b_102><c_102>`Xbo, `<a_118><b_95><c_10>`Xbo, `<a_118><b_95><c_2>`Xbo, `<a_39><b_69><c_69>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=5/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 6/7 history items (coverage 86%), anchored on: Assassin's Creed - Pla…, Assassin's Creed IV Bl…, Assassin's Creed Rogue…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #48 — Category-miss·even top-class (a) wrong
- **History** (4 items; platforms PS×2,PS2×1,PC×1): PlayStation 2 Console Slim… | Mortal Kombat: Shaolin Mon… | Buyee 128MB Memory Card fo… | WWE SmackDown! Here Comes …
- **GT**: `<a_231><b_57><c_52>` WWE Smackdown! Shut Your Mouth _(platform ?)_ ｜ **native**: `<a_249><b_170><c_61>` Buyee 128MB Memory Card for So… ✗
- **beam top5**: `<a_249><b_138><c_30>`PS, `<a_249><b_138><c_211>`PS, `<a_80><b_73><c_171>`Xbo, `<a_80><b_241><c_223>`Xbo, `<a_175><b_27><c_27>`PS
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=8/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 3/4 history items (coverage 75%), anchored on: Mortal Kombat: Shaolin…, WWE SmackDown! Here Co…, Buyee 128MB Memory Car…; novel candidates=0 (**pure history restatement**); genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item. Note: target shares word(s) ['smackdown', 'wwe'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #49 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_162×10/10)
- **History** (8 items; platforms WiiU×5,?×3): Super Smash Bros. - Ninten… | Hyrule Warriors - Nintendo… | Super Mario Maker - Ninten… | Captain Falcon amiibo - Ja… | Wario amiibo - Japan Impor… | Nintendo Mr. Game & Watch …
- **GT**: `<a_216><b_54><c_190>` The Legend of Zelda: Breath of the Wild - Wii … _(platform WiiU)_ ｜ **native**: `<a_162><b_219><c_101>` Nintendo Super Smash Bros Palu… ✗
- **beam top5**: `<a_162><b_235><c_217>`?, `<a_162><b_57><c_111>`Wii, `<a_162><b_219><c_101>`?, `<a_162><b_219><c_233>`?, `<a_162><b_219><c_249>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_162 family 10/10); unique(a,b)=8/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 4/8 history items (coverage 50%), anchored on: Super Smash Bros. - Ni…, Super Mario Maker - Ni…, Captain Falcon amiibo …; novel candidates=0 (**pure history restatement**); templated opening; genre: action,competitive.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item.

### #50 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_231×7/10)
- **History** (9 items; platforms PS3×7,PS4×1,?×1): Minecraft - PlayStation 4 | NIKE Toddlers Tanjun (TDV)… | Call of Duty: Black Ops Co… | WWE 2K16 - PlayStation 3 | Call of Duty: Black Ops II… | Minecraft: Story Mode - Se…
- **GT**: `<a_189><b_154><c_99>` MIZAR 5 Empty Standard Playstation 3 Replaceme… _(platform PS3)_ ｜ **native**: `<a_231><b_107><c_4>` WWE 2K15 - PlayStation 4 ✗
- **beam top5**: `<a_231><b_237><c_82>`PS4, `<a_201><b_2><c_102>`PS4, `<a_201><b_31><c_107>`PS4, `<a_231><b_107><c_4>`PS4, `<a_231><b_117><c_8>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS3 vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_231 family 7/10); unique(a,b)=6/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 5/8 history items (coverage 62%), anchored on: Resident Evil 5 - Play…, Mortal Kombat: Komplet…, Minecraft: Story Mode …; novel candidates=0 (**pure history restatement**); templated opening; genre: action,fighting,horror.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=SUBCLASS-continuation (score3). we recommended something **more history-consistent** than the user's actual pick (rec3>target1) → **model too conservative / user more exploratory**.

### #51 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_202×10/10)
- **History** (4 items; platforms PC×2,?×1,Switch×1): Buffalo iBuffalo Classic U… | Fallout: New Vegas Ultimat… | Logitech G910 Orion Spark … | G810 Orion Spectrum RGB Me…
- **GT**: `<a_113><b_205><c_51>` Retro Link GameCube Style USB Wired Controller _(platform GameCube)_ ｜ **native**: `<a_202><b_33><c_133>` G810 Orion Spectrum RGB Mechan… ✗
- **beam top5**: `<a_202><b_58><c_105>`?, `<a_202><b_58><c_107>`?, `<a_202><b_82><c_172>`?, `<a_202><b_33><c_133>`Swi, `<a_202><b_34><c_39>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_202 family 10/10); unique(a,b)=7/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 3/4 history items (coverage 75%), anchored on: Buffalo iBuffalo Class…, Logitech G910 Orion Sp…, Fallout: New Vegas Ult…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,immersive,narrative.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=SUBCLASS-continuation (score3). we recommended something **more history-consistent** than the user's actual pick (rec3>target1) → **model too conservative / user more exploratory**. Note: target shares word(s) ['usb'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #52 — Category-OK·item wrong
- **History** (4 items; platforms PSVita×3,PS4×1): Resistance: Burning Skies … | LittleBigPlanet - PlayStat… | PlayStation All-Stars Batt… | Dishonored 2 - PlayStation…
- **GT**: `<a_39><b_51><c_188>` Titanfall 2 - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_191><b_10><c_232>` Watch Dogs 2 - PlayStation 4 ✗
- **beam top5**: `<a_191><b_10><c_232>`PS4, `<a_201><b_31><c_107>`PS4, `<a_123><b_58><c_78>`PS4, `<a_191><b_204><c_225>`PS4, `<a_201><b_213><c_242>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=10/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Resistance: Burning Sk…, PlayStation All-Stars …, LittleBigPlanet - Play…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item.

### #53 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_80×8/10)
- **History** (3 items; platforms DS×1,PS3×1,?×1): Castlevania Lords of Shado… | Far Cry 3 - Playstation 3 | Bloody Roar 4
- **GT**: `<a_200><b_24><c_219>` Devil May Cry PS3 _(platform PS3)_ ｜ **native**: `<a_80><b_202><c_95>` Far Cry 3 - Playstation 3 ✗
- **beam top5**: `<a_80><b_202><c_49>`?, `<a_80><b_69><c_85>`PS4, `<a_80><b_48><c_186>`?, `<a_80><b_140><c_71>`PS3, `<a_80><b_202><c_95>`PS3
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_80 family 8/10); unique(a,b)=8/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Castlevania Lords of S…, Far Cry 3 - Playstatio…, Bloody Roar 4; novel candidates=0 (**pure history restatement**); genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=SUBCLASS-continuation (score3). we recommended something **more history-consistent** than the user's actual pick (rec3>target1) → **model too conservative / user more exploratory**. Note: target shares word(s) ['cry'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #54 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_250×7/10)
- **History** (2 items; platforms WiiU×2): Super Mario Maker - Ninten… | Yoshi's Woolly World -  Wi…
- **GT**: `<a_211><b_88><c_34>` Pokemon Y _(platform ?)_ ｜ **native**: `<a_250><b_116><c_22>` Yoshi's Woolly World Bundle  -… ✗
- **beam top5**: `<a_250><b_112><c_111>`Wii, `<a_250><b_116><c_22>`Wii, `<a_162><b_251><c_136>`Wii, `<a_250><b_172><c_5>`?, `<a_162><b_116><c_253>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_250 family 7/10); unique(a,b)=10/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: Super Mario Maker - Ni…, Yoshi's Woolly World -…; novel candidates=0 (**pure history restatement**); genre: action.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #55 — Category-miss·even top-class (a) wrong
- **History** (3 items; platforms WiiU×2,?×1): Super Mario Maker - Ninten… | Yoshi's Woolly World -  Wi… | Pokemon Y
- **GT**: `<a_111><b_130><c_0>` Just Dance 2017 - Wii U _(platform WiiU)_ ｜ **native**: `<a_211><b_133><c_30>` Pokemon Alpha Sapphire - Ninte… ✗
- **beam top5**: `<a_211><b_133><c_123>`3DS, `<a_211><b_105><c_223>`3DS, `<a_211><b_105><c_215>`?, `<a_211><b_133><c_30>`3DS, `<a_211><b_159><c_123>`3DS
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=WiiU vs rec=3DS); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=7/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Super Mario Maker - Ni…, Yoshi's Woolly World -…, Pokemon Y; novel candidates=0 (**pure history restatement**); templated opening; genre: action,adventure,platformer.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #56 — Category-OK·item wrong
- **History** (4 items; platforms WiiU×3,?×1): Super Mario Maker - Ninten… | Yoshi's Woolly World -  Wi… | Pokemon Y | Just Dance 2017 - Wii U
- **GT**: `<a_39><b_114><c_215>` Call of Duty: Ghosts - Nintendo Wii U _(platform WiiU)_ ｜ **native**: `<a_211><b_133><c_30>` Pokemon Alpha Sapphire - Ninte… ✗
- **beam top5**: `<a_250><b_238><c_255>`Wii, `<a_211><b_159><c_123>`3DS, `<a_111><b_238><c_188>`PS4, `<a_211><b_149><c_18>`3DS, `<a_211><b_105><c_215>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(WiiU); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=9/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Super Mario Maker - Ni…, Yoshi's Woolly World -…, Pokemon Y; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,platformer.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #57 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_45×8/10)
- **History** (4 items; platforms XboxOne×4): Terraria - Xbox One | Xbox One Special Edition D… | Forza Horizon 3 - Xbox One | Farming Simulator 17 - Xbo…
- **GT**: `<a_61><b_181><c_62>` Xbox 360 Wireless Controller - Gold Chrome _(platform Xbox360)_ ｜ **native**: `<a_45><b_201><c_12>` Rocket League: Collector's Edi… ✗
- **beam top5**: `<a_45><b_168><c_1>`Xbo, `<a_45><b_201><c_12>`Xbo, `<a_205><b_10><c_3>`Xbo, `<a_45><b_207><c_3>`Xbo, `<a_45><b_168><c_109>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=Xbox360 vs rec=XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_45 family 8/10); unique(a,b)=8/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Terraria - Xbox One, Forza Horizon 3 - Xbox…, Farming Simulator 17 -…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,adventure,strategy.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item. Note: target shares word(s) ['controller', 'wireless'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #58 — Category-OK·item wrong
- **History** (10 items; platforms PS4×10): Until Dawn - PlayStation 4 | Until Dawn - PlayStation 4 | Abzu - PlayStation 4 | Tales from the Borderlands… | The Wolf Among Us - PlaySt… | Battlefield 1 - PlayStatio…
- **GT**: `<a_205><b_208><c_148>` Gran Turismo Sport - Limited Edition - PlaySta… _(platform PS4)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_201><b_18><c_56>`PS4, `<a_123><b_58><c_78>`PS4, `<a_123><b_58><c_16>`Xbo, `<a_123><b_100><c_33>`PS4, `<a_201><b_213><c_242>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 6/9 history items (coverage 67%), anchored on: Life is Strange - Play…, Tales from the Borderl…, Until Dawn - PlayStati…; novel candidates=1; templated opening; genre: action,horror,immersive.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #59 — Category-miss·even top-class (a) wrong
- **History** (4 items; platforms 3DS×4): Story of Seasons - Nintend… | Nintendo New 3DS Xl - Red … | Monster Hunter 4 Ultimate … | dreamGEAR Comfort GRIP Pro…
- **GT**: `<a_141><b_189><c_201>` PlanetSide 2 [Download] _(platform ?)_ ｜ **native**: `<a_211><b_31><c_154>` Pokemon Super Mystery Dungeon … ✗
- **beam top5**: `<a_119><b_119><c_158>`3DS, `<a_119><b_35><c_129>`3DS, `<a_119><b_168><c_182>`3DS, `<a_211><b_31><c_154>`3DS, `<a_162><b_251><c_136>`Wii
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=10/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 3/4 history items (coverage 75%), anchored on: Story of Seasons - Nin…, Monster Hunter 4 Ultim…, dreamGEAR Comfort GRIP…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,adventure,rpg.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #60 — Category-miss·even top-class (a) wrong
- **History** (6 items; platforms ?×6): The Legend of Zelda: Ocari… | Disney's Aladdin | Street Fighter II' Special… | Streets of Rage 2 | Wave Race 64 | Nintendo 64 Controller - O…
- **GT**: `<a_239><b_199><c_42>` The Adventures of Bayou Billy _(platform ?)_ ｜ **native**: `<a_113><b_232><c_97>` Redesigned REPLACEMENT Joystic… ✗
- **beam top5**: `<a_113><b_232><c_97>`?, `<a_113><b_44><c_172>`Gam, `<a_113><b_232><c_152>`?, `<a_219><b_166><c_158>`?, `<a_113><b_127><c_139>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (2 a top-classes); unique(a,b)=6/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 5/6 history items (coverage 83%), anchored on: The Legend of Zelda: O…, Disney's Aladdin, Street Fighter II' Spe…; novel candidates=0 (**pure history restatement**); genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #61 — Category-OK·item wrong
- **History** (7 items; platforms ?×7): Disney's Aladdin | Street Fighter II' Special… | Streets of Rage 2 | Wave Race 64 | Nintendo 64 Controller - O… | The Adventures of Bayou Bi…
- **GT**: `<a_233><b_229><c_215>` Double Dragon II: The Revenge _(platform ?)_ ｜ **native**: `<a_113><b_232><c_97>` Redesigned REPLACEMENT Joystic… ✗
- **beam top5**: `<a_233><b_124><c_83>`?, `<a_113><b_232><c_97>`?, `<a_113><b_127><c_139>`?, `<a_250><b_199><c_170>`?, `<a_233><b_7><c_241>`?
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; in beam: share-a=3/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 5/7 history items (coverage 71%), anchored on: The Legend of Zelda: O…, The Adventures of Bayo…, Wave Race 64; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item.

### #62 — Category-OK·item wrong
- **History** (5 items; platforms PS4×3,?×1,PS3×1): Fallout 4 - PlayStation 4 | Divinity: Original Sin - E… | Mega Man 2 - Nintendo NES | Mortal Kombat: Komplete Ed… | Mass Effect Andromeda - Pr…
- **GT**: `<a_141><b_73><c_216>` Star Wars: Battlefront - Standard Edition - Pl… _(platform PS4)_ ｜ **native**: `<a_201><b_31><c_107>` Uncharted 4: A Thief's End - P… ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_201><b_213><c_242>`PS4, `<a_201><b_2><c_102>`PS4, `<a_200><b_169><c_179>`PS4, `<a_131><b_209><c_151>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=10/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/5 history items (coverage 80%), anchored on: Fallout 4 - PlayStatio…, Divinity: Original Sin…, Mass Effect Andromeda …; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #63 — Category-miss·even top-class (a) wrong
- **History** (4 items; platforms ?×2,PS×1,Wii×1): Grand Theft Auto III | Grand Theft Auto Vice City | Red Dead Revolver - PlaySt… | Wii Stand (RVL-017)
- **GT**: `<a_140><b_58><c_71>` Guitar Hero Live - PlayStation 3 _(platform PS3)_ ｜ **native**: `<a_61><b_181><c_195>` Xbox 360 Wireless Controller -… ✗
- **beam top5**: `<a_240><b_33><c_93>`?, `<a_240><b_221><c_2>`PS3, `<a_240><b_40><c_2>`PS, `<a_61><b_181><c_195>`Xbo, `<a_61><b_181><c_175>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=9/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 1/4 history items (coverage 25%), anchored on: Wii Stand (RVL-017); novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #64 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_61×10/10)
- **History** (4 items; platforms WiiU×2,PC×1,Xbox360×1): Super Mario Maker - Ninten… | StarCraft II: Heart of the… | LEGO Dimensions Starter Pa… | Microsoft Xbox 360 Wireles…
- **GT**: `<a_45><b_201><c_12>` Rocket League: Collector's Edition - Xbox One _(platform XboxOne)_ ｜ **native**: `<a_61><b_181><c_195>` Xbox 360 Wireless Controller -… ✗
- **beam top5**: `<a_61><b_131><c_197>`Xbo, `<a_61><b_181><c_195>`Xbo, `<a_61><b_150><c_0>`Xbo, `<a_61><b_53><c_0>`Xbo, `<a_61><b_150><c_5>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=XboxOne vs rec=Xbox); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_61 family 10/10); unique(a,b)=5/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Super Mario Maker - Ni…, LEGO Dimensions Starte…, StarCraft II: Heart of…; novel candidates=0 (**pure history restatement**); genre: action,immersive,accessor.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #65 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_61×10/10)
- **History** (5 items; platforms WiiU×2,PC×1,Xbox360×1): Super Mario Maker - Ninten… | StarCraft II: Heart of the… | LEGO Dimensions Starter Pa… | Microsoft Xbox 360 Wireles… | Rocket League: Collector's…
- **GT**: `<a_205><b_175><c_169>` Tony Hawk's Pro Skater 5 - Standard Edition - … _(platform XboxOne)_ ｜ **native**: `<a_61><b_181><c_195>` Xbox 360 Wireless Controller -… ✗
- **beam top5**: `<a_61><b_131><c_197>`Xbo, `<a_61><b_111><c_197>`Xbo, `<a_61><b_181><c_195>`Xbo, `<a_61><b_53><c_5>`Xbo, `<a_61><b_137><c_255>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=XboxOne vs rec=Xbox); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_61 family 10/10); unique(a,b)=7/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 4/5 history items (coverage 80%), anchored on: Super Mario Maker - Ni…, LEGO Dimensions Starte…, Rocket League: Collect…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,sports,accessor.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #66 — Category-OK·item wrong
- **History** (1 items; platforms ?×1): Logitech Gamepad F310
- **GT**: `<a_202><b_30><c_0>` Masione LED USB Gaming Wired Keyboard with 7 A… _(platform ?)_ ｜ **native**: `<a_61><b_0><c_234>` Logitech Gamepad F310 ✗
- **beam top5**: `<a_202><b_82><c_172>`?, `<a_202><b_16><c_110>`?, `<a_202><b_34><c_39>`?, `<a_61><b_167><c_197>`Xbo, `<a_214><b_24><c_0>`?
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; in beam: share-a=6/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=8/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 0/1 history items (coverage 0%); novel candidates=0 (**pure history restatement**); genre: peripheral,accessor,controller.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=DRIFT (platform/word-linked) (score1). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #67 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_202×8/10)
- **History** (2 items; platforms ?×2): Logitech Gamepad F310 | Masione LED USB Gaming Wir…
- **GT**: `<a_250><b_106><c_156>` Nintendo Selects: Super Mario Galaxy 2 _(platform ?)_ ｜ **native**: `<a_202><b_16><c_110>` Razer DeathAdder Expert - Opti… ✗
- **beam top5**: `<a_202><b_82><c_172>`?, `<a_202><b_58><c_107>`?, `<a_202><b_200><c_67>`?, `<a_202><b_16><c_110>`?, `<a_202><b_34><c_39>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_202 family 8/10); unique(a,b)=9/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 0/2 history items (coverage 0%); novel candidates=0 (**pure history restatement**); genre: action,peripheral,accessor.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #68 — Category-OK·item wrong · BEAM-COLLAPSE (<a_250×10/10)
- **History** (3 items; platforms ?×3): Logitech Gamepad F310 | Masione LED USB Gaming Wir… | Nintendo Selects: Super Ma…
- **GT**: `<a_250><b_92><c_44>` Nintendo Selects: Donkey Kong Country: Tropica… _(platform ?)_ ｜ **native**: `<a_250><b_55><c_95>` Mario Kart 7 ✗
- **beam top5**: `<a_250><b_14><c_196>`?, `<a_250><b_219><c_103>`?, `<a_250><b_165><c_76>`?, `<a_250><b_55><c_137>`?, `<a_250><b_55><c_95>`?
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; in beam: share-a=10/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_250 family 10/10); unique(a,b)=7/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Logitech Gamepad F310, Masione LED USB Gaming…, Nintendo Selects: Supe…; novel candidates=0 (**pure history restatement**); genre: action,nostalg,peripheral.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item. Note: target shares word(s) ['selects'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #69 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_250×10/10)
- **History** (4 items; platforms ?×4): Logitech Gamepad F310 | Masione LED USB Gaming Wir… | Nintendo Selects: Super Ma… | Nintendo Selects: Donkey K…
- **GT**: `<a_1><b_121><c_156>` Monster Hunter 3 Ultimate - Nintendo Wii U _(platform WiiU)_ ｜ **native**: `<a_250><b_238><c_106>` Mario Party DS ✗
- **beam top5**: `<a_250><b_14><c_196>`?, `<a_250><b_14><c_103>`DS, `<a_250><b_207><c_203>`Wii, `<a_250><b_238><c_106>`DS, `<a_250><b_55><c_95>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_250 family 10/10); unique(a,b)=7/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 2/4 history items (coverage 50%), anchored on: Logitech Gamepad F310, Masione LED USB Gaming…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,platformer,nostalg.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #70 — Category-miss·even top-class (a) wrong
- **History** (5 items; platforms ?×4,WiiU×1): Logitech Gamepad F310 | Masione LED USB Gaming Wir… | Nintendo Selects: Super Ma… | Nintendo Selects: Donkey K… | Monster Hunter 3 Ultimate …
- **GT**: `<a_84><b_235><c_1>` Nintendo Wii U Deluxe Set: Super Mario Bros U … _(platform WiiU)_ ｜ **native**: `<a_250><b_238><c_255>` Mario Party 10 + Mario amiibo … ✗
- **beam top5**: `<a_113><b_35><c_8>`Gam, `<a_113><b_35><c_14>`Gam, `<a_250><b_55><c_95>`?, `<a_113><b_112><c_109>`Wii, `<a_113><b_240><c_225>`Wii
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=WiiU vs rec=GameCube); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=9/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 5/5 history items (coverage 100%), anchored on: Logitech Gamepad F310, Masione LED USB Gaming…, Nintendo Selects: Supe…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,platformer.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item. Note: target shares word(s) ['mario', 'super'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #71 — Category-miss·even top-class (a) wrong
- **History** (10 items; platforms PS4×5,PS×2,DS×1): Injustice 2 - PS4 [Digital… | Tekken 7 -  PS4 Digital Co… | Star Trek: Bridge Crew - P… | The Legend of Heroes: Trai… | Titanfall 2 - Vanguard Col… | Gran Turismo Sport - PlayS…
- **GT**: `<a_201><b_151><c_255>` Playstation Plus: 3 Month Membership [Digital … _(platform PS-generic)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_123><b_58><c_16>`Xbo, `<a_24><b_72><c_142>`PS4, `<a_123><b_58><c_78>`PS4, `<a_39><b_77><c_105>`Xbo, `<a_24><b_185><c_47>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS-generic vs rec=XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (7 distinct a top-classes); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 5/10 history items (coverage 50%), anchored on: The Evil Within - PC, Persona 5 - SteelBook …, Titanfall 2 - Vanguard…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item. Note: target shares word(s) ['code', 'digital'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #72 — Category-miss·even top-class (a) wrong
- **History** (10 items; platforms PS4×5,PS×3,PC×1): Tekken 7 -  PS4 Digital Co… | Star Trek: Bridge Crew - P… | The Legend of Heroes: Trai… | Titanfall 2 - Vanguard Col… | Gran Turismo Sport - PlayS… | Playstation Plus: 3 Month …
- **GT**: `<a_249><b_31><c_126>` Sony PlayStation Vita WiFi _(platform PSVita)_ ｜ **native**: `<a_24><b_72><c_142>` Horizon Zero Dawn - PlayStatio… ✗
- **beam top5**: `<a_123><b_58><c_78>`PS4, `<a_24><b_72><c_142>`PS4, `<a_24><b_86><c_14>`PS4, `<a_201><b_31><c_107>`PS4, `<a_30><b_92><c_0>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PSVita vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (7 distinct a top-classes); unique(a,b)=9/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 6/10 history items (coverage 60%), anchored on: The Evil Within - PC, Persona 5 - SteelBook …, The Legend of Heroes: …; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=DRIFT (platform/word-linked) (score1). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #73 — Category-miss·even top-class (a) wrong
- **History** (10 items; platforms PS4×5,PS×3,PS3×1): Star Trek: Bridge Crew - P… | The Legend of Heroes: Trai… | Titanfall 2 - Vanguard Col… | Gran Turismo Sport - PlayS… | Playstation Plus: 3 Month … | Sony PlayStation Vita WiFi
- **GT**: `<a_232><b_79><c_116>` Fire Emblem Fates: Conquest DLC - 3DS [Digital… _(platform 3DS)_ ｜ **native**: `<a_30><b_92><c_0>` Persona 5 - Standard Edition -… ✗
- **beam top5**: `<a_123><b_58><c_78>`PS4, `<a_30><b_92><c_146>`PS4, `<a_1><b_173><c_4>`PS4, `<a_30><b_92><c_0>`PS4, `<a_1><b_43><c_207>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=3DS vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (7 distinct a top-classes); unique(a,b)=9/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 4/10 history items (coverage 40%), anchored on: Persona 5 - SteelBook …, The Legend of Heroes: …, Gran Turismo Sport - P…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item. Note: target shares word(s) ['code', 'digital'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #74 — Category-OK·item wrong · BEAM-COLLAPSE (<a_123×9/10)
- **History** (2 items; platforms PS4×2): Fallout 4 Season Pass - PS… | Dead Island Definitive Col…
- **GT**: `<a_201><b_151><c_255>` Playstation Plus: 3 Month Membership [Digital … _(platform PS-generic)_ ｜ **native**: `<a_123><b_142><c_36>` 7 Days to Die - PlayStation 4 ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_123><b_171><c_44>`Xbo, `<a_123><b_142><c_36>`PS4, `<a_123><b_188><c_192>`PS4, `<a_123><b_76><c_232>`PS4
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform mismatch(GT=PS-generic vs rec=PS4); in beam: share-a=1/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_123 family 9/10); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: Fallout 4 Season Pass …, Dead Island Definitive…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item. Note: target shares word(s) ['code', 'digital'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #75 — Category-OK·item wrong · BEAM-COLLAPSE (<a_123×9/10)
- **History** (3 items; platforms PS4×2,PS×1): Fallout 4 Season Pass - PS… | Dead Island Definitive Col… | Playstation Plus: 3 Month …
- **GT**: `<a_194><b_36><c_254>` Final Fantasy XV - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_123><b_142><c_36>` 7 Days to Die - PlayStation 4 ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_123><b_188><c_192>`PS4, `<a_123><b_78><c_71>`PS4, `<a_123><b_142><c_36>`PS4, `<a_123><b_44><c_0>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_123 family 9/10); unique(a,b)=10/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Fallout 4 Season Pass …, Dead Island Definitive…, Playstation Plus: 3 Mo…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #76 — Category-miss·even top-class (a) wrong
- **History** (4 items; platforms PS4×3,PS×1): Fallout 4 Season Pass - PS… | Dead Island Definitive Col… | Playstation Plus: 3 Month … | Final Fantasy XV - PlaySta…
- **GT**: `<a_113><b_104><c_28>` Nintendo 3DS Compatible with 3DS / 3DS XL / 2D… _(platform 3DS)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_201><b_18><c_56>`PS4, `<a_123><b_129><c_247>`PS4, `<a_123><b_58><c_78>`PS4, `<a_123><b_44><c_0>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=3DS vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=9/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Fallout 4 Season Pass …, Final Fantasy XV - Pla…, Dead Island Definitive…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #77 — Category-OK·item wrong
- **History** (5 items; platforms PS4×3,PS×1,3DS×1): Fallout 4 Season Pass - PS… | Dead Island Definitive Col… | Playstation Plus: 3 Month … | Final Fantasy XV - PlaySta… | Nintendo 3DS Compatible wi…
- **GT**: `<a_1><b_74><c_130>` Monster Hunter Generations - Nintendo 3DS Stan… _(platform 3DS)_ ｜ **native**: `<a_113><b_235><c_2>` Nintendo New 3DS XL - Black ✗
- **beam top5**: `<a_131><b_41><c_229>`PS4, `<a_113><b_235><c_2>`3DS, `<a_113><b_235><c_28>`3DS, `<a_119><b_168><c_182>`3DS, `<a_201><b_31><c_107>`PS4
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform mismatch(GT=3DS vs rec=PS4); in beam: share-a=1/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (7 distinct a top-classes); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/5 history items (coverage 80%), anchored on: Fallout 4 Season Pass …, Final Fantasy XV - Pla…, Dead Island Definitive…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #78 — Category-miss·even top-class (a) wrong
- **History** (1 items; platforms WiiU×1): Fosmon Component HD AV Cab…
- **GT**: `<a_92><b_68><c_129>` Doom - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_21><b_132><c_226>` Fosmon Component HD AV Cable t… ✗
- **beam top5**: `<a_21><b_242><c_102>`Gam, `<a_113><b_112><c_144>`Wii, `<a_21><b_125><c_39>`Wii, `<a_21><b_132><c_226>`Wii, `<a_113><b_112><c_109>`Wii
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS4 vs rec=GameCube); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=8/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 0/1 history items (coverage 0%); novel candidates=0 (**pure history restatement**); genre: immersive,peripheral,accessor.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #79 — Category-OK·item wrong
- **History** (2 items; platforms WiiU×1,PS4×1): Fosmon Component HD AV Cab… | Doom - PlayStation 4
- **GT**: `<a_71><b_86><c_236>` UNCHARTED: The Nathan Drake Collection - PlayS… _(platform PS4)_ ｜ **native**: `<a_131><b_224><c_68>` Overwatch - Origins Edition - … ✗
- **beam top5**: `<a_131><b_209><c_151>`PS4, `<a_7><b_248><c_16>`Xbo, `<a_131><b_210><c_0>`PS4, `<a_201><b_31><c_107>`PS4, `<a_7><b_36><c_0>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=9/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: Fosmon Component HD AV…, Doom - PlayStation 4; novel candidates=0 (**pure history restatement**); genre: action,immersive,narrative.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item.

### #80 — Category-miss·even top-class (a) wrong
- **History** (3 items; platforms PS4×2,WiiU×1): Fosmon Component HD AV Cab… | Doom - PlayStation 4 | UNCHARTED: The Nathan Drak…
- **GT**: `<a_89><b_86><c_50>` World of Warcraft 60 Day Game Time [Digital Co… _(platform ?)_ ｜ **native**: `<a_201><b_31><c_107>` Uncharted 4: A Thief's End - P… ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_131><b_210><c_0>`PS4, `<a_131><b_209><c_151>`PS4, `<a_201><b_2><c_102>`PS4, `<a_201><b_213><c_242>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=9/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Doom - PlayStation 4, UNCHARTED: The Nathan …, Fosmon Component HD AV…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,adventure,immersive.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=DRIFT (platform/word-linked) (score1). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #81 — Category-OK·item wrong
- **History** (4 items; platforms PS4×2,WiiU×1,?×1): Fosmon Component HD AV Cab… | Doom - PlayStation 4 | UNCHARTED: The Nathan Drak… | World of Warcraft 60 Day G…
- **GT**: `<a_89><b_141><c_30>` World of Warcraft (Battle Chest Box) - PC/Mac … _(platform PC)_ ｜ **native**: `<a_89><b_86><c_50>` World of Warcraft 60 Day Game … ✗
- **beam top5**: `<a_131><b_210><c_0>`PS4, `<a_89><b_86><c_158>`PC, `<a_141><b_73><c_216>`PS4, `<a_89><b_86><c_50>`?, `<a_131><b_209><c_151>`PS4
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform mismatch(GT=PC vs rec=PS4); in beam: share-a=5/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=9/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Doom - PlayStation 4, UNCHARTED: The Nathan …, Fosmon Component HD AV…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=DRIFT (platform/word-linked) (score1). user's pick is **more history-consistent** than our top-1 (target2>rec1) → we **drifted off** a catchable continuation. Note: target shares word(s) ['code', 'digital', 'online', 'warcraft', 'world'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #82 — Category-miss·even top-class (a) wrong
- **History** (9 items; platforms XboxOne×4,PS4×3,?×2): Resident Evil Origins Coll… | Bloodborne | Quantum Break - Xbox One | Tomsenn Kinect Sensor TV M… | NVIDIA SHIELD - 4K HDR Str… | The King of Fighters XIV: …
- **GT**: `<a_7><b_36><c_217>` Xbox One X 1TB Limited Edition Console - Proje… _(platform XboxOne)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_123><b_58><c_78>`PS4, `<a_201><b_31><c_107>`PS4, `<a_24><b_129><c_173>`PS4, `<a_123><b_171><c_44>`Xbo, `<a_123><b_33><c_93>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=XboxOne vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 6/9 history items (coverage 67%), anchored on: Until Dawn - PlayStati…, Resident Evil Origins …, Nyko Power Pack for Pl…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,horror,multiplayer.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item.

### #83 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_202×8/10)
- **History** (4 items; platforms ?×2,Switch×1,PS4×1): Razer BlackWidow Chroma: C… | Razer Naga Epic Chroma MMO… | Nintendo Pokemon Go Plus | KontrolFreek FPS Freek Vor…
- **GT**: `<a_231><b_46><c_171>` KontrolFreek CQCX Thumb Grips for PlayStation … _(platform PS4)_ ｜ **native**: `<a_202><b_11><c_104>` Razer Limited Edition Naga MMO… ✗
- **beam top5**: `<a_202><b_58><c_107>`?, `<a_202><b_11><c_104>`?, `<a_202><b_58><c_57>`?, `<a_202><b_120><c_89>`?, `<a_202><b_251><c_120>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_202 family 8/10); unique(a,b)=6/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 2/4 history items (coverage 50%), anchored on: Nintendo Pokemon Go Pl…, KontrolFreek FPS Freek…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,immersive,narrative.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item. Note: target shares word(s) ['controller', 'kontrolfreek'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #84 — Category-OK·item wrong · BEAM-COLLAPSE (<a_217×10/10)
- **History** (10 items; platforms XboxOne×6,?×4): Skylanders SuperChargers: … | Skylanders SuperChargers: … | Skylanders SuperChargers: … | Rare Replay - Xbox One | XCom 2 - Xbox One | Skylanders Swap Force Star…
- **GT**: `<a_217><b_60><c_155>` Skylanders SuperChargers Starter Pack - PlaySt… _(platform PS4)_ ｜ **native**: `<a_217><b_71><c_128>` Skylanders SuperChargers: Vehi… ✗
- **beam top5**: `<a_217><b_71><c_11>`?, `<a_217><b_71><c_2>`?, `<a_217><b_71><c_128>`?, `<a_217><b_71><c_4>`?, `<a_217><b_71><c_226>`?
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; in beam: share-a=10/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_217 family 10/10); unique(a,b)=1/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 4/10 history items (coverage 40%), anchored on: Skylanders SuperCharge…, Skylanders SuperCharge…, Skylanders Swap Force …; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=SUBCLASS-continuation (score3). we recommended something **more history-consistent** than the user's actual pick (rec3>target2) → **model too conservative / user more exploratory**. Note: target shares word(s) ['skylanders', 'starter', 'superchargers'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #85 — Near-miss·same (a,b) subcluster, only c differs · BEAM-COLLAPSE (<a_217×10/10)
- **History** (10 items; platforms XboxOne×6,?×3,PS4×1): Skylanders SuperChargers: … | Skylanders SuperChargers: … | Rare Replay - Xbox One | XCom 2 - Xbox One | Skylanders Swap Force Star… | Skylanders SuperChargers S…
- **GT**: `<a_217><b_71><c_18>` Skylanders SuperChargers: Drivers Splat Charac… _(platform ?)_ ｜ **native**: `<a_217><b_71><c_22>` Skylanders SuperChargers: Driv… ✗
- **beam top5**: `<a_217><b_71><c_11>`?, `<a_217><b_71><c_2>`?, `<a_217><b_71><c_226>`?, `<a_217><b_71><c_85>`?, `<a_217><b_71><c_128>`?
- **Rec↔GT gap**: beam's closest item shares (a,b) subcluster with GT, only c differs (same series/SKU), still missed; in beam: share-a=10/10, share-(a,b)=10/10.
- **Beam diversity**: **Low** (collapsed to <a_217 family 10/10); unique(a,b)=1/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 6/10 history items (coverage 60%), anchored on: Skylanders SuperCharge…, Skylanders SuperCharge…, Skylanders Swap Force …; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=SUBCLASS-continuation (score3); our pred[0]=SUBCLASS-continuation (score3). same relatedness tier (score3) but wrong specific item. Note: target shares word(s) ['character', 'drivers', 'skylanders', 'superchargers'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #86 — Category-miss·even top-class (a) wrong
- **History** (4 items; platforms PS4×4): WWE 2K16 - PlayStation 4 | Grand Theft Auto V - PlayS… | WWE 2K17 - PlayStation 4 | NHL 17 - PlayStation 4
- **GT**: `<a_86><b_12><c_93>` South Park: The Fractured but Whole - PlayStat… _(platform PS4)_ ｜ **native**: `<a_45><b_28><c_168>` FIFA 17 - PlayStation 4 ✗
- **beam top5**: `<a_231><b_223><c_1>`Xbo, `<a_231><b_237><c_82>`PS4, `<a_45><b_28><c_168>`PS4, `<a_201><b_31><c_107>`PS4, `<a_231><b_237><c_4>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS4 vs rec=Xbox360); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=6/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: WWE 2K16 - PlayStation…, Grand Theft Auto V - P…, WWE 2K17 - PlayStation…; novel candidates=0 (**pure history restatement**); genre: action,sports,simulation.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #87 — Category-miss·even top-class (a) wrong
- **History** (1 items; platforms PS3×1): PS3 500 GB Grand Theft Aut…
- **GT**: `<a_235><b_189><c_196>` Rayman Origins _(platform ?)_ ｜ **native**: `<a_140><b_133><c_15>` Sony Playstation 3 160GB Syste… ✗
- **beam top5**: `<a_140><b_213><c_236>`PS4, `<a_140><b_133><c_15>`PS3, `<a_61><b_47><c_8>`PS3, `<a_140><b_133><c_1>`PS3, `<a_140><b_133><c_57>`PS3
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=7/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 1/1 history items (coverage 100%), anchored on: PS3 500 GB Grand Theft…; novel candidates=0 (**pure history restatement**); genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=EXPLORATION (unrelated) (score0). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #88 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_249×7/10)
- **History** (4 items; platforms ?×2,PS×2): Nintendo 64 System - Video… | GoldenEye 007 | Sony Playstation 1 COMPLET… | Gamily Playstation 1 Memor…
- **GT**: `<a_231><b_153><c_147>` Super Mario Bros. 3 _(platform ?)_ ｜ **native**: `<a_249><b_52><c_108>` Sony Playstation Memory Card ✗
- **beam top5**: `<a_249><b_221><c_234>`PS, `<a_61><b_47><c_60>`PS, `<a_249><b_170><c_61>`PS, `<a_249><b_138><c_102>`PS, `<a_249><b_52><c_108>`PS
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_249 family 7/10); unique(a,b)=7/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Nintendo 64 System - V…, Sony Playstation 1 COM…, Gamily Playstation 1 M…; novel candidates=0 (**pure history restatement**); genre: action,immersive,nostalg.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #89 — Category-OK·item wrong
- **History** (5 items; platforms ?×3,PS×2): Nintendo 64 System - Video… | GoldenEye 007 | Sony Playstation 1 COMPLET… | Gamily Playstation 1 Memor… | Super Mario Bros. 3
- **GT**: `<a_21><b_38><c_115>` Retro-Bit SNES 6-Feet Extension Cable _(platform ?)_ ｜ **native**: `<a_249><b_52><c_108>` Sony Playstation Memory Card ✗
- **beam top5**: `<a_61><b_47><c_60>`PS, `<a_233><b_106><c_144>`?, `<a_249><b_221><c_234>`PS, `<a_233><b_44><c_175>`?, `<a_249><b_170><c_61>`PS
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; in beam: share-a=1/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (6 distinct a top-classes); unique(a,b)=10/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 4/5 history items (coverage 80%), anchored on: Sony Playstation 1 COM…, Gamily Playstation 1 M…, GoldenEye 007; novel candidates=0 (**pure history restatement**); templated opening; genre: action,shooter,immersive.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=EXPLORATION (unrelated) (score0). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #90 — Category-miss·even top-class (a) wrong
- **History** (6 items; platforms ?×4,PS×2): Nintendo 64 System - Video… | GoldenEye 007 | Sony Playstation 1 COMPLET… | Gamily Playstation 1 Memor… | Super Mario Bros. 3 | Retro-Bit SNES 6-Feet Exte…
- **GT**: `<a_193><b_157><c_142>` Sonic the Hedgehog _(platform ?)_ ｜ **native**: `<a_21><b_44><c_75>` PS2 Controller Extension Cable… ✗
- **beam top5**: `<a_61><b_47><c_60>`PS, `<a_249><b_80><c_0>`PS2, `<a_249><b_221><c_234>`PS, `<a_249><b_170><c_61>`PS, `<a_21><b_129><c_194>`PS
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=10/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 3/6 history items (coverage 50%), anchored on: GoldenEye 007, Super Mario Bros. 3, Retro-Bit SNES 6-Feet …; novel candidates=0 (**pure history restatement**); templated opening; genre: action,shooter,nostalg.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=EXPLORATION (unrelated) (score0). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #91 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_233×10/10)
- **History** (7 items; platforms ?×5,PS×2): GoldenEye 007 | Sony Playstation 1 COMPLET… | Gamily Playstation 1 Memor… | Super Mario Bros. 3 | Retro-Bit SNES 6-Feet Exte… | Sonic the Hedgehog
- **GT**: `<a_250><b_41><c_199>` Super Mario Bros. _(platform ?)_ ｜ **native**: `<a_233><b_44><c_175>` Sega Dreamcast Controller (Ori… ✗
- **beam top5**: `<a_233><b_106><c_144>`?, `<a_233><b_206><c_153>`?, `<a_233><b_21><c_136>`?, `<a_233><b_45><c_52>`?, `<a_233><b_44><c_175>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_233 family 10/10); unique(a,b)=10/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 4/7 history items (coverage 57%), anchored on: Gamily Playstation 1 M…, Retro-Bit SNES 6-Feet …, GoldenEye 007; novel candidates=0 (**pure history restatement**); genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=EXPLORATION (unrelated) (score0). user's pick is **more history-consistent** than our top-1 (target1>rec0) → we **drifted off** a catchable continuation. Note: target shares word(s) ['bros', 'mario', 'super'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #92 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_233×7/10)
- **History** (8 items; platforms ?×6,PS×2): Sony Playstation 1 COMPLET… | Gamily Playstation 1 Memor… | Super Mario Bros. 3 | Retro-Bit SNES 6-Feet Exte… | Sonic the Hedgehog | Super Mario Bros.
- **GT**: `<a_208><b_166><c_139>` Mike Tyson's Punch-Out!! - Nintendo NES _(platform ?)_ ｜ **native**: `<a_233><b_44><c_175>` Sega Dreamcast Controller (Ori… ✗
- **beam top5**: `<a_233><b_201><c_25>`PS4, `<a_233><b_106><c_144>`?, `<a_233><b_206><c_153>`?, `<a_233><b_44><c_175>`?, `<a_233><b_45><c_52>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_233 family 7/10); unique(a,b)=10/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 0/8 history items (coverage 0%); novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=EXPLORATION (unrelated) (score0). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #93 — Category-miss·even top-class (a) wrong
- **History** (9 items; platforms ?×7,PS×2): Gamily Playstation 1 Memor… | Super Mario Bros. 3 | Retro-Bit SNES 6-Feet Exte… | Sonic the Hedgehog | Super Mario Bros. | Mike Tyson's Punch-Out!! -…
- **GT**: `<a_61><b_21><c_48>` Sony Playstation Controller - Gray (Non-Dualsh… _(platform PS-generic)_ ｜ **native**: `<a_233><b_7><c_241>` Mortal Kombat II ✗
- **beam top5**: `<a_233><b_7><c_241>`?, `<a_233><b_45><c_52>`?, `<a_233><b_106><c_144>`?, `<a_208><b_174><c_227>`?, `<a_233><b_44><c_175>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (2 a top-classes); unique(a,b)=10/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/9 history items (coverage 44%), anchored on: GoldenEye 007, Super Mario Bros. 3, Retro-Bit SNES 6-Feet …; novel candidates=2; templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=EXPLORATION (unrelated) (score0). user's pick is **more history-consistent** than our top-1 (target1>rec0) → we **drifted off** a catchable continuation. Note: target shares word(s) ['sony'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #94 — Category-OK·item wrong
- **History** (6 items; platforms PS4×3,?×2,XboxOne×1): Red Dead Redemption: Game … | Mafia II | Mafia II | Just Cause 3 - PlayStation… | Fallout 4 - PlayStation 4 | Fallout 4 Season Pass - PS…
- **GT**: `<a_13><b_218><c_173>` Agents of Mayhem - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_123><b_72><c_7>` Far Cry 4 - PlayStation 4 ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_123><b_72><c_7>`PS4, `<a_118><b_233><c_76>`PS4, `<a_201><b_145><c_9>`PS4, `<a_123><b_76><c_232>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=10/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 5/5 history items (coverage 100%), anchored on: Mafia II, Just Cause 3 - PlaySta…, Fallout 4 - PlayStatio…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item.

### #95 — Category-miss·even top-class (a) wrong
- **History** (10 items; platforms PS4×4,PS×2,PS3×2): Assassin's Creed: The Amer… | Digimon Story: Cyber Sleut… | Xbox One 500 GB Console - … | Final Fantasy Type-0 HD - … | Assassin's Creed: Syndicat… | Star Ocean Till the End of…
- **GT**: `<a_249><b_134><c_122>` Sony PSP-1001K PlayStation Portable (PSP) Syst… _(platform PSP)_ ｜ **native**: `<a_194><b_33><c_4>` Dark Souls II: Scholar of the … ✗
- **beam top5**: `<a_194><b_215><c_154>`?, `<a_194><b_33><c_4>`PS4, `<a_194><b_33><c_2>`Xbo, `<a_194><b_21><c_76>`PS4, `<a_194><b_87><c_112>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=9/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 6/10 history items (coverage 60%), anchored on: Unravel - PS4 [Digital…, Final Fantasy XV - Pla…, Assassin's Creed Rogue…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,role-playing,immersive.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**. Note: target shares word(s) ['black'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #96 — Category-miss·even top-class (a) wrong
- **History** (10 items; platforms PS4×3,PS×2,PS3×2): Digimon Story: Cyber Sleut… | Xbox One 500 GB Console - … | Final Fantasy Type-0 HD - … | Assassin's Creed: Syndicat… | Star Ocean Till the End of… | Sony PSP-1001K PlayStation…
- **GT**: `<a_249><b_134><c_122>` Sony PSP-1001K PlayStation Portable (PSP) Syst… _(platform PSP)_ ｜ **native**: `<a_1><b_150><c_189>` Legend of Heroes: Trails of Co… ✗
- **beam top5**: `<a_194><b_87><c_112>`PS4, `<a_194><b_33><c_4>`PS4, `<a_118><b_150><c_122>`PS4, `<a_194><b_21><c_76>`PS4, `<a_1><b_173><c_4>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PSP vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=10/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 7/10 history items (coverage 70%), anchored on: Final Fantasy XV - Pla…, Assassin's Creed Rogue…, Assassin's Creed: The …; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=SUBCLASS-continuation (score3); our pred[0]=CLASS-continuation (score2). user's pick is **more history-consistent** than our top-1 (target3>rec2) → we **drifted off** a catchable continuation. Note: target shares word(s) ['1001k', 'black', 'portable', 'sony'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #97 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_249×9/10)
- **History** (1 items; platforms PS×1): Datel Max Playstation 2 Ac…
- **GT**: `<a_8><b_230><c_140>` Generic AC Power Adapter Charger for Nintendo … _(platform 3DS)_ ｜ **native**: `<a_249><b_170><c_61>` Buyee 128MB Memory Card for So… ✗
- **beam top5**: `<a_249><b_221><c_234>`PS, `<a_249><b_38><c_208>`PS, `<a_249><b_170><c_61>`PS, `<a_61><b_47><c_60>`PS, `<a_249><b_80><c_0>`PS2
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=3DS vs rec=PS2); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_249 family 9/10); unique(a,b)=7/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 1/1 history items (coverage 100%), anchored on: Datel Max Playstation …; novel candidates=0 (**pure history restatement**); genre: action,peripheral,accessor.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #98 — Category-miss·even top-class (a) wrong
- **History** (2 items; platforms PS×1,3DS×1): Datel Max Playstation 2 Ac… | Generic AC Power Adapter C…
- **GT**: `<a_175><b_179><c_41>` Nintendo 3DS - Flame Red _(platform 3DS)_ ｜ **native**: `<a_113><b_104><c_28>` Nintendo 3DS Compatible with 3… ✗
- **beam top5**: `<a_8><b_70><c_241>`Xbo, `<a_8><b_230><c_178>`3DS, `<a_113><b_104><c_28>`3DS, `<a_8><b_93><c_169>`Wii, `<a_249><b_170><c_61>`PS
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=3DS vs rec=XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=10/10, platforms=5, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: Datel Max Playstation …, Generic AC Power Adapt…; novel candidates=0 (**pure history restatement**); genre: action,nostalg,retro.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #99 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_249×9/10)
- **History** (3 items; platforms 3DS×2,PS×1): Datel Max Playstation 2 Ac… | Generic AC Power Adapter C… | Nintendo 3DS - Flame Red
- **GT**: `<a_245><b_232><c_158>` LEGO Jurassic World - Nintendo 3DS _(platform 3DS)_ ｜ **native**: `<a_249><b_170><c_61>` Buyee 128MB Memory Card for So… ✗
- **beam top5**: `<a_249><b_170><c_61>`PS, `<a_249><b_183><c_124>`PSP, `<a_249><b_194><c_103>`PSV, `<a_249><b_183><c_22>`PSP, `<a_249><b_180><c_74>`PSV
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=3DS vs rec=PS2); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_249 family 9/10); unique(a,b)=9/10, platforms=5, unique titles=9/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Datel Max Playstation …, Generic AC Power Adapt…, Nintendo 3DS - Flame R…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,nostalg,retro.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #100 — Category-miss·even top-class (a) wrong
- **History** (4 items; platforms 3DS×3,PS×1): Datel Max Playstation 2 Ac… | Generic AC Power Adapter C… | Nintendo 3DS - Flame Red | LEGO Jurassic World - Nint…
- **GT**: `<a_1><b_229><c_126>` Monster Hunter 3 Ultimate - Nintendo 3DS _(platform 3DS)_ ｜ **native**: `<a_245><b_232><c_5>` LEGO Jurassic World - PlayStat… ✗
- **beam top5**: `<a_245><b_232><c_5>`PS3, `<a_245><b_232><c_39>`PSV, `<a_245><b_91><c_144>`PS3, `<a_249><b_183><c_124>`PSP, `<a_249><b_170><c_61>`PS
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=3DS vs rec=PS3); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=6/10, platforms=6, unique titles=9/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Datel Max Playstation …, Generic AC Power Adapt…, Nintendo 3DS - Flame R…; novel candidates=0 (**pure history restatement**); genre: action,immersive,narrative.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=SUBCLASS-continuation (score3). we recommended something **more history-consistent** than the user's actual pick (rec3>target1) → **model too conservative / user more exploratory**.

### #101 — Category-OK·item wrong
- **History** (10 items; platforms 3DS×3,Xbox360×3,PS4×2): Assassin's Creed IV Black … | Medal of Honor - Xbox 360 | Kinect Sensor TV Mounting … | Mario Golf: World Tour - N… | Kirby Triple Deluxe - Nint… | Action Replay DSi
- **GT**: `<a_86><b_12><c_93>` South Park: The Fractured but Whole - PlayStat… _(platform PS4)_ ｜ **native**: `<a_240><b_76><c_14>` Thief - PlayStation 4 ✗
- **beam top5**: `<a_140><b_50><c_3>`PS4, `<a_80><b_66><c_0>`?, `<a_219><b_31><c_249>`3DS, `<a_219><b_127><c_200>`DS, `<a_113><b_31><c_38>`3DS
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (6 distinct a top-classes); unique(a,b)=8/10, platforms=5, unique titles=10/10.
- **Reasoning quality**: cites 7/10 history items (coverage 70%), anchored on: Need for Speed: Hot Pu…, Assassin's Creed IV Bl…, PlayStation 4 500GB Co…; novel candidates=1; templated opening; genre: action,adventure,racing.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #102 — Hit@6
- **History** (10 items; platforms PS4×5,?×4,WiiU×1): Kirby Mass Attack | Meta Knight amiibo - Japan… | Nintendo Super Smash Bros … | Watch Dogs - PlayStation 4 | Watch Dogs 2 - PlayStation… | Call Of Duty: Infinite War…
- **GT**: `<a_24><b_72><c_142>` Horizon Zero Dawn - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_191><b_10><c_232>` Watch Dogs 2 - PlayStation 4 ✗
- **beam top5**: `<a_123><b_58><c_78>`PS4, `<a_39><b_51><c_188>`PS4, `<a_1><b_43><c_207>`PS4, `<a_39><b_78><c_54>`PS4, `<a_201><b_45><c_166>`PS4
- **Rec↔GT gap**: correct item at beam rank 6, pred[0] prefix-depth only 0/3; platform consistent(PS4); in beam: share-a=1/10, share-(a,b)=1/10.
- **Beam diversity**: **High** (7 distinct a top-classes); unique(a,b)=10/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 6/10 history items (coverage 60%), anchored on: Mad Max - PlayStation …, Watch Dogs - PlayStati…, The Legend of Zelda: T…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). target is a sensible DRIFT and **was caught**.

### #103 — Category-OK·item wrong
- **History** (4 items; platforms 3DS×2,?×1,PS4×1): Mario Kart 7 | Nintendo 3DS Compatible wi… | Nintendo New 3DS Xl - Red … | Just Dance 2016 (Gold Edit…
- **GT**: `<a_189><b_5><c_25>` Controller Gear PS4 Controller Stand - Officia… _(platform PS4)_ ｜ **native**: `<a_111><b_238><c_188>` Just Dance 2016 - PlayStation … ✗
- **beam top5**: `<a_111><b_238><c_188>`PS4, `<a_250><b_238><c_255>`Wii, `<a_113><b_235><c_2>`3DS, `<a_111><b_236><c_47>`PS4, `<a_162><b_251><c_136>`Wii
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=8/10, platforms=7, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Mario Kart 7, Nintendo 3DS Compatibl…, Just Dance 2016 (Gold …; novel candidates=0 (**pure history restatement**); genre: action,accessor.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #104 — Category-OK·item wrong
- **History** (5 items; platforms 3DS×2,PS4×2,?×1): Mario Kart 7 | Nintendo 3DS Compatible wi… | Nintendo New 3DS Xl - Red … | Just Dance 2016 (Gold Edit… | Controller Gear PS4 Contro…
- **GT**: `<a_111><b_158><c_30>` Just Dance 2017 - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_111><b_238><c_188>` Just Dance 2016 - PlayStation … ✗
- **beam top5**: `<a_111><b_238><c_188>`PS4, `<a_189><b_90><c_110>`PS4, `<a_189><b_236><c_252>`PS, `<a_189><b_151><c_87>`PS4, `<a_189><b_201><c_57>`PS4
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform consistent(PS4); in beam: share-a=5/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (2 a top-classes); unique(a,b)=8/10, platforms=5, unique titles=10/10.
- **Reasoning quality**: cites 4/5 history items (coverage 80%), anchored on: Mario Kart 7, Nintendo 3DS Compatibl…, Just Dance 2016 (Gold …; novel candidates=0 (**pure history restatement**); templated opening; genre: action,immersive,portable.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item. Note: target shares word(s) ['dance', 'just'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #105 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_162×9/10)
- **History** (10 items; platforms WiiU×4,PS4×3,?×2): Uncharted 4: A Thief's End… | Nintendo Donkey Kong amiib… | Monster Hunter 4 Ultimate … | Dragon Quest Builders - Pl… | Nintendo Rosalina amiibo (… | Steam Controller
- **GT**: `<a_191><b_246><c_101>` Metro Redux - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_162><b_130><c_224>` Nintendo Donkey Kong amiibo (S… ✗
- **beam top5**: `<a_162><b_130><c_51>`Wii, `<a_162><b_222><c_61>`Wii, `<a_162><b_130><c_2>`Wii, `<a_162><b_122><c_56>`?, `<a_162><b_130><c_224>`Wii
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS4 vs rec=WiiU); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_162 family 9/10); unique(a,b)=4/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/10 history items (coverage 40%), anchored on: Nintendo Daisy amiibo …, Nintendo Waluigi amiib…, Mighty No. 9 - PlaySta…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=SUBCLASS-continuation (score3). we recommended something **more history-consistent** than the user's actual pick (rec3>target1) → **model too conservative / user more exploratory**.

### #106 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_39×8/10)
- **History** (3 items; platforms XboxOne×3): Pro Evolution Soccer 2015 … | Xbox One Chat Headset | Titanfall - Xbox One
- **GT**: `<a_157><b_17><c_153>` Rock Candy Wii Gesture Controller - Purple _(platform Wii)_ ｜ **native**: `<a_39><b_151><c_9>` Halo 5: Guardians ✗
- **beam top5**: `<a_39><b_114><c_237>`Xbo, `<a_39><b_114><c_209>`Xbo, `<a_39><b_69><c_69>`Xbo, `<a_39><b_204><c_3>`Xbo, `<a_39><b_151><c_9>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=Wii vs rec=XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_39 family 8/10); unique(a,b)=7/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Pro Evolution Soccer 2…, Xbox One Chat Headset, Titanfall - Xbox One; novel candidates=0 (**pure history restatement**); genre: action,shooter,sports.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #107 — Category-OK·item wrong
- **History** (4 items; platforms XboxOne×3,Wii×1): Pro Evolution Soccer 2015 … | Xbox One Chat Headset | Titanfall - Xbox One | Rock Candy Wii Gesture Con…
- **GT**: `<a_45><b_78><c_36>` NBA Live 14 - Xbox One _(platform XboxOne)_ ｜ **native**: `<a_61><b_214><c_252>` Xbox One Media Remote ✗
- **beam top5**: `<a_61><b_214><c_252>`Xbo, `<a_39><b_114><c_237>`Xbo, `<a_61><b_181><c_195>`Xbo, `<a_39><b_114><c_209>`Xbo, `<a_61><b_53><c_5>`Xbo
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform consistent(XboxOne); in beam: share-a=1/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=9/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Pro Evolution Soccer 2…, Titanfall - Xbox One, Xbox One Chat Headset; novel candidates=0 (**pure history restatement**); genre: sports,immersive,accessor.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=DRIFT (platform/word-linked) (score1). user's pick is **more history-consistent** than our top-1 (target2>rec1) → we **drifted off** a catchable continuation.

### #108 — Category-OK·item wrong · BEAM-COLLAPSE (<a_119×7/10)
- **History** (4 items; platforms WiiU×3,3DS×1): Nintendo Wii U Fit Balance… | Official Gamer Essentials … | Spirit Camera: The Cursed … | Wii U Gamepad Silicone Jac…
- **GT**: `<a_113><b_152><c_199>` HORI Compact PlayStand - Zelda Edition, Offici… _(platform Switch)_ ｜ **native**: `<a_119><b_112><c_222>` Wii U Gamepad Silicone Jacket … ✗
- **beam top5**: `<a_113><b_112><c_109>`Wii, `<a_113><b_104><c_28>`3DS, `<a_119><b_93><c_19>`Wii, `<a_119><b_119><c_158>`3DS, `<a_119><b_146><c_253>`3DS
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform mismatch(GT=Switch vs rec=WiiU); in beam: share-a=3/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_119 family 7/10); unique(a,b)=10/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 3/4 history items (coverage 75%), anchored on: Official Gamer Essenti…, Spirit Camera: The Cur…, Wii U Gamepad Silicone…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,horror.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item.

### #109 — Category-OK·item wrong
- **History** (4 items; platforms PS4×4): PlayStation 4 Camera (Old … | Uncharted 4: A Thief's End… | SQDeal Dust Proof Dust Pre… | Assassins Creed Syndicate …
- **GT**: `<a_194><b_15><c_66>` Dishonored 2 - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_118><b_185><c_102>` Batman: Arkham Knight - PlaySt… ✗
- **beam top5**: `<a_123><b_72><c_7>`PS4, `<a_201><b_213><c_242>`PS4, `<a_201><b_2><c_102>`PS4, `<a_118><b_185><c_102>`PS4, `<a_201><b_85><c_136>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=10/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 3/4 history items (coverage 75%), anchored on: Uncharted 4: A Thief's…, Assassins Creed Syndic…, PlayStation 4 Camera (…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item.

### #110 — Category-miss·even top-class (a) wrong
- **History** (4 items; platforms PS4×4): Just Dance 2016 - PlayStat… | PlayStation 4 500GB Consol… | PlayStation 4 Camera (Old … | Doom: Collector's Edition …
- **GT**: `<a_231><b_33><c_2>` ZD-N Vibration-Feedback USB Wired Gamepad Gami… _(platform PS3)_ ｜ **native**: `<a_131><b_224><c_68>` Overwatch - Origins Edition - … ✗
- **beam top5**: `<a_61><b_251><c_144>`PS4, `<a_131><b_224><c_68>`PS4, `<a_201><b_31><c_107>`PS4, `<a_131><b_41><c_229>`PS4, `<a_39><b_175><c_240>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS3 vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (7 distinct a top-classes); unique(a,b)=10/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Just Dance 2016 - Play…, PlayStation 4 500GB Co…, Doom: Collector's Edit…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,immersive,accessor.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=DRIFT (platform/word-linked) (score1). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #111 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_202×9/10)
- **History** (2 items; platforms ?×2): AULA LED Backlit Gaming Ke… | HAVIT HV-MS672 3200DPI Wir…
- **GT**: `<a_195><b_59><c_156>` Shin Megami Tensei IV - Nintendo 3DS _(platform 3DS)_ ｜ **native**: `<a_202><b_11><c_246>` Razer Naga Epic Chroma MMO Gam… ✗
- **beam top5**: `<a_202><b_253><c_105>`?, `<a_202><b_82><c_172>`?, `<a_202><b_34><c_39>`?, `<a_202><b_16><c_110>`?, `<a_202><b_203><c_93>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_202 family 9/10); unique(a,b)=9/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: AULA LED Backlit Gamin…, HAVIT HV-MS672 3200DPI…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,peripheral,accessor.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #112 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_195×10/10)
- **History** (3 items; platforms ?×2,3DS×1): AULA LED Backlit Gaming Ke… | HAVIT HV-MS672 3200DPI Wir… | Shin Megami Tensei IV - Ni…
- **GT**: `<a_216><b_93><c_101>` The Legend of Zelda: A Link Between Worlds 3D _(platform ?)_ ｜ **native**: `<a_195><b_179><c_27>` Star Ocean Till the End of Tim… ✗
- **beam top5**: `<a_195><b_36><c_218>`?, `<a_195><b_179><c_27>`PS, `<a_195><b_4><c_1>`PS, `<a_195><b_4><c_0>`?, `<a_195><b_179><c_9>`PSP
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_195 family 10/10); unique(a,b)=6/10, platforms=6, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: AULA LED Backlit Gamin…, HAVIT HV-MS672 3200DPI…, Shin Megami Tensei IV …; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,strategy.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #113 — Category-OK·item wrong
- **History** (4 items; platforms ?×2,3DS×1,DS×1): AULA LED Backlit Gaming Ke… | HAVIT HV-MS672 3200DPI Wir… | Shin Megami Tensei IV - Ni… | The Legend of Zelda: A Lin…
- **GT**: `<a_119><b_168><c_182>` HORI Screen Protective Filter for Nintendo NEW… _(platform 3DS)_ ｜ **native**: `<a_216><b_112><c_119>` The Legend of Zelda: Majora's … ✗
- **beam top5**: `<a_113><b_104><c_28>`3DS, `<a_113><b_235><c_28>`3DS, `<a_113><b_235><c_2>`3DS, `<a_216><b_165><c_184>`Wii, `<a_216><b_112><c_114>`Wii
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(3DS); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=8/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: AULA LED Backlit Gamin…, HAVIT HV-MS672 3200DPI…, Shin Megami Tensei IV …; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,immersive.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item.

### #114 — Category-OK·item wrong · BEAM-COLLAPSE (<a_119×8/10)
- **History** (5 items; platforms ?×2,3DS×2,DS×1): AULA LED Backlit Gaming Ke… | HAVIT HV-MS672 3200DPI Wir… | Shin Megami Tensei IV - Ni… | The Legend of Zelda: A Lin… | HORI Screen Protective Fil…
- **GT**: `<a_216><b_121><c_190>` Nintendo Selects: The Legend of Zelda Ocarina … _(platform ?)_ ｜ **native**: `<a_119><b_168><c_182>` HORI Screen Protective Filter … ✗
- **beam top5**: `<a_119><b_235><c_165>`3DS, `<a_119><b_119><c_158>`3DS, `<a_119><b_35><c_129>`3DS, `<a_119><b_146><c_253>`3DS, `<a_119><b_31><c_233>`3DS
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; in beam: share-a=1/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_119 family 8/10); unique(a,b)=10/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 5/5 history items (coverage 100%), anchored on: AULA LED Backlit Gamin…, HAVIT HV-MS672 3200DPI…, Shin Megami Tensei IV …; novel candidates=0 (**pure history restatement**); templated opening; genre: action,adventure,rpg.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item. Note: target shares word(s) ['3d', 'legend', 'zelda'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #115 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_216×7/10)
- **History** (6 items; platforms ?×3,3DS×2,DS×1): AULA LED Backlit Gaming Ke… | HAVIT HV-MS672 3200DPI Wir… | Shin Megami Tensei IV - Ni… | The Legend of Zelda: A Lin… | HORI Screen Protective Fil… | Nintendo Selects: The Lege…
- **GT**: `<a_194><b_235><c_193>` Final Fantasy XII: The Zodiac Age - PlayStatio… _(platform PS4)_ ｜ **native**: `<a_216><b_112><c_119>` The Legend of Zelda: Majora's … ✗
- **beam top5**: `<a_216><b_51><c_130>`3DS, `<a_216><b_112><c_119>`?, `<a_119><b_31><c_233>`3DS, `<a_216><b_112><c_114>`Wii, `<a_113><b_235><c_2>`3DS
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS4 vs rec=3DS); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_216 family 7/10); unique(a,b)=9/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 5/6 history items (coverage 83%), anchored on: AULA LED Backlit Gamin…, HAVIT HV-MS672 3200DPI…, Shin Megami Tensei IV …; novel candidates=0 (**pure history restatement**); templated opening; genre: action,adventure,rpg.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #116 — Category-OK·item wrong
- **History** (2 items; platforms PS4×2): Metal Gear Solid V: Ground… | Middle Earth: Shadow of Mo…
- **GT**: `<a_118><b_162><c_110>` Batman: Arkham Origins - Playstation 3 _(platform PS3)_ ｜ **native**: `<a_201><b_145><c_9>` The Witcher 3: Wild Hunt - Pla… ✗
- **beam top5**: `<a_201><b_145><c_9>`PS4, `<a_118><b_95><c_6>`PS4, `<a_123><b_129><c_247>`PS4, `<a_118><b_150><c_122>`PS4, `<a_123><b_72><c_7>`PS4
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform mismatch(GT=PS3 vs rec=PS4); in beam: share-a=4/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=10/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: Metal Gear Solid V: Gr…, Middle Earth: Shadow o…; novel candidates=0 (**pure history restatement**); genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=DRIFT (platform/word-linked) (score1). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #117 — Hit@4
- **History** (3 items; platforms PS4×2,PS3×1): Metal Gear Solid V: Ground… | Middle Earth: Shadow of Mo… | Batman: Arkham Origins - P…
- **GT**: `<a_123><b_129><c_247>` Metal Gear Solid V: The Phantom Pain - PlaySta… _(platform PS4)_ ｜ **native**: `<a_118><b_185><c_102>` Batman: Arkham Knight - PlaySt… ✗
- **beam top5**: `<a_118><b_185><c_102>`PS4, `<a_123><b_72><c_7>`PS4, `<a_118><b_150><c_122>`PS4, `<a_123><b_129><c_247>`PS4, `<a_118><b_95><c_6>`PS4
- **Rec↔GT gap**: correct item at beam rank 4, pred[0] prefix-depth only 0/3; platform consistent(PS4); in beam: share-a=4/10, share-(a,b)=1/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=10/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Metal Gear Solid V: Gr…, Middle Earth: Shadow o…, Batman: Arkham Origins…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). target is a sensible CLASS-cont and **was caught**.

### #118 — Category-miss·even top-class (a) wrong
- **History** (3 items; platforms PS4×3): Assassin's Creed: Syndicat… | Overwatch - Origins Editio… | Mad Max - PlayStation 4
- **GT**: `<a_191><b_56><c_45>` Payday 2 - Playstation 3 _(platform PS3)_ ｜ **native**: `<a_131><b_209><c_151>` No Man's Sky - PlayStation 4 ✗
- **beam top5**: `<a_141><b_73><c_216>`PS4, `<a_201><b_31><c_107>`PS4, `<a_131><b_210><c_0>`PS4, `<a_131><b_209><c_151>`PS4, `<a_201><b_145><c_9>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS3 vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=10/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Assassin's Creed: Synd…, Overwatch - Origins Ed…, Mad Max - PlayStation …; novel candidates=0 (**pure history restatement**); templated opening; genre: action,multiplayer,immersive.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=DRIFT (platform/word-linked) (score1). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #119 — Category-miss·even top-class (a) wrong
- **History** (4 items; platforms PS4×3,PS3×1): Assassin's Creed: Syndicat… | Overwatch - Origins Editio… | Mad Max - PlayStation 4 | Payday 2 - Playstation 3
- **GT**: `<a_24><b_37><c_113>` BioShock Infinite - PS3 [Digital Code] _(platform PS3)_ ｜ **native**: `<a_131><b_209><c_151>` No Man's Sky - PlayStation 4 ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_131><b_210><c_0>`PS4, `<a_131><b_145><c_6>`PS4, `<a_131><b_209><c_151>`PS4, `<a_200><b_186><c_92>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS3 vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=10/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Assassin's Creed: Synd…, Overwatch - Origins Ed…, Payday 2 - Playstation…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,multiplayer,immersive.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item.

### #120 — Category-OK·item wrong
- **History** (5 items; platforms Xbox360×2,3DS×2,PS4×1): Deus Ex Human Revolution: … | Horizon Zero Dawn - PlaySt… | Pok&eacute;mon Omega Ruby … | Pok&eacute;mon Sun - Ninte… | The Wolf Among Us - Xbox 3…
- **GT**: `<a_201><b_100><c_205>` Tales from the Borderlands - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_201><b_31><c_107>` Uncharted 4: A Thief's End - P… ✗
- **beam top5**: `<a_201><b_18><c_56>`PS4, `<a_201><b_31><c_107>`PS4, `<a_201><b_213><c_242>`PS4, `<a_118><b_242><c_8>`PS4, `<a_123><b_58><c_78>`PS4
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform consistent(PS4); in beam: share-a=3/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (8 distinct a top-classes); unique(a,b)=10/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 5/5 history items (coverage 100%), anchored on: Deus Ex Human Revoluti…, Horizon Zero Dawn - Pl…, The Wolf Among Us - Xb…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item.

### #121 — Hit@4
- **History** (7 items; platforms PS4×5,?×1,WiiU×1): PlayStation 4 500GB Consol… | Middle Earth: Shadow of Mo… | Bloodborne | Wolfenstein: The Old Blood… | Titanfall 2 - PlayStation … | The Legend of Zelda: Breat…
- **GT**: `<a_24><b_72><c_142>` Horizon Zero Dawn - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_194><b_15><c_66>` Dishonored 2 - PlayStation 4 ✗
- **beam top5**: `<a_194><b_15><c_66>`PS4, `<a_194><b_87><c_112>`PS4, `<a_123><b_58><c_78>`PS4, `<a_24><b_72><c_142>`PS4, `<a_24><b_86><c_14>`PS4
- **Rec↔GT gap**: correct item at beam rank 4, pred[0] prefix-depth only 0/3; platform consistent(PS4); in beam: share-a=2/10, share-(a,b)=1/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=10/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 6/7 history items (coverage 86%), anchored on: Star Wars: Battlefront…, Bloodborne, Wolfenstein: The Old B…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). target is a sensible DRIFT and **was caught**.

### #122 — Category-OK·item wrong · BEAM-COLLAPSE (<a_24×8/10)
- **History** (2 items; platforms PS4×2): Until Dawn - PlayStation 4 | Ratchet & Clank - PlayStat…
- **GT**: `<a_24><b_118><c_34>` Abzu - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_24><b_86><c_14>` Uncharted 4: A Thief's End Spe… ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_24><b_178><c_18>`Xbo, `<a_24><b_129><c_173>`PS4, `<a_24><b_145><c_101>`PS4, `<a_24><b_86><c_14>`PS4
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform consistent(PS4); in beam: share-a=8/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_24 family 8/10); unique(a,b)=10/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: Until Dawn - PlayStati…, Ratchet & Clank - Play…; novel candidates=0 (**pure history restatement**); genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #123 — Category-OK·item wrong
- **History** (8 items; platforms XboxOne×6,PC×1,DS×1): SteelSeries Nimbus Wireles… | Turtle Beach - Ear Force H… | Thrustmaster TMX Force Fee… | Thrustmaster Y-350X 7.1 Po… | SteelSeries Siberia 200 Ga… | PDP Talon Media Remote Con…
- **GT**: `<a_131><b_38><c_83>` For Honor - Xbox One _(platform XboxOne)_ ｜ **native**: `<a_61><b_214><c_225>` PDP Talon Media Remote Control… ✗
- **beam top5**: `<a_61><b_231><c_105>`Xbo, `<a_61><b_214><c_225>`Xbo, `<a_202><b_50><c_200>`DS, `<a_202><b_11><c_246>`?, `<a_202><b_3><c_27>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=8/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 5/8 history items (coverage 62%), anchored on: Mortal Kombat X Fight …, Razer Wildcat eSports …, Turtle Beach - Ear For…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,immersive,peripheral.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=SUBCLASS-continuation (score3). we recommended something **more history-consistent** than the user's actual pick (rec3>target1) → **model too conservative / user more exploratory**.

### #124 — Category-OK·item wrong
- **History** (9 items; platforms XboxOne×7,PC×1,DS×1): Turtle Beach - Ear Force H… | Thrustmaster TMX Force Fee… | Thrustmaster Y-350X 7.1 Po… | SteelSeries Siberia 200 Ga… | PDP Talon Media Remote Con… | For Honor - Xbox One
- **GT**: `<a_86><b_37><c_30>` Steep - Xbox One _(platform XboxOne)_ ｜ **native**: `<a_61><b_214><c_225>` PDP Talon Media Remote Control… ✗
- **beam top5**: `<a_61><b_231><c_105>`Xbo, `<a_61><b_53><c_47>`Xbo, `<a_61><b_111><c_109>`Xbo, `<a_202><b_50><c_200>`DS, `<a_202><b_11><c_246>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=10/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 6/9 history items (coverage 67%), anchored on: Mortal Kombat X Fight …, Razer Wildcat eSports …, Turtle Beach - Ear For…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,peripheral,accessor.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=SUBCLASS-continuation (score3). we recommended something **more history-consistent** than the user's actual pick (rec3>target1) → **model too conservative / user more exploratory**.

### #125 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_202×10/10)
- **History** (6 items; platforms ?×3,PS4×2,XboxOne×1): Far Cry Primal - PlayStati… | Logitech G610 Orion Brown … | Logitech G900 Chaos Spectr… | PDP NFL Official Face-Off … | CORSAIR Scimitar Pro RGB -… | Watch Dogs 2 - PlayStation…
- **GT**: `<a_86><b_12><c_93>` South Park: The Fractured but Whole - PlayStat… _(platform PS4)_ ｜ **native**: `<a_202><b_253><c_113>` CORSAIR Sabre - RGB Gaming Mou… ✗
- **beam top5**: `<a_202><b_58><c_107>`?, `<a_202><b_253><c_113>`?, `<a_202><b_253><c_105>`?, `<a_202><b_58><c_105>`?, `<a_202><b_3><c_27>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_202 family 10/10); unique(a,b)=8/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/6 history items (coverage 67%), anchored on: Logitech G610 Orion Br…, Logitech G900 Chaos Sp…, Watch Dogs 2 - PlaySta…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,immersive,narrative.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=SUBCLASS-continuation (score3). we recommended something **more history-consistent** than the user's actual pick (rec3>target1) → **model too conservative / user more exploratory**.

### #126 — Category-miss·even top-class (a) wrong
- **History** (5 items; platforms ?×2,XboxOne×1,PS4×1): Tom Clancy's Rainbow Six S… | Sega Genesis Core System 2… | Forza Horizon 2 for Xbox O… | Homefront: The Revolution … | Pok&eacute;mon Sun - Ninte…
- **GT**: `<a_194><b_36><c_254>` Final Fantasy XV - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_211><b_159><c_123>` Pok&eacute;mon Moon - Nintendo… ✗
- **beam top5**: `<a_211><b_159><c_123>`3DS, `<a_123><b_58><c_16>`Xbo, `<a_123><b_100><c_0>`Xbo, `<a_123><b_228><c_139>`Xbo, `<a_123><b_188><c_70>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS4 vs rec=3DS); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/5 history items (coverage 80%), anchored on: Tom Clancy's Rainbow S…, Homefront: The Revolut…, Forza Horizon 2 for Xb…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,strategy,immersive.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=SUBCLASS-continuation (score3). we recommended something **more history-consistent** than the user's actual pick (rec3>target1) → **model too conservative / user more exploratory**.

### #127 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_195×9/10)
- **History** (1 items; platforms GameBoy×1): Pokemon Ruby Version - Gam…
- **GT**: `<a_8><b_170><c_114>` Generic AC Adapter for Nintendo DS and Game Bo… _(platform DS)_ ｜ **native**: `<a_195><b_241><c_186>` Nintendo Game Boy Advance SP -… ✗
- **beam top5**: `<a_195><b_223><c_246>`?, `<a_195><b_223><c_49>`?, `<a_195><b_244><c_242>`?, `<a_195><b_241><c_186>`Gam, `<a_211><b_255><c_20>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_195 family 9/10); unique(a,b)=5/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 1/1 history items (coverage 100%), anchored on: Pokemon Ruby Version -…; novel candidates=0 (**pure history restatement**); genre: action,adventure,role-playing.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**. Note: target shares word(s) ['advance'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #128 — Category-miss·even top-class (a) wrong
- **History** (2 items; platforms GameBoy×1,DS×1): Pokemon Ruby Version - Gam… | Generic AC Adapter for Nin…
- **GT**: `<a_175><b_179><c_0>` Nintendo DS Lite Onyx Black _(platform DS)_ ｜ **native**: `<a_195><b_241><c_186>` Nintendo Game Boy Advance SP -… ✗
- **beam top5**: `<a_219><b_150><c_56>`Gam, `<a_113><b_104><c_28>`3DS, `<a_195><b_244><c_242>`?, `<a_195><b_241><c_186>`Gam, `<a_219><b_81><c_183>`Gam
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=DS vs rec=GameBoy); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=9/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: Pokemon Ruby Version -…, Generic AC Adapter for…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,immersive,nostalg.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item.

### #129 — Category-OK·item wrong
- **History** (3 items; platforms DS×2,GameBoy×1): Pokemon Ruby Version - Gam… | Generic AC Adapter for Nin… | Nintendo DS Lite Onyx Blac…
- **GT**: `<a_113><b_9><c_133>` Gamecube Controller For Nintendo White _(platform GameCube)_ ｜ **native**: `<a_195><b_241><c_186>` Nintendo Game Boy Advance SP -… ✗
- **beam top5**: `<a_219><b_150><c_56>`Gam, `<a_195><b_241><c_186>`Gam, `<a_219><b_170><c_180>`Gam, `<a_195><b_4><c_218>`?, `<a_195><b_244><c_242>`?
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform mismatch(GT=GameCube vs rec=GameBoy); in beam: share-a=1/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=10/10, platforms=5, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Pokemon Ruby Version -…, Nintendo DS Lite Onyx …, Generic AC Adapter for…; novel candidates=0 (**pure history restatement**); genre: immersive,nostalg,retro.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=DRIFT (platform/word-linked) (score1). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #130 — Hit·repurchase/same-item (easy) · BEAM-COLLAPSE (<a_219×7/10)
- **History** (4 items; platforms DS×2,GameBoy×1,GameCube×1): Pokemon Ruby Version - Gam… | Generic AC Adapter for Nin… | Nintendo DS Lite Onyx Blac… | Gamecube Controller For Ni…
- **GT**: `<a_113><b_9><c_133>` Gamecube Controller For Nintendo White _(platform GameCube)_ ｜ **native**: `<a_113><b_9><c_133>` Gamecube Controller For Ninten… ✓
- **beam top5**: `<a_113><b_9><c_133>`Gam, `<a_113><b_9><c_194>`Wii, `<a_113><b_9><c_63>`Wii, `<a_219><b_235><c_104>`3DS, `<a_219><b_150><c_56>`Gam
- **Rec↔GT gap**: top-1 exact hit.
- **Beam diversity**: **Low** (collapsed to <a_219 family 7/10); unique(a,b)=8/10, platforms=6, unique titles=10/10.
- **Reasoning quality**: cites 3/4 history items (coverage 75%), anchored on: Pokemon Ruby Version -…, Generic AC Adapter for…, Gamecube Controller Fo…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,role-playing,immersive.
- **Target sensibility (ceiling)**: target=SUBCLASS-continuation (score3); our pred[0]=SUBCLASS-continuation (score3). target is a sensible SUBCLASS-cont and **was caught**.

### #131 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_113×7/10)
- **History** (5 items; platforms DS×2,GameCube×2,GameBoy×1): Pokemon Ruby Version - Gam… | Generic AC Adapter for Nin… | Nintendo DS Lite Onyx Blac… | Gamecube Controller For Ni… | Gamecube Controller For Ni…
- **GT**: `<a_193><b_217><c_145>` Sonic and the Secret Rings - Nintendo Wii _(platform Wii)_ ｜ **native**: `<a_113><b_9><c_133>` Gamecube Controller For Ninten… ✗
- **beam top5**: `<a_219><b_235><c_104>`3DS, `<a_113><b_9><c_63>`Wii, `<a_113><b_9><c_133>`Gam, `<a_113><b_127><c_139>`?, `<a_113><b_235><c_28>`3DS
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=Wii vs rec=3DS); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_113 family 7/10); unique(a,b)=7/10, platforms=5, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Pokemon Ruby Version -…, Nintendo DS Lite Onyx …, Gamecube Controller Fo…; novel candidates=0 (**pure history restatement**); genre: action,multiplayer,nostalg.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=DRIFT (platform/word-linked) (score1). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #132 — Category-miss·even top-class (a) wrong
- **History** (6 items; platforms DS×2,GameCube×2,GameBoy×1): Pokemon Ruby Version - Gam… | Generic AC Adapter for Nin… | Nintendo DS Lite Onyx Blac… | Gamecube Controller For Ni… | Gamecube Controller For Ni… | Sonic and the Secret Rings…
- **GT**: `<a_195><b_6><c_156>` Harvest Moon: Tree of Tranquility - Nintendo W… _(platform Wii)_ ｜ **native**: `<a_193><b_153><c_247>` Sonic and the Black Knight - N… ✗
- **beam top5**: `<a_219><b_235><c_104>`3DS, `<a_193><b_40><c_61>`Xbo, `<a_113><b_35><c_8>`Gam, `<a_193><b_153><c_247>`Wii, `<a_113><b_127><c_139>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=Wii vs rec=3DS); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=6/10, platforms=7, unique titles=10/10.
- **Reasoning quality**: cites 4/5 history items (coverage 80%), anchored on: Pokemon Ruby Version -…, Generic AC Adapter for…, Gamecube Controller Fo…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=DRIFT (platform/word-linked) (score1). user's pick is **more history-consistent** than our top-1 (target2>rec1) → we **drifted off** a catchable continuation.

### #133 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_49×10/10)
- **History** (9 items; platforms PS4×4,?×3,PS3×2): PlayStation 3 40GB System | PlayStation 3 40GB System | Pokemon X | Disney Infinity:Star Wars … | Disney Infinity 3.0 Editio… | Disney Infinity 3.0: The F…
- **GT**: `<a_189><b_201><c_57>` PlayStation 4 Camera (Old Model) _(platform PS4)_ ｜ **native**: `<a_49><b_110><c_219>` Disney Infinity 3.0 Edition: S… ✗
- **beam top5**: `<a_49><b_110><c_219>`?, `<a_49><b_137><c_187>`?, `<a_49><b_146><c_81>`?, `<a_49><b_234><c_73>`?, `<a_49><b_125><c_112>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_49 family 10/10); unique(a,b)=10/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 3/8 history items (coverage 38%), anchored on: PowerA DualShock 4 Cha…, PlayStation 4 500GB Co…, PlayStation 3 40GB Sys…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,immersive,narrative.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item.

### #134 — Category-miss·even top-class (a) wrong
- **History** (10 items; platforms PS4×5,?×3,PS3×2): PlayStation 3 40GB System | Pokemon X | Disney Infinity:Star Wars … | Disney Infinity 3.0 Editio… | Disney Infinity 3.0: The F… | PlayStation 4 Camera (Old …
- **GT**: `<a_39><b_182><c_73>` Call of Duty: Black Ops III - Standard Edition… _(platform Xbox360)_ ｜ **native**: `<a_49><b_119><c_5>` Disney Infinity 3.0 Edition: S… ✗
- **beam top5**: `<a_61><b_251><c_3>`PS4, `<a_201><b_31><c_107>`PS4, `<a_61><b_251><c_51>`PS4, `<a_49><b_110><c_219>`?, `<a_189><b_236><c_135>`PS
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=Xbox360 vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=8/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 6/9 history items (coverage 67%), anchored on: PowerA DualShock 4 Cha…, PlayStation 4 500GB Co…, PlayStation 3 40GB Sys…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,immersive,narrative.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=DRIFT (platform/word-linked) (score1). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #135 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_49×8/10)
- **History** (10 items; platforms PS4×4,?×3,PS3×2): Pokemon X | Disney Infinity:Star Wars … | Disney Infinity 3.0 Editio… | Disney Infinity 3.0: The F… | PlayStation 4 Camera (Old … | Call of Duty: Black Ops II…
- **GT**: `<a_61><b_214><c_239>` HDE Media Remote Control for Microsoft Xbox On… _(platform XboxOne)_ ｜ **native**: `<a_49><b_234><c_73>` Disney Infinity 3.0 Edition: S… ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_49><b_110><c_219>`?, `<a_49><b_48><c_91>`?, `<a_49><b_137><c_187>`?, `<a_49><b_234><c_73>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=XboxOne vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_49 family 8/10); unique(a,b)=9/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 6/9 history items (coverage 67%), anchored on: PlayStation 4 Universa…, PlayStation 4 500GB Co…, PlayStation 3 40GB Sys…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,adventure,immersive.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**. Note: target shares word(s) ['media', 'remote'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #136 — Category-OK·item wrong
- **History** (10 items; platforms PS4×4,XboxOne×2,PS3×1): Robot amiibo - Japan Impor… | Samurai Warriors 4-II - Pl… | Doom: Collector's Edition … | Xbox One Stereo Headset Ad… | Doom - Xbox One | NieR: Automata - Playstati…
- **GT**: `<a_123><b_1><c_232>` Zombie Army Trilogy - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_1><b_150><c_189>` Legend of Heroes: Trails of Co… ✗
- **beam top5**: `<a_121><b_76><c_208>`PS4, `<a_1><b_25><c_254>`3DS, `<a_1><b_150><c_189>`PS3, `<a_121><b_91><c_244>`PS4, `<a_121><b_146><c_26>`PS3
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=9/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 6/10 history items (coverage 60%), anchored on: Samurai Warriors 4-II …, Doom: Collector's Edit…, Shovel Knight Amiibo -…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,fighting.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #137 — Category-OK·item wrong
- **History** (10 items; platforms PS4×5,XboxOne×2,3DS×1): Samurai Warriors 4-II - Pl… | Doom: Collector's Edition … | Xbox One Stereo Headset Ad… | Doom - Xbox One | NieR: Automata - Playstati… | Zombie Army Trilogy - Play…
- **GT**: `<a_24><b_96><c_27>` Rise of the Tomb Raider: 20 Year Celebration -… _(platform PS4)_ ｜ **native**: `<a_131><b_224><c_68>` Overwatch - Origins Edition - … ✗
- **beam top5**: `<a_162><b_125><c_53>`?, `<a_123><b_171><c_243>`PS4, `<a_24><b_129><c_173>`PS4, `<a_24><b_185><c_47>`Xbo, `<a_131><b_224><c_82>`Xbo
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; in beam: share-a=2/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=8/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 6/10 history items (coverage 60%), anchored on: Guilty Gear Xrd SIGN L…, Samurai Warriors 4-II …, Shovel Knight Amiibo -…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,fighting.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #138 — Hit@4
- **History** (10 items; platforms PS4×5,XboxOne×2,3DS×1): Doom: Collector's Edition … | Xbox One Stereo Headset Ad… | Doom - Xbox One | NieR: Automata - Playstati… | Zombie Army Trilogy - Play… | Rise of the Tomb Raider: 2…
- **GT**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - PS4 Digital Code _(platform PS4)_ ｜ **native**: `<a_24><b_185><c_47>` ReCore - Xbox One ✗
- **beam top5**: `<a_24><b_185><c_47>`Xbo, `<a_24><b_129><c_173>`PS4, `<a_24><b_72><c_142>`PS4, `<a_123><b_58><c_78>`PS4, `<a_1><b_43><c_207>`PS4
- **Rec↔GT gap**: correct item at beam rank 4, pred[0] prefix-depth only 0/3; platform mismatch(GT=PS4 vs rec=XboxOne); in beam: share-a=3/10, share-(a,b)=1/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=10/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 3/10 history items (coverage 30%), anchored on: Samurai Warriors 4-II …, Doom: Collector's Edit…, NieR: Automata - Plays…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,shooter.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). target is a sensible CLASS-cont and **was caught**.

### #139 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_123×7/10)
- **History** (10 items; platforms PS4×6,XboxOne×2,WiiU×1): Xbox One Stereo Headset Ad… | Doom - Xbox One | NieR: Automata - Playstati… | Zombie Army Trilogy - Play… | Rise of the Tomb Raider: 2… | Resident Evil 7: Biohazard…
- **GT**: `<a_175><b_216><c_18>` Ultimate Marvel vs Capcom 3 - PlayStation Vita _(platform PSVita)_ ｜ **native**: `<a_123><b_58><c_16>` Resident Evil 7 Biohazard - Xb… ✗
- **beam top5**: `<a_123><b_58><c_16>`Xbo, `<a_24><b_185><c_47>`Xbo, `<a_24><b_129><c_173>`PS4, `<a_123><b_78><c_71>`PS4, `<a_123><b_33><c_93>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PSVita vs rec=XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_123 family 7/10); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 7/10 history items (coverage 70%), anchored on: Samurai Warriors 4-II …, Doom: Collector's Edit…, Doom - Xbox One; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,shooter.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=SUBCLASS-continuation (score3). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #140 — Category-OK·item wrong
- **History** (10 items; platforms PS4×6,XboxOne×2,?×1): Doom - Xbox One | NieR: Automata - Playstati… | Zombie Army Trilogy - Play… | Rise of the Tomb Raider: 2… | Resident Evil 7: Biohazard… | Ultimate Marvel vs Capcom …
- **GT**: `<a_131><b_41><c_74>` Doom: Collector's Edition - Xbox One _(platform XboxOne)_ ｜ **native**: `<a_123><b_58><c_16>` Resident Evil 7 Biohazard - Xb… ✗
- **beam top5**: `<a_123><b_58><c_16>`Xbo, `<a_24><b_129><c_173>`PS4, `<a_24><b_185><c_47>`Xbo, `<a_24><b_72><c_142>`PS4, `<a_123><b_33><c_93>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 6/10 history items (coverage 60%), anchored on: Samurai Warriors 4-II …, Doom - Xbox One, Doom: Collector's Edit…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,shooter.
- **Target sensibility (ceiling)**: target=SUBCLASS-continuation (score3); our pred[0]=SUBCLASS-continuation (score3). same relatedness tier (score3) but wrong specific item. Note: target shares word(s) ["collector's", 'doom'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #141 — Category-OK·item wrong
- **History** (10 items; platforms PS4×4,XboxOne×4,?×1): 7 Days to Die - Xbox One | Xbox One S 500GB Console -… | Call Of Duty: Infinite War… | Playstation Plus: 3 Month … | Call of Duty: Infinite War… | Zacro 13ft PS4 Controller …
- **GT**: `<a_201><b_213><c_242>` The Last of Us Remastered - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_39><b_77><c_105>` Call of Duty: Infinite Warfare… ✗
- **beam top5**: `<a_39><b_77><c_105>`Xbo, `<a_123><b_58><c_16>`Xbo, `<a_123><b_58><c_78>`PS4, `<a_61><b_251><c_144>`PS4, `<a_123><b_100><c_0>`Xbo
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform mismatch(GT=PS4 vs rec=XboxOne); in beam: share-a=1/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=8/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 6/10 history items (coverage 60%), anchored on: Call of Duty: Ghosts -…, Call Of Duty: Infinite…, Xbox One Wireless Cont…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,shooter,multiplayer.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=DRIFT (platform/word-linked) (score1). user's pick is **more history-consistent** than our top-1 (target2>rec1) → we **drifted off** a catchable continuation.

### #142 — Category-OK·item wrong · BEAM-COLLAPSE (<a_39×8/10)
- **History** (10 items; platforms ?×3,PS4×2,3DS×2): Wii Remote Plus - Black | Nintendo Nunchuk Controlle… | Nintendo Wii U Pro Control… | Mega Man Legacy Collection… | The King of Fighters XIV: … | Halo 5: Guardians
- **GT**: `<a_7><b_36><c_217>` Xbox One X 1TB Limited Edition Console - Proje… _(platform XboxOne)_ ｜ **native**: `<a_39><b_77><c_105>` Call of Duty: Infinite Warfare… ✗
- **beam top5**: `<a_39><b_77><c_105>`Xbo, `<a_39><b_175><c_240>`Xbo, `<a_39><b_69><c_69>`Xbo, `<a_7><b_248><c_176>`Xbo, `<a_39><b_51><c_21>`Xbo
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform consistent(XboxOne); in beam: share-a=1/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_39 family 8/10); unique(a,b)=9/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 5/10 history items (coverage 50%), anchored on: Street Fighter V - Pla…, The King of Fighters X…, Halo 5: Guardians; novel candidates=0 (**pure history restatement**); templated opening; genre: action,adventure,fighting.
- **Target sensibility (ceiling)**: target=SUBCLASS-continuation (score3); our pred[0]=CLASS-continuation (score2). user's pick is **more history-consistent** than our top-1 (target3>rec2) → we **drifted off** a catchable continuation. Note: target shares word(s) ['discontinued'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #143 — Category-miss·even top-class (a) wrong
- **History** (2 items; platforms XboxOne×2): Tom Clancy&rsquo;s Ghost R… | Dishonored 2 - Xbox One
- **GT**: `<a_113><b_4><c_80>` Zettaguard New Classic Pro Controller Console … _(platform Wii)_ ｜ **native**: `<a_194><b_15><c_66>` Dishonored 2 - PlayStation 4 ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_201><b_213><c_242>`PS4, `<a_194><b_15><c_9>`PS4, `<a_194><b_15><c_66>`PS4, `<a_123><b_58><c_78>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=Wii vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=9/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: Tom Clancy&rsquo;s Gho…, Dishonored 2 - Xbox On…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,role-playing,immersive.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=EXPLORATION (unrelated) (score0). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #144 — Category-miss·even top-class (a) wrong
- **History** (3 items; platforms XboxOne×2,Wii×1): Tom Clancy&rsquo;s Ghost R… | Dishonored 2 - Xbox One | Zettaguard New Classic Pro…
- **GT**: `<a_140><b_69><c_39>` Watch Dogs xbox one _(platform XboxOne)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_194><b_15><c_66>`PS4, `<a_123><b_44><c_0>`PS4, `<a_123><b_58><c_78>`PS4, `<a_194><b_15><c_9>`PS4, `<a_123><b_142><c_36>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=XboxOne vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=9/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Tom Clancy&rsquo;s Gho…, Dishonored 2 - Xbox On…, Zettaguard New Classic…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,role-playing,immersive.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=SUBCLASS-continuation (score3). we recommended something **more history-consistent** than the user's actual pick (rec3>target1) → **model too conservative / user more exploratory**.

### #145 — Category-miss·even top-class (a) wrong
- **History** (4 items; platforms XboxOne×3,Wii×1): Tom Clancy&rsquo;s Ghost R… | Dishonored 2 - Xbox One | Zettaguard New Classic Pro… | Watch Dogs xbox one
- **GT**: `<a_84><b_54><c_87>` Nintendo Wii U 32GB Mario Kart 8 (Pre-Installe… _(platform WiiU)_ ｜ **native**: `<a_131><b_155><c_206>` Fallout 4 - Xbox One ✗
- **beam top5**: `<a_131><b_155><c_206>`Xbo, `<a_123><b_76><c_255>`Xbo, `<a_123><b_58><c_16>`Xbo, `<a_191><b_187><c_236>`Xbo, `<a_131><b_210><c_0>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=WiiU vs rec=XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=8/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Tom Clancy&rsquo;s Gho…, Dishonored 2 - Xbox On…, Watch Dogs xbox one; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=DRIFT (platform/word-linked) (score1). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #146 — Category-miss·even top-class (a) wrong
- **History** (5 items; platforms XboxOne×3,Wii×1,WiiU×1): Tom Clancy&rsquo;s Ghost R… | Dishonored 2 - Xbox One | Zettaguard New Classic Pro… | Watch Dogs xbox one | Nintendo Wii U 32GB Mario …
- **GT**: `<a_39><b_251><c_254>` Titanfall - Xbox 360 _(platform Xbox360)_ ｜ **native**: `<a_131><b_155><c_206>` Fallout 4 - Xbox One ✗
- **beam top5**: `<a_131><b_155><c_206>`Xbo, `<a_131><b_210><c_0>`PS4, `<a_123><b_171><c_44>`Xbo, `<a_131><b_224><c_16>`PC, `<a_191><b_10><c_19>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=Xbox360 vs rec=XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=6/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 4/5 history items (coverage 80%), anchored on: Tom Clancy&rsquo;s Gho…, Dishonored 2 - Xbox On…, Watch Dogs xbox one; novel candidates=0 (**pure history restatement**); templated opening; genre: action,role-playing,multiplayer.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=DRIFT (platform/word-linked) (score1). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #147 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_39×7/10)
- **History** (3 items; platforms PS4×2,PC×1): Final Fantasy XV - PlaySta… | The Last of Us Remastered … | Tom Clancy's Rainbow Six S…
- **GT**: `<a_201><b_151><c_255>` Playstation Plus: 3 Month Membership [Digital … _(platform PS-generic)_ ｜ **native**: `<a_39><b_156><c_118>` Tom Clancy's Rainbow Six Siege… ✗
- **beam top5**: `<a_39><b_69><c_69>`Xbo, `<a_39><b_77><c_105>`Xbo, `<a_39><b_156><c_118>`Xbo, `<a_39><b_51><c_254>`PC, `<a_123><b_76><c_232>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS-generic vs rec=XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_39 family 7/10); unique(a,b)=8/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Final Fantasy XV - Pla…, The Last of Us Remaste…, Tom Clancy's Rainbow S…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item.

### #148 — Category-miss·even top-class (a) wrong
- **History** (4 items; platforms PS4×2,PC×1,PS×1): Final Fantasy XV - PlaySta… | The Last of Us Remastered … | Tom Clancy's Rainbow Six S… | Playstation Plus: 3 Month …
- **GT**: `<a_201><b_78><c_157>` inFAMOUS: Second Son Standard Edition (PlaySta… _(platform PS4)_ ｜ **native**: `<a_39><b_156><c_118>` Tom Clancy's Rainbow Six Siege… ✗
- **beam top5**: `<a_39><b_69><c_69>`Xbo, `<a_39><b_77><c_105>`Xbo, `<a_39><b_51><c_21>`Xbo, `<a_39><b_182><c_247>`PS4, `<a_39><b_151><c_9>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS4 vs rec=XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=10/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Final Fantasy XV - Pla…, The Last of Us Remaste…, Tom Clancy's Rainbow S…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item.

### #149 — Category-miss·even top-class (a) wrong
- **History** (5 items; platforms PS4×3,PC×1,PS×1): Final Fantasy XV - PlaySta… | The Last of Us Remastered … | Tom Clancy's Rainbow Six S… | Playstation Plus: 3 Month … | inFAMOUS: Second Son Stand…
- **GT**: `<a_61><b_40><c_177>` Microsoft Xbox 360 Wired Controller for Window… _(platform Xbox360)_ ｜ **native**: `<a_123><b_76><c_232>` Far Cry Primal - PlayStation 4… ✗
- **beam top5**: `<a_131><b_210><c_0>`PS4, `<a_201><b_31><c_107>`PS4, `<a_123><b_72><c_7>`PS4, `<a_123><b_129><c_247>`PS4, `<a_39><b_69><c_69>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=Xbox360 vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=10/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 5/5 history items (coverage 100%), anchored on: Final Fantasy XV - Pla…, The Last of Us Remaste…, Tom Clancy's Rainbow S…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=DRIFT (platform/word-linked) (score1). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #150 — Category-OK·item wrong
- **History** (6 items; platforms PS4×3,PC×1,PS×1): Final Fantasy XV - PlaySta… | The Last of Us Remastered … | Tom Clancy's Rainbow Six S… | Playstation Plus: 3 Month … | inFAMOUS: Second Son Stand… | Microsoft Xbox 360 Wired C…
- **GT**: `<a_39><b_78><c_54>` Battlefield 1 - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_39><b_156><c_118>` Tom Clancy's Rainbow Six Siege… ✗
- **beam top5**: `<a_61><b_53><c_46>`Xbo, `<a_39><b_69><c_69>`Xbo, `<a_61><b_167><c_164>`Xbo, `<a_61><b_53><c_5>`Xbo, `<a_39><b_156><c_118>`Xbo
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform mismatch(GT=PS4 vs rec=XboxOne); in beam: share-a=4/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (2 a top-classes); unique(a,b)=8/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 5/6 history items (coverage 83%), anchored on: Final Fantasy XV - Pla…, The Last of Us Remaste…, Tom Clancy's Rainbow S…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item.

### #151 — Category-OK·item wrong
- **History** (4 items; platforms PS4×3,PS3×1): Fallout: New Vegas Ultimat… | Tomb Raider: Definitive Ed… | Wolfenstein: The Old Blood… | Street Fighter V - PlaySta…
- **GT**: `<a_208><b_146><c_3>` Onechanbara Z2: Chaos - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_208><b_175><c_24>` Street Fighter V - Collector's… ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_208><b_175><c_24>`PS4, `<a_194><b_87><c_249>`PS4, `<a_131><b_210><c_0>`PS4, `<a_208><b_32><c_26>`PS4
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform consistent(PS4); in beam: share-a=4/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=8/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Fallout: New Vegas Ult…, Tomb Raider: Definitiv…, Wolfenstein: The Old B…; novel candidates=0 (**pure history restatement**); genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=DRIFT (platform/word-linked) (score1). user's pick is **more history-consistent** than our top-1 (target2>rec1) → we **drifted off** a catchable continuation.

### #152 — Category-OK·item wrong
- **History** (7 items; platforms ?×5,PC×2): The Sims 3 Seasons | The Sims 3: Master Suite S… | The Sims 3: Showtime - PC/… | The Sims 4 Luxury Party St… | The Sims 4 - Romantic Gard… | The Sims 4 Outdoor Retreat…
- **GT**: `<a_22><b_126><c_226>` The Sims 4 Get to Work _(platform ?)_ ｜ **native**: `<a_22><b_89><c_201>` The Sims 4 Cool Kitchen Stuff … ✗
- **beam top5**: `<a_22><b_89><c_201>`?, `<a_22><b_173><c_203>`?, `<a_22><b_88><c_75>`PC, `<a_195><b_84><c_111>`PC, `<a_195><b_69><c_235>`?
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; in beam: share-a=5/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (2 a top-classes); unique(a,b)=5/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 5/7 history items (coverage 71%), anchored on: The Sims 3 Starter Pac…, The Sims 3 Seasons, The Sims 3: Master Sui…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,immersive.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item. Note: target shares word(s) ['sims'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #153 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_123×10/10)
- **History** (4 items; platforms PS4×4): Rise of the Tomb Raider: 2… | Resident Evil Origins Coll… | Resident Evil 5 - Standard… | Resident Evil 4 - PlayStat…
- **GT**: `<a_194><b_242><c_173>` Lightning Returns: Final Fantasy XIII _(platform ?)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_123><b_58><c_78>`PS4, `<a_123><b_160><c_188>`PS4, `<a_123><b_188><c_192>`PS4, `<a_123><b_33><c_93>`PS4, `<a_123><b_171><c_243>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_123 family 10/10); unique(a,b)=8/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Rise of the Tomb Raide…, Resident Evil Origins …, Resident Evil 5 - Stan…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #154 — Category-OK·item wrong · BEAM-COLLAPSE (<a_123×7/10)
- **History** (5 items; platforms PS4×4,?×1): Rise of the Tomb Raider: 2… | Resident Evil Origins Coll… | Resident Evil 5 - Standard… | Resident Evil 4 - PlayStat… | Lightning Returns: Final F…
- **GT**: `<a_194><b_36><c_254>` Final Fantasy XV - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_123><b_78><c_71>` Resident Evil 4 - PlayStation … ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_24><b_129><c_173>`PS4, `<a_24><b_72><c_142>`PS4, `<a_123><b_58><c_78>`PS4, `<a_123><b_171><c_243>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_123 family 7/10); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/5 history items (coverage 80%), anchored on: Rise of the Tomb Raide…, Resident Evil Origins …, Resident Evil 4 - Play…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item. Note: target shares word(s) ['fantasy', 'final'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #155 — Category-miss·even top-class (a) wrong
- **History** (6 items; platforms PS4×5,?×1): Rise of the Tomb Raider: 2… | Resident Evil Origins Coll… | Resident Evil 5 - Standard… | Resident Evil 4 - PlayStat… | Lightning Returns: Final F… | Final Fantasy XV - PlaySta…
- **GT**: `<a_92><b_18><c_43>` Final Fantasy XIII - Playstation 3 _(platform PS3)_ ｜ **native**: `<a_194><b_15><c_66>` Dishonored 2 - PlayStation 4 ✗
- **beam top5**: `<a_194><b_215><c_154>`?, `<a_24><b_72><c_142>`PS4, `<a_194><b_15><c_66>`PS4, `<a_194><b_87><c_112>`PS4, `<a_194><b_87><c_249>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=7/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 6/6 history items (coverage 100%), anchored on: Rise of the Tomb Raide…, Resident Evil Origins …, Lightning Returns: Fin…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**. Note: target shares word(s) ['fantasy', 'final', 'xiii'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #156 — Category-miss·even top-class (a) wrong
- **History** (7 items; platforms PS4×5,?×1,PS3×1): Resident Evil Origins Coll… | Resident Evil 5 - Standard… | Resident Evil 4 - PlayStat… | Lightning Returns: Final F… | Final Fantasy XV - PlaySta… | Final Fantasy XIII - Plays…
- **GT**: `<a_10><b_120><c_54>` Dragon Age Origins: Ultimate Edition - Playsta… _(platform PS3)_ ｜ **native**: `<a_194><b_87><c_112>` Dark Souls III - PlayStation 4… ✗
- **beam top5**: `<a_194><b_215><c_154>`?, `<a_194><b_87><c_112>`PS4, `<a_194><b_87><c_249>`PS4, `<a_194><b_15><c_66>`PS4, `<a_24><b_72><c_142>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=7/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 6/7 history items (coverage 86%), anchored on: Rise of the Tomb Raide…, Resident Evil Origins …, Lightning Returns: Fin…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**. Note: target shares word(s) ['origins'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #157 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_202×10/10)
- **History** (4 items; platforms ?×3,Switch×1): Razer Naga Epic Chroma MMO… | Razer Diamondback - Chroma… | Razer Blackwidow Ultimate … | Razer DeathAdder Expert - …
- **GT**: `<a_205><b_208><c_148>` Gran Turismo Sport - Limited Edition - PlaySta… _(platform PS4)_ ｜ **native**: `<a_202><b_16><c_110>` Razer DeathAdder Expert - Opti… ✗
- **beam top5**: `<a_202><b_58><c_107>`?, `<a_202><b_58><c_57>`?, `<a_202><b_58><c_122>`?, `<a_202><b_113><c_73>`?, `<a_202><b_120><c_89>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_202 family 10/10); unique(a,b)=6/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 3/4 history items (coverage 75%), anchored on: Razer Naga Epic Chroma…, Razer Diamondback - Ch…, Razer DeathAdder Exper…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,peripheral,accessor.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #158 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_202×7/10)
- **History** (3 items; platforms Switch×1,PS4×1,?×1): Razer BlackWidow Chroma: C… | Razer Kraken Pro Analog Ga… | Steam Controller
- **GT**: `<a_8><b_173><c_201>` dreamGEAR- Playstation 4 Charge and Play Premi… _(platform PS4)_ ｜ **native**: `<a_202><b_11><c_246>` Razer Naga Epic Chroma MMO Gam… ✗
- **beam top5**: `<a_202><b_11><c_246>`?, `<a_202><b_58><c_57>`?, `<a_202><b_120><c_89>`?, `<a_202><b_16><c_110>`?, `<a_202><b_3><c_27>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_202 family 7/10); unique(a,b)=10/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Razer BlackWidow Chrom…, Razer Kraken Pro Analo…, Steam Controller; novel candidates=0 (**pure history restatement**); templated opening; genre: action,immersive,peripheral.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #159 — Category-miss·even top-class (a) wrong
- **History** (4 items; platforms PS4×2,Switch×1,?×1): Razer BlackWidow Chroma: C… | Razer Kraken Pro Analog Ga… | Steam Controller | dreamGEAR- Playstation 4 C…
- **GT**: `<a_89><b_134><c_152>` Star Wars: The Old Republic - 14,500 Cartel Co… _(platform ?)_ ｜ **native**: `<a_202><b_11><c_246>` Razer Naga Epic Chroma MMO Gam… ✗
- **beam top5**: `<a_202><b_11><c_246>`?, `<a_61><b_251><c_144>`PS4, `<a_61><b_131><c_197>`Xbo, `<a_202><b_16><c_110>`?, `<a_202><b_113><c_73>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (2 a top-classes); unique(a,b)=9/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Razer BlackWidow Chrom…, Razer Kraken Pro Analo…, Steam Controller; novel candidates=0 (**pure history restatement**); genre: peripheral,accessor.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #160 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_201×7/10)
- **History** (7 items; platforms PS4×3,Wii×2,3DS×1): Just Dance 2015 - Wii | Just Dance 2016 - Wii | The Last of Us Remastered … | Until Dawn - PlayStation 4 | Steam Controller | PlayStation 4 500GB Consol…
- **GT**: `<a_113><b_29><c_105>` HORI Nintendo Switch Pokken Tournament DX Pro … _(platform Switch)_ ｜ **native**: `<a_201><b_169><c_181>` PlayStation 4 500GB Console - … ✗
- **beam top5**: `<a_131><b_210><c_0>`PS4, `<a_201><b_36><c_195>`PS4, `<a_201><b_169><c_181>`PS4, `<a_201><b_2><c_195>`PS4, `<a_201><b_169><c_103>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=Switch vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_201 family 7/10); unique(a,b)=8/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 6/7 history items (coverage 86%), anchored on: The Last of Us Remaste…, Until Dawn - PlayStati…, Just Dance 2015 - Wii; novel candidates=0 (**pure history restatement**); genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item. Note: target shares word(s) ['controller', 'pokemon'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #161 — Category-OK·item wrong
- **History** (8 items; platforms PS4×3,Wii×2,3DS×1): Just Dance 2016 - Wii | The Last of Us Remastered … | Until Dawn - PlayStation 4 | Steam Controller | PlayStation 4 500GB Consol… | HORI Nintendo Switch Pokke…
- **GT**: `<a_113><b_152><c_199>` HORI Compact PlayStand - Zelda Edition, Offici… _(platform Switch)_ ｜ **native**: `<a_111><b_176><c_225>` Just Dance 2016 - Xbox 360 ✗
- **beam top5**: `<a_111><b_19><c_7>`Xbo, `<a_111><b_176><c_225>`Xbo, `<a_111><b_238><c_188>`PS4, `<a_61><b_35><c_122>`PS, `<a_61><b_35><c_105>`PS4
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform mismatch(GT=Switch vs rec=XboxOne); in beam: share-a=1/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=8/10, platforms=5, unique titles=10/10.
- **Reasoning quality**: cites 6/8 history items (coverage 75%), anchored on: The Last of Us Remaste…, Until Dawn - PlayStati…, Just Dance 2015 - Wii; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item. Note: target shares word(s) ['by', 'hori', 'licensed', 'officially'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #162 — Category-OK·item wrong · BEAM-COLLAPSE (<a_61×7/10)
- **History** (9 items; platforms PS4×3,Wii×2,Switch×2): The Last of Us Remastered … | Until Dawn - PlayStation 4 | Steam Controller | PlayStation 4 500GB Consol… | HORI Nintendo Switch Pokke… | HORI Compact PlayStand - Z…
- **GT**: `<a_191><b_209><c_103>` Heavy Rain and Beyond Two Souls Collection HD … _(platform PS4)_ ｜ **native**: `<a_61><b_35><c_122>` Mad Catz Street Fighter V Arca… ✗
- **beam top5**: `<a_61><b_44><c_172>`PS4, `<a_61><b_251><c_144>`PS4, `<a_61><b_35><c_122>`PS, `<a_111><b_238><c_188>`PS4, `<a_61><b_35><c_106>`PS
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_61 family 7/10); unique(a,b)=8/10, platforms=5, unique titles=10/10.
- **Reasoning quality**: cites 6/9 history items (coverage 67%), anchored on: The Last of Us Remaste…, Until Dawn - PlayStati…, Just Dance 2015 - Wii; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**. Note: target shares word(s) ['remastered'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #163 — Category-OK·item wrong
- **History** (9 items; platforms PS4×5,XboxOne×3,?×1): Horizon Zero Dawn - PlaySt… | Resident Evil 6 - PlayStat… | Resident Evil 7 Biohazard … | ScreamRide | Toy Soldiers: War Chest Ha… | Ratchet & Clank - PS4 [Dig…
- **GT**: `<a_111><b_176><c_131>` Just Dance 2016 - Xbox One _(platform XboxOne)_ ｜ **native**: `<a_123><b_228><c_139>` Dead Rising 4 - Xbox One ✗
- **beam top5**: `<a_74><b_5><c_203>`Xbo, `<a_140><b_237><c_62>`PS4, `<a_86><b_18><c_29>`Xbo, `<a_123><b_228><c_139>`Xbo, `<a_74><b_218><c_206>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=9/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 6/9 history items (coverage 67%), anchored on: Final Fantasy X X-2 HD…, ReCore - Xbox One, Resident Evil 6 - Play…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #164 — Category-OK·item wrong
- **History** (10 items; platforms PS4×5,XboxOne×4,?×1): Resident Evil 6 - PlayStat… | Resident Evil 7 Biohazard … | ScreamRide | Toy Soldiers: War Chest Ha… | Ratchet & Clank - PS4 [Dig… | Just Dance 2016 - Xbox One
- **GT**: `<a_240><b_76><c_129>` Thief Xbox one _(platform XboxOne)_ ｜ **native**: `<a_123><b_58><c_16>` Resident Evil 7 Biohazard - Xb… ✗
- **beam top5**: `<a_74><b_5><c_203>`Xbo, `<a_74><b_218><c_206>`PS4, `<a_123><b_171><c_44>`Xbo, `<a_123><b_78><c_71>`PS4, `<a_123><b_228><c_139>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 7/10 history items (coverage 70%), anchored on: Final Fantasy X X-2 HD…, ReCore - Xbox One, Resident Evil 6 - Play…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #165 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_123×10/10)
- **History** (10 items; platforms XboxOne×5,PS4×4,?×1): Resident Evil 7 Biohazard … | ScreamRide | Toy Soldiers: War Chest Ha… | Ratchet & Clank - PS4 [Dig… | Just Dance 2016 - Xbox One | Thief Xbox one
- **GT**: `<a_106><b_169><c_144>` Tearaway Unfolded - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_123><b_228><c_139>` Dead Rising 4 - Xbox One ✗
- **beam top5**: `<a_123><b_228><c_139>`Xbo, `<a_123><b_58><c_16>`Xbo, `<a_123><b_33><c_93>`PS4, `<a_123><b_171><c_44>`Xbo, `<a_123><b_58><c_78>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS4 vs rec=XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_123 family 10/10); unique(a,b)=7/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 5/10 history items (coverage 50%), anchored on: Resident Evil 6 - Play…, Resident Evil 7 Biohaz…, Just Dance 2016 - Xbox…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #166 — Category-miss·even top-class (a) wrong
- **History** (2 items; platforms PS4×2): WWE 2K16 - PlayStation 4 | Agents of Mayhem - PlaySta…
- **GT**: `<a_71><b_86><c_236>` UNCHARTED: The Nathan Drake Collection - PlayS… _(platform PS4)_ ｜ **native**: `<a_208><b_25><c_47>` Dragon Ball Z: Extreme Butoden… ✗
- **beam top5**: `<a_13><b_142><c_118>`PSV, `<a_123><b_72><c_7>`PS4, `<a_201><b_31><c_107>`PS4, `<a_1><b_252><c_25>`PS4, `<a_131><b_210><c_0>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS4 vs rec=PSVita); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (6 distinct a top-classes); unique(a,b)=10/10, platforms=5, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: WWE 2K16 - PlayStation…, Agents of Mayhem - Pla…; novel candidates=0 (**pure history restatement**); genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #167 — Category-OK·item wrong
- **History** (8 items; platforms WiiU×3,PS4×3,?×2): Hyrule Warriors - Nintendo… | Tokyo Mirage Sessions #FE … | Nintendo Wii U Console 8GB… | Dragon Age Inquisition - S… | Sleeping Dogs: Definitive … | UNCHARTED: The Nathan Drak…
- **GT**: `<a_24><b_145><c_101>` Tomb Raider: Definitive Edition - PlayStation … _(platform PS4)_ ｜ **native**: `<a_131><b_210><c_0>` Fallout 4 - PlayStation 4 ✗
- **beam top5**: `<a_208><b_175><c_0>`PS4, `<a_131><b_210><c_0>`PS4, `<a_118><b_185><c_102>`PS4, `<a_1><b_25><c_254>`3DS, `<a_208><b_235><c_151>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=10/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 5/8 history items (coverage 62%), anchored on: The Legend of Zelda: S…, The Legend of Zelda: O…, Tokyo Mirage Sessions …; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item. Note: target shares word(s) ['definitive'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #168 — Category-OK·item wrong
- **History** (3 items; platforms PS3×3): Alice: Madness Returns - P… | Dragon Ball Xenoverse - Pl… | Insten Replacement Control…
- **GT**: `<a_249><b_129><c_134>` PlayStation 3 40GB System _(platform PS3)_ ｜ **native**: `<a_21><b_194><c_2>` Insten Replacement Controller … ✗
- **beam top5**: `<a_21><b_194><c_2>`PS3, `<a_249><b_170><c_61>`PS, `<a_61><b_47><c_32>`PS3, `<a_21><b_138><c_81>`Gam, `<a_61><b_47><c_8>`PS3
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform consistent(PS3); in beam: share-a=3/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=9/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Alice: Madness Returns…, Dragon Ball Xenoverse …, Insten Replacement Con…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=SUBCLASS-continuation (score3). we recommended something **more history-consistent** than the user's actual pick (rec3>target1) → **model too conservative / user more exploratory**.

### #169 — Hit@7 · RERANK-HARM
- **History** (4 items; platforms PS3×4): Alice: Madness Returns - P… | Dragon Ball Xenoverse - Pl… | Insten Replacement Control… | PlayStation 3 40GB System
- **GT**: `<a_249><b_129><c_134>` PlayStation 3 40GB System _(platform PS3)_ ｜ **native**: `<a_249><b_129><c_134>` PlayStation 3 40GB System ✓
- **beam top5**: `<a_249><b_80><c_0>`PS2, `<a_61><b_47><c_32>`PS3, `<a_21><b_138><c_81>`Gam, `<a_249><b_129><c_157>`PS3, `<a_249><b_138><c_30>`PS
- **Rec↔GT gap**: correct item at beam rank 7, pred[0] prefix-depth only 1/3; platform mismatch(GT=PS3 vs rec=PS2); in beam: share-a=5/10, share-(a,b)=2/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=8/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Alice: Madness Returns…, Dragon Ball Xenoverse …, Insten Replacement Con…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=SUBCLASS-continuation (score3); our pred[0]=CLASS-continuation (score2). target is a sensible SUBCLASS-cont and **was caught**.

### #170 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_39×7/10)
- **History** (9 items; platforms XboxOne×5,?×2,Xbox360×2): Dragon Ball Xenoverse - Xb… | ReCore - Xbox One | Microsoft Xbox 360 Wired C… | Battlefield 1 Early Enlist… | Killzone Mercenary | Battlefield Hardline Delux…
- **GT**: `<a_59><b_168><c_1>` Midnight Club _(platform ?)_ ｜ **native**: `<a_39><b_77><c_105>` Call of Duty: Infinite Warfare… ✗
- **beam top5**: `<a_39><b_77><c_105>`Xbo, `<a_39><b_77><c_69>`Xbo, `<a_39><b_51><c_21>`Xbo, `<a_61><b_53><c_5>`Xbo, `<a_61><b_137><c_255>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_39 family 7/10); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 5/9 history items (coverage 56%), anchored on: Call of Duty: Advanced…, Battlefield Hardline D…, Battlefield 1 Early En…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,shooter,strategy.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #171 — Category-OK·item wrong · BEAM-COLLAPSE (<a_123×7/10)
- **History** (10 items; platforms PS4×6,PS3×2,?×2): Mass Effect Andromeda - Pr… | Zombie Army Trilogy - Play… | Mad Max - PlayStation 4 | Saints Row IV: Re-Elected … | Far Cry Compilation | Prey - Pre-load - PS4 Digi…
- **GT**: `<a_191><b_204><c_225>` Just Cause 3 - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_123><b_100><c_33>`PS4, `<a_123><b_44><c_0>`PS4, `<a_24><b_72><c_142>`PS4, `<a_123><b_72><c_238>`PS3
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_123 family 7/10); unique(a,b)=10/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 5/10 history items (coverage 50%), anchored on: Deus Ex Human Revoluti…, Deus Ex: Mankind Divid…, Mass Effect Andromeda …; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #172 — Category-miss·even top-class (a) wrong
- **History** (3 items; platforms Xbox360×2,PS3×1): Assassin's Creed IV Black … | Xbox 360 Microsoft Authent… | Dead Rising - Xbox 360
- **GT**: `<a_89><b_210><c_218>` Guild Wars 2, Heart of Thorns - PC Guild Wars … _(platform PC)_ ｜ **native**: `<a_39><b_204><c_1>` Battlefield 4 - Xbox 360 ✗
- **beam top5**: `<a_140><b_69><c_39>`Xbo, `<a_61><b_214><c_252>`Xbo, `<a_39><b_204><c_1>`Xbo, `<a_80><b_212><c_236>`Xbo, `<a_39><b_182><c_247>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PC vs rec=XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=8/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Assassin's Creed IV Bl…, Dead Rising - Xbox 360, Xbox 360 Microsoft Aut…; novel candidates=0 (**pure history restatement**); genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=EXPLORATION (unrelated) (score0). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #173 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_89×10/10)
- **History** (4 items; platforms Xbox360×2,PS3×1,PC×1): Assassin's Creed IV Black … | Xbox 360 Microsoft Authent… | Dead Rising - Xbox 360 | Guild Wars 2, Heart of Tho…
- **GT**: `<a_157><b_178><c_201>` Snoopy's Grand Adventure - Xbox 360 _(platform Xbox360)_ ｜ **native**: `<a_89><b_86><c_50>` World of Warcraft 60 Day Game … ✗
- **beam top5**: `<a_89><b_86><c_50>`?, `<a_89><b_210><c_218>`PC, `<a_89><b_239><c_104>`PC, `<a_89><b_86><c_158>`PC, `<a_89><b_221><c_81>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_89 family 10/10); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Assassin's Creed IV Bl…, Dead Rising - Xbox 360, Guild Wars 2, Heart of…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #174 — Hit@2 · BEAM-COLLAPSE (<a_123×9/10)
- **History** (2 items; platforms PS4×2): Resident Evil: Revelations… | Resident Evil 4 - PlayStat…
- **GT**: `<a_201><b_31><c_107>` Uncharted 4: A Thief's End - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_123><b_142><c_36>` 7 Days to Die - PlayStation 4 ✗
- **beam top5**: `<a_123><b_188><c_192>`PS4, `<a_201><b_31><c_107>`PS4, `<a_123><b_142><c_36>`PS4, `<a_123><b_2><c_26>`PS4, `<a_123><b_58><c_78>`PS4
- **Rec↔GT gap**: correct item at beam rank 2, pred[0] prefix-depth only 0/3; platform consistent(PS4); in beam: share-a=1/10, share-(a,b)=1/10.
- **Beam diversity**: **Low** (collapsed to <a_123 family 9/10); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: Resident Evil: Revelat…, Resident Evil 4 - Play…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). target is a sensible DRIFT and **was caught**.

### #175 — Category-OK·item wrong · BEAM-COLLAPSE (<a_123×9/10)
- **History** (3 items; platforms PS4×3): Resident Evil: Revelations… | Resident Evil 4 - PlayStat… | Uncharted 4: A Thief's End…
- **GT**: `<a_131><b_210><c_0>` Fallout 4 - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_123><b_58><c_78>`PS4, `<a_123><b_100><c_33>`PS4, `<a_123><b_188><c_192>`PS4, `<a_123><b_142><c_36>`PS4, `<a_201><b_213><c_242>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_123 family 9/10); unique(a,b)=10/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Resident Evil: Revelat…, Resident Evil 4 - Play…, Uncharted 4: A Thief's…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #176 — Category-OK·item wrong · BEAM-COLLAPSE (<a_123×9/10)
- **History** (4 items; platforms PS4×4): Resident Evil: Revelations… | Resident Evil 4 - PlayStat… | Uncharted 4: A Thief's End… | Fallout 4 - PlayStation 4
- **GT**: `<a_24><b_96><c_27>` Rise of the Tomb Raider: 20 Year Celebration -… _(platform PS4)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_123><b_100><c_33>`PS4, `<a_201><b_213><c_242>`PS4, `<a_123><b_142><c_36>`PS4, `<a_123><b_188><c_192>`PS4, `<a_123><b_58><c_78>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_123 family 9/10); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Resident Evil: Revelat…, Resident Evil 4 - Play…, Uncharted 4: A Thief's…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #177 — Category-OK·item wrong · BEAM-COLLAPSE (<a_123×9/10)
- **History** (4 items; platforms XboxOne×4): Far Cry 4 - Xbox One | The Wolf Among Us - Xbox O… | DMC Devil May Cry: Definit… | Resident Evil 5 - Standard…
- **GT**: `<a_191><b_10><c_19>` Watch Dogs 2 - Xbox One _(platform XboxOne)_ ｜ **native**: `<a_123><b_72><c_191>` Far Cry 4 - Xbox One ✗
- **beam top5**: `<a_123><b_1><c_56>`Xbo, `<a_123><b_178><c_34>`?, `<a_123><b_145><c_171>`?, `<a_123><b_171><c_44>`Xbo, `<a_123><b_78><c_20>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_123 family 9/10); unique(a,b)=9/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Far Cry 4 - Xbox One, Resident Evil 5 - Stan…, The Wolf Among Us - Xb…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #178 — Category-OK·item wrong · BEAM-COLLAPSE (<a_162×10/10)
- **History** (1 items; platforms ?×1): Yoshi amiibo (Super Smash …
- **GT**: `<a_162><b_148><c_47>` Zero Suit Samus amiibo - Japan Import (Super S… _(platform ?)_ ｜ **native**: `<a_162><b_122><c_56>` Mario Modern Color Amiibo - Ja… ✗
- **beam top5**: `<a_162><b_219><c_174>`?, `<a_162><b_231><c_30>`?, `<a_162><b_218><c_126>`?, `<a_162><b_125><c_53>`?, `<a_162><b_219><c_249>`?
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; in beam: share-a=10/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_162 family 10/10); unique(a,b)=7/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 0/1 history items (coverage 0%); novel candidates=0 (**pure history restatement**); genre: action.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item. Note: target shares word(s) ['amiibo', 'bros', 'series', 'smash', 'super'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #179 — Category-OK·item wrong · BEAM-COLLAPSE (<a_162×8/10)
- **History** (2 items; platforms ?×2): Yoshi amiibo (Super Smash … | Zero Suit Samus amiibo - J…
- **GT**: `<a_162><b_60><c_17>` Wolf Link Amiibo Jp Model (The Legend of Zelda… _(platform ?)_ ｜ **native**: `<a_162><b_219><c_101>` Nintendo Super Smash Bros Palu… ✗
- **beam top5**: `<a_162><b_219><c_101>`?, `<a_162><b_219><c_233>`?, `<a_162><b_219><c_78>`?, `<a_162><b_139><c_171>`?, `<a_162><b_219><c_249>`?
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; in beam: share-a=8/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_162 family 8/10); unique(a,b)=5/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 0/2 history items (coverage 0%); novel candidates=0 (**pure history restatement**); genre: action,nostalg.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item. Note: target shares word(s) ['amiibo', 'series'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #180 — Category-OK·item wrong · BEAM-COLLAPSE (<a_162×10/10)
- **History** (3 items; platforms ?×3): Yoshi amiibo (Super Smash … | Zero Suit Samus amiibo - J… | Wolf Link Amiibo Jp Model …
- **GT**: `<a_162><b_2><c_193>` Nintendo Falco Amiibo - Wii U _(platform WiiU)_ ｜ **native**: `<a_162><b_122><c_56>` Mario Modern Color Amiibo - Ja… ✗
- **beam top5**: `<a_162><b_139><c_171>`?, `<a_162><b_219><c_233>`?, `<a_162><b_122><c_56>`?, `<a_162><b_85><c_94>`3DS, `<a_162><b_149><c_74>`3DS
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; in beam: share-a=10/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_162 family 10/10); unique(a,b)=8/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 0/3 history items (coverage 0%); novel candidates=0 (**pure history restatement**); genre: action.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item. Note: target shares word(s) ['amiibo'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #181 — Category-OK·item wrong · BEAM-COLLAPSE (<a_162×10/10)
- **History** (4 items; platforms ?×3,WiiU×1): Yoshi amiibo (Super Smash … | Zero Suit Samus amiibo - J… | Wolf Link Amiibo Jp Model … | Nintendo Falco Amiibo - Wi…
- **GT**: `<a_162><b_242><c_145>` Samus amiibo - Japan Import (Super Smash Bros … _(platform ?)_ ｜ **native**: `<a_162><b_122><c_56>` Mario Modern Color Amiibo - Ja… ✗
- **beam top5**: `<a_162><b_57><c_111>`Wii, `<a_162><b_52><c_132>`?, `<a_162><b_139><c_171>`?, `<a_162><b_122><c_56>`?, `<a_162><b_119><c_2>`?
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; in beam: share-a=10/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_162 family 10/10); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 0/4 history items (coverage 0%); novel candidates=0 (**pure history restatement**); templated opening; genre: action,nostalg.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item. Note: target shares word(s) ['amiibo', 'bros', 'import', 'japan', 'samus'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #182 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_162×10/10)
- **History** (5 items; platforms ?×4,WiiU×1): Yoshi amiibo (Super Smash … | Zero Suit Samus amiibo - J… | Wolf Link Amiibo Jp Model … | Nintendo Falco Amiibo - Wi… | Samus amiibo - Japan Impor…
- **GT**: `<a_250><b_12><c_83>` Mario - Gold amiibo (Super Mario Bros Series) _(platform ?)_ ｜ **native**: `<a_162><b_219><c_78>` Pit amiibo - Japan Import (Sup… ✗
- **beam top5**: `<a_162><b_57><c_111>`Wii, `<a_162><b_219><c_233>`?, `<a_162><b_219><c_78>`?, `<a_162><b_219><c_101>`?, `<a_162><b_219><c_249>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_162 family 10/10); unique(a,b)=4/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 0/5 history items (coverage 0%); novel candidates=0 (**pure history restatement**); templated opening; genre: action.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**. Note: target shares word(s) ['amiibo', 'bros', 'series', 'super'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #183 — Category-OK·item wrong · BEAM-COLLAPSE (<a_162×10/10)
- **History** (6 items; platforms ?×5,WiiU×1): Yoshi amiibo (Super Smash … | Zero Suit Samus amiibo - J… | Wolf Link Amiibo Jp Model … | Nintendo Falco Amiibo - Wi… | Samus amiibo - Japan Impor… | Mario - Gold amiibo (Super…
- **GT**: `<a_162><b_97><c_155>` Ness amiibo (Super Smash Bros Series) _(platform ?)_ ｜ **native**: `<a_162><b_219><c_78>` Pit amiibo - Japan Import (Sup… ✗
- **beam top5**: `<a_162><b_219><c_233>`?, `<a_162><b_57><c_111>`Wii, `<a_162><b_219><c_101>`?, `<a_162><b_219><c_78>`?, `<a_162><b_219><c_249>`?
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; in beam: share-a=10/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_162 family 10/10); unique(a,b)=3/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 2/6 history items (coverage 33%), anchored on: Yoshi amiibo (Super Sm…, Zero Suit Samus amiibo…; novel candidates=0 (**pure history restatement**); templated opening; genre: action.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item. Note: target shares word(s) ['amiibo', 'bros', 'series', 'smash', 'super'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #184 — Category-OK·item wrong
- **History** (3 items; platforms PS4×2,XboxOne×1): PlayStation 4 Universal Me… | Star Wars: Battlefront - S… | Xbox One S 2TB Console - L…
- **GT**: `<a_61><b_214><c_225>` PDP Talon Media Remote Control for Xbox One, T… _(platform XboxOne)_ ｜ **native**: `<a_7><b_248><c_176>` Xbox One S 500GB Console - Hal… ✗
- **beam top5**: `<a_7><b_248><c_176>`Xbo, `<a_7><b_248><c_16>`Xbo, `<a_7><b_56><c_74>`Xbo, `<a_39><b_77><c_105>`Xbo, `<a_201><b_151><c_255>`PS
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=9/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: PlayStation 4 Universa…, Star Wars: Battlefront…, Xbox One S 2TB Console…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,multiplayer,immersive.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**. Note: target shares word(s) ['media', 'remote'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #185 — Near-miss·same (a,b) subcluster, only c differs
- **History** (4 items; platforms PS4×2,XboxOne×2): PlayStation 4 Universal Me… | Star Wars: Battlefront - S… | Xbox One S 2TB Console - L… | PDP Talon Media Remote Con…
- **GT**: `<a_7><b_36><c_217>` Xbox One X 1TB Limited Edition Console - Proje… _(platform XboxOne)_ ｜ **native**: `<a_7><b_248><c_176>` Xbox One S 500GB Console - Hal… ✗
- **beam top5**: `<a_7><b_248><c_16>`Xbo, `<a_61><b_214><c_252>`Xbo, `<a_7><b_248><c_176>`Xbo, `<a_61><b_231><c_105>`Xbo, `<a_7><b_248><c_2>`Xbo
- **Rec↔GT gap**: beam's closest item shares (a,b) subcluster with GT, only c differs (same series/SKU), still missed; platform consistent(XboxOne); in beam: share-a=5/10, share-(a,b)=1/10.
- **Beam diversity**: **Medium** (2 a top-classes); unique(a,b)=6/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: PlayStation 4 Universa…, Star Wars: Battlefront…, Xbox One S 2TB Console…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,immersive,accessor.
- **Target sensibility (ceiling)**: target=SUBCLASS-continuation (score3); our pred[0]=CLASS-continuation (score2). user's pick is **more history-consistent** than our top-1 (target3>rec2) → we **drifted off** a catchable continuation. Note: target shares word(s) ['discontinued'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #186 — Category-miss·even top-class (a) wrong
- **History** (6 items; platforms PS4×4,?×1,PS×1): WWE 2K17 - PlayStation 4 | Horizon Zero Dawn - PlaySt… | Injustice 2 - PS4 [Digital… | The Wolf Among Us - PlaySt… | Sly 2: Band of Thieves | Sly 3 Honor Among Thieves …
- **GT**: `<a_205><b_32><c_66>` TrackMania Turbo - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_239><b_115><c_84>` Sly 3 Honor Among Thieves - Pl… ✗
- **beam top5**: `<a_239><b_157><c_47>`?, `<a_74><b_218><c_91>`PS3, `<a_239><b_115><c_84>`PS, `<a_233><b_21><c_136>`?, `<a_233><b_218><c_125>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=10/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 5/6 history items (coverage 83%), anchored on: Horizon Zero Dawn - Pl…, The Wolf Among Us - Pl…, Injustice 2 - PS4 [Dig…; novel candidates=0 (**pure history restatement**); genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=SUBCLASS-continuation (score3). we recommended something **more history-consistent** than the user's actual pick (rec3>target1) → **model too conservative / user more exploratory**.

### #187 — Category-miss·even top-class (a) wrong
- **History** (3 items; platforms PS×2,PC×1): PlayStation 2X Network Ada… | H.A.W.X. - PC DVD-Rom | PlayStation 2 Memory Card …
- **GT**: `<a_8><b_195><c_84>` Nyko Power Kit Plus - 2 Pack Rechargeable Batt… _(platform Xbox360)_ ｜ **native**: `<a_13><b_122><c_188>` Resistance: Burning Skies - Pl… ✗
- **beam top5**: `<a_249><b_170><c_61>`PS, `<a_13><b_134><c_245>`Xbo, `<a_13><b_194><c_173>`PS3, `<a_21><b_44><c_75>`PS2, `<a_13><b_247><c_57>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=Xbox360 vs rec=PS2); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=9/10, platforms=6, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: PlayStation 2X Network…, H.A.W.X. - PC DVD-Rom, PlayStation 2 Memory C…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,simulation,immersive.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #188 — Category-OK·item wrong
- **History** (10 items; platforms Xbox360×7,?×2,DS×1): Bioshock Infinite: The Com… | Madden NFL 17 - Standard E… | Two Worlds 2 - Xbox 360 | Singularity - Xbox 360 | Two Worlds II Official Str… | The Witcher 2: Assassins O…
- **GT**: `<a_24><b_252><c_227>` Too Human - Xbox 360 _(platform Xbox360)_ ｜ **native**: `<a_140><b_225><c_196>` Singularity - Xbox 360 ✗
- **beam top5**: `<a_140><b_225><c_196>`Xbo, `<a_141><b_227><c_21>`Xbo, `<a_140><b_160><c_117>`Xbo, `<a_194><b_72><c_187>`Xbo, `<a_194><b_15><c_1>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(Xbox360); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=10/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 6/10 history items (coverage 60%), anchored on: Dragon Age Origins: Ul…, The Witcher 2: Assassi…, Dead Space 2; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=SUBCLASS-continuation (score3). we recommended something **more history-consistent** than the user's actual pick (rec3>target1) → **model too conservative / user more exploratory**.

### #189 — Category-miss·even top-class (a) wrong
- **History** (5 items; platforms PS3×2,DS×2,3DS×1): Burnout Paradise - Playsta… | Namco Museum - Nintendo DS | Bejeweled 3 - Nintendo DS | 28-in 1 Blue Game Card Cas… | Dead Rising 2 - Playstatio…
- **GT**: `<a_24><b_86><c_212>` Uncharted: Drake's Fortune - Playstation 3 _(platform PS3)_ ｜ **native**: `<a_80><b_202><c_95>` Far Cry 3 - Playstation 3 ✗
- **beam top5**: `<a_80><b_69><c_85>`PS4, `<a_123><b_72><c_7>`PS4, `<a_80><b_202><c_95>`PS3, `<a_80><b_202><c_49>`?, `<a_123><b_72><c_238>`PS3
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS3 vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=7/10, platforms=5, unique titles=10/10.
- **Reasoning quality**: cites 5/5 history items (coverage 100%), anchored on: Burnout Paradise - Pla…, Namco Museum - Nintend…, Dead Rising 2 - Playst…; novel candidates=0 (**pure history restatement**); genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #190 — Hit@5 · RERANK-HARM · BEAM-COLLAPSE (<a_80×7/10)
- **History** (6 items; platforms PS3×3,DS×2,3DS×1): Burnout Paradise - Playsta… | Namco Museum - Nintendo DS | Bejeweled 3 - Nintendo DS | 28-in 1 Blue Game Card Cas… | Dead Rising 2 - Playstatio… | Uncharted: Drake's Fortune…
- **GT**: `<a_80><b_59><c_15>` Resident Evil 6 - Playstation 3 _(platform PS3)_ ｜ **native**: `<a_80><b_59><c_15>` Resident Evil 6 - Playstation … ✓
- **beam top5**: `<a_71><b_86><c_62>`PSV, `<a_80><b_69><c_85>`PS4, `<a_71><b_86><c_248>`PS3, `<a_80><b_202><c_95>`PS3, `<a_80><b_59><c_15>`PS3
- **Rec↔GT gap**: correct item at beam rank 5, pred[0] prefix-depth only 0/3; platform mismatch(GT=PS3 vs rec=PSVita); in beam: share-a=7/10, share-(a,b)=3/10.
- **Beam diversity**: **Low** (collapsed to <a_80 family 7/10); unique(a,b)=7/10, platforms=5, unique titles=10/10.
- **Reasoning quality**: cites 5/6 history items (coverage 83%), anchored on: Burnout Paradise - Pla…, Uncharted: Drake's For…, Bejeweled 3 - Nintendo…; novel candidates=0 (**pure history restatement**); genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=DRIFT (platform/word-linked) (score1). target is a sensible CLASS-cont and **was caught**.

### #191 — Category-OK·item wrong
- **History** (4 items; platforms ?×2,3DS×1,WiiU×1): Mario & Sonic at the Londo… | Mario & Sonic at the Rio 2… | Mario & Sonic at the Rio 2… | Super Mario Galaxy 2
- **GT**: `<a_193><b_0><c_61>` Mario & Sonic at the Sochi 2014 Olympic Winter… _(platform WiiU)_ ｜ **native**: `<a_193><b_40><c_126>` Sonic Riders Zero Gravity - Ni… ✗
- **beam top5**: `<a_193><b_219><c_226>`Gam, `<a_193><b_40><c_61>`Xbo, `<a_175><b_30><c_225>`?, `<a_193><b_240><c_28>`?, `<a_193><b_40><c_112>`Wii
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform mismatch(GT=WiiU vs rec=GameCube); in beam: share-a=6/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (2 a top-classes); unique(a,b)=6/10, platforms=5, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Mario & Sonic at the L…, Mario & Sonic at the R…, Mario & Sonic at the R…; novel candidates=0 (**pure history restatement**); genre: action,immersive,narrative.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item. Note: target shares word(s) ['at', 'mario', 'olympic', 'sonic'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #192 — Category-OK·item wrong · BEAM-COLLAPSE (<a_162×10/10)
- **History** (3 items; platforms GameBoy×1,?×1,WiiU×1): Hydra Performance&reg; Gam… | Sonic amiibo - Japan Impor… | Mario Party 10 + Mario ami…
- **GT**: `<a_162><b_5><c_144>` Nintendo NFC Reader/Writer Accessory - Nintend… _(platform 3DS)_ ｜ **native**: `<a_162><b_251><c_136>` Animal Crossing: amiibo Festiv… ✗
- **beam top5**: `<a_162><b_81><c_26>`?, `<a_162><b_251><c_136>`Wii, `<a_162><b_49><c_93>`?, `<a_162><b_231><c_30>`?, `<a_162><b_172><c_85>`?
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; in beam: share-a=10/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_162 family 10/10); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Hydra Performance&reg;…, Sonic amiibo - Japan I…, Mario Party 10 + Mario…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,multiplayer,nostalg.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item.

### #193 — Category-miss·even top-class (a) wrong
- **History** (4 items; platforms PS4×2,?×2): Okca&reg; Dual Charger Por… | DualShock 4 Wireless Contr… | Final Fantasy XIV Online: … | Assassin's Creed Chronicle…
- **GT**: `<a_201><b_151><c_255>` Playstation Plus: 3 Month Membership [Digital … _(platform PS-generic)_ ｜ **native**: `<a_118><b_185><c_102>` Batman: Arkham Knight - PlaySt… ✗
- **beam top5**: `<a_131><b_28><c_96>`PS4, `<a_131><b_210><c_0>`PS4, `<a_118><b_185><c_102>`PS4, `<a_118><b_150><c_122>`PS4, `<a_194><b_215><c_154>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS-generic vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=9/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Okca&reg; Dual Charger…, DualShock 4 Wireless C…, Assassin's Creed Chron…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,immersive,narrative.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item. Note: target shares word(s) ['code'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #194 — Category-miss·even top-class (a) wrong
- **History** (4 items; platforms 3DS×4): Meta Knight amiibo - Ninte… | Kirby: Planet Robobot - Ni… | King Dedede amiibo - Ninte… | Kirby amiibo - Nintendo 3D…
- **GT**: `<a_201><b_151><c_255>` Playstation Plus: 3 Month Membership [Digital … _(platform PS-generic)_ ｜ **native**: `<a_162><b_85><c_94>` Kirby amiibo - Nintendo 3DS ✗
- **beam top5**: `<a_162><b_105><c_210>`?, `<a_162><b_125><c_53>`?, `<a_162><b_85><c_94>`3DS, `<a_162><b_105><c_225>`?, `<a_239><b_142><c_92>`Wii
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=8/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Meta Knight amiibo - N…, King Dedede amiibo - N…, Kirby amiibo - Nintend…; novel candidates=0 (**pure history restatement**); genre: action,nostalg,exploration.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #195 — Category-OK·item wrong
- **History** (5 items; platforms 3DS×4,PS×1): Meta Knight amiibo - Ninte… | Kirby: Planet Robobot - Ni… | King Dedede amiibo - Ninte… | Kirby amiibo - Nintendo 3D… | Playstation Plus: 3 Month …
- **GT**: `<a_250><b_121><c_156>` Nintendo Selects: Super Mario 3D World _(platform ?)_ ｜ **native**: `<a_162><b_85><c_94>` Kirby amiibo - Nintendo 3DS ✗
- **beam top5**: `<a_162><b_105><c_210>`?, `<a_162><b_125><c_53>`?, `<a_162><b_85><c_94>`3DS, `<a_162><b_105><c_225>`?, `<a_250><b_92><c_44>`?
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; in beam: share-a=3/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=9/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 4/5 history items (coverage 80%), anchored on: Meta Knight amiibo - N…, King Dedede amiibo - N…, Kirby amiibo - Nintend…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,multiplayer.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #196 — Category-miss·even top-class (a) wrong
- **History** (5 items; platforms PS4×2,WiiU×1,?×1): Mario Kart 8 - Nintendo Wi… | Gen 2 x Extension Cable fo… | Fallout 4 - PlayStation 4 | Overwatch - Collector's Ed… | Controller Gear PS4 Contro…
- **GT**: `<a_7><b_36><c_217>` Xbox One X 1TB Limited Edition Console - Proje… _(platform XboxOne)_ ｜ **native**: `<a_131><b_224><c_68>` Overwatch - Origins Edition - … ✗
- **beam top5**: `<a_131><b_41><c_229>`PS4, `<a_201><b_151><c_255>`PS, `<a_131><b_224><c_68>`PS4, `<a_131><b_224><c_16>`PC, `<a_201><b_31><c_107>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=XboxOne vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (6 distinct a top-classes); unique(a,b)=9/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 4/5 history items (coverage 80%), anchored on: Mario Kart 8 - Nintend…, Fallout 4 - PlayStatio…, Overwatch - Collector'…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,racing.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #197 — Category-OK·item wrong
- **History** (1 items; platforms PC×1): Hyperkin "GN6" Premium Gen…
- **GT**: `<a_214><b_95><c_1>` Razer Naga Hex MOBA PC Gaming Mouse - Green _(platform PC)_ ｜ **native**: `<a_61><b_170><c_90>` Buffalo iBuffalo Classic USB G… ✗
- **beam top5**: `<a_61><b_0><c_187>`?, `<a_61><b_0><c_234>`?, `<a_61><b_170><c_90>`PC, `<a_214><b_24><c_0>`?, `<a_61><b_240><c_44>`PC
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; in beam: share-a=2/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=8/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 0/1 history items (coverage 0%); novel candidates=0 (**pure history restatement**); genre: nostalg,retro,peripheral.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #198 — Category-miss·even top-class (a) wrong
- **History** (2 items; platforms PC×2): Hyperkin "GN6" Premium Gen… | Razer Naga Hex MOBA PC Gam…
- **GT**: `<a_8><b_70><c_241>` Xbox One Play and Charge Kit _(platform XboxOne)_ ｜ **native**: `<a_61><b_0><c_234>` Logitech Gamepad F310 ✗
- **beam top5**: `<a_61><b_0><c_187>`?, `<a_61><b_167><c_197>`Xbo, `<a_61><b_131><c_197>`Xbo, `<a_214><b_95><c_29>`?, `<a_61><b_0><c_234>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=8/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: Hyperkin "GN6" Premium…, Razer Naga Hex MOBA PC…; novel candidates=0 (**pure history restatement**); genre: nostalg,retro,peripheral.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #199 — Category-OK·item wrong · BEAM-COLLAPSE (<a_61×10/10)
- **History** (3 items; platforms PC×2,XboxOne×1): Hyperkin "GN6" Premium Gen… | Razer Naga Hex MOBA PC Gam… | Xbox One Play and Charge K…
- **GT**: `<a_189><b_94><c_9>` Antec X-1 Cooler for Xbox One _(platform XboxOne)_ ｜ **native**: `<a_61><b_53><c_5>` Xbox One Wireless Controller a… ✗
- **beam top5**: `<a_61><b_53><c_5>`Xbo, `<a_61><b_167><c_197>`Xbo, `<a_61><b_217><c_168>`Xbo, `<a_61><b_131><c_197>`Xbo, `<a_61><b_167><c_164>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_61 family 10/10); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Hyperkin "GN6" Premium…, Razer Naga Hex MOBA PC…, Xbox One Play and Char…; novel candidates=0 (**pure history restatement**); genre: action,peripheral,accessor.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #200 — Hit@1 · BEAM-COLLAPSE (<a_61×8/10)
- **History** (4 items; platforms PC×2,XboxOne×2): Hyperkin "GN6" Premium Gen… | Razer Naga Hex MOBA PC Gam… | Xbox One Play and Charge K… | Antec X-1 Cooler for Xbox …
- **GT**: `<a_61><b_131><c_197>` Microsoft Xbox Wireless Adapter for Windows 10 _(platform Xbox)_ ｜ **native**: `<a_61><b_131><c_197>` Microsoft Xbox Wireless Adapte… ✓
- **beam top5**: `<a_61><b_131><c_197>`Xbo, `<a_61><b_167><c_197>`Xbo, `<a_61><b_167><c_164>`Xbo, `<a_61><b_53><c_5>`Xbo, `<a_202><b_16><c_110>`?
- **Rec↔GT gap**: top-1 exact hit.
- **Beam diversity**: **Low** (collapsed to <a_61 family 8/10); unique(a,b)=8/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Hyperkin "GN6" Premium…, Razer Naga Hex MOBA PC…, Xbox One Play and Char…; novel candidates=0 (**pure history restatement**); genre: action,peripheral.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). target is a sensible CLASS-cont and **was caught**.

### #201 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_61×9/10)
- **History** (5 items; platforms PC×2,XboxOne×2,Xbox×1): Hyperkin "GN6" Premium Gen… | Razer Naga Hex MOBA PC Gam… | Xbox One Play and Charge K… | Antec X-1 Cooler for Xbox … | Microsoft Xbox Wireless Ad…
- **GT**: `<a_106><b_68><c_238>` Shantae: Half-Genie Hero - Risky Beats Edition… _(platform PSVita)_ ｜ **native**: `<a_61><b_131><c_197>` Microsoft Xbox Wireless Adapte… ✗
- **beam top5**: `<a_61><b_131><c_197>`Xbo, `<a_61><b_167><c_197>`Xbo, `<a_61><b_111><c_109>`Xbo, `<a_61><b_167><c_164>`Xbo, `<a_61><b_214><c_225>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PSVita vs rec=Xbox); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_61 family 9/10); unique(a,b)=6/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 4/5 history items (coverage 80%), anchored on: Hyperkin "GN6" Premium…, Razer Naga Hex MOBA PC…, Xbox One Play and Char…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,peripheral,accessor.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=SUBCLASS-continuation (score3). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #202 — Category-miss·even top-class (a) wrong
- **History** (6 items; platforms PC×2,XboxOne×2,Xbox×1): Hyperkin "GN6" Premium Gen… | Razer Naga Hex MOBA PC Gam… | Xbox One Play and Charge K… | Antec X-1 Cooler for Xbox … | Microsoft Xbox Wireless Ad… | Shantae: Half-Genie Hero -…
- **GT**: `<a_193><b_177><c_13>` SEGA 3D Classics Collection - Nintendo 3DS _(platform 3DS)_ ｜ **native**: `<a_61><b_131><c_197>` Microsoft Xbox Wireless Adapte… ✗
- **beam top5**: `<a_61><b_167><c_197>`Xbo, `<a_61><b_131><c_197>`Xbo, `<a_106><b_68><c_238>`PSV, `<a_249><b_68><c_59>`PSV, `<a_1><b_150><c_189>`PS3
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=3DS vs rec=XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=10/10, platforms=5, unique titles=10/10.
- **Reasoning quality**: cites 6/6 history items (coverage 100%), anchored on: Hyperkin "GN6" Premium…, Razer Naga Hex MOBA PC…, Xbox One Play and Char…; novel candidates=0 (**pure history restatement**); genre: immersive,narrative,peripheral.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #203 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_61×7/10)
- **History** (7 items; platforms PC×2,XboxOne×2,Xbox×1): Razer Naga Hex MOBA PC Gam… | Xbox One Play and Charge K… | Antec X-1 Cooler for Xbox … | Microsoft Xbox Wireless Ad… | Shantae: Half-Genie Hero -… | SEGA 3D Classics Collectio…
- **GT**: `<a_1><b_163><c_179>` 7th Dragon III Code: VFD - Nintendo 3DS _(platform 3DS)_ ｜ **native**: `<a_61><b_131><c_197>` Microsoft Xbox Wireless Adapte… ✗
- **beam top5**: `<a_61><b_167><c_197>`Xbo, `<a_61><b_0><c_187>`?, `<a_61><b_131><c_197>`Xbo, `<a_61><b_167><c_164>`Xbo, `<a_61><b_111><c_109>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=3DS vs rec=XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_61 family 7/10); unique(a,b)=8/10, platforms=6, unique titles=10/10.
- **Reasoning quality**: cites 4/7 history items (coverage 57%), anchored on: Shantae: Half-Genie He…, SEGA 3D Classics Colle…, Hyperkin "GN6" Premium…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,nostalg,retro.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #204 — Category-miss·even top-class (a) wrong
- **History** (7 items; platforms XboxOne×4,PS4×3): Xbox One Special Edition D… | Tom Clancy's Rainbow Six S… | Sunset Overdrive Day One E… | Watch Dogs 2: Gold Edition… | No Man's Sky - PlayStation… | Attack on Titan - PlayStat…
- **GT**: `<a_13><b_218><c_173>` Agents of Mayhem - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_39><b_51><c_21>` Titanfall 2 - Xbox One ✗
- **beam top5**: `<a_39><b_77><c_105>`Xbo, `<a_39><b_51><c_21>`Xbo, `<a_123><b_58><c_16>`Xbo, `<a_39><b_51><c_188>`PS4, `<a_123><b_58><c_78>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS4 vs rec=XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=7/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/7 history items (coverage 57%), anchored on: Tom Clancy's Rainbow S…, No Man's Sky - PlaySta…, Sunset Overdrive Day O…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,shooter,multiplayer.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #205 — Category-OK·item wrong · BEAM-COLLAPSE (<a_61×9/10)
- **History** (4 items; platforms ?×2,XboxOne×1,Xbox×1): Azio Levetron L70 LED Back… | Steam Controller | Microsoft Xbox One Control… | Microsoft Xbox Wireless Ad…
- **GT**: `<a_202><b_164><c_89>` ASTRO Gaming A40 TR Headset + MixAmp Pro TR fo… _(platform XboxOne)_ ｜ **native**: `<a_61><b_131><c_197>` Microsoft Xbox Wireless Adapte… ✗
- **beam top5**: `<a_61><b_131><c_197>`Xbo, `<a_61><b_167><c_197>`Xbo, `<a_61><b_167><c_164>`Xbo, `<a_202><b_16><c_110>`?, `<a_61><b_111><c_109>`Xbo
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform mismatch(GT=XboxOne vs rec=Xbox); in beam: share-a=1/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_61 family 9/10); unique(a,b)=8/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 3/4 history items (coverage 75%), anchored on: Azio Levetron L70 LED …, Steam Controller, Microsoft Xbox Wireles…; novel candidates=0 (**pure history restatement**); genre: multiplayer,immersive,peripheral.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=SUBCLASS-continuation (score3). we recommended something **more history-consistent** than the user's actual pick (rec3>target2) → **model too conservative / user more exploratory**. Note: target shares word(s) ['gaming'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #206 — Near-miss·same (a,b) subcluster, only c differs · BEAM-COLLAPSE (<a_202×10/10)
- **History** (5 items; platforms ?×2,XboxOne×2,Xbox×1): Azio Levetron L70 LED Back… | Steam Controller | Microsoft Xbox One Control… | Microsoft Xbox Wireless Ad… | ASTRO Gaming A40 TR Headse…
- **GT**: `<a_202><b_50><c_6>` ASTRO Gaming A50 Wireless Dolby Gaming Headset… _(platform PS4)_ ｜ **native**: `<a_202><b_11><c_246>` Razer Naga Epic Chroma MMO Gam… ✗
- **beam top5**: `<a_202><b_86><c_197>`DS, `<a_202><b_11><c_246>`?, `<a_202><b_50><c_200>`DS, `<a_202><b_11><c_2>`DS, `<a_202><b_16><c_110>`?
- **Rec↔GT gap**: beam's closest item shares (a,b) subcluster with GT, only c differs (same series/SKU), still missed; in beam: share-a=10/10, share-(a,b)=1/10.
- **Beam diversity**: **Low** (collapsed to <a_202 family 10/10); unique(a,b)=8/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 4/5 history items (coverage 80%), anchored on: Azio Levetron L70 LED …, Steam Controller, Microsoft Xbox One Con…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,immersive,peripheral.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item. Note: target shares word(s) ['astro', 'black', 'gaming', 'headset', 'wireless'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #207 — Category-OK·item wrong
- **History** (1 items; platforms XboxOne×1): Grand Theft Auto V - Xbox …
- **GT**: `<a_131><b_2><c_39>` Borderlands: The Handsome Collection - Xbox On… _(platform XboxOne)_ ｜ **native**: `<a_39><b_69><c_69>` Call of Duty: Black Ops III - … ✗
- **beam top5**: `<a_39><b_69><c_69>`Xbo, `<a_131><b_155><c_206>`Xbo, `<a_231><b_117><c_187>`Xbo, `<a_80><b_69><c_85>`PS4, `<a_80><b_171><c_131>`Xbo
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform consistent(XboxOne); in beam: share-a=1/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (7 distinct a top-classes); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 0/1 history items (coverage 0%); novel candidates=0 (**pure history restatement**); genre: action,adventure,immersive.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item.

### #208 — Category-OK·item wrong
- **History** (2 items; platforms XboxOne×2): Grand Theft Auto V - Xbox … | Borderlands: The Handsome …
- **GT**: `<a_240><b_95><c_71>` Mafia III - Xbox One _(platform XboxOne)_ ｜ **native**: `<a_131><b_155><c_206>` Fallout 4 - Xbox One ✗
- **beam top5**: `<a_131><b_155><c_206>`Xbo, `<a_39><b_69><c_69>`Xbo, `<a_7><b_2><c_105>`Xbo, `<a_39><b_77><c_69>`Xbo, `<a_131><b_145><c_18>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=10/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: Grand Theft Auto V - X…, Borderlands: The Hands…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,multiplayer,immersive.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item.

### #209 — Hit@8
- **History** (3 items; platforms XboxOne×3): Grand Theft Auto V - Xbox … | Borderlands: The Handsome … | Mafia III - Xbox One
- **GT**: `<a_123><b_228><c_139>` Dead Rising 4 - Xbox One _(platform XboxOne)_ ｜ **native**: `<a_39><b_77><c_105>` Call of Duty: Infinite Warfare… ✗
- **beam top5**: `<a_39><b_77><c_105>`Xbo, `<a_39><b_51><c_21>`Xbo, `<a_123><b_76><c_255>`Xbo, `<a_39><b_77><c_69>`Xbo, `<a_123><b_188><c_70>`Xbo
- **Rec↔GT gap**: correct item at beam rank 8, pred[0] prefix-depth only 0/3; platform consistent(XboxOne); in beam: share-a=6/10, share-(a,b)=1/10.
- **Beam diversity**: **Medium** (2 a top-classes); unique(a,b)=9/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Grand Theft Auto V - X…, Borderlands: The Hands…, Mafia III - Xbox One; novel candidates=0 (**pure history restatement**); templated opening; genre: action,immersive,narrative.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). target is a sensible DRIFT and **was caught**.

### #210 — Hit@7 · BEAM-COLLAPSE (<a_123×10/10)
- **History** (4 items; platforms XboxOne×4): Grand Theft Auto V - Xbox … | Borderlands: The Handsome … | Mafia III - Xbox One | Dead Rising 4 - Xbox One
- **GT**: `<a_123><b_228><c_123>` Left 4 Dead - Xbox 360 _(platform Xbox360)_ ｜ **native**: `<a_123><b_76><c_255>` Far Cry Primal - Xbox One Stan… ✗
- **beam top5**: `<a_123><b_188><c_70>`Xbo, `<a_123><b_76><c_255>`Xbo, `<a_123><b_58><c_16>`Xbo, `<a_123><b_171><c_44>`Xbo, `<a_123><b_100><c_0>`Xbo
- **Rec↔GT gap**: correct item at beam rank 7, pred[0] prefix-depth only 1/3; platform mismatch(GT=Xbox360 vs rec=XboxOne); in beam: share-a=10/10, share-(a,b)=1/10.
- **Beam diversity**: **Low** (collapsed to <a_123 family 10/10); unique(a,b)=9/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Grand Theft Auto V - X…, Dead Rising 4 - Xbox O…, Borderlands: The Hands…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,horror,multiplayer.
- **Target sensibility (ceiling)**: target=SUBCLASS-continuation (score3); our pred[0]=CLASS-continuation (score2). target is a sensible SUBCLASS-cont and **was caught**.

### #211 — Category-OK·item wrong · BEAM-COLLAPSE (<a_162×10/10)
- **History** (4 items; platforms ?×2,3DS×2): Captain Falcon amiibo - Ja… | Meta Knight amiibo - Ninte… | Nintendo NFC Reader/Writer… | PDP Donkey Kong Display
- **GT**: `<a_162><b_60><c_17>` Wolf Link Amiibo Jp Model (The Legend of Zelda… _(platform ?)_ ｜ **native**: `<a_162><b_140><c_85>` Waddle Dee amiibo - Nintendo 3… ✗
- **beam top5**: `<a_162><b_118><c_196>`?, `<a_162><b_105><c_210>`?, `<a_162><b_140><c_85>`3DS, `<a_162><b_85><c_94>`3DS, `<a_162><b_5><c_144>`3DS
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; in beam: share-a=10/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_162 family 10/10); unique(a,b)=10/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Captain Falcon amiibo …, Meta Knight amiibo - N…, Nintendo NFC Reader/Wr…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,nostalg.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item. Note: target shares word(s) ['amiibo', 'series'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #212 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_162×10/10)
- **History** (5 items; platforms ?×3,3DS×2): Captain Falcon amiibo - Ja… | Meta Knight amiibo - Ninte… | Nintendo NFC Reader/Writer… | PDP Donkey Kong Display | Wolf Link Amiibo Jp Model …
- **GT**: `<a_119><b_147><c_182>` PDP Master Sword Stylus Display _(platform ?)_ ｜ **native**: `<a_162><b_85><c_94>` Kirby amiibo - Nintendo 3DS ✗
- **beam top5**: `<a_162><b_118><c_196>`?, `<a_162><b_140><c_85>`3DS, `<a_162><b_105><c_210>`?, `<a_162><b_85><c_94>`3DS, `<a_162><b_5><c_144>`3DS
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_162 family 10/10); unique(a,b)=10/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/5 history items (coverage 80%), anchored on: Captain Falcon amiibo …, Meta Knight amiibo - N…, Wolf Link Amiibo Jp Mo…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,accessor.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**. Note: target shares word(s) ['display', 'pdp'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #213 — Near-miss·same (a,b) subcluster, only c differs · BEAM-COLLAPSE (<a_162×10/10)
- **History** (4 items; platforms ?×3,PS4×1): Reflet amiibo - Japan Impo… | Lucina amiibo - Japan Impo… | Robot amiibo - Japan Impor… | Odin Sphere Leifthrasir: S…
- **GT**: `<a_162><b_119><c_40>` Amiibo Marth (Japanese import) _(platform ?)_ ｜ **native**: `<a_162><b_106><c_220>` Dark Pit amiibo - Japan Import… ✗
- **beam top5**: `<a_162><b_235><c_217>`?, `<a_162><b_21><c_210>`?, `<a_162><b_57><c_111>`Wii, `<a_162><b_125><c_53>`?, `<a_162><b_106><c_211>`?
- **Rec↔GT gap**: beam's closest item shares (a,b) subcluster with GT, only c differs (same series/SKU), still missed; in beam: share-a=10/10, share-(a,b)=2/10.
- **Beam diversity**: **Low** (collapsed to <a_162 family 10/10); unique(a,b)=7/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 3/4 history items (coverage 75%), anchored on: Reflet amiibo - Japan …, Lucina amiibo - Japan …, Odin Sphere Leifthrasi…; novel candidates=0 (**pure history restatement**); templated opening; genre: action.
- **Target sensibility (ceiling)**: target=SUBCLASS-continuation (score3); our pred[0]=CLASS-continuation (score2). user's pick is **more history-consistent** than our top-1 (target3>rec2) → we **drifted off** a catchable continuation. Note: target shares word(s) ['amiibo', 'import'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #214 — Hit@1
- **History** (4 items; platforms 3DS×3,DS×1): Shovel Knight - Nintendo 3… | Shin Megami Tensei: Strang… | Etrian Mystery Dungeon - N… | Kirby Triple Deluxe - Nint…
- **GT**: `<a_216><b_28><c_31>` Etrian Odyssey 2 Untold: The Fafnir Knight - N… _(platform 3DS)_ ｜ **native**: `<a_216><b_28><c_31>` Etrian Odyssey 2 Untold: The F… ✓
- **beam top5**: `<a_216><b_28><c_31>`3DS, `<a_216><b_92><c_163>`3DS, `<a_216><b_219><c_158>`3DS, `<a_216><b_28><c_41>`?, `<a_216><b_92><c_192>`3DS
- **Rec↔GT gap**: top-1 exact hit.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=6/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 3/4 history items (coverage 75%), anchored on: Shovel Knight - Ninten…, Etrian Mystery Dungeon…, Kirby Triple Deluxe - …; novel candidates=0 (**pure history restatement**); genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). target is a sensible CLASS-cont and **was caught**.

### #215 — Category-miss·even top-class (a) wrong
- **History** (10 items; platforms ?×4,PS3×4,PSP×1): Kingdom Hearts HD 2.5 ReMI… | WWE '13 | PSP Super Travel Case With… | Heavy Rain: Director's Cut… | The Sims 3 Island Paradise… | The Sims 3 Seasons
- **GT**: `<a_235><b_226><c_182>` Toy Story 2 _(platform ?)_ ｜ **native**: `<a_211><b_133><c_30>` Pokemon Alpha Sapphire - Ninte… ✗
- **beam top5**: `<a_22><b_173><c_203>`?, `<a_211><b_133><c_30>`3DS, `<a_22><b_252><c_160>`?, `<a_211><b_133><c_123>`3DS, `<a_211><b_31><c_95>`3DS
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=8/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 7/10 history items (coverage 70%), anchored on: Pokemon Stadium, The Sims 3 Seasons, MLB 13 The Show - Play…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,adventure,sports.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #216 — Category-OK·item wrong · BEAM-COLLAPSE (<a_39×8/10)
- **History** (4 items; platforms XboxOne×3,Xbox360×1): Fallout 4 - Xbox One | Xbox One Chatpad + Chat He… | Xbox One Play and Charge K… | Call of Duty 2 - Xbox 360
- **GT**: `<a_24><b_178><c_18>` Rise of the Tomb Raider - Xbox One _(platform XboxOne)_ ｜ **native**: `<a_39><b_182><c_109>` Call of Duty: Black Ops Combo … ✗
- **beam top5**: `<a_39><b_69><c_69>`Xbo, `<a_39><b_77><c_105>`Xbo, `<a_39><b_77><c_69>`Xbo, `<a_39><b_124><c_106>`?, `<a_39><b_40><c_248>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_39 family 8/10); unique(a,b)=9/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Fallout 4 - Xbox One, Call of Duty 2 - Xbox …, Xbox One Chatpad + Cha…; novel candidates=0 (**pure history restatement**); genre: action,shooter,immersive.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #217 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_80×7/10)
- **History** (6 items; platforms PS3×3,?×3): Heavenly Sword - Playstati… | Resistance: Fall of Man - … | Grand Theft Auto IV | Grand Theft Auto IV - Play… | Grand Theft Auto IV | Grand Theft Auto IV & Epis…
- **GT**: `<a_201><b_45><c_166>` Prey - Pre-load - PS4 Digital Code _(platform PS4)_ ｜ **native**: `<a_80><b_140><c_246>` Modnation Racers - PlayStation… ✗
- **beam top5**: `<a_80><b_202><c_49>`?, `<a_240><b_221><c_2>`PS3, `<a_240><b_40><c_2>`PS, `<a_80><b_140><c_246>`PS, `<a_80><b_69><c_76>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_80 family 7/10); unique(a,b)=8/10, platforms=5, unique titles=10/10.
- **Reasoning quality**: cites 5/6 history items (coverage 83%), anchored on: Heavenly Sword - Plays…, Resistance: Fall of Ma…, Grand Theft Auto IV; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=EXPLORATION (unrelated) (score0). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #218 — Category-miss·even top-class (a) wrong
- **History** (4 items; platforms PS3×3,?×1): No More Heroes: Heroes' Pa… | Dead Space (PlayStation 3) | Dead Space (PlayStation 3) | Dead Space 3 Limited Editi…
- **GT**: `<a_201><b_45><c_166>` Prey - Pre-load - PS4 Digital Code _(platform PS4)_ ｜ **native**: `<a_71><b_171><c_0>` Dead Space 3 Limited Edition ✗
- **beam top5**: `<a_80><b_59><c_29>`PS3, `<a_80><b_59><c_15>`PS3, `<a_71><b_202><c_11>`?, `<a_71><b_59><c_0>`?, `<a_80><b_171><c_8>`PS3
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS4 vs rec=PS3); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (2 a top-classes); unique(a,b)=6/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: No More Heroes: Heroes…, Dead Space (PlayStatio…, Dead Space 3 Limited E…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=DRIFT (platform/word-linked) (score1). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #219 — Category-miss·even top-class (a) wrong
- **History** (4 items; platforms XboxOne×1,Xbox×1,PC×1): Xbox One Wireless Controll… | Microsoft Xbox Wireless Ad… | Plants vs. Zombies Garden … | Playstation Plus: 3 Month …
- **GT**: `<a_202><b_120><c_89>` Logitech G900 Chaos Spectrum Professional Grad… _(platform ?)_ ｜ **native**: `<a_131><b_224><c_10>` Overwatch - Origins Edition - … ✗
- **beam top5**: `<a_61><b_167><c_197>`Xbo, `<a_61><b_131><c_197>`Xbo, `<a_131><b_224><c_16>`PC, `<a_61><b_111><c_109>`Xbo, `<a_131><b_224><c_10>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (2 a top-classes); unique(a,b)=8/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Xbox One Wireless Cont…, Microsoft Xbox Wireles…, Plants vs. Zombies Gar…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,adventure,multiplayer.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**. Note: target shares word(s) ['wireless'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #220 — Hit@1
- **History** (6 items; platforms PS4×4,XboxOne×2): Far Cry 4 - PlayStation 4 | Borderlands: The Handsome … | Microsoft Xbox One Elite | Quantum Break - Xbox One | Deus Ex: Mankind Divided -… | Uncharted 4: A Thief's End…
- **GT**: `<a_24><b_72><c_142>` Horizon Zero Dawn - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_24><b_72><c_142>`PS4, `<a_201><b_31><c_107>`PS4, `<a_39><b_51><c_188>`PS4, `<a_123><b_100><c_33>`PS4, `<a_39><b_51><c_21>`Xbo
- **Rec↔GT gap**: top-1 exact hit.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 5/6 history items (coverage 83%), anchored on: Far Cry 4 - PlayStatio…, Borderlands: The Hands…, Quantum Break - Xbox O…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). target is a sensible CLASS-cont and **was caught**.

### #221 — Category-OK·item wrong
- **History** (3 items; platforms PS4×3): Grand Theft Auto V - PlayS… | Uncharted 4: A Thief's End… | Fallout 4 - PlayStation 4
- **GT**: `<a_123><b_129><c_247>` Metal Gear Solid V: The Phantom Pain - PlaySta… _(platform PS4)_ ｜ **native**: `<a_201><b_213><c_242>` The Last of Us Remastered - Pl… ✗
- **beam top5**: `<a_131><b_155><c_206>`Xbo, `<a_123><b_72><c_7>`PS4, `<a_201><b_145><c_9>`PS4, `<a_201><b_213><c_242>`PS4, `<a_201><b_31><c_107>`PS4
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform mismatch(GT=PS4 vs rec=XboxOne); in beam: share-a=2/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=10/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Grand Theft Auto V - P…, Uncharted 4: A Thief's…, Fallout 4 - PlayStatio…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #222 — Category-OK·item wrong
- **History** (4 items; platforms PS4×4): Generic-3 Pack Combo Prote… | The Last of Us Remastered … | Plantronics GAMECOM 818 Wi… | Deadpool - PlayStation 4
- **GT**: `<a_86><b_12><c_93>` South Park: The Fractured but Whole - PlayStat… _(platform PS4)_ ｜ **native**: `<a_131><b_224><c_68>` Overwatch - Origins Edition - … ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_131><b_41><c_229>`PS4, `<a_131><b_209><c_151>`PS4, `<a_140><b_10><c_248>`PS4, `<a_92><b_68><c_129>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (6 distinct a top-classes); unique(a,b)=10/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: The Last of Us Remaste…, Generic-3 Pack Combo P…, Plantronics GAMECOM 81…; novel candidates=0 (**pure history restatement**); genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item.

### #223 — Category-miss·even top-class (a) wrong
- **History** (6 items; platforms 3DS×4,?×2): Pokemon Alpha Sapphire - N… | Nintendo 3DS Compatible wi… | HORI Screen Protective Fil… | Nintendo New 3DS XL - Blac… | Steam Controller | Razer Naga Epic Chroma MMO…
- **GT**: `<a_211><b_239><c_254>` YO-KAI WATCH 2: Fleshy Souls - Nintendo 3DS _(platform 3DS)_ ｜ **native**: `<a_202><b_11><c_2>` SteelSeries Siberia 200 Gaming… ✗
- **beam top5**: `<a_61><b_131><c_197>`Xbo, `<a_202><b_11><c_246>`?, `<a_202><b_58><c_107>`?, `<a_202><b_120><c_89>`?, `<a_61><b_167><c_197>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=3DS vs rec=Xbox); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (2 a top-classes); unique(a,b)=8/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 4/6 history items (coverage 67%), anchored on: Pokemon Alpha Sapphire…, Nintendo 3DS Compatibl…, HORI Screen Protective…; novel candidates=0 (**pure history restatement**); genre: immersive,portable,peripheral.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item.

### #224 — Category-miss·even top-class (a) wrong
- **History** (1 items; platforms 3DS×1): Nintendo 3DS Compatible wi…
- **GT**: `<a_216><b_112><c_119>` The Legend of Zelda: Majora's Mask 3D _(platform ?)_ ｜ **native**: `<a_113><b_235><c_2>` Nintendo New 3DS XL - Black ✗
- **beam top5**: `<a_113><b_235><c_2>`3DS, `<a_113><b_235><c_28>`3DS, `<a_119><b_168><c_182>`3DS, `<a_113><b_104><c_28>`3DS, `<a_113><b_31><c_38>`3DS
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=7/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 1/1 history items (coverage 100%), anchored on: Nintendo 3DS Compatibl…; novel candidates=0 (**pure history restatement**); genre: action,accessor.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #225 — Category-OK·item wrong · BEAM-COLLAPSE (<a_123×8/10)
- **History** (4 items; platforms PS4×3,PS3×1): Far Cry 4 - PS3 [Digital C… | Just Dance 2017 - PlayStat… | Mafia III - PlayStation 4 | Tom Clancy&rsquo;s Ghost R…
- **GT**: `<a_24><b_72><c_142>` Horizon Zero Dawn - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_123><b_58><c_78>`PS4, `<a_191><b_10><c_232>`PS4, `<a_123><b_142><c_36>`PS4, `<a_123><b_76><c_232>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_123 family 8/10); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Far Cry 4 - PS3 [Digit…, Mafia III - PlayStatio…, Just Dance 2017 - Play…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item.

### #226 — Category-miss·even top-class (a) wrong
- **History** (8 items; platforms ?×4,PS2×2,PS×1): Spyro the Dragon | Spyro 2: Ripto's Rage | Spyro: Year of the Dragon | Until Dawn - PlayStation 4 | Wireless Game Controller, … | CTR: Crash Team Racing
- **GT**: `<a_21><b_12><c_226>` Beastron A/V Cable for Nintendo Wii _(platform Wii)_ ｜ **native**: `<a_61><b_61><c_16>` Wireless Game Controller, Doub… ✗
- **beam top5**: `<a_61><b_61><c_203>`PS2, `<a_205><b_143><c_74>`?, `<a_233><b_44><c_175>`?, `<a_205><b_143><c_57>`?, `<a_233><b_201><c_25>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=Wii vs rec=PS2); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=7/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 6/8 history items (coverage 75%), anchored on: Spyro the Dragon, Spyro 2: Ripto's Rage, Spyro: Year of the Dra…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=SUBCLASS-continuation (score3). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #227 — Hit·repurchase/same-item (easy)
- **History** (9 items; platforms ?×4,PS2×2,PS×1): Spyro 2: Ripto's Rage | Spyro: Year of the Dragon | Until Dawn - PlayStation 4 | Wireless Game Controller, … | CTR: Crash Team Racing | Beastron A/V Cable for Nin…
- **GT**: `<a_21><b_12><c_226>` Beastron A/V Cable for Nintendo Wii _(platform Wii)_ ｜ **native**: `<a_21><b_12><c_226>` Beastron A/V Cable for Nintend… ✓
- **beam top5**: `<a_21><b_12><c_226>`Wii, `<a_21><b_125><c_39>`Wii, `<a_21><b_242><c_102>`Gam, `<a_219><b_57><c_168>`Gam, `<a_233><b_44><c_175>`?
- **Rec↔GT gap**: top-1 exact hit.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=9/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 5/9 history items (coverage 56%), anchored on: Spyro the Dragon, Spyro 2: Ripto's Rage, Buyee 128MB Memory Car…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=SUBCLASS-continuation (score3); our pred[0]=SUBCLASS-continuation (score3). target is a sensible SUBCLASS-cont and **was caught**.

### #228 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_175×8/10)
- **History** (9 items; platforms ?×7,PS3×1,Xbox360×1): Final Fantasy VII: Dirge o… | Heavenly Sword - Playstati… | Final Fantasy XIII-2 | Lightning Returns: Final F… | Final Fantasy Legend | Super Mario Bros. Deluxe
- **GT**: `<a_121><b_76><c_208>` Star Ocean: Integrity and Faithlessness - Play… _(platform PS4)_ ｜ **native**: `<a_175><b_24><c_11>` New Super Mario Bros ✗
- **beam top5**: `<a_175><b_24><c_11>`?, `<a_175><b_24><c_4>`Wii, `<a_194><b_24><c_128>`?, `<a_175><b_24><c_254>`?, `<a_175><b_113><c_236>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_175 family 8/10); unique(a,b)=5/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 6/9 history items (coverage 67%), anchored on: Final Fantasy X, Final Fantasy X-2, Heavenly Sword - Plays…; novel candidates=0 (**pure history restatement**); genre: action,adventure,role-playing.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=SUBCLASS-continuation (score3). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #229 — Category-miss·even top-class (a) wrong
- **History** (10 items; platforms PS4×4,PSVita×2,?×2): The Wolf Among Us | Samurai Warriors 4 Empires… | Warriors Orochi 3 Ultimate… | 7th Dragon III Code: VFD -… | Persona 5 - SteelBook Edit… | Mass Effect Andromeda - Pr…
- **GT**: `<a_7><b_156><c_24>` Turtle Beach - Ear Force X12 Amplified Stereo … _(platform Xbox360)_ ｜ **native**: `<a_1><b_150><c_189>` Legend of Heroes: Trails of Co… ✗
- **beam top5**: `<a_1><b_150><c_189>`PS3, `<a_1><b_177><c_70>`PSV, `<a_1><b_177><c_184>`PS4, `<a_1><b_116><c_233>`PS4, `<a_1><b_68><c_121>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=Xbox360 vs rec=PS3); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=8/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 5/10 history items (coverage 50%), anchored on: Tales of Hearts R (PSV…, 7th Dragon III Code: V…, Persona 5 - SteelBook …; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,immersive.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #230 — Hit@1
- **History** (7 items; platforms PS3×7): Resistance: Fall of Man - … | Fallout: New Vegas Ultimat… | Assassin's Creed IV Black … | The Evil Within - Playstat… | Dark Souls II - Playstatio… | BioShock Infinite - PS3 [D…
- **GT**: `<a_194><b_215><c_154>` Bloodborne _(platform ?)_ ｜ **native**: `<a_201><b_145><c_9>` The Witcher 3: Wild Hunt - Pla… ✗
- **beam top5**: `<a_194><b_215><c_154>`?, `<a_123><b_72><c_7>`PS4, `<a_201><b_145><c_9>`PS4, `<a_201><b_215><c_247>`PS4, `<a_123><b_72><c_238>`PS3
- **Rec↔GT gap**: top-1 exact hit.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=8/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 6/7 history items (coverage 86%), anchored on: Red Dead Redemption - …, Assassin's Creed IV Bl…, Resistance: Fall of Ma…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). target is a sensible CLASS-cont and **was caught**.

### #231 — Category-OK·item wrong
- **History** (5 items; platforms PS3×2,PS4×2,PS2×1): Red Dead Redemption - Play… | Hydra Performance Wireless… | Destiny: The Taken King - … | Far Cry Primal - PlayStati… | Fallout 4 - PlayStation 4
- **GT**: `<a_92><b_68><c_129>` Doom - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_131><b_210><c_0>` Fallout 4 - PlayStation 4 ✗
- **beam top5**: `<a_131><b_28><c_96>`PS4, `<a_123><b_72><c_7>`PS4, `<a_131><b_155><c_206>`Xbo, `<a_131><b_210><c_0>`PS4, `<a_201><b_145><c_9>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=9/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 4/5 history items (coverage 80%), anchored on: Red Dead Redemption - …, Destiny: The Taken Kin…, Far Cry Primal - PlayS…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #232 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_240×8/10)
- **History** (4 items; platforms Xbox360×2,?×2): Rise of the Tomb Raider - … | Forza Motorsport 3 - Xbox … | Tomb Raider: Underworld | GoldenEye 007: Reloaded
- **GT**: `<a_22><b_23><c_155>` Life is Strange - Xbox One _(platform XboxOne)_ ｜ **native**: `<a_240><b_87><c_195>` Max Payne 3 - Xbox 360 ✗
- **beam top5**: `<a_240><b_33><c_93>`?, `<a_240><b_87><c_195>`Xbo, `<a_240><b_87><c_41>`PS, `<a_240><b_221><c_2>`PS3, `<a_240><b_243><c_111>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_240 family 8/10); unique(a,b)=9/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 3/4 history items (coverage 75%), anchored on: Rise of the Tomb Raide…, Tomb Raider: Underworl…, GoldenEye 007: Reloade…; novel candidates=0 (**pure history restatement**); genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #233 — Category-OK·item wrong
- **History** (10 items; platforms PS4×5,XboxOne×5): FIFA 17 - Xbox One | FIFA 17 - PlayStation 4 | Battlefield Hardline Delux… | Mortal Kombat X - Xbox One | Just Dance Disney Party 2 … | Angry Birds: Star Wars - P…
- **GT**: `<a_74><b_115><c_116>` Injustice 2 - PS4 [Digital Code] _(platform PS4)_ ｜ **native**: `<a_245><b_193><c_0>` LEGO Jurassic World - Xbox One… ✗
- **beam top5**: `<a_245><b_193><c_0>`Xbo, `<a_22><b_2><c_8>`Xbo, `<a_123><b_76><c_255>`Xbo, `<a_74><b_5><c_203>`Xbo, `<a_245><b_121><c_92>`Xbo
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform mismatch(GT=PS4 vs rec=XboxOne); in beam: share-a=1/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=8/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 5/10 history items (coverage 50%), anchored on: Need for Speed - PlayS…, Fallout 4 - PlayStatio…, Battlefield Hardline D…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,racing,strategy.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #234 — Category-OK·item wrong
- **History** (3 items; platforms ?×2,PS4×1): Logitech Gamepad F310 | Logitech Gamepad F710 | Metal Gear Solid V: The Ph…
- **GT**: `<a_194><b_36><c_254>` Final Fantasy XV - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_118><b_233><c_76>` Tom Clancy's The Division - Pl… ✗
- **beam top5**: `<a_123><b_72><c_7>`PS4, `<a_131><b_210><c_0>`PS4, `<a_118><b_233><c_76>`PS4, `<a_201><b_213><c_242>`PS4, `<a_118><b_233><c_3>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 0/3 history items (coverage 0%); novel candidates=0 (**pure history restatement**); genre: immersive,narrative,peripheral.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #235 — Hit@4
- **History** (4 items; platforms ?×2,PS4×2): Logitech Gamepad F310 | Logitech Gamepad F710 | Metal Gear Solid V: The Ph… | Final Fantasy XV - PlaySta…
- **GT**: `<a_201><b_31><c_107>` Uncharted 4: A Thief's End - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_194><b_15><c_66>` Dishonored 2 - PlayStation 4 ✗
- **beam top5**: `<a_123><b_100><c_33>`PS4, `<a_201><b_213><c_242>`PS4, `<a_201><b_18><c_56>`PS4, `<a_201><b_31><c_107>`PS4, `<a_194><b_15><c_66>`PS4
- **Rec↔GT gap**: correct item at beam rank 4, pred[0] prefix-depth only 0/3; platform consistent(PS4); in beam: share-a=3/10, share-(a,b)=1/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 2/4 history items (coverage 50%), anchored on: Metal Gear Solid V: Th…, Final Fantasy XV - Pla…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,immersive,narrative.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). target is a sensible DRIFT and **was caught**.

### #236 — Category-OK·item wrong
- **History** (5 items; platforms PS4×3,?×2): Logitech Gamepad F310 | Logitech Gamepad F710 | Metal Gear Solid V: The Ph… | Final Fantasy XV - PlaySta… | Uncharted 4: A Thief's End…
- **GT**: `<a_200><b_7><c_144>` DMC Devil May Cry: Definitive Edition - PlaySt… _(platform PS4)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_201><b_18><c_56>`PS4, `<a_123><b_100><c_33>`PS4, `<a_201><b_213><c_242>`PS4, `<a_194><b_15><c_66>`PS4, `<a_131><b_209><c_151>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=9/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 5/5 history items (coverage 100%), anchored on: Metal Gear Solid V: Th…, Final Fantasy XV - Pla…, Uncharted 4: A Thief's…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #237 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_49×10/10)
- **History** (8 items; platforms ?×5,3DS×1,Xbox360×1): Disney Infinity 3.0 Editio… | Disney Infinity 3.0 Editon… | Disney Infinity 3.0 Editio… | Disney Infinity 3.0 Editio… | Disney Infinity 3.0 Editio… | Disney Infinty Cars Playse…
- **GT**: `<a_74><b_100><c_233>` Minecraft _(platform ?)_ ｜ **native**: `<a_49><b_110><c_219>` Disney Infinity 3.0 Edition: S… ✗
- **beam top5**: `<a_49><b_110><c_219>`?, `<a_49><b_125><c_112>`?, `<a_49><b_94><c_203>`?, `<a_49><b_119><c_95>`?, `<a_49><b_110><c_128>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_49 family 10/10); unique(a,b)=6/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 4/8 history items (coverage 50%), anchored on: Disney Infinity 3.0 Ed…, Disney Infinity 3.0 Ed…, Disney Infinity 3.0 Ed…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,immersive,narrative.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #238 — Category-OK·item wrong
- **History** (6 items; platforms PS4×6): NHL 16 - PlayStation 4 | Mega Man Legacy Collection… | The Last of Us Remastered … | Grand Theft Auto V - PlayS… | Call of Duty: Black Ops II… | DualShock 4 Wireless Contr…
- **GT**: `<a_201><b_151><c_255>` Playstation Plus: 3 Month Membership [Digital … _(platform PS-generic)_ ｜ **native**: `<a_201><b_169><c_181>` PlayStation 4 500GB Console - … ✗
- **beam top5**: `<a_61><b_251><c_144>`PS4, `<a_201><b_169><c_181>`PS4, `<a_201><b_169><c_103>`PS4, `<a_131><b_210><c_0>`PS4, `<a_201><b_2><c_102>`PS4
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform mismatch(GT=PS-generic vs rec=PS4); in beam: share-a=5/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=8/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 4/6 history items (coverage 67%), anchored on: NHL 16 - PlayStation 4, The Last of Us Remaste…, Grand Theft Auto V - P…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=SUBCLASS-continuation (score3). we recommended something **more history-consistent** than the user's actual pick (rec3>target2) → **model too conservative / user more exploratory**. Note: target shares word(s) ['code', 'digital'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #239 — Category-OK·item wrong · BEAM-COLLAPSE (<a_249×7/10)
- **History** (6 items; platforms PSVita×4,PS3×1,PS4×1): CTA Digital PS Vita Travel… | PS Vita 2000 Trigger Grip … | Mortal Kombat - PlayStatio… | Sony PlayStation Vita WiFi | Sony Playstation PS3 Duals… | Tekken 7 -  PS4 Digital Co…
- **GT**: `<a_195><b_67><c_23>` Sly Cooper: Thieves in Time - PS Vita [Digital… _(platform PSVita)_ ｜ **native**: `<a_249><b_68><c_59>` 16GB PlayStation Vita Memory C… ✗
- **beam top5**: `<a_249><b_68><c_59>`PSV, `<a_249><b_180><c_74>`PSV, `<a_200><b_168><c_118>`PS3, `<a_249><b_134><c_162>`PSV, `<a_200><b_7><c_144>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PSVita); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_249 family 7/10); unique(a,b)=10/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 4/6 history items (coverage 67%), anchored on: CTA Digital PS Vita Tr…, PS Vita 2000 Trigger G…, Mortal Kombat - PlaySt…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,fighting,immersive.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**. Note: target shares word(s) ['code', 'digital'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #240 — Category-OK·item wrong · BEAM-COLLAPSE (<a_119×10/10)
- **History** (4 items; platforms PS4×3,WiiU×1): Junsi Kingdom Hearts Body … | Wii U Gamepad Silicone Jac… | SQDeal Dust Proof Dust Pre… | Grip-iT Analog Stick Cover…
- **GT**: `<a_119><b_168><c_182>` HORI Screen Protective Filter for Nintendo NEW… _(platform 3DS)_ ｜ **native**: `<a_119><b_217><c_221>` Grip-iT Analog Stick Covers, S… ✗
- **beam top5**: `<a_119><b_93><c_19>`Wii, `<a_119><b_181><c_184>`Xbo, `<a_119><b_29><c_3>`Xbo, `<a_119><b_29><c_206>`PS4, `<a_119><b_217><c_221>`?
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform mismatch(GT=3DS vs rec=WiiU); in beam: share-a=10/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_119 family 10/10); unique(a,b)=8/10, platforms=5, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Junsi Kingdom Hearts B…, Wii U Gamepad Silicone…, SQDeal Dust Proof Dust…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,accessor.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item.

### #241 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_45×10/10)
- **History** (10 items; platforms PS4×6,XboxOne×3,Xbox360×1): Call of Duty: Infinite War… | Call of Duty: Infinite War… | Call Of Duty: Infinite War… | Call of Duty: Infinite War… | Call of Duty: Advanced War… | NBA 2K15 - Xbox 360
- **GT**: `<a_205><b_208><c_148>` Gran Turismo Sport - Limited Edition - PlaySta… _(platform PS4)_ ｜ **native**: `<a_45><b_168><c_146>` NBA 2K17 - Legend Edition - Xb… ✗
- **beam top5**: `<a_45><b_168><c_146>`Xbo, `<a_45><b_246><c_5>`PS4, `<a_45><b_168><c_2>`PS4, `<a_45><b_3><c_16>`Xbo, `<a_45><b_18><c_254>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS4 vs rec=XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_45 family 10/10); unique(a,b)=5/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/10 history items (coverage 40%), anchored on: Battlefield 1 - PlaySt…, Call of Duty: Infinite…, Call Of Duty: Infinite…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,shooter,sports.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=SUBCLASS-continuation (score3). we recommended something **more history-consistent** than the user's actual pick (rec3>target1) → **model too conservative / user more exploratory**.

### #242 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_123×8/10)
- **History** (6 items; platforms PS4×6): Uncharted 4: A Thief's End… | The Evil Within - PlayStat… | The Witcher 3: Wild Hunt -… | Deus Ex: Mankind Divided -… | Rise of the Tomb Raider: 2… | Resident Evil 7: Biohazard…
- **GT**: `<a_194><b_36><c_254>` Final Fantasy XV - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_123><b_58><c_16>` Resident Evil 7 Biohazard - Xb… ✗
- **beam top5**: `<a_123><b_58><c_16>`Xbo, `<a_24><b_72><c_142>`PS4, `<a_123><b_100><c_33>`PS4, `<a_123><b_44><c_0>`PS4, `<a_123><b_142><c_36>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS4 vs rec=XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_123 family 8/10); unique(a,b)=8/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 5/6 history items (coverage 83%), anchored on: Uncharted 4: A Thief's…, The Evil Within - Play…, Resident Evil 7: Bioha…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=SUBCLASS-continuation (score3). we recommended something **more history-consistent** than the user's actual pick (rec3>target1) → **model too conservative / user more exploratory**.

### #243 — Category-miss·even top-class (a) wrong
- **History** (8 items; platforms XboxOne×6,3DS×2): Turtle Beach - Ear Force X… | Xbox One Limited Edition H… | Bravely Second: End Layer … | Final Fantasy XV - Xbox On… | Pok&eacute;mon Sun - Ninte… | NHL 17 - Xbox One
- **GT**: `<a_121><b_155><c_99>` NieR: Automata - Playstation 4 _(platform PS4)_ ｜ **native**: `<a_45><b_28><c_168>` FIFA 17 - PlayStation 4 ✗
- **beam top5**: `<a_39><b_77><c_105>`Xbo, `<a_39><b_51><c_21>`Xbo, `<a_45><b_28><c_168>`PS4, `<a_45><b_168><c_109>`Xbo, `<a_191><b_10><c_19>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS4 vs rec=XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=8/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 6/8 history items (coverage 75%), anchored on: NHL 16 - Xbox One, NHL 17 - Xbox One, Halo 5 Guardians - Xbo…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,sports.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=DRIFT (platform/word-linked) (score1). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #244 — Category-OK·item wrong
- **History** (4 items; platforms PS4×4): Doom - PlayStation 4 | Transformers Devastation -… | Tom Clancy's The Division … | Battlefield 1 - PlayStatio…
- **GT**: `<a_24><b_72><c_142>` Horizon Zero Dawn - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_39><b_51><c_188>` Titanfall 2 - PlayStation 4 ✗
- **beam top5**: `<a_39><b_51><c_188>`PS4, `<a_39><b_77><c_105>`Xbo, `<a_39><b_51><c_21>`Xbo, `<a_123><b_100><c_33>`PS4, `<a_39><b_78><c_205>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=7/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 3/4 history items (coverage 75%), anchored on: Doom - PlayStation 4, Battlefield 1 - PlaySt…, Tom Clancy's The Divis…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,shooter,multiplayer.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #245 — Category-OK·item wrong
- **History** (5 items; platforms PS4×5): Doom - PlayStation 4 | Transformers Devastation -… | Tom Clancy's The Division … | Battlefield 1 - PlayStatio… | Horizon Zero Dawn - PlaySt…
- **GT**: `<a_123><b_10><c_33>` Wolfenstein: The Old Blood - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_39><b_51><c_188>`PS4, `<a_201><b_31><c_107>`PS4, `<a_201><b_18><c_56>`PS4, `<a_123><b_100><c_33>`PS4, `<a_123><b_58><c_78>`PS4
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform consistent(PS4); in beam: share-a=3/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=10/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 3/5 history items (coverage 60%), anchored on: Doom - PlayStation 4, Horizon Zero Dawn - Pl…, Battlefield 1 - PlaySt…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #246 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_61×10/10)
- **History** (5 items; platforms XboxOne×2,?×1,Xbox×1): Xbox One Chatpad + Chat He… | Logitech G602 Lag-Free Wir… | Xbox One Wireless Controll… | Microsoft Xbox Wireless Ad… | DualShock 4 Wireless Contr…
- **GT**: `<a_162><b_125><c_53>` Yoshi amiibo (Super Smash Bros Series) _(platform ?)_ ｜ **native**: `<a_61><b_131><c_197>` Microsoft Xbox Wireless Adapte… ✗
- **beam top5**: `<a_61><b_167><c_197>`Xbo, `<a_61><b_131><c_197>`Xbo, `<a_61><b_44><c_172>`PS4, `<a_61><b_251><c_144>`PS4, `<a_61><b_170><c_90>`PC
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_61 family 10/10); unique(a,b)=8/10, platforms=5, unique titles=10/10.
- **Reasoning quality**: cites 5/5 history items (coverage 100%), anchored on: Xbox One Chatpad + Cha…, Logitech G602 Lag-Free…, Xbox One Wireless Cont…; novel candidates=0 (**pure history restatement**); genre: peripheral,accessor,controller.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #247 — Category-OK·item wrong · BEAM-COLLAPSE (<a_162×10/10)
- **History** (6 items; platforms XboxOne×2,?×2,Xbox×1): Xbox One Chatpad + Chat He… | Logitech G602 Lag-Free Wir… | Xbox One Wireless Controll… | Microsoft Xbox Wireless Ad… | DualShock 4 Wireless Contr… | Yoshi amiibo (Super Smash …
- **GT**: `<a_162><b_130><c_72>` Nintendo Boo amiibo (SM Series) - Nintendo Wii… _(platform WiiU)_ ｜ **native**: `<a_162><b_122><c_56>` Mario Modern Color Amiibo - Ja… ✗
- **beam top5**: `<a_162><b_231><c_30>`?, `<a_162><b_49><c_93>`?, `<a_162><b_180><c_145>`?, `<a_162><b_2><c_170>`?, `<a_162><b_242><c_145>`?
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; in beam: share-a=10/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_162 family 10/10); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 3/6 history items (coverage 50%), anchored on: Xbox One Chatpad + Cha…, Microsoft Xbox Wireles…, Yoshi amiibo (Super Sm…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,accessor,controller.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item. Note: target shares word(s) ['amiibo', 'series'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #248 — Category-miss·even top-class (a) wrong
- **History** (1 items; platforms DS×1): PlayStation Gold Wireless …
- **GT**: `<a_194><b_87><c_112>` Dark Souls III - PlayStation 4 Standard Editio… _(platform PS4)_ ｜ **native**: `<a_7><b_248><c_2>` Xbox One Limited Edition Halo … ✗
- **beam top5**: `<a_7><b_248><c_16>`Xbo, `<a_7><b_248><c_177>`Xbo, `<a_7><b_248><c_2>`Xbo, `<a_7><b_2><c_105>`Xbo, `<a_7><b_36><c_0>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS4 vs rec=XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (2 a top-classes); unique(a,b)=7/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 0/1 history items (coverage 0%); novel candidates=0 (**pure history restatement**); genre: multiplayer,immersive,peripheral.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #249 — Category-miss·even top-class (a) wrong
- **History** (2 items; platforms DS×1,PS4×1): PlayStation Gold Wireless … | Dark Souls III - PlayStati…
- **GT**: `<a_45><b_246><c_5>` EA Sports UFC 2 - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_194><b_87><c_249>` Dark Souls III: Day 1 Edition … ✗
- **beam top5**: `<a_194><b_215><c_154>`?, `<a_194><b_87><c_249>`PS4, `<a_194><b_87><c_220>`PS4, `<a_131><b_209><c_151>`PS4, `<a_131><b_210><c_0>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (2 a top-classes); unique(a,b)=8/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: Dark Souls III - PlayS…, PlayStation Gold Wirel…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,immersive.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #250 — Hit@6 · BEAM-COLLAPSE (<a_45×8/10)
- **History** (3 items; platforms PS4×2,DS×1): PlayStation Gold Wireless … | Dark Souls III - PlayStati… | EA Sports UFC 2 - PlayStat…
- **GT**: `<a_45><b_28><c_168>` FIFA 17 - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_45><b_168><c_146>` NBA 2K17 - Legend Edition - Xb… ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_45><b_168><c_1>`Xbo, `<a_45><b_168><c_2>`PS4, `<a_45><b_168><c_109>`Xbo, `<a_45><b_168><c_146>`Xbo
- **Rec↔GT gap**: correct item at beam rank 6, pred[0] prefix-depth only 0/3; platform consistent(PS4); in beam: share-a=8/10, share-(a,b)=1/10.
- **Beam diversity**: **Low** (collapsed to <a_45 family 8/10); unique(a,b)=7/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: PlayStation Gold Wirel…, Dark Souls III - PlayS…, EA Sports UFC 2 - Play…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,sports.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=DRIFT (platform/word-linked) (score1). target is a sensible CLASS-cont and **was caught**.

### #251 — Category-OK·item wrong · BEAM-COLLAPSE (<a_45×8/10)
- **History** (4 items; platforms PS4×3,DS×1): PlayStation Gold Wireless … | Dark Souls III - PlayStati… | EA Sports UFC 2 - PlayStat… | FIFA 17 - PlayStation 4
- **GT**: `<a_131><b_175><c_170>` For Honor: Deluxe Edition (Includes Extra Cont… _(platform PS4)_ ｜ **native**: `<a_45><b_28><c_168>` FIFA 17 - PlayStation 4 ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_45><b_168><c_2>`PS4, `<a_45><b_193><c_4>`PS4, `<a_45><b_10><c_13>`PS4, `<a_45><b_28><c_168>`PS4
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform consistent(PS4); in beam: share-a=1/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_45 family 8/10); unique(a,b)=8/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 2/4 history items (coverage 50%), anchored on: Dark Souls III - PlayS…, FIFA 17 - PlayStation …; novel candidates=0 (**pure history restatement**); templated opening; genre: action,sports,strategy.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item.

### #252 — Category-miss·even top-class (a) wrong
- **History** (5 items; platforms PS4×4,DS×1): PlayStation Gold Wireless … | Dark Souls III - PlayStati… | EA Sports UFC 2 - PlayStat… | FIFA 17 - PlayStation 4 | For Honor: Deluxe Edition …
- **GT**: `<a_8><b_193><c_132>` ACC PS4 DUALSHOCK 4 CHARGING STATION BY SONY #… _(platform PS4)_ ｜ **native**: `<a_39><b_51><c_188>` Titanfall 2 - PlayStation 4 ✗
- **beam top5**: `<a_39><b_175><c_240>`Xbo, `<a_39><b_51><c_188>`PS4, `<a_39><b_51><c_21>`Xbo, `<a_39><b_51><c_170>`PC, `<a_45><b_168><c_2>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS4 vs rec=XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=7/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 3/5 history items (coverage 60%), anchored on: Dark Souls III - PlayS…, EA Sports UFC 2 - Play…, For Honor: Deluxe Edit…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=EXPLORATION (unrelated) (score0). user's pick is **more history-consistent** than our top-1 (target1>rec0) → we **drifted off** a catchable continuation.

### #253 — Category-OK·item wrong
- **History** (6 items; platforms PS4×5,DS×1): PlayStation Gold Wireless … | Dark Souls III - PlayStati… | EA Sports UFC 2 - PlayStat… | FIFA 17 - PlayStation 4 | For Honor: Deluxe Edition … | ACC PS4 DUALSHOCK 4 CHARGI…
- **GT**: `<a_201><b_134><c_202>` 500GB PlayStation 4 Console - Batman Arkham Kn… _(platform PS4)_ ｜ **native**: `<a_45><b_28><c_168>` FIFA 17 - PlayStation 4 ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_123><b_58><c_78>`PS4, `<a_39><b_51><c_188>`PS4, `<a_39><b_175><c_240>`Xbo, `<a_191><b_10><c_232>`PS4
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform consistent(PS4); in beam: share-a=1/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (6 distinct a top-classes); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/6 history items (coverage 67%), anchored on: Dark Souls III - PlayS…, EA Sports UFC 2 - Play…, FIFA 17 - PlayStation …; novel candidates=0 (**pure history restatement**); templated opening; genre: action,shooter,sports.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item.

### #254 — Category-OK·item wrong
- **History** (9 items; platforms XboxOne×8,Xbox360×1): Fallout 4 - Xbox One | Far Cry Primal - Xbox One … | Rise of the Tomb Raider - … | Tom Clancy&rsquo;s Ghost R… | Unravel - Xbox One Digital… | ReCore - Xbox One
- **GT**: `<a_191><b_78><c_53>` Just Cause 3 - Xbox One Digital Code _(platform XboxOne)_ ｜ **native**: `<a_123><b_228><c_139>` Dead Rising 4 - Xbox One ✗
- **beam top5**: `<a_123><b_58><c_16>`Xbo, `<a_24><b_72><c_142>`PS4, `<a_123><b_188><c_70>`Xbo, `<a_24><b_129><c_118>`Xbo, `<a_24><b_185><c_47>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=10/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 6/9 history items (coverage 67%), anchored on: Rise of the Tomb Raide…, Rise of the Tomb Raide…, Far Cry 4 - Xbox One; novel candidates=0 (**pure history restatement**); genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**. Note: target shares word(s) ['code', 'digital'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #255 — Category-OK·item wrong · BEAM-COLLAPSE (<a_45×10/10)
- **History** (3 items; platforms PS4×3): Ratchet & Clank - PlayStat… | Uncharted 4: A Thief's End… | MLB The Show 16 - PlayStat…
- **GT**: `<a_123><b_100><c_33>` Tom Clancy&rsquo;s Ghost Recon Wildlands - Pla… _(platform PS4)_ ｜ **native**: `<a_45><b_28><c_168>` FIFA 17 - PlayStation 4 ✗
- **beam top5**: `<a_45><b_168><c_2>`PS4, `<a_45><b_107><c_83>`PS4, `<a_45><b_28><c_168>`PS4, `<a_45><b_226><c_3>`PS4, `<a_45><b_168><c_24>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_45 family 10/10); unique(a,b)=8/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Ratchet & Clank - Play…, Uncharted 4: A Thief's…, MLB The Show 16 - Play…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #256 — Category-OK·item wrong
- **History** (4 items; platforms PS4×4): Ratchet & Clank - PlayStat… | Uncharted 4: A Thief's End… | MLB The Show 16 - PlayStat… | Tom Clancy&rsquo;s Ghost R…
- **GT**: `<a_205><b_208><c_188>` Gran Turismo Sport - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_123><b_142><c_36>` 7 Days to Die - PlayStation 4 ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_123><b_142><c_36>`PS4, `<a_123><b_58><c_78>`PS4, `<a_123><b_76><c_232>`PS4, `<a_123><b_2><c_26>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=9/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 3/4 history items (coverage 75%), anchored on: Uncharted 4: A Thief's…, Tom Clancy&rsquo;s Gho…, MLB The Show 16 - Play…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item.

### #257 — Category-OK·item wrong · BEAM-COLLAPSE (<a_205×9/10)
- **History** (5 items; platforms PS4×5): Ratchet & Clank - PlayStat… | Uncharted 4: A Thief's End… | MLB The Show 16 - PlayStat… | Tom Clancy&rsquo;s Ghost R… | Gran Turismo Sport - PlayS…
- **GT**: `<a_205><b_208><c_148>` Gran Turismo Sport - Limited Edition - PlaySta… _(platform PS4)_ ｜ **native**: `<a_205><b_207><c_181>` DiRT Rally - PlayStation 4 ✗
- **beam top5**: `<a_205><b_8><c_170>`PS4, `<a_205><b_111><c_114>`PS4, `<a_205><b_207><c_181>`PS4, `<a_205><b_60><c_93>`PS4, `<a_205><b_8><c_38>`PS4
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform consistent(PS4); in beam: share-a=9/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_205 family 9/10); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/5 history items (coverage 80%), anchored on: Uncharted 4: A Thief's…, Tom Clancy&rsquo;s Gho…, MLB The Show 16 - Play…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=SUBCLASS-continuation (score3); our pred[0]=CLASS-continuation (score2). user's pick is **more history-consistent** than our top-1 (target3>rec2) → we **drifted off** a catchable continuation. Note: target shares word(s) ['gran', 'sport', 'turismo'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #258 — Hit@1 · BEAM-COLLAPSE (<a_216×7/10)
- **History** (1 items; platforms 3DS×1): Fire Emblem Fates: Conques…
- **GT**: `<a_1><b_25><c_194>` Fire Emblem Fates: Birthright - Nintendo 3DS B… _(platform 3DS)_ ｜ **native**: `<a_1><b_25><c_194>` Fire Emblem Fates: Birthright … ✓
- **beam top5**: `<a_1><b_25><c_194>`3DS, `<a_1><b_150><c_189>`PS3, `<a_1><b_141><c_192>`PS4, `<a_216><b_219><c_158>`3DS, `<a_216><b_235><c_168>`3DS
- **Rec↔GT gap**: top-1 exact hit.
- **Beam diversity**: **Low** (collapsed to <a_216 family 7/10); unique(a,b)=10/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 1/1 history items (coverage 100%), anchored on: Fire Emblem Fates: Con…; novel candidates=0 (**pure history restatement**); genre: action,role-playing,immersive.
- **Target sensibility (ceiling)**: target=SUBCLASS-continuation (score3); our pred[0]=SUBCLASS-continuation (score3). target is a sensible SUBCLASS-cont and **was caught**.

### #259 — Category-miss·even top-class (a) wrong
- **History** (2 items; platforms 3DS×2): Fire Emblem Fates: Conques… | Fire Emblem Fates: Birthri…
- **GT**: `<a_211><b_159><c_123>` Pok&eacute;mon Moon - Nintendo 3DS _(platform 3DS)_ ｜ **native**: `<a_216><b_91><c_137>` Stella Glow - Nintendo 3DS ✗
- **beam top5**: `<a_162><b_251><c_136>`Wii, `<a_162><b_125><c_53>`?, `<a_1><b_25><c_194>`3DS, `<a_1><b_150><c_189>`PS3, `<a_216><b_91><c_137>`3DS
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=3DS vs rec=WiiU); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=9/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: Fire Emblem Fates: Con…, Fire Emblem Fates: Bir…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,strategy.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=EXPLORATION (unrelated) (score0). user's pick is **more history-consistent** than our top-1 (target1>rec0) → we **drifted off** a catchable continuation.

### #260 — Hit@1
- **History** (3 items; platforms 3DS×3): Fire Emblem Fates: Conques… | Fire Emblem Fates: Birthri… | Pok&eacute;mon Moon - Nint…
- **GT**: `<a_211><b_159><c_71>` Pok&eacute;mon Sun - Nintendo 3DS _(platform 3DS)_ ｜ **native**: `<a_211><b_159><c_71>` Pok&eacute;mon Sun - Nintendo … ✓
- **beam top5**: `<a_211><b_159><c_71>`3DS, `<a_211><b_159><c_123>`3DS, `<a_216><b_159><c_141>`3DS, `<a_216><b_235><c_168>`3DS, `<a_211><b_133><c_30>`3DS
- **Rec↔GT gap**: top-1 exact hit.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=9/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Fire Emblem Fates: Con…, Fire Emblem Fates: Bir…, Pok&eacute;mon Moon - …; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,immersive.
- **Target sensibility (ceiling)**: target=SUBCLASS-continuation (score3); our pred[0]=SUBCLASS-continuation (score3). target is a sensible SUBCLASS-cont and **was caught**.

### #261 — Category-miss·even top-class (a) wrong
- **History** (4 items; platforms 3DS×4): Fire Emblem Fates: Conques… | Fire Emblem Fates: Birthri… | Pok&eacute;mon Moon - Nint… | Pok&eacute;mon Sun - Ninte…
- **GT**: `<a_113><b_159><c_2>` Wii Classic Controller Pro - Black (Japanese V… _(platform Wii)_ ｜ **native**: `<a_216><b_48><c_110>` Dragon Quest VIII: Journey of … ✗
- **beam top5**: `<a_211><b_159><c_71>`3DS, `<a_162><b_5><c_144>`3DS, `<a_162><b_125><c_53>`?, `<a_216><b_235><c_168>`3DS, `<a_216><b_48><c_110>`3DS
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=Wii vs rec=3DS); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Fire Emblem Fates: Con…, Fire Emblem Fates: Bir…, Pok&eacute;mon Moon - …; novel candidates=0 (**pure history restatement**); templated opening; genre: action,adventure,rpg.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=SUBCLASS-continuation (score3). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #262 — Category-OK·item wrong
- **History** (5 items; platforms 3DS×4,Wii×1): Fire Emblem Fates: Conques… | Fire Emblem Fates: Birthri… | Pok&eacute;mon Moon - Nint… | Pok&eacute;mon Sun - Ninte… | Wii Classic Controller Pro…
- **GT**: `<a_162><b_174><c_61>` Villager amiibo - Japan Import (Super Smash Br… _(platform ?)_ ｜ **native**: `<a_113><b_112><c_109>` Nintendo Wii U Pro Controller … ✗
- **beam top5**: `<a_113><b_112><c_109>`Wii, `<a_162><b_5><c_144>`3DS, `<a_162><b_125><c_53>`?, `<a_211><b_159><c_71>`3DS, `<a_162><b_130><c_1>`Wii
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; in beam: share-a=3/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=9/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 5/5 history items (coverage 100%), anchored on: Fire Emblem Fates: Con…, Fire Emblem Fates: Bir…, Pok&eacute;mon Moon - …; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,immersive.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #263 — Category-OK·item wrong · BEAM-COLLAPSE (<a_162×10/10)
- **History** (6 items; platforms 3DS×4,Wii×1,?×1): Fire Emblem Fates: Conques… | Fire Emblem Fates: Birthri… | Pok&eacute;mon Moon - Nint… | Pok&eacute;mon Sun - Ninte… | Wii Classic Controller Pro… | Villager amiibo - Japan Im…
- **GT**: `<a_162><b_214><c_137>` Nintendo amiibo series Shulk Collectible Figur… _(platform ?)_ ｜ **native**: `<a_162><b_122><c_56>` Mario Modern Color Amiibo - Ja… ✗
- **beam top5**: `<a_162><b_122><c_56>`?, `<a_162><b_172><c_85>`?, `<a_162><b_125><c_53>`?, `<a_162><b_122><c_61>`?, `<a_162><b_46><c_162>`3DS
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; in beam: share-a=10/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_162 family 10/10); unique(a,b)=7/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 6/6 history items (coverage 100%), anchored on: Fire Emblem Fates: Con…, Fire Emblem Fates: Bir…, Pok&eacute;mon Moon - …; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,immersive.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item. Note: target shares word(s) ['amiibo', 'series'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #264 — Hit@9 · BEAM-COLLAPSE (<a_162×10/10)
- **History** (7 items; platforms 3DS×4,?×2,Wii×1): Fire Emblem Fates: Birthri… | Pok&eacute;mon Moon - Nint… | Pok&eacute;mon Sun - Ninte… | Wii Classic Controller Pro… | Villager amiibo - Japan Im… | Nintendo amiibo series Shu…
- **GT**: `<a_162><b_106><c_98>` Reflet amiibo - Japan Import (Super Smash Bros… _(platform ?)_ ｜ **native**: `<a_162><b_122><c_56>` Mario Modern Color Amiibo - Ja… ✗
- **beam top5**: `<a_162><b_122><c_56>`?, `<a_162><b_125><c_53>`?, `<a_162><b_122><c_61>`?, `<a_162><b_119><c_2>`?, `<a_162><b_219><c_249>`?
- **Rec↔GT gap**: correct item at beam rank 9, pred[0] prefix-depth only 1/3; in beam: share-a=10/10, share-(a,b)=3/10.
- **Beam diversity**: **Low** (collapsed to <a_162 family 10/10); unique(a,b)=5/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 4/7 history items (coverage 57%), anchored on: Fire Emblem Fates: Con…, Fire Emblem Fates: Bir…, Villager amiibo - Japa…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,strategy.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). target is a sensible CLASS-cont and **was caught**.

### #265 — Hit@6 · BEAM-COLLAPSE (<a_162×10/10)
- **History** (8 items; platforms 3DS×4,?×3,Wii×1): Pok&eacute;mon Moon - Nint… | Pok&eacute;mon Sun - Ninte… | Wii Classic Controller Pro… | Villager amiibo - Japan Im… | Nintendo amiibo series Shu… | Reflet amiibo - Japan Impo…
- **GT**: `<a_162><b_119><c_2>` Lucina amiibo - Japan Import (Super Smash Bros… _(platform ?)_ ｜ **native**: `<a_162><b_219><c_249>` Ganondorf amiibo - Japan Impor… ✗
- **beam top5**: `<a_162><b_21><c_210>`?, `<a_162><b_45><c_208>`?, `<a_162><b_219><c_249>`?, `<a_162><b_2><c_170>`?, `<a_162><b_125><c_53>`?
- **Rec↔GT gap**: correct item at beam rank 6, pred[0] prefix-depth only 1/3; in beam: share-a=10/10, share-(a,b)=1/10.
- **Beam diversity**: **Low** (collapsed to <a_162 family 10/10); unique(a,b)=7/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 2/8 history items (coverage 25%), anchored on: Villager amiibo - Japa…, Reflet amiibo - Japan …; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,immersive.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). target is a sensible CLASS-cont and **was caught**.

### #266 — Hit@7 · BEAM-COLLAPSE (<a_162×10/10)
- **History** (9 items; platforms 3DS×4,?×4,Wii×1): Pok&eacute;mon Sun - Ninte… | Wii Classic Controller Pro… | Villager amiibo - Japan Im… | Nintendo amiibo series Shu… | Reflet amiibo - Japan Impo… | Lucina amiibo - Japan Impo…
- **GT**: `<a_162><b_219><c_101>` Nintendo Super Smash Bros Palutena amiibo _(platform ?)_ ｜ **native**: `<a_162><b_219><c_249>` Ganondorf amiibo - Japan Impor… ✗
- **beam top5**: `<a_162><b_251><c_136>`Wii, `<a_162><b_21><c_210>`?, `<a_162><b_228><c_210>`?, `<a_162><b_219><c_249>`?, `<a_162><b_122><c_56>`?
- **Rec↔GT gap**: correct item at beam rank 7, pred[0] prefix-depth only 1/3; in beam: share-a=10/10, share-(a,b)=3/10.
- **Beam diversity**: **Low** (collapsed to <a_162 family 10/10); unique(a,b)=7/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/9 history items (coverage 44%), anchored on: Fire Emblem Fates: Con…, Fire Emblem Fates: Bir…, Villager amiibo - Japa…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,strategy,simulation.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). target is a sensible CLASS-cont and **was caught**.

### #267 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_162×10/10)
- **History** (10 items; platforms ?×5,3DS×4,Wii×1): Wii Classic Controller Pro… | Villager amiibo - Japan Im… | Nintendo amiibo series Shu… | Reflet amiibo - Japan Impo… | Lucina amiibo - Japan Impo… | Nintendo Super Smash Bros …
- **GT**: `<a_232><b_68><c_178>` Fire Emblem Fates - Special Edition - Nintendo… _(platform 3DS)_ ｜ **native**: `<a_162><b_219><c_101>` Nintendo Super Smash Bros Palu… ✗
- **beam top5**: `<a_162><b_45><c_208>`?, `<a_162><b_251><c_136>`Wii, `<a_162><b_122><c_56>`?, `<a_162><b_139><c_171>`?, `<a_162><b_2><c_170>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_162 family 10/10); unique(a,b)=8/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 6/10 history items (coverage 60%), anchored on: Villager amiibo - Japa…, Nintendo amiibo series…, Reflet amiibo - Japan …; novel candidates=0 (**pure history restatement**); templated opening; genre: action,adventure,rpg.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**. Note: target shares word(s) ['emblem', 'fates', 'fire'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #268 — Category-OK·item wrong
- **History** (5 items; platforms PS4×5): Mafia III - PlayStation 4 | The Elder Scrolls V: Skyri… | Call Of Duty: Infinite War… | Steep - PS4 Digital Code | Mass Effect Andromeda - Pr…
- **GT**: `<a_205><b_208><c_188>` Gran Turismo Sport - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_123><b_58><c_78>`PS4, `<a_39><b_77><c_105>`Xbo, `<a_39><b_51><c_188>`PS4, `<a_123><b_100><c_33>`PS4, `<a_201><b_45><c_166>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=10/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/5 history items (coverage 80%), anchored on: Mafia III - PlayStatio…, The Elder Scrolls V: S…, Call Of Duty: Infinite…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item.

### #269 — Hit@3 · RERANK-HARM
- **History** (1 items; platforms PS×1): PlayStation Eye
- **GT**: `<a_140><b_220><c_113>` PlayStation Eye _(platform PS-generic)_ ｜ **native**: `<a_140><b_220><c_113>` PlayStation Eye ✓
- **beam top5**: `<a_61><b_47><c_32>`PS3, `<a_61><b_47><c_8>`PS3, `<a_140><b_220><c_113>`PS, `<a_175><b_220><c_145>`Wii, `<a_175><b_220><c_18>`Wii
- **Rec↔GT gap**: correct item at beam rank 3, pred[0] prefix-depth only 0/3; platform mismatch(GT=PS-generic vs rec=PS3); in beam: share-a=3/10, share-(a,b)=2/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=5/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 1/1 history items (coverage 100%), anchored on: PlayStation Eye; novel candidates=0 (**pure history restatement**); genre: action,immersive,peripheral.
- **Target sensibility (ceiling)**: target=SUBCLASS-continuation (score3); our pred[0]=EXPLORATION (unrelated) (score0). target is a sensible SUBCLASS-cont and **was caught**.

### #270 — Category-miss·even top-class (a) wrong
- **History** (2 items; platforms PS×2): PlayStation Eye | PlayStation Eye
- **GT**: `<a_84><b_109><c_95>` Nintendo Wii Remote Plus - White _(platform Wii)_ ｜ **native**: `<a_140><b_220><c_113>` PlayStation Eye ✗
- **beam top5**: `<a_61><b_47><c_8>`PS3, `<a_61><b_47><c_32>`PS3, `<a_140><b_220><c_113>`PS, `<a_61><b_251><c_51>`PS4, `<a_189><b_201><c_57>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=Wii vs rec=PS3); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=7/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 0/1 history items (coverage 0%); novel candidates=0 (**pure history restatement**); genre: action,peripheral,accessor.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=EXPLORATION (unrelated) (score0). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #271 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_84×8/10)
- **History** (3 items; platforms PS×2,Wii×1): PlayStation Eye | PlayStation Eye | Nintendo Wii Remote Plus -…
- **GT**: `<a_21><b_36><c_20>` HDE Charging Cable for PS3 Controllers USB Cha… _(platform PS3)_ ｜ **native**: `<a_84><b_222><c_22>` Mario Kart 8 - Nintendo Wii U ✗
- **beam top5**: `<a_175><b_220><c_145>`Wii, `<a_84><b_222><c_22>`Wii, `<a_84><b_222><c_164>`Wii, `<a_84><b_149><c_181>`Wii, `<a_84><b_141><c_255>`Wii
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS3 vs rec=Wii); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_84 family 8/10); unique(a,b)=9/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: PlayStation Eye, Nintendo Wii Remote Pl…; novel candidates=0 (**pure history restatement**); genre: action,immersive,accessor.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=DRIFT (platform/word-linked) (score1). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #272 — Category-OK·item wrong · BEAM-COLLAPSE (<a_84×7/10)
- **History** (4 items; platforms PS×2,Wii×1,PS3×1): PlayStation Eye | PlayStation Eye | Nintendo Wii Remote Plus -… | HDE Charging Cable for PS3…
- **GT**: `<a_162><b_111><c_79>` Wii Stand (RVL-017) _(platform Wii)_ ｜ **native**: `<a_84><b_109><c_95>` Nintendo Wii Remote Plus - Whi… ✗
- **beam top5**: `<a_175><b_220><c_145>`Wii, `<a_175><b_220><c_18>`Wii, `<a_61><b_47><c_8>`PS3, `<a_84><b_109><c_95>`Wii, `<a_84><b_250><c_189>`Wii
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(Wii); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_84 family 7/10); unique(a,b)=8/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 0/3 history items (coverage 0%); novel candidates=0 (**pure history restatement**); templated opening; genre: action,peripheral,accessor.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item.

### #273 — Category-miss·even top-class (a) wrong
- **History** (5 items; platforms PS×2,Wii×2,PS3×1): PlayStation Eye | PlayStation Eye | Nintendo Wii Remote Plus -… | HDE Charging Cable for PS3… | Wii Stand (RVL-017)
- **GT**: `<a_111><b_176><c_21>` Just Dance 2016 - PlayStation 3 _(platform PS3)_ ｜ **native**: `<a_84><b_250><c_189>` Nintendo Wii Remote Plus, Yosh… ✗
- **beam top5**: `<a_175><b_220><c_145>`Wii, `<a_61><b_47><c_8>`PS3, `<a_84><b_250><c_255>`Wii, `<a_84><b_250><c_189>`Wii, `<a_113><b_231><c_3>`Wii
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS3 vs rec=Wii); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=9/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: PlayStation Eye, Nintendo Wii Remote Pl…, HDE Charging Cable for…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,nostalg,peripheral.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item.

### #274 — Category-OK·item wrong
- **History** (10 items; platforms PS4×9,?×1): Titanfall 2 Deluxe Edition… | Dishonored 2 - PlayStation… | Watch Dogs - PlayStation 4 | Doom - PlayStation 4 | Assassin's Creed: Syndicat… | Assassin's Creed IV Black …
- **GT**: `<a_123><b_76><c_232>` Far Cry Primal - PlayStation 4 Standard Editio… _(platform PS4)_ ｜ **native**: `<a_71><b_60><c_105>` Assassin's Creed IV Black Flag… ✗
- **beam top5**: `<a_71><b_33><c_249>`PS3, `<a_71><b_86><c_236>`PS4, `<a_118><b_237><c_113>`PS4, `<a_118><b_150><c_122>`PS4, `<a_118><b_185><c_102>`PS4
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform mismatch(GT=PS4 vs rec=PS3); in beam: share-a=1/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=7/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 6/10 history items (coverage 60%), anchored on: Life is Strange - Play…, Dishonored Definitive …, Titanfall 2 - PlayStat…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #275 — Category-OK·item wrong · BEAM-COLLAPSE (<a_205×8/10)
- **History** (2 items; platforms PS4×2): Injustice 2 - PS4 [Digital… | Gran Turismo Sport - PlayS…
- **GT**: `<a_123><b_52><c_20>` Metal Gear Solid _(platform ?)_ ｜ **native**: `<a_205><b_60><c_93>` F1 2016 - PlayStation 4 ✗
- **beam top5**: `<a_205><b_0><c_108>`PS4, `<a_123><b_72><c_7>`PS4, `<a_205><b_60><c_93>`PS4, `<a_205><b_0><c_112>`?, `<a_205><b_208><c_52>`?
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; in beam: share-a=1/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_205 family 8/10); unique(a,b)=6/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: Injustice 2 - PS4 [Dig…, Gran Turismo Sport - P…; novel candidates=0 (**pure history restatement**); genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #276 — Category-miss·even top-class (a) wrong
- **History** (3 items; platforms PS4×3): Star Wars: Battlefront & S… | Star Wars: Battlefront - S… | KontrolFreek FPS Freek Vor…
- **GT**: `<a_201><b_151><c_255>` Playstation Plus: 3 Month Membership [Digital … _(platform PS-generic)_ ｜ **native**: `<a_231><b_46><c_171>` KontrolFreek CQCX Thumb Grips … ✗
- **beam top5**: `<a_231><b_46><c_223>`PS4, `<a_231><b_158><c_0>`PS4, `<a_61><b_35><c_105>`PS4, `<a_61><b_106><c_125>`PS4, `<a_231><b_46><c_171>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS-generic vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=7/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Star Wars: Battlefront…, Star Wars: Battlefront…, KontrolFreek FPS Freek…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,immersive,nostalg.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**. Note: target shares word(s) ['code', 'digital'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #277 — Category-OK·item wrong
- **History** (4 items; platforms PS4×3,PS×1): Star Wars: Battlefront & S… | Star Wars: Battlefront - S… | KontrolFreek FPS Freek Vor… | Playstation Plus: 3 Month …
- **GT**: `<a_24><b_72><c_142>` Horizon Zero Dawn - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_131><b_224><c_68>` Overwatch - Origins Edition - … ✗
- **beam top5**: `<a_131><b_41><c_229>`PS4, `<a_201><b_31><c_107>`PS4, `<a_131><b_224><c_68>`PS4, `<a_231><b_46><c_171>`PS4, `<a_61><b_106><c_251>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Star Wars: Battlefront…, Star Wars: Battlefront…, KontrolFreek FPS Freek…; novel candidates=0 (**pure history restatement**); genre: multiplayer,immersive,accessor.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #278 — Category-OK·item wrong
- **History** (3 items; platforms ?×1,PS3×1,PS4×1): Dead Space 3 Limited Editi… | Portal 2 - Playstation 3 | Titanfall 2 - PlayStation …
- **GT**: `<a_39><b_78><c_54>` Battlefield 1 - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_201><b_213><c_242>`PS4, `<a_24><b_129><c_173>`PS4, `<a_123><b_58><c_78>`PS4, `<a_123><b_142><c_36>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=10/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Dead Space 3 Limited E…, Portal 2 - Playstation…, Titanfall 2 - PlayStat…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,horror,multiplayer.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=DRIFT (platform/word-linked) (score1). user's pick is **more history-consistent** than our top-1 (target2>rec1) → we **drifted off** a catchable continuation.

### #279 — Hit@6
- **History** (4 items; platforms Xbox360×2,3DS×2): Halo 4 - Xbox 360 (Standar… | Destiny: The Taken King - … | Pokemon Alpha Sapphire - N… | Pok&eacute;mon Omega Ruby …
- **GT**: `<a_211><b_159><c_71>` Pok&eacute;mon Sun - Nintendo 3DS _(platform 3DS)_ ｜ **native**: `<a_211><b_133><c_123>` Pok&eacute;mon Omega Ruby - Ni… ✗
- **beam top5**: `<a_131><b_28><c_96>`PS4, `<a_211><b_133><c_123>`3DS, `<a_211><b_159><c_123>`3DS, `<a_131><b_145><c_18>`Xbo, `<a_131><b_210><c_0>`PS4
- **Rec↔GT gap**: correct item at beam rank 6, pred[0] prefix-depth only 0/3; platform mismatch(GT=3DS vs rec=PS4); in beam: share-a=5/10, share-(a,b)=2/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=7/10, platforms=5, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Halo 4 - Xbox 360 (Sta…, Destiny: The Taken Kin…, Pokemon Alpha Sapphire…; novel candidates=0 (**pure history restatement**); genre: action,rpg,shooter.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). target is a sensible CLASS-cont and **was caught**.

### #280 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_201×8/10)
- **History** (1 items; platforms PS4×1): PlayStation 4 500GB Consol…
- **GT**: `<a_71><b_179><c_202>` Dante's Inferno Divine Edition - Playstation 3 _(platform PS3)_ ｜ **native**: `<a_201><b_2><c_102>` PlayStation 4 500GB Console - … ✗
- **beam top5**: `<a_131><b_210><c_0>`PS4, `<a_201><b_36><c_195>`PS4, `<a_201><b_31><c_107>`PS4, `<a_201><b_2><c_102>`PS4, `<a_201><b_201><c_84>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS3 vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_201 family 8/10); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 0/1 history items (coverage 0%); novel candidates=0 (**pure history restatement**); genre: action,nostalg,retro.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=DRIFT (platform/word-linked) (score1). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #281 — Category-OK·item wrong
- **History** (2 items; platforms PS4×1,PS3×1): PlayStation 4 500GB Consol… | Dante's Inferno Divine Edi…
- **GT**: `<a_71><b_159><c_0>` Castlevania _(platform ?)_ ｜ **native**: `<a_71><b_60><c_118>` Assassin's Creed IV Black Flag… ✗
- **beam top5**: `<a_71><b_33><c_249>`PS3, `<a_71><b_60><c_105>`PS4, `<a_118><b_150><c_122>`PS4, `<a_118><b_95><c_6>`PS4, `<a_71><b_86><c_236>`PS4
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; in beam: share-a=6/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (2 a top-classes); unique(a,b)=7/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 0/2 history items (coverage 0%); novel candidates=0 (**pure history restatement**); genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item.

### #282 — Category-OK·item wrong · BEAM-COLLAPSE (<a_71×10/10)
- **History** (3 items; platforms PS4×1,PS3×1,?×1): PlayStation 4 500GB Consol… | Dante's Inferno Divine Edi… | Castlevania
- **GT**: `<a_194><b_222><c_98>` Castlevania: Lords of Shadow 2 - PS3 [Digital … _(platform PS3)_ ｜ **native**: `<a_71><b_159><c_0>` Castlevania ✗
- **beam top5**: `<a_71><b_164><c_196>`PS3, `<a_71><b_164><c_177>`PSP, `<a_71><b_66><c_14>`?, `<a_71><b_159><c_7>`?, `<a_71><b_171><c_0>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS3); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_71 family 10/10); unique(a,b)=8/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Dante's Inferno Divine…, Castlevania, PlayStation 4 500GB Co…; novel candidates=0 (**pure history restatement**); genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**. Note: target shares word(s) ['castlevania'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #283 — Category-miss·even top-class (a) wrong
- **History** (4 items; platforms PS3×2,PS4×1,?×1): PlayStation 4 500GB Consol… | Dante's Inferno Divine Edi… | Castlevania | Castlevania: Lords of Shad…
- **GT**: `<a_118><b_67><c_59>` The Walking Dead: Season 2 - PlayStation 3 _(platform PS3)_ ｜ **native**: `<a_194><b_222><c_98>` Castlevania: Lords of Shadow 2… ✗
- **beam top5**: `<a_194><b_215><c_154>`?, `<a_194><b_24><c_128>`?, `<a_71><b_202><c_11>`?, `<a_194><b_222><c_98>`PS3, `<a_194><b_21><c_1>`PS3
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=10/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 2/4 history items (coverage 50%), anchored on: Dante's Inferno Divine…, Castlevania: Lords of …; novel candidates=0 (**pure history restatement**); genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #284 — Category-OK·item wrong
- **History** (4 items; platforms XboxOne×4): NBA 2K16 - Xbox One | WWE 2K16 - Xbox One | The Wolf Among Us - Xbox O… | Madden NFL 17 -  Standard …
- **GT**: `<a_194><b_36><c_216>` Final Fantasy XV - Xbox One _(platform XboxOne)_ ｜ **native**: `<a_231><b_102><c_225>` Madden NFL 17 -  Standard Edit… ✗
- **beam top5**: `<a_231><b_117><c_187>`Xbo, `<a_231><b_237><c_82>`PS4, `<a_45><b_168><c_1>`Xbo, `<a_231><b_223><c_4>`Xbo, `<a_231><b_102><c_225>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (2 a top-classes); unique(a,b)=8/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: NBA 2K16 - Xbox One, WWE 2K16 - Xbox One, The Wolf Among Us - Xb…; novel candidates=0 (**pure history restatement**); genre: action,sports,immersive.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #285 — Category-OK·item wrong
- **History** (9 items; platforms PS4×9): The Walking Dead: The Comp… | Mafia III - PlayStation 4 | Dishonored 2 - PlayStation… | Mass Effect Andromeda - Pr… | Dead Island Definitive Col… | Tom Clancy's The Division …
- **GT**: `<a_191><b_68><c_161>` inFAMOUS: Second Son Limited Edition (PlayStat… _(platform PS4)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_123><b_58><c_78>`PS4, `<a_24><b_72><c_142>`PS4, `<a_123><b_100><c_33>`PS4, `<a_123><b_58><c_16>`Xbo, `<a_201><b_31><c_107>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 6/9 history items (coverage 67%), anchored on: Call of Duty: Black Op…, The Walking Dead: The …, Alekhine's Gun - PlayS…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item.

### #286 — Category-OK·item wrong
- **History** (10 items; platforms PS4×5,?×4,XboxOne×1): Steep - PS4 Digital Code | CORSAIR Scimitar Pro RGB -… | CORSAIR Scimitar Pro RGB -… | Tom Clancy&rsquo;s Ghost R… | Tom Clancy&rsquo;s Ghost R… | Dragon Quest Builders - Pl…
- **GT**: `<a_86><b_12><c_93>` South Park: The Fractured but Whole - PlayStat… _(platform PS4)_ ｜ **native**: `<a_1><b_43><c_207>` The Last Guardian - PlayStatio… ✗
- **beam top5**: `<a_1><b_43><c_207>`PS4, `<a_123><b_58><c_78>`PS4, `<a_123><b_100><c_166>`DS, `<a_1><b_173><c_4>`PS4, `<a_123><b_142><c_36>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 5/9 history items (coverage 56%), anchored on: Tom Clancy's The Divis…, Tom Clancy&rsquo;s Gho…, Watch Dogs 2 - PlaySta…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,shooter.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #287 — Category-miss·even top-class (a) wrong
- **History** (1 items; platforms ?×1): Diablo III: Reaper of Soul…
- **GT**: `<a_113><b_9><c_63>` Mayflash GameCube Controller Adapter for Wii U… _(platform WiiU)_ ｜ **native**: `<a_10><b_20><c_0>` Diablo III: Ultimate Evil Edit… ✗
- **beam top5**: `<a_10><b_20><c_0>`?, `<a_10><b_67><c_155>`?, `<a_10><b_33><c_56>`?, `<a_10><b_33><c_116>`?, `<a_10><b_67><c_51>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=8/10, platforms=3, unique titles=8/10.
- **Reasoning quality**: cites 1/1 history items (coverage 100%), anchored on: Diablo III: Reaper of …; novel candidates=0 (**pure history restatement**); genre: action,immersive,narrative.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #288 — Category-miss·even top-class (a) wrong
- **History** (2 items; platforms ?×1,WiiU×1): Diablo III: Reaper of Soul… | Mayflash GameCube Controll…
- **GT**: `<a_111><b_71><c_5>` Rock Band 4 Band-in-a-Box Bundle - Xbox One _(platform XboxOne)_ ｜ **native**: `<a_202><b_16><c_110>` Razer DeathAdder Expert - Opti… ✗
- **beam top5**: `<a_61><b_0><c_187>`?, `<a_61><b_9><c_199>`PS3, `<a_61><b_9><c_122>`PS3, `<a_202><b_16><c_110>`?, `<a_113><b_9><c_63>`Wii
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=8/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: Diablo III: Reaper of …, Mayflash GameCube Cont…; novel candidates=0 (**pure history restatement**); genre: action,immersive,nostalg.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=EXPLORATION (unrelated) (score0). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #289 — Category-OK·item wrong
- **History** (4 items; platforms PS4×2,XboxOne×1,3DS×1): The Last of Us Remastered … | Digimon Story: Cyber Sleut… | Xbox One Stereo Headset Ad… | Pokemon Alpha Sapphire - N…
- **GT**: `<a_216><b_44><c_79>` Bravely Second: End Layer - Nintendo 3DS _(platform 3DS)_ ｜ **native**: `<a_211><b_133><c_123>` Pok&eacute;mon Omega Ruby - Ni… ✗
- **beam top5**: `<a_211><b_133><c_123>`3DS, `<a_211><b_159><c_123>`3DS, `<a_1><b_25><c_254>`3DS, `<a_211><b_159><c_71>`3DS, `<a_1><b_150><c_189>`PS3
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(3DS); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (2 a top-classes); unique(a,b)=8/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: The Last of Us Remaste…, Digimon Story: Cyber S…, Pokemon Alpha Sapphire…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=SUBCLASS-continuation (score3). we recommended something **more history-consistent** than the user's actual pick (rec3>target1) → **model too conservative / user more exploratory**.

### #290 — Category-miss·even top-class (a) wrong
- **History** (1 items; platforms PS×1): PlayStation TV
- **GT**: `<a_141><b_73><c_216>` Star Wars: Battlefront - Standard Edition - Pl… _(platform PS4)_ ｜ **native**: `<a_61><b_47><c_32>` PlayStation 3 Dualshock 3 Wire… ✗
- **beam top5**: `<a_189><b_99><c_126>`PS, `<a_231><b_28><c_63>`PS4, `<a_61><b_214><c_252>`Xbo, `<a_208><b_175><c_0>`PS4, `<a_61><b_38><c_203>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS4 vs rec=PS-generic); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=9/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 0/1 history items (coverage 0%); novel candidates=0 (**pure history restatement**); genre: action,multiplayer,family-friendly.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=SUBCLASS-continuation (score3). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #291 — Category-miss·even top-class (a) wrong
- **History** (2 items; platforms PS×1,PS4×1): PlayStation TV | Star Wars: Battlefront - S…
- **GT**: `<a_216><b_219><c_158>` Hyrule Warriors: Legends - Nintendo 3DS _(platform 3DS)_ ｜ **native**: `<a_201><b_2><c_102>` PlayStation 4 500GB Console - … ✗
- **beam top5**: `<a_201><b_36><c_195>`PS4, `<a_208><b_175><c_0>`PS4, `<a_131><b_210><c_0>`PS4, `<a_201><b_31><c_107>`PS4, `<a_201><b_2><c_102>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=3DS vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=10/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: Star Wars: Battlefront…, PlayStation TV; novel candidates=0 (**pure history restatement**); genre: action,strategy,multiplayer.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=DRIFT (platform/word-linked) (score1). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #292 — Category-miss·even top-class (a) wrong
- **History** (3 items; platforms PS×1,PS4×1,3DS×1): PlayStation TV | Star Wars: Battlefront - S… | Hyrule Warriors: Legends -…
- **GT**: `<a_195><b_216><c_209>` Alice: Madness Returns - Playstation 3 _(platform PS3)_ ｜ **native**: `<a_1><b_25><c_254>` Fire Emblem Fates: Conquest - … ✗
- **beam top5**: `<a_1><b_25><c_254>`3DS, `<a_1><b_101><c_0>`Wii, `<a_131><b_41><c_229>`PS4, `<a_208><b_175><c_0>`PS4, `<a_201><b_31><c_107>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS3 vs rec=3DS); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=9/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 2/3 history items (coverage 67%), anchored on: Star Wars: Battlefront…, Hyrule Warriors: Legen…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=DRIFT (platform/word-linked) (score1). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #293 — Category-miss·even top-class (a) wrong
- **History** (4 items; platforms PS×1,PS4×1,3DS×1): PlayStation TV | Star Wars: Battlefront - S… | Hyrule Warriors: Legends -… | Alice: Madness Returns - P…
- **GT**: `<a_249><b_155><c_14>` 4GB PlayStation Vita Memory Card _(platform PSVita)_ ｜ **native**: `<a_195><b_4><c_0>` Kingdom Hearts ✗
- **beam top5**: `<a_195><b_241><c_163>`PS, `<a_195><b_4><c_0>`?, `<a_194><b_21><c_76>`PS4, `<a_195><b_4><c_2>`PSP, `<a_194><b_32><c_11>`PSV
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PSVita vs rec=PS2); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=7/10, platforms=6, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Star Wars: Battlefront…, Hyrule Warriors: Legen…, Alice: Madness Returns…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #294 — Category-miss·even top-class (a) wrong
- **History** (5 items; platforms PS×1,PS4×1,3DS×1): PlayStation TV | Star Wars: Battlefront - S… | Hyrule Warriors: Legends -… | Alice: Madness Returns - P… | 4GB PlayStation Vita Memor…
- **GT**: `<a_74><b_204><c_217>` PlayStation All-Stars Battle Royale PS Vita - … _(platform PSVita)_ ｜ **native**: `<a_249><b_31><c_126>` Sony PlayStation Vita WiFi ✗
- **beam top5**: `<a_249><b_170><c_61>`PS, `<a_201><b_31><c_107>`PS4, `<a_249><b_63><c_20>`PSV, `<a_249><b_31><c_126>`PSV, `<a_249><b_68><c_59>`PSV
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PSVita vs rec=PS2); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=9/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 4/5 history items (coverage 80%), anchored on: Star Wars: Battlefront…, Hyrule Warriors: Legen…, Alice: Madness Returns…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #295 — Category-miss·even top-class (a) wrong
- **History** (6 items; platforms PSVita×2,PS×1,PS4×1): PlayStation TV | Star Wars: Battlefront - S… | Hyrule Warriors: Legends -… | Alice: Madness Returns - P… | 4GB PlayStation Vita Memor… | PlayStation All-Stars Batt…
- **GT**: `<a_245><b_139><c_1>` LEGO Star Wars: The Force Awakens - PlayStatio… _(platform PSVita)_ ｜ **native**: `<a_1><b_121><c_178>` Monster Hunter 4 Ultimate Stan… ✗
- **beam top5**: `<a_74><b_218><c_91>`PS3, `<a_1><b_99><c_2>`PS4, `<a_1><b_173><c_4>`PS4, `<a_74><b_218><c_206>`PS4, `<a_1><b_209><c_76>`PS3
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PSVita vs rec=PS3); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=9/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 5/6 history items (coverage 83%), anchored on: Star Wars: Battlefront…, Hyrule Warriors: Legen…, PlayStation All-Stars …; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**. Note: target shares word(s) ['star', 'wars'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #296 — Category-OK·item wrong · BEAM-COLLAPSE (<a_39×7/10)
- **History** (4 items; platforms XboxOne×3,?×1): NBA 2K16 - Xbox One | Dead Rising 3: Apocalypse … | Call of Duty: Infinite War… | Turtle Beach - Ear Force H…
- **GT**: `<a_39><b_69><c_69>` Call of Duty: Black Ops III - Standard Edition… _(platform XboxOne)_ ｜ **native**: `<a_39><b_77><c_105>` Call of Duty: Infinite Warfare… ✗
- **beam top5**: `<a_39><b_77><c_105>`Xbo, `<a_39><b_51><c_21>`Xbo, `<a_39><b_77><c_233>`Xbo, `<a_7><b_2><c_105>`Xbo, `<a_39><b_77><c_69>`Xbo
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform consistent(XboxOne); in beam: share-a=7/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_39 family 7/10); unique(a,b)=7/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: NBA 2K16 - Xbox One, Dead Rising 3: Apocaly…, Call of Duty: Infinite…; novel candidates=0 (**pure history restatement**); genre: action,shooter,sports.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=SUBCLASS-continuation (score3). we recommended something **more history-consistent** than the user's actual pick (rec3>target2) → **model too conservative / user more exploratory**. Note: target shares word(s) ['call', 'duty'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #297 — Category-OK·item wrong
- **History** (5 items; platforms XboxOne×4,?×1): NBA 2K16 - Xbox One | Dead Rising 3: Apocalypse … | Call of Duty: Infinite War… | Turtle Beach - Ear Force H… | Call of Duty: Black Ops II…
- **GT**: `<a_202><b_164><c_89>` ASTRO Gaming A40 TR Headset + MixAmp Pro TR fo… _(platform XboxOne)_ ｜ **native**: `<a_39><b_77><c_105>` Call of Duty: Infinite Warfare… ✗
- **beam top5**: `<a_7><b_248><c_16>`Xbo, `<a_39><b_77><c_105>`Xbo, `<a_7><b_2><c_105>`Xbo, `<a_131><b_155><c_206>`Xbo, `<a_39><b_77><c_233>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=8/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/5 history items (coverage 80%), anchored on: Call of Duty: Infinite…, Call of Duty: Black Op…, Dead Rising 3: Apocaly…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,shooter,strategy.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**. Note: target shares word(s) ['headset'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #298 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_131×8/10)
- **History** (2 items; platforms PC×1,PS4×1): Call of Duty: Black Ops II… | Fallout 4 - PlayStation 4
- **GT**: `<a_74><b_218><c_196>` Ratchet & Clank Up Your Arsenal - PlayStation … _(platform PS2)_ ｜ **native**: `<a_131><b_155><c_206>` Fallout 4 - Xbox One ✗
- **beam top5**: `<a_131><b_28><c_96>`PS4, `<a_131><b_155><c_206>`Xbo, `<a_141><b_73><c_216>`PS4, `<a_141><b_73><c_7>`PS4, `<a_131><b_145><c_6>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS2 vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_131 family 8/10); unique(a,b)=7/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: Call of Duty: Black Op…, Fallout 4 - PlayStatio…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,shooter.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #299 — Category-OK·item wrong · BEAM-COLLAPSE (<a_121×8/10)
- **History** (1 items; platforms PS4×1): NieR: Automata - Playstati…
- **GT**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - PS4 Digital Code _(platform PS4)_ ｜ **native**: `<a_121><b_76><c_208>` Star Ocean: Integrity and Fait… ✗
- **beam top5**: `<a_121><b_76><c_208>`PS4, `<a_121><b_35><c_0>`PS4, `<a_1><b_150><c_189>`PS3, `<a_121><b_91><c_244>`PS4, `<a_121><b_192><c_253>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_121 family 8/10); unique(a,b)=10/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 1/1 history items (coverage 100%), anchored on: NieR: Automata - Plays…; novel candidates=0 (**pure history restatement**); genre: action,adventure,strategy.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #300 — Category-miss·even top-class (a) wrong
- **History** (2 items; platforms PS4×2): NieR: Automata - Playstati… | Resident Evil 7: Biohazard…
- **GT**: `<a_195><b_122><c_178>` Zero Escape: Virtue's Last Reward - Nintendo 3… _(platform 3DS)_ ｜ **native**: `<a_123><b_58><c_16>` Resident Evil 7 Biohazard - Xb… ✗
- **beam top5**: `<a_123><b_58><c_16>`Xbo, `<a_123><b_78><c_71>`PS4, `<a_24><b_129><c_173>`PS4, `<a_123><b_33><c_93>`PS4, `<a_24><b_185><c_47>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=3DS vs rec=XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=10/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: NieR: Automata - Plays…, Resident Evil 7: Bioha…; novel candidates=0 (**pure history restatement**); genre: action,horror,immersive.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=SUBCLASS-continuation (score3). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #301 — Category-miss·even top-class (a) wrong
- **History** (7 items; platforms ?×6,PS4×1): Super Mario World 2: Yoshi… | Super Mario Bros. 2 | Animal Crossing | The Legend of Zelda: Ocari… | Donkey Kong Country Return… | Assassins Creed Unity PS4
- **GT**: `<a_71><b_158><c_1>` The Evil Within - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_211><b_105><c_215>` Animal Crossing: New Leaf ✗
- **beam top5**: `<a_211><b_105><c_215>`?, `<a_216><b_112><c_114>`Wii, `<a_250><b_156><c_1>`?, `<a_216><b_156><c_1>`?, `<a_250><b_116><c_226>`Wii
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=8/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 6/7 history items (coverage 86%), anchored on: Donkey Kong Country, Super Mario World 2: Y…, Super Mario Bros. 2; novel candidates=0 (**pure history restatement**); genre: action,adventure,puzzle.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #302 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_84×8/10)
- **History** (10 items; platforms PS4×4,WiiU×3,DS×1): Plants vs. Zombies Garden … | AmazonBasics Heavy-Duty Va… | Nintendo Wii U Fit Balance… | The Legend of Zelda: Breat… | Madden NFL 17 - Standard E… | Wii Sports Club - Wii U
- **GT**: `<a_118><b_78><c_177>` The Walking Dead: The Complete First Season - … _(platform PS4)_ ｜ **native**: `<a_84><b_1><c_164>` Wii Sports Club - Wii U ✗
- **beam top5**: `<a_84><b_25><c_96>`Wii, `<a_84><b_149><c_181>`Wii, `<a_84><b_250><c_210>`Wii, `<a_84><b_54><c_87>`Wii, `<a_84><b_250><c_189>`Wii
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS4 vs rec=WiiU); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_84 family 8/10); unique(a,b)=9/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 6/10 history items (coverage 60%), anchored on: Dragon Quest IV: Chapt…, Battlefield 1 - PlaySt…, Plants vs. Zombies Gar…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #303 — Category-OK·item wrong
- **History** (10 items; platforms PS4×5,WiiU×3,Wii×1): AmazonBasics Heavy-Duty Va… | Nintendo Wii U Fit Balance… | The Legend of Zelda: Breat… | Madden NFL 17 - Standard E… | Wii Sports Club - Wii U | The Walking Dead: The Comp…
- **GT**: `<a_194><b_33><c_2>` Dark Souls II: Scholar of the First Sin - Xbox… _(platform XboxOne)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_39><b_51><c_21>`Xbo, `<a_123><b_58><c_78>`PS4, `<a_39><b_175><c_240>`Xbo, `<a_201><b_56><c_74>`PS4, `<a_123><b_58><c_16>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=8/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 6/10 history items (coverage 60%), anchored on: Battlefield 1 - PlaySt…, Titanfall 2 - PlayStat…, Plants vs. Zombies Gar…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,adventure,shooter.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=SUBCLASS-continuation (score3). we recommended something **more history-consistent** than the user's actual pick (rec3>target1) → **model too conservative / user more exploratory**. Note: target shares word(s) ['first'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #304 — Category-miss·even top-class (a) wrong
- **History** (10 items; platforms PS4×5,WiiU×3,PSVita×1): Nintendo Wii U Fit Balance… | The Legend of Zelda: Breat… | Madden NFL 17 - Standard E… | Wii Sports Club - Wii U | The Walking Dead: The Comp… | Dark Souls II: Scholar of …
- **GT**: `<a_22><b_192><c_187>` Middle Earth: Shadow of Mordor Game of the Yea… _(platform XboxOne)_ ｜ **native**: `<a_194><b_15><c_66>` Dishonored 2 - PlayStation 4 ✗
- **beam top5**: `<a_194><b_87><c_249>`PS4, `<a_194><b_87><c_112>`PS4, `<a_194><b_15><c_66>`PS4, `<a_123><b_58><c_78>`PS4, `<a_131><b_41><c_229>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=XboxOne vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=8/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 5/10 history items (coverage 50%), anchored on: Battlefield 1 - PlaySt…, Titanfall 2 - PlayStat…, Plants vs. Zombies Gar…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,adventure,shooter.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #305 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_217×7/10)
- **History** (10 items; platforms ?×8,WiiU×1,PS4×1): Snoopy's Grand Adventure -… | Skylanders SuperChargers D… | Skylanders SuperChargers: … | MLB The Show 16 - PlayStat… | Nintendo Selects: Pikmin 3 | Nintendo Selects: Donkey K…
- **GT**: `<a_162><b_222><c_61>` Nintendo Waluigi amiibo (SM Series) - Nintendo… _(platform WiiU)_ ｜ **native**: `<a_217><b_71><c_226>` Skylanders SuperChargers: Raci… ✗
- **beam top5**: `<a_217><b_71><c_22>`?, `<a_217><b_71><c_11>`?, `<a_217><b_71><c_226>`?, `<a_217><b_71><c_85>`?, `<a_217><b_71><c_151>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_217 family 7/10); unique(a,b)=4/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 6/10 history items (coverage 60%), anchored on: Skylanders Trap Team: …, Skylanders SWAP Force …, Skylanders SWAP Force …; novel candidates=0 (**pure history restatement**); templated opening; genre: action,adventure,immersive.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=SUBCLASS-continuation (score3). we recommended something **more history-consistent** than the user's actual pick (rec3>target1) → **model too conservative / user more exploratory**.

### #306 — Category-OK·item wrong
- **History** (3 items; platforms ?×2,Xbox360×1): Microsoft Xbox 360 Wireles… | Havit Rainbow Backlit Wire… | HAVIT RGB Backlit Wired Me…
- **GT**: `<a_202><b_113><c_73>` RAZER MAMBA TOURNAMENT EDITION: 16,000 Adjusta… _(platform ?)_ ｜ **native**: `<a_214><b_226><c_146>` Havit Rainbow Backlit Wired Ga… ✗
- **beam top5**: `<a_61><b_131><c_197>`Xbo, `<a_214><b_24><c_0>`?, `<a_61><b_181><c_195>`Xbo, `<a_214><b_64><c_229>`?, `<a_214><b_226><c_73>`?
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; in beam: share-a=1/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=9/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Microsoft Xbox 360 Wir…, Havit Rainbow Backlit …, HAVIT RGB Backlit Wire…; novel candidates=0 (**pure history restatement**); genre: action,peripheral,accessor.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**. Note: target shares word(s) ['gaming', 'mouse'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #307 — Near-miss·same (a,b) subcluster, only c differs · BEAM-COLLAPSE (<a_202×10/10)
- **History** (4 items; platforms ?×3,Xbox360×1): Microsoft Xbox 360 Wireles… | Havit Rainbow Backlit Wire… | HAVIT RGB Backlit Wired Me… | RAZER MAMBA TOURNAMENT EDI…
- **GT**: `<a_202><b_213><c_48>` Razer Blackwidow _(platform ?)_ ｜ **native**: `<a_202><b_200><c_67>` Logitech G600 MMO Gaming Mouse… ✗
- **beam top5**: `<a_202><b_253><c_158>`?, `<a_202><b_30><c_0>`?, `<a_202><b_34><c_39>`?, `<a_202><b_200><c_67>`?, `<a_202><b_203><c_93>`?
- **Rec↔GT gap**: beam's closest item shares (a,b) subcluster with GT, only c differs (same series/SKU), still missed; in beam: share-a=10/10, share-(a,b)=1/10.
- **Beam diversity**: **Low** (collapsed to <a_202 family 10/10); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Microsoft Xbox 360 Wir…, Havit Rainbow Backlit …, HAVIT RGB Backlit Wire…; novel candidates=0 (**pure history restatement**); genre: action,peripheral,accessor.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item. Note: target shares word(s) ['razer'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #308 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_245×9/10)
- **History** (10 items; platforms XboxOne×6,?×2,Xbox360×1): Xbox One 500GB Console - A… | Ultimate NES Remix - Ninte… | LEGO Dimensions Starter Pa… | Assassin&rsquo;s Creed Syn… | Ghostbusters Slimer Fun Pa… | Nyko Modular Charge Statio…
- **GT**: `<a_13><b_224><c_3>` Plants vs. Zombies Garden Warfare 2 - Xbox One _(platform XboxOne)_ ｜ **native**: `<a_245><b_121><c_191>` LEGO Dimensions Starter Pack -… ✗
- **beam top5**: `<a_245><b_93><c_22>`?, `<a_245><b_86><c_40>`Xbo, `<a_245><b_29><c_110>`?, `<a_49><b_36><c_1>`Xbo, `<a_245><b_193><c_0>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_245 family 9/10); unique(a,b)=9/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 4/10 history items (coverage 40%), anchored on: Wolfenstein: The New O…, Assassin&rsquo;s Creed…, LEGO Dimensions Starte…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #309 — Hit·repurchase/same-item (easy)
- **History** (1 items; platforms Wii×1): Wii Play
- **GT**: `<a_84><b_243><c_6>` Wii Play _(platform Wii)_ ｜ **native**: `<a_84><b_243><c_6>` Wii Play ✓
- **beam top5**: `<a_84><b_243><c_6>`Wii, `<a_84><b_136><c_91>`Wii, `<a_175><b_225><c_3>`Wii, `<a_175><b_48><c_69>`Wii, `<a_84><b_222><c_164>`Wii
- **Rec↔GT gap**: top-1 exact hit.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=8/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 1/1 history items (coverage 100%), anchored on: Wii Play; novel candidates=0 (**pure history restatement**); genre: action,multiplayer.
- **Target sensibility (ceiling)**: target=SUBCLASS-continuation (score3); our pred[0]=SUBCLASS-continuation (score3). target is a sensible SUBCLASS-cont and **was caught**.

### #310 — Category-miss·even top-class (a) wrong
- **History** (2 items; platforms Wii×2): Wii Play | Wii Play
- **GT**: `<a_140><b_103><c_43>` Xbox 360 4GB Console _(platform Xbox360)_ ｜ **native**: `<a_84><b_132><c_6>` Wii Sports Resort ✗
- **beam top5**: `<a_175><b_220><c_18>`Wii, `<a_175><b_225><c_3>`Wii, `<a_175><b_24><c_4>`Wii, `<a_175><b_113><c_76>`?, `<a_84><b_243><c_6>`Wii
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=Xbox360 vs rec=Wii); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (2 a top-classes); unique(a,b)=8/10, platforms=2, unique titles=9/10.
- **Reasoning quality**: cites 1/1 history items (coverage 100%), anchored on: Wii Play; novel candidates=0 (**pure history restatement**); genre: action,multiplayer,accessor.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=DRIFT (platform/word-linked) (score1). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #311 — Category-miss·even top-class (a) wrong
- **History** (3 items; platforms Wii×2,Xbox360×1): Wii Play | Wii Play | Xbox 360 4GB Console
- **GT**: `<a_193><b_0><c_187>` Mario & Sonic at the Olympic Games for wii _(platform Wii)_ ｜ **native**: `<a_61><b_181><c_195>` Xbox 360 Wireless Controller -… ✗
- **beam top5**: `<a_61><b_181><c_195>`Xbo, `<a_175><b_103><c_55>`Xbo, `<a_175><b_103><c_21>`Xbo, `<a_111><b_149><c_227>`?, `<a_140><b_105><c_178>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=Wii vs rec=Xbox360); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (6 distinct a top-classes); unique(a,b)=8/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: Wii Play, Xbox 360 4GB Console; novel candidates=0 (**pure history restatement**); templated opening; genre: action,multiplayer,family-friendly.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item.

### #312 — Category-OK·item wrong
- **History** (4 items; platforms Wii×3,Xbox360×1): Wii Play | Wii Play | Xbox 360 4GB Console | Mario & Sonic at the Olymp…
- **GT**: `<a_175><b_225><c_3>` Wii Fit Game with Balance Board _(platform Wii)_ ｜ **native**: `<a_175><b_24><c_4>` New Super Mario Bros. Wii ✗
- **beam top5**: `<a_175><b_24><c_4>`Wii, `<a_84><b_222><c_135>`Wii, `<a_84><b_206><c_162>`Wii, `<a_84><b_222><c_164>`Wii, `<a_84><b_132><c_6>`Wii
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform consistent(Wii); in beam: share-a=2/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=7/10, platforms=3, unique titles=9/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Wii Play, Xbox 360 4GB Console, Mario & Sonic at the O…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,racing,multiplayer.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item.

### #313 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_61×9/10)
- **History** (4 items; platforms Xbox360×2,PC×1,PS3×1): Hisurprise 2x Black Batter… | Xbox 360 Microsoft Authent… | Minecraft for PC/Mac [Onli… | PlayStation 3 500 GB Syste…
- **GT**: `<a_194><b_97><c_127>` Demon's Souls _(platform ?)_ ｜ **native**: `<a_61><b_181><c_195>` Xbox 360 Wireless Controller -… ✗
- **beam top5**: `<a_61><b_181><c_195>`Xbo, `<a_61><b_167><c_197>`Xbo, `<a_61><b_214><c_252>`Xbo, `<a_61><b_53><c_46>`Xbo, `<a_61><b_137><c_255>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_61 family 9/10); unique(a,b)=7/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Hisurprise 2x Black Ba…, Xbox 360 Microsoft Aut…, Minecraft for PC/Mac […; novel candidates=0 (**pure history restatement**); genre: action,immersive,accessor.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #314 — Category-miss·even top-class (a) wrong
- **History** (5 items; platforms Xbox360×2,PC×1,PS3×1): Hisurprise 2x Black Batter… | Xbox 360 Microsoft Authent… | Minecraft for PC/Mac [Onli… | PlayStation 3 500 GB Syste… | Demon's Souls
- **GT**: `<a_24><b_51><c_181>` God of War III - Playstation 3 _(platform PS3)_ ｜ **native**: `<a_61><b_181><c_195>` Xbox 360 Wireless Controller -… ✗
- **beam top5**: `<a_61><b_181><c_195>`Xbo, `<a_202><b_200><c_67>`?, `<a_202><b_16><c_110>`?, `<a_194><b_20><c_194>`Xbo, `<a_194><b_33><c_4>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS3 vs rec=Xbox360); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=9/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 3/5 history items (coverage 60%), anchored on: Hisurprise 2x Black Ba…, Xbox 360 Microsoft Aut…, Demon's Souls; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,immersive.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #315 — Category-miss·even top-class (a) wrong
- **History** (1 items; platforms Xbox360×1): South Park:  The Stick of …
- **GT**: `<a_201><b_85><c_136>` Until Dawn - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_131><b_155><c_206>` Fallout 4 - Xbox One ✗
- **beam top5**: `<a_131><b_155><c_206>`Xbo, `<a_74><b_100><c_233>`?, `<a_86><b_18><c_30>`Xbo, `<a_131><b_233><c_112>`?, `<a_74><b_5><c_203>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS4 vs rec=XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=9/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 1/1 history items (coverage 100%), anchored on: South Park:  The Stick…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,adventure,narrative.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=EXPLORATION (unrelated) (score0). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #316 — Category-OK·item wrong
- **History** (2 items; platforms Xbox360×1,PS4×1): South Park:  The Stick of … | Until Dawn - PlayStation 4
- **GT**: `<a_86><b_12><c_93>` South Park: The Fractured but Whole - PlayStat… _(platform PS4)_ ｜ **native**: `<a_131><b_210><c_0>` Fallout 4 - PlayStation 4 ✗
- **beam top5**: `<a_131><b_210><c_0>`PS4, `<a_201><b_31><c_107>`PS4, `<a_131><b_155><c_206>`Xbo, `<a_201><b_213><c_242>`PS4, `<a_22><b_192><c_20>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=10/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: South Park:  The Stick…, Until Dawn - PlayStati…; novel candidates=0 (**pure history restatement**); genre: action,horror,immersive.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=DRIFT (platform/word-linked) (score1). user's pick is **more history-consistent** than our top-1 (target2>rec1) → we **drifted off** a catchable continuation. Note: target shares word(s) ['park', 'south'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #317 — Category-miss·even top-class (a) wrong
- **History** (3 items; platforms PS4×2,Xbox360×1): South Park:  The Stick of … | Until Dawn - PlayStation 4 | South Park: The Fractured …
- **GT**: `<a_24><b_72><c_142>` Horizon Zero Dawn - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_86><b_18><c_30>` Back to the Future: The Game -… ✗
- **beam top5**: `<a_86><b_18><c_29>`Xbo, `<a_86><b_18><c_30>`Xbo, `<a_131><b_210><c_0>`PS4, `<a_86><b_18><c_2>`PS4, `<a_86><b_68><c_56>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS4 vs rec=XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=7/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: South Park:  The Stick…, Until Dawn - PlayStati…, South Park: The Fractu…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,adventure,role-playing.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**. Note: target shares word(s) ['dawn'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #318 — Category-OK·item wrong
- **History** (4 items; platforms PS4×3,Xbox360×1): South Park:  The Stick of … | Until Dawn - PlayStation 4 | South Park: The Fractured … | Horizon Zero Dawn - PlaySt…
- **GT**: `<a_121><b_155><c_99>` NieR: Automata - Playstation 4 _(platform PS4)_ ｜ **native**: `<a_24><b_72><c_142>` Horizon Zero Dawn - PlayStatio… ✗
- **beam top5**: `<a_24><b_86><c_14>`PS4, `<a_24><b_145><c_101>`PS4, `<a_201><b_31><c_107>`PS4, `<a_24><b_185><c_47>`Xbo, `<a_123><b_142><c_36>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=10/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: South Park:  The Stick…, South Park: The Fractu…, Until Dawn - PlayStati…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #319 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_162×7/10)
- **History** (5 items; platforms ?×2,WiiU×1,Wii×1): JINHEZO Wired Infrared Ray… | New Interchangeable Power … | Pikmin, New Play Control -… | Pikmin & Olimar Amiibo (Su… | Minecraft: Favorites Pack …
- **GT**: `<a_113><b_112><c_109>` Nintendo Wii U Pro Controller - Black _(platform WiiU)_ ｜ **native**: `<a_162><b_125><c_53>` Yoshi amiibo (Super Smash Bros… ✗
- **beam top5**: `<a_162><b_5><c_144>`3DS, `<a_162><b_105><c_210>`?, `<a_162><b_125><c_53>`?, `<a_162><b_122><c_56>`?, `<a_211><b_31><c_154>`3DS
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=WiiU vs rec=3DS); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_162 family 7/10); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/5 history items (coverage 80%), anchored on: JINHEZO Wired Infrared…, New Interchangeable Po…, Pikmin, New Play Contr…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,immersive,accessor.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #320 — Category-miss·even top-class (a) wrong
- **History** (10 items; platforms ?×8,XboxOne×2): Final Fantasy XIV Online | Life is Strange - Episode … | Watch Dogs 2 - Xbox One Di… | Battlefield 1 [Online Game… | Logitech G700s Rechargeabl… | Xenoblade Chronicles X
- **GT**: `<a_113><b_152><c_199>` HORI Compact PlayStand - Zelda Edition, Offici… _(platform Switch)_ ｜ **native**: `<a_1><b_101><c_0>` Xenoblade Chronicles X Special… ✗
- **beam top5**: `<a_1><b_101><c_0>`Wii, `<a_1><b_25><c_254>`3DS, `<a_131><b_224><c_16>`PC, `<a_1><b_173><c_4>`PS4, `<a_1><b_150><c_189>`PS3
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=Switch vs rec=WiiU); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (2 a top-classes); unique(a,b)=8/10, platforms=7, unique titles=10/10.
- **Reasoning quality**: cites 6/10 history items (coverage 60%), anchored on: Final Fantasy XIV Onli…, Xenoblade Chronicles X, Star Wars: The Old Rep…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,multiplayer.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=SUBCLASS-continuation (score3). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #321 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_10×10/10)
- **History** (1 items; platforms PC×1): The Elder Scrolls V: Skyri…
- **GT**: `<a_162><b_125><c_53>` Yoshi amiibo (Super Smash Bros Series) _(platform ?)_ ｜ **native**: `<a_10><b_86><c_40>` The Elder Scrolls V: Skyrim Le… ✗
- **beam top5**: `<a_10><b_53><c_1>`Xbo, `<a_10><b_28><c_234>`Xbo, `<a_10><b_79><c_56>`PC, `<a_10><b_86><c_7>`PS3, `<a_10><b_86><c_68>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_10 family 10/10); unique(a,b)=7/10, platforms=5, unique titles=10/10.
- **Reasoning quality**: cites 1/1 history items (coverage 100%), anchored on: The Elder Scrolls V: S…; novel candidates=0 (**pure history restatement**); genre: action,role-playing,rpg.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #322 — Category-OK·item wrong · BEAM-COLLAPSE (<a_162×10/10)
- **History** (2 items; platforms PC×1,?×1): The Elder Scrolls V: Skyri… | Yoshi amiibo (Super Smash …
- **GT**: `<a_162><b_54><c_123>` Splatoon 3-pack amiibo (Splatoon Series) _(platform ?)_ ｜ **native**: `<a_162><b_122><c_3>` Little Mac amiibo - Japan Impo… ✗
- **beam top5**: `<a_162><b_231><c_30>`?, `<a_162><b_219><c_174>`?, `<a_162><b_122><c_3>`PC, `<a_162><b_219><c_249>`?, `<a_162><b_122><c_195>`?
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; in beam: share-a=10/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_162 family 10/10); unique(a,b)=7/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: The Elder Scrolls V: S…, Yoshi amiibo (Super Sm…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,immersive.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item. Note: target shares word(s) ['amiibo', 'series'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #323 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_162×10/10)
- **History** (3 items; platforms ?×2,PC×1): The Elder Scrolls V: Skyri… | Yoshi amiibo (Super Smash … | Splatoon 3-pack amiibo (Sp…
- **GT**: `<a_157><b_85><c_178>` PDP Donkey Kong Display _(platform ?)_ ｜ **native**: `<a_162><b_172><c_85>` Tom Nook Amiibo (Animal Crossi… ✗
- **beam top5**: `<a_162><b_231><c_30>`?, `<a_162><b_251><c_136>`Wii, `<a_162><b_172><c_85>`?, `<a_162><b_122><c_56>`?, `<a_162><b_172><c_0>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_162 family 10/10); unique(a,b)=7/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Yoshi amiibo (Super Sm…, Splatoon 3-pack amiibo…, The Elder Scrolls V: S…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,immersive.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #324 — Category-OK·item wrong · BEAM-COLLAPSE (<a_162×10/10)
- **History** (4 items; platforms ?×3,PC×1): The Elder Scrolls V: Skyri… | Yoshi amiibo (Super Smash … | Splatoon 3-pack amiibo (Sp… | PDP Donkey Kong Display
- **GT**: `<a_162><b_219><c_174>` Shulk amiibo (Super Smash Bros Series) _(platform ?)_ ｜ **native**: `<a_162><b_172><c_85>` Tom Nook Amiibo (Animal Crossi… ✗
- **beam top5**: `<a_162><b_172><c_85>`?, `<a_162><b_105><c_210>`?, `<a_162><b_251><c_136>`Wii, `<a_162><b_231><c_30>`?, `<a_162><b_172><c_0>`?
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; in beam: share-a=10/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_162 family 10/10); unique(a,b)=8/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Yoshi amiibo (Super Sm…, Splatoon 3-pack amiibo…, PDP Donkey Kong Displa…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,immersive,nostalg.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item. Note: target shares word(s) ['amiibo', 'bros', 'series', 'smash', 'super'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #325 — Category-miss·even top-class (a) wrong
- **History** (9 items; platforms XboxOne×7,?×1,PS4×1): Nyko Modular Power Station… | Battlefield Hardline - Xbo… | Gears of War 4 - Xbox One | Wolfenstein: The Old Blood… | Homefront: The Revolution … | Rise of the Tomb Raider: 2…
- **GT**: `<a_24><b_72><c_142>` Horizon Zero Dawn - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_39><b_77><c_105>` Call of Duty: Infinite Warfare… ✗
- **beam top5**: `<a_39><b_77><c_105>`Xbo, `<a_39><b_51><c_21>`Xbo, `<a_123><b_58><c_16>`Xbo, `<a_39><b_77><c_69>`Xbo, `<a_123><b_188><c_70>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS4 vs rec=XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (2 a top-classes); unique(a,b)=8/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 6/9 history items (coverage 67%), anchored on: Halo 5: Guardians - Li…, Wolfenstein: The New O…, Battlefield Hardline -…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,shooter,multiplayer.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=DRIFT (platform/word-linked) (score1). user's pick is **more history-consistent** than our top-1 (target2>rec1) → we **drifted off** a catchable continuation.

### #326 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_22×7/10)
- **History** (7 items; platforms PS4×3,?×3,DS×1): The Sims 4 [Online Game Co… | Sleeping Dogs: Definitive … | The Sims 4 Get to Work [On… | The Sims 4 Kids Room Stuff… | HAVIT HV-MS672 3200DPI Wir… | Prey - Pre-load - PS4 Digi…
- **GT**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - PS4 Digital Code _(platform PS4)_ ｜ **native**: `<a_22><b_173><c_203>` The Sims 4 - Movie Hangout Stu… ✗
- **beam top5**: `<a_22><b_173><c_203>`?, `<a_22><b_190><c_180>`?, `<a_22><b_89><c_201>`?, `<a_22><b_173><c_9>`?, `<a_201><b_31><c_107>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_22 family 7/10); unique(a,b)=8/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 5/7 history items (coverage 71%), anchored on: The Sims 4 [Online Gam…, The Sims 4 Kids Room S…, Assassins Creed Syndic…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**. Note: target shares word(s) ['code', 'digital'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #327 — Category-miss·even top-class (a) wrong
- **History** (1 items; platforms PS4×1): Uncharted 4: A Thief's End…
- **GT**: `<a_13><b_68><c_173>` Lost Planet: Extreme Condition - Playstation 3 _(platform PS3)_ ｜ **native**: `<a_201><b_213><c_242>` The Last of Us Remastered - Pl… ✗
- **beam top5**: `<a_123><b_72><c_7>`PS4, `<a_201><b_213><c_242>`PS4, `<a_201><b_145><c_9>`PS4, `<a_24><b_145><c_101>`PS4, `<a_201><b_31><c_107>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS3 vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=10/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 1/1 history items (coverage 100%), anchored on: Uncharted 4: A Thief's…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=DRIFT (platform/word-linked) (score1). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #328 — Hit@6
- **History** (2 items; platforms PS4×2): Alien: Isolation - PlaySta… | Dying Light: The Following…
- **GT**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - PS4 Digital Code _(platform PS4)_ ｜ **native**: `<a_123><b_142><c_36>` 7 Days to Die - PlayStation 4 ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_201><b_213><c_242>`PS4, `<a_123><b_78><c_71>`PS4, `<a_201><b_239><c_3>`PS4, `<a_123><b_76><c_232>`PS4
- **Rec↔GT gap**: correct item at beam rank 6, pred[0] prefix-depth only 0/3; platform consistent(PS4); in beam: share-a=6/10, share-(a,b)=1/10.
- **Beam diversity**: **Medium** (2 a top-classes); unique(a,b)=10/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: Alien: Isolation - Pla…, Dying Light: The Follo…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=DRIFT (platform/word-linked) (score1). target is a sensible CLASS-cont and **was caught**.

### #329 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_123×10/10)
- **History** (3 items; platforms PS4×3): Alien: Isolation - PlaySta… | Dying Light: The Following… | Resident Evil 7: Biohazard…
- **GT**: `<a_201><b_45><c_166>` Prey - Pre-load - PS4 Digital Code _(platform PS4)_ ｜ **native**: `<a_123><b_58><c_16>` Resident Evil 7 Biohazard - Xb… ✗
- **beam top5**: `<a_123><b_58><c_16>`Xbo, `<a_123><b_160><c_188>`PS4, `<a_123><b_78><c_71>`PS4, `<a_123><b_158><c_19>`PS4, `<a_123><b_100><c_33>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS4 vs rec=XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_123 family 10/10); unique(a,b)=10/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Alien: Isolation - Pla…, Dying Light: The Follo…, Resident Evil 7: Bioha…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=SUBCLASS-continuation (score3). we recommended something **more history-consistent** than the user's actual pick (rec3>target1) → **model too conservative / user more exploratory**. Note: target shares word(s) ['code', 'digital'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #330 — Category-miss·even top-class (a) wrong
- **History** (5 items; platforms 3DS×3,?×1,PS4×1): The Legend of Legacy - Nin… | PDP New Nintendo 3DS XL Cl… | BenQ ZOWIE FK1 E-Sports Am… | Shin Megami Tensei IV: Apo… | Resident Evil 7: Biohazard…
- **GT**: `<a_61><b_166><c_249>` Thrustmaster T150 RS Racing Wheel for PlayStat… _(platform PS3)_ ｜ **native**: `<a_1><b_116><c_233>` Dragon Quest Builders - PlaySt… ✗
- **beam top5**: `<a_1><b_116><c_233>`PS4, `<a_1><b_173><c_4>`PS4, `<a_1><b_25><c_254>`3DS, `<a_1><b_163><c_179>`3DS, `<a_1><b_150><c_189>`PS3
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS3 vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=10/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 4/5 history items (coverage 80%), anchored on: The Legend of Legacy -…, Shin Megami Tensei IV:…, PDP New Nintendo 3DS X…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,immersive.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=DRIFT (platform/word-linked) (score1). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #331 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_208×10/10)
- **History** (3 items; platforms PS4×2,PSVita×1): Controller Gear PS4 Contro… | Dead or Alive Xtreme 3 Ven… | Resident Evil Origins Coll…
- **GT**: `<a_201><b_239><c_225>` Resident Evil Origins Collection - Xbox One St… _(platform XboxOne)_ ｜ **native**: `<a_208><b_87><c_200>` DEAD OR ALIVE 5 Last Round - P… ✗
- **beam top5**: `<a_208><b_196><c_65>`PS, `<a_208><b_129><c_14>`Xbo, `<a_208><b_87><c_200>`PS4, `<a_208><b_135><c_101>`?, `<a_208><b_209><c_219>`PSV
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=XboxOne vs rec=PS2); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_208 family 10/10); unique(a,b)=9/10, platforms=5, unique titles=10/10.
- **Reasoning quality**: cites 2/3 history items (coverage 67%), anchored on: Resident Evil Origins …, Dead or Alive Xtreme 3…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,fighting,horror.
- **Target sensibility (ceiling)**: target=SUBCLASS-continuation (score3); our pred[0]=CLASS-continuation (score2). user's pick is **more history-consistent** than our top-1 (target3>rec2) → we **drifted off** a catchable continuation. Note: target shares word(s) ['collection', 'evil', 'origins', 'resident'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #332 — Category-OK·item wrong
- **History** (4 items; platforms PS4×4): UNCHARTED: The Nathan Drak… | Resident Evil 4 - PlayStat… | The King of Fighters XIV: … | Titanfall 2 - PlayStation …
- **GT**: `<a_201><b_18><c_56>` Mass Effect Andromeda - Pre-load - PS4 Digital… _(platform PS4)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_39><b_51><c_21>`Xbo, `<a_39><b_78><c_54>`PS4, `<a_123><b_58><c_78>`PS4, `<a_123><b_100><c_33>`PS4, `<a_24><b_72><c_142>`PS4
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform mismatch(GT=PS4 vs rec=XboxOne); in beam: share-a=1/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: UNCHARTED: The Nathan …, Resident Evil 4 - Play…, The King of Fighters X…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=SUBCLASS-continuation (score3). we recommended something **more history-consistent** than the user's actual pick (rec3>target1) → **model too conservative / user more exploratory**.

### #333 — Near-miss·same (a,b) subcluster, only c differs
- **History** (7 items; platforms PS×5,PS2×1,?×1): Resident Evil: Code Veroni… | PlayStation 2 Console Slim… | God of War - PlayStation 2 | Scarface The World Is Your… | Destroy All Humans - PlayS… | The Suffering
- **GT**: `<a_80><b_59><c_15>` Resident Evil 6 - Playstation 3 _(platform PS3)_ ｜ **native**: `<a_71><b_30><c_178>` The Suffering ✗
- **beam top5**: `<a_71><b_171><c_196>`PS3, `<a_71><b_197><c_195>`?, `<a_71><b_204><c_152>`?, `<a_71><b_223><c_141>`?, `<a_80><b_59><c_176>`Gam
- **Rec↔GT gap**: beam's closest item shares (a,b) subcluster with GT, only c differs (same series/SKU), still missed; platform consistent(PS3); in beam: share-a=4/10, share-(a,b)=1/10.
- **Beam diversity**: **Medium** (2 a top-classes); unique(a,b)=8/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 6/7 history items (coverage 86%), anchored on: Primal - PlayStation 2, God of War - PlayStati…, Scarface The World Is …; novel candidates=0 (**pure history restatement**); templated opening; genre: action,immersive,narrative.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**. Note: target shares word(s) ['evil', 'resident'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #334 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_162×10/10)
- **History** (7 items; platforms Wii×2,GameCube×2,?×2): HDE 128MB (2048 Blocks) Bl… | Gamecube Controller For Ni… | Gamecube Controller For Ni… | Amiibo Marth (Japanese imp… | Mario - Gold amiibo (Super… | Nintendo NFC Reader/Writer…
- **GT**: `<a_214><b_24><c_0>` HAVIT HV-MS672 3200DPI Wired Mouse, 4 Adjustab… _(platform ?)_ ｜ **native**: `<a_162><b_251><c_136>` Animal Crossing: amiibo Festiv… ✗
- **beam top5**: `<a_162><b_118><c_196>`?, `<a_162><b_251><c_136>`Wii, `<a_162><b_231><c_30>`?, `<a_162><b_49><c_93>`?, `<a_162><b_172><c_85>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_162 family 10/10); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/6 history items (coverage 67%), anchored on: Generic Orange Spice C…, Amiibo Marth (Japanese…, Gamecube Controller Fo…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,accessor.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**. Note: target shares word(s) ['black'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #335 — Category-miss·even top-class (a) wrong
- **History** (10 items; platforms 3DS×6,PS4×2,PS×1): Fire Emblem Fates: Birthri… | HORI Duraflexi Clear Prote… | Nintendo Switch Travel Pou… | Street Fighter V - PlaySta… | Nintendo Selects: The Lege… | Fire Emblem Fates: Map Pac…
- **GT**: `<a_61><b_214><c_225>` PDP Talon Media Remote Control for Xbox One, T… _(platform XboxOne)_ ｜ **native**: `<a_232><b_79><c_116>` Fire Emblem Fates: Conquest DL… ✗
- **beam top5**: `<a_232><b_79><c_116>`3DS, `<a_232><b_68><c_178>`3DS, `<a_162><b_125><c_53>`?, `<a_232><b_68><c_10>`3DS, `<a_162><b_251><c_136>`Wii
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=XboxOne vs rec=3DS); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=8/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 6/10 history items (coverage 60%), anchored on: Mad Catz Street Fighte…, Tom Clancy's The Divis…, HORI Screen Protective…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,adventure,rpg.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=SUBCLASS-continuation (score3). we recommended something **more history-consistent** than the user's actual pick (rec3>target2) → **model too conservative / user more exploratory**.

### #336 — Category-miss·even top-class (a) wrong
- **History** (3 items; platforms PS4×3): UNCHARTED: The Nathan Drak… | Street Fighter V - PlaySta… | God of War 3 Remastered - …
- **GT**: `<a_231><b_33><c_2>` ZD-N Vibration-Feedback USB Wired Gamepad Gami… _(platform PS3)_ ｜ **native**: `<a_201><b_145><c_9>` The Witcher 3: Wild Hunt - Pla… ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_141><b_73><c_216>`PS4, `<a_24><b_145><c_101>`PS4, `<a_201><b_36><c_195>`PS4, `<a_201><b_145><c_9>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS3 vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=10/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: UNCHARTED: The Nathan …, Street Fighter V - Pla…, God of War 3 Remastere…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=DRIFT (platform/word-linked) (score1). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #337 — Category-miss·even top-class (a) wrong
- **History** (4 items; platforms PS4×3,3DS×1): PlayStation 4 Console - De… | Final Fantasy XV - PlaySta… | Hyrule Warriors: Legends -… | Overwatch - Origins Editio…
- **GT**: `<a_201><b_151><c_255>` Playstation Plus: 3 Month Membership [Digital … _(platform PS-generic)_ ｜ **native**: `<a_131><b_224><c_68>` Overwatch - Origins Edition - … ✗
- **beam top5**: `<a_1><b_116><c_233>`PS4, `<a_131><b_209><c_151>`PS4, `<a_131><b_224><c_68>`PS4, `<a_194><b_15><c_66>`PS4, `<a_1><b_43><c_207>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS-generic vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (7 distinct a top-classes); unique(a,b)=9/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 3/4 history items (coverage 75%), anchored on: Final Fantasy XV - Pla…, Overwatch - Origins Ed…, Hyrule Warriors: Legen…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,adventure,rpg.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=DRIFT (platform/word-linked) (score1). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #338 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_39×9/10)
- **History** (3 items; platforms Xbox360×3): Call of Duty: Modern Warfa… | Mortal Kombat: Komplete Ed… | Call of Duty: Advanced War…
- **GT**: `<a_245><b_155><c_109>` Middle Earth: Shadow of Mordor - Xbox 360 _(platform Xbox360)_ ｜ **native**: `<a_39><b_182><c_109>` Call of Duty: Black Ops Combo … ✗
- **beam top5**: `<a_39><b_114><c_237>`Xbo, `<a_39><b_182><c_247>`PS4, `<a_39><b_182><c_109>`Xbo, `<a_39><b_114><c_209>`Xbo, `<a_39><b_224><c_27>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=Xbox360 vs rec=XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_39 family 9/10); unique(a,b)=5/10, platforms=5, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Call of Duty: Modern W…, Mortal Kombat: Komplet…, Call of Duty: Advanced…; novel candidates=0 (**pure history restatement**); genre: action,shooter,strategy.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=SUBCLASS-continuation (score3). we recommended something **more history-consistent** than the user's actual pick (rec3>target1) → **model too conservative / user more exploratory**.

### #339 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_1×10/10)
- **History** (10 items; platforms XboxOne×5,PSVita×4,?×1): Ori and the Blind Forest: … | Resident Evil: Revelations… | Child of Light - PlayStati… | Rare Replay - Xbox One | Mario Kart 7 | Grand Kingdom - PlayStatio…
- **GT**: `<a_123><b_178><c_34>` State of Decay- Year-One Survival Edition _(platform ?)_ ｜ **native**: `<a_1><b_150><c_189>` Legend of Heroes: Trails of Co… ✗
- **beam top5**: `<a_1><b_242><c_201>`PS4, `<a_1><b_68><c_121>`PS4, `<a_1><b_150><c_189>`PS3, `<a_1><b_200><c_195>`?, `<a_1><b_25><c_254>`3DS
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_1 family 10/10); unique(a,b)=10/10, platforms=5, unique titles=10/10.
- **Reasoning quality**: cites 6/10 history items (coverage 60%), anchored on: Yomawari: Night Alone …, Child of Light - PlayS…, Mighty No. 9 - Xbox On…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item.

### #340 — Category-miss·even top-class (a) wrong
- **History** (1 items; platforms ?×1): Animal Crossing: New Leaf
- **GT**: `<a_195><b_36><c_218>` Fire Emblem: Awakening _(platform ?)_ ｜ **native**: `<a_211><b_105><c_223>` Animal Crossing: Happy Home De… ✗
- **beam top5**: `<a_162><b_251><c_136>`Wii, `<a_119><b_185><c_105>`3DS, `<a_211><b_105><c_223>`3DS, `<a_211><b_112><c_5>`3DS, `<a_162><b_125><c_53>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=9/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 1/1 history items (coverage 100%), anchored on: Animal Crossing: New L…; novel candidates=0 (**pure history restatement**); genre: action,role-playing,simulation.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=DRIFT (platform/word-linked) (score1). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #341 — Category-OK·item wrong
- **History** (2 items; platforms ?×2): Animal Crossing: New Leaf | Fire Emblem: Awakening
- **GT**: `<a_216><b_93><c_101>` The Legend of Zelda: A Link Between Worlds 3D _(platform ?)_ ｜ **native**: `<a_211><b_142><c_127>` Pokemon Conquest ✗
- **beam top5**: `<a_211><b_142><c_127>`?, `<a_216><b_51><c_130>`3DS, `<a_211><b_105><c_223>`3DS, `<a_211><b_88><c_34>`?, `<a_211><b_112><c_5>`3DS
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; in beam: share-a=3/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=10/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: Animal Crossing: New L…, Fire Emblem: Awakening; novel candidates=0 (**pure history restatement**); templated opening; genre: action,strategy,simulation.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #342 — Hit@7 · RERANK-HARM
- **History** (3 items; platforms ?×2,DS×1): Animal Crossing: New Leaf | Fire Emblem: Awakening | The Legend of Zelda: A Lin…
- **GT**: `<a_216><b_112><c_119>` The Legend of Zelda: Majora's Mask 3D _(platform ?)_ ｜ **native**: `<a_216><b_112><c_119>` The Legend of Zelda: Majora's … ✓
- **beam top5**: `<a_216><b_51><c_130>`3DS, `<a_216><b_112><c_114>`Wii, `<a_211><b_105><c_223>`3DS, `<a_211><b_112><c_5>`3DS, `<a_216><b_142><c_77>`3DS
- **Rec↔GT gap**: correct item at beam rank 7, pred[0] prefix-depth only 1/3; in beam: share-a=6/10, share-(a,b)=2/10.
- **Beam diversity**: **Medium** (2 a top-classes); unique(a,b)=9/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Animal Crossing: New L…, Fire Emblem: Awakening, The Legend of Zelda: A…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,adventure,puzzle.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). target is a sensible CLASS-cont and **was caught**.

### #343 — Category-OK·item wrong · BEAM-COLLAPSE (<a_216×8/10)
- **History** (4 items; platforms ?×3,DS×1): Animal Crossing: New Leaf | Fire Emblem: Awakening | The Legend of Zelda: A Lin… | The Legend of Zelda: Major…
- **GT**: `<a_216><b_44><c_79>` Bravely Second: End Layer - Nintendo 3DS _(platform 3DS)_ ｜ **native**: `<a_216><b_142><c_77>` Bravely Default - Nintendo 3DS ✗
- **beam top5**: `<a_216><b_51><c_130>`3DS, `<a_216><b_235><c_168>`3DS, `<a_216><b_112><c_114>`Wii, `<a_216><b_142><c_77>`3DS, `<a_216><b_219><c_158>`3DS
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform consistent(3DS); in beam: share-a=8/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_216 family 8/10); unique(a,b)=10/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 2/4 history items (coverage 50%), anchored on: Animal Crossing: New L…, The Legend of Zelda: A…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,adventure,rpg.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item.

### #344 — Category-OK·item wrong · BEAM-COLLAPSE (<a_216×8/10)
- **History** (5 items; platforms ?×3,DS×1,3DS×1): Animal Crossing: New Leaf | Fire Emblem: Awakening | The Legend of Zelda: A Lin… | The Legend of Zelda: Major… | Bravely Second: End Layer …
- **GT**: `<a_211><b_159><c_123>` Pok&eacute;mon Moon - Nintendo 3DS _(platform 3DS)_ ｜ **native**: `<a_216><b_235><c_168>` Final Fantasy Explorers - Nint… ✗
- **beam top5**: `<a_1><b_25><c_254>`3DS, `<a_216><b_235><c_168>`3DS, `<a_216><b_51><c_130>`3DS, `<a_216><b_219><c_158>`3DS, `<a_211><b_112><c_5>`3DS
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform consistent(3DS); in beam: share-a=1/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_216 family 8/10); unique(a,b)=10/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/5 history items (coverage 80%), anchored on: Animal Crossing: New L…, The Legend of Zelda: A…, The Legend of Zelda: M…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,adventure,rpg.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=DRIFT (platform/word-linked) (score1). user's pick is **more history-consistent** than our top-1 (target2>rec1) → we **drifted off** a catchable continuation.

### #345 — Hit@1
- **History** (6 items; platforms ?×3,3DS×2,DS×1): Animal Crossing: New Leaf | Fire Emblem: Awakening | The Legend of Zelda: A Lin… | The Legend of Zelda: Major… | Bravely Second: End Layer … | Pok&eacute;mon Moon - Nint…
- **GT**: `<a_211><b_159><c_71>` Pok&eacute;mon Sun - Nintendo 3DS _(platform 3DS)_ ｜ **native**: `<a_211><b_159><c_71>` Pok&eacute;mon Sun - Nintendo … ✓
- **beam top5**: `<a_211><b_159><c_71>`3DS, `<a_216><b_159><c_141>`3DS, `<a_216><b_76><c_23>`3DS, `<a_1><b_25><c_254>`3DS, `<a_216><b_48><c_110>`3DS
- **Rec↔GT gap**: top-1 exact hit.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=8/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 5/6 history items (coverage 83%), anchored on: Animal Crossing: New L…, The Legend of Zelda: M…, Pok&eacute;mon Moon - …; novel candidates=0 (**pure history restatement**); genre: adventure,rpg,immersive.
- **Target sensibility (ceiling)**: target=SUBCLASS-continuation (score3); our pred[0]=SUBCLASS-continuation (score3). target is a sensible SUBCLASS-cont and **was caught**.

### #346 — Category-OK·item wrong
- **History** (7 items; platforms ?×3,3DS×3,DS×1): Fire Emblem: Awakening | The Legend of Zelda: A Lin… | The Legend of Zelda: Major… | Bravely Second: End Layer … | Pok&eacute;mon Moon - Nint… | Pok&eacute;mon Sun - Ninte…
- **GT**: `<a_216><b_92><c_192>` Etrian Odyssey Untold: The Millennium Girl - N… _(platform 3DS)_ ｜ **native**: `<a_211><b_159><c_71>` Pok&eacute;mon Sun - Nintendo … ✗
- **beam top5**: `<a_1><b_25><c_254>`3DS, `<a_216><b_48><c_110>`3DS, `<a_1><b_25><c_194>`3DS, `<a_216><b_159><c_141>`3DS, `<a_211><b_159><c_71>`3DS
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform consistent(3DS); in beam: share-a=3/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=8/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/7 history items (coverage 57%), anchored on: Animal Crossing: New L…, The Legend of Zelda: M…, Pok&eacute;mon Moon - …; novel candidates=0 (**pure history restatement**); templated opening; genre: action,adventure,rpg.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=DRIFT (platform/word-linked) (score1). user's pick is **more history-consistent** than our top-1 (target2>rec1) → we **drifted off** a catchable continuation.

### #347 — Category-OK·item wrong
- **History** (8 items; platforms 3DS×4,?×3,DS×1): The Legend of Zelda: A Lin… | The Legend of Zelda: Major… | Bravely Second: End Layer … | Pok&eacute;mon Moon - Nint… | Pok&eacute;mon Sun - Ninte… | Etrian Odyssey Untold: The…
- **GT**: `<a_216><b_146><c_129>` The Legend of Legacy - Nintendo 3DS _(platform 3DS)_ ｜ **native**: `<a_216><b_48><c_110>` Dragon Quest VIII: Journey of … ✗
- **beam top5**: `<a_216><b_48><c_110>`3DS, `<a_216><b_76><c_23>`3DS, `<a_1><b_25><c_254>`3DS, `<a_216><b_159><c_141>`3DS, `<a_211><b_31><c_154>`3DS
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform consistent(3DS); in beam: share-a=4/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=8/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 5/8 history items (coverage 62%), anchored on: Animal Crossing: New L…, The Legend of Zelda: M…, Etrian Odyssey Untold:…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,adventure,rpg.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item. Note: target shares word(s) ['legend'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #348 — Category-OK·item wrong
- **History** (1 items; platforms XboxOne×1): Sniper Elite III - Xbox On…
- **GT**: `<a_123><b_189><c_223>` Red Dead Redemption: Game of the Year Edition … _(platform XboxOne)_ ｜ **native**: `<a_123><b_72><c_191>` Far Cry 4 - Xbox One ✗
- **beam top5**: `<a_123><b_72><c_191>`Xbo, `<a_123><b_246><c_254>`Xbo, `<a_123><b_72><c_7>`PS4, `<a_118><b_1><c_2>`Xbo, `<a_123><b_72><c_182>`Xbo
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform consistent(XboxOne); in beam: share-a=6/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=7/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 1/1 history items (coverage 100%), anchored on: Sniper Elite III - Xbo…; novel candidates=0 (**pure history restatement**); genre: action,strategy,immersive.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item.

### #349 — Category-OK·item wrong · BEAM-COLLAPSE (<a_140×9/10)
- **History** (2 items; platforms Xbox360×2): Medal of Honor Warfighter … | Tom Clancy's Ghost Recon: …
- **GT**: `<a_71><b_33><c_62>` Assassin's Creed IV Black Flag - Xbox 360 _(platform Xbox360)_ ｜ **native**: `<a_140><b_212><c_230>` Homefront - Xbox 360 ✗
- **beam top5**: `<a_140><b_212><c_230>`Xbo, `<a_140><b_221><c_16>`PC, `<a_80><b_162><c_230>`Xbo, `<a_140><b_161><c_25>`Xbo, `<a_140><b_221><c_161>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(Xbox360); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_140 family 9/10); unique(a,b)=6/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: Medal of Honor Warfigh…, Tom Clancy's Ghost Rec…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,shooter,strategy.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #350 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_140×7/10)
- **History** (3 items; platforms Xbox360×3): Medal of Honor Warfighter … | Tom Clancy's Ghost Recon: … | Assassin's Creed IV Black …
- **GT**: `<a_24><b_152><c_33>` Rise of the Tomb Raider - Xbox 360 - Xbox 360 … _(platform Xbox360)_ ｜ **native**: `<a_140><b_65><c_232>` Tom Clancy's Ghost Recon: Futu… ✗
- **beam top5**: `<a_140><b_221><c_16>`PC, `<a_140><b_212><c_230>`Xbo, `<a_140><b_50><c_3>`PS4, `<a_80><b_69><c_76>`Xbo, `<a_39><b_204><c_1>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=Xbox360 vs rec=PC); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_140 family 7/10); unique(a,b)=8/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Medal of Honor Warfigh…, Tom Clancy's Ghost Rec…, Assassin's Creed IV Bl…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,shooter,strategy.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #351 — Category-OK·item wrong · BEAM-COLLAPSE (<a_24×7/10)
- **History** (3 items; platforms PS3×3): Dragon Age Inquisition - S… | Bound by Flame - PlayStati… | Metro Last Light - Playsta…
- **GT**: `<a_24><b_72><c_142>` Horizon Zero Dawn - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_24><b_176><c_166>` Metro Last Light - Playstation… ✗
- **beam top5**: `<a_24><b_51><c_181>`PS3, `<a_24><b_51><c_183>`PS, `<a_24><b_252><c_227>`Xbo, `<a_24><b_44><c_74>`PS3, `<a_24><b_247><c_115>`PS4
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform mismatch(GT=PS4 vs rec=PS3); in beam: share-a=7/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_24 family 7/10); unique(a,b)=8/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Dragon Age Inquisition…, Bound by Flame - PlayS…, Metro Last Light - Pla…; novel candidates=0 (**pure history restatement**); genre: action,role-playing,immersive.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item.

### #352 — Category-OK·item wrong
- **History** (10 items; platforms XboxOne×10): Agents of Mayhem - Xbox On… | Assassin&rsquo;s Creed Syn… | Transformers Devastation -… | Madden NFL 16 - Xbox One | Middle Earth: Shadow of Mo… | Tekken 7 - Xbox One
- **GT**: `<a_205><b_89><c_183>` The Golf Club: Collector's Edition - Xbox One _(platform XboxOne)_ ｜ **native**: `<a_123><b_76><c_255>` Far Cry Primal - Xbox One Stan… ✗
- **beam top5**: `<a_131><b_155><c_206>`Xbo, `<a_123><b_76><c_255>`Xbo, `<a_131><b_55><c_86>`Xbo, `<a_39><b_77><c_69>`Xbo, `<a_39><b_69><c_69>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=10/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 7/10 history items (coverage 70%), anchored on: Assassin's Creed Unity…, Battlefield 1 - Xbox O…, Batman: Arkham Knight …; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item.

### #353 — Category-miss·even top-class (a) wrong
- **History** (3 items; platforms Xbox×1,Xbox360×1,?×1): James Bond 007 Nightfire -… | Tom Clancy's Ghost Recon A… | Ace Combat 6: Fires of Lib…
- **GT**: `<a_8><b_141><c_167>` Nyko Charge Block Solo - Controller Charging S… _(platform XboxOne)_ ｜ **native**: `<a_140><b_242><c_197>` Halo 2 - Xbox ✗
- **beam top5**: `<a_140><b_242><c_197>`Xbo, `<a_39><b_124><c_106>`?, `<a_39><b_40><c_248>`Xbo, `<a_39><b_211><c_56>`Xbo, `<a_140><b_65><c_232>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=XboxOne vs rec=Xbox); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=9/10, platforms=5, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: James Bond 007 Nightfi…, Tom Clancy's Ghost Rec…, Ace Combat 6: Fires of…; novel candidates=0 (**pure history restatement**); genre: action,shooter,strategy.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #354 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_162×8/10)
- **History** (7 items; platforms XboxOne×2,?×2,Xbox×1): Logitech G602 Lag-Free Wir… | Xbox One Wireless Controll… | Microsoft Xbox Wireless Ad… | DualShock 4 Wireless Contr… | Yoshi amiibo (Super Smash … | Nintendo Boo amiibo (SM Se…
- **GT**: `<a_71><b_251><c_145>` Dark Souls: Prepare To Die Edition [Online Gam… _(platform ?)_ ｜ **native**: `<a_162><b_130><c_51>` Nintendo Wario amiibo (SM Seri… ✗
- **beam top5**: `<a_162><b_130><c_51>`Wii, `<a_162><b_222><c_61>`Wii, `<a_162><b_130><c_1>`Wii, `<a_162><b_130><c_2>`Wii, `<a_162><b_172><c_85>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_162 family 8/10); unique(a,b)=5/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/7 history items (coverage 57%), anchored on: Xbox One Chatpad + Cha…, Xbox One Wireless Cont…, Yoshi amiibo (Super Sm…; novel candidates=0 (**pure history restatement**); genre: action,nostalg,peripheral.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=SUBCLASS-continuation (score3). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #355 — Category-OK·item wrong · BEAM-COLLAPSE (<a_162×10/10)
- **History** (8 items; platforms ?×3,XboxOne×2,Xbox×1): Xbox One Wireless Controll… | Microsoft Xbox Wireless Ad… | DualShock 4 Wireless Contr… | Yoshi amiibo (Super Smash … | Nintendo Boo amiibo (SM Se… | Dark Souls: Prepare To Die…
- **GT**: `<a_162><b_106><c_211>` Jigglypuff amiibo - Japan Import (Super Smash … _(platform ?)_ ｜ **native**: `<a_162><b_130><c_51>` Nintendo Wario amiibo (SM Seri… ✗
- **beam top5**: `<a_162><b_81><c_26>`?, `<a_162><b_130><c_51>`Wii, `<a_162><b_130><c_1>`Wii, `<a_162><b_231><c_30>`?, `<a_162><b_222><c_61>`Wii
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; in beam: share-a=10/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_162 family 10/10); unique(a,b)=8/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 5/8 history items (coverage 62%), anchored on: Xbox One Chatpad + Cha…, Xbox One Wireless Cont…, Yoshi amiibo (Super Sm…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,immersive.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item. Note: target shares word(s) ['amiibo', 'bros', 'series', 'smash', 'super'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #356 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_250×9/10)
- **History** (9 items; platforms WiiU×3,PS4×3,?×2): Assassin's Creed: Syndicat… | Far Cry Primal - PlayStati… | Mario Party 10 | Eastvita Full 1080p 720P H… | Nintendo Selects: Donkey K… | The Legend of Zelda: Breat…
- **GT**: `<a_7><b_181><c_27>` Xbox One Chat Headset _(platform XboxOne)_ ｜ **native**: `<a_250><b_116><c_226>` Yoshi's Woolly World -  Wii U ✗
- **beam top5**: `<a_250><b_112><c_111>`Wii, `<a_250><b_116><c_22>`Wii, `<a_250><b_238><c_255>`Wii, `<a_250><b_121><c_156>`?, `<a_250><b_116><c_226>`Wii
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=XboxOne vs rec=WiiU); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_250 family 9/10); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 6/9 history items (coverage 67%), anchored on: Super Mario Maker - Ni…, Nintendo Selects: Donk…, The Last of Us Remaste…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #357 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_194×7/10)
- **History** (1 items; platforms PSVita×1): FINAL FANTASY X|X-2 HD Rem…
- **GT**: `<a_61><b_131><c_197>` Microsoft Xbox Wireless Adapter for Windows 10 _(platform Xbox)_ ｜ **native**: `<a_194><b_21><c_76>` Final Fantasy X X-2 HD Remaste… ✗
- **beam top5**: `<a_194><b_121><c_62>`PS4, `<a_1><b_150><c_189>`PS3, `<a_194><b_21><c_219>`PS4, `<a_194><b_21><c_76>`PS4, `<a_194><b_219><c_28>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=Xbox vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_194 family 7/10); unique(a,b)=8/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 1/1 history items (coverage 100%), anchored on: FINAL FANTASY X|X-2 HD…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,immersive.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #358 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_61×8/10)
- **History** (2 items; platforms PSVita×1,Xbox×1): FINAL FANTASY X|X-2 HD Rem… | Microsoft Xbox Wireless Ad…
- **GT**: `<a_250><b_92><c_44>` Nintendo Selects: Donkey Kong Country: Tropica… _(platform ?)_ ｜ **native**: `<a_61><b_131><c_197>` Microsoft Xbox Wireless Adapte… ✗
- **beam top5**: `<a_61><b_167><c_197>`Xbo, `<a_61><b_111><c_197>`Xbo, `<a_61><b_131><c_197>`Xbo, `<a_61><b_53><c_46>`Xbo, `<a_61><b_111><c_109>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_61 family 8/10); unique(a,b)=8/10, platforms=5, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: FINAL FANTASY X|X-2 HD…, Microsoft Xbox Wireles…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,immersive.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #359 — Category-miss·even top-class (a) wrong
- **History** (3 items; platforms PSVita×1,Xbox×1,?×1): FINAL FANTASY X|X-2 HD Rem… | Microsoft Xbox Wireless Ad… | Nintendo Selects: Donkey K…
- **GT**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - PS4 Digital Code _(platform PS4)_ ｜ **native**: `<a_250><b_238><c_255>` Mario Party 10 + Mario amiibo … ✗
- **beam top5**: `<a_61><b_131><c_197>`Xbo, `<a_250><b_238><c_255>`Wii, `<a_250><b_55><c_95>`?, `<a_113><b_29><c_66>`Wii, `<a_250><b_92><c_0>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS4 vs rec=Xbox); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=8/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: FINAL FANTASY X|X-2 HD…, Nintendo Selects: Donk…, Microsoft Xbox Wireles…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,adventure,rpg.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=SUBCLASS-continuation (score3). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #360 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_123×9/10)
- **History** (4 items; platforms PSVita×1,Xbox×1,?×1): FINAL FANTASY X|X-2 HD Rem… | Microsoft Xbox Wireless Ad… | Nintendo Selects: Donkey K… | Resident Evil 7: Biohazard…
- **GT**: `<a_111><b_130><c_0>` Just Dance 2017 - Wii U _(platform WiiU)_ ｜ **native**: `<a_123><b_58><c_16>` Resident Evil 7 Biohazard - Xb… ✗
- **beam top5**: `<a_123><b_58><c_16>`Xbo, `<a_123><b_171><c_44>`Xbo, `<a_123><b_188><c_192>`PS4, `<a_123><b_33><c_93>`PS4, `<a_123><b_33><c_95>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=WiiU vs rec=XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_123 family 9/10); unique(a,b)=8/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 3/4 history items (coverage 75%), anchored on: FINAL FANTASY X|X-2 HD…, Resident Evil 7: Bioha…, Microsoft Xbox Wireles…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=SUBCLASS-continuation (score3). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #361 — Hit@5
- **History** (8 items; platforms PS4×8): Until Dawn - PlayStation 4 | Dragon Age Inquisition - S… | Middle Earth: Shadow of Mo… | Dark Souls III: Day 1 Edit… | Doom - PlayStation 4 | Mass Effect Andromeda - Pr…
- **GT**: `<a_24><b_72><c_142>` Horizon Zero Dawn - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_194><b_15><c_66>` Dishonored 2 - PlayStation 4 ✗
- **beam top5**: `<a_194><b_87><c_112>`PS4, `<a_194><b_15><c_66>`PS4, `<a_201><b_31><c_107>`PS4, `<a_194><b_15><c_9>`PS4, `<a_24><b_72><c_142>`PS4
- **Rec↔GT gap**: correct item at beam rank 5, pred[0] prefix-depth only 0/3; platform consistent(PS4); in beam: share-a=1/10, share-(a,b)=1/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=9/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 7/8 history items (coverage 88%), anchored on: The Witcher 3: Wild Hu…, Dragon Age Inquisition…, Until Dawn - PlayStati…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=SUBCLASS-continuation (score3). target is a sensible DRIFT and **was caught**.

### #362 — Category-OK·item wrong · BEAM-COLLAPSE (<a_123×9/10)
- **History** (5 items; platforms PS4×5): Divinity: Original Sin - E… | Just Cause 3 - PlayStation… | Tom Clancy's The Division … | Fallout 4: Automatron - PS… | 7 Days to Die - PlayStatio…
- **GT**: `<a_140><b_90><c_138>` Battleborn - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_123><b_142><c_36>` 7 Days to Die - PlayStation 4 ✗
- **beam top5**: `<a_123><b_100><c_33>`PS4, `<a_123><b_58><c_78>`PS4, `<a_123><b_160><c_188>`PS4, `<a_123><b_2><c_26>`PS4, `<a_123><b_160><c_69>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_123 family 9/10); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 5/5 history items (coverage 100%), anchored on: Divinity: Original Sin…, Tom Clancy's The Divis…, Just Cause 3 - PlaySta…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #363 — Category-OK·item wrong
- **History** (6 items; platforms PS4×6): Divinity: Original Sin - E… | Just Cause 3 - PlayStation… | Tom Clancy's The Division … | Fallout 4: Automatron - PS… | 7 Days to Die - PlayStatio… | Battleborn - PlayStation 4
- **GT**: `<a_1><b_5><c_65>` Dynasty Warriors 8: Xtreme Legends, Complete E… _(platform PS4)_ ｜ **native**: `<a_131><b_209><c_151>` No Man's Sky - PlayStation 4 ✗
- **beam top5**: `<a_131><b_209><c_151>`PS4, `<a_131><b_41><c_229>`PS4, `<a_201><b_31><c_107>`PS4, `<a_123><b_100><c_33>`PS4, `<a_131><b_224><c_68>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=10/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 5/6 history items (coverage 83%), anchored on: Divinity: Original Sin…, Just Cause 3 - PlaySta…, Fallout 4: Automatron …; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #364 — Category-miss·even top-class (a) wrong
- **History** (1 items; platforms ?×1): Call of Duty 4: Modern War…
- **GT**: `<a_200><b_186><c_92>` Mafia III - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_39><b_124><c_209>` Call of Duty 4: Modern Warfare… ✗
- **beam top5**: `<a_39><b_124><c_209>`?, `<a_80><b_69><c_230>`PC, `<a_39><b_124><c_106>`?, `<a_80><b_69><c_76>`Xbo, `<a_80><b_162><c_230>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=6/10, platforms=4, unique titles=9/10.
- **Reasoning quality**: cites 1/1 history items (coverage 100%), anchored on: Call of Duty 4: Modern…; novel candidates=0 (**pure history restatement**); genre: action,shooter,multiplayer.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=SUBCLASS-continuation (score3). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #365 — Hit@4 · BEAM-COLLAPSE (<a_123×7/10)
- **History** (2 items; platforms ?×1,PS4×1): Call of Duty 4: Modern War… | Mafia III - PlayStation 4
- **GT**: `<a_39><b_78><c_54>` Battlefield 1 - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_123><b_76><c_232>` Far Cry Primal - PlayStation 4… ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_123><b_72><c_7>`PS4, `<a_123><b_129><c_247>`PS4, `<a_39><b_78><c_54>`PS4, `<a_39><b_51><c_188>`PS4
- **Rec↔GT gap**: correct item at beam rank 4, pred[0] prefix-depth only 0/3; platform consistent(PS4); in beam: share-a=2/10, share-(a,b)=1/10.
- **Beam diversity**: **Low** (collapsed to <a_123 family 7/10); unique(a,b)=9/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: Call of Duty 4: Modern…, Mafia III - PlayStatio…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,shooter,multiplayer.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=DRIFT (platform/word-linked) (score1). target is a sensible CLASS-cont and **was caught**.

### #366 — Category-miss·even top-class (a) wrong
- **History** (1 items; platforms Xbox360×1): Bioshock - Xbox 360
- **GT**: `<a_141><b_221><c_44>` Fallout 3 _(platform ?)_ ｜ **native**: `<a_140><b_68><c_13>` Bioshock 2 - Xbox 360 ✗
- **beam top5**: `<a_80><b_202><c_49>`?, `<a_80><b_212><c_38>`?, `<a_80><b_203><c_141>`Xbo, `<a_140><b_68><c_13>`Xbo, `<a_140><b_203><c_107>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=8/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 1/1 history items (coverage 100%), anchored on: Bioshock - Xbox 360; novel candidates=0 (**pure history restatement**); genre: action,horror,immersive.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=EXPLORATION (unrelated) (score0). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #367 — Category-OK·item wrong
- **History** (2 items; platforms Xbox360×1,?×1): Bioshock - Xbox 360 | Fallout 3
- **GT**: `<a_140><b_212><c_49>` Borderlands - Xbox 360 _(platform Xbox360)_ ｜ **native**: `<a_140><b_68><c_13>` Bioshock 2 - Xbox 360 ✗
- **beam top5**: `<a_80><b_202><c_49>`?, `<a_140><b_221><c_161>`?, `<a_140><b_160><c_117>`Xbo, `<a_80><b_212><c_38>`?, `<a_141><b_202><c_240>`?
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; in beam: share-a=5/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=8/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: Bioshock - Xbox 360, Fallout 3; novel candidates=0 (**pure history restatement**); templated opening; genre: action,role-playing,immersive.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=EXPLORATION (unrelated) (score0). user's pick is **more history-consistent** than our top-1 (target1>rec0) → we **drifted off** a catchable continuation.

### #368 — Category-OK·item wrong · BEAM-COLLAPSE (<a_140×7/10)
- **History** (3 items; platforms Xbox360×2,?×1): Bioshock - Xbox 360 | Fallout 3 | Borderlands - Xbox 360
- **GT**: `<a_140><b_176><c_51>` Battlefield: Bad Company _(platform ?)_ ｜ **native**: `<a_140><b_212><c_49>` Borderlands - Xbox 360 ✗
- **beam top5**: `<a_140><b_212><c_49>`Xbo, `<a_140><b_221><c_16>`PC, `<a_140><b_221><c_18>`PC, `<a_140><b_221><c_21>`?, `<a_140><b_221><c_161>`?
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; in beam: share-a=7/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_140 family 7/10); unique(a,b)=6/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Bioshock - Xbox 360, Fallout 3, Borderlands - Xbox 360; novel candidates=0 (**pure history restatement**); templated opening; genre: action,role-playing,multiplayer.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=SUBCLASS-continuation (score3). we recommended something **more history-consistent** than the user's actual pick (rec3>target2) → **model too conservative / user more exploratory**.

### #369 — Category-OK·item wrong
- **History** (4 items; platforms Xbox360×2,?×2): Bioshock - Xbox 360 | Fallout 3 | Borderlands - Xbox 360 | Battlefield: Bad Company
- **GT**: `<a_140><b_161><c_25>` Call of Duty: World at War Platinum Hits - Xbo… _(platform Xbox360)_ ｜ **native**: `<a_140><b_176><c_51>` Battlefield: Bad Company ✗
- **beam top5**: `<a_140><b_212><c_49>`Xbo, `<a_140><b_176><c_37>`Xbo, `<a_140><b_191><c_66>`Xbo, `<a_80><b_212><c_38>`?, `<a_80><b_202><c_49>`?
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform consistent(Xbox360); in beam: share-a=6/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=6/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Bioshock - Xbox 360, Borderlands - Xbox 360, Battlefield: Bad Compa…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,multiplayer,immersive.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=SUBCLASS-continuation (score3). we recommended something **more history-consistent** than the user's actual pick (rec3>target2) → **model too conservative / user more exploratory**.

### #370 — Category-OK·item wrong · BEAM-COLLAPSE (<a_140×9/10)
- **History** (5 items; platforms Xbox360×3,?×2): Bioshock - Xbox 360 | Fallout 3 | Borderlands - Xbox 360 | Battlefield: Bad Company | Call of Duty: World at War…
- **GT**: `<a_140><b_176><c_37>` Battlefield Bad Company 2 - Xbox 360 _(platform Xbox360)_ ｜ **native**: `<a_140><b_212><c_49>` Borderlands - Xbox 360 ✗
- **beam top5**: `<a_140><b_212><c_49>`Xbo, `<a_140><b_221><c_16>`PC, `<a_140><b_4><c_214>`PS3, `<a_140><b_221><c_161>`?, `<a_140><b_221><c_21>`?
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform consistent(Xbox360); in beam: share-a=9/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_140 family 9/10); unique(a,b)=6/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 4/5 history items (coverage 80%), anchored on: Bioshock - Xbox 360, Borderlands - Xbox 360, Battlefield: Bad Compa…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,shooter,multiplayer.
- **Target sensibility (ceiling)**: target=SUBCLASS-continuation (score3); our pred[0]=SUBCLASS-continuation (score3). same relatedness tier (score3) but wrong specific item. Note: target shares word(s) ['bad', 'battlefield', 'company'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #371 — Category-miss·even top-class (a) wrong
- **History** (6 items; platforms Xbox360×4,?×2): Bioshock - Xbox 360 | Fallout 3 | Borderlands - Xbox 360 | Battlefield: Bad Company | Call of Duty: World at War… | Battlefield Bad Company 2 …
- **GT**: `<a_71><b_59><c_0>` Dead Space 2 _(platform ?)_ ｜ **native**: `<a_140><b_212><c_49>` Borderlands - Xbox 360 ✗
- **beam top5**: `<a_140><b_212><c_49>`Xbo, `<a_140><b_212><c_79>`Xbo, `<a_39><b_138><c_240>`?, `<a_140><b_191><c_66>`Xbo, `<a_140><b_176><c_37>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=7/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 3/6 history items (coverage 50%), anchored on: Bioshock - Xbox 360, Borderlands - Xbox 360, Battlefield Bad Compan…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,shooter,strategy.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=SUBCLASS-continuation (score3). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #372 — Category-miss·even top-class (a) wrong
- **History** (10 items; platforms PS×3,Wii×2,?×2): Donkey Kong Country Return… | PS3 500 GB Grand Theft Aut… | The Legend of Zelda: Twili… | Black - PlayStation 2 | Tomb Raider Game of the Ye… | Manhunt - PlayStation 2
- **GT**: `<a_140><b_107><c_50>` GoldenEye 007 _(platform ?)_ ｜ **native**: `<a_240><b_157><c_127>` Manhunt 2 - Sony PSP ✗
- **beam top5**: `<a_240><b_215><c_158>`?, `<a_71><b_171><c_196>`PS3, `<a_240><b_157><c_127>`PSP, `<a_71><b_66><c_11>`?, `<a_71><b_66><c_14>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (2 a top-classes); unique(a,b)=7/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 6/10 history items (coverage 60%), anchored on: The Saboteur - Xbox 36…, Manhunt - PlayStation …, Ghostbusters: The Vide…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item.

### #373 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_250×10/10)
- **History** (7 items; platforms ?×6,PS3×1): Mewtwo amiibo - Japan Impo… | Donkey Kong Country | Teenage Mutant Ninja Turtl… | Resident Evil: Revelations… | Resident Evil 2 | Donkey Kong Country 2: Did…
- **GT**: `<a_219><b_191><c_170>` 16-bit Entertainment System(NOT SNES MINI, NO … _(platform ?)_ ｜ **native**: `<a_250><b_53><c_134>` Wario Land: Super Mario Land 3 ✗
- **beam top5**: `<a_250><b_199><c_170>`?, `<a_250><b_156><c_1>`?, `<a_250><b_165><c_76>`?, `<a_250><b_173><c_199>`?, `<a_250><b_238><c_224>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_250 family 10/10); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/7 history items (coverage 57%), anchored on: Donkey Kong Country, Donkey Kong Country 2:…, Resident Evil: Revelat…; novel candidates=0 (**pure history restatement**); genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=SUBCLASS-continuation (score3). we recommended something **more history-consistent** than the user's actual pick (rec3>target1) → **model too conservative / user more exploratory**. Note: target shares word(s) ['super'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #374 — Category-miss·even top-class (a) wrong
- **History** (8 items; platforms Xbox360×3,?×3,PSVita×1): Nintendo 64 System - Video… | Carmageddon: Max Damage - … | Battlefield Hardline - Xbo… | Contra 4 | Atari Flashback Classics: … | SpongeBob SquarePants: Pla…
- **GT**: `<a_141><b_241><c_37>` Spider-Man: Shattered Dimensions - Xbox 360 _(platform Xbox360)_ ｜ **native**: `<a_219><b_123><c_0>` Atari Flashback Classics: Volu… ✗
- **beam top5**: `<a_233><b_106><c_144>`?, `<a_233><b_21><c_136>`?, `<a_219><b_168><c_108>`Gam, `<a_250><b_165><c_76>`?, `<a_233><b_44><c_175>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (6 distinct a top-classes); unique(a,b)=9/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 6/8 history items (coverage 75%), anchored on: Dungeon Travelers 2: T…, Contra 4, Nintendo 64 System - V…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=EXPLORATION (unrelated) (score0). user's pick is **more history-consistent** than our top-1 (target1>rec0) → we **drifted off** a catchable continuation.

### #375 — Category-miss·even top-class (a) wrong
- **History** (1 items; platforms PC×1): Rollercoaster Tycoon 2: Tr…
- **GT**: `<a_140><b_221><c_18>` Crysis - PC _(platform PC)_ ｜ **native**: `<a_141><b_221><c_44>` Fallout 3 ✗
- **beam top5**: `<a_141><b_203><c_180>`Xbo, `<a_141><b_221><c_44>`?, `<a_195><b_84><c_230>`PC, `<a_141><b_203><c_9>`PS3, `<a_141><b_213><c_117>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PC vs rec=Xbox360); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (7 distinct a top-classes); unique(a,b)=9/10, platforms=5, unique titles=10/10.
- **Reasoning quality**: cites 1/1 history items (coverage 100%), anchored on: Rollercoaster Tycoon 2…; novel candidates=0 (**pure history restatement**); genre: action,strategy,simulation.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=EXPLORATION (unrelated) (score0). user's pick is **more history-consistent** than our top-1 (target1>rec0) → we **drifted off** a catchable continuation.

### #376 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_140×9/10)
- **History** (2 items; platforms PC×2): Rollercoaster Tycoon 2: Tr… | Crysis - PC
- **GT**: `<a_10><b_67><c_155>` Diablo III _(platform ?)_ ｜ **native**: `<a_140><b_161><c_9>` Call of Duty 4: Modern Warfare… ✗
- **beam top5**: `<a_140><b_161><c_25>`Xbo, `<a_140><b_221><c_16>`PC, `<a_80><b_202><c_49>`?, `<a_140><b_221><c_18>`PC, `<a_140><b_221><c_161>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_140 family 9/10); unique(a,b)=4/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: Crysis - PC, Rollercoaster Tycoon 2…; novel candidates=0 (**pure history restatement**); genre: action,shooter,simulation.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #377 — Near-miss·same (a,b) subcluster, only c differs
- **History** (3 items; platforms PC×2,?×1): Rollercoaster Tycoon 2: Tr… | Crysis - PC | Diablo III
- **GT**: `<a_140><b_221><c_145>` Crysis 2 - PC _(platform PC)_ ｜ **native**: `<a_10><b_67><c_155>` Diablo III ✗
- **beam top5**: `<a_10><b_67><c_155>`?, `<a_141><b_48><c_20>`PC, `<a_141><b_197><c_13>`?, `<a_140><b_221><c_16>`PC, `<a_10><b_79><c_56>`PC
- **Rec↔GT gap**: beam's closest item shares (a,b) subcluster with GT, only c differs (same series/SKU), still missed; in beam: share-a=3/10, share-(a,b)=3/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=7/10, platforms=3, unique titles=9/10.
- **Reasoning quality**: cites 2/3 history items (coverage 67%), anchored on: Crysis - PC, Diablo III; novel candidates=0 (**pure history restatement**); templated opening; genre: action,role-playing,shooter.
- **Target sensibility (ceiling)**: target=SUBCLASS-continuation (score3); our pred[0]=SUBCLASS-continuation (score3). same relatedness tier (score3) but wrong specific item. Note: target shares word(s) ['crysis'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #378 — Category-miss·even top-class (a) wrong
- **History** (4 items; platforms PC×3,?×1): Rollercoaster Tycoon 2: Tr… | Crysis - PC | Diablo III | Crysis 2 - PC
- **GT**: `<a_71><b_212><c_18>` Dishonored - PC _(platform PC)_ ｜ **native**: `<a_10><b_67><c_155>` Diablo III ✗
- **beam top5**: `<a_10><b_67><c_155>`?, `<a_10><b_20><c_0>`?, `<a_10><b_33><c_116>`?, `<a_10><b_33><c_56>`?, `<a_10><b_67><c_51>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=8/10, platforms=3, unique titles=8/10.
- **Reasoning quality**: cites 3/4 history items (coverage 75%), anchored on: Crysis - PC, Crysis 2 - PC, Diablo III; novel candidates=0 (**pure history restatement**); templated opening; genre: action,role-playing,shooter.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=SUBCLASS-continuation (score3). we recommended something **more history-consistent** than the user's actual pick (rec3>target1) → **model too conservative / user more exploratory**.

### #379 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_175×7/10)
- **History** (3 items; platforms ?×2,Wii×1): Wii Fit Plus with Balance … | Bully: Scholarship Edition | Bully: Scholarship Edition
- **GT**: `<a_191><b_204><c_225>` Just Cause 3 - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_235><b_65><c_0>` Bully: Scholarship Edition ✗
- **beam top5**: `<a_175><b_171><c_29>`Wii, `<a_175><b_225><c_5>`Wii, `<a_175><b_225><c_3>`Wii, `<a_235><b_65><c_0>`?, `<a_235><b_69><c_186>`Wii
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS4 vs rec=Wii); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_175 family 7/10); unique(a,b)=7/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: Bully: Scholarship Edi…, Wii Fit Plus with Bala…; novel candidates=0 (**pure history restatement**); genre: action,narrative,humor.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #380 — Category-OK·item wrong
- **History** (4 items; platforms ?×2,Wii×1,PS4×1): Wii Fit Plus with Balance … | Bully: Scholarship Edition | Bully: Scholarship Edition | Just Cause 3 - PlayStation…
- **GT**: `<a_205><b_207><c_181>` DiRT Rally - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_123><b_72><c_7>` Far Cry 4 - PlayStation 4 ✗
- **beam top5**: `<a_80><b_69><c_85>`PS4, `<a_123><b_72><c_7>`PS4, `<a_80><b_171><c_9>`PS4, `<a_45><b_107><c_1>`PS4, `<a_240><b_132><c_110>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=9/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 2/3 history items (coverage 67%), anchored on: Bully: Scholarship Edi…, Just Cause 3 - PlaySta…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item.

### #381 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_61×10/10)
- **History** (2 items; platforms DS×1,PC×1): Corsair Gaming VOID USB RG… | Minecraft for PC/Mac [Onli…
- **GT**: `<a_250><b_172><c_5>` Light Blue Yarn Yoshi Amiibo (Yoshi's Woolly W… _(platform ?)_ ｜ **native**: `<a_61><b_53><c_46>` Xbox One Wireless Controller [… ✗
- **beam top5**: `<a_61><b_53><c_46>`Xbo, `<a_61><b_167><c_197>`Xbo, `<a_61><b_214><c_252>`Xbo, `<a_61><b_217><c_168>`Xbo, `<a_61><b_53><c_5>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_61 family 10/10); unique(a,b)=7/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: Corsair Gaming VOID US…, Minecraft for PC/Mac […; novel candidates=0 (**pure history restatement**); genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=EXPLORATION (unrelated) (score0). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #382 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_162×8/10)
- **History** (3 items; platforms DS×1,PC×1,?×1): Corsair Gaming VOID USB RG… | Minecraft for PC/Mac [Onli… | Light Blue Yarn Yoshi Amii…
- **GT**: `<a_7><b_224><c_80>` Microsoft OEM Kinect Adapter for Windows _(platform PC)_ ｜ **native**: `<a_162><b_116><c_253>` HORI Amiibo Card Folio Officia… ✗
- **beam top5**: `<a_162><b_116><c_253>`?, `<a_162><b_116><c_238>`Wii, `<a_162><b_172><c_85>`?, `<a_162><b_172><c_0>`?, `<a_250><b_172><c_11>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_162 family 8/10); unique(a,b)=5/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Corsair Gaming VOID US…, Minecraft for PC/Mac […, Light Blue Yarn Yoshi …; novel candidates=0 (**pure history restatement**); templated opening; genre: action,peripheral,accessor.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item.

### #383 — Category-miss·even top-class (a) wrong
- **History** (3 items; platforms ?×2,PS3×1): WWE All Stars - Playstatio… | WWE '13 | Dead Space 3 Limited Editi…
- **GT**: `<a_22><b_236><c_185>` Life is Strange - Episode 1 [Online Game Code] _(platform ?)_ ｜ **native**: `<a_80><b_59><c_29>` Resident Evil 5 - Playstation … ✗
- **beam top5**: `<a_80><b_59><c_29>`PS3, `<a_80><b_59><c_0>`?, `<a_80><b_59><c_15>`PS3, `<a_80><b_212><c_38>`?, `<a_231><b_237><c_131>`PS3
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=6/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: WWE All Stars - Playst…, WWE '13, Dead Space 3 Limited E…; novel candidates=0 (**pure history restatement**); genre: action,fighting,horror.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=DRIFT (platform/word-linked) (score1). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #384 — Category-miss·even top-class (a) wrong
- **History** (4 items; platforms ?×3,PS3×1): WWE All Stars - Playstatio… | WWE '13 | Dead Space 3 Limited Editi… | Life is Strange - Episode …
- **GT**: `<a_92><b_20><c_102>` Call of Duty: Infinite Warfare - Standard Edit… _(platform PS4)_ ｜ **native**: `<a_80><b_171><c_9>` Need for Speed - PlayStation 4 ✗
- **beam top5**: `<a_71><b_171><c_196>`PS3, `<a_80><b_59><c_29>`PS3, `<a_231><b_107><c_2>`Xbo, `<a_123><b_171><c_136>`?, `<a_80><b_59><c_0>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS4 vs rec=PS3); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=6/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: WWE All Stars - Playst…, WWE '13, Dead Space 3 Limited E…; novel candidates=0 (**pure history restatement**); genre: action,rpg,fighting.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=SUBCLASS-continuation (score3). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #385 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_123×7/10)
- **History** (5 items; platforms ?×3,PS3×1,PS4×1): WWE All Stars - Playstatio… | WWE '13 | Dead Space 3 Limited Editi… | Life is Strange - Episode … | Call of Duty: Infinite War…
- **GT**: `<a_175><b_171><c_117>` Just Dance 3 _(platform ?)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_39><b_51><c_188>`PS4, `<a_123><b_58><c_16>`Xbo, `<a_123><b_171><c_44>`Xbo, `<a_123><b_58><c_78>`PS4, `<a_39><b_78><c_54>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_123 family 7/10); unique(a,b)=8/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 5/5 history items (coverage 100%), anchored on: WWE All Stars - Playst…, WWE '13, Dead Space 3 Limited E…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,fighting,horror.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=DRIFT (platform/word-linked) (score1). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #386 — Category-miss·even top-class (a) wrong
- **History** (4 items; platforms PS4×3,?×1): KontrolFreek FPS Freek Vor… | Pack of 16pcs Pandaren Thu… | Disney Infinity 3.0 Editio… | ASTRO Gaming A50 Wireless …
- **GT**: `<a_201><b_151><c_255>` Playstation Plus: 3 Month Membership [Digital … _(platform PS-generic)_ ｜ **native**: `<a_49><b_146><c_81>` Disney Infinity 3.0 Edition: S… ✗
- **beam top5**: `<a_49><b_146><c_81>`?, `<a_202><b_86><c_197>`DS, `<a_202><b_11><c_2>`DS, `<a_61><b_85><c_232>`PS4, `<a_49><b_146><c_13>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=7/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: KontrolFreek FPS Freek…, Pack of 16pcs Pandaren…, Disney Infinity 3.0 Ed…; novel candidates=0 (**pure history restatement**); genre: immersive,peripheral,accessor.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=SUBCLASS-continuation (score3). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #387 — Hit@9
- **History** (2 items; platforms XboxOne×1,PS4×1): Xbox One Limited Edition H… | Controller Gear PS4 Contro…
- **GT**: `<a_201><b_151><c_255>` Playstation Plus: 3 Month Membership [Digital … _(platform PS-generic)_ ｜ **native**: `<a_61><b_214><c_252>` Xbox One Media Remote ✗
- **beam top5**: `<a_7><b_248><c_16>`Xbo, `<a_74><b_5><c_203>`Xbo, `<a_201><b_36><c_181>`PS4, `<a_7><b_248><c_177>`Xbo, `<a_201><b_31><c_107>`PS4
- **Rec↔GT gap**: correct item at beam rank 9, pred[0] prefix-depth only 0/3; platform mismatch(GT=PS-generic vs rec=XboxOne); in beam: share-a=4/10, share-(a,b)=1/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=8/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 0/2 history items (coverage 0%); novel candidates=0 (**pure history restatement**); genre: immersive,narrative,family-friendly.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=SUBCLASS-continuation (score3). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #388 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_61×7/10)
- **History** (3 items; platforms XboxOne×1,PS4×1,PS×1): Xbox One Limited Edition H… | Controller Gear PS4 Contro… | Playstation Plus: 3 Month …
- **GT**: `<a_162><b_47><c_65>` Nintendo eShop Gift Card _(platform ?)_ ｜ **native**: `<a_61><b_214><c_252>` Xbox One Media Remote ✗
- **beam top5**: `<a_7><b_248><c_16>`Xbo, `<a_7><b_248><c_177>`Xbo, `<a_61><b_214><c_252>`Xbo, `<a_61><b_167><c_197>`Xbo, `<a_7><b_115><c_252>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_61 family 7/10); unique(a,b)=7/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Xbox One Limited Editi…, Controller Gear PS4 Co…, Playstation Plus: 3 Mo…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,immersive,controller.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=SUBCLASS-continuation (score3). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #389 — Category-miss·even top-class (a) wrong
- **History** (4 items; platforms XboxOne×1,PS4×1,PS×1): Xbox One Limited Edition H… | Controller Gear PS4 Contro… | Playstation Plus: 3 Month … | Nintendo eShop Gift Card
- **GT**: `<a_21><b_54><c_195>` Old Skool Ac Power Adapter for the Nintendo Ga… _(platform GameCube)_ ｜ **native**: `<a_162><b_251><c_136>` Animal Crossing: amiibo Festiv… ✗
- **beam top5**: `<a_162><b_251><c_136>`Wii, `<a_61><b_251><c_144>`PS4, `<a_61><b_251><c_51>`PS4, `<a_61><b_251><c_2>`PS4, `<a_61><b_167><c_197>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=GameCube vs rec=WiiU); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=8/10, platforms=5, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Xbox One Limited Editi…, Controller Gear PS4 Co…, Playstation Plus: 3 Mo…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,accessor.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #390 — Category-miss·even top-class (a) wrong
- **History** (5 items; platforms PS4×2,?×2,3DS×1): Pro Evolution Soccer 2016 … | RAZER MAMBA TOURNAMENT EDI… | Kirby: Planet Robobot - Ni… | Pokemon X | Gran Turismo Sport - Limit…
- **GT**: `<a_205><b_252><c_109>` Ride 2 - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_211><b_159><c_71>` Pok&eacute;mon Sun - Nintendo … ✗
- **beam top5**: `<a_211><b_159><c_123>`3DS, `<a_211><b_133><c_30>`3DS, `<a_211><b_159><c_71>`3DS, `<a_211><b_133><c_123>`3DS, `<a_1><b_101><c_0>`Wii
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS4 vs rec=3DS); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=8/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 4/5 history items (coverage 80%), anchored on: Pro Evolution Soccer 2…, Gran Turismo Sport - L…, Pokemon X; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item.

### #391 — Category-miss·even top-class (a) wrong
- **History** (10 items; platforms PS4×4,XboxOne×3,PSVita×2): Call of Duty: Infinite War… | Sony 8GB Memory Card for P… | Dead Rising 4 - Xbox One | Ratchet & Clank Vita Bundl… | Dungeons 2 - PlayStation 4 | Cut The Rope: Triple Treat…
- **GT**: `<a_205><b_208><c_188>` Gran Turismo Sport - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_123><b_58><c_16>`Xbo, `<a_123><b_228><c_123>`Xbo, `<a_123><b_58><c_78>`PS4, `<a_123><b_171><c_44>`Xbo, `<a_123><b_142><c_36>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS4 vs rec=XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=8/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 5/10 history items (coverage 50%), anchored on: Homefront: The Revolut…, Wolfenstein: The Old B…, Dishonored 2 - PlaySta…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,adventure,shooter.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #392 — Category-OK·item wrong · BEAM-COLLAPSE (<a_123×7/10)
- **History** (8 items; platforms PS4×8): Assassin's Creed Unity Lim… | Just Cause 3 - PlayStation… | Until Dawn - PlayStation 4 | Watch Dogs 2 - PlayStation… | Batman: Arkham Knight - Pl… | Metal Gear Solid V: The Ph…
- **GT**: `<a_200><b_169><c_179>` Mad Max - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_123><b_72><c_7>` Far Cry 4 - PlayStation 4 ✗
- **beam top5**: `<a_123><b_72><c_7>`PS4, `<a_201><b_213><c_242>`PS4, `<a_123><b_100><c_33>`PS4, `<a_201><b_18><c_56>`PS4, `<a_123><b_76><c_232>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_123 family 7/10); unique(a,b)=9/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 6/8 history items (coverage 75%), anchored on: Uncharted 4: A Thief's…, Until Dawn - PlayStati…, Just Cause 3 - PlaySta…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #393 — Category-OK·item wrong
- **History** (9 items; platforms PS4×9): Just Cause 3 - PlayStation… | Until Dawn - PlayStation 4 | Watch Dogs 2 - PlayStation… | Batman: Arkham Knight - Pl… | Metal Gear Solid V: The Ph… | Mad Max - PlayStation 4
- **GT**: `<a_24><b_96><c_27>` Rise of the Tomb Raider: 20 Year Celebration -… _(platform PS4)_ ｜ **native**: `<a_123><b_72><c_7>` Far Cry 4 - PlayStation 4 ✗
- **beam top5**: `<a_123><b_72><c_7>`PS4, `<a_201><b_213><c_242>`PS4, `<a_200><b_186><c_92>`PS4, `<a_201><b_18><c_56>`PS4, `<a_201><b_145><c_9>`PS4
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform consistent(PS4); in beam: share-a=1/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=9/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 6/9 history items (coverage 67%), anchored on: Uncharted 4: A Thief's…, Assassin's Creed Unity…, Just Cause 3 - PlaySta…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #394 — Hit@8 · RERANK-HARM
- **History** (1 items; platforms ?×1): Bloodborne
- **GT**: `<a_194><b_33><c_4>` Dark Souls II: Scholar of the First Sin - Play… _(platform PS4)_ ｜ **native**: `<a_194><b_33><c_4>` Dark Souls II: Scholar of the … ✓
- **beam top5**: `<a_194><b_87><c_249>`PS4, `<a_201><b_145><c_9>`PS4, `<a_201><b_213><c_242>`PS4, `<a_194><b_87><c_112>`PS4, `<a_194><b_121><c_62>`PS4
- **Rec↔GT gap**: correct item at beam rank 8, pred[0] prefix-depth only 1/3; platform consistent(PS4); in beam: share-a=5/10, share-(a,b)=1/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 1/1 history items (coverage 100%), anchored on: Bloodborne; novel candidates=0 (**pure history restatement**); genre: action,rpg,immersive.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). target is a sensible CLASS-cont and **was caught**.

### #395 — Category-miss·even top-class (a) wrong
- **History** (4 items; platforms PS4×3,XboxOne×1): Uncharted 4: A Thief's End… | Mafia III - PlayStation 4 | Xbox One Stereo Headset Ad… | Horizon Zero Dawn - PlaySt…
- **GT**: `<a_202><b_253><c_113>` CORSAIR Sabre - RGB Gaming Mouse - Lightweight… _(platform ?)_ ｜ **native**: `<a_201><b_56><c_74>` Steep - PS4 Digital Code ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_201><b_18><c_56>`PS4, `<a_191><b_10><c_232>`PS4, `<a_201><b_56><c_74>`PS4, `<a_201><b_45><c_166>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=10/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Uncharted 4: A Thief's…, Horizon Zero Dawn - Pl…, Mafia III - PlayStatio…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=DRIFT (platform/word-linked) (score1). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #396 — Category-miss·even top-class (a) wrong
- **History** (4 items; platforms PS4×3,?×1): Senran Kagura Estival Vers… | Dragon Quest Heroes: The W… | Prey - Pre-load - PS4 Digi… | dreamGEAR- Playstation 4 C…
- **GT**: `<a_113><b_152><c_199>` HORI Compact PlayStand - Zelda Edition, Offici… _(platform Switch)_ ｜ **native**: `<a_201><b_31><c_107>` Uncharted 4: A Thief's End - P… ✗
- **beam top5**: `<a_131><b_41><c_229>`PS4, `<a_201><b_31><c_107>`PS4, `<a_131><b_209><c_151>`PS4, `<a_194><b_87><c_249>`PS4, `<a_1><b_173><c_4>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=Switch vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (6 distinct a top-classes); unique(a,b)=10/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Senran Kagura Estival …, Dragon Quest Heroes: T…, Prey - Pre-load - PS4 …; novel candidates=0 (**pure history restatement**); templated opening; genre: action,immersive,narrative.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=DRIFT (platform/word-linked) (score1). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #397 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_131×7/10)
- **History** (9 items; platforms PS4×4,PC×2,XboxOne×2): Fallout 4 - PC | Fallout 4 - Pip-Boy Editio… | Fallout 4 - Pip-Boy Editio… | Xenoblade Chronicles X | Just Cause 3 - PlayStation… | Deus Ex: Mankind Divided -…
- **GT**: `<a_106><b_116><c_155>` Terraria - Nintendo 3DS _(platform 3DS)_ ｜ **native**: `<a_131><b_224><c_68>` Overwatch - Origins Edition - … ✗
- **beam top5**: `<a_131><b_41><c_229>`PS4, `<a_131><b_41><c_74>`Xbo, `<a_131><b_41><c_210>`PC, `<a_131><b_209><c_151>`PS4, `<a_131><b_224><c_68>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=3DS vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_131 family 7/10); unique(a,b)=6/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 4/9 history items (coverage 44%), anchored on: Fallout 4 - PC, Fallout 4 - Pip-Boy Ed…, Xenoblade Chronicles X; novel candidates=0 (**pure history restatement**); templated opening; genre: action,role-playing,immersive.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #398 — Category-miss·even top-class (a) wrong
- **History** (3 items; platforms PSVita×2,PC×1): Sony PlayStation Vita WiFi | PlayStation Vita Wi-Fi mod… | Grand Theft Auto V - PC Do…
- **GT**: `<a_86><b_149><c_225>` Bully Scholarship Edition - PC _(platform PC)_ ｜ **native**: `<a_201><b_31><c_107>` Uncharted 4: A Thief's End - P… ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_7><b_248><c_16>`Xbo, `<a_131><b_155><c_206>`Xbo, `<a_201><b_2><c_102>`PS4, `<a_201><b_36><c_181>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PC vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=9/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Sony PlayStation Vita …, PlayStation Vita Wi-Fi…, Grand Theft Auto V - P…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,immersive,narrative.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=EXPLORATION (unrelated) (score0). user's pick is **more history-consistent** than our top-1 (target1>rec0) → we **drifted off** a catchable continuation.

### #399 — Category-miss·even top-class (a) wrong
- **History** (4 items; platforms PSVita×2,PC×2): Sony PlayStation Vita WiFi | PlayStation Vita Wi-Fi mod… | Grand Theft Auto V - PC Do… | Bully Scholarship Edition …
- **GT**: `<a_1><b_209><c_76>` Tales of Symphonia Chronicles - Playstation 3 _(platform PS3)_ ｜ **native**: `<a_131><b_155><c_206>` Fallout 4 - Xbox One ✗
- **beam top5**: `<a_7><b_248><c_16>`Xbo, `<a_201><b_31><c_107>`PS4, `<a_61><b_167><c_197>`Xbo, `<a_131><b_155><c_206>`Xbo, `<a_61><b_131><c_197>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS3 vs rec=XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=10/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Sony PlayStation Vita …, PlayStation Vita Wi-Fi…, Grand Theft Auto V - P…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=EXPLORATION (unrelated) (score0). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #400 — Category-OK·item wrong
- **History** (5 items; platforms PSVita×2,PC×2,PS3×1): Sony PlayStation Vita WiFi | PlayStation Vita Wi-Fi mod… | Grand Theft Auto V - PC Do… | Bully Scholarship Edition … | Tales of Symphonia Chronic…
- **GT**: `<a_1><b_46><c_242>` Tales of Xillia 2 - PlayStation 3 _(platform PS3)_ ｜ **native**: `<a_1><b_150><c_189>` Legend of Heroes: Trails of Co… ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_131><b_155><c_206>`Xbo, `<a_131><b_210><c_0>`PS4, `<a_1><b_150><c_189>`PS3, `<a_1><b_173><c_4>`PS4
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform mismatch(GT=PS3 vs rec=PS4); in beam: share-a=3/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=10/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 4/5 history items (coverage 80%), anchored on: Grand Theft Auto V - P…, Tales of Symphonia Chr…, PlayStation Vita Wi-Fi…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=EXPLORATION (unrelated) (score0). user's pick is **more history-consistent** than our top-1 (target2>rec0) → we **drifted off** a catchable continuation. Note: target shares word(s) ['tales'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #401 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_123×7/10)
- **History** (4 items; platforms PS4×3,Xbox×1): Middle Earth: Shadow of Mo… | Microsoft Xbox Wireless Ad… | Resident Evil 4 - PlayStat… | Batman: Return to Arkham -…
- **GT**: `<a_86><b_12><c_93>` South Park: The Fractured but Whole - PlayStat… _(platform PS4)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_39><b_77><c_105>`Xbo, `<a_123><b_100><c_33>`PS4, `<a_123><b_58><c_78>`PS4, `<a_39><b_51><c_188>`PS4, `<a_39><b_78><c_54>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS4 vs rec=XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_123 family 7/10); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Middle Earth: Shadow o…, Resident Evil 4 - Play…, Microsoft Xbox Wireles…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=EXPLORATION (unrelated) (score0). user's pick is **more history-consistent** than our top-1 (target1>rec0) → we **drifted off** a catchable continuation.

### #402 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_1×8/10)
- **History** (4 items; platforms WiiU×2,PS4×2): Xenoblade Chronicles X Spe… | Bayonetta 2 (Single Disc) … | Tales of Zestiria: Collect… | NieR: Automata - Playstati…
- **GT**: `<a_7><b_36><c_217>` Xbox One X 1TB Limited Edition Console - Proje… _(platform XboxOne)_ ｜ **native**: `<a_1><b_150><c_189>` Legend of Heroes: Trails of Co… ✗
- **beam top5**: `<a_1><b_116><c_233>`PS4, `<a_1><b_150><c_189>`PS3, `<a_1><b_25><c_254>`3DS, `<a_1><b_177><c_184>`PS4, `<a_121><b_76><c_208>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=XboxOne vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_1 family 8/10); unique(a,b)=10/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Xenoblade Chronicles X…, Tales of Zestiria: Col…, NieR: Automata - Plays…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,immersive.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #403 — Category-miss·even top-class (a) wrong
- **History** (10 items; platforms DS×4,3DS×3,?×2): Radiant Historia - Nintend… | Silent Hill HD Collection … | Spirit Camera: The Cursed … | Fire Emblem: Awakening | Project X Zone - Nintendo … | Shin Megami Tensei IV - Ni…
- **GT**: `<a_1><b_101><c_3>` Xenoblade Chronicles X _(platform ?)_ ｜ **native**: `<a_195><b_59><c_156>` Shin Megami Tensei IV - Ninten… ✗
- **beam top5**: `<a_30><b_211><c_255>`DS, `<a_216><b_51><c_130>`3DS, `<a_195><b_36><c_218>`?, `<a_30><b_33><c_40>`PSV, `<a_195><b_59><c_156>`3DS
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=9/10, platforms=5, unique titles=10/10.
- **Reasoning quality**: cites 7/10 history items (coverage 70%), anchored on: Phoenix Wright: Ace At…, Phoenix Wright, Ace At…, Phoenix Wright Ace Att…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,adventure,rpg.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item.

### #404 — Category-miss·even top-class (a) wrong
- **History** (3 items; platforms ?×2,GameCube×1): Metroid: Other M | Donkey Kong Classics | Soul Calibur II - Gamecube
- **GT**: `<a_193><b_25><c_82>` Star Fox Assault _(platform ?)_ ｜ **native**: `<a_208><b_51><c_1>` Soul Calibur IV - Playstation … ✗
- **beam top5**: `<a_208><b_51><c_1>`PS3, `<a_208><b_51><c_0>`PS, `<a_208><b_242><c_41>`PS, `<a_1><b_99><c_2>`PS4, `<a_208><b_26><c_212>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=7/10, platforms=7, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Metroid: Other M, Donkey Kong Classics, Soul Calibur II - Game…; novel candidates=0 (**pure history restatement**); genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #405 — Category-OK·item wrong · BEAM-COLLAPSE (<a_205×9/10)
- **History** (10 items; platforms PS4×8,PSVita×1,PS3×1): Batman: Arkham Knight - Pl… | Horizon Zero Dawn - PlaySt… | Persona 5 - SteelBook Edit… | Back to the Future: The Ga… | Gran Turismo 5 - Playstati… | Gran Turismo Sport - Limit…
- **GT**: `<a_39><b_51><c_188>` Titanfall 2 - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_205><b_62><c_68>` F1 2015 (Formula One) - PlaySt… ✗
- **beam top5**: `<a_24><b_72><c_142>`PS4, `<a_205><b_208><c_52>`?, `<a_205><b_207><c_181>`PS4, `<a_205><b_60><c_93>`PS4, `<a_205><b_8><c_38>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_205 family 9/10); unique(a,b)=10/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 6/10 history items (coverage 60%), anchored on: Middle Earth: Shadow o…, Tales from the Borderl…, Persona 5 - SteelBook …; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #406 — Category-miss·even top-class (a) wrong
- **History** (1 items; platforms Xbox360×1): Lego Star Wars: The Comple…
- **GT**: `<a_113><b_136><c_194>` Zettaguard Classic Controller for Nintendo Wii _(platform Wii)_ ｜ **native**: `<a_245><b_90><c_188>` Lego Star Wars: The Complete S… ✗
- **beam top5**: `<a_49><b_218><c_179>`?, `<a_245><b_26><c_39>`DS, `<a_245><b_185><c_59>`PS4, `<a_49><b_218><c_3>`PSV, `<a_49><b_218><c_101>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=5/10, platforms=8, unique titles=10/10.
- **Reasoning quality**: cites 1/1 history items (coverage 100%), anchored on: Lego Star Wars: The Co…; novel candidates=0 (**pure history restatement**); genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=DRIFT (platform/word-linked) (score1). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #407 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_113×7/10)
- **History** (2 items; platforms Xbox360×1,Wii×1): Lego Star Wars: The Comple… | Zettaguard Classic Control…
- **GT**: `<a_49><b_218><c_101>` Lego: Marvel Super Heroes, XBOX 360 _(platform Xbox360)_ ｜ **native**: `<a_113><b_35><c_14>` Nintendo Super Smash Bros. Bla… ✗
- **beam top5**: `<a_113><b_9><c_63>`Wii, `<a_245><b_26><c_39>`DS, `<a_113><b_35><c_14>`Gam, `<a_113><b_9><c_194>`Wii, `<a_113><b_112><c_109>`Wii
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=Xbox360 vs rec=WiiU); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_113 family 7/10); unique(a,b)=7/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: Lego Star Wars: The Co…, Zettaguard Classic Con…; novel candidates=0 (**pure history restatement**); genre: action,immersive,nostalg.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**. Note: target shares word(s) ['lego'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #408 — Category-miss·even top-class (a) wrong
- **History** (3 items; platforms Xbox360×2,Wii×1): Lego Star Wars: The Comple… | Zettaguard Classic Control… | Lego: Marvel Super Heroes,…
- **GT**: `<a_189><b_201><c_57>` PlayStation 4 Camera (Old Model) _(platform PS4)_ ｜ **native**: `<a_113><b_35><c_14>` Nintendo Super Smash Bros. Bla… ✗
- **beam top5**: `<a_113><b_9><c_63>`Wii, `<a_49><b_47><c_60>`PSV, `<a_49><b_218><c_179>`?, `<a_84><b_136><c_91>`Wii, `<a_113><b_35><c_14>`Gam
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS4 vs rec=WiiU); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=8/10, platforms=5, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Lego Star Wars: The Co…, Lego: Marvel Super Her…, Zettaguard Classic Con…; novel candidates=0 (**pure history restatement**); genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #409 — Category-OK·item wrong
- **History** (4 items; platforms Xbox360×2,Wii×1,PS4×1): Lego Star Wars: The Comple… | Zettaguard Classic Control… | Lego: Marvel Super Heroes,… | PlayStation 4 Camera (Old …
- **GT**: `<a_84><b_222><c_22>` Mario Kart 8 - Nintendo Wii U _(platform WiiU)_ ｜ **native**: `<a_231><b_28><c_63>` PlayStation 4 500GB Console [O… ✗
- **beam top5**: `<a_231><b_28><c_63>`PS4, `<a_245><b_185><c_59>`PS4, `<a_49><b_47><c_60>`PSV, `<a_175><b_103><c_7>`PS4, `<a_39><b_50><c_16>`PS3
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform mismatch(GT=WiiU vs rec=PS4); in beam: share-a=1/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (7 distinct a top-classes); unique(a,b)=8/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Lego Star Wars: The Co…, Lego: Marvel Super Her…, Zettaguard Classic Con…; novel candidates=0 (**pure history restatement**); genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=DRIFT (platform/word-linked) (score1). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #410 — Category-miss·even top-class (a) wrong
- **History** (5 items; platforms Xbox360×2,Wii×1,PS4×1): Lego Star Wars: The Comple… | Zettaguard Classic Control… | Lego: Marvel Super Heroes,… | PlayStation 4 Camera (Old … | Mario Kart 8 - Nintendo Wi…
- **GT**: `<a_249><b_180><c_74>` PlayStation Vita Memory Card 64GB (PCH-Z641J) _(platform PSVita)_ ｜ **native**: `<a_84><b_217><c_3>` HORI Mario Kart 8 Racing Wheel… ✗
- **beam top5**: `<a_84><b_217><c_3>`Wii, `<a_84><b_235><c_3>`Wii, `<a_245><b_232><c_39>`PSV, `<a_84><b_222><c_22>`Wii, `<a_84><b_149><c_181>`Wii
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PSVita vs rec=WiiU); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=9/10, platforms=5, unique titles=10/10.
- **Reasoning quality**: cites 4/5 history items (coverage 80%), anchored on: Lego Star Wars: The Co…, Lego: Marvel Super Her…, Zettaguard Classic Con…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #411 — Category-miss·even top-class (a) wrong
- **History** (6 items; platforms Xbox360×2,Wii×1,PS4×1): Lego Star Wars: The Comple… | Zettaguard Classic Control… | Lego: Marvel Super Heroes,… | PlayStation 4 Camera (Old … | Mario Kart 8 - Nintendo Wi… | PlayStation Vita Memory Ca…
- **GT**: `<a_92><b_68><c_129>` Doom - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_84><b_149><c_181>` Beastron Mario Kart Racing Whe… ✗
- **beam top5**: `<a_84><b_235><c_3>`Wii, `<a_245><b_185><c_59>`PS4, `<a_245><b_232><c_39>`PSV, `<a_49><b_112><c_10>`?, `<a_245><b_232><c_5>`PS3
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS4 vs rec=WiiU); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=9/10, platforms=6, unique titles=10/10.
- **Reasoning quality**: cites 5/6 history items (coverage 83%), anchored on: Lego Star Wars: The Co…, Lego: Marvel Super Her…, Mario Kart 8 - Nintend…; novel candidates=0 (**pure history restatement**); genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #412 — Category-miss·even top-class (a) wrong
- **History** (7 items; platforms Xbox360×2,PS4×2,Wii×1): Zettaguard Classic Control… | Lego: Marvel Super Heroes,… | PlayStation 4 Camera (Old … | Mario Kart 8 - Nintendo Wi… | PlayStation Vita Memory Ca… | Doom - PlayStation 4
- **GT**: `<a_61><b_131><c_197>` Microsoft Xbox Wireless Adapter for Windows 10 _(platform Xbox)_ ｜ **native**: `<a_201><b_31><c_107>` Uncharted 4: A Thief's End - P… ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_201><b_213><c_242>`PS4, `<a_131><b_210><c_0>`PS4, `<a_201><b_2><c_102>`PS4, `<a_201><b_201><c_84>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=Xbox vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (6 distinct a top-classes); unique(a,b)=10/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 5/7 history items (coverage 71%), anchored on: Lego Star Wars: The Co…, Lego: Marvel Super Her…, Mario Kart 8 - Nintend…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=DRIFT (platform/word-linked) (score1). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #413 — Category-OK·item wrong
- **History** (8 items; platforms Xbox360×2,PS4×2,Wii×1): Lego: Marvel Super Heroes,… | PlayStation 4 Camera (Old … | Mario Kart 8 - Nintendo Wi… | PlayStation Vita Memory Ca… | Doom - PlayStation 4 | Microsoft Xbox Wireless Ad…
- **GT**: `<a_61><b_70><c_135>` Xbox Elite Wireless Controller _(platform Xbox)_ ｜ **native**: `<a_61><b_131><c_197>` Microsoft Xbox Wireless Adapte… ✗
- **beam top5**: `<a_61><b_167><c_197>`Xbo, `<a_61><b_131><c_197>`Xbo, `<a_201><b_31><c_107>`PS4, `<a_131><b_210><c_0>`PS4, `<a_131><b_41><c_229>`PS4
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform mismatch(GT=Xbox vs rec=XboxOne); in beam: share-a=2/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=9/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 4/8 history items (coverage 50%), anchored on: Lego Star Wars: The Co…, Lego: Marvel Super Her…, PlayStation 4 Camera (…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item. Note: target shares word(s) ['controller', 'wireless'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #414 — Category-OK·item wrong · BEAM-COLLAPSE (<a_61×7/10)
- **History** (9 items; platforms Xbox360×2,PS4×2,Xbox×2): PlayStation 4 Camera (Old … | Mario Kart 8 - Nintendo Wi… | PlayStation Vita Memory Ca… | Doom - PlayStation 4 | Microsoft Xbox Wireless Ad… | Xbox Elite Wireless Contro…
- **GT**: `<a_24><b_185><c_47>` ReCore - Xbox One _(platform XboxOne)_ ｜ **native**: `<a_61><b_167><c_164>` Microsoft Xbox One Controller … ✗
- **beam top5**: `<a_61><b_167><c_197>`Xbo, `<a_61><b_167><c_164>`Xbo, `<a_201><b_31><c_107>`PS4, `<a_61><b_111><c_109>`Xbo, `<a_61><b_131><c_197>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_61 family 7/10); unique(a,b)=9/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 2/9 history items (coverage 22%), anchored on: Mario Kart 8 - Nintend…, Doom - PlayStation 4; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #415 — Category-miss·even top-class (a) wrong
- **History** (10 items; platforms Xbox360×2,PS4×2,Xbox×2): Mario Kart 8 - Nintendo Wi… | PlayStation Vita Memory Ca… | Doom - PlayStation 4 | Microsoft Xbox Wireless Ad… | Xbox Elite Wireless Contro… | ReCore - Xbox One
- **GT**: `<a_8><b_34><c_189>` Nintendo 3DS XL Battery Replacement SPR-003 (N… _(platform 3DS)_ ｜ **native**: `<a_61><b_214><c_225>` PDP Talon Media Remote Control… ✗
- **beam top5**: `<a_39><b_77><c_105>`Xbo, `<a_123><b_58><c_78>`PS4, `<a_39><b_51><c_21>`Xbo, `<a_24><b_72><c_142>`PS4, `<a_201><b_56><c_74>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=3DS vs rec=XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (7 distinct a top-classes); unique(a,b)=10/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 2/10 history items (coverage 20%), anchored on: Lego Star Wars: The Co…, Lego: Marvel Super Her…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=DRIFT (platform/word-linked) (score1). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #416 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_61×10/10)
- **History** (10 items; platforms PS4×2,Xbox×2,Wii×1): PlayStation Vita Memory Ca… | Doom - PlayStation 4 | Microsoft Xbox Wireless Ad… | Xbox Elite Wireless Contro… | ReCore - Xbox One | Nintendo 3DS XL Battery Re…
- **GT**: `<a_39><b_78><c_205>` Battlefield 1 - Xbox One _(platform XboxOne)_ ｜ **native**: `<a_61><b_111><c_109>` Xbox One Chatpad + Chat Headse… ✗
- **beam top5**: `<a_61><b_251><c_144>`PS4, `<a_61><b_111><c_109>`Xbo, `<a_61><b_214><c_225>`Xbo, `<a_61><b_131><c_197>`Xbo, `<a_61><b_137><c_255>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=XboxOne vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_61 family 10/10); unique(a,b)=7/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 7/10 history items (coverage 70%), anchored on: PlayStation 4 Camera (…, Microsoft Xbox Wireles…, ReCore - Xbox One; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #417 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_39×7/10)
- **History** (10 items; platforms PS4×2,Xbox×2,XboxOne×2): Doom - PlayStation 4 | Microsoft Xbox Wireless Ad… | Xbox Elite Wireless Contro… | ReCore - Xbox One | Nintendo 3DS XL Battery Re… | Battlefield 1 - Xbox One
- **GT**: `<a_194><b_235><c_193>` Final Fantasy XII: The Zodiac Age - PlayStatio… _(platform PS4)_ ｜ **native**: `<a_39><b_77><c_105>` Call of Duty: Infinite Warfare… ✗
- **beam top5**: `<a_39><b_77><c_105>`Xbo, `<a_39><b_51><c_21>`Xbo, `<a_123><b_58><c_78>`PS4, `<a_39><b_77><c_69>`Xbo, `<a_39><b_175><c_240>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS4 vs rec=XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_39 family 7/10); unique(a,b)=8/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/10 history items (coverage 40%), anchored on: Lego: Marvel Super Her…, Battlefield 1 - Xbox O…, PlayStation 4 Camera (…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #418 — Category-miss·even top-class (a) wrong
- **History** (10 items; platforms PS4×3,Xbox×2,XboxOne×2): Microsoft Xbox Wireless Ad… | Xbox Elite Wireless Contro… | ReCore - Xbox One | Nintendo 3DS XL Battery Re… | Battlefield 1 - Xbox One | Final Fantasy XII: The Zod…
- **GT**: `<a_216><b_123><c_81>` Apollo Justice: Ace Attorney _(platform ?)_ ｜ **native**: `<a_131><b_52><c_86>` Gears of War 4 - Xbox One ✗
- **beam top5**: `<a_39><b_77><c_105>`Xbo, `<a_39><b_51><c_21>`Xbo, `<a_123><b_58><c_78>`PS4, `<a_24><b_72><c_142>`PS4, `<a_194><b_15><c_66>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (6 distinct a top-classes); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 5/10 history items (coverage 50%), anchored on: Battlefield 1 - Xbox O…, Final Fantasy XII: The…, PlayStation 4 Camera (…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,adventure,shooter.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #419 — Category-miss·even top-class (a) wrong
- **History** (10 items; platforms PS4×2,Xbox×2,XboxOne×2): Xbox Elite Wireless Contro… | ReCore - Xbox One | Nintendo 3DS XL Battery Re… | Battlefield 1 - Xbox One | Final Fantasy XII: The Zod… | Apollo Justice: Ace Attorn…
- **GT**: `<a_195><b_197><c_114>` Ace Attorney Investigations: Miles Edgeworth _(platform ?)_ ｜ **native**: `<a_216><b_27><c_5>` Phoenix Wright: Ace Attorney -… ✗
- **beam top5**: `<a_216><b_27><c_0>`DS, `<a_216><b_27><c_5>`DS, `<a_216><b_27><c_1>`DS, `<a_216><b_48><c_110>`3DS, `<a_216><b_44><c_79>`3DS
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=8/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 6/10 history items (coverage 60%), anchored on: Mario Kart 8 - Nintend…, Battlefield 1 - Xbox O…, Final Fantasy XII: The…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,shooter,racing.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**. Note: target shares word(s) ['ace', 'attorney'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #420 — Category-miss·even top-class (a) wrong
- **History** (10 items; platforms PS4×2,Xbox×2,XboxOne×2): ReCore - Xbox One | Nintendo 3DS XL Battery Re… | Battlefield 1 - Xbox One | Final Fantasy XII: The Zod… | Apollo Justice: Ace Attorn… | Ace Attorney Investigation…
- **GT**: `<a_194><b_148><c_225>` Dark Souls - Xbox 360 _(platform Xbox360)_ ｜ **native**: `<a_30><b_211><c_255>` Ghost Trick: Phantom Detective… ✗
- **beam top5**: `<a_216><b_92><c_192>`3DS, `<a_30><b_211><c_255>`DS, `<a_30><b_144><c_145>`PSV, `<a_216><b_27><c_5>`DS, `<a_216><b_92><c_163>`3DS
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=Xbox360 vs rec=3DS); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=8/10, platforms=6, unique titles=10/10.
- **Reasoning quality**: cites 4/10 history items (coverage 40%), anchored on: ReCore - Xbox One, Final Fantasy XII: The…, Apollo Justice: Ace At…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item.

### #421 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_194×10/10)
- **History** (10 items; platforms PS4×2,Xbox×2,XboxOne×2): Nintendo 3DS XL Battery Re… | Battlefield 1 - Xbox One | Final Fantasy XII: The Zod… | Apollo Justice: Ace Attorn… | Ace Attorney Investigation… | Dark Souls - Xbox 360
- **GT**: `<a_61><b_56><c_1>` Dragonpad Wired USB Controller (Black) for PC … _(platform Xbox360)_ ｜ **native**: `<a_194><b_20><c_194>` Dark Souls III: Day 1 Edition … ✗
- **beam top5**: `<a_194><b_215><c_154>`?, `<a_194><b_33><c_2>`Xbo, `<a_194><b_15><c_66>`PS4, `<a_194><b_33><c_4>`PS4, `<a_194><b_87><c_112>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_194 family 10/10); unique(a,b)=6/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 8/10 history items (coverage 80%), anchored on: Doom - PlayStation 4, ReCore - Xbox One, Final Fantasy XII: The…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,shooter.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item. Note: target shares word(s) ['controller'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #422 — Category-OK·item wrong · BEAM-COLLAPSE (<a_61×10/10)
- **History** (10 items; platforms Xbox×2,XboxOne×2,?×2): Battlefield 1 - Xbox One | Final Fantasy XII: The Zod… | Apollo Justice: Ace Attorn… | Ace Attorney Investigation… | Dark Souls - Xbox 360 | Dragonpad Wired USB Contro…
- **GT**: `<a_10><b_16><c_3>` Dragon Age Inquisition - Deluxe Edition -  Xbo… _(platform XboxOne)_ ｜ **native**: `<a_61><b_56><c_2>` Wired USB Controller for PC & … ✗
- **beam top5**: `<a_61><b_167><c_164>`Xbo, `<a_61><b_150><c_0>`Xbo, `<a_61><b_9><c_122>`PS3, `<a_61><b_56><c_2>`Xbo, `<a_61><b_98><c_108>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_61 family 10/10); unique(a,b)=9/10, platforms=6, unique titles=10/10.
- **Reasoning quality**: cites 6/10 history items (coverage 60%), anchored on: Battlefield 1 - Xbox O…, Final Fantasy XII: The…, Microsoft Xbox Wireles…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,adventure,rpg.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**. Note: target shares word(s) ['age'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #423 — Category-OK·item wrong
- **History** (10 items; platforms XboxOne×3,?×2,Xbox360×2): Final Fantasy XII: The Zod… | Apollo Justice: Ace Attorn… | Ace Attorney Investigation… | Dark Souls - Xbox 360 | Dragonpad Wired USB Contro… | Dragon Age Inquisition - D…
- **GT**: `<a_205><b_136><c_51>` Forza Horizon 2 for Xbox One _(platform XboxOne)_ ｜ **native**: `<a_10><b_16><c_4>` Dragon Age Inquisition - Delux… ✗
- **beam top5**: `<a_194><b_33><c_2>`Xbo, `<a_216><b_27><c_5>`DS, `<a_194><b_215><c_154>`?, `<a_10><b_53><c_1>`Xbo, `<a_194><b_33><c_4>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=7/10, platforms=5, unique titles=10/10.
- **Reasoning quality**: cites 7/10 history items (coverage 70%), anchored on: ReCore - Xbox One, Final Fantasy XII: The…, Dark Souls - Xbox 360; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #424 — Category-miss·even top-class (a) wrong
- **History** (9 items; platforms 3DS×3,?×2,XboxOne×1): The Last of Us Remastered … | Nintendo New 3DS XL - Blac… | Microsoft Xbox Wireless Ad… | Nintendo 3DS Compatible wi… | Gen USB Charge Cable for N… | Generic 3.6V 3600mAh Batte…
- **GT**: `<a_249><b_31><c_126>` Sony PlayStation Vita WiFi _(platform PSVita)_ ｜ **native**: `<a_113><b_235><c_2>` Nintendo New 3DS XL - Black ✗
- **beam top5**: `<a_113><b_235><c_2>`3DS, `<a_119><b_168><c_182>`3DS, `<a_113><b_235><c_28>`3DS, `<a_113><b_104><c_28>`3DS, `<a_113><b_31><c_215>`3DS
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PSVita vs rec=3DS); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=7/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 5/9 history items (coverage 56%), anchored on: Xbox One Play and Char…, Gen USB Charge Cable f…, Nintendo New 3DS XL - …; novel candidates=0 (**pure history restatement**); templated opening; genre: action,immersive,narrative.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=SUBCLASS-continuation (score3). we recommended something **more history-consistent** than the user's actual pick (rec3>target1) → **model too conservative / user more exploratory**. Note: target shares word(s) ['sony'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #425 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_202×8/10)
- **History** (3 items; platforms PC×1,Switch×1,WiiU×1): MAYFLASH N64 Controller Ad… | CM Storm QuickFire Rapid-i… | Mayflash GameCube Controll…
- **GT**: `<a_61><b_91><c_41>` HORI Real Arcade Pro 4 Kai for PlayStation 4, … _(platform PS4)_ ｜ **native**: `<a_202><b_34><c_140>` Logitech G402 Hyperion Fury FP… ✗
- **beam top5**: `<a_202><b_253><c_158>`?, `<a_202><b_82><c_172>`?, `<a_202><b_253><c_105>`?, `<a_202><b_34><c_39>`?, `<a_202><b_34><c_140>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_202 family 8/10); unique(a,b)=7/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: MAYFLASH N64 Controlle…, CM Storm QuickFire Rap…, Mayflash GameCube Cont…; novel candidates=0 (**pure history restatement**); genre: action,nostalg,retro.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #426 — Category-miss·even top-class (a) wrong
- **History** (4 items; platforms PC×1,Switch×1,WiiU×1): MAYFLASH N64 Controller Ad… | CM Storm QuickFire Rapid-i… | Mayflash GameCube Controll… | HORI Real Arcade Pro 4 Kai…
- **GT**: `<a_202><b_203><c_93>` SteelSeries Rival 300, Optical Gaming Mouse - … _(platform ?)_ ｜ **native**: `<a_61><b_91><c_41>` HORI Real Arcade Pro 4 Kai for… ✗
- **beam top5**: `<a_61><b_99><c_240>`PS3, `<a_61><b_91><c_41>`PS4, `<a_61><b_166><c_249>`PS3, `<a_61><b_166><c_225>`PS4, `<a_113><b_35><c_8>`Gam
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (2 a top-classes); unique(a,b)=5/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: MAYFLASH N64 Controlle…, CM Storm QuickFire Rap…, Mayflash GameCube Cont…; novel candidates=0 (**pure history restatement**); genre: action,nostalg,retro.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item. Note: target shares word(s) ['gaming'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #427 — Near-miss·same (a,b) subcluster, only c differs · BEAM-COLLAPSE (<a_202×10/10)
- **History** (5 items; platforms PC×1,Switch×1,WiiU×1): MAYFLASH N64 Controller Ad… | CM Storm QuickFire Rapid-i… | Mayflash GameCube Controll… | HORI Real Arcade Pro 4 Kai… | SteelSeries Rival 300, Opt…
- **GT**: `<a_202><b_58><c_57>` Logitech G610 Orion Brown Backlit Mechanical G… _(platform ?)_ ｜ **native**: `<a_202><b_120><c_89>` Logitech G900 Chaos Spectrum P… ✗
- **beam top5**: `<a_202><b_253><c_105>`?, `<a_202><b_3><c_27>`?, `<a_202><b_3><c_102>`?, `<a_202><b_58><c_107>`?, `<a_202><b_120><c_89>`?
- **Rec↔GT gap**: beam's closest item shares (a,b) subcluster with GT, only c differs (same series/SKU), still missed; in beam: share-a=10/10, share-(a,b)=1/10.
- **Beam diversity**: **Low** (collapsed to <a_202 family 10/10); unique(a,b)=9/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 5/5 history items (coverage 100%), anchored on: MAYFLASH N64 Controlle…, CM Storm QuickFire Rap…, HORI Real Arcade Pro 4…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,nostalg,retro.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item. Note: target shares word(s) ['backlit', 'brown', 'gaming', 'keyboard', 'mechanical'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #428 — Category-miss·even top-class (a) wrong
- **History** (9 items; platforms PS4×6,XboxOne×2,Xbox360×1): Call of Duty: Infinite War… | Senran Kagura Estival Vers… | Doom - PlayStation 4 | NieR: Automata - Playstati… | Prey - Pre-load - PS4 Digi… | Call of Duty: Ghosts Harde…
- **GT**: `<a_231><b_76><c_105>` MOE CHRONICLE (ENGLISH SUBTITLES) - PS VITA _(platform PSVita)_ ｜ **native**: `<a_194><b_15><c_66>` Dishonored 2 - PlayStation 4 ✗
- **beam top5**: `<a_194><b_87><c_112>`PS4, `<a_194><b_15><c_66>`PS4, `<a_1><b_43><c_207>`PS4, `<a_24><b_72><c_142>`PS4, `<a_24><b_129><c_173>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PSVita vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (6 distinct a top-classes); unique(a,b)=10/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 7/9 history items (coverage 78%), anchored on: Dark Souls - Xbox 360, Dark Souls III: Collec…, Call of Duty: Infinite…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,multiplayer.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #429 — Category-OK·item wrong · BEAM-COLLAPSE (<a_162×10/10)
- **History** (8 items; platforms ?×6,3DS×2): Mario Classic Color Amiibo… | Nintendo Selects: Super Ma… | Skque 28 in 1 Game Card Ca… | PowerA Universal Nintendo … | Nintendo Selects: Super Ma… | Yoshi amiibo (Super Smash …
- **GT**: `<a_162><b_2><c_193>` Nintendo Falco Amiibo - Wii U _(platform WiiU)_ ｜ **native**: `<a_162><b_219><c_249>` Ganondorf amiibo - Japan Impor… ✗
- **beam top5**: `<a_162><b_231><c_30>`?, `<a_162><b_242><c_145>`?, `<a_162><b_235><c_217>`?, `<a_162><b_219><c_174>`?, `<a_162><b_214><c_137>`?
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; in beam: share-a=10/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_162 family 10/10); unique(a,b)=8/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 6/8 history items (coverage 75%), anchored on: Mario Modern Color Ami…, amiibo Rosetta & Chiko…, Mario Classic Color Am…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,nostalg,accessor.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item. Note: target shares word(s) ['amiibo'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #430 — Category-OK·item wrong · BEAM-COLLAPSE (<a_61×10/10)
- **History** (3 items; platforms XboxOne×3): Turtle Beach - Ear Force R… | Xbox One Play and Charge K… | Xbox One Chatpad + Chat He…
- **GT**: `<a_194><b_36><c_216>` Final Fantasy XV - Xbox One _(platform XboxOne)_ ｜ **native**: `<a_61><b_137><c_255>` Xbox One Kinect Sensor with Da… ✗
- **beam top5**: `<a_61><b_167><c_197>`Xbo, `<a_61><b_227><c_97>`Xbo, `<a_61><b_131><c_197>`Xbo, `<a_61><b_214><c_252>`Xbo, `<a_61><b_53><c_5>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_61 family 10/10); unique(a,b)=7/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Turtle Beach - Ear For…, Xbox One Chatpad + Cha…, Xbox One Play and Char…; novel candidates=0 (**pure history restatement**); genre: action,multiplayer,accessor.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #431 — Category-miss·even top-class (a) wrong
- **History** (4 items; platforms XboxOne×4): Turtle Beach - Ear Force R… | Xbox One Play and Charge K… | Xbox One Chatpad + Chat He… | Final Fantasy XV - Xbox On…
- **GT**: `<a_123><b_72><c_191>` Far Cry 4 - Xbox One _(platform XboxOne)_ ｜ **native**: `<a_7><b_11><c_2>` PDP Titanfall 2 Official Marau… ✗
- **beam top5**: `<a_61><b_131><c_197>`Xbo, `<a_39><b_77><c_105>`Xbo, `<a_7><b_248><c_16>`Xbo, `<a_7><b_36><c_0>`Xbo, `<a_7><b_248><c_2>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=XboxOne vs rec=Xbox); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 3/4 history items (coverage 75%), anchored on: Turtle Beach - Ear For…, Xbox One Play and Char…, Final Fantasy XV - Xbo…; novel candidates=0 (**pure history restatement**); genre: action,immersive,narrative.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #432 — Near-miss·same (a,b) subcluster, only c differs
- **History** (5 items; platforms XboxOne×5): Turtle Beach - Ear Force R… | Xbox One Play and Charge K… | Xbox One Chatpad + Chat He… | Final Fantasy XV - Xbox On… | Far Cry 4 - Xbox One
- **GT**: `<a_7><b_36><c_217>` Xbox One X 1TB Limited Edition Console - Proje… _(platform XboxOne)_ ｜ **native**: `<a_131><b_155><c_206>` Fallout 4 - Xbox One ✗
- **beam top5**: `<a_39><b_77><c_105>`Xbo, `<a_131><b_155><c_206>`Xbo, `<a_7><b_248><c_16>`Xbo, `<a_7><b_36><c_0>`Xbo, `<a_39><b_77><c_69>`Xbo
- **Rec↔GT gap**: beam's closest item shares (a,b) subcluster with GT, only c differs (same series/SKU), still missed; platform consistent(XboxOne); in beam: share-a=3/10, share-(a,b)=1/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=8/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 5/5 history items (coverage 100%), anchored on: Turtle Beach - Ear For…, Xbox One Play and Char…, Xbox One Chatpad + Cha…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=DRIFT (platform/word-linked) (score1). user's pick is **more history-consistent** than our top-1 (target2>rec1) → we **drifted off** a catchable continuation. Note: target shares word(s) ['discontinued'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #433 — Category-OK·item wrong
- **History** (2 items; platforms PS4×2): Uncharted 4: A Thief's End… | Batman: Arkham Knight - Pl…
- **GT**: `<a_71><b_86><c_236>` UNCHARTED: The Nathan Drake Collection - PlayS… _(platform PS4)_ ｜ **native**: `<a_201><b_31><c_107>` Uncharted 4: A Thief's End - P… ✗
- **beam top5**: `<a_201><b_145><c_9>`PS4, `<a_201><b_213><c_242>`PS4, `<a_123><b_72><c_7>`PS4, `<a_123><b_129><c_247>`PS4, `<a_131><b_210><c_0>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=10/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: Uncharted 4: A Thief's…, Batman: Arkham Knight …; novel candidates=0 (**pure history restatement**); genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**. Note: target shares word(s) ['uncharted'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #434 — Category-OK·item wrong
- **History** (4 items; platforms PSVita×4): Ratchet & Clank Vita Bundl… | PlayStation All-Stars Batt… | Sly Cooper: Thieves in Tim… | The Sly Collection - PlayS…
- **GT**: `<a_74><b_115><c_116>` Injustice 2 - PS4 [Digital Code] _(platform PS4)_ ｜ **native**: `<a_74><b_218><c_91>` Ratchet and Clank: Into the Ne… ✗
- **beam top5**: `<a_74><b_218><c_91>`PS3, `<a_74><b_218><c_196>`PS, `<a_74><b_229><c_149>`PS, `<a_74><b_218><c_206>`PS4, `<a_193><b_21><c_3>`PS
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform mismatch(GT=PS4 vs rec=PS3); in beam: share-a=5/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=7/10, platforms=5, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Ratchet & Clank Vita B…, PlayStation All-Stars …, Sly Cooper: Thieves in…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item. Note: target shares word(s) ['code', 'digital'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #435 — Category-OK·item wrong
- **History** (4 items; platforms PS4×4): Metal Gear Solid V: The Ph… | Naruto Shippuden: Ultimate… | Uncharted 4: A Thief's End… | Titanfall 2 - PlayStation …
- **GT**: `<a_92><b_20><c_102>` Call of Duty: Infinite Warfare - Standard Edit… _(platform PS4)_ ｜ **native**: `<a_39><b_51><c_21>` Titanfall 2 - Xbox One ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_39><b_51><c_21>`Xbo, `<a_39><b_77><c_105>`Xbo, `<a_39><b_78><c_54>`PS4, `<a_201><b_56><c_74>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=8/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 3/4 history items (coverage 75%), anchored on: Metal Gear Solid V: Th…, Uncharted 4: A Thief's…, Titanfall 2 - PlayStat…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item.

### #436 — Category-miss·even top-class (a) wrong
- **History** (2 items; platforms 3DS×1,?×1): Nintendo 3DS Compatible wi… | The Legend of Zelda: Major…
- **GT**: `<a_71><b_159><c_7>` Castlevania: Portrait of Ruin _(platform ?)_ ｜ **native**: `<a_216><b_112><c_114>` The Legend of Zelda: The Wind … ✗
- **beam top5**: `<a_113><b_235><c_2>`3DS, `<a_216><b_112><c_114>`Wii, `<a_119><b_168><c_182>`3DS, `<a_216><b_93><c_101>`DS, `<a_211><b_112><c_5>`3DS
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=8/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: Nintendo 3DS Compatibl…, The Legend of Zelda: M…; novel candidates=0 (**pure history restatement**); genre: action,puzzle,immersive.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #437 — Category-OK·item wrong · BEAM-COLLAPSE (<a_216×10/10)
- **History** (3 items; platforms ?×2,3DS×1): Nintendo 3DS Compatible wi… | The Legend of Zelda: Major… | Castlevania: Portrait of R…
- **GT**: `<a_216><b_124><c_98>` Castlevania _(platform ?)_ ｜ **native**: `<a_216><b_112><c_114>` The Legend of Zelda: The Wind … ✗
- **beam top5**: `<a_216><b_112><c_114>`Wii, `<a_216><b_159><c_141>`3DS, `<a_216><b_93><c_101>`DS, `<a_216><b_51><c_130>`3DS, `<a_216><b_219><c_158>`3DS
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; in beam: share-a=10/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_216 family 10/10); unique(a,b)=8/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Nintendo 3DS Compatibl…, The Legend of Zelda: M…, Castlevania: Portrait …; novel candidates=0 (**pure history restatement**); genre: action,adventure,rpg.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=SUBCLASS-continuation (score3). we recommended something **more history-consistent** than the user's actual pick (rec3>target2) → **model too conservative / user more exploratory**. Note: target shares word(s) ['castlevania'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #438 — Category-OK·item wrong · BEAM-COLLAPSE (<a_123×7/10)
- **History** (2 items; platforms PS4×2): 7 Days to Die - PlayStatio… | No Man's Sky - Limited Edi…
- **GT**: `<a_61><b_106><c_251>` HORI Fighting Stick Mini 4 for PlayStation 4 a… _(platform PS4)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_123><b_129><c_247>`PS4, `<a_123><b_58><c_16>`Xbo, `<a_123><b_58><c_78>`PS4, `<a_131><b_209><c_151>`PS4, `<a_123><b_160><c_188>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_123 family 7/10); unique(a,b)=8/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: 7 Days to Die - PlaySt…, No Man's Sky - Limited…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,adventure,strategy.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #439 — Category-miss·even top-class (a) wrong
- **History** (4 items; platforms XboxOne×3,3DS×1): FIFA 16 - Standard Edition… | Tom Clancy&rsquo;s Ghost R… | FIFA 17 - Xbox One | Shovel Knight - Nintendo 3…
- **GT**: `<a_39><b_51><c_21>` Titanfall 2 - Xbox One _(platform XboxOne)_ ｜ **native**: `<a_239><b_32><c_170>` Chibi-Robo!: Zip Lash - Ninten… ✗
- **beam top5**: `<a_239><b_32><c_111>`3DS, `<a_239><b_32><c_170>`3DS, `<a_1><b_101><c_3>`?, `<a_1><b_121><c_178>`3DS, `<a_1><b_25><c_254>`3DS
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=XboxOne vs rec=3DS); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=9/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: FIFA 16 - Standard Edi…, FIFA 17 - Xbox One, Tom Clancy&rsquo;s Gho…; novel candidates=0 (**pure history restatement**); genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #440 — Category-miss·even top-class (a) wrong
- **History** (5 items; platforms PS4×4,Xbox360×1): Assassin's Creed: Syndicat… | Fallout 4 - PlayStation 4 | Batman: Arkham Knight - Pl… | Deus Ex: Mankind Divided -… | Tom Clancy's Rainbow Six V…
- **GT**: `<a_194><b_76><c_27>` The Witcher Enhanced - PC _(platform PC)_ ｜ **native**: `<a_39><b_156><c_118>` Tom Clancy's Rainbow Six Siege… ✗
- **beam top5**: `<a_123><b_129><c_247>`PS4, `<a_123><b_193><c_255>`PS4, `<a_123><b_72><c_7>`PS4, `<a_39><b_156><c_118>`Xbo, `<a_39><b_156><c_145>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PC vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (2 a top-classes); unique(a,b)=7/10, platforms=5, unique titles=10/10.
- **Reasoning quality**: cites 5/5 history items (coverage 100%), anchored on: Assassin's Creed: Synd…, Fallout 4 - PlayStatio…, Batman: Arkham Knight …; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=DRIFT (platform/word-linked) (score1). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #441 — Category-OK·item wrong · BEAM-COLLAPSE (<a_123×8/10)
- **History** (6 items; platforms PS4×4,Xbox360×1,PC×1): Assassin's Creed: Syndicat… | Fallout 4 - PlayStation 4 | Batman: Arkham Knight - Pl… | Deus Ex: Mankind Divided -… | Tom Clancy's Rainbow Six V… | The Witcher Enhanced - PC
- **GT**: `<a_194><b_72><c_187>` The Witcher 2: Assassins Of Kings - Enhanced E… _(platform Xbox360)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_123><b_100><c_33>`PS4, `<a_39><b_51><c_188>`PS4, `<a_123><b_58><c_78>`PS4, `<a_123><b_58><c_16>`Xbo, `<a_123><b_76><c_232>`PS4
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform mismatch(GT=Xbox360 vs rec=PS4); in beam: share-a=1/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_123 family 8/10); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 5/6 history items (coverage 83%), anchored on: Assassin's Creed: Synd…, The Witcher Enhanced -…, Tom Clancy's Rainbow S…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=DRIFT (platform/word-linked) (score1). user's pick is **more history-consistent** than our top-1 (target2>rec1) → we **drifted off** a catchable continuation. Note: target shares word(s) ['enhanced', 'witcher'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #442 — Category-OK·item wrong
- **History** (4 items; platforms Wii×2,XboxOne×2): Wii Nunchuk Controller - W… | Wii Remote Controller | Zoo Tycoon XBOX ONE | Xbox One 500 GB Console - …
- **GT**: `<a_61><b_183><c_108>` Controller Gear Controller Stand v1.0 - Offici… _(platform XboxOne)_ ｜ **native**: `<a_61><b_53><c_5>` Xbox One Wireless Controller a… ✗
- **beam top5**: `<a_61><b_53><c_5>`Xbo, `<a_61><b_53><c_46>`Xbo, `<a_74><b_100><c_233>`?, `<a_61><b_53><c_0>`Xbo, `<a_61><b_181><c_195>`Xbo
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform consistent(XboxOne); in beam: share-a=5/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (6 distinct a top-classes); unique(a,b)=8/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 0/4 history items (coverage 0%); novel candidates=0 (**pure history restatement**); genre: action,multiplayer,immersive.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item. Note: target shares word(s) ['black', 'controller'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #443 — Category-OK·item wrong · BEAM-COLLAPSE (<a_118×8/10)
- **History** (8 items; platforms PSVita×6,PS4×1,?×1): Freedom Wars - PlayStation… | Silent Hill: Book of Memor… | Zero Time Dilemma Vita | Zero Escape: Virtue's Last… | The Amazing Spider-Man - P… | Batman: Arkham Origins Bla…
- **GT**: `<a_249><b_184><c_166>` PlayStation Vita Wi-Fi model Glacier White (PC… _(platform PSVita)_ ｜ **native**: `<a_118><b_191><c_72>` Batman: Arkham Origins Blackga… ✗
- **beam top5**: `<a_118><b_191><c_72>`PSV, `<a_118><b_185><c_102>`PS4, `<a_118><b_41><c_55>`?, `<a_118><b_150><c_122>`PS4, `<a_118><b_1><c_2>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PSVita); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_118 family 8/10); unique(a,b)=8/10, platforms=6, unique titles=10/10.
- **Reasoning quality**: cites 6/8 history items (coverage 75%), anchored on: The Last of Us Remaste…, Bloodborne, Zero Time Dilemma Vita; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=SUBCLASS-continuation (score3). we recommended something **more history-consistent** than the user's actual pick (rec3>target1) → **model too conservative / user more exploratory**.

### #444 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_162×10/10)
- **History** (9 items; platforms ?×6,3DS×2,WiiU×1): Nintendo Selects: Super Ma… | Skque 28 in 1 Game Card Ca… | PowerA Universal Nintendo … | Nintendo Selects: Super Ma… | Yoshi amiibo (Super Smash … | Nintendo Falco Amiibo - Wi…
- **GT**: `<a_119><b_35><c_129>` PDP New Nintendo 3DS XL Clip Armor - Mario _(platform 3DS)_ ｜ **native**: `<a_162><b_218><c_126>` Pikmin & Olimar Amiibo (Super … ✗
- **beam top5**: `<a_162><b_52><c_132>`?, `<a_162><b_134><c_221>`?, `<a_162><b_242><c_145>`?, `<a_162><b_219><c_249>`?, `<a_162><b_218><c_126>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_162 family 10/10); unique(a,b)=9/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 6/9 history items (coverage 67%), anchored on: Mario Modern Color Ami…, amiibo Rosetta & Chiko…, Mario Classic Color Am…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,adventure,nostalg.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item. Note: target shares word(s) ['mario'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #445 — Category-miss·even top-class (a) wrong
- **History** (6 items; platforms XboxOne×5,PS4×1): Call of Duty: Black Ops II… | Microsoft Xbox One Elite | Xbox One 1TB Console - Lim… | Xbox One 500GB Console - G… | Xbox One 1TB Console : Ris… | PlayStation 4 500GB Consol…
- **GT**: `<a_194><b_183><c_27>` Dark Souls III [Online Game Code] _(platform ?)_ ｜ **native**: `<a_201><b_36><c_181>` PlayStation 4 500GB Console - … ✗
- **beam top5**: `<a_201><b_36><c_195>`PS4, `<a_7><b_36><c_0>`Xbo, `<a_201><b_2><c_102>`PS4, `<a_201><b_36><c_181>`PS4, `<a_201><b_2><c_195>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=8/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/6 history items (coverage 67%), anchored on: Call of Duty: Black Op…, Xbox One 1TB Console -…, Xbox One 500GB Console…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,accessor.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item. Note: target shares word(s) ['iii'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #446 — Category-miss·even top-class (a) wrong
- **History** (1 items; platforms Wii×1): Mayflash W010 Wireless Sen…
- **GT**: `<a_194><b_21><c_1>` Final Fantasy X X-2 HD Remaster  Standard Edit… _(platform PS3)_ ｜ **native**: `<a_157><b_198><c_79>` Mayflash W010 Wireless Sensor … ✗
- **beam top5**: `<a_157><b_81><c_22>`Wii, `<a_21><b_94><c_14>`PS4, `<a_61><b_170><c_90>`PC, `<a_157><b_198><c_79>`Wii, `<a_21><b_94><c_61>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS3 vs rec=Wii); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=9/10, platforms=6, unique titles=10/10.
- **Reasoning quality**: cites 1/1 history items (coverage 100%), anchored on: Mayflash W010 Wireless…; novel candidates=0 (**pure history restatement**); genre: accessor.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #447 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_194×9/10)
- **History** (2 items; platforms Wii×1,PS3×1): Mayflash W010 Wireless Sen… | Final Fantasy X X-2 HD Rem…
- **GT**: `<a_61><b_9><c_122>` Mayflash Wireless PS3 Controller To PC USB Ada… _(platform PS3)_ ｜ **native**: `<a_194><b_21><c_76>` Final Fantasy X X-2 HD Remaste… ✗
- **beam top5**: `<a_194><b_21><c_76>`PS4, `<a_194><b_21><c_219>`PS4, `<a_194><b_121><c_62>`PS4, `<a_194><b_215><c_154>`?, `<a_194><b_21><c_254>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS3 vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_194 family 9/10); unique(a,b)=8/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: Mayflash W010 Wireless…, Final Fantasy X X-2 HD…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,immersive.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=SUBCLASS-continuation (score3). we recommended something **more history-consistent** than the user's actual pick (rec3>target1) → **model too conservative / user more exploratory**. Note: target shares word(s) ['mayflash', 'wireless'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #448 — Category-miss·even top-class (a) wrong
- **History** (3 items; platforms PS3×2,Wii×1): Mayflash W010 Wireless Sen… | Final Fantasy X X-2 HD Rem… | Mayflash Wireless PS3 Cont…
- **GT**: `<a_121><b_9><c_206>` Kingdom Hearts HD 2.5 ReMIX - PlayStation 3 _(platform PS3)_ ｜ **native**: `<a_194><b_15><c_66>` Dishonored 2 - PlayStation 4 ✗
- **beam top5**: `<a_61><b_251><c_144>`PS4, `<a_194><b_87><c_249>`PS4, `<a_61><b_251><c_51>`PS4, `<a_131><b_210><c_0>`PS4, `<a_194><b_21><c_76>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS3 vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=8/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Mayflash W010 Wireless…, Final Fantasy X X-2 HD…, Mayflash Wireless PS3 …; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,immersive.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**. Note: target shares word(s) ['hd'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #449 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_61×9/10)
- **History** (4 items; platforms PS3×3,Wii×1): Mayflash W010 Wireless Sen… | Final Fantasy X X-2 HD Rem… | Mayflash Wireless PS3 Cont… | Kingdom Hearts HD 2.5 ReMI…
- **GT**: `<a_157><b_14><c_80>` Perfect Shot for Wii (Colors May Vary) _(platform Wii)_ ｜ **native**: `<a_61><b_251><c_51>` DualShock 4 Wireless Controlle… ✗
- **beam top5**: `<a_61><b_44><c_172>`PS4, `<a_61><b_251><c_144>`PS4, `<a_61><b_131><c_197>`Xbo, `<a_61><b_75><c_143>`PS3, `<a_61><b_251><c_51>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=Wii vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_61 family 9/10); unique(a,b)=9/10, platforms=6, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Mayflash W010 Wireless…, Final Fantasy X X-2 HD…, Kingdom Hearts HD 2.5 …; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,immersive.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item.

### #450 — Category-OK·item wrong · BEAM-COLLAPSE (<a_61×9/10)
- **History** (5 items; platforms PS3×3,Wii×2): Mayflash W010 Wireless Sen… | Final Fantasy X X-2 HD Rem… | Mayflash Wireless PS3 Cont… | Kingdom Hearts HD 2.5 ReMI… | Perfect Shot for Wii (Colo…
- **GT**: `<a_30><b_40><c_121>` House of the Dead: Overkill - Nintendo Wii _(platform Wii)_ ｜ **native**: `<a_157><b_14><c_80>` Perfect Shot for Wii (Colors M… ✗
- **beam top5**: `<a_157><b_14><c_80>`Wii, `<a_61><b_131><c_197>`Xbo, `<a_61><b_0><c_187>`?, `<a_61><b_44><c_172>`PS4, `<a_61><b_0><c_234>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(Wii); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_61 family 9/10); unique(a,b)=9/10, platforms=6, unique titles=10/10.
- **Reasoning quality**: cites 3/5 history items (coverage 60%), anchored on: Mayflash W010 Wireless…, Final Fantasy X X-2 HD…, Kingdom Hearts HD 2.5 …; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,immersive.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=SUBCLASS-continuation (score3). we recommended something **more history-consistent** than the user's actual pick (rec3>target1) → **model too conservative / user more exploratory**.

### #451 — Category-OK·item wrong
- **History** (2 items; platforms XboxOne×2): Borderlands: The Handsome … | Xbox One Play and Charge K…
- **GT**: `<a_214><b_103><c_234>` Xbox One Wireless Controller (Without 3.5 mill… _(platform XboxOne)_ ｜ **native**: `<a_61><b_53><c_5>` Xbox One Wireless Controller a… ✗
- **beam top5**: `<a_7><b_248><c_16>`Xbo, `<a_61><b_53><c_5>`Xbo, `<a_131><b_155><c_206>`Xbo, `<a_61><b_214><c_252>`Xbo, `<a_7><b_2><c_105>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=9/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: Borderlands: The Hands…, Xbox One Play and Char…; novel candidates=0 (**pure history restatement**); genre: action,immersive,accessor.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item.

### #452 — Category-OK·item wrong
- **History** (2 items; platforms PS4×2): Star Wars: Battlefront - S… | NHL 17 - PlayStation 4
- **GT**: `<a_45><b_161><c_3>` NHL 16 - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_45><b_28><c_168>` FIFA 17 - PlayStation 4 ✗
- **beam top5**: `<a_45><b_28><c_168>`PS4, `<a_201><b_31><c_107>`PS4, `<a_39><b_51><c_188>`PS4, `<a_39><b_78><c_54>`PS4, `<a_45><b_193><c_4>`PS4
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform consistent(PS4); in beam: share-a=5/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=8/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: Star Wars: Battlefront…, NHL 17 - PlayStation 4; novel candidates=0 (**pure history restatement**); templated opening; genre: action,sports,strategy.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item. Note: target shares word(s) ['nhl'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #453 — Hit@1
- **History** (4 items; platforms PS4×4): Grand Theft Auto V - PlayS… | Uncharted 4: A Thief's End… | Fallout 4 - PlayStation 4 | Metal Gear Solid V: The Ph…
- **GT**: `<a_123><b_72><c_7>` Far Cry 4 - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_123><b_72><c_7>` Far Cry 4 - PlayStation 4 ✓
- **beam top5**: `<a_123><b_72><c_7>`PS4, `<a_201><b_145><c_9>`PS4, `<a_118><b_233><c_76>`PS4, `<a_118><b_95><c_6>`PS4, `<a_201><b_213><c_242>`PS4
- **Rec↔GT gap**: top-1 exact hit.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=10/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Grand Theft Auto V - P…, Uncharted 4: A Thief's…, Fallout 4 - PlayStatio…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). target is a sensible CLASS-cont and **was caught**.

### #454 — Category-OK·item wrong · BEAM-COLLAPSE (<a_202×7/10)
- **History** (4 items; platforms ?×2,XboxOne×1,PS3×1): Xbox One Stereo Headset Ad… | Logitech G910 Orion Spark … | Logitech G900 Chaos Spectr… | Matricom G-Pad XYBA Wirele…
- **GT**: `<a_61><b_131><c_197>` Microsoft Xbox Wireless Adapter for Windows 10 _(platform Xbox)_ ｜ **native**: `<a_202><b_120><c_89>` Logitech G900 Chaos Spectrum P… ✗
- **beam top5**: `<a_202><b_58><c_105>`?, `<a_202><b_200><c_67>`?, `<a_61><b_167><c_197>`Xbo, `<a_202><b_11><c_246>`?, `<a_61><b_170><c_90>`PC
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; in beam: share-a=3/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_202 family 7/10); unique(a,b)=9/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Xbox One Stereo Headse…, Logitech G910 Orion Sp…, Logitech G900 Chaos Sp…; novel candidates=0 (**pure history restatement**); genre: action,immersive,peripheral.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=SUBCLASS-continuation (score3). we recommended something **more history-consistent** than the user's actual pick (rec3>target2) → **model too conservative / user more exploratory**. Note: target shares word(s) ['adapter', 'wireless'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #455 — Category-OK·item wrong
- **History** (3 items; platforms PS4×2,PSVita×1): Persona 4: Dancing All Nig… | Plantronics GAMECOM 818 Wi… | Ratchet & Clank - PlayStat…
- **GT**: `<a_24><b_72><c_142>` Horizon Zero Dawn - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_121><b_35><c_0>` Megadimension Neptunia VII - P… ✗
- **beam top5**: `<a_131><b_209><c_151>`PS4, `<a_121><b_35><c_0>`PS4, `<a_121><b_76><c_208>`PS4, `<a_131><b_224><c_68>`PS4, `<a_121><b_146><c_26>`PS3
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=9/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Persona 4: Dancing All…, Plantronics GAMECOM 81…, Ratchet & Clank - Play…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item.

### #456 — Category-miss·even top-class (a) wrong
- **History** (4 items; platforms PS4×3,PSVita×1): Persona 4: Dancing All Nig… | Plantronics GAMECOM 818 Wi… | Ratchet & Clank - PlayStat… | Horizon Zero Dawn - PlaySt…
- **GT**: `<a_61><b_166><c_249>` Thrustmaster T150 RS Racing Wheel for PlayStat… _(platform PS3)_ ｜ **native**: `<a_121><b_155><c_99>` NieR: Automata - Playstation 4 ✗
- **beam top5**: `<a_24><b_86><c_14>`PS4, `<a_24><b_38><c_11>`PS4, `<a_24><b_96><c_27>`PS4, `<a_121><b_155><c_99>`PS4, `<a_1><b_43><c_207>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS3 vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=10/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Persona 4: Dancing All…, Ratchet & Clank - Play…, Plantronics GAMECOM 81…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #457 — Category-OK·item wrong
- **History** (4 items; platforms ?×3,GameCube×1): Metroid: Other M | Donkey Kong Classics | Soul Calibur II - Gamecube | Star Fox Assault
- **GT**: `<a_175><b_107><c_18>` Super Smash Bros Melee _(platform ?)_ ｜ **native**: `<a_208><b_51><c_1>` Soul Calibur IV - Playstation … ✗
- **beam top5**: `<a_208><b_51><c_1>`PS3, `<a_208><b_51><c_0>`PS, `<a_208><b_242><c_41>`PS, `<a_175><b_30><c_198>`?, `<a_208><b_26><c_212>`?
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; in beam: share-a=3/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=7/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Metroid: Other M, Soul Calibur II - Game…, Donkey Kong Classics; novel candidates=0 (**pure history restatement**); genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item.

### #458 — Category-miss·even top-class (a) wrong
- **History** (4 items; platforms PS3×3,PS×1): Tekken 5 - PlayStation 2 | PlayStation 3 Dualshock 3 … | PlayStation 3 Dualshock 3 … | PlayStation 3 - 320 GB Sys…
- **GT**: `<a_194><b_25><c_86>` Final Fantasy X _(platform ?)_ ｜ **native**: `<a_61><b_47><c_32>` PlayStation 3 Dualshock 3 Wire… ✗
- **beam top5**: `<a_61><b_47><c_8>`PS3, `<a_61><b_47><c_153>`PS3, `<a_61><b_47><c_32>`PS3, `<a_175><b_73><c_7>`PS3, `<a_61><b_47><c_10>`PS3
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=7/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: PlayStation 3 Dualshoc…, PlayStation 3 - 320 GB…, Tekken 5 - PlayStation…; novel candidates=0 (**pure history restatement**); genre: action,fighting,immersive.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=SUBCLASS-continuation (score3). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #459 — Category-miss·even top-class (a) wrong
- **History** (5 items; platforms PS3×3,PS×1,?×1): Tekken 5 - PlayStation 2 | PlayStation 3 Dualshock 3 … | PlayStation 3 Dualshock 3 … | PlayStation 3 - 320 GB Sys… | Final Fantasy X
- **GT**: `<a_193><b_21><c_3>` Mega Man X8 - PlayStation 2 _(platform PS2)_ ｜ **native**: `<a_194><b_255><c_47>` Final Fantasy X-2 ✗
- **beam top5**: `<a_194><b_255><c_47>`?, `<a_61><b_47><c_153>`PS3, `<a_194><b_24><c_128>`?, `<a_61><b_47><c_8>`PS3, `<a_194><b_140><c_160>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=6/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 3/4 history items (coverage 75%), anchored on: Final Fantasy X, PlayStation 3 Dualshoc…, PlayStation 3 - 320 GB…; novel candidates=0 (**pure history restatement**); genre: action,multiplayer,immersive.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #460 — Category-miss·even top-class (a) wrong
- **History** (4 items; platforms ?×3,Xbox360×1): Halo 3 - Xbox 360 | Call of Duty 4: Modern War… | Call of Duty 4: Modern War… | Fortune Street
- **GT**: `<a_240><b_33><c_93>` Grand Theft Auto IV _(platform ?)_ ｜ **native**: `<a_140><b_161><c_25>` Call of Duty: World at War Pla… ✗
- **beam top5**: `<a_140><b_161><c_25>`Xbo, `<a_39><b_40><c_248>`Xbo, `<a_140><b_221><c_161>`?, `<a_140><b_242><c_55>`?, `<a_140><b_212><c_79>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (2 a top-classes); unique(a,b)=8/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 2/3 history items (coverage 67%), anchored on: Call of Duty 4: Modern…, Fortune Street; novel candidates=0 (**pure history restatement**); genre: action,shooter,strategy.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #461 — Hit@2 · BEAM-COLLAPSE (<a_140×9/10)
- **History** (5 items; platforms ?×4,Xbox360×1): Halo 3 - Xbox 360 | Call of Duty 4: Modern War… | Call of Duty 4: Modern War… | Fortune Street | Grand Theft Auto IV
- **GT**: `<a_140><b_242><c_55>` Halo 3 _(platform ?)_ ｜ **native**: `<a_140><b_161><c_25>` Call of Duty: World at War Pla… ✗
- **beam top5**: `<a_140><b_161><c_25>`Xbo, `<a_140><b_242><c_55>`?, `<a_140><b_221><c_161>`?, `<a_39><b_40><c_248>`Xbo, `<a_140><b_221><c_21>`?
- **Rec↔GT gap**: correct item at beam rank 2, pred[0] prefix-depth only 1/3; in beam: share-a=9/10, share-(a,b)=1/10.
- **Beam diversity**: **Low** (collapsed to <a_140 family 9/10); unique(a,b)=6/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 3/4 history items (coverage 75%), anchored on: Call of Duty 4: Modern…, Grand Theft Auto IV, Fortune Street; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). target is a sensible CLASS-cont and **was caught**.

### #462 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_208×7/10)
- **History** (10 items; platforms PS4×5,PSVita×3,Xbox360×2): Tales of Hearts R (PSVita) | Tales of Vesperia - Xbox 3… | Tales of Vesperia - Xbox 3… | MegaTagmension Blanc + Nep… | Persona 5 - SteelBook Edit… | HORI Fighting Commander fo…
- **GT**: `<a_121><b_35><c_2>` Hyperdimension Neptunia Re;Birth3: V Generatio… _(platform PSVita)_ ｜ **native**: `<a_61><b_99><c_203>` HORI Fighting Commander for Pl… ✗
- **beam top5**: `<a_61><b_99><c_203>`PS4, `<a_61><b_99><c_2>`PS4, `<a_61><b_99><c_240>`PS3, `<a_208><b_128><c_224>`PS4, `<a_208><b_177><c_1>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PSVita vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_208 family 7/10); unique(a,b)=4/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 4/9 history items (coverage 44%), anchored on: The Legend of Heroes: …, Tales of Vesperia - Xb…, Guilty Gear Xrd -Revel…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,fighting.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=SUBCLASS-continuation (score3). we recommended something **more history-consistent** than the user's actual pick (rec3>target2) → **model too conservative / user more exploratory**.

### #463 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_240×8/10)
- **History** (5 items; platforms PS4×4,?×1): dreamGEAR- Playstation 4 C… | SmaAcc Cooling Fan with Du… | The Elder Scrolls V: Skyri… | DualShock 4 Wireless Contr… | Mafia II
- **GT**: `<a_119><b_217><c_221>` Grip-iT Analog Stick Covers, Set of 4 _(platform ?)_ ｜ **native**: `<a_80><b_48><c_186>` Mafia II ✗
- **beam top5**: `<a_80><b_48><c_186>`?, `<a_240><b_33><c_93>`?, `<a_240><b_221><c_2>`PS3, `<a_240><b_37><c_115>`Xbo, `<a_240><b_40><c_2>`PS
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_240 family 8/10); unique(a,b)=8/10, platforms=7, unique titles=10/10.
- **Reasoning quality**: cites 4/5 history items (coverage 80%), anchored on: dreamGEAR- Playstation…, SmaAcc Cooling Fan wit…, The Elder Scrolls V: S…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,immersive,narrative.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=SUBCLASS-continuation (score3). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #464 — Category-miss·even top-class (a) wrong
- **History** (1 items; platforms Xbox360×1): Velvet Assassin - Xbox 360
- **GT**: `<a_201><b_151><c_255>` Playstation Plus: 3 Month Membership [Digital … _(platform PS-generic)_ ｜ **native**: `<a_80><b_216><c_116>` Velvet Assassin - Xbox 360 ✗
- **beam top5**: `<a_80><b_216><c_116>`Xbo, `<a_80><b_216><c_22>`Xbo, `<a_80><b_216><c_55>`Xbo, `<a_80><b_176><c_55>`Xbo, `<a_205><b_208><c_52>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS-generic vs rec=Xbox360); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=8/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 1/1 history items (coverage 100%), anchored on: Velvet Assassin - Xbox…; novel candidates=0 (**pure history restatement**); genre: action,racing,multiplayer.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=SUBCLASS-continuation (score3). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #465 — Category-miss·even top-class (a) wrong
- **History** (2 items; platforms Xbox360×1,PS×1): Velvet Assassin - Xbox 360 | Playstation Plus: 3 Month …
- **GT**: `<a_118><b_71><c_33>` Assassin's Creed Rogue- Xbox 360 _(platform Xbox360)_ ｜ **native**: `<a_201><b_151><c_255>` Playstation Plus: 3 Month Memb… ✗
- **beam top5**: `<a_201><b_36><c_181>`PS4, `<a_201><b_31><c_107>`PS4, `<a_201><b_2><c_102>`PS4, `<a_123><b_72><c_7>`PS4, `<a_39><b_182><c_247>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=Xbox360 vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=9/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: Velvet Assassin - Xbox…, Playstation Plus: 3 Mo…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,racing,multiplayer.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #466 — Category-miss·even top-class (a) wrong
- **History** (3 items; platforms Xbox360×2,PS×1): Velvet Assassin - Xbox 360 | Playstation Plus: 3 Month … | Assassin's Creed Rogue- Xb…
- **GT**: `<a_140><b_156><c_111>` Alpha Protocol - Xbox 360 _(platform Xbox360)_ ｜ **native**: `<a_118><b_95><c_10>` Assassin&rsquo;s Creed Syndica… ✗
- **beam top5**: `<a_118><b_95><c_6>`PS4, `<a_118><b_95><c_10>`Xbo, `<a_123><b_72><c_182>`Xbo, `<a_123><b_72><c_191>`Xbo, `<a_118><b_95><c_2>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=Xbox360 vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=6/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Velvet Assassin - Xbox…, Assassin's Creed Rogue…, Playstation Plus: 3 Mo…; novel candidates=0 (**pure history restatement**); genre: action,adventure,shooter.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #467 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_140×9/10)
- **History** (4 items; platforms Xbox360×3,PS×1): Velvet Assassin - Xbox 360 | Playstation Plus: 3 Month … | Assassin's Creed Rogue- Xb… | Alpha Protocol - Xbox 360
- **GT**: `<a_80><b_95><c_147>` Dead Rising 3 _(platform ?)_ ｜ **native**: `<a_140><b_212><c_49>` Borderlands - Xbox 360 ✗
- **beam top5**: `<a_140><b_212><c_49>`Xbo, `<a_140><b_212><c_230>`Xbo, `<a_140><b_4><c_214>`PS3, `<a_140><b_225><c_255>`Xbo, `<a_140><b_65><c_232>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_140 family 9/10); unique(a,b)=7/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Assassin's Creed Rogue…, Alpha Protocol - Xbox …, Playstation Plus: 3 Mo…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item.

### #468 — Hit@4
- **History** (1 items; platforms Xbox360×1): Grand Theft Auto V - Xbox …
- **GT**: `<a_39><b_182><c_247>` Call of Duty: Black Ops III - Standard Edition… _(platform PS4)_ ｜ **native**: `<a_80><b_140><c_0>` Saints Row IV ✗
- **beam top5**: `<a_240><b_37><c_115>`Xbo, `<a_80><b_140><c_98>`Xbo, `<a_240><b_33><c_93>`?, `<a_39><b_182><c_247>`PS4, `<a_80><b_140><c_0>`?
- **Rec↔GT gap**: correct item at beam rank 4, pred[0] prefix-depth only 0/3; platform mismatch(GT=PS4 vs rec=XboxOne); in beam: share-a=2/10, share-(a,b)=2/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=7/10, platforms=5, unique titles=10/10.
- **Reasoning quality**: cites 1/1 history items (coverage 100%), anchored on: Grand Theft Auto V - X…; novel candidates=0 (**pure history restatement**); genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=DRIFT (platform/word-linked) (score1). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #469 — Hit@4
- **History** (2 items; platforms Xbox360×1,PS4×1): Grand Theft Auto V - Xbox … | Call of Duty: Black Ops II…
- **GT**: `<a_201><b_145><c_9>` The Witcher 3: Wild Hunt - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_201><b_31><c_107>` Uncharted 4: A Thief's End - P… ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_131><b_210><c_0>`PS4, `<a_39><b_69><c_69>`Xbo, `<a_201><b_145><c_9>`PS4, `<a_201><b_2><c_102>`PS4
- **Rec↔GT gap**: correct item at beam rank 4, pred[0] prefix-depth only 1/3; platform consistent(PS4); in beam: share-a=5/10, share-(a,b)=1/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=10/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: Grand Theft Auto V - X…, Call of Duty: Black Op…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,adventure,shooter.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). target is a sensible DRIFT and **was caught**.

### #470 — Hit@5
- **History** (3 items; platforms PS4×2,Xbox360×1): Grand Theft Auto V - Xbox … | Call of Duty: Black Ops II… | The Witcher 3: Wild Hunt -…
- **GT**: `<a_118><b_95><c_6>` Assassin's Creed: Syndicate - Standard Edition… _(platform PS4)_ ｜ **native**: `<a_131><b_210><c_0>` Fallout 4 - PlayStation 4 ✗
- **beam top5**: `<a_131><b_210><c_0>`PS4, `<a_201><b_31><c_107>`PS4, `<a_201><b_36><c_195>`PS4, `<a_201><b_213><c_242>`PS4, `<a_118><b_95><c_6>`PS4
- **Rec↔GT gap**: correct item at beam rank 5, pred[0] prefix-depth only 0/3; platform consistent(PS4); in beam: share-a=2/10, share-(a,b)=1/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=10/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Grand Theft Auto V - X…, Call of Duty: Black Op…, The Witcher 3: Wild Hu…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). target is a sensible DRIFT and **was caught**.

### #471 — Category-OK·item wrong
- **History** (4 items; platforms PS4×3,Xbox360×1): Grand Theft Auto V - Xbox … | Call of Duty: Black Ops II… | The Witcher 3: Wild Hunt -… | Assassin's Creed: Syndicat…
- **GT**: `<a_74><b_218><c_206>` Ratchet & Clank - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_118><b_185><c_102>` Batman: Arkham Knight - PlaySt… ✗
- **beam top5**: `<a_131><b_210><c_0>`PS4, `<a_118><b_185><c_102>`PS4, `<a_201><b_31><c_107>`PS4, `<a_123><b_72><c_7>`PS4, `<a_118><b_150><c_122>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=10/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 3/4 history items (coverage 75%), anchored on: Grand Theft Auto V - X…, Assassin's Creed: Synd…, Call of Duty: Black Op…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item.

### #472 — Category-OK·item wrong
- **History** (5 items; platforms PS4×4,Xbox360×1): Grand Theft Auto V - Xbox … | Call of Duty: Black Ops II… | The Witcher 3: Wild Hunt -… | Assassin's Creed: Syndicat… | Ratchet & Clank - PlayStat…
- **GT**: `<a_24><b_96><c_27>` Rise of the Tomb Raider: 20 Year Celebration -… _(platform PS4)_ ｜ **native**: `<a_131><b_210><c_0>` Fallout 4 - PlayStation 4 ✗
- **beam top5**: `<a_131><b_210><c_0>`PS4, `<a_201><b_31><c_107>`PS4, `<a_118><b_185><c_102>`PS4, `<a_201><b_213><c_242>`PS4, `<a_123><b_129><c_247>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=10/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 4/5 history items (coverage 80%), anchored on: Grand Theft Auto V - X…, Assassin's Creed: Synd…, Call of Duty: Black Op…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item.

### #473 — Category-miss·even top-class (a) wrong
- **History** (1 items; platforms 3DS×1): 28-in 1 Blue Game Card Cas…
- **GT**: `<a_250><b_55><c_95>` Mario Kart 7 _(platform ?)_ ｜ **native**: `<a_219><b_235><c_104>` Nintendo 3DS Game Card Case 24… ✗
- **beam top5**: `<a_219><b_235><c_104>`3DS, `<a_219><b_63><c_195>`3DS, `<a_113><b_104><c_28>`3DS, `<a_119><b_119><c_158>`3DS, `<a_113><b_235><c_2>`3DS
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=8/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 1/1 history items (coverage 100%), anchored on: 28-in 1 Blue Game Card…; novel candidates=0 (**pure history restatement**); genre: accessor.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #474 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_80×8/10)
- **History** (7 items; platforms PC×2,XboxOne×2,?×2): Dishonored - PC | Metal Gear Solid V: Ground… | Mass Effect 3 [Online Game… | Thief Xbox one | Dead Rising 3 | Dead Island - Xbox 360
- **GT**: `<a_201><b_85><c_136>` Until Dawn - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_80><b_212><c_169>` Dead Island - Xbox 360 ✗
- **beam top5**: `<a_80><b_212><c_236>`Xbo, `<a_80><b_59><c_196>`Xbo, `<a_80><b_212><c_38>`?, `<a_123><b_171><c_136>`?, `<a_123><b_72><c_182>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS4 vs rec=Xbox360); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_80 family 8/10); unique(a,b)=5/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 5/7 history items (coverage 71%), anchored on: Fallout 4 - PC, Metal Gear Solid V: Gr…, Mass Effect 3 [Online …; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=SUBCLASS-continuation (score3). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #475 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_39×8/10)
- **History** (1 items; platforms XboxOne×1): Battlefield 4 - Xbox One
- **GT**: `<a_245><b_141><c_101>` Lego Indiana Jones: The Original Adventures - … _(platform PS3)_ ｜ **native**: `<a_39><b_95><c_159>` Titanfall - Xbox One ✗
- **beam top5**: `<a_39><b_114><c_237>`Xbo, `<a_39><b_69><c_69>`Xbo, `<a_39><b_198><c_73>`?, `<a_39><b_95><c_159>`Xbo, `<a_39><b_198><c_69>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS3 vs rec=XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_39 family 8/10); unique(a,b)=7/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 1/1 history items (coverage 100%), anchored on: Battlefield 4 - Xbox O…; novel candidates=0 (**pure history restatement**); genre: action,strategy,multiplayer.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #476 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_245×9/10)
- **History** (2 items; platforms XboxOne×1,PS3×1): Battlefield 4 - Xbox One | Lego Indiana Jones: The Or…
- **GT**: `<a_74><b_184><c_158>` Lego Indiana Jones 2: The Adventure Continues … _(platform PS3)_ ｜ **native**: `<a_245><b_141><c_101>` Lego Indiana Jones: The Origin… ✗
- **beam top5**: `<a_245><b_141><c_7>`Wii, `<a_245><b_91><c_188>`Xbo, `<a_245><b_91><c_144>`PS3, `<a_245><b_141><c_249>`?, `<a_245><b_141><c_101>`PS3
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS3 vs rec=Wii); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_245 family 9/10); unique(a,b)=4/10, platforms=6, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: Battlefield 4 - Xbox O…, Lego Indiana Jones: Th…; novel candidates=0 (**pure history restatement**); genre: action,adventure,shooter.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=SUBCLASS-continuation (score3). we recommended something **more history-consistent** than the user's actual pick (rec3>target1) → **model too conservative / user more exploratory**. Note: target shares word(s) ['indiana', 'jones', 'lego'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #477 — Category-miss·even top-class (a) wrong
- **History** (6 items; platforms PS4×4,XboxOne×2): UNCHARTED: The Nathan Drak… | Tomb Raider: Definitive Ed… | Metal Gear Solid V: The Ph… | Battlefield Hardline - Pla… | The Witcher 3: Wild Hunt -… | Middle Earth: Shadow of Mo…
- **GT**: `<a_39><b_151><c_9>` Halo 5: Guardians _(platform ?)_ ｜ **native**: `<a_194><b_15><c_4>` Dishonored Definitive Edition … ✗
- **beam top5**: `<a_24><b_178><c_18>`Xbo, `<a_24><b_145><c_3>`Xbo, `<a_194><b_215><c_154>`?, `<a_201><b_145><c_9>`PS4, `<a_118><b_95><c_6>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=8/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 4/6 history items (coverage 67%), anchored on: UNCHARTED: The Nathan …, Metal Gear Solid V: Th…, The Witcher 3: Wild Hu…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #478 — Category-OK·item wrong
- **History** (7 items; platforms PS4×4,XboxOne×2,?×1): Tomb Raider: Definitive Ed… | Metal Gear Solid V: The Ph… | Battlefield Hardline - Pla… | The Witcher 3: Wild Hunt -… | Middle Earth: Shadow of Mo… | Halo 5: Guardians
- **GT**: `<a_118><b_98><c_14>` Tom Clancy's The Division - Xbox One _(platform XboxOne)_ ｜ **native**: `<a_194><b_88><c_140>` The Witcher 3: Wild Hunt - Xbo… ✗
- **beam top5**: `<a_24><b_178><c_18>`Xbo, `<a_123><b_72><c_191>`Xbo, `<a_118><b_95><c_6>`PS4, `<a_123><b_72><c_7>`PS4, `<a_194><b_15><c_4>`Xbo
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform consistent(XboxOne); in beam: share-a=2/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=8/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 6/7 history items (coverage 86%), anchored on: UNCHARTED: The Nathan …, Tomb Raider: Definitiv…, Metal Gear Solid V: Th…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #479 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_131×8/10)
- **History** (3 items; platforms PS4×1,?×1,XboxOne×1): Horizon Zero Dawn - PlaySt… | Battlefield 1 Exclusive Co… | Xbox One X 1TB Limited Edi…
- **GT**: `<a_8><b_70><c_241>` Xbox One Play and Charge Kit _(platform XboxOne)_ ｜ **native**: `<a_131><b_224><c_68>` Overwatch - Origins Edition - … ✗
- **beam top5**: `<a_131><b_41><c_229>`PS4, `<a_39><b_51><c_21>`Xbo, `<a_131><b_224><c_68>`PS4, `<a_131><b_37><c_113>`Xbo, `<a_131><b_38><c_83>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=XboxOne vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_131 family 8/10); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Horizon Zero Dawn - Pl…, Battlefield 1 Exclusiv…, Xbox One X 1TB Limited…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,multiplayer.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #480 — Category-miss·even top-class (a) wrong
- **History** (3 items; platforms PS4×3): Star Wars: Battlefront - S… | NHL 17 - PlayStation 4 | NHL 16 - PlayStation 4
- **GT**: `<a_22><b_88><c_75>` The Sims 4 - PC/Mac _(platform PC)_ ｜ **native**: `<a_45><b_28><c_168>` FIFA 17 - PlayStation 4 ✗
- **beam top5**: `<a_45><b_28><c_168>`PS4, `<a_201><b_31><c_107>`PS4, `<a_45><b_246><c_5>`PS4, `<a_39><b_77><c_105>`Xbo, `<a_39><b_51><c_188>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PC vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=8/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: NHL 17 - PlayStation 4, NHL 16 - PlayStation 4, Star Wars: Battlefront…; novel candidates=0 (**pure history restatement**); genre: action,shooter,sports.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #481 — Category-OK·item wrong · BEAM-COLLAPSE (<a_45×8/10)
- **History** (4 items; platforms PS4×3,PC×1): Star Wars: Battlefront - S… | NHL 17 - PlayStation 4 | NHL 16 - PlayStation 4 | The Sims 4 - PC/Mac
- **GT**: `<a_13><b_1><c_233>` Plants vs. Zombies Garden Warfare 2 - PlayStat… _(platform PS4)_ ｜ **native**: `<a_45><b_28><c_168>` FIFA 17 - PlayStation 4 ✗
- **beam top5**: `<a_45><b_246><c_5>`PS4, `<a_45><b_28><c_168>`PS4, `<a_45><b_246><c_6>`PS4, `<a_45><b_18><c_254>`PS4, `<a_39><b_78><c_54>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_45 family 8/10); unique(a,b)=6/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Star Wars: Battlefront…, NHL 17 - PlayStation 4, NHL 16 - PlayStation 4; novel candidates=0 (**pure history restatement**); templated opening; genre: action,sports,simulation.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #482 — Category-OK·item wrong
- **History** (5 items; platforms PS4×4,PC×1): Star Wars: Battlefront - S… | NHL 17 - PlayStation 4 | NHL 16 - PlayStation 4 | The Sims 4 - PC/Mac | Plants vs. Zombies Garden …
- **GT**: `<a_191><b_214><c_179>` Watch Dogs 2: Gold Edition (Includes Extra Con… _(platform PS4)_ ｜ **native**: `<a_45><b_28><c_168>` FIFA 17 - PlayStation 4 ✗
- **beam top5**: `<a_45><b_28><c_168>`PS4, `<a_39><b_78><c_54>`PS4, `<a_39><b_51><c_188>`PS4, `<a_131><b_224><c_68>`PS4, `<a_45><b_246><c_5>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=7/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 5/5 history items (coverage 100%), anchored on: NHL 17 - PlayStation 4, NHL 16 - PlayStation 4, Star Wars: Battlefront…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,shooter,sports.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #483 — Hit@2 · RERANK-HARM
- **History** (6 items; platforms PS4×5,PC×1): Star Wars: Battlefront - S… | NHL 17 - PlayStation 4 | NHL 16 - PlayStation 4 | The Sims 4 - PC/Mac | Plants vs. Zombies Garden … | Watch Dogs 2: Gold Edition…
- **GT**: `<a_45><b_28><c_168>` FIFA 17 - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_45><b_28><c_168>` FIFA 17 - PlayStation 4 ✓
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_45><b_28><c_168>`PS4, `<a_45><b_246><c_5>`PS4, `<a_131><b_209><c_151>`PS4, `<a_131><b_224><c_68>`PS4
- **Rec↔GT gap**: correct item at beam rank 2, pred[0] prefix-depth only 0/3; platform consistent(PS4); in beam: share-a=3/10, share-(a,b)=2/10.
- **Beam diversity**: **High** (6 distinct a top-classes); unique(a,b)=9/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 5/6 history items (coverage 83%), anchored on: Star Wars: Battlefront…, NHL 17 - PlayStation 4, The Sims 4 - PC/Mac; novel candidates=0 (**pure history restatement**); templated opening; genre: action,shooter,sports.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=DRIFT (platform/word-linked) (score1). target is a sensible CLASS-cont and **was caught**.

### #484 — Hit@2
- **History** (4 items; platforms XboxOne×2,PS4×2): The Witcher 3: Wild Hunt -… | Nyko Intercooler Stand - C… | Middle Earth: Shadow of Mo… | Mafia III - PlayStation 4
- **GT**: `<a_201><b_31><c_107>` Uncharted 4: A Thief's End - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_191><b_10><c_232>`PS4, `<a_201><b_31><c_107>`PS4, `<a_201><b_18><c_56>`PS4, `<a_123><b_76><c_232>`PS4, `<a_201><b_213><c_242>`PS4
- **Rec↔GT gap**: correct item at beam rank 2, pred[0] prefix-depth only 0/3; platform consistent(PS4); in beam: share-a=4/10, share-(a,b)=1/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: The Witcher 3: Wild Hu…, Middle Earth: Shadow o…, Mafia III - PlayStatio…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). target is a sensible DRIFT and **was caught**.

### #485 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_111×9/10)
- **History** (1 items; platforms Wii×1): Just Dance 2016 - Wii
- **GT**: `<a_7><b_215><c_114>` Turtle Beach - Ear Force Stealth 400 Fully Wir… _(platform PS4)_ ｜ **native**: `<a_111><b_176><c_225>` Just Dance 2016 - Xbox 360 ✗
- **beam top5**: `<a_111><b_19><c_7>`Xbo, `<a_111><b_222><c_31>`Xbo, `<a_111><b_238><c_188>`PS4, `<a_111><b_176><c_225>`Xbo, `<a_175><b_171><c_29>`Wii
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS4 vs rec=XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_111 family 9/10); unique(a,b)=8/10, platforms=5, unique titles=10/10.
- **Reasoning quality**: cites 0/1 history items (coverage 0%); novel candidates=0 (**pure history restatement**); genre: action,competitive.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #486 — Category-miss·even top-class (a) wrong
- **History** (2 items; platforms Wii×1,PS4×1): Just Dance 2016 - Wii | Turtle Beach - Ear Force S…
- **GT**: `<a_201><b_85><c_136>` Until Dawn - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_7><b_248><c_16>` Xbox One Limited Edition Halo … ✗
- **beam top5**: `<a_7><b_248><c_16>`Xbo, `<a_7><b_248><c_2>`Xbo, `<a_111><b_78><c_70>`Xbo, `<a_111><b_238><c_188>`PS4, `<a_61><b_217><c_168>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS4 vs rec=XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=8/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: Just Dance 2016 - Wii, Turtle Beach - Ear For…; novel candidates=0 (**pure history restatement**); genre: action,immersive,accessor.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #487 — Category-OK·item wrong
- **History** (10 items; platforms ?×4,WiiU×2,PS3×1): PS3 Starhawk | Ratchet & Clank Collection | Sonic Adventure 2 Battle -… | Kirby: Planet Robobot - Ni… | Ratchet & Clank - PlayStat… | Spyro the Dragon
- **GT**: `<a_250><b_57><c_233>` Super Mario 3D World - Nintendo Wii U _(platform WiiU)_ ｜ **native**: `<a_239><b_148><c_156>` Spyro 2: Ripto's Rage ✗
- **beam top5**: `<a_239><b_115><c_84>`PS, `<a_239><b_152><c_205>`?, `<a_239><b_152><c_35>`?, `<a_239><b_148><c_156>`?, `<a_239><b_92><c_111>`?
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform mismatch(GT=WiiU vs rec=PS2); in beam: share-a=2/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=8/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 6/10 history items (coverage 60%), anchored on: Super Paper Mario, Paper Mario: Color Spl…, PS3 Starhawk; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item. Note: target shares word(s) ['mario', 'super'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #488 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_141×7/10)
- **History** (2 items; platforms Xbox360×1,?×1): Star Wars the Force Unleas… | Fallout 3: Game of the Yea…
- **GT**: `<a_140><b_3><c_78>` Lollipop Chainsaw - Xbox 360 _(platform Xbox360)_ ｜ **native**: `<a_131><b_233><c_112>` Fallout: New Vegas - Ultimate … ✗
- **beam top5**: `<a_131><b_233><c_112>`?, `<a_141><b_221><c_44>`?, `<a_80><b_48><c_186>`?, `<a_141><b_225><c_35>`Xbo, `<a_141><b_212><c_21>`PC
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_141 family 7/10); unique(a,b)=10/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 2/2 history items (coverage 100%), anchored on: Star Wars the Force Un…, Fallout 3: Game of the…; novel candidates=0 (**pure history restatement**); genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item.

### #489 — Category-miss·even top-class (a) wrong
- **History** (1 items; platforms PS4×1): Mayflash F500 Arcade Fight…
- **GT**: `<a_157><b_232><c_136>` Sanwa GT-Y Octagonal Restrictor Plate for JLF … _(platform ?)_ ｜ **native**: `<a_61><b_99><c_2>` Mayflash F500 Arcade Fight Sti… ✗
- **beam top5**: `<a_61><b_99><c_2>`PS4, `<a_208><b_51><c_1>`PS3, `<a_208><b_196><c_65>`PS, `<a_113><b_35><c_8>`Gam, `<a_113><b_35><c_14>`Gam
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=6/10, platforms=5, unique titles=10/10.
- **Reasoning quality**: cites 1/1 history items (coverage 100%), anchored on: Mayflash F500 Arcade F…; novel candidates=0 (**pure history restatement**); genre: action,fighting,nostalg.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=SUBCLASS-continuation (score3). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #490 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_249×9/10)
- **History** (2 items; platforms PSVita×2): PlayStation Vita Wi-Fi mod… | Smatree P100 Carrying Case…
- **GT**: `<a_13><b_218><c_173>` Agents of Mayhem - PlayStation 4 _(platform PS4)_ ｜ **native**: `<a_249><b_31><c_126>` Sony PlayStation Vita WiFi ✗
- **beam top5**: `<a_231><b_142><c_63>`PSV, `<a_249><b_217><c_160>`PSV, `<a_249><b_181><c_229>`PSV, `<a_249><b_31><c_126>`PSV, `<a_249><b_63><c_20>`PSV
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS4 vs rec=PSVita); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_249 family 9/10); unique(a,b)=7/10, platforms=1, unique titles=10/10.
- **Reasoning quality**: cites 0/2 history items (coverage 0%); novel candidates=0 (**pure history restatement**); genre: accessor.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=SUBCLASS-continuation (score3). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #491 — Category-miss·even top-class (a) wrong · BEAM-COLLAPSE (<a_211×10/10)
- **History** (4 items; platforms 3DS×3,?×1): YO-KAI WATCH - 3DS | Etrian Mystery Dungeon - N… | Paper Mario: Sticker Star | YO-KAI WATCH 2: Fleshy Sou…
- **GT**: `<a_195><b_53><c_2>` Final Fantasy: The 4 Heroes of Light _(platform ?)_ ｜ **native**: `<a_211><b_149><c_18>` YO-KAI WATCH - 3DS ✗
- **beam top5**: `<a_211><b_31><c_154>`3DS, `<a_211><b_105><c_215>`?, `<a_211><b_112><c_5>`3DS, `<a_211><b_159><c_123>`3DS, `<a_211><b_229><c_134>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_211 family 10/10); unique(a,b)=9/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 2/4 history items (coverage 50%), anchored on: YO-KAI WATCH - 3DS, Etrian Mystery Dungeon…; novel candidates=0 (**pure history restatement**); genre: adventure,rpg,puzzle.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #492 — Category-OK·item wrong
- **History** (4 items; platforms XboxOne×2,Xbox360×1,Switch×1): Rocksmith 2014 Edition - X… | Alien: Isolation - Xbox On… | Doom - Xbox One | Razer BlackWidow Chroma: C…
- **GT**: `<a_202><b_253><c_113>` CORSAIR Sabre - RGB Gaming Mouse - Lightweight… _(platform ?)_ ｜ **native**: `<a_202><b_11><c_246>` Razer Naga Epic Chroma MMO Gam… ✗
- **beam top5**: `<a_202><b_11><c_246>`?, `<a_202><b_58><c_107>`?, `<a_202><b_11><c_104>`?, `<a_202><b_86><c_197>`DS, `<a_202><b_16><c_110>`?
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; in beam: share-a=6/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (2 a top-classes); unique(a,b)=8/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Alien: Isolation - Xbo…, Doom - Xbox One, Rocksmith 2014 Edition…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,shooter,immersive.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item. Note: target shares word(s) ['gaming', 'rgb'] with history — **semantically related yet missed** (exposes SID-class misalignment / tokenization limit).

### #493 — Category-miss·even top-class (a) wrong
- **History** (3 items; platforms ?×1,WiiU×1,XboxOne×1): Diablo III: Reaper of Soul… | Mayflash GameCube Controll… | Rock Band 4 Band-in-a-Box …
- **GT**: `<a_214><b_190><c_72>` UtechSmart Venus 16400 DPI High Precision Lase… _(platform ?)_ ｜ **native**: `<a_111><b_71><c_5>` Rock Band 4 Band-in-a-Box Bund… ✗
- **beam top5**: `<a_111><b_71><c_51>`Xbo, `<a_111><b_164><c_141>`Xbo, `<a_111><b_60><c_202>`PS4, `<a_111><b_164><c_222>`PS4, `<a_111><b_45><c_113>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=8/10, platforms=5, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Diablo III: Reaper of …, Mayflash GameCube Cont…, Rock Band 4 Band-in-a-…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,rpg,immersive.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=SUBCLASS-continuation (score3). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #494 — Category-miss·even top-class (a) wrong
- **History** (4 items; platforms ?×2,WiiU×1,XboxOne×1): Diablo III: Reaper of Soul… | Mayflash GameCube Controll… | Rock Band 4 Band-in-a-Box … | UtechSmart Venus 16400 DPI…
- **GT**: `<a_131><b_224><c_127>` Overwatch - Collector's Edition - PC _(platform PC)_ ｜ **native**: `<a_202><b_11><c_2>` SteelSeries Siberia 200 Gaming… ✗
- **beam top5**: `<a_61><b_167><c_197>`Xbo, `<a_61><b_131><c_197>`Xbo, `<a_7><b_248><c_16>`Xbo, `<a_202><b_200><c_67>`?, `<a_111><b_164><c_222>`PS4
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PC vs rec=XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=10/10, platforms=4, unique titles=10/10.
- **Reasoning quality**: cites 3/4 history items (coverage 75%), anchored on: Diablo III: Reaper of …, Rock Band 4 Band-in-a-…, UtechSmart Venus 16400…; novel candidates=0 (**pure history restatement**); templated opening; genre: action,adventure,rpg.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=DRIFT (platform/word-linked) (score1). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #495 — Category-OK·item wrong · BEAM-COLLAPSE (<a_205×9/10)
- **History** (4 items; platforms PS4×4): Assassin's Creed Unity Lim… | Uncharted 4: A Thief's End… | Assassin's Creed: Syndicat… | Gran Turismo Sport - PlayS…
- **GT**: `<a_74><b_115><c_116>` Injustice 2 - PS4 [Digital Code] _(platform PS4)_ ｜ **native**: `<a_205><b_0><c_108>` MotoGP 14 - PlayStation 4 ✗
- **beam top5**: `<a_205><b_8><c_170>`PS4, `<a_205><b_207><c_181>`PS4, `<a_118><b_185><c_102>`PS4, `<a_205><b_0><c_108>`PS4, `<a_205><b_0><c_112>`?
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_205 family 9/10); unique(a,b)=8/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/4 history items (coverage 100%), anchored on: Assassin's Creed Unity…, Assassin's Creed: Synd…, Uncharted 4: A Thief's…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #496 — Category-OK·item wrong · BEAM-COLLAPSE (<a_39×7/10)
- **History** (5 items; platforms XboxOne×3,PS4×2): Metal Gear Solid V: The Ph… | UNCHARTED: The Nathan Drak… | Rise of the Tomb Raider - … | Doom - Xbox One | Titanfall 2 - Xbox One
- **GT**: `<a_13><b_218><c_16>` Agents of Mayhem - Xbox One _(platform XboxOne)_ ｜ **native**: `<a_39><b_77><c_105>` Call of Duty: Infinite Warfare… ✗
- **beam top5**: `<a_39><b_77><c_105>`Xbo, `<a_39><b_77><c_69>`Xbo, `<a_39><b_51><c_188>`PS4, `<a_123><b_58><c_16>`Xbo, `<a_39><b_78><c_205>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform consistent(XboxOne); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Low** (collapsed to <a_39 family 7/10); unique(a,b)=6/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 5/5 history items (coverage 100%), anchored on: Metal Gear Solid V: Th…, UNCHARTED: The Nathan …, Rise of the Tomb Raide…; novel candidates=0 (**pure history restatement**); genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=CLASS-continuation (score2). we recommended something **more history-consistent** than the user's actual pick (rec2>target1) → **model too conservative / user more exploratory**.

### #497 — Category-miss·even top-class (a) wrong
- **History** (6 items; platforms XboxOne×4,PS4×2): Metal Gear Solid V: The Ph… | UNCHARTED: The Nathan Drak… | Rise of the Tomb Raider - … | Doom - Xbox One | Titanfall 2 - Xbox One | Agents of Mayhem - Xbox On…
- **GT**: `<a_140><b_176><c_51>` Battlefield: Bad Company _(platform ?)_ ｜ **native**: `<a_123><b_228><c_139>` Dead Rising 4 - Xbox One ✗
- **beam top5**: `<a_13><b_93><c_77>`Xbo, `<a_13><b_224><c_3>`Xbo, `<a_39><b_77><c_105>`Xbo, `<a_123><b_58><c_16>`Xbo, `<a_13><b_224><c_7>`Xbo
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (3 a top-classes); unique(a,b)=7/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 4/6 history items (coverage 67%), anchored on: Metal Gear Solid V: Th…, Rise of the Tomb Raide…, Doom - Xbox One; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=CLASS-continuation (score2); our pred[0]=CLASS-continuation (score2). same relatedness tier (score2) but wrong specific item.

### #498 — Category-miss·even top-class (a) wrong
- **History** (3 items; platforms PS4×2,PSP×1): Horizon Zero Dawn - PlaySt… | XFUNY(TM) Dustproof Quakep… | NieR: Automata - Playstati…
- **GT**: `<a_205><b_138><c_74>` Twisted Metal - PS3 [Digital Code] _(platform PS3)_ ｜ **native**: `<a_121><b_155><c_99>` NieR: Automata - Playstation 4 ✗
- **beam top5**: `<a_121><b_76><c_208>`PS4, `<a_1><b_173><c_4>`PS4, `<a_1><b_116><c_233>`PS4, `<a_121><b_91><c_244>`PS4, `<a_1><b_150><c_189>`PS3
- **Rec↔GT gap**: beam mismatches GT even at top-class a — category judgment failed; platform mismatch(GT=PS3 vs rec=PS4); in beam: share-a=0/10, share-(a,b)=0/10.
- **Beam diversity**: **Medium** (4 a top-classes); unique(a,b)=9/10, platforms=3, unique titles=10/10.
- **Reasoning quality**: cites 3/3 history items (coverage 100%), anchored on: Horizon Zero Dawn - Pl…, NieR: Automata - Plays…, XFUNY(TM) Dustproof Qu…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=EXPLORATION (unrelated) (score0); our pred[0]=CLASS-continuation (score2). user **EXPLORED**: target has no SID-class/platform/word link to history → a history-based model can hardly catch this (**ceiling loss**).

### #499 — Category-OK·item wrong
- **History** (4 items; platforms PS4×2,PSP×1,PS3×1): Horizon Zero Dawn - PlaySt… | XFUNY(TM) Dustproof Quakep… | NieR: Automata - Playstati… | Twisted Metal - PS3 [Digit…
- **GT**: `<a_123><b_160><c_188>` Dead Island Definitive Collection - PlayStatio… _(platform PS4)_ ｜ **native**: `<a_121><b_76><c_208>` Star Ocean: Integrity and Fait… ✗
- **beam top5**: `<a_1><b_116><c_233>`PS4, `<a_121><b_76><c_208>`PS4, `<a_1><b_173><c_4>`PS4, `<a_1><b_150><c_189>`PS3, `<a_121><b_35><c_0>`PS4
- **Rec↔GT gap**: beam only matches GT top-class a; b/c all off; platform consistent(PS4); in beam: share-a=1/10, share-(a,b)=0/10.
- **Beam diversity**: **High** (5 distinct a top-classes); unique(a,b)=10/10, platforms=2, unique titles=10/10.
- **Reasoning quality**: cites 3/4 history items (coverage 75%), anchored on: Horizon Zero Dawn - Pl…, NieR: Automata - Plays…, Twisted Metal - PS3 [D…; novel candidates=0 (**pure history restatement**); templated opening; genre: action-adventure,action,adventure.
- **Target sensibility (ceiling)**: target=DRIFT (platform/word-linked) (score1); our pred[0]=DRIFT (platform/word-linked) (score1). same relatedness tier (score1) but wrong specific item.

---

## Appendix A: Human-read representative cases

**#0 exploration failure** — History LEGO/Minecraft (PS3 family-friendly); GT = Just Dance 2017 (motion/dance). The "PlayStation Eye (motion camera)" in history strongly hints at motion/dance, but reasoning misreads it as generic "interactive gaming" and the beam collapses onto LEGO (`<a_245>`). The target is a sensible "same-platform, different-genre" drift, but reasoning misses the key cue.

**#1 tokenization limit** — History includes **Dark Souls III**; GT = **Demon's Souls** (same-studio Souls-like). Relatedness catches it via the shared word "souls" (CLASS-continuation), but the SID's a top-class does not co-locate the two (GT a=194 not in history a-set), and the model drifts to shooters (`<a_39>`) dragged by Titanfall/Madden. → **semantically related yet SID-misaligned**, exposing a tokenization ceiling.

**#3 RERANK harm** — All PS4 action-adventure; GT = Uncharted 4. Native hits directly, but the constrained beam ranks a controller at #1 and pushes the correct answer to #2 → HR@1 lost.

**#130 easy hit** — Retro-console accessories, GT = Gamecube controller (already in history). Repurchase/same-family; category restatement suffices to hit.

> Hits concentrate on **repurchase / same-series / same-platform accessories** (subclass-continuation HR 47%); failures concentrate on **exploration** and cases requiring **specific-title / genre pivot**.

## Appendix B: Follow-up implications

1. **Ceiling is bounded by user exploratory behavior**: ~30% of targets are exploration and 44% drift; a pure history-sequence model has a low ceiling → inject non-history signals (content semantics / collaborative filtering / temporal / context) to attack the exploration tier.
2. **Model is over-conservative**: our pred[0] is on average more history-consistent than the user's actual click (more conservative in 38% of items) → users actually explore more; add an exploration/novelty incentive to the RL reward to correct the exploitation bias.
3. **Reasoning ≈ stylized prefix**: 99.9% of cited SIDs are history restatements, 0.01 new candidates/item → make reasoning actually ground candidate items.
4. **Constrained beam is net-negative**: native HR@1 > beam HR@1, net loss of 5 items → drop/replace the constrained beam.
5. **Tokenization alignment**: cases like #1 (same-studio same-series, Dark Souls → Demon's Souls) are semantically related yet land in different SID a-classes → improve SID quantization so semantic neighbors share prefixes, directly raising the continuation-tier ceiling.
6. **Redundancy is compressible**: 70% templated opening, near-constant length → add a reasoning length/density penalty.
