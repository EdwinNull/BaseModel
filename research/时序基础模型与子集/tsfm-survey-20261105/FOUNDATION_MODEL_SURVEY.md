# FOUNDATION_MODEL_SURVEY：现有模型在 MIMIC-IV / MC-MED 哪些子集上表现差、原因与对策，以及时序基础模型背景

> 2026-11-06 更新（A 部分新增）；B 部分为 2026-11-05 · 纯文献调研，未跑实验 · 配套表格 `FOUNDATION_MODEL_SURVEY.xlsx`（19 个工作表）与 `csv/`。所有判断都附论文位置；没读到原文的地方标了阅读范围。


# A 部分：子集缺陷、原因与对策（2026-11-06）

## A0. 一页结论


研究主线：找出现有方法在数据集哪些子集上表现差，查清原因，再针对性地修。本页 A 部分是 11-06 新增的子集缺陷调研（33 篇文献），B 部分是 11-05 的时序基础模型背景调研。纯文献调研，未跑实验。


**总判断：** 在 MIMIC-IV / MIMIC-IV-ED / eICU 上，表现差的子集已被反复报告，集中在四个方向：种族与保险（含交叉子群）、年龄、测量过程、时间。MC-MED 上本轮只找到一份分组结果（MC-BEC，单阈值 TPR），没有找到按子集系统评估模型的工作，这是本项目可以占的空白（检索范围有限，不宣称“首个”）。

**A1 文献里哪些子集表现差？**
- 种族、保险与交叉子群：MIMIC-IV-ED 入院预测的种族 ΔTPR 0.251（FAIM Table 4）；交叉子群 ECE 最高约 0.119（美洲原住民男性，Lett 2025）；MIMIC-III 院内死亡中 Medicaid、黑人患者 AUROC / AUPRC 更差，Medicare（多为老年）风险被明显低估（Röösli 2022）。
- 年龄与性别：MC-MED 前身上，固定阈值下 decomp-60 的 TPR 年轻组（<55 岁）0.87、≥55 岁 0.94，女性 0.88、男性 0.92（MC-BEC Table 5）。较差的是年轻组和女性，但这是单阈值 TPR，混着基础率。分诊层面老年人被漏判：ESI 1 级识别需立即抢救的老年人灵敏度 42.3%；衰弱老人中 NEWS2 预测 30 天死亡 AUC 0.70。
- 测量过程：去掉监护数据后 decomp-60 AUPRC 0.25 → 0.14（MC-BEC Table 4）；项目 mp_benchmark 中 drop40 让五个模型 ΔAUPRC −0.016 至 −0.036、个体预测翻转 6.2%–9.7%；MIMIC-III 的测量频率随年龄和种族系统变化，只用测量模式预测死亡 AUC 0.76（Shi 2025）。
- 时间：MIMIC-IV 上 2008–10 训练的脓毒症模型到 2017–19 AUROC 最多降 0.090（Guo 2022）。

**A2 原因有哪些？** 七类：C1 样本少；C2 基础率不同造成的指标伪差（AUPRC 偏向高患病率子集，McDermott 2024 Theorem 3）；C3 测量过程被当作捷径；C4 测量误差同时进入输入和标签（脉搏血氧对深肤色高估，隐匿低氧黑人 6.8% vs 白人 4.9%，而 SpO2<90 正是 decomp_60 的事件定义之一）；C5 标签与分组变量有噪声（ESI 误分诊 32.2%）；C6 生理异质性（同样的体征在老年人代表不同风险，预警评分加年龄后 AUC 都提高）；C7 时间与流程偏移。

**A3 怎么找？** 预设分组只能找到单变量子集；AFISP 在恶化预警模型上找到的 13 个子群里 9 个是多变量组合。建议预设分组 + 数据驱动（AFISP、误差聚类、Domino 式嵌入切片），且发现和确认用两份独立数据。

**A4 怎么修？** 证据较强、代价低：分组再校准 / 多重校准（ECE 0.083 → 0.065，AUROC 不变）、冻结表示 + 分组平衡重训分类头（DFR）、有针对性补数据（AFISP 学习曲线）。常常无效：公平约束（组内性能普遍下降）、单属性重加权（扩大其他属性差距）、域泛化 / 无监督域适应（时间偏移和跨年龄都没有胜过 ERM，项目 AL4 跨年龄全部无效）。校准只改概率、不改排序。

**A5 本项目下一步（按研究者 11-06 决定）**
1. 审计：在 MC-MED 冻结测试集上，对已有全部模型按人群、临床、测量过程三族子集打分；老年从 65 岁起算，按 65–74 / ≥75 切分；跨子集比较以 AUROC 和校准为主，AUPRC 与患病率并列；每个子集至少约 30 个事件。
2. 发现：AFISP 式稳定性分析 + 误差聚类，在验证集上找组合子集，在冻结测试集上确认。
3. 归因：逐个子集检查 C1–C7（基础率、学习曲线、过程分层与 mask 替换、事件分量、校准斜率、域分类器）。
4. 修复：F1 再校准 → F4 DFR → F3 补数据 → F5 / F6 输入与过程增强；F7 / F8 只作对照。
5. 复现：在 MIMIC-IV-ED 上用 5 个可对齐变量重复审计与归因；MIRA 的结果单独报告（预训练含 MIMIC-IV）。

**A6 研究者决定（11-06）**
1. 输入窗口：视情况延长，先查新版 GD / GAM 的生命体征与检验密度（检查项见 xlsx『窗口密度检查』，只交回聚合量）。
2. VIMTS 放在不规则时序专用模型组，不归入基础模型组。
3. 老年从 65 岁起算，按 65–74 / ≥75 切分。这一口径只用于子集审计，项目 D70（≥60 岁主分析、≥65 岁亚组）不变；子集表另报 ≥60 以便对齐。
4. MIRA 分开考虑：MIMIC-IV / MIMIC-IV-ED 上的结果单独成表并标注重叠。
5. 子集在验证集上发现、在冻结测试集上确认。
6. 标签变体（去掉 SpO2 分量）、年龄校正阈值与分组阈值只作敏感性分析。
可检验假设 S1–S6 见 xlsx『MC-MED子集审计方案』与报告。



## A1. 文献中已报告的表现差子集

| 编号 | 文献 | 数据集与规模 | 任务 / 模型 | 表现差的子集（原文数字） | 位置 | 作者给的原因 | 证据类型 | 阅读范围 | 对 MC-MED decomp_60 的启示 |
|---|---|---|---|---|---|---|---|---|---|
| E1 | Chen et al., MC-BEC, NeurIPS 2023 D&B（arXiv 2311.04937） | MC-MED 前身 MC-MED-v0：斯坦福急诊有监护床位 2020–2022，102,731 次就诊 | decomp 60/90/120（评估期 15 分钟后 60–120 分钟内新出现 HR>110、MAP<65 或 SpO2<90；评估期或分诊时已异常者排除）；多任务 LightGBM，输入含分诊、人口学与监护 | 固定灵敏度阈值（验证集灵敏度 0.85）下 decomp-60 的 TPR：年龄 <55 岁 0.87、≥55 岁 0.94；女性 0.88、男性 0.92；去掉监护模态后多任务模型 decomp-60 AUPRC 0.25 → 0.14 | Sec 3.2–3.3；Table 4、Table 5 | 未分析原因 | 直接实验 | 正文与表格逐字；附录为工具摘要 | 唯一与 MC-MED 同源的分组结果：较差的是年轻组和女性，不是老年组。但这是单阈值 TPR，受各组基础率与风险分布影响，没有组内 AUROC、样本量和置信区间；表内差值与显示值有出入（性别 0.92−0.88 记为 0.05） |
| E2 | Kansal et al., MC-MED, Sci Data 2025;12:1094 | MC-MED 1.0.0：118,385 次就诊 / 70,545 人 | 数据描述论文，无基线模型 | 没有基准结果，也没有分组分析 | Methods、Technical Validation | 不适用 | 无证据 | 正文；人口学表（PhysioNet Table 11）为工具摘要 | 数据特性会制造子集：只覆盖有监护床位的就诊；监护数据按床位记录、再按入床和离开时间切分；年龄加 0–2 岁扰动并截断在 18–90；时间按患者平移（日历季节类子集可能不可用，需核对）；numerics 有 Chart / Monitor 来源字段 |
| E3 | Gustafsson et al., SignalMC-MED, arXiv 2603.09940（2026） | MC-MED 22,256 次就诊，按时间切分 | ECG / PPG 基础模型线性探针，20 个任务（含急诊去向） | 未做分组、缺失或偏移分析 | Table 2、Table 4 | 不适用 | 无证据 | 正文约一半逐字 | MC-MED 上的基础模型评测同样没有子集分析 |
| E4 | Xie et al., Sci Data 2022（MIMIC-IV-ED 基准） | MIMIC-IV-ED 441,437 次成人就诊 | 住院、危重结局、72 小时复诊；LR / RF / GB / MLP / LSTM 与 ESI、NEWS 等评分 | 未做分组分析；分诊时点危重结局 AUROC：ESI 0.804、NEWS 0.634、最佳 MLP 0.883 | Table 6 | 不适用 | 无证据（分组） | 正文逐字 | 最常用的 MIMIC-IV-ED 基准没有子集报告，复用它的工作也大多没有 |
| E5 | Lett et al., JAMA Netw Open 2025;8(5):e2512947 | MIMIC-IV-ED 160,016 次就诊；波士顿儿童医院 22,222 次 | 急诊入院预测；XGBoost、惩罚 LR | 种族 × 性别交叉子群误差更大，例如边际去偏后 ECE：美洲原住民男性 0.119、西语裔女性 0.104、黑人女性 0.102；FNR：美洲原住民男性 0.218 | Results；Figure 2–3 | 交叉子群样本少；各组入院率不同时 FNR、FPR、校准不可能同时相等 | 直接实验 | 正文；补充表未读 | 只按单一属性分组会漏掉交叉子群（老年女性、少数族裔男性等） |
| E6 | Liu et al., FAIM, arXiv 2403.05235 | MIMIC-IV-ED 418,100；新加坡总医院急诊 1,716,830 | 急诊入院预测；LR 与多种公平方法 | 基线 LR 的种族 ΔTPR 0.251、ΔTNR 0.224；性别 ΔTPR 0.074 | Table 2、Table 4 | 未分析 | 直接实验 | 全文含表 | MIMIC-IV-ED 上种族差距远大于性别差距 |
| E7 | Röösli et al., Sci Data 2022;9:24 | MIMIC-III 院内死亡基准模型（LSTM），外部 STARR | ICU 48 小时院内死亡 | Medicaid 与私人保险事件率相近（8.5% vs 8.3%），Medicaid 的 AUROC、AUPRC 更差；黑人事件率更低（9.7% vs 11.3%）仍更差；Medicare（多为 ≥65 岁）风险被明显低估；外部验证事件召回低于 20% | Results：classification parity、calibration 各段 | 类别不平衡、少数群体代表性不足 | 直接实验 | 全文 | 老年组的问题可能主要在校准（风险被低估），而不是排序 |
| E8 | Meng et al., Sci Rep 2022;12:7166（MIMIC-IF） | MIMIC-IV | 院内死亡深度模型 | 模型依赖人口学特征；不同种族、性别、年龄的机械通气处置不同 | 摘要 | 处置差异进入数据 | 作者分析 | 摘要 | 处置差异会变成模型可利用的捷径 |
| E9 | Guo et al., Sci Rep 2022;12:2726 | MIMIC-IV ICU，按 2008–10 / 11–13 / 14–16 / 17–19 分组 | 死亡、长住院、脓毒症、有创通气；前馈网络 | 2008–10 训练、2017–19 测试，脓毒症 AUROC 最多降 0.090（95% CI 0.080–0.101） | 摘要 | 医疗实践随时间变化 | 直接实验 | 摘要 | 时间段本身就是一类子集；DG / UDA 没有比 ERM 更稳 |
| E10 | Shi et al., BMC Med Inform Decis Mak 2025;25:241 | MIMIC-III 23,426 人，首个 24 小时 | 测量模式与人口学的关联（TMLE）及死亡预测 | 调整病情后：≥65 岁生命体征测得更频繁、缺口更少（化验更少）；白人首 24 小时血压测量 34.22 次，黑人 32.79 次；只用测量模式预测 ICU 死亡 AUC 0.76 | Results；Figure 与 Table | 监护实践中的系统差异 | 直接实验 | 全文 | 观测密度随年龄和种族系统变化，而观测密度本身带结局信息，模型会学到它 |
| E11 | Agniel et al., BMJ 2018;361:k1479 | 波士顿两院 669,452 人，272 项化验 | 3 年生存 | 是否开了化验在 86% 的化验项目上与生存显著相关；化验时间比化验值更能预测生存的占 68% | Abstract；Table 1–2 | 医疗过程本身产生信号 | 直接实验 | 正文与表 | “测得多 = 病重”是普遍规律，测量习惯不同的子集上会失效 |
| E12 | Jeanselme et al., ML4H 2022（PMLR 193） | MIMIC-III、SUPPORT | 短期生存预测 | 两种常用插补方法之间的选择可以翻转黑人 / 非黑人的公平方向；分组插补可能反而伤害边缘群体 | Introduction；Theorem 4.1–4.2 | 三种“临床存在”机制：就医受限、按判断采集、确认偏差 | 直接实验 + 理论 | 部分（结果数字未取得） | 缺失感知模型（GRU-D、BRITS 等）之间的差别必须按子集报告 |
| E13 | Wong et al., JAMA Netw Open 2021;4:e2131674 | eICU、MIMIC-III、MIMIC-IV 等 87,971 对 SpO2–SaO2 | 脉搏血氧偏差 | 隐匿低氧：黑人 6.8%、西语裔 6.0%、亚裔 4.8%、白人 4.9%；隐匿低氧者 24 小时后 SOFA 更高、院内死亡更高 | 摘要 | 脉搏血氧对深肤色高估 | 直接实验 | 摘要 | decomp_60 的输入和标签都用 SpO2：部分子集的低氧事件可能被漏记 |
| E14 | Platts-Mills et al., Acad Emerg Med 2010；Grossmann et al., PLoS One 2014 | ≥65 岁急诊 782 人；519 / 394 人 | ESI 分诊准确性 | ESI 1 级识别需要立即抢救干预的老年人灵敏度 42.3%；老年漏分诊 22.5%（干预后 24.2%），随年龄增大而升高 | 摘要 | 未遵循 ESI 流程；老年表现不典型 | 直接实验 | 摘要 | ESI 分层本身带误差：ESI 3 级里混有被低估的老年患者 |
| E15 | Sax et al., JAMA Netw Open 2023;6:e233404 | KPNC 21 个急诊 5,315,176 次 | ESI 误分诊 | 误分诊 32.2%（漏分 3.3%、过分 28.9%）；黑人漏分诊相对风险 +18.5%；服高危药物 +30.3%、合并症多 +22.4%、近期 ICU +36.7% | 摘要 | 分诊主观性 | 直接实验 | 摘要 | 同上；用药与合并症是 MC-MED 可取的分层变量 |
| E16 | Kemp et al., BMC Emerg Med 2020；Martín-Conty et al., QJM 2024 | ≥75 岁衰弱老人 1,711 次；院前 8,028 人 | NEWS2 等预警评分 | 衰弱老人中 NEWS2 预测 30 天死亡 AUC 0.70、入院 0.62；各评分加入年龄后 AUC 都显著提高（NEWS2 P=0.001） | 摘要 | 同样的体征在不同年龄代表不同风险 | 直接实验 | 摘要 | 只用体征、不含年龄的模型（如 decomp_60 冻结基准）在老年组可能排序变差 |
| E17 | Subbaswamy et al., npj Digit Med 2024;7:334（AFISP） | 多院住院恶化监测模型，测试 60,998 次 | 非 ICU 恶化预警 | 整体 AUROC 0.986，最差 5% 子集 0.919；找到 13 个子群，4 个 AUROC 区间低于 0.9，9 个是多变量组合（单变量分组发现不了）；给最差子群补训练数据可补回差距 | Results；Table 与 Figure | 子群数据不足 | 直接实验 | 全文 | 预设单变量分组不够，需要数据驱动的子集发现 |
| E18 | Seyyed-Kalantari et al., Nat Med 2021；Oakden-Rayner et al., CHIL 2020 | MIMIC-CXR 等胸片 | 影像分类 | 女性、黑人、低社会经济地位漏诊更多，交叉子群（如西语裔女性）更严重；隐藏分层造成最多约 20% 的性能差，例如无胸管气胸 AUC 0.77 vs 有胸管 0.94 | 摘要；Sec 3 | 捷径特征、子类罕见、标签不准 | 直接实验 | 摘要；扩展摘要全文 | 不是时序，但机制（捷径、隐藏分层）可直接迁移 |
| P1 | 本项目 mp_benchmark_v1（MC-MED decomp_60） | 冻结 benchmark 测试集 5,236，患病率 12.0% | FF-LSTM、GRU-D、BRITS、mTAND、Raindrop | drop40 下 ΔAUPRC −0.016 至 −0.036；个体预测翻转率 6.2%–9.7%；群体指标不变不代表个体稳定 | 项目背景 §6.3 | — | 项目内实验 | 聚合量 | 已有 drop / 连续缺失测试集，可直接按子集拆开看哪些人掉得最多 |
| P2 | 本项目 AL4 无监督域适应 | MIMIC → eICU；跨年龄 | 10 种 UDA | 跨中心 7 种显著好于“仅源域 + 重校准”；跨年龄全部无效 | 项目背景 §6.2 | — | 项目内实验 | 聚合量 | 年龄差异不是简单的协变量偏移，通用域适应修不了 |

## A2. 原因：七类机制与诊断方法

| 编号 | 机制 | 文献证据 | 在 MC-MED decomp_60 上可能的表现 | 诊断方法（只需聚合量或已有基础设施） |
|---|---|---|---|---|
| C1 | 样本少、方差大 | Chen 2018（差异分解为偏差 / 方差 / 噪声，补数据可降差异）；AFISP 学习曲线；Lett 2025 交叉子群 | 少数族裔（黑人约 6%）、ESI 1 / 5、≥80 岁等子集事件数少，指标区间宽 | 按患者聚类 bootstrap 区间；子集学习曲线（固定其他数据，逐步增加该子集训练样本） |
| C2 | 基础率不同造成的指标伪差 | McDermott 2024 Theorem 3（AUPRC 偏向高患病率子集）；Röösli 2022；MC-BEC 单阈值 TPR | 患病率更高的子集（可能是老年、ESI 1–2，需核对）AUPRC 与固定阈值灵敏度会“看起来更好”，患病率低的子集相反 | 并列报告 AUROC、AUPRC 与患病率；若只有 AUPRC 差、AUROC 不差，主要是指标问题 |
| C3 | 测量过程差异（观测密度、缺失通道、来源）被当作捷径 | Agniel 2018；Shi 2025（测量模式单独预测死亡 AUC 0.76，且随年龄、种族变化）；Jeanselme 2022；MC-BEC 去监护 AUPRC 0.25 → 0.14 | 窗口内观测少、缺血压或 SpO2 通道、以人工录入（Chart）为主的窗口，模型排序变差或概率漂移 | 按有效点数分位与缺失通道组合分层；只用过程特征的模型在各子集的 AUROC；把子集窗口的 mask 换成匹配多数组的 mask 后重打分 |
| C4 | 测量误差同时进入输入与标签 | Wong 2021、Mettler 2024（脉搏血氧对深肤色高估） | SpO2<90 是事件定义之一：部分患者真实低氧未被记成事件，表现为该子集“事件少、模型漏报” | 按事件分量（HR / MAP / SpO2）分别报告灵敏度；种族 × 分量交叉；去掉 SpO2 分量的标签变体做敏感性分析 |
| C5 | 标签与分组变量本身有噪声 | ESI 误分诊 32.2%（Sax 2023），老年 ESI 1 灵敏度 42.3%（Platts-Mills 2010） | ESI 3（约 65%）内部混有高风险患者；HR>110 阈值对服用 β 受体阻滞剂或老年人更难触发 | 各 ESI 组内的事件率与 AUROC；按事件分量和年龄交叉看事件构成 |
| C6 | 生理异质性：同样的数值在不同人群代表不同风险 | Martín-Conty 2024（加入年龄提升所有预警评分）；Kemp 2020；Röösli 2022 老年风险被低估 | 冻结基准只输入六项体征、不含年龄，老年人的风险可能被系统低估或排序变差 | 子集内校准截距与斜率；加入年龄 × 体征交互是否显著改善；按子集看特征归因 |
| C7 | 分布偏移（时间、地点、流程） | Guo 2022（脓毒症 AUROC 降 0.090）；Zhang 2021；项目 AL4（跨年龄 UDA 全部无效） | 2020–2022 跨越 COVID 不同阶段；但 MC-MED 时间按患者平移，日历子集可能做不了 | 用域分类器 AUROC 量化子集与训练集的差异；先核对去标识后是否保留季节和时段 |

## A3. 子集发现方法

| 方法 | 做法 | 证据 | 用在 MC-MED 时的注意点 |
|---|---|---|---|
| 预设分组（schema completion） | 按年龄、性别、种族、ESI 等先验分组逐一评估 | 多数临床公平研究的做法（Röösli、Lett、FAIM） | 切点需研究者定；交叉子群要单列 |
| AFISP（Subbaswamy 2024） | 先做稳定性分析找到最差的 α 比例子集，再用 SIRUS 规则学习把它描述成可读的子群 | 13 个子群中 9 个是多变量组合；合成数据中找回目标子群 83.4%，SliceFinder 94.6%，但 AFISP 随特征数扩展好得多 | 适合把人群、临床、测量过程字段一起放进去 |
| SliceFinder / SliceLine | 在离散化特征的组合上穷举搜索误差显著偏高的切片 | AFISP 文中作为对照，准确但随特征数爆炸 | 字段少（<30）时可直接用 |
| Domino（Eyuboglu 2022） | 在嵌入上拟合“误差感知”混合模型，再用跨模态嵌入给切片命名 | 1,235 个设置中找回 36% 的切片；EEG 时序上跨模态嵌入 precision@10 0.697 vs 单模态 0.532 | 可用 TSFM 或 GRU-D 的窗口嵌入做聚类；没有配对文本时命名要靠人工 |
| 误差聚类（Oakden-Rayner 2020） | 对模型倒数第二层特征做 k-means，比较高误差簇与低误差簇的属性 | 胸片气胸：高误差簇有胸管比例 0.17、低误差簇 0.68 | 最便宜，适合先跑一遍 |
| 发现与确认分开 | 在一份数据上发现，在另一份独立数据上确认 | AFISP 与 Domino 的局限都指出小样本下信号和噪声难分 | 冻结测试集已多次使用；按 11-06 决定，在验证集上发现、在测试集上确认 |

## A4. 对策：证据支持什么、不支持什么

| 编号 | 对策 | 证据 | 效果 | 局限 | 在本项目的用法 | 建议优先级 |
|---|---|---|---|---|---|---|
| F1 | 分组再校准 / 多重校准 | Barda 2021 JAMIA；Lett 2025；Tan 2026（isotonic） | 跨子群校准方差降 98.8%（PCE）/ 94.3%（FRAX）；MIMIC-IV-ED ECE 0.083 → 0.065，AUROC 0.85 不变 | 只改概率、不改排序（Locati 2026：校准不缩小 AUROC 差距） | 先做：现有 pos_weight≈7.08 本来就让概率整体偏高 | 高 |
| F2 | 分组阈值 | Locati 2026（ICML 研讨会，摘要） | TPR 差距 0.20–0.23 → <0.03 | 属于阈值决策；可能被视为差别对待 | 只作敏感性分析（11-06 决定） | 中 |
| F3 | 有针对性补数据 / 选数据 | AFISP 学习曲线；Chen 2018；Tan 2026 | 最差子群训练样本补到约 2,000 例时，与多数其他子群相当（AFISP） | 盲目加整源数据会伤害子集：黑人子集最差 −4.1%（Tan 2026） | 从 MC-MED 训练池对子集加权或过采样；或从 MIMIC-IV-ED 引入同类子集（5 个可对齐变量） | 高 |
| F4 | 冻结表示 + 分组平衡重训分类头（DFR / CRT） | Yang 2023 ICML（SubpopBench） | 在虚假相关与类别不平衡两类偏移上收益明显；无属性标签时平均最差组准确率 ERM 59.9、DFR 66.2 | 对属性不平衡、属性泛化两类偏移几乎无效 | 和 TSFM 冻结嵌入 + 探针的设定天然契合 | 高 |
| F5 | 输入加入上下文（年龄、ESI、到达方式） | Martín-Conty 2024 | 各预警评分加入年龄后 AUC 都显著提高 | 改变模型输入定义，需登记新版本 | 对应 C6；检验老年子集差距是否缩小 | 中 |
| F6 | 缺失 / 过程感知建模与过程扰动增强 | 项目 mp_benchmark；Jeanselme 2022 | 缺失感知模型对删减的稳健性不同（ΔAUPRC −0.006 至 −0.036） | 插补方式会翻转公平方向，必须按子集报告 | 对应 C3 与现有 M2 路线 | 中 |
| F7 | 公平约束 / 单属性重加权 / GroupDRO | Pfohl 2021；FAIM Table 2；Locati 2026；Yang 2023 | 组内性能几乎普遍下降（Pfohl）；Reductions 让 AUC 0.790 → 0.706；单属性重加权扩大其他属性差距 | 常常只是把误差挪到别的组 | 只作对照 | 低 |
| F8 | 域泛化 / 无监督域适应 | Guo 2022；Zhang 2021；项目 AL4 | 时间偏移上 DG / UDA 不比 ERM 稳（AUROC 差 −0.003 至 0.050）；eICU 跨地区 8 种 DG 都没有稳定胜过 ERM；跨年龄 UDA 全部无效 | 子集差异多数不是可对齐的协变量偏移 | 不建议作为主线 | 低 |

## A5. MC-MED decomp_60 子集审计方案（建议）

子集清单：

| 子集族 | 子集（建议切点，需研究者定） | 为什么查 | 所需字段 | 对应假设 |
|---|---|---|---|---|
| A 人群 | 年龄：18–44 / 45–64 / 65–74 / ≥75；老年 = ≥65（研究者 11-06 定）；只用于子集审计（D70 的 ≥60 主分析不变）；另报 ≥60 以对齐 | MC-BEC 年龄 TPR 差 0.07；老年校准被低估（Röösli）；预警评分加年龄更好 | visits 年龄（已扰动 0–2 岁） | S1 |
| A 人群 | 性别 | MC-BEC 女性 TPR 0.88 vs 男性 0.92 | 性别 | S1 |
| A 人群 | 种族、族裔；种族 × 性别、年龄 × 性别交叉 | 脉搏血氧偏差；MIMIC-IV-ED 种族 ΔTPR 0.251；交叉子群误差更大 | 种族、族裔 | S3 |
| B 临床 | ESI 1–2 / 3 / 4–5 | ESI 本身误分诊多，ESI 3 内部混杂 | 分诊级别 | S5 |
| B 临床 | 到达方式、主诉类别、是否服高危药物 | 漏分诊的危险因素（Sax 2023） | visits、用药 | S5 |
| B 临床 | 评估期末到阈值的距离（HR 距 110、MAP 距 65、SpO2 距 90）分位 | 标签是“跨阈值”，入选者评估期都正常 | numerics | S2 |
| B 临床 | 事件分量（仅阳性）：HR 型 / MAP 型 / SpO2 型 / 多分量 | 不同生理过程，可预测性不同 | 标签派生过程 | S2、S3 |
| C 测量过程 | 0–15 分钟每通道有效点数分位 | 稀疏窗口；TSFM 有效 token 数（H1） | numerics | S4 |
| C 测量过程 | 缺失通道组合（如无血压、无 SpO2） | MC-BEC 去监护 AUPRC 0.25 → 0.14 | numerics | S4 |
| C 测量过程 | 数据来源 Chart / Monitor 比例 | 人工录入与监护自动值的噪声和频率不同 | numerics.Source | S4 |
| C 测量过程 | 入床距到院时间；时段（若去标识保留） | 等待时间与病情、流程相关 | visits 时间 | S6 |
| D 数据驱动 | AFISP / 误差聚类在 A–C 全部字段与模型嵌入上发现的组合子集 | 多变量子集单变量分组发现不了 | 以上全部 + 嵌入 | — |

可检验假设：

| 编号 | 假设（MC-MED decomp_60） | 依据与证据类型 | 检验（聚合量） |
|---|---|---|---|
| S1 | 年龄与性别：固定阈值下年轻组、女性灵敏度更低；老年组的问题更可能在校准而不在排序 | MC-BEC Table 5（直接实验，单阈值）；Röösli 2022（直接实验，MIMIC-III）；Martín-Conty 2024 | <65 / 65–74 / ≥75 各组 AUROC、校准截距 / 斜率、固定阈值灵敏度，并列各组患病率 |
| S2 | “评估期正常但远离阈值”的患者最难：模型主要靠“离阈值多近” | 任务定义（设计推断） | 按评估期末到阈值距离分层的灵敏度与 AUROC；阳性按事件分量拆开 |
| S3 | SpO2 型事件在深肤色患者中被漏记，表现为该子集事件率偏低、模型漏报 | Wong 2021、Mettler 2024（直接实验，ICU）；迁移到急诊为推断 | 种族 × 事件分量的事件率与灵敏度；去掉 SpO2 分量的标签变体（只作敏感性分析） |
| S4 | 观测稀疏、缺通道、以人工录入为主的窗口上，各模型排序变差，且不同缺失机制模型差别最大 | MC-BEC Table 4；Shi 2025；项目 mp_benchmark（直接实验） | 按有效点数分位、缺失通道组合、来源分层的 AUROC；已有 drop20 / drop40 / continuous5min 结果按子集拆开的 ΔAUROC 与翻转率 |
| S5 | ESI 3 组内 AUROC 低于 ESI 1–2，原因是组内病情混杂而非样本少 | Sax 2023、Platts-Mills 2010（直接实验，分诊） | 各 ESI 组的事件率、AUROC、观测密度；ESI 3 内再做数据驱动切片 |
| S6 | 入床前等待时间长短与时段不同的子集表现不同 | 推断（无直接文献） | 按入床延迟分位与时段的 AUROC（先核对去标识时间） |

步骤：

| 步骤 | 做什么 | 产出（只交回聚合量） | 依赖 |
|---|---|---|---|
| 1 审计 | 在冻结测试集上，对已有全部模型（XGBoost、FF-LSTM、GRU-D、BRITS、mTAND、Raindrop、OPL-MT-MNAR、MIRA、TimesFM 3.0、VIMTS-Adapter）按 A–C 子集打分 | 子集 × 模型的 AUROC、AUPRC、患病率、校准、固定阈值灵敏度，含按患者 bootstrap 区间与 Holm 校正 | 已定：老年 ≥65，按 65–74 / ≥75 切分；每个子集至少约 30 个事件 |
| 2 发现 | 在发现用数据上跑 AFISP 式稳定性分析与误差聚类，找出组合子集；在确认用数据上复核 | 可读的子集规则、规模、AUROC 与区间 | 已定：验证集上发现、冻结测试集上确认 |
| 3 归因 | 对每个确认的子集依次检查 C1–C7：基础率、学习曲线、过程分层与 mask 替换、事件分量、校准斜率、域分类器 | 每个子集的主要原因与证据强度 | 已定：标签变体只作敏感性分析 |
| 4 修复 | 按 F1 → F4 → F3 → F5 / F6 的顺序做，F7 / F8 只作对照 | 最差子集 AUROC、总体 AUROC、校准与 FNR 差距的权衡表 | 已定：分组阈值只作敏感性分析；输入改动（如加年龄）需登记新版本 |
| 5 复现 | 在 MIMIC-IV-ED 上用对齐的 5 个变量重复步骤 1 与 3 | 同一类子集在两个数据集是否都差 | MIMIC-IV-ED 任务口径；MIRA 结果单独报告（预训练含 MIMIC-IV） |

指标与统计（建议）：跨子集比较以 AUROC 为主（McDermott 2024 建议），并报告校准截距 / 斜率（先单调再校准，因 pos_weight≈7.08 使概率整体偏高）；AUPRC 与该子集患病率并列；固定阈值（验证集定、冻结）下的灵敏度 / FNR；按患者聚类 bootstrap 1,000 次；子集 Δ = 子集 − 补集；预设子集 Holm 校正；数据驱动子集在验证集上发现、在冻结测试集上确认（11-06 决定）。


## A6. 研究者决定（11-06）

| 事项 | 研究者决定（11-06） | 说明与后续 |
|---|---|---|
| 1 是否延长窗口或做上下文长度扫描 | 视情况延长：先查新版 GD / GAM 的生命体征与检验密度是否满足条件 | MC-MED 输入的稀疏程度原本按旧版 GD / GAM 设定；新版数据更密。检查项见『窗口密度检查』。延长属于改 benchmark 设定，需登记新版本；未延长前，上下文相关解释仍只写“与假设一致” |
| 2 VIMTS 是否归入基础模型组 | 不归入；放在不规则时序专用模型组 | 与 GRU-D、mTAND、Raindrop 等同组比较；zero-shot 口径只用于其余基础模型 |
| 3 子集清单、切点、最小规模与子集主要指标 | 老年从 65 岁起算，按 65–74 / ≥75 切分；其余按建议 | 主指标 AUROC + 校准，AUPRC 与患病率并列；每个子集至少约 30 个事件。只用于子集审计，项目 D70（≥60 岁主分析、≥65 岁亚组）不变；子集表另报 ≥60 以便对齐（11-06 确认） |
| 4 MIRA 与 MIMIC-IV 的重叠 | MIRA 分开考虑 | 在 MIMIC-IV / MIMIC-IV-ED 上的结果单独成表并标注预训练重叠，不与其他模型合并排名 |
| 5 子集发现与确认怎么切分 | 按建议 | 在验证集上做数据驱动的子集发现，在冻结测试集上确认；切分方式登记在案 |
| 6 标签变体与分组阈值是否纳入 | 按建议 | 主分析用原标签与单一阈值；去掉 SpO2 分量的标签、年龄校正阈值、分组阈值都只作敏感性分析 |

延长窗口前的密度检查（建议；在本地对 GD / GAM 运行，只交回聚合量）：

| 检查项 | 聚合量（只交回汇总） | 用途 |
|---|---|---|
| 1 每例观测数 | 各生命体征 / 检验在候选窗口内的每例观测数中位数与 IQR，分 GD / GAM、新旧版本；候选窗口长度需研究者定 | 判断新版数据能支撑多长的输入窗口 |
| 2 覆盖率 | 窗口内至少 1 次、至少 3 次观测的就诊比例（每个变量） | 避免窗口变长但多数人仍无观测 |
| 3 观测间隔 | 相邻两次观测间隔的中位数与 IQR | 决定 MC-MED 降采样或 drop 的强度 |
| 4 同时观测 | 核心体征在窗口内都有观测的就诊比例 | 多变量模型的可用样本量 |
| 5 按年龄分层 | 上述 1–4 按 <65 / 65–74 / ≥75 分层 | 观测密度随年龄变化本身是子集差异来源（C3） |
| 6 判定 | 若新版 GD / GAM 在更长窗口内仍有足够观测，就把 MC-MED 窗口延长到相应长度，并按新版密度重设降采样与 drop；“足够”的阈值需研究者定 | 让 MC-MED 设定继续代表医院数据 |

## A7. 来源（子集调研）

| 文献 | 链接 | 阅读范围 |
|---|---|---|
| Chen et al. 2023 MC-BEC | https://arxiv.org/abs/2311.04937 | 正文与 Table 2–5 逐字；附录为工具摘要 |
| Kansal et al. 2025 MC-MED | https://doi.org/10.1038/s41597-025-05419-5 | 正文；PhysioNet Table 11 为工具摘要 |
| MC-MED PhysioNet 1.0.0 | https://physionet.org/content/mc-med/1.0.0/ | 部分 |
| Gustafsson et al. 2026 SignalMC-MED | https://arxiv.org/abs/2603.09940 | 正文约一半 |
| Xie et al. 2022 MIMIC-IV-ED 基准 | https://arxiv.org/abs/2111.11017 | 正文 |
| Lett et al. 2025 JAMA Netw Open | https://doi.org/10.1001/jamanetworkopen.2025.12947 | 正文 |
| Liu et al. FAIM | https://arxiv.org/abs/2403.05235 | 全文含表 |
| Röösli et al. 2022 Sci Data | https://doi.org/10.1038/s41597-021-01110-7 | 全文 |
| Meng et al. 2022 Sci Rep | https://doi.org/10.1038/s41598-022-11012-2 | 摘要 |
| Guo et al. 2022 Sci Rep | https://doi.org/10.1038/s41598-022-06484-1 | 摘要 |
| Zhang et al. 2021 CHIL | https://arxiv.org/abs/2103.11163 | 正文部分逐字 |
| Shi et al. 2025 BMC MIDM | https://doi.org/10.1186/s12911-025-03058-9 | 全文 |
| Agniel et al. 2018 BMJ | https://doi.org/10.1136/bmj.k1479 | 正文与表 |
| Jeanselme et al. 2022 ML4H | https://proceedings.mlr.press/v193/jeanselme22a.html | 部分 |
| Wong et al. 2021 JAMA Netw Open | https://doi.org/10.1001/jamanetworkopen.2021.31674 | 摘要 |
| Mettler et al. 2024 medRxiv | https://www.medrxiv.org/content/10.1101/2024.03.28.24305036v1 | 摘要 |
| Pradhan et al. 2025 Front Med | https://doi.org/10.3389/fmed.2025.1606254 | 部分 |
| Platts-Mills et al. 2010 | https://doi.org/10.1111/j.1553-2712.2010.00670.x | 摘要 |
| Grossmann et al. 2014 | https://doi.org/10.1371/journal.pone.0106203 | 摘要 |
| Sax et al. 2023 | https://doi.org/10.1001/jamanetworkopen.2023.3404 | 摘要 |
| Kemp et al. 2020 | https://doi.org/10.1186/s12873-020-00379-y | 摘要 |
| Martín-Conty et al. 2024 | https://doi.org/10.1093/qjmed/hcae031 | 摘要 |
| Subbaswamy et al. 2024 AFISP | https://doi.org/10.1038/s41746-024-01275-6 | 全文 |
| Seyyed-Kalantari et al. 2021 | https://pubmed.ncbi.nlm.nih.gov/34893776/ | 摘要 |
| Oakden-Rayner et al. 2020 | https://arxiv.org/abs/1909.12475 | 扩展摘要全文 |
| McDermott et al. 2024 | https://arxiv.org/abs/2401.06091 | 正文部分逐字 |
| Yang et al. 2023 SubpopBench | https://proceedings.mlr.press/v202/yang23s.html | 正文部分逐字 |
| Eyuboglu et al. 2022 Domino | https://arxiv.org/abs/2203.14960 | 正文部分逐字 |
| Barda et al. 2021 JAMIA | https://doi.org/10.1093/jamia/ocaa283 | 摘要 |
| Pfohl et al. 2021 JBI | https://doi.org/10.1016/j.jbi.2020.103621 | 摘要 |
| Chen, Johansson, Sontag 2018 | https://arxiv.org/abs/1805.12002 | 摘要 |
| Tan, Shen, Chen 2026 | https://arxiv.org/abs/2604.03478 | 正文约三分之二 |
| Locati et al. 2026 ICML 研讨会 | https://icml.cc/virtual/2026/71757 | 摘要 |

# B 部分：时序基础模型背景（2026-11-05）

## 0. 口径

| 项目 | 说明 |
|---|---|
| 调研日期 | 2026-11-05；只做文献与模型背景调研，未跑任何实验 |
| 数据安全 | 全文只用论文、模型卡与项目已有聚合结果，没有接触 MC-MED / MIMIC / eICU 的逐条记录 |
| Medical 标签 | Yes：语料全部或主要为医疗；Partial：论文列出部分医疗数据（注明是生理信号还是公共卫生计数）；No：语料清单里没有医疗；Not reported：论文没有给出可判断的清单。医疗占比没给就写 Not reported，不估算 |
| ICU / ED | 分开写；只有论文或数据卡明确写出才算 'Yes'，不按数据集名称推断 |
| Time scale | Long-context oriented：论文把长上下文作为设计目标，或训练 / 评价上下文 ≥ 约 1000；Medium：上下文 ≤512 且论文未强调长上下文；Mixed / unclear：按数据集变化或未报告。每个判断在 '时间尺度依据' 列写出论文位置 |
| Zero-shot | 表中所有 'ZS forecasting' 都指 '在训练未见的数据集上直接做数值预测'，不是零样本临床结局预测。VIMTS 需要在目标集训练，标为 '无 ZS' |
| MC-MED 维度 | D1 床旁 / ICU 生理数据；D2 急诊场景；D3 不规则 / 缺失原生处理；D4 15 点短窗口可直接输入（✓ 点级 token 或时间戳；△ 能输入但只形成 1 个填充 token 或需特殊处理；✗ 依赖周期 / lag / 固定长输入）；D5 多变量联合建模。✓ 有论文证据，△ 部分或不明确，✗ 无或未报告 |
| 两个评级 | 预训练分布相似度：看 D1、D2 与语料组成；输入设计适配度：看 D3、D4、D5。两者分开评，综合列只作排序参考，是研究者可以改的判断 |
| 15 点窗口 | 按 MC-MED 1 分钟均值、0–15 分钟输入推算：每个变量每个窗口至多约 15 个点。表中 '约等于几个 token' 是按 patch 长度推算，不是实验结果 |
| 阅读范围标记 | '原文' = 读到了相应段落原文；'摘要级' = 只看到摘要或转述；'Not seen' = 未读到。凭记忆的内容已标 '凭记忆，需核对原文' |
| 名称辨析 | VIMTS = Hu et al. ICML 2025（arXiv 2505.22815）；Aurora = 华东师大多模态预测模型（ICLR 2026，arXiv 2509.22295），不是微软气象模型；TimesFM 3.0 只有模型卡与博客，无论文；Chronos-Bolt 无论文 |
| 失效解释的写法 | 不写 '因为预训练没有 ED，所以表现差'；有证据时写 '这一结果与预训练分布不匹配的假设一致'，并注明证据来源与类型 |

## 1. 一页结论（时序基础模型部分）


范围：14 个主模型 + 7 个补充模型，纯文献调研。MC-MED 设定指 decomp_60、六项生命体征、0–15 分钟输入；按 1 分钟均值推算，每个变量每个窗口至多约 15 个点。

**总判断：** 所有被比较的模型都不是为 "15 分钟、多变量、带缺失的急诊生命体征" 设计或评测的。最接近的是 MIRA（见过 ICU 生命体征，原生支持不规则时间），但它也是 ICU 住院场景、单变量、只训练数值预测。没有一篇模型论文做过患者层面的亚组分析，所以 Age / Gender / ESI 亚组的结果只能从数据侧解释，不能引用论文作为先验。

**Q1 哪些模型偏长上下文？**
- Long-context oriented（有论文依据）：Time-MoE（≤4096）、Sundial（2880）、Timer-XL（2880，标题即 Long-Context）、Moirai 1.x（零样本上下文 1000–5000）、VisionTS（1728–4032）、Chronos-2（8192）、TimesFM 2.5 / 3.0（16k / 15,360，仅模型卡）。
- Medium（≤512）：MIRA、TimesFM 1.0、Chronos、LightGTS、MOMENT。Mixed / unclear：VIMTS、Aurora、Moirai 2.0。
- 主模型论文里做过的最短上下文实验是 Moirai 的 100 点（Fig 5）和 Sundial 的 480 点（Fig 10）；补充模型 Lag-Llama 的连续窗口超参搜索到 32 点，但其 lag 特征需要更长历史；Timer-XL Fig 3 的最短 lookback 以时间跨度（8 小时）表示，折合点数未核对。15 点量级没有直接证据。15 分钟窗口在 Sundial、TimesFM、Timer-XL、Moirai、Aurora 里只能形成 1 个部分填充的 token（按 patch 长度推算）。

**Q2 哪些真正见过医疗数据？**
- 床旁生理 / ICU 数据：只有 MIRA（MIMIC-III 88%、MIMIC-IV 10.6%，语料 100% 医疗，App E Table 7）。
- 少量生理波形：Sundial（ECG 4.65%）、Timer-XL（经 UTSD：EEG / ECG / PPG / 心率）、LightGTS（EEG / ECG / 动物血压）、MOMENT（ECG 类）。
- 只有公共卫生汇总计数：Time-MoE（0.0001%）、Moirai 1.x（0.01%）、TimesFM 2.0（CDC FluView）。Aurora 有 Health 领域但未列数据集。
- Not reported：TimesFM 2.5 / 3.0、Chronos-2、Moirai 2.0（GiftEvalPretrain 清单未公开）。No：TimesFM 1.0、Chronos、VisionTS、Lag-Llama。
- 明确见过 ED 时序的：没有。MIRA 只说 MIMIC-IV 覆盖急诊入院，未说明用了 ED 模块。

**Q3 哪些支持不规则时间？**
- 原生时间戳：MIRA（CT-RoPE + Neural ODE，可零样本）、VIMTS（连续时间嵌入 + 可用性 mask，但必须在目标集训练）。
- 只有缺失 mask、没有时间间隔：Chronos（PAD token）、Chronos-2、Moirai 2.0、MOMENT。其余都假设规则网格；TimesFM 2.0 模型卡要求先线性插值。

**Q4 哪些论文已经发现短上下文 / 亚组 / 域偏移问题？**
- 短上下文：Timer-XL 明确说短输入 "insufficient learning of global tendencies"（Sec 1、Fig 3）；Chronos（Fig 11b）、Moirai（Fig 5）、VisionTS（Fig 6）都显示上下文越长越好。这些实验都在 ≥100 点的范围，不能直接外推到 15 点。反向线索：TimesFM 1.0 训练时覆盖 1–512 的所有长度；Chronos-2 称上下文学习在短上下文任务上收益最大。
- 高频：Sundial 自述 "very high-frequency data is not guaranteed"（App E）；GIFT-Eval 发现高频数据是基础模型的弱项（Sec 4.1）。
- 亚组：只到数据集 / 领域 / 频率 / 预测长度；没有年龄、性别或病情严重度分层。
- 域偏移：TimesFM 去掉合成数据后欠代表频率变差（Fig 3d）；Moirai 数据多样性消融（Table 7）；LightGTS 采样粒度实验（Fig 4）。独立评测 Gu et al.（ML4H 2024）在 eICU / MIMIC-III 体征上发现多数 TSFM 零样本不如从头训练的传统模型，异常值检测差。

**Q5 哪些模型与 MC-MED 的预训练分布差异最大？**
- 最大：VisionTS（只有 ImageNet，且要按周期折图）、LightGTS（周期 tokenization）、Lag-Llama（lag 特征需要长历史）、Time-MoE（90.5% 气象）、TimesFM 1.0 与 Chronos（无医疗）。
- 最接近：MIRA（数据层面）、VIMTS（输入设计层面，但不是零样本基础模型）。

**对本项目的含义（建议；涉及窗口与指标的需研究者决定）**
1. 结果表加 "每个模型实际 token 数 / 窗口内有效观测点数" 两列，作为解释的第一层证据。
2. 论文里的 zero-shot 都是数值预测。MC-MED 上用冻结嵌入 + 分类器的，应称 "冻结表示 + 探针"，不叫零样本临床预测。
3. Age / Gender / ESI 亚组先报告数据侧差异（观测密度、基线体征、事件率、实际输入长度），再判断某个结果是否 "与预训练分布不匹配的假设一致"。
4. 是否延长输入窗口或做上下文长度扫描属于 "t0 与窗口"，需研究者决定。
5. 若用 MIMIC-IV-ED 做外部验证，MIRA 预训练含 MIMIC-IV，需先排查重叠。


## 2. 主表（精简版；完整字段见 xlsx『主表』『主表_全部字段』）

| Model | Native task | Pretraining data | Scale | Medical | ICU / ED | Time scale | Context | Irregular | Missing | Zero-shot | Subgroup | Robustness | Domain shift | Context-length analysis |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MIRA | 点预测（单变量，时间戳条件） | MIMIC-III/IV、WAVES、PTB-XL、Sleep-EDF；从 Time-MoE 续训 | 454B | Yes | ICU 是；ED 不明确 | Medium（证据有限） | ≤512 | 原生时间戳（CT-RoPE + ODE） | 允许 NaN，推理处理未说明 | ZS forecasting | 仅数据集 | 缺失率 10–90%（FluNet） | OOD vs ID | 无 |
| Time-MoE | 自回归点预测 | Time-300B（Nature 90.5%） | 309B | Partial（0.0001%） | 否；否 | Long | ≤4096 | 否 | 仅清洗时切分 | ZS forecasting | 数据集 × 长度 | 无 | 零样本 vs 微调 | 无 |
| Sundial | 概率预测（流匹配） | TimeBench（ERA5 62%，ECG 4.65%） | 1032B | Partial（ECG） | NR；否 | Long | 2880，patch 16 | 否 | 未报告 | ZS 概率预测 | 数据集 | 无 | 数据规模 94B→1032B | Fig 10：480–2880，依任务 |
| TimesFM 1.0 | 点预测 | Wiki、Trends、合成等 | 约 100B | No | 否；否 | Medium | 512，patch 32 | 否 | padding mask | ZS forecasting | 数据集 | 无 | 去掉合成数据→欠代表频率变差 | 无扫描；随机遮蔽覆盖 1–512 |
| TimesFM 2.5 / 3.0 | 分位数预测；3.0 多变量 + 协变量 | GiftEvalPretrain + Wiki + Trends + 合成 | 3.0 >1T | NR（2.0 Partial） | NR；NR | Long | 16k / 15,360 | NR | 2.0 需线性插值 | ZS forecasting | NR | NR | NR | NR |
| Timer-XL | 预测（单 / 多变量 / 协变量） | UTSD + LOTSA；ERA5 | 约 232B | Partial（EEG/ECG/PPG/HR） | NR；否 | Long | 2880，patch 96 | NR | NR | ZS forecasting | 数据集 × 长度 | 3 个种子 | 跨时间 / 站点 | Fig 3、Table 15：越长越好至月级 |
| VisionTS | 点预测（图像重建） | 只有 ImageNet | 不适用 | No | 否；否 | Long | 1728–4032 | 否（需周期） | NR | 跨模态 ZS | 数据集 | 无 | 嵌入分布（Fig 7） | Fig 6：L 越长越好 |
| VIMTS | 不规则多变量预测 | ImageNet MAE + 目标集自监督 | 数据集级 | Partial（目标集） | ICU（目标集）；否 | Mixed | 24 h（ICU） | 原生（连续时间嵌入） | 原生 mask + GCN | 无 ZS | 数据集 | 无 | 无 | 无 |
| Aurora | 多模态概率预测 | 跨域多模态语料（含 Health） | >1B 点 | Partial | NR；NR | Mixed | NR（README 528） | 否 | NR | ZS（单 / 多模态） | TimeMMD 领域（含 Health） | 无 | 零样本 vs 10% few-shot | 无 |
| LightGTS | 预测（周期 token） | 33 个数据集（含 EEG/ECG） | NR | Partial | NR；否 | Medium | 约 10 个周期 | 否（需周期） | NR | ZS forecasting | 数据集 × 长度 | 采样粒度（Fig 4） | 跨时间尺度（Fig 2b） | 无 |
| Chronos / Bolt | 概率预测（量化 token） | 28 个真实数据集 + 合成 | 约 84B | No | 否；否 | Medium | 512 | 否 | PAD token | ZS 概率预测 | 数据集 | 合成模式（Fig 12、16） | Benchmark I vs II | Fig 11b：到 1024 前越长越好 |
| Chronos-2 | 单 / 多变量 / 协变量预测（ICL） | Chronos / GIFT 子集 + 合成 | NR | NR | NR；NR | Long | 8192 | 否 | 二值 mask | ZS（含多变量） | fev 任务子集 | 无 | 纯合成版本 | Fig 8c：8K > 2K；ICL 利于短上下文 |
| Moirai 1.x | 概率预测（any-variate） | LOTSA（Healthcare 0.01%） | 27.6B | Partial（计数） | 否；否 | Long | 评价 1000–5000 | 否 | NR | ZS 概率预测 | 数据集 | 无 | 数据多样性（Table 7） | Fig 5：100–5000 越长越好 |
| Moirai 2.0 | 单变量分位数预测 | GIFT Pretrain + 合成 + 内部遥测 | 约 295B | NR | NR；NR | Mixed | NR | NR | 缺失指示 | ZS forecasting | GIFT 领域 / 长度 | 无 | 领域排名 | 无 |

NR = Not reported；ZS = zero-shot。


## 3. 预训练分布 vs MC-MED

MC-MED 目标画像：

| 项目 | 内容 |
|---|---|
| 场景 | 斯坦福成人急诊有监护床位，2020-09 至 2022-09，118,385 次就诊（PhysioNet 页面，项目 research/数据集资源/ed-datasets-20261103 S122） |
| 采样 | 监护数值为 1 分钟均值；另有 ECG/PPG/呼吸波形（同上） |
| 本项目任务 | decomp_60；六项生命体征；输入窗口 0–15 分钟（项目背景 §6.4）→ 每个变量每个窗口至多约 15 个点（由 1 分钟均值推算） |
| 观测特点 | 短窗口、多变量、存在缺失与断续；项目已做 drop20 / drop40 / continuous5min 删减 |
| 下游目标 | 二分类结局（不是数值预测）；拟做 Age、Gender、ESI 亚组 |


| Model | Pretraining mainly long/short | Medical | Irregular | High-frequency vitals | ED data | Similarity to MC-MED | Potential mismatch |
|---|---|---|---|---|---|---|---|
| MIRA | 中等（≤512 点，点级 token） | Yes（100% 医疗语料，但从 Time-MoE 通用权重续训） | Yes：预训练含不规则 MIMIC-III；原生时间戳输入 | ICU 生命体征（频率未报告）+ 100 Hz 波形；无 1 分钟监护数值的明确证据 | 不明确（MIMIC-IV 描述含急诊入院，未说明用 ED 模块） | 中（本表最接近，但仍有明显差距） | ①人群与时段：成人 ICU 住院（MIMIC-III 2001–2012）而非急诊到院后 15 分钟；②单变量、通道独立，六项体征之间不交互；③只训练数值预测，不涉及结局；④NaN / mask 在推理中如何处理未说明；⑤若以后用 MIMIC-IV-ED 做外部验证，MIRA 预训练含 MIMIC-IV，需排查重叠 |
| Time-MoE | 长（≤4096；评价输入 512–3072） | Partial（公共卫生计数 0.0001%） | No（缺失处切分清洗） | No | No | 很低 | 90.5% 为 Nature（气象）数据；预训练把缺失段切掉，模型没见过带缺失的短窗；点级 token 能接收 15 个点，但没有短上下文的评价或消融 |
| Sundial | 长（≤2880；lookback 实验 480–2880） | Partial（ECG 48B，4.65%） | No | 只有 ECG 波形；无生命体征数值 | No | 低 | patch 长 16：15 分钟窗口（约 15 点）不足一个 patch，只能靠左侧填充成 1 个 token；作者自述 '高频数据表现无保证'；62% 为 ERA5 气象；单变量 |
| TimesFM 1.0 | 中等（≤512，训练覆盖 1–512） | No | No | No | No | 很低 | 语料以 Wiki 浏览量、Google Trends 为主；输入 patch 32 > 15 点，整段上下文只构成一个部分填充的 patch，归一化统计量也只来自这 ≤15 个点；单变量 |
| TimesFM 2.5 / 3.0 | 长（16k / 15,360） | Not reported（2.0 含 CDC 流感监测） | Not reported | Not reported | Not reported | 低 | 无论文，预训练组成只到 GiftEvalPretrain 一级；3.0 支持多变量与协变量，但 patch 32 > 15 点；2.0 模型卡要求先线性插值缺失；权重非商用 |
| Timer-XL | 长（2880；标题即 Long-Context） | Partial（UTSD 的 EEG/ECG/PPG/心率；LOTSA 计数） | Not reported | Partial（BIDMC32HR 心率、IEEEPPG） | No | 低 | patch 96 ≫ 15 点；作者明言短上下文 'leads to insufficient learning of global tendencies'；最佳 lookback 在日到月量级；零样本权重为单变量预训练 |
| VisionTS | 长（各数据集调到 1728–4032） | No（只有 ImageNet） | No | No | No | 很低（与 MC-MED 差异最大之一） | 需要周期 P 把序列折成图像；15 分钟生命体征没有可用周期（P=1 退化为单列）；性能随 L 增加而提高；单变量、无概率输出 |
| VIMTS | 不适用（按数据集；ICU 24 h 窗口） | Partial（PhysioNet 2012、MIMIC 作为目标数据集训练） | Yes（原生） | ICU 体征与化验（目标数据集） | No | 设计最接近，但不是零样本基础模型 | 必须在 MC-MED 上自监督 + 训练，不能算 zero-shot；原论文 ICU 窗口为 24 h → 24 h，patch 8 个时间步，15 分钟窗口的分块需要重设；没有跨数据集迁移实验 |
| Aurora | 不明确（README 示例 528） | Partial（Health 领域，具体数据集未列） | No | Not reported | Not reported | 低 | 多模态依赖文本描述（预训练文本由 LLM 生成）；图像分支按 FFT 周期渲染；token 长 48 > 15 点；通道独立 |
| LightGTS | 中等（10 个周期 token，约 480–528 点） | Partial（EEG/ECG/动物血压） | No | No | No | 很低（与 MC-MED 差异最大之一） | tokenization 以周期长度为 patch，15 分钟窗口内的生命体征通常没有稳定周期；作者承认 FFT 周期不准时性能受损；无缺失处理 |
| Chronos / Chronos-Bolt | 中等（512） | No | No | No | No | 很低 | 训练集无医疗；均值缩放 + 量化对 '大均值、小方差' 序列精度下降（Fig 16b），SpO₂ 这类近乎平坦的序列正属此类；指数型 / 突变趋势预测失败（Fig 12b）；单变量 |
| Chronos-2 | 长（8192） | Not reported | No（有缺失 mask） | Not reported | Not reported | 低 | 多变量能力完全来自合成数据；真实数据清单未读到；有缺失 mask 但无时间间隔建模；作者称上下文学习对短历史有帮助，这一点与 MC-MED 方向一致 |
| Moirai（1.0/1.1） | 长（评价 1000–5000） | Partial（计数 0.01%） | No | No | No | 很低 | 分钟级数据的 patch 为 32/64/128，均 > 15 点；约 57% 观测来自模拟建筑数据（按 Table 8 计算）；论文未说明推理缺失处理 |
| Moirai 2.0 | 不明确（未报告） | Not reported | No（有缺失指示） | Not reported | Not reported | 很低 | 单变量；含内部 CloudOps 遥测；上下文长度未报告；作者称语料对自然类数据代表性不足 |
| MOMENT（补充） | 中等（固定 512） | Partial（ILI、UCR/UEA 的 ECG 类、异常检测中的人体信号） | No（有观测 mask） | Partial（ECG 类波形） | No | 低 | 输入固定 512，短于 512 的序列左侧补零：15 点窗口约 97% 为填充；单变量 |
| Lag-Llama（补充） | 短连续窗口（最优 32）+ 长 lag 历史 | No | No | No | No | 很低 | lag 特征 'requires an L-sized or larger context window'（Sec 4.1），15 点窗口下绝大多数 lag 取不到；语料 6 个领域无医疗 |

评分细项（✓ 有论文证据；△ 部分 / 不明确；✗ 无或未报告）：

| Model | D1 生理/ICU | D2 急诊 | D3 不规则/缺失 | D4 15 点短窗 | D5 多变量 | 预训练分布相似度 | 输入设计适配度 | 依据 |
|---|---|---|---|---|---|---|---|---|
| MIRA | ✓ | △ | ✓ | ✓ | ✗ | 中（全表最高） | 中 | Table 7、App E（语料）；Sec 3.1–3.2（时间戳、CT-RoPE、ODE）；Sec 3.3（Time-MoE 初始化）；Table 6（512） |
| Time-MoE | ✗ | ✗ | ✗ | △ | ✗ | 很低 | 低 | Table 1、Table 10、App C；Sec 3.2.3、Sec 4.1 |
| Sundial | △ | ✗ | ✗ | ✗ | ✗ | 低 | 低 | Table 4、Table 5（patch 16）、Sec 4.1.1、App E、App C.3 Fig 10 |
| TimesFM 1.0 | ✗ | ✗ | ✗ | △ | ✗ | 很低 | 低—中 | Table 1、Sec 4（Patch Masking）、Sec 5（归一化） |
| TimesFM 2.5 / 3.0 | ✗ | ✗ | ✗ | △ | ✓（3.0） | 很低 / 未知 | 中（3.0） | HF 模型卡、README、Google Research 博客 |
| Timer-XL | △ | ✗ | ✗ | ✗ | ✓ | 低 | 低 | Sec 1、Sec 4.1 Fig 3、App E.4 Table 15、Table 9/11、UTSD HF 卡 |
| VisionTS | ✗ | ✗ | ✗ | ✗ | ✗ | 无（无时序预训练） | 很低 | Abstract、Sec 3、Sec 4.2 Fig 6、Sec 6 |
| VIMTS | △ | ✗ | ✓ | △ | ✓ | 不适用（视觉 MAE + 目标数据集自监督） | 高 | Sec 2.3、Sec 2.6、Sec 3.1、Table 2、Sec 6 |
| Aurora | △ | ✗ | ✗ | ✗ | ✗ | 低 | 低 | App A.1（v1）、Sec 3.1.1、Sec 4.1、README |
| LightGTS | △ | ✗ | ✗ | ✗ | ✗ | 低 | 很低 | Sec 3.1.1、App A.4、App B.1、Table 7 |
| Chronos / Chronos-Bolt | ✗ | ✗ | △ | ✓ | ✗ | 很低 | 中—低 | Table 3、Sec 3.1、Sec 5.7 Figs 12、16 |
| Chronos-2 | ✗ | ✗ | △ | △ | ✓ | 很低 / 未知 | 中 | Sec 3.1、Sec 3.3、Sec 4.2、Sec 5.2、Sec 6 |
| Moirai（1.0/1.1） | ✗ | ✗ | ✗ | ✗ | ✓ | 很低 | 低—中 | Table 2、Table 3、Table 8、App B.1、Sec 4.4 Fig 5 |
| Moirai 2.0 | ✗ | ✗ | △ | △ | ✗ | 很低 / 未知 | 低—中 | Sec 3.1、Sec 4、Sec 5.1 Figs 3–4 |
| MOMENT（补充） | △ | ✗ | △ | ✗ | ✗ | 低 | 低 | Sec 3.1–3.2（本机 PDF） |
| Lag-Llama（补充） | ✗ | ✗ | ✗ | ✗ | ✗ | 很低 | 很低 | Sec 4.1、Sec 5.1、Table 5（本机 PDF） |

## 4. 上下文长度证据（最重要的一项）

| Model | 训练 / 最大上下文 | 输入切分方式 | 15 点窗口约等于几个 token（推算） | 论文中的上下文长度实验 | 实验里最短的上下文 | 结论方向 | 位置 |
|---|---|---|---|---|---|---|---|
| MIRA | ≤512 点 | 点级 token + 连续时间戳 | 15 | 无 | — | Not reported | Table 6；全文无上下文实验 |
| Time-MoE | ≤4096（含预测段） | 点级 token | 15 | 无单独消融；评价输入 512–3072 与预测长度绑定 | 512（评价设定） | Not reported | Sec 4.1 |
| Sundial | 2880 | patch 16 | 1（左侧填充 1 点） | TSLib lookback 480 / 960 / 1440 / 1920 / 2400 / 2880 | 480 | 依任务而定，应按预测长度与周期调 | App C.3 Fig 10 |
| TimesFM 1.0 | 512 | 输入 patch 32 | 1（填充 17 点） | 无长度扫描；Fig 3c 只比较 patch 长度 8–128 | — | 设计上用随机遮蔽覆盖 1–512 的所有上下文长度 | Sec 4 'Patch Masking'；Fig 3c |
| TimesFM 2.5 / 3.0 | 16k / 15,360 | 3.0：输入 patch 32 | 1 | Not reported（无论文） | — | Not reported | README、模型卡 |
| Timer-XL | 2880（ERA5 3072） | patch 96 | 1（填充 81 点） | Fig 3 lookback 8 小时→1 年；Table 15 与 DLinear、PatchTST 比较；Fig 8 推理 lookback 96–3072；Fig 5b 预训练上下文 1440 vs 2880 | 8 小时（以时间跨度表示） | 日→月持续改善，月 / 年后放缓或变差；作者明言短上下文学不到全局趋势 | Sec 1；Sec 4.1 Fig 3；App E.4 Table 15；Fig 5b、Fig 8 |
| VisionTS | 各数据集调到 1728–4032 | 按周期 P 折成图像，再切 16×16 图像 patch | 取决于 P；无周期时 P=1 | Fig 6 改变上下文长度 L | 未读到具体取值 | L 越长越好，高频数据尤甚 | Sec 4.2 Fig 6；App B.1 Table 8 |
| VIMTS | 按数据集（ICU 24 h） | 等长时间窗 patch（ICU 为 8 个时间步）+ TTCN 聚合 | 需重设窗长 | 无（只扫隐藏维、patch 大小、mask 比例等） | — | Not reported | Table 2；App A.5；Figs 5–9 |
| Aurora | Not reported（README 示例 528） | token 长 48 | 1 | 正文无；附录未读到 | — | Not reported | README；Sec 3.1.1 |
| LightGTS | 10 个周期 token（约 480–528 点） | patch = 周期长度 | ≤1（15 分钟内通常无稳定周期） | 无（N 固定为 10） | — | Not reported | App A.4；README |
| Chronos | 512 | 点级量化 token | 15 | 用 4 种训练上下文长度训练 Chronos-T5-Small | 见 Fig 11b | 到 1024 前越长越好，再长持平或变差 | Sec 5.6 Fig 11b |
| Chronos-Bolt | README 未写 | patch 输入（长度 README 未写） | Not reported | 无论文 | — | Not reported | README |
| Chronos-2 | 8192（两阶段 2048→8192） | patch（长度正文未写） | Not reported | Fig 8c：2K 与 8K 上下文后训练比较 | 2048 | 8K 更好（高频数据多的 GIFT-Eval 最明显）；上下文学习在短上下文任务上收益最大 | Sec 5.4 Fig 8c；Sec 5.2 |
| Moirai（1.0/1.1） | 训练 ≤512 token；评价 1000–5000 | 按频率选 patch：分钟级 32/64/128 | 1 | Fig 5：上下文 100–5000 | 100 | 越长越好 | Sec 4.4 Fig 5；App B.1 |
| Moirai 2.0 | Not reported | patch（长度未报告） | Not reported | 无（只有约 10K 上下文的速度测试） | — | Not reported | Sec 3.3 |
| MOMENT（补充） | 固定 512 | patch 8，短序列左侧补零 | 2（其余约 97% 为填充） | Not reported | — | Not reported | Sec 3.2 |
| Lag-Llama（补充） | 连续窗口 C 搜索 32–1024 | 点级 token + 长 lag 特征 | 15，但多数 lag 取不到 | C 的超参搜索 | 32（最优） | 短连续窗口最优，但依赖足够长的历史来取 lag | Sec 4.1；Table 5 |
| Gu et al. 2024（独立评测） | 默认历史 6 h（5 分钟重采样） | — | — | eICU 上改变历史窗口 | 见 Fig 3 | 多数情况下历史越长越好 | Sec 4.2 Fig 3 |

## 5. 已知失效模式证据矩阵

证据类型从强到弱：直接实验 > 独立评测 > 作者陈述 / 作者分析 > 设计推断 > 无证据。项目内实验单列。

| 可能的失效模式 | 模型 / 来源 | 论文里的证据 | 位置 | 证据类型 | 将来可用的表述 |
|---|---|---|---|---|---|
| 短 context 下差 | Timer-XL | 'a short-context input leads to insufficient learning of global tendencies'；lookback 从日延长到月持续改善 | Sec 1；Sec 4.1 Fig 3；App E.4 Table 15 | 作者陈述 + 直接实验（长上下文方向） | 与 '输入远短于模型设计与评测所用上下文' 的假设一致 |
| 短 context 下差 | Chronos | 训练上下文长度增加到 1024 前，域内与零样本均改善 | Sec 5.6 Fig 11b | 直接实验（只测到较长一端） | 同上；注意该实验未测极短上下文 |
| 短 context 下差 | Moirai | 上下文 100→5000，验证集 MAE 下降 | Sec 4.4 Fig 5 | 直接实验（最短 100） | 同上；最短 100 点仍远长于 MC-MED 的约 15 点 |
| 短 context 下差 | VisionTS | L 增大性能提高，高频数据尤甚 | Sec 4.2 Fig 6 | 直接实验 | 同上 |
| 短 context 下差 | Sundial | lookback 480–2880，结论 '取决于任务' | App C.3 Fig 10 | 直接实验（未测 <480） | 不能作为短上下文证据，只说明未被检验 |
| 短 context 下差 | Gu et al. 2024（ML4H，eICU / MIMIC-III 体征） | 'longer historical windows tend to improve performance in most cases' | Sec 4.2 Fig 3 | 独立评测，直接实验 | 临床体征上也观察到历史越长越好 |
| 短 context 下差（反向证据） | TimesFM 1.0 | 训练时随机遮蔽，使模型见到 1–512 的所有上下文长度 | Sec 4 'Patch Masking' | 设计 | 若 TimesFM 在短窗口下仍好于其他模型，可能与此设计有关（需实验确认） |
| 短 context 下差（反向证据） | Chronos-2 | 上下文学习在 '很多短上下文任务' 的 CBII 上收益 'especially strong'；组共享对冷启动 / 短历史有帮助 | Sec 5.2；Sec 3.2 | 作者陈述 + 基准子集 | 多序列上下文学习可能缓解短窗口问题 |
| 短 context 下差（反向证据） | Al Attrach et al. 2026（ICLR 研讨会，MIMIC-IV） | 近期窗口只有 8 个事件时，缓存的基础模型摘要使 AUROC 相对提升 6.5%；256 个事件时只剩 0.1%（不显著） | 摘要 | 独立评测（只读到摘要） | 基础模型表示在短窗口下的价值可能反而最大，取决于是否带入更长的历史 |
| 短 context 下差（设计层） | Sundial / TimesFM / Timer-XL / Moirai / Aurora | patch 长度 16 / 32 / 96 / 分钟级 32–128 / 48，都 ≥ 15 点 | Sundial Table 5；TimesFM Sec 4；Timer-XL Table 11；Moirai App B.1；Aurora README | 设计推断（非实验） | 15 分钟窗口在这些模型里只形成一个（部分填充的）token，可作为解释假设，需用 '实际 token 数' 分层验证 |
| 分钟级 / 高频数据差 | Sundial | 'The performance on very high-frequency data is not guaranteed, since TimeBench contains many middle- and low-frequency time series' | App E | 作者陈述 | 与 '预训练频率分布偏中低频' 的假设一致 |
| 分钟级 / 高频数据差 | GIFT-Eval（基准论文） | 'higher frequency data ... poses challenges that foundation models are less suited to address' | Sec 4.1 Table 8 | 独立基准 | 同上 |
| 分钟级 / 高频数据差 | TimesFM 1.0 | 去掉合成数据后，15 分钟 ETTm 等代表性不足的频率明显变差 | Sec 6.2 Fig 3d | 直接消融 | 频率覆盖不足会伤害零样本表现 |
| 稀疏 / 缺失 / 不规则下差 | MIRA | WHO FluNet 缺失率 10%→90%，RMSE 2.85→3.97（不单调） | Sec 4.4 Table 4 | 直接实验 | 缺失增加时误差上升；注意是流感监测数据，不是体征 |
| 稀疏 / 缺失 / 不规则下差 | Chronos | 稀疏尖峰无法被量化 token 表示 | Sec 5.7 Fig 16a | 作者分析 | 与 tokenization 机制有关 |
| 稀疏 / 缺失 / 不规则下差 | Time-MoE / Moirai / Moirai 2.0 | 预训练前在缺失处切分或过滤缺失较多的序列 | Time-MoE App C；Moirai App A；Moirai 2.0 Sec 4 | 数据处理（设计） | 预训练很少见到带缺失的输入，与 '缺失分布不匹配' 的假设一致 |
| 稀疏 / 缺失 / 不规则下差 | TimesFM 2.0 | 模型卡要求有 NaN 时先线性插值、上下文须连续 | HF 模型卡 | 使用说明 | 插值方式本身是管线的一部分，需在报告中写明 |
| 稀疏 / 缺失 / 不规则下差（反向证据） | 本项目 week02 F3 | 稀疏到每变量 1 个值，TSFM 探针相对 LR 仍 +0.041 AUPRC；各模型 AUPRC 均降约 32–37% | 项目背景 §6.2 | 项目内实验 | 稀疏本身不一定让 TSFM 相对变差 |
| 稀疏 / 缺失 / 不规则下差 | LightGTS | 不同采样粒度下 LightGTS 稳定，Timer、Time-MoE 波动 | Sec 4.6 Fig 4 | 直接实验 | 固定 patch 的模型对采样粒度变化更敏感 |
| 高危 ESI / 急性变化下差 | （所有模型论文） | 无患者层面或病情严重度分层 | — | 无证据 | 不能说 '论文已发现'；只能写 '原论文未检验此情形' |
| 高危 ESI / 急性变化下差 | Gu et al. 2024 | TSFM 'performed poorly in detecting abnormal clinical values' | Table 4 | 独立评测 | 与 '模型对异常值 / 急性偏离不敏感' 的假设一致 |
| 高危 ESI / 急性变化下差 | Chronos | 线性趋势可以，指数趋势预测不足 | Sec 5.7 Fig 12b | 作者分析（合成数据） | 对快速恶化轨迹可能低估（需在高危组验证） |
| 高危 ESI / 急性变化下差 | Sundial | MSE 预训练导致单峰、过平滑预测；多步自回归可能过平滑 | App C.1；App E | 作者陈述 | 点误差训练的模型倾向均值回归 |
| 老年患者 / 性别亚组差 | （所有模型论文与已读独立评测） | 无年龄或性别分层结果 | — | 无证据 | 只能从数据侧解释（各亚组观测密度、基线体征分布、事件率、实际输入长度），不能归因于预训练 |
| 老年患者 / 性别亚组差 | MIRA | 语料来自 MIMIC-III/IV 成人 ICU，但年龄分布未报告 | App E | 无直接证据 | 不能推断 MIRA 对老年人更好或更差 |
| 跨院 / 分布偏移 | Pucher et al. 2026（AIIM） | 基础模型 'showed superior transportability across hospital settings and patient populations' | 摘要 | 独立评测（只读到摘要） | 跨院迁移上基础模型未必更差 |
| 跨院 / 分布偏移 | 本项目 week02 F2 | eICU 外部医院 12 个嵌入全部显著低于手工 LightGBM（−0.013 至 −0.054 AUPRC） | 项目背景 §6.2 | 项目内实验 | 冻结嵌入跨院不如手工特征 |
| 跨院 / 分布偏移 | Syed et al. 2026（ICML 立场论文） | 7 个 TSFM × 72 个数据集 × 6 个领域，'substantial cross-domain variability' | 摘要 | 独立评测（只读到摘要） | 领域差异大，医疗需单独基准 |
| 单变量模型丢失体征间关系 | Gu et al. 2024 | Moirai 加入全部五项体征后 'improved significantly'，传统模型没有类似收益 | Sec 4.3 Fig 4 | 独立评测 | 多变量输入可能有用；通道独立模型（多数 TSFM）用不到这一点 |
| 单变量模型丢失体征间关系 | Chronos-2 | 多变量收益 'modest' | Sec 5.2 | 作者陈述 | 多变量增益可能有限 |
| 平坦序列 / 尺度问题（如 SpO₂） | Chronos | 尺度大、方差小时 token 精度下降 | Sec 5.7 Fig 16b | 作者分析 | SpO₂ 等近乎恒定的变量可能受影响，可按变量分层检查 |
| 平坦序列 / 尺度问题（如 SpO₂） | TimesFM 1.0 / Sundial / Chronos-2 | 分别用首个 patch 的均值方差、样本内两阶段实例归一化、历史标准化 + arcsinh | TimesFM Sec 5；Sundial Sec 4.1.1；Chronos-2 Eq 1–2 | 设计 | 15 点窗口的统计量不稳定，是可检验的解释 |
| 零样本口径错位 | 所有预测型 TSFM | 论文中的 zero-shot 都是 '在未见数据集上做数值预测'，没有零样本临床结局预测 | 各论文零样本定义 | 定义 | MC-MED 上的 'zero-shot' 若加了分类头或线性探针，应改称冻结表示 / 线性探针 |
| 零样本口径错位 | 本项目 week02 F4 | 零标签 '预测轨迹 → 预警' AUROC 0.55–0.59 | 项目背景 §6.2 | 项目内实验 | 真正零标签的预警几乎没有判别力 |

## 6. 逐模型详细记录


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


### TimesFM 1.0

- **论文 / 来源**：A decoder-only foundation model for time-series forecasting（Abhimanyu Das, Weihao Kong, Rajat Sen, Yichen Zhou，Google Research）arXiv 2310.10688
- **年份**：2024
- **会议 / 期刊**：ICML 2024（PMLR 235:10148–10167）
- **是否开源 / 代码**：是：github.com/google-research/timesfm（代码 Apache-2.0）
- **公开 checkpoint**：HF TimesFM collection（1.0-200m；README 指向）；论文 200M（另有 17M/70M 消融，Fig 3a）
- **Native task（原生任务）**：零样本点预测；解码器，输入 patch 32、输出 patch 128（Sec 4）；MSE；单变量；预训练不含协变量（App A.1、A.7）
- **Pretraining data**：Wiki pageviews（约 300B 点）、Google Trends（约 0.5B）、合成 300 万条 × 2048（6.1B；ARMA/季节/趋势/阶跃，App A.8）、M4、Electricity、Traffic、Weather（10 分钟）、Favorita、LibCity（Table 1）；采样 80% 真实 / 20% 合成（Sec 5）
- **Scale**：O(100B) 时间点（Sec 1、Sec 7）
- **Medical data**：No
- **医疗数据明细（论文原文）**：Table 1 无任何医疗数据集
- **ICU seen?**：No
- **ED seen?**：No
- **生命体征 seen?**：No
- **预训练含不规则采样?**：No（全部为规则粒度）
- **预训练频率范围**：10 分钟（Weather）至年（M4）
- **Time scale 判断**：Medium
- **Time scale 依据**：最大上下文 512（周频 256、≥月频 64，Sec 5）；训练时随机遮蔽首个 patch 的一部分，使模型见到 1 到 512 的所有上下文长度（Sec 4 'Patch Masking'）
- **Context length**：≤512
- **Forecast horizon**：任意（输出 patch 128，自回归拼接）
- **Irregular support**：不支持（规则网格）
- **Missing support**：有左侧 padding mask（Sec 4）；含缺失值的 Monash 数据集被排除出评价（Sec 6.1）
- **Zero-shot type**：Zero-shot forecasting
- **Zero-shot 细节（排除 / 归一化 / 头）**：评价集 'intentionally held out from our pretraining data'（Sec 6）；用上下文首个 patch 的均值与标准差归一化（Sec 5）；部分 Monash 数据集在训练段末尾按 32/64/最大值选择上下文长度（App A.5.2）
- **Subgroup analysis**：按数据集（App A.5）；Monash / Darts / ETT 三组汇总（Fig 2）
- **Robustness**：Not reported
- **Domain shift**：零样本 vs 监督基线；ETT 微调（App A.3）；去掉合成数据后，代表性不足的频率（15 分钟 ETTm、季/年）明显变差（Fig 3d，Sec 6.2：'can make the model not generalize well to underrepresented frequencies'）
- **Context-length analysis**：无上下文长度扫描；Fig 3c 只比较输入 patch 长度 8–128（16、32 最好）；靠训练时随机遮蔽覆盖短上下文
- **作者自述局限 / 已知问题**：App A.1：概率预测与协变量不是本文重点；上下文长度是唯一可调的 '提示'
- **与本项目已有结果的关联**：week02 F1：零样本生命体征预测中 TimesFM 系列领先
- **阅读范围**：全文（本机 PDF，arXiv v4）


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


### VIMTS

- **论文 / 来源**：IMTS is Worth Time × Channel Patches: Visual Masked Autoencoders for Irregular Multivariate Time Series Prediction（Zhangyi Hu … Yutao Yue）arXiv 2505.22815；方法名 VIMTS
- **年份**：2025
- **会议 / 期刊**：ICML 2025
- **是否开源 / 代码**：是：github.com/WHU-HZY/VIMTS（MIT）
- **公开 checkpoint**：Not reported（README 要求每个数据集先跑 pretrain.sh 自监督，再微调）
- **Native task（原生任务）**：不规则多变量时序（IMTS）预测：给定观测与查询时间戳，预测各通道在查询时刻的值（Sec 2.2）；不是跨数据集通用基础模型
- **Pretraining data**：视觉 MAE-base 的图像预训练（RGB，App A.3）+ 在每个目标 IMTS 数据集上做掩码 patch 重建自监督（Sec 2.6），再监督微调
- **Scale**：不适用（数据集级：PhysioNet 12,000 样本、MIMIC 23,457 样本、Human Activity 5,400、USHCN 1,114，Table 2）
- **Medical data**：Partial（医疗数据只作为目标数据集训练与评价，不是跨数据集预训练）
- **医疗数据明细（论文原文）**：PhysioNet 2012（ICU，41 通道，缺失 85.7%）、MIMIC（README 为 MIMIC-III，96 通道，缺失 96.7%）（Table 2）
- **ICU seen?**：Yes（作为目标数据集）
- **ED seen?**：No
- **生命体征 seen?**：Yes（PhysioNet 2012 / MIMIC 的 ICU 体征与化验，作为目标数据集）
- **预训练含不规则采样?**：目标数据集高度不规则（Table 2）；图像预训练不适用
- **预训练频率范围**：按数据集：ICU 24 小时窗口；Human Activity 毫秒级；USHCN 月
- **Time scale 判断**：Mixed / unclear
- **Time scale 依据**：按数据集设定：PhysioNet、MIMIC 用 24 小时观测预测后 24 小时；Human Activity 3,000 ms→1,000 ms；USHCN 24 个月→下月（Table 2）；ICU 数据 patch 为 8 个时间步（App A.5）
- **Context length**：24 h（ICU）等，按数据集
- **Forecast horizon**：ICU：后 24 h
- **Irregular support**：原生支持：可学习的连续时间嵌入（Sec 2.3.1 Eq 1）；按等长时间窗切 patch，TTCN 聚合窗内不定数量的观测；不做插值（App A.2.3）
- **Missing support**：原生支持：可用性二值 mask（Sec 2.3.2 Eq 5）+ GCN 跨通道特征级补全（Sec 2.3.3）
- **Zero-shot type**：无 zero-shot（Sec 6：'hindering true zero-shot capabilities without parameter tuning'）
- **Zero-shot 细节（排除 / 归一化 / 头）**：每个数据集 60/20/20 切分、自监督 + 微调（Sec 3.1）；few-shot 10/20/50%（Table 5）；归一化 Not reported
- **Subgroup analysis**：只按数据集（Table 1）
- **Robustness**：Not reported（缺失率只作为数据集描述）
- **Domain shift**：Not reported（无跨数据集实验）
- **Context-length analysis**：Not reported（未改变观测窗口；Figs 5–9 只扫隐藏维、patch 大小、mask 比例、GCN 层数、嵌入维度）
- **作者自述局限 / 已知问题**：Sec 6：'current models are limited to fixed patch sizes and the number of channels'；无真正零样本；MAE 放大到 base 以上无收益（Sec 4.2）
- **与本项目已有结果的关联**：合作摘要 MC-MED decomp_60：VIMTS-Adapter AUPRC 0.159（XGBoost 0.317；非严格排名）
- **阅读范围**：正文 + App A.1–A.5、B.1–B.2 原文（B.2 之后为摘要级）


### Aurora

- **论文 / 来源**：Aurora: Towards Universal Generative Multimodal Time Series Forecasting（Xingjian Wu … Bin Yang, Chenjuan Guo，华东师大）arXiv 2509.22295。注：不是微软的气象模型 'Aurora: A foundation model for the Earth system'（Nature 2025）
- **年份**：2026（arXiv 2025-09）
- **会议 / 期刊**：ICLR 2026
- **是否开源 / 代码**：是：github.com/decisionintelligence/Aurora；pip aurora-model
- **公开 checkpoint**：HF DecisionIntelligence/Aurora（HF 卡标 0.2B 参数；论文未写参数量）
- **Native task（原生任务）**：生成式概率预测（token 级条件流匹配，Eq 25）；以 LLM 生成的文本描述和由序列渲染的图像为条件的多模态预测，也可单模态零样本（Sec 3、4.3）；通道独立 + RevIN
- **Pretraining data**：'Cross-Domain Multimodal Time Series Corpus'：ERA5、IoT、Monash、UEA、UCR 子集 + PRSA、医疗时序（引 Wang et al. 2024）、SCINet、FRED-MD、NN5（App A.1，v1）；文本描述由 LLM 生成（Sec 4.1）
- **Scale**：'more than 1 billion time series points'（App A.1，v1）
- **Medical data**：Partial
- **医疗数据明细（论文原文）**：App A.1：'both the pre-training and target sets incorporate weather, Energy, Health, and Economy data, they are from different sources'；健康类具体数据集与占比未列出（来源比例只在 Fig 6 图片中）
- **ICU seen?**：Not reported
- **ED seen?**：Not reported
- **生命体征 seen?**：Not reported
- **预训练含不规则采样?**：Not reported
- **预训练频率范围**：Not reported
- **Time scale 判断**：Mixed / unclear
- **Time scale 依据**：论文未给预训练与评价的上下文长度（App A.3 称各基线用其推荐长度）；README 示例 lookback 528、token 长 48
- **Context length**：Not reported（README 示例 528）
- **Forecast horizon**：按基准（App A.3）
- **Irregular support**：不支持：规则网格上的非重叠 patch + 左侧填充（Eq 1–2）
- **Missing support**：Not reported（只有预训练时对文本/图像模态的随机遮蔽，Sec 4.3）
- **Zero-shot type**：Zero-shot forecasting（单模态或多模态）
- **Zero-shot 细节（排除 / 归一化 / 头）**：'these benchmarking datasets are strictly excluded from the pretraining time series corpus'（Sec 4.1）；RevIN
- **Subgroup analysis**：Table 1：TimeMMD 9 个领域（含 Health）。Health 零样本 MSE/MAE：Aurora 1.553/0.850，Sundial 1.970/0.992，VisionTS 2.436/1.221，Moirai 2.736/1.241；Table 3：ProbTS 含 ILI（CRPS Aurora 0.147、Sundial 0.148、Chronos 0.170、Moirai 0.159）
- **Robustness**：Not reported
- **Domain shift**：零样本 vs 10% few-shot（Table 1）
- **Context-length analysis**：Not reported（正文无 lookback 实验；附录未读到）
- **作者自述局限 / 已知问题**：Not seen（未读到局限性章节）
- **阅读范围**：正文（v6）+ App A.1–A.4（v1）；ICLR 版附录未读到


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


### Chronos / Chronos-Bolt

- **论文 / 来源**：Chronos: Learning the Language of Time Series（Abdul Fatir Ansari, Lorenzo Stella … Yuyang Wang，Amazon）arXiv 2403.07815；Chronos-Bolt 无论文（README）
- **年份**：2024
- **会议 / 期刊**：TMLR（10/2024）
- **是否开源 / 代码**：是：github.com/amazon-science/chronos-forecasting（Apache-2.0）
- **公开 checkpoint**：amazon/chronos-t5-mini 20M / small 46M / base 200M / large 710M（Sec 5.2）；Chronos-Bolt tiny 9M / mini 21M / small 48M / base 205M（README）
- **Native task（原生任务）**：单变量概率预测：均值缩放 + 均匀量化为 4096 个 token，交叉熵训练（Sec 3.1–3.2），自回归采样（Sec 3.3）。Bolt：patch 输入、直接多步分位数输出（README）
- **Pretraining data**：28 个真实数据集（13 个仅训练 + 15 个 Benchmark I 域内）+ 1,000 万 TSMixup 增广 + 100 万 KernelSynth 高斯过程合成，按 9:1 采样（Sec 5.2，Table 3）
- **Scale**：约 89 万条序列、约 84B 观测（Sec 5.1）
- **Medical data**：No
- **医疗数据明细（论文原文）**：训练集无医疗数据（Table 3）；医疗只出现在零样本 Benchmark II：Covid Deaths（日）、Hospital（月）
- **ICU seen?**：No
- **ED seen?**：No
- **生命体征 seen?**：No
- **预训练含不规则采样?**：No
- **预训练频率范围**：5 分钟至年（Sec 5.1）
- **Time scale 判断**：Medium
- **Time scale 依据**：训练上下文 512（T5 默认）、预测 64（Sec 5.2）；上下文消融显示到 1024 为止有收益（Fig 11b）
- **Context length**：512（Bolt：README 未写）
- **Forecast horizon**：训练 64；任务 6–48（Table 3）
- **Irregular support**：不支持：Sec 6.1 'we have focused on univariate forecasting of uniformly-spaced time series'
- **Missing support**：支持：缺失值用 PAD token 替代（Sec 3.1）
- **Zero-shot type**：Zero-shot forecasting（概率）
- **Zero-shot 细节（排除 / 归一化 / 头）**：Benchmark II 27 个训练未见数据集（Sec 5.5.2，Fig 5）；Benchmark I 为域内（Fig 4）；均值缩放只用上下文
- **Subgroup analysis**：按数据集（Tables 7–10）；域内 vs 零样本
- **Robustness**：合成模式定性分析：噪声可、指数趋势失败（Fig 12b）；Fig 16：稀疏尖峰、'大均值小方差' 序列因缩放 + 量化损失精度
- **Domain shift**：Benchmark I（域内）vs II（零样本）；微调（Sec 5.5.2）
- **Context-length analysis**：Fig 11b（Sec 5.6）：用 4 种训练上下文长度训练 Chronos-T5-Small，'improvements ... as context length increases up to 1024'，更长则 'saturate or worsen'，作者归因于评价集缺少 ≥15 分钟的高频数据
- **作者自述局限 / 已知问题**：Sec 5.7：tokenization 局限——稀疏序列尖峰无法表示（Fig 16a）；尺度大、方差小时精度下降（Fig 16b）；只支持单变量、等间隔（Sec 6.1）
- **与本项目已有结果的关联**：P1 主文后训练骨干为 Chronos-T5-small（零样本 cov80 0.741）
- **阅读范围**：全文含附录（本机 PDF，TMLR 版）；Bolt 仅 README


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


### Moirai（1.0/1.1）

- **论文 / 来源**：Unified Training of Universal Time Series Forecasting Transformers（Gerald Woo … Doyen Sahoo，Salesforce）arXiv 2402.02592
- **年份**：2024
- **会议 / 期刊**：ICML 2024（README 标注 Oral）
- **是否开源 / 代码**：是：github.com/SalesforceAIResearch/uni2ts；数据 HF Salesforce/lotsa_data
- **公开 checkpoint**：Small 14M / Base 91M / Large 311M（Table 4）；README 有 Moirai-1.1-R
- **Native task（原生任务）**：概率预测：混合分布对数似然（Eq 1）；掩码编码器；any-variate attention 支持单 / 多变量与协变量（Sec 3.1）
- **Pretraining data**：LOTSA，105 个数据集、9 个领域（Table 2）：Energy 59.17%、Transport 17.73%、Climate 15.15%、CloudOps 5.49%、Web 1.55%、Sales 0.72%、Econ/Fin 0.10%、Nature 0.09%、Healthcare 0.01%。Energy 中 Buildings900K 为模拟建筑数据约 15.7B（按 Table 8 计算约占总量 57%，非论文所述）
- **Scale**：27.6B 观测（Sec 3.2.1）
- **Medical data**：Partial
- **医疗数据明细（论文原文）**：Healthcare 1,594,281 观测（0.01%）：Hospital（月）、COVID Deaths（日）、US Births（日）（Table 14）；CDC FluView ILINet（周）、WHO NREVSS（周）、Project Tycho（周）（Table 17）。均为汇总计数
- **ICU seen?**：No
- **ED seen?**：No
- **生命体征 seen?**：No
- **预训练含不规则采样?**：Not reported（过滤缺失过多的序列，App A）
- **预训练频率范围**：秒至年；按观测：小时 71.9%、分钟 25.4%、日 2.6%（Table 3）
- **Time scale 判断**：Long-context oriented
- **Time scale 依据**：零样本上下文在验证集上从 {1000…5000} 选择（Sec 4.2）；Fig 5 上下文越长越好，'capable of handling thousands of time steps'（Sec 4.4）
- **Context length**：预训练窗口随机长度，总长 ≤512 token（Sec 3.2.2）；patch 按频率：分钟 32/64/128、小时 32/64、日/周 16/32（App B.1）；评价 1000–5000
- **Forecast horizon**：按任务（Table 18；LSF 96–720）
- **Irregular support**：不支持：需给定频率以选 patch（App B.1），无时间戳输入
- **Missing support**：论文未描述推理时缺失处理：Not reported（[mask] token 只用于预测区间，Sec 3.1）
- **Zero-shot type**：Zero-shot forecasting（概率）
- **Zero-shot 细节（排除 / 归一化 / 头）**：'datasets used in the following have not been included in LOTSA'：Electricity、Solar、Walmart、Weather、Istanbul Traffic、Turkey Power（Sec 4.2，Table 5）；LSF 6 集（Table 6）；Monash 为域内（训练段在 LOTSA）；实例归一化
- **Subgroup analysis**：Monash 按数据集（Table 20，含 Hospital、COVID Deaths、US Births）；领域 / 频率分层：Not reported
- **Robustness**：Not reported
- **Domain shift**：域内 Monash vs OOD；去掉 LOTSA 只用 GluonTS+Monash：0.809 vs 0.655（Table 7，'diversity of data is critical'）
- **Context-length analysis**：Fig 5（Sec 4.4）：上下文 100–5000，ETTm1 / Electricity / Weather 验证集 MAE 随长度下降；<100 未测
- **作者自述局限 / 已知问题**：Sec 5：'multi patch size mapping is somewhat heuristic'；'limited support for high-dimensional time series'；LOTSA 领域与频率多样性不足；几乎未调参
- **与本项目已有结果的关联**：week02 P1-E：Moirai-MoE 上也出现 '点误差奖励塌缩、R-f 不塌缩'
- **阅读范围**：正文 + 附录数据表（Tables 8–17）原文


### Moirai 2.0

- **论文 / 来源**：Moirai 2.0: When Less Is More for Time Series Forecasting（Chenghao Liu … Junnan Li，Salesforce）arXiv 2511.11698
- **年份**：2025（v3 2026-02）
- **会议 / 期刊**：arXiv 预印本
- **是否开源 / 代码**：是：uni2ts
- **公开 checkpoint**：Salesforce/moirai-2.0-R-small 11.4M（CC-BY-NC-4.0）；Table 1 另训练 base 87.1M、large 305M
- **Native task（原生任务）**：解码器单变量分位数预测（9 个分位数，Eq 2–3），multi-token 输出、自回归多分位数解码（Sec 3）；不支持多变量与协变量
- **Pretraining data**：36M 序列、约 295B 观测：GIFT-Eval Pretrain 230B、GIFT-Eval TrainTest 训练段、Chronos-Mixup 63B、KernelSynth 1.02B、Salesforce 内部 CloudOps 遥测 1.48B（Sec 4）
- **Scale**：约 295B 观测
- **Medical data**：Not reported
- **医疗数据明细（论文原文）**：GIFT-Eval Pretrain 的组成清单未公开（HF 卡：71 个单变量 + 17 个多变量数据集、7 个领域），无法确认医疗内容
- **ICU seen?**：Not reported
- **ED seen?**：Not reported
- **生命体征 seen?**：Not reported
- **预训练含不规则采样?**：Not reported（过滤缺失较多的序列，Sec 4）
- **预训练频率范围**：Not reported
- **Time scale 判断**：Mixed / unclear
- **Time scale 依据**：预训练与评价上下文长度均 Not reported；只有 KV cache 速度测试（约 10K 上下文，Sec 3.3）
- **Context length**：Not reported
- **Forecast horizon**：GIFT-Eval 短 / 中 / 长
- **Irregular support**：Not reported
- **Missing support**：支持：每个时间步拼接缺失指示（Eq 1）；训练时随机遮蔽 50% 输入 patch（Sec 3.2）；缺失目标不计损失
- **Zero-shot type**：Zero-shot forecasting
- **Zero-shot 细节（排除 / 归一化 / 头）**：只与 '可复现且无测试泄漏' 的模型比较（Sec 5.1）；实例归一化只用序列前 30% 的统计量（Sec 3.1）
- **Subgroup analysis**：GIFT-Eval 按领域（Fig 3：除 Nature 外多数领域前十，'pretraining corpus underrepresents natural and environmental time series'）与预测长度（Fig 4：短期第 4、中期第 6、长期第 8）
- **Robustness**：Not reported
- **Domain shift**：只有按领域的排名
- **Context-length analysis**：Not reported
- **作者自述局限 / 已知问题**：Table 1：small 0.728 / base 0.732 / large 0.743（MASE），'we do not observe scaling benefits'；预测越长越弱
- **阅读范围**：正文到 Sec 5.4（Sec 6 与 Table 2 数值为摘要级；附录未读到）


## 7. 补充模型

| Model | 论文 | 会议 / 年份 | 原生任务 | 预训练数据 | Medical | 上下文 | 不规则 / 缺失 | 要点 | 阅读范围 |
|---|---|---|---|---|---|---|---|---|---|
| MOMENT | MOMENT: A Family of Open Time-series Foundation Models（Goswami … Dubrawski）arXiv 2402.03885 | ICML 2024 | 通用：长期预测（线性探针）、零样本短期预测、分类（表示 + SVM）、异常检测、插补（Table 1） | Time Series Pile：Informer 9 集（含 ILI）、Monash 58 集、UCR/UEA 159 集（含 ECG 类）、TSB-UAD 1,980 条（含人体信号）（Sec 3.1） | Partial | 固定 512，patch 8，短序列左侧补零（Sec 3.2） | 掩码重建预训练，有观测 mask；无时间戳 | 每个数据集先切分 train/val/test 以减少污染（Fig 2）；是表中少数原生支持分类 / 插补 / 异常检测的模型 | 本机 PDF 全文 |
| Lag-Llama | Lag-Llama: Towards Foundation Models for Probabilistic Time Series Forecasting（Rasul, Ashok … Rish）arXiv 2310.08278 | 预印本（2023/2024） | 单变量概率预测（Student-t） | 27 个数据集、6 个领域：能源、交通、经济、自然、空气质量、云运维；7,965 条序列，约 3.52 亿个窗口（Sec 5.1） | No | 连续窗口 C 搜索 {32…1024}，最优 32；lag 特征需更长历史（Sec 4.1、Table 5） | No | 项目 week02：eICU 上比 Naive 还差 | 本机 PDF 全文 |
| Timer（UTSD） | Timer: Generative Pre-trained Transformers Are Large Time Series Models（Yong Liu … Mingsheng Long）arXiv 2402.02368 | ICML 2024 | 预测、插补、异常检测 | UTSD 7 个领域、最多约 10 亿点；Health 域 9 个数据集（EEG、ECG、PPG、心率、动物血压，HF 卡） | Partial | lookback 672；预训练上下文 1440，patch 96（Sec 4.1） | S3 格式不要求时间对齐（Sec 3.2）；缺失线性插值（附录摘要级） | Fig 13：lookback 288–672 越长越好；Timer-XL 的前身 | 正文 + HF 数据卡（附录摘要级） |
| Moirai-MoE | Moirai-MoE: Empowering Time Series Foundation Models with Sparse Mixture of Experts（Xu Liu … Doyen Sahoo）arXiv 2410.10469 | 预印本 2024 | 概率预测（解码器 MoE） | LOTSA | Partial（同 LOTSA） | patch 16；预训练上下文 Not reported | Not reported | Fig 6：浅层专家分配随频率不同；项目 P1-E 用过 | HTML 正文（部分） |
| VisionTS++ | VisionTS++: Cross-Modal Time Series Foundation Model with Continual Pre-trained Vision Backbones（Lefei Shen … Chenghao Liu）arXiv 2508.04379 | 预印本 2025 | 零样本预测 | ImageNet MAE 初始化，在 LOTSA（>231B 观测）上续训（Sec 4.1）；GIFT-Eval 版用 GiftEvalPretrain 重训（Sec 4.3） | Partial（继承 LOTSA 计数） | Not reported | Not reported | 随机初始化约差 30%（Sec 4.4） | HTML 正文（部分） |
| TimesFM 2.0 | HF 模型卡 google/timesfm-2.0-500m-pytorch | 2024–2025 | 零样本点预测（10 个未校准分位数头） | 1.0 数据 + LOTSA 20 个子集（含 CDC FluView WHO NREVSS） | Partial | 2048 | NaN 需先线性插值 | 保留频率指示 | 模型卡 |
| PULSE-ICU | PULSE-ICU: A Pretrained Unified Long-Sequence Encoder for Multi-task Prediction in Intensive Care Units（Jang, Yoon, Lee）arXiv 2511.22199 | 预印本 2025 | ICU EHR 事件级表示，微调 18 个预测任务 | ICU EHR 事件序列，'without resampling'；外部验证 eICU、HiRID、P12 | Yes | Longformer 长序列 | 事件级输入，不重采样 | 代表另一条路线：EHR 事件基础模型，而不是数值预测 TSFM | 仅摘要 |

## 8. 独立临床评测

| 论文 | 出处 | 数据与设定 | 模型与方式 | 主要发现 | 与本项目的关系 | 阅读范围 |
|---|---|---|---|---|---|---|
| Are Time Series Foundation Models Ready for Vital Sign Forecasting in Healthcare?（Xiao Gu … David A. Clifton） | ML4H 2024，PMLR 259:401–419 | eICU（6,199 患者）、MIMIC-III Waveform（1,089 患者）；患者级 6:2:2；5 分钟中位数重采样；默认历史 6 h、预测 3 h；HR、SBP、DBP、RR、SpO₂；连续缺失 >1 h 的片段删除，其余前向填充 | TimesFM（零样本）、Chronos S/B/L、Moirai S/B/L、Lag-Llama（零样本 + 全量微调）vs ARIMA、GRU、PatchTST 等从头训练 | Table 3：'the zero-shot performance of most TSFMs is not competitive with even the trained-from-scratch performance of most conventional methods'（eICU HR MAE：GRU 4.462、TimesFM 5.228、Chronos-S 4.807、Lag-Llama 7.365）；Table 4：异常值检测差；Table 5：NEWS2 变化检测上零样本与传统方法相当；Fig 3：历史越长多数更好；Fig 4：Moirai 多变量输入明显改善 | 最接近 MC-MED 的独立证据：同为分钟级床旁体征，但是 ICU、6 h 历史；无年龄 / 性别 / 严重度亚组 | 正文与 Tables 1–6 原文；附录摘要级 |
| Can one model fit all? Evaluating foundation models for time series forecasting across clinical medicine（Gernot Pucher … Christopher Sauer） | Artificial Intelligence in Medicine 2026，doi:10.1016/j.artmed.2026.103473 | 埃森大学医院 + 两家地区医院 + MIMIC-IV；6 个临床用例（体征、化验、床位） | Chronos、TimesFM 等，零样本与微调 vs 神经网络、GBDT、AutoML、统计模型 | 零样本 'frequently approached the performance of optimized task-specific models'；微调后 Chronos、TimesFM 分别 19、18 次进入最佳（AutoML 21 次）；'superior transportability across hospital settings and patient populations' | 跨院迁移的反向证据 | 仅摘要 |
| Evaluating Zero-Shot Foundation Models for Time Series Forecasting in Clinical Settings: A Simulation Study with Electronic Health Records（Pucher … Sauer） | AI4TS 研讨会 2025 | 德国大学医院 EHR + 两个外部验证集，3 个用例 | Chronos、Time-LLM、Time-MoE 零样本 vs 任务专用模型 | 任务专用（尤其深度学习）模型多数场景更准；零样本在外部验证集上 'competitive' | 同上 | 仅摘要 |
| Position: Time-Series Foundation Models Require Explicit Domain-Level Benchmarks（Md Asif Bin Syed … Azmine Toushik Wasi） | ICML 2026，PMLR 306 | 72 个数据集、6 个领域（含医疗） | 7 个 TSFM | 'substantial cross-domain variability'；临床记录有 'irregular sampling and informative missingness' | 支持为医疗单独做基准 | 仅摘要 |
| Cached Foundation Model Summaries for Memory-Efficient Clinical Time Series Inference（Rafi Al Attrach … Peter Schüffler） | ICLR 2026 研讨会（TSALM） | MIMIC-IV 不规则事件序列 | 基础模型把历史压成缓存摘要 + 轻量模型看近期短窗口 | 近期窗口 8 个事件时 AUROC 相对 +6.5%（p<0.001），256 个事件时 +0.1%（不显著）；近期历史的摘要比远期更有用 | 短窗口下基础模型表示可能价值最大，但前提是能带入更长历史 | 仅摘要 |

## 9. 调研结果评估：对本项目研究方向意味着什么

### 9.1 五个问题的证据强度

| 问题 | 结论 | 证据强度 | 主要缺口 |
|---|---|---|---|
| Q1 长 / 短上下文 | 多数模型偏长；没有模型为 ≤15 点设计 | 强（直接实验 + 作者陈述 + 设计参数） | 主模型论文实验最短 100 点（Moirai）/ 480 点（Sundial）；Lag-Llama 超参搜索到 32 点但依赖长 lag；15 点区间没有直接证据，外推要靠本项目实验 |
| Q2 医疗数据 | 只有 MIRA 以 ICU 生理数据为主 | 中—强（依赖语料清单） | GiftEvalPretrain 组成未公开，TimesFM 2.5 / 3.0、Chronos-2、Moirai 2.0 无法判断；Aurora 的 Health 数据集未列 |
| Q3 不规则时间 | 只有 MIRA、VIMTS 原生支持 | 强（方法设计明确） | MIRA 推理时 NaN / mask 的实际处理未说明 |
| Q4 已知问题 | 短上下文、高频有证据；患者亚组完全没有 | "没有做亚组" 在阅读范围内是确定的；域偏移为中 | 独立临床评测除 Gu et al. 外只读到摘要 |
| Q5 与 MC-MED 的差异 | VisionTS、LightGTS、Lag-Llama、Time-MoE 差异最大；MIRA 最接近 | 判断性（按 D1–D5 规则） | 评级规则是本调研定的，研究者可以改权重 |

### 9.2 与项目已有结果对照（只用聚合量）

| 已有结果 | 口径 | 与本调研的关系 |
|---|---|---|
| week02 F1：零样本生命体征预测中 TimesFM 系列领先，MIRA 见过 MIMIC 也没领先 | 公开数据 week02 | MIRA 的医疗语料优势没有转化为零样本预测优势。TimesFM 1.0 训练时覆盖 1–512 所有上下文长度（Sec 4），可能与其稳健有关，属于假设，需实验确认 |
| week02 F3：稀疏到每变量 1 个值，TSFM 探针相对 LR 仍 +0.041 AUPRC | 公开数据 week02 | 提醒：不能默认 "稀疏 / 短窗口一定让 TSFM 相对变差"，Q1 的长上下文证据只说明绝对性能，不说明相对差距 |
| week02 F4：零标签 "预测轨迹 → 预警" AUROC 0.55–0.59 | 公开数据 week02 | 与 "论文的 zero-shot 是数值预测，不是临床结局预测" 一致 |
| 合作同学 MC-MED decomp_60 汇总：XGBoost AUPRC 0.317；MIRA-Large 0.218；VIMTS-Adapter 0.159；TimesFM 3.0 0.146 | N=1,328、事件 224（16.87%）；与冻结 benchmark 测试集（5,236，患病率 12.0%）口径不同；无置信区间，非严格排名 | 数据相似度最高的 MIRA 在三者中最高，与 "预训练分布相似度" 的方向一致；但输入设计适配度最高的 VIMTS 并不高。三个点、无区间，不足以检验任何假设，只能作为待检验线索 |

### 9.3 可检验的解释假设（供实验侧选用）

每条假设都给出 "需要什么聚合量" 和 "结果支持 / 不支持时怎么写"。是否做、怎么做由研究者决定。

| 编号 | 假设 | 调研证据 | 需要的聚合量或实验 | 支持时的写法 |
|---|---|---|---|---|
| H1 | 有效 token 太少：patch ≥15 的模型在 15 分钟窗口里只形成 1 个部分填充的 token | Sundial Table 5、TimesFM Sec 4、Timer-XL Table 11、Moirai App B.1（设计参数）；Timer-XL Sec 1（作者陈述） | 每个模型的实际 token 数；点级 token 模型（MIRA、Chronos、Time-MoE）与 patch 模型的相对差距；按窗口内有效观测点数分层 | "patch 模型与基线的差距大于点级 token 模型，这一结果与 '输入远短于模型设计上下文' 的假设一致" |
| H2 | 缺失模式不匹配：预训练几乎没见过带缺失的输入 | Time-MoE App C、Moirai App A、Moirai 2.0 Sec 4（预训练过滤缺失）；TimesFM 2.0 要求插值 | 现有 drop20 / drop40 / continuous5min 测试集上，TSFM 与传统模型的 Δ 对比 | "删减后 TSFM 下降幅度大于传统模型，这一结果与预训练缺失分布不匹配的假设一致" |
| H3 | 归一化统计量不稳：15 个点估计均值方差 | TimesFM Sec 5、Sundial Sec 4.1.1、Chronos Fig 16b | 按变量（尤其 SpO₂ 这类近乎平坦的序列）或按窗口内方差分层的表现 | "低方差窗口上误差更大，这一结果与实例归一化在短窗口上不稳定的假设一致" |
| H4 | 单变量模型丢失体征间关系 | Gu et al. 2024 Fig 4；Chronos-2 Sec 5.2（收益 modest） | 多变量模型（Chronos-2、TimesFM 3.0、Moirai、VIMTS）与通道独立模型对比；同一模型单 / 多变量输入对比 | "多变量输入带来改善，与 Gu et al. 2024 的观察一致" |
| H5 | 亚组差异来自数据侧而不是预训练 | 所有模型论文均无患者亚组 | 各 Age / Gender / ESI 亚组的观测密度、实际输入长度、事件率、基线体征分布 | "该亚组的有效观测更少，模型差距同步扩大，这一结果与 H1 / H2 一致；原论文未检验患者亚组" |
| H6 | 急性 / 高危轨迹被平滑 | Gu et al. 2024 Table 4（异常值检测差）；Chronos Fig 12b（指数趋势）；Sundial App C.1（MSE 导致过平滑） | 高 ESI 级别（高危）亚组上的校准与灵敏度 | "高危组灵敏度下降，与 '点误差训练的模型倾向均值回归' 的作者分析一致" |

### 9.4 解释结果时的写法

- 不写："因为预训练没有 ED 数据，所以 TimesFM 3.0 表现差。"
- 可以写："TimesFM 3.0 在 0–15 分钟窗口上 AUPRC 低于 XGBoost。这一结果与 '输入远短于模型预训练与评测所用上下文（15,360）' 的假设一致（依据：模型卡上下文长度；Timer-XL Sec 1 关于短上下文的作者陈述），本研究未直接检验上下文长度的作用。"
- 引用证据时注明类型：直接实验 / 独立评测 / 作者陈述 / 设计推断 / 无证据。设计推断（如 "只形成 1 个 token"）不能写成 "论文发现"。

### 9.5 需研究者决定的事项（A 档）

1. 是否延长输入窗口或做上下文长度扫描（属于 "t0 与窗口"）。不做：只能说 "与假设一致"；做：H1 可以直接检验，但会改变既定 benchmark 设定，需登记为新版本。
2. VIMTS 是否归入 "基础模型" 组。它需要在 MC-MED 上自监督 + 训练，归入会让 "zero-shot" 口径不统一；单列则对比更干净。
3. 亚组切点（年龄、ESI 分组方式）与亚组上的主要指标。
4. 若用 MIMIC-IV-ED 做外部验证，MIRA 与 MIMIC-IV 预训练重叠的处理（排除 MIRA、改用其他外部集，或只报告并标注）。

### 9.6 本调研的局限

- 未读到原文的部分：Chronos-2 Table 6（训练数据清单）与附录、Aurora ICLR 版附录、Time-MoE App D 与 Table 10 后半、Moirai 2.0 Sec 6 与附录、GIFT-Eval App D/E、VisionTS 附录 B.9。对应字段已标 "Not seen" 或 "摘要级"。
- TimesFM 2.5 / 3.0、Chronos-Bolt 没有论文，只能用模型卡与 README。
- 独立临床评测中，Pucher 2025 / 2026、Syed 2026、Al Attrach 2026、PULSE-ICU 只读到摘要。
- "15 点约等于几个 token" 是按 patch 长度推算；D1–D5 与两个评级是本调研的判断规则，不是论文结论。
- 论文内部不一致已在 "来源与阅读范围" 表列出（MIRA 数据描述与 Table 7 不符、OOD 数据集个数不符；Timer-XL 的 UTSD 点数 10 亿 vs 868.8M；LightGTS 的 N=10 vs App A.4 的 N=4）。
- BIDMC32HR 原始来源为重症监护患者记录一条是凭记忆，需核对原数据集说明。


## 10. 来源与阅读范围

| Model | 主要来源 | 定位 | 阅读范围 | 未读到的部分 / 待核对 |
|---|---|---|---|---|
| MIRA | Li et al., MIRA, NeurIPS 2025 | arXiv 2506.07584（v7）；github.com/microsoft/MIRA | 正文 + 附录 A–I 原文 | 内部不一致：Sec 3.3 称含流行病与心理健康数据，Table 7 无；正文称 7 个 OOD 数据集，Table 2 只有 6 个；'best results on all datasets' 与 Table 2 不符 |
| Time-MoE | Shi et al., Time-MoE, ICLR 2025 | arXiv 2409.16040；github.com/Time-MoE/Time-MoE | 正文 + App B/C | Table 10 后半、App D |
| Sundial | Liu et al., Sundial, ICML 2025 | arXiv 2502.00816（v4）；github.com/thuml/Sundial | 正文 + 附录 A–F | ECG 子集具体库名未给出 |
| TimesFM 1.0 | Das et al., ICML 2024 | arXiv 2310.10688（v4，本机 PDF 09_TimesFM.pdf） | 全文 | — |
| TimesFM 2.0 / 2.5 / 3.0 | HF 模型卡 google/timesfm-2.0-500m-pytorch、timesfm-2.5-200m-pytorch、timesfm-3.0-pytorch；README；Google Research 博客 2026-08-31 | huggingface.co/google；github.com/google-research/timesfm | 模型卡 + README + 博客 | 无论文；GiftEvalPretrain 组成清单未公开 |
| Timer-XL | Liu et al., Timer-XL, ICLR 2025 | arXiv 2410.04803（v4）；github.com/thuml/Timer-XL | 正文 + App A–E | Tables 14–16；UTSD 点数正文写 10 亿、Table 9 为 868.8M；BIDMC32HR 来源属性凭记忆 |
| Timer / UTSD | Liu et al., Timer, ICML 2024；HF thuml/UTSD 数据卡 | arXiv 2402.02368 | 正文 + 数据卡 | 附录（摘要级） |
| VisionTS / VisionTS++ | Chen et al., ICML 2025；Shen et al., arXiv 2508.04379 | arXiv 2408.17253；github.com/Keytoyze/VisionTS | VisionTS 正文；VisionTS++ 正文部分 | VisionTS 附录 B.9；Fig 6 具体取值 |
| VIMTS | Hu et al., ICML 2025 | arXiv 2505.22815；github.com/WHU-HZY/VIMTS | 正文 + App A.1–A.5、B.1–B.2 | B.2 之后 |
| Aurora | Wu et al., ICLR 2026（华东师大） | arXiv 2509.22295；github.com/decisionintelligence/Aurora | 正文（v6）+ App A.1–A.4（v1） | ICLR 版附录；Fig 6 来源比例；局限性章节 |
| LightGTS | Wang et al., ICML 2025 | arXiv 2506.06005；github.com/decisionintelligence/LightGTS | 正文 + App A–C | Table 13 数值截断；N=10 与 App A.4 'N=4' 不一致 |
| Chronos / Chronos-Bolt | Ansari et al., TMLR 10/2024；Chronos-Bolt README | arXiv 2403.07815（本机 PDF 08_Chronos.pdf）；github.com/amazon-science/chronos-forecasting | 全文含附录；Bolt 仅 README | Bolt 无论文，patch 长度未核对 |
| Chronos-2 | Ansari et al., arXiv 2510.15821 | arXiv 2510.15821；HF amazon/chronos-2 | 正文 | 附录 A/B、Table 6（训练数据清单） |
| Moirai（1.0/1.1） | Woo et al., ICML 2024 | arXiv 2402.02592；github.com/SalesforceAIResearch/uni2ts | 正文 + Tables 8–17 | — |
| Moirai-MoE | Liu et al., arXiv 2410.10469 | arXiv 2410.10469 | 正文部分 | 附录 |
| Moirai 2.0 | Liu et al., arXiv 2511.11698（v3） | arXiv 2511.11698 | 正文到 Sec 5.4 | Sec 6、Table 2 数值（摘要级）、附录 |
| MOMENT | Goswami et al., ICML 2024 | arXiv 2402.03885（本机 PDF 11_Moment.pdf） | 全文 | — |
| Lag-Llama | Rasul et al., arXiv 2310.08278 | 本机 PDF 10_Lag-Llama.pdf | 全文 | — |
| GIFT-Eval | Aksu et al., arXiv 2410.10393 | arXiv 2410.10393；HF Salesforce/GiftEvalPretrain | 正文 | App D/E/F.2；Healthcare 测试集名称 |
| 独立临床评测 | Gu et al. ML4H 2024；Pucher et al. AI4TS 2025、AIIM 2026；Syed et al. ICML 2026；Al Attrach et al. ICLR 2026 研讨会；PULSE-ICU | PMLR 259:401–419；doi:10.1016/j.artmed.2026.103473；PMLR 306；arXiv 2511.22199 | Gu 正文与表格原文；其余仅摘要 | 除 Gu 外均为摘要级 |
