# 00 · 执行偏差与已知问题登记（Week 5 · 密度/跨度 benchmark）

**日期**：2026-09-08　**范围**：`plan/week5/report.md` 的 B0–B4 建立实验
**纪律**：预注册判据与冻结契约（锚点、门控、切分、标签、主指标、等价界）本轮**未修改**；
所有冲突只进本登记，不改写产物正文。分类：`契约` / `实现缺陷` / `口径偏差` / `能力边界`。

---

## 1. 实现缺陷（全部由机器校验抓出，非人眼发现）

| 号 | 事实 | 抓出方式 | 处置与代价 |
|---|---|---|---|
| **W5-1** | `ds_stats.load_channel` 直接沿用事件表分组偏移，未把行按请求队列顺序重新 gather。`cohort_manifest` 的 CSN **不是升序**（实测 `sorted=False`），因此首次构建的全部视图特征把观测行错配到别的就诊上 | 400 就诊子样本跑 B0 验收 2 时越界报错；更早的信号是 `win30` 与 `win60` 的可行例数**完全相同**（不可能） | 改为显式重排 gather 并断言 `len(idx) == ends[-1]`；**删除全部视图产物与已完成的 B1 run，重建重跑**。教训：任何"按 CSN 对齐"都必须走 `align_pos` 一类的显式映射，禁止裸 `searchsorted` |
| **W5-2** | LSTM 适配器把 `(B, C, L)` 先 `permute(0,2,1)` 成 `(B,L,C)` 再 `reshape(B*C, L, 1)`，该 reshape 不是通道独立展开，而是把**不同样本、不同通道的时间步互相穿插** —— 一条序列会读到别的患者的观测；实测给纯 padding 加 5 列，整批分数最大变化 **1.7e-2** | B0 验收 5（改 padding 长度必须逐位不变）**FAIL** | 改为通道主序 `(C,B,L)` 展开 + 对称折回；新增验收 **T5b 跨样本隔离**（把所有被 mask 的位置填成 ±500 量级垃圾，整批分数必须完全不变）。修复后 T5/T5b 全部 maxdiff = 0 |
| **W5-3** | `fit_lstm` 在返回前 `load_state_dict(best_state)`，因此"末态指纹"恒等于最佳快照指纹 —— 原 T04 快照验收成为**永真式** | 验收 6 判 False 后追查 | `final_state_sha` 改取**回载之前**的权重指纹，并新增 `final_state_sha_after_restore` 必须等于 best 快照；两条一起判 |
| **W5-4** | 分析层 `analyse()` 从长表取 `y` 时未按 CSN 去重 → 向量长度 = 就诊数 × seed 数，与预测矩阵不符而崩 | 首次 B2 分析 | `drop_duplicates("CSN")`。属"把同一患者的 5 份预测当 5 个独立样本"同类错误的一个变体，正是 §9 明令禁止的口径 |
| **W5-5** | `fit_lgbm` 末次拟合对 `n_estimators` 重复传参；`verdict_directional` 嵌套三元式语法错误 | 编译/冒烟 | 修正；无科学影响 |

**登记结论**：本轮 5 个实现缺陷中，W5-1 与 W5-2 会**静默产出错误数字**（不报错、不崩溃），
且都不是人眼看代码看出来的。它们分别被"子样本不变性测试"和"padding 不变性测试"抓到。
故这两类测试应作为 benchmark 的**发布前置条件**（与 Wave 6 P0-2 同一结论，本轮再次验证）。

---

## 2. 口径偏差（与上游计划文本不同，已按实测登记，不回填改写计划）

| 号 | 计划文本 | 实测/本轮做法 | 影响 |
|---|---|---|---|
| **W5-6** | `report.md` §4.2：MIRA 输出 768/1024 冲突未决 | Wave 6 已核：`models_cache/MIRA_pretrained/config.json` 的 `hidden_size = 768`，维数从 config 读取而非硬编码 | B4 用 768 维；该未决项在本轮**闭环** |
| **W5-7** | §7 第一批 LightGBM：与 Wave 6 M2 同一 HPO 协议（每细胞 50 次随机搜索） | 本轮改为**每 (任务 × 臂) 用 seed 0 搜索一次并冻结**，随后 5 seed 各自重拟合（seed 仍进入 LightGBM 三随机源） | 90 细胞的搜索成本降到 18 次；seed 间差异仍是训练随机性，但**不含 HPO 抽样差异**。已写入每个 run 的 `hpo.note` |
| **W5-8** | §4.2 C2-density 子集字面 = 监护跨度 + 各通道点数 | 主线 A5 用扩展定义（另加各通道 `S_c`、`R_c`、`N_c/120`、`(N_c−1)/S_c`、通道存在），并同时报 A6 = 字面窄定义 | §4.3 明列这些是本指南的**候选报告定义**，故两版并列，不宣称替换既有 C2 实现 |
| **W5-9** | §5 双份记录行为 native / retained 分名保存 | 视图层每列都带 `native_*` 与 `retained_*` 两份；密集视图下两者逐位相同 | 满足要求；B2/B3 表内额外给出"保留跨度中位 vs native 跨度中位"审计 |
| **W5-10** | §6.2 档位 `K={2,3,4,6,24}` + 仅最早点 + 仅最近点 | 全部实现；单点臂的 `S_c` 恒为 0，按规则**不进入**固定跨度主效应 | 与 §6.2 规则一致 |
| **W5-11** | §6.3 跨度机制臂候选档位 30/60/90 min、匹配容差待定 | 冻结为容差 **5 min**、K=6（另跑 2×2 = K∈{2,6} × S∈{30,90}）；匹配不到真实点即判"不支持"，不硬凑 | 实际跨度偏离名义值，已逐视图在审计表给出 |
| **W5-12** | §11 40 GPU·h 上限 | 见 `05_ledger/`（生成时按 run 记录与 GPU 账本汇总） | 未触发停止条件则继续；超限即停并上报 |

---

## 3. 能力边界（判定能力的物理下限，不是"无效应"）

| 号 | 事实 | 后果 |
|---|---|---|
| **W5-13** | C1 四通道共同可行率上限 ≈ **38%**（主队列 78,418 中约 30,136 次就诊在 2h 窗内四条 Monitor 通道都≥1 点）；K=24 降到 ≈ 32% | B2/B3 的结论域是"四类监护通道都有 K 个真实点"的子人群；已在 §1.3 表与每张卡片的覆盖率中报告，未静默放宽资格 |
| **W5-14** | `decomp_D120` 在共同可行交集内的 val 阳性例数很小 | 该任务上 ±0.005 判定的可检出性受限；区间宽度与"不判定"并列报告，不得读作"无差异" |
| **W5-15** | §6.2 提出"四通道共同可行率很低时可另立 HR 单通道机制子实验" | **本轮未擅自开跑**：它需要新增一档队列定义，属研究者裁决项（是否立项、以及命名与是否替换主线）。当前所有机制结论都在四通道交集上 |
| **W5-16** | §7 第二批 PhysioStack / DeepJoint、以及 SignalMC-MED 波形支线 | 未进入本轮：PhysioStack 需先解决每 batch PCA 与 token 边界兼容性并有权重核验；DeepJoint 需重定义任务头；波形需独立队列与新的锚点门控。三者都需要单独的准入验收，不在本轮"首批可审计预测"范围内 |

---

## 4. 与上一轮结果树的接缝

`result/Week5/` 原有产物（Wave 6 的 E6.0–E6.7）经研究者 2026-09-08 指示判定为
**Week 4 的延伸**，已整体移至 `result/Week4/10_wave6/`，移动过程只改名不改内容，
映射与后果见 `result/Week4/10_wave6/MERGE_NOTE_并入登记.md`。
本轮 `result/Week5/` 的含义改为 **B0–B4 密度/跨度 benchmark 产物**。

代码侧注意：`wave6/src/common6.py` 的 `WAVE6_OUT` 默认值仍指向 `result/Week5`；
本轮 `ds_common.py` 已在导入前把它显式改指 `result/Week4/10_wave6`，
避免复用 Wave 6 模块时把新产物写进 Week5。

---

## 5. 追加登记（2026-09-08 15:00–16:00，分析与出图阶段）

| 号 | 事实 | 抓出方式 | 处置 |
|---|---|---|---|
| **W5-17** | `ds_analyze.analyse()` 在 Holm 赋值处按「声明族」遍历，而某些臂只在部分组里存在（B3 的 `dense` 在 shift 轨按设计不跑）→ `KeyError: R5_dense_vs_win60` 直接中止 B3 分析 | 运行期崩溃（不是静默错误） | 改为只对**该组实际存在**的对比做 Holm，并把被跳过的对比与缺失臂写进 `analysis.json.skipped_contrasts`（跳过必须可见，不得静默） |
| **W5-18** | B2 的 matched 与 shift 被 `analyse()` 按 `(task, model, track)` 分到不同组 → 两轨**永不进入同一配对 bootstrap**，matched − shift 的「重训能否缓解」对比无法计算 | 代码审查 + 结果键检查 | 两轨先并入同一 `track="paired"` 组再求差中之差；`analysis.json.shift_vs_matched` 为修复后产物 |
| **W5-19** | `gen_figs` 里把 `fp("中文标签")` 返回的对象再传给 `fp()` → `FontProperties.set_size(Text)` 崩溃；且逐标签 `Text` 包装**没有触发 CJK 逐字形回退**，图里中文渲染成方框（F1b 起崩溃；F2/F3/F4 曾带 glyph missing 警告） | 运行期崩溃 + matplotlib `UserWarning: Glyph ... missing` | 改为注册 Droid 字体后设 `rcParams["font.family"] = ["DejaVu Sans","Droid Sans Fallback"]` 全局回退，标签直接传字符串；重跑后**零 missing-glyph 警告**，F0/F1/F1b/F2/F3/F4 全部产出并嵌进 PDF（30 页、12 个图像对象） |
| **W5-20** | B1 的分析曾在 run 只完成 141/180 时跑出过一版 `b1_analysis.json`（时间戳早于 run 齐备时刻） | 产物时间戳比对 | 未采用该版：等 180/180 齐备后整卡重算，报告用的是重算版（`verify` 对 180 个细胞逐位复算通过）。教训：**分析产物必须记录其所依赖的 run 数**，否则「旧稿」与「新稿」在文件系统上无法区分 |
| **W5-21** | 若干次 `pkill -f <pattern>` 误杀了自己的启动 shell（命令行本身含该 pattern），导致一批编排任务静默未启动 | 预期产物未出现，追查发现 | 改用 `pgrep -f 'xxx[x]'` 括号技巧 + 按 PID kill；并在每步之后核对产物是否存在，不假设后台任务已启动 |

## 6. 与判定无关但影响解读的两处口径事实

- **B1 的置换/噪声对照确实为负**：`A8_C0_NUM_PERM` 与 `A4_C0_NUM` 的 val AUPRC 差在 0.0002 量级，
  `A9` 等维噪声同理 ⇒ `P4 = A5 − A8 = +0.0107` 的增益不是「多了 21 列」带来的，
  而是模型确实用到了记录行为与结局的关联。按 §6.1 的边界，这仍**不构成**因果解释。
- **`P7` 与 `P3` 的差**：§4.2 字面窄定义（HR 跨度 + 各通道点数）在 dispo 上只给 +0.0033（界内），
  而含 `R_c`/密度/频率的扩展定义给 +0.0105（成立）⇒ 本轮增益主要来自
  **最新性与按跨度归一的频率**，不是「点数」本身。该区分是结果观察，不改动任何臂定义。
| **W5-22** | 队列漏斗里 `Dispo_time ≤ t_w` 的排除比例写成 0.00%：分子 `excl_decided_early` 取自 **in_main** 之后的人群，而 in_main 本身已经排除这些行 ⇒ 恒为 0 | 与 Wave 6 E6.0 实测的 15.02% 对不上，追查分母定义 | 改在**步骤 3 的分母**（in_denominator）上计算，并同时给出分子分母原始计数。修正后 train∪val 的该比例为 **15.05%**，与 Wave 6 的 15.02%（全 chrono 队列）同量级；停止阈值 25% 未触发 |
| **W5-23** | 标签定义哈希用 `to_numpy().tobytes()` 计算，object dtype 下哈希的是**指针**而非内容 ⇒ 同一份标签两次运行得到不同哈希（`af28df25…` vs `72c0792a…`），哈希失去溯源意义 | 修正 W5-22 后重跑发现哈希又变了 | 改为对排序后的规范 CSV 字节取 SHA-256；连续两次运行验证：哈希同为 `7d3d60b7bfd81232`，且 `labels.parquet` / `cohort_manifest.parquet` 字节级一致 ⇒ 队列与标签层可复现 |

## 7. 第二轮追加登记（2026-09-09，对账 + B5 + B6）

| 号 | 事实 | 抓出方式 | 处置 |
|---|---|---|---|
| **W5-24** | 首轮报告的实际时间覆盖审计表，最后一列把 **native 最新性误印成 native 跨度**（同一表达式写了两遍），造成 dense 行"retained R=0 而 native R=103=跨度"的自相矛盾观感 | 研究者对账质疑 → 回查 `view_manifest` | 数据层无误：dense 的四通道 `N_c/S_c/R_c` 的 native 与 retained **逐位相同**；仅修 `ds_report.py` 渲染并补 `median_native_recency_HR`。详见 `05_recon/reconciliation.json` |
| **W5-25** | 首轮所有对比只报「配对 bootstrap 均值差」，与均值表里的 seed 均值差（例：B4 decomp agg15 `0.1258−0.0974=0.0284` vs 表中 `0.0305`）看起来"对不上" | 研究者对账质疑 | 两者是**不同估计量**（AP 非线性 + 重采样丢弃单类重采样），不是数据不一致。已给全部 102 个对比补 `delta_point`，报告表格两列并列，并写明 CI/Holm 只属于 bootstrap 口径 |
| **W5-26** | 首轮判定文字把「TOST 等价」「单侧效应在界内」「校正后不显著」压成同一句"效应小于判据界" | 研究者对账质疑 | 判定函数重写为互斥 5 类（`verdict_v2`），全部既有对比按新口径重贴标签（不改任何 CI、p 或判据数值），新口径写进各卡 `analysis.json.verdict_taxonomy` |
| **W5-27** | 首轮把 dispo 上"k 族高于 dense/win 族约 +0.045"部分归因于长序列可优化性 —— **两卡队列本就不同**，该归因不成立 | 同队列重算（05_recon） | 同一批 val CSN 上重算：dispo 跨族差 **−0.0014**、decomp **+0.0191** ⇒ 差值主要是队列构成效应。§9 的解读已相应收紧，另做读出方式敏感性作为独立检验（不用于解释首轮差值） |
| **W5-28** | B5 首版把通道存在列写成 `chan_avail_*`（实际列名是 `avail_*`），且 LOO/单组的取值方式写错 → 直接 KeyError，未产出任何错误结果 | 启动即崩溃 + 臂构造自检（逐臂列数、常数列、锚与单组臂列数不得相同） | 修正后新增断言式自检：若某臂列集合与锚相同或组内全为常数 ⇒ 判为构造性空对比并上报。本轮 10 个臂列数 584/588/588/593/592/609/605/605/600/601，互不相同且无常数列 |
| **W5-29** | 第二轮分析若沿用逐次调用 sklearn AP，B5 的 10 臂 × 5 seed × 10,000 次重采样在 dispo（9,832 val）上约 21 分钟/组 × 8 组，不可接受 | 成本估算 | 实现 `ds_fastboot`：每个 (臂, seed) 只排序一次，重采样阶段做 O(n) 计数运算。**与 sklearn 逐位等价性实测**：visit 级最大偏差 2.8e-17、MRN 聚类级 2.8e-17（首版聚类分支曾因把计数按排序顺序索引而偏差 0.048，已被该等价性检查抓到并修正）。协议未变：仍 10,000 次、各臂共用索引、逐 seed 求 AP 后平均 |
| **W5-30** | B6 的读出敏感性三视图各自使用**不同的可行队列**（dense/k6/k24 的共同可行交集不同），直接跨臂配对会拿 3,559 例与 3,022 例比较 → 分析层报错 | 分析层长度断言报错（未产出错误数字） | 在 `ds_analyze2.analyse()` 加入**共同支持域强制交集**，并把 `n_val / n_val_before_intersect` 写进每个组；先交集再配对，绝不静默混用不同队列 |


## 8. 第三轮追加登记（2026-09-10，协议核查 §2 + B7 + B8）

| 号 | 事实 | 抓出方式 | 处置 |
|---|---|---|---|
| **W5-31** | 判定层缺陷：`verdict_v2` 只要「对 0 校正后显著且方向为正」就写「增益成立（…单侧界越过阈值）」，**从未检验 CI95 下界**，而 B5 预注册写明 S1–S4 需 Holm p<0.05 **且** CI95 下界 > +0.005（例：`S3_g3` dispo·LR +0.0040 [0.0021, 0.0059] 被标「增益成立」） | 研究者按计划文档 §2.1 质疑 → 回读预注册与判定函数逐条比对 | 新增 `verdict_round3.verdict_v3`：三条栏分列（对 0 的 Holm p / 实质阈值 CI95 下界 > +0.005 / TOST 两个单侧 p），按各对比**原预注册规则**重映射；结果写 `06_b5/analysis_v2.json`、`07_b6/analysis_v2.json`，前后对照见 `08_protocol_audit/verdicts_before_after.csv`。旧 `analysis.json` 原样保留 |
| **W5-32** | B6 的 `shift` 轨在 PREREG 与报告正文写成「只用 C0+数值摘要训练，再在带记录行为列的抽稀 val 上打分」——字面上模型不可能凭空获得已学到的 R 系数 | 计划文档 §2.2 → 逐 run 读 `run_record.json` 并重跑复现校验 | **实现是对的、文字是错的**：`b6_robust.main_tabular` 逐臂在 dense 视图上训练（该臂自己的列集合与预处理器），在受损 val 上打分；dense 条件复现最大绝对差 3e-8（float32 舍入级）。仅更正说明，证据落 `08_protocol_audit/shift_track_audit.json` |
| **W5-33** | `T_rec_minus_full` 的系数实为 `full − rec`，名称与方向相反（dense 表写 +0.0032 但含义是完整块减 R） | 计划文档 §2.2 → 核对 `analyze_b6.py` 系数 | v2 分析更名为 `T_full_minus_rec` 并重算；旧名与旧值保留在 `07_b6/analysis.json` |
| **W5-34** | B6 的抽稀掩码 rng 种子用 `abs(hash(条件名))`，而 CPython 字符串哈希按进程随机化 ⇒ **受损条件跨进程不可再导出**（复现校验：`dense` 差 3e-8，`rand50` 差 0.37~0.48） | W5-32 的复现校验顺带抓到 | 记为已知缺陷：B6 的 matched/shift 在同一进程内共用同一掩码，内部比较仍可比，但**不构成可复现的稳健性证据**；B8 起改用 `zlib.crc32(条件名)` 派生种子，并在每个 `run_record.json` 落盘 `sim_seed` |
| **W5-35** | B5 组定义含确定性重复：`density_120_c ≡ n_points_c/120`（4 对线性）、`monitoring_span_min ≡ span_min_HR`（1 对完全等值）、`freq_per_min_c ≡ (n−1)/span`（函数式）；且实际完整块 **25 列**，预注册写「G5 = 21 列」（21 是首轮 P3 字面子集） | 计划文档 §2.3 → 用真实 dense 特征矩阵逐对核验 | 导出 `08_protocol_audit/{duplicates.csv,group_column_inventory.json,feature_columns.csv}`；**LOO 结论受限**：移除 G3 保留 G4 时点数仍被模型看见，故 `S8_loo_G3` 的零增量不能写成「点数不重要」。B7 基线改用去重后的 N/S |
| **W5-36** | 缺失哨兵未定义清楚：`fit_scaler/apply_scaler` 用 `nan_to_num` ⇒ 不可见通道的 `R_c` 在缩放后恒为 0，等价于「该通道可见人群的平均最新性」，与 `avail_c==0` 完全共线 | W5-35 的哨兵导出 | 在 B7 里显式处理：presence 掩码进基线，并另跑显式 120 min 哨兵版本，两者之差 `F7_sentinel_gap` 直接进表；不选一个有利哨兵 |
| **W5-37** | 本轮自查新缺陷：判定层用 `(v.get("holm_p_vs0") or 1.0) < 0.05` 判显著，而 Holm p 可以是**精确 0.0** → 被 `or` 当成缺失，部分「对 0 显著」被误写为「不显著」 | 首版 v3 输出与手算 CI 对撞（S2/S5/S7 的 holm=0 却写「未证明」） | 改 `_sig()`：`None` 才视为缺失；修正后重跑全部 v3 分析（B7/B8 用同一函数，故三张卡一起受益） |
| **W5-38** | B7/B8 的基线列集合与 B5/B6 不同（去重、显式哨兵、末端中断） ⇒ LightGBM 的 HPO 必须重搜，可能改变正则化行为 | 协议设计期自审 | 作为**新增敏感性协议**独立登记（附录 H/I），不回填 B5；HPO 仍按（任务×臂）一次搜索后冻结，`hpo_seed=0` 与是否纳入 HPO 随机性在 run_record 中写明 |
| **W5-39** | B8 分析首版把 `DiD_DR` 的系数写成 `(锚_c − R_c) − (锚_dense − R_dense)`，即效应定义的**相反数**（`DiD_Dfull` 是对的）⇒ 两轨的"增强/退化"标签被颠倒（例如 dispo·LR shift 轨 `term40` 真值 −0.0060 被写成 +0.0060「增益增强」） | 结果复核时拿 `DR__dense` 与 `DR__term40` 手算差值对撞（0.0013 − 0.0073 = −0.0060 与表中 +0.0060 反号） | 已改 `analyze_b8.contrasts()` 为 `(R_c − 锚_c) − (R_dense − 锚_dense)` 并重跑 B8 分析与版式；**TOST/等价结论不受影响**（等价对符号对称），受影响的是"增强/退化"两处方向性标签。首版 JSON 的字段值仍可在 `10_b8/analysis.json` 的 `coef` 里核对 |
| **W5-40** | 版式缺陷（自第二轮构建器继承）：`0.2 第二轮新增结论一览` 被排在 §8 与 §9 之间，读者按编号找不到它 | 第三轮给报告加 `0.3/0.4` 时检查 §标题序列发现 | `ds_report3.main()` 把 `0.2/0.3/0.4` 移到 §0.1 之后（仍在 §0 内）；重出 md 与两版 PDF。仅改排版，未改任何数值 |
| **W5-41** | B7 缺失分层首版在"某层某任务 val 阳性数 < 20"时直接崩在 `np.percentile`（空 bootstrap 分布），且 `n_val/pos_events_val` 用跨任务 CSN 去重并集 → 两个任务显示同一个数 | 首版运行 IndexError + 复核表内数值 | 改为**按任务粒度**剔除阳性不足的任务并登记进 `09_b7/missing_strata_meta.json.skipped_strata`；例数与阳性数按「该层该任务」统计；判据不变（阈值 20 与"例数 < 2000 只作描述"一并写明） |


## 9. 第四轮追加登记（2026-09-11，观测过程 benchmark 方案：B9 复核 + B10）

| 号 | 事实 | 抓出方式 | 处置 |
|---|---|---|---|
| **W5-42** | B9 的 `analysis.json` 只覆盖 **60/70** 个 run：`decomp_D120` 的 `B_only_LGBM` 与 `Count_LGBM` 共 10 个 run 目录写于分析之后（`runs/` mtime 16:31 晚于 `analysis.json` 16:11），跨族描述性对比因此缺臂 | 本轮盘点逐卡比对 `ls runs` 计数与 `analysis.n_runs` | 按同一 PREREG 协议重跑 `analyze_b9.py`（不新增拟合、不改判据）；现 `n_runs=70`、`verify.n_cells=70`、各臂 val 集合一致。教训固化：报告生成前必须比对 run 目录数与分析读入数 |
| **W5-43** | 本机 `mamba_ssm` / `causal_conv1d` **不可安装**（代理不可达、无 PyPI、无 `nvcc`），ReTAMamba 的 Mamba 主干无原生实现可用 | 环境探测（`import` 失败 + `pip download` 超时 + `which nvcc` 空） | 登记为执行偏差而非静默替代：selective-SSM 用等价的纯 PyTorch 零阶保持递推（`h ← h·exp(ΔA) + ΔB·Δ·x`，`y = C·h + D·x`），causal 深度卷积用 `F.conv1d(groups=d_inner)`；新增 **g12** 验收与独立朴素逐步写法逐槽对照，实测 `max_abs_diff = 4.8e-07`。**只声称同一离散化语义，不声称复现作者 CUDA kernel 的位级结果** |
| **W5-44** | 本端口首版把多尺度聚合权重写成 `w_rel × obs_mask`。快照 `aggregation.py:101-113` 只用 `w_rel` 加权，`obs_mask` 仅用于 `cnt_obs/coverage`。错误写法下**每个入模 token 的 `dt` 恒为 0**（观测槽的 `R_c=0` 是定义），最新性通路被结构性删除，恒等 gate 消融也随之变成构造性空操作 | `accept_b10.py` 的 **g7 模块消费**：`max\|Δscore\|_zero_dt` 实测 **0.0**（分数逐位不变）而阻断 | 改回快照语义（LOCF carry 按可靠度打折后仍参与均值），g7 复测 `zero_dt = 0.026`、`wipe_obs_mask = 0.079`、`identity_gate = 0.016`（且该消融与主模型共享除 gate 外全部权重）、`zero_value = 0.057` 全部 > 容差。同时把恒等 gate 的比较改为**复制同一份权重**，避免拿两个不同随机初始化之差冒充机制效应 |
| **W5-45** | 背景块（`NUM`/`O_core_v2`/`R`）沿用 `phase_b8.cond_stats`，其 `sim_mask` **只做干预、不做 `t ≤ t_w` 过滤**，正确性依赖「事件存储已按 `t_w` 门控」这一外部事实；网格路径首版同样只断言不过滤 | `accept_b10.py` 的 **g1 未来信息不变性**：向 `events_*.npz` 注入 `t_w+180min` 的伪记录后，背景帧发生变化（`background_identical=False`），网格路径则直接触发「读到 t_w 之后的记录」停止断言 | B10 侧新增 `ds_b10view.cond_stats_gated`：与 `phase_b8.cond_stats` 同公式、同 `sim_mask`，但额外显式施加 `t ≤ t_w`，并把被排除行数落盘。**实测真实存储上排除数 = 0，dense/term20 的背景与 `phase_b8` 逐位相同（max\|diff\| = 0.0，NaN 位置一致）**，故不回填、也不改变 B7/B8/B9 任何数字；`build_grid` 同样加显式门控（g1 现要求网格与背景同时不变）。B10 的 5 个正式拟合进程启动于该修正之前，因上述逐位等价性，其数值与修正后代码一致，`run_record.json` 内的 `code_hash` 记录实际运行代码 |
| **W5-46** | 判等缺陷：`np.array_equal` 对含合法 NaN 的背景帧恒为 `False`，使 g1 在数据确实不变时仍报失败（同一帧自比重跑也不等） | 用「仅清缓存、不换数据」的对照重跑定位（`cache-only rerun identical: False`） | g1 改用 `np.array_equal(..., equal_nan=True)`，并要求**网格与背景同时**不变才通过（比原判定更强）。教训：本项目背景块合法携带 NaN（0 点通道），任何帧级等价断言都必须显式声明 NaN 语义 |
| **W5-47** | ReTAMamba 固定快照**缺失** `models/retamamba/backbone.py`、`head.py`、`utils.py`（`model.py:19,21,25` 仍 import 它们），亦无 `src/config/configs.py`、`benchmark_dataset.py`、`metrics.py` 与任何 `__init__.py`；作者默认训练入口不可运行 | 逐 import 核对快照文件清单 | 按 `model.py` 的调用点重建其接口（`MambaBackbone(d_model, n_layers, d_state, d_conv, expand, drop)`；`dense_to_observed_padded` = `ds_b10view.event_batch(observed_only=True)`），预测头由本项目**两编码器共用的融合头**取代（方案 §8 要求同一融合）；因此 B10 的 `OP_ReTAMamba` 是「按快照语义重建的适配实现」，**不声称与作者完整仓库等价**，论文默认 48h/`{60,120,240}`/`budget=32` 的偏离已逐条写入 PREREG §4 |
| **W5-48** | B10 的 `run_record` 目录数（80）不等于拟合数（40）：同一模型对 dense/term20 各做一次读出，若照原样进账本会把机时算四倍 | 协议设计期自审（B8 的 shift 轨同样是 1 拟合 2 读出） | `wall_secs` 只落在 dense 读出目录，term20 目录写 0.0；每条记录带 `provenance.fit_group` 与 `n_fits_this_dir_carries_wall`；`gen_ledger3.py` 的 `is_gpu` 补齐 `model_info.device` 与 `setenc/op` 两类模型（此前会把 B9/B10 的 GPU wall 误记成 CPU），并在账本里写明「run 目录数不是拟合数」 |
| **W5-49** | B10 的 80 条 run 记录带 **3 种 `code_hash`**（`ds_b10view.py` 在拟合进行中被动过三次：`build_grid` 的显式 t_w 门控 → `cond_stats_gated` → 验收用的 `REAL_CACHE`）；其余 7 个入 hash 的文件（含 `ds_retamamba.py`、`ds_opmodels.py`）**全轮逐位相同**，故 W5-44 的主干修正在任何一次拟合之前就已生效 | 第四轮环境清单 `00_data/environment_manifest_20260911.json` 的 `per_card_code_hashes` 与 `gen_env_manifest4.py` 输出 | 不重跑，改用**更强的直接证据**：每条 `run_record.provenance.view_tensor_sha` 都存了实际喂给模型的 `X / dt_norm_grid / stat` 张量 SHA-256。实测**三组 code_hash 组之间的 sha 集合完全一致**（dense 与 term20 各一组，跨组并集唯一），即三个代码版本产出的输入数组逐位相同；叠加 W5-45 的「真实存储被 t_w 门控排除行数 = 0、背景与 `phase_b8` 逐位相同（max\|diff\| = 0.0）」，拟合数值不受该中途编辑影响。教训：长时拟合期间不应修改被 hash 的源文件；若必须改，必须留下**输入张量级**的等价证据而不只是口头声明 |
| **W5-50** | 三个冻结输入在仓库内**没有产出脚本**，只有读取方：`c0_static.parquet`（549 列，占 B7/B8/B9/B10 背景块 600 列中的 **549** 列）、`c3_events.parquet`（4,184,684 行事件长表）、`b9_ev_tokens.npz`（B9 token）。`channels6.build_c0 / build_c3_events / ds_evtoken.build` 都存在且自包含，但从没被任何脚本调用 ⇒ 显然当年是交互式产出 | 研究者授权一次性打开 test 后，为「test 侧能否重建」做链路核查（2026-09-12）；`gen_test_manifest.py` 的 `frozen_input_reproducibility` 与 `probe_t1_c0.py` | 不猜、不默认「重跑即可」：为每个输入写**逐位复现探针**，以既有 train/val 产物为准。结果：C0 **PASS**（548/548 共享列、0 个不一致、`max\|diff\|=0.0`、列序一致；并定位出冻结词表 = 248 词条、拟合人群是**官方 train 切分全部 81,588 个 CSN**，不是 `in_main` 的 68,586（后者只得 223 词条，首版探针据此假失败）；词表不含 val/test ⇒ 无词汇泄漏）；C3 **PASS**（4,184,684 行、列与 CSN 集合一致、每列 `max\|diff\|=0.0`，50 s）；B9 token 见 `T1_probe_b9_tokens.json`。探针脚本入库（`probe_t1_c0.py`），三个 JSON 落 `13_test_final/`。**遗留治理问题**：冻结管线存在「无脚本产出」的输入本身就是可复现性缺口，与 test 无关；建议后续把这四个构建步骤写成有序驱动脚本（本轮不擅自改动 Wave6 冻结行为） |
| **W5-51** | **操作事故（助手自身）**：为探 B9 token 是否可复现，第一版探针直接调用 `ds_evtoken.build()` 而**未重定向输出路径**，覆盖了冻结输入 `cache/b9_ev_tokens.npz` 与 `b9_ev_tokens_meta.json`（mtime 由 09-11 15:03 变为 09-12 18:06）。更糟的是第二版探针拿「重建结果 vs 现存文件」比，得到 `bit_identical=True` —— 那是**循环证据**（自己和自己比），却写成 PASS | 复核冻结文件 mtime 时发现与本轮开始时 `ls` 记录的 09-11 15:03 不符 | ①立即停止使用该循环结论，把探针改为**必须含独立证据**才允许 PASS；②用两条独立证据判定实际无损：现存 meta 与 **70/70** 条 B9 `run_record` 在消费时记录的 `vocab_sha/n_tokens/n_rows_source/n_rows_retained/budget/n_types_train/unk_tokens_val/n_truncated_visits` **逐项相同**，且字节数与 09-11 相同（22,988,653）；用现存 token 重算 `dispo_T3__E11__s0` 的 val 预测，AP `0.8071297994149058` 与存表**逐位相同**（`abs_diff = 0.0`），`n_params`/`best_epoch` 一致 ⇒ 重建是确定性的、内容未变，B9 全部结论不受影响；③探针改为写临时目录并断言 `sha256(冻结文件) before == after`；④纪律固化：**任何调用带写盘副作用的既有函数前，必须先确认输出路径已重定向**，且「比较对象可能已被同一操作产生」的情形不得算验收 |
| **W5-52** | T-1 逐位复现验收中，`b9_ev_tokens.npz` **未通过**：含 test 的树与冻结树在 train/val 的 78,418 个 CSN 中有 77,956 个 token 内容不一致（`type_id` 多重集不同、`(type_id,cont)` 集合不同，非段内顺序问题）；而同一棵树上 `c3_events` 逐位一致（4,184,684 行 × 5 列，0 不一致）、两份 meta 的 `vocab_sha` 与 `n_types_train=770`、`global_median/iqr`、`unk_tokens_val=1786` 全相同 ⇒ 「输入相同 + 词表相同 ⇒ 输出不同」的矛盾，夜间未定位 | `verify_t1_layer.py`（新增按 CSN 分段比对）；`13_test_final/T1_未决项_b9_tokens.md` 记录了已排除项（段映射错位、`row_id` 重编号、词表差异）与三条未排除候选 | **不放宽判据、不删失败记录**：以修正案 A1 把 B9 从一次性 test 读数中剔除（Tier-1 与 B10 照常），恢复条件为重跑验收得 `T1_pass=true`。对既有结论无影响：用当前 token 重算 `dispo_T3__E11__s0` 的 AP 与存表逐位相同（`abs_diff=0.0`），且 B9 的 set encoder 对 token 置换不变（g6 实跑通过）。候选线索之一：W5-51 中我覆盖过该文件，故「冻结 vs 新建」两个操作数可能都产自今天的不同调用条件 |
| **W5-53** | 一次性 test 读数完成后自查出**两个判定层缺陷**：**D-1** `analyze_test_final.py` 把模型名嵌进对比名（`T1_*__lr`/`__lgbm`），而 `analyse_v3` 在每个层内都会计算全部对比名 ⇒ 直接打印日志会出现「lr 与 lgbm 数值完全相同」的**错层重复行**（真实逐例预测并无问题：同臂 lr AP 0.78086 vs lgbm 0.80930）；**D-2** `shift` 轨被实现成与 `dense` 使用**同一个评价行集合**（`{"dense": ev, "shift": ev}` 共用同一 X）⇒ shift 与 dense 逐位相同、Δ 恰为 0，是退化计算 | 读数后核对「两模型不可能给出逐位相同的 CI」+ 核对 shift 与 dense 的 AP 完全相等 | D-1：改为只保留「对比名后缀 == 该层模型」的行，产出 `table_F11_test_corrected.csv`，全部结论取自该表，原始 JSON 保留可核。D-2：**本次 shift 的 `T1_DR_shift`/`T1_DiD_shift`/`T1_AbsLoss_shift` 全部作废、不进入任何结论**；`matched` 轨实现正确照常使用。补算 shift 需重跑评价器但不改变任何模型见过的数据（test 行始终只用于打分），故登记为「同一冻结拟合的补算」而非第二次消费，是否补算由研究者决定。**教训**：读数前的彩排只比对了 `dense` 轨存表值，未覆盖「新增读出轨」的自洽性 ⇒ 以后凡新增轨必须为该轨本身设计可断言的不变量（如 shift 必须 ≠ dense，除非干预未改动任何样本） |
