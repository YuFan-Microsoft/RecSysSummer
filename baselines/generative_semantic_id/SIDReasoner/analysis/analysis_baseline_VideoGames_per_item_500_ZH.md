# SIDReasoner Baseline · Video_Games · 前500条【逐条分析】

> 源: HF `yufan/rec_inference_results/baseline_Video_Games.json`（官方 endpoint 解码）。thinking mode + 约束 beam-10；`native`=`</think>`后贪心单条解码。

## 方法说明
每条从四个维度分析：**(1) 推荐↔GT差距** SID前缀深度a>b>c(0–3)衡量差多远+平台错配；**(2) beam多样性** unique a/(a,b)/平台/标题、是否坍缩；**(3) reasoning质量** 复述/新候选/genre/平台pivot；**(4) target合理性(天花板)**——用户真实 target 相对 history 是延续还是探索，并对比“用户真实点击 vs 我们推荐”谁更贴近历史。relatedness 用 SID前缀(SID本身即语义量化)+平台+标题词面 三信号，分四档：子类延续(3)/大类延续(2)/漂移(1)/探索(0)。

## ★ 用户 target 合理性 & 性能天花板（核心）

**用户真实 target 相对历史的关联分布**（决定“能不能被历史预测”）:
| 关联档 | 含义 | 条数 | 占比 | beam@10 HR | native HR |
|---|---|---:|---:|---:|---:|
| 3 子类延续 | 复购/同系列 | 19 | 3.8% | 47.4% | 42.1% |
| 2 大类延续 | 同大类不同款 | 114 | 22.8% | 16.7% | 6.1% |
| 1 漂移(平台/词面关联) | 换平台/词面相关 | 218 | 43.6% | 5.0% | 0.5% |
| 0 探索(无关联) | 全新领域 | 149 | 29.8% | 1.3% | 0.0% |

- **硬天花板**: **探索类 target 占 29.8%**（与历史零关联），beam@10 命中仅 1.3% → 基于历史的模型基本打不中；再加漂移类 43.6%(HR 5.0%)，**共 73.4% 的 target 仅弱关联或无关联**。
- **真正可命中的信号量少**: 明确“延续”(大类+子类)仅占 **26.6%**；模型收益几乎全来自这部分（子类延续 HR 47.4%、大类延续 HR 16.7%）。
- **谁更 make sense（保守度对比）**: 平均关联分 target=1.01 vs 我们pred[0]=1.83 vs native=2.07。其中我们推荐**比用户真实点击更贴历史**的有 **299(60%)** 条，我们更发散的 40(8%) 条，同档 161 条。→ **模型系统性比用户更保守**：押注“历史延续”，而用户近半在探索，二者错位正是天花板的主因。
- **含义**: 在 exploration/drift 子集上，任何纯历史序列模型的上限都很低；真正的提升空间在 **26.6% 的延续类**里把 HR 从当前 ~21% 拉高，以及**引入历史之外的信号**(内容/协同/时序)去攻探索类。

---

## 逐条分析（#0–#499）

### #0 — 类目对·item错 · BEAM坍缩(<a_245×9/10)
- **历史**(6项; 平台 PS3×4,PS×2): PlayStation Eye | PlayStation Eye | Angry Birds Star Wars - Pl… | DuckTales - Remastered PS3… | Minecraft - PlayStation 3 | LEGO Jurassic World - Play…
- **GT**: `<a_111><b_158><c_21>` Just Dance 2017 - PlayStation 3 _(平台 PS3)_ ｜ **native**: `<a_245><b_232><c_5>` LEGO Jurassic World - PlayStat… ✗
- **beam top5**: `<a_245><b_91><c_144>`PS3, `<a_245><b_232><c_39>`PSV, `<a_245><b_86><c_8>`PS3, `<a_245><b_232><c_5>`PS3, `<a_245><b_91><c_188>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS3)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_245 家族 9/10）；unique(a,b)=6/10，平台数=5，unique标题=10/10。
- **reasoning质量**: 引用历史 4/5（覆盖80%），锚定: Angry Birds Star Wars …, LEGO Jurassic World - …, DuckTales - Remastered…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #1 — 类目错·(a)大类都不对
- **历史**(4项; 平台 PS4×4): Metro Redux - PlayStation … | Dark Souls III - PlayStati… | Madden NFL 17 - Standard E… | Titanfall 2 - PlayStation …
- **GT**: `<a_194><b_97><c_127>` Demon's Souls _(平台 ?)_ ｜ **native**: `<a_39><b_51><c_21>` Titanfall 2 - Xbox One ✗
- **beam top5**: `<a_39><b_77><c_105>`Xbo, `<a_201><b_56><c_74>`PS4, `<a_39><b_51><c_21>`Xbo, `<a_39><b_78><c_54>`PS4, `<a_39><b_77><c_69>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=7/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Metro Redux - PlayStat…, Dark Souls III - PlayS…, Madden NFL 17 - Standa…；新候选=0（**纯复述历史**）；模板开头；genre: action,multiplayer,immersive。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。 注意 target 与历史共享词 ['souls']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #2 — 类目对·item错
- **历史**(5项; 平台 PS4×5): Watch Dogs 2 - PlayStation… | Ratchet & Clank - PlayStat… | Horizon Zero Dawn - PlaySt… | CorpCo 6ft AC Power Cord f… | Deadpool - PlayStation 4
- **GT**: `<a_61><b_251><c_51>` DualShock 4 Wireless Controller for PlayStatio… _(平台 PS4)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_24><b_86><c_14>`PS4, `<a_201><b_31><c_107>`PS4, `<a_201><b_18><c_56>`PS4, `<a_123><b_58><c_78>`PS4, `<a_24><b_96><c_27>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=10/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 5/5（覆盖100%），锚定: Watch Dogs 2 - PlaySta…, Ratchet & Clank - Play…, Horizon Zero Dawn - Pl…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #3 — 命中@2 · RERANK伤害
- **历史**(6项; 平台 PS4×6): Watch Dogs 2 - PlayStation… | Ratchet & Clank - PlayStat… | Horizon Zero Dawn - PlaySt… | CorpCo 6ft AC Power Cord f… | Deadpool - PlayStation 4 | DualShock 4 Wireless Contr…
- **GT**: `<a_201><b_31><c_107>` Uncharted 4: A Thief's End - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_201><b_31><c_107>` Uncharted 4: A Thief's End - P… ✓
- **beam top5**: `<a_61><b_251><c_144>`PS4, `<a_201><b_31><c_107>`PS4, `<a_201><b_213><c_242>`PS4, `<a_123><b_58><c_78>`PS4, `<a_201><b_151><c_255>`PS
- **推荐↔GT差距**: 正确项在 beam 第2位，pred[0] 前缀深度仅 0/3；平台一致(PS4)；beam中 share-a=4/10, share-(a,b)=1/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/6（覆盖67%），锚定: Watch Dogs 2 - PlaySta…, Horizon Zero Dawn - Pl…, CorpCo 6ft AC Power Co…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=子类延续(score3)。target 是合理的漂移(平台/词面关联)，且**已命中**。

### #4 — 类目对·item错
- **历史**(7项; 平台 PS4×7): Ratchet & Clank - PlayStat… | Horizon Zero Dawn - PlaySt… | CorpCo 6ft AC Power Cord f… | Deadpool - PlayStation 4 | DualShock 4 Wireless Contr… | Uncharted 4: A Thief's End…
- **GT**: `<a_189><b_243><c_254>` Limited Edition Vertical Stand for Glacier Whi… _(平台 PS4)_ ｜ **native**: `<a_201><b_213><c_242>` The Last of Us Remastered - Pl… ✗
- **beam top5**: `<a_123><b_58><c_78>`PS4, `<a_24><b_86><c_14>`PS4, `<a_201><b_18><c_56>`PS4, `<a_201><b_56><c_74>`PS4, `<a_201><b_213><c_242>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=10/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 6/7（覆盖86%），锚定: Watch Dogs 2 - PlaySta…, Horizon Zero Dawn - Pl…, CorpCo 6ft AC Power Co…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。

### #5 — 类目错·(a)大类都不对 · BEAM坍缩(<a_61×9/10)
- **历史**(1项; 平台 Xbox360×1): JINHEZO Sensor TV Mount Cl…
- **GT**: `<a_118><b_162><c_110>` Batman: Arkham Origins - Playstation 3 _(平台 PS3)_ ｜ **native**: `<a_61><b_181><c_195>` Xbox 360 Wireless Controller -… ✗
- **beam top5**: `<a_61><b_181><c_195>`Xbo, `<a_61><b_137><c_255>`Xbo, `<a_189><b_45><c_10>`Xbo, `<a_61><b_56><c_2>`Xbo, `<a_61><b_181><c_175>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS3 vs 荐=Xbox360)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_61 家族 9/10）；unique(a,b)=6/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 1/1（覆盖100%），锚定: JINHEZO Sensor TV Moun…；新候选=0（**纯复述历史**）；genre: accessor。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=漂移(平台/词面关联)(score1)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #6 — 类目错·(a)大类都不对
- **历史**(2项; 平台 Xbox360×1,PS3×1): JINHEZO Sensor TV Mount Cl… | Batman: Arkham Origins - P…
- **GT**: `<a_49><b_218><c_81>` LEGO Marvel Super Heroes - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_61><b_181><c_195>` Xbox 360 Wireless Controller -… ✗
- **beam top5**: `<a_61><b_181><c_195>`Xbo, `<a_61><b_214><c_252>`Xbo, `<a_118><b_41><c_55>`?, `<a_118><b_1><c_224>`Xbo, `<a_118><b_162><c_110>`PS3
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS4 vs 荐=Xbox360)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=10/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: JINHEZO Sensor TV Moun…, Batman: Arkham Origins…；新候选=0（**纯复述历史**）；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=漂移(平台/词面关联)(score1)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #7 — 类目对·item错
- **历史**(3项; 平台 Xbox360×1,PS3×1,PS4×1): JINHEZO Sensor TV Mount Cl… | Batman: Arkham Origins - P… | LEGO Marvel Super Heroes -…
- **GT**: `<a_49><b_236><c_171>` LEGO Marvel's Avengers - Xbox 360 _(平台 Xbox360)_ ｜ **native**: `<a_201><b_213><c_242>` The Last of Us Remastered - Pl… ✗
- **beam top5**: `<a_123><b_72><c_7>`PS4, `<a_201><b_31><c_107>`PS4, `<a_245><b_185><c_59>`PS4, `<a_201><b_213><c_242>`PS4, `<a_49><b_47><c_60>`PSV
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台错配(GT=Xbox360 vs 荐=PS4)；beam中 share-a=1/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=10/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Batman: Arkham Origins…, LEGO Marvel Super Hero…, JINHEZO Sensor TV Moun…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=漂移(平台/词面关联)(score1)。用户点击比我们top1**更贴历史**(target2>荐1) → 我们把可命中的延续**跑偏**了。 注意 target 与历史共享词 ['lego']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #8 — 类目对·item错
- **历史**(4项; 平台 Xbox360×2,PS3×1,PS4×1): JINHEZO Sensor TV Mount Cl… | Batman: Arkham Origins - P… | LEGO Marvel Super Heroes -… | LEGO Marvel's Avengers - X…
- **GT**: `<a_131><b_210><c_0>` Fallout 4 - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_49><b_47><c_60>` LEGO Marvel Super Heroes - PS … ✗
- **beam top5**: `<a_123><b_72><c_7>`PS4, `<a_49><b_47><c_60>`PSV, `<a_123><b_72><c_191>`Xbo, `<a_245><b_185><c_59>`PS4, `<a_217><b_121><c_56>`PSV
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=9/10，平台数=5，unique标题=10/10。
- **reasoning质量**: 引用历史 3/4（覆盖75%），锚定: LEGO Marvel Super Hero…, LEGO Marvel's Avengers…, Batman: Arkham Origins…；新候选=0（**纯复述历史**）；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。

### #9 — 类目对·item错
- **历史**(5项; 平台 Xbox360×2,PS4×2,PS3×1): JINHEZO Sensor TV Mount Cl… | Batman: Arkham Origins - P… | LEGO Marvel Super Heroes -… | LEGO Marvel's Avengers - X… | Fallout 4 - PlayStation 4
- **GT**: `<a_74><b_218><c_206>` Ratchet & Clank - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_118><b_185><c_102>` Batman: Arkham Knight - PlaySt… ✗
- **beam top5**: `<a_123><b_72><c_7>`PS4, `<a_118><b_185><c_102>`PS4, `<a_201><b_31><c_107>`PS4, `<a_201><b_145><c_9>`PS4, `<a_118><b_95><c_6>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=10/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/5（覆盖80%），锚定: Batman: Arkham Origins…, Fallout 4 - PlayStatio…, LEGO Marvel Super Hero…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。

### #10 — 类目对·item错
- **历史**(6项; 平台 PS4×3,Xbox360×2,PS3×1): JINHEZO Sensor TV Mount Cl… | Batman: Arkham Origins - P… | LEGO Marvel Super Heroes -… | LEGO Marvel's Avengers - X… | Fallout 4 - PlayStation 4 | Ratchet & Clank - PlayStat…
- **GT**: `<a_13><b_1><c_233>` Plants vs. Zombies Garden Warfare 2 - PlayStat… _(平台 PS4)_ ｜ **native**: `<a_118><b_185><c_102>` Batman: Arkham Knight - PlaySt… ✗
- **beam top5**: `<a_123><b_72><c_7>`PS4, `<a_141><b_73><c_216>`PS4, `<a_118><b_185><c_102>`PS4, `<a_141><b_73><c_7>`PS4, `<a_201><b_31><c_107>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/6（覆盖67%），锚定: Batman: Arkham Origins…, Fallout 4 - PlayStatio…, LEGO Marvel Super Hero…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。

### #11 — 类目对·item错
- **历史**(7项; 平台 PS4×4,Xbox360×2,PS3×1): Batman: Arkham Origins - P… | LEGO Marvel Super Heroes -… | LEGO Marvel's Avengers - X… | Fallout 4 - PlayStation 4 | Ratchet & Clank - PlayStat… | Plants vs. Zombies Garden …
- **GT**: `<a_24><b_72><c_142>` Horizon Zero Dawn - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_123><b_72><c_7>` Far Cry 4 - PlayStation 4 ✗
- **beam top5**: `<a_123><b_72><c_7>`PS4, `<a_74><b_128><c_20>`PS4, `<a_201><b_31><c_107>`PS4, `<a_141><b_73><c_216>`PS4, `<a_141><b_73><c_7>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（7 个不同 a 大类）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 5/7（覆盖71%），锚定: Batman: Arkham Origins…, Fallout 4 - PlayStatio…, LEGO Marvel Super Hero…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。

### #12 — 类目错·(a)大类都不对
- **历史**(8项; 平台 PS4×5,Xbox360×2,PS3×1): LEGO Marvel Super Heroes -… | LEGO Marvel's Avengers - X… | Fallout 4 - PlayStation 4 | Ratchet & Clank - PlayStat… | Plants vs. Zombies Garden … | Horizon Zero Dawn - PlaySt…
- **GT**: `<a_217><b_148><c_123>` The Amazing Spider-Man 2 - Xbox 360 _(平台 Xbox360)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_123><b_100><c_33>`PS4, `<a_201><b_18><c_56>`PS4, `<a_24><b_86><c_14>`PS4, `<a_123><b_58><c_78>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=Xbox360 vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=10/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 5/8（覆盖62%），锚定: Batman: Arkham Origins…, Fallout 4 - PlayStatio…, LEGO Marvel Super Hero…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。

### #13 — 类目错·(a)大类都不对 · BEAM坍缩(<a_123×7/10)
- **历史**(9项; 平台 PS4×5,Xbox360×3,PS3×1): LEGO Marvel's Avengers - X… | Fallout 4 - PlayStation 4 | Ratchet & Clank - PlayStat… | Plants vs. Zombies Garden … | Horizon Zero Dawn - PlaySt… | The Amazing Spider-Man 2 -…
- **GT**: `<a_217><b_176><c_0>` Teenage Mutant Ninja Turtles: Mutants in Manha… _(平台 Xbox360)_ ｜ **native**: `<a_123><b_100><c_33>` Tom Clancy&rsquo;s Ghost Recon… ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_123><b_100><c_33>`PS4, `<a_123><b_76><c_232>`PS4, `<a_123><b_100><c_0>`Xbo, `<a_123><b_58><c_78>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=Xbox360 vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_123 家族 7/10）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/9（覆盖44%），锚定: Batman: Arkham Origins…, Fallout 4 - PlayStatio…, LEGO Marvel Super Hero…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=漂移(平台/词面关联)(score1)。用户点击比我们top1**更贴历史**(target2>荐1) → 我们把可命中的延续**跑偏**了。

### #14 — 类目错·(a)大类都不对 · BEAM坍缩(<a_123×7/10)
- **历史**(6项; 平台 Xbox360×4,?×2): Guitar Hero 2 - Xbox 360 | Thief - Xbox 360 | The Amazing Spider-Man | Watch Dogs - Xbox 360 | Minecraft | Far Cry 4 - Xbox 360
- **GT**: `<a_39><b_51><c_188>` Titanfall 2 - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_123><b_72><c_191>` Far Cry 4 - Xbox One ✗
- **beam top5**: `<a_123><b_72><c_191>`Xbo, `<a_123><b_102><c_217>`Xbo, `<a_123><b_72><c_33>`PC, `<a_123><b_233><c_44>`?, `<a_123><b_246><c_254>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS4 vs 荐=XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_123 家族 7/10）；unique(a,b)=7/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 5/6（覆盖83%），锚定: Guitar Hero 2 - Xbox 3…, Thief - Xbox 360, Far Cry 4 - Xbox 360；新候选=0（**纯复述历史**）；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=子类延续(score3)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #15 — 命中@6
- **历史**(1项; 平台 PS4×1): PlayStation 4 Camera (Old …
- **GT**: `<a_61><b_251><c_51>` DualShock 4 Wireless Controller for PlayStatio… _(平台 PS4)_ ｜ **native**: `<a_201><b_213><c_242>` The Last of Us Remastered - Pl… ✗
- **beam top5**: `<a_231><b_28><c_63>`PS4, `<a_201><b_31><c_107>`PS4, `<a_201><b_213><c_242>`PS4, `<a_8><b_4><c_188>`PS4, `<a_39><b_182><c_247>`PS4
- **推荐↔GT差距**: 正确项在 beam 第6位，pred[0] 前缀深度仅 0/3；平台一致(PS4)；beam中 share-a=1/10, share-(a,b)=1/10。
- **beam多样性**: **高**（6 个不同 a 大类）；unique(a,b)=10/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 0/1（覆盖0%）；新候选=0（**纯复述历史**）；genre: peripheral,accessor。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。target 是合理的漂移(平台/词面关联)，且**已命中**。

### #16 — 类目对·item错
- **历史**(2项; 平台 PS4×2): PlayStation 4 Camera (Old … | DualShock 4 Wireless Contr…
- **GT**: `<a_140><b_50><c_3>` Call of Duty: Ghosts - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_201><b_213><c_242>` The Last of Us Remastered - Pl… ✗
- **beam top5**: `<a_231><b_28><c_63>`PS4, `<a_201><b_2><c_102>`PS4, `<a_201><b_201><c_84>`PS4, `<a_201><b_213><c_242>`PS4, `<a_201><b_36><c_181>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（6 个不同 a 大类）；unique(a,b)=10/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 0/2（覆盖0%）；新候选=0（**纯复述历史**）；genre: action,immersive,accessor。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。

### #17 — 类目错·(a)大类都不对
- **历史**(3项; 平台 PS4×3): PlayStation 4 Camera (Old … | DualShock 4 Wireless Contr… | Call of Duty: Ghosts - Pla…
- **GT**: `<a_21><b_19><c_204>` Nyko Net Connect for Wii _(平台 Wii)_ ｜ **native**: `<a_201><b_213><c_242>` The Last of Us Remastered - Pl… ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_201><b_36><c_195>`PS4, `<a_39><b_204><c_65>`PS4, `<a_201><b_213><c_242>`PS4, `<a_201><b_2><c_102>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=Wii vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=10/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 0/3（覆盖0%）；新候选=0（**纯复述历史**）；模板开头；genre: action,shooter,immersive。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=漂移(平台/词面关联)(score1)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #18 — 类目对·item错
- **历史**(4项; 平台 PS4×3,Wii×1): PlayStation 4 Camera (Old … | DualShock 4 Wireless Contr… | Call of Duty: Ghosts - Pla… | Nyko Net Connect for Wii
- **GT**: `<a_140><b_164><c_230>` PlayStation 4 Battlefield 4 Launch Day Bundle _(平台 PS4)_ ｜ **native**: `<a_21><b_19><c_204>` Nyko Net Connect for Wii ✗
- **beam top5**: `<a_61><b_47><c_32>`PS3, `<a_61><b_47><c_60>`PS, `<a_61><b_47><c_8>`PS3, `<a_21><b_19><c_204>`Wii, `<a_140><b_220><c_113>`PS
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台错配(GT=PS4 vs 荐=PS3)；beam中 share-a=4/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=6/10，平台数=6，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: PlayStation 4 Camera (…, DualShock 4 Wireless C…, Call of Duty: Ghosts -…；新候选=0（**纯复述历史**）；模板开头；genre: action,shooter,immersive。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。

### #19 — 类目对·item错 · BEAM坍缩(<a_61×8/10)
- **历史**(3项; 平台 WiiU×1,PSVita×1,PS×1): Super Smash Bros. - Ninten… | Corpse Party: Blood Drive … | USPRO&reg; PlayStation 2 W…
- **GT**: `<a_61><b_248><c_151>` Steam Controller _(平台 ?)_ ｜ **native**: `<a_61><b_247><c_90>` USPRO&reg; PlayStation 2 Wired… ✗
- **beam top5**: `<a_61><b_44><c_172>`PS4, `<a_61><b_247><c_172>`PS4, `<a_113><b_35><c_14>`Gam, `<a_61><b_35><c_122>`PS, `<a_61><b_228><c_90>`?
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；beam中 share-a=8/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_61 家族 8/10）；unique(a,b)=8/10，平台数=6，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Super Smash Bros. - Ni…, Corpse Party: Blood Dr…, USPRO&reg; PlayStation…；新候选=0（**纯复述历史**）；模板开头；genre: action,horror,multiplayer。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。 注意 target 与历史共享词 ['controller']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #20 — 类目对·item错
- **历史**(4项; 平台 XboxOne×3,?×1): Wolfenstein: The New Order | Grand Theft Auto V - Xbox … | Doom - Xbox One | Naruto Shippuden: Ultimate…
- **GT**: `<a_86><b_105><c_118>` South Park: The Fractured but Whole - Xbox One _(平台 XboxOne)_ ｜ **native**: `<a_131><b_155><c_206>` Fallout 4 - Xbox One ✗
- **beam top5**: `<a_131><b_155><c_206>`Xbo, `<a_39><b_69><c_69>`Xbo, `<a_39><b_77><c_69>`Xbo, `<a_131><b_55><c_86>`Xbo, `<a_39><b_77><c_105>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（2 个 a 大类）；unique(a,b)=9/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Wolfenstein: The New O…, Grand Theft Auto V - X…, Doom - Xbox One；新候选=0（**纯复述历史**）；模板开头；genre: action,shooter,fighting。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。

### #21 — 类目错·(a)大类都不对
- **历史**(3项; 平台 PS4×2,PSVita×1): Transformers Devastation -… | PlayStation 4 500GB Consol… | Sony PlayStation Vita WiFi
- **GT**: `<a_7><b_36><c_217>` Xbox One X 1TB Limited Edition Console - Proje… _(平台 XboxOne)_ ｜ **native**: `<a_201><b_213><c_242>` The Last of Us Remastered - Pl… ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_208><b_175><c_0>`PS4, `<a_131><b_210><c_0>`PS4, `<a_201><b_36><c_181>`PS4, `<a_201><b_213><c_242>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=XboxOne vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=10/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Transformers Devastati…, PlayStation 4 500GB Co…, Sony PlayStation Vita …；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['discontinued', 'limited']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #22 — 类目对·item错
- **历史**(4项; 平台 PS4×2,WiiU×1,3DS×1): Gravity Rush Remastered - … | Valkyria Chronicles Remast… | Tokyo Mirage Sessions #FE … | Nintendo - New 3DS XL Lege…
- **GT**: `<a_30><b_92><c_0>` Persona 5 - Standard Edition - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_1><b_150><c_189>` Legend of Heroes: Trails of Co… ✗
- **beam top5**: `<a_121><b_35><c_0>`PS4, `<a_1><b_25><c_254>`3DS, `<a_1><b_150><c_189>`PS3, `<a_1><b_177><c_184>`PS4, `<a_1><b_68><c_121>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（2 个 a 大类）；unique(a,b)=10/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Gravity Rush Remastere…, Valkyria Chronicles Re…, Tokyo Mirage Sessions …；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,strategy。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #23 — 类目错·(a)大类都不对
- **历史**(10项; 平台 ?×3,Wii×2,PS×2): Mercenaries: Playground of… | Donkey Kong Country Return… | PS3 500 GB Grand Theft Aut… | The Legend of Zelda: Twili… | Black - PlayStation 2 | Tomb Raider Game of the Ye…
- **GT**: `<a_240><b_157><c_13>` Manhunt - PlayStation 2 _(平台 PS2)_ ｜ **native**: `<a_239><b_39><c_242>` Kirby Nightmare in Dream Land ✗
- **beam top5**: `<a_71><b_66><c_11>`?, `<a_239><b_236><c_95>`Wii, `<a_24><b_156><c_78>`PS3, `<a_239><b_196><c_173>`?, `<a_175><b_83><c_0>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=9/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 6/10（覆盖60%），锚定: Kirby's Return to Drea…, Donkey Kong Country Re…, Ghostbusters: The Vide…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。

### #24 — 类目对·item错 · BEAM坍缩(<a_80×7/10)
- **历史**(7项; 平台 GameCube×3,PS4×2,?×2): Resident Evil 2 - Gamecube | The Evil Within - PlayStat… | Resident Evil 3: Nemesis | Resident Evil - Gamecube | Resident Evil 4 - PlayStat… | Resident Evil Code Veronic…
- **GT**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - PS4 Digital Code _(平台 PS4)_ ｜ **native**: `<a_80><b_59><c_0>` Resident Evil 2 ✗
- **beam top5**: `<a_80><b_59><c_248>`Xbo, `<a_80><b_59><c_0>`?, `<a_80><b_59><c_29>`PS3, `<a_80><b_59><c_159>`PS, `<a_123><b_67><c_103>`Gam
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台错配(GT=PS4 vs 荐=Xbox360)；beam中 share-a=3/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_80 家族 7/10）；unique(a,b)=3/10，平台数=5，unique标题=10/10。
- **reasoning质量**: 引用历史 4/7（覆盖57%），锚定: Resident Evil 4 - Game…, Resident Evil 2 - Game…, The Evil Within - Play…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=子类延续(score3)。我们推的比用户真实点击**更贴历史**(荐3>target2) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['code', 'evil', 'resident']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #25 — 类目错·(a)大类都不对 · BEAM坍缩(<a_21×10/10)
- **历史**(9项; 平台 ?×2,PS2×2,PS3×1): PS2 Controller Extension C… | PS2 Controller Extension C… | Retro Bit Universal 3 in 1… | 4x Wii/Gamecube Extension … | GBA SP Gameboy Game boy Ad… | Buffalo iBuffalo Classic U…
- **GT**: `<a_13><b_87><c_62>` Time Crisis: Razing Storm - Playstation 3 _(平台 PS3)_ ｜ **native**: `<a_21><b_44><c_75>` PS2 Controller Extension Cable… ✗
- **beam top5**: `<a_21><b_44><c_75>`PS2, `<a_21><b_138><c_81>`Gam, `<a_21><b_144><c_105>`?, `<a_21><b_18><c_85>`PS3, `<a_21><b_117><c_122>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS3 vs 荐=PS2)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_21 家族 10/10）；unique(a,b)=10/10，平台数=6，unique标题=10/10。
- **reasoning质量**: 引用历史 7/8（覆盖88%），锚定: Sega Saturn System - V…, PS3 Optical Digital Ca…, PS2 Controller Extensi…；新候选=0（**纯复述历史**）；模板开头；genre: action,nostalg,retro。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=子类延续(score3)。我们推的比用户真实点击**更贴历史**(荐3>target1) → **模型偏保守/用户更爱探索**。

### #26 — 类目错·(a)大类都不对 · BEAM坍缩(<a_113×7/10)
- **历史**(4项; 平台 ?×1,PS×1,DS×1): Street Fighter Anniversary… | Buyee 128MB Memory Card fo… | Nintendo 2DS - Electric Bl… | HORI Compact PlayStand - Z…
- **GT**: `<a_250><b_55><c_95>` Mario Kart 7 _(平台 ?)_ ｜ **native**: `<a_113><b_232><c_97>` Redesigned REPLACEMENT Joystic… ✗
- **beam top5**: `<a_113><b_232><c_97>`?, `<a_208><b_196><c_65>`PS, `<a_113><b_91><c_165>`?, `<a_61><b_228><c_90>`?, `<a_113><b_235><c_2>`3DS
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_113 家族 7/10）；unique(a,b)=8/10，平台数=5，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Street Fighter Anniver…, Buyee 128MB Memory Car…, Nintendo 2DS - Electri…；新候选=0（**纯复述历史**）；genre: action,fighting,nostalg。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #27 — 类目错·(a)大类都不对
- **历史**(5项; 平台 ?×2,PS×1,DS×1): Street Fighter Anniversary… | Buyee 128MB Memory Card fo… | Nintendo 2DS - Electric Bl… | HORI Compact PlayStand - Z… | Mario Kart 7
- **GT**: `<a_119><b_109><c_15>` Lilyy Protective Soft Silicone Rubber Gel Skin… _(平台 ?)_ ｜ **native**: `<a_113><b_232><c_97>` Redesigned REPLACEMENT Joystic… ✗
- **beam top5**: `<a_113><b_232><c_97>`?, `<a_250><b_21><c_158>`?, `<a_113><b_235><c_2>`3DS, `<a_113><b_35><c_14>`Gam, `<a_193><b_104><c_221>`PC
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=9/10，平台数=5，unique标题=10/10。
- **reasoning质量**: 引用历史 5/5（覆盖100%），锚定: Street Fighter Anniver…, Nintendo 2DS - Electri…, Mario Kart 7；新候选=0（**纯复述历史**）；模板开头；genre: action,fighting,racing。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['2ds']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #28 — 类目对·item错 · BEAM坍缩(<a_113×9/10)
- **历史**(6项; 平台 ?×2,DS×2,PS×1): Street Fighter Anniversary… | Buyee 128MB Memory Card fo… | Nintendo 2DS - Electric Bl… | HORI Compact PlayStand - Z… | Mario Kart 7 | Lilyy Protective Soft Sili…
- **GT**: `<a_119><b_178><c_139>` Mudder Protective Travel Carrying Case Cover f… _(平台 ?)_ ｜ **native**: `<a_113><b_104><c_28>` Nintendo 3DS Compatible with 3… ✗
- **beam top5**: `<a_113><b_104><c_28>`3DS, `<a_113><b_232><c_97>`?, `<a_113><b_230><c_103>`3DS, `<a_113><b_174><c_101>`?, `<a_113><b_235><c_2>`3DS
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；beam中 share-a=1/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_113 家族 9/10）；unique(a,b)=9/10，平台数=6，unique标题=10/10。
- **reasoning质量**: 引用历史 4/6（覆盖67%），锚定: Street Fighter Anniver…, Mario Kart 7, Nintendo 2DS - Electri…；新候选=0（**纯复述历史**）；模板开头；genre: action,nostalg,retro。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。 注意 target 与历史共享词 ['2ds', 'case', 'cover', 'protective']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #29 — 类目错·(a)大类都不对
- **历史**(10项; 平台 PS4×7,XboxOne×2,PC×1): Mass Effect Andromeda - Pr… | Grand Theft Auto V - Xbox … | Horizon Zero Dawn - PlaySt… | Watch Dogs 2 - PlayStation… | Watch Dogs 2: Deluxe Editi… | Persona 5 - Standard Editi…
- **GT**: `<a_201><b_151><c_255>` Playstation Plus: 3 Month Membership [Digital … _(平台 PS-generic)_ ｜ **native**: `<a_30><b_92><c_146>` Persona 5 - SteelBook Edition … ✗
- **beam top5**: `<a_24><b_185><c_47>`Xbo, `<a_30><b_92><c_146>`PS4, `<a_24><b_38><c_11>`PS4, `<a_30><b_92><c_0>`PS4, `<a_191><b_76><c_188>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS-generic vs 荐=XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=9/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 6/10（覆盖60%），锚定: Dishonored 2 - PlaySta…, Horizon Zero Dawn - Pl…, The Witness - PS4 [Dig…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。 注意 target 与历史共享词 ['code', 'digital']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #30 — 类目错·(a)大类都不对
- **历史**(2项; 平台 PS×2): Shin Megami Tensei: Person… | Shin Megami Tensei: Person…
- **GT**: `<a_201><b_239><c_3>` Resident Evil Origins Collection - PlayStation… _(平台 PS4)_ ｜ **native**: `<a_30><b_104><c_169>` Shin Megami Tensei: Persona 3 … ✗
- **beam top5**: `<a_30><b_104><c_169>`PS, `<a_195><b_171><c_31>`PSP, `<a_30><b_128><c_164>`PS3, `<a_216><b_92><c_163>`3DS, `<a_30><b_106><c_179>`PSV
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS4 vs 荐=PS2)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=9/10，平台数=6，unique标题=10/10。
- **reasoning质量**: 引用历史 1/1（覆盖100%），锚定: Shin Megami Tensei: Pe…；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,immersive。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=子类延续(score3)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #31 — 类目错·(a)大类都不对 · BEAM坍缩(<a_113×9/10)
- **历史**(5项; 平台 Wii×2,?×1,PC×1): Mayflash W010 Wireless Sen… | Logitech G27 Racing Wheel | Buffalo iBuffalo Classic U… | New Super Mario Bros. Wii | Super Mario Maker - Ninten…
- **GT**: `<a_202><b_115><c_229>` AULA LED Backlit Gaming Keyboard (3 Colorways) _(平台 ?)_ ｜ **native**: `<a_113><b_35><c_14>` Nintendo Super Smash Bros. Bla… ✗
- **beam top5**: `<a_113><b_9><c_63>`Wii, `<a_113><b_147><c_140>`Wii, `<a_113><b_104><c_28>`3DS, `<a_113><b_240><c_225>`Wii, `<a_113><b_35><c_14>`Gam
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_113 家族 9/10）；unique(a,b)=8/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 5/5（覆盖100%），锚定: Mayflash W010 Wireless…, Buffalo iBuffalo Class…, New Super Mario Bros. …；新候选=0（**纯复述历史**）；genre: platformer,multiplayer,nostalg。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=漂移(平台/词面关联)(score1)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #32 — 类目错·(a)大类都不对 · BEAM坍缩(<a_216×10/10)
- **历史**(10项; 平台 3DS×4,?×3,PSVita×2): Theatrhythm Final Fantasy:… | Nintendo NFC Reader/Writer… | Animal Crossing Card amiib… | Mario & Sonic at the Londo… | Tearaway | The Legend of Zelda: Major…
- **GT**: `<a_10><b_86><c_68>` The Elder Scrolls V: Skyrim Legendary Edition … _(平台 ?)_ ｜ **native**: `<a_216><b_51><c_130>` Xenoblade Chronicles 3D - New … ✗
- **beam top5**: `<a_216><b_93><c_101>`DS, `<a_216><b_112><c_114>`Wii, `<a_216><b_219><c_158>`3DS, `<a_216><b_51><c_130>`3DS, `<a_216><b_122><c_148>`3DS
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_216 家族 10/10）；unique(a,b)=9/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 8/10（覆盖80%），锚定: DanganRonpa: Trigger H…, The Legend of Zelda: M…, Bejeweled 3 - Nintendo…；新候选=0（**纯复述历史**）；模板开头；genre: action,adventure,puzzle。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #33 — 类目对·item错 · BEAM坍缩(<a_205×10/10)
- **历史**(3项; 平台 Xbox360×2,XboxOne×1): Forza Horizon - Xbox 360 | Forza Horizon 3 - Xbox One | Forza Motorsport 4 - Xbox …
- **GT**: `<a_245><b_155><c_254>` Middle Earth: Shadow of Mordor - Xbox One _(平台 XboxOne)_ ｜ **native**: `<a_205><b_136><c_51>` Forza Horizon 2 for Xbox One ✗
- **beam top5**: `<a_205><b_136><c_51>`Xbo, `<a_205><b_40><c_3>`?, `<a_205><b_40><c_83>`?, `<a_205><b_136><c_234>`Xbo, `<a_205><b_60><c_111>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_205 家族 10/10）；unique(a,b)=7/10，平台数=4，unique标题=9/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Forza Horizon - Xbox 3…, Forza Horizon 3 - Xbox…, Forza Motorsport 4 - X…；新候选=0（**纯复述历史**）；模板开头；genre: action,racing,multiplayer。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #34 — 类目错·(a)大类都不对
- **历史**(5项; 平台 DS×1,PC×1,?×1): SteelSeries Flux Gaming He… | Dark Souls II: Collector's… | Halo 5: Guardians | Fallout 4: Contraptions Wo… | HORI Compact PlayStand - Z…
- **GT**: `<a_89><b_221><c_81>` $20 Battle.net Store Gift Card Balance - Blizz… _(平台 ?)_ ｜ **native**: `<a_131><b_137><c_58>` Fallout 4: Contraptions Worksh… ✗
- **beam top5**: `<a_61><b_44><c_172>`PS4, `<a_61><b_131><c_197>`Xbo, `<a_7><b_248><c_16>`Xbo, `<a_131><b_155><c_206>`Xbo, `<a_7><b_248><c_2>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=9/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 5/5（覆盖100%），锚定: Dark Souls II: Collect…, Fallout 4: Contraption…, HORI Compact PlayStand…；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,immersive。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=探索(无关联)(score0)。用户点击比我们top1**更贴历史**(target1>荐0) → 我们把可命中的延续**跑偏**了。 注意 target 与历史共享词 ['code', 'digital']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #35 — 类目对·item错 · BEAM坍缩(<a_39×8/10)
- **历史**(7项; 平台 XboxOne×3,?×2,Xbox360×2): Call of Duty: Black Ops II… | Titanfall - Xbox One | R.C. Pro-Am | Borderlands Triple Pack - … | Destiny: The Taken King - … | Forza Motorsport 6 - Xbox …
- **GT**: `<a_123><b_33><c_95>` Resident Evil 5 - Standard Edition - Xbox One _(平台 XboxOne)_ ｜ **native**: `<a_39><b_151><c_9>` Halo 5: Guardians ✗
- **beam top5**: `<a_39><b_114><c_237>`Xbo, `<a_39><b_77><c_69>`Xbo, `<a_39><b_114><c_209>`Xbo, `<a_39><b_77><c_105>`Xbo, `<a_39><b_151><c_9>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_39 家族 8/10）；unique(a,b)=8/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 6/7（覆盖86%），锚定: Call of Duty: Black Op…, Titanfall - Xbox One, R.C. Pro-Am；新候选=0（**纯复述历史**）；模板开头；genre: action,shooter,racing。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #36 — 类目错·(a)大类都不对
- **历史**(3项; 平台 PS4×2,PS3×1): Sony Computer Entertainmen… | Tom Clancy's The Division … | Mega Man Legacy Collection…
- **GT**: `<a_249><b_180><c_74>` PlayStation Vita Memory Card 64GB (PCH-Z641J) _(平台 PSVita)_ ｜ **native**: `<a_201><b_31><c_107>` Uncharted 4: A Thief's End - P… ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_131><b_210><c_0>`PS4, `<a_201><b_2><c_102>`PS4, `<a_131><b_209><c_151>`PS4, `<a_201><b_213><c_242>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PSVita vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（6 个不同 a 大类）；unique(a,b)=10/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Tom Clancy's The Divis…, Mega Man Legacy Collec…, Sony Computer Entertai…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=漂移(平台/词面关联)(score1)。用户点击比我们top1**更贴历史**(target2>荐1) → 我们把可命中的延续**跑偏**了。

### #37 — 类目对·item错
- **历史**(1项; 平台 PS4×1): Star Wars: Battlefront - S…
- **GT**: `<a_45><b_226><c_3>` NHL 17 - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_131><b_210><c_0>` Fallout 4 - PlayStation 4 ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_131><b_210><c_0>`PS4, `<a_201><b_36><c_195>`PS4, `<a_141><b_73><c_7>`PS4, `<a_201><b_213><c_242>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=9/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 0/1（覆盖0%）；新候选=0（**纯复述历史**）；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。

### #38 — 类目对·item错
- **历史**(5项; 平台 PS4×3,?×2): Doom - PlayStation 4 | Rise of the Tomb Raider: 2… | Atari Flashback Classics: … | Atari Flashback Classics: … | Dragon Quest Builders - Pl…
- **GT**: `<a_205><b_208><c_148>` Gran Turismo Sport - Limited Edition - PlaySta… _(平台 PS4)_ ｜ **native**: `<a_1><b_43><c_207>` The Last Guardian - PlayStatio… ✗
- **beam top5**: `<a_123><b_58><c_78>`PS4, `<a_1><b_43><c_207>`PS4, `<a_1><b_173><c_4>`PS4, `<a_24><b_72><c_142>`PS4, `<a_131><b_209><c_151>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（7 个不同 a 大类）；unique(a,b)=10/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Doom - PlayStation 4, Rise of the Tomb Raide…, Atari Flashback Classi…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。

### #39 — 类目对·item错 · BEAM坍缩(<a_162×7/10)
- **历史**(6项; 平台 ?×3,3DS×2,WiiU×1): Yoshi amiibo (Super Smash … | PDP New Nintendo 3DS XL Cl… | Ganondorf amiibo - Japan I… | Wolf Link Amiibo Jp Model … | Kirby amiibo - Nintendo 3D… | Nintendo Diddy Kong amiibo…
- **GT**: `<a_162><b_134><c_221>` Donkey Kong amiibo - Japan Import (Super Smash… _(平台 ?)_ ｜ **native**: `<a_162><b_147><c_226>` Nintendo Diddy Kong amiibo (SM… ✗
- **beam top5**: `<a_162><b_12><c_210>`Wii, `<a_162><b_130><c_2>`Wii, `<a_162><b_130><c_1>`Wii, `<a_162><b_130><c_72>`Wii, `<a_162><b_130><c_51>`Wii
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；beam中 share-a=7/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_162 家族 7/10）；unique(a,b)=7/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 0/6（覆盖0%）；新候选=0（**纯复述历史**）；模板开头；genre: action,accessor。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。 注意 target 与历史共享词 ['amiibo', 'bros', 'import', 'japan', 'kong']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #40 — 类目对·item错 · BEAM坍缩(<a_162×10/10)
- **历史**(7项; 平台 ?×4,3DS×2,WiiU×1): PDP New Nintendo 3DS XL Cl… | Ganondorf amiibo - Japan I… | Wolf Link Amiibo Jp Model … | Kirby amiibo - Nintendo 3D… | Nintendo Diddy Kong amiibo… | Donkey Kong amiibo - Japan…
- **GT**: `<a_162><b_45><c_208>` Bowser Jr. amiibo - Japan Import (Super Smash … _(平台 ?)_ ｜ **native**: `<a_162><b_130><c_72>` Nintendo Boo amiibo (SM Series… ✗
- **beam top5**: `<a_162><b_130><c_1>`Wii, `<a_162><b_130><c_2>`Wii, `<a_162><b_130><c_72>`Wii, `<a_162><b_12><c_210>`Wii, `<a_162><b_97><c_155>`?
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；beam中 share-a=10/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_162 家族 10/10）；unique(a,b)=7/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 2/7（覆盖29%），锚定: Donkey Kong amiibo - J…, Kirby amiibo - Nintend…；新候选=0（**纯复述历史**）；模板开头；genre: action。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。 注意 target 与历史共享词 ['amiibo', 'bros', 'import', 'japan', 'series']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #41 — 类目错·(a)大类都不对 · BEAM坍缩(<a_175×9/10)
- **历史**(6项; 平台 PS3×2,PS4×1,WiiU×1): Final Fantasy XIII - Plays… | Doom - PlayStation 4 | Street Fighter X Tekken - … | Yoshi's Woolly World -  Wi… | Wii | Nintendo Selects: Donkey K…
- **GT**: `<a_191><b_204><c_225>` Just Cause 3 - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_175><b_24><c_4>` New Super Mario Bros. Wii ✗
- **beam top5**: `<a_175><b_24><c_4>`Wii, `<a_175><b_24><c_11>`?, `<a_175><b_24><c_254>`?, `<a_175><b_113><c_76>`?, `<a_175><b_73><c_7>`PS3
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS4 vs 荐=Wii)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_175 家族 9/10）；unique(a,b)=5/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 4/6（覆盖67%），锚定: Final Fantasy XIII - P…, Doom - PlayStation 4, Nintendo Selects: Donk…；新候选=0（**纯复述历史**）；模板开头；genre: action,fighting,multiplayer。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。

### #42 — 类目错·(a)大类都不对 · BEAM坍缩(<a_250×10/10)
- **历史**(8项; 平台 Xbox360×3,WiiU×2,Wii×1): Nintendo 3DS Midnight Purp… | SpongeBob SquarePants: Pla… | Guitar Hero III: Legends o… | Yoshi's Woolly World -  Wi… | Yoshi's Story | Donkey Kong Country Tropic…
- **GT**: `<a_84><b_92><c_101>` Carnival Games - Nintendo Wii _(平台 Wii)_ ｜ **native**: `<a_250><b_57><c_233>` Super Mario 3D World - Nintend… ✗
- **beam top5**: `<a_250><b_57><c_233>`Wii, `<a_250><b_116><c_22>`Wii, `<a_250><b_219><c_103>`?, `<a_250><b_92><c_0>`?, `<a_250><b_112><c_111>`Wii
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=Wii vs 荐=WiiU)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_250 家族 10/10）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/8（覆盖50%），锚定: Yoshi's Woolly World -…, Donkey Kong Country Tr…, Nintendo 3DS Midnight …；新候选=0（**纯复述历史**）；模板开头；genre: action,adventure,narrative。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。

### #43 — 类目错·(a)大类都不对
- **历史**(9项; 平台 Xbox360×3,Wii×2,WiiU×2): SpongeBob SquarePants: Pla… | Guitar Hero III: Legends o… | Yoshi's Woolly World -  Wi… | Yoshi's Story | Donkey Kong Country Tropic… | Carnival Games - Nintendo …
- **GT**: `<a_80><b_216><c_246>` Sonic Ultimate Genesis Collection - Xbox 360 _(平台 Xbox360)_ ｜ **native**: `<a_84><b_222><c_22>` Mario Kart 8 - Nintendo Wii U ✗
- **beam top5**: `<a_84><b_222><c_135>`Wii, `<a_84><b_222><c_22>`Wii, `<a_84><b_109><c_95>`Wii, `<a_250><b_92><c_0>`?, `<a_84><b_222><c_164>`Wii
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=Xbox360 vs 荐=Wii)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（2 个 a 大类）；unique(a,b)=8/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 5/9（覆盖56%），锚定: Wii, Yoshi's Woolly World -…, Donkey Kong Country Tr…；新候选=0（**纯复述历史**）；模板开头；genre: action,adventure,multiplayer。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #44 — 类目错·(a)大类都不对
- **历史**(10项; 平台 Xbox360×4,Wii×2,WiiU×2): Guitar Hero III: Legends o… | Yoshi's Woolly World -  Wi… | Yoshi's Story | Donkey Kong Country Tropic… | Carnival Games - Nintendo … | Sonic Ultimate Genesis Col…
- **GT**: `<a_235><b_30><c_137>` Scooby Doo First Frights - Nintendo Wii _(平台 Wii)_ ｜ **native**: `<a_250><b_57><c_233>` Super Mario 3D World - Nintend… ✗
- **beam top5**: `<a_84><b_222><c_22>`Wii, `<a_250><b_57><c_233>`Wii, `<a_84><b_222><c_135>`Wii, `<a_250><b_92><c_0>`?, `<a_84><b_222><c_164>`Wii
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=Wii vs 荐=WiiU)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（2 个 a 大类）；unique(a,b)=7/10，平台数=3，unique标题=9/10。
- **reasoning质量**: 引用历史 5/10（覆盖50%），锚定: Wii, Yoshi's Woolly World -…, Donkey Kong Country Tr…；新候选=0（**纯复述历史**）；模板开头；genre: action,adventure,multiplayer。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #45 — 类目错·(a)大类都不对 · BEAM坍缩(<a_250×9/10)
- **历史**(10项; 平台 Xbox360×4,WiiU×2,Wii×2): Yoshi's Woolly World -  Wi… | Yoshi's Story | Donkey Kong Country Tropic… | Carnival Games - Nintendo … | Sonic Ultimate Genesis Col… | Scooby Doo First Frights -…
- **GT**: `<a_193><b_185><c_114>` Sonic Gems Collection - Gamecube _(平台 GameCube)_ ｜ **native**: `<a_250><b_57><c_233>` Super Mario 3D World - Nintend… ✗
- **beam top5**: `<a_250><b_219><c_103>`?, `<a_250><b_57><c_233>`Wii, `<a_250><b_238><c_106>`DS, `<a_250><b_92><c_0>`?, `<a_250><b_120><c_101>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_250 家族 9/10）；unique(a,b)=10/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 5/10（覆盖50%），锚定: Yoshi's Woolly World -…, Donkey Kong Country Tr…, SpongeBob SquarePants:…；新候选=0（**纯复述历史**）；模板开头；genre: adventure,racing,puzzle。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['collection', 'sonic']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #46 — 类目错·(a)大类都不对
- **历史**(3项; 平台 ?×2,Xbox360×1): Halo 3 - Xbox 360 | Call of Duty 4: Modern War… | Call of Duty 4: Modern War…
- **GT**: `<a_206><b_156><c_152>` Fortune Street _(平台 ?)_ ｜ **native**: `<a_39><b_40><c_248>` Call of Duty: Modern Warfare 3… ✗
- **beam top5**: `<a_39><b_40><c_248>`Xbo, `<a_140><b_161><c_25>`Xbo, `<a_140><b_176><c_37>`Xbo, `<a_140><b_242><c_55>`?, `<a_140><b_212><c_79>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（2 个 a 大类）；unique(a,b)=8/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: Halo 3 - Xbox 360, Call of Duty 4: Modern…；新候选=0（**纯复述历史**）；genre: action,shooter,multiplayer。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #47 — 类目对·item错
- **历史**(7项; 平台 PS3×3,XboxOne×3,Xbox360×1): Assassin's Creed IV Black … | Assassin's Creed Rogue- Pl… | Battlefield Bad Company 2 … | Assassin's Creed Unity - X… | Far Cry Primal - Xbox One … | Watch Dogs xbox one
- **GT**: `<a_194><b_15><c_156>` Dishonored 2 - Xbox One _(平台 XboxOne)_ ｜ **native**: `<a_123><b_72><c_191>` Far Cry 4 - Xbox One ✗
- **beam top5**: `<a_123><b_72><c_191>`Xbo, `<a_123><b_102><c_102>`Xbo, `<a_118><b_95><c_10>`Xbo, `<a_118><b_95><c_2>`Xbo, `<a_39><b_69><c_69>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=5/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 6/7（覆盖86%），锚定: Assassin's Creed - Pla…, Assassin's Creed IV Bl…, Assassin's Creed Rogue…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #48 — 类目错·(a)大类都不对
- **历史**(4项; 平台 PS×2,PS2×1,PC×1): PlayStation 2 Console Slim… | Mortal Kombat: Shaolin Mon… | Buyee 128MB Memory Card fo… | WWE SmackDown! Here Comes …
- **GT**: `<a_231><b_57><c_52>` WWE Smackdown! Shut Your Mouth _(平台 ?)_ ｜ **native**: `<a_249><b_170><c_61>` Buyee 128MB Memory Card for So… ✗
- **beam top5**: `<a_249><b_138><c_30>`PS, `<a_249><b_138><c_211>`PS, `<a_80><b_73><c_171>`Xbo, `<a_80><b_241><c_223>`Xbo, `<a_175><b_27><c_27>`PS
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=8/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 3/4（覆盖75%），锚定: Mortal Kombat: Shaolin…, WWE SmackDown! Here Co…, Buyee 128MB Memory Car…；新候选=0（**纯复述历史**）；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。 注意 target 与历史共享词 ['smackdown', 'wwe']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #49 — 类目错·(a)大类都不对 · BEAM坍缩(<a_162×10/10)
- **历史**(8项; 平台 WiiU×5,?×3): Super Smash Bros. - Ninten… | Hyrule Warriors - Nintendo… | Super Mario Maker - Ninten… | Captain Falcon amiibo - Ja… | Wario amiibo - Japan Impor… | Nintendo Mr. Game & Watch …
- **GT**: `<a_216><b_54><c_190>` The Legend of Zelda: Breath of the Wild - Wii … _(平台 WiiU)_ ｜ **native**: `<a_162><b_219><c_101>` Nintendo Super Smash Bros Palu… ✗
- **beam top5**: `<a_162><b_235><c_217>`?, `<a_162><b_57><c_111>`Wii, `<a_162><b_219><c_101>`?, `<a_162><b_219><c_233>`?, `<a_162><b_219><c_249>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_162 家族 10/10）；unique(a,b)=8/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 4/8（覆盖50%），锚定: Super Smash Bros. - Ni…, Super Mario Maker - Ni…, Captain Falcon amiibo …；新候选=0（**纯复述历史**）；模板开头；genre: action,competitive。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。

### #50 — 类目错·(a)大类都不对 · BEAM坍缩(<a_231×7/10)
- **历史**(9项; 平台 PS3×7,PS4×1,?×1): Minecraft - PlayStation 4 | NIKE Toddlers Tanjun (TDV)… | Call of Duty: Black Ops Co… | WWE 2K16 - PlayStation 3 | Call of Duty: Black Ops II… | Minecraft: Story Mode - Se…
- **GT**: `<a_189><b_154><c_99>` MIZAR 5 Empty Standard Playstation 3 Replaceme… _(平台 PS3)_ ｜ **native**: `<a_231><b_107><c_4>` WWE 2K15 - PlayStation 4 ✗
- **beam top5**: `<a_231><b_237><c_82>`PS4, `<a_201><b_2><c_102>`PS4, `<a_201><b_31><c_107>`PS4, `<a_231><b_107><c_4>`PS4, `<a_231><b_117><c_8>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS3 vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_231 家族 7/10）；unique(a,b)=6/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 5/8（覆盖62%），锚定: Resident Evil 5 - Play…, Mortal Kombat: Komplet…, Minecraft: Story Mode …；新候选=0（**纯复述历史**）；模板开头；genre: action,fighting,horror。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=子类延续(score3)。我们推的比用户真实点击**更贴历史**(荐3>target1) → **模型偏保守/用户更爱探索**。

### #51 — 类目错·(a)大类都不对 · BEAM坍缩(<a_202×10/10)
- **历史**(4项; 平台 PC×2,?×1,Switch×1): Buffalo iBuffalo Classic U… | Fallout: New Vegas Ultimat… | Logitech G910 Orion Spark … | G810 Orion Spectrum RGB Me…
- **GT**: `<a_113><b_205><c_51>` Retro Link GameCube Style USB Wired Controller _(平台 GameCube)_ ｜ **native**: `<a_202><b_33><c_133>` G810 Orion Spectrum RGB Mechan… ✗
- **beam top5**: `<a_202><b_58><c_105>`?, `<a_202><b_58><c_107>`?, `<a_202><b_82><c_172>`?, `<a_202><b_33><c_133>`Swi, `<a_202><b_34><c_39>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_202 家族 10/10）；unique(a,b)=7/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 3/4（覆盖75%），锚定: Buffalo iBuffalo Class…, Logitech G910 Orion Sp…, Fallout: New Vegas Ult…；新候选=0（**纯复述历史**）；模板开头；genre: action,immersive,narrative。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=子类延续(score3)。我们推的比用户真实点击**更贴历史**(荐3>target1) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['usb']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #52 — 类目对·item错
- **历史**(4项; 平台 PSVita×3,PS4×1): Resistance: Burning Skies … | LittleBigPlanet - PlayStat… | PlayStation All-Stars Batt… | Dishonored 2 - PlayStation…
- **GT**: `<a_39><b_51><c_188>` Titanfall 2 - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_191><b_10><c_232>` Watch Dogs 2 - PlayStation 4 ✗
- **beam top5**: `<a_191><b_10><c_232>`PS4, `<a_201><b_31><c_107>`PS4, `<a_123><b_58><c_78>`PS4, `<a_191><b_204><c_225>`PS4, `<a_201><b_213><c_242>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=10/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Resistance: Burning Sk…, PlayStation All-Stars …, LittleBigPlanet - Play…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。

### #53 — 类目错·(a)大类都不对 · BEAM坍缩(<a_80×8/10)
- **历史**(3项; 平台 DS×1,PS3×1,?×1): Castlevania Lords of Shado… | Far Cry 3 - Playstation 3 | Bloody Roar 4
- **GT**: `<a_200><b_24><c_219>` Devil May Cry PS3 _(平台 PS3)_ ｜ **native**: `<a_80><b_202><c_95>` Far Cry 3 - Playstation 3 ✗
- **beam top5**: `<a_80><b_202><c_49>`?, `<a_80><b_69><c_85>`PS4, `<a_80><b_48><c_186>`?, `<a_80><b_140><c_71>`PS3, `<a_80><b_202><c_95>`PS3
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_80 家族 8/10）；unique(a,b)=8/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Castlevania Lords of S…, Far Cry 3 - Playstatio…, Bloody Roar 4；新候选=0（**纯复述历史**）；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=子类延续(score3)。我们推的比用户真实点击**更贴历史**(荐3>target1) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['cry']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #54 — 类目错·(a)大类都不对 · BEAM坍缩(<a_250×7/10)
- **历史**(2项; 平台 WiiU×2): Super Mario Maker - Ninten… | Yoshi's Woolly World -  Wi…
- **GT**: `<a_211><b_88><c_34>` Pokemon Y _(平台 ?)_ ｜ **native**: `<a_250><b_116><c_22>` Yoshi's Woolly World Bundle  -… ✗
- **beam top5**: `<a_250><b_112><c_111>`Wii, `<a_250><b_116><c_22>`Wii, `<a_162><b_251><c_136>`Wii, `<a_250><b_172><c_5>`?, `<a_162><b_116><c_253>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_250 家族 7/10）；unique(a,b)=10/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: Super Mario Maker - Ni…, Yoshi's Woolly World -…；新候选=0（**纯复述历史**）；genre: action。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #55 — 类目错·(a)大类都不对
- **历史**(3项; 平台 WiiU×2,?×1): Super Mario Maker - Ninten… | Yoshi's Woolly World -  Wi… | Pokemon Y
- **GT**: `<a_111><b_130><c_0>` Just Dance 2017 - Wii U _(平台 WiiU)_ ｜ **native**: `<a_211><b_133><c_30>` Pokemon Alpha Sapphire - Ninte… ✗
- **beam top5**: `<a_211><b_133><c_123>`3DS, `<a_211><b_105><c_223>`3DS, `<a_211><b_105><c_215>`?, `<a_211><b_133><c_30>`3DS, `<a_211><b_159><c_123>`3DS
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=WiiU vs 荐=3DS)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=7/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Super Mario Maker - Ni…, Yoshi's Woolly World -…, Pokemon Y；新候选=0（**纯复述历史**）；模板开头；genre: action,adventure,platformer。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #56 — 类目对·item错
- **历史**(4项; 平台 WiiU×3,?×1): Super Mario Maker - Ninten… | Yoshi's Woolly World -  Wi… | Pokemon Y | Just Dance 2017 - Wii U
- **GT**: `<a_39><b_114><c_215>` Call of Duty: Ghosts - Nintendo Wii U _(平台 WiiU)_ ｜ **native**: `<a_211><b_133><c_30>` Pokemon Alpha Sapphire - Ninte… ✗
- **beam top5**: `<a_250><b_238><c_255>`Wii, `<a_211><b_159><c_123>`3DS, `<a_111><b_238><c_188>`PS4, `<a_211><b_149><c_18>`3DS, `<a_211><b_105><c_215>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(WiiU)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=9/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Super Mario Maker - Ni…, Yoshi's Woolly World -…, Pokemon Y；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,platformer。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #57 — 类目错·(a)大类都不对 · BEAM坍缩(<a_45×8/10)
- **历史**(4项; 平台 XboxOne×4): Terraria - Xbox One | Xbox One Special Edition D… | Forza Horizon 3 - Xbox One | Farming Simulator 17 - Xbo…
- **GT**: `<a_61><b_181><c_62>` Xbox 360 Wireless Controller - Gold Chrome _(平台 Xbox360)_ ｜ **native**: `<a_45><b_201><c_12>` Rocket League: Collector's Edi… ✗
- **beam top5**: `<a_45><b_168><c_1>`Xbo, `<a_45><b_201><c_12>`Xbo, `<a_205><b_10><c_3>`Xbo, `<a_45><b_207><c_3>`Xbo, `<a_45><b_168><c_109>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=Xbox360 vs 荐=XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_45 家族 8/10）；unique(a,b)=8/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Terraria - Xbox One, Forza Horizon 3 - Xbox…, Farming Simulator 17 -…；新候选=0（**纯复述历史**）；模板开头；genre: action,adventure,strategy。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。 注意 target 与历史共享词 ['controller', 'wireless']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #58 — 类目对·item错
- **历史**(10项; 平台 PS4×10): Until Dawn - PlayStation 4 | Until Dawn - PlayStation 4 | Abzu - PlayStation 4 | Tales from the Borderlands… | The Wolf Among Us - PlaySt… | Battlefield 1 - PlayStatio…
- **GT**: `<a_205><b_208><c_148>` Gran Turismo Sport - Limited Edition - PlaySta… _(平台 PS4)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_201><b_18><c_56>`PS4, `<a_123><b_58><c_78>`PS4, `<a_123><b_58><c_16>`Xbo, `<a_123><b_100><c_33>`PS4, `<a_201><b_213><c_242>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 6/9（覆盖67%），锚定: Life is Strange - Play…, Tales from the Borderl…, Until Dawn - PlayStati…；新候选=1；模板开头；genre: action,horror,immersive。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #59 — 类目错·(a)大类都不对
- **历史**(4项; 平台 3DS×4): Story of Seasons - Nintend… | Nintendo New 3DS Xl - Red … | Monster Hunter 4 Ultimate … | dreamGEAR Comfort GRIP Pro…
- **GT**: `<a_141><b_189><c_201>` PlanetSide 2 [Download] _(平台 ?)_ ｜ **native**: `<a_211><b_31><c_154>` Pokemon Super Mystery Dungeon … ✗
- **beam top5**: `<a_119><b_119><c_158>`3DS, `<a_119><b_35><c_129>`3DS, `<a_119><b_168><c_182>`3DS, `<a_211><b_31><c_154>`3DS, `<a_162><b_251><c_136>`Wii
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=10/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 3/4（覆盖75%），锚定: Story of Seasons - Nin…, Monster Hunter 4 Ultim…, dreamGEAR Comfort GRIP…；新候选=0（**纯复述历史**）；模板开头；genre: action,adventure,rpg。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #60 — 类目错·(a)大类都不对
- **历史**(6项; 平台 ?×6): The Legend of Zelda: Ocari… | Disney's Aladdin | Street Fighter II' Special… | Streets of Rage 2 | Wave Race 64 | Nintendo 64 Controller - O…
- **GT**: `<a_239><b_199><c_42>` The Adventures of Bayou Billy _(平台 ?)_ ｜ **native**: `<a_113><b_232><c_97>` Redesigned REPLACEMENT Joystic… ✗
- **beam top5**: `<a_113><b_232><c_97>`?, `<a_113><b_44><c_172>`Gam, `<a_113><b_232><c_152>`?, `<a_219><b_166><c_158>`?, `<a_113><b_127><c_139>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（2 个 a 大类）；unique(a,b)=6/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 5/6（覆盖83%），锚定: The Legend of Zelda: O…, Disney's Aladdin, Street Fighter II' Spe…；新候选=0（**纯复述历史**）；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #61 — 类目对·item错
- **历史**(7项; 平台 ?×7): Disney's Aladdin | Street Fighter II' Special… | Streets of Rage 2 | Wave Race 64 | Nintendo 64 Controller - O… | The Adventures of Bayou Bi…
- **GT**: `<a_233><b_229><c_215>` Double Dragon II: The Revenge _(平台 ?)_ ｜ **native**: `<a_113><b_232><c_97>` Redesigned REPLACEMENT Joystic… ✗
- **beam top5**: `<a_233><b_124><c_83>`?, `<a_113><b_232><c_97>`?, `<a_113><b_127><c_139>`?, `<a_250><b_199><c_170>`?, `<a_233><b_7><c_241>`?
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；beam中 share-a=3/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 5/7（覆盖71%），锚定: The Legend of Zelda: O…, The Adventures of Bayo…, Wave Race 64；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。

### #62 — 类目对·item错
- **历史**(5项; 平台 PS4×3,?×1,PS3×1): Fallout 4 - PlayStation 4 | Divinity: Original Sin - E… | Mega Man 2 - Nintendo NES | Mortal Kombat: Komplete Ed… | Mass Effect Andromeda - Pr…
- **GT**: `<a_141><b_73><c_216>` Star Wars: Battlefront - Standard Edition - Pl… _(平台 PS4)_ ｜ **native**: `<a_201><b_31><c_107>` Uncharted 4: A Thief's End - P… ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_201><b_213><c_242>`PS4, `<a_201><b_2><c_102>`PS4, `<a_200><b_169><c_179>`PS4, `<a_131><b_209><c_151>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=10/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/5（覆盖80%），锚定: Fallout 4 - PlayStatio…, Divinity: Original Sin…, Mass Effect Andromeda …；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #63 — 类目错·(a)大类都不对
- **历史**(4项; 平台 ?×2,PS×1,Wii×1): Grand Theft Auto III | Grand Theft Auto Vice City | Red Dead Revolver - PlaySt… | Wii Stand (RVL-017)
- **GT**: `<a_140><b_58><c_71>` Guitar Hero Live - PlayStation 3 _(平台 PS3)_ ｜ **native**: `<a_61><b_181><c_195>` Xbox 360 Wireless Controller -… ✗
- **beam top5**: `<a_240><b_33><c_93>`?, `<a_240><b_221><c_2>`PS3, `<a_240><b_40><c_2>`PS, `<a_61><b_181><c_195>`Xbo, `<a_61><b_181><c_175>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=9/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 1/4（覆盖25%），锚定: Wii Stand (RVL-017)；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #64 — 类目错·(a)大类都不对 · BEAM坍缩(<a_61×10/10)
- **历史**(4项; 平台 WiiU×2,PC×1,Xbox360×1): Super Mario Maker - Ninten… | StarCraft II: Heart of the… | LEGO Dimensions Starter Pa… | Microsoft Xbox 360 Wireles…
- **GT**: `<a_45><b_201><c_12>` Rocket League: Collector's Edition - Xbox One _(平台 XboxOne)_ ｜ **native**: `<a_61><b_181><c_195>` Xbox 360 Wireless Controller -… ✗
- **beam top5**: `<a_61><b_131><c_197>`Xbo, `<a_61><b_181><c_195>`Xbo, `<a_61><b_150><c_0>`Xbo, `<a_61><b_53><c_0>`Xbo, `<a_61><b_150><c_5>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=XboxOne vs 荐=Xbox)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_61 家族 10/10）；unique(a,b)=5/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Super Mario Maker - Ni…, LEGO Dimensions Starte…, StarCraft II: Heart of…；新候选=0（**纯复述历史**）；genre: action,immersive,accessor。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #65 — 类目错·(a)大类都不对 · BEAM坍缩(<a_61×10/10)
- **历史**(5项; 平台 WiiU×2,PC×1,Xbox360×1): Super Mario Maker - Ninten… | StarCraft II: Heart of the… | LEGO Dimensions Starter Pa… | Microsoft Xbox 360 Wireles… | Rocket League: Collector's…
- **GT**: `<a_205><b_175><c_169>` Tony Hawk's Pro Skater 5 - Standard Edition - … _(平台 XboxOne)_ ｜ **native**: `<a_61><b_181><c_195>` Xbox 360 Wireless Controller -… ✗
- **beam top5**: `<a_61><b_131><c_197>`Xbo, `<a_61><b_111><c_197>`Xbo, `<a_61><b_181><c_195>`Xbo, `<a_61><b_53><c_5>`Xbo, `<a_61><b_137><c_255>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=XboxOne vs 荐=Xbox)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_61 家族 10/10）；unique(a,b)=7/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 4/5（覆盖80%），锚定: Super Mario Maker - Ni…, LEGO Dimensions Starte…, Rocket League: Collect…；新候选=0（**纯复述历史**）；模板开头；genre: action,sports,accessor。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #66 — 类目对·item错
- **历史**(1项; 平台 ?×1): Logitech Gamepad F310
- **GT**: `<a_202><b_30><c_0>` Masione LED USB Gaming Wired Keyboard with 7 A… _(平台 ?)_ ｜ **native**: `<a_61><b_0><c_234>` Logitech Gamepad F310 ✗
- **beam top5**: `<a_202><b_82><c_172>`?, `<a_202><b_16><c_110>`?, `<a_202><b_34><c_39>`?, `<a_61><b_167><c_197>`Xbo, `<a_214><b_24><c_0>`?
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；beam中 share-a=6/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=8/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 0/1（覆盖0%）；新候选=0（**纯复述历史**）；genre: peripheral,accessor,controller。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=漂移(平台/词面关联)(score1)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #67 — 类目错·(a)大类都不对 · BEAM坍缩(<a_202×8/10)
- **历史**(2项; 平台 ?×2): Logitech Gamepad F310 | Masione LED USB Gaming Wir…
- **GT**: `<a_250><b_106><c_156>` Nintendo Selects: Super Mario Galaxy 2 _(平台 ?)_ ｜ **native**: `<a_202><b_16><c_110>` Razer DeathAdder Expert - Opti… ✗
- **beam top5**: `<a_202><b_82><c_172>`?, `<a_202><b_58><c_107>`?, `<a_202><b_200><c_67>`?, `<a_202><b_16><c_110>`?, `<a_202><b_34><c_39>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_202 家族 8/10）；unique(a,b)=9/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 0/2（覆盖0%）；新候选=0（**纯复述历史**）；genre: action,peripheral,accessor。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #68 — 类目对·item错 · BEAM坍缩(<a_250×10/10)
- **历史**(3项; 平台 ?×3): Logitech Gamepad F310 | Masione LED USB Gaming Wir… | Nintendo Selects: Super Ma…
- **GT**: `<a_250><b_92><c_44>` Nintendo Selects: Donkey Kong Country: Tropica… _(平台 ?)_ ｜ **native**: `<a_250><b_55><c_95>` Mario Kart 7 ✗
- **beam top5**: `<a_250><b_14><c_196>`?, `<a_250><b_219><c_103>`?, `<a_250><b_165><c_76>`?, `<a_250><b_55><c_137>`?, `<a_250><b_55><c_95>`?
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；beam中 share-a=10/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_250 家族 10/10）；unique(a,b)=7/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Logitech Gamepad F310, Masione LED USB Gaming…, Nintendo Selects: Supe…；新候选=0（**纯复述历史**）；genre: action,nostalg,peripheral。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。 注意 target 与历史共享词 ['selects']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #69 — 类目错·(a)大类都不对 · BEAM坍缩(<a_250×10/10)
- **历史**(4项; 平台 ?×4): Logitech Gamepad F310 | Masione LED USB Gaming Wir… | Nintendo Selects: Super Ma… | Nintendo Selects: Donkey K…
- **GT**: `<a_1><b_121><c_156>` Monster Hunter 3 Ultimate - Nintendo Wii U _(平台 WiiU)_ ｜ **native**: `<a_250><b_238><c_106>` Mario Party DS ✗
- **beam top5**: `<a_250><b_14><c_196>`?, `<a_250><b_14><c_103>`DS, `<a_250><b_207><c_203>`Wii, `<a_250><b_238><c_106>`DS, `<a_250><b_55><c_95>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_250 家族 10/10）；unique(a,b)=7/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 2/4（覆盖50%），锚定: Logitech Gamepad F310, Masione LED USB Gaming…；新候选=0（**纯复述历史**）；模板开头；genre: action,platformer,nostalg。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #70 — 类目错·(a)大类都不对
- **历史**(5项; 平台 ?×4,WiiU×1): Logitech Gamepad F310 | Masione LED USB Gaming Wir… | Nintendo Selects: Super Ma… | Nintendo Selects: Donkey K… | Monster Hunter 3 Ultimate …
- **GT**: `<a_84><b_235><c_1>` Nintendo Wii U Deluxe Set: Super Mario Bros U … _(平台 WiiU)_ ｜ **native**: `<a_250><b_238><c_255>` Mario Party 10 + Mario amiibo … ✗
- **beam top5**: `<a_113><b_35><c_8>`Gam, `<a_113><b_35><c_14>`Gam, `<a_250><b_55><c_95>`?, `<a_113><b_112><c_109>`Wii, `<a_113><b_240><c_225>`Wii
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=WiiU vs 荐=GameCube)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=9/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 5/5（覆盖100%），锚定: Logitech Gamepad F310, Masione LED USB Gaming…, Nintendo Selects: Supe…；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,platformer。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。 注意 target 与历史共享词 ['mario', 'super']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #71 — 类目错·(a)大类都不对
- **历史**(10项; 平台 PS4×5,PS×2,DS×1): Injustice 2 - PS4 [Digital… | Tekken 7 -  PS4 Digital Co… | Star Trek: Bridge Crew - P… | The Legend of Heroes: Trai… | Titanfall 2 - Vanguard Col… | Gran Turismo Sport - PlayS…
- **GT**: `<a_201><b_151><c_255>` Playstation Plus: 3 Month Membership [Digital … _(平台 PS-generic)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_123><b_58><c_16>`Xbo, `<a_24><b_72><c_142>`PS4, `<a_123><b_58><c_78>`PS4, `<a_39><b_77><c_105>`Xbo, `<a_24><b_185><c_47>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS-generic vs 荐=XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（7 个不同 a 大类）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 5/10（覆盖50%），锚定: The Evil Within - PC, Persona 5 - SteelBook …, Titanfall 2 - Vanguard…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。 注意 target 与历史共享词 ['code', 'digital']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #72 — 类目错·(a)大类都不对
- **历史**(10项; 平台 PS4×5,PS×3,PC×1): Tekken 7 -  PS4 Digital Co… | Star Trek: Bridge Crew - P… | The Legend of Heroes: Trai… | Titanfall 2 - Vanguard Col… | Gran Turismo Sport - PlayS… | Playstation Plus: 3 Month …
- **GT**: `<a_249><b_31><c_126>` Sony PlayStation Vita WiFi _(平台 PSVita)_ ｜ **native**: `<a_24><b_72><c_142>` Horizon Zero Dawn - PlayStatio… ✗
- **beam top5**: `<a_123><b_58><c_78>`PS4, `<a_24><b_72><c_142>`PS4, `<a_24><b_86><c_14>`PS4, `<a_201><b_31><c_107>`PS4, `<a_30><b_92><c_0>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PSVita vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（7 个不同 a 大类）；unique(a,b)=9/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 6/10（覆盖60%），锚定: The Evil Within - PC, Persona 5 - SteelBook …, The Legend of Heroes: …；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=漂移(平台/词面关联)(score1)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #73 — 类目错·(a)大类都不对
- **历史**(10项; 平台 PS4×5,PS×3,PS3×1): Star Trek: Bridge Crew - P… | The Legend of Heroes: Trai… | Titanfall 2 - Vanguard Col… | Gran Turismo Sport - PlayS… | Playstation Plus: 3 Month … | Sony PlayStation Vita WiFi
- **GT**: `<a_232><b_79><c_116>` Fire Emblem Fates: Conquest DLC - 3DS [Digital… _(平台 3DS)_ ｜ **native**: `<a_30><b_92><c_0>` Persona 5 - Standard Edition -… ✗
- **beam top5**: `<a_123><b_58><c_78>`PS4, `<a_30><b_92><c_146>`PS4, `<a_1><b_173><c_4>`PS4, `<a_30><b_92><c_0>`PS4, `<a_1><b_43><c_207>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=3DS vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（7 个不同 a 大类）；unique(a,b)=9/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 4/10（覆盖40%），锚定: Persona 5 - SteelBook …, The Legend of Heroes: …, Gran Turismo Sport - P…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。 注意 target 与历史共享词 ['code', 'digital']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #74 — 类目对·item错 · BEAM坍缩(<a_123×9/10)
- **历史**(2项; 平台 PS4×2): Fallout 4 Season Pass - PS… | Dead Island Definitive Col…
- **GT**: `<a_201><b_151><c_255>` Playstation Plus: 3 Month Membership [Digital … _(平台 PS-generic)_ ｜ **native**: `<a_123><b_142><c_36>` 7 Days to Die - PlayStation 4 ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_123><b_171><c_44>`Xbo, `<a_123><b_142><c_36>`PS4, `<a_123><b_188><c_192>`PS4, `<a_123><b_76><c_232>`PS4
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台错配(GT=PS-generic vs 荐=PS4)；beam中 share-a=1/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_123 家族 9/10）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: Fallout 4 Season Pass …, Dead Island Definitive…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。 注意 target 与历史共享词 ['code', 'digital']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #75 — 类目对·item错 · BEAM坍缩(<a_123×9/10)
- **历史**(3项; 平台 PS4×2,PS×1): Fallout 4 Season Pass - PS… | Dead Island Definitive Col… | Playstation Plus: 3 Month …
- **GT**: `<a_194><b_36><c_254>` Final Fantasy XV - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_123><b_142><c_36>` 7 Days to Die - PlayStation 4 ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_123><b_188><c_192>`PS4, `<a_123><b_78><c_71>`PS4, `<a_123><b_142><c_36>`PS4, `<a_123><b_44><c_0>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_123 家族 9/10）；unique(a,b)=10/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Fallout 4 Season Pass …, Dead Island Definitive…, Playstation Plus: 3 Mo…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #76 — 类目错·(a)大类都不对
- **历史**(4项; 平台 PS4×3,PS×1): Fallout 4 Season Pass - PS… | Dead Island Definitive Col… | Playstation Plus: 3 Month … | Final Fantasy XV - PlaySta…
- **GT**: `<a_113><b_104><c_28>` Nintendo 3DS Compatible with 3DS / 3DS XL / 2D… _(平台 3DS)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_201><b_18><c_56>`PS4, `<a_123><b_129><c_247>`PS4, `<a_123><b_58><c_78>`PS4, `<a_123><b_44><c_0>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=3DS vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=9/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Fallout 4 Season Pass …, Final Fantasy XV - Pla…, Dead Island Definitive…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #77 — 类目对·item错
- **历史**(5项; 平台 PS4×3,PS×1,3DS×1): Fallout 4 Season Pass - PS… | Dead Island Definitive Col… | Playstation Plus: 3 Month … | Final Fantasy XV - PlaySta… | Nintendo 3DS Compatible wi…
- **GT**: `<a_1><b_74><c_130>` Monster Hunter Generations - Nintendo 3DS Stan… _(平台 3DS)_ ｜ **native**: `<a_113><b_235><c_2>` Nintendo New 3DS XL - Black ✗
- **beam top5**: `<a_131><b_41><c_229>`PS4, `<a_113><b_235><c_2>`3DS, `<a_113><b_235><c_28>`3DS, `<a_119><b_168><c_182>`3DS, `<a_201><b_31><c_107>`PS4
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台错配(GT=3DS vs 荐=PS4)；beam中 share-a=1/10, share-(a,b)=0/10。
- **beam多样性**: **高**（7 个不同 a 大类）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/5（覆盖80%），锚定: Fallout 4 Season Pass …, Final Fantasy XV - Pla…, Dead Island Definitive…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #78 — 类目错·(a)大类都不对
- **历史**(1项; 平台 WiiU×1): Fosmon Component HD AV Cab…
- **GT**: `<a_92><b_68><c_129>` Doom - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_21><b_132><c_226>` Fosmon Component HD AV Cable t… ✗
- **beam top5**: `<a_21><b_242><c_102>`Gam, `<a_113><b_112><c_144>`Wii, `<a_21><b_125><c_39>`Wii, `<a_21><b_132><c_226>`Wii, `<a_113><b_112><c_109>`Wii
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS4 vs 荐=GameCube)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=8/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 0/1（覆盖0%）；新候选=0（**纯复述历史**）；genre: immersive,peripheral,accessor。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #79 — 类目对·item错
- **历史**(2项; 平台 WiiU×1,PS4×1): Fosmon Component HD AV Cab… | Doom - PlayStation 4
- **GT**: `<a_71><b_86><c_236>` UNCHARTED: The Nathan Drake Collection - PlayS… _(平台 PS4)_ ｜ **native**: `<a_131><b_224><c_68>` Overwatch - Origins Edition - … ✗
- **beam top5**: `<a_131><b_209><c_151>`PS4, `<a_7><b_248><c_16>`Xbo, `<a_131><b_210><c_0>`PS4, `<a_201><b_31><c_107>`PS4, `<a_7><b_36><c_0>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=9/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: Fosmon Component HD AV…, Doom - PlayStation 4；新候选=0（**纯复述历史**）；genre: action,immersive,narrative。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。

### #80 — 类目错·(a)大类都不对
- **历史**(3项; 平台 PS4×2,WiiU×1): Fosmon Component HD AV Cab… | Doom - PlayStation 4 | UNCHARTED: The Nathan Drak…
- **GT**: `<a_89><b_86><c_50>` World of Warcraft 60 Day Game Time [Digital Co… _(平台 ?)_ ｜ **native**: `<a_201><b_31><c_107>` Uncharted 4: A Thief's End - P… ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_131><b_210><c_0>`PS4, `<a_131><b_209><c_151>`PS4, `<a_201><b_2><c_102>`PS4, `<a_201><b_213><c_242>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=9/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Doom - PlayStation 4, UNCHARTED: The Nathan …, Fosmon Component HD AV…；新候选=0（**纯复述历史**）；模板开头；genre: action,adventure,immersive。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=漂移(平台/词面关联)(score1)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #81 — 类目对·item错
- **历史**(4项; 平台 PS4×2,WiiU×1,?×1): Fosmon Component HD AV Cab… | Doom - PlayStation 4 | UNCHARTED: The Nathan Drak… | World of Warcraft 60 Day G…
- **GT**: `<a_89><b_141><c_30>` World of Warcraft (Battle Chest Box) - PC/Mac … _(平台 PC)_ ｜ **native**: `<a_89><b_86><c_50>` World of Warcraft 60 Day Game … ✗
- **beam top5**: `<a_131><b_210><c_0>`PS4, `<a_89><b_86><c_158>`PC, `<a_141><b_73><c_216>`PS4, `<a_89><b_86><c_50>`?, `<a_131><b_209><c_151>`PS4
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台错配(GT=PC vs 荐=PS4)；beam中 share-a=5/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=9/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Doom - PlayStation 4, UNCHARTED: The Nathan …, Fosmon Component HD AV…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=漂移(平台/词面关联)(score1)。用户点击比我们top1**更贴历史**(target2>荐1) → 我们把可命中的延续**跑偏**了。 注意 target 与历史共享词 ['code', 'digital', 'online', 'warcraft', 'world']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #82 — 类目错·(a)大类都不对
- **历史**(9项; 平台 XboxOne×4,PS4×3,?×2): Resident Evil Origins Coll… | Bloodborne | Quantum Break - Xbox One | Tomsenn Kinect Sensor TV M… | NVIDIA SHIELD - 4K HDR Str… | The King of Fighters XIV: …
- **GT**: `<a_7><b_36><c_217>` Xbox One X 1TB Limited Edition Console - Proje… _(平台 XboxOne)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_123><b_58><c_78>`PS4, `<a_201><b_31><c_107>`PS4, `<a_24><b_129><c_173>`PS4, `<a_123><b_171><c_44>`Xbo, `<a_123><b_33><c_93>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=XboxOne vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 6/9（覆盖67%），锚定: Until Dawn - PlayStati…, Resident Evil Origins …, Nyko Power Pack for Pl…；新候选=0（**纯复述历史**）；模板开头；genre: action,horror,multiplayer。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。

### #83 — 类目错·(a)大类都不对 · BEAM坍缩(<a_202×8/10)
- **历史**(4项; 平台 ?×2,Switch×1,PS4×1): Razer BlackWidow Chroma: C… | Razer Naga Epic Chroma MMO… | Nintendo Pokemon Go Plus | KontrolFreek FPS Freek Vor…
- **GT**: `<a_231><b_46><c_171>` KontrolFreek CQCX Thumb Grips for PlayStation … _(平台 PS4)_ ｜ **native**: `<a_202><b_11><c_104>` Razer Limited Edition Naga MMO… ✗
- **beam top5**: `<a_202><b_58><c_107>`?, `<a_202><b_11><c_104>`?, `<a_202><b_58><c_57>`?, `<a_202><b_120><c_89>`?, `<a_202><b_251><c_120>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_202 家族 8/10）；unique(a,b)=6/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 2/4（覆盖50%），锚定: Nintendo Pokemon Go Pl…, KontrolFreek FPS Freek…；新候选=0（**纯复述历史**）；模板开头；genre: action,immersive,narrative。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。 注意 target 与历史共享词 ['controller', 'kontrolfreek']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #84 — 类目对·item错 · BEAM坍缩(<a_217×10/10)
- **历史**(10项; 平台 XboxOne×6,?×4): Skylanders SuperChargers: … | Skylanders SuperChargers: … | Skylanders SuperChargers: … | Rare Replay - Xbox One | XCom 2 - Xbox One | Skylanders Swap Force Star…
- **GT**: `<a_217><b_60><c_155>` Skylanders SuperChargers Starter Pack - PlaySt… _(平台 PS4)_ ｜ **native**: `<a_217><b_71><c_128>` Skylanders SuperChargers: Vehi… ✗
- **beam top5**: `<a_217><b_71><c_11>`?, `<a_217><b_71><c_2>`?, `<a_217><b_71><c_128>`?, `<a_217><b_71><c_4>`?, `<a_217><b_71><c_226>`?
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；beam中 share-a=10/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_217 家族 10/10）；unique(a,b)=1/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 4/10（覆盖40%），锚定: Skylanders SuperCharge…, Skylanders SuperCharge…, Skylanders Swap Force …；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=子类延续(score3)。我们推的比用户真实点击**更贴历史**(荐3>target2) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['skylanders', 'starter', 'superchargers']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #85 — 近失·同(a,b)细分仅c不同 · BEAM坍缩(<a_217×10/10)
- **历史**(10项; 平台 XboxOne×6,?×3,PS4×1): Skylanders SuperChargers: … | Skylanders SuperChargers: … | Rare Replay - Xbox One | XCom 2 - Xbox One | Skylanders Swap Force Star… | Skylanders SuperChargers S…
- **GT**: `<a_217><b_71><c_18>` Skylanders SuperChargers: Drivers Splat Charac… _(平台 ?)_ ｜ **native**: `<a_217><b_71><c_22>` Skylanders SuperChargers: Driv… ✗
- **beam top5**: `<a_217><b_71><c_11>`?, `<a_217><b_71><c_2>`?, `<a_217><b_71><c_226>`?, `<a_217><b_71><c_85>`?, `<a_217><b_71><c_128>`?
- **推荐↔GT差距**: beam 最接近项与 GT 同 (a,b) 细分、仅 c 不同（同系列/不同款），未命中；beam中 share-a=10/10, share-(a,b)=10/10。
- **beam多样性**: **低**（坍缩到 <a_217 家族 10/10）；unique(a,b)=1/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 6/10（覆盖60%），锚定: Skylanders SuperCharge…, Skylanders SuperCharge…, Skylanders Swap Force …；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=子类延续(score3); 我们pred[0]=子类延续(score3)。关联档位相同(score3)但选错具体 item。 注意 target 与历史共享词 ['character', 'drivers', 'skylanders', 'superchargers']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #86 — 类目错·(a)大类都不对
- **历史**(4项; 平台 PS4×4): WWE 2K16 - PlayStation 4 | Grand Theft Auto V - PlayS… | WWE 2K17 - PlayStation 4 | NHL 17 - PlayStation 4
- **GT**: `<a_86><b_12><c_93>` South Park: The Fractured but Whole - PlayStat… _(平台 PS4)_ ｜ **native**: `<a_45><b_28><c_168>` FIFA 17 - PlayStation 4 ✗
- **beam top5**: `<a_231><b_223><c_1>`Xbo, `<a_231><b_237><c_82>`PS4, `<a_45><b_28><c_168>`PS4, `<a_201><b_31><c_107>`PS4, `<a_231><b_237><c_4>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS4 vs 荐=Xbox360)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=6/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: WWE 2K16 - PlayStation…, Grand Theft Auto V - P…, WWE 2K17 - PlayStation…；新候选=0（**纯复述历史**）；genre: action,sports,simulation。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #87 — 类目错·(a)大类都不对
- **历史**(1项; 平台 PS3×1): PS3 500 GB Grand Theft Aut…
- **GT**: `<a_235><b_189><c_196>` Rayman Origins _(平台 ?)_ ｜ **native**: `<a_140><b_133><c_15>` Sony Playstation 3 160GB Syste… ✗
- **beam top5**: `<a_140><b_213><c_236>`PS4, `<a_140><b_133><c_15>`PS3, `<a_61><b_47><c_8>`PS3, `<a_140><b_133><c_1>`PS3, `<a_140><b_133><c_57>`PS3
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=7/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 1/1（覆盖100%），锚定: PS3 500 GB Grand Theft…；新候选=0（**纯复述历史**）；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=探索(无关联)(score0)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #88 — 类目错·(a)大类都不对 · BEAM坍缩(<a_249×7/10)
- **历史**(4项; 平台 ?×2,PS×2): Nintendo 64 System - Video… | GoldenEye 007 | Sony Playstation 1 COMPLET… | Gamily Playstation 1 Memor…
- **GT**: `<a_231><b_153><c_147>` Super Mario Bros. 3 _(平台 ?)_ ｜ **native**: `<a_249><b_52><c_108>` Sony Playstation Memory Card ✗
- **beam top5**: `<a_249><b_221><c_234>`PS, `<a_61><b_47><c_60>`PS, `<a_249><b_170><c_61>`PS, `<a_249><b_138><c_102>`PS, `<a_249><b_52><c_108>`PS
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_249 家族 7/10）；unique(a,b)=7/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Nintendo 64 System - V…, Sony Playstation 1 COM…, Gamily Playstation 1 M…；新候选=0（**纯复述历史**）；genre: action,immersive,nostalg。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #89 — 类目对·item错
- **历史**(5项; 平台 ?×3,PS×2): Nintendo 64 System - Video… | GoldenEye 007 | Sony Playstation 1 COMPLET… | Gamily Playstation 1 Memor… | Super Mario Bros. 3
- **GT**: `<a_21><b_38><c_115>` Retro-Bit SNES 6-Feet Extension Cable _(平台 ?)_ ｜ **native**: `<a_249><b_52><c_108>` Sony Playstation Memory Card ✗
- **beam top5**: `<a_61><b_47><c_60>`PS, `<a_233><b_106><c_144>`?, `<a_249><b_221><c_234>`PS, `<a_233><b_44><c_175>`?, `<a_249><b_170><c_61>`PS
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；beam中 share-a=1/10, share-(a,b)=0/10。
- **beam多样性**: **高**（6 个不同 a 大类）；unique(a,b)=10/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 4/5（覆盖80%），锚定: Sony Playstation 1 COM…, Gamily Playstation 1 M…, GoldenEye 007；新候选=0（**纯复述历史**）；模板开头；genre: action,shooter,immersive。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=探索(无关联)(score0)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #90 — 类目错·(a)大类都不对
- **历史**(6项; 平台 ?×4,PS×2): Nintendo 64 System - Video… | GoldenEye 007 | Sony Playstation 1 COMPLET… | Gamily Playstation 1 Memor… | Super Mario Bros. 3 | Retro-Bit SNES 6-Feet Exte…
- **GT**: `<a_193><b_157><c_142>` Sonic the Hedgehog _(平台 ?)_ ｜ **native**: `<a_21><b_44><c_75>` PS2 Controller Extension Cable… ✗
- **beam top5**: `<a_61><b_47><c_60>`PS, `<a_249><b_80><c_0>`PS2, `<a_249><b_221><c_234>`PS, `<a_249><b_170><c_61>`PS, `<a_21><b_129><c_194>`PS
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=10/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 3/6（覆盖50%），锚定: GoldenEye 007, Super Mario Bros. 3, Retro-Bit SNES 6-Feet …；新候选=0（**纯复述历史**）；模板开头；genre: action,shooter,nostalg。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=探索(无关联)(score0)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #91 — 类目错·(a)大类都不对 · BEAM坍缩(<a_233×10/10)
- **历史**(7项; 平台 ?×5,PS×2): GoldenEye 007 | Sony Playstation 1 COMPLET… | Gamily Playstation 1 Memor… | Super Mario Bros. 3 | Retro-Bit SNES 6-Feet Exte… | Sonic the Hedgehog
- **GT**: `<a_250><b_41><c_199>` Super Mario Bros. _(平台 ?)_ ｜ **native**: `<a_233><b_44><c_175>` Sega Dreamcast Controller (Ori… ✗
- **beam top5**: `<a_233><b_106><c_144>`?, `<a_233><b_206><c_153>`?, `<a_233><b_21><c_136>`?, `<a_233><b_45><c_52>`?, `<a_233><b_44><c_175>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_233 家族 10/10）；unique(a,b)=10/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 4/7（覆盖57%），锚定: Gamily Playstation 1 M…, Retro-Bit SNES 6-Feet …, GoldenEye 007；新候选=0（**纯复述历史**）；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=探索(无关联)(score0)。用户点击比我们top1**更贴历史**(target1>荐0) → 我们把可命中的延续**跑偏**了。 注意 target 与历史共享词 ['bros', 'mario', 'super']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #92 — 类目错·(a)大类都不对 · BEAM坍缩(<a_233×7/10)
- **历史**(8项; 平台 ?×6,PS×2): Sony Playstation 1 COMPLET… | Gamily Playstation 1 Memor… | Super Mario Bros. 3 | Retro-Bit SNES 6-Feet Exte… | Sonic the Hedgehog | Super Mario Bros.
- **GT**: `<a_208><b_166><c_139>` Mike Tyson's Punch-Out!! - Nintendo NES _(平台 ?)_ ｜ **native**: `<a_233><b_44><c_175>` Sega Dreamcast Controller (Ori… ✗
- **beam top5**: `<a_233><b_201><c_25>`PS4, `<a_233><b_106><c_144>`?, `<a_233><b_206><c_153>`?, `<a_233><b_44><c_175>`?, `<a_233><b_45><c_52>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_233 家族 7/10）；unique(a,b)=10/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 0/8（覆盖0%）；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=探索(无关联)(score0)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #93 — 类目错·(a)大类都不对
- **历史**(9项; 平台 ?×7,PS×2): Gamily Playstation 1 Memor… | Super Mario Bros. 3 | Retro-Bit SNES 6-Feet Exte… | Sonic the Hedgehog | Super Mario Bros. | Mike Tyson's Punch-Out!! -…
- **GT**: `<a_61><b_21><c_48>` Sony Playstation Controller - Gray (Non-Dualsh… _(平台 PS-generic)_ ｜ **native**: `<a_233><b_7><c_241>` Mortal Kombat II ✗
- **beam top5**: `<a_233><b_7><c_241>`?, `<a_233><b_45><c_52>`?, `<a_233><b_106><c_144>`?, `<a_208><b_174><c_227>`?, `<a_233><b_44><c_175>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（2 个 a 大类）；unique(a,b)=10/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/9（覆盖44%），锚定: GoldenEye 007, Super Mario Bros. 3, Retro-Bit SNES 6-Feet …；新候选=2；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=探索(无关联)(score0)。用户点击比我们top1**更贴历史**(target1>荐0) → 我们把可命中的延续**跑偏**了。 注意 target 与历史共享词 ['sony']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #94 — 类目对·item错
- **历史**(6项; 平台 PS4×3,?×2,XboxOne×1): Red Dead Redemption: Game … | Mafia II | Mafia II | Just Cause 3 - PlayStation… | Fallout 4 - PlayStation 4 | Fallout 4 Season Pass - PS…
- **GT**: `<a_13><b_218><c_173>` Agents of Mayhem - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_123><b_72><c_7>` Far Cry 4 - PlayStation 4 ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_123><b_72><c_7>`PS4, `<a_118><b_233><c_76>`PS4, `<a_201><b_145><c_9>`PS4, `<a_123><b_76><c_232>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=10/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 5/5（覆盖100%），锚定: Mafia II, Just Cause 3 - PlaySta…, Fallout 4 - PlayStatio…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。

### #95 — 类目错·(a)大类都不对
- **历史**(10项; 平台 PS4×4,PS×2,PS3×2): Assassin's Creed: The Amer… | Digimon Story: Cyber Sleut… | Xbox One 500 GB Console - … | Final Fantasy Type-0 HD - … | Assassin's Creed: Syndicat… | Star Ocean Till the End of…
- **GT**: `<a_249><b_134><c_122>` Sony PSP-1001K PlayStation Portable (PSP) Syst… _(平台 PSP)_ ｜ **native**: `<a_194><b_33><c_4>` Dark Souls II: Scholar of the … ✗
- **beam top5**: `<a_194><b_215><c_154>`?, `<a_194><b_33><c_4>`PS4, `<a_194><b_33><c_2>`Xbo, `<a_194><b_21><c_76>`PS4, `<a_194><b_87><c_112>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=9/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 6/10（覆盖60%），锚定: Unravel - PS4 [Digital…, Final Fantasy XV - Pla…, Assassin's Creed Rogue…；新候选=0（**纯复述历史**）；模板开头；genre: action,role-playing,immersive。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['black']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #96 — 类目错·(a)大类都不对
- **历史**(10项; 平台 PS4×3,PS×2,PS3×2): Digimon Story: Cyber Sleut… | Xbox One 500 GB Console - … | Final Fantasy Type-0 HD - … | Assassin's Creed: Syndicat… | Star Ocean Till the End of… | Sony PSP-1001K PlayStation…
- **GT**: `<a_249><b_134><c_122>` Sony PSP-1001K PlayStation Portable (PSP) Syst… _(平台 PSP)_ ｜ **native**: `<a_1><b_150><c_189>` Legend of Heroes: Trails of Co… ✗
- **beam top5**: `<a_194><b_87><c_112>`PS4, `<a_194><b_33><c_4>`PS4, `<a_118><b_150><c_122>`PS4, `<a_194><b_21><c_76>`PS4, `<a_1><b_173><c_4>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PSP vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=10/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 7/10（覆盖70%），锚定: Final Fantasy XV - Pla…, Assassin's Creed Rogue…, Assassin's Creed: The …；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=子类延续(score3); 我们pred[0]=大类延续(score2)。用户点击比我们top1**更贴历史**(target3>荐2) → 我们把可命中的延续**跑偏**了。 注意 target 与历史共享词 ['1001k', 'black', 'portable', 'sony']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #97 — 类目错·(a)大类都不对 · BEAM坍缩(<a_249×9/10)
- **历史**(1项; 平台 PS×1): Datel Max Playstation 2 Ac…
- **GT**: `<a_8><b_230><c_140>` Generic AC Power Adapter Charger for Nintendo … _(平台 3DS)_ ｜ **native**: `<a_249><b_170><c_61>` Buyee 128MB Memory Card for So… ✗
- **beam top5**: `<a_249><b_221><c_234>`PS, `<a_249><b_38><c_208>`PS, `<a_249><b_170><c_61>`PS, `<a_61><b_47><c_60>`PS, `<a_249><b_80><c_0>`PS2
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=3DS vs 荐=PS2)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_249 家族 9/10）；unique(a,b)=7/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 1/1（覆盖100%），锚定: Datel Max Playstation …；新候选=0（**纯复述历史**）；genre: action,peripheral,accessor。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #98 — 类目错·(a)大类都不对
- **历史**(2项; 平台 PS×1,3DS×1): Datel Max Playstation 2 Ac… | Generic AC Power Adapter C…
- **GT**: `<a_175><b_179><c_41>` Nintendo 3DS - Flame Red _(平台 3DS)_ ｜ **native**: `<a_113><b_104><c_28>` Nintendo 3DS Compatible with 3… ✗
- **beam top5**: `<a_8><b_70><c_241>`Xbo, `<a_8><b_230><c_178>`3DS, `<a_113><b_104><c_28>`3DS, `<a_8><b_93><c_169>`Wii, `<a_249><b_170><c_61>`PS
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=3DS vs 荐=XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=10/10，平台数=5，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: Datel Max Playstation …, Generic AC Power Adapt…；新候选=0（**纯复述历史**）；genre: action,nostalg,retro。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #99 — 类目错·(a)大类都不对 · BEAM坍缩(<a_249×9/10)
- **历史**(3项; 平台 3DS×2,PS×1): Datel Max Playstation 2 Ac… | Generic AC Power Adapter C… | Nintendo 3DS - Flame Red
- **GT**: `<a_245><b_232><c_158>` LEGO Jurassic World - Nintendo 3DS _(平台 3DS)_ ｜ **native**: `<a_249><b_170><c_61>` Buyee 128MB Memory Card for So… ✗
- **beam top5**: `<a_249><b_170><c_61>`PS, `<a_249><b_183><c_124>`PSP, `<a_249><b_194><c_103>`PSV, `<a_249><b_183><c_22>`PSP, `<a_249><b_180><c_74>`PSV
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=3DS vs 荐=PS2)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_249 家族 9/10）；unique(a,b)=9/10，平台数=5，unique标题=9/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Datel Max Playstation …, Generic AC Power Adapt…, Nintendo 3DS - Flame R…；新候选=0（**纯复述历史**）；模板开头；genre: action,nostalg,retro。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #100 — 类目错·(a)大类都不对
- **历史**(4项; 平台 3DS×3,PS×1): Datel Max Playstation 2 Ac… | Generic AC Power Adapter C… | Nintendo 3DS - Flame Red | LEGO Jurassic World - Nint…
- **GT**: `<a_1><b_229><c_126>` Monster Hunter 3 Ultimate - Nintendo 3DS _(平台 3DS)_ ｜ **native**: `<a_245><b_232><c_5>` LEGO Jurassic World - PlayStat… ✗
- **beam top5**: `<a_245><b_232><c_5>`PS3, `<a_245><b_232><c_39>`PSV, `<a_245><b_91><c_144>`PS3, `<a_249><b_183><c_124>`PSP, `<a_249><b_170><c_61>`PS
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=3DS vs 荐=PS3)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=6/10，平台数=6，unique标题=9/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Datel Max Playstation …, Generic AC Power Adapt…, Nintendo 3DS - Flame R…；新候选=0（**纯复述历史**）；genre: action,immersive,narrative。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=子类延续(score3)。我们推的比用户真实点击**更贴历史**(荐3>target1) → **模型偏保守/用户更爱探索**。

### #101 — 类目对·item错
- **历史**(10项; 平台 3DS×3,Xbox360×3,PS4×2): Assassin's Creed IV Black … | Medal of Honor - Xbox 360 | Kinect Sensor TV Mounting … | Mario Golf: World Tour - N… | Kirby Triple Deluxe - Nint… | Action Replay DSi
- **GT**: `<a_86><b_12><c_93>` South Park: The Fractured but Whole - PlayStat… _(平台 PS4)_ ｜ **native**: `<a_240><b_76><c_14>` Thief - PlayStation 4 ✗
- **beam top5**: `<a_140><b_50><c_3>`PS4, `<a_80><b_66><c_0>`?, `<a_219><b_31><c_249>`3DS, `<a_219><b_127><c_200>`DS, `<a_113><b_31><c_38>`3DS
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（6 个不同 a 大类）；unique(a,b)=8/10，平台数=5，unique标题=10/10。
- **reasoning质量**: 引用历史 7/10（覆盖70%），锚定: Need for Speed: Hot Pu…, Assassin's Creed IV Bl…, PlayStation 4 500GB Co…；新候选=1；模板开头；genre: action,adventure,racing。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #102 — 命中@6
- **历史**(10项; 平台 PS4×5,?×4,WiiU×1): Kirby Mass Attack | Meta Knight amiibo - Japan… | Nintendo Super Smash Bros … | Watch Dogs - PlayStation 4 | Watch Dogs 2 - PlayStation… | Call Of Duty: Infinite War…
- **GT**: `<a_24><b_72><c_142>` Horizon Zero Dawn - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_191><b_10><c_232>` Watch Dogs 2 - PlayStation 4 ✗
- **beam top5**: `<a_123><b_58><c_78>`PS4, `<a_39><b_51><c_188>`PS4, `<a_1><b_43><c_207>`PS4, `<a_39><b_78><c_54>`PS4, `<a_201><b_45><c_166>`PS4
- **推荐↔GT差距**: 正确项在 beam 第6位，pred[0] 前缀深度仅 0/3；平台一致(PS4)；beam中 share-a=1/10, share-(a,b)=1/10。
- **beam多样性**: **高**（7 个不同 a 大类）；unique(a,b)=10/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 6/10（覆盖60%），锚定: Mad Max - PlayStation …, Watch Dogs - PlayStati…, The Legend of Zelda: T…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。target 是合理的漂移(平台/词面关联)，且**已命中**。

### #103 — 类目对·item错
- **历史**(4项; 平台 3DS×2,?×1,PS4×1): Mario Kart 7 | Nintendo 3DS Compatible wi… | Nintendo New 3DS Xl - Red … | Just Dance 2016 (Gold Edit…
- **GT**: `<a_189><b_5><c_25>` Controller Gear PS4 Controller Stand - Officia… _(平台 PS4)_ ｜ **native**: `<a_111><b_238><c_188>` Just Dance 2016 - PlayStation … ✗
- **beam top5**: `<a_111><b_238><c_188>`PS4, `<a_250><b_238><c_255>`Wii, `<a_113><b_235><c_2>`3DS, `<a_111><b_236><c_47>`PS4, `<a_162><b_251><c_136>`Wii
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=8/10，平台数=7，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Mario Kart 7, Nintendo 3DS Compatibl…, Just Dance 2016 (Gold …；新候选=0（**纯复述历史**）；genre: action,accessor。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #104 — 类目对·item错
- **历史**(5项; 平台 3DS×2,PS4×2,?×1): Mario Kart 7 | Nintendo 3DS Compatible wi… | Nintendo New 3DS Xl - Red … | Just Dance 2016 (Gold Edit… | Controller Gear PS4 Contro…
- **GT**: `<a_111><b_158><c_30>` Just Dance 2017 - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_111><b_238><c_188>` Just Dance 2016 - PlayStation … ✗
- **beam top5**: `<a_111><b_238><c_188>`PS4, `<a_189><b_90><c_110>`PS4, `<a_189><b_236><c_252>`PS, `<a_189><b_151><c_87>`PS4, `<a_189><b_201><c_57>`PS4
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台一致(PS4)；beam中 share-a=5/10, share-(a,b)=0/10。
- **beam多样性**: **中**（2 个 a 大类）；unique(a,b)=8/10，平台数=5，unique标题=10/10。
- **reasoning质量**: 引用历史 4/5（覆盖80%），锚定: Mario Kart 7, Nintendo 3DS Compatibl…, Just Dance 2016 (Gold …；新候选=0（**纯复述历史**）；模板开头；genre: action,immersive,portable。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。 注意 target 与历史共享词 ['dance', 'just']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #105 — 类目错·(a)大类都不对 · BEAM坍缩(<a_162×9/10)
- **历史**(10项; 平台 WiiU×4,PS4×3,?×2): Uncharted 4: A Thief's End… | Nintendo Donkey Kong amiib… | Monster Hunter 4 Ultimate … | Dragon Quest Builders - Pl… | Nintendo Rosalina amiibo (… | Steam Controller
- **GT**: `<a_191><b_246><c_101>` Metro Redux - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_162><b_130><c_224>` Nintendo Donkey Kong amiibo (S… ✗
- **beam top5**: `<a_162><b_130><c_51>`Wii, `<a_162><b_222><c_61>`Wii, `<a_162><b_130><c_2>`Wii, `<a_162><b_122><c_56>`?, `<a_162><b_130><c_224>`Wii
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS4 vs 荐=WiiU)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_162 家族 9/10）；unique(a,b)=4/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/10（覆盖40%），锚定: Nintendo Daisy amiibo …, Nintendo Waluigi amiib…, Mighty No. 9 - PlaySta…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=子类延续(score3)。我们推的比用户真实点击**更贴历史**(荐3>target1) → **模型偏保守/用户更爱探索**。

### #106 — 类目错·(a)大类都不对 · BEAM坍缩(<a_39×8/10)
- **历史**(3项; 平台 XboxOne×3): Pro Evolution Soccer 2015 … | Xbox One Chat Headset | Titanfall - Xbox One
- **GT**: `<a_157><b_17><c_153>` Rock Candy Wii Gesture Controller - Purple _(平台 Wii)_ ｜ **native**: `<a_39><b_151><c_9>` Halo 5: Guardians ✗
- **beam top5**: `<a_39><b_114><c_237>`Xbo, `<a_39><b_114><c_209>`Xbo, `<a_39><b_69><c_69>`Xbo, `<a_39><b_204><c_3>`Xbo, `<a_39><b_151><c_9>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=Wii vs 荐=XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_39 家族 8/10）；unique(a,b)=7/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Pro Evolution Soccer 2…, Xbox One Chat Headset, Titanfall - Xbox One；新候选=0（**纯复述历史**）；genre: action,shooter,sports。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #107 — 类目对·item错
- **历史**(4项; 平台 XboxOne×3,Wii×1): Pro Evolution Soccer 2015 … | Xbox One Chat Headset | Titanfall - Xbox One | Rock Candy Wii Gesture Con…
- **GT**: `<a_45><b_78><c_36>` NBA Live 14 - Xbox One _(平台 XboxOne)_ ｜ **native**: `<a_61><b_214><c_252>` Xbox One Media Remote ✗
- **beam top5**: `<a_61><b_214><c_252>`Xbo, `<a_39><b_114><c_237>`Xbo, `<a_61><b_181><c_195>`Xbo, `<a_39><b_114><c_209>`Xbo, `<a_61><b_53><c_5>`Xbo
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台一致(XboxOne)；beam中 share-a=1/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=9/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Pro Evolution Soccer 2…, Titanfall - Xbox One, Xbox One Chat Headset；新候选=0（**纯复述历史**）；genre: sports,immersive,accessor。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=漂移(平台/词面关联)(score1)。用户点击比我们top1**更贴历史**(target2>荐1) → 我们把可命中的延续**跑偏**了。

### #108 — 类目对·item错 · BEAM坍缩(<a_119×7/10)
- **历史**(4项; 平台 WiiU×3,3DS×1): Nintendo Wii U Fit Balance… | Official Gamer Essentials … | Spirit Camera: The Cursed … | Wii U Gamepad Silicone Jac…
- **GT**: `<a_113><b_152><c_199>` HORI Compact PlayStand - Zelda Edition, Offici… _(平台 Switch)_ ｜ **native**: `<a_119><b_112><c_222>` Wii U Gamepad Silicone Jacket … ✗
- **beam top5**: `<a_113><b_112><c_109>`Wii, `<a_113><b_104><c_28>`3DS, `<a_119><b_93><c_19>`Wii, `<a_119><b_119><c_158>`3DS, `<a_119><b_146><c_253>`3DS
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台错配(GT=Switch vs 荐=WiiU)；beam中 share-a=3/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_119 家族 7/10）；unique(a,b)=10/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 3/4（覆盖75%），锚定: Official Gamer Essenti…, Spirit Camera: The Cur…, Wii U Gamepad Silicone…；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,horror。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。

### #109 — 类目对·item错
- **历史**(4项; 平台 PS4×4): PlayStation 4 Camera (Old … | Uncharted 4: A Thief's End… | SQDeal Dust Proof Dust Pre… | Assassins Creed Syndicate …
- **GT**: `<a_194><b_15><c_66>` Dishonored 2 - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_118><b_185><c_102>` Batman: Arkham Knight - PlaySt… ✗
- **beam top5**: `<a_123><b_72><c_7>`PS4, `<a_201><b_213><c_242>`PS4, `<a_201><b_2><c_102>`PS4, `<a_118><b_185><c_102>`PS4, `<a_201><b_85><c_136>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=10/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 3/4（覆盖75%），锚定: Uncharted 4: A Thief's…, Assassins Creed Syndic…, PlayStation 4 Camera (…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。

### #110 — 类目错·(a)大类都不对
- **历史**(4项; 平台 PS4×4): Just Dance 2016 - PlayStat… | PlayStation 4 500GB Consol… | PlayStation 4 Camera (Old … | Doom: Collector's Edition …
- **GT**: `<a_231><b_33><c_2>` ZD-N Vibration-Feedback USB Wired Gamepad Gami… _(平台 PS3)_ ｜ **native**: `<a_131><b_224><c_68>` Overwatch - Origins Edition - … ✗
- **beam top5**: `<a_61><b_251><c_144>`PS4, `<a_131><b_224><c_68>`PS4, `<a_201><b_31><c_107>`PS4, `<a_131><b_41><c_229>`PS4, `<a_39><b_175><c_240>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS3 vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（7 个不同 a 大类）；unique(a,b)=10/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Just Dance 2016 - Play…, PlayStation 4 500GB Co…, Doom: Collector's Edit…；新候选=0（**纯复述历史**）；模板开头；genre: action,immersive,accessor。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=漂移(平台/词面关联)(score1)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #111 — 类目错·(a)大类都不对 · BEAM坍缩(<a_202×9/10)
- **历史**(2项; 平台 ?×2): AULA LED Backlit Gaming Ke… | HAVIT HV-MS672 3200DPI Wir…
- **GT**: `<a_195><b_59><c_156>` Shin Megami Tensei IV - Nintendo 3DS _(平台 3DS)_ ｜ **native**: `<a_202><b_11><c_246>` Razer Naga Epic Chroma MMO Gam… ✗
- **beam top5**: `<a_202><b_253><c_105>`?, `<a_202><b_82><c_172>`?, `<a_202><b_34><c_39>`?, `<a_202><b_16><c_110>`?, `<a_202><b_203><c_93>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_202 家族 9/10）；unique(a,b)=9/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: AULA LED Backlit Gamin…, HAVIT HV-MS672 3200DPI…；新候选=0（**纯复述历史**）；模板开头；genre: action,peripheral,accessor。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #112 — 类目错·(a)大类都不对 · BEAM坍缩(<a_195×10/10)
- **历史**(3项; 平台 ?×2,3DS×1): AULA LED Backlit Gaming Ke… | HAVIT HV-MS672 3200DPI Wir… | Shin Megami Tensei IV - Ni…
- **GT**: `<a_216><b_93><c_101>` The Legend of Zelda: A Link Between Worlds 3D _(平台 ?)_ ｜ **native**: `<a_195><b_179><c_27>` Star Ocean Till the End of Tim… ✗
- **beam top5**: `<a_195><b_36><c_218>`?, `<a_195><b_179><c_27>`PS, `<a_195><b_4><c_1>`PS, `<a_195><b_4><c_0>`?, `<a_195><b_179><c_9>`PSP
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_195 家族 10/10）；unique(a,b)=6/10，平台数=6，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: AULA LED Backlit Gamin…, HAVIT HV-MS672 3200DPI…, Shin Megami Tensei IV …；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,strategy。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #113 — 类目对·item错
- **历史**(4项; 平台 ?×2,3DS×1,DS×1): AULA LED Backlit Gaming Ke… | HAVIT HV-MS672 3200DPI Wir… | Shin Megami Tensei IV - Ni… | The Legend of Zelda: A Lin…
- **GT**: `<a_119><b_168><c_182>` HORI Screen Protective Filter for Nintendo NEW… _(平台 3DS)_ ｜ **native**: `<a_216><b_112><c_119>` The Legend of Zelda: Majora's … ✗
- **beam top5**: `<a_113><b_104><c_28>`3DS, `<a_113><b_235><c_28>`3DS, `<a_113><b_235><c_2>`3DS, `<a_216><b_165><c_184>`Wii, `<a_216><b_112><c_114>`Wii
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(3DS)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=8/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: AULA LED Backlit Gamin…, HAVIT HV-MS672 3200DPI…, Shin Megami Tensei IV …；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,immersive。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。

### #114 — 类目对·item错 · BEAM坍缩(<a_119×8/10)
- **历史**(5项; 平台 ?×2,3DS×2,DS×1): AULA LED Backlit Gaming Ke… | HAVIT HV-MS672 3200DPI Wir… | Shin Megami Tensei IV - Ni… | The Legend of Zelda: A Lin… | HORI Screen Protective Fil…
- **GT**: `<a_216><b_121><c_190>` Nintendo Selects: The Legend of Zelda Ocarina … _(平台 ?)_ ｜ **native**: `<a_119><b_168><c_182>` HORI Screen Protective Filter … ✗
- **beam top5**: `<a_119><b_235><c_165>`3DS, `<a_119><b_119><c_158>`3DS, `<a_119><b_35><c_129>`3DS, `<a_119><b_146><c_253>`3DS, `<a_119><b_31><c_233>`3DS
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；beam中 share-a=1/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_119 家族 8/10）；unique(a,b)=10/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 5/5（覆盖100%），锚定: AULA LED Backlit Gamin…, HAVIT HV-MS672 3200DPI…, Shin Megami Tensei IV …；新候选=0（**纯复述历史**）；模板开头；genre: action,adventure,rpg。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。 注意 target 与历史共享词 ['3d', 'legend', 'zelda']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #115 — 类目错·(a)大类都不对 · BEAM坍缩(<a_216×7/10)
- **历史**(6项; 平台 ?×3,3DS×2,DS×1): AULA LED Backlit Gaming Ke… | HAVIT HV-MS672 3200DPI Wir… | Shin Megami Tensei IV - Ni… | The Legend of Zelda: A Lin… | HORI Screen Protective Fil… | Nintendo Selects: The Lege…
- **GT**: `<a_194><b_235><c_193>` Final Fantasy XII: The Zodiac Age - PlayStatio… _(平台 PS4)_ ｜ **native**: `<a_216><b_112><c_119>` The Legend of Zelda: Majora's … ✗
- **beam top5**: `<a_216><b_51><c_130>`3DS, `<a_216><b_112><c_119>`?, `<a_119><b_31><c_233>`3DS, `<a_216><b_112><c_114>`Wii, `<a_113><b_235><c_2>`3DS
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS4 vs 荐=3DS)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_216 家族 7/10）；unique(a,b)=9/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 5/6（覆盖83%），锚定: AULA LED Backlit Gamin…, HAVIT HV-MS672 3200DPI…, Shin Megami Tensei IV …；新候选=0（**纯复述历史**）；模板开头；genre: action,adventure,rpg。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #116 — 类目对·item错
- **历史**(2项; 平台 PS4×2): Metal Gear Solid V: Ground… | Middle Earth: Shadow of Mo…
- **GT**: `<a_118><b_162><c_110>` Batman: Arkham Origins - Playstation 3 _(平台 PS3)_ ｜ **native**: `<a_201><b_145><c_9>` The Witcher 3: Wild Hunt - Pla… ✗
- **beam top5**: `<a_201><b_145><c_9>`PS4, `<a_118><b_95><c_6>`PS4, `<a_123><b_129><c_247>`PS4, `<a_118><b_150><c_122>`PS4, `<a_123><b_72><c_7>`PS4
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台错配(GT=PS3 vs 荐=PS4)；beam中 share-a=4/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=10/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: Metal Gear Solid V: Gr…, Middle Earth: Shadow o…；新候选=0（**纯复述历史**）；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=漂移(平台/词面关联)(score1)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #117 — 命中@4
- **历史**(3项; 平台 PS4×2,PS3×1): Metal Gear Solid V: Ground… | Middle Earth: Shadow of Mo… | Batman: Arkham Origins - P…
- **GT**: `<a_123><b_129><c_247>` Metal Gear Solid V: The Phantom Pain - PlaySta… _(平台 PS4)_ ｜ **native**: `<a_118><b_185><c_102>` Batman: Arkham Knight - PlaySt… ✗
- **beam top5**: `<a_118><b_185><c_102>`PS4, `<a_123><b_72><c_7>`PS4, `<a_118><b_150><c_122>`PS4, `<a_123><b_129><c_247>`PS4, `<a_118><b_95><c_6>`PS4
- **推荐↔GT差距**: 正确项在 beam 第4位，pred[0] 前缀深度仅 0/3；平台一致(PS4)；beam中 share-a=4/10, share-(a,b)=1/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=10/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Metal Gear Solid V: Gr…, Middle Earth: Shadow o…, Batman: Arkham Origins…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。target 是合理的大类延续，且**已命中**。

### #118 — 类目错·(a)大类都不对
- **历史**(3项; 平台 PS4×3): Assassin's Creed: Syndicat… | Overwatch - Origins Editio… | Mad Max - PlayStation 4
- **GT**: `<a_191><b_56><c_45>` Payday 2 - Playstation 3 _(平台 PS3)_ ｜ **native**: `<a_131><b_209><c_151>` No Man's Sky - PlayStation 4 ✗
- **beam top5**: `<a_141><b_73><c_216>`PS4, `<a_201><b_31><c_107>`PS4, `<a_131><b_210><c_0>`PS4, `<a_131><b_209><c_151>`PS4, `<a_201><b_145><c_9>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS3 vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=10/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Assassin's Creed: Synd…, Overwatch - Origins Ed…, Mad Max - PlayStation …；新候选=0（**纯复述历史**）；模板开头；genre: action,multiplayer,immersive。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=漂移(平台/词面关联)(score1)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #119 — 类目错·(a)大类都不对
- **历史**(4项; 平台 PS4×3,PS3×1): Assassin's Creed: Syndicat… | Overwatch - Origins Editio… | Mad Max - PlayStation 4 | Payday 2 - Playstation 3
- **GT**: `<a_24><b_37><c_113>` BioShock Infinite - PS3 [Digital Code] _(平台 PS3)_ ｜ **native**: `<a_131><b_209><c_151>` No Man's Sky - PlayStation 4 ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_131><b_210><c_0>`PS4, `<a_131><b_145><c_6>`PS4, `<a_131><b_209><c_151>`PS4, `<a_200><b_186><c_92>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS3 vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=10/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Assassin's Creed: Synd…, Overwatch - Origins Ed…, Payday 2 - Playstation…；新候选=0（**纯复述历史**）；模板开头；genre: action,multiplayer,immersive。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。

### #120 — 类目对·item错
- **历史**(5项; 平台 Xbox360×2,3DS×2,PS4×1): Deus Ex Human Revolution: … | Horizon Zero Dawn - PlaySt… | Pok&eacute;mon Omega Ruby … | Pok&eacute;mon Sun - Ninte… | The Wolf Among Us - Xbox 3…
- **GT**: `<a_201><b_100><c_205>` Tales from the Borderlands - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_201><b_31><c_107>` Uncharted 4: A Thief's End - P… ✗
- **beam top5**: `<a_201><b_18><c_56>`PS4, `<a_201><b_31><c_107>`PS4, `<a_201><b_213><c_242>`PS4, `<a_118><b_242><c_8>`PS4, `<a_123><b_58><c_78>`PS4
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台一致(PS4)；beam中 share-a=3/10, share-(a,b)=0/10。
- **beam多样性**: **高**（8 个不同 a 大类）；unique(a,b)=10/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 5/5（覆盖100%），锚定: Deus Ex Human Revoluti…, Horizon Zero Dawn - Pl…, The Wolf Among Us - Xb…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。

### #121 — 命中@4
- **历史**(7项; 平台 PS4×5,?×1,WiiU×1): PlayStation 4 500GB Consol… | Middle Earth: Shadow of Mo… | Bloodborne | Wolfenstein: The Old Blood… | Titanfall 2 - PlayStation … | The Legend of Zelda: Breat…
- **GT**: `<a_24><b_72><c_142>` Horizon Zero Dawn - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_194><b_15><c_66>` Dishonored 2 - PlayStation 4 ✗
- **beam top5**: `<a_194><b_15><c_66>`PS4, `<a_194><b_87><c_112>`PS4, `<a_123><b_58><c_78>`PS4, `<a_24><b_72><c_142>`PS4, `<a_24><b_86><c_14>`PS4
- **推荐↔GT差距**: 正确项在 beam 第4位，pred[0] 前缀深度仅 0/3；平台一致(PS4)；beam中 share-a=2/10, share-(a,b)=1/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=10/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 6/7（覆盖86%），锚定: Star Wars: Battlefront…, Bloodborne, Wolfenstein: The Old B…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。target 是合理的漂移(平台/词面关联)，且**已命中**。

### #122 — 类目对·item错 · BEAM坍缩(<a_24×8/10)
- **历史**(2项; 平台 PS4×2): Until Dawn - PlayStation 4 | Ratchet & Clank - PlayStat…
- **GT**: `<a_24><b_118><c_34>` Abzu - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_24><b_86><c_14>` Uncharted 4: A Thief's End Spe… ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_24><b_178><c_18>`Xbo, `<a_24><b_129><c_173>`PS4, `<a_24><b_145><c_101>`PS4, `<a_24><b_86><c_14>`PS4
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台一致(PS4)；beam中 share-a=8/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_24 家族 8/10）；unique(a,b)=10/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: Until Dawn - PlayStati…, Ratchet & Clank - Play…；新候选=0（**纯复述历史**）；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #123 — 类目对·item错
- **历史**(8项; 平台 XboxOne×6,PC×1,DS×1): SteelSeries Nimbus Wireles… | Turtle Beach - Ear Force H… | Thrustmaster TMX Force Fee… | Thrustmaster Y-350X 7.1 Po… | SteelSeries Siberia 200 Ga… | PDP Talon Media Remote Con…
- **GT**: `<a_131><b_38><c_83>` For Honor - Xbox One _(平台 XboxOne)_ ｜ **native**: `<a_61><b_214><c_225>` PDP Talon Media Remote Control… ✗
- **beam top5**: `<a_61><b_231><c_105>`Xbo, `<a_61><b_214><c_225>`Xbo, `<a_202><b_50><c_200>`DS, `<a_202><b_11><c_246>`?, `<a_202><b_3><c_27>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=8/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 5/8（覆盖62%），锚定: Mortal Kombat X Fight …, Razer Wildcat eSports …, Turtle Beach - Ear For…；新候选=0（**纯复述历史**）；模板开头；genre: action,immersive,peripheral。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=子类延续(score3)。我们推的比用户真实点击**更贴历史**(荐3>target1) → **模型偏保守/用户更爱探索**。

### #124 — 类目对·item错
- **历史**(9项; 平台 XboxOne×7,PC×1,DS×1): Turtle Beach - Ear Force H… | Thrustmaster TMX Force Fee… | Thrustmaster Y-350X 7.1 Po… | SteelSeries Siberia 200 Ga… | PDP Talon Media Remote Con… | For Honor - Xbox One
- **GT**: `<a_86><b_37><c_30>` Steep - Xbox One _(平台 XboxOne)_ ｜ **native**: `<a_61><b_214><c_225>` PDP Talon Media Remote Control… ✗
- **beam top5**: `<a_61><b_231><c_105>`Xbo, `<a_61><b_53><c_47>`Xbo, `<a_61><b_111><c_109>`Xbo, `<a_202><b_50><c_200>`DS, `<a_202><b_11><c_246>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=10/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 6/9（覆盖67%），锚定: Mortal Kombat X Fight …, Razer Wildcat eSports …, Turtle Beach - Ear For…；新候选=0（**纯复述历史**）；模板开头；genre: action,peripheral,accessor。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=子类延续(score3)。我们推的比用户真实点击**更贴历史**(荐3>target1) → **模型偏保守/用户更爱探索**。

### #125 — 类目错·(a)大类都不对 · BEAM坍缩(<a_202×10/10)
- **历史**(6项; 平台 ?×3,PS4×2,XboxOne×1): Far Cry Primal - PlayStati… | Logitech G610 Orion Brown … | Logitech G900 Chaos Spectr… | PDP NFL Official Face-Off … | CORSAIR Scimitar Pro RGB -… | Watch Dogs 2 - PlayStation…
- **GT**: `<a_86><b_12><c_93>` South Park: The Fractured but Whole - PlayStat… _(平台 PS4)_ ｜ **native**: `<a_202><b_253><c_113>` CORSAIR Sabre - RGB Gaming Mou… ✗
- **beam top5**: `<a_202><b_58><c_107>`?, `<a_202><b_253><c_113>`?, `<a_202><b_253><c_105>`?, `<a_202><b_58><c_105>`?, `<a_202><b_3><c_27>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_202 家族 10/10）；unique(a,b)=8/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/6（覆盖67%），锚定: Logitech G610 Orion Br…, Logitech G900 Chaos Sp…, Watch Dogs 2 - PlaySta…；新候选=0（**纯复述历史**）；模板开头；genre: action,immersive,narrative。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=子类延续(score3)。我们推的比用户真实点击**更贴历史**(荐3>target1) → **模型偏保守/用户更爱探索**。

### #126 — 类目错·(a)大类都不对
- **历史**(5项; 平台 ?×2,XboxOne×1,PS4×1): Tom Clancy's Rainbow Six S… | Sega Genesis Core System 2… | Forza Horizon 2 for Xbox O… | Homefront: The Revolution … | Pok&eacute;mon Sun - Ninte…
- **GT**: `<a_194><b_36><c_254>` Final Fantasy XV - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_211><b_159><c_123>` Pok&eacute;mon Moon - Nintendo… ✗
- **beam top5**: `<a_211><b_159><c_123>`3DS, `<a_123><b_58><c_16>`Xbo, `<a_123><b_100><c_0>`Xbo, `<a_123><b_228><c_139>`Xbo, `<a_123><b_188><c_70>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS4 vs 荐=3DS)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/5（覆盖80%），锚定: Tom Clancy's Rainbow S…, Homefront: The Revolut…, Forza Horizon 2 for Xb…；新候选=0（**纯复述历史**）；模板开头；genre: action,strategy,immersive。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=子类延续(score3)。我们推的比用户真实点击**更贴历史**(荐3>target1) → **模型偏保守/用户更爱探索**。

### #127 — 类目错·(a)大类都不对 · BEAM坍缩(<a_195×9/10)
- **历史**(1项; 平台 GameBoy×1): Pokemon Ruby Version - Gam…
- **GT**: `<a_8><b_170><c_114>` Generic AC Adapter for Nintendo DS and Game Bo… _(平台 DS)_ ｜ **native**: `<a_195><b_241><c_186>` Nintendo Game Boy Advance SP -… ✗
- **beam top5**: `<a_195><b_223><c_246>`?, `<a_195><b_223><c_49>`?, `<a_195><b_244><c_242>`?, `<a_195><b_241><c_186>`Gam, `<a_211><b_255><c_20>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_195 家族 9/10）；unique(a,b)=5/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 1/1（覆盖100%），锚定: Pokemon Ruby Version -…；新候选=0（**纯复述历史**）；genre: action,adventure,role-playing。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['advance']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #128 — 类目错·(a)大类都不对
- **历史**(2项; 平台 GameBoy×1,DS×1): Pokemon Ruby Version - Gam… | Generic AC Adapter for Nin…
- **GT**: `<a_175><b_179><c_0>` Nintendo DS Lite Onyx Black _(平台 DS)_ ｜ **native**: `<a_195><b_241><c_186>` Nintendo Game Boy Advance SP -… ✗
- **beam top5**: `<a_219><b_150><c_56>`Gam, `<a_113><b_104><c_28>`3DS, `<a_195><b_244><c_242>`?, `<a_195><b_241><c_186>`Gam, `<a_219><b_81><c_183>`Gam
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=DS vs 荐=GameBoy)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=9/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: Pokemon Ruby Version -…, Generic AC Adapter for…；新候选=0（**纯复述历史**）；模板开头；genre: action,immersive,nostalg。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。

### #129 — 类目对·item错
- **历史**(3项; 平台 DS×2,GameBoy×1): Pokemon Ruby Version - Gam… | Generic AC Adapter for Nin… | Nintendo DS Lite Onyx Blac…
- **GT**: `<a_113><b_9><c_133>` Gamecube Controller For Nintendo White _(平台 GameCube)_ ｜ **native**: `<a_195><b_241><c_186>` Nintendo Game Boy Advance SP -… ✗
- **beam top5**: `<a_219><b_150><c_56>`Gam, `<a_195><b_241><c_186>`Gam, `<a_219><b_170><c_180>`Gam, `<a_195><b_4><c_218>`?, `<a_195><b_244><c_242>`?
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台错配(GT=GameCube vs 荐=GameBoy)；beam中 share-a=1/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=10/10，平台数=5，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Pokemon Ruby Version -…, Nintendo DS Lite Onyx …, Generic AC Adapter for…；新候选=0（**纯复述历史**）；genre: immersive,nostalg,retro。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=漂移(平台/词面关联)(score1)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #130 — 命中·复购/同款易例 · BEAM坍缩(<a_219×7/10)
- **历史**(4项; 平台 DS×2,GameBoy×1,GameCube×1): Pokemon Ruby Version - Gam… | Generic AC Adapter for Nin… | Nintendo DS Lite Onyx Blac… | Gamecube Controller For Ni…
- **GT**: `<a_113><b_9><c_133>` Gamecube Controller For Nintendo White _(平台 GameCube)_ ｜ **native**: `<a_113><b_9><c_133>` Gamecube Controller For Ninten… ✓
- **beam top5**: `<a_113><b_9><c_133>`Gam, `<a_113><b_9><c_194>`Wii, `<a_113><b_9><c_63>`Wii, `<a_219><b_235><c_104>`3DS, `<a_219><b_150><c_56>`Gam
- **推荐↔GT差距**: top-1 完全命中。
- **beam多样性**: **低**（坍缩到 <a_219 家族 7/10）；unique(a,b)=8/10，平台数=6，unique标题=10/10。
- **reasoning质量**: 引用历史 3/4（覆盖75%），锚定: Pokemon Ruby Version -…, Generic AC Adapter for…, Gamecube Controller Fo…；新候选=0（**纯复述历史**）；模板开头；genre: action,role-playing,immersive。
- **target合理性(天花板)**: target=子类延续(score3); 我们pred[0]=子类延续(score3)。target 是合理的子类延续，且**已命中**。

### #131 — 类目错·(a)大类都不对 · BEAM坍缩(<a_113×7/10)
- **历史**(5项; 平台 DS×2,GameCube×2,GameBoy×1): Pokemon Ruby Version - Gam… | Generic AC Adapter for Nin… | Nintendo DS Lite Onyx Blac… | Gamecube Controller For Ni… | Gamecube Controller For Ni…
- **GT**: `<a_193><b_217><c_145>` Sonic and the Secret Rings - Nintendo Wii _(平台 Wii)_ ｜ **native**: `<a_113><b_9><c_133>` Gamecube Controller For Ninten… ✗
- **beam top5**: `<a_219><b_235><c_104>`3DS, `<a_113><b_9><c_63>`Wii, `<a_113><b_9><c_133>`Gam, `<a_113><b_127><c_139>`?, `<a_113><b_235><c_28>`3DS
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=Wii vs 荐=3DS)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_113 家族 7/10）；unique(a,b)=7/10，平台数=5，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Pokemon Ruby Version -…, Nintendo DS Lite Onyx …, Gamecube Controller Fo…；新候选=0（**纯复述历史**）；genre: action,multiplayer,nostalg。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=漂移(平台/词面关联)(score1)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #132 — 类目错·(a)大类都不对
- **历史**(6项; 平台 DS×2,GameCube×2,GameBoy×1): Pokemon Ruby Version - Gam… | Generic AC Adapter for Nin… | Nintendo DS Lite Onyx Blac… | Gamecube Controller For Ni… | Gamecube Controller For Ni… | Sonic and the Secret Rings…
- **GT**: `<a_195><b_6><c_156>` Harvest Moon: Tree of Tranquility - Nintendo W… _(平台 Wii)_ ｜ **native**: `<a_193><b_153><c_247>` Sonic and the Black Knight - N… ✗
- **beam top5**: `<a_219><b_235><c_104>`3DS, `<a_193><b_40><c_61>`Xbo, `<a_113><b_35><c_8>`Gam, `<a_193><b_153><c_247>`Wii, `<a_113><b_127><c_139>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=Wii vs 荐=3DS)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=6/10，平台数=7，unique标题=10/10。
- **reasoning质量**: 引用历史 4/5（覆盖80%），锚定: Pokemon Ruby Version -…, Generic AC Adapter for…, Gamecube Controller Fo…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=漂移(平台/词面关联)(score1)。用户点击比我们top1**更贴历史**(target2>荐1) → 我们把可命中的延续**跑偏**了。

### #133 — 类目错·(a)大类都不对 · BEAM坍缩(<a_49×10/10)
- **历史**(9项; 平台 PS4×4,?×3,PS3×2): PlayStation 3 40GB System | PlayStation 3 40GB System | Pokemon X | Disney Infinity:Star Wars … | Disney Infinity 3.0 Editio… | Disney Infinity 3.0: The F…
- **GT**: `<a_189><b_201><c_57>` PlayStation 4 Camera (Old Model) _(平台 PS4)_ ｜ **native**: `<a_49><b_110><c_219>` Disney Infinity 3.0 Edition: S… ✗
- **beam top5**: `<a_49><b_110><c_219>`?, `<a_49><b_137><c_187>`?, `<a_49><b_146><c_81>`?, `<a_49><b_234><c_73>`?, `<a_49><b_125><c_112>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_49 家族 10/10）；unique(a,b)=10/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 3/8（覆盖38%），锚定: PowerA DualShock 4 Cha…, PlayStation 4 500GB Co…, PlayStation 3 40GB Sys…；新候选=0（**纯复述历史**）；模板开头；genre: action,immersive,narrative。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。

### #134 — 类目错·(a)大类都不对
- **历史**(10项; 平台 PS4×5,?×3,PS3×2): PlayStation 3 40GB System | Pokemon X | Disney Infinity:Star Wars … | Disney Infinity 3.0 Editio… | Disney Infinity 3.0: The F… | PlayStation 4 Camera (Old …
- **GT**: `<a_39><b_182><c_73>` Call of Duty: Black Ops III - Standard Edition… _(平台 Xbox360)_ ｜ **native**: `<a_49><b_119><c_5>` Disney Infinity 3.0 Edition: S… ✗
- **beam top5**: `<a_61><b_251><c_3>`PS4, `<a_201><b_31><c_107>`PS4, `<a_61><b_251><c_51>`PS4, `<a_49><b_110><c_219>`?, `<a_189><b_236><c_135>`PS
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=Xbox360 vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=8/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 6/9（覆盖67%），锚定: PowerA DualShock 4 Cha…, PlayStation 4 500GB Co…, PlayStation 3 40GB Sys…；新候选=0（**纯复述历史**）；模板开头；genre: action,immersive,narrative。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=漂移(平台/词面关联)(score1)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #135 — 类目错·(a)大类都不对 · BEAM坍缩(<a_49×8/10)
- **历史**(10项; 平台 PS4×4,?×3,PS3×2): Pokemon X | Disney Infinity:Star Wars … | Disney Infinity 3.0 Editio… | Disney Infinity 3.0: The F… | PlayStation 4 Camera (Old … | Call of Duty: Black Ops II…
- **GT**: `<a_61><b_214><c_239>` HDE Media Remote Control for Microsoft Xbox On… _(平台 XboxOne)_ ｜ **native**: `<a_49><b_234><c_73>` Disney Infinity 3.0 Edition: S… ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_49><b_110><c_219>`?, `<a_49><b_48><c_91>`?, `<a_49><b_137><c_187>`?, `<a_49><b_234><c_73>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=XboxOne vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_49 家族 8/10）；unique(a,b)=9/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 6/9（覆盖67%），锚定: PlayStation 4 Universa…, PlayStation 4 500GB Co…, PlayStation 3 40GB Sys…；新候选=0（**纯复述历史**）；模板开头；genre: action,adventure,immersive。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['media', 'remote']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #136 — 类目对·item错
- **历史**(10项; 平台 PS4×4,XboxOne×2,PS3×1): Robot amiibo - Japan Impor… | Samurai Warriors 4-II - Pl… | Doom: Collector's Edition … | Xbox One Stereo Headset Ad… | Doom - Xbox One | NieR: Automata - Playstati…
- **GT**: `<a_123><b_1><c_232>` Zombie Army Trilogy - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_1><b_150><c_189>` Legend of Heroes: Trails of Co… ✗
- **beam top5**: `<a_121><b_76><c_208>`PS4, `<a_1><b_25><c_254>`3DS, `<a_1><b_150><c_189>`PS3, `<a_121><b_91><c_244>`PS4, `<a_121><b_146><c_26>`PS3
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=9/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 6/10（覆盖60%），锚定: Samurai Warriors 4-II …, Doom: Collector's Edit…, Shovel Knight Amiibo -…；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,fighting。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #137 — 类目对·item错
- **历史**(10项; 平台 PS4×5,XboxOne×2,3DS×1): Samurai Warriors 4-II - Pl… | Doom: Collector's Edition … | Xbox One Stereo Headset Ad… | Doom - Xbox One | NieR: Automata - Playstati… | Zombie Army Trilogy - Play…
- **GT**: `<a_24><b_96><c_27>` Rise of the Tomb Raider: 20 Year Celebration -… _(平台 PS4)_ ｜ **native**: `<a_131><b_224><c_68>` Overwatch - Origins Edition - … ✗
- **beam top5**: `<a_162><b_125><c_53>`?, `<a_123><b_171><c_243>`PS4, `<a_24><b_129><c_173>`PS4, `<a_24><b_185><c_47>`Xbo, `<a_131><b_224><c_82>`Xbo
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；beam中 share-a=2/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=8/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 6/10（覆盖60%），锚定: Guilty Gear Xrd SIGN L…, Samurai Warriors 4-II …, Shovel Knight Amiibo -…；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,fighting。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #138 — 命中@4
- **历史**(10项; 平台 PS4×5,XboxOne×2,3DS×1): Doom: Collector's Edition … | Xbox One Stereo Headset Ad… | Doom - Xbox One | NieR: Automata - Playstati… | Zombie Army Trilogy - Play… | Rise of the Tomb Raider: 2…
- **GT**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - PS4 Digital Code _(平台 PS4)_ ｜ **native**: `<a_24><b_185><c_47>` ReCore - Xbox One ✗
- **beam top5**: `<a_24><b_185><c_47>`Xbo, `<a_24><b_129><c_173>`PS4, `<a_24><b_72><c_142>`PS4, `<a_123><b_58><c_78>`PS4, `<a_1><b_43><c_207>`PS4
- **推荐↔GT差距**: 正确项在 beam 第4位，pred[0] 前缀深度仅 0/3；平台错配(GT=PS4 vs 荐=XboxOne)；beam中 share-a=3/10, share-(a,b)=1/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=10/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 3/10（覆盖30%），锚定: Samurai Warriors 4-II …, Doom: Collector's Edit…, NieR: Automata - Plays…；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,shooter。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。target 是合理的大类延续，且**已命中**。

### #139 — 类目错·(a)大类都不对 · BEAM坍缩(<a_123×7/10)
- **历史**(10项; 平台 PS4×6,XboxOne×2,WiiU×1): Xbox One Stereo Headset Ad… | Doom - Xbox One | NieR: Automata - Playstati… | Zombie Army Trilogy - Play… | Rise of the Tomb Raider: 2… | Resident Evil 7: Biohazard…
- **GT**: `<a_175><b_216><c_18>` Ultimate Marvel vs Capcom 3 - PlayStation Vita _(平台 PSVita)_ ｜ **native**: `<a_123><b_58><c_16>` Resident Evil 7 Biohazard - Xb… ✗
- **beam top5**: `<a_123><b_58><c_16>`Xbo, `<a_24><b_185><c_47>`Xbo, `<a_24><b_129><c_173>`PS4, `<a_123><b_78><c_71>`PS4, `<a_123><b_33><c_93>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PSVita vs 荐=XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_123 家族 7/10）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 7/10（覆盖70%），锚定: Samurai Warriors 4-II …, Doom: Collector's Edit…, Doom - Xbox One；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,shooter。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=子类延续(score3)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #140 — 类目对·item错
- **历史**(10项; 平台 PS4×6,XboxOne×2,?×1): Doom - Xbox One | NieR: Automata - Playstati… | Zombie Army Trilogy - Play… | Rise of the Tomb Raider: 2… | Resident Evil 7: Biohazard… | Ultimate Marvel vs Capcom …
- **GT**: `<a_131><b_41><c_74>` Doom: Collector's Edition - Xbox One _(平台 XboxOne)_ ｜ **native**: `<a_123><b_58><c_16>` Resident Evil 7 Biohazard - Xb… ✗
- **beam top5**: `<a_123><b_58><c_16>`Xbo, `<a_24><b_129><c_173>`PS4, `<a_24><b_185><c_47>`Xbo, `<a_24><b_72><c_142>`PS4, `<a_123><b_33><c_93>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 6/10（覆盖60%），锚定: Samurai Warriors 4-II …, Doom - Xbox One, Doom: Collector's Edit…；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,shooter。
- **target合理性(天花板)**: target=子类延续(score3); 我们pred[0]=子类延续(score3)。关联档位相同(score3)但选错具体 item。 注意 target 与历史共享词 ["collector's", 'doom']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #141 — 类目对·item错
- **历史**(10项; 平台 PS4×4,XboxOne×4,?×1): 7 Days to Die - Xbox One | Xbox One S 500GB Console -… | Call Of Duty: Infinite War… | Playstation Plus: 3 Month … | Call of Duty: Infinite War… | Zacro 13ft PS4 Controller …
- **GT**: `<a_201><b_213><c_242>` The Last of Us Remastered - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_39><b_77><c_105>` Call of Duty: Infinite Warfare… ✗
- **beam top5**: `<a_39><b_77><c_105>`Xbo, `<a_123><b_58><c_16>`Xbo, `<a_123><b_58><c_78>`PS4, `<a_61><b_251><c_144>`PS4, `<a_123><b_100><c_0>`Xbo
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台错配(GT=PS4 vs 荐=XboxOne)；beam中 share-a=1/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=8/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 6/10（覆盖60%），锚定: Call of Duty: Ghosts -…, Call Of Duty: Infinite…, Xbox One Wireless Cont…；新候选=0（**纯复述历史**）；模板开头；genre: action,shooter,multiplayer。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=漂移(平台/词面关联)(score1)。用户点击比我们top1**更贴历史**(target2>荐1) → 我们把可命中的延续**跑偏**了。

### #142 — 类目对·item错 · BEAM坍缩(<a_39×8/10)
- **历史**(10项; 平台 ?×3,PS4×2,3DS×2): Wii Remote Plus - Black | Nintendo Nunchuk Controlle… | Nintendo Wii U Pro Control… | Mega Man Legacy Collection… | The King of Fighters XIV: … | Halo 5: Guardians
- **GT**: `<a_7><b_36><c_217>` Xbox One X 1TB Limited Edition Console - Proje… _(平台 XboxOne)_ ｜ **native**: `<a_39><b_77><c_105>` Call of Duty: Infinite Warfare… ✗
- **beam top5**: `<a_39><b_77><c_105>`Xbo, `<a_39><b_175><c_240>`Xbo, `<a_39><b_69><c_69>`Xbo, `<a_7><b_248><c_176>`Xbo, `<a_39><b_51><c_21>`Xbo
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台一致(XboxOne)；beam中 share-a=1/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_39 家族 8/10）；unique(a,b)=9/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 5/10（覆盖50%），锚定: Street Fighter V - Pla…, The King of Fighters X…, Halo 5: Guardians；新候选=0（**纯复述历史**）；模板开头；genre: action,adventure,fighting。
- **target合理性(天花板)**: target=子类延续(score3); 我们pred[0]=大类延续(score2)。用户点击比我们top1**更贴历史**(target3>荐2) → 我们把可命中的延续**跑偏**了。 注意 target 与历史共享词 ['discontinued']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #143 — 类目错·(a)大类都不对
- **历史**(2项; 平台 XboxOne×2): Tom Clancy&rsquo;s Ghost R… | Dishonored 2 - Xbox One
- **GT**: `<a_113><b_4><c_80>` Zettaguard New Classic Pro Controller Console … _(平台 Wii)_ ｜ **native**: `<a_194><b_15><c_66>` Dishonored 2 - PlayStation 4 ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_201><b_213><c_242>`PS4, `<a_194><b_15><c_9>`PS4, `<a_194><b_15><c_66>`PS4, `<a_123><b_58><c_78>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=Wii vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=9/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: Tom Clancy&rsquo;s Gho…, Dishonored 2 - Xbox On…；新候选=0（**纯复述历史**）；模板开头；genre: action,role-playing,immersive。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=探索(无关联)(score0)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #144 — 类目错·(a)大类都不对
- **历史**(3项; 平台 XboxOne×2,Wii×1): Tom Clancy&rsquo;s Ghost R… | Dishonored 2 - Xbox One | Zettaguard New Classic Pro…
- **GT**: `<a_140><b_69><c_39>` Watch Dogs xbox one _(平台 XboxOne)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_194><b_15><c_66>`PS4, `<a_123><b_44><c_0>`PS4, `<a_123><b_58><c_78>`PS4, `<a_194><b_15><c_9>`PS4, `<a_123><b_142><c_36>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=XboxOne vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=9/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Tom Clancy&rsquo;s Gho…, Dishonored 2 - Xbox On…, Zettaguard New Classic…；新候选=0（**纯复述历史**）；模板开头；genre: action,role-playing,immersive。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=子类延续(score3)。我们推的比用户真实点击**更贴历史**(荐3>target1) → **模型偏保守/用户更爱探索**。

### #145 — 类目错·(a)大类都不对
- **历史**(4项; 平台 XboxOne×3,Wii×1): Tom Clancy&rsquo;s Ghost R… | Dishonored 2 - Xbox One | Zettaguard New Classic Pro… | Watch Dogs xbox one
- **GT**: `<a_84><b_54><c_87>` Nintendo Wii U 32GB Mario Kart 8 (Pre-Installe… _(平台 WiiU)_ ｜ **native**: `<a_131><b_155><c_206>` Fallout 4 - Xbox One ✗
- **beam top5**: `<a_131><b_155><c_206>`Xbo, `<a_123><b_76><c_255>`Xbo, `<a_123><b_58><c_16>`Xbo, `<a_191><b_187><c_236>`Xbo, `<a_131><b_210><c_0>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=WiiU vs 荐=XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=8/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Tom Clancy&rsquo;s Gho…, Dishonored 2 - Xbox On…, Watch Dogs xbox one；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=漂移(平台/词面关联)(score1)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #146 — 类目错·(a)大类都不对
- **历史**(5项; 平台 XboxOne×3,Wii×1,WiiU×1): Tom Clancy&rsquo;s Ghost R… | Dishonored 2 - Xbox One | Zettaguard New Classic Pro… | Watch Dogs xbox one | Nintendo Wii U 32GB Mario …
- **GT**: `<a_39><b_251><c_254>` Titanfall - Xbox 360 _(平台 Xbox360)_ ｜ **native**: `<a_131><b_155><c_206>` Fallout 4 - Xbox One ✗
- **beam top5**: `<a_131><b_155><c_206>`Xbo, `<a_131><b_210><c_0>`PS4, `<a_123><b_171><c_44>`Xbo, `<a_131><b_224><c_16>`PC, `<a_191><b_10><c_19>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=Xbox360 vs 荐=XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=6/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 4/5（覆盖80%），锚定: Tom Clancy&rsquo;s Gho…, Dishonored 2 - Xbox On…, Watch Dogs xbox one；新候选=0（**纯复述历史**）；模板开头；genre: action,role-playing,multiplayer。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=漂移(平台/词面关联)(score1)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #147 — 类目错·(a)大类都不对 · BEAM坍缩(<a_39×7/10)
- **历史**(3项; 平台 PS4×2,PC×1): Final Fantasy XV - PlaySta… | The Last of Us Remastered … | Tom Clancy's Rainbow Six S…
- **GT**: `<a_201><b_151><c_255>` Playstation Plus: 3 Month Membership [Digital … _(平台 PS-generic)_ ｜ **native**: `<a_39><b_156><c_118>` Tom Clancy's Rainbow Six Siege… ✗
- **beam top5**: `<a_39><b_69><c_69>`Xbo, `<a_39><b_77><c_105>`Xbo, `<a_39><b_156><c_118>`Xbo, `<a_39><b_51><c_254>`PC, `<a_123><b_76><c_232>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS-generic vs 荐=XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_39 家族 7/10）；unique(a,b)=8/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Final Fantasy XV - Pla…, The Last of Us Remaste…, Tom Clancy's Rainbow S…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。

### #148 — 类目错·(a)大类都不对
- **历史**(4项; 平台 PS4×2,PC×1,PS×1): Final Fantasy XV - PlaySta… | The Last of Us Remastered … | Tom Clancy's Rainbow Six S… | Playstation Plus: 3 Month …
- **GT**: `<a_201><b_78><c_157>` inFAMOUS: Second Son Standard Edition (PlaySta… _(平台 PS4)_ ｜ **native**: `<a_39><b_156><c_118>` Tom Clancy's Rainbow Six Siege… ✗
- **beam top5**: `<a_39><b_69><c_69>`Xbo, `<a_39><b_77><c_105>`Xbo, `<a_39><b_51><c_21>`Xbo, `<a_39><b_182><c_247>`PS4, `<a_39><b_151><c_9>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS4 vs 荐=XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=10/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Final Fantasy XV - Pla…, The Last of Us Remaste…, Tom Clancy's Rainbow S…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。

### #149 — 类目错·(a)大类都不对
- **历史**(5项; 平台 PS4×3,PC×1,PS×1): Final Fantasy XV - PlaySta… | The Last of Us Remastered … | Tom Clancy's Rainbow Six S… | Playstation Plus: 3 Month … | inFAMOUS: Second Son Stand…
- **GT**: `<a_61><b_40><c_177>` Microsoft Xbox 360 Wired Controller for Window… _(平台 Xbox360)_ ｜ **native**: `<a_123><b_76><c_232>` Far Cry Primal - PlayStation 4… ✗
- **beam top5**: `<a_131><b_210><c_0>`PS4, `<a_201><b_31><c_107>`PS4, `<a_123><b_72><c_7>`PS4, `<a_123><b_129><c_247>`PS4, `<a_39><b_69><c_69>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=Xbox360 vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=10/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 5/5（覆盖100%），锚定: Final Fantasy XV - Pla…, The Last of Us Remaste…, Tom Clancy's Rainbow S…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=漂移(平台/词面关联)(score1)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #150 — 类目对·item错
- **历史**(6项; 平台 PS4×3,PC×1,PS×1): Final Fantasy XV - PlaySta… | The Last of Us Remastered … | Tom Clancy's Rainbow Six S… | Playstation Plus: 3 Month … | inFAMOUS: Second Son Stand… | Microsoft Xbox 360 Wired C…
- **GT**: `<a_39><b_78><c_54>` Battlefield 1 - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_39><b_156><c_118>` Tom Clancy's Rainbow Six Siege… ✗
- **beam top5**: `<a_61><b_53><c_46>`Xbo, `<a_39><b_69><c_69>`Xbo, `<a_61><b_167><c_164>`Xbo, `<a_61><b_53><c_5>`Xbo, `<a_39><b_156><c_118>`Xbo
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台错配(GT=PS4 vs 荐=XboxOne)；beam中 share-a=4/10, share-(a,b)=0/10。
- **beam多样性**: **中**（2 个 a 大类）；unique(a,b)=8/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 5/6（覆盖83%），锚定: Final Fantasy XV - Pla…, The Last of Us Remaste…, Tom Clancy's Rainbow S…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。

### #151 — 类目对·item错
- **历史**(4项; 平台 PS4×3,PS3×1): Fallout: New Vegas Ultimat… | Tomb Raider: Definitive Ed… | Wolfenstein: The Old Blood… | Street Fighter V - PlaySta…
- **GT**: `<a_208><b_146><c_3>` Onechanbara Z2: Chaos - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_208><b_175><c_24>` Street Fighter V - Collector's… ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_208><b_175><c_24>`PS4, `<a_194><b_87><c_249>`PS4, `<a_131><b_210><c_0>`PS4, `<a_208><b_32><c_26>`PS4
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台一致(PS4)；beam中 share-a=4/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=8/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Fallout: New Vegas Ult…, Tomb Raider: Definitiv…, Wolfenstein: The Old B…；新候选=0（**纯复述历史**）；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=漂移(平台/词面关联)(score1)。用户点击比我们top1**更贴历史**(target2>荐1) → 我们把可命中的延续**跑偏**了。

### #152 — 类目对·item错
- **历史**(7项; 平台 ?×5,PC×2): The Sims 3 Seasons | The Sims 3: Master Suite S… | The Sims 3: Showtime - PC/… | The Sims 4 Luxury Party St… | The Sims 4 - Romantic Gard… | The Sims 4 Outdoor Retreat…
- **GT**: `<a_22><b_126><c_226>` The Sims 4 Get to Work _(平台 ?)_ ｜ **native**: `<a_22><b_89><c_201>` The Sims 4 Cool Kitchen Stuff … ✗
- **beam top5**: `<a_22><b_89><c_201>`?, `<a_22><b_173><c_203>`?, `<a_22><b_88><c_75>`PC, `<a_195><b_84><c_111>`PC, `<a_195><b_69><c_235>`?
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；beam中 share-a=5/10, share-(a,b)=0/10。
- **beam多样性**: **中**（2 个 a 大类）；unique(a,b)=5/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 5/7（覆盖71%），锚定: The Sims 3 Starter Pac…, The Sims 3 Seasons, The Sims 3: Master Sui…；新候选=0（**纯复述历史**）；模板开头；genre: action,immersive。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。 注意 target 与历史共享词 ['sims']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #153 — 类目错·(a)大类都不对 · BEAM坍缩(<a_123×10/10)
- **历史**(4项; 平台 PS4×4): Rise of the Tomb Raider: 2… | Resident Evil Origins Coll… | Resident Evil 5 - Standard… | Resident Evil 4 - PlayStat…
- **GT**: `<a_194><b_242><c_173>` Lightning Returns: Final Fantasy XIII _(平台 ?)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_123><b_58><c_78>`PS4, `<a_123><b_160><c_188>`PS4, `<a_123><b_188><c_192>`PS4, `<a_123><b_33><c_93>`PS4, `<a_123><b_171><c_243>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_123 家族 10/10）；unique(a,b)=8/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Rise of the Tomb Raide…, Resident Evil Origins …, Resident Evil 5 - Stan…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #154 — 类目对·item错 · BEAM坍缩(<a_123×7/10)
- **历史**(5项; 平台 PS4×4,?×1): Rise of the Tomb Raider: 2… | Resident Evil Origins Coll… | Resident Evil 5 - Standard… | Resident Evil 4 - PlayStat… | Lightning Returns: Final F…
- **GT**: `<a_194><b_36><c_254>` Final Fantasy XV - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_123><b_78><c_71>` Resident Evil 4 - PlayStation … ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_24><b_129><c_173>`PS4, `<a_24><b_72><c_142>`PS4, `<a_123><b_58><c_78>`PS4, `<a_123><b_171><c_243>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_123 家族 7/10）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/5（覆盖80%），锚定: Rise of the Tomb Raide…, Resident Evil Origins …, Resident Evil 4 - Play…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。 注意 target 与历史共享词 ['fantasy', 'final']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #155 — 类目错·(a)大类都不对
- **历史**(6项; 平台 PS4×5,?×1): Rise of the Tomb Raider: 2… | Resident Evil Origins Coll… | Resident Evil 5 - Standard… | Resident Evil 4 - PlayStat… | Lightning Returns: Final F… | Final Fantasy XV - PlaySta…
- **GT**: `<a_92><b_18><c_43>` Final Fantasy XIII - Playstation 3 _(平台 PS3)_ ｜ **native**: `<a_194><b_15><c_66>` Dishonored 2 - PlayStation 4 ✗
- **beam top5**: `<a_194><b_215><c_154>`?, `<a_24><b_72><c_142>`PS4, `<a_194><b_15><c_66>`PS4, `<a_194><b_87><c_112>`PS4, `<a_194><b_87><c_249>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=7/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 6/6（覆盖100%），锚定: Rise of the Tomb Raide…, Resident Evil Origins …, Lightning Returns: Fin…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['fantasy', 'final', 'xiii']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #156 — 类目错·(a)大类都不对
- **历史**(7项; 平台 PS4×5,?×1,PS3×1): Resident Evil Origins Coll… | Resident Evil 5 - Standard… | Resident Evil 4 - PlayStat… | Lightning Returns: Final F… | Final Fantasy XV - PlaySta… | Final Fantasy XIII - Plays…
- **GT**: `<a_10><b_120><c_54>` Dragon Age Origins: Ultimate Edition - Playsta… _(平台 PS3)_ ｜ **native**: `<a_194><b_87><c_112>` Dark Souls III - PlayStation 4… ✗
- **beam top5**: `<a_194><b_215><c_154>`?, `<a_194><b_87><c_112>`PS4, `<a_194><b_87><c_249>`PS4, `<a_194><b_15><c_66>`PS4, `<a_24><b_72><c_142>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=7/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 6/7（覆盖86%），锚定: Rise of the Tomb Raide…, Resident Evil Origins …, Lightning Returns: Fin…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['origins']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #157 — 类目错·(a)大类都不对 · BEAM坍缩(<a_202×10/10)
- **历史**(4项; 平台 ?×3,Switch×1): Razer Naga Epic Chroma MMO… | Razer Diamondback - Chroma… | Razer Blackwidow Ultimate … | Razer DeathAdder Expert - …
- **GT**: `<a_205><b_208><c_148>` Gran Turismo Sport - Limited Edition - PlaySta… _(平台 PS4)_ ｜ **native**: `<a_202><b_16><c_110>` Razer DeathAdder Expert - Opti… ✗
- **beam top5**: `<a_202><b_58><c_107>`?, `<a_202><b_58><c_57>`?, `<a_202><b_58><c_122>`?, `<a_202><b_113><c_73>`?, `<a_202><b_120><c_89>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_202 家族 10/10）；unique(a,b)=6/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 3/4（覆盖75%），锚定: Razer Naga Epic Chroma…, Razer Diamondback - Ch…, Razer DeathAdder Exper…；新候选=0（**纯复述历史**）；模板开头；genre: action,peripheral,accessor。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #158 — 类目错·(a)大类都不对 · BEAM坍缩(<a_202×7/10)
- **历史**(3项; 平台 Switch×1,PS4×1,?×1): Razer BlackWidow Chroma: C… | Razer Kraken Pro Analog Ga… | Steam Controller
- **GT**: `<a_8><b_173><c_201>` dreamGEAR- Playstation 4 Charge and Play Premi… _(平台 PS4)_ ｜ **native**: `<a_202><b_11><c_246>` Razer Naga Epic Chroma MMO Gam… ✗
- **beam top5**: `<a_202><b_11><c_246>`?, `<a_202><b_58><c_57>`?, `<a_202><b_120><c_89>`?, `<a_202><b_16><c_110>`?, `<a_202><b_3><c_27>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_202 家族 7/10）；unique(a,b)=10/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Razer BlackWidow Chrom…, Razer Kraken Pro Analo…, Steam Controller；新候选=0（**纯复述历史**）；模板开头；genre: action,immersive,peripheral。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #159 — 类目错·(a)大类都不对
- **历史**(4项; 平台 PS4×2,Switch×1,?×1): Razer BlackWidow Chroma: C… | Razer Kraken Pro Analog Ga… | Steam Controller | dreamGEAR- Playstation 4 C…
- **GT**: `<a_89><b_134><c_152>` Star Wars: The Old Republic - 14,500 Cartel Co… _(平台 ?)_ ｜ **native**: `<a_202><b_11><c_246>` Razer Naga Epic Chroma MMO Gam… ✗
- **beam top5**: `<a_202><b_11><c_246>`?, `<a_61><b_251><c_144>`PS4, `<a_61><b_131><c_197>`Xbo, `<a_202><b_16><c_110>`?, `<a_202><b_113><c_73>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（2 个 a 大类）；unique(a,b)=9/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Razer BlackWidow Chrom…, Razer Kraken Pro Analo…, Steam Controller；新候选=0（**纯复述历史**）；genre: peripheral,accessor。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #160 — 类目错·(a)大类都不对 · BEAM坍缩(<a_201×7/10)
- **历史**(7项; 平台 PS4×3,Wii×2,3DS×1): Just Dance 2015 - Wii | Just Dance 2016 - Wii | The Last of Us Remastered … | Until Dawn - PlayStation 4 | Steam Controller | PlayStation 4 500GB Consol…
- **GT**: `<a_113><b_29><c_105>` HORI Nintendo Switch Pokken Tournament DX Pro … _(平台 Switch)_ ｜ **native**: `<a_201><b_169><c_181>` PlayStation 4 500GB Console - … ✗
- **beam top5**: `<a_131><b_210><c_0>`PS4, `<a_201><b_36><c_195>`PS4, `<a_201><b_169><c_181>`PS4, `<a_201><b_2><c_195>`PS4, `<a_201><b_169><c_103>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=Switch vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_201 家族 7/10）；unique(a,b)=8/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 6/7（覆盖86%），锚定: The Last of Us Remaste…, Until Dawn - PlayStati…, Just Dance 2015 - Wii；新候选=0（**纯复述历史**）；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。 注意 target 与历史共享词 ['controller', 'pokemon']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #161 — 类目对·item错
- **历史**(8项; 平台 PS4×3,Wii×2,3DS×1): Just Dance 2016 - Wii | The Last of Us Remastered … | Until Dawn - PlayStation 4 | Steam Controller | PlayStation 4 500GB Consol… | HORI Nintendo Switch Pokke…
- **GT**: `<a_113><b_152><c_199>` HORI Compact PlayStand - Zelda Edition, Offici… _(平台 Switch)_ ｜ **native**: `<a_111><b_176><c_225>` Just Dance 2016 - Xbox 360 ✗
- **beam top5**: `<a_111><b_19><c_7>`Xbo, `<a_111><b_176><c_225>`Xbo, `<a_111><b_238><c_188>`PS4, `<a_61><b_35><c_122>`PS, `<a_61><b_35><c_105>`PS4
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台错配(GT=Switch vs 荐=XboxOne)；beam中 share-a=1/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=8/10，平台数=5，unique标题=10/10。
- **reasoning质量**: 引用历史 6/8（覆盖75%），锚定: The Last of Us Remaste…, Until Dawn - PlayStati…, Just Dance 2015 - Wii；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。 注意 target 与历史共享词 ['by', 'hori', 'licensed', 'officially']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #162 — 类目对·item错 · BEAM坍缩(<a_61×7/10)
- **历史**(9项; 平台 PS4×3,Wii×2,Switch×2): The Last of Us Remastered … | Until Dawn - PlayStation 4 | Steam Controller | PlayStation 4 500GB Consol… | HORI Nintendo Switch Pokke… | HORI Compact PlayStand - Z…
- **GT**: `<a_191><b_209><c_103>` Heavy Rain and Beyond Two Souls Collection HD … _(平台 PS4)_ ｜ **native**: `<a_61><b_35><c_122>` Mad Catz Street Fighter V Arca… ✗
- **beam top5**: `<a_61><b_44><c_172>`PS4, `<a_61><b_251><c_144>`PS4, `<a_61><b_35><c_122>`PS, `<a_111><b_238><c_188>`PS4, `<a_61><b_35><c_106>`PS
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_61 家族 7/10）；unique(a,b)=8/10，平台数=5，unique标题=10/10。
- **reasoning质量**: 引用历史 6/9（覆盖67%），锚定: The Last of Us Remaste…, Until Dawn - PlayStati…, Just Dance 2015 - Wii；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['remastered']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #163 — 类目对·item错
- **历史**(9项; 平台 PS4×5,XboxOne×3,?×1): Horizon Zero Dawn - PlaySt… | Resident Evil 6 - PlayStat… | Resident Evil 7 Biohazard … | ScreamRide | Toy Soldiers: War Chest Ha… | Ratchet & Clank - PS4 [Dig…
- **GT**: `<a_111><b_176><c_131>` Just Dance 2016 - Xbox One _(平台 XboxOne)_ ｜ **native**: `<a_123><b_228><c_139>` Dead Rising 4 - Xbox One ✗
- **beam top5**: `<a_74><b_5><c_203>`Xbo, `<a_140><b_237><c_62>`PS4, `<a_86><b_18><c_29>`Xbo, `<a_123><b_228><c_139>`Xbo, `<a_74><b_218><c_206>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=9/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 6/9（覆盖67%），锚定: Final Fantasy X X-2 HD…, ReCore - Xbox One, Resident Evil 6 - Play…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #164 — 类目对·item错
- **历史**(10项; 平台 PS4×5,XboxOne×4,?×1): Resident Evil 6 - PlayStat… | Resident Evil 7 Biohazard … | ScreamRide | Toy Soldiers: War Chest Ha… | Ratchet & Clank - PS4 [Dig… | Just Dance 2016 - Xbox One
- **GT**: `<a_240><b_76><c_129>` Thief Xbox one _(平台 XboxOne)_ ｜ **native**: `<a_123><b_58><c_16>` Resident Evil 7 Biohazard - Xb… ✗
- **beam top5**: `<a_74><b_5><c_203>`Xbo, `<a_74><b_218><c_206>`PS4, `<a_123><b_171><c_44>`Xbo, `<a_123><b_78><c_71>`PS4, `<a_123><b_228><c_139>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 7/10（覆盖70%），锚定: Final Fantasy X X-2 HD…, ReCore - Xbox One, Resident Evil 6 - Play…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #165 — 类目错·(a)大类都不对 · BEAM坍缩(<a_123×10/10)
- **历史**(10项; 平台 XboxOne×5,PS4×4,?×1): Resident Evil 7 Biohazard … | ScreamRide | Toy Soldiers: War Chest Ha… | Ratchet & Clank - PS4 [Dig… | Just Dance 2016 - Xbox One | Thief Xbox one
- **GT**: `<a_106><b_169><c_144>` Tearaway Unfolded - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_123><b_228><c_139>` Dead Rising 4 - Xbox One ✗
- **beam top5**: `<a_123><b_228><c_139>`Xbo, `<a_123><b_58><c_16>`Xbo, `<a_123><b_33><c_93>`PS4, `<a_123><b_171><c_44>`Xbo, `<a_123><b_58><c_78>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS4 vs 荐=XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_123 家族 10/10）；unique(a,b)=7/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 5/10（覆盖50%），锚定: Resident Evil 6 - Play…, Resident Evil 7 Biohaz…, Just Dance 2016 - Xbox…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #166 — 类目错·(a)大类都不对
- **历史**(2项; 平台 PS4×2): WWE 2K16 - PlayStation 4 | Agents of Mayhem - PlaySta…
- **GT**: `<a_71><b_86><c_236>` UNCHARTED: The Nathan Drake Collection - PlayS… _(平台 PS4)_ ｜ **native**: `<a_208><b_25><c_47>` Dragon Ball Z: Extreme Butoden… ✗
- **beam top5**: `<a_13><b_142><c_118>`PSV, `<a_123><b_72><c_7>`PS4, `<a_201><b_31><c_107>`PS4, `<a_1><b_252><c_25>`PS4, `<a_131><b_210><c_0>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS4 vs 荐=PSVita)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（6 个不同 a 大类）；unique(a,b)=10/10，平台数=5，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: WWE 2K16 - PlayStation…, Agents of Mayhem - Pla…；新候选=0（**纯复述历史**）；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #167 — 类目对·item错
- **历史**(8项; 平台 WiiU×3,PS4×3,?×2): Hyrule Warriors - Nintendo… | Tokyo Mirage Sessions #FE … | Nintendo Wii U Console 8GB… | Dragon Age Inquisition - S… | Sleeping Dogs: Definitive … | UNCHARTED: The Nathan Drak…
- **GT**: `<a_24><b_145><c_101>` Tomb Raider: Definitive Edition - PlayStation … _(平台 PS4)_ ｜ **native**: `<a_131><b_210><c_0>` Fallout 4 - PlayStation 4 ✗
- **beam top5**: `<a_208><b_175><c_0>`PS4, `<a_131><b_210><c_0>`PS4, `<a_118><b_185><c_102>`PS4, `<a_1><b_25><c_254>`3DS, `<a_208><b_235><c_151>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=10/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 5/8（覆盖62%），锚定: The Legend of Zelda: S…, The Legend of Zelda: O…, Tokyo Mirage Sessions …；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。 注意 target 与历史共享词 ['definitive']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #168 — 类目对·item错
- **历史**(3项; 平台 PS3×3): Alice: Madness Returns - P… | Dragon Ball Xenoverse - Pl… | Insten Replacement Control…
- **GT**: `<a_249><b_129><c_134>` PlayStation 3 40GB System _(平台 PS3)_ ｜ **native**: `<a_21><b_194><c_2>` Insten Replacement Controller … ✗
- **beam top5**: `<a_21><b_194><c_2>`PS3, `<a_249><b_170><c_61>`PS, `<a_61><b_47><c_32>`PS3, `<a_21><b_138><c_81>`Gam, `<a_61><b_47><c_8>`PS3
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台一致(PS3)；beam中 share-a=3/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=9/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Alice: Madness Returns…, Dragon Ball Xenoverse …, Insten Replacement Con…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=子类延续(score3)。我们推的比用户真实点击**更贴历史**(荐3>target1) → **模型偏保守/用户更爱探索**。

### #169 — 命中@7 · RERANK伤害
- **历史**(4项; 平台 PS3×4): Alice: Madness Returns - P… | Dragon Ball Xenoverse - Pl… | Insten Replacement Control… | PlayStation 3 40GB System
- **GT**: `<a_249><b_129><c_134>` PlayStation 3 40GB System _(平台 PS3)_ ｜ **native**: `<a_249><b_129><c_134>` PlayStation 3 40GB System ✓
- **beam top5**: `<a_249><b_80><c_0>`PS2, `<a_61><b_47><c_32>`PS3, `<a_21><b_138><c_81>`Gam, `<a_249><b_129><c_157>`PS3, `<a_249><b_138><c_30>`PS
- **推荐↔GT差距**: 正确项在 beam 第7位，pred[0] 前缀深度仅 1/3；平台错配(GT=PS3 vs 荐=PS2)；beam中 share-a=5/10, share-(a,b)=2/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=8/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Alice: Madness Returns…, Dragon Ball Xenoverse …, Insten Replacement Con…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=子类延续(score3); 我们pred[0]=大类延续(score2)。target 是合理的子类延续，且**已命中**。

### #170 — 类目错·(a)大类都不对 · BEAM坍缩(<a_39×7/10)
- **历史**(9项; 平台 XboxOne×5,?×2,Xbox360×2): Dragon Ball Xenoverse - Xb… | ReCore - Xbox One | Microsoft Xbox 360 Wired C… | Battlefield 1 Early Enlist… | Killzone Mercenary | Battlefield Hardline Delux…
- **GT**: `<a_59><b_168><c_1>` Midnight Club _(平台 ?)_ ｜ **native**: `<a_39><b_77><c_105>` Call of Duty: Infinite Warfare… ✗
- **beam top5**: `<a_39><b_77><c_105>`Xbo, `<a_39><b_77><c_69>`Xbo, `<a_39><b_51><c_21>`Xbo, `<a_61><b_53><c_5>`Xbo, `<a_61><b_137><c_255>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_39 家族 7/10）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 5/9（覆盖56%），锚定: Call of Duty: Advanced…, Battlefield Hardline D…, Battlefield 1 Early En…；新候选=0（**纯复述历史**）；模板开头；genre: action,shooter,strategy。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #171 — 类目对·item错 · BEAM坍缩(<a_123×7/10)
- **历史**(10项; 平台 PS4×6,PS3×2,?×2): Mass Effect Andromeda - Pr… | Zombie Army Trilogy - Play… | Mad Max - PlayStation 4 | Saints Row IV: Re-Elected … | Far Cry Compilation | Prey - Pre-load - PS4 Digi…
- **GT**: `<a_191><b_204><c_225>` Just Cause 3 - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_123><b_100><c_33>`PS4, `<a_123><b_44><c_0>`PS4, `<a_24><b_72><c_142>`PS4, `<a_123><b_72><c_238>`PS3
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_123 家族 7/10）；unique(a,b)=10/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 5/10（覆盖50%），锚定: Deus Ex Human Revoluti…, Deus Ex: Mankind Divid…, Mass Effect Andromeda …；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #172 — 类目错·(a)大类都不对
- **历史**(3项; 平台 Xbox360×2,PS3×1): Assassin's Creed IV Black … | Xbox 360 Microsoft Authent… | Dead Rising - Xbox 360
- **GT**: `<a_89><b_210><c_218>` Guild Wars 2, Heart of Thorns - PC Guild Wars … _(平台 PC)_ ｜ **native**: `<a_39><b_204><c_1>` Battlefield 4 - Xbox 360 ✗
- **beam top5**: `<a_140><b_69><c_39>`Xbo, `<a_61><b_214><c_252>`Xbo, `<a_39><b_204><c_1>`Xbo, `<a_80><b_212><c_236>`Xbo, `<a_39><b_182><c_247>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PC vs 荐=XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=8/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Assassin's Creed IV Bl…, Dead Rising - Xbox 360, Xbox 360 Microsoft Aut…；新候选=0（**纯复述历史**）；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=探索(无关联)(score0)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #173 — 类目错·(a)大类都不对 · BEAM坍缩(<a_89×10/10)
- **历史**(4项; 平台 Xbox360×2,PS3×1,PC×1): Assassin's Creed IV Black … | Xbox 360 Microsoft Authent… | Dead Rising - Xbox 360 | Guild Wars 2, Heart of Tho…
- **GT**: `<a_157><b_178><c_201>` Snoopy's Grand Adventure - Xbox 360 _(平台 Xbox360)_ ｜ **native**: `<a_89><b_86><c_50>` World of Warcraft 60 Day Game … ✗
- **beam top5**: `<a_89><b_86><c_50>`?, `<a_89><b_210><c_218>`PC, `<a_89><b_239><c_104>`PC, `<a_89><b_86><c_158>`PC, `<a_89><b_221><c_81>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_89 家族 10/10）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Assassin's Creed IV Bl…, Dead Rising - Xbox 360, Guild Wars 2, Heart of…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #174 — 命中@2 · BEAM坍缩(<a_123×9/10)
- **历史**(2项; 平台 PS4×2): Resident Evil: Revelations… | Resident Evil 4 - PlayStat…
- **GT**: `<a_201><b_31><c_107>` Uncharted 4: A Thief's End - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_123><b_142><c_36>` 7 Days to Die - PlayStation 4 ✗
- **beam top5**: `<a_123><b_188><c_192>`PS4, `<a_201><b_31><c_107>`PS4, `<a_123><b_142><c_36>`PS4, `<a_123><b_2><c_26>`PS4, `<a_123><b_58><c_78>`PS4
- **推荐↔GT差距**: 正确项在 beam 第2位，pred[0] 前缀深度仅 0/3；平台一致(PS4)；beam中 share-a=1/10, share-(a,b)=1/10。
- **beam多样性**: **低**（坍缩到 <a_123 家族 9/10）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: Resident Evil: Revelat…, Resident Evil 4 - Play…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。target 是合理的漂移(平台/词面关联)，且**已命中**。

### #175 — 类目对·item错 · BEAM坍缩(<a_123×9/10)
- **历史**(3项; 平台 PS4×3): Resident Evil: Revelations… | Resident Evil 4 - PlayStat… | Uncharted 4: A Thief's End…
- **GT**: `<a_131><b_210><c_0>` Fallout 4 - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_123><b_58><c_78>`PS4, `<a_123><b_100><c_33>`PS4, `<a_123><b_188><c_192>`PS4, `<a_123><b_142><c_36>`PS4, `<a_201><b_213><c_242>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_123 家族 9/10）；unique(a,b)=10/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Resident Evil: Revelat…, Resident Evil 4 - Play…, Uncharted 4: A Thief's…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #176 — 类目对·item错 · BEAM坍缩(<a_123×9/10)
- **历史**(4项; 平台 PS4×4): Resident Evil: Revelations… | Resident Evil 4 - PlayStat… | Uncharted 4: A Thief's End… | Fallout 4 - PlayStation 4
- **GT**: `<a_24><b_96><c_27>` Rise of the Tomb Raider: 20 Year Celebration -… _(平台 PS4)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_123><b_100><c_33>`PS4, `<a_201><b_213><c_242>`PS4, `<a_123><b_142><c_36>`PS4, `<a_123><b_188><c_192>`PS4, `<a_123><b_58><c_78>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_123 家族 9/10）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Resident Evil: Revelat…, Resident Evil 4 - Play…, Uncharted 4: A Thief's…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #177 — 类目对·item错 · BEAM坍缩(<a_123×9/10)
- **历史**(4项; 平台 XboxOne×4): Far Cry 4 - Xbox One | The Wolf Among Us - Xbox O… | DMC Devil May Cry: Definit… | Resident Evil 5 - Standard…
- **GT**: `<a_191><b_10><c_19>` Watch Dogs 2 - Xbox One _(平台 XboxOne)_ ｜ **native**: `<a_123><b_72><c_191>` Far Cry 4 - Xbox One ✗
- **beam top5**: `<a_123><b_1><c_56>`Xbo, `<a_123><b_178><c_34>`?, `<a_123><b_145><c_171>`?, `<a_123><b_171><c_44>`Xbo, `<a_123><b_78><c_20>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_123 家族 9/10）；unique(a,b)=9/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Far Cry 4 - Xbox One, Resident Evil 5 - Stan…, The Wolf Among Us - Xb…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #178 — 类目对·item错 · BEAM坍缩(<a_162×10/10)
- **历史**(1项; 平台 ?×1): Yoshi amiibo (Super Smash …
- **GT**: `<a_162><b_148><c_47>` Zero Suit Samus amiibo - Japan Import (Super S… _(平台 ?)_ ｜ **native**: `<a_162><b_122><c_56>` Mario Modern Color Amiibo - Ja… ✗
- **beam top5**: `<a_162><b_219><c_174>`?, `<a_162><b_231><c_30>`?, `<a_162><b_218><c_126>`?, `<a_162><b_125><c_53>`?, `<a_162><b_219><c_249>`?
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；beam中 share-a=10/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_162 家族 10/10）；unique(a,b)=7/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 0/1（覆盖0%）；新候选=0（**纯复述历史**）；genre: action。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。 注意 target 与历史共享词 ['amiibo', 'bros', 'series', 'smash', 'super']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #179 — 类目对·item错 · BEAM坍缩(<a_162×8/10)
- **历史**(2项; 平台 ?×2): Yoshi amiibo (Super Smash … | Zero Suit Samus amiibo - J…
- **GT**: `<a_162><b_60><c_17>` Wolf Link Amiibo Jp Model (The Legend of Zelda… _(平台 ?)_ ｜ **native**: `<a_162><b_219><c_101>` Nintendo Super Smash Bros Palu… ✗
- **beam top5**: `<a_162><b_219><c_101>`?, `<a_162><b_219><c_233>`?, `<a_162><b_219><c_78>`?, `<a_162><b_139><c_171>`?, `<a_162><b_219><c_249>`?
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；beam中 share-a=8/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_162 家族 8/10）；unique(a,b)=5/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 0/2（覆盖0%）；新候选=0（**纯复述历史**）；genre: action,nostalg。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。 注意 target 与历史共享词 ['amiibo', 'series']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #180 — 类目对·item错 · BEAM坍缩(<a_162×10/10)
- **历史**(3项; 平台 ?×3): Yoshi amiibo (Super Smash … | Zero Suit Samus amiibo - J… | Wolf Link Amiibo Jp Model …
- **GT**: `<a_162><b_2><c_193>` Nintendo Falco Amiibo - Wii U _(平台 WiiU)_ ｜ **native**: `<a_162><b_122><c_56>` Mario Modern Color Amiibo - Ja… ✗
- **beam top5**: `<a_162><b_139><c_171>`?, `<a_162><b_219><c_233>`?, `<a_162><b_122><c_56>`?, `<a_162><b_85><c_94>`3DS, `<a_162><b_149><c_74>`3DS
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；beam中 share-a=10/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_162 家族 10/10）；unique(a,b)=8/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 0/3（覆盖0%）；新候选=0（**纯复述历史**）；genre: action。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。 注意 target 与历史共享词 ['amiibo']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #181 — 类目对·item错 · BEAM坍缩(<a_162×10/10)
- **历史**(4项; 平台 ?×3,WiiU×1): Yoshi amiibo (Super Smash … | Zero Suit Samus amiibo - J… | Wolf Link Amiibo Jp Model … | Nintendo Falco Amiibo - Wi…
- **GT**: `<a_162><b_242><c_145>` Samus amiibo - Japan Import (Super Smash Bros … _(平台 ?)_ ｜ **native**: `<a_162><b_122><c_56>` Mario Modern Color Amiibo - Ja… ✗
- **beam top5**: `<a_162><b_57><c_111>`Wii, `<a_162><b_52><c_132>`?, `<a_162><b_139><c_171>`?, `<a_162><b_122><c_56>`?, `<a_162><b_119><c_2>`?
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；beam中 share-a=10/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_162 家族 10/10）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 0/4（覆盖0%）；新候选=0（**纯复述历史**）；模板开头；genre: action,nostalg。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。 注意 target 与历史共享词 ['amiibo', 'bros', 'import', 'japan', 'samus']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #182 — 类目错·(a)大类都不对 · BEAM坍缩(<a_162×10/10)
- **历史**(5项; 平台 ?×4,WiiU×1): Yoshi amiibo (Super Smash … | Zero Suit Samus amiibo - J… | Wolf Link Amiibo Jp Model … | Nintendo Falco Amiibo - Wi… | Samus amiibo - Japan Impor…
- **GT**: `<a_250><b_12><c_83>` Mario - Gold amiibo (Super Mario Bros Series) _(平台 ?)_ ｜ **native**: `<a_162><b_219><c_78>` Pit amiibo - Japan Import (Sup… ✗
- **beam top5**: `<a_162><b_57><c_111>`Wii, `<a_162><b_219><c_233>`?, `<a_162><b_219><c_78>`?, `<a_162><b_219><c_101>`?, `<a_162><b_219><c_249>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_162 家族 10/10）；unique(a,b)=4/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 0/5（覆盖0%）；新候选=0（**纯复述历史**）；模板开头；genre: action。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['amiibo', 'bros', 'series', 'super']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #183 — 类目对·item错 · BEAM坍缩(<a_162×10/10)
- **历史**(6项; 平台 ?×5,WiiU×1): Yoshi amiibo (Super Smash … | Zero Suit Samus amiibo - J… | Wolf Link Amiibo Jp Model … | Nintendo Falco Amiibo - Wi… | Samus amiibo - Japan Impor… | Mario - Gold amiibo (Super…
- **GT**: `<a_162><b_97><c_155>` Ness amiibo (Super Smash Bros Series) _(平台 ?)_ ｜ **native**: `<a_162><b_219><c_78>` Pit amiibo - Japan Import (Sup… ✗
- **beam top5**: `<a_162><b_219><c_233>`?, `<a_162><b_57><c_111>`Wii, `<a_162><b_219><c_101>`?, `<a_162><b_219><c_78>`?, `<a_162><b_219><c_249>`?
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；beam中 share-a=10/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_162 家族 10/10）；unique(a,b)=3/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 2/6（覆盖33%），锚定: Yoshi amiibo (Super Sm…, Zero Suit Samus amiibo…；新候选=0（**纯复述历史**）；模板开头；genre: action。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。 注意 target 与历史共享词 ['amiibo', 'bros', 'series', 'smash', 'super']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #184 — 类目对·item错
- **历史**(3项; 平台 PS4×2,XboxOne×1): PlayStation 4 Universal Me… | Star Wars: Battlefront - S… | Xbox One S 2TB Console - L…
- **GT**: `<a_61><b_214><c_225>` PDP Talon Media Remote Control for Xbox One, T… _(平台 XboxOne)_ ｜ **native**: `<a_7><b_248><c_176>` Xbox One S 500GB Console - Hal… ✗
- **beam top5**: `<a_7><b_248><c_176>`Xbo, `<a_7><b_248><c_16>`Xbo, `<a_7><b_56><c_74>`Xbo, `<a_39><b_77><c_105>`Xbo, `<a_201><b_151><c_255>`PS
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=9/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: PlayStation 4 Universa…, Star Wars: Battlefront…, Xbox One S 2TB Console…；新候选=0（**纯复述历史**）；模板开头；genre: action,multiplayer,immersive。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['media', 'remote']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #185 — 近失·同(a,b)细分仅c不同
- **历史**(4项; 平台 PS4×2,XboxOne×2): PlayStation 4 Universal Me… | Star Wars: Battlefront - S… | Xbox One S 2TB Console - L… | PDP Talon Media Remote Con…
- **GT**: `<a_7><b_36><c_217>` Xbox One X 1TB Limited Edition Console - Proje… _(平台 XboxOne)_ ｜ **native**: `<a_7><b_248><c_176>` Xbox One S 500GB Console - Hal… ✗
- **beam top5**: `<a_7><b_248><c_16>`Xbo, `<a_61><b_214><c_252>`Xbo, `<a_7><b_248><c_176>`Xbo, `<a_61><b_231><c_105>`Xbo, `<a_7><b_248><c_2>`Xbo
- **推荐↔GT差距**: beam 最接近项与 GT 同 (a,b) 细分、仅 c 不同（同系列/不同款），未命中；平台一致(XboxOne)；beam中 share-a=5/10, share-(a,b)=1/10。
- **beam多样性**: **中**（2 个 a 大类）；unique(a,b)=6/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: PlayStation 4 Universa…, Star Wars: Battlefront…, Xbox One S 2TB Console…；新候选=0（**纯复述历史**）；模板开头；genre: action,immersive,accessor。
- **target合理性(天花板)**: target=子类延续(score3); 我们pred[0]=大类延续(score2)。用户点击比我们top1**更贴历史**(target3>荐2) → 我们把可命中的延续**跑偏**了。 注意 target 与历史共享词 ['discontinued']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #186 — 类目错·(a)大类都不对
- **历史**(6项; 平台 PS4×4,?×1,PS×1): WWE 2K17 - PlayStation 4 | Horizon Zero Dawn - PlaySt… | Injustice 2 - PS4 [Digital… | The Wolf Among Us - PlaySt… | Sly 2: Band of Thieves | Sly 3 Honor Among Thieves …
- **GT**: `<a_205><b_32><c_66>` TrackMania Turbo - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_239><b_115><c_84>` Sly 3 Honor Among Thieves - Pl… ✗
- **beam top5**: `<a_239><b_157><c_47>`?, `<a_74><b_218><c_91>`PS3, `<a_239><b_115><c_84>`PS, `<a_233><b_21><c_136>`?, `<a_233><b_218><c_125>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=10/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 5/6（覆盖83%），锚定: Horizon Zero Dawn - Pl…, The Wolf Among Us - Pl…, Injustice 2 - PS4 [Dig…；新候选=0（**纯复述历史**）；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=子类延续(score3)。我们推的比用户真实点击**更贴历史**(荐3>target1) → **模型偏保守/用户更爱探索**。

### #187 — 类目错·(a)大类都不对
- **历史**(3项; 平台 PS×2,PC×1): PlayStation 2X Network Ada… | H.A.W.X. - PC DVD-Rom | PlayStation 2 Memory Card …
- **GT**: `<a_8><b_195><c_84>` Nyko Power Kit Plus - 2 Pack Rechargeable Batt… _(平台 Xbox360)_ ｜ **native**: `<a_13><b_122><c_188>` Resistance: Burning Skies - Pl… ✗
- **beam top5**: `<a_249><b_170><c_61>`PS, `<a_13><b_134><c_245>`Xbo, `<a_13><b_194><c_173>`PS3, `<a_21><b_44><c_75>`PS2, `<a_13><b_247><c_57>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=Xbox360 vs 荐=PS2)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=9/10，平台数=6，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: PlayStation 2X Network…, H.A.W.X. - PC DVD-Rom, PlayStation 2 Memory C…；新候选=0（**纯复述历史**）；模板开头；genre: action,simulation,immersive。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #188 — 类目对·item错
- **历史**(10项; 平台 Xbox360×7,?×2,DS×1): Bioshock Infinite: The Com… | Madden NFL 17 - Standard E… | Two Worlds 2 - Xbox 360 | Singularity - Xbox 360 | Two Worlds II Official Str… | The Witcher 2: Assassins O…
- **GT**: `<a_24><b_252><c_227>` Too Human - Xbox 360 _(平台 Xbox360)_ ｜ **native**: `<a_140><b_225><c_196>` Singularity - Xbox 360 ✗
- **beam top5**: `<a_140><b_225><c_196>`Xbo, `<a_141><b_227><c_21>`Xbo, `<a_140><b_160><c_117>`Xbo, `<a_194><b_72><c_187>`Xbo, `<a_194><b_15><c_1>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(Xbox360)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=10/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 6/10（覆盖60%），锚定: Dragon Age Origins: Ul…, The Witcher 2: Assassi…, Dead Space 2；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=子类延续(score3)。我们推的比用户真实点击**更贴历史**(荐3>target1) → **模型偏保守/用户更爱探索**。

### #189 — 类目错·(a)大类都不对
- **历史**(5项; 平台 PS3×2,DS×2,3DS×1): Burnout Paradise - Playsta… | Namco Museum - Nintendo DS | Bejeweled 3 - Nintendo DS | 28-in 1 Blue Game Card Cas… | Dead Rising 2 - Playstatio…
- **GT**: `<a_24><b_86><c_212>` Uncharted: Drake's Fortune - Playstation 3 _(平台 PS3)_ ｜ **native**: `<a_80><b_202><c_95>` Far Cry 3 - Playstation 3 ✗
- **beam top5**: `<a_80><b_69><c_85>`PS4, `<a_123><b_72><c_7>`PS4, `<a_80><b_202><c_95>`PS3, `<a_80><b_202><c_49>`?, `<a_123><b_72><c_238>`PS3
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS3 vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=7/10，平台数=5，unique标题=10/10。
- **reasoning质量**: 引用历史 5/5（覆盖100%），锚定: Burnout Paradise - Pla…, Namco Museum - Nintend…, Dead Rising 2 - Playst…；新候选=0（**纯复述历史**）；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #190 — 命中@5 · RERANK伤害 · BEAM坍缩(<a_80×7/10)
- **历史**(6项; 平台 PS3×3,DS×2,3DS×1): Burnout Paradise - Playsta… | Namco Museum - Nintendo DS | Bejeweled 3 - Nintendo DS | 28-in 1 Blue Game Card Cas… | Dead Rising 2 - Playstatio… | Uncharted: Drake's Fortune…
- **GT**: `<a_80><b_59><c_15>` Resident Evil 6 - Playstation 3 _(平台 PS3)_ ｜ **native**: `<a_80><b_59><c_15>` Resident Evil 6 - Playstation … ✓
- **beam top5**: `<a_71><b_86><c_62>`PSV, `<a_80><b_69><c_85>`PS4, `<a_71><b_86><c_248>`PS3, `<a_80><b_202><c_95>`PS3, `<a_80><b_59><c_15>`PS3
- **推荐↔GT差距**: 正确项在 beam 第5位，pred[0] 前缀深度仅 0/3；平台错配(GT=PS3 vs 荐=PSVita)；beam中 share-a=7/10, share-(a,b)=3/10。
- **beam多样性**: **低**（坍缩到 <a_80 家族 7/10）；unique(a,b)=7/10，平台数=5，unique标题=10/10。
- **reasoning质量**: 引用历史 5/6（覆盖83%），锚定: Burnout Paradise - Pla…, Uncharted: Drake's For…, Bejeweled 3 - Nintendo…；新候选=0（**纯复述历史**）；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=漂移(平台/词面关联)(score1)。target 是合理的大类延续，且**已命中**。

### #191 — 类目对·item错
- **历史**(4项; 平台 ?×2,3DS×1,WiiU×1): Mario & Sonic at the Londo… | Mario & Sonic at the Rio 2… | Mario & Sonic at the Rio 2… | Super Mario Galaxy 2
- **GT**: `<a_193><b_0><c_61>` Mario & Sonic at the Sochi 2014 Olympic Winter… _(平台 WiiU)_ ｜ **native**: `<a_193><b_40><c_126>` Sonic Riders Zero Gravity - Ni… ✗
- **beam top5**: `<a_193><b_219><c_226>`Gam, `<a_193><b_40><c_61>`Xbo, `<a_175><b_30><c_225>`?, `<a_193><b_240><c_28>`?, `<a_193><b_40><c_112>`Wii
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台错配(GT=WiiU vs 荐=GameCube)；beam中 share-a=6/10, share-(a,b)=0/10。
- **beam多样性**: **中**（2 个 a 大类）；unique(a,b)=6/10，平台数=5，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Mario & Sonic at the L…, Mario & Sonic at the R…, Mario & Sonic at the R…；新候选=0（**纯复述历史**）；genre: action,immersive,narrative。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。 注意 target 与历史共享词 ['at', 'mario', 'olympic', 'sonic']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #192 — 类目对·item错 · BEAM坍缩(<a_162×10/10)
- **历史**(3项; 平台 GameBoy×1,?×1,WiiU×1): Hydra Performance&reg; Gam… | Sonic amiibo - Japan Impor… | Mario Party 10 + Mario ami…
- **GT**: `<a_162><b_5><c_144>` Nintendo NFC Reader/Writer Accessory - Nintend… _(平台 3DS)_ ｜ **native**: `<a_162><b_251><c_136>` Animal Crossing: amiibo Festiv… ✗
- **beam top5**: `<a_162><b_81><c_26>`?, `<a_162><b_251><c_136>`Wii, `<a_162><b_49><c_93>`?, `<a_162><b_231><c_30>`?, `<a_162><b_172><c_85>`?
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；beam中 share-a=10/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_162 家族 10/10）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Hydra Performance&reg;…, Sonic amiibo - Japan I…, Mario Party 10 + Mario…；新候选=0（**纯复述历史**）；模板开头；genre: action,multiplayer,nostalg。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。

### #193 — 类目错·(a)大类都不对
- **历史**(4项; 平台 PS4×2,?×2): Okca&reg; Dual Charger Por… | DualShock 4 Wireless Contr… | Final Fantasy XIV Online: … | Assassin's Creed Chronicle…
- **GT**: `<a_201><b_151><c_255>` Playstation Plus: 3 Month Membership [Digital … _(平台 PS-generic)_ ｜ **native**: `<a_118><b_185><c_102>` Batman: Arkham Knight - PlaySt… ✗
- **beam top5**: `<a_131><b_28><c_96>`PS4, `<a_131><b_210><c_0>`PS4, `<a_118><b_185><c_102>`PS4, `<a_118><b_150><c_122>`PS4, `<a_194><b_215><c_154>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS-generic vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=9/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Okca&reg; Dual Charger…, DualShock 4 Wireless C…, Assassin's Creed Chron…；新候选=0（**纯复述历史**）；模板开头；genre: action,immersive,narrative。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。 注意 target 与历史共享词 ['code']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #194 — 类目错·(a)大类都不对
- **历史**(4项; 平台 3DS×4): Meta Knight amiibo - Ninte… | Kirby: Planet Robobot - Ni… | King Dedede amiibo - Ninte… | Kirby amiibo - Nintendo 3D…
- **GT**: `<a_201><b_151><c_255>` Playstation Plus: 3 Month Membership [Digital … _(平台 PS-generic)_ ｜ **native**: `<a_162><b_85><c_94>` Kirby amiibo - Nintendo 3DS ✗
- **beam top5**: `<a_162><b_105><c_210>`?, `<a_162><b_125><c_53>`?, `<a_162><b_85><c_94>`3DS, `<a_162><b_105><c_225>`?, `<a_239><b_142><c_92>`Wii
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=8/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Meta Knight amiibo - N…, King Dedede amiibo - N…, Kirby amiibo - Nintend…；新候选=0（**纯复述历史**）；genre: action,nostalg,exploration。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #195 — 类目对·item错
- **历史**(5项; 平台 3DS×4,PS×1): Meta Knight amiibo - Ninte… | Kirby: Planet Robobot - Ni… | King Dedede amiibo - Ninte… | Kirby amiibo - Nintendo 3D… | Playstation Plus: 3 Month …
- **GT**: `<a_250><b_121><c_156>` Nintendo Selects: Super Mario 3D World _(平台 ?)_ ｜ **native**: `<a_162><b_85><c_94>` Kirby amiibo - Nintendo 3DS ✗
- **beam top5**: `<a_162><b_105><c_210>`?, `<a_162><b_125><c_53>`?, `<a_162><b_85><c_94>`3DS, `<a_162><b_105><c_225>`?, `<a_250><b_92><c_44>`?
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；beam中 share-a=3/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=9/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 4/5（覆盖80%），锚定: Meta Knight amiibo - N…, King Dedede amiibo - N…, Kirby amiibo - Nintend…；新候选=0（**纯复述历史**）；模板开头；genre: action,multiplayer。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #196 — 类目错·(a)大类都不对
- **历史**(5项; 平台 PS4×2,WiiU×1,?×1): Mario Kart 8 - Nintendo Wi… | Gen 2 x Extension Cable fo… | Fallout 4 - PlayStation 4 | Overwatch - Collector's Ed… | Controller Gear PS4 Contro…
- **GT**: `<a_7><b_36><c_217>` Xbox One X 1TB Limited Edition Console - Proje… _(平台 XboxOne)_ ｜ **native**: `<a_131><b_224><c_68>` Overwatch - Origins Edition - … ✗
- **beam top5**: `<a_131><b_41><c_229>`PS4, `<a_201><b_151><c_255>`PS, `<a_131><b_224><c_68>`PS4, `<a_131><b_224><c_16>`PC, `<a_201><b_31><c_107>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=XboxOne vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（6 个不同 a 大类）；unique(a,b)=9/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 4/5（覆盖80%），锚定: Mario Kart 8 - Nintend…, Fallout 4 - PlayStatio…, Overwatch - Collector'…；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,racing。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #197 — 类目对·item错
- **历史**(1项; 平台 PC×1): Hyperkin "GN6" Premium Gen…
- **GT**: `<a_214><b_95><c_1>` Razer Naga Hex MOBA PC Gaming Mouse - Green _(平台 PC)_ ｜ **native**: `<a_61><b_170><c_90>` Buffalo iBuffalo Classic USB G… ✗
- **beam top5**: `<a_61><b_0><c_187>`?, `<a_61><b_0><c_234>`?, `<a_61><b_170><c_90>`PC, `<a_214><b_24><c_0>`?, `<a_61><b_240><c_44>`PC
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；beam中 share-a=2/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=8/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 0/1（覆盖0%）；新候选=0（**纯复述历史**）；genre: nostalg,retro,peripheral。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #198 — 类目错·(a)大类都不对
- **历史**(2项; 平台 PC×2): Hyperkin "GN6" Premium Gen… | Razer Naga Hex MOBA PC Gam…
- **GT**: `<a_8><b_70><c_241>` Xbox One Play and Charge Kit _(平台 XboxOne)_ ｜ **native**: `<a_61><b_0><c_234>` Logitech Gamepad F310 ✗
- **beam top5**: `<a_61><b_0><c_187>`?, `<a_61><b_167><c_197>`Xbo, `<a_61><b_131><c_197>`Xbo, `<a_214><b_95><c_29>`?, `<a_61><b_0><c_234>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=8/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: Hyperkin "GN6" Premium…, Razer Naga Hex MOBA PC…；新候选=0（**纯复述历史**）；genre: nostalg,retro,peripheral。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #199 — 类目对·item错 · BEAM坍缩(<a_61×10/10)
- **历史**(3项; 平台 PC×2,XboxOne×1): Hyperkin "GN6" Premium Gen… | Razer Naga Hex MOBA PC Gam… | Xbox One Play and Charge K…
- **GT**: `<a_189><b_94><c_9>` Antec X-1 Cooler for Xbox One _(平台 XboxOne)_ ｜ **native**: `<a_61><b_53><c_5>` Xbox One Wireless Controller a… ✗
- **beam top5**: `<a_61><b_53><c_5>`Xbo, `<a_61><b_167><c_197>`Xbo, `<a_61><b_217><c_168>`Xbo, `<a_61><b_131><c_197>`Xbo, `<a_61><b_167><c_164>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_61 家族 10/10）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Hyperkin "GN6" Premium…, Razer Naga Hex MOBA PC…, Xbox One Play and Char…；新候选=0（**纯复述历史**）；genre: action,peripheral,accessor。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #200 — 命中@1 · BEAM坍缩(<a_61×8/10)
- **历史**(4项; 平台 PC×2,XboxOne×2): Hyperkin "GN6" Premium Gen… | Razer Naga Hex MOBA PC Gam… | Xbox One Play and Charge K… | Antec X-1 Cooler for Xbox …
- **GT**: `<a_61><b_131><c_197>` Microsoft Xbox Wireless Adapter for Windows 10 _(平台 Xbox)_ ｜ **native**: `<a_61><b_131><c_197>` Microsoft Xbox Wireless Adapte… ✓
- **beam top5**: `<a_61><b_131><c_197>`Xbo, `<a_61><b_167><c_197>`Xbo, `<a_61><b_167><c_164>`Xbo, `<a_61><b_53><c_5>`Xbo, `<a_202><b_16><c_110>`?
- **推荐↔GT差距**: top-1 完全命中。
- **beam多样性**: **低**（坍缩到 <a_61 家族 8/10）；unique(a,b)=8/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Hyperkin "GN6" Premium…, Razer Naga Hex MOBA PC…, Xbox One Play and Char…；新候选=0（**纯复述历史**）；genre: action,peripheral。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。target 是合理的大类延续，且**已命中**。

### #201 — 类目错·(a)大类都不对 · BEAM坍缩(<a_61×9/10)
- **历史**(5项; 平台 PC×2,XboxOne×2,Xbox×1): Hyperkin "GN6" Premium Gen… | Razer Naga Hex MOBA PC Gam… | Xbox One Play and Charge K… | Antec X-1 Cooler for Xbox … | Microsoft Xbox Wireless Ad…
- **GT**: `<a_106><b_68><c_238>` Shantae: Half-Genie Hero - Risky Beats Edition… _(平台 PSVita)_ ｜ **native**: `<a_61><b_131><c_197>` Microsoft Xbox Wireless Adapte… ✗
- **beam top5**: `<a_61><b_131><c_197>`Xbo, `<a_61><b_167><c_197>`Xbo, `<a_61><b_111><c_109>`Xbo, `<a_61><b_167><c_164>`Xbo, `<a_61><b_214><c_225>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PSVita vs 荐=Xbox)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_61 家族 9/10）；unique(a,b)=6/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 4/5（覆盖80%），锚定: Hyperkin "GN6" Premium…, Razer Naga Hex MOBA PC…, Xbox One Play and Char…；新候选=0（**纯复述历史**）；模板开头；genre: action,peripheral,accessor。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=子类延续(score3)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #202 — 类目错·(a)大类都不对
- **历史**(6项; 平台 PC×2,XboxOne×2,Xbox×1): Hyperkin "GN6" Premium Gen… | Razer Naga Hex MOBA PC Gam… | Xbox One Play and Charge K… | Antec X-1 Cooler for Xbox … | Microsoft Xbox Wireless Ad… | Shantae: Half-Genie Hero -…
- **GT**: `<a_193><b_177><c_13>` SEGA 3D Classics Collection - Nintendo 3DS _(平台 3DS)_ ｜ **native**: `<a_61><b_131><c_197>` Microsoft Xbox Wireless Adapte… ✗
- **beam top5**: `<a_61><b_167><c_197>`Xbo, `<a_61><b_131><c_197>`Xbo, `<a_106><b_68><c_238>`PSV, `<a_249><b_68><c_59>`PSV, `<a_1><b_150><c_189>`PS3
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=3DS vs 荐=XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=10/10，平台数=5，unique标题=10/10。
- **reasoning质量**: 引用历史 6/6（覆盖100%），锚定: Hyperkin "GN6" Premium…, Razer Naga Hex MOBA PC…, Xbox One Play and Char…；新候选=0（**纯复述历史**）；genre: immersive,narrative,peripheral。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #203 — 类目错·(a)大类都不对 · BEAM坍缩(<a_61×7/10)
- **历史**(7项; 平台 PC×2,XboxOne×2,Xbox×1): Razer Naga Hex MOBA PC Gam… | Xbox One Play and Charge K… | Antec X-1 Cooler for Xbox … | Microsoft Xbox Wireless Ad… | Shantae: Half-Genie Hero -… | SEGA 3D Classics Collectio…
- **GT**: `<a_1><b_163><c_179>` 7th Dragon III Code: VFD - Nintendo 3DS _(平台 3DS)_ ｜ **native**: `<a_61><b_131><c_197>` Microsoft Xbox Wireless Adapte… ✗
- **beam top5**: `<a_61><b_167><c_197>`Xbo, `<a_61><b_0><c_187>`?, `<a_61><b_131><c_197>`Xbo, `<a_61><b_167><c_164>`Xbo, `<a_61><b_111><c_109>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=3DS vs 荐=XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_61 家族 7/10）；unique(a,b)=8/10，平台数=6，unique标题=10/10。
- **reasoning质量**: 引用历史 4/7（覆盖57%），锚定: Shantae: Half-Genie He…, SEGA 3D Classics Colle…, Hyperkin "GN6" Premium…；新候选=0（**纯复述历史**）；模板开头；genre: action,nostalg,retro。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #204 — 类目错·(a)大类都不对
- **历史**(7项; 平台 XboxOne×4,PS4×3): Xbox One Special Edition D… | Tom Clancy's Rainbow Six S… | Sunset Overdrive Day One E… | Watch Dogs 2: Gold Edition… | No Man's Sky - PlayStation… | Attack on Titan - PlayStat…
- **GT**: `<a_13><b_218><c_173>` Agents of Mayhem - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_39><b_51><c_21>` Titanfall 2 - Xbox One ✗
- **beam top5**: `<a_39><b_77><c_105>`Xbo, `<a_39><b_51><c_21>`Xbo, `<a_123><b_58><c_16>`Xbo, `<a_39><b_51><c_188>`PS4, `<a_123><b_58><c_78>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS4 vs 荐=XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=7/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/7（覆盖57%），锚定: Tom Clancy's Rainbow S…, No Man's Sky - PlaySta…, Sunset Overdrive Day O…；新候选=0（**纯复述历史**）；模板开头；genre: action,shooter,multiplayer。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #205 — 类目对·item错 · BEAM坍缩(<a_61×9/10)
- **历史**(4项; 平台 ?×2,XboxOne×1,Xbox×1): Azio Levetron L70 LED Back… | Steam Controller | Microsoft Xbox One Control… | Microsoft Xbox Wireless Ad…
- **GT**: `<a_202><b_164><c_89>` ASTRO Gaming A40 TR Headset + MixAmp Pro TR fo… _(平台 XboxOne)_ ｜ **native**: `<a_61><b_131><c_197>` Microsoft Xbox Wireless Adapte… ✗
- **beam top5**: `<a_61><b_131><c_197>`Xbo, `<a_61><b_167><c_197>`Xbo, `<a_61><b_167><c_164>`Xbo, `<a_202><b_16><c_110>`?, `<a_61><b_111><c_109>`Xbo
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台错配(GT=XboxOne vs 荐=Xbox)；beam中 share-a=1/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_61 家族 9/10）；unique(a,b)=8/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 3/4（覆盖75%），锚定: Azio Levetron L70 LED …, Steam Controller, Microsoft Xbox Wireles…；新候选=0（**纯复述历史**）；genre: multiplayer,immersive,peripheral。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=子类延续(score3)。我们推的比用户真实点击**更贴历史**(荐3>target2) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['gaming']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #206 — 近失·同(a,b)细分仅c不同 · BEAM坍缩(<a_202×10/10)
- **历史**(5项; 平台 ?×2,XboxOne×2,Xbox×1): Azio Levetron L70 LED Back… | Steam Controller | Microsoft Xbox One Control… | Microsoft Xbox Wireless Ad… | ASTRO Gaming A40 TR Headse…
- **GT**: `<a_202><b_50><c_6>` ASTRO Gaming A50 Wireless Dolby Gaming Headset… _(平台 PS4)_ ｜ **native**: `<a_202><b_11><c_246>` Razer Naga Epic Chroma MMO Gam… ✗
- **beam top5**: `<a_202><b_86><c_197>`DS, `<a_202><b_11><c_246>`?, `<a_202><b_50><c_200>`DS, `<a_202><b_11><c_2>`DS, `<a_202><b_16><c_110>`?
- **推荐↔GT差距**: beam 最接近项与 GT 同 (a,b) 细分、仅 c 不同（同系列/不同款），未命中；beam中 share-a=10/10, share-(a,b)=1/10。
- **beam多样性**: **低**（坍缩到 <a_202 家族 10/10）；unique(a,b)=8/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 4/5（覆盖80%），锚定: Azio Levetron L70 LED …, Steam Controller, Microsoft Xbox One Con…；新候选=0（**纯复述历史**）；模板开头；genre: action,immersive,peripheral。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。 注意 target 与历史共享词 ['astro', 'black', 'gaming', 'headset', 'wireless']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #207 — 类目对·item错
- **历史**(1项; 平台 XboxOne×1): Grand Theft Auto V - Xbox …
- **GT**: `<a_131><b_2><c_39>` Borderlands: The Handsome Collection - Xbox On… _(平台 XboxOne)_ ｜ **native**: `<a_39><b_69><c_69>` Call of Duty: Black Ops III - … ✗
- **beam top5**: `<a_39><b_69><c_69>`Xbo, `<a_131><b_155><c_206>`Xbo, `<a_231><b_117><c_187>`Xbo, `<a_80><b_69><c_85>`PS4, `<a_80><b_171><c_131>`Xbo
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台一致(XboxOne)；beam中 share-a=1/10, share-(a,b)=0/10。
- **beam多样性**: **高**（7 个不同 a 大类）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 0/1（覆盖0%）；新候选=0（**纯复述历史**）；genre: action,adventure,immersive。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。

### #208 — 类目对·item错
- **历史**(2项; 平台 XboxOne×2): Grand Theft Auto V - Xbox … | Borderlands: The Handsome …
- **GT**: `<a_240><b_95><c_71>` Mafia III - Xbox One _(平台 XboxOne)_ ｜ **native**: `<a_131><b_155><c_206>` Fallout 4 - Xbox One ✗
- **beam top5**: `<a_131><b_155><c_206>`Xbo, `<a_39><b_69><c_69>`Xbo, `<a_7><b_2><c_105>`Xbo, `<a_39><b_77><c_69>`Xbo, `<a_131><b_145><c_18>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=10/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: Grand Theft Auto V - X…, Borderlands: The Hands…；新候选=0（**纯复述历史**）；模板开头；genre: action,multiplayer,immersive。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。

### #209 — 命中@8
- **历史**(3项; 平台 XboxOne×3): Grand Theft Auto V - Xbox … | Borderlands: The Handsome … | Mafia III - Xbox One
- **GT**: `<a_123><b_228><c_139>` Dead Rising 4 - Xbox One _(平台 XboxOne)_ ｜ **native**: `<a_39><b_77><c_105>` Call of Duty: Infinite Warfare… ✗
- **beam top5**: `<a_39><b_77><c_105>`Xbo, `<a_39><b_51><c_21>`Xbo, `<a_123><b_76><c_255>`Xbo, `<a_39><b_77><c_69>`Xbo, `<a_123><b_188><c_70>`Xbo
- **推荐↔GT差距**: 正确项在 beam 第8位，pred[0] 前缀深度仅 0/3；平台一致(XboxOne)；beam中 share-a=6/10, share-(a,b)=1/10。
- **beam多样性**: **中**（2 个 a 大类）；unique(a,b)=9/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Grand Theft Auto V - X…, Borderlands: The Hands…, Mafia III - Xbox One；新候选=0（**纯复述历史**）；模板开头；genre: action,immersive,narrative。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。target 是合理的漂移(平台/词面关联)，且**已命中**。

### #210 — 命中@7 · BEAM坍缩(<a_123×10/10)
- **历史**(4项; 平台 XboxOne×4): Grand Theft Auto V - Xbox … | Borderlands: The Handsome … | Mafia III - Xbox One | Dead Rising 4 - Xbox One
- **GT**: `<a_123><b_228><c_123>` Left 4 Dead - Xbox 360 _(平台 Xbox360)_ ｜ **native**: `<a_123><b_76><c_255>` Far Cry Primal - Xbox One Stan… ✗
- **beam top5**: `<a_123><b_188><c_70>`Xbo, `<a_123><b_76><c_255>`Xbo, `<a_123><b_58><c_16>`Xbo, `<a_123><b_171><c_44>`Xbo, `<a_123><b_100><c_0>`Xbo
- **推荐↔GT差距**: 正确项在 beam 第7位，pred[0] 前缀深度仅 1/3；平台错配(GT=Xbox360 vs 荐=XboxOne)；beam中 share-a=10/10, share-(a,b)=1/10。
- **beam多样性**: **低**（坍缩到 <a_123 家族 10/10）；unique(a,b)=9/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Grand Theft Auto V - X…, Dead Rising 4 - Xbox O…, Borderlands: The Hands…；新候选=0（**纯复述历史**）；模板开头；genre: action,horror,multiplayer。
- **target合理性(天花板)**: target=子类延续(score3); 我们pred[0]=大类延续(score2)。target 是合理的子类延续，且**已命中**。

### #211 — 类目对·item错 · BEAM坍缩(<a_162×10/10)
- **历史**(4项; 平台 ?×2,3DS×2): Captain Falcon amiibo - Ja… | Meta Knight amiibo - Ninte… | Nintendo NFC Reader/Writer… | PDP Donkey Kong Display
- **GT**: `<a_162><b_60><c_17>` Wolf Link Amiibo Jp Model (The Legend of Zelda… _(平台 ?)_ ｜ **native**: `<a_162><b_140><c_85>` Waddle Dee amiibo - Nintendo 3… ✗
- **beam top5**: `<a_162><b_118><c_196>`?, `<a_162><b_105><c_210>`?, `<a_162><b_140><c_85>`3DS, `<a_162><b_85><c_94>`3DS, `<a_162><b_5><c_144>`3DS
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；beam中 share-a=10/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_162 家族 10/10）；unique(a,b)=10/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Captain Falcon amiibo …, Meta Knight amiibo - N…, Nintendo NFC Reader/Wr…；新候选=0（**纯复述历史**）；模板开头；genre: action,nostalg。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。 注意 target 与历史共享词 ['amiibo', 'series']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #212 — 类目错·(a)大类都不对 · BEAM坍缩(<a_162×10/10)
- **历史**(5项; 平台 ?×3,3DS×2): Captain Falcon amiibo - Ja… | Meta Knight amiibo - Ninte… | Nintendo NFC Reader/Writer… | PDP Donkey Kong Display | Wolf Link Amiibo Jp Model …
- **GT**: `<a_119><b_147><c_182>` PDP Master Sword Stylus Display _(平台 ?)_ ｜ **native**: `<a_162><b_85><c_94>` Kirby amiibo - Nintendo 3DS ✗
- **beam top5**: `<a_162><b_118><c_196>`?, `<a_162><b_140><c_85>`3DS, `<a_162><b_105><c_210>`?, `<a_162><b_85><c_94>`3DS, `<a_162><b_5><c_144>`3DS
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_162 家族 10/10）；unique(a,b)=10/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/5（覆盖80%），锚定: Captain Falcon amiibo …, Meta Knight amiibo - N…, Wolf Link Amiibo Jp Mo…；新候选=0（**纯复述历史**）；模板开头；genre: action,accessor。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['display', 'pdp']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #213 — 近失·同(a,b)细分仅c不同 · BEAM坍缩(<a_162×10/10)
- **历史**(4项; 平台 ?×3,PS4×1): Reflet amiibo - Japan Impo… | Lucina amiibo - Japan Impo… | Robot amiibo - Japan Impor… | Odin Sphere Leifthrasir: S…
- **GT**: `<a_162><b_119><c_40>` Amiibo Marth (Japanese import) _(平台 ?)_ ｜ **native**: `<a_162><b_106><c_220>` Dark Pit amiibo - Japan Import… ✗
- **beam top5**: `<a_162><b_235><c_217>`?, `<a_162><b_21><c_210>`?, `<a_162><b_57><c_111>`Wii, `<a_162><b_125><c_53>`?, `<a_162><b_106><c_211>`?
- **推荐↔GT差距**: beam 最接近项与 GT 同 (a,b) 细分、仅 c 不同（同系列/不同款），未命中；beam中 share-a=10/10, share-(a,b)=2/10。
- **beam多样性**: **低**（坍缩到 <a_162 家族 10/10）；unique(a,b)=7/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 3/4（覆盖75%），锚定: Reflet amiibo - Japan …, Lucina amiibo - Japan …, Odin Sphere Leifthrasi…；新候选=0（**纯复述历史**）；模板开头；genre: action。
- **target合理性(天花板)**: target=子类延续(score3); 我们pred[0]=大类延续(score2)。用户点击比我们top1**更贴历史**(target3>荐2) → 我们把可命中的延续**跑偏**了。 注意 target 与历史共享词 ['amiibo', 'import']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #214 — 命中@1
- **历史**(4项; 平台 3DS×3,DS×1): Shovel Knight - Nintendo 3… | Shin Megami Tensei: Strang… | Etrian Mystery Dungeon - N… | Kirby Triple Deluxe - Nint…
- **GT**: `<a_216><b_28><c_31>` Etrian Odyssey 2 Untold: The Fafnir Knight - N… _(平台 3DS)_ ｜ **native**: `<a_216><b_28><c_31>` Etrian Odyssey 2 Untold: The F… ✓
- **beam top5**: `<a_216><b_28><c_31>`3DS, `<a_216><b_92><c_163>`3DS, `<a_216><b_219><c_158>`3DS, `<a_216><b_28><c_41>`?, `<a_216><b_92><c_192>`3DS
- **推荐↔GT差距**: top-1 完全命中。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=6/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 3/4（覆盖75%），锚定: Shovel Knight - Ninten…, Etrian Mystery Dungeon…, Kirby Triple Deluxe - …；新候选=0（**纯复述历史**）；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。target 是合理的大类延续，且**已命中**。

### #215 — 类目错·(a)大类都不对
- **历史**(10项; 平台 ?×4,PS3×4,PSP×1): Kingdom Hearts HD 2.5 ReMI… | WWE '13 | PSP Super Travel Case With… | Heavy Rain: Director's Cut… | The Sims 3 Island Paradise… | The Sims 3 Seasons
- **GT**: `<a_235><b_226><c_182>` Toy Story 2 _(平台 ?)_ ｜ **native**: `<a_211><b_133><c_30>` Pokemon Alpha Sapphire - Ninte… ✗
- **beam top5**: `<a_22><b_173><c_203>`?, `<a_211><b_133><c_30>`3DS, `<a_22><b_252><c_160>`?, `<a_211><b_133><c_123>`3DS, `<a_211><b_31><c_95>`3DS
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=8/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 7/10（覆盖70%），锚定: Pokemon Stadium, The Sims 3 Seasons, MLB 13 The Show - Play…；新候选=0（**纯复述历史**）；模板开头；genre: action,adventure,sports。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #216 — 类目对·item错 · BEAM坍缩(<a_39×8/10)
- **历史**(4项; 平台 XboxOne×3,Xbox360×1): Fallout 4 - Xbox One | Xbox One Chatpad + Chat He… | Xbox One Play and Charge K… | Call of Duty 2 - Xbox 360
- **GT**: `<a_24><b_178><c_18>` Rise of the Tomb Raider - Xbox One _(平台 XboxOne)_ ｜ **native**: `<a_39><b_182><c_109>` Call of Duty: Black Ops Combo … ✗
- **beam top5**: `<a_39><b_69><c_69>`Xbo, `<a_39><b_77><c_105>`Xbo, `<a_39><b_77><c_69>`Xbo, `<a_39><b_124><c_106>`?, `<a_39><b_40><c_248>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_39 家族 8/10）；unique(a,b)=9/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Fallout 4 - Xbox One, Call of Duty 2 - Xbox …, Xbox One Chatpad + Cha…；新候选=0（**纯复述历史**）；genre: action,shooter,immersive。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #217 — 类目错·(a)大类都不对 · BEAM坍缩(<a_80×7/10)
- **历史**(6项; 平台 PS3×3,?×3): Heavenly Sword - Playstati… | Resistance: Fall of Man - … | Grand Theft Auto IV | Grand Theft Auto IV - Play… | Grand Theft Auto IV | Grand Theft Auto IV & Epis…
- **GT**: `<a_201><b_45><c_166>` Prey - Pre-load - PS4 Digital Code _(平台 PS4)_ ｜ **native**: `<a_80><b_140><c_246>` Modnation Racers - PlayStation… ✗
- **beam top5**: `<a_80><b_202><c_49>`?, `<a_240><b_221><c_2>`PS3, `<a_240><b_40><c_2>`PS, `<a_80><b_140><c_246>`PS, `<a_80><b_69><c_76>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_80 家族 7/10）；unique(a,b)=8/10，平台数=5，unique标题=10/10。
- **reasoning质量**: 引用历史 5/6（覆盖83%），锚定: Heavenly Sword - Plays…, Resistance: Fall of Ma…, Grand Theft Auto IV；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=探索(无关联)(score0)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #218 — 类目错·(a)大类都不对
- **历史**(4项; 平台 PS3×3,?×1): No More Heroes: Heroes' Pa… | Dead Space (PlayStation 3) | Dead Space (PlayStation 3) | Dead Space 3 Limited Editi…
- **GT**: `<a_201><b_45><c_166>` Prey - Pre-load - PS4 Digital Code _(平台 PS4)_ ｜ **native**: `<a_71><b_171><c_0>` Dead Space 3 Limited Edition ✗
- **beam top5**: `<a_80><b_59><c_29>`PS3, `<a_80><b_59><c_15>`PS3, `<a_71><b_202><c_11>`?, `<a_71><b_59><c_0>`?, `<a_80><b_171><c_8>`PS3
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS4 vs 荐=PS3)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（2 个 a 大类）；unique(a,b)=6/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: No More Heroes: Heroes…, Dead Space (PlayStatio…, Dead Space 3 Limited E…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=漂移(平台/词面关联)(score1)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #219 — 类目错·(a)大类都不对
- **历史**(4项; 平台 XboxOne×1,Xbox×1,PC×1): Xbox One Wireless Controll… | Microsoft Xbox Wireless Ad… | Plants vs. Zombies Garden … | Playstation Plus: 3 Month …
- **GT**: `<a_202><b_120><c_89>` Logitech G900 Chaos Spectrum Professional Grad… _(平台 ?)_ ｜ **native**: `<a_131><b_224><c_10>` Overwatch - Origins Edition - … ✗
- **beam top5**: `<a_61><b_167><c_197>`Xbo, `<a_61><b_131><c_197>`Xbo, `<a_131><b_224><c_16>`PC, `<a_61><b_111><c_109>`Xbo, `<a_131><b_224><c_10>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（2 个 a 大类）；unique(a,b)=8/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Xbox One Wireless Cont…, Microsoft Xbox Wireles…, Plants vs. Zombies Gar…；新候选=0（**纯复述历史**）；模板开头；genre: action,adventure,multiplayer。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['wireless']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #220 — 命中@1
- **历史**(6项; 平台 PS4×4,XboxOne×2): Far Cry 4 - PlayStation 4 | Borderlands: The Handsome … | Microsoft Xbox One Elite | Quantum Break - Xbox One | Deus Ex: Mankind Divided -… | Uncharted 4: A Thief's End…
- **GT**: `<a_24><b_72><c_142>` Horizon Zero Dawn - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_24><b_72><c_142>`PS4, `<a_201><b_31><c_107>`PS4, `<a_39><b_51><c_188>`PS4, `<a_123><b_100><c_33>`PS4, `<a_39><b_51><c_21>`Xbo
- **推荐↔GT差距**: top-1 完全命中。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 5/6（覆盖83%），锚定: Far Cry 4 - PlayStatio…, Borderlands: The Hands…, Quantum Break - Xbox O…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。target 是合理的大类延续，且**已命中**。

### #221 — 类目对·item错
- **历史**(3项; 平台 PS4×3): Grand Theft Auto V - PlayS… | Uncharted 4: A Thief's End… | Fallout 4 - PlayStation 4
- **GT**: `<a_123><b_129><c_247>` Metal Gear Solid V: The Phantom Pain - PlaySta… _(平台 PS4)_ ｜ **native**: `<a_201><b_213><c_242>` The Last of Us Remastered - Pl… ✗
- **beam top5**: `<a_131><b_155><c_206>`Xbo, `<a_123><b_72><c_7>`PS4, `<a_201><b_145><c_9>`PS4, `<a_201><b_213><c_242>`PS4, `<a_201><b_31><c_107>`PS4
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台错配(GT=PS4 vs 荐=XboxOne)；beam中 share-a=2/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=10/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Grand Theft Auto V - P…, Uncharted 4: A Thief's…, Fallout 4 - PlayStatio…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #222 — 类目对·item错
- **历史**(4项; 平台 PS4×4): Generic-3 Pack Combo Prote… | The Last of Us Remastered … | Plantronics GAMECOM 818 Wi… | Deadpool - PlayStation 4
- **GT**: `<a_86><b_12><c_93>` South Park: The Fractured but Whole - PlayStat… _(平台 PS4)_ ｜ **native**: `<a_131><b_224><c_68>` Overwatch - Origins Edition - … ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_131><b_41><c_229>`PS4, `<a_131><b_209><c_151>`PS4, `<a_140><b_10><c_248>`PS4, `<a_92><b_68><c_129>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（6 个不同 a 大类）；unique(a,b)=10/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: The Last of Us Remaste…, Generic-3 Pack Combo P…, Plantronics GAMECOM 81…；新候选=0（**纯复述历史**）；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。

### #223 — 类目错·(a)大类都不对
- **历史**(6项; 平台 3DS×4,?×2): Pokemon Alpha Sapphire - N… | Nintendo 3DS Compatible wi… | HORI Screen Protective Fil… | Nintendo New 3DS XL - Blac… | Steam Controller | Razer Naga Epic Chroma MMO…
- **GT**: `<a_211><b_239><c_254>` YO-KAI WATCH 2: Fleshy Souls - Nintendo 3DS _(平台 3DS)_ ｜ **native**: `<a_202><b_11><c_2>` SteelSeries Siberia 200 Gaming… ✗
- **beam top5**: `<a_61><b_131><c_197>`Xbo, `<a_202><b_11><c_246>`?, `<a_202><b_58><c_107>`?, `<a_202><b_120><c_89>`?, `<a_61><b_167><c_197>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=3DS vs 荐=Xbox)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（2 个 a 大类）；unique(a,b)=8/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 4/6（覆盖67%），锚定: Pokemon Alpha Sapphire…, Nintendo 3DS Compatibl…, HORI Screen Protective…；新候选=0（**纯复述历史**）；genre: immersive,portable,peripheral。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。

### #224 — 类目错·(a)大类都不对
- **历史**(1项; 平台 3DS×1): Nintendo 3DS Compatible wi…
- **GT**: `<a_216><b_112><c_119>` The Legend of Zelda: Majora's Mask 3D _(平台 ?)_ ｜ **native**: `<a_113><b_235><c_2>` Nintendo New 3DS XL - Black ✗
- **beam top5**: `<a_113><b_235><c_2>`3DS, `<a_113><b_235><c_28>`3DS, `<a_119><b_168><c_182>`3DS, `<a_113><b_104><c_28>`3DS, `<a_113><b_31><c_38>`3DS
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=7/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 1/1（覆盖100%），锚定: Nintendo 3DS Compatibl…；新候选=0（**纯复述历史**）；genre: action,accessor。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #225 — 类目对·item错 · BEAM坍缩(<a_123×8/10)
- **历史**(4项; 平台 PS4×3,PS3×1): Far Cry 4 - PS3 [Digital C… | Just Dance 2017 - PlayStat… | Mafia III - PlayStation 4 | Tom Clancy&rsquo;s Ghost R…
- **GT**: `<a_24><b_72><c_142>` Horizon Zero Dawn - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_123><b_58><c_78>`PS4, `<a_191><b_10><c_232>`PS4, `<a_123><b_142><c_36>`PS4, `<a_123><b_76><c_232>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_123 家族 8/10）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Far Cry 4 - PS3 [Digit…, Mafia III - PlayStatio…, Just Dance 2017 - Play…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。

### #226 — 类目错·(a)大类都不对
- **历史**(8项; 平台 ?×4,PS2×2,PS×1): Spyro the Dragon | Spyro 2: Ripto's Rage | Spyro: Year of the Dragon | Until Dawn - PlayStation 4 | Wireless Game Controller, … | CTR: Crash Team Racing
- **GT**: `<a_21><b_12><c_226>` Beastron A/V Cable for Nintendo Wii _(平台 Wii)_ ｜ **native**: `<a_61><b_61><c_16>` Wireless Game Controller, Doub… ✗
- **beam top5**: `<a_61><b_61><c_203>`PS2, `<a_205><b_143><c_74>`?, `<a_233><b_44><c_175>`?, `<a_205><b_143><c_57>`?, `<a_233><b_201><c_25>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=Wii vs 荐=PS2)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=7/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 6/8（覆盖75%），锚定: Spyro the Dragon, Spyro 2: Ripto's Rage, Spyro: Year of the Dra…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=子类延续(score3)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #227 — 命中·复购/同款易例
- **历史**(9项; 平台 ?×4,PS2×2,PS×1): Spyro 2: Ripto's Rage | Spyro: Year of the Dragon | Until Dawn - PlayStation 4 | Wireless Game Controller, … | CTR: Crash Team Racing | Beastron A/V Cable for Nin…
- **GT**: `<a_21><b_12><c_226>` Beastron A/V Cable for Nintendo Wii _(平台 Wii)_ ｜ **native**: `<a_21><b_12><c_226>` Beastron A/V Cable for Nintend… ✓
- **beam top5**: `<a_21><b_12><c_226>`Wii, `<a_21><b_125><c_39>`Wii, `<a_21><b_242><c_102>`Gam, `<a_219><b_57><c_168>`Gam, `<a_233><b_44><c_175>`?
- **推荐↔GT差距**: top-1 完全命中。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=9/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 5/9（覆盖56%），锚定: Spyro the Dragon, Spyro 2: Ripto's Rage, Buyee 128MB Memory Car…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=子类延续(score3); 我们pred[0]=子类延续(score3)。target 是合理的子类延续，且**已命中**。

### #228 — 类目错·(a)大类都不对 · BEAM坍缩(<a_175×8/10)
- **历史**(9项; 平台 ?×7,PS3×1,Xbox360×1): Final Fantasy VII: Dirge o… | Heavenly Sword - Playstati… | Final Fantasy XIII-2 | Lightning Returns: Final F… | Final Fantasy Legend | Super Mario Bros. Deluxe
- **GT**: `<a_121><b_76><c_208>` Star Ocean: Integrity and Faithlessness - Play… _(平台 PS4)_ ｜ **native**: `<a_175><b_24><c_11>` New Super Mario Bros ✗
- **beam top5**: `<a_175><b_24><c_11>`?, `<a_175><b_24><c_4>`Wii, `<a_194><b_24><c_128>`?, `<a_175><b_24><c_254>`?, `<a_175><b_113><c_236>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_175 家族 8/10）；unique(a,b)=5/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 6/9（覆盖67%），锚定: Final Fantasy X, Final Fantasy X-2, Heavenly Sword - Plays…；新候选=0（**纯复述历史**）；genre: action,adventure,role-playing。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=子类延续(score3)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #229 — 类目错·(a)大类都不对
- **历史**(10项; 平台 PS4×4,PSVita×2,?×2): The Wolf Among Us | Samurai Warriors 4 Empires… | Warriors Orochi 3 Ultimate… | 7th Dragon III Code: VFD -… | Persona 5 - SteelBook Edit… | Mass Effect Andromeda - Pr…
- **GT**: `<a_7><b_156><c_24>` Turtle Beach - Ear Force X12 Amplified Stereo … _(平台 Xbox360)_ ｜ **native**: `<a_1><b_150><c_189>` Legend of Heroes: Trails of Co… ✗
- **beam top5**: `<a_1><b_150><c_189>`PS3, `<a_1><b_177><c_70>`PSV, `<a_1><b_177><c_184>`PS4, `<a_1><b_116><c_233>`PS4, `<a_1><b_68><c_121>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=Xbox360 vs 荐=PS3)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=8/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 5/10（覆盖50%），锚定: Tales of Hearts R (PSV…, 7th Dragon III Code: V…, Persona 5 - SteelBook …；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,immersive。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #230 — 命中@1
- **历史**(7项; 平台 PS3×7): Resistance: Fall of Man - … | Fallout: New Vegas Ultimat… | Assassin's Creed IV Black … | The Evil Within - Playstat… | Dark Souls II - Playstatio… | BioShock Infinite - PS3 [D…
- **GT**: `<a_194><b_215><c_154>` Bloodborne _(平台 ?)_ ｜ **native**: `<a_201><b_145><c_9>` The Witcher 3: Wild Hunt - Pla… ✗
- **beam top5**: `<a_194><b_215><c_154>`?, `<a_123><b_72><c_7>`PS4, `<a_201><b_145><c_9>`PS4, `<a_201><b_215><c_247>`PS4, `<a_123><b_72><c_238>`PS3
- **推荐↔GT差距**: top-1 完全命中。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=8/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 6/7（覆盖86%），锚定: Red Dead Redemption - …, Assassin's Creed IV Bl…, Resistance: Fall of Ma…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。target 是合理的大类延续，且**已命中**。

### #231 — 类目对·item错
- **历史**(5项; 平台 PS3×2,PS4×2,PS2×1): Red Dead Redemption - Play… | Hydra Performance Wireless… | Destiny: The Taken King - … | Far Cry Primal - PlayStati… | Fallout 4 - PlayStation 4
- **GT**: `<a_92><b_68><c_129>` Doom - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_131><b_210><c_0>` Fallout 4 - PlayStation 4 ✗
- **beam top5**: `<a_131><b_28><c_96>`PS4, `<a_123><b_72><c_7>`PS4, `<a_131><b_155><c_206>`Xbo, `<a_131><b_210><c_0>`PS4, `<a_201><b_145><c_9>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=9/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 4/5（覆盖80%），锚定: Red Dead Redemption - …, Destiny: The Taken Kin…, Far Cry Primal - PlayS…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #232 — 类目错·(a)大类都不对 · BEAM坍缩(<a_240×8/10)
- **历史**(4项; 平台 Xbox360×2,?×2): Rise of the Tomb Raider - … | Forza Motorsport 3 - Xbox … | Tomb Raider: Underworld | GoldenEye 007: Reloaded
- **GT**: `<a_22><b_23><c_155>` Life is Strange - Xbox One _(平台 XboxOne)_ ｜ **native**: `<a_240><b_87><c_195>` Max Payne 3 - Xbox 360 ✗
- **beam top5**: `<a_240><b_33><c_93>`?, `<a_240><b_87><c_195>`Xbo, `<a_240><b_87><c_41>`PS, `<a_240><b_221><c_2>`PS3, `<a_240><b_243><c_111>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_240 家族 8/10）；unique(a,b)=9/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 3/4（覆盖75%），锚定: Rise of the Tomb Raide…, Tomb Raider: Underworl…, GoldenEye 007: Reloade…；新候选=0（**纯复述历史**）；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #233 — 类目对·item错
- **历史**(10项; 平台 PS4×5,XboxOne×5): FIFA 17 - Xbox One | FIFA 17 - PlayStation 4 | Battlefield Hardline Delux… | Mortal Kombat X - Xbox One | Just Dance Disney Party 2 … | Angry Birds: Star Wars - P…
- **GT**: `<a_74><b_115><c_116>` Injustice 2 - PS4 [Digital Code] _(平台 PS4)_ ｜ **native**: `<a_245><b_193><c_0>` LEGO Jurassic World - Xbox One… ✗
- **beam top5**: `<a_245><b_193><c_0>`Xbo, `<a_22><b_2><c_8>`Xbo, `<a_123><b_76><c_255>`Xbo, `<a_74><b_5><c_203>`Xbo, `<a_245><b_121><c_92>`Xbo
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台错配(GT=PS4 vs 荐=XboxOne)；beam中 share-a=1/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=8/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 5/10（覆盖50%），锚定: Need for Speed - PlayS…, Fallout 4 - PlayStatio…, Battlefield Hardline D…；新候选=0（**纯复述历史**）；模板开头；genre: action,racing,strategy。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #234 — 类目对·item错
- **历史**(3项; 平台 ?×2,PS4×1): Logitech Gamepad F310 | Logitech Gamepad F710 | Metal Gear Solid V: The Ph…
- **GT**: `<a_194><b_36><c_254>` Final Fantasy XV - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_118><b_233><c_76>` Tom Clancy's The Division - Pl… ✗
- **beam top5**: `<a_123><b_72><c_7>`PS4, `<a_131><b_210><c_0>`PS4, `<a_118><b_233><c_76>`PS4, `<a_201><b_213><c_242>`PS4, `<a_118><b_233><c_3>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 0/3（覆盖0%）；新候选=0（**纯复述历史**）；genre: immersive,narrative,peripheral。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #235 — 命中@4
- **历史**(4项; 平台 ?×2,PS4×2): Logitech Gamepad F310 | Logitech Gamepad F710 | Metal Gear Solid V: The Ph… | Final Fantasy XV - PlaySta…
- **GT**: `<a_201><b_31><c_107>` Uncharted 4: A Thief's End - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_194><b_15><c_66>` Dishonored 2 - PlayStation 4 ✗
- **beam top5**: `<a_123><b_100><c_33>`PS4, `<a_201><b_213><c_242>`PS4, `<a_201><b_18><c_56>`PS4, `<a_201><b_31><c_107>`PS4, `<a_194><b_15><c_66>`PS4
- **推荐↔GT差距**: 正确项在 beam 第4位，pred[0] 前缀深度仅 0/3；平台一致(PS4)；beam中 share-a=3/10, share-(a,b)=1/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 2/4（覆盖50%），锚定: Metal Gear Solid V: Th…, Final Fantasy XV - Pla…；新候选=0（**纯复述历史**）；模板开头；genre: action,immersive,narrative。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。target 是合理的漂移(平台/词面关联)，且**已命中**。

### #236 — 类目对·item错
- **历史**(5项; 平台 PS4×3,?×2): Logitech Gamepad F310 | Logitech Gamepad F710 | Metal Gear Solid V: The Ph… | Final Fantasy XV - PlaySta… | Uncharted 4: A Thief's End…
- **GT**: `<a_200><b_7><c_144>` DMC Devil May Cry: Definitive Edition - PlaySt… _(平台 PS4)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_201><b_18><c_56>`PS4, `<a_123><b_100><c_33>`PS4, `<a_201><b_213><c_242>`PS4, `<a_194><b_15><c_66>`PS4, `<a_131><b_209><c_151>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=9/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 5/5（覆盖100%），锚定: Metal Gear Solid V: Th…, Final Fantasy XV - Pla…, Uncharted 4: A Thief's…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #237 — 类目错·(a)大类都不对 · BEAM坍缩(<a_49×10/10)
- **历史**(8项; 平台 ?×5,3DS×1,Xbox360×1): Disney Infinity 3.0 Editio… | Disney Infinity 3.0 Editon… | Disney Infinity 3.0 Editio… | Disney Infinity 3.0 Editio… | Disney Infinity 3.0 Editio… | Disney Infinty Cars Playse…
- **GT**: `<a_74><b_100><c_233>` Minecraft _(平台 ?)_ ｜ **native**: `<a_49><b_110><c_219>` Disney Infinity 3.0 Edition: S… ✗
- **beam top5**: `<a_49><b_110><c_219>`?, `<a_49><b_125><c_112>`?, `<a_49><b_94><c_203>`?, `<a_49><b_119><c_95>`?, `<a_49><b_110><c_128>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_49 家族 10/10）；unique(a,b)=6/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 4/8（覆盖50%），锚定: Disney Infinity 3.0 Ed…, Disney Infinity 3.0 Ed…, Disney Infinity 3.0 Ed…；新候选=0（**纯复述历史**）；模板开头；genre: action,immersive,narrative。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #238 — 类目对·item错
- **历史**(6项; 平台 PS4×6): NHL 16 - PlayStation 4 | Mega Man Legacy Collection… | The Last of Us Remastered … | Grand Theft Auto V - PlayS… | Call of Duty: Black Ops II… | DualShock 4 Wireless Contr…
- **GT**: `<a_201><b_151><c_255>` Playstation Plus: 3 Month Membership [Digital … _(平台 PS-generic)_ ｜ **native**: `<a_201><b_169><c_181>` PlayStation 4 500GB Console - … ✗
- **beam top5**: `<a_61><b_251><c_144>`PS4, `<a_201><b_169><c_181>`PS4, `<a_201><b_169><c_103>`PS4, `<a_131><b_210><c_0>`PS4, `<a_201><b_2><c_102>`PS4
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台错配(GT=PS-generic vs 荐=PS4)；beam中 share-a=5/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=8/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 4/6（覆盖67%），锚定: NHL 16 - PlayStation 4, The Last of Us Remaste…, Grand Theft Auto V - P…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=子类延续(score3)。我们推的比用户真实点击**更贴历史**(荐3>target2) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['code', 'digital']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #239 — 类目对·item错 · BEAM坍缩(<a_249×7/10)
- **历史**(6项; 平台 PSVita×4,PS3×1,PS4×1): CTA Digital PS Vita Travel… | PS Vita 2000 Trigger Grip … | Mortal Kombat - PlayStatio… | Sony PlayStation Vita WiFi | Sony Playstation PS3 Duals… | Tekken 7 -  PS4 Digital Co…
- **GT**: `<a_195><b_67><c_23>` Sly Cooper: Thieves in Time - PS Vita [Digital… _(平台 PSVita)_ ｜ **native**: `<a_249><b_68><c_59>` 16GB PlayStation Vita Memory C… ✗
- **beam top5**: `<a_249><b_68><c_59>`PSV, `<a_249><b_180><c_74>`PSV, `<a_200><b_168><c_118>`PS3, `<a_249><b_134><c_162>`PSV, `<a_200><b_7><c_144>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PSVita)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_249 家族 7/10）；unique(a,b)=10/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 4/6（覆盖67%），锚定: CTA Digital PS Vita Tr…, PS Vita 2000 Trigger G…, Mortal Kombat - PlaySt…；新候选=0（**纯复述历史**）；模板开头；genre: action,fighting,immersive。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['code', 'digital']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #240 — 类目对·item错 · BEAM坍缩(<a_119×10/10)
- **历史**(4项; 平台 PS4×3,WiiU×1): Junsi Kingdom Hearts Body … | Wii U Gamepad Silicone Jac… | SQDeal Dust Proof Dust Pre… | Grip-iT Analog Stick Cover…
- **GT**: `<a_119><b_168><c_182>` HORI Screen Protective Filter for Nintendo NEW… _(平台 3DS)_ ｜ **native**: `<a_119><b_217><c_221>` Grip-iT Analog Stick Covers, S… ✗
- **beam top5**: `<a_119><b_93><c_19>`Wii, `<a_119><b_181><c_184>`Xbo, `<a_119><b_29><c_3>`Xbo, `<a_119><b_29><c_206>`PS4, `<a_119><b_217><c_221>`?
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台错配(GT=3DS vs 荐=WiiU)；beam中 share-a=10/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_119 家族 10/10）；unique(a,b)=8/10，平台数=5，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Junsi Kingdom Hearts B…, Wii U Gamepad Silicone…, SQDeal Dust Proof Dust…；新候选=0（**纯复述历史**）；模板开头；genre: action,accessor。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。

### #241 — 类目错·(a)大类都不对 · BEAM坍缩(<a_45×10/10)
- **历史**(10项; 平台 PS4×6,XboxOne×3,Xbox360×1): Call of Duty: Infinite War… | Call of Duty: Infinite War… | Call Of Duty: Infinite War… | Call of Duty: Infinite War… | Call of Duty: Advanced War… | NBA 2K15 - Xbox 360
- **GT**: `<a_205><b_208><c_148>` Gran Turismo Sport - Limited Edition - PlaySta… _(平台 PS4)_ ｜ **native**: `<a_45><b_168><c_146>` NBA 2K17 - Legend Edition - Xb… ✗
- **beam top5**: `<a_45><b_168><c_146>`Xbo, `<a_45><b_246><c_5>`PS4, `<a_45><b_168><c_2>`PS4, `<a_45><b_3><c_16>`Xbo, `<a_45><b_18><c_254>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS4 vs 荐=XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_45 家族 10/10）；unique(a,b)=5/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/10（覆盖40%），锚定: Battlefield 1 - PlaySt…, Call of Duty: Infinite…, Call Of Duty: Infinite…；新候选=0（**纯复述历史**）；模板开头；genre: action,shooter,sports。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=子类延续(score3)。我们推的比用户真实点击**更贴历史**(荐3>target1) → **模型偏保守/用户更爱探索**。

### #242 — 类目错·(a)大类都不对 · BEAM坍缩(<a_123×8/10)
- **历史**(6项; 平台 PS4×6): Uncharted 4: A Thief's End… | The Evil Within - PlayStat… | The Witcher 3: Wild Hunt -… | Deus Ex: Mankind Divided -… | Rise of the Tomb Raider: 2… | Resident Evil 7: Biohazard…
- **GT**: `<a_194><b_36><c_254>` Final Fantasy XV - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_123><b_58><c_16>` Resident Evil 7 Biohazard - Xb… ✗
- **beam top5**: `<a_123><b_58><c_16>`Xbo, `<a_24><b_72><c_142>`PS4, `<a_123><b_100><c_33>`PS4, `<a_123><b_44><c_0>`PS4, `<a_123><b_142><c_36>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS4 vs 荐=XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_123 家族 8/10）；unique(a,b)=8/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 5/6（覆盖83%），锚定: Uncharted 4: A Thief's…, The Evil Within - Play…, Resident Evil 7: Bioha…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=子类延续(score3)。我们推的比用户真实点击**更贴历史**(荐3>target1) → **模型偏保守/用户更爱探索**。

### #243 — 类目错·(a)大类都不对
- **历史**(8项; 平台 XboxOne×6,3DS×2): Turtle Beach - Ear Force X… | Xbox One Limited Edition H… | Bravely Second: End Layer … | Final Fantasy XV - Xbox On… | Pok&eacute;mon Sun - Ninte… | NHL 17 - Xbox One
- **GT**: `<a_121><b_155><c_99>` NieR: Automata - Playstation 4 _(平台 PS4)_ ｜ **native**: `<a_45><b_28><c_168>` FIFA 17 - PlayStation 4 ✗
- **beam top5**: `<a_39><b_77><c_105>`Xbo, `<a_39><b_51><c_21>`Xbo, `<a_45><b_28><c_168>`PS4, `<a_45><b_168><c_109>`Xbo, `<a_191><b_10><c_19>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS4 vs 荐=XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=8/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 6/8（覆盖75%），锚定: NHL 16 - Xbox One, NHL 17 - Xbox One, Halo 5 Guardians - Xbo…；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,sports。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=漂移(平台/词面关联)(score1)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #244 — 类目对·item错
- **历史**(4项; 平台 PS4×4): Doom - PlayStation 4 | Transformers Devastation -… | Tom Clancy's The Division … | Battlefield 1 - PlayStatio…
- **GT**: `<a_24><b_72><c_142>` Horizon Zero Dawn - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_39><b_51><c_188>` Titanfall 2 - PlayStation 4 ✗
- **beam top5**: `<a_39><b_51><c_188>`PS4, `<a_39><b_77><c_105>`Xbo, `<a_39><b_51><c_21>`Xbo, `<a_123><b_100><c_33>`PS4, `<a_39><b_78><c_205>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=7/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 3/4（覆盖75%），锚定: Doom - PlayStation 4, Battlefield 1 - PlaySt…, Tom Clancy's The Divis…；新候选=0（**纯复述历史**）；模板开头；genre: action,shooter,multiplayer。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #245 — 类目对·item错
- **历史**(5项; 平台 PS4×5): Doom - PlayStation 4 | Transformers Devastation -… | Tom Clancy's The Division … | Battlefield 1 - PlayStatio… | Horizon Zero Dawn - PlaySt…
- **GT**: `<a_123><b_10><c_33>` Wolfenstein: The Old Blood - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_39><b_51><c_188>`PS4, `<a_201><b_31><c_107>`PS4, `<a_201><b_18><c_56>`PS4, `<a_123><b_100><c_33>`PS4, `<a_123><b_58><c_78>`PS4
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台一致(PS4)；beam中 share-a=3/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=10/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 3/5（覆盖60%），锚定: Doom - PlayStation 4, Horizon Zero Dawn - Pl…, Battlefield 1 - PlaySt…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #246 — 类目错·(a)大类都不对 · BEAM坍缩(<a_61×10/10)
- **历史**(5项; 平台 XboxOne×2,?×1,Xbox×1): Xbox One Chatpad + Chat He… | Logitech G602 Lag-Free Wir… | Xbox One Wireless Controll… | Microsoft Xbox Wireless Ad… | DualShock 4 Wireless Contr…
- **GT**: `<a_162><b_125><c_53>` Yoshi amiibo (Super Smash Bros Series) _(平台 ?)_ ｜ **native**: `<a_61><b_131><c_197>` Microsoft Xbox Wireless Adapte… ✗
- **beam top5**: `<a_61><b_167><c_197>`Xbo, `<a_61><b_131><c_197>`Xbo, `<a_61><b_44><c_172>`PS4, `<a_61><b_251><c_144>`PS4, `<a_61><b_170><c_90>`PC
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_61 家族 10/10）；unique(a,b)=8/10，平台数=5，unique标题=10/10。
- **reasoning质量**: 引用历史 5/5（覆盖100%），锚定: Xbox One Chatpad + Cha…, Logitech G602 Lag-Free…, Xbox One Wireless Cont…；新候选=0（**纯复述历史**）；genre: peripheral,accessor,controller。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #247 — 类目对·item错 · BEAM坍缩(<a_162×10/10)
- **历史**(6项; 平台 XboxOne×2,?×2,Xbox×1): Xbox One Chatpad + Chat He… | Logitech G602 Lag-Free Wir… | Xbox One Wireless Controll… | Microsoft Xbox Wireless Ad… | DualShock 4 Wireless Contr… | Yoshi amiibo (Super Smash …
- **GT**: `<a_162><b_130><c_72>` Nintendo Boo amiibo (SM Series) - Nintendo Wii… _(平台 WiiU)_ ｜ **native**: `<a_162><b_122><c_56>` Mario Modern Color Amiibo - Ja… ✗
- **beam top5**: `<a_162><b_231><c_30>`?, `<a_162><b_49><c_93>`?, `<a_162><b_180><c_145>`?, `<a_162><b_2><c_170>`?, `<a_162><b_242><c_145>`?
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；beam中 share-a=10/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_162 家族 10/10）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 3/6（覆盖50%），锚定: Xbox One Chatpad + Cha…, Microsoft Xbox Wireles…, Yoshi amiibo (Super Sm…；新候选=0（**纯复述历史**）；模板开头；genre: action,accessor,controller。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。 注意 target 与历史共享词 ['amiibo', 'series']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #248 — 类目错·(a)大类都不对
- **历史**(1项; 平台 DS×1): PlayStation Gold Wireless …
- **GT**: `<a_194><b_87><c_112>` Dark Souls III - PlayStation 4 Standard Editio… _(平台 PS4)_ ｜ **native**: `<a_7><b_248><c_2>` Xbox One Limited Edition Halo … ✗
- **beam top5**: `<a_7><b_248><c_16>`Xbo, `<a_7><b_248><c_177>`Xbo, `<a_7><b_248><c_2>`Xbo, `<a_7><b_2><c_105>`Xbo, `<a_7><b_36><c_0>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS4 vs 荐=XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（2 个 a 大类）；unique(a,b)=7/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 0/1（覆盖0%）；新候选=0（**纯复述历史**）；genre: multiplayer,immersive,peripheral。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #249 — 类目错·(a)大类都不对
- **历史**(2项; 平台 DS×1,PS4×1): PlayStation Gold Wireless … | Dark Souls III - PlayStati…
- **GT**: `<a_45><b_246><c_5>` EA Sports UFC 2 - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_194><b_87><c_249>` Dark Souls III: Day 1 Edition … ✗
- **beam top5**: `<a_194><b_215><c_154>`?, `<a_194><b_87><c_249>`PS4, `<a_194><b_87><c_220>`PS4, `<a_131><b_209><c_151>`PS4, `<a_131><b_210><c_0>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（2 个 a 大类）；unique(a,b)=8/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: Dark Souls III - PlayS…, PlayStation Gold Wirel…；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,immersive。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #250 — 命中@6 · BEAM坍缩(<a_45×8/10)
- **历史**(3项; 平台 PS4×2,DS×1): PlayStation Gold Wireless … | Dark Souls III - PlayStati… | EA Sports UFC 2 - PlayStat…
- **GT**: `<a_45><b_28><c_168>` FIFA 17 - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_45><b_168><c_146>` NBA 2K17 - Legend Edition - Xb… ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_45><b_168><c_1>`Xbo, `<a_45><b_168><c_2>`PS4, `<a_45><b_168><c_109>`Xbo, `<a_45><b_168><c_146>`Xbo
- **推荐↔GT差距**: 正确项在 beam 第6位，pred[0] 前缀深度仅 0/3；平台一致(PS4)；beam中 share-a=8/10, share-(a,b)=1/10。
- **beam多样性**: **低**（坍缩到 <a_45 家族 8/10）；unique(a,b)=7/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: PlayStation Gold Wirel…, Dark Souls III - PlayS…, EA Sports UFC 2 - Play…；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,sports。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=漂移(平台/词面关联)(score1)。target 是合理的大类延续，且**已命中**。

### #251 — 类目对·item错 · BEAM坍缩(<a_45×8/10)
- **历史**(4项; 平台 PS4×3,DS×1): PlayStation Gold Wireless … | Dark Souls III - PlayStati… | EA Sports UFC 2 - PlayStat… | FIFA 17 - PlayStation 4
- **GT**: `<a_131><b_175><c_170>` For Honor: Deluxe Edition (Includes Extra Cont… _(平台 PS4)_ ｜ **native**: `<a_45><b_28><c_168>` FIFA 17 - PlayStation 4 ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_45><b_168><c_2>`PS4, `<a_45><b_193><c_4>`PS4, `<a_45><b_10><c_13>`PS4, `<a_45><b_28><c_168>`PS4
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台一致(PS4)；beam中 share-a=1/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_45 家族 8/10）；unique(a,b)=8/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 2/4（覆盖50%），锚定: Dark Souls III - PlayS…, FIFA 17 - PlayStation …；新候选=0（**纯复述历史**）；模板开头；genre: action,sports,strategy。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。

### #252 — 类目错·(a)大类都不对
- **历史**(5项; 平台 PS4×4,DS×1): PlayStation Gold Wireless … | Dark Souls III - PlayStati… | EA Sports UFC 2 - PlayStat… | FIFA 17 - PlayStation 4 | For Honor: Deluxe Edition …
- **GT**: `<a_8><b_193><c_132>` ACC PS4 DUALSHOCK 4 CHARGING STATION BY SONY #… _(平台 PS4)_ ｜ **native**: `<a_39><b_51><c_188>` Titanfall 2 - PlayStation 4 ✗
- **beam top5**: `<a_39><b_175><c_240>`Xbo, `<a_39><b_51><c_188>`PS4, `<a_39><b_51><c_21>`Xbo, `<a_39><b_51><c_170>`PC, `<a_45><b_168><c_2>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS4 vs 荐=XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=7/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 3/5（覆盖60%），锚定: Dark Souls III - PlayS…, EA Sports UFC 2 - Play…, For Honor: Deluxe Edit…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=探索(无关联)(score0)。用户点击比我们top1**更贴历史**(target1>荐0) → 我们把可命中的延续**跑偏**了。

### #253 — 类目对·item错
- **历史**(6项; 平台 PS4×5,DS×1): PlayStation Gold Wireless … | Dark Souls III - PlayStati… | EA Sports UFC 2 - PlayStat… | FIFA 17 - PlayStation 4 | For Honor: Deluxe Edition … | ACC PS4 DUALSHOCK 4 CHARGI…
- **GT**: `<a_201><b_134><c_202>` 500GB PlayStation 4 Console - Batman Arkham Kn… _(平台 PS4)_ ｜ **native**: `<a_45><b_28><c_168>` FIFA 17 - PlayStation 4 ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_123><b_58><c_78>`PS4, `<a_39><b_51><c_188>`PS4, `<a_39><b_175><c_240>`Xbo, `<a_191><b_10><c_232>`PS4
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台一致(PS4)；beam中 share-a=1/10, share-(a,b)=0/10。
- **beam多样性**: **高**（6 个不同 a 大类）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/6（覆盖67%），锚定: Dark Souls III - PlayS…, EA Sports UFC 2 - Play…, FIFA 17 - PlayStation …；新候选=0（**纯复述历史**）；模板开头；genre: action,shooter,sports。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。

### #254 — 类目对·item错
- **历史**(9项; 平台 XboxOne×8,Xbox360×1): Fallout 4 - Xbox One | Far Cry Primal - Xbox One … | Rise of the Tomb Raider - … | Tom Clancy&rsquo;s Ghost R… | Unravel - Xbox One Digital… | ReCore - Xbox One
- **GT**: `<a_191><b_78><c_53>` Just Cause 3 - Xbox One Digital Code _(平台 XboxOne)_ ｜ **native**: `<a_123><b_228><c_139>` Dead Rising 4 - Xbox One ✗
- **beam top5**: `<a_123><b_58><c_16>`Xbo, `<a_24><b_72><c_142>`PS4, `<a_123><b_188><c_70>`Xbo, `<a_24><b_129><c_118>`Xbo, `<a_24><b_185><c_47>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=10/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 6/9（覆盖67%），锚定: Rise of the Tomb Raide…, Rise of the Tomb Raide…, Far Cry 4 - Xbox One；新候选=0（**纯复述历史**）；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['code', 'digital']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #255 — 类目对·item错 · BEAM坍缩(<a_45×10/10)
- **历史**(3项; 平台 PS4×3): Ratchet & Clank - PlayStat… | Uncharted 4: A Thief's End… | MLB The Show 16 - PlayStat…
- **GT**: `<a_123><b_100><c_33>` Tom Clancy&rsquo;s Ghost Recon Wildlands - Pla… _(平台 PS4)_ ｜ **native**: `<a_45><b_28><c_168>` FIFA 17 - PlayStation 4 ✗
- **beam top5**: `<a_45><b_168><c_2>`PS4, `<a_45><b_107><c_83>`PS4, `<a_45><b_28><c_168>`PS4, `<a_45><b_226><c_3>`PS4, `<a_45><b_168><c_24>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_45 家族 10/10）；unique(a,b)=8/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Ratchet & Clank - Play…, Uncharted 4: A Thief's…, MLB The Show 16 - Play…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #256 — 类目对·item错
- **历史**(4项; 平台 PS4×4): Ratchet & Clank - PlayStat… | Uncharted 4: A Thief's End… | MLB The Show 16 - PlayStat… | Tom Clancy&rsquo;s Ghost R…
- **GT**: `<a_205><b_208><c_188>` Gran Turismo Sport - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_123><b_142><c_36>` 7 Days to Die - PlayStation 4 ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_123><b_142><c_36>`PS4, `<a_123><b_58><c_78>`PS4, `<a_123><b_76><c_232>`PS4, `<a_123><b_2><c_26>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=9/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 3/4（覆盖75%），锚定: Uncharted 4: A Thief's…, Tom Clancy&rsquo;s Gho…, MLB The Show 16 - Play…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。

### #257 — 类目对·item错 · BEAM坍缩(<a_205×9/10)
- **历史**(5项; 平台 PS4×5): Ratchet & Clank - PlayStat… | Uncharted 4: A Thief's End… | MLB The Show 16 - PlayStat… | Tom Clancy&rsquo;s Ghost R… | Gran Turismo Sport - PlayS…
- **GT**: `<a_205><b_208><c_148>` Gran Turismo Sport - Limited Edition - PlaySta… _(平台 PS4)_ ｜ **native**: `<a_205><b_207><c_181>` DiRT Rally - PlayStation 4 ✗
- **beam top5**: `<a_205><b_8><c_170>`PS4, `<a_205><b_111><c_114>`PS4, `<a_205><b_207><c_181>`PS4, `<a_205><b_60><c_93>`PS4, `<a_205><b_8><c_38>`PS4
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台一致(PS4)；beam中 share-a=9/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_205 家族 9/10）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/5（覆盖80%），锚定: Uncharted 4: A Thief's…, Tom Clancy&rsquo;s Gho…, MLB The Show 16 - Play…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=子类延续(score3); 我们pred[0]=大类延续(score2)。用户点击比我们top1**更贴历史**(target3>荐2) → 我们把可命中的延续**跑偏**了。 注意 target 与历史共享词 ['gran', 'sport', 'turismo']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #258 — 命中@1 · BEAM坍缩(<a_216×7/10)
- **历史**(1项; 平台 3DS×1): Fire Emblem Fates: Conques…
- **GT**: `<a_1><b_25><c_194>` Fire Emblem Fates: Birthright - Nintendo 3DS B… _(平台 3DS)_ ｜ **native**: `<a_1><b_25><c_194>` Fire Emblem Fates: Birthright … ✓
- **beam top5**: `<a_1><b_25><c_194>`3DS, `<a_1><b_150><c_189>`PS3, `<a_1><b_141><c_192>`PS4, `<a_216><b_219><c_158>`3DS, `<a_216><b_235><c_168>`3DS
- **推荐↔GT差距**: top-1 完全命中。
- **beam多样性**: **低**（坍缩到 <a_216 家族 7/10）；unique(a,b)=10/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 1/1（覆盖100%），锚定: Fire Emblem Fates: Con…；新候选=0（**纯复述历史**）；genre: action,role-playing,immersive。
- **target合理性(天花板)**: target=子类延续(score3); 我们pred[0]=子类延续(score3)。target 是合理的子类延续，且**已命中**。

### #259 — 类目错·(a)大类都不对
- **历史**(2项; 平台 3DS×2): Fire Emblem Fates: Conques… | Fire Emblem Fates: Birthri…
- **GT**: `<a_211><b_159><c_123>` Pok&eacute;mon Moon - Nintendo 3DS _(平台 3DS)_ ｜ **native**: `<a_216><b_91><c_137>` Stella Glow - Nintendo 3DS ✗
- **beam top5**: `<a_162><b_251><c_136>`Wii, `<a_162><b_125><c_53>`?, `<a_1><b_25><c_194>`3DS, `<a_1><b_150><c_189>`PS3, `<a_216><b_91><c_137>`3DS
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=3DS vs 荐=WiiU)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=9/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: Fire Emblem Fates: Con…, Fire Emblem Fates: Bir…；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,strategy。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=探索(无关联)(score0)。用户点击比我们top1**更贴历史**(target1>荐0) → 我们把可命中的延续**跑偏**了。

### #260 — 命中@1
- **历史**(3项; 平台 3DS×3): Fire Emblem Fates: Conques… | Fire Emblem Fates: Birthri… | Pok&eacute;mon Moon - Nint…
- **GT**: `<a_211><b_159><c_71>` Pok&eacute;mon Sun - Nintendo 3DS _(平台 3DS)_ ｜ **native**: `<a_211><b_159><c_71>` Pok&eacute;mon Sun - Nintendo … ✓
- **beam top5**: `<a_211><b_159><c_71>`3DS, `<a_211><b_159><c_123>`3DS, `<a_216><b_159><c_141>`3DS, `<a_216><b_235><c_168>`3DS, `<a_211><b_133><c_30>`3DS
- **推荐↔GT差距**: top-1 完全命中。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=9/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Fire Emblem Fates: Con…, Fire Emblem Fates: Bir…, Pok&eacute;mon Moon - …；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,immersive。
- **target合理性(天花板)**: target=子类延续(score3); 我们pred[0]=子类延续(score3)。target 是合理的子类延续，且**已命中**。

### #261 — 类目错·(a)大类都不对
- **历史**(4项; 平台 3DS×4): Fire Emblem Fates: Conques… | Fire Emblem Fates: Birthri… | Pok&eacute;mon Moon - Nint… | Pok&eacute;mon Sun - Ninte…
- **GT**: `<a_113><b_159><c_2>` Wii Classic Controller Pro - Black (Japanese V… _(平台 Wii)_ ｜ **native**: `<a_216><b_48><c_110>` Dragon Quest VIII: Journey of … ✗
- **beam top5**: `<a_211><b_159><c_71>`3DS, `<a_162><b_5><c_144>`3DS, `<a_162><b_125><c_53>`?, `<a_216><b_235><c_168>`3DS, `<a_216><b_48><c_110>`3DS
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=Wii vs 荐=3DS)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Fire Emblem Fates: Con…, Fire Emblem Fates: Bir…, Pok&eacute;mon Moon - …；新候选=0（**纯复述历史**）；模板开头；genre: action,adventure,rpg。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=子类延续(score3)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #262 — 类目对·item错
- **历史**(5项; 平台 3DS×4,Wii×1): Fire Emblem Fates: Conques… | Fire Emblem Fates: Birthri… | Pok&eacute;mon Moon - Nint… | Pok&eacute;mon Sun - Ninte… | Wii Classic Controller Pro…
- **GT**: `<a_162><b_174><c_61>` Villager amiibo - Japan Import (Super Smash Br… _(平台 ?)_ ｜ **native**: `<a_113><b_112><c_109>` Nintendo Wii U Pro Controller … ✗
- **beam top5**: `<a_113><b_112><c_109>`Wii, `<a_162><b_5><c_144>`3DS, `<a_162><b_125><c_53>`?, `<a_211><b_159><c_71>`3DS, `<a_162><b_130><c_1>`Wii
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；beam中 share-a=3/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=9/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 5/5（覆盖100%），锚定: Fire Emblem Fates: Con…, Fire Emblem Fates: Bir…, Pok&eacute;mon Moon - …；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,immersive。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #263 — 类目对·item错 · BEAM坍缩(<a_162×10/10)
- **历史**(6项; 平台 3DS×4,Wii×1,?×1): Fire Emblem Fates: Conques… | Fire Emblem Fates: Birthri… | Pok&eacute;mon Moon - Nint… | Pok&eacute;mon Sun - Ninte… | Wii Classic Controller Pro… | Villager amiibo - Japan Im…
- **GT**: `<a_162><b_214><c_137>` Nintendo amiibo series Shulk Collectible Figur… _(平台 ?)_ ｜ **native**: `<a_162><b_122><c_56>` Mario Modern Color Amiibo - Ja… ✗
- **beam top5**: `<a_162><b_122><c_56>`?, `<a_162><b_172><c_85>`?, `<a_162><b_125><c_53>`?, `<a_162><b_122><c_61>`?, `<a_162><b_46><c_162>`3DS
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；beam中 share-a=10/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_162 家族 10/10）；unique(a,b)=7/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 6/6（覆盖100%），锚定: Fire Emblem Fates: Con…, Fire Emblem Fates: Bir…, Pok&eacute;mon Moon - …；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,immersive。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。 注意 target 与历史共享词 ['amiibo', 'series']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #264 — 命中@9 · BEAM坍缩(<a_162×10/10)
- **历史**(7项; 平台 3DS×4,?×2,Wii×1): Fire Emblem Fates: Birthri… | Pok&eacute;mon Moon - Nint… | Pok&eacute;mon Sun - Ninte… | Wii Classic Controller Pro… | Villager amiibo - Japan Im… | Nintendo amiibo series Shu…
- **GT**: `<a_162><b_106><c_98>` Reflet amiibo - Japan Import (Super Smash Bros… _(平台 ?)_ ｜ **native**: `<a_162><b_122><c_56>` Mario Modern Color Amiibo - Ja… ✗
- **beam top5**: `<a_162><b_122><c_56>`?, `<a_162><b_125><c_53>`?, `<a_162><b_122><c_61>`?, `<a_162><b_119><c_2>`?, `<a_162><b_219><c_249>`?
- **推荐↔GT差距**: 正确项在 beam 第9位，pred[0] 前缀深度仅 1/3；beam中 share-a=10/10, share-(a,b)=3/10。
- **beam多样性**: **低**（坍缩到 <a_162 家族 10/10）；unique(a,b)=5/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 4/7（覆盖57%），锚定: Fire Emblem Fates: Con…, Fire Emblem Fates: Bir…, Villager amiibo - Japa…；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,strategy。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。target 是合理的大类延续，且**已命中**。

### #265 — 命中@6 · BEAM坍缩(<a_162×10/10)
- **历史**(8项; 平台 3DS×4,?×3,Wii×1): Pok&eacute;mon Moon - Nint… | Pok&eacute;mon Sun - Ninte… | Wii Classic Controller Pro… | Villager amiibo - Japan Im… | Nintendo amiibo series Shu… | Reflet amiibo - Japan Impo…
- **GT**: `<a_162><b_119><c_2>` Lucina amiibo - Japan Import (Super Smash Bros… _(平台 ?)_ ｜ **native**: `<a_162><b_219><c_249>` Ganondorf amiibo - Japan Impor… ✗
- **beam top5**: `<a_162><b_21><c_210>`?, `<a_162><b_45><c_208>`?, `<a_162><b_219><c_249>`?, `<a_162><b_2><c_170>`?, `<a_162><b_125><c_53>`?
- **推荐↔GT差距**: 正确项在 beam 第6位，pred[0] 前缀深度仅 1/3；beam中 share-a=10/10, share-(a,b)=1/10。
- **beam多样性**: **低**（坍缩到 <a_162 家族 10/10）；unique(a,b)=7/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 2/8（覆盖25%），锚定: Villager amiibo - Japa…, Reflet amiibo - Japan …；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,immersive。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。target 是合理的大类延续，且**已命中**。

### #266 — 命中@7 · BEAM坍缩(<a_162×10/10)
- **历史**(9项; 平台 3DS×4,?×4,Wii×1): Pok&eacute;mon Sun - Ninte… | Wii Classic Controller Pro… | Villager amiibo - Japan Im… | Nintendo amiibo series Shu… | Reflet amiibo - Japan Impo… | Lucina amiibo - Japan Impo…
- **GT**: `<a_162><b_219><c_101>` Nintendo Super Smash Bros Palutena amiibo _(平台 ?)_ ｜ **native**: `<a_162><b_219><c_249>` Ganondorf amiibo - Japan Impor… ✗
- **beam top5**: `<a_162><b_251><c_136>`Wii, `<a_162><b_21><c_210>`?, `<a_162><b_228><c_210>`?, `<a_162><b_219><c_249>`?, `<a_162><b_122><c_56>`?
- **推荐↔GT差距**: 正确项在 beam 第7位，pred[0] 前缀深度仅 1/3；beam中 share-a=10/10, share-(a,b)=3/10。
- **beam多样性**: **低**（坍缩到 <a_162 家族 10/10）；unique(a,b)=7/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/9（覆盖44%），锚定: Fire Emblem Fates: Con…, Fire Emblem Fates: Bir…, Villager amiibo - Japa…；新候选=0（**纯复述历史**）；模板开头；genre: action,strategy,simulation。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。target 是合理的大类延续，且**已命中**。

### #267 — 类目错·(a)大类都不对 · BEAM坍缩(<a_162×10/10)
- **历史**(10项; 平台 ?×5,3DS×4,Wii×1): Wii Classic Controller Pro… | Villager amiibo - Japan Im… | Nintendo amiibo series Shu… | Reflet amiibo - Japan Impo… | Lucina amiibo - Japan Impo… | Nintendo Super Smash Bros …
- **GT**: `<a_232><b_68><c_178>` Fire Emblem Fates - Special Edition - Nintendo… _(平台 3DS)_ ｜ **native**: `<a_162><b_219><c_101>` Nintendo Super Smash Bros Palu… ✗
- **beam top5**: `<a_162><b_45><c_208>`?, `<a_162><b_251><c_136>`Wii, `<a_162><b_122><c_56>`?, `<a_162><b_139><c_171>`?, `<a_162><b_2><c_170>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_162 家族 10/10）；unique(a,b)=8/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 6/10（覆盖60%），锚定: Villager amiibo - Japa…, Nintendo amiibo series…, Reflet amiibo - Japan …；新候选=0（**纯复述历史**）；模板开头；genre: action,adventure,rpg。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['emblem', 'fates', 'fire']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #268 — 类目对·item错
- **历史**(5项; 平台 PS4×5): Mafia III - PlayStation 4 | The Elder Scrolls V: Skyri… | Call Of Duty: Infinite War… | Steep - PS4 Digital Code | Mass Effect Andromeda - Pr…
- **GT**: `<a_205><b_208><c_188>` Gran Turismo Sport - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_123><b_58><c_78>`PS4, `<a_39><b_77><c_105>`Xbo, `<a_39><b_51><c_188>`PS4, `<a_123><b_100><c_33>`PS4, `<a_201><b_45><c_166>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=10/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/5（覆盖80%），锚定: Mafia III - PlayStatio…, The Elder Scrolls V: S…, Call Of Duty: Infinite…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。

### #269 — 命中@3 · RERANK伤害
- **历史**(1项; 平台 PS×1): PlayStation Eye
- **GT**: `<a_140><b_220><c_113>` PlayStation Eye _(平台 PS-generic)_ ｜ **native**: `<a_140><b_220><c_113>` PlayStation Eye ✓
- **beam top5**: `<a_61><b_47><c_32>`PS3, `<a_61><b_47><c_8>`PS3, `<a_140><b_220><c_113>`PS, `<a_175><b_220><c_145>`Wii, `<a_175><b_220><c_18>`Wii
- **推荐↔GT差距**: 正确项在 beam 第3位，pred[0] 前缀深度仅 0/3；平台错配(GT=PS-generic vs 荐=PS3)；beam中 share-a=3/10, share-(a,b)=2/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=5/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 1/1（覆盖100%），锚定: PlayStation Eye；新候选=0（**纯复述历史**）；genre: action,immersive,peripheral。
- **target合理性(天花板)**: target=子类延续(score3); 我们pred[0]=探索(无关联)(score0)。target 是合理的子类延续，且**已命中**。

### #270 — 类目错·(a)大类都不对
- **历史**(2项; 平台 PS×2): PlayStation Eye | PlayStation Eye
- **GT**: `<a_84><b_109><c_95>` Nintendo Wii Remote Plus - White _(平台 Wii)_ ｜ **native**: `<a_140><b_220><c_113>` PlayStation Eye ✗
- **beam top5**: `<a_61><b_47><c_8>`PS3, `<a_61><b_47><c_32>`PS3, `<a_140><b_220><c_113>`PS, `<a_61><b_251><c_51>`PS4, `<a_189><b_201><c_57>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=Wii vs 荐=PS3)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=7/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 0/1（覆盖0%）；新候选=0（**纯复述历史**）；genre: action,peripheral,accessor。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=探索(无关联)(score0)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #271 — 类目错·(a)大类都不对 · BEAM坍缩(<a_84×8/10)
- **历史**(3项; 平台 PS×2,Wii×1): PlayStation Eye | PlayStation Eye | Nintendo Wii Remote Plus -…
- **GT**: `<a_21><b_36><c_20>` HDE Charging Cable for PS3 Controllers USB Cha… _(平台 PS3)_ ｜ **native**: `<a_84><b_222><c_22>` Mario Kart 8 - Nintendo Wii U ✗
- **beam top5**: `<a_175><b_220><c_145>`Wii, `<a_84><b_222><c_22>`Wii, `<a_84><b_222><c_164>`Wii, `<a_84><b_149><c_181>`Wii, `<a_84><b_141><c_255>`Wii
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS3 vs 荐=Wii)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_84 家族 8/10）；unique(a,b)=9/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: PlayStation Eye, Nintendo Wii Remote Pl…；新候选=0（**纯复述历史**）；genre: action,immersive,accessor。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=漂移(平台/词面关联)(score1)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #272 — 类目对·item错 · BEAM坍缩(<a_84×7/10)
- **历史**(4项; 平台 PS×2,Wii×1,PS3×1): PlayStation Eye | PlayStation Eye | Nintendo Wii Remote Plus -… | HDE Charging Cable for PS3…
- **GT**: `<a_162><b_111><c_79>` Wii Stand (RVL-017) _(平台 Wii)_ ｜ **native**: `<a_84><b_109><c_95>` Nintendo Wii Remote Plus - Whi… ✗
- **beam top5**: `<a_175><b_220><c_145>`Wii, `<a_175><b_220><c_18>`Wii, `<a_61><b_47><c_8>`PS3, `<a_84><b_109><c_95>`Wii, `<a_84><b_250><c_189>`Wii
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(Wii)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_84 家族 7/10）；unique(a,b)=8/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 0/3（覆盖0%）；新候选=0（**纯复述历史**）；模板开头；genre: action,peripheral,accessor。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。

### #273 — 类目错·(a)大类都不对
- **历史**(5项; 平台 PS×2,Wii×2,PS3×1): PlayStation Eye | PlayStation Eye | Nintendo Wii Remote Plus -… | HDE Charging Cable for PS3… | Wii Stand (RVL-017)
- **GT**: `<a_111><b_176><c_21>` Just Dance 2016 - PlayStation 3 _(平台 PS3)_ ｜ **native**: `<a_84><b_250><c_189>` Nintendo Wii Remote Plus, Yosh… ✗
- **beam top5**: `<a_175><b_220><c_145>`Wii, `<a_61><b_47><c_8>`PS3, `<a_84><b_250><c_255>`Wii, `<a_84><b_250><c_189>`Wii, `<a_113><b_231><c_3>`Wii
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS3 vs 荐=Wii)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=9/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: PlayStation Eye, Nintendo Wii Remote Pl…, HDE Charging Cable for…；新候选=0（**纯复述历史**）；模板开头；genre: action,nostalg,peripheral。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。

### #274 — 类目对·item错
- **历史**(10项; 平台 PS4×9,?×1): Titanfall 2 Deluxe Edition… | Dishonored 2 - PlayStation… | Watch Dogs - PlayStation 4 | Doom - PlayStation 4 | Assassin's Creed: Syndicat… | Assassin's Creed IV Black …
- **GT**: `<a_123><b_76><c_232>` Far Cry Primal - PlayStation 4 Standard Editio… _(平台 PS4)_ ｜ **native**: `<a_71><b_60><c_105>` Assassin's Creed IV Black Flag… ✗
- **beam top5**: `<a_71><b_33><c_249>`PS3, `<a_71><b_86><c_236>`PS4, `<a_118><b_237><c_113>`PS4, `<a_118><b_150><c_122>`PS4, `<a_118><b_185><c_102>`PS4
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台错配(GT=PS4 vs 荐=PS3)；beam中 share-a=1/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=7/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 6/10（覆盖60%），锚定: Life is Strange - Play…, Dishonored Definitive …, Titanfall 2 - PlayStat…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #275 — 类目对·item错 · BEAM坍缩(<a_205×8/10)
- **历史**(2项; 平台 PS4×2): Injustice 2 - PS4 [Digital… | Gran Turismo Sport - PlayS…
- **GT**: `<a_123><b_52><c_20>` Metal Gear Solid _(平台 ?)_ ｜ **native**: `<a_205><b_60><c_93>` F1 2016 - PlayStation 4 ✗
- **beam top5**: `<a_205><b_0><c_108>`PS4, `<a_123><b_72><c_7>`PS4, `<a_205><b_60><c_93>`PS4, `<a_205><b_0><c_112>`?, `<a_205><b_208><c_52>`?
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；beam中 share-a=1/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_205 家族 8/10）；unique(a,b)=6/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: Injustice 2 - PS4 [Dig…, Gran Turismo Sport - P…；新候选=0（**纯复述历史**）；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #276 — 类目错·(a)大类都不对
- **历史**(3项; 平台 PS4×3): Star Wars: Battlefront & S… | Star Wars: Battlefront - S… | KontrolFreek FPS Freek Vor…
- **GT**: `<a_201><b_151><c_255>` Playstation Plus: 3 Month Membership [Digital … _(平台 PS-generic)_ ｜ **native**: `<a_231><b_46><c_171>` KontrolFreek CQCX Thumb Grips … ✗
- **beam top5**: `<a_231><b_46><c_223>`PS4, `<a_231><b_158><c_0>`PS4, `<a_61><b_35><c_105>`PS4, `<a_61><b_106><c_125>`PS4, `<a_231><b_46><c_171>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS-generic vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=7/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Star Wars: Battlefront…, Star Wars: Battlefront…, KontrolFreek FPS Freek…；新候选=0（**纯复述历史**）；模板开头；genre: action,immersive,nostalg。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['code', 'digital']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #277 — 类目对·item错
- **历史**(4项; 平台 PS4×3,PS×1): Star Wars: Battlefront & S… | Star Wars: Battlefront - S… | KontrolFreek FPS Freek Vor… | Playstation Plus: 3 Month …
- **GT**: `<a_24><b_72><c_142>` Horizon Zero Dawn - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_131><b_224><c_68>` Overwatch - Origins Edition - … ✗
- **beam top5**: `<a_131><b_41><c_229>`PS4, `<a_201><b_31><c_107>`PS4, `<a_131><b_224><c_68>`PS4, `<a_231><b_46><c_171>`PS4, `<a_61><b_106><c_251>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Star Wars: Battlefront…, Star Wars: Battlefront…, KontrolFreek FPS Freek…；新候选=0（**纯复述历史**）；genre: multiplayer,immersive,accessor。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #278 — 类目对·item错
- **历史**(3项; 平台 ?×1,PS3×1,PS4×1): Dead Space 3 Limited Editi… | Portal 2 - Playstation 3 | Titanfall 2 - PlayStation …
- **GT**: `<a_39><b_78><c_54>` Battlefield 1 - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_201><b_213><c_242>`PS4, `<a_24><b_129><c_173>`PS4, `<a_123><b_58><c_78>`PS4, `<a_123><b_142><c_36>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=10/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Dead Space 3 Limited E…, Portal 2 - Playstation…, Titanfall 2 - PlayStat…；新候选=0（**纯复述历史**）；模板开头；genre: action,horror,multiplayer。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=漂移(平台/词面关联)(score1)。用户点击比我们top1**更贴历史**(target2>荐1) → 我们把可命中的延续**跑偏**了。

### #279 — 命中@6
- **历史**(4项; 平台 Xbox360×2,3DS×2): Halo 4 - Xbox 360 (Standar… | Destiny: The Taken King - … | Pokemon Alpha Sapphire - N… | Pok&eacute;mon Omega Ruby …
- **GT**: `<a_211><b_159><c_71>` Pok&eacute;mon Sun - Nintendo 3DS _(平台 3DS)_ ｜ **native**: `<a_211><b_133><c_123>` Pok&eacute;mon Omega Ruby - Ni… ✗
- **beam top5**: `<a_131><b_28><c_96>`PS4, `<a_211><b_133><c_123>`3DS, `<a_211><b_159><c_123>`3DS, `<a_131><b_145><c_18>`Xbo, `<a_131><b_210><c_0>`PS4
- **推荐↔GT差距**: 正确项在 beam 第6位，pred[0] 前缀深度仅 0/3；平台错配(GT=3DS vs 荐=PS4)；beam中 share-a=5/10, share-(a,b)=2/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=7/10，平台数=5，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Halo 4 - Xbox 360 (Sta…, Destiny: The Taken Kin…, Pokemon Alpha Sapphire…；新候选=0（**纯复述历史**）；genre: action,rpg,shooter。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。target 是合理的大类延续，且**已命中**。

### #280 — 类目错·(a)大类都不对 · BEAM坍缩(<a_201×8/10)
- **历史**(1项; 平台 PS4×1): PlayStation 4 500GB Consol…
- **GT**: `<a_71><b_179><c_202>` Dante's Inferno Divine Edition - Playstation 3 _(平台 PS3)_ ｜ **native**: `<a_201><b_2><c_102>` PlayStation 4 500GB Console - … ✗
- **beam top5**: `<a_131><b_210><c_0>`PS4, `<a_201><b_36><c_195>`PS4, `<a_201><b_31><c_107>`PS4, `<a_201><b_2><c_102>`PS4, `<a_201><b_201><c_84>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS3 vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_201 家族 8/10）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 0/1（覆盖0%）；新候选=0（**纯复述历史**）；genre: action,nostalg,retro。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=漂移(平台/词面关联)(score1)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #281 — 类目对·item错
- **历史**(2项; 平台 PS4×1,PS3×1): PlayStation 4 500GB Consol… | Dante's Inferno Divine Edi…
- **GT**: `<a_71><b_159><c_0>` Castlevania _(平台 ?)_ ｜ **native**: `<a_71><b_60><c_118>` Assassin's Creed IV Black Flag… ✗
- **beam top5**: `<a_71><b_33><c_249>`PS3, `<a_71><b_60><c_105>`PS4, `<a_118><b_150><c_122>`PS4, `<a_118><b_95><c_6>`PS4, `<a_71><b_86><c_236>`PS4
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；beam中 share-a=6/10, share-(a,b)=0/10。
- **beam多样性**: **中**（2 个 a 大类）；unique(a,b)=7/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 0/2（覆盖0%）；新候选=0（**纯复述历史**）；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。

### #282 — 类目对·item错 · BEAM坍缩(<a_71×10/10)
- **历史**(3项; 平台 PS4×1,PS3×1,?×1): PlayStation 4 500GB Consol… | Dante's Inferno Divine Edi… | Castlevania
- **GT**: `<a_194><b_222><c_98>` Castlevania: Lords of Shadow 2 - PS3 [Digital … _(平台 PS3)_ ｜ **native**: `<a_71><b_159><c_0>` Castlevania ✗
- **beam top5**: `<a_71><b_164><c_196>`PS3, `<a_71><b_164><c_177>`PSP, `<a_71><b_66><c_14>`?, `<a_71><b_159><c_7>`?, `<a_71><b_171><c_0>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS3)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_71 家族 10/10）；unique(a,b)=8/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Dante's Inferno Divine…, Castlevania, PlayStation 4 500GB Co…；新候选=0（**纯复述历史**）；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['castlevania']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #283 — 类目错·(a)大类都不对
- **历史**(4项; 平台 PS3×2,PS4×1,?×1): PlayStation 4 500GB Consol… | Dante's Inferno Divine Edi… | Castlevania | Castlevania: Lords of Shad…
- **GT**: `<a_118><b_67><c_59>` The Walking Dead: Season 2 - PlayStation 3 _(平台 PS3)_ ｜ **native**: `<a_194><b_222><c_98>` Castlevania: Lords of Shadow 2… ✗
- **beam top5**: `<a_194><b_215><c_154>`?, `<a_194><b_24><c_128>`?, `<a_71><b_202><c_11>`?, `<a_194><b_222><c_98>`PS3, `<a_194><b_21><c_1>`PS3
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=10/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 2/4（覆盖50%），锚定: Dante's Inferno Divine…, Castlevania: Lords of …；新候选=0（**纯复述历史**）；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #284 — 类目对·item错
- **历史**(4项; 平台 XboxOne×4): NBA 2K16 - Xbox One | WWE 2K16 - Xbox One | The Wolf Among Us - Xbox O… | Madden NFL 17 -  Standard …
- **GT**: `<a_194><b_36><c_216>` Final Fantasy XV - Xbox One _(平台 XboxOne)_ ｜ **native**: `<a_231><b_102><c_225>` Madden NFL 17 -  Standard Edit… ✗
- **beam top5**: `<a_231><b_117><c_187>`Xbo, `<a_231><b_237><c_82>`PS4, `<a_45><b_168><c_1>`Xbo, `<a_231><b_223><c_4>`Xbo, `<a_231><b_102><c_225>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（2 个 a 大类）；unique(a,b)=8/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: NBA 2K16 - Xbox One, WWE 2K16 - Xbox One, The Wolf Among Us - Xb…；新候选=0（**纯复述历史**）；genre: action,sports,immersive。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #285 — 类目对·item错
- **历史**(9项; 平台 PS4×9): The Walking Dead: The Comp… | Mafia III - PlayStation 4 | Dishonored 2 - PlayStation… | Mass Effect Andromeda - Pr… | Dead Island Definitive Col… | Tom Clancy's The Division …
- **GT**: `<a_191><b_68><c_161>` inFAMOUS: Second Son Limited Edition (PlayStat… _(平台 PS4)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_123><b_58><c_78>`PS4, `<a_24><b_72><c_142>`PS4, `<a_123><b_100><c_33>`PS4, `<a_123><b_58><c_16>`Xbo, `<a_201><b_31><c_107>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 6/9（覆盖67%），锚定: Call of Duty: Black Op…, The Walking Dead: The …, Alekhine's Gun - PlayS…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。

### #286 — 类目对·item错
- **历史**(10项; 平台 PS4×5,?×4,XboxOne×1): Steep - PS4 Digital Code | CORSAIR Scimitar Pro RGB -… | CORSAIR Scimitar Pro RGB -… | Tom Clancy&rsquo;s Ghost R… | Tom Clancy&rsquo;s Ghost R… | Dragon Quest Builders - Pl…
- **GT**: `<a_86><b_12><c_93>` South Park: The Fractured but Whole - PlayStat… _(平台 PS4)_ ｜ **native**: `<a_1><b_43><c_207>` The Last Guardian - PlayStatio… ✗
- **beam top5**: `<a_1><b_43><c_207>`PS4, `<a_123><b_58><c_78>`PS4, `<a_123><b_100><c_166>`DS, `<a_1><b_173><c_4>`PS4, `<a_123><b_142><c_36>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 5/9（覆盖56%），锚定: Tom Clancy's The Divis…, Tom Clancy&rsquo;s Gho…, Watch Dogs 2 - PlaySta…；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,shooter。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #287 — 类目错·(a)大类都不对
- **历史**(1项; 平台 ?×1): Diablo III: Reaper of Soul…
- **GT**: `<a_113><b_9><c_63>` Mayflash GameCube Controller Adapter for Wii U… _(平台 WiiU)_ ｜ **native**: `<a_10><b_20><c_0>` Diablo III: Ultimate Evil Edit… ✗
- **beam top5**: `<a_10><b_20><c_0>`?, `<a_10><b_67><c_155>`?, `<a_10><b_33><c_56>`?, `<a_10><b_33><c_116>`?, `<a_10><b_67><c_51>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=8/10，平台数=3，unique标题=8/10。
- **reasoning质量**: 引用历史 1/1（覆盖100%），锚定: Diablo III: Reaper of …；新候选=0（**纯复述历史**）；genre: action,immersive,narrative。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #288 — 类目错·(a)大类都不对
- **历史**(2项; 平台 ?×1,WiiU×1): Diablo III: Reaper of Soul… | Mayflash GameCube Controll…
- **GT**: `<a_111><b_71><c_5>` Rock Band 4 Band-in-a-Box Bundle - Xbox One _(平台 XboxOne)_ ｜ **native**: `<a_202><b_16><c_110>` Razer DeathAdder Expert - Opti… ✗
- **beam top5**: `<a_61><b_0><c_187>`?, `<a_61><b_9><c_199>`PS3, `<a_61><b_9><c_122>`PS3, `<a_202><b_16><c_110>`?, `<a_113><b_9><c_63>`Wii
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=8/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: Diablo III: Reaper of …, Mayflash GameCube Cont…；新候选=0（**纯复述历史**）；genre: action,immersive,nostalg。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=探索(无关联)(score0)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #289 — 类目对·item错
- **历史**(4项; 平台 PS4×2,XboxOne×1,3DS×1): The Last of Us Remastered … | Digimon Story: Cyber Sleut… | Xbox One Stereo Headset Ad… | Pokemon Alpha Sapphire - N…
- **GT**: `<a_216><b_44><c_79>` Bravely Second: End Layer - Nintendo 3DS _(平台 3DS)_ ｜ **native**: `<a_211><b_133><c_123>` Pok&eacute;mon Omega Ruby - Ni… ✗
- **beam top5**: `<a_211><b_133><c_123>`3DS, `<a_211><b_159><c_123>`3DS, `<a_1><b_25><c_254>`3DS, `<a_211><b_159><c_71>`3DS, `<a_1><b_150><c_189>`PS3
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(3DS)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（2 个 a 大类）；unique(a,b)=8/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: The Last of Us Remaste…, Digimon Story: Cyber S…, Pokemon Alpha Sapphire…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=子类延续(score3)。我们推的比用户真实点击**更贴历史**(荐3>target1) → **模型偏保守/用户更爱探索**。

### #290 — 类目错·(a)大类都不对
- **历史**(1项; 平台 PS×1): PlayStation TV
- **GT**: `<a_141><b_73><c_216>` Star Wars: Battlefront - Standard Edition - Pl… _(平台 PS4)_ ｜ **native**: `<a_61><b_47><c_32>` PlayStation 3 Dualshock 3 Wire… ✗
- **beam top5**: `<a_189><b_99><c_126>`PS, `<a_231><b_28><c_63>`PS4, `<a_61><b_214><c_252>`Xbo, `<a_208><b_175><c_0>`PS4, `<a_61><b_38><c_203>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS4 vs 荐=PS-generic)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=9/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 0/1（覆盖0%）；新候选=0（**纯复述历史**）；genre: action,multiplayer,family-friendly。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=子类延续(score3)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #291 — 类目错·(a)大类都不对
- **历史**(2项; 平台 PS×1,PS4×1): PlayStation TV | Star Wars: Battlefront - S…
- **GT**: `<a_216><b_219><c_158>` Hyrule Warriors: Legends - Nintendo 3DS _(平台 3DS)_ ｜ **native**: `<a_201><b_2><c_102>` PlayStation 4 500GB Console - … ✗
- **beam top5**: `<a_201><b_36><c_195>`PS4, `<a_208><b_175><c_0>`PS4, `<a_131><b_210><c_0>`PS4, `<a_201><b_31><c_107>`PS4, `<a_201><b_2><c_102>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=3DS vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=10/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: Star Wars: Battlefront…, PlayStation TV；新候选=0（**纯复述历史**）；genre: action,strategy,multiplayer。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=漂移(平台/词面关联)(score1)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #292 — 类目错·(a)大类都不对
- **历史**(3项; 平台 PS×1,PS4×1,3DS×1): PlayStation TV | Star Wars: Battlefront - S… | Hyrule Warriors: Legends -…
- **GT**: `<a_195><b_216><c_209>` Alice: Madness Returns - Playstation 3 _(平台 PS3)_ ｜ **native**: `<a_1><b_25><c_254>` Fire Emblem Fates: Conquest - … ✗
- **beam top5**: `<a_1><b_25><c_254>`3DS, `<a_1><b_101><c_0>`Wii, `<a_131><b_41><c_229>`PS4, `<a_208><b_175><c_0>`PS4, `<a_201><b_31><c_107>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS3 vs 荐=3DS)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=9/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 2/3（覆盖67%），锚定: Star Wars: Battlefront…, Hyrule Warriors: Legen…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=漂移(平台/词面关联)(score1)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #293 — 类目错·(a)大类都不对
- **历史**(4项; 平台 PS×1,PS4×1,3DS×1): PlayStation TV | Star Wars: Battlefront - S… | Hyrule Warriors: Legends -… | Alice: Madness Returns - P…
- **GT**: `<a_249><b_155><c_14>` 4GB PlayStation Vita Memory Card _(平台 PSVita)_ ｜ **native**: `<a_195><b_4><c_0>` Kingdom Hearts ✗
- **beam top5**: `<a_195><b_241><c_163>`PS, `<a_195><b_4><c_0>`?, `<a_194><b_21><c_76>`PS4, `<a_195><b_4><c_2>`PSP, `<a_194><b_32><c_11>`PSV
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PSVita vs 荐=PS2)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=7/10，平台数=6，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Star Wars: Battlefront…, Hyrule Warriors: Legen…, Alice: Madness Returns…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #294 — 类目错·(a)大类都不对
- **历史**(5项; 平台 PS×1,PS4×1,3DS×1): PlayStation TV | Star Wars: Battlefront - S… | Hyrule Warriors: Legends -… | Alice: Madness Returns - P… | 4GB PlayStation Vita Memor…
- **GT**: `<a_74><b_204><c_217>` PlayStation All-Stars Battle Royale PS Vita - … _(平台 PSVita)_ ｜ **native**: `<a_249><b_31><c_126>` Sony PlayStation Vita WiFi ✗
- **beam top5**: `<a_249><b_170><c_61>`PS, `<a_201><b_31><c_107>`PS4, `<a_249><b_63><c_20>`PSV, `<a_249><b_31><c_126>`PSV, `<a_249><b_68><c_59>`PSV
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PSVita vs 荐=PS2)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=9/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 4/5（覆盖80%），锚定: Star Wars: Battlefront…, Hyrule Warriors: Legen…, Alice: Madness Returns…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #295 — 类目错·(a)大类都不对
- **历史**(6项; 平台 PSVita×2,PS×1,PS4×1): PlayStation TV | Star Wars: Battlefront - S… | Hyrule Warriors: Legends -… | Alice: Madness Returns - P… | 4GB PlayStation Vita Memor… | PlayStation All-Stars Batt…
- **GT**: `<a_245><b_139><c_1>` LEGO Star Wars: The Force Awakens - PlayStatio… _(平台 PSVita)_ ｜ **native**: `<a_1><b_121><c_178>` Monster Hunter 4 Ultimate Stan… ✗
- **beam top5**: `<a_74><b_218><c_91>`PS3, `<a_1><b_99><c_2>`PS4, `<a_1><b_173><c_4>`PS4, `<a_74><b_218><c_206>`PS4, `<a_1><b_209><c_76>`PS3
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PSVita vs 荐=PS3)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=9/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 5/6（覆盖83%），锚定: Star Wars: Battlefront…, Hyrule Warriors: Legen…, PlayStation All-Stars …；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['star', 'wars']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #296 — 类目对·item错 · BEAM坍缩(<a_39×7/10)
- **历史**(4项; 平台 XboxOne×3,?×1): NBA 2K16 - Xbox One | Dead Rising 3: Apocalypse … | Call of Duty: Infinite War… | Turtle Beach - Ear Force H…
- **GT**: `<a_39><b_69><c_69>` Call of Duty: Black Ops III - Standard Edition… _(平台 XboxOne)_ ｜ **native**: `<a_39><b_77><c_105>` Call of Duty: Infinite Warfare… ✗
- **beam top5**: `<a_39><b_77><c_105>`Xbo, `<a_39><b_51><c_21>`Xbo, `<a_39><b_77><c_233>`Xbo, `<a_7><b_2><c_105>`Xbo, `<a_39><b_77><c_69>`Xbo
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台一致(XboxOne)；beam中 share-a=7/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_39 家族 7/10）；unique(a,b)=7/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: NBA 2K16 - Xbox One, Dead Rising 3: Apocaly…, Call of Duty: Infinite…；新候选=0（**纯复述历史**）；genre: action,shooter,sports。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=子类延续(score3)。我们推的比用户真实点击**更贴历史**(荐3>target2) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['call', 'duty']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #297 — 类目对·item错
- **历史**(5项; 平台 XboxOne×4,?×1): NBA 2K16 - Xbox One | Dead Rising 3: Apocalypse … | Call of Duty: Infinite War… | Turtle Beach - Ear Force H… | Call of Duty: Black Ops II…
- **GT**: `<a_202><b_164><c_89>` ASTRO Gaming A40 TR Headset + MixAmp Pro TR fo… _(平台 XboxOne)_ ｜ **native**: `<a_39><b_77><c_105>` Call of Duty: Infinite Warfare… ✗
- **beam top5**: `<a_7><b_248><c_16>`Xbo, `<a_39><b_77><c_105>`Xbo, `<a_7><b_2><c_105>`Xbo, `<a_131><b_155><c_206>`Xbo, `<a_39><b_77><c_233>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=8/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/5（覆盖80%），锚定: Call of Duty: Infinite…, Call of Duty: Black Op…, Dead Rising 3: Apocaly…；新候选=0（**纯复述历史**）；模板开头；genre: action,shooter,strategy。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['headset']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #298 — 类目错·(a)大类都不对 · BEAM坍缩(<a_131×8/10)
- **历史**(2项; 平台 PC×1,PS4×1): Call of Duty: Black Ops II… | Fallout 4 - PlayStation 4
- **GT**: `<a_74><b_218><c_196>` Ratchet & Clank Up Your Arsenal - PlayStation … _(平台 PS2)_ ｜ **native**: `<a_131><b_155><c_206>` Fallout 4 - Xbox One ✗
- **beam top5**: `<a_131><b_28><c_96>`PS4, `<a_131><b_155><c_206>`Xbo, `<a_141><b_73><c_216>`PS4, `<a_141><b_73><c_7>`PS4, `<a_131><b_145><c_6>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS2 vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_131 家族 8/10）；unique(a,b)=7/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: Call of Duty: Black Op…, Fallout 4 - PlayStatio…；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,shooter。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #299 — 类目对·item错 · BEAM坍缩(<a_121×8/10)
- **历史**(1项; 平台 PS4×1): NieR: Automata - Playstati…
- **GT**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - PS4 Digital Code _(平台 PS4)_ ｜ **native**: `<a_121><b_76><c_208>` Star Ocean: Integrity and Fait… ✗
- **beam top5**: `<a_121><b_76><c_208>`PS4, `<a_121><b_35><c_0>`PS4, `<a_1><b_150><c_189>`PS3, `<a_121><b_91><c_244>`PS4, `<a_121><b_192><c_253>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_121 家族 8/10）；unique(a,b)=10/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 1/1（覆盖100%），锚定: NieR: Automata - Plays…；新候选=0（**纯复述历史**）；genre: action,adventure,strategy。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #300 — 类目错·(a)大类都不对
- **历史**(2项; 平台 PS4×2): NieR: Automata - Playstati… | Resident Evil 7: Biohazard…
- **GT**: `<a_195><b_122><c_178>` Zero Escape: Virtue's Last Reward - Nintendo 3… _(平台 3DS)_ ｜ **native**: `<a_123><b_58><c_16>` Resident Evil 7 Biohazard - Xb… ✗
- **beam top5**: `<a_123><b_58><c_16>`Xbo, `<a_123><b_78><c_71>`PS4, `<a_24><b_129><c_173>`PS4, `<a_123><b_33><c_93>`PS4, `<a_24><b_185><c_47>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=3DS vs 荐=XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=10/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: NieR: Automata - Plays…, Resident Evil 7: Bioha…；新候选=0（**纯复述历史**）；genre: action,horror,immersive。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=子类延续(score3)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #301 — 类目错·(a)大类都不对
- **历史**(7项; 平台 ?×6,PS4×1): Super Mario World 2: Yoshi… | Super Mario Bros. 2 | Animal Crossing | The Legend of Zelda: Ocari… | Donkey Kong Country Return… | Assassins Creed Unity PS4
- **GT**: `<a_71><b_158><c_1>` The Evil Within - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_211><b_105><c_215>` Animal Crossing: New Leaf ✗
- **beam top5**: `<a_211><b_105><c_215>`?, `<a_216><b_112><c_114>`Wii, `<a_250><b_156><c_1>`?, `<a_216><b_156><c_1>`?, `<a_250><b_116><c_226>`Wii
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=8/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 6/7（覆盖86%），锚定: Donkey Kong Country, Super Mario World 2: Y…, Super Mario Bros. 2；新候选=0（**纯复述历史**）；genre: action,adventure,puzzle。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #302 — 类目错·(a)大类都不对 · BEAM坍缩(<a_84×8/10)
- **历史**(10项; 平台 PS4×4,WiiU×3,DS×1): Plants vs. Zombies Garden … | AmazonBasics Heavy-Duty Va… | Nintendo Wii U Fit Balance… | The Legend of Zelda: Breat… | Madden NFL 17 - Standard E… | Wii Sports Club - Wii U
- **GT**: `<a_118><b_78><c_177>` The Walking Dead: The Complete First Season - … _(平台 PS4)_ ｜ **native**: `<a_84><b_1><c_164>` Wii Sports Club - Wii U ✗
- **beam top5**: `<a_84><b_25><c_96>`Wii, `<a_84><b_149><c_181>`Wii, `<a_84><b_250><c_210>`Wii, `<a_84><b_54><c_87>`Wii, `<a_84><b_250><c_189>`Wii
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS4 vs 荐=WiiU)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_84 家族 8/10）；unique(a,b)=9/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 6/10（覆盖60%），锚定: Dragon Quest IV: Chapt…, Battlefield 1 - PlaySt…, Plants vs. Zombies Gar…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #303 — 类目对·item错
- **历史**(10项; 平台 PS4×5,WiiU×3,Wii×1): AmazonBasics Heavy-Duty Va… | Nintendo Wii U Fit Balance… | The Legend of Zelda: Breat… | Madden NFL 17 - Standard E… | Wii Sports Club - Wii U | The Walking Dead: The Comp…
- **GT**: `<a_194><b_33><c_2>` Dark Souls II: Scholar of the First Sin - Xbox… _(平台 XboxOne)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_39><b_51><c_21>`Xbo, `<a_123><b_58><c_78>`PS4, `<a_39><b_175><c_240>`Xbo, `<a_201><b_56><c_74>`PS4, `<a_123><b_58><c_16>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=8/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 6/10（覆盖60%），锚定: Battlefield 1 - PlaySt…, Titanfall 2 - PlayStat…, Plants vs. Zombies Gar…；新候选=0（**纯复述历史**）；模板开头；genre: action,adventure,shooter。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=子类延续(score3)。我们推的比用户真实点击**更贴历史**(荐3>target1) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['first']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #304 — 类目错·(a)大类都不对
- **历史**(10项; 平台 PS4×5,WiiU×3,PSVita×1): Nintendo Wii U Fit Balance… | The Legend of Zelda: Breat… | Madden NFL 17 - Standard E… | Wii Sports Club - Wii U | The Walking Dead: The Comp… | Dark Souls II: Scholar of …
- **GT**: `<a_22><b_192><c_187>` Middle Earth: Shadow of Mordor Game of the Yea… _(平台 XboxOne)_ ｜ **native**: `<a_194><b_15><c_66>` Dishonored 2 - PlayStation 4 ✗
- **beam top5**: `<a_194><b_87><c_249>`PS4, `<a_194><b_87><c_112>`PS4, `<a_194><b_15><c_66>`PS4, `<a_123><b_58><c_78>`PS4, `<a_131><b_41><c_229>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=XboxOne vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=8/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 5/10（覆盖50%），锚定: Battlefield 1 - PlaySt…, Titanfall 2 - PlayStat…, Plants vs. Zombies Gar…；新候选=0（**纯复述历史**）；模板开头；genre: action,adventure,shooter。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #305 — 类目错·(a)大类都不对 · BEAM坍缩(<a_217×7/10)
- **历史**(10项; 平台 ?×8,WiiU×1,PS4×1): Snoopy's Grand Adventure -… | Skylanders SuperChargers D… | Skylanders SuperChargers: … | MLB The Show 16 - PlayStat… | Nintendo Selects: Pikmin 3 | Nintendo Selects: Donkey K…
- **GT**: `<a_162><b_222><c_61>` Nintendo Waluigi amiibo (SM Series) - Nintendo… _(平台 WiiU)_ ｜ **native**: `<a_217><b_71><c_226>` Skylanders SuperChargers: Raci… ✗
- **beam top5**: `<a_217><b_71><c_22>`?, `<a_217><b_71><c_11>`?, `<a_217><b_71><c_226>`?, `<a_217><b_71><c_85>`?, `<a_217><b_71><c_151>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_217 家族 7/10）；unique(a,b)=4/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 6/10（覆盖60%），锚定: Skylanders Trap Team: …, Skylanders SWAP Force …, Skylanders SWAP Force …；新候选=0（**纯复述历史**）；模板开头；genre: action,adventure,immersive。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=子类延续(score3)。我们推的比用户真实点击**更贴历史**(荐3>target1) → **模型偏保守/用户更爱探索**。

### #306 — 类目对·item错
- **历史**(3项; 平台 ?×2,Xbox360×1): Microsoft Xbox 360 Wireles… | Havit Rainbow Backlit Wire… | HAVIT RGB Backlit Wired Me…
- **GT**: `<a_202><b_113><c_73>` RAZER MAMBA TOURNAMENT EDITION: 16,000 Adjusta… _(平台 ?)_ ｜ **native**: `<a_214><b_226><c_146>` Havit Rainbow Backlit Wired Ga… ✗
- **beam top5**: `<a_61><b_131><c_197>`Xbo, `<a_214><b_24><c_0>`?, `<a_61><b_181><c_195>`Xbo, `<a_214><b_64><c_229>`?, `<a_214><b_226><c_73>`?
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；beam中 share-a=1/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=9/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Microsoft Xbox 360 Wir…, Havit Rainbow Backlit …, HAVIT RGB Backlit Wire…；新候选=0（**纯复述历史**）；genre: action,peripheral,accessor。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['gaming', 'mouse']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #307 — 近失·同(a,b)细分仅c不同 · BEAM坍缩(<a_202×10/10)
- **历史**(4项; 平台 ?×3,Xbox360×1): Microsoft Xbox 360 Wireles… | Havit Rainbow Backlit Wire… | HAVIT RGB Backlit Wired Me… | RAZER MAMBA TOURNAMENT EDI…
- **GT**: `<a_202><b_213><c_48>` Razer Blackwidow _(平台 ?)_ ｜ **native**: `<a_202><b_200><c_67>` Logitech G600 MMO Gaming Mouse… ✗
- **beam top5**: `<a_202><b_253><c_158>`?, `<a_202><b_30><c_0>`?, `<a_202><b_34><c_39>`?, `<a_202><b_200><c_67>`?, `<a_202><b_203><c_93>`?
- **推荐↔GT差距**: beam 最接近项与 GT 同 (a,b) 细分、仅 c 不同（同系列/不同款），未命中；beam中 share-a=10/10, share-(a,b)=1/10。
- **beam多样性**: **低**（坍缩到 <a_202 家族 10/10）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Microsoft Xbox 360 Wir…, Havit Rainbow Backlit …, HAVIT RGB Backlit Wire…；新候选=0（**纯复述历史**）；genre: action,peripheral,accessor。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。 注意 target 与历史共享词 ['razer']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #308 — 类目错·(a)大类都不对 · BEAM坍缩(<a_245×9/10)
- **历史**(10项; 平台 XboxOne×6,?×2,Xbox360×1): Xbox One 500GB Console - A… | Ultimate NES Remix - Ninte… | LEGO Dimensions Starter Pa… | Assassin&rsquo;s Creed Syn… | Ghostbusters Slimer Fun Pa… | Nyko Modular Charge Statio…
- **GT**: `<a_13><b_224><c_3>` Plants vs. Zombies Garden Warfare 2 - Xbox One _(平台 XboxOne)_ ｜ **native**: `<a_245><b_121><c_191>` LEGO Dimensions Starter Pack -… ✗
- **beam top5**: `<a_245><b_93><c_22>`?, `<a_245><b_86><c_40>`Xbo, `<a_245><b_29><c_110>`?, `<a_49><b_36><c_1>`Xbo, `<a_245><b_193><c_0>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_245 家族 9/10）；unique(a,b)=9/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 4/10（覆盖40%），锚定: Wolfenstein: The New O…, Assassin&rsquo;s Creed…, LEGO Dimensions Starte…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #309 — 命中·复购/同款易例
- **历史**(1项; 平台 Wii×1): Wii Play
- **GT**: `<a_84><b_243><c_6>` Wii Play _(平台 Wii)_ ｜ **native**: `<a_84><b_243><c_6>` Wii Play ✓
- **beam top5**: `<a_84><b_243><c_6>`Wii, `<a_84><b_136><c_91>`Wii, `<a_175><b_225><c_3>`Wii, `<a_175><b_48><c_69>`Wii, `<a_84><b_222><c_164>`Wii
- **推荐↔GT差距**: top-1 完全命中。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=8/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 1/1（覆盖100%），锚定: Wii Play；新候选=0（**纯复述历史**）；genre: action,multiplayer。
- **target合理性(天花板)**: target=子类延续(score3); 我们pred[0]=子类延续(score3)。target 是合理的子类延续，且**已命中**。

### #310 — 类目错·(a)大类都不对
- **历史**(2项; 平台 Wii×2): Wii Play | Wii Play
- **GT**: `<a_140><b_103><c_43>` Xbox 360 4GB Console _(平台 Xbox360)_ ｜ **native**: `<a_84><b_132><c_6>` Wii Sports Resort ✗
- **beam top5**: `<a_175><b_220><c_18>`Wii, `<a_175><b_225><c_3>`Wii, `<a_175><b_24><c_4>`Wii, `<a_175><b_113><c_76>`?, `<a_84><b_243><c_6>`Wii
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=Xbox360 vs 荐=Wii)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（2 个 a 大类）；unique(a,b)=8/10，平台数=2，unique标题=9/10。
- **reasoning质量**: 引用历史 1/1（覆盖100%），锚定: Wii Play；新候选=0（**纯复述历史**）；genre: action,multiplayer,accessor。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=漂移(平台/词面关联)(score1)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #311 — 类目错·(a)大类都不对
- **历史**(3项; 平台 Wii×2,Xbox360×1): Wii Play | Wii Play | Xbox 360 4GB Console
- **GT**: `<a_193><b_0><c_187>` Mario & Sonic at the Olympic Games for wii _(平台 Wii)_ ｜ **native**: `<a_61><b_181><c_195>` Xbox 360 Wireless Controller -… ✗
- **beam top5**: `<a_61><b_181><c_195>`Xbo, `<a_175><b_103><c_55>`Xbo, `<a_175><b_103><c_21>`Xbo, `<a_111><b_149><c_227>`?, `<a_140><b_105><c_178>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=Wii vs 荐=Xbox360)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（6 个不同 a 大类）；unique(a,b)=8/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: Wii Play, Xbox 360 4GB Console；新候选=0（**纯复述历史**）；模板开头；genre: action,multiplayer,family-friendly。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。

### #312 — 类目对·item错
- **历史**(4项; 平台 Wii×3,Xbox360×1): Wii Play | Wii Play | Xbox 360 4GB Console | Mario & Sonic at the Olymp…
- **GT**: `<a_175><b_225><c_3>` Wii Fit Game with Balance Board _(平台 Wii)_ ｜ **native**: `<a_175><b_24><c_4>` New Super Mario Bros. Wii ✗
- **beam top5**: `<a_175><b_24><c_4>`Wii, `<a_84><b_222><c_135>`Wii, `<a_84><b_206><c_162>`Wii, `<a_84><b_222><c_164>`Wii, `<a_84><b_132><c_6>`Wii
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台一致(Wii)；beam中 share-a=2/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=7/10，平台数=3，unique标题=9/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Wii Play, Xbox 360 4GB Console, Mario & Sonic at the O…；新候选=0（**纯复述历史**）；模板开头；genre: action,racing,multiplayer。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。

### #313 — 类目错·(a)大类都不对 · BEAM坍缩(<a_61×9/10)
- **历史**(4项; 平台 Xbox360×2,PC×1,PS3×1): Hisurprise 2x Black Batter… | Xbox 360 Microsoft Authent… | Minecraft for PC/Mac [Onli… | PlayStation 3 500 GB Syste…
- **GT**: `<a_194><b_97><c_127>` Demon's Souls _(平台 ?)_ ｜ **native**: `<a_61><b_181><c_195>` Xbox 360 Wireless Controller -… ✗
- **beam top5**: `<a_61><b_181><c_195>`Xbo, `<a_61><b_167><c_197>`Xbo, `<a_61><b_214><c_252>`Xbo, `<a_61><b_53><c_46>`Xbo, `<a_61><b_137><c_255>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_61 家族 9/10）；unique(a,b)=7/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Hisurprise 2x Black Ba…, Xbox 360 Microsoft Aut…, Minecraft for PC/Mac […；新候选=0（**纯复述历史**）；genre: action,immersive,accessor。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #314 — 类目错·(a)大类都不对
- **历史**(5项; 平台 Xbox360×2,PC×1,PS3×1): Hisurprise 2x Black Batter… | Xbox 360 Microsoft Authent… | Minecraft for PC/Mac [Onli… | PlayStation 3 500 GB Syste… | Demon's Souls
- **GT**: `<a_24><b_51><c_181>` God of War III - Playstation 3 _(平台 PS3)_ ｜ **native**: `<a_61><b_181><c_195>` Xbox 360 Wireless Controller -… ✗
- **beam top5**: `<a_61><b_181><c_195>`Xbo, `<a_202><b_200><c_67>`?, `<a_202><b_16><c_110>`?, `<a_194><b_20><c_194>`Xbo, `<a_194><b_33><c_4>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS3 vs 荐=Xbox360)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=9/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 3/5（覆盖60%），锚定: Hisurprise 2x Black Ba…, Xbox 360 Microsoft Aut…, Demon's Souls；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,immersive。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #315 — 类目错·(a)大类都不对
- **历史**(1项; 平台 Xbox360×1): South Park:  The Stick of …
- **GT**: `<a_201><b_85><c_136>` Until Dawn - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_131><b_155><c_206>` Fallout 4 - Xbox One ✗
- **beam top5**: `<a_131><b_155><c_206>`Xbo, `<a_74><b_100><c_233>`?, `<a_86><b_18><c_30>`Xbo, `<a_131><b_233><c_112>`?, `<a_74><b_5><c_203>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS4 vs 荐=XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=9/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 1/1（覆盖100%），锚定: South Park:  The Stick…；新候选=0（**纯复述历史**）；模板开头；genre: action,adventure,narrative。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=探索(无关联)(score0)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #316 — 类目对·item错
- **历史**(2项; 平台 Xbox360×1,PS4×1): South Park:  The Stick of … | Until Dawn - PlayStation 4
- **GT**: `<a_86><b_12><c_93>` South Park: The Fractured but Whole - PlayStat… _(平台 PS4)_ ｜ **native**: `<a_131><b_210><c_0>` Fallout 4 - PlayStation 4 ✗
- **beam top5**: `<a_131><b_210><c_0>`PS4, `<a_201><b_31><c_107>`PS4, `<a_131><b_155><c_206>`Xbo, `<a_201><b_213><c_242>`PS4, `<a_22><b_192><c_20>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=10/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: South Park:  The Stick…, Until Dawn - PlayStati…；新候选=0（**纯复述历史**）；genre: action,horror,immersive。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=漂移(平台/词面关联)(score1)。用户点击比我们top1**更贴历史**(target2>荐1) → 我们把可命中的延续**跑偏**了。 注意 target 与历史共享词 ['park', 'south']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #317 — 类目错·(a)大类都不对
- **历史**(3项; 平台 PS4×2,Xbox360×1): South Park:  The Stick of … | Until Dawn - PlayStation 4 | South Park: The Fractured …
- **GT**: `<a_24><b_72><c_142>` Horizon Zero Dawn - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_86><b_18><c_30>` Back to the Future: The Game -… ✗
- **beam top5**: `<a_86><b_18><c_29>`Xbo, `<a_86><b_18><c_30>`Xbo, `<a_131><b_210><c_0>`PS4, `<a_86><b_18><c_2>`PS4, `<a_86><b_68><c_56>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS4 vs 荐=XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=7/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: South Park:  The Stick…, Until Dawn - PlayStati…, South Park: The Fractu…；新候选=0（**纯复述历史**）；模板开头；genre: action,adventure,role-playing。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['dawn']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #318 — 类目对·item错
- **历史**(4项; 平台 PS4×3,Xbox360×1): South Park:  The Stick of … | Until Dawn - PlayStation 4 | South Park: The Fractured … | Horizon Zero Dawn - PlaySt…
- **GT**: `<a_121><b_155><c_99>` NieR: Automata - Playstation 4 _(平台 PS4)_ ｜ **native**: `<a_24><b_72><c_142>` Horizon Zero Dawn - PlayStatio… ✗
- **beam top5**: `<a_24><b_86><c_14>`PS4, `<a_24><b_145><c_101>`PS4, `<a_201><b_31><c_107>`PS4, `<a_24><b_185><c_47>`Xbo, `<a_123><b_142><c_36>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=10/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: South Park:  The Stick…, South Park: The Fractu…, Until Dawn - PlayStati…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #319 — 类目错·(a)大类都不对 · BEAM坍缩(<a_162×7/10)
- **历史**(5项; 平台 ?×2,WiiU×1,Wii×1): JINHEZO Wired Infrared Ray… | New Interchangeable Power … | Pikmin, New Play Control -… | Pikmin & Olimar Amiibo (Su… | Minecraft: Favorites Pack …
- **GT**: `<a_113><b_112><c_109>` Nintendo Wii U Pro Controller - Black _(平台 WiiU)_ ｜ **native**: `<a_162><b_125><c_53>` Yoshi amiibo (Super Smash Bros… ✗
- **beam top5**: `<a_162><b_5><c_144>`3DS, `<a_162><b_105><c_210>`?, `<a_162><b_125><c_53>`?, `<a_162><b_122><c_56>`?, `<a_211><b_31><c_154>`3DS
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=WiiU vs 荐=3DS)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_162 家族 7/10）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/5（覆盖80%），锚定: JINHEZO Wired Infrared…, New Interchangeable Po…, Pikmin, New Play Contr…；新候选=0（**纯复述历史**）；模板开头；genre: action,immersive,accessor。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #320 — 类目错·(a)大类都不对
- **历史**(10项; 平台 ?×8,XboxOne×2): Final Fantasy XIV Online | Life is Strange - Episode … | Watch Dogs 2 - Xbox One Di… | Battlefield 1 [Online Game… | Logitech G700s Rechargeabl… | Xenoblade Chronicles X
- **GT**: `<a_113><b_152><c_199>` HORI Compact PlayStand - Zelda Edition, Offici… _(平台 Switch)_ ｜ **native**: `<a_1><b_101><c_0>` Xenoblade Chronicles X Special… ✗
- **beam top5**: `<a_1><b_101><c_0>`Wii, `<a_1><b_25><c_254>`3DS, `<a_131><b_224><c_16>`PC, `<a_1><b_173><c_4>`PS4, `<a_1><b_150><c_189>`PS3
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=Switch vs 荐=WiiU)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（2 个 a 大类）；unique(a,b)=8/10，平台数=7，unique标题=10/10。
- **reasoning质量**: 引用历史 6/10（覆盖60%），锚定: Final Fantasy XIV Onli…, Xenoblade Chronicles X, Star Wars: The Old Rep…；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,multiplayer。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=子类延续(score3)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #321 — 类目错·(a)大类都不对 · BEAM坍缩(<a_10×10/10)
- **历史**(1项; 平台 PC×1): The Elder Scrolls V: Skyri…
- **GT**: `<a_162><b_125><c_53>` Yoshi amiibo (Super Smash Bros Series) _(平台 ?)_ ｜ **native**: `<a_10><b_86><c_40>` The Elder Scrolls V: Skyrim Le… ✗
- **beam top5**: `<a_10><b_53><c_1>`Xbo, `<a_10><b_28><c_234>`Xbo, `<a_10><b_79><c_56>`PC, `<a_10><b_86><c_7>`PS3, `<a_10><b_86><c_68>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_10 家族 10/10）；unique(a,b)=7/10，平台数=5，unique标题=10/10。
- **reasoning质量**: 引用历史 1/1（覆盖100%），锚定: The Elder Scrolls V: S…；新候选=0（**纯复述历史**）；genre: action,role-playing,rpg。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #322 — 类目对·item错 · BEAM坍缩(<a_162×10/10)
- **历史**(2项; 平台 PC×1,?×1): The Elder Scrolls V: Skyri… | Yoshi amiibo (Super Smash …
- **GT**: `<a_162><b_54><c_123>` Splatoon 3-pack amiibo (Splatoon Series) _(平台 ?)_ ｜ **native**: `<a_162><b_122><c_3>` Little Mac amiibo - Japan Impo… ✗
- **beam top5**: `<a_162><b_231><c_30>`?, `<a_162><b_219><c_174>`?, `<a_162><b_122><c_3>`PC, `<a_162><b_219><c_249>`?, `<a_162><b_122><c_195>`?
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；beam中 share-a=10/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_162 家族 10/10）；unique(a,b)=7/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: The Elder Scrolls V: S…, Yoshi amiibo (Super Sm…；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,immersive。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。 注意 target 与历史共享词 ['amiibo', 'series']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #323 — 类目错·(a)大类都不对 · BEAM坍缩(<a_162×10/10)
- **历史**(3项; 平台 ?×2,PC×1): The Elder Scrolls V: Skyri… | Yoshi amiibo (Super Smash … | Splatoon 3-pack amiibo (Sp…
- **GT**: `<a_157><b_85><c_178>` PDP Donkey Kong Display _(平台 ?)_ ｜ **native**: `<a_162><b_172><c_85>` Tom Nook Amiibo (Animal Crossi… ✗
- **beam top5**: `<a_162><b_231><c_30>`?, `<a_162><b_251><c_136>`Wii, `<a_162><b_172><c_85>`?, `<a_162><b_122><c_56>`?, `<a_162><b_172><c_0>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_162 家族 10/10）；unique(a,b)=7/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Yoshi amiibo (Super Sm…, Splatoon 3-pack amiibo…, The Elder Scrolls V: S…；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,immersive。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #324 — 类目对·item错 · BEAM坍缩(<a_162×10/10)
- **历史**(4项; 平台 ?×3,PC×1): The Elder Scrolls V: Skyri… | Yoshi amiibo (Super Smash … | Splatoon 3-pack amiibo (Sp… | PDP Donkey Kong Display
- **GT**: `<a_162><b_219><c_174>` Shulk amiibo (Super Smash Bros Series) _(平台 ?)_ ｜ **native**: `<a_162><b_172><c_85>` Tom Nook Amiibo (Animal Crossi… ✗
- **beam top5**: `<a_162><b_172><c_85>`?, `<a_162><b_105><c_210>`?, `<a_162><b_251><c_136>`Wii, `<a_162><b_231><c_30>`?, `<a_162><b_172><c_0>`?
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；beam中 share-a=10/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_162 家族 10/10）；unique(a,b)=8/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Yoshi amiibo (Super Sm…, Splatoon 3-pack amiibo…, PDP Donkey Kong Displa…；新候选=0（**纯复述历史**）；模板开头；genre: action,immersive,nostalg。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。 注意 target 与历史共享词 ['amiibo', 'bros', 'series', 'smash', 'super']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #325 — 类目错·(a)大类都不对
- **历史**(9项; 平台 XboxOne×7,?×1,PS4×1): Nyko Modular Power Station… | Battlefield Hardline - Xbo… | Gears of War 4 - Xbox One | Wolfenstein: The Old Blood… | Homefront: The Revolution … | Rise of the Tomb Raider: 2…
- **GT**: `<a_24><b_72><c_142>` Horizon Zero Dawn - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_39><b_77><c_105>` Call of Duty: Infinite Warfare… ✗
- **beam top5**: `<a_39><b_77><c_105>`Xbo, `<a_39><b_51><c_21>`Xbo, `<a_123><b_58><c_16>`Xbo, `<a_39><b_77><c_69>`Xbo, `<a_123><b_188><c_70>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS4 vs 荐=XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（2 个 a 大类）；unique(a,b)=8/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 6/9（覆盖67%），锚定: Halo 5: Guardians - Li…, Wolfenstein: The New O…, Battlefield Hardline -…；新候选=0（**纯复述历史**）；模板开头；genre: action,shooter,multiplayer。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=漂移(平台/词面关联)(score1)。用户点击比我们top1**更贴历史**(target2>荐1) → 我们把可命中的延续**跑偏**了。

### #326 — 类目错·(a)大类都不对 · BEAM坍缩(<a_22×7/10)
- **历史**(7项; 平台 PS4×3,?×3,DS×1): The Sims 4 [Online Game Co… | Sleeping Dogs: Definitive … | The Sims 4 Get to Work [On… | The Sims 4 Kids Room Stuff… | HAVIT HV-MS672 3200DPI Wir… | Prey - Pre-load - PS4 Digi…
- **GT**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - PS4 Digital Code _(平台 PS4)_ ｜ **native**: `<a_22><b_173><c_203>` The Sims 4 - Movie Hangout Stu… ✗
- **beam top5**: `<a_22><b_173><c_203>`?, `<a_22><b_190><c_180>`?, `<a_22><b_89><c_201>`?, `<a_22><b_173><c_9>`?, `<a_201><b_31><c_107>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_22 家族 7/10）；unique(a,b)=8/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 5/7（覆盖71%），锚定: The Sims 4 [Online Gam…, The Sims 4 Kids Room S…, Assassins Creed Syndic…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['code', 'digital']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #327 — 类目错·(a)大类都不对
- **历史**(1项; 平台 PS4×1): Uncharted 4: A Thief's End…
- **GT**: `<a_13><b_68><c_173>` Lost Planet: Extreme Condition - Playstation 3 _(平台 PS3)_ ｜ **native**: `<a_201><b_213><c_242>` The Last of Us Remastered - Pl… ✗
- **beam top5**: `<a_123><b_72><c_7>`PS4, `<a_201><b_213><c_242>`PS4, `<a_201><b_145><c_9>`PS4, `<a_24><b_145><c_101>`PS4, `<a_201><b_31><c_107>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS3 vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=10/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 1/1（覆盖100%），锚定: Uncharted 4: A Thief's…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=漂移(平台/词面关联)(score1)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #328 — 命中@6
- **历史**(2项; 平台 PS4×2): Alien: Isolation - PlaySta… | Dying Light: The Following…
- **GT**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - PS4 Digital Code _(平台 PS4)_ ｜ **native**: `<a_123><b_142><c_36>` 7 Days to Die - PlayStation 4 ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_201><b_213><c_242>`PS4, `<a_123><b_78><c_71>`PS4, `<a_201><b_239><c_3>`PS4, `<a_123><b_76><c_232>`PS4
- **推荐↔GT差距**: 正确项在 beam 第6位，pred[0] 前缀深度仅 0/3；平台一致(PS4)；beam中 share-a=6/10, share-(a,b)=1/10。
- **beam多样性**: **中**（2 个 a 大类）；unique(a,b)=10/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: Alien: Isolation - Pla…, Dying Light: The Follo…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=漂移(平台/词面关联)(score1)。target 是合理的大类延续，且**已命中**。

### #329 — 类目错·(a)大类都不对 · BEAM坍缩(<a_123×10/10)
- **历史**(3项; 平台 PS4×3): Alien: Isolation - PlaySta… | Dying Light: The Following… | Resident Evil 7: Biohazard…
- **GT**: `<a_201><b_45><c_166>` Prey - Pre-load - PS4 Digital Code _(平台 PS4)_ ｜ **native**: `<a_123><b_58><c_16>` Resident Evil 7 Biohazard - Xb… ✗
- **beam top5**: `<a_123><b_58><c_16>`Xbo, `<a_123><b_160><c_188>`PS4, `<a_123><b_78><c_71>`PS4, `<a_123><b_158><c_19>`PS4, `<a_123><b_100><c_33>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS4 vs 荐=XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_123 家族 10/10）；unique(a,b)=10/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Alien: Isolation - Pla…, Dying Light: The Follo…, Resident Evil 7: Bioha…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=子类延续(score3)。我们推的比用户真实点击**更贴历史**(荐3>target1) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['code', 'digital']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #330 — 类目错·(a)大类都不对
- **历史**(5项; 平台 3DS×3,?×1,PS4×1): The Legend of Legacy - Nin… | PDP New Nintendo 3DS XL Cl… | BenQ ZOWIE FK1 E-Sports Am… | Shin Megami Tensei IV: Apo… | Resident Evil 7: Biohazard…
- **GT**: `<a_61><b_166><c_249>` Thrustmaster T150 RS Racing Wheel for PlayStat… _(平台 PS3)_ ｜ **native**: `<a_1><b_116><c_233>` Dragon Quest Builders - PlaySt… ✗
- **beam top5**: `<a_1><b_116><c_233>`PS4, `<a_1><b_173><c_4>`PS4, `<a_1><b_25><c_254>`3DS, `<a_1><b_163><c_179>`3DS, `<a_1><b_150><c_189>`PS3
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS3 vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=10/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 4/5（覆盖80%），锚定: The Legend of Legacy -…, Shin Megami Tensei IV:…, PDP New Nintendo 3DS X…；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,immersive。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=漂移(平台/词面关联)(score1)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #331 — 类目错·(a)大类都不对 · BEAM坍缩(<a_208×10/10)
- **历史**(3项; 平台 PS4×2,PSVita×1): Controller Gear PS4 Contro… | Dead or Alive Xtreme 3 Ven… | Resident Evil Origins Coll…
- **GT**: `<a_201><b_239><c_225>` Resident Evil Origins Collection - Xbox One St… _(平台 XboxOne)_ ｜ **native**: `<a_208><b_87><c_200>` DEAD OR ALIVE 5 Last Round - P… ✗
- **beam top5**: `<a_208><b_196><c_65>`PS, `<a_208><b_129><c_14>`Xbo, `<a_208><b_87><c_200>`PS4, `<a_208><b_135><c_101>`?, `<a_208><b_209><c_219>`PSV
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=XboxOne vs 荐=PS2)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_208 家族 10/10）；unique(a,b)=9/10，平台数=5，unique标题=10/10。
- **reasoning质量**: 引用历史 2/3（覆盖67%），锚定: Resident Evil Origins …, Dead or Alive Xtreme 3…；新候选=0（**纯复述历史**）；模板开头；genre: action,fighting,horror。
- **target合理性(天花板)**: target=子类延续(score3); 我们pred[0]=大类延续(score2)。用户点击比我们top1**更贴历史**(target3>荐2) → 我们把可命中的延续**跑偏**了。 注意 target 与历史共享词 ['collection', 'evil', 'origins', 'resident']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #332 — 类目对·item错
- **历史**(4项; 平台 PS4×4): UNCHARTED: The Nathan Drak… | Resident Evil 4 - PlayStat… | The King of Fighters XIV: … | Titanfall 2 - PlayStation …
- **GT**: `<a_201><b_18><c_56>` Mass Effect Andromeda - Pre-load - PS4 Digital… _(平台 PS4)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_39><b_51><c_21>`Xbo, `<a_39><b_78><c_54>`PS4, `<a_123><b_58><c_78>`PS4, `<a_123><b_100><c_33>`PS4, `<a_24><b_72><c_142>`PS4
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台错配(GT=PS4 vs 荐=XboxOne)；beam中 share-a=1/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: UNCHARTED: The Nathan …, Resident Evil 4 - Play…, The King of Fighters X…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=子类延续(score3)。我们推的比用户真实点击**更贴历史**(荐3>target1) → **模型偏保守/用户更爱探索**。

### #333 — 近失·同(a,b)细分仅c不同
- **历史**(7项; 平台 PS×5,PS2×1,?×1): Resident Evil: Code Veroni… | PlayStation 2 Console Slim… | God of War - PlayStation 2 | Scarface The World Is Your… | Destroy All Humans - PlayS… | The Suffering
- **GT**: `<a_80><b_59><c_15>` Resident Evil 6 - Playstation 3 _(平台 PS3)_ ｜ **native**: `<a_71><b_30><c_178>` The Suffering ✗
- **beam top5**: `<a_71><b_171><c_196>`PS3, `<a_71><b_197><c_195>`?, `<a_71><b_204><c_152>`?, `<a_71><b_223><c_141>`?, `<a_80><b_59><c_176>`Gam
- **推荐↔GT差距**: beam 最接近项与 GT 同 (a,b) 细分、仅 c 不同（同系列/不同款），未命中；平台一致(PS3)；beam中 share-a=4/10, share-(a,b)=1/10。
- **beam多样性**: **中**（2 个 a 大类）；unique(a,b)=8/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 6/7（覆盖86%），锚定: Primal - PlayStation 2, God of War - PlayStati…, Scarface The World Is …；新候选=0（**纯复述历史**）；模板开头；genre: action,immersive,narrative。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['evil', 'resident']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #334 — 类目错·(a)大类都不对 · BEAM坍缩(<a_162×10/10)
- **历史**(7项; 平台 Wii×2,GameCube×2,?×2): HDE 128MB (2048 Blocks) Bl… | Gamecube Controller For Ni… | Gamecube Controller For Ni… | Amiibo Marth (Japanese imp… | Mario - Gold amiibo (Super… | Nintendo NFC Reader/Writer…
- **GT**: `<a_214><b_24><c_0>` HAVIT HV-MS672 3200DPI Wired Mouse, 4 Adjustab… _(平台 ?)_ ｜ **native**: `<a_162><b_251><c_136>` Animal Crossing: amiibo Festiv… ✗
- **beam top5**: `<a_162><b_118><c_196>`?, `<a_162><b_251><c_136>`Wii, `<a_162><b_231><c_30>`?, `<a_162><b_49><c_93>`?, `<a_162><b_172><c_85>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_162 家族 10/10）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/6（覆盖67%），锚定: Generic Orange Spice C…, Amiibo Marth (Japanese…, Gamecube Controller Fo…；新候选=0（**纯复述历史**）；模板开头；genre: action,accessor。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['black']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #335 — 类目错·(a)大类都不对
- **历史**(10项; 平台 3DS×6,PS4×2,PS×1): Fire Emblem Fates: Birthri… | HORI Duraflexi Clear Prote… | Nintendo Switch Travel Pou… | Street Fighter V - PlaySta… | Nintendo Selects: The Lege… | Fire Emblem Fates: Map Pac…
- **GT**: `<a_61><b_214><c_225>` PDP Talon Media Remote Control for Xbox One, T… _(平台 XboxOne)_ ｜ **native**: `<a_232><b_79><c_116>` Fire Emblem Fates: Conquest DL… ✗
- **beam top5**: `<a_232><b_79><c_116>`3DS, `<a_232><b_68><c_178>`3DS, `<a_162><b_125><c_53>`?, `<a_232><b_68><c_10>`3DS, `<a_162><b_251><c_136>`Wii
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=XboxOne vs 荐=3DS)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=8/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 6/10（覆盖60%），锚定: Mad Catz Street Fighte…, Tom Clancy's The Divis…, HORI Screen Protective…；新候选=0（**纯复述历史**）；模板开头；genre: action,adventure,rpg。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=子类延续(score3)。我们推的比用户真实点击**更贴历史**(荐3>target2) → **模型偏保守/用户更爱探索**。

### #336 — 类目错·(a)大类都不对
- **历史**(3项; 平台 PS4×3): UNCHARTED: The Nathan Drak… | Street Fighter V - PlaySta… | God of War 3 Remastered - …
- **GT**: `<a_231><b_33><c_2>` ZD-N Vibration-Feedback USB Wired Gamepad Gami… _(平台 PS3)_ ｜ **native**: `<a_201><b_145><c_9>` The Witcher 3: Wild Hunt - Pla… ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_141><b_73><c_216>`PS4, `<a_24><b_145><c_101>`PS4, `<a_201><b_36><c_195>`PS4, `<a_201><b_145><c_9>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS3 vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=10/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: UNCHARTED: The Nathan …, Street Fighter V - Pla…, God of War 3 Remastere…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=漂移(平台/词面关联)(score1)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #337 — 类目错·(a)大类都不对
- **历史**(4项; 平台 PS4×3,3DS×1): PlayStation 4 Console - De… | Final Fantasy XV - PlaySta… | Hyrule Warriors: Legends -… | Overwatch - Origins Editio…
- **GT**: `<a_201><b_151><c_255>` Playstation Plus: 3 Month Membership [Digital … _(平台 PS-generic)_ ｜ **native**: `<a_131><b_224><c_68>` Overwatch - Origins Edition - … ✗
- **beam top5**: `<a_1><b_116><c_233>`PS4, `<a_131><b_209><c_151>`PS4, `<a_131><b_224><c_68>`PS4, `<a_194><b_15><c_66>`PS4, `<a_1><b_43><c_207>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS-generic vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（7 个不同 a 大类）；unique(a,b)=9/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 3/4（覆盖75%），锚定: Final Fantasy XV - Pla…, Overwatch - Origins Ed…, Hyrule Warriors: Legen…；新候选=0（**纯复述历史**）；模板开头；genre: action,adventure,rpg。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=漂移(平台/词面关联)(score1)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #338 — 类目错·(a)大类都不对 · BEAM坍缩(<a_39×9/10)
- **历史**(3项; 平台 Xbox360×3): Call of Duty: Modern Warfa… | Mortal Kombat: Komplete Ed… | Call of Duty: Advanced War…
- **GT**: `<a_245><b_155><c_109>` Middle Earth: Shadow of Mordor - Xbox 360 _(平台 Xbox360)_ ｜ **native**: `<a_39><b_182><c_109>` Call of Duty: Black Ops Combo … ✗
- **beam top5**: `<a_39><b_114><c_237>`Xbo, `<a_39><b_182><c_247>`PS4, `<a_39><b_182><c_109>`Xbo, `<a_39><b_114><c_209>`Xbo, `<a_39><b_224><c_27>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=Xbox360 vs 荐=XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_39 家族 9/10）；unique(a,b)=5/10，平台数=5，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Call of Duty: Modern W…, Mortal Kombat: Komplet…, Call of Duty: Advanced…；新候选=0（**纯复述历史**）；genre: action,shooter,strategy。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=子类延续(score3)。我们推的比用户真实点击**更贴历史**(荐3>target1) → **模型偏保守/用户更爱探索**。

### #339 — 类目错·(a)大类都不对 · BEAM坍缩(<a_1×10/10)
- **历史**(10项; 平台 XboxOne×5,PSVita×4,?×1): Ori and the Blind Forest: … | Resident Evil: Revelations… | Child of Light - PlayStati… | Rare Replay - Xbox One | Mario Kart 7 | Grand Kingdom - PlayStatio…
- **GT**: `<a_123><b_178><c_34>` State of Decay- Year-One Survival Edition _(平台 ?)_ ｜ **native**: `<a_1><b_150><c_189>` Legend of Heroes: Trails of Co… ✗
- **beam top5**: `<a_1><b_242><c_201>`PS4, `<a_1><b_68><c_121>`PS4, `<a_1><b_150><c_189>`PS3, `<a_1><b_200><c_195>`?, `<a_1><b_25><c_254>`3DS
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_1 家族 10/10）；unique(a,b)=10/10，平台数=5，unique标题=10/10。
- **reasoning质量**: 引用历史 6/10（覆盖60%），锚定: Yomawari: Night Alone …, Child of Light - PlayS…, Mighty No. 9 - Xbox On…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。

### #340 — 类目错·(a)大类都不对
- **历史**(1项; 平台 ?×1): Animal Crossing: New Leaf
- **GT**: `<a_195><b_36><c_218>` Fire Emblem: Awakening _(平台 ?)_ ｜ **native**: `<a_211><b_105><c_223>` Animal Crossing: Happy Home De… ✗
- **beam top5**: `<a_162><b_251><c_136>`Wii, `<a_119><b_185><c_105>`3DS, `<a_211><b_105><c_223>`3DS, `<a_211><b_112><c_5>`3DS, `<a_162><b_125><c_53>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=9/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 1/1（覆盖100%），锚定: Animal Crossing: New L…；新候选=0（**纯复述历史**）；genre: action,role-playing,simulation。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=漂移(平台/词面关联)(score1)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #341 — 类目对·item错
- **历史**(2项; 平台 ?×2): Animal Crossing: New Leaf | Fire Emblem: Awakening
- **GT**: `<a_216><b_93><c_101>` The Legend of Zelda: A Link Between Worlds 3D _(平台 ?)_ ｜ **native**: `<a_211><b_142><c_127>` Pokemon Conquest ✗
- **beam top5**: `<a_211><b_142><c_127>`?, `<a_216><b_51><c_130>`3DS, `<a_211><b_105><c_223>`3DS, `<a_211><b_88><c_34>`?, `<a_211><b_112><c_5>`3DS
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；beam中 share-a=3/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=10/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: Animal Crossing: New L…, Fire Emblem: Awakening；新候选=0（**纯复述历史**）；模板开头；genre: action,strategy,simulation。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #342 — 命中@7 · RERANK伤害
- **历史**(3项; 平台 ?×2,DS×1): Animal Crossing: New Leaf | Fire Emblem: Awakening | The Legend of Zelda: A Lin…
- **GT**: `<a_216><b_112><c_119>` The Legend of Zelda: Majora's Mask 3D _(平台 ?)_ ｜ **native**: `<a_216><b_112><c_119>` The Legend of Zelda: Majora's … ✓
- **beam top5**: `<a_216><b_51><c_130>`3DS, `<a_216><b_112><c_114>`Wii, `<a_211><b_105><c_223>`3DS, `<a_211><b_112><c_5>`3DS, `<a_216><b_142><c_77>`3DS
- **推荐↔GT差距**: 正确项在 beam 第7位，pred[0] 前缀深度仅 1/3；beam中 share-a=6/10, share-(a,b)=2/10。
- **beam多样性**: **中**（2 个 a 大类）；unique(a,b)=9/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Animal Crossing: New L…, Fire Emblem: Awakening, The Legend of Zelda: A…；新候选=0（**纯复述历史**）；模板开头；genre: action,adventure,puzzle。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。target 是合理的大类延续，且**已命中**。

### #343 — 类目对·item错 · BEAM坍缩(<a_216×8/10)
- **历史**(4项; 平台 ?×3,DS×1): Animal Crossing: New Leaf | Fire Emblem: Awakening | The Legend of Zelda: A Lin… | The Legend of Zelda: Major…
- **GT**: `<a_216><b_44><c_79>` Bravely Second: End Layer - Nintendo 3DS _(平台 3DS)_ ｜ **native**: `<a_216><b_142><c_77>` Bravely Default - Nintendo 3DS ✗
- **beam top5**: `<a_216><b_51><c_130>`3DS, `<a_216><b_235><c_168>`3DS, `<a_216><b_112><c_114>`Wii, `<a_216><b_142><c_77>`3DS, `<a_216><b_219><c_158>`3DS
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台一致(3DS)；beam中 share-a=8/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_216 家族 8/10）；unique(a,b)=10/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 2/4（覆盖50%），锚定: Animal Crossing: New L…, The Legend of Zelda: A…；新候选=0（**纯复述历史**）；模板开头；genre: action,adventure,rpg。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。

### #344 — 类目对·item错 · BEAM坍缩(<a_216×8/10)
- **历史**(5项; 平台 ?×3,DS×1,3DS×1): Animal Crossing: New Leaf | Fire Emblem: Awakening | The Legend of Zelda: A Lin… | The Legend of Zelda: Major… | Bravely Second: End Layer …
- **GT**: `<a_211><b_159><c_123>` Pok&eacute;mon Moon - Nintendo 3DS _(平台 3DS)_ ｜ **native**: `<a_216><b_235><c_168>` Final Fantasy Explorers - Nint… ✗
- **beam top5**: `<a_1><b_25><c_254>`3DS, `<a_216><b_235><c_168>`3DS, `<a_216><b_51><c_130>`3DS, `<a_216><b_219><c_158>`3DS, `<a_211><b_112><c_5>`3DS
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台一致(3DS)；beam中 share-a=1/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_216 家族 8/10）；unique(a,b)=10/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/5（覆盖80%），锚定: Animal Crossing: New L…, The Legend of Zelda: A…, The Legend of Zelda: M…；新候选=0（**纯复述历史**）；模板开头；genre: action,adventure,rpg。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=漂移(平台/词面关联)(score1)。用户点击比我们top1**更贴历史**(target2>荐1) → 我们把可命中的延续**跑偏**了。

### #345 — 命中@1
- **历史**(6项; 平台 ?×3,3DS×2,DS×1): Animal Crossing: New Leaf | Fire Emblem: Awakening | The Legend of Zelda: A Lin… | The Legend of Zelda: Major… | Bravely Second: End Layer … | Pok&eacute;mon Moon - Nint…
- **GT**: `<a_211><b_159><c_71>` Pok&eacute;mon Sun - Nintendo 3DS _(平台 3DS)_ ｜ **native**: `<a_211><b_159><c_71>` Pok&eacute;mon Sun - Nintendo … ✓
- **beam top5**: `<a_211><b_159><c_71>`3DS, `<a_216><b_159><c_141>`3DS, `<a_216><b_76><c_23>`3DS, `<a_1><b_25><c_254>`3DS, `<a_216><b_48><c_110>`3DS
- **推荐↔GT差距**: top-1 完全命中。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=8/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 5/6（覆盖83%），锚定: Animal Crossing: New L…, The Legend of Zelda: M…, Pok&eacute;mon Moon - …；新候选=0（**纯复述历史**）；genre: adventure,rpg,immersive。
- **target合理性(天花板)**: target=子类延续(score3); 我们pred[0]=子类延续(score3)。target 是合理的子类延续，且**已命中**。

### #346 — 类目对·item错
- **历史**(7项; 平台 ?×3,3DS×3,DS×1): Fire Emblem: Awakening | The Legend of Zelda: A Lin… | The Legend of Zelda: Major… | Bravely Second: End Layer … | Pok&eacute;mon Moon - Nint… | Pok&eacute;mon Sun - Ninte…
- **GT**: `<a_216><b_92><c_192>` Etrian Odyssey Untold: The Millennium Girl - N… _(平台 3DS)_ ｜ **native**: `<a_211><b_159><c_71>` Pok&eacute;mon Sun - Nintendo … ✗
- **beam top5**: `<a_1><b_25><c_254>`3DS, `<a_216><b_48><c_110>`3DS, `<a_1><b_25><c_194>`3DS, `<a_216><b_159><c_141>`3DS, `<a_211><b_159><c_71>`3DS
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台一致(3DS)；beam中 share-a=3/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=8/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/7（覆盖57%），锚定: Animal Crossing: New L…, The Legend of Zelda: M…, Pok&eacute;mon Moon - …；新候选=0（**纯复述历史**）；模板开头；genre: action,adventure,rpg。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=漂移(平台/词面关联)(score1)。用户点击比我们top1**更贴历史**(target2>荐1) → 我们把可命中的延续**跑偏**了。

### #347 — 类目对·item错
- **历史**(8项; 平台 3DS×4,?×3,DS×1): The Legend of Zelda: A Lin… | The Legend of Zelda: Major… | Bravely Second: End Layer … | Pok&eacute;mon Moon - Nint… | Pok&eacute;mon Sun - Ninte… | Etrian Odyssey Untold: The…
- **GT**: `<a_216><b_146><c_129>` The Legend of Legacy - Nintendo 3DS _(平台 3DS)_ ｜ **native**: `<a_216><b_48><c_110>` Dragon Quest VIII: Journey of … ✗
- **beam top5**: `<a_216><b_48><c_110>`3DS, `<a_216><b_76><c_23>`3DS, `<a_1><b_25><c_254>`3DS, `<a_216><b_159><c_141>`3DS, `<a_211><b_31><c_154>`3DS
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台一致(3DS)；beam中 share-a=4/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=8/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 5/8（覆盖62%），锚定: Animal Crossing: New L…, The Legend of Zelda: M…, Etrian Odyssey Untold:…；新候选=0（**纯复述历史**）；模板开头；genre: action,adventure,rpg。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。 注意 target 与历史共享词 ['legend']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #348 — 类目对·item错
- **历史**(1项; 平台 XboxOne×1): Sniper Elite III - Xbox On…
- **GT**: `<a_123><b_189><c_223>` Red Dead Redemption: Game of the Year Edition … _(平台 XboxOne)_ ｜ **native**: `<a_123><b_72><c_191>` Far Cry 4 - Xbox One ✗
- **beam top5**: `<a_123><b_72><c_191>`Xbo, `<a_123><b_246><c_254>`Xbo, `<a_123><b_72><c_7>`PS4, `<a_118><b_1><c_2>`Xbo, `<a_123><b_72><c_182>`Xbo
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台一致(XboxOne)；beam中 share-a=6/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=7/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 1/1（覆盖100%），锚定: Sniper Elite III - Xbo…；新候选=0（**纯复述历史**）；genre: action,strategy,immersive。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。

### #349 — 类目对·item错 · BEAM坍缩(<a_140×9/10)
- **历史**(2项; 平台 Xbox360×2): Medal of Honor Warfighter … | Tom Clancy's Ghost Recon: …
- **GT**: `<a_71><b_33><c_62>` Assassin's Creed IV Black Flag - Xbox 360 _(平台 Xbox360)_ ｜ **native**: `<a_140><b_212><c_230>` Homefront - Xbox 360 ✗
- **beam top5**: `<a_140><b_212><c_230>`Xbo, `<a_140><b_221><c_16>`PC, `<a_80><b_162><c_230>`Xbo, `<a_140><b_161><c_25>`Xbo, `<a_140><b_221><c_161>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(Xbox360)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_140 家族 9/10）；unique(a,b)=6/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: Medal of Honor Warfigh…, Tom Clancy's Ghost Rec…；新候选=0（**纯复述历史**）；模板开头；genre: action,shooter,strategy。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #350 — 类目错·(a)大类都不对 · BEAM坍缩(<a_140×7/10)
- **历史**(3项; 平台 Xbox360×3): Medal of Honor Warfighter … | Tom Clancy's Ghost Recon: … | Assassin's Creed IV Black …
- **GT**: `<a_24><b_152><c_33>` Rise of the Tomb Raider - Xbox 360 - Xbox 360 … _(平台 Xbox360)_ ｜ **native**: `<a_140><b_65><c_232>` Tom Clancy's Ghost Recon: Futu… ✗
- **beam top5**: `<a_140><b_221><c_16>`PC, `<a_140><b_212><c_230>`Xbo, `<a_140><b_50><c_3>`PS4, `<a_80><b_69><c_76>`Xbo, `<a_39><b_204><c_1>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=Xbox360 vs 荐=PC)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_140 家族 7/10）；unique(a,b)=8/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Medal of Honor Warfigh…, Tom Clancy's Ghost Rec…, Assassin's Creed IV Bl…；新候选=0（**纯复述历史**）；模板开头；genre: action,shooter,strategy。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #351 — 类目对·item错 · BEAM坍缩(<a_24×7/10)
- **历史**(3项; 平台 PS3×3): Dragon Age Inquisition - S… | Bound by Flame - PlayStati… | Metro Last Light - Playsta…
- **GT**: `<a_24><b_72><c_142>` Horizon Zero Dawn - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_24><b_176><c_166>` Metro Last Light - Playstation… ✗
- **beam top5**: `<a_24><b_51><c_181>`PS3, `<a_24><b_51><c_183>`PS, `<a_24><b_252><c_227>`Xbo, `<a_24><b_44><c_74>`PS3, `<a_24><b_247><c_115>`PS4
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台错配(GT=PS4 vs 荐=PS3)；beam中 share-a=7/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_24 家族 7/10）；unique(a,b)=8/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Dragon Age Inquisition…, Bound by Flame - PlayS…, Metro Last Light - Pla…；新候选=0（**纯复述历史**）；genre: action,role-playing,immersive。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。

### #352 — 类目对·item错
- **历史**(10项; 平台 XboxOne×10): Agents of Mayhem - Xbox On… | Assassin&rsquo;s Creed Syn… | Transformers Devastation -… | Madden NFL 16 - Xbox One | Middle Earth: Shadow of Mo… | Tekken 7 - Xbox One
- **GT**: `<a_205><b_89><c_183>` The Golf Club: Collector's Edition - Xbox One _(平台 XboxOne)_ ｜ **native**: `<a_123><b_76><c_255>` Far Cry Primal - Xbox One Stan… ✗
- **beam top5**: `<a_131><b_155><c_206>`Xbo, `<a_123><b_76><c_255>`Xbo, `<a_131><b_55><c_86>`Xbo, `<a_39><b_77><c_69>`Xbo, `<a_39><b_69><c_69>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=10/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 7/10（覆盖70%），锚定: Assassin's Creed Unity…, Battlefield 1 - Xbox O…, Batman: Arkham Knight …；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。

### #353 — 类目错·(a)大类都不对
- **历史**(3项; 平台 Xbox×1,Xbox360×1,?×1): James Bond 007 Nightfire -… | Tom Clancy's Ghost Recon A… | Ace Combat 6: Fires of Lib…
- **GT**: `<a_8><b_141><c_167>` Nyko Charge Block Solo - Controller Charging S… _(平台 XboxOne)_ ｜ **native**: `<a_140><b_242><c_197>` Halo 2 - Xbox ✗
- **beam top5**: `<a_140><b_242><c_197>`Xbo, `<a_39><b_124><c_106>`?, `<a_39><b_40><c_248>`Xbo, `<a_39><b_211><c_56>`Xbo, `<a_140><b_65><c_232>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=XboxOne vs 荐=Xbox)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=9/10，平台数=5，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: James Bond 007 Nightfi…, Tom Clancy's Ghost Rec…, Ace Combat 6: Fires of…；新候选=0（**纯复述历史**）；genre: action,shooter,strategy。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #354 — 类目错·(a)大类都不对 · BEAM坍缩(<a_162×8/10)
- **历史**(7项; 平台 XboxOne×2,?×2,Xbox×1): Logitech G602 Lag-Free Wir… | Xbox One Wireless Controll… | Microsoft Xbox Wireless Ad… | DualShock 4 Wireless Contr… | Yoshi amiibo (Super Smash … | Nintendo Boo amiibo (SM Se…
- **GT**: `<a_71><b_251><c_145>` Dark Souls: Prepare To Die Edition [Online Gam… _(平台 ?)_ ｜ **native**: `<a_162><b_130><c_51>` Nintendo Wario amiibo (SM Seri… ✗
- **beam top5**: `<a_162><b_130><c_51>`Wii, `<a_162><b_222><c_61>`Wii, `<a_162><b_130><c_1>`Wii, `<a_162><b_130><c_2>`Wii, `<a_162><b_172><c_85>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_162 家族 8/10）；unique(a,b)=5/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/7（覆盖57%），锚定: Xbox One Chatpad + Cha…, Xbox One Wireless Cont…, Yoshi amiibo (Super Sm…；新候选=0（**纯复述历史**）；genre: action,nostalg,peripheral。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=子类延续(score3)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #355 — 类目对·item错 · BEAM坍缩(<a_162×10/10)
- **历史**(8项; 平台 ?×3,XboxOne×2,Xbox×1): Xbox One Wireless Controll… | Microsoft Xbox Wireless Ad… | DualShock 4 Wireless Contr… | Yoshi amiibo (Super Smash … | Nintendo Boo amiibo (SM Se… | Dark Souls: Prepare To Die…
- **GT**: `<a_162><b_106><c_211>` Jigglypuff amiibo - Japan Import (Super Smash … _(平台 ?)_ ｜ **native**: `<a_162><b_130><c_51>` Nintendo Wario amiibo (SM Seri… ✗
- **beam top5**: `<a_162><b_81><c_26>`?, `<a_162><b_130><c_51>`Wii, `<a_162><b_130><c_1>`Wii, `<a_162><b_231><c_30>`?, `<a_162><b_222><c_61>`Wii
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；beam中 share-a=10/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_162 家族 10/10）；unique(a,b)=8/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 5/8（覆盖62%），锚定: Xbox One Chatpad + Cha…, Xbox One Wireless Cont…, Yoshi amiibo (Super Sm…；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,immersive。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。 注意 target 与历史共享词 ['amiibo', 'bros', 'series', 'smash', 'super']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #356 — 类目错·(a)大类都不对 · BEAM坍缩(<a_250×9/10)
- **历史**(9项; 平台 WiiU×3,PS4×3,?×2): Assassin's Creed: Syndicat… | Far Cry Primal - PlayStati… | Mario Party 10 | Eastvita Full 1080p 720P H… | Nintendo Selects: Donkey K… | The Legend of Zelda: Breat…
- **GT**: `<a_7><b_181><c_27>` Xbox One Chat Headset _(平台 XboxOne)_ ｜ **native**: `<a_250><b_116><c_226>` Yoshi's Woolly World -  Wii U ✗
- **beam top5**: `<a_250><b_112><c_111>`Wii, `<a_250><b_116><c_22>`Wii, `<a_250><b_238><c_255>`Wii, `<a_250><b_121><c_156>`?, `<a_250><b_116><c_226>`Wii
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=XboxOne vs 荐=WiiU)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_250 家族 9/10）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 6/9（覆盖67%），锚定: Super Mario Maker - Ni…, Nintendo Selects: Donk…, The Last of Us Remaste…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #357 — 类目错·(a)大类都不对 · BEAM坍缩(<a_194×7/10)
- **历史**(1项; 平台 PSVita×1): FINAL FANTASY X|X-2 HD Rem…
- **GT**: `<a_61><b_131><c_197>` Microsoft Xbox Wireless Adapter for Windows 10 _(平台 Xbox)_ ｜ **native**: `<a_194><b_21><c_76>` Final Fantasy X X-2 HD Remaste… ✗
- **beam top5**: `<a_194><b_121><c_62>`PS4, `<a_1><b_150><c_189>`PS3, `<a_194><b_21><c_219>`PS4, `<a_194><b_21><c_76>`PS4, `<a_194><b_219><c_28>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=Xbox vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_194 家族 7/10）；unique(a,b)=8/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 1/1（覆盖100%），锚定: FINAL FANTASY X|X-2 HD…；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,immersive。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #358 — 类目错·(a)大类都不对 · BEAM坍缩(<a_61×8/10)
- **历史**(2项; 平台 PSVita×1,Xbox×1): FINAL FANTASY X|X-2 HD Rem… | Microsoft Xbox Wireless Ad…
- **GT**: `<a_250><b_92><c_44>` Nintendo Selects: Donkey Kong Country: Tropica… _(平台 ?)_ ｜ **native**: `<a_61><b_131><c_197>` Microsoft Xbox Wireless Adapte… ✗
- **beam top5**: `<a_61><b_167><c_197>`Xbo, `<a_61><b_111><c_197>`Xbo, `<a_61><b_131><c_197>`Xbo, `<a_61><b_53><c_46>`Xbo, `<a_61><b_111><c_109>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_61 家族 8/10）；unique(a,b)=8/10，平台数=5，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: FINAL FANTASY X|X-2 HD…, Microsoft Xbox Wireles…；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,immersive。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #359 — 类目错·(a)大类都不对
- **历史**(3项; 平台 PSVita×1,Xbox×1,?×1): FINAL FANTASY X|X-2 HD Rem… | Microsoft Xbox Wireless Ad… | Nintendo Selects: Donkey K…
- **GT**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - PS4 Digital Code _(平台 PS4)_ ｜ **native**: `<a_250><b_238><c_255>` Mario Party 10 + Mario amiibo … ✗
- **beam top5**: `<a_61><b_131><c_197>`Xbo, `<a_250><b_238><c_255>`Wii, `<a_250><b_55><c_95>`?, `<a_113><b_29><c_66>`Wii, `<a_250><b_92><c_0>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS4 vs 荐=Xbox)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=8/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: FINAL FANTASY X|X-2 HD…, Nintendo Selects: Donk…, Microsoft Xbox Wireles…；新候选=0（**纯复述历史**）；模板开头；genre: action,adventure,rpg。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=子类延续(score3)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #360 — 类目错·(a)大类都不对 · BEAM坍缩(<a_123×9/10)
- **历史**(4项; 平台 PSVita×1,Xbox×1,?×1): FINAL FANTASY X|X-2 HD Rem… | Microsoft Xbox Wireless Ad… | Nintendo Selects: Donkey K… | Resident Evil 7: Biohazard…
- **GT**: `<a_111><b_130><c_0>` Just Dance 2017 - Wii U _(平台 WiiU)_ ｜ **native**: `<a_123><b_58><c_16>` Resident Evil 7 Biohazard - Xb… ✗
- **beam top5**: `<a_123><b_58><c_16>`Xbo, `<a_123><b_171><c_44>`Xbo, `<a_123><b_188><c_192>`PS4, `<a_123><b_33><c_93>`PS4, `<a_123><b_33><c_95>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=WiiU vs 荐=XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_123 家族 9/10）；unique(a,b)=8/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 3/4（覆盖75%），锚定: FINAL FANTASY X|X-2 HD…, Resident Evil 7: Bioha…, Microsoft Xbox Wireles…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=子类延续(score3)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #361 — 命中@5
- **历史**(8项; 平台 PS4×8): Until Dawn - PlayStation 4 | Dragon Age Inquisition - S… | Middle Earth: Shadow of Mo… | Dark Souls III: Day 1 Edit… | Doom - PlayStation 4 | Mass Effect Andromeda - Pr…
- **GT**: `<a_24><b_72><c_142>` Horizon Zero Dawn - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_194><b_15><c_66>` Dishonored 2 - PlayStation 4 ✗
- **beam top5**: `<a_194><b_87><c_112>`PS4, `<a_194><b_15><c_66>`PS4, `<a_201><b_31><c_107>`PS4, `<a_194><b_15><c_9>`PS4, `<a_24><b_72><c_142>`PS4
- **推荐↔GT差距**: 正确项在 beam 第5位，pred[0] 前缀深度仅 0/3；平台一致(PS4)；beam中 share-a=1/10, share-(a,b)=1/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=9/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 7/8（覆盖88%），锚定: The Witcher 3: Wild Hu…, Dragon Age Inquisition…, Until Dawn - PlayStati…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=子类延续(score3)。target 是合理的漂移(平台/词面关联)，且**已命中**。

### #362 — 类目对·item错 · BEAM坍缩(<a_123×9/10)
- **历史**(5项; 平台 PS4×5): Divinity: Original Sin - E… | Just Cause 3 - PlayStation… | Tom Clancy's The Division … | Fallout 4: Automatron - PS… | 7 Days to Die - PlayStatio…
- **GT**: `<a_140><b_90><c_138>` Battleborn - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_123><b_142><c_36>` 7 Days to Die - PlayStation 4 ✗
- **beam top5**: `<a_123><b_100><c_33>`PS4, `<a_123><b_58><c_78>`PS4, `<a_123><b_160><c_188>`PS4, `<a_123><b_2><c_26>`PS4, `<a_123><b_160><c_69>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_123 家族 9/10）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 5/5（覆盖100%），锚定: Divinity: Original Sin…, Tom Clancy's The Divis…, Just Cause 3 - PlaySta…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #363 — 类目对·item错
- **历史**(6项; 平台 PS4×6): Divinity: Original Sin - E… | Just Cause 3 - PlayStation… | Tom Clancy's The Division … | Fallout 4: Automatron - PS… | 7 Days to Die - PlayStatio… | Battleborn - PlayStation 4
- **GT**: `<a_1><b_5><c_65>` Dynasty Warriors 8: Xtreme Legends, Complete E… _(平台 PS4)_ ｜ **native**: `<a_131><b_209><c_151>` No Man's Sky - PlayStation 4 ✗
- **beam top5**: `<a_131><b_209><c_151>`PS4, `<a_131><b_41><c_229>`PS4, `<a_201><b_31><c_107>`PS4, `<a_123><b_100><c_33>`PS4, `<a_131><b_224><c_68>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=10/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 5/6（覆盖83%），锚定: Divinity: Original Sin…, Just Cause 3 - PlaySta…, Fallout 4: Automatron …；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #364 — 类目错·(a)大类都不对
- **历史**(1项; 平台 ?×1): Call of Duty 4: Modern War…
- **GT**: `<a_200><b_186><c_92>` Mafia III - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_39><b_124><c_209>` Call of Duty 4: Modern Warfare… ✗
- **beam top5**: `<a_39><b_124><c_209>`?, `<a_80><b_69><c_230>`PC, `<a_39><b_124><c_106>`?, `<a_80><b_69><c_76>`Xbo, `<a_80><b_162><c_230>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=6/10，平台数=4，unique标题=9/10。
- **reasoning质量**: 引用历史 1/1（覆盖100%），锚定: Call of Duty 4: Modern…；新候选=0（**纯复述历史**）；genre: action,shooter,multiplayer。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=子类延续(score3)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #365 — 命中@4 · BEAM坍缩(<a_123×7/10)
- **历史**(2项; 平台 ?×1,PS4×1): Call of Duty 4: Modern War… | Mafia III - PlayStation 4
- **GT**: `<a_39><b_78><c_54>` Battlefield 1 - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_123><b_76><c_232>` Far Cry Primal - PlayStation 4… ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_123><b_72><c_7>`PS4, `<a_123><b_129><c_247>`PS4, `<a_39><b_78><c_54>`PS4, `<a_39><b_51><c_188>`PS4
- **推荐↔GT差距**: 正确项在 beam 第4位，pred[0] 前缀深度仅 0/3；平台一致(PS4)；beam中 share-a=2/10, share-(a,b)=1/10。
- **beam多样性**: **低**（坍缩到 <a_123 家族 7/10）；unique(a,b)=9/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: Call of Duty 4: Modern…, Mafia III - PlayStatio…；新候选=0（**纯复述历史**）；模板开头；genre: action,shooter,multiplayer。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=漂移(平台/词面关联)(score1)。target 是合理的大类延续，且**已命中**。

### #366 — 类目错·(a)大类都不对
- **历史**(1项; 平台 Xbox360×1): Bioshock - Xbox 360
- **GT**: `<a_141><b_221><c_44>` Fallout 3 _(平台 ?)_ ｜ **native**: `<a_140><b_68><c_13>` Bioshock 2 - Xbox 360 ✗
- **beam top5**: `<a_80><b_202><c_49>`?, `<a_80><b_212><c_38>`?, `<a_80><b_203><c_141>`Xbo, `<a_140><b_68><c_13>`Xbo, `<a_140><b_203><c_107>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=8/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 1/1（覆盖100%），锚定: Bioshock - Xbox 360；新候选=0（**纯复述历史**）；genre: action,horror,immersive。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=探索(无关联)(score0)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #367 — 类目对·item错
- **历史**(2项; 平台 Xbox360×1,?×1): Bioshock - Xbox 360 | Fallout 3
- **GT**: `<a_140><b_212><c_49>` Borderlands - Xbox 360 _(平台 Xbox360)_ ｜ **native**: `<a_140><b_68><c_13>` Bioshock 2 - Xbox 360 ✗
- **beam top5**: `<a_80><b_202><c_49>`?, `<a_140><b_221><c_161>`?, `<a_140><b_160><c_117>`Xbo, `<a_80><b_212><c_38>`?, `<a_141><b_202><c_240>`?
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；beam中 share-a=5/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=8/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: Bioshock - Xbox 360, Fallout 3；新候选=0（**纯复述历史**）；模板开头；genre: action,role-playing,immersive。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=探索(无关联)(score0)。用户点击比我们top1**更贴历史**(target1>荐0) → 我们把可命中的延续**跑偏**了。

### #368 — 类目对·item错 · BEAM坍缩(<a_140×7/10)
- **历史**(3项; 平台 Xbox360×2,?×1): Bioshock - Xbox 360 | Fallout 3 | Borderlands - Xbox 360
- **GT**: `<a_140><b_176><c_51>` Battlefield: Bad Company _(平台 ?)_ ｜ **native**: `<a_140><b_212><c_49>` Borderlands - Xbox 360 ✗
- **beam top5**: `<a_140><b_212><c_49>`Xbo, `<a_140><b_221><c_16>`PC, `<a_140><b_221><c_18>`PC, `<a_140><b_221><c_21>`?, `<a_140><b_221><c_161>`?
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；beam中 share-a=7/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_140 家族 7/10）；unique(a,b)=6/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Bioshock - Xbox 360, Fallout 3, Borderlands - Xbox 360；新候选=0（**纯复述历史**）；模板开头；genre: action,role-playing,multiplayer。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=子类延续(score3)。我们推的比用户真实点击**更贴历史**(荐3>target2) → **模型偏保守/用户更爱探索**。

### #369 — 类目对·item错
- **历史**(4项; 平台 Xbox360×2,?×2): Bioshock - Xbox 360 | Fallout 3 | Borderlands - Xbox 360 | Battlefield: Bad Company
- **GT**: `<a_140><b_161><c_25>` Call of Duty: World at War Platinum Hits - Xbo… _(平台 Xbox360)_ ｜ **native**: `<a_140><b_176><c_51>` Battlefield: Bad Company ✗
- **beam top5**: `<a_140><b_212><c_49>`Xbo, `<a_140><b_176><c_37>`Xbo, `<a_140><b_191><c_66>`Xbo, `<a_80><b_212><c_38>`?, `<a_80><b_202><c_49>`?
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台一致(Xbox360)；beam中 share-a=6/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=6/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Bioshock - Xbox 360, Borderlands - Xbox 360, Battlefield: Bad Compa…；新候选=0（**纯复述历史**）；模板开头；genre: action,multiplayer,immersive。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=子类延续(score3)。我们推的比用户真实点击**更贴历史**(荐3>target2) → **模型偏保守/用户更爱探索**。

### #370 — 类目对·item错 · BEAM坍缩(<a_140×9/10)
- **历史**(5项; 平台 Xbox360×3,?×2): Bioshock - Xbox 360 | Fallout 3 | Borderlands - Xbox 360 | Battlefield: Bad Company | Call of Duty: World at War…
- **GT**: `<a_140><b_176><c_37>` Battlefield Bad Company 2 - Xbox 360 _(平台 Xbox360)_ ｜ **native**: `<a_140><b_212><c_49>` Borderlands - Xbox 360 ✗
- **beam top5**: `<a_140><b_212><c_49>`Xbo, `<a_140><b_221><c_16>`PC, `<a_140><b_4><c_214>`PS3, `<a_140><b_221><c_161>`?, `<a_140><b_221><c_21>`?
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台一致(Xbox360)；beam中 share-a=9/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_140 家族 9/10）；unique(a,b)=6/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 4/5（覆盖80%），锚定: Bioshock - Xbox 360, Borderlands - Xbox 360, Battlefield: Bad Compa…；新候选=0（**纯复述历史**）；模板开头；genre: action,shooter,multiplayer。
- **target合理性(天花板)**: target=子类延续(score3); 我们pred[0]=子类延续(score3)。关联档位相同(score3)但选错具体 item。 注意 target 与历史共享词 ['bad', 'battlefield', 'company']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #371 — 类目错·(a)大类都不对
- **历史**(6项; 平台 Xbox360×4,?×2): Bioshock - Xbox 360 | Fallout 3 | Borderlands - Xbox 360 | Battlefield: Bad Company | Call of Duty: World at War… | Battlefield Bad Company 2 …
- **GT**: `<a_71><b_59><c_0>` Dead Space 2 _(平台 ?)_ ｜ **native**: `<a_140><b_212><c_49>` Borderlands - Xbox 360 ✗
- **beam top5**: `<a_140><b_212><c_49>`Xbo, `<a_140><b_212><c_79>`Xbo, `<a_39><b_138><c_240>`?, `<a_140><b_191><c_66>`Xbo, `<a_140><b_176><c_37>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=7/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 3/6（覆盖50%），锚定: Bioshock - Xbox 360, Borderlands - Xbox 360, Battlefield Bad Compan…；新候选=0（**纯复述历史**）；模板开头；genre: action,shooter,strategy。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=子类延续(score3)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #372 — 类目错·(a)大类都不对
- **历史**(10项; 平台 PS×3,Wii×2,?×2): Donkey Kong Country Return… | PS3 500 GB Grand Theft Aut… | The Legend of Zelda: Twili… | Black - PlayStation 2 | Tomb Raider Game of the Ye… | Manhunt - PlayStation 2
- **GT**: `<a_140><b_107><c_50>` GoldenEye 007 _(平台 ?)_ ｜ **native**: `<a_240><b_157><c_127>` Manhunt 2 - Sony PSP ✗
- **beam top5**: `<a_240><b_215><c_158>`?, `<a_71><b_171><c_196>`PS3, `<a_240><b_157><c_127>`PSP, `<a_71><b_66><c_11>`?, `<a_71><b_66><c_14>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（2 个 a 大类）；unique(a,b)=7/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 6/10（覆盖60%），锚定: The Saboteur - Xbox 36…, Manhunt - PlayStation …, Ghostbusters: The Vide…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。

### #373 — 类目错·(a)大类都不对 · BEAM坍缩(<a_250×10/10)
- **历史**(7项; 平台 ?×6,PS3×1): Mewtwo amiibo - Japan Impo… | Donkey Kong Country | Teenage Mutant Ninja Turtl… | Resident Evil: Revelations… | Resident Evil 2 | Donkey Kong Country 2: Did…
- **GT**: `<a_219><b_191><c_170>` 16-bit Entertainment System(NOT SNES MINI, NO … _(平台 ?)_ ｜ **native**: `<a_250><b_53><c_134>` Wario Land: Super Mario Land 3 ✗
- **beam top5**: `<a_250><b_199><c_170>`?, `<a_250><b_156><c_1>`?, `<a_250><b_165><c_76>`?, `<a_250><b_173><c_199>`?, `<a_250><b_238><c_224>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_250 家族 10/10）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/7（覆盖57%），锚定: Donkey Kong Country, Donkey Kong Country 2:…, Resident Evil: Revelat…；新候选=0（**纯复述历史**）；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=子类延续(score3)。我们推的比用户真实点击**更贴历史**(荐3>target1) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['super']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #374 — 类目错·(a)大类都不对
- **历史**(8项; 平台 Xbox360×3,?×3,PSVita×1): Nintendo 64 System - Video… | Carmageddon: Max Damage - … | Battlefield Hardline - Xbo… | Contra 4 | Atari Flashback Classics: … | SpongeBob SquarePants: Pla…
- **GT**: `<a_141><b_241><c_37>` Spider-Man: Shattered Dimensions - Xbox 360 _(平台 Xbox360)_ ｜ **native**: `<a_219><b_123><c_0>` Atari Flashback Classics: Volu… ✗
- **beam top5**: `<a_233><b_106><c_144>`?, `<a_233><b_21><c_136>`?, `<a_219><b_168><c_108>`Gam, `<a_250><b_165><c_76>`?, `<a_233><b_44><c_175>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（6 个不同 a 大类）；unique(a,b)=9/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 6/8（覆盖75%），锚定: Dungeon Travelers 2: T…, Contra 4, Nintendo 64 System - V…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=探索(无关联)(score0)。用户点击比我们top1**更贴历史**(target1>荐0) → 我们把可命中的延续**跑偏**了。

### #375 — 类目错·(a)大类都不对
- **历史**(1项; 平台 PC×1): Rollercoaster Tycoon 2: Tr…
- **GT**: `<a_140><b_221><c_18>` Crysis - PC _(平台 PC)_ ｜ **native**: `<a_141><b_221><c_44>` Fallout 3 ✗
- **beam top5**: `<a_141><b_203><c_180>`Xbo, `<a_141><b_221><c_44>`?, `<a_195><b_84><c_230>`PC, `<a_141><b_203><c_9>`PS3, `<a_141><b_213><c_117>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PC vs 荐=Xbox360)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（7 个不同 a 大类）；unique(a,b)=9/10，平台数=5，unique标题=10/10。
- **reasoning质量**: 引用历史 1/1（覆盖100%），锚定: Rollercoaster Tycoon 2…；新候选=0（**纯复述历史**）；genre: action,strategy,simulation。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=探索(无关联)(score0)。用户点击比我们top1**更贴历史**(target1>荐0) → 我们把可命中的延续**跑偏**了。

### #376 — 类目错·(a)大类都不对 · BEAM坍缩(<a_140×9/10)
- **历史**(2项; 平台 PC×2): Rollercoaster Tycoon 2: Tr… | Crysis - PC
- **GT**: `<a_10><b_67><c_155>` Diablo III _(平台 ?)_ ｜ **native**: `<a_140><b_161><c_9>` Call of Duty 4: Modern Warfare… ✗
- **beam top5**: `<a_140><b_161><c_25>`Xbo, `<a_140><b_221><c_16>`PC, `<a_80><b_202><c_49>`?, `<a_140><b_221><c_18>`PC, `<a_140><b_221><c_161>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_140 家族 9/10）；unique(a,b)=4/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: Crysis - PC, Rollercoaster Tycoon 2…；新候选=0（**纯复述历史**）；genre: action,shooter,simulation。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #377 — 近失·同(a,b)细分仅c不同
- **历史**(3项; 平台 PC×2,?×1): Rollercoaster Tycoon 2: Tr… | Crysis - PC | Diablo III
- **GT**: `<a_140><b_221><c_145>` Crysis 2 - PC _(平台 PC)_ ｜ **native**: `<a_10><b_67><c_155>` Diablo III ✗
- **beam top5**: `<a_10><b_67><c_155>`?, `<a_141><b_48><c_20>`PC, `<a_141><b_197><c_13>`?, `<a_140><b_221><c_16>`PC, `<a_10><b_79><c_56>`PC
- **推荐↔GT差距**: beam 最接近项与 GT 同 (a,b) 细分、仅 c 不同（同系列/不同款），未命中；beam中 share-a=3/10, share-(a,b)=3/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=7/10，平台数=3，unique标题=9/10。
- **reasoning质量**: 引用历史 2/3（覆盖67%），锚定: Crysis - PC, Diablo III；新候选=0（**纯复述历史**）；模板开头；genre: action,role-playing,shooter。
- **target合理性(天花板)**: target=子类延续(score3); 我们pred[0]=子类延续(score3)。关联档位相同(score3)但选错具体 item。 注意 target 与历史共享词 ['crysis']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #378 — 类目错·(a)大类都不对
- **历史**(4项; 平台 PC×3,?×1): Rollercoaster Tycoon 2: Tr… | Crysis - PC | Diablo III | Crysis 2 - PC
- **GT**: `<a_71><b_212><c_18>` Dishonored - PC _(平台 PC)_ ｜ **native**: `<a_10><b_67><c_155>` Diablo III ✗
- **beam top5**: `<a_10><b_67><c_155>`?, `<a_10><b_20><c_0>`?, `<a_10><b_33><c_116>`?, `<a_10><b_33><c_56>`?, `<a_10><b_67><c_51>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=8/10，平台数=3，unique标题=8/10。
- **reasoning质量**: 引用历史 3/4（覆盖75%），锚定: Crysis - PC, Crysis 2 - PC, Diablo III；新候选=0（**纯复述历史**）；模板开头；genre: action,role-playing,shooter。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=子类延续(score3)。我们推的比用户真实点击**更贴历史**(荐3>target1) → **模型偏保守/用户更爱探索**。

### #379 — 类目错·(a)大类都不对 · BEAM坍缩(<a_175×7/10)
- **历史**(3项; 平台 ?×2,Wii×1): Wii Fit Plus with Balance … | Bully: Scholarship Edition | Bully: Scholarship Edition
- **GT**: `<a_191><b_204><c_225>` Just Cause 3 - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_235><b_65><c_0>` Bully: Scholarship Edition ✗
- **beam top5**: `<a_175><b_171><c_29>`Wii, `<a_175><b_225><c_5>`Wii, `<a_175><b_225><c_3>`Wii, `<a_235><b_65><c_0>`?, `<a_235><b_69><c_186>`Wii
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS4 vs 荐=Wii)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_175 家族 7/10）；unique(a,b)=7/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: Bully: Scholarship Edi…, Wii Fit Plus with Bala…；新候选=0（**纯复述历史**）；genre: action,narrative,humor。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #380 — 类目对·item错
- **历史**(4项; 平台 ?×2,Wii×1,PS4×1): Wii Fit Plus with Balance … | Bully: Scholarship Edition | Bully: Scholarship Edition | Just Cause 3 - PlayStation…
- **GT**: `<a_205><b_207><c_181>` DiRT Rally - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_123><b_72><c_7>` Far Cry 4 - PlayStation 4 ✗
- **beam top5**: `<a_80><b_69><c_85>`PS4, `<a_123><b_72><c_7>`PS4, `<a_80><b_171><c_9>`PS4, `<a_45><b_107><c_1>`PS4, `<a_240><b_132><c_110>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=9/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 2/3（覆盖67%），锚定: Bully: Scholarship Edi…, Just Cause 3 - PlaySta…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。

### #381 — 类目错·(a)大类都不对 · BEAM坍缩(<a_61×10/10)
- **历史**(2项; 平台 DS×1,PC×1): Corsair Gaming VOID USB RG… | Minecraft for PC/Mac [Onli…
- **GT**: `<a_250><b_172><c_5>` Light Blue Yarn Yoshi Amiibo (Yoshi's Woolly W… _(平台 ?)_ ｜ **native**: `<a_61><b_53><c_46>` Xbox One Wireless Controller [… ✗
- **beam top5**: `<a_61><b_53><c_46>`Xbo, `<a_61><b_167><c_197>`Xbo, `<a_61><b_214><c_252>`Xbo, `<a_61><b_217><c_168>`Xbo, `<a_61><b_53><c_5>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_61 家族 10/10）；unique(a,b)=7/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: Corsair Gaming VOID US…, Minecraft for PC/Mac […；新候选=0（**纯复述历史**）；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=探索(无关联)(score0)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #382 — 类目错·(a)大类都不对 · BEAM坍缩(<a_162×8/10)
- **历史**(3项; 平台 DS×1,PC×1,?×1): Corsair Gaming VOID USB RG… | Minecraft for PC/Mac [Onli… | Light Blue Yarn Yoshi Amii…
- **GT**: `<a_7><b_224><c_80>` Microsoft OEM Kinect Adapter for Windows _(平台 PC)_ ｜ **native**: `<a_162><b_116><c_253>` HORI Amiibo Card Folio Officia… ✗
- **beam top5**: `<a_162><b_116><c_253>`?, `<a_162><b_116><c_238>`Wii, `<a_162><b_172><c_85>`?, `<a_162><b_172><c_0>`?, `<a_250><b_172><c_11>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_162 家族 8/10）；unique(a,b)=5/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Corsair Gaming VOID US…, Minecraft for PC/Mac […, Light Blue Yarn Yoshi …；新候选=0（**纯复述历史**）；模板开头；genre: action,peripheral,accessor。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。

### #383 — 类目错·(a)大类都不对
- **历史**(3项; 平台 ?×2,PS3×1): WWE All Stars - Playstatio… | WWE '13 | Dead Space 3 Limited Editi…
- **GT**: `<a_22><b_236><c_185>` Life is Strange - Episode 1 [Online Game Code] _(平台 ?)_ ｜ **native**: `<a_80><b_59><c_29>` Resident Evil 5 - Playstation … ✗
- **beam top5**: `<a_80><b_59><c_29>`PS3, `<a_80><b_59><c_0>`?, `<a_80><b_59><c_15>`PS3, `<a_80><b_212><c_38>`?, `<a_231><b_237><c_131>`PS3
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=6/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: WWE All Stars - Playst…, WWE '13, Dead Space 3 Limited E…；新候选=0（**纯复述历史**）；genre: action,fighting,horror。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=漂移(平台/词面关联)(score1)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #384 — 类目错·(a)大类都不对
- **历史**(4项; 平台 ?×3,PS3×1): WWE All Stars - Playstatio… | WWE '13 | Dead Space 3 Limited Editi… | Life is Strange - Episode …
- **GT**: `<a_92><b_20><c_102>` Call of Duty: Infinite Warfare - Standard Edit… _(平台 PS4)_ ｜ **native**: `<a_80><b_171><c_9>` Need for Speed - PlayStation 4 ✗
- **beam top5**: `<a_71><b_171><c_196>`PS3, `<a_80><b_59><c_29>`PS3, `<a_231><b_107><c_2>`Xbo, `<a_123><b_171><c_136>`?, `<a_80><b_59><c_0>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS4 vs 荐=PS3)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=6/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: WWE All Stars - Playst…, WWE '13, Dead Space 3 Limited E…；新候选=0（**纯复述历史**）；genre: action,rpg,fighting。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=子类延续(score3)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #385 — 类目错·(a)大类都不对 · BEAM坍缩(<a_123×7/10)
- **历史**(5项; 平台 ?×3,PS3×1,PS4×1): WWE All Stars - Playstatio… | WWE '13 | Dead Space 3 Limited Editi… | Life is Strange - Episode … | Call of Duty: Infinite War…
- **GT**: `<a_175><b_171><c_117>` Just Dance 3 _(平台 ?)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_39><b_51><c_188>`PS4, `<a_123><b_58><c_16>`Xbo, `<a_123><b_171><c_44>`Xbo, `<a_123><b_58><c_78>`PS4, `<a_39><b_78><c_54>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_123 家族 7/10）；unique(a,b)=8/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 5/5（覆盖100%），锚定: WWE All Stars - Playst…, WWE '13, Dead Space 3 Limited E…；新候选=0（**纯复述历史**）；模板开头；genre: action,fighting,horror。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=漂移(平台/词面关联)(score1)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #386 — 类目错·(a)大类都不对
- **历史**(4项; 平台 PS4×3,?×1): KontrolFreek FPS Freek Vor… | Pack of 16pcs Pandaren Thu… | Disney Infinity 3.0 Editio… | ASTRO Gaming A50 Wireless …
- **GT**: `<a_201><b_151><c_255>` Playstation Plus: 3 Month Membership [Digital … _(平台 PS-generic)_ ｜ **native**: `<a_49><b_146><c_81>` Disney Infinity 3.0 Edition: S… ✗
- **beam top5**: `<a_49><b_146><c_81>`?, `<a_202><b_86><c_197>`DS, `<a_202><b_11><c_2>`DS, `<a_61><b_85><c_232>`PS4, `<a_49><b_146><c_13>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=7/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: KontrolFreek FPS Freek…, Pack of 16pcs Pandaren…, Disney Infinity 3.0 Ed…；新候选=0（**纯复述历史**）；genre: immersive,peripheral,accessor。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=子类延续(score3)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #387 — 命中@9
- **历史**(2项; 平台 XboxOne×1,PS4×1): Xbox One Limited Edition H… | Controller Gear PS4 Contro…
- **GT**: `<a_201><b_151><c_255>` Playstation Plus: 3 Month Membership [Digital … _(平台 PS-generic)_ ｜ **native**: `<a_61><b_214><c_252>` Xbox One Media Remote ✗
- **beam top5**: `<a_7><b_248><c_16>`Xbo, `<a_74><b_5><c_203>`Xbo, `<a_201><b_36><c_181>`PS4, `<a_7><b_248><c_177>`Xbo, `<a_201><b_31><c_107>`PS4
- **推荐↔GT差距**: 正确项在 beam 第9位，pred[0] 前缀深度仅 0/3；平台错配(GT=PS-generic vs 荐=XboxOne)；beam中 share-a=4/10, share-(a,b)=1/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=8/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 0/2（覆盖0%）；新候选=0（**纯复述历史**）；genre: immersive,narrative,family-friendly。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=子类延续(score3)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #388 — 类目错·(a)大类都不对 · BEAM坍缩(<a_61×7/10)
- **历史**(3项; 平台 XboxOne×1,PS4×1,PS×1): Xbox One Limited Edition H… | Controller Gear PS4 Contro… | Playstation Plus: 3 Month …
- **GT**: `<a_162><b_47><c_65>` Nintendo eShop Gift Card _(平台 ?)_ ｜ **native**: `<a_61><b_214><c_252>` Xbox One Media Remote ✗
- **beam top5**: `<a_7><b_248><c_16>`Xbo, `<a_7><b_248><c_177>`Xbo, `<a_61><b_214><c_252>`Xbo, `<a_61><b_167><c_197>`Xbo, `<a_7><b_115><c_252>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_61 家族 7/10）；unique(a,b)=7/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Xbox One Limited Editi…, Controller Gear PS4 Co…, Playstation Plus: 3 Mo…；新候选=0（**纯复述历史**）；模板开头；genre: action,immersive,controller。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=子类延续(score3)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #389 — 类目错·(a)大类都不对
- **历史**(4项; 平台 XboxOne×1,PS4×1,PS×1): Xbox One Limited Edition H… | Controller Gear PS4 Contro… | Playstation Plus: 3 Month … | Nintendo eShop Gift Card
- **GT**: `<a_21><b_54><c_195>` Old Skool Ac Power Adapter for the Nintendo Ga… _(平台 GameCube)_ ｜ **native**: `<a_162><b_251><c_136>` Animal Crossing: amiibo Festiv… ✗
- **beam top5**: `<a_162><b_251><c_136>`Wii, `<a_61><b_251><c_144>`PS4, `<a_61><b_251><c_51>`PS4, `<a_61><b_251><c_2>`PS4, `<a_61><b_167><c_197>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=GameCube vs 荐=WiiU)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=8/10，平台数=5，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Xbox One Limited Editi…, Controller Gear PS4 Co…, Playstation Plus: 3 Mo…；新候选=0（**纯复述历史**）；模板开头；genre: action,accessor。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #390 — 类目错·(a)大类都不对
- **历史**(5项; 平台 PS4×2,?×2,3DS×1): Pro Evolution Soccer 2016 … | RAZER MAMBA TOURNAMENT EDI… | Kirby: Planet Robobot - Ni… | Pokemon X | Gran Turismo Sport - Limit…
- **GT**: `<a_205><b_252><c_109>` Ride 2 - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_211><b_159><c_71>` Pok&eacute;mon Sun - Nintendo … ✗
- **beam top5**: `<a_211><b_159><c_123>`3DS, `<a_211><b_133><c_30>`3DS, `<a_211><b_159><c_71>`3DS, `<a_211><b_133><c_123>`3DS, `<a_1><b_101><c_0>`Wii
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS4 vs 荐=3DS)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=8/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 4/5（覆盖80%），锚定: Pro Evolution Soccer 2…, Gran Turismo Sport - L…, Pokemon X；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。

### #391 — 类目错·(a)大类都不对
- **历史**(10项; 平台 PS4×4,XboxOne×3,PSVita×2): Call of Duty: Infinite War… | Sony 8GB Memory Card for P… | Dead Rising 4 - Xbox One | Ratchet & Clank Vita Bundl… | Dungeons 2 - PlayStation 4 | Cut The Rope: Triple Treat…
- **GT**: `<a_205><b_208><c_188>` Gran Turismo Sport - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_123><b_58><c_16>`Xbo, `<a_123><b_228><c_123>`Xbo, `<a_123><b_58><c_78>`PS4, `<a_123><b_171><c_44>`Xbo, `<a_123><b_142><c_36>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS4 vs 荐=XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=8/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 5/10（覆盖50%），锚定: Homefront: The Revolut…, Wolfenstein: The Old B…, Dishonored 2 - PlaySta…；新候选=0（**纯复述历史**）；模板开头；genre: action,adventure,shooter。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #392 — 类目对·item错 · BEAM坍缩(<a_123×7/10)
- **历史**(8项; 平台 PS4×8): Assassin's Creed Unity Lim… | Just Cause 3 - PlayStation… | Until Dawn - PlayStation 4 | Watch Dogs 2 - PlayStation… | Batman: Arkham Knight - Pl… | Metal Gear Solid V: The Ph…
- **GT**: `<a_200><b_169><c_179>` Mad Max - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_123><b_72><c_7>` Far Cry 4 - PlayStation 4 ✗
- **beam top5**: `<a_123><b_72><c_7>`PS4, `<a_201><b_213><c_242>`PS4, `<a_123><b_100><c_33>`PS4, `<a_201><b_18><c_56>`PS4, `<a_123><b_76><c_232>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_123 家族 7/10）；unique(a,b)=9/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 6/8（覆盖75%），锚定: Uncharted 4: A Thief's…, Until Dawn - PlayStati…, Just Cause 3 - PlaySta…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #393 — 类目对·item错
- **历史**(9项; 平台 PS4×9): Just Cause 3 - PlayStation… | Until Dawn - PlayStation 4 | Watch Dogs 2 - PlayStation… | Batman: Arkham Knight - Pl… | Metal Gear Solid V: The Ph… | Mad Max - PlayStation 4
- **GT**: `<a_24><b_96><c_27>` Rise of the Tomb Raider: 20 Year Celebration -… _(平台 PS4)_ ｜ **native**: `<a_123><b_72><c_7>` Far Cry 4 - PlayStation 4 ✗
- **beam top5**: `<a_123><b_72><c_7>`PS4, `<a_201><b_213><c_242>`PS4, `<a_200><b_186><c_92>`PS4, `<a_201><b_18><c_56>`PS4, `<a_201><b_145><c_9>`PS4
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台一致(PS4)；beam中 share-a=1/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=9/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 6/9（覆盖67%），锚定: Uncharted 4: A Thief's…, Assassin's Creed Unity…, Just Cause 3 - PlaySta…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #394 — 命中@8 · RERANK伤害
- **历史**(1项; 平台 ?×1): Bloodborne
- **GT**: `<a_194><b_33><c_4>` Dark Souls II: Scholar of the First Sin - Play… _(平台 PS4)_ ｜ **native**: `<a_194><b_33><c_4>` Dark Souls II: Scholar of the … ✓
- **beam top5**: `<a_194><b_87><c_249>`PS4, `<a_201><b_145><c_9>`PS4, `<a_201><b_213><c_242>`PS4, `<a_194><b_87><c_112>`PS4, `<a_194><b_121><c_62>`PS4
- **推荐↔GT差距**: 正确项在 beam 第8位，pred[0] 前缀深度仅 1/3；平台一致(PS4)；beam中 share-a=5/10, share-(a,b)=1/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 1/1（覆盖100%），锚定: Bloodborne；新候选=0（**纯复述历史**）；genre: action,rpg,immersive。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。target 是合理的大类延续，且**已命中**。

### #395 — 类目错·(a)大类都不对
- **历史**(4项; 平台 PS4×3,XboxOne×1): Uncharted 4: A Thief's End… | Mafia III - PlayStation 4 | Xbox One Stereo Headset Ad… | Horizon Zero Dawn - PlaySt…
- **GT**: `<a_202><b_253><c_113>` CORSAIR Sabre - RGB Gaming Mouse - Lightweight… _(平台 ?)_ ｜ **native**: `<a_201><b_56><c_74>` Steep - PS4 Digital Code ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_201><b_18><c_56>`PS4, `<a_191><b_10><c_232>`PS4, `<a_201><b_56><c_74>`PS4, `<a_201><b_45><c_166>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=10/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Uncharted 4: A Thief's…, Horizon Zero Dawn - Pl…, Mafia III - PlayStatio…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=漂移(平台/词面关联)(score1)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #396 — 类目错·(a)大类都不对
- **历史**(4项; 平台 PS4×3,?×1): Senran Kagura Estival Vers… | Dragon Quest Heroes: The W… | Prey - Pre-load - PS4 Digi… | dreamGEAR- Playstation 4 C…
- **GT**: `<a_113><b_152><c_199>` HORI Compact PlayStand - Zelda Edition, Offici… _(平台 Switch)_ ｜ **native**: `<a_201><b_31><c_107>` Uncharted 4: A Thief's End - P… ✗
- **beam top5**: `<a_131><b_41><c_229>`PS4, `<a_201><b_31><c_107>`PS4, `<a_131><b_209><c_151>`PS4, `<a_194><b_87><c_249>`PS4, `<a_1><b_173><c_4>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=Switch vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（6 个不同 a 大类）；unique(a,b)=10/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Senran Kagura Estival …, Dragon Quest Heroes: T…, Prey - Pre-load - PS4 …；新候选=0（**纯复述历史**）；模板开头；genre: action,immersive,narrative。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=漂移(平台/词面关联)(score1)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #397 — 类目错·(a)大类都不对 · BEAM坍缩(<a_131×7/10)
- **历史**(9项; 平台 PS4×4,PC×2,XboxOne×2): Fallout 4 - PC | Fallout 4 - Pip-Boy Editio… | Fallout 4 - Pip-Boy Editio… | Xenoblade Chronicles X | Just Cause 3 - PlayStation… | Deus Ex: Mankind Divided -…
- **GT**: `<a_106><b_116><c_155>` Terraria - Nintendo 3DS _(平台 3DS)_ ｜ **native**: `<a_131><b_224><c_68>` Overwatch - Origins Edition - … ✗
- **beam top5**: `<a_131><b_41><c_229>`PS4, `<a_131><b_41><c_74>`Xbo, `<a_131><b_41><c_210>`PC, `<a_131><b_209><c_151>`PS4, `<a_131><b_224><c_68>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=3DS vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_131 家族 7/10）；unique(a,b)=6/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 4/9（覆盖44%），锚定: Fallout 4 - PC, Fallout 4 - Pip-Boy Ed…, Xenoblade Chronicles X；新候选=0（**纯复述历史**）；模板开头；genre: action,role-playing,immersive。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #398 — 类目错·(a)大类都不对
- **历史**(3项; 平台 PSVita×2,PC×1): Sony PlayStation Vita WiFi | PlayStation Vita Wi-Fi mod… | Grand Theft Auto V - PC Do…
- **GT**: `<a_86><b_149><c_225>` Bully Scholarship Edition - PC _(平台 PC)_ ｜ **native**: `<a_201><b_31><c_107>` Uncharted 4: A Thief's End - P… ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_7><b_248><c_16>`Xbo, `<a_131><b_155><c_206>`Xbo, `<a_201><b_2><c_102>`PS4, `<a_201><b_36><c_181>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PC vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=9/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Sony PlayStation Vita …, PlayStation Vita Wi-Fi…, Grand Theft Auto V - P…；新候选=0（**纯复述历史**）；模板开头；genre: action,immersive,narrative。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=探索(无关联)(score0)。用户点击比我们top1**更贴历史**(target1>荐0) → 我们把可命中的延续**跑偏**了。

### #399 — 类目错·(a)大类都不对
- **历史**(4项; 平台 PSVita×2,PC×2): Sony PlayStation Vita WiFi | PlayStation Vita Wi-Fi mod… | Grand Theft Auto V - PC Do… | Bully Scholarship Edition …
- **GT**: `<a_1><b_209><c_76>` Tales of Symphonia Chronicles - Playstation 3 _(平台 PS3)_ ｜ **native**: `<a_131><b_155><c_206>` Fallout 4 - Xbox One ✗
- **beam top5**: `<a_7><b_248><c_16>`Xbo, `<a_201><b_31><c_107>`PS4, `<a_61><b_167><c_197>`Xbo, `<a_131><b_155><c_206>`Xbo, `<a_61><b_131><c_197>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS3 vs 荐=XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=10/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Sony PlayStation Vita …, PlayStation Vita Wi-Fi…, Grand Theft Auto V - P…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=探索(无关联)(score0)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #400 — 类目对·item错
- **历史**(5项; 平台 PSVita×2,PC×2,PS3×1): Sony PlayStation Vita WiFi | PlayStation Vita Wi-Fi mod… | Grand Theft Auto V - PC Do… | Bully Scholarship Edition … | Tales of Symphonia Chronic…
- **GT**: `<a_1><b_46><c_242>` Tales of Xillia 2 - PlayStation 3 _(平台 PS3)_ ｜ **native**: `<a_1><b_150><c_189>` Legend of Heroes: Trails of Co… ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_131><b_155><c_206>`Xbo, `<a_131><b_210><c_0>`PS4, `<a_1><b_150><c_189>`PS3, `<a_1><b_173><c_4>`PS4
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台错配(GT=PS3 vs 荐=PS4)；beam中 share-a=3/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=10/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 4/5（覆盖80%），锚定: Grand Theft Auto V - P…, Tales of Symphonia Chr…, PlayStation Vita Wi-Fi…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=探索(无关联)(score0)。用户点击比我们top1**更贴历史**(target2>荐0) → 我们把可命中的延续**跑偏**了。 注意 target 与历史共享词 ['tales']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #401 — 类目错·(a)大类都不对 · BEAM坍缩(<a_123×7/10)
- **历史**(4项; 平台 PS4×3,Xbox×1): Middle Earth: Shadow of Mo… | Microsoft Xbox Wireless Ad… | Resident Evil 4 - PlayStat… | Batman: Return to Arkham -…
- **GT**: `<a_86><b_12><c_93>` South Park: The Fractured but Whole - PlayStat… _(平台 PS4)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_39><b_77><c_105>`Xbo, `<a_123><b_100><c_33>`PS4, `<a_123><b_58><c_78>`PS4, `<a_39><b_51><c_188>`PS4, `<a_39><b_78><c_54>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS4 vs 荐=XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_123 家族 7/10）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Middle Earth: Shadow o…, Resident Evil 4 - Play…, Microsoft Xbox Wireles…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=探索(无关联)(score0)。用户点击比我们top1**更贴历史**(target1>荐0) → 我们把可命中的延续**跑偏**了。

### #402 — 类目错·(a)大类都不对 · BEAM坍缩(<a_1×8/10)
- **历史**(4项; 平台 WiiU×2,PS4×2): Xenoblade Chronicles X Spe… | Bayonetta 2 (Single Disc) … | Tales of Zestiria: Collect… | NieR: Automata - Playstati…
- **GT**: `<a_7><b_36><c_217>` Xbox One X 1TB Limited Edition Console - Proje… _(平台 XboxOne)_ ｜ **native**: `<a_1><b_150><c_189>` Legend of Heroes: Trails of Co… ✗
- **beam top5**: `<a_1><b_116><c_233>`PS4, `<a_1><b_150><c_189>`PS3, `<a_1><b_25><c_254>`3DS, `<a_1><b_177><c_184>`PS4, `<a_121><b_76><c_208>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=XboxOne vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_1 家族 8/10）；unique(a,b)=10/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Xenoblade Chronicles X…, Tales of Zestiria: Col…, NieR: Automata - Plays…；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,immersive。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #403 — 类目错·(a)大类都不对
- **历史**(10项; 平台 DS×4,3DS×3,?×2): Radiant Historia - Nintend… | Silent Hill HD Collection … | Spirit Camera: The Cursed … | Fire Emblem: Awakening | Project X Zone - Nintendo … | Shin Megami Tensei IV - Ni…
- **GT**: `<a_1><b_101><c_3>` Xenoblade Chronicles X _(平台 ?)_ ｜ **native**: `<a_195><b_59><c_156>` Shin Megami Tensei IV - Ninten… ✗
- **beam top5**: `<a_30><b_211><c_255>`DS, `<a_216><b_51><c_130>`3DS, `<a_195><b_36><c_218>`?, `<a_30><b_33><c_40>`PSV, `<a_195><b_59><c_156>`3DS
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=9/10，平台数=5，unique标题=10/10。
- **reasoning质量**: 引用历史 7/10（覆盖70%），锚定: Phoenix Wright: Ace At…, Phoenix Wright, Ace At…, Phoenix Wright Ace Att…；新候选=0（**纯复述历史**）；模板开头；genre: action,adventure,rpg。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。

### #404 — 类目错·(a)大类都不对
- **历史**(3项; 平台 ?×2,GameCube×1): Metroid: Other M | Donkey Kong Classics | Soul Calibur II - Gamecube
- **GT**: `<a_193><b_25><c_82>` Star Fox Assault _(平台 ?)_ ｜ **native**: `<a_208><b_51><c_1>` Soul Calibur IV - Playstation … ✗
- **beam top5**: `<a_208><b_51><c_1>`PS3, `<a_208><b_51><c_0>`PS, `<a_208><b_242><c_41>`PS, `<a_1><b_99><c_2>`PS4, `<a_208><b_26><c_212>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=7/10，平台数=7，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Metroid: Other M, Donkey Kong Classics, Soul Calibur II - Game…；新候选=0（**纯复述历史**）；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #405 — 类目对·item错 · BEAM坍缩(<a_205×9/10)
- **历史**(10项; 平台 PS4×8,PSVita×1,PS3×1): Batman: Arkham Knight - Pl… | Horizon Zero Dawn - PlaySt… | Persona 5 - SteelBook Edit… | Back to the Future: The Ga… | Gran Turismo 5 - Playstati… | Gran Turismo Sport - Limit…
- **GT**: `<a_39><b_51><c_188>` Titanfall 2 - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_205><b_62><c_68>` F1 2015 (Formula One) - PlaySt… ✗
- **beam top5**: `<a_24><b_72><c_142>`PS4, `<a_205><b_208><c_52>`?, `<a_205><b_207><c_181>`PS4, `<a_205><b_60><c_93>`PS4, `<a_205><b_8><c_38>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_205 家族 9/10）；unique(a,b)=10/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 6/10（覆盖60%），锚定: Middle Earth: Shadow o…, Tales from the Borderl…, Persona 5 - SteelBook …；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #406 — 类目错·(a)大类都不对
- **历史**(1项; 平台 Xbox360×1): Lego Star Wars: The Comple…
- **GT**: `<a_113><b_136><c_194>` Zettaguard Classic Controller for Nintendo Wii _(平台 Wii)_ ｜ **native**: `<a_245><b_90><c_188>` Lego Star Wars: The Complete S… ✗
- **beam top5**: `<a_49><b_218><c_179>`?, `<a_245><b_26><c_39>`DS, `<a_245><b_185><c_59>`PS4, `<a_49><b_218><c_3>`PSV, `<a_49><b_218><c_101>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=5/10，平台数=8，unique标题=10/10。
- **reasoning质量**: 引用历史 1/1（覆盖100%），锚定: Lego Star Wars: The Co…；新候选=0（**纯复述历史**）；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=漂移(平台/词面关联)(score1)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #407 — 类目错·(a)大类都不对 · BEAM坍缩(<a_113×7/10)
- **历史**(2项; 平台 Xbox360×1,Wii×1): Lego Star Wars: The Comple… | Zettaguard Classic Control…
- **GT**: `<a_49><b_218><c_101>` Lego: Marvel Super Heroes, XBOX 360 _(平台 Xbox360)_ ｜ **native**: `<a_113><b_35><c_14>` Nintendo Super Smash Bros. Bla… ✗
- **beam top5**: `<a_113><b_9><c_63>`Wii, `<a_245><b_26><c_39>`DS, `<a_113><b_35><c_14>`Gam, `<a_113><b_9><c_194>`Wii, `<a_113><b_112><c_109>`Wii
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=Xbox360 vs 荐=WiiU)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_113 家族 7/10）；unique(a,b)=7/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: Lego Star Wars: The Co…, Zettaguard Classic Con…；新候选=0（**纯复述历史**）；genre: action,immersive,nostalg。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['lego']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #408 — 类目错·(a)大类都不对
- **历史**(3项; 平台 Xbox360×2,Wii×1): Lego Star Wars: The Comple… | Zettaguard Classic Control… | Lego: Marvel Super Heroes,…
- **GT**: `<a_189><b_201><c_57>` PlayStation 4 Camera (Old Model) _(平台 PS4)_ ｜ **native**: `<a_113><b_35><c_14>` Nintendo Super Smash Bros. Bla… ✗
- **beam top5**: `<a_113><b_9><c_63>`Wii, `<a_49><b_47><c_60>`PSV, `<a_49><b_218><c_179>`?, `<a_84><b_136><c_91>`Wii, `<a_113><b_35><c_14>`Gam
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS4 vs 荐=WiiU)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=8/10，平台数=5，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Lego Star Wars: The Co…, Lego: Marvel Super Her…, Zettaguard Classic Con…；新候选=0（**纯复述历史**）；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #409 — 类目对·item错
- **历史**(4项; 平台 Xbox360×2,Wii×1,PS4×1): Lego Star Wars: The Comple… | Zettaguard Classic Control… | Lego: Marvel Super Heroes,… | PlayStation 4 Camera (Old …
- **GT**: `<a_84><b_222><c_22>` Mario Kart 8 - Nintendo Wii U _(平台 WiiU)_ ｜ **native**: `<a_231><b_28><c_63>` PlayStation 4 500GB Console [O… ✗
- **beam top5**: `<a_231><b_28><c_63>`PS4, `<a_245><b_185><c_59>`PS4, `<a_49><b_47><c_60>`PSV, `<a_175><b_103><c_7>`PS4, `<a_39><b_50><c_16>`PS3
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台错配(GT=WiiU vs 荐=PS4)；beam中 share-a=1/10, share-(a,b)=0/10。
- **beam多样性**: **高**（7 个不同 a 大类）；unique(a,b)=8/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Lego Star Wars: The Co…, Lego: Marvel Super Her…, Zettaguard Classic Con…；新候选=0（**纯复述历史**）；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=漂移(平台/词面关联)(score1)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #410 — 类目错·(a)大类都不对
- **历史**(5项; 平台 Xbox360×2,Wii×1,PS4×1): Lego Star Wars: The Comple… | Zettaguard Classic Control… | Lego: Marvel Super Heroes,… | PlayStation 4 Camera (Old … | Mario Kart 8 - Nintendo Wi…
- **GT**: `<a_249><b_180><c_74>` PlayStation Vita Memory Card 64GB (PCH-Z641J) _(平台 PSVita)_ ｜ **native**: `<a_84><b_217><c_3>` HORI Mario Kart 8 Racing Wheel… ✗
- **beam top5**: `<a_84><b_217><c_3>`Wii, `<a_84><b_235><c_3>`Wii, `<a_245><b_232><c_39>`PSV, `<a_84><b_222><c_22>`Wii, `<a_84><b_149><c_181>`Wii
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PSVita vs 荐=WiiU)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=9/10，平台数=5，unique标题=10/10。
- **reasoning质量**: 引用历史 4/5（覆盖80%），锚定: Lego Star Wars: The Co…, Lego: Marvel Super Her…, Zettaguard Classic Con…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #411 — 类目错·(a)大类都不对
- **历史**(6项; 平台 Xbox360×2,Wii×1,PS4×1): Lego Star Wars: The Comple… | Zettaguard Classic Control… | Lego: Marvel Super Heroes,… | PlayStation 4 Camera (Old … | Mario Kart 8 - Nintendo Wi… | PlayStation Vita Memory Ca…
- **GT**: `<a_92><b_68><c_129>` Doom - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_84><b_149><c_181>` Beastron Mario Kart Racing Whe… ✗
- **beam top5**: `<a_84><b_235><c_3>`Wii, `<a_245><b_185><c_59>`PS4, `<a_245><b_232><c_39>`PSV, `<a_49><b_112><c_10>`?, `<a_245><b_232><c_5>`PS3
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS4 vs 荐=WiiU)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=9/10，平台数=6，unique标题=10/10。
- **reasoning质量**: 引用历史 5/6（覆盖83%），锚定: Lego Star Wars: The Co…, Lego: Marvel Super Her…, Mario Kart 8 - Nintend…；新候选=0（**纯复述历史**）；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #412 — 类目错·(a)大类都不对
- **历史**(7项; 平台 Xbox360×2,PS4×2,Wii×1): Zettaguard Classic Control… | Lego: Marvel Super Heroes,… | PlayStation 4 Camera (Old … | Mario Kart 8 - Nintendo Wi… | PlayStation Vita Memory Ca… | Doom - PlayStation 4
- **GT**: `<a_61><b_131><c_197>` Microsoft Xbox Wireless Adapter for Windows 10 _(平台 Xbox)_ ｜ **native**: `<a_201><b_31><c_107>` Uncharted 4: A Thief's End - P… ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_201><b_213><c_242>`PS4, `<a_131><b_210><c_0>`PS4, `<a_201><b_2><c_102>`PS4, `<a_201><b_201><c_84>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=Xbox vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（6 个不同 a 大类）；unique(a,b)=10/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 5/7（覆盖71%），锚定: Lego Star Wars: The Co…, Lego: Marvel Super Her…, Mario Kart 8 - Nintend…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=漂移(平台/词面关联)(score1)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #413 — 类目对·item错
- **历史**(8项; 平台 Xbox360×2,PS4×2,Wii×1): Lego: Marvel Super Heroes,… | PlayStation 4 Camera (Old … | Mario Kart 8 - Nintendo Wi… | PlayStation Vita Memory Ca… | Doom - PlayStation 4 | Microsoft Xbox Wireless Ad…
- **GT**: `<a_61><b_70><c_135>` Xbox Elite Wireless Controller _(平台 Xbox)_ ｜ **native**: `<a_61><b_131><c_197>` Microsoft Xbox Wireless Adapte… ✗
- **beam top5**: `<a_61><b_167><c_197>`Xbo, `<a_61><b_131><c_197>`Xbo, `<a_201><b_31><c_107>`PS4, `<a_131><b_210><c_0>`PS4, `<a_131><b_41><c_229>`PS4
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台错配(GT=Xbox vs 荐=XboxOne)；beam中 share-a=2/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=9/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 4/8（覆盖50%），锚定: Lego Star Wars: The Co…, Lego: Marvel Super Her…, PlayStation 4 Camera (…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。 注意 target 与历史共享词 ['controller', 'wireless']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #414 — 类目对·item错 · BEAM坍缩(<a_61×7/10)
- **历史**(9项; 平台 Xbox360×2,PS4×2,Xbox×2): PlayStation 4 Camera (Old … | Mario Kart 8 - Nintendo Wi… | PlayStation Vita Memory Ca… | Doom - PlayStation 4 | Microsoft Xbox Wireless Ad… | Xbox Elite Wireless Contro…
- **GT**: `<a_24><b_185><c_47>` ReCore - Xbox One _(平台 XboxOne)_ ｜ **native**: `<a_61><b_167><c_164>` Microsoft Xbox One Controller … ✗
- **beam top5**: `<a_61><b_167><c_197>`Xbo, `<a_61><b_167><c_164>`Xbo, `<a_201><b_31><c_107>`PS4, `<a_61><b_111><c_109>`Xbo, `<a_61><b_131><c_197>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_61 家族 7/10）；unique(a,b)=9/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 2/9（覆盖22%），锚定: Mario Kart 8 - Nintend…, Doom - PlayStation 4；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #415 — 类目错·(a)大类都不对
- **历史**(10项; 平台 Xbox360×2,PS4×2,Xbox×2): Mario Kart 8 - Nintendo Wi… | PlayStation Vita Memory Ca… | Doom - PlayStation 4 | Microsoft Xbox Wireless Ad… | Xbox Elite Wireless Contro… | ReCore - Xbox One
- **GT**: `<a_8><b_34><c_189>` Nintendo 3DS XL Battery Replacement SPR-003 (N… _(平台 3DS)_ ｜ **native**: `<a_61><b_214><c_225>` PDP Talon Media Remote Control… ✗
- **beam top5**: `<a_39><b_77><c_105>`Xbo, `<a_123><b_58><c_78>`PS4, `<a_39><b_51><c_21>`Xbo, `<a_24><b_72><c_142>`PS4, `<a_201><b_56><c_74>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=3DS vs 荐=XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（7 个不同 a 大类）；unique(a,b)=10/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 2/10（覆盖20%），锚定: Lego Star Wars: The Co…, Lego: Marvel Super Her…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=漂移(平台/词面关联)(score1)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #416 — 类目错·(a)大类都不对 · BEAM坍缩(<a_61×10/10)
- **历史**(10项; 平台 PS4×2,Xbox×2,Wii×1): PlayStation Vita Memory Ca… | Doom - PlayStation 4 | Microsoft Xbox Wireless Ad… | Xbox Elite Wireless Contro… | ReCore - Xbox One | Nintendo 3DS XL Battery Re…
- **GT**: `<a_39><b_78><c_205>` Battlefield 1 - Xbox One _(平台 XboxOne)_ ｜ **native**: `<a_61><b_111><c_109>` Xbox One Chatpad + Chat Headse… ✗
- **beam top5**: `<a_61><b_251><c_144>`PS4, `<a_61><b_111><c_109>`Xbo, `<a_61><b_214><c_225>`Xbo, `<a_61><b_131><c_197>`Xbo, `<a_61><b_137><c_255>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=XboxOne vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_61 家族 10/10）；unique(a,b)=7/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 7/10（覆盖70%），锚定: PlayStation 4 Camera (…, Microsoft Xbox Wireles…, ReCore - Xbox One；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #417 — 类目错·(a)大类都不对 · BEAM坍缩(<a_39×7/10)
- **历史**(10项; 平台 PS4×2,Xbox×2,XboxOne×2): Doom - PlayStation 4 | Microsoft Xbox Wireless Ad… | Xbox Elite Wireless Contro… | ReCore - Xbox One | Nintendo 3DS XL Battery Re… | Battlefield 1 - Xbox One
- **GT**: `<a_194><b_235><c_193>` Final Fantasy XII: The Zodiac Age - PlayStatio… _(平台 PS4)_ ｜ **native**: `<a_39><b_77><c_105>` Call of Duty: Infinite Warfare… ✗
- **beam top5**: `<a_39><b_77><c_105>`Xbo, `<a_39><b_51><c_21>`Xbo, `<a_123><b_58><c_78>`PS4, `<a_39><b_77><c_69>`Xbo, `<a_39><b_175><c_240>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS4 vs 荐=XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_39 家族 7/10）；unique(a,b)=8/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/10（覆盖40%），锚定: Lego: Marvel Super Her…, Battlefield 1 - Xbox O…, PlayStation 4 Camera (…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #418 — 类目错·(a)大类都不对
- **历史**(10项; 平台 PS4×3,Xbox×2,XboxOne×2): Microsoft Xbox Wireless Ad… | Xbox Elite Wireless Contro… | ReCore - Xbox One | Nintendo 3DS XL Battery Re… | Battlefield 1 - Xbox One | Final Fantasy XII: The Zod…
- **GT**: `<a_216><b_123><c_81>` Apollo Justice: Ace Attorney _(平台 ?)_ ｜ **native**: `<a_131><b_52><c_86>` Gears of War 4 - Xbox One ✗
- **beam top5**: `<a_39><b_77><c_105>`Xbo, `<a_39><b_51><c_21>`Xbo, `<a_123><b_58><c_78>`PS4, `<a_24><b_72><c_142>`PS4, `<a_194><b_15><c_66>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（6 个不同 a 大类）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 5/10（覆盖50%），锚定: Battlefield 1 - Xbox O…, Final Fantasy XII: The…, PlayStation 4 Camera (…；新候选=0（**纯复述历史**）；模板开头；genre: action,adventure,shooter。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #419 — 类目错·(a)大类都不对
- **历史**(10项; 平台 PS4×2,Xbox×2,XboxOne×2): Xbox Elite Wireless Contro… | ReCore - Xbox One | Nintendo 3DS XL Battery Re… | Battlefield 1 - Xbox One | Final Fantasy XII: The Zod… | Apollo Justice: Ace Attorn…
- **GT**: `<a_195><b_197><c_114>` Ace Attorney Investigations: Miles Edgeworth _(平台 ?)_ ｜ **native**: `<a_216><b_27><c_5>` Phoenix Wright: Ace Attorney -… ✗
- **beam top5**: `<a_216><b_27><c_0>`DS, `<a_216><b_27><c_5>`DS, `<a_216><b_27><c_1>`DS, `<a_216><b_48><c_110>`3DS, `<a_216><b_44><c_79>`3DS
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=8/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 6/10（覆盖60%），锚定: Mario Kart 8 - Nintend…, Battlefield 1 - Xbox O…, Final Fantasy XII: The…；新候选=0（**纯复述历史**）；模板开头；genre: action,shooter,racing。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['ace', 'attorney']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #420 — 类目错·(a)大类都不对
- **历史**(10项; 平台 PS4×2,Xbox×2,XboxOne×2): ReCore - Xbox One | Nintendo 3DS XL Battery Re… | Battlefield 1 - Xbox One | Final Fantasy XII: The Zod… | Apollo Justice: Ace Attorn… | Ace Attorney Investigation…
- **GT**: `<a_194><b_148><c_225>` Dark Souls - Xbox 360 _(平台 Xbox360)_ ｜ **native**: `<a_30><b_211><c_255>` Ghost Trick: Phantom Detective… ✗
- **beam top5**: `<a_216><b_92><c_192>`3DS, `<a_30><b_211><c_255>`DS, `<a_30><b_144><c_145>`PSV, `<a_216><b_27><c_5>`DS, `<a_216><b_92><c_163>`3DS
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=Xbox360 vs 荐=3DS)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=8/10，平台数=6，unique标题=10/10。
- **reasoning质量**: 引用历史 4/10（覆盖40%），锚定: ReCore - Xbox One, Final Fantasy XII: The…, Apollo Justice: Ace At…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。

### #421 — 类目错·(a)大类都不对 · BEAM坍缩(<a_194×10/10)
- **历史**(10项; 平台 PS4×2,Xbox×2,XboxOne×2): Nintendo 3DS XL Battery Re… | Battlefield 1 - Xbox One | Final Fantasy XII: The Zod… | Apollo Justice: Ace Attorn… | Ace Attorney Investigation… | Dark Souls - Xbox 360
- **GT**: `<a_61><b_56><c_1>` Dragonpad Wired USB Controller (Black) for PC … _(平台 Xbox360)_ ｜ **native**: `<a_194><b_20><c_194>` Dark Souls III: Day 1 Edition … ✗
- **beam top5**: `<a_194><b_215><c_154>`?, `<a_194><b_33><c_2>`Xbo, `<a_194><b_15><c_66>`PS4, `<a_194><b_33><c_4>`PS4, `<a_194><b_87><c_112>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_194 家族 10/10）；unique(a,b)=6/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 8/10（覆盖80%），锚定: Doom - PlayStation 4, ReCore - Xbox One, Final Fantasy XII: The…；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,shooter。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。 注意 target 与历史共享词 ['controller']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #422 — 类目对·item错 · BEAM坍缩(<a_61×10/10)
- **历史**(10项; 平台 Xbox×2,XboxOne×2,?×2): Battlefield 1 - Xbox One | Final Fantasy XII: The Zod… | Apollo Justice: Ace Attorn… | Ace Attorney Investigation… | Dark Souls - Xbox 360 | Dragonpad Wired USB Contro…
- **GT**: `<a_10><b_16><c_3>` Dragon Age Inquisition - Deluxe Edition -  Xbo… _(平台 XboxOne)_ ｜ **native**: `<a_61><b_56><c_2>` Wired USB Controller for PC & … ✗
- **beam top5**: `<a_61><b_167><c_164>`Xbo, `<a_61><b_150><c_0>`Xbo, `<a_61><b_9><c_122>`PS3, `<a_61><b_56><c_2>`Xbo, `<a_61><b_98><c_108>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_61 家族 10/10）；unique(a,b)=9/10，平台数=6，unique标题=10/10。
- **reasoning质量**: 引用历史 6/10（覆盖60%），锚定: Battlefield 1 - Xbox O…, Final Fantasy XII: The…, Microsoft Xbox Wireles…；新候选=0（**纯复述历史**）；模板开头；genre: action,adventure,rpg。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['age']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #423 — 类目对·item错
- **历史**(10项; 平台 XboxOne×3,?×2,Xbox360×2): Final Fantasy XII: The Zod… | Apollo Justice: Ace Attorn… | Ace Attorney Investigation… | Dark Souls - Xbox 360 | Dragonpad Wired USB Contro… | Dragon Age Inquisition - D…
- **GT**: `<a_205><b_136><c_51>` Forza Horizon 2 for Xbox One _(平台 XboxOne)_ ｜ **native**: `<a_10><b_16><c_4>` Dragon Age Inquisition - Delux… ✗
- **beam top5**: `<a_194><b_33><c_2>`Xbo, `<a_216><b_27><c_5>`DS, `<a_194><b_215><c_154>`?, `<a_10><b_53><c_1>`Xbo, `<a_194><b_33><c_4>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=7/10，平台数=5，unique标题=10/10。
- **reasoning质量**: 引用历史 7/10（覆盖70%），锚定: ReCore - Xbox One, Final Fantasy XII: The…, Dark Souls - Xbox 360；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #424 — 类目错·(a)大类都不对
- **历史**(9项; 平台 3DS×3,?×2,XboxOne×1): The Last of Us Remastered … | Nintendo New 3DS XL - Blac… | Microsoft Xbox Wireless Ad… | Nintendo 3DS Compatible wi… | Gen USB Charge Cable for N… | Generic 3.6V 3600mAh Batte…
- **GT**: `<a_249><b_31><c_126>` Sony PlayStation Vita WiFi _(平台 PSVita)_ ｜ **native**: `<a_113><b_235><c_2>` Nintendo New 3DS XL - Black ✗
- **beam top5**: `<a_113><b_235><c_2>`3DS, `<a_119><b_168><c_182>`3DS, `<a_113><b_235><c_28>`3DS, `<a_113><b_104><c_28>`3DS, `<a_113><b_31><c_215>`3DS
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PSVita vs 荐=3DS)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=7/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 5/9（覆盖56%），锚定: Xbox One Play and Char…, Gen USB Charge Cable f…, Nintendo New 3DS XL - …；新候选=0（**纯复述历史**）；模板开头；genre: action,immersive,narrative。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=子类延续(score3)。我们推的比用户真实点击**更贴历史**(荐3>target1) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['sony']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #425 — 类目错·(a)大类都不对 · BEAM坍缩(<a_202×8/10)
- **历史**(3项; 平台 PC×1,Switch×1,WiiU×1): MAYFLASH N64 Controller Ad… | CM Storm QuickFire Rapid-i… | Mayflash GameCube Controll…
- **GT**: `<a_61><b_91><c_41>` HORI Real Arcade Pro 4 Kai for PlayStation 4, … _(平台 PS4)_ ｜ **native**: `<a_202><b_34><c_140>` Logitech G402 Hyperion Fury FP… ✗
- **beam top5**: `<a_202><b_253><c_158>`?, `<a_202><b_82><c_172>`?, `<a_202><b_253><c_105>`?, `<a_202><b_34><c_39>`?, `<a_202><b_34><c_140>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_202 家族 8/10）；unique(a,b)=7/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: MAYFLASH N64 Controlle…, CM Storm QuickFire Rap…, Mayflash GameCube Cont…；新候选=0（**纯复述历史**）；genre: action,nostalg,retro。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #426 — 类目错·(a)大类都不对
- **历史**(4项; 平台 PC×1,Switch×1,WiiU×1): MAYFLASH N64 Controller Ad… | CM Storm QuickFire Rapid-i… | Mayflash GameCube Controll… | HORI Real Arcade Pro 4 Kai…
- **GT**: `<a_202><b_203><c_93>` SteelSeries Rival 300, Optical Gaming Mouse - … _(平台 ?)_ ｜ **native**: `<a_61><b_91><c_41>` HORI Real Arcade Pro 4 Kai for… ✗
- **beam top5**: `<a_61><b_99><c_240>`PS3, `<a_61><b_91><c_41>`PS4, `<a_61><b_166><c_249>`PS3, `<a_61><b_166><c_225>`PS4, `<a_113><b_35><c_8>`Gam
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（2 个 a 大类）；unique(a,b)=5/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: MAYFLASH N64 Controlle…, CM Storm QuickFire Rap…, Mayflash GameCube Cont…；新候选=0（**纯复述历史**）；genre: action,nostalg,retro。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。 注意 target 与历史共享词 ['gaming']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #427 — 近失·同(a,b)细分仅c不同 · BEAM坍缩(<a_202×10/10)
- **历史**(5项; 平台 PC×1,Switch×1,WiiU×1): MAYFLASH N64 Controller Ad… | CM Storm QuickFire Rapid-i… | Mayflash GameCube Controll… | HORI Real Arcade Pro 4 Kai… | SteelSeries Rival 300, Opt…
- **GT**: `<a_202><b_58><c_57>` Logitech G610 Orion Brown Backlit Mechanical G… _(平台 ?)_ ｜ **native**: `<a_202><b_120><c_89>` Logitech G900 Chaos Spectrum P… ✗
- **beam top5**: `<a_202><b_253><c_105>`?, `<a_202><b_3><c_27>`?, `<a_202><b_3><c_102>`?, `<a_202><b_58><c_107>`?, `<a_202><b_120><c_89>`?
- **推荐↔GT差距**: beam 最接近项与 GT 同 (a,b) 细分、仅 c 不同（同系列/不同款），未命中；beam中 share-a=10/10, share-(a,b)=1/10。
- **beam多样性**: **低**（坍缩到 <a_202 家族 10/10）；unique(a,b)=9/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 5/5（覆盖100%），锚定: MAYFLASH N64 Controlle…, CM Storm QuickFire Rap…, HORI Real Arcade Pro 4…；新候选=0（**纯复述历史**）；模板开头；genre: action,nostalg,retro。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。 注意 target 与历史共享词 ['backlit', 'brown', 'gaming', 'keyboard', 'mechanical']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #428 — 类目错·(a)大类都不对
- **历史**(9项; 平台 PS4×6,XboxOne×2,Xbox360×1): Call of Duty: Infinite War… | Senran Kagura Estival Vers… | Doom - PlayStation 4 | NieR: Automata - Playstati… | Prey - Pre-load - PS4 Digi… | Call of Duty: Ghosts Harde…
- **GT**: `<a_231><b_76><c_105>` MOE CHRONICLE (ENGLISH SUBTITLES) - PS VITA _(平台 PSVita)_ ｜ **native**: `<a_194><b_15><c_66>` Dishonored 2 - PlayStation 4 ✗
- **beam top5**: `<a_194><b_87><c_112>`PS4, `<a_194><b_15><c_66>`PS4, `<a_1><b_43><c_207>`PS4, `<a_24><b_72><c_142>`PS4, `<a_24><b_129><c_173>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PSVita vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（6 个不同 a 大类）；unique(a,b)=10/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 7/9（覆盖78%），锚定: Dark Souls - Xbox 360, Dark Souls III: Collec…, Call of Duty: Infinite…；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,multiplayer。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #429 — 类目对·item错 · BEAM坍缩(<a_162×10/10)
- **历史**(8项; 平台 ?×6,3DS×2): Mario Classic Color Amiibo… | Nintendo Selects: Super Ma… | Skque 28 in 1 Game Card Ca… | PowerA Universal Nintendo … | Nintendo Selects: Super Ma… | Yoshi amiibo (Super Smash …
- **GT**: `<a_162><b_2><c_193>` Nintendo Falco Amiibo - Wii U _(平台 WiiU)_ ｜ **native**: `<a_162><b_219><c_249>` Ganondorf amiibo - Japan Impor… ✗
- **beam top5**: `<a_162><b_231><c_30>`?, `<a_162><b_242><c_145>`?, `<a_162><b_235><c_217>`?, `<a_162><b_219><c_174>`?, `<a_162><b_214><c_137>`?
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；beam中 share-a=10/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_162 家族 10/10）；unique(a,b)=8/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 6/8（覆盖75%），锚定: Mario Modern Color Ami…, amiibo Rosetta & Chiko…, Mario Classic Color Am…；新候选=0（**纯复述历史**）；模板开头；genre: action,nostalg,accessor。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。 注意 target 与历史共享词 ['amiibo']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #430 — 类目对·item错 · BEAM坍缩(<a_61×10/10)
- **历史**(3项; 平台 XboxOne×3): Turtle Beach - Ear Force R… | Xbox One Play and Charge K… | Xbox One Chatpad + Chat He…
- **GT**: `<a_194><b_36><c_216>` Final Fantasy XV - Xbox One _(平台 XboxOne)_ ｜ **native**: `<a_61><b_137><c_255>` Xbox One Kinect Sensor with Da… ✗
- **beam top5**: `<a_61><b_167><c_197>`Xbo, `<a_61><b_227><c_97>`Xbo, `<a_61><b_131><c_197>`Xbo, `<a_61><b_214><c_252>`Xbo, `<a_61><b_53><c_5>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_61 家族 10/10）；unique(a,b)=7/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Turtle Beach - Ear For…, Xbox One Chatpad + Cha…, Xbox One Play and Char…；新候选=0（**纯复述历史**）；genre: action,multiplayer,accessor。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #431 — 类目错·(a)大类都不对
- **历史**(4项; 平台 XboxOne×4): Turtle Beach - Ear Force R… | Xbox One Play and Charge K… | Xbox One Chatpad + Chat He… | Final Fantasy XV - Xbox On…
- **GT**: `<a_123><b_72><c_191>` Far Cry 4 - Xbox One _(平台 XboxOne)_ ｜ **native**: `<a_7><b_11><c_2>` PDP Titanfall 2 Official Marau… ✗
- **beam top5**: `<a_61><b_131><c_197>`Xbo, `<a_39><b_77><c_105>`Xbo, `<a_7><b_248><c_16>`Xbo, `<a_7><b_36><c_0>`Xbo, `<a_7><b_248><c_2>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=XboxOne vs 荐=Xbox)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 3/4（覆盖75%），锚定: Turtle Beach - Ear For…, Xbox One Play and Char…, Final Fantasy XV - Xbo…；新候选=0（**纯复述历史**）；genre: action,immersive,narrative。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #432 — 近失·同(a,b)细分仅c不同
- **历史**(5项; 平台 XboxOne×5): Turtle Beach - Ear Force R… | Xbox One Play and Charge K… | Xbox One Chatpad + Chat He… | Final Fantasy XV - Xbox On… | Far Cry 4 - Xbox One
- **GT**: `<a_7><b_36><c_217>` Xbox One X 1TB Limited Edition Console - Proje… _(平台 XboxOne)_ ｜ **native**: `<a_131><b_155><c_206>` Fallout 4 - Xbox One ✗
- **beam top5**: `<a_39><b_77><c_105>`Xbo, `<a_131><b_155><c_206>`Xbo, `<a_7><b_248><c_16>`Xbo, `<a_7><b_36><c_0>`Xbo, `<a_39><b_77><c_69>`Xbo
- **推荐↔GT差距**: beam 最接近项与 GT 同 (a,b) 细分、仅 c 不同（同系列/不同款），未命中；平台一致(XboxOne)；beam中 share-a=3/10, share-(a,b)=1/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=8/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 5/5（覆盖100%），锚定: Turtle Beach - Ear For…, Xbox One Play and Char…, Xbox One Chatpad + Cha…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=漂移(平台/词面关联)(score1)。用户点击比我们top1**更贴历史**(target2>荐1) → 我们把可命中的延续**跑偏**了。 注意 target 与历史共享词 ['discontinued']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #433 — 类目对·item错
- **历史**(2项; 平台 PS4×2): Uncharted 4: A Thief's End… | Batman: Arkham Knight - Pl…
- **GT**: `<a_71><b_86><c_236>` UNCHARTED: The Nathan Drake Collection - PlayS… _(平台 PS4)_ ｜ **native**: `<a_201><b_31><c_107>` Uncharted 4: A Thief's End - P… ✗
- **beam top5**: `<a_201><b_145><c_9>`PS4, `<a_201><b_213><c_242>`PS4, `<a_123><b_72><c_7>`PS4, `<a_123><b_129><c_247>`PS4, `<a_131><b_210><c_0>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=10/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: Uncharted 4: A Thief's…, Batman: Arkham Knight …；新候选=0（**纯复述历史**）；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['uncharted']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #434 — 类目对·item错
- **历史**(4项; 平台 PSVita×4): Ratchet & Clank Vita Bundl… | PlayStation All-Stars Batt… | Sly Cooper: Thieves in Tim… | The Sly Collection - PlayS…
- **GT**: `<a_74><b_115><c_116>` Injustice 2 - PS4 [Digital Code] _(平台 PS4)_ ｜ **native**: `<a_74><b_218><c_91>` Ratchet and Clank: Into the Ne… ✗
- **beam top5**: `<a_74><b_218><c_91>`PS3, `<a_74><b_218><c_196>`PS, `<a_74><b_229><c_149>`PS, `<a_74><b_218><c_206>`PS4, `<a_193><b_21><c_3>`PS
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台错配(GT=PS4 vs 荐=PS3)；beam中 share-a=5/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=7/10，平台数=5，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Ratchet & Clank Vita B…, PlayStation All-Stars …, Sly Cooper: Thieves in…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。 注意 target 与历史共享词 ['code', 'digital']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #435 — 类目对·item错
- **历史**(4项; 平台 PS4×4): Metal Gear Solid V: The Ph… | Naruto Shippuden: Ultimate… | Uncharted 4: A Thief's End… | Titanfall 2 - PlayStation …
- **GT**: `<a_92><b_20><c_102>` Call of Duty: Infinite Warfare - Standard Edit… _(平台 PS4)_ ｜ **native**: `<a_39><b_51><c_21>` Titanfall 2 - Xbox One ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_39><b_51><c_21>`Xbo, `<a_39><b_77><c_105>`Xbo, `<a_39><b_78><c_54>`PS4, `<a_201><b_56><c_74>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=8/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 3/4（覆盖75%），锚定: Metal Gear Solid V: Th…, Uncharted 4: A Thief's…, Titanfall 2 - PlayStat…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。

### #436 — 类目错·(a)大类都不对
- **历史**(2项; 平台 3DS×1,?×1): Nintendo 3DS Compatible wi… | The Legend of Zelda: Major…
- **GT**: `<a_71><b_159><c_7>` Castlevania: Portrait of Ruin _(平台 ?)_ ｜ **native**: `<a_216><b_112><c_114>` The Legend of Zelda: The Wind … ✗
- **beam top5**: `<a_113><b_235><c_2>`3DS, `<a_216><b_112><c_114>`Wii, `<a_119><b_168><c_182>`3DS, `<a_216><b_93><c_101>`DS, `<a_211><b_112><c_5>`3DS
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=8/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: Nintendo 3DS Compatibl…, The Legend of Zelda: M…；新候选=0（**纯复述历史**）；genre: action,puzzle,immersive。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #437 — 类目对·item错 · BEAM坍缩(<a_216×10/10)
- **历史**(3项; 平台 ?×2,3DS×1): Nintendo 3DS Compatible wi… | The Legend of Zelda: Major… | Castlevania: Portrait of R…
- **GT**: `<a_216><b_124><c_98>` Castlevania _(平台 ?)_ ｜ **native**: `<a_216><b_112><c_114>` The Legend of Zelda: The Wind … ✗
- **beam top5**: `<a_216><b_112><c_114>`Wii, `<a_216><b_159><c_141>`3DS, `<a_216><b_93><c_101>`DS, `<a_216><b_51><c_130>`3DS, `<a_216><b_219><c_158>`3DS
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；beam中 share-a=10/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_216 家族 10/10）；unique(a,b)=8/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Nintendo 3DS Compatibl…, The Legend of Zelda: M…, Castlevania: Portrait …；新候选=0（**纯复述历史**）；genre: action,adventure,rpg。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=子类延续(score3)。我们推的比用户真实点击**更贴历史**(荐3>target2) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['castlevania']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #438 — 类目对·item错 · BEAM坍缩(<a_123×7/10)
- **历史**(2项; 平台 PS4×2): 7 Days to Die - PlayStatio… | No Man's Sky - Limited Edi…
- **GT**: `<a_61><b_106><c_251>` HORI Fighting Stick Mini 4 for PlayStation 4 a… _(平台 PS4)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_123><b_129><c_247>`PS4, `<a_123><b_58><c_16>`Xbo, `<a_123><b_58><c_78>`PS4, `<a_131><b_209><c_151>`PS4, `<a_123><b_160><c_188>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_123 家族 7/10）；unique(a,b)=8/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: 7 Days to Die - PlaySt…, No Man's Sky - Limited…；新候选=0（**纯复述历史**）；模板开头；genre: action,adventure,strategy。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #439 — 类目错·(a)大类都不对
- **历史**(4项; 平台 XboxOne×3,3DS×1): FIFA 16 - Standard Edition… | Tom Clancy&rsquo;s Ghost R… | FIFA 17 - Xbox One | Shovel Knight - Nintendo 3…
- **GT**: `<a_39><b_51><c_21>` Titanfall 2 - Xbox One _(平台 XboxOne)_ ｜ **native**: `<a_239><b_32><c_170>` Chibi-Robo!: Zip Lash - Ninten… ✗
- **beam top5**: `<a_239><b_32><c_111>`3DS, `<a_239><b_32><c_170>`3DS, `<a_1><b_101><c_3>`?, `<a_1><b_121><c_178>`3DS, `<a_1><b_25><c_254>`3DS
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=XboxOne vs 荐=3DS)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=9/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: FIFA 16 - Standard Edi…, FIFA 17 - Xbox One, Tom Clancy&rsquo;s Gho…；新候选=0（**纯复述历史**）；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #440 — 类目错·(a)大类都不对
- **历史**(5项; 平台 PS4×4,Xbox360×1): Assassin's Creed: Syndicat… | Fallout 4 - PlayStation 4 | Batman: Arkham Knight - Pl… | Deus Ex: Mankind Divided -… | Tom Clancy's Rainbow Six V…
- **GT**: `<a_194><b_76><c_27>` The Witcher Enhanced - PC _(平台 PC)_ ｜ **native**: `<a_39><b_156><c_118>` Tom Clancy's Rainbow Six Siege… ✗
- **beam top5**: `<a_123><b_129><c_247>`PS4, `<a_123><b_193><c_255>`PS4, `<a_123><b_72><c_7>`PS4, `<a_39><b_156><c_118>`Xbo, `<a_39><b_156><c_145>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PC vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（2 个 a 大类）；unique(a,b)=7/10，平台数=5，unique标题=10/10。
- **reasoning质量**: 引用历史 5/5（覆盖100%），锚定: Assassin's Creed: Synd…, Fallout 4 - PlayStatio…, Batman: Arkham Knight …；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=漂移(平台/词面关联)(score1)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #441 — 类目对·item错 · BEAM坍缩(<a_123×8/10)
- **历史**(6项; 平台 PS4×4,Xbox360×1,PC×1): Assassin's Creed: Syndicat… | Fallout 4 - PlayStation 4 | Batman: Arkham Knight - Pl… | Deus Ex: Mankind Divided -… | Tom Clancy's Rainbow Six V… | The Witcher Enhanced - PC
- **GT**: `<a_194><b_72><c_187>` The Witcher 2: Assassins Of Kings - Enhanced E… _(平台 Xbox360)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_123><b_100><c_33>`PS4, `<a_39><b_51><c_188>`PS4, `<a_123><b_58><c_78>`PS4, `<a_123><b_58><c_16>`Xbo, `<a_123><b_76><c_232>`PS4
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台错配(GT=Xbox360 vs 荐=PS4)；beam中 share-a=1/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_123 家族 8/10）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 5/6（覆盖83%），锚定: Assassin's Creed: Synd…, The Witcher Enhanced -…, Tom Clancy's Rainbow S…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=漂移(平台/词面关联)(score1)。用户点击比我们top1**更贴历史**(target2>荐1) → 我们把可命中的延续**跑偏**了。 注意 target 与历史共享词 ['enhanced', 'witcher']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #442 — 类目对·item错
- **历史**(4项; 平台 Wii×2,XboxOne×2): Wii Nunchuk Controller - W… | Wii Remote Controller | Zoo Tycoon XBOX ONE | Xbox One 500 GB Console - …
- **GT**: `<a_61><b_183><c_108>` Controller Gear Controller Stand v1.0 - Offici… _(平台 XboxOne)_ ｜ **native**: `<a_61><b_53><c_5>` Xbox One Wireless Controller a… ✗
- **beam top5**: `<a_61><b_53><c_5>`Xbo, `<a_61><b_53><c_46>`Xbo, `<a_74><b_100><c_233>`?, `<a_61><b_53><c_0>`Xbo, `<a_61><b_181><c_195>`Xbo
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台一致(XboxOne)；beam中 share-a=5/10, share-(a,b)=0/10。
- **beam多样性**: **高**（6 个不同 a 大类）；unique(a,b)=8/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 0/4（覆盖0%）；新候选=0（**纯复述历史**）；genre: action,multiplayer,immersive。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。 注意 target 与历史共享词 ['black', 'controller']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #443 — 类目对·item错 · BEAM坍缩(<a_118×8/10)
- **历史**(8项; 平台 PSVita×6,PS4×1,?×1): Freedom Wars - PlayStation… | Silent Hill: Book of Memor… | Zero Time Dilemma Vita | Zero Escape: Virtue's Last… | The Amazing Spider-Man - P… | Batman: Arkham Origins Bla…
- **GT**: `<a_249><b_184><c_166>` PlayStation Vita Wi-Fi model Glacier White (PC… _(平台 PSVita)_ ｜ **native**: `<a_118><b_191><c_72>` Batman: Arkham Origins Blackga… ✗
- **beam top5**: `<a_118><b_191><c_72>`PSV, `<a_118><b_185><c_102>`PS4, `<a_118><b_41><c_55>`?, `<a_118><b_150><c_122>`PS4, `<a_118><b_1><c_2>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PSVita)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_118 家族 8/10）；unique(a,b)=8/10，平台数=6，unique标题=10/10。
- **reasoning质量**: 引用历史 6/8（覆盖75%），锚定: The Last of Us Remaste…, Bloodborne, Zero Time Dilemma Vita；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=子类延续(score3)。我们推的比用户真实点击**更贴历史**(荐3>target1) → **模型偏保守/用户更爱探索**。

### #444 — 类目错·(a)大类都不对 · BEAM坍缩(<a_162×10/10)
- **历史**(9项; 平台 ?×6,3DS×2,WiiU×1): Nintendo Selects: Super Ma… | Skque 28 in 1 Game Card Ca… | PowerA Universal Nintendo … | Nintendo Selects: Super Ma… | Yoshi amiibo (Super Smash … | Nintendo Falco Amiibo - Wi…
- **GT**: `<a_119><b_35><c_129>` PDP New Nintendo 3DS XL Clip Armor - Mario _(平台 3DS)_ ｜ **native**: `<a_162><b_218><c_126>` Pikmin & Olimar Amiibo (Super … ✗
- **beam top5**: `<a_162><b_52><c_132>`?, `<a_162><b_134><c_221>`?, `<a_162><b_242><c_145>`?, `<a_162><b_219><c_249>`?, `<a_162><b_218><c_126>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_162 家族 10/10）；unique(a,b)=9/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 6/9（覆盖67%），锚定: Mario Modern Color Ami…, amiibo Rosetta & Chiko…, Mario Classic Color Am…；新候选=0（**纯复述历史**）；模板开头；genre: action,adventure,nostalg。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。 注意 target 与历史共享词 ['mario']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #445 — 类目错·(a)大类都不对
- **历史**(6项; 平台 XboxOne×5,PS4×1): Call of Duty: Black Ops II… | Microsoft Xbox One Elite | Xbox One 1TB Console - Lim… | Xbox One 500GB Console - G… | Xbox One 1TB Console : Ris… | PlayStation 4 500GB Consol…
- **GT**: `<a_194><b_183><c_27>` Dark Souls III [Online Game Code] _(平台 ?)_ ｜ **native**: `<a_201><b_36><c_181>` PlayStation 4 500GB Console - … ✗
- **beam top5**: `<a_201><b_36><c_195>`PS4, `<a_7><b_36><c_0>`Xbo, `<a_201><b_2><c_102>`PS4, `<a_201><b_36><c_181>`PS4, `<a_201><b_2><c_195>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=8/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/6（覆盖67%），锚定: Call of Duty: Black Op…, Xbox One 1TB Console -…, Xbox One 500GB Console…；新候选=0（**纯复述历史**）；模板开头；genre: action,accessor。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。 注意 target 与历史共享词 ['iii']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #446 — 类目错·(a)大类都不对
- **历史**(1项; 平台 Wii×1): Mayflash W010 Wireless Sen…
- **GT**: `<a_194><b_21><c_1>` Final Fantasy X X-2 HD Remaster  Standard Edit… _(平台 PS3)_ ｜ **native**: `<a_157><b_198><c_79>` Mayflash W010 Wireless Sensor … ✗
- **beam top5**: `<a_157><b_81><c_22>`Wii, `<a_21><b_94><c_14>`PS4, `<a_61><b_170><c_90>`PC, `<a_157><b_198><c_79>`Wii, `<a_21><b_94><c_61>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS3 vs 荐=Wii)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=9/10，平台数=6，unique标题=10/10。
- **reasoning质量**: 引用历史 1/1（覆盖100%），锚定: Mayflash W010 Wireless…；新候选=0（**纯复述历史**）；genre: accessor。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #447 — 类目错·(a)大类都不对 · BEAM坍缩(<a_194×9/10)
- **历史**(2项; 平台 Wii×1,PS3×1): Mayflash W010 Wireless Sen… | Final Fantasy X X-2 HD Rem…
- **GT**: `<a_61><b_9><c_122>` Mayflash Wireless PS3 Controller To PC USB Ada… _(平台 PS3)_ ｜ **native**: `<a_194><b_21><c_76>` Final Fantasy X X-2 HD Remaste… ✗
- **beam top5**: `<a_194><b_21><c_76>`PS4, `<a_194><b_21><c_219>`PS4, `<a_194><b_121><c_62>`PS4, `<a_194><b_215><c_154>`?, `<a_194><b_21><c_254>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS3 vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_194 家族 9/10）；unique(a,b)=8/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: Mayflash W010 Wireless…, Final Fantasy X X-2 HD…；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,immersive。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=子类延续(score3)。我们推的比用户真实点击**更贴历史**(荐3>target1) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['mayflash', 'wireless']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #448 — 类目错·(a)大类都不对
- **历史**(3项; 平台 PS3×2,Wii×1): Mayflash W010 Wireless Sen… | Final Fantasy X X-2 HD Rem… | Mayflash Wireless PS3 Cont…
- **GT**: `<a_121><b_9><c_206>` Kingdom Hearts HD 2.5 ReMIX - PlayStation 3 _(平台 PS3)_ ｜ **native**: `<a_194><b_15><c_66>` Dishonored 2 - PlayStation 4 ✗
- **beam top5**: `<a_61><b_251><c_144>`PS4, `<a_194><b_87><c_249>`PS4, `<a_61><b_251><c_51>`PS4, `<a_131><b_210><c_0>`PS4, `<a_194><b_21><c_76>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS3 vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=8/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Mayflash W010 Wireless…, Final Fantasy X X-2 HD…, Mayflash Wireless PS3 …；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,immersive。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['hd']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #449 — 类目错·(a)大类都不对 · BEAM坍缩(<a_61×9/10)
- **历史**(4项; 平台 PS3×3,Wii×1): Mayflash W010 Wireless Sen… | Final Fantasy X X-2 HD Rem… | Mayflash Wireless PS3 Cont… | Kingdom Hearts HD 2.5 ReMI…
- **GT**: `<a_157><b_14><c_80>` Perfect Shot for Wii (Colors May Vary) _(平台 Wii)_ ｜ **native**: `<a_61><b_251><c_51>` DualShock 4 Wireless Controlle… ✗
- **beam top5**: `<a_61><b_44><c_172>`PS4, `<a_61><b_251><c_144>`PS4, `<a_61><b_131><c_197>`Xbo, `<a_61><b_75><c_143>`PS3, `<a_61><b_251><c_51>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=Wii vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_61 家族 9/10）；unique(a,b)=9/10，平台数=6，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Mayflash W010 Wireless…, Final Fantasy X X-2 HD…, Kingdom Hearts HD 2.5 …；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,immersive。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。

### #450 — 类目对·item错 · BEAM坍缩(<a_61×9/10)
- **历史**(5项; 平台 PS3×3,Wii×2): Mayflash W010 Wireless Sen… | Final Fantasy X X-2 HD Rem… | Mayflash Wireless PS3 Cont… | Kingdom Hearts HD 2.5 ReMI… | Perfect Shot for Wii (Colo…
- **GT**: `<a_30><b_40><c_121>` House of the Dead: Overkill - Nintendo Wii _(平台 Wii)_ ｜ **native**: `<a_157><b_14><c_80>` Perfect Shot for Wii (Colors M… ✗
- **beam top5**: `<a_157><b_14><c_80>`Wii, `<a_61><b_131><c_197>`Xbo, `<a_61><b_0><c_187>`?, `<a_61><b_44><c_172>`PS4, `<a_61><b_0><c_234>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(Wii)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_61 家族 9/10）；unique(a,b)=9/10，平台数=6，unique标题=10/10。
- **reasoning质量**: 引用历史 3/5（覆盖60%），锚定: Mayflash W010 Wireless…, Final Fantasy X X-2 HD…, Kingdom Hearts HD 2.5 …；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,immersive。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=子类延续(score3)。我们推的比用户真实点击**更贴历史**(荐3>target1) → **模型偏保守/用户更爱探索**。

### #451 — 类目对·item错
- **历史**(2项; 平台 XboxOne×2): Borderlands: The Handsome … | Xbox One Play and Charge K…
- **GT**: `<a_214><b_103><c_234>` Xbox One Wireless Controller (Without 3.5 mill… _(平台 XboxOne)_ ｜ **native**: `<a_61><b_53><c_5>` Xbox One Wireless Controller a… ✗
- **beam top5**: `<a_7><b_248><c_16>`Xbo, `<a_61><b_53><c_5>`Xbo, `<a_131><b_155><c_206>`Xbo, `<a_61><b_214><c_252>`Xbo, `<a_7><b_2><c_105>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=9/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: Borderlands: The Hands…, Xbox One Play and Char…；新候选=0（**纯复述历史**）；genre: action,immersive,accessor。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。

### #452 — 类目对·item错
- **历史**(2项; 平台 PS4×2): Star Wars: Battlefront - S… | NHL 17 - PlayStation 4
- **GT**: `<a_45><b_161><c_3>` NHL 16 - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_45><b_28><c_168>` FIFA 17 - PlayStation 4 ✗
- **beam top5**: `<a_45><b_28><c_168>`PS4, `<a_201><b_31><c_107>`PS4, `<a_39><b_51><c_188>`PS4, `<a_39><b_78><c_54>`PS4, `<a_45><b_193><c_4>`PS4
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台一致(PS4)；beam中 share-a=5/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=8/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: Star Wars: Battlefront…, NHL 17 - PlayStation 4；新候选=0（**纯复述历史**）；模板开头；genre: action,sports,strategy。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。 注意 target 与历史共享词 ['nhl']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #453 — 命中@1
- **历史**(4项; 平台 PS4×4): Grand Theft Auto V - PlayS… | Uncharted 4: A Thief's End… | Fallout 4 - PlayStation 4 | Metal Gear Solid V: The Ph…
- **GT**: `<a_123><b_72><c_7>` Far Cry 4 - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_123><b_72><c_7>` Far Cry 4 - PlayStation 4 ✓
- **beam top5**: `<a_123><b_72><c_7>`PS4, `<a_201><b_145><c_9>`PS4, `<a_118><b_233><c_76>`PS4, `<a_118><b_95><c_6>`PS4, `<a_201><b_213><c_242>`PS4
- **推荐↔GT差距**: top-1 完全命中。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=10/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Grand Theft Auto V - P…, Uncharted 4: A Thief's…, Fallout 4 - PlayStatio…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。target 是合理的大类延续，且**已命中**。

### #454 — 类目对·item错 · BEAM坍缩(<a_202×7/10)
- **历史**(4项; 平台 ?×2,XboxOne×1,PS3×1): Xbox One Stereo Headset Ad… | Logitech G910 Orion Spark … | Logitech G900 Chaos Spectr… | Matricom G-Pad XYBA Wirele…
- **GT**: `<a_61><b_131><c_197>` Microsoft Xbox Wireless Adapter for Windows 10 _(平台 Xbox)_ ｜ **native**: `<a_202><b_120><c_89>` Logitech G900 Chaos Spectrum P… ✗
- **beam top5**: `<a_202><b_58><c_105>`?, `<a_202><b_200><c_67>`?, `<a_61><b_167><c_197>`Xbo, `<a_202><b_11><c_246>`?, `<a_61><b_170><c_90>`PC
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；beam中 share-a=3/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_202 家族 7/10）；unique(a,b)=9/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Xbox One Stereo Headse…, Logitech G910 Orion Sp…, Logitech G900 Chaos Sp…；新候选=0（**纯复述历史**）；genre: action,immersive,peripheral。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=子类延续(score3)。我们推的比用户真实点击**更贴历史**(荐3>target2) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['adapter', 'wireless']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #455 — 类目对·item错
- **历史**(3项; 平台 PS4×2,PSVita×1): Persona 4: Dancing All Nig… | Plantronics GAMECOM 818 Wi… | Ratchet & Clank - PlayStat…
- **GT**: `<a_24><b_72><c_142>` Horizon Zero Dawn - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_121><b_35><c_0>` Megadimension Neptunia VII - P… ✗
- **beam top5**: `<a_131><b_209><c_151>`PS4, `<a_121><b_35><c_0>`PS4, `<a_121><b_76><c_208>`PS4, `<a_131><b_224><c_68>`PS4, `<a_121><b_146><c_26>`PS3
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=9/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Persona 4: Dancing All…, Plantronics GAMECOM 81…, Ratchet & Clank - Play…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。

### #456 — 类目错·(a)大类都不对
- **历史**(4项; 平台 PS4×3,PSVita×1): Persona 4: Dancing All Nig… | Plantronics GAMECOM 818 Wi… | Ratchet & Clank - PlayStat… | Horizon Zero Dawn - PlaySt…
- **GT**: `<a_61><b_166><c_249>` Thrustmaster T150 RS Racing Wheel for PlayStat… _(平台 PS3)_ ｜ **native**: `<a_121><b_155><c_99>` NieR: Automata - Playstation 4 ✗
- **beam top5**: `<a_24><b_86><c_14>`PS4, `<a_24><b_38><c_11>`PS4, `<a_24><b_96><c_27>`PS4, `<a_121><b_155><c_99>`PS4, `<a_1><b_43><c_207>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS3 vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=10/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Persona 4: Dancing All…, Ratchet & Clank - Play…, Plantronics GAMECOM 81…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #457 — 类目对·item错
- **历史**(4项; 平台 ?×3,GameCube×1): Metroid: Other M | Donkey Kong Classics | Soul Calibur II - Gamecube | Star Fox Assault
- **GT**: `<a_175><b_107><c_18>` Super Smash Bros Melee _(平台 ?)_ ｜ **native**: `<a_208><b_51><c_1>` Soul Calibur IV - Playstation … ✗
- **beam top5**: `<a_208><b_51><c_1>`PS3, `<a_208><b_51><c_0>`PS, `<a_208><b_242><c_41>`PS, `<a_175><b_30><c_198>`?, `<a_208><b_26><c_212>`?
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；beam中 share-a=3/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=7/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Metroid: Other M, Soul Calibur II - Game…, Donkey Kong Classics；新候选=0（**纯复述历史**）；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。

### #458 — 类目错·(a)大类都不对
- **历史**(4项; 平台 PS3×3,PS×1): Tekken 5 - PlayStation 2 | PlayStation 3 Dualshock 3 … | PlayStation 3 Dualshock 3 … | PlayStation 3 - 320 GB Sys…
- **GT**: `<a_194><b_25><c_86>` Final Fantasy X _(平台 ?)_ ｜ **native**: `<a_61><b_47><c_32>` PlayStation 3 Dualshock 3 Wire… ✗
- **beam top5**: `<a_61><b_47><c_8>`PS3, `<a_61><b_47><c_153>`PS3, `<a_61><b_47><c_32>`PS3, `<a_175><b_73><c_7>`PS3, `<a_61><b_47><c_10>`PS3
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=7/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: PlayStation 3 Dualshoc…, PlayStation 3 - 320 GB…, Tekken 5 - PlayStation…；新候选=0（**纯复述历史**）；genre: action,fighting,immersive。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=子类延续(score3)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #459 — 类目错·(a)大类都不对
- **历史**(5项; 平台 PS3×3,PS×1,?×1): Tekken 5 - PlayStation 2 | PlayStation 3 Dualshock 3 … | PlayStation 3 Dualshock 3 … | PlayStation 3 - 320 GB Sys… | Final Fantasy X
- **GT**: `<a_193><b_21><c_3>` Mega Man X8 - PlayStation 2 _(平台 PS2)_ ｜ **native**: `<a_194><b_255><c_47>` Final Fantasy X-2 ✗
- **beam top5**: `<a_194><b_255><c_47>`?, `<a_61><b_47><c_153>`PS3, `<a_194><b_24><c_128>`?, `<a_61><b_47><c_8>`PS3, `<a_194><b_140><c_160>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=6/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 3/4（覆盖75%），锚定: Final Fantasy X, PlayStation 3 Dualshoc…, PlayStation 3 - 320 GB…；新候选=0（**纯复述历史**）；genre: action,multiplayer,immersive。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #460 — 类目错·(a)大类都不对
- **历史**(4项; 平台 ?×3,Xbox360×1): Halo 3 - Xbox 360 | Call of Duty 4: Modern War… | Call of Duty 4: Modern War… | Fortune Street
- **GT**: `<a_240><b_33><c_93>` Grand Theft Auto IV _(平台 ?)_ ｜ **native**: `<a_140><b_161><c_25>` Call of Duty: World at War Pla… ✗
- **beam top5**: `<a_140><b_161><c_25>`Xbo, `<a_39><b_40><c_248>`Xbo, `<a_140><b_221><c_161>`?, `<a_140><b_242><c_55>`?, `<a_140><b_212><c_79>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（2 个 a 大类）；unique(a,b)=8/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 2/3（覆盖67%），锚定: Call of Duty 4: Modern…, Fortune Street；新候选=0（**纯复述历史**）；genre: action,shooter,strategy。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #461 — 命中@2 · BEAM坍缩(<a_140×9/10)
- **历史**(5项; 平台 ?×4,Xbox360×1): Halo 3 - Xbox 360 | Call of Duty 4: Modern War… | Call of Duty 4: Modern War… | Fortune Street | Grand Theft Auto IV
- **GT**: `<a_140><b_242><c_55>` Halo 3 _(平台 ?)_ ｜ **native**: `<a_140><b_161><c_25>` Call of Duty: World at War Pla… ✗
- **beam top5**: `<a_140><b_161><c_25>`Xbo, `<a_140><b_242><c_55>`?, `<a_140><b_221><c_161>`?, `<a_39><b_40><c_248>`Xbo, `<a_140><b_221><c_21>`?
- **推荐↔GT差距**: 正确项在 beam 第2位，pred[0] 前缀深度仅 1/3；beam中 share-a=9/10, share-(a,b)=1/10。
- **beam多样性**: **低**（坍缩到 <a_140 家族 9/10）；unique(a,b)=6/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 3/4（覆盖75%），锚定: Call of Duty 4: Modern…, Grand Theft Auto IV, Fortune Street；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。target 是合理的大类延续，且**已命中**。

### #462 — 类目错·(a)大类都不对 · BEAM坍缩(<a_208×7/10)
- **历史**(10项; 平台 PS4×5,PSVita×3,Xbox360×2): Tales of Hearts R (PSVita) | Tales of Vesperia - Xbox 3… | Tales of Vesperia - Xbox 3… | MegaTagmension Blanc + Nep… | Persona 5 - SteelBook Edit… | HORI Fighting Commander fo…
- **GT**: `<a_121><b_35><c_2>` Hyperdimension Neptunia Re;Birth3: V Generatio… _(平台 PSVita)_ ｜ **native**: `<a_61><b_99><c_203>` HORI Fighting Commander for Pl… ✗
- **beam top5**: `<a_61><b_99><c_203>`PS4, `<a_61><b_99><c_2>`PS4, `<a_61><b_99><c_240>`PS3, `<a_208><b_128><c_224>`PS4, `<a_208><b_177><c_1>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PSVita vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_208 家族 7/10）；unique(a,b)=4/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 4/9（覆盖44%），锚定: The Legend of Heroes: …, Tales of Vesperia - Xb…, Guilty Gear Xrd -Revel…；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,fighting。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=子类延续(score3)。我们推的比用户真实点击**更贴历史**(荐3>target2) → **模型偏保守/用户更爱探索**。

### #463 — 类目错·(a)大类都不对 · BEAM坍缩(<a_240×8/10)
- **历史**(5项; 平台 PS4×4,?×1): dreamGEAR- Playstation 4 C… | SmaAcc Cooling Fan with Du… | The Elder Scrolls V: Skyri… | DualShock 4 Wireless Contr… | Mafia II
- **GT**: `<a_119><b_217><c_221>` Grip-iT Analog Stick Covers, Set of 4 _(平台 ?)_ ｜ **native**: `<a_80><b_48><c_186>` Mafia II ✗
- **beam top5**: `<a_80><b_48><c_186>`?, `<a_240><b_33><c_93>`?, `<a_240><b_221><c_2>`PS3, `<a_240><b_37><c_115>`Xbo, `<a_240><b_40><c_2>`PS
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_240 家族 8/10）；unique(a,b)=8/10，平台数=7，unique标题=10/10。
- **reasoning质量**: 引用历史 4/5（覆盖80%），锚定: dreamGEAR- Playstation…, SmaAcc Cooling Fan wit…, The Elder Scrolls V: S…；新候选=0（**纯复述历史**）；模板开头；genre: action,immersive,narrative。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=子类延续(score3)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #464 — 类目错·(a)大类都不对
- **历史**(1项; 平台 Xbox360×1): Velvet Assassin - Xbox 360
- **GT**: `<a_201><b_151><c_255>` Playstation Plus: 3 Month Membership [Digital … _(平台 PS-generic)_ ｜ **native**: `<a_80><b_216><c_116>` Velvet Assassin - Xbox 360 ✗
- **beam top5**: `<a_80><b_216><c_116>`Xbo, `<a_80><b_216><c_22>`Xbo, `<a_80><b_216><c_55>`Xbo, `<a_80><b_176><c_55>`Xbo, `<a_205><b_208><c_52>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS-generic vs 荐=Xbox360)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=8/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 1/1（覆盖100%），锚定: Velvet Assassin - Xbox…；新候选=0（**纯复述历史**）；genre: action,racing,multiplayer。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=子类延续(score3)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #465 — 类目错·(a)大类都不对
- **历史**(2项; 平台 Xbox360×1,PS×1): Velvet Assassin - Xbox 360 | Playstation Plus: 3 Month …
- **GT**: `<a_118><b_71><c_33>` Assassin's Creed Rogue- Xbox 360 _(平台 Xbox360)_ ｜ **native**: `<a_201><b_151><c_255>` Playstation Plus: 3 Month Memb… ✗
- **beam top5**: `<a_201><b_36><c_181>`PS4, `<a_201><b_31><c_107>`PS4, `<a_201><b_2><c_102>`PS4, `<a_123><b_72><c_7>`PS4, `<a_39><b_182><c_247>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=Xbox360 vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=9/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: Velvet Assassin - Xbox…, Playstation Plus: 3 Mo…；新候选=0（**纯复述历史**）；模板开头；genre: action,racing,multiplayer。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #466 — 类目错·(a)大类都不对
- **历史**(3项; 平台 Xbox360×2,PS×1): Velvet Assassin - Xbox 360 | Playstation Plus: 3 Month … | Assassin's Creed Rogue- Xb…
- **GT**: `<a_140><b_156><c_111>` Alpha Protocol - Xbox 360 _(平台 Xbox360)_ ｜ **native**: `<a_118><b_95><c_10>` Assassin&rsquo;s Creed Syndica… ✗
- **beam top5**: `<a_118><b_95><c_6>`PS4, `<a_118><b_95><c_10>`Xbo, `<a_123><b_72><c_182>`Xbo, `<a_123><b_72><c_191>`Xbo, `<a_118><b_95><c_2>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=Xbox360 vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=6/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Velvet Assassin - Xbox…, Assassin's Creed Rogue…, Playstation Plus: 3 Mo…；新候选=0（**纯复述历史**）；genre: action,adventure,shooter。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #467 — 类目错·(a)大类都不对 · BEAM坍缩(<a_140×9/10)
- **历史**(4项; 平台 Xbox360×3,PS×1): Velvet Assassin - Xbox 360 | Playstation Plus: 3 Month … | Assassin's Creed Rogue- Xb… | Alpha Protocol - Xbox 360
- **GT**: `<a_80><b_95><c_147>` Dead Rising 3 _(平台 ?)_ ｜ **native**: `<a_140><b_212><c_49>` Borderlands - Xbox 360 ✗
- **beam top5**: `<a_140><b_212><c_49>`Xbo, `<a_140><b_212><c_230>`Xbo, `<a_140><b_4><c_214>`PS3, `<a_140><b_225><c_255>`Xbo, `<a_140><b_65><c_232>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_140 家族 9/10）；unique(a,b)=7/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Assassin's Creed Rogue…, Alpha Protocol - Xbox …, Playstation Plus: 3 Mo…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。

### #468 — 命中@4
- **历史**(1项; 平台 Xbox360×1): Grand Theft Auto V - Xbox …
- **GT**: `<a_39><b_182><c_247>` Call of Duty: Black Ops III - Standard Edition… _(平台 PS4)_ ｜ **native**: `<a_80><b_140><c_0>` Saints Row IV ✗
- **beam top5**: `<a_240><b_37><c_115>`Xbo, `<a_80><b_140><c_98>`Xbo, `<a_240><b_33><c_93>`?, `<a_39><b_182><c_247>`PS4, `<a_80><b_140><c_0>`?
- **推荐↔GT差距**: 正确项在 beam 第4位，pred[0] 前缀深度仅 0/3；平台错配(GT=PS4 vs 荐=XboxOne)；beam中 share-a=2/10, share-(a,b)=2/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=7/10，平台数=5，unique标题=10/10。
- **reasoning质量**: 引用历史 1/1（覆盖100%），锚定: Grand Theft Auto V - X…；新候选=0（**纯复述历史**）；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=漂移(平台/词面关联)(score1)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #469 — 命中@4
- **历史**(2项; 平台 Xbox360×1,PS4×1): Grand Theft Auto V - Xbox … | Call of Duty: Black Ops II…
- **GT**: `<a_201><b_145><c_9>` The Witcher 3: Wild Hunt - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_201><b_31><c_107>` Uncharted 4: A Thief's End - P… ✗
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_131><b_210><c_0>`PS4, `<a_39><b_69><c_69>`Xbo, `<a_201><b_145><c_9>`PS4, `<a_201><b_2><c_102>`PS4
- **推荐↔GT差距**: 正确项在 beam 第4位，pred[0] 前缀深度仅 1/3；平台一致(PS4)；beam中 share-a=5/10, share-(a,b)=1/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=10/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: Grand Theft Auto V - X…, Call of Duty: Black Op…；新候选=0（**纯复述历史**）；模板开头；genre: action,adventure,shooter。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。target 是合理的漂移(平台/词面关联)，且**已命中**。

### #470 — 命中@5
- **历史**(3项; 平台 PS4×2,Xbox360×1): Grand Theft Auto V - Xbox … | Call of Duty: Black Ops II… | The Witcher 3: Wild Hunt -…
- **GT**: `<a_118><b_95><c_6>` Assassin's Creed: Syndicate - Standard Edition… _(平台 PS4)_ ｜ **native**: `<a_131><b_210><c_0>` Fallout 4 - PlayStation 4 ✗
- **beam top5**: `<a_131><b_210><c_0>`PS4, `<a_201><b_31><c_107>`PS4, `<a_201><b_36><c_195>`PS4, `<a_201><b_213><c_242>`PS4, `<a_118><b_95><c_6>`PS4
- **推荐↔GT差距**: 正确项在 beam 第5位，pred[0] 前缀深度仅 0/3；平台一致(PS4)；beam中 share-a=2/10, share-(a,b)=1/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=10/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Grand Theft Auto V - X…, Call of Duty: Black Op…, The Witcher 3: Wild Hu…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。target 是合理的漂移(平台/词面关联)，且**已命中**。

### #471 — 类目对·item错
- **历史**(4项; 平台 PS4×3,Xbox360×1): Grand Theft Auto V - Xbox … | Call of Duty: Black Ops II… | The Witcher 3: Wild Hunt -… | Assassin's Creed: Syndicat…
- **GT**: `<a_74><b_218><c_206>` Ratchet & Clank - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_118><b_185><c_102>` Batman: Arkham Knight - PlaySt… ✗
- **beam top5**: `<a_131><b_210><c_0>`PS4, `<a_118><b_185><c_102>`PS4, `<a_201><b_31><c_107>`PS4, `<a_123><b_72><c_7>`PS4, `<a_118><b_150><c_122>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=10/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 3/4（覆盖75%），锚定: Grand Theft Auto V - X…, Assassin's Creed: Synd…, Call of Duty: Black Op…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。

### #472 — 类目对·item错
- **历史**(5项; 平台 PS4×4,Xbox360×1): Grand Theft Auto V - Xbox … | Call of Duty: Black Ops II… | The Witcher 3: Wild Hunt -… | Assassin's Creed: Syndicat… | Ratchet & Clank - PlayStat…
- **GT**: `<a_24><b_96><c_27>` Rise of the Tomb Raider: 20 Year Celebration -… _(平台 PS4)_ ｜ **native**: `<a_131><b_210><c_0>` Fallout 4 - PlayStation 4 ✗
- **beam top5**: `<a_131><b_210><c_0>`PS4, `<a_201><b_31><c_107>`PS4, `<a_118><b_185><c_102>`PS4, `<a_201><b_213><c_242>`PS4, `<a_123><b_129><c_247>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=10/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 4/5（覆盖80%），锚定: Grand Theft Auto V - X…, Assassin's Creed: Synd…, Call of Duty: Black Op…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。

### #473 — 类目错·(a)大类都不对
- **历史**(1项; 平台 3DS×1): 28-in 1 Blue Game Card Cas…
- **GT**: `<a_250><b_55><c_95>` Mario Kart 7 _(平台 ?)_ ｜ **native**: `<a_219><b_235><c_104>` Nintendo 3DS Game Card Case 24… ✗
- **beam top5**: `<a_219><b_235><c_104>`3DS, `<a_219><b_63><c_195>`3DS, `<a_113><b_104><c_28>`3DS, `<a_119><b_119><c_158>`3DS, `<a_113><b_235><c_2>`3DS
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=8/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 1/1（覆盖100%），锚定: 28-in 1 Blue Game Card…；新候选=0（**纯复述历史**）；genre: accessor。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #474 — 类目错·(a)大类都不对 · BEAM坍缩(<a_80×8/10)
- **历史**(7项; 平台 PC×2,XboxOne×2,?×2): Dishonored - PC | Metal Gear Solid V: Ground… | Mass Effect 3 [Online Game… | Thief Xbox one | Dead Rising 3 | Dead Island - Xbox 360
- **GT**: `<a_201><b_85><c_136>` Until Dawn - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_80><b_212><c_169>` Dead Island - Xbox 360 ✗
- **beam top5**: `<a_80><b_212><c_236>`Xbo, `<a_80><b_59><c_196>`Xbo, `<a_80><b_212><c_38>`?, `<a_123><b_171><c_136>`?, `<a_123><b_72><c_182>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS4 vs 荐=Xbox360)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_80 家族 8/10）；unique(a,b)=5/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 5/7（覆盖71%），锚定: Fallout 4 - PC, Metal Gear Solid V: Gr…, Mass Effect 3 [Online …；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=子类延续(score3)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #475 — 类目错·(a)大类都不对 · BEAM坍缩(<a_39×8/10)
- **历史**(1项; 平台 XboxOne×1): Battlefield 4 - Xbox One
- **GT**: `<a_245><b_141><c_101>` Lego Indiana Jones: The Original Adventures - … _(平台 PS3)_ ｜ **native**: `<a_39><b_95><c_159>` Titanfall - Xbox One ✗
- **beam top5**: `<a_39><b_114><c_237>`Xbo, `<a_39><b_69><c_69>`Xbo, `<a_39><b_198><c_73>`?, `<a_39><b_95><c_159>`Xbo, `<a_39><b_198><c_69>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS3 vs 荐=XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_39 家族 8/10）；unique(a,b)=7/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 1/1（覆盖100%），锚定: Battlefield 4 - Xbox O…；新候选=0（**纯复述历史**）；genre: action,strategy,multiplayer。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #476 — 类目错·(a)大类都不对 · BEAM坍缩(<a_245×9/10)
- **历史**(2项; 平台 XboxOne×1,PS3×1): Battlefield 4 - Xbox One | Lego Indiana Jones: The Or…
- **GT**: `<a_74><b_184><c_158>` Lego Indiana Jones 2: The Adventure Continues … _(平台 PS3)_ ｜ **native**: `<a_245><b_141><c_101>` Lego Indiana Jones: The Origin… ✗
- **beam top5**: `<a_245><b_141><c_7>`Wii, `<a_245><b_91><c_188>`Xbo, `<a_245><b_91><c_144>`PS3, `<a_245><b_141><c_249>`?, `<a_245><b_141><c_101>`PS3
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS3 vs 荐=Wii)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_245 家族 9/10）；unique(a,b)=4/10，平台数=6，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: Battlefield 4 - Xbox O…, Lego Indiana Jones: Th…；新候选=0（**纯复述历史**）；genre: action,adventure,shooter。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=子类延续(score3)。我们推的比用户真实点击**更贴历史**(荐3>target1) → **模型偏保守/用户更爱探索**。 注意 target 与历史共享词 ['indiana', 'jones', 'lego']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #477 — 类目错·(a)大类都不对
- **历史**(6项; 平台 PS4×4,XboxOne×2): UNCHARTED: The Nathan Drak… | Tomb Raider: Definitive Ed… | Metal Gear Solid V: The Ph… | Battlefield Hardline - Pla… | The Witcher 3: Wild Hunt -… | Middle Earth: Shadow of Mo…
- **GT**: `<a_39><b_151><c_9>` Halo 5: Guardians _(平台 ?)_ ｜ **native**: `<a_194><b_15><c_4>` Dishonored Definitive Edition … ✗
- **beam top5**: `<a_24><b_178><c_18>`Xbo, `<a_24><b_145><c_3>`Xbo, `<a_194><b_215><c_154>`?, `<a_201><b_145><c_9>`PS4, `<a_118><b_95><c_6>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=8/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 4/6（覆盖67%），锚定: UNCHARTED: The Nathan …, Metal Gear Solid V: Th…, The Witcher 3: Wild Hu…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #478 — 类目对·item错
- **历史**(7项; 平台 PS4×4,XboxOne×2,?×1): Tomb Raider: Definitive Ed… | Metal Gear Solid V: The Ph… | Battlefield Hardline - Pla… | The Witcher 3: Wild Hunt -… | Middle Earth: Shadow of Mo… | Halo 5: Guardians
- **GT**: `<a_118><b_98><c_14>` Tom Clancy's The Division - Xbox One _(平台 XboxOne)_ ｜ **native**: `<a_194><b_88><c_140>` The Witcher 3: Wild Hunt - Xbo… ✗
- **beam top5**: `<a_24><b_178><c_18>`Xbo, `<a_123><b_72><c_191>`Xbo, `<a_118><b_95><c_6>`PS4, `<a_123><b_72><c_7>`PS4, `<a_194><b_15><c_4>`Xbo
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台一致(XboxOne)；beam中 share-a=2/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=8/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 6/7（覆盖86%），锚定: UNCHARTED: The Nathan …, Tomb Raider: Definitiv…, Metal Gear Solid V: Th…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #479 — 类目错·(a)大类都不对 · BEAM坍缩(<a_131×8/10)
- **历史**(3项; 平台 PS4×1,?×1,XboxOne×1): Horizon Zero Dawn - PlaySt… | Battlefield 1 Exclusive Co… | Xbox One X 1TB Limited Edi…
- **GT**: `<a_8><b_70><c_241>` Xbox One Play and Charge Kit _(平台 XboxOne)_ ｜ **native**: `<a_131><b_224><c_68>` Overwatch - Origins Edition - … ✗
- **beam top5**: `<a_131><b_41><c_229>`PS4, `<a_39><b_51><c_21>`Xbo, `<a_131><b_224><c_68>`PS4, `<a_131><b_37><c_113>`Xbo, `<a_131><b_38><c_83>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=XboxOne vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_131 家族 8/10）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Horizon Zero Dawn - Pl…, Battlefield 1 Exclusiv…, Xbox One X 1TB Limited…；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,multiplayer。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #480 — 类目错·(a)大类都不对
- **历史**(3项; 平台 PS4×3): Star Wars: Battlefront - S… | NHL 17 - PlayStation 4 | NHL 16 - PlayStation 4
- **GT**: `<a_22><b_88><c_75>` The Sims 4 - PC/Mac _(平台 PC)_ ｜ **native**: `<a_45><b_28><c_168>` FIFA 17 - PlayStation 4 ✗
- **beam top5**: `<a_45><b_28><c_168>`PS4, `<a_201><b_31><c_107>`PS4, `<a_45><b_246><c_5>`PS4, `<a_39><b_77><c_105>`Xbo, `<a_39><b_51><c_188>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PC vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=8/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: NHL 17 - PlayStation 4, NHL 16 - PlayStation 4, Star Wars: Battlefront…；新候选=0（**纯复述历史**）；genre: action,shooter,sports。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #481 — 类目对·item错 · BEAM坍缩(<a_45×8/10)
- **历史**(4项; 平台 PS4×3,PC×1): Star Wars: Battlefront - S… | NHL 17 - PlayStation 4 | NHL 16 - PlayStation 4 | The Sims 4 - PC/Mac
- **GT**: `<a_13><b_1><c_233>` Plants vs. Zombies Garden Warfare 2 - PlayStat… _(平台 PS4)_ ｜ **native**: `<a_45><b_28><c_168>` FIFA 17 - PlayStation 4 ✗
- **beam top5**: `<a_45><b_246><c_5>`PS4, `<a_45><b_28><c_168>`PS4, `<a_45><b_246><c_6>`PS4, `<a_45><b_18><c_254>`PS4, `<a_39><b_78><c_54>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_45 家族 8/10）；unique(a,b)=6/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Star Wars: Battlefront…, NHL 17 - PlayStation 4, NHL 16 - PlayStation 4；新候选=0（**纯复述历史**）；模板开头；genre: action,sports,simulation。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #482 — 类目对·item错
- **历史**(5项; 平台 PS4×4,PC×1): Star Wars: Battlefront - S… | NHL 17 - PlayStation 4 | NHL 16 - PlayStation 4 | The Sims 4 - PC/Mac | Plants vs. Zombies Garden …
- **GT**: `<a_191><b_214><c_179>` Watch Dogs 2: Gold Edition (Includes Extra Con… _(平台 PS4)_ ｜ **native**: `<a_45><b_28><c_168>` FIFA 17 - PlayStation 4 ✗
- **beam top5**: `<a_45><b_28><c_168>`PS4, `<a_39><b_78><c_54>`PS4, `<a_39><b_51><c_188>`PS4, `<a_131><b_224><c_68>`PS4, `<a_45><b_246><c_5>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=7/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 5/5（覆盖100%），锚定: NHL 17 - PlayStation 4, NHL 16 - PlayStation 4, Star Wars: Battlefront…；新候选=0（**纯复述历史**）；模板开头；genre: action,shooter,sports。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #483 — 命中@2 · RERANK伤害
- **历史**(6项; 平台 PS4×5,PC×1): Star Wars: Battlefront - S… | NHL 17 - PlayStation 4 | NHL 16 - PlayStation 4 | The Sims 4 - PC/Mac | Plants vs. Zombies Garden … | Watch Dogs 2: Gold Edition…
- **GT**: `<a_45><b_28><c_168>` FIFA 17 - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_45><b_28><c_168>` FIFA 17 - PlayStation 4 ✓
- **beam top5**: `<a_201><b_31><c_107>`PS4, `<a_45><b_28><c_168>`PS4, `<a_45><b_246><c_5>`PS4, `<a_131><b_209><c_151>`PS4, `<a_131><b_224><c_68>`PS4
- **推荐↔GT差距**: 正确项在 beam 第2位，pred[0] 前缀深度仅 0/3；平台一致(PS4)；beam中 share-a=3/10, share-(a,b)=2/10。
- **beam多样性**: **高**（6 个不同 a 大类）；unique(a,b)=9/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 5/6（覆盖83%），锚定: Star Wars: Battlefront…, NHL 17 - PlayStation 4, The Sims 4 - PC/Mac；新候选=0（**纯复述历史**）；模板开头；genre: action,shooter,sports。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=漂移(平台/词面关联)(score1)。target 是合理的大类延续，且**已命中**。

### #484 — 命中@2
- **历史**(4项; 平台 XboxOne×2,PS4×2): The Witcher 3: Wild Hunt -… | Nyko Intercooler Stand - C… | Middle Earth: Shadow of Mo… | Mafia III - PlayStation 4
- **GT**: `<a_201><b_31><c_107>` Uncharted 4: A Thief's End - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_123><b_58><c_78>` Resident Evil 7: Biohazard - P… ✗
- **beam top5**: `<a_191><b_10><c_232>`PS4, `<a_201><b_31><c_107>`PS4, `<a_201><b_18><c_56>`PS4, `<a_123><b_76><c_232>`PS4, `<a_201><b_213><c_242>`PS4
- **推荐↔GT差距**: 正确项在 beam 第2位，pred[0] 前缀深度仅 0/3；平台一致(PS4)；beam中 share-a=4/10, share-(a,b)=1/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: The Witcher 3: Wild Hu…, Middle Earth: Shadow o…, Mafia III - PlayStatio…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。target 是合理的漂移(平台/词面关联)，且**已命中**。

### #485 — 类目错·(a)大类都不对 · BEAM坍缩(<a_111×9/10)
- **历史**(1项; 平台 Wii×1): Just Dance 2016 - Wii
- **GT**: `<a_7><b_215><c_114>` Turtle Beach - Ear Force Stealth 400 Fully Wir… _(平台 PS4)_ ｜ **native**: `<a_111><b_176><c_225>` Just Dance 2016 - Xbox 360 ✗
- **beam top5**: `<a_111><b_19><c_7>`Xbo, `<a_111><b_222><c_31>`Xbo, `<a_111><b_238><c_188>`PS4, `<a_111><b_176><c_225>`Xbo, `<a_175><b_171><c_29>`Wii
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS4 vs 荐=XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_111 家族 9/10）；unique(a,b)=8/10，平台数=5，unique标题=10/10。
- **reasoning质量**: 引用历史 0/1（覆盖0%）；新候选=0（**纯复述历史**）；genre: action,competitive。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #486 — 类目错·(a)大类都不对
- **历史**(2项; 平台 Wii×1,PS4×1): Just Dance 2016 - Wii | Turtle Beach - Ear Force S…
- **GT**: `<a_201><b_85><c_136>` Until Dawn - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_7><b_248><c_16>` Xbox One Limited Edition Halo … ✗
- **beam top5**: `<a_7><b_248><c_16>`Xbo, `<a_7><b_248><c_2>`Xbo, `<a_111><b_78><c_70>`Xbo, `<a_111><b_238><c_188>`PS4, `<a_61><b_217><c_168>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS4 vs 荐=XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=8/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: Just Dance 2016 - Wii, Turtle Beach - Ear For…；新候选=0（**纯复述历史**）；genre: action,immersive,accessor。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #487 — 类目对·item错
- **历史**(10项; 平台 ?×4,WiiU×2,PS3×1): PS3 Starhawk | Ratchet & Clank Collection | Sonic Adventure 2 Battle -… | Kirby: Planet Robobot - Ni… | Ratchet & Clank - PlayStat… | Spyro the Dragon
- **GT**: `<a_250><b_57><c_233>` Super Mario 3D World - Nintendo Wii U _(平台 WiiU)_ ｜ **native**: `<a_239><b_148><c_156>` Spyro 2: Ripto's Rage ✗
- **beam top5**: `<a_239><b_115><c_84>`PS, `<a_239><b_152><c_205>`?, `<a_239><b_152><c_35>`?, `<a_239><b_148><c_156>`?, `<a_239><b_92><c_111>`?
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台错配(GT=WiiU vs 荐=PS2)；beam中 share-a=2/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=8/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 6/10（覆盖60%），锚定: Super Paper Mario, Paper Mario: Color Spl…, PS3 Starhawk；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。 注意 target 与历史共享词 ['mario', 'super']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #488 — 类目错·(a)大类都不对 · BEAM坍缩(<a_141×7/10)
- **历史**(2项; 平台 Xbox360×1,?×1): Star Wars the Force Unleas… | Fallout 3: Game of the Yea…
- **GT**: `<a_140><b_3><c_78>` Lollipop Chainsaw - Xbox 360 _(平台 Xbox360)_ ｜ **native**: `<a_131><b_233><c_112>` Fallout: New Vegas - Ultimate … ✗
- **beam top5**: `<a_131><b_233><c_112>`?, `<a_141><b_221><c_44>`?, `<a_80><b_48><c_186>`?, `<a_141><b_225><c_35>`Xbo, `<a_141><b_212><c_21>`PC
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_141 家族 7/10）；unique(a,b)=10/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 2/2（覆盖100%），锚定: Star Wars the Force Un…, Fallout 3: Game of the…；新候选=0（**纯复述历史**）；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。

### #489 — 类目错·(a)大类都不对
- **历史**(1项; 平台 PS4×1): Mayflash F500 Arcade Fight…
- **GT**: `<a_157><b_232><c_136>` Sanwa GT-Y Octagonal Restrictor Plate for JLF … _(平台 ?)_ ｜ **native**: `<a_61><b_99><c_2>` Mayflash F500 Arcade Fight Sti… ✗
- **beam top5**: `<a_61><b_99><c_2>`PS4, `<a_208><b_51><c_1>`PS3, `<a_208><b_196><c_65>`PS, `<a_113><b_35><c_8>`Gam, `<a_113><b_35><c_14>`Gam
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=6/10，平台数=5，unique标题=10/10。
- **reasoning质量**: 引用历史 1/1（覆盖100%），锚定: Mayflash F500 Arcade F…；新候选=0（**纯复述历史**）；genre: action,fighting,nostalg。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=子类延续(score3)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #490 — 类目错·(a)大类都不对 · BEAM坍缩(<a_249×9/10)
- **历史**(2项; 平台 PSVita×2): PlayStation Vita Wi-Fi mod… | Smatree P100 Carrying Case…
- **GT**: `<a_13><b_218><c_173>` Agents of Mayhem - PlayStation 4 _(平台 PS4)_ ｜ **native**: `<a_249><b_31><c_126>` Sony PlayStation Vita WiFi ✗
- **beam top5**: `<a_231><b_142><c_63>`PSV, `<a_249><b_217><c_160>`PSV, `<a_249><b_181><c_229>`PSV, `<a_249><b_31><c_126>`PSV, `<a_249><b_63><c_20>`PSV
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS4 vs 荐=PSVita)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_249 家族 9/10）；unique(a,b)=7/10，平台数=1，unique标题=10/10。
- **reasoning质量**: 引用历史 0/2（覆盖0%）；新候选=0（**纯复述历史**）；genre: accessor。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=子类延续(score3)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #491 — 类目错·(a)大类都不对 · BEAM坍缩(<a_211×10/10)
- **历史**(4项; 平台 3DS×3,?×1): YO-KAI WATCH - 3DS | Etrian Mystery Dungeon - N… | Paper Mario: Sticker Star | YO-KAI WATCH 2: Fleshy Sou…
- **GT**: `<a_195><b_53><c_2>` Final Fantasy: The 4 Heroes of Light _(平台 ?)_ ｜ **native**: `<a_211><b_149><c_18>` YO-KAI WATCH - 3DS ✗
- **beam top5**: `<a_211><b_31><c_154>`3DS, `<a_211><b_105><c_215>`?, `<a_211><b_112><c_5>`3DS, `<a_211><b_159><c_123>`3DS, `<a_211><b_229><c_134>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_211 家族 10/10）；unique(a,b)=9/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 2/4（覆盖50%），锚定: YO-KAI WATCH - 3DS, Etrian Mystery Dungeon…；新候选=0（**纯复述历史**）；genre: adventure,rpg,puzzle。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #492 — 类目对·item错
- **历史**(4项; 平台 XboxOne×2,Xbox360×1,Switch×1): Rocksmith 2014 Edition - X… | Alien: Isolation - Xbox On… | Doom - Xbox One | Razer BlackWidow Chroma: C…
- **GT**: `<a_202><b_253><c_113>` CORSAIR Sabre - RGB Gaming Mouse - Lightweight… _(平台 ?)_ ｜ **native**: `<a_202><b_11><c_246>` Razer Naga Epic Chroma MMO Gam… ✗
- **beam top5**: `<a_202><b_11><c_246>`?, `<a_202><b_58><c_107>`?, `<a_202><b_11><c_104>`?, `<a_202><b_86><c_197>`DS, `<a_202><b_16><c_110>`?
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；beam中 share-a=6/10, share-(a,b)=0/10。
- **beam多样性**: **中**（2 个 a 大类）；unique(a,b)=8/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Alien: Isolation - Xbo…, Doom - Xbox One, Rocksmith 2014 Edition…；新候选=0（**纯复述历史**）；模板开头；genre: action,shooter,immersive。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。 注意 target 与历史共享词 ['gaming', 'rgb']，**语义相关却未命中**（暴露 SID大类未对齐/tokenization 局限）。

### #493 — 类目错·(a)大类都不对
- **历史**(3项; 平台 ?×1,WiiU×1,XboxOne×1): Diablo III: Reaper of Soul… | Mayflash GameCube Controll… | Rock Band 4 Band-in-a-Box …
- **GT**: `<a_214><b_190><c_72>` UtechSmart Venus 16400 DPI High Precision Lase… _(平台 ?)_ ｜ **native**: `<a_111><b_71><c_5>` Rock Band 4 Band-in-a-Box Bund… ✗
- **beam top5**: `<a_111><b_71><c_51>`Xbo, `<a_111><b_164><c_141>`Xbo, `<a_111><b_60><c_202>`PS4, `<a_111><b_164><c_222>`PS4, `<a_111><b_45><c_113>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=8/10，平台数=5，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Diablo III: Reaper of …, Mayflash GameCube Cont…, Rock Band 4 Band-in-a-…；新候选=0（**纯复述历史**）；模板开头；genre: action,rpg,immersive。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=子类延续(score3)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #494 — 类目错·(a)大类都不对
- **历史**(4项; 平台 ?×2,WiiU×1,XboxOne×1): Diablo III: Reaper of Soul… | Mayflash GameCube Controll… | Rock Band 4 Band-in-a-Box … | UtechSmart Venus 16400 DPI…
- **GT**: `<a_131><b_224><c_127>` Overwatch - Collector's Edition - PC _(平台 PC)_ ｜ **native**: `<a_202><b_11><c_2>` SteelSeries Siberia 200 Gaming… ✗
- **beam top5**: `<a_61><b_167><c_197>`Xbo, `<a_61><b_131><c_197>`Xbo, `<a_7><b_248><c_16>`Xbo, `<a_202><b_200><c_67>`?, `<a_111><b_164><c_222>`PS4
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PC vs 荐=XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=10/10，平台数=4，unique标题=10/10。
- **reasoning质量**: 引用历史 3/4（覆盖75%），锚定: Diablo III: Reaper of …, Rock Band 4 Band-in-a-…, UtechSmart Venus 16400…；新候选=0（**纯复述历史**）；模板开头；genre: action,adventure,rpg。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=漂移(平台/词面关联)(score1)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #495 — 类目对·item错 · BEAM坍缩(<a_205×9/10)
- **历史**(4项; 平台 PS4×4): Assassin's Creed Unity Lim… | Uncharted 4: A Thief's End… | Assassin's Creed: Syndicat… | Gran Turismo Sport - PlayS…
- **GT**: `<a_74><b_115><c_116>` Injustice 2 - PS4 [Digital Code] _(平台 PS4)_ ｜ **native**: `<a_205><b_0><c_108>` MotoGP 14 - PlayStation 4 ✗
- **beam top5**: `<a_205><b_8><c_170>`PS4, `<a_205><b_207><c_181>`PS4, `<a_118><b_185><c_102>`PS4, `<a_205><b_0><c_108>`PS4, `<a_205><b_0><c_112>`?
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_205 家族 9/10）；unique(a,b)=8/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/4（覆盖100%），锚定: Assassin's Creed Unity…, Assassin's Creed: Synd…, Uncharted 4: A Thief's…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #496 — 类目对·item错 · BEAM坍缩(<a_39×7/10)
- **历史**(5项; 平台 XboxOne×3,PS4×2): Metal Gear Solid V: The Ph… | UNCHARTED: The Nathan Drak… | Rise of the Tomb Raider - … | Doom - Xbox One | Titanfall 2 - Xbox One
- **GT**: `<a_13><b_218><c_16>` Agents of Mayhem - Xbox One _(平台 XboxOne)_ ｜ **native**: `<a_39><b_77><c_105>` Call of Duty: Infinite Warfare… ✗
- **beam top5**: `<a_39><b_77><c_105>`Xbo, `<a_39><b_77><c_69>`Xbo, `<a_39><b_51><c_188>`PS4, `<a_123><b_58><c_16>`Xbo, `<a_39><b_78><c_205>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台一致(XboxOne)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **低**（坍缩到 <a_39 家族 7/10）；unique(a,b)=6/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 5/5（覆盖100%），锚定: Metal Gear Solid V: Th…, UNCHARTED: The Nathan …, Rise of the Tomb Raide…；新候选=0（**纯复述历史**）；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=大类延续(score2)。我们推的比用户真实点击**更贴历史**(荐2>target1) → **模型偏保守/用户更爱探索**。

### #497 — 类目错·(a)大类都不对
- **历史**(6项; 平台 XboxOne×4,PS4×2): Metal Gear Solid V: The Ph… | UNCHARTED: The Nathan Drak… | Rise of the Tomb Raider - … | Doom - Xbox One | Titanfall 2 - Xbox One | Agents of Mayhem - Xbox On…
- **GT**: `<a_140><b_176><c_51>` Battlefield: Bad Company _(平台 ?)_ ｜ **native**: `<a_123><b_228><c_139>` Dead Rising 4 - Xbox One ✗
- **beam top5**: `<a_13><b_93><c_77>`Xbo, `<a_13><b_224><c_3>`Xbo, `<a_39><b_77><c_105>`Xbo, `<a_123><b_58><c_16>`Xbo, `<a_13><b_224><c_7>`Xbo
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（3 个 a 大类）；unique(a,b)=7/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 4/6（覆盖67%），锚定: Metal Gear Solid V: Th…, Rise of the Tomb Raide…, Doom - Xbox One；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=大类延续(score2); 我们pred[0]=大类延续(score2)。关联档位相同(score2)但选错具体 item。

### #498 — 类目错·(a)大类都不对
- **历史**(3项; 平台 PS4×2,PSP×1): Horizon Zero Dawn - PlaySt… | XFUNY(TM) Dustproof Quakep… | NieR: Automata - Playstati…
- **GT**: `<a_205><b_138><c_74>` Twisted Metal - PS3 [Digital Code] _(平台 PS3)_ ｜ **native**: `<a_121><b_155><c_99>` NieR: Automata - Playstation 4 ✗
- **beam top5**: `<a_121><b_76><c_208>`PS4, `<a_1><b_173><c_4>`PS4, `<a_1><b_116><c_233>`PS4, `<a_121><b_91><c_244>`PS4, `<a_1><b_150><c_189>`PS3
- **推荐↔GT差距**: beam 与 GT 连大类 a 都不一致，类目判断失败；平台错配(GT=PS3 vs 荐=PS4)；beam中 share-a=0/10, share-(a,b)=0/10。
- **beam多样性**: **中**（4 个 a 大类）；unique(a,b)=9/10，平台数=3，unique标题=10/10。
- **reasoning质量**: 引用历史 3/3（覆盖100%），锚定: Horizon Zero Dawn - Pl…, NieR: Automata - Plays…, XFUNY(TM) Dustproof Qu…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=探索(无关联)(score0); 我们pred[0]=大类延续(score2)。用户**探索**：target 与历史无任何 SID大类/平台/词面关联 → 基于历史几乎不可能命中（**天花板损失**）。

### #499 — 类目对·item错
- **历史**(4项; 平台 PS4×2,PSP×1,PS3×1): Horizon Zero Dawn - PlaySt… | XFUNY(TM) Dustproof Quakep… | NieR: Automata - Playstati… | Twisted Metal - PS3 [Digit…
- **GT**: `<a_123><b_160><c_188>` Dead Island Definitive Collection - PlayStatio… _(平台 PS4)_ ｜ **native**: `<a_121><b_76><c_208>` Star Ocean: Integrity and Fait… ✗
- **beam top5**: `<a_1><b_116><c_233>`PS4, `<a_121><b_76><c_208>`PS4, `<a_1><b_173><c_4>`PS4, `<a_1><b_150><c_189>`PS3, `<a_121><b_35><c_0>`PS4
- **推荐↔GT差距**: beam 仅大类 a 与 GT 一致，b/c 全偏；平台一致(PS4)；beam中 share-a=1/10, share-(a,b)=0/10。
- **beam多样性**: **高**（5 个不同 a 大类）；unique(a,b)=10/10，平台数=2，unique标题=10/10。
- **reasoning质量**: 引用历史 3/4（覆盖75%），锚定: Horizon Zero Dawn - Pl…, NieR: Automata - Plays…, Twisted Metal - PS3 [D…；新候选=0（**纯复述历史**）；模板开头；genre: action-adventure,action,adventure。
- **target合理性(天花板)**: target=漂移(平台/词面关联)(score1); 我们pred[0]=漂移(平台/词面关联)(score1)。关联档位相同(score1)但选错具体 item。

---

## 附录A: 代表性案例人工精读

**#0 探索失败** — 历史 LEGO/Minecraft(PS3家庭向)；GT=Just Dance 2017(体感舞蹈)。history 里 "PlayStation Eye(体感摄像头)" 强烈暗示体感/舞蹈，但推理误读为泛"interactive gaming"，beam 全塌成 LEGO(`<a_245>`)。target 本身是"同平台换品类"的合理漂移，但推理未捕捉关键线索。

**#1 tokenization 局限** — 历史含 **Dark Souls III**；GT=**Demon's Souls**(同厂魂系)。relatedness 靠共享词 "souls" 判为大类延续，但 SID 的 a 大类没把两者放一起(GT a=194 不在历史 a 集)，模型被 Titanfall/Madden 带偏到 shooter(`<a_39>`)。→ **语义相关但 SID 未对齐**，暴露 tokenization 天花板。

**#3 RERANK 伤害** — 全 PS4 动作冒险；GT=Uncharted4。native 直接命中，但约束 beam 把手柄排到 #1、正确答案挤到 #2 → HR@1 丢失。

**#130 易例命中** — 复古主机配件，GT=Gamecube 手柄(已在历史)。复购/同族，类目复述即命中。

> 命中集中在**复购/同系列/同平台配件**(子类延续 HR 47%)；失败集中在**探索**与**需要 specific-title/genre pivot** 的场景。

## 附录B: follow-up 启示

1. **天花板受用户探索性限制**: ~30% target 是探索、44% 漂移，纯历史序列模型上限低 → 需引入历史外信号(内容语义/协同过滤/时序/上下文)攻探索类。
2. **模型过度保守**: 我们 pred[0] 平均比用户真实点击更贴历史(38% 条更保守) → 用户实际更爱探索；可在 RL reward 里加入"探索/新颖性"激励，纠正 exploitation 偏置。
3. **reasoning≈风格化前缀**: 99.9% 提及 SID 是历史复述、0.01 新候选/条 → 让推理真正 ground 候选 item。
4. **约束 beam 净负**: native HR@1 > beam HR@1，净损失5条 → 去掉/改造约束 beam。
5. **tokenization 对齐**: #1 类同厂同系列(Dark Souls→Demon's Souls)语义相关却 SID 大类不对 → 改进 SID 量化使语义近邻共享前缀，直接抬高延续类命中上限。
6. **冗余可压缩**: 70% 模板开头、长度恒定 → 推理长度/信息密度惩罚。
