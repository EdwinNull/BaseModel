# 时序基础模型在急诊数据上的子集表现：调研与实验结果汇总

## 0. 研究主线

本项目的主线：

1. 调研当前常用时序基础模型，重点看它们使用的是长时序还是短时序、预训练数据是什么、是否包含医疗数据、是否支持不规则采样或缺失；
2. 查看已有文献是否已经报告过某些患者子集上的性能下降；
3. 选择适合的 8 个时序基础模型，在 MC-MED 与 MIMIC-IV-ED 上完成实验；
4. 按人口学、临床特征和 measurement process 将两个急诊数据集划分为子集；
5. 比较各模型在不同 subgroup 中的表现，寻找多个模型共同表现较差的子集；
6. 比较这些弱子集是否在两个数据集中重复出现。

本文件只做到“调研 + 实验 + 发现问题”，不包含模型修复方案。

---

# 第一部分：文献调研与模型背景

## 1. 文献中已经报告过哪些弱子集

现有文献显示，临床模型的弱子集主要集中在几类：年龄、性别、种族及交叉人群、分诊严重度、测量过程以及时间/流程变化。MC-MED 本身几乎没有系统的患者 subgroup 评估，因此在 MC-MED 和 MIMIC-IV-ED 上对时序基础模型做统一 subgroup 审计具有明确意义。

## A1. 文献中已报告的表现差子集

| 编号  | 文献                                                                       | 数据集与规模                                               | 任务 / 模型                                                                                                    | 表现差的子集（原文数字）                                                                                                                   | 位置                                           | 作者给的原因                             | 证据类型      | 阅读范围                             | 对 MC-MED decomp_60 的启示                                                                                                      |
| --- | ------------------------------------------------------------------------ | ---------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------- | ---------------------------------- | --------- | -------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| E1  | Chen et al., MC-BEC, NeurIPS 2023 D&B（arXiv 2311.04937）                  | MC-MED 前身 MC-MED-v0：斯坦福急诊有监护床位 2020–2022，102,731 次就诊 | decomp 60/90/120（评估期 15 分钟后 60–120 分钟内新出现 HR>110、MAP<65 或 SpO2<90；评估期或分诊时已异常者排除）；多任务 LightGBM，输入含分诊、人口学与监护 | 固定灵敏度阈值（验证集灵敏度 0.85）下 decomp-60 的 TPR：年龄 <55 岁 0.87、≥55 岁 0.94；女性 0.88、男性 0.92；去掉监护模态后多任务模型 decomp-60 AUPRC 0.25 → 0.14        | Sec 3.2–3.3；Table 4、Table 5                  | 未分析原因                              | 直接实验      | 正文与表格逐字；附录为工具摘要                  | 唯一与 MC-MED 同源的分组结果：较差的是年轻组和女性，不是老年组。但这是单阈值 TPR，受各组基础率与风险分布影响，没有组内 AUROC、样本量和置信区间；表内差值与显示值有出入（性别 0.92−0.88 记为 0.05）          |
| E2  | Kansal et al., MC-MED, Sci Data 2025;12:1094                             | MC-MED 1.0.0：118,385 次就诊 / 70,545 人                  | 数据描述论文，无基线模型                                                                                               | 没有基准结果，也没有分组分析                                                                                                                 | Methods、Technical Validation                 | 不适用                                | 无证据       | 正文；人口学表（PhysioNet Table 11）为工具摘要 | 数据特性会制造子集：只覆盖有监护床位的就诊；监护数据按床位记录、再按入床和离开时间切分；年龄加 0–2 岁扰动并截断在 18–90；时间按患者平移（日历季节类子集可能不可用，需核对）；numerics 有 Chart / Monitor 来源字段 |
| E3  | Gustafsson et al., SignalMC-MED, arXiv 2603.09940（2026）                  | MC-MED 22,256 次就诊，按时间切分                              | ECG / PPG 基础模型线性探针，20 个任务（含急诊去向）                                                                           | 未做分组、缺失或偏移分析                                                                                                                   | Table 2、Table 4                              | 不适用                                | 无证据       | 正文约一半逐字                          | MC-MED 上的基础模型评测同样没有子集分析                                                                                                     |
| E4  | Xie et al., Sci Data 2022（MIMIC-IV-ED 基准）                                | MIMIC-IV-ED 441,437 次成人就诊                            | 住院、危重结局、72 小时复诊；LR / RF / GB / MLP / LSTM 与 ESI、NEWS 等评分                                                   | 未做分组分析；分诊时点危重结局 AUROC：ESI 0.804、NEWS 0.634、最佳 MLP 0.883                                                                        | Table 6                                      | 不适用                                | 无证据（分组）   | 正文逐字                             | 最常用的 MIMIC-IV-ED 基准没有子集报告，复用它的工作也大多没有                                                                                       |
| E5  | Lett et al., JAMA Netw Open 2025;8(5):e2512947                           | MIMIC-IV-ED 160,016 次就诊；波士顿儿童医院 22,222 次             | 急诊入院预测；XGBoost、惩罚 LR                                                                                       | 种族 × 性别交叉子群误差更大，例如边际去偏后 ECE：美洲原住民男性 0.119、西语裔女性 0.104、黑人女性 0.102；FNR：美洲原住民男性 0.218                                             | Results；Figure 2–3                           | 交叉子群样本少；各组入院率不同时 FNR、FPR、校准不可能同时相等 | 直接实验      | 正文；补充表未读                         | 只按单一属性分组会漏掉交叉子群（老年女性、少数族裔男性等）                                                                                               |
| E6  | Liu et al., FAIM, arXiv 2403.05235                                       | MIMIC-IV-ED 418,100；新加坡总医院急诊 1,716,830               | 急诊入院预测；LR 与多种公平方法                                                                                          | 基线 LR 的种族 ΔTPR 0.251、ΔTNR 0.224；性别 ΔTPR 0.074                                                                                  | Table 2、Table 4                              | 未分析                                | 直接实验      | 全文含表                             | MIMIC-IV-ED 上种族差距远大于性别差距                                                                                                    |
| E7  | Röösli et al., Sci Data 2022;9:24                                        | MIMIC-III 院内死亡基准模型（LSTM），外部 STARR                    | ICU 48 小时院内死亡                                                                                              | Medicaid 与私人保险事件率相近（8.5% vs 8.3%），Medicaid 的 AUROC、AUPRC 更差；黑人事件率更低（9.7% vs 11.3%）仍更差；Medicare（多为 ≥65 岁）风险被明显低估；外部验证事件召回低于 20% | Results：classification parity、calibration 各段 | 类别不平衡、少数群体代表性不足                    | 直接实验      | 全文                               | 老年组的问题可能主要在校准（风险被低估），而不是排序                                                                                                  |
| E8  | Meng et al., Sci Rep 2022;12:7166（MIMIC-IF）                              | MIMIC-IV                                             | 院内死亡深度模型                                                                                                   | 模型依赖人口学特征；不同种族、性别、年龄的机械通气处置不同                                                                                                  | 摘要                                           | 处置差异进入数据                           | 作者分析      | 摘要                               | 处置差异会变成模型可利用的捷径                                                                                                             |
| E9  | Guo et al., Sci Rep 2022;12:2726                                         | MIMIC-IV ICU，按 2008–10 / 11–13 / 14–16 / 17–19 分组    | 死亡、长住院、脓毒症、有创通气；前馈网络                                                                                       | 2008–10 训练、2017–19 测试，脓毒症 AUROC 最多降 0.090（95% CI 0.080–0.101）                                                                  | 摘要                                           | 医疗实践随时间变化                          | 直接实验      | 摘要                               | 时间段本身就是一类子集；DG / UDA 没有比 ERM 更稳                                                                                             |
| E10 | Shi et al., BMC Med Inform Decis Mak 2025;25:241                         | MIMIC-III 23,426 人，首个 24 小时                          | 测量模式与人口学的关联（TMLE）及死亡预测                                                                                     | 调整病情后：≥65 岁生命体征测得更频繁、缺口更少（化验更少）；白人首 24 小时血压测量 34.22 次，黑人 32.79 次；只用测量模式预测 ICU 死亡 AUC 0.76                                      | Results；Figure 与 Table                       | 监护实践中的系统差异                         | 直接实验      | 全文                               | 观测密度随年龄和种族系统变化，而观测密度本身带结局信息，模型会学到它                                                                                          |
| E11 | Agniel et al., BMJ 2018;361:k1479                                        | 波士顿两院 669,452 人，272 项化验                              | 3 年生存                                                                                                      | 是否开了化验在 86% 的化验项目上与生存显著相关；化验时间比化验值更能预测生存的占 68%                                                                                 | Abstract；Table 1–2                           | 医疗过程本身产生信号                         | 直接实验      | 正文与表                             | “测得多 = 病重”是普遍规律，测量习惯不同的子集上会失效                                                                                               |
| E12 | Jeanselme et al., ML4H 2022（PMLR 193）                                    | MIMIC-III、SUPPORT                                    | 短期生存预测                                                                                                     | 两种常用插补方法之间的选择可以翻转黑人 / 非黑人的公平方向；分组插补可能反而伤害边缘群体                                                                                  | Introduction；Theorem 4.1–4.2                 | 三种“临床存在”机制：就医受限、按判断采集、确认偏差         | 直接实验 + 理论 | 部分（结果数字未取得）                      | 缺失感知模型（GRU-D、BRITS 等）之间的差别必须按子集报告                                                                                           |
| E13 | Wong et al., JAMA Netw Open 2021;4:e2131674                              | eICU、MIMIC-III、MIMIC-IV 等 87,971 对 SpO2–SaO2         | 脉搏血氧偏差                                                                                                     | 隐匿低氧：黑人 6.8%、西语裔 6.0%、亚裔 4.8%、白人 4.9%；隐匿低氧者 24 小时后 SOFA 更高、院内死亡更高                                                              | 摘要                                           | 脉搏血氧对深肤色高估                         | 直接实验      | 摘要                               | decomp_60 的输入和标签都用 SpO2：部分子集的低氧事件可能被漏记                                                                                      |
| E14 | Platts-Mills et al., Acad Emerg Med 2010；Grossmann et al., PLoS One 2014 | ≥65 岁急诊 782 人；519 / 394 人                            | ESI 分诊准确性                                                                                                  | ESI 1 级识别需要立即抢救干预的老年人灵敏度 42.3%；老年漏分诊 22.5%（干预后 24.2%），随年龄增大而升高                                                                 | 摘要                                           | 未遵循 ESI 流程；老年表现不典型                 | 直接实验      | 摘要                               | ESI 分层本身带误差：ESI 3 级里混有被低估的老年患者                                                                                              |
| E15 | Sax et al., JAMA Netw Open 2023;6:e233404                                | KPNC 21 个急诊 5,315,176 次                              | ESI 误分诊                                                                                                    | 误分诊 32.2%（漏分 3.3%、过分 28.9%）；黑人漏分诊相对风险 +18.5%；服高危药物 +30.3%、合并症多 +22.4%、近期 ICU +36.7%                                            | 摘要                                           | 分诊主观性                              | 直接实验      | 摘要                               | 同上；用药与合并症是 MC-MED 可取的分层变量                                                                                                   |
| E16 | Kemp et al., BMC Emerg Med 2020；Martín-Conty et al., QJM 2024            | ≥75 岁衰弱老人 1,711 次；院前 8,028 人                         | NEWS2 等预警评分                                                                                                | 衰弱老人中 NEWS2 预测 30 天死亡 AUC 0.70、入院 0.62；各评分加入年龄后 AUC 都显著提高（NEWS2 P=0.001）                                                       | 摘要                                           | 同样的体征在不同年龄代表不同风险                   | 直接实验      | 摘要                               | 只用体征、不含年龄的模型（如 decomp_60 冻结基准）在老年组可能排序变差                                                                                    |
| E17 | Subbaswamy et al., npj Digit Med 2024;7:334（AFISP）                       | 多院住院恶化监测模型，测试 60,998 次                               | 非 ICU 恶化预警                                                                                                 | 整体 AUROC 0.986，最差 5% 子集 0.919；找到 13 个子群，4 个 AUROC 区间低于 0.9，9 个是多变量组合（单变量分组发现不了）；给最差子群补训练数据可补回差距                                | Results；Table 与 Figure                       | 子群数据不足                             | 直接实验      | 全文                               | 预设单变量分组不够，需要数据驱动的子集发现                                                                                                       |
| E18 | Seyyed-Kalantari et al., Nat Med 2021；Oakden-Rayner et al., CHIL 2020    | MIMIC-CXR 等胸片                                        | 影像分类                                                                                                       | 女性、黑人、低社会经济地位漏诊更多，交叉子群（如西语裔女性）更严重；隐藏分层造成最多约 20% 的性能差，例如无胸管气胸 AUC 0.77 vs 有胸管 0.94                                              | 摘要；Sec 3                                     | 捷径特征、子类罕见、标签不准                     | 直接实验      | 摘要；扩展摘要全文                        | 不是时序，但机制（捷径、隐藏分层）可直接迁移                                                                                                      |

## 2. 本项目实际采用的 subgroup 划分

### 2.1 MC-MED

| 子集族  | 实际分组                                                                                    |
| ---- | --------------------------------------------------------------------------------------- |
| 人口学  | Age：18–44 / 45–64 / 65–79 / ≥80；Gender；Ethnicity；Race 原始类别；Age×Gender；Race×Gender       |
| 临床   | ESI：1–2 / 3 / 4–5；Arrival mode；HR/MAP/SpO₂ 距阈值分组                                        |
| 测量过程 | Total density；HR/MAP/SpO₂ 单通道 density；Chart / Monitor 来源                                |
| 其他   | Chief complaint 仅做 mapping audit；rooming delay 因覆盖不足未纳入主结果；共同 risk cohort 中缺失模式无法形成有效对照 |

### 2.2 MIMIC-IV-ED

| 子集族  | 实际分组                                                                         |
| ---- | ---------------------------------------------------------------------------- |
| 人口学  | Age：18–44 / 45–64 / 65–79 / ≥80；Gender；Race 原始类别；Age×Gender；Race×Gender      |
| 临床   | ESI：1–2 / 3 / 4–5；Arrival mode；Chief complaint 仅做 counts/mapping audit       |
| 测量过程 | Total density；HR / SpO₂ / SBP / DBP / RR 单通道 density；Missing pattern         |
| 其他   | Ethnicity 无独立冻结字段；MIMIC 无原始 MAP 通道，因此 measurement-density 对照使用 SBP/DBP 等原始变量 |

这里不再讨论“建议怎么分”，以上就是已经完成实验时实际采用的划分。

## 3. 实际运行的 8 个时序基础模型

| Model            | 预训练/主要数据                                           | 时间尺度/上下文              | 医疗数据         | 不规则/缺失支持                | 患者 subgroup 分析       |
| ---------------- | -------------------------------------------------- | --------------------- | ------------ | ----------------------- | -------------------- |
| MIRA             | MIMIC-III/IV、WAVES、PTB-XL、Sleep-EDF；从 Time-MoE 初始化 | ≤512，点级 token         | 是，以医疗数据为主    | 原生连续时间戳；可处理不规则时间        | 原论文未做 Age/Gender/ESI |
| Time-MoE         | Time-300B，约 90.5% Nature/气象                        | ≤4096，偏长上下文           | 极少，仅公共卫生汇总数据 | 规则网格；预训练时常在缺失处切分        | 未做患者 subgroup        |
| Sundial          | TimeBench，ERA5 占比高，含少量 ECG                         | 2880，patch 16，偏长上下文   | 少量 ECG       | 规则网格；缺失原生支持有限           | 未做患者 subgroup        |
| TimesFM 3.0      | GiftEvalPretrain + Wiki + Trends + 合成              | 最长约 15,360，偏长上下文      | 未明确报告        | 规则网格为主                  | 未做患者 subgroup        |
| Timer / Timer-XL | UTSD + LOTSA，含少量 EEG/ECG/PPG/HR                    | 2880，patch 96，长上下文    | 部分           | 不规则/缺失支持未明确             | 未做患者 subgroup        |
| LightGTS         | 33 个跨域数据集，含 EEG/ECG 等                              | 约数百点、周期 token         | 部分           | 依赖规则周期                  | 未做患者 subgroup        |
| VisionTS         | 仅 ImageNet 视觉预训练                                   | 典型 lookback 1728–4032 | 否            | 规则序列、周期折图               | 未做患者 subgroup        |
| Chronos-2        | Chronos/GIFT 子集 + 大量合成数据                           | 2048→8192，长上下文        | 未明确报告        | 有 missing mask，但无时间间隔建模 | 未做患者 subgroup        |

## 4. 常用时序基础模型主要研究长时序还是短时序？

### 4.1 主结论

目前常用时序基础模型整体上 **明显偏向中长上下文**，真正针对“十几个点的超短时序”设计和系统评测的模型很少。

| Model            | 典型/最大上下文      | 长短时序判断              | 常见预训练/评测数据                               |
| ---------------- | -------------:| ------------------- | ---------------------------------------- |
| MIRA             | ≤512 点        | 中等长度；8 个模型中相对更适合短输入 | MIMIC-III/IV、WAVES、PTB-XL、Sleep-EDF      |
| Time-MoE         | ≤4096         | 长时序                 | Time-300B，主要为气象、能源、交通等                   |
| Sundial          | 2880          | 长时序                 | ERA5、LOTSA、Chronos 数据、ECG 等              |
| TimesFM 3.0      | 约 15k         | 长时序                 | GiftEvalPretrain、Wiki、Google Trends、合成数据 |
| Timer / Timer-XL | 2880          | 长时序                 | UTSD、LOTSA、ERA5                          |
| LightGTS         | 约数百点、周期 token | 中等到偏长               | Monash、UEA/UCR、交通、EEG/ECG 等              |
| VisionTS         | 典型 1728–4032  | 长时序                 | ImageNet 视觉预训练；时序任务上多用较长 lookback        |
| Chronos-2        | 2048→8192     | 长时序                 | Chronos/GIFT 子集 + 合成数据                   |

### 4.2 这些模型通常用什么数据集？

可以把常见数据分成几类：

- **气象/环境**：ERA5、Weather、ETT 等；
- **能源/交通**：Electricity、Traffic、PEMS、Solar 等；
- **通用跨域集合**：LOTSA、UTSD、GIFT-Eval / GiftEvalPretrain、Monash；
- **医疗相关**：MIRA 使用 MIMIC-III/IV 等医疗数据；Sundial、Timer、LightGTS 只包含少量 ECG/EEG/PPG/HR 等生理信号；其他模型多数没有明确的急诊生命体征预训练数据。

### 4.3 原论文有没有做患者 subgroup？

**基本没有。**

这些模型论文常见的划分方式主要是：

- 不同数据集；
- 不同预测长度；
- 不同上下文长度；
- 不同领域或频率；
- 域内 / 域外；
- zero-shot / fine-tune。

但几乎没有按 **Age、Gender、ESI、Arrival、Race、measurement density** 这类患者级或急诊流程级 subgroup 做系统分析。

### 4.4 对本项目最关键的一句话

> **现有 TSFM 大多是在中长时序、通用或非急诊数据上建立的，而我们的任务是短窗口急诊生命体征；同时原论文基本没有做患者级 subgroup，因此把 8 个模型放到 MC-MED 和 MIMIC-IV-ED 上统一做 subgroup 审计是必要的。**

详细的各模型上下文、patch、预训练数据和文献位置放在附录中。

### 3.1 八模型调研的核心结论

- 这 8 个模型中，**没有模型是专门为“急诊、短窗口、生命体征、患者 subgroup”设计的**。
- 多数模型偏向长上下文；MC-MED 的 0–15 min 输入与它们常见的数百到数千点上下文差异很大。
- MIRA 最接近医疗场景，但它的预训练主要是 ICU/医疗数据，不代表已经适配 ED subgroup。
- 原模型论文基本都没有 Age、Gender、ESI 这类患者级 subgroup 结果，所以本项目的 subgroup 实验不是重复原论文，而是在补这一块空白。

---

## 5. 文献来源（子集调研）

| 文献                                  | 链接                                                            | 阅读范围                        |
| ----------------------------------- | ------------------------------------------------------------- | --------------------------- |
| Chen et al. 2023 MC-BEC             | https://arxiv.org/abs/2311.04937                              | 正文与 Table 2–5 逐字；附录为工具摘要    |
| Kansal et al. 2025 MC-MED           | https://doi.org/10.1038/s41597-025-05419-5                    | 正文；PhysioNet Table 11 为工具摘要 |
| MC-MED PhysioNet 1.0.0              | https://physionet.org/content/mc-med/1.0.0/                   | 部分                          |
| Gustafsson et al. 2026 SignalMC-MED | https://arxiv.org/abs/2603.09940                              | 正文约一半                       |
| Xie et al. 2022 MIMIC-IV-ED 基准      | https://arxiv.org/abs/2111.11017                              | 正文                          |
| Lett et al. 2025 JAMA Netw Open     | https://doi.org/10.1001/jamanetworkopen.2025.12947            | 正文                          |
| Liu et al. FAIM                     | https://arxiv.org/abs/2403.05235                              | 全文含表                        |
| Röösli et al. 2022 Sci Data         | https://doi.org/10.1038/s41597-021-01110-7                    | 全文                          |
| Meng et al. 2022 Sci Rep            | https://doi.org/10.1038/s41598-022-11012-2                    | 摘要                          |
| Guo et al. 2022 Sci Rep             | https://doi.org/10.1038/s41598-022-06484-1                    | 摘要                          |
| Zhang et al. 2021 CHIL              | https://arxiv.org/abs/2103.11163                              | 正文部分逐字                      |
| Shi et al. 2025 BMC MIDM            | https://doi.org/10.1186/s12911-025-03058-9                    | 全文                          |
| Agniel et al. 2018 BMJ              | https://doi.org/10.1136/bmj.k1479                             | 正文与表                        |
| Jeanselme et al. 2022 ML4H          | https://proceedings.mlr.press/v193/jeanselme22a.html          | 部分                          |
| Wong et al. 2021 JAMA Netw Open     | https://doi.org/10.1001/jamanetworkopen.2021.31674            | 摘要                          |
| Mettler et al. 2024 medRxiv         | https://www.medrxiv.org/content/10.1101/2024.03.28.24305036v1 | 摘要                          |
| Pradhan et al. 2025 Front Med       | https://doi.org/10.3389/fmed.2025.1606254                     | 部分                          |
| Platts-Mills et al. 2010            | https://doi.org/10.1111/j.1553-2712.2010.00670.x              | 摘要                          |
| Grossmann et al. 2014               | https://doi.org/10.1371/journal.pone.0106203                  | 摘要                          |
| Sax et al. 2023                     | https://doi.org/10.1001/jamanetworkopen.2023.3404             | 摘要                          |
| Kemp et al. 2020                    | https://doi.org/10.1186/s12873-020-00379-y                    | 摘要                          |
| Martín-Conty et al. 2024            | https://doi.org/10.1093/qjmed/hcae031                         | 摘要                          |
| Subbaswamy et al. 2024 AFISP        | https://doi.org/10.1038/s41746-024-01275-6                    | 全文                          |
| Seyyed-Kalantari et al. 2021        | https://pubmed.ncbi.nlm.nih.gov/34893776/                     | 摘要                          |
| Oakden-Rayner et al. 2020           | https://arxiv.org/abs/1909.12475                              | 扩展摘要全文                      |
| McDermott et al. 2024               | https://arxiv.org/abs/2401.06091                              | 正文部分逐字                      |
| Yang et al. 2023 SubpopBench        | https://proceedings.mlr.press/v202/yang23s.html               | 正文部分逐字                      |
| Eyuboglu et al. 2022 Domino         | https://arxiv.org/abs/2203.14960                              | 正文部分逐字                      |
| Barda et al. 2021 JAMIA             | https://doi.org/10.1093/jamia/ocaa283                         | 摘要                          |
| Pfohl et al. 2021 JBI               | https://doi.org/10.1016/j.jbi.2020.103621                     | 摘要                          |
| Chen, Johansson, Sontag 2018        | https://arxiv.org/abs/1805.12002                              | 摘要                          |
| Tan, Shen, Chen 2026                | https://arxiv.org/abs/2604.03478                              | 正文约三分之二                     |
| Locati et al. 2026 ICML 研讨会         | https://icml.cc/virtual/2026/71757                            | 摘要                          |

---

# 第二部分：MC-MED 8 模型 Subgroup 结果

# MC-MED 8 模型 Subgroup 结果表

> 口径：以下主表使用 **R-max AUROC / AUPRC**。  
> “Worst subgroup”按稳定子集中的 **ΔAUROC_complement 最低**确定。  
> `UNSTABLE` 表示样本量/阳性数不足，不作为主要结论。  
> 共同风险 cohort：3,434 visits / 427 positives。

## 1. Age subgroup（年龄子集）

| Model       | 18–44         | 45–64         | 65–79         | ≥80           | Worst subgroup |
|:----------- |:------------- |:------------- |:------------- |:------------- |:-------------- |
| Chronos-2   | 0.500 / 0.121 | 0.500 / 0.127 | 0.499 / 0.102 | 0.505 / 0.165 | 65–79 (-0.002) |
| MIRA        | 0.503 / 0.128 | 0.504 / 0.134 | 0.510 / 0.122 | 0.499 / 0.161 | ≥80 (-0.006)   |
| Time-MoE    | 0.667 / 0.194 | 0.594 / 0.186 | 0.575 / 0.122 | 0.544 / 0.180 | ≥80 (-0.071)   |
| Sundial     | 0.500 / 0.121 | 0.500 / 0.127 | 0.500 / 0.102 | 0.500 / 0.161 | 18–44 (+0.000) |
| TimesFM 3.0 | 0.497 / 0.123 | 0.530 / 0.134 | 0.522 / 0.114 | 0.536 / 0.170 | 18–44 (-0.033) |
| Timer       | 0.500 / 0.121 | 0.500 / 0.127 | 0.500 / 0.102 | 0.500 / 0.161 | 18–44 (+0.000) |
| LightGTS    | 0.499 / 0.121 | 0.500 / 0.127 | 0.499 / 0.102 | 0.500 / 0.161 | 65–79 (-0.000) |
| VisionTS    | 0.499 / 0.121 | 0.500 / 0.127 | 0.499 / 0.102 | 0.499 / 0.161 | ≥80 (-0.001)   |

### Age subgroup counts

| subgroup | N    | positives | prevalence | status |
|:-------- | ----:| ---------:| ----------:|:------ |
| ≥80      | 533  | 86        | 0.161351   | STABLE |
| 65–79    | 879  | 90        | 0.102389   | STABLE |
| 18–44    | 952  | 115       | 0.120798   | STABLE |
| 45–64    | 1070 | 136       | 0.127103   | STABLE |

## 2. Gender subgroup（性别子集）

| Model       | Female        | Male          | Worst subgroup  |
|:----------- |:------------- |:------------- |:--------------- |
| Chronos-2   | 0.502 / 0.126 | 0.500 / 0.125 | Male (-0.002)   |
| MIRA        | 0.501 / 0.128 | 0.507 / 0.138 | Female (-0.006) |
| Time-MoE    | 0.598 / 0.169 | 0.602 / 0.160 | Female (-0.004) |
| Sundial     | 0.500 / 0.124 | 0.500 / 0.125 | Female (+0.000) |
| TimesFM 3.0 | 0.521 / 0.131 | 0.520 / 0.128 | Male (-0.001)   |
| Timer       | 0.500 / 0.124 | 0.500 / 0.125 | Female (+0.000) |
| LightGTS    | 0.500 / 0.124 | 0.499 / 0.125 | Male (-0.001)   |
| VisionTS    | 0.500 / 0.124 | 0.499 / 0.125 | Male (-0.000)   |

### Gender subgroup counts

| subgroup        | N    | positives | prevalence | status        |
|:--------------- | ----:| ---------:| ----------:|:------------- |
| Male            | 1664 | 208       | 0.125      | STABLE        |
| Female          | 1769 | 219       | 0.123799   | STABLE        |
| Other / Unknown | 1    | 0         | 0          | VERY_UNSTABLE |

## 3. Ethnicity subgroup（族裔子集）

| Model       | Hispanic/Latino | Non-Hispanic/Non-Latino | Worst subgroup                   |
|:----------- |:--------------- |:----------------------- |:-------------------------------- |
| Chronos-2   | 0.500 / 0.123   | 0.501 / 0.126           | Hispanic/Latino (-0.001)         |
| MIRA        | 0.500 / 0.123   | 0.505 / 0.135           | Hispanic/Latino (-0.005)         |
| Time-MoE    | 0.660 / 0.225   | 0.581 / 0.151           | Non-Hispanic/Non-Latino (-0.081) |
| Sundial     | 0.500 / 0.123   | 0.500 / 0.125           | Hispanic/Latino (+0.000)         |
| TimesFM 3.0 | 0.538 / 0.131   | 0.516 / 0.130           | Non-Hispanic/Non-Latino (-0.020) |
| Timer       | 0.500 / 0.123   | 0.500 / 0.125           | Hispanic/Latino (+0.000)         |
| LightGTS    | 0.499 / 0.123   | 0.500 / 0.125           | Hispanic/Latino (-0.001)         |
| VisionTS    | 0.499 / 0.123   | 0.500 / 0.125           | Hispanic/Latino (-0.000)         |

## 4. ESI subgroup（ESI 分诊等级子集）

| Model       | High (1–2)    | Moderate (3)  | Low (4–5) | Worst subgroup        |
|:----------- |:------------- |:------------- |:--------- |:--------------------- |
| Chronos-2   | 0.500 / 0.155 | 0.501 / 0.116 | UNSTABLE  | High (1–2) (-0.001)   |
| MIRA        | 0.503 / 0.160 | 0.505 / 0.123 | UNSTABLE  | High (1–2) (-0.002)   |
| Time-MoE    | 0.593 / 0.205 | 0.590 / 0.144 | UNSTABLE  | Moderate (3) (-0.021) |
| Sundial     | 0.500 / 0.155 | 0.500 / 0.114 | UNSTABLE  | High (1–2) (+0.000)   |
| TimesFM 3.0 | 0.524 / 0.161 | 0.521 / 0.118 | UNSTABLE  | Moderate (3) (+0.003) |
| Timer       | 0.500 / 0.155 | 0.500 / 0.114 | UNSTABLE  | High (1–2) (+0.000)   |
| LightGTS    | 0.500 / 0.155 | 0.500 / 0.114 | UNSTABLE  | Moderate (3) (-0.000) |
| VisionTS    | 0.500 / 0.155 | 0.499 / 0.114 | UNSTABLE  | Moderate (3) (-0.001) |

### ESI subgroup counts

| subgroup        | N    | positives | prevalence | status        |
|:--------------- | ----:| ---------:| ----------:|:------------- |
| Moderate (3)    | 2280 | 260       | 0.114035   | STABLE        |
| High (1–2)      | 1002 | 155       | 0.154691   | STABLE        |
| Low (4–5)       | 132  | 10        | 0.0757576  | UNSTABLE      |
| Other / Unknown | 20   | 2         | 0.1        | VERY_UNSTABLE |

## 5. Arrival mode subgroup（到达方式子集）

| Model       | Ambulance / EMS | Walk-in / Self | Other / Unknown | Worst subgroup           |
|:----------- |:--------------- |:-------------- |:--------------- |:------------------------ |
| Chronos-2   | 0.502 / 0.162   | 0.500 / 0.106  | UNSTABLE        | Walk-in / Self (-0.002)  |
| MIRA        | 0.504 / 0.167   | 0.504 / 0.113  | UNSTABLE        | Ambulance / EMS (-0.000) |
| Time-MoE    | 0.569 / 0.192   | 0.615 / 0.148  | UNSTABLE        | Ambulance / EMS (-0.046) |
| Sundial     | 0.500 / 0.160   | 0.500 / 0.106  | UNSTABLE        | Ambulance / EMS (+0.000) |
| TimesFM 3.0 | 0.521 / 0.166   | 0.521 / 0.109  | UNSTABLE        | Walk-in / Self (-0.001)  |
| Timer       | 0.500 / 0.160   | 0.500 / 0.106  | UNSTABLE        | Ambulance / EMS (+0.000) |
| LightGTS    | 0.499 / 0.160   | 0.500 / 0.106  | UNSTABLE        | Ambulance / EMS (-0.000) |
| VisionTS    | 0.499 / 0.160   | 0.500 / 0.106  | UNSTABLE        | Ambulance / EMS (-0.001) |

### Arrival mode counts

| subgroup        | N    | positives | prevalence | status        |
|:--------------- | ----:| ---------:| ----------:|:------------- |
| Walk-in / Self  | 2257 | 239       | 0.105893   | STABLE        |
| Ambulance / EMS | 1175 | 188       | 0.16       | STABLE        |
| Other / Unknown | 2    | 0         | 0          | VERY_UNSTABLE |

## 6. Measurement-process：每个模型最弱稳定子集

| Model       | Worst measurement subgroup               | ΔAUROC vs complement | N    | Positives | Status |
|:----------- |:---------------------------------------- | --------------------:| ----:| ---------:|:------ |
| Chronos-2   | MAP density: Q2                          | -0.003               | 858  | 98        | STABLE |
| MIRA        | HR density: Q1 sparse                    | -0.007               | 859  | 66        | STABLE |
| Time-MoE    | SpO2 density: Q4 dense                   | -0.095               | 859  | 104       | STABLE |
| Sundial     | HR density: Q1 sparse                    | 0                    | 859  | 66        | STABLE |
| TimesFM 3.0 | Chart / Monitor source: Monitor-dominant | -0.036               | 3074 | 395       | STABLE |
| Timer       | HR density: Q1 sparse                    | 0                    | 859  | 66        | STABLE |
| LightGTS    | MAP density: Q4 dense                    | -0.001               | 859  | 135       | STABLE |
| VisionTS    | HR density: Q1 sparse                    | -0.002               | 859  | 66        | STABLE |

## 7. 每个模型三类最弱 subgroup 总结

| Model       | Population                              | Clinical                           | Measurement                                       |
|:----------- |:--------------------------------------- |:---------------------------------- |:------------------------------------------------- |
| Chronos-2   | Race × Gender: White Female (-0.003)    | Distance to threshold: Q3 (-0.003) | MAP density: Q2 (-0.003)                          |
| MIRA        | Race × Gender: White Female (-0.007)    | Distance to threshold: Q4 (-0.006) | HR density: Q1 sparse (-0.007)                    |
| Time-MoE    | Age × Gender: ≥80 Female (-0.113)       | Distance to threshold: Q3 (-0.120) | SpO2 density: Q4 dense (-0.095)                   |
| Sundial     | Age × Gender: 65–79 Female (+0.000)     | Distance to threshold: Q4 (+0.000) | HR density: Q1 sparse (+0.000)                    |
| TimesFM 3.0 | Age (primary four bins): 18–44 (-0.033) | Distance to threshold: Q2 (-0.023) | Chart / Monitor source: Monitor-dominant (-0.036) |
| Timer       | Age × Gender: 65–79 Female (+0.000)     | Distance to threshold: Q4 (+0.000) | HR density: Q1 sparse (+0.000)                    |
| LightGTS    | Age × Gender: 18–44 Male (-0.001)       | Distance to threshold: Q1 (-0.001) | MAP density: Q4 dense (-0.001)                    |
| VisionTS    | Age × Gender: ≥80 Female (-0.002)       | Distance to threshold: Q1 (-0.001) | HR density: Q1 sparse (-0.002)                    |

## 8. 共同 failure 候选

按预设筛查标准：稳定 subgroup 中，**至少 5/8 模型 ΔAUROC_complement < 0**，并且在 R-max、R-mean-max、R-count 三种风险分数下方向一致。

- **Age 18–44：5/8 模型**
- **Age × Gender：18–44 Male：5/8 模型**
- **MAP density Q4 dense：5/8 模型**

这些目前是 **描述性 candidate common failure subgroup**，还不能解释为机制性结论。

## 9. 当前不适合做主表的 subgroup

- **Race**：仅有原始 MC-MED 类别，没有冻结的大类 mapping；部分类别不稳定。
- **Chief complaint**：只有 mapping audit，没有可靠性能分组。
- **Rooming delay**：时间戳覆盖率不足，当前不可靠。
- **Missing-channel pattern**：共同 risk cohort 3,434 例全部为三通道齐全，无法形成对照。
- **Multi-component event**：冻结标签只保留 earliest trigger，不能识别多个同时 trigger。

## 10. 当前结果一句话

MC-MED 中，平均意义上 **≥80 岁、Female、ESI Moderate (3)** 以及部分高密度测量组相对更弱；更值得后续跨数据集复现的共同 failure 候选是 **18–44、18–44 Male、MAP density Q4 dense**。

---

---

# 第三部分：MIMIC-IV-ED 8 模型 Subgroup 结果

# MIMIC-IV-ED 8 模型 Subgroup 结果表

> **口径说明**：本文件主分析基于冻结的 MIMIC-IV-ED v1 zero-shot forecasting benchmark（**2 h context → 12 h forecast**）。  
> 表中数值为 **8 个模型平均的相对 ΔMAE = (subgroup MAE − complement MAE) / complement MAE**；**正值表示该子集预测更差，负值表示更好**。  
> HR / MAP / SpO₂ 分变量报告，不直接平均不同量纲的原始 MAE。  
> 这些 forecasting error **不能与 MC-MED 的 decomp_60 risk AUROC 直接等同**。

## 0. 本部分结果解释新增参照

原来的 subgroup 表格和顺序全部保留。本版只增加四类解释参照：

1. **LOCF**：判断某个 subgroup 的 forecasting error 增大，是不是该 subgroup 本身就更难预测；
2. **Context-max**：判断“先预测、再套固定阈值”是否丢失了上下文已有的异常信息；
3. **监督模型**：判断某个风险 subgroup 是否连经过训练的模型也同样困难；
4. **正式统计判据**：用 bootstrap 95% CI + Holm 校正，区分“方向一致”和“统计上稳定更差”。

另外，Time-MoE 使用官方 normalization 后重新解释；冻结路径只作为复现记录。

> **注意：** 这些新增内容用于“复核和解释原结果”，不会删除原来的 Age、Gender、Race、ESI、Arrival、density、missing pattern 等表格。

## 1. Age subgroup（年龄子集）

| Subgroup | N stays | HR     | MAP   | SpO2   |
|:-------- | -------:|:------ |:----- |:------ |
| 18–44    | 12201   | +26.4% | -7.1% | -22.9% |
| 45–64    | 11461   | -4.3%  | -0.8% | -0.6%  |
| 65–79    | 7181    | -10.7% | +2.1% | +14.8% |
| ≥80      | 4506    | -14.7% | +9.8% | +19.6% |

**主要观察：**

- 18–44：HR 明显更差（+26.4%），但 MAP / SpO₂ 反而更好。
- ≥80：MAP（+9.8%）和 SpO₂（+19.6%）明显更差。
- 因此“年龄弱点”具有明显的 **变量特异性**，不能只说某一年龄段整体最差。

## 2. Gender subgroup（性别子集）

| Subgroup | N stays | HR    | MAP   | SpO2  |
|:-------- | -------:|:----- |:----- |:----- |
| Female   | 19466   | -2.0% | +4.2% | -4.7% |
| Male     | 15883   | +2.0% | -4.0% | +4.9% |

**主要观察：**

- Male：HR、SpO₂ 更差。
- Female：MAP 更差。
- 若跨三个变量综合看，Male 的 forecasting degradation 略更突出，但不是所有变量同方向。

## 3. Age × Gender

| Subgroup     | N stays | HR     | MAP    | SpO2   |
|:------------ | -------:|:------ |:------ |:------ |
| 18–44 Female | 7072    | +21.4% | -6.8%  | -28.5% |
| 18–44 Male   | 5129    | +21.0% | -5.2%  | -8.8%  |
| 45–64 Female | 5732    | -7.1%  | +1.0%  | -2.1%  |
| 45–64 Male   | 5729    | +0.1%  | -2.2%  | +1.1%  |
| 65–79 Female | 3888    | -8.8%  | +6.0%  | +12.5% |
| 65–79 Male   | 3293    | -10.2% | -3.0%  | +12.7% |
| ≥80 Female   | 2774    | -14.5% | +13.2% | +20.0% |
| ≥80 Male     | 1732    | -12.4% | +2.3%  | +14.2% |

其中 **18–44 Male 的 HR 误差在 8/8 模型中均高于 complement**，与 MC-MED 的 18–44 Male candidate failure 在方向上形成部分呼应，但 MIMIC 的 MAP / SpO₂ 没有同步变差，因此只能称为 **变量特定复现信号**。

## 4. Race subgroup

MIMIC-IV-ED 保留原始 race 标签，没有人为重新聚合。以下仅列 N≥100 的原始类别：

| Subgroup                       | N stays | HR     | MAP    | SpO2   |
|:------------------------------ | -------:|:------ |:------ |:------ |
| ASIAN                          | 577     | +7.9%  | -3.0%  | -3.6%  |
| ASIAN - ASIAN INDIAN           | 121     | +7.0%  | +8.6%  | -21.6% |
| ASIAN - CHINESE                | 581     | -7.9%  | -7.9%  | -16.1% |
| ASIAN - SOUTH EAST ASIAN       | 179     | -4.0%  | +9.7%  | -12.4% |
| BLACK/AFRICAN                  | 408     | -6.3%  | -4.1%  | -4.7%  |
| BLACK/AFRICAN AMERICAN         | 6105    | -1.2%  | +0.2%  | -9.6%  |
| BLACK/CAPE VERDEAN             | 612     | -4.9%  | +4.9%  | -7.8%  |
| BLACK/CARIBBEAN ISLAND         | 272     | -11.4% | +6.5%  | -7.1%  |
| HISPANIC OR LATINO             | 250     | +11.7% | +0.9%  | -15.6% |
| HISPANIC/LATINO - DOMINICAN    | 620     | +0.3%  | -1.0%  | -17.4% |
| HISPANIC/LATINO - GUATEMALAN   | 215     | +2.9%  | -4.2%  | -1.7%  |
| HISPANIC/LATINO - HONDURAN     | 119     | -5.5%  | +22.0% | +10.7% |
| HISPANIC/LATINO - MEXICAN      | 104     | +10.4% | -12.9% | -3.6%  |
| HISPANIC/LATINO - PUERTO RICAN | 1404    | +2.9%  | -2.9%  | -11.8% |
| HISPANIC/LATINO - SALVADORAN   | 135     | +2.0%  | +1.7%  | -16.2% |
| OTHER                          | 1722    | +1.8%  | -5.4%  | -8.7%  |
| PORTUGUESE                     | 103     | -6.3%  | -2.6%  | +57.4% |
| UNKNOWN                        | 282     | +12.9% | +21.7% | -2.0%  |
| WHITE                          | 19320   | +0.9%  | +0.8%  | +10.2% |
| WHITE - BRAZILIAN              | 156     | +6.3%  | -7.5%  | -29.3% |
| WHITE - EASTERN EUROPEAN       | 119     | -2.4%  | +13.8% | -13.2% |
| WHITE - OTHER EUROPEAN         | 801     | -7.4%  | -1.4%  | +23.1% |
| WHITE - RUSSIAN                | 622     | -2.2%  | +6.0%  | +15.8% |

> Race 类别较多，且部分小组样本有限；当前主要作为探索性结果。Ethnicity 在冻结输入中没有独立可用字段。

## 5. ESI subgroup

| Subgroup     | N stays | HR     | MAP    | SpO2   |
|:------------ | -------:|:------ |:------ |:------ |
| High (1–2)   | 14258   | +2.1%  | +8.8%  | +16.8% |
| Moderate (3) | 19331   | -1.6%  | -6.2%  | -13.2% |
| Low (4–5)    | 1599    | +1.6%  | -18.5% | -12.1% |
| Unknown      | 161     | +12.2% | +21.7% | -7.8%  |

**主要观察：**

- High（ESI 1–2）：MAP、SpO₂ forecasting error 明显更高。
- Moderate（3）：三个变量整体并没有同方向变差。
- 因此 MIMIC forecasting 的 ESI 弱点更偏向 **高危患者**，这与 MC-MED risk 分析中 ESI 3 较弱并不完全一致。

## 6. Arrival mode

| Subgroup        | N stays | HR     | MAP    | SpO2   |
|:--------------- | -------:|:------ |:------ |:------ |
| Ambulance / EMS | 13414   | -11.2% | +3.7%  | +14.4% |
| Walk-in / Self  | 21414   | +12.3% | -4.3%  | -12.8% |
| Other / Unknown | 521     | +4.2%  | +15.9% | +10.3% |

**主要观察：**

- Ambulance / EMS：MAP 与 SpO₂ 更难预测。
- Walk-in / Self：HR 更难预测。
- Other / Unknown 样本较少，仅作描述性观察。

## 7. Measurement process：Total density（测量过程：总观测密度）

| Subgroup  | N stays | HR    | MAP   | SpO2  |
|:--------- | -------:|:----- |:----- |:----- |
| Q1 sparse | 8617    | -3.0% | -2.3% | -2.0% |
| Q2        | 8711    | -0.1% | -1.0% | -0.6% |
| Q3        | 9001    | -0.9% | +0.7% | -0.0% |
| Q4 dense  | 9020    | +3.8% | +2.3% | +2.3% |

这里信号非常清楚：**Q4 dense 在 HR / MAP / SpO₂ 三个变量上均表现更差**。

## 8. Per-variable observation density（单变量观测密度）

### HR density

| Subgroup  | N stays | HR    | MAP   | SpO2  |
|:--------- | -------:|:----- |:----- |:----- |
| Q1 sparse | 8611    | -4.1% | -1.7% | -2.8% |
| Q2        | 8727    | -0.5% | -2.1% | -0.5% |
| Q3        | 8993    | -0.6% | +0.5% | -0.5% |
| Q4 dense  | 9018    | +4.8% | +2.9% | +3.3% |

### SpO₂ density

| Subgroup  | N stays | HR    | MAP   | SpO2  |
|:--------- | -------:|:----- |:----- |:----- |
| Q1 sparse | 8622    | -2.2% | -1.1% | -1.7% |
| Q2        | 8719    | -0.8% | -2.2% | -1.7% |
| Q3        | 8991    | -1.0% | +0.8% | +0.5% |
| Q4 dense  | 9017    | +3.7% | +2.3% | +2.5% |

### SBP density

| Subgroup  | N stays | HR    | MAP   | SpO2  |
|:--------- | -------:|:----- |:----- |:----- |
| Q1 sparse | 8625    | -3.2% | -2.0% | -1.8% |
| Q2        | 8719    | -0.3% | -2.2% | -1.3% |
| Q3        | 8978    | -0.5% | +1.1% | -0.3% |
| Q4 dense  | 9027    | +3.7% | +2.7% | +2.9% |

### DBP density

| Subgroup  | N stays | HR    | MAP   | SpO2  |
|:--------- | -------:|:----- |:----- |:----- |
| Q1 sparse | 8629    | -2.9% | -2.3% | -1.9% |
| Q2        | 8714    | -0.6% | -1.9% | -1.7% |
| Q3        | 8980    | -0.5% | +1.1% | -0.0% |
| Q4 dense  | 9026    | +3.6% | +2.7% | +3.1% |

### RR density

| Subgroup  | N stays | HR    | MAP   | SpO2  |
|:--------- | -------:|:----- |:----- |:----- |
| Q1 sparse | 8629    | -3.1% | -1.7% | -1.1% |
| Q2        | 8716    | -0.5% | -2.0% | -1.6% |
| Q3        | 8982    | -0.6% | +0.6% | -0.3% |
| Q4 dense  | 9022    | +3.9% | +2.8% | +2.6% |

整体上，各类生命体征的 **Q4 dense** 都呈现一致的误差升高趋势，是 MIMIC-IV-ED 最值得继续验证的 measurement-process failure candidate。

## 9. Missing-pattern subgroup（缺失模式子集）

| Subgroup                               | N stays | HR      | MAP    | SpO2   |
|:-------------------------------------- | -------:|:------- |:------ |:------ |
| all required forecast channels present | 34986   | -15.7%  | -1.2%  | +14.5% |
| missing HR                             | 11      | +nan%   | -32.9% | -14.7% |
| missing MAP                            | 145     | +18.1%  | +nan%  | -12.8% |
| missing SpO2                           | 215     | +18.5%  | +3.1%  | +nan%  |
| multiple required channels missing     | 4       | +119.4% | +23.7% | +19.9% |

注意：

- missing SpO₂：N=215；
- missing MAP：N=145；
- missing HR：N=11；
- multiple missing：N=4。

因此除 “all required channels present” 外，大部分缺失模式样本较小，只适合探索性报告。

## 10. 每个模型最弱 subgroup（最弱子集）

| Model       | Domain      | Worst subgroup                                          | Metric                                 | Relative degradation | N stays | N observations | Status      |
|:----------- |:----------- |:------------------------------------------------------- |:-------------------------------------- |:-------------------- | -------:| --------------:|:----------- |
| Chronos-2   | population  | Race: PORTUGUESE                                        | relative MAE degradation vs complement | +61.4%               | 101     | 231            | DESCRIPTIVE |
| Chronos-2   | clinical    | HR threshold distance: Q1 sparse                        | relative MAE degradation vs complement | +81.7%               | 8949    | 23571          | DESCRIPTIVE |
| Chronos-2   | measurement | Missing pattern: missing MAP                            | relative MAE degradation vs complement | +24.9%               | 145     | 311            | DESCRIPTIVE |
| MIRA        | population  | Race: PORTUGUESE                                        | relative MAE degradation vs complement | +61.5%               | 101     | 231            | DESCRIPTIVE |
| MIRA        | clinical    | HR threshold distance: Q1 sparse                        | relative MAE degradation vs complement | +79.9%               | 8949    | 23571          | DESCRIPTIVE |
| MIRA        | measurement | Missing pattern: missing SpO2                           | relative MAE degradation vs complement | +23.9%               | 215     | 536            | DESCRIPTIVE |
| Time-MoE    | population  | Race × Gender: UNKNOWN Female                           | relative MAE degradation vs complement | +93.8%               | 118     | 327            | DESCRIPTIVE |
| Time-MoE    | clinical    | ESI: Unknown                                            | relative MAE degradation vs complement | +111.3%              | 161     | 592            | DESCRIPTIVE |
| Time-MoE    | measurement | Missing pattern: all required forecast channels present | relative MAE degradation vs complement | +19.1%               | 33905   | 80964          | DESCRIPTIVE |
| Sundial     | population  | Race: PORTUGUESE                                        | relative MAE degradation vs complement | +61.9%               | 101     | 231            | DESCRIPTIVE |
| Sundial     | clinical    | HR threshold distance: Q1 sparse                        | relative MAE degradation vs complement | +80.2%               | 8949    | 23571          | DESCRIPTIVE |
| Sundial     | measurement | Missing pattern: missing MAP                            | relative MAE degradation vs complement | +24.0%               | 145     | 311            | DESCRIPTIVE |
| TimesFM 3.0 | population  | Race: HISPANIC/LATINO - HONDURAN                        | relative MAE degradation vs complement | +62.0%               | 113     | 267            | DESCRIPTIVE |
| TimesFM 3.0 | clinical    | ESI: Unknown                                            | relative MAE degradation vs complement | +78.6%               | 155     | 541            | DESCRIPTIVE |
| TimesFM 3.0 | measurement | Missing pattern: all required forecast channels present | relative MAE degradation vs complement | +27.3%               | 33905   | 80964          | DESCRIPTIVE |
| Timer       | population  | Race: PORTUGUESE                                        | relative MAE degradation vs complement | +62.5%               | 101     | 231            | DESCRIPTIVE |
| Timer       | clinical    | HR threshold distance: Q1 sparse                        | relative MAE degradation vs complement | +80.8%               | 8949    | 23571          | DESCRIPTIVE |
| Timer       | measurement | Missing pattern: missing SpO2                           | relative MAE degradation vs complement | +19.2%               | 215     | 536            | DESCRIPTIVE |
| LightGTS    | population  | Race: PORTUGUESE                                        | relative MAE degradation vs complement | +64.1%               | 101     | 231            | DESCRIPTIVE |
| LightGTS    | clinical    | HR threshold distance: Q1 sparse                        | relative MAE degradation vs complement | +81.9%               | 8949    | 23571          | DESCRIPTIVE |
| LightGTS    | measurement | Missing pattern: missing SpO2                           | relative MAE degradation vs complement | +22.2%               | 215     | 536            | DESCRIPTIVE |
| VisionTS    | population  | Race: PORTUGUESE                                        | relative MAE degradation vs complement | +65.5%               | 101     | 231            | DESCRIPTIVE |
| VisionTS    | clinical    | HR threshold distance: Q1 sparse                        | relative MAE degradation vs complement | +81.2%               | 8949    | 23571          | DESCRIPTIVE |
| VisionTS    | measurement | Missing pattern: missing MAP                            | relative MAE degradation vs complement | +22.5%               | 145     | 311            | DESCRIPTIVE |

> 该表按每个模型在 population / clinical / measurement 三个 domain 中最大的 relative MAE degradation 选取。部分 subgroup 的 N 较小，因此保留原始 `Status`，不要把描述性 worst group 当成稳定机制结论。

## 11. Common forecasting-failure candidates（共同预测误差失败候选子集）

冻结结果中出现大量 **≥5/8 模型同方向**的 forecasting error subgroup。最值得汇报的几个是：

- **Age 18–44 / HR：8/8**
- **Age × Gender 18–44 Male / HR：8/8**
- **Age ≥80 / MAP：8/8**
- **Age ≥80 / SpO₂：8/8**
- **ESI High (1–2) / MAP：8/8**
- **ESI High (1–2) / SpO₂：8/8**
- **Total density Q4 / HR：8/8**
- **Total density Q4 / MAP：7/8**
- **Total density Q4 / SpO₂：7/8**
- HR / SBP / DBP / RR / SpO₂ 各通道的 **Q4 dense** 也普遍出现 7/8–8/8 同向退化。

这些是 **forecasting-error candidate common failures**，不是 risk-AUROC failure。

## 11A. LOCF 复核：这些 forecasting subgroup 差异是不是模型特有？

原来的 Age、Gender、ESI、Arrival、density 表先保留不变。新增 LOCF 参照后，需要进一步区分：

- **如果模型和 LOCF 在同一 subgroup 都变差，而且幅度接近**：更像是该 subgroup 的体征本身更难预测；
- **如果模型相对 LOCF 额外变差**：才更像是 TSFM 在该 subgroup 上多吃亏。

### 11A.1 MIMIC-IV-ED：子集相对补集的 MAE 差（8 模型平均 / LOCF）

| 子集             | HR              | MAP           | SpO₂            |
| -------------- | --------------- | ------------- | --------------- |
| <65 岁          | +20.1% / +20.2% | −5.5% / −5.6% | −19.7% / −19.4% |
| ≥75 岁          | −15.7% / −15.7% | +8.1% / +8.1% | +18.0% / +15.8% |
| ≥80 岁          | −15.9% / −16.0% | +8.1% / +9.0% | +20.8% / +19.4% |
| 男性             | +1.6% / +0.3%   | −4.7% / −4.6% | +4.9% / +4.1%   |
| ESI 1–2        | −2.1% / −7.0%   | +4.6% / +2.3% | +16.1% / +12.4% |
| 急救车或直升机送达      | −11.9% / −11.8% | +2.1% / +2.3% | +16.3% / +15.4% |
| vitalsign ≤1 次 | +6.3% / +22.1%  | +1.3% / +9.8% | −10.4% / −5.8%  |
| vitalsign >1 次 | −4.9% / −18.1%  | −0.2% / −9.0% | +12.8% / +6.2%  |
| 2 h 内已越阈       | +65.8% / +50.2% | +8.1% / +5.6% | +36.0% / +32.6% |

### 11A.2 读法

1. **年龄、性别、ESI、到达方式的大部分误差差异，LOCF 也会出现，而且幅度很接近。**  
   例如 <65 岁 HR 为 +20.1% / +20.2%，≥80 岁 SpO₂ 为 +20.8% / +19.4%。因此原来“8/8 同向”的现象不能直接解释成 TSFM 特有 failure。

2. **模型相对 LOCF 额外吃亏的地方，主要出现在上下文并非完全平直的就诊。**  

   - vitalsign >1 次：HR 的模型 MAE / LOCF MAE 中位数为 1.129，补集 1.009，8/8 模型更高；
   - 2 h 内已越阈：HR 为 1.114 vs 1.019，8/8 模型更高；
   - ESI 1–2：HR 为 1.060 vs 1.021，8/8 模型更高。

3. 因此原来的 **18–44、18–44 Male、Q4 dense** 仍可保留为“原始描述性现象”，但加入 LOCF 后，不再把它们直接称为“TSFM 特有共同失败”。

## 12. MIMIC-IV-ED：D103 Risk Subgroup（D103 风险子集）

### 12.0 正式判据

在原来的“至少 5/8 模型同方向”描述性筛查之外，本版增加正式统计复核：

- subgroup 与 complement 都需要有足够事件数；
- 计算 `AUROC_subgroup − AUROC_complement`；
- 按患者聚类 bootstrap（B=1000）计算 95% CI；
- 在每个“模型 × 分数 × 标签”内部做 Holm 多重校正；
- 只有 **95% CI 上限 < 0 且 Holm 校正后 p < 0.05**，才作为“表现显著更差”的主结论。

同时加入三个参照：

- **LOCF**：最后一个观测值向前延伸；
- **Context-max**：直接看上下文中最异常的值；
- **监督模型**：LR、LightGBM、BRITS、mTAND、Raindrop，仅用于判断某个 subgroup 是不是“本身就难”。

### 12.1 正式统计复核

本表使用正式判据复核 D103 风险子集；Time-MoE 主结果按 official normalization 解释，冻结路径只作复现记录。

| 子集                       | N / 事件（患病率）          | 七个零样本模型的 AUROC 差                         | 判为差的零样本                               | 五个监督模型的 AUROC 差              | 判为差的监督            | 归类                         |
| ------------------------ | -------------------- | ---------------------------------------- | ------------------------------------- | ---------------------------- | ----------------- | -------------------------- |
| vitalsign ≤1 次 × ESI 1–2 | 9,167 / 466（5.1%）    | −0.056 到 −0.080                          | 全部（含 LOCF、Context-max、Time-MoE）       | −0.195 到 −0.235              | 全部                | **子集本身难**（最差的格子）           |
| vitalsign ≤1 次           | 29,083 / 613（2.1%）   | −0.009 到 −0.036                          | MIRA、Sundial、Chronos-2（及 Context-max） | −0.041 到 −0.077              | 全部                | 子集本身难                      |
| 2 h 内未越阈                 | 33,396 / 1,178（3.5%） | 组内 AUROC 0.499–0.507（TimesFM 0.551）      | MIRA、Sundial、Chronos-2、Context-max    | −0.029 到 −0.054              | 全部                | 零样本侧是规则退化；监督模型也差，同时也是子集本身难 |
| ≥75 岁                    | 6,810 / 664（9.8%）    | −0.021 到 −0.029（3 个模型区间上限 <0，Holm 后都不显著） | 无                                     | −0.027 到 −0.032（区间上限都 <0）    | LightGBM、Raindrop | 监督模型达到判据；零样本同向但未达到         |
| ≥80 岁                    | 4,710 / 485（10.3%）   | −0.020 到 −0.033                          | 无                                     | −0.030 到 −0.039              | mTAND、Raindrop    | 同上                         |
| 非呼吸系统主诊断                 | 35,830 / 1,802（5.0%） | −0.007 到 −0.045                          | 无                                     | −0.034 到 −0.049              | 除 mTAND 外 4 个     | 只有监督模型差（相对较小的呼吸系统组）        |
| vitalsign >1 次 × ESI 3–5 | 2,690 / 93（3.5%）     | −0.028 到 +0.009                          | 只有 Time-MoE 冻结路径                      | −0.065 到 −0.088              | LR、Raindrop       | 只有监督模型差                    |
| 急救车或直升机送达                | 14,102 / 1,348（9.6%） | −0.023 到 −0.005                          | 无                                     | −0.019 到 −0.034              | Raindrop          | 只有监督模型差                    |
| 男性                       | 17,062 / 1,084（6.4%） | −0.020 到 −0.004                          | 无                                     | −0.014 到 −0.008              | 无                 | 不差                         |
| ESI 3（对 ESI 1–2）         | 20,562 / 214         | 组内 0.593–0.624，对 0.607–0.620             | 无                                     | 组内 0.785–0.804，对 0.794–0.826 | 无                 | 不差                         |
| ESI 4–5                  | 1,970 / <10          | —                                        | —                                     | —                            | —                 | 事件不足，只描述                   |

补充：

- **Simpson 现象。** ESI 1–2 与 ESI 3–5 两组的组内 AUROC（零样本 0.596–0.627）都低于总体（0.617–0.638）。总体判别有一部分来自两组之间的患病率差（11.4% 对 0.95%），密度分组也有同样的情况。
- **Time-MoE 冻结路径的子集方向与其他模型相反**：≤1 次组更好（+0.048），>1 次组更差。这与 本部分末尾的 Time-MoE 归一化审计 一致：它的分数不是越阈预测。

### 12.2 原始方向性筛查（保留追溯）

下面保留原始 R-max 中“至少 5/8 模型 ΔAUROC<0”的方向性筛查，作为追溯材料；它不等同于正式统计显著：

| Subgroup                 | Models with ΔAUROC<0 | Mean ΔAUROC | Legacy worse flags |
|:------------------------ |:-------------------- | -----------:|:------------------ |
| age60 = >=60             | 8/8                  | -0.015      | 0/8                |
| arrival = 急救车/直升机送达      | 8/8                  | -0.015      | 0/8                |
| sex = 男                  | 8/8                  | -0.015      | 0/8                |
| age_1106 = >=75          | 8/8                  | -0.026      | 0/8                |
| age = >=80               | 8/8                  | -0.027      | 0/8                |
| dx_resp = 非呼吸系统主诊断       | 8/8                  | -0.028      | 0/8                |
| density_x_esi = <=1      | ESI 3-5              | 8/8         | -0.038             |
| density_x_esi = <=1      | ESI 1-2              | 8/8         | -0.079             |
| arrival = 其他/未知          | 7/8                  | -0.007      | 0/8                |
| esi3 = ESI 3             | 7/8                  | -0.015      | 0/8                |
| density = <=1            | 7/8                  | -0.017      | 3/8                |
| esi = ESI 3-5            | 6/8                  | -0.005      | 0/8                |
| early_abnormal = 2h 内未越阈 | 6/8                  | -0.022      | 3/8                |
| density_x_esi = >1       | ESI 3-5              | 5/8         | -0.025             |

最明显的是：

- `density_x_esi = <=1 | ESI 1-2`：8/8，平均 ΔAUROC ≈ -0.079；
- `age >=80`：8/8，平均 ΔAUROC ≈ -0.027；
- `density <=1`：7/8，平均 ΔAUROC ≈ -0.017；
- `sex = male`：8/8，平均 ΔAUROC ≈ -0.015；
- `arrival = ambulance/helicopter`：8/8，平均 ΔAUROC ≈ -0.015。

**重要：D103 是另一 outcome task，不是 MC-MED decomp_60 的外部验证。**

## 13. MC-MED vs MIMIC-IV-ED：当前最重要的对照

| Subgroup / axis         | MC-MED                                                 | MIMIC-IV-ED                                                       | Cross-dataset reading         |
|:----------------------- |:------------------------------------------------------ |:----------------------------------------------------------------- |:----------------------------- |
| Age 18–44               | MC-MED: 5/8 ΔAUROC<0 candidate                         | MIMIC: HR MAE higher in 8/8; MAP/SpO₂ not same direction          | Partial / variable-specific   |
| Age × Gender 18–44 Male | MC-MED: 5/8 ΔAUROC<0 candidate                         | MIMIC: HR MAE higher in 8/8; MAP/SpO₂ not same direction          | Partial / variable-specific   |
| Dense measurement       | MC-MED: MAP density Q4 dense, 5/8 ΔAUROC<0             | MIMIC: total Q4 HR 8/8; MAP/SpO₂ 7/8 higher MAE                   | Forecast-error candidate      |
| Age ≥80                 | MC-MED: average weakest age by R-max ΔAUROC_complement | MIMIC: MAP/SpO₂ MAE higher in 8/8; D103 ΔAUROC<0 in 8/8           | Converging descriptive signal |
| Gender                  | MC-MED: Female average weakest                         | MIMIC forecasting: Male overall weaker; D103 male ΔAUROC<0 in 8/8 | Not consistent                |
| ESI                     | MC-MED: Moderate (3) weakest stable risk subgroup      | MIMIC forecasting: High (1–2) highest avg degradation             | Not directly consistent       |

### 当前可用的结论

1. **18–44**：MC-MED 中是 5/8 risk common-failure candidate；MIMIC-IV-ED 中 HR forecasting 为 8/8 同向变差，但 MAP / SpO₂ 不一致，因此属于 **部分复现**。
2. **18–44 Male**：同样只在 MIMIC HR 上形成 8/8 同向误差升高，因此也是 **变量特定的部分复现**。
3. **Dense measurement**：两个数据集都出现值得注意的信号。MC-MED 为 MAP density Q4 dense；MIMIC 则 total / HR / SBP / DBP / RR / SpO₂ 的 Q4 dense 广泛变差。这是目前最值得继续追踪的 **跨数据集 measurement-process candidate**。
4. **≥80**：MC-MED 平均年龄组结果较弱；MIMIC 的 MAP / SpO₂ 以及旧 D103 risk 也出现较弱信号，是第二个值得保留的跨库候选。
5. Gender 和 ESI 的两库结果目前 **不够一致**，暂时不应写成跨库共同 failure。

### 13.1 加入 LOCF、监督模型和正式判据后的补充判断

| 现象                 | MIMIC-IV-ED                                    | MC-MED                  | 当前判读                                  |
| ------------------ | ---------------------------------------------- | ----------------------- | ------------------------------------- |
| ≥75 岁排序更差（监督模型）    | 五个监督模型均为负向，2 个达到正式判据                           | 五个监督模型均为负向，1 个达到正式判据    | **目前最稳定的跨库 subgroup 信号**              |
| 18–44 / 18–44 Male | HR forecasting 原始误差较高，但 LOCF 也几乎同方向            | 旧 R-max 方向性筛查中出现        | **保留为探索性现象，不再称 TSFM 特有复现**            |
| Dense measurement  | 原始 Q4 dense forecasting error 较高               | 旧 MAP Q4 dense 方向性筛查出现  | **LOCF/正式判据后证据不足，保留探索性**              |
| 稀疏窗口 × 高 ESI       | D103 中 `vitalsign ≤1 × ESI 1–2` 对零样本和监督模型都明显更差 | MC-MED 当前没有完全可对齐的同样稳定结果 | **更像 subgroup 本身困难，而不是 zero-shot 特有** |
| 性别                 | 风险分正式判据不支持男性是稳定弱组                              | MC-MED 旧描述性结果偏 Female   | **两库不一致**                             |
| ESI                | D103 最突出的是 sparse × ESI 1–2                    | MC-MED 旧描述性结果偏 ESI 3    | **任务口径不同，不作共同 failure**               |

**因此，两库对照的主结论应更新为：**

- 原先的 18–44、18–44 Male、dense measurement 仍是值得记录的**描述性现象**；
- 但加入 LOCF 和正式统计后，不能把它们直接解释成 TSFM 特有共同失败；
- 当前更稳定的跨库信号是 **≥75 岁排序更差（主要由监督参照支持）**；
- MIMIC-IV-ED 中最突出的 D103 subgroup 是 **vitalsign ≤1 次 × ESI 1–2**，但监督模型同样更差，因此更像“这个 subgroup 本身难”。

## 14. 当前不能强结论的部分

- Race：原始类别过细，暂未建立两库共享 mapping。
- Ethnicity：MIMIC 冻结输入中没有独立字段。
- Chief complaint：有原字段，但没有冻结 mapping，因此暂不做性能比较。
- Monitor / Chart：MIMIC 的 Source 不能可靠对应 MC-MED 的 Monitor / Chart。
- MIMIC 没有原始 MAP channel；当前 benchmark 中 MAP 为派生变量，measurement-density 对照使用原始 SBP / DBP / HR / SpO₂ / RR。
- Forecasting MAE 与 D103 risk AUROC 是两种不同任务，必须分开解释。

## 15. 一句话总结

**MIMIC-IV-ED 中最稳定的共同 forecasting failure 信号集中在年龄相关的变量特定误差（18–44 的 HR、≥80 的 MAP/SpO₂）以及高 observation density（Q4 dense）；其中 dense-measurement failure 与 MC-MED 的 MAP-density Q4 candidate 最接近，最值得下一阶段做跨数据集归因。**

> **补充解释（以新增复核为准）：** 原始表中“18–44、18–44 Male、Q4 dense”等仍保留作为描述性结果；但 LOCF 也能复现其中大部分误差差异，因此当前不把它们直接表述为 TSFM 特有 common failure。

---

## 16. Time-MoE normalization audit（归一化审计）

| 量                       | MIMIC-IV-ED                   | MC-MED                        |
| ----------------------- | ----------------------------- | ----------------------------- |
| 第 1 步预测减最后一个值（平均）       | HR +32.1、MAP +32.6、SpO₂ +14.2 | HR +33.4、MAP +29.9、SpO₂ +14.1 |
| SpO₂ 预测超过 100 的序列比例     | 99.9%                         | 100%                          |
| 总体 HR MAE（冻结 → 官方归一化）   | 17.02 → 11.04                 | 7.31 → 4.82                   |
| R-max AUROC（冻结 → 官方归一化） | D103 0.720 → 0.618            | 0.600 → 0.500                 |

冻结路径的输出整体上抬，HR 分量在大量上下文正常的就诊上也越过 110，风险分实际上变成了心率水平和上下文波动的某种组合，不是"预测轨迹越阈"的能力。因此本部分解释 Time-MoE 时以 official normalization 为准；冻结路径仅保留为复现记录。

---

---

# 附录

## 附录 A：8 个已运行模型的详细记录（上下文长度、预训练数据、缺失/不规则支持等）

### MIRA

- **论文 / 来源**：MIRA: Medical Time Series Foundation Model for Real-World Health Data（Hao Li … Jiang Bian，Microsoft Research）arXiv 2506.07584
- **年份**：2025
- **会议 / 期刊**：NeurIPS 2025
- **是否开源 / 代码**：是：github.com/microsoft/MIRA
- **公开 checkpoint**：论文与 README 未给出权重地址（README 推理示例用占位 ckpt_path）：Not reported。尺寸 small 73M / base 114M / large 455M 总参（激活 30M/50M/200M，Table 1）
- **Native task（原生任务）**：零样本点预测：给定 (值, 时间戳) 序列，预测目标时间戳处的值（Sec 3.1 Eq 1）；Huber 多步损失（Sec 3.3）；单变量、通道独立；只报告 RMSE/MAE，无概率输出（Sec 4.1）
- **Pretraining data**：MIMIC-III 400B（88.06%）、MIMIC-IV 48B（10.57%）、WAVES 4.8B（1.06%）、PTB-XL 1.3B（0.29%）、Sleep-EDF 0.14B（0.03%）（Table 7，App E）；并从 Time-MoE checkpoint 续训（Sec 3.3），即间接继承 Time-300B 的通用预训练
- **Scale**：454B 时间点（Abstract、Table 7）
- **Medical data**：Yes
- **医疗数据明细（论文原文）**：所列语料全部为医疗：MIMIC-III（ICU，>40,000 患者，生命体征与化验）、MIMIC-IV（App E 写 'covering ICU and emergency department admissions'）、WAVES（儿科 ICU/手术室波形）、PTB-XL（12 导联 ECG，100 Hz）、Sleep-EDF（睡眠 EEG/呼吸，100 Hz）。Sec 3.3 另称含流行病监测与心理健康数据，但 Table 7 无对应来源（论文内部不一致）
- **ICU seen?**：Yes（MIMIC-III、WAVES，App E）
- **ED seen?**：不明确：App E 称 MIMIC-IV 覆盖 ICU 与急诊入院，但未说明是否使用 MIMIC-IV-ED 模块；不能算明确见过 ED 时序
- **生命体征 seen?**：Yes（MIMIC-III 生命体征，App E）；采样频率 Not reported
- **预训练含不规则采样?**：Yes：App E 称 MIMIC-III 'irregular sampling patterns and substantial missingness'；是否重采样 Not reported
- **预训练频率范围**：仅 PTB-XL、Sleep-EDF 写明 100 Hz；MIMIC 与 WAVES 频率 Not reported
- **Time scale 判断**：Medium（证据有限）
- **Time scale 依据**：最大序列长度 512 个点（Sec 3.3、App F、Table 6，未说明是否含预测段）；点级 token、无 patch（Table 6）；评价预测长度 24/32/48/64（App F）；全文无上下文长度实验
- **Context length**：≤512 点（Table 6）；README 示例 history=12
- **Forecast horizon**：24 / 32 / 48 / 64（App F）
- **Irregular support**：原生支持：输入 (x_i, t_i)，'Timestamps t_i follow non-uniform intervals'（Sec 3.1）；CT-RoPE 用连续时间做旋转位置编码（Eq 2），时间戳按序列 min-max 缩放（App B Eq 15）；Neural ODE 在时间戳之间演化并外推到任意目标时间（Sec 3.2.3，Eq 9–10）
- **Missing support**：公式允许 x_i 为 NaN（Sec 3.1），评价只计未遮蔽点（App I）；推理时模型内部如何处理 NaN / mask：Not reported（README 数据格式有 mask 字段，推理示例没有）
- **Zero-shot type**：Zero-shot forecasting（不是 zero-shot 临床结局预测）
- **Zero-shot 细节（排除 / 归一化 / 头）**：'evaluated directly without any task-specific training or fine-tuning'（Sec 4.2）。OOD：CinC 2012、Heart Rate（PPG）、MIT-BIH、CDC-IHA、JH COVID-19、ILI（Table 2；正文说 7 个，表里 6 个）；ID：预训练源的留出部分（Table 3，切分细节 Not reported）。CinC 2012 与 MIMIC 的重叠未讨论；数值归一化 Not reported（README 用输入均值/标准差 z-score）
- **Subgroup analysis**：只按数据集（Tables 2–3）；按频率只有专家激活的定性图（Fig 3）；无患者 / 变量 / 预测长度分层
- **Robustness**：Table 4：WHO FluNet 零样本，缺失率 10%→90%，MIRA-large RMSE 2.85→3.97（不单调）；'不规则'只用一种 30% 随机遮蔽模拟（Sec 4.1）；噪声、重采样：Not reported
- **Domain shift**：OOD（Table 2）vs ID（Table 3）；Table 2 中在医疗语料上续训的通用基线优于其原版；没有'去掉医疗预训练'的 MIRA 消融
- **Context-length analysis**：Not reported（正文与附录 A–I 均无上下文 / 历史长度实验）
- **作者自述局限 / 已知问题**：Sec 5 只说公开去标识数据 'may not fully reflect the complexities of real-world clinical deployment'。正文说 'best results on all datasets'，但 Table 2 首位计数 MIRA-large 为 4/6（RMSE）；ILI 上 RMSE 1.154 vs T-PatchGNN 0.195；PTB-XL 上 Time-MoE 优于 MIRA（Table 3）
- **与本项目已有结果的关联**：week02 F1：MIRA 见过 MIMIC 也没在零样本生命体征预测中领先；GAM→GD v1.0：MIRA 冻结嵌入 AUROC 0.609（最低）；合作摘要 MC-MED decomp_60：MIRA-Large AUPRC 0.218（XGBoost 0.317；N=1,328、事件率 16.87%，非严格排名）
- **阅读范围**：正文 + 附录 A–I（arXiv v7，逐段原文）

### Time-MoE

- **论文 / 来源**：Time-MoE: Billion-Scale Time Series Foundation Models with Mixture of Experts（Xiaoming Shi … Ming Jin）arXiv 2409.16040
- **年份**：2025（arXiv 2024-09）
- **会议 / 期刊**：ICLR 2025（README 标注 Spotlight）
- **是否开源 / 代码**：是：github.com/Time-MoE/Time-MoE（Apache-2.0）
- **公开 checkpoint**：Maple728/TimeMoE-50M、Maple728/TimeMoE-200M（README）；ultra 2.4B 未见公开。激活/总参：50M/113M、200M/453M、1.1B/2.4B（Table 2）
- **Native task（原生任务）**：解码器自回归点预测；多分辨率预测头 {1,8,32,64}（Sec 3.1）；Huber + 负载均衡辅助损失（Eq 9–11）；通道独立；无协变量（README TODO）
- **Pretraining data**：Time-300B：Nature 279.7B（90.50%）、Energy 16.0B（5.17%）、Synthetic 9.22B（2.98%）、Transport 0.69%、Web 0.58%、Sales 0.008%、Healthcare 0.0001%、Finance 0.0001%（Table 1）
- **Scale**：309.09B 观测 / 48.2M 序列（Table 1）；训练实际消耗约 117B（App C）
- **Medical data**：Partial
- **医疗数据明细（论文原文）**：Healthcare 471,040 观测（0.0001%，1,752 条序列，Table 1）：COVID Deaths（日）、Hospital（月）、CDC FluView ILINet（周）、WHO NREVSS（周）、Project Tycho（周）、US Births（日）（Table 10）。均为公共卫生 / 医院汇总计数，不是床旁生理数据
- **ICU seen?**：No（Table 10 可读部分未见）
- **ED seen?**：No
- **生命体征 seen?**：No
- **预训练含不规则采样?**：Not reported（清洗时在 NaN/inf 处切分子序列，App C）
- **预训练频率范围**：4 秒（Solar Power）至年（Tourism Yearly）（Table 10）
- **Time scale 判断**：Long-context oriented
- **Time scale 依据**：训练最大序列 4096（上下文 + 预测，Sec 3.2.3、Table 8）；零样本评价输入长度 512/1024/2048/3072 分别配预测 96/192/336/720（Sec 4.1）
- **Context length**：≤4096（含预测段）
- **Forecast horizon**：评价 96 / 192 / 336 / 720
- **Irregular support**：不支持：输入只有点值 x_t，无时间戳（Eq 1）；规则网格为隐含前提
- **Missing support**：仅数据清洗层面：在缺失处切分、丢弃一阶/二阶差分为零比例 >0.2 的窗口（App C）；模型层面 NaN / mask：Not reported
- **Zero-shot type**：Zero-shot forecasting
- **Zero-shot 细节（排除 / 归一化 / 头）**：6 个 'not included in the pre-training corpora' 的基准：ETTh1/h2/m1/m2、Weather、Global Temp（Sec 4.1）；泄漏核查 Not reported（Table 10 含 Weather 与 WeatherBench 条目）；README 用上下文均值/标准差 z-score
- **Subgroup analysis**：按数据集 × 预测长度（Tables 3–4）；无领域 / 频率分层
- **Robustness**：Not reported（文中 'sparse' 指 MoE 稀疏激活，不是稀疏观测）
- **Domain shift**：零样本 vs 训练集上微调 1 epoch（Table 3 vs Table 4）
- **Context-length analysis**：Not reported（输入长度随预测长度一起变，未单独消融）
- **作者自述局限 / 已知问题**：无 Limitations 节；Sec 3.2.1：'data quality still remains a challenge, with prevalent issues such as missing values and invalid observations'；README：更长序列需自行微调
- **与本项目已有结果的关联**：MIRA 从 Time-MoE 初始化，二者结论应一起看
- **阅读范围**：正文 + App B/C（Table 10 后半与 App D 未读到）

### Sundial

- **论文 / 来源**：Sundial: A Family of Highly Capable Time Series Foundation Models（Yong Liu, Guo Qin … Mingsheng Long，清华 THUML）arXiv 2502.00816
- **年份**：2025
- **会议 / 期刊**：ICML 2025（README 标注 Oral）
- **是否开源 / 代码**：是：github.com/thuml/Sundial（Apache-2.0）
- **公开 checkpoint**：thuml/sundial-base-128m（Sec 5.1 脚注）；Small 32M / Base 128M / Large 444M（Table 5）
- **Native task（原生任务）**：零样本概率预测（生成多条样本）+ 点预测；TimeFlow 损失（条件流匹配，Sec 4.1.3）；单变量预训练，无协变量（App E）
- **Pretraining data**：TimeBench：ERA5 各分辨率合计 643B（62.3%）、LOTSA 230B（22.3%）、Chronos 数据 94B（9.1%）、ECG 48B（4.65%）、Finance 1.0%、IoT 0.56%、合成 0.05%（Table 4）
- **Scale**：1032B 时间点（Table 4）
- **Medical data**：Partial
- **医疗数据明细（论文原文）**：明确列出的只有 ECG 48B（4.65%，引用 PhysioNet / Goldberger 2000，具体库名 Not reported）；LOTSA、Chronos 子集中的少量公共卫生计数未逐项列出
- **ICU seen?**：Not reported
- **ED seen?**：No / Not reported
- **生命体征 seen?**：仅 ECG 波形；生命体征 Not reported
- **预训练含不规则采样?**：Not reported；App A 预处理含 'missing values imputation'
- **预训练频率范围**：各数据集频率 Not reported；App E：'TimeBench contains many middle- and low-frequency time series'
- **Time scale 判断**：Long-context oriented
- **Time scale 依据**：预训练最大上下文 2880（Sec 4）；App C.3 强调基础模型应增强 'long-context capabilities to handle high-frequency data'
- **Context length**：≤2880；patch 16（Table 5）
- **Forecast horizon**：TSLib / GIFT-Eval 输出 720 后截断；FEV 16（App B）
- **Irregular support**：不支持：只读数值，按索引切 patch（Sec 4.1.1）
- **Missing support**：只有长度不整除时的左侧填充 mask（Sec 4.1.1），不是缺失值机制；推理缺失处理 Not reported
- **Zero-shot type**：Zero-shot forecasting（概率）
- **Zero-shot 细节（排除 / 归一化 / 头）**：'All evaluated datasets are excluded from the pre-training dataset'（Sec 5.1，App A）；样本内两阶段实例归一化（Sec 4.1.1）；ERA5 与 Weather 基准的潜在重叠未讨论
- **Subgroup analysis**：按数据集（Tables 1、9）；GIFT-Eval 只给总分（Table 2）
- **Robustness**：Not reported
- **Domain shift**：零样本 vs 微调 vs 从头训练（Sec 5.5，Fig 8）；预训练数据规模 94B/230B/1032B（Table 8，Weather MSE 0.254/0.252/0.234）
- **Context-length analysis**：Fig 10（App C.3）：TSLib 上 lookback 480/960/1440/1920/2400/2880；结论 'performance is largely dependent on the forecasting task itself'，lookback 应按预测长度与周期调；未测 <480
- **作者自述局限 / 已知问题**：App E：'The performance on very high-frequency data is not guaranteed, since TimeBench contains many middle- and low-frequency time series'；单变量预训练无法用变量相关性；多步自回归可能过度平滑；App C.1：MSE 预训练导致单峰、过平滑预测（流匹配的动机）。默认采样数 FEV 20 条、GIFT-Eval 100 条（App B）
- **与本项目已有结果的关联**：week02 F1：Sundial 区间过窄（cov80≈0.36），当时怀疑调用问题；论文 Fig 7 显示样本数与流步数增加时 FEV 指标改善，应核对我们调用的样本数
- **阅读范围**：正文 + 附录 A–F（PDF v4 原文）

### TimesFM 2.5 / 3.0

- **论文 / 来源**：无论文；HF 模型卡 google/timesfm-2.0-500m、timesfm-2.5-200m、timesfm-3.0-pytorch，GitHub README，Google Research 博客（2026-08-31）
- **年份**：2.5：2025-09；3.0：2026-08
- **会议 / 期刊**：无（模型卡 / 博客）
- **是否开源 / 代码**：代码 Apache-2.0；2.5 及以前权重 Apache-2.0；3.0 权重为非商用许可（README）
- **公开 checkpoint**：2.0：500M；2.5：200M（+可选 30M 分位数头）；3.0：330M（20 层，d=1280）
- **Native task（原生任务）**：零样本预测。2.5：连续分位数预测，最长 1k 预测步，XReg 协变量（2025-10）；3.0：原生多变量 + 仅过去 / 过去与未来协变量，9 个分位数（README、博客）
- **Pretraining data**：2.0：1.0 数据 + LOTSA 20 个子集（含 cdc_fluview_who_nrevss）；2.5：GiftEvalPretrain + Wiki + Trends + 合成/增广；3.0：GiftEvalPretrain（去掉与 fev-bench 重叠的数据集）+ Wiki + Trends + 合成/增广（模型卡）
- **Scale**：3.0：'more than 1 trillion time points'（博客）；2.x：Not reported
- **Medical data**：2.0：Partial；2.5 / 3.0：Not reported
- **医疗数据明细（论文原文）**：2.0 模型卡列出 CDC FluView WHO NREVSS（流感实验室监测周数据）；GiftEvalPretrain 的组成清单未公开（HF 卡只给总量 4.5M 序列、230B 点），无法确认是否含医疗数据
- **ICU seen?**：Not reported
- **ED seen?**：Not reported
- **生命体征 seen?**：Not reported
- **预训练含不规则采样?**：Not reported
- **预训练频率范围**：Not reported
- **Time scale 判断**：Long-context oriented
- **Time scale 依据**：2.0 上下文 2048；2.5 '16k context length'（README）；3.0 global_context 15,360（README MLX 说明）
- **Context length**：2.0：2048；2.5：16k；3.0：15,360
- **Forecast horizon**：2.5：分位数头最长 1k；3.0：Not reported（示例 12–128）
- **Irregular support**：Not reported（规则网格）
- **Missing support**：2.0 模型卡：有 NaN 时 'fill in the missing values with linear interpolation before calling the model'，上下文须连续；2.5 / 3.0：Not reported
- **Zero-shot type**：Zero-shot forecasting
- **Zero-shot 细节（排除 / 归一化 / 头）**：3.0 博客称在 GIFT-Eval、fev-bench、TIME 上排名第一（仅图表）；3.0 训练集去除与 fev-bench 重叠的数据
- **Subgroup analysis**：Not reported（无论文）
- **Robustness**：Not reported
- **Domain shift**：Not reported
- **Context-length analysis**：Not reported
- **作者自述局限 / 已知问题**：3.0 权重限非商用、非生产；'not an officially supported Google product'
- **与本项目已有结果的关联**：合作摘要 MC-MED decomp_60：TimesFM 3.0 AUPRC 0.146（XGBoost 0.317；非严格排名）
- **阅读范围**：模型卡 + README + 博客（无论文可读）

### Timer-XL

- **论文 / 来源**：Timer-XL: Long-Context Transformers for Unified Time Series Forecasting（Yong Liu, Guo Qin, Xiangdong Huang, Jianmin Wang, Mingsheng Long）arXiv 2410.04803
- **年份**：2025
- **会议 / 期刊**：ICLR 2025
- **是否开源 / 代码**：是：github.com/thuml/Timer-XL（另见 OpenLTM）
- **公开 checkpoint**：thuml/timer-base-84m（README；Table 7 称 Timer-XL_Base；L=8、D=1024、patch 96，Table 11）
- **Native task（原生任务）**：预测（单变量 / 多变量 / 协变量）：patch 级下一 token 预测 + MSE（Sec 3.1）；TimeAttention 用变量依赖矩阵 × 因果时间 mask（Sec 3.2）
- **Pretraining data**：零样本权重：UTSD + LOTSA 单变量预训练（Sec 4.4、Table 9）；ERA5-Large（3 小时，约 5 亿点）用于多变量预训练（App B.1）
- **Scale**：LOTSA 231.1B 点 + UTSD 约 8.7 亿（Table 9；正文写 10 亿）
- **Medical data**：Partial
- **医疗数据明细（论文原文）**：Timer-XL 论文本身未列医疗数据。经 UTSD（HF 数据卡 Health 域）：MotorImagery、SelfRegulationSCP1/2、TDBrain（EEG）、AtrialFibrillation（ECG）、IEEEPPG（PPG）、BIDMC32HR（心率）、PigArtPressure、PigCVP；经 LOTSA：6 个公共卫生计数集（约 0.01%）。医疗占比 Not reported
- **ICU seen?**：Not reported（BIDMC32HR 的原始来源是重症监护患者记录——凭记忆，需核对原数据集说明）
- **ED seen?**：No
- **生命体征 seen?**：Partial（BIDMC32HR 心率、IEEEPPG 波形）
- **预训练含不规则采样?**：Not reported（Timer 论文称 S3 格式 'applies to broad univariate and irregular time series'，Sec 3.2）
- **预训练频率范围**：Timer-XL 实验：5 分钟（PEMS）至 3 小时（ERA5）；UTSD：0.001 秒至日
- **Time scale 判断**：Long-context oriented
- **Time scale 依据**：标题即 Long-Context；预训练上下文 2880（Timer 为 1440，Sec 4.4）；Sec 1：'a short-context input leads to insufficient learning of global tendencies'
- **Context length**：2880（UTSD/LOTSA）、3072（ERA5）；patch 96
- **Forecast horizon**：预训练 96；评价 96/192/336/720 滚动
- **Irregular support**：Not reported（只用规则频率数据，Table 9）
- **Missing support**：Not reported
- **Zero-shot type**：Zero-shot forecasting
- **Zero-shot 细节（排除 / 归一化 / 头）**：零样本：ETTm1/m2/h1/h2、ECL、Weather（Table 7）；Traffic 因 '常被大模型预训练使用' 不评；Timer-XL 自身的排除清单与泄漏讨论 Not reported
- **Subgroup analysis**：按数据集 × 预测长度（Tables 3、4、7、12、13）
- **Robustness**：只有 3 个种子的方差（Table 10）
- **Domain shift**：ERA5-Large 跨时间、跨站点泛化（Fig 5 中）；零样本跨数据集（Table 7）
- **Context-length analysis**：Fig 3（Sec 4.1）：lookback 从 8 小时到 1 年，'extending the daily context to monthly' 提升，月/年后 'improves slowly and deteriorates'；Table 15（App E.4）：Timer-XL 与 DLinear 随上下文变长改善，PatchTST 退化；Fig 8：ERA5 上推理 lookback 96–3072，最佳 lookback 不一定等于训练长度；Fig 5b：预训练上下文 1440→2880 后零样本全部改善
- **作者自述局限 / 已知问题**：App E.4：'context bottlenecks deserve further exploration'；通道相关注意力开销 O(N²T²)（App A.2）
- **阅读范围**：Timer-XL 正文 + App A–E（PDF）；Timer / UTSD 用 HF 数据卡 + 论文正文（附录只有摘要级）

### VisionTS

- **论文 / 来源**：VisionTS: Visual Masked Autoencoders Are Free-Lunch Zero-Shot Time Series Forecasters（Mouxiang Chen … Chenghao Liu）arXiv 2408.17253
- **年份**：2025
- **会议 / 期刊**：ICML 2025
- **是否开源 / 代码**：是：github.com/Keytoyze/VisionTS（MIT；pip install visionts）
- **公开 checkpoint**：直接使用 ImageNet 预训练的 MAE（默认 Base 112M；Large 330M、Huge 657M，Table 2）；无时序 checkpoint
- **Native task（原生任务）**：零样本点预测：按周期 P 把一维序列折成二维灰度图，MAE 重建被遮住的右侧列即为预测（Sec 3）；单变量 / 通道独立；不做概率预测（Sec 6）
- **Pretraining data**：只有 ImageNet 图像：'a visual masked autoencoder, pre-trained on the ImageNet dataset'，'without further adaptation in the time series domain'（Abstract）
- **Scale**：ImageNet（无时序数据）
- **Medical data**：No
- **医疗数据明细（论文原文）**：无任何时序预训练
- **ICU seen?**：No
- **ED seen?**：No
- **生命体征 seen?**：No
- **预训练含不规则采样?**：不适用
- **预训练频率范围**：不适用
- **Time scale 判断**：Long-context oriented
- **Time scale 依据**：上下文 L 在各数据集验证集上调：ETTh1 2880、ETTh2 1728、ETTm1 2304、ETTm2 4032、Weather 4032、Electricity 2880（App B.1 Table 8，附录为摘要级）；Fig 6：L 越长越好，高频数据尤甚
- **Context length**：LTSF 1728–4032；Monash 300/1000；GIFT-Eval 2000
- **Forecast horizon**：96 / 192 / 336 / 720
- **Irregular support**：不支持：需要周期 P（由采样频率决定，Sec 3）与规则网格；无明显周期时取 P=1（Sec 3，App B.6）
- **Missing support**：Not reported
- **Zero-shot type**：Zero-shot forecasting（跨模态：图像→时序）
- **Zero-shot 细节（排除 / 归一化 / 头）**：'without fine-tuning on time-series modalities'（Sec 4.1）；实例归一化后缩放到标准差 r=0.4（Sec 3）；选了 6 个不在 Moirai 预训练集里的 LTSF 数据集
- **Subgroup analysis**：按数据集（Table 1）；Monash 29 集（Fig 5）；GIFT-Eval（Fig 4）；按频率分层：正文 Not reported
- **Robustness**：Not reported
- **Domain shift**：Fig 7：部分时序图像的 MAE 嵌入落在 ImageNet 分布内（ETTm1、Electricity）
- **Context-length analysis**：Fig 6（Sec 4.2）：'performance typically improves with increasing L, particularly on high-frequency datasets like Weather (10-minute frequency) and ETTm1/ETTm2 (15-minute frequency)'；短输入 Not reported
- **作者自述局限 / 已知问题**：Sec 6：'cannot capture multivariate interactions and perform distribution forecasting'；MAE 越大略差（Table 2：0.309/0.311/0.315）。后续 VisionTS++（arXiv 2508.04379）在 LOTSA 上续训 MAE
- **阅读范围**：正文全文；附录为摘要级（B.9 未读到原文）

### LightGTS

- **论文 / 来源**：LightGTS: A Lightweight General Time Series Forecasting Model（Yihang Wang … Bin Yang, Chenjuan Guo，华东师大）arXiv 2506.06005
- **年份**：2025
- **会议 / 期刊**：ICML 2025
- **是否开源 / 代码**：是：github.com/decisionintelligence/LightGTS
- **公开 checkpoint**：HF DecisionIntelligence/LightGTS（README：2025-09 发布 mini）；tiny 1.3M、mini 4M（Table 10）
- **Native task（原生任务）**：预测（96–720 步）：周期 tokenization（patch = 周期长度，flex 投影适配不同周期）+ 周期并行解码；MSE；RevIN；通道独立（Sec 3）
- **Pretraining data**：Monash、UEA、UCR 子集 + PRSA、TDbrain、PEMS03/04/07/08/bay、FRED-MD、NN5，共 33 个数据集（App A.1，Table 7）
- **Scale**：总量 Not reported（只有各数据集点数）
- **Medical data**：Partial
- **医疗数据明细（论文原文）**：Table 7 'Health'：MotorImagery、SelfRegulationSCP1/2、TDbrain（EEG）、AtrialFibrillation（ECG）、PigArtPressure、PigCVP（动物血流动力学）；占比 Not reported
- **ICU seen?**：Not reported
- **ED seen?**：No
- **生命体征 seen?**：No（只有 EEG/ECG/动物血压波形）
- **预训练含不规则采样?**：Not reported
- **预训练频率范围**：1 毫秒至月（App A.1，Table 7）
- **Time scale 判断**：Medium
- **Time scale 依据**：历史固定 N=10 个周期 token、预测 K=4 个（App A.4）；参考 patch 48（Sec 4.6），即约 480 点；README 用 context_points 528、patch_len 48
- **Context length**：约 10 × 周期（README 528）
- **Forecast horizon**：96 / 192 / 336 / 720
- **Irregular support**：不支持：需由采样率先验或 FFT 得到周期（Sec 3.1.1、App B.1）
- **Missing support**：Not reported
- **Zero-shot type**：Zero-shot forecasting
- **Zero-shot 细节（排除 / 归一化 / 头）**：目标集 'strictly exclusive from the pre-training datasets'（Sec 4.1），预训练与目标 'no overlap'（App A.1）；RevIN
- **Subgroup analysis**：按数据集 × 预测长度（Table 12）
- **Robustness**：Fig 4（Sec 4.6）：ETT 在不同采样粒度下零样本，LightGTS 'maintains stable performance'，Timer、Time-MoE 波动——本表中唯一直接测 '采样频率变化' 的实验
- **Domain shift**：Fig 2b：在 ETTh1 训练、在其他时间尺度测试，只有周期 tokenization 能迁移
- **Context-length analysis**：Not reported（N 固定为 10）
- **作者自述局限 / 已知问题**：无 Limitations 节；App B.1：FFT 周期 'may not align with the intrinsic period, which can hinder model performance'
- **阅读范围**：正文 + App A–C（Table 13 数值截断）

### Chronos-2

- **论文 / 来源**：Chronos-2: From Univariate to Universal Forecasting（Abdul Fatir Ansari … Michael Bohlke-Schneider）arXiv 2510.15821
- **年份**：2025
- **会议 / 期刊**：arXiv 技术报告（未见正式发表）
- **是否开源 / 代码**：是：同 chronos-forecasting 仓库（Apache-2.0）
- **公开 checkpoint**：amazon/chronos-2（120M）、autogluon/chronos-2-small（28M）、autogluon/chronos-2-synth（120M，纯合成数据训练）
- **Native task（原生任务）**：零样本单变量 / 多变量 / 协变量预测（过去与已知未来协变量，数值与类别）；组注意力实现上下文学习（Sec 3.2、3.4）；21 个分位数的分位数损失（Eq 4）
- **Pretraining data**：Chronos 与 GIFT-Eval 预训练语料的选定子集 + TSI、TCM 合成（Sec 4.1）；多变量与协变量任务 'relied entirely on synthetic data'（Sec 4.2）；完整清单在 Table 6（未读到）
- **Scale**：Not reported（正文无总量）
- **Medical data**：Not reported
- **医疗数据明细（论文原文）**：Table 6 未读到；HF 卡只写 'Subset of Chronos Datasets'、'Subset of GIFT-Eval Pretrain'、合成数据
- **ICU seen?**：Not reported
- **ED seen?**：Not reported
- **生命体征 seen?**：Not reported
- **预训练含不规则采样?**：Not reported
- **预训练频率范围**：Not reported
- **Time scale 判断**：Long-context oriented
- **Time scale 依据**：两阶段预训练：上下文 2048，第二阶段扩到 8192（Sec 3.3）；HF 卡最大上下文 8192、最大预测 1024
- **Context length**：8192
- **Forecast horizon**：≤1024（HF 卡）
- **Irregular support**：不支持：只有相对时间索引（Sec 3.1），无时间间隔建模
- **Missing support**：支持：二值 mask，缺失值不参与均值 / 标准差计算并置零（Sec 3.1）；损失中排除缺失目标（Sec 3.3）
- **Zero-shot type**：Zero-shot forecasting（含多变量与协变量）
- **Zero-shot 细节（排除 / 归一化 / 头）**：fev-bench：'None of these datasets or tasks were seen by Chronos-2 during training'；GIFT-Eval 与部分数据集的训练段有重叠（Sec 5.1）；Table 3 估计的泄漏率：Chronos-2 0%、TiRex 1%、TimesFM-2.5 8%、Toto 8%、Moirai-2.0 28%；标准化后 arcsinh（Eq 1–2）
- **Subgroup analysis**：fev-bench 单变量 32 / 多变量 26 / 协变量 42 个任务子集（Figs 3–4）；能源与零售协变量任务（Fig 5）；按频率 / 预测长度：Not reported
- **Robustness**：Not reported
- **Domain shift**：纯合成数据版本 Chronos-2-Synth（Fig 8b：fev 技能分 45.9 vs 47.3）
- **Context-length analysis**：无上下文长度扫描；Fig 8c：2K vs 8K 上下文后训练，fev 46.9→47.3、GIFT 50.1→51.4、CBII 45.8→46.6，'particularly on the GIFT-Eval benchmark, which contains many high-frequency datasets'（Sec 5.4）；上下文学习在 'many tasks with short contexts' 的 CBII 上收益 'especially strong'（Sec 5.2）
- **作者自述局限 / 已知问题**：Sec 6：单变量以外的能力 'rely entirely on synthetic data'；多变量收益 'modest'（Sec 5.2）
- **阅读范围**：正文（附录 A/B 未读到）

## 附录 B：独立临床评测

“独立临床评测”指的是：**不是模型原作者自己在通用时序数据上测试，而是其他研究者把这些时序基础模型拿到 eICU、MIMIC 等临床数据上重新评估。**

它的价值是给本项目提供外部背景证据，例如：

- 多数 TSFM 在临床生命体征 zero-shot forecasting 上并不一定优于专门训练的传统模型；
- 临床生命体征的历史窗口长度、异常值、跨院泛化等问题已经被独立研究观察到；
- 但这些工作同样很少做 Age / Gender / ESI 这样的患者级 subgroup。

因此这部分保留在附录，不占主汇报主线。

| 论文                                                                                                                                                         | 出处                                                                        | 数据与设定                                                                                                                      | 模型与方式                                                                                    | 主要发现                                                                                                                                                                                                                                                                                                     | 与本项目的关系                                                   | 阅读范围                    |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- | ----------------------- |
| Are Time Series Foundation Models Ready for Vital Sign Forecasting in Healthcare?（Xiao Gu … David A. Clifton）                                              | ML4H 2024，PMLR 259:401–419                                                | eICU（6,199 患者）、MIMIC-III Waveform（1,089 患者）；患者级 6:2:2；5 分钟中位数重采样；默认历史 6 h、预测 3 h；HR、SBP、DBP、RR、SpO₂；连续缺失 >1 h 的片段删除，其余前向填充 | TimesFM（零样本）、Chronos S/B/L、Moirai S/B/L、Lag-Llama（零样本 + 全量微调）vs ARIMA、GRU、PatchTST 等从头训练 | Table 3：'the zero-shot performance of most TSFMs is not competitive with even the trained-from-scratch performance of most conventional methods'（eICU HR MAE：GRU 4.462、TimesFM 5.228、Chronos-S 4.807、Lag-Llama 7.365）；Table 4：异常值检测差；Table 5：NEWS2 变化检测上零样本与传统方法相当；Fig 3：历史越长多数更好；Fig 4：Moirai 多变量输入明显改善 | 最接近 MC-MED 的独立证据：同为分钟级床旁体征，但是 ICU、6 h 历史；无年龄 / 性别 / 严重度亚组 | 正文与 Tables 1–6 原文；附录摘要级 |
| Can one model fit all? Evaluating foundation models for time series forecasting across clinical medicine（Gernot Pucher … Christopher Sauer）                | Artificial Intelligence in Medicine 2026，doi:10.1016/j.artmed.2026.103473 | 埃森大学医院 + 两家地区医院 + MIMIC-IV；6 个临床用例（体征、化验、床位）                                                                               | Chronos、TimesFM 等，零样本与微调 vs 神经网络、GBDT、AutoML、统计模型                                        | 零样本 'frequently approached the performance of optimized task-specific models'；微调后 Chronos、TimesFM 分别 19、18 次进入最佳（AutoML 21 次）；'superior transportability across hospital settings and patient populations'                                                                                               | 跨院迁移的反向证据                                                 | 仅摘要                     |
| Evaluating Zero-Shot Foundation Models for Time Series Forecasting in Clinical Settings: A Simulation Study with Electronic Health Records（Pucher … Sauer） | AI4TS 研讨会 2025                                                            | 德国大学医院 EHR + 两个外部验证集，3 个用例                                                                                                 | Chronos、Time-LLM、Time-MoE 零样本 vs 任务专用模型                                                  | 任务专用（尤其深度学习）模型多数场景更准；零样本在外部验证集上 'competitive'                                                                                                                                                                                                                                                            | 同上                                                        | 仅摘要                     |
| Position: Time-Series Foundation Models Require Explicit Domain-Level Benchmarks（Md Asif Bin Syed … Azmine Toushik Wasi）                                   | ICML 2026，PMLR 306                                                        | 72 个数据集、6 个领域（含医疗）                                                                                                         | 7 个 TSFM                                                                                 | 'substantial cross-domain variability'；临床记录有 'irregular sampling and informative missingness'                                                                                                                                                                                                            | 支持为医疗单独做基准                                                | 仅摘要                     |
| Cached Foundation Model Summaries for Memory-Efficient Clinical Time Series Inference（Rafi Al Attrach … Peter Schüffler）                                   | ICLR 2026 研讨会（TSALM）                                                      | MIMIC-IV 不规则事件序列                                                                                                           | 基础模型把历史压成缓存摘要 + 轻量模型看近期短窗口                                                               | 近期窗口 8 个事件时 AUROC 相对 +6.5%（p<0.001），256 个事件时 +0.1%（不显著）；近期历史的摘要比远期更有用                                                                                                                                                                                                                                    | 短窗口下基础模型表示可能价值最大，但前提是能带入更长历史                              | 仅摘要                     |
