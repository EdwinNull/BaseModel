# 模型缺陷调研汇报：MC-MED / MIMIC-IV 上哪些子集表现差、为什么、怎么修（含时序基础模型背景）

2026-11-06 · 本文件为在线报告（Claude Doc）的 Markdown 导出

## 第一部分：哪些子集表现差、为什么、怎么修（11-06 新增）

研究主线是找出现有方法在 MIMIC-IV、MC-MED 等数据集的哪些子集上表现差，查清原因，再有针对性地修。本部分是纯文献调研（33 篇，未跑实验），每条证据都标了阅读范围；第二部分是 11-05 的时序基础模型背景调研，保持原样。

**总判断。** 在 MIMIC-IV、MIMIC-IV-ED 和 eICU 上，表现差的子集已被反复报告，集中在四个方向：种族与保险（含交叉子群）、年龄、测量过程、时间。MC-MED 上本轮只找到一份分组结果（MC-BEC，单阈值 TPR），没有找到按子集系统评估模型的工作。这是本项目可以占的空白，但检索范围有限，不宣称“首个”。

**哪些子集表现差。**

- **种族、保险与交叉子群：** MIMIC-IV-ED 入院预测中基线 LR 的种族 ΔTPR 为 0.251（FAIM Table 4）；种族 × 性别交叉子群 ECE 最高约 0.119（美洲原住民男性，Lett 2025）；MIMIC-III 院内死亡中 Medicaid 与黑人患者 AUROC、AUPRC 更差，Medicare（多为 ≥65 岁）风险被明显低估（Röösli 2022）。
- **年龄与性别：** MC-MED 前身 MC-MED-v0 上，固定阈值下 decomp-60 的 TPR 年轻组（<55 岁）0.87、≥55 岁 0.94，女性 0.88、男性 0.92（MC-BEC Table 5）。较差的是年轻组和女性，不是老年组；但这是单阈值 TPR，混着各组基础率。分诊层面老年人被漏判：ESI 1 级识别需立即抢救的老年人灵敏度只有 42.3%（Platts-Mills 2010）。
- **测量过程：** 去掉监护数据后 decomp-60 AUPRC 从 0.25 降到 0.14（MC-BEC Table 4）；本项目 mp_benchmark 中 drop40 让五个模型 ΔAUPRC 为 −0.016 至 −0.036、个体预测翻转 6.2%–9.7%；MIMIC-III 的测量频率随年龄和种族系统变化，只用测量模式预测 ICU 死亡 AUC 0.76（Shi 2025）。
- **时间：** MIMIC-IV 上 2008–10 训练的脓毒症模型到 2017–19 AUROC 最多降 0.090（Guo 2022）。

**为什么。** 归纳为七类机制 C1–C7：样本少、基础率造成的指标伪差、测量过程被当作捷径、测量误差同时进入输入和标签、标签与分组变量有噪声、生理异质性、分布偏移。对 decomp_60 最需要警惕的是 C4：SpO2<90 是事件定义之一，而脉搏血氧对深肤色有高估（隐匿低氧黑人 6.8% vs 白人 4.9%，Wong 2021），部分子集的事件可能被漏记。这一点是从 ICU 证据迁移到急诊的推断，需要用数据检验。

**怎么修。** 证据较强、代价低的是分组再校准或多重校准、冻结表示 + 分组平衡重训分类头（DFR）、有针对性地补数据。常常无效的是公平约束（组内性能普遍下降）、单属性重加权（扩大其他属性差距）和域泛化或无监督域适应（时间偏移上不比 ERM 稳，项目 AL4 跨年龄全部无效）。要注意校准只改概率、不改排序。

**本项目下一步（按研究者 11-06 决定）。**

1. 审计：在 MC-MED 冻结测试集上，对已有全部模型按人群、临床、测量过程三族子集打分。跨子集比较以 AUROC 和校准为主，AUPRC 与患病率并列。
2. 发现：AFISP 式稳定性分析加误差聚类，找组合子集，在验证集上发现、在冻结测试集上确认。
3. 归因：逐个子集检查 C1–C7。
4. 修复：再校准 → DFR → 补数据 → 输入与过程增强；公平约束和域适应只作对照。
5. 复现：在 MIMIC-IV-ED 上用 5 个可对齐变量重复审计与归因；MIRA 的结果单独报告。

## 文献中已报告的表现差子集

下表只收原文给出数字或明确结论的子集。"证据类型" 区分直接实验、作者分析、理论与无证据；"阅读范围" 说明我们读到哪一层（全文、正文、摘要）。完整 20 行与对 MC-MED 的逐条启示见 xlsx『子集缺陷证据』。

| 编号 | 文献与数据 | 任务 | 表现差的子集（原文数字） | 证据类型 · 阅读范围 |
|---|---|---|---|---|
| E1 | MC-BEC（Chen 2023），MC-MED-v0 102,731 次就诊 | decomp 60/90/120，LightGBM 多任务 | 固定阈值 decomp-60 TPR：<55 岁 0.87 vs ≥55 岁 0.94；女性 0.88 vs 男性 0.92；去掉监护模态 AUPRC 0.25 → 0.14 | 直接实验 · 正文与表逐字 |
| E2 | MC-MED（Kansal 2025），118,385 次 | 数据描述 | 无基准、无分组；年龄加 0–2 岁扰动并截断 18–90；时间按患者平移 | 无证据 · 正文 |
| E3 | SignalMC-MED（Gustafsson 2026） | ECG / PPG 基础模型探针 | 未做分组、缺失或偏移分析 | 无证据 · 正文约一半 |
| E4 | MIMIC-IV-ED 基准（Xie 2022），441,437 次 | 住院、危重、72 小时复诊 | 未做分组；分诊时点危重 AUROC：ESI 0.804、NEWS 0.634、MLP 0.883 | 无证据（分组）· 正文 |
| E5 | Lett 2025，MIMIC-IV-ED 160,016 次 | 急诊入院 | 种族 × 性别交叉子群误差更大：ECE 美洲原住民男性 0.119、西语裔女性 0.104、黑人女性 0.102 | 直接实验 · 正文 |
| E6 | FAIM（Liu），MIMIC-IV-ED 418,100 次 | 急诊入院 LR | 种族 ΔTPR 0.251、ΔTNR 0.224；性别 ΔTPR 0.074 | 直接实验 · 全文含表 |
| E7 | Röösli 2022，MIMIC-III 基准 LSTM | ICU 48 小时院内死亡 | Medicaid 与私人保险事件率相近（8.5% vs 8.3%）但 AUROC、AUPRC 更差；黑人事件率更低仍更差；Medicare 风险被明显低估；外部验证召回 <20% | 直接实验 · 全文 |
| E8 | Meng 2022，MIMIC-IV | 院内死亡 | 模型依赖人口学特征；机械通气处置随种族、性别、年龄不同 | 作者分析 · 摘要 |
| E9 | Guo 2022，MIMIC-IV ICU 四个时间段 | 死亡、脓毒症等 | 2008–10 训练、2017–19 测试，脓毒症 AUROC 最多降 0.090 | 直接实验 · 摘要 |
| E10 | Shi 2025，MIMIC-III 23,426 人 | 测量模式与人口学 | ≥65 岁体征测得更频繁；白人首 24 小时血压 34.22 次、黑人 32.79 次；只用测量模式预测死亡 AUC 0.76 | 直接实验 · 全文 |
| E11 | Agniel 2018，669,452 人 | 3 年生存 | 是否开化验在 86% 的项目上与生存显著相关；化验时间比化验值更能预测的占 68% | 直接实验 · 正文与表 |
| E12 | Jeanselme 2022，MIMIC-III | 短期生存 | 两种常用插补的选择可翻转黑人 / 非黑人的公平方向 | 实验 + 理论 · 部分 |
| E13 | Wong 2021，eICU / MIMIC 87,971 对 | 脉搏血氧偏差 | 隐匿低氧：黑人 6.8%、西语裔 6.0%、亚裔 4.8%、白人 4.9% | 直接实验 · 摘要 |
| E14 | Platts-Mills 2010；Grossmann 2014 | ≥65 岁 ESI 分诊 | ESI 1 识别需立即抢救者灵敏度 42.3%；老年漏分诊 22.5% | 直接实验 · 摘要 |
| E15 | Sax 2023，KPNC 5,315,176 次 | ESI 误分诊 | 误分诊 32.2%；黑人漏分诊 +18.5%，高危药物 +30.3%，近期 ICU +36.7% | 直接实验 · 摘要 |
| E16 | Kemp 2020；Martín-Conty 2024 | NEWS2 等预警评分 | 衰弱老人 NEWS2 预测 30 天死亡 AUC 0.70；各评分加年龄后 AUC 都显著提高 | 直接实验 · 摘要 |
| E17 | AFISP（Subbaswamy 2024），测试 60,998 次 | 住院恶化预警 | 整体 AUROC 0.986、最差 5% 子集 0.919；13 个子群中 9 个为多变量组合 | 直接实验 · 全文 |
| E18 | Seyyed-Kalantari 2021；Oakden-Rayner 2020 | 胸片分类 | 女性、黑人、低社经漏诊更多；无胸管气胸 AUC 0.77 vs 有胸管 0.94 | 直接实验 · 摘要 |
| P1 | 本项目 mp_benchmark_v1 | decomp_60 五个缺失感知模型 | drop40 ΔAUPRC −0.016 至 −0.036；个体翻转 6.2%–9.7% | 项目内实验 · 聚合量 |
| P2 | 本项目 AL4 | 10 种 UDA | 跨中心 7 种显著有效；跨年龄全部无效 | 项目内实验 · 聚合量 |

**三点读法。**

1. MC-MED 本身只有 E1 一份分组结果。它显示的较差组是年轻组和女性，与 "老年人最难" 的直觉相反。但这是验证集灵敏度 0.85 对应的单一阈值下的 TPR，各组患病率与风险分布不同就会产生这种差，原文没有给组内 AUROC、样本量和置信区间。表 5 的性别差值印成 0.05，与 0.92 − 0.88 不符，引用前需核对原文。
2. 老年组的问题在 MIMIC 上更多表现为校准（风险被低估，E7）和分诊漏判（E14），而不是排序。这一点决定了老年子集应该先看校准截距与斜率，而不只看 AUROC。
3. 最常用的两个基准（E2 MC-MED、E4 MIMIC-IV-ED）都没有子集报告；E5、E6 的分组结果来自另起的公平性研究。Lett 2025 预印本与正式版部分百分比有出入，表中按正式版。

## 原因：七类机制

把上表的作者解释与方法学文献合在一起，子集表现差的原因可以归为七类。它们不互斥，一个子集往往同时受两三类影响。第三列是对 MC-MED decomp_60 的推断，不是已观察到的结果；第四列只需要聚合量或项目已有的基础设施。

| 编号 | 机制 | 文献证据 | 在 MC-MED decomp_60 上可能的表现（推断） | 诊断方法 |
|---|---|---|---|---|
| C1 | 样本少、方差大 | Chen 2018（差异可分解为偏差 / 方差 / 噪声，补数据可降差异）；AFISP 学习曲线；Lett 2025 交叉子群 | 少数族裔、ESI 1 / 5、≥80 岁等子集事件数少，指标区间宽 | 按患者聚类 bootstrap 区间；子集学习曲线 |
| C2 | 基础率不同造成的指标伪差 | McDermott 2024 Theorem 3（AUPRC 偏向高患病率子集）；Röösli 2022；MC-BEC 单阈值 TPR | 患病率更高的子集（可能是老年、ESI 1–2，需核对）AUPRC 与固定阈值灵敏度会 "看起来更好" | 并列 AUROC、AUPRC 与患病率；只有 AUPRC 差而 AUROC 不差时，主要是指标问题 |
| C3 | 测量过程（观测密度、缺失通道、来源）被当作捷径 | Agniel 2018；Shi 2025（测量模式单独预测死亡 AUC 0.76）；Jeanselme 2022；MC-BEC 去监护 AUPRC 0.25 → 0.14 | 窗口内观测少、缺血压或 SpO2 通道、以人工录入为主的窗口上排序变差或概率漂移 | 按有效点数与缺失通道分层；只用过程特征的模型在各子集的 AUROC；mask 替换后重打分 |
| C4 | 测量误差同时进入输入与标签 | Wong 2021、Mettler 2024（脉搏血氧对深肤色高估） | SpO2<90 是事件定义之一：部分患者真实低氧未记成事件，表现为子集 "事件少、模型漏报" | 按事件分量分别报告灵敏度；种族 × 分量交叉；去 SpO2 分量的标签变体（只作敏感性分析） |
| C5 | 标签与分组变量本身有噪声 | Sax 2023（ESI 误分诊 32.2%）；Platts-Mills 2010（老年 ESI 1 灵敏度 42.3%） | ESI 3 内部混有高风险患者；HR>110 对服 β 受体阻滞剂者或老年人更难触发 | 各 ESI 组内事件率与 AUROC；事件分量 × 年龄 |
| C6 | 生理异质性：同样数值在不同人群代表不同风险 | Martín-Conty 2024（加年龄提升所有预警评分）；Kemp 2020；Röösli 2022 | 冻结基准只输入六项体征、不含年龄，老年风险可能被系统低估 | 子集内校准截距与斜率；加年龄 × 体征交互是否改善 |
| C7 | 分布偏移（时间、地点、流程） | Guo 2022；Zhang 2021；项目 AL4 | 2020–2022 跨越 COVID 各阶段；但时间按患者平移，日历子集可能做不了 | 域分类器 AUROC；先核对去标识后是否保留季节与时段 |

**对本项目最关键的两条。** 第一，C2 决定了怎么比：在 decomp_60 这种患病率 12% 左右、各子集患病率可能差很多的任务上，直接比较子集 AUPRC 或单阈值灵敏度会把基础率差异误读成模型缺陷。第二，C4 是 decomp_60 特有的风险：标签由同一套监护体征派生，测量误差不只让输入变差，还会让 "真值" 本身在某些子集上偏低。后者目前是从 ICU 证据迁移过来的推断，需要用事件分量拆分来检验。

## 子集比较的指标陷阱

比较子集时选错指标，会把基础率差异当成模型缺陷，或者反过来掩盖真实缺陷。

- **AUPRC 不适合作跨子集的主指标。** 随机分类器的 AUPRC 等于患病率，所以患病率高的子集天然 AUPRC 高。McDermott et al. 2024（Theorem 3，正文部分逐字）进一步证明，优化 AUPRC 会优先改善高患病率子集的排序，可能加大子集间差距。
- **固定阈值下的 TPR / FNR 也混着基础率。** 同一个阈值在风险分布不同的子集里对应不同的工作点。MC-BEC Table 5 和 FAIM 的 ΔTPR 都属于这一类；它们说明临床上哪组被漏报更多，但不能单独说明模型在该组排序更差。
- **校准与排序要分开看。** Röösli 2022 中老年（Medicare）组的主要问题是风险被低估；Locati 2026（摘要）报告校准不缩小 AUROC 差距。只看 AUROC 会漏掉校准型缺陷，只看 ECE 会漏掉排序型缺陷。

**建议口径（11-06 研究者同意按此执行）。**

1. 子集主指标：AUROC 加校准（校准截距与斜率，或分组 ECE）。
2. AUPRC 必须与该子集患病率并列；固定阈值灵敏度作为临床补充，阈值在全体验证集上定。
3. 区间用按患者聚类的 bootstrap（同一患者多次就诊不独立）；多个子集的显著性用 Holm 校正。
4. 最小规模：建议每个子集至少约 30 个事件，不足的只报告描述量不下结论。这个数字是经验建议，不是文献结论。
5. 各子集的患病率必须在与冻结测试集相同的纳排口径下计算；不同汇总口径的样本量与事件率不能混用。

## 如何系统地找子集

预设分组（年龄、性别、种族、ESI）是必要的起点，但只能找到事先想到的单变量子集。AFISP 在住院恶化预警模型上找到的 13 个表现差子群中，有 9 个是多变量组合，单变量分组发现不了。因此建议预设分组与数据驱动方法并用。

| 方法 | 做法 | 证据 | 用在 MC-MED 时的注意点 |
|---|---|---|---|
| 预设分组 | 按先验变量逐一评估 | 多数临床公平研究的做法（Röösli、Lett、FAIM） | 老年 ≥65，按 65–74 / ≥75 切分（11-06 定）；交叉子群单列 |
| AFISP（Subbaswamy 2024） | 稳定性分析找出最差 α 比例子集，再用 SIRUS 规则学习描述成可读子群 | 合成数据中找回目标子群 83.4%（SliceFinder 94.6%），但随特征数扩展好得多 | 适合把人群、临床、测量过程字段一起放进去 |
| SliceFinder / SliceLine | 在离散化特征组合上穷举搜索误差显著偏高的切片 | AFISP 文中的对照，准确但随特征数爆炸 | 字段少（<30）时可直接用 |
| Domino（Eyuboglu 2022） | 在嵌入上拟合误差感知混合模型，再用跨模态嵌入给切片命名 | 1,235 个设置中找回 36% 的切片；EEG 上跨模态 precision@10 0.697 vs 单模态 0.532 | 可用 TSFM 或 GRU-D 的窗口嵌入；没有配对文本时命名靠人工 |
| 误差聚类（Oakden-Rayner 2020） | 对倒数第二层特征 k-means，比较高误差簇与低误差簇的属性 | 胸片气胸：高误差簇有胸管比例 0.17、低误差簇 0.68 | 最便宜，适合先跑一遍 |
| 发现与确认分开 | 在一份数据上发现，在另一份独立数据上确认 | AFISP 与 Domino 都指出小样本下信号与噪声难分 | 冻结测试集已多次使用，11-06 定为验证集发现、测试集确认 |

数据驱动方法找到的子集只是 "误差集中的地方"，不自带原因。每个确认后的子集仍要经过上一节 C1–C7 的归因检查，再决定用哪种对策。

## 对策：哪些有证据、哪些常常无效

对策要对应原因。校准类对策只修 C2 / C6 带来的概率偏差；补数据对应 C1；输入与过程增强对应 C3 / C6；C4 / C5 是标签问题，模型侧对策修不了，只能做敏感性分析。优先级是综合证据强度、代价与本项目设定后的建议。

| 编号 | 对策 | 效果（原文数字） | 局限 | 在本项目的用法 | 优先级 |
|---|---|---|---|---|---|
| F1 | 分组再校准 / 多重校准 | 跨子群校准方差降 98.8% / 94.3%（Barda 2021）；MIMIC-IV-ED ECE 0.083 → 0.065，AUROC 0.85 不变（Lett 2025） | 只改概率、不改排序 | 先做；现有 pos_weight≈7.08 本来就让概率整体偏高 | 高 |
| F2 | 分组阈值 | TPR 差距 0.20–0.23 → <0.03（Locati 2026，摘要） | 属阈值决策；可能被视为差别对待 | 只作敏感性分析，已按此定（11-06） | 中 |
| F3 | 有针对性补数据 / 选数据 | 最差子群训练样本补到约 2,000 例时与多数其他子群相当（AFISP） | 盲目加整源数据会伤子集：黑人子集最差 −4.1%（Tan 2026） | 从 MC-MED 训练池对子集加权或过采样；或从 MIMIC-IV-ED 引入同类子集 | 高 |
| F4 | 冻结表示 + 分组平衡重训分类头（DFR / CRT） | 无属性标签时平均最差组准确率 ERM 59.9、DFR 66.2（Yang 2023） | 对属性不平衡、属性泛化两类偏移几乎无效 | 与 TSFM 冻结嵌入 + 探针的设定天然契合 | 高 |
| F5 | 输入加入上下文（年龄、ESI、到达方式） | 各预警评分加年龄后 AUC 都显著提高（Martín-Conty 2024） | 改变模型输入定义，需登记新版本 | 对应 C6；检验老年子集差距是否缩小 | 中 |
| F6 | 缺失 / 过程感知建模与过程扰动增强 | 各缺失感知模型对删减的稳健性不同（项目 mp_benchmark） | 插补方式会翻转公平方向（Jeanselme 2022），必须按子集报告 | 对应 C3 与现有 M2 路线 | 中 |
| F7 | 公平约束 / 单属性重加权 / GroupDRO | 组内性能几乎普遍下降（Pfohl 2021）；Reductions 让 AUC 0.790 → 0.706（FAIM）；单属性重加权扩大其他属性差距 | 常常只是把误差挪到别的组 | 只作对照 | 低 |
| F8 | 域泛化 / 无监督域适应 | 时间偏移上不比 ERM 稳（Guo 2022）；eICU 跨地区 8 种 DG 都没有稳定胜过 ERM（Zhang 2021）；项目 AL4 跨年龄全部无效 | 子集差异多数不是可对齐的协变量偏移 | 不建议作为主线 | 低 |

**一个要提前说清的权衡。** 公平约束类方法的典型结果是差距缩小但最差组本身没有变好，而是其他组变差。本项目评价对策时，建议同时报告最差子集 AUROC、总体 AUROC、校准与 FNR 差距，只看 "差距" 一个数会把这种结果误判为改善。

## MC-MED decomp_60 子集审计方案（建议）

下面是把上述证据落到本项目的方案草稿。切点、发现 / 确认切分和标签变体的处理已由研究者在 11-06 定下（见文末）；老年 ≥65 只用于子集审计，项目 D70 的 ≥60 岁主分析不变。所有步骤只交回聚合量。

**子集清单。**

| 子集族 | 子集（建议切点） | 为什么查 | 所需字段 | 假设 |
|---|---|---|---|---|
| A 人群 | 年龄 18–44 / 45–64 / 65–74 / ≥75（老年 = ≥65，11-06 定）；另报 ≥60 以对齐 D70 主分析 | MC-BEC 年龄 TPR 差 0.07；老年风险被低估；预警评分加年龄更好 | 年龄（已加 0–2 岁扰动） | S1 |
| A 人群 | 性别 | MC-BEC 女性 TPR 0.88 vs 男性 0.92 | 性别 | S1 |
| A 人群 | 种族、族裔；种族 × 性别、年龄 × 性别交叉 | 脉搏血氧偏差；MIMIC-IV-ED 种族 ΔTPR 0.251；交叉子群误差更大 | 种族、族裔 | S3 |
| B 临床 | ESI 1–2 / 3 / 4–5 | ESI 误分诊多，ESI 3 内部混杂 | 分诊级别 | S5 |
| B 临床 | 到达方式、主诉类别、是否服高危药物 | 漏分诊的危险因素（Sax 2023） | visits、用药 | S5 |
| B 临床 | 评估期末到阈值的距离分位 | 标签是 "跨阈值"，入选者评估期都正常 | numerics | S2 |
| B 临床 | 事件分量（仅阳性）：HR 型 / MAP 型 / SpO2 型 / 多分量 | 不同生理过程，可预测性不同 | 标签派生过程 | S2、S3 |
| C 测量过程 | 0–15 分钟每通道有效点数分位 | 稀疏窗口；TSFM 有效 token 数（H1） | numerics | S4 |
| C 测量过程 | 缺失通道组合（如无血压、无 SpO2） | MC-BEC 去监护 AUPRC 0.25 → 0.14 | numerics | S4 |
| C 测量过程 | 数据来源 Chart / Monitor 比例 | 人工录入与监护自动值的噪声和频率不同 | numerics 来源字段 | S4 |
| C 测量过程 | 入床距到院时间；时段（若去标识保留） | 等待时间与病情、流程相关 | visits 时间 | S6 |
| D 数据驱动 | AFISP / 误差聚类在 A–C 全部字段与模型嵌入上发现的组合子集 | 多变量子集单变量分组发现不了 | 以上全部 + 嵌入 | — |

**可检验假设。** 这些是待检验的假设，不是结论。结果出来后只写 "与某假设一致 / 不一致"。

| 编号 | 假设 | 依据与证据类型 | 检验（聚合量） |
|---|---|---|---|
| S1 | 固定阈值下年轻组、女性灵敏度更低；老年组的问题更可能在校准而不在排序 | MC-BEC Table 5（直接实验，单阈值）；Röösli 2022；Martín-Conty 2024 | <65 / 65–74 / ≥75 各组 AUROC、校准截距 / 斜率、固定阈值灵敏度，并列患病率 |
| S2 | 评估期正常但远离阈值的患者最难：模型主要靠 "离阈值多近" | 任务定义（设计推断） | 按到阈值距离分层的灵敏度与 AUROC；阳性按事件分量拆开 |
| S3 | SpO2 型事件在深肤色患者中被漏记，表现为该子集事件率偏低、模型漏报 | Wong 2021、Mettler 2024（ICU 直接实验）；迁移到急诊为推断 | 种族 × 事件分量的事件率与灵敏度；去 SpO2 分量的标签变体（只作敏感性分析） |
| S4 | 观测稀疏、缺通道、以人工录入为主的窗口上各模型排序变差，且不同缺失机制模型差别最大 | MC-BEC Table 4；Shi 2025；项目 mp_benchmark | 按有效点数、缺失通道、来源分层的 AUROC；已有 drop20 / drop40 / continuous5min 结果按子集拆开的 ΔAUROC 与翻转率 |
| S5 | ESI 3 组内 AUROC 低于 ESI 1–2，原因是组内病情混杂而非样本少 | Sax 2023、Platts-Mills 2010（分诊直接实验） | 各 ESI 组事件率、AUROC、观测密度；ESI 3 内再做数据驱动切片 |
| S6 | 入床前等待时间与时段不同的子集表现不同 | 推断（无直接文献） | 按入床延迟分位与时段的 AUROC（先核对去标识时间） |

**五步流程。**

1. **审计：** 在冻结测试集上，对已有全部模型（XGBoost、FF-LSTM、GRU-D、BRITS、mTAND、Raindrop、OPL-MT-MNAR、MIRA、TimesFM 3.0、VIMTS-Adapter）按 A–C 子集打分，交回子集 × 模型的 AUROC、AUPRC、患病率、校准、固定阈值灵敏度及区间。
2. **发现：** 在发现用数据上跑 AFISP 式稳定性分析与误差聚类，在确认用数据上复核，交回可读的子集规则、规模与 AUROC。
3. **归因：** 对每个确认的子集依次检查 C1–C7（基础率、学习曲线、过程分层与 mask 替换、事件分量、校准斜率、域分类器），得到每个子集的主要原因与证据强度。
4. **修复：** 按 F1 → F4 → F3 → F5 / F6 的顺序做，F7 / F8 只作对照；交回最差子集 AUROC、总体 AUROC、校准与 FNR 差距的权衡表。
5. **复现：** 在 MIMIC-IV-ED 上用对齐的 5 个变量重复步骤 1 与 3，看同一类子集是否在两个数据集都差。

**与第二部分的关系。** 第二部分的 H1–H6 是针对时序基础模型的解释假设（如短上下文、不规则采样），本节 S1–S6 是针对数据子集的假设。C 族子集（有效点数、缺失通道）把两者连在一起：如果基础模型在稀疏窗口上掉得比传统模型更多，这一结果与 H1 一致。

## 第二部分：时序基础模型背景（11-05）· 结论摘要

被比较的 14 个时序基础模型（另补 7 个）没有一个是为 "15 分钟、多变量、带缺失的急诊生命体征" 设计或评测的。最接近的是 MIRA：它见过 ICU 生命体征，原生支持不规则时间，但仍是 ICU 住院场景、单变量、只训练数值预测。没有一篇模型论文做过患者层面的亚组分析，所以 Age / Gender / ESI 亚组的结果只能从数据侧解释，不能引用论文作为先验。

| 问题 | 回答 | 证据强度 |
| --- | --- | --- |
| 哪些模型偏长上下文 | Time-MoE、Sundial、Timer-XL、Moirai 1.x、VisionTS、Chronos-2、TimesFM 2.5 / 3.0；主模型论文里最短的上下文实验是 100 点（Moirai Fig 5），没有测到 15 点量级 | 强，但 15 点区间无直接证据 |
| 哪些真正见过医疗数据 | 床旁 / ICU 生理数据只有 MIRA（100% 医疗语料）；Sundial、Timer-XL、LightGTS、MOMENT 只有少量 ECG / EEG / PPG 波形；Time-MoE、Moirai、TimesFM 2.0 只有公共卫生计数；明确见过 ED 时序的：没有 | 中—强（GiftEvalPretrain 清单未公开） |
| 哪些支持不规则时间 | 原生时间戳只有 MIRA 和 VIMTS；Chronos、Chronos-2、Moirai 2.0、MOMENT 只有缺失 mask | 强 |
| 哪些论文已发现问题 | 短上下文：Timer-XL、Chronos、Moirai、VisionTS；高频：Sundial、GIFT-Eval；患者亚组：无；独立评测 Gu et al. 2024 发现 ICU 体征上零样本多数不如从头训练 | 短上下文与高频为强；亚组 "没做" 是确定的 |
| 哪些与 MC-MED 差异最大 | VisionTS、LightGTS、Lag-Llama、Time-MoE、TimesFM 1.0、Chronos | 判断性（D1–D5 规则） |

对实验侧最直接的含义：15 分钟窗口在 Sundial、TimesFM、Timer-XL、Moirai、Aurora 里只形成 1 个部分填充的 token（按 patch 长度推算）。结果表建议加 "实际 token 数 / 有效观测点数" 两列，作为解释的第一层证据。

## 调研范围与口径

本报告只做文献与模型背景调研，未跑实验；所有判断都附论文位置，没读到原文的地方标了阅读范围。未接触 MC-MED、MIMIC、eICU 的逐条记录。

- **主模型（14 行）**：MIRA、Time-MoE、Sundial、TimesFM 1.0、TimesFM 2.5 / 3.0、Timer-XL、VisionTS、VIMTS、Aurora、LightGTS、Chronos / Chronos-Bolt、Chronos-2、Moirai 1.x、Moirai 2.0。
- **补充模型**：MOMENT、Lag-Llama、Timer（UTSD）、Moirai-MoE、VisionTS++、TimesFM 2.0、PULSE-ICU（EHR 事件级基础模型，作为另一条路线的参照）。
- **名称辨析**：VIMTS = Hu et al.，ICML 2025（arXiv 2505.22815），是不规则多变量时序的视觉 MAE 方法，不是跨数据集基础模型。Aurora = 华东师大多模态预测模型（ICLR 2026，arXiv 2509.22295），不是微软的地球系统模型。TimesFM 3.0 只有 HF 模型卡与 2026-08-31 的 Google Research 博客，没有论文；Chronos-Bolt 也没有论文。
- **MC-MED 目标设定**：decomp\_60、六项生命体征、输入窗口 0–15 分钟、监护数值为 1 分钟均值，推算每个变量每个窗口至多约 15 个点。

| 标签 | 口径 |
| --- | --- |
| Medical | Yes = 语料全部或主要为医疗；Partial = 列出部分医疗数据（注明是生理信号还是公共卫生计数）；No = 清单无医疗；Not reported = 无可判断的清单。占比没给就写 Not reported，不估算 |
| ICU / ED | 分开写；只有论文或数据卡明确写出才算 Yes，不按数据集名称推断 |
| Time scale | Long-context oriented = 论文把长上下文作为设计目标，或训练 / 评价上下文约 ≥1000；Medium = ≤512 且未强调长上下文；Mixed / unclear = 按数据集变化或未报告 |
| Zero-shot | 表中的 zero-shot 都指 "在训练未见的数据集上直接做数值预测"，不是零样本临床结局预测 |
| 证据类型 | 直接实验 > 独立评测 > 作者陈述 / 分析 > 设计推断 > 无证据 |

## 预训练数据与医疗内容

只有 MIRA 的预训练以床旁生理数据为主；其余模型的医疗内容要么是少量波形，要么是公共卫生汇总计数，或者无法判断。没有模型明确见过 ED 时序。

| Model | 预训练主体（位置） | Medical | 医疗内容 | ICU | ED |
| --- | --- | --- | --- | --- | --- |
| MIRA | MIMIC-III 88.06%、MIMIC-IV 10.57%、WAVES、PTB-XL、Sleep-EDF，共 454B；从 Time-MoE 续训（Table 7、Sec 3.3） | Yes | ICU 生命体征与化验、ECG、睡眠 EEG | Yes | 不明确：MIMIC-IV 描述含急诊入院，未说明用 ED 模块 |
| Sundial | TimeBench：ERA5 62.3%、LOTSA 22.3%、Chronos 数据 9.1%、ECG 4.65%（1032B，Table 4） | Partial | ECG 48B（库名未给） | Not reported | No |
| Timer-XL | UTSD + LOTSA（Table 9） | Partial | 经 UTSD：EEG、ECG、PPG、BIDMC32HR 心率、动物血压 | Not reported | No |
| LightGTS | 33 个数据集（Table 7） | Partial | EEG、ECG、动物血流动力学 | Not reported | No |
| Aurora | 跨域多模态语料，>1B 点（App A.1） | Partial | "Health" 领域，具体数据集未列 | Not reported | Not reported |
| Time-MoE | Time-300B：Nature 90.5%（309B，Table 1） | Partial | 公共卫生计数 0.0001% | No | No |
| Moirai 1.x | LOTSA：Energy 59.2%（其中模拟建筑数据按 Table 8 算约占总量 57%）（27.6B） | Partial | 公共卫生计数 0.01% | No | No |
| TimesFM 1.0 | Wiki 浏览量、Google Trends、合成（Table 1） | No | 无 | No | No |
| Chronos | 28 个真实数据集 + TSMixup + KernelSynth（Table 3） | No | 无（医疗只在零样本评价集） | No | No |
| VisionTS | 只有 ImageNet | No | 无 | No | No |
| VIMTS | ImageNet MAE + 目标集自监督 | Partial | PhysioNet 2012、MIMIC 只作目标集 | Yes（目标集） | No |
| TimesFM 2.5 / 3.0 | GiftEvalPretrain + Wiki + Trends + 合成（模型卡） | Not reported | 2.0 含 CDC FluView；GiftEvalPretrain 清单未公开 | Not reported | Not reported |
| Chronos-2 | Chronos / GIFT 子集 + 合成（Sec 4.1） | Not reported | 清单在 Table 6，未读到 | Not reported | Not reported |
| Moirai 2.0 | GIFT Pretrain + Chronos-Mixup + 内部遥测，约 295B（Sec 4） | Not reported | 清单未公开 | Not reported | Not reported |

MIRA 的两个提醒：它从 Time-MoE 通用权重续训，所以并非只见过医疗数据；若以后用 MIMIC-IV-ED 做外部验证，需先排查与 MIMIC-IV 预训练的重叠。

## 时间尺度与上下文长度

多数模型的训练与评价上下文在 512 到 15,360 点之间；主模型的上下文实验最短测到 100 点（Moirai Fig 5）；补充模型 Lag-Llama 的连续窗口超参搜索到 32 点，但它的 lag 特征需要更长历史。Timer-XL Fig 3 的最短 lookback 以时间跨度（8 小时）表示，折合点数取决于数据频率，未核对。15 点量级没有直接证据。

> 图：各模型训练 / 评价上下文长度与 MC-MED 15 点窗口的对比（交互图见在线报告；数据见 xlsx『上下文长度证据』工作表）

时间尺度判断：Long-context oriented 为 Time-MoE、Sundial、Timer-XL、Moirai 1.x、VisionTS、Chronos-2、TimesFM 2.5 / 3.0；Medium 为 MIRA（证据有限）、TimesFM 1.0、Chronos、LightGTS、MOMENT；Mixed / unclear 为 VIMTS、Aurora、Moirai 2.0。Lag-Llama 的最优连续窗口只有 32 点，但 lag 特征要求更长的历史。

比上下文长度更直接的是 patch 长度：它决定 15 个点进入模型后还剩几个 token。

| Model | 输入切分 | 15 点窗口约等于几个 token（推算） | 论文的上下文实验与结论 |
| --- | --- | --- | --- |
| MIRA | 点级 token + 连续时间戳 | 15 | 无 |
| Time-MoE | 点级 token | 15 | 无单独消融 |
| Chronos | 点级量化 token | 15 | Fig 11b：训练上下文到 1024 前越长越好 |
| Lag-Llama | 点级 token + lag 特征 | 15，但多数 lag 取不到 | 最优 C=32；lag 需要 "L-sized or larger context"（Sec 4.1） |
| MOMENT | patch 8，固定 512，左侧补零 | 2（约 97% 为填充） | 无 |
| Sundial | patch 16 | 1 | Fig 10：480–2880，依任务而定 |
| TimesFM 1.0 | patch 32 | 1 | 无长度扫描；训练时随机遮蔽覆盖 1–512（Sec 4） |
| TimesFM 3.0 | patch 32 | 1 | 无论文 |
| Moirai 1.x | 分钟级 patch 32 / 64 / 128 | 1 | Fig 5：100–5000 越长越好 |
| Aurora | token 长 48 | 1 | 无 |
| Timer-XL | patch 96 | 1 | Fig 3：日→月持续改善；Sec 1 明言短输入学不到全局趋势 |
| LightGTS | patch = 周期长度 | ≤1 | 无（N 固定为 10） |
| VisionTS | 按周期 P 折成图像 | 取决于 P，无周期时 P=1 | Fig 6：L 越长越好，高频尤甚 |
| Chronos-2 | patch（长度正文未写） | Not reported | Fig 8c：8K 优于 2K；上下文学习在短上下文任务上收益最大（Sec 5.2） |
| VIMTS | 等长时间窗 patch（ICU 为 8 个时间步） | 需重设窗长 | 无 |

两条反向线索值得在实验中留意：TimesFM 1.0 训练时刻意让模型见到所有短上下文；Al Attrach et al.（ICLR 2026 研讨会，基于摘要）在 MIMIC-IV 上发现近期窗口只有 8 个事件时，基础模型摘要带来的 AUROC 提升最大（相对 +6.5%）。

## 不规则时间与缺失处理

只有 MIRA 和 VIMTS 原生接收时间戳；其中只有 MIRA 能零样本使用。其余模型假设规则网格，最多带一个缺失 mask。

| 类别 | 模型 | 机制（位置） | 对 MC-MED 的含义 |
| --- | --- | --- | --- |
| 原生时间戳，可零样本 | MIRA | 输入 (值, 时间戳)，CT-RoPE 连续时间位置编码，Neural ODE 外推到任意目标时刻（Sec 3.1–3.2） | 能直接吃不等间隔的体征；但推理时 NaN / mask 如何处理未说明，README 推理示例无 mask |
| 原生时间戳，需目标集训练 | VIMTS | 可学习连续时间嵌入 + 可用性 mask + GCN 跨通道补全（Sec 2.3） | 设计最贴近，但必须在 MC-MED 上自监督 + 训练，不属于零样本 |
| 只有缺失 mask | Chronos、Chronos-2、Moirai 2.0、MOMENT | PAD token（Chronos Sec 3.1）；二值 mask，缺失不参与归一化（Chronos-2 Sec 3.1）；缺失指示（Moirai 2.0 Eq 1）；观测 mask（MOMENT） | 能表达 "这里没值"，不能表达间隔长短 |
| 规则网格，需预先处理 | TimesFM、Time-MoE、Sundial、Timer-XL、Moirai 1.x、LightGTS、VisionTS、Aurora | TimesFM 2.0 模型卡要求先线性插值；Time-MoE、Moirai 预训练前在缺失处切分或过滤缺失多的序列 | 插值 / 前向填充方式本身是管线的一部分，需在报告中写明 |

预训练阶段见过不规则数据的只有 MIRA（MIMIC-III "irregular sampling patterns and substantial missingness"，App E）。Time-MoE、Moirai、Moirai 2.0 在预训练前主动去掉了缺失段，模型几乎没见过带缺失的输入。

## zero-shot 的真实含义

论文里的 zero-shot 都是 "在训练没见过的数据集上直接做数值预测"，没有一篇做零样本临床结局预测。MC-MED decomp\_60 是二分类结局，所以只有下表第一种用法和论文口径一致。

| 用法 | 是否用 MC-MED 标签 | 与论文 zero-shot 的关系 | 项目已有结果 |
| --- | --- | --- | --- |
| 预测轨迹 → 规则或阈值预警 | 不用 | 唯一与论文口径一致的用法 | week02 F4：AUROC 0.55–0.59（公开数据） |
| 冻结嵌入 + 线性探针 / 分类器 | 用 | 不是 zero-shot，建议称 "冻结表示 + 探针" | week02 F2、F3 |
| Adapter / 微调 | 用 | 不是 zero-shot | 合作同学的 VIMTS-Adapter |

其他三点：

- **推理时用上下文自身的统计量归一化**：TimesFM 用首个 patch 的均值方差（Sec 5）；Sundial 用样本内两阶段实例归一化（Sec 4.1.1）；Chronos 用均值缩放（Sec 3.1）；Chronos-2 用标准化 + arcsinh（Eq 1–2）；Moirai 2.0 只用前 30% 的统计量（Sec 3.1）。在 15 点窗口上，这些统计量本身就不稳定。
- **"未见数据集" 的核查程度不同**：Chronos-2 Table 3 估计各模型在 GIFT-Eval 上的泄漏率为 Chronos-2 0%、TimesFM-2.5 8%、Moirai-2.0 28%；GIFT-Eval 论文称 TimesFM、Chronos、Moirai 的预训练与其测试集部分重叠；MIRA 的 OOD 集 CinC 2012 与 MIMIC 的关系未讨论。
- **两个特例**：VIMTS 没有 zero-shot（Sec 6 自述）；VisionTS 是跨模态 zero-shot，只用 ImageNet 图像预训练。

## 论文自带的分析与已知失效模式

没有一篇模型论文做患者层面（年龄、性别、病情严重度）的亚组，最细到数据集 / 领域 / 频率 / 预测长度。鲁棒性实验只有 MIRA（缺失率）和 LightGTS（采样粒度）两项。

| Model | 亚组（最细到） | 鲁棒性 | 域偏移 / 迁移 | 上下文长度 |
| --- | --- | --- | --- | --- |
| MIRA | 数据集 | 缺失率 10%→90%，RMSE 2.85→3.97（WHO FluNet，Table 4） | OOD vs ID（Tables 2–3） | 无 |
| Time-MoE | 数据集 × 预测长度 | 无 | 零样本 vs 微调 | 无 |
| Sundial | 数据集 | 无 | 数据规模 94B / 230B / 1032B（Table 8） | Fig 10 |
| TimesFM 1.0 | 数据集 | 无 | 去掉合成数据后欠代表频率变差（Fig 3d） | 无（只比较 patch 长度） |
| TimesFM 2.5 / 3.0 | 无论文 | 无论文 | 无论文 | 无论文 |
| Timer-XL | 数据集 × 预测长度 | 3 个种子的方差 | ERA5 跨时间 / 站点 | Fig 3、Table 15、Fig 8 |
| VisionTS | 数据集 | 无 | 嵌入分布（Fig 7） | Fig 6 |
| VIMTS | 数据集 | 无 | 无 | 无 |
| Aurora | 领域（TimeMMD 含 Health） | 无 | 零样本 vs 10% few-shot | 无 |
| LightGTS | 数据集 × 预测长度 | 采样粒度变化（Fig 4） | 跨时间尺度（Fig 2b） | 无 |
| Chronos | 数据集 | 合成模式定性分析（Figs 12、16） | Benchmark I vs II | Fig 11b |
| Chronos-2 | fev 任务子集 | 无 | 纯合成数据版本（Fig 8b） | Fig 8c |
| Moirai 1.x | 数据集 | 无 | 数据多样性消融（Table 7） | Fig 5 |
| Moirai 2.0 | 领域与预测长度（Figs 3–4） | 无 | 领域排名 | 无 |

已知失效模式按证据强度整理如下（完整 34 条见 xlsx『失效模式证据』）：

| 失效模式 | 最强证据 | 证据类型 | 对 MC-MED 的外推程度 |
| --- | --- | --- | --- |
| 短上下文下差 | Timer-XL Sec 1 + Fig 3；Chronos Fig 11b；Moirai Fig 5；Gu et al. 2024 Fig 3（ICU 体征） | 直接实验 + 作者陈述 | 低：实验都在 ≥100 点 |
| 分钟级 / 高频数据差 | Sundial App E；GIFT-Eval Sec 4.1；TimesFM Fig 3d | 作者陈述 + 独立基准 | 中 |
| 缺失 / 稀疏下差 | MIRA Table 4；预训练过滤缺失（Time-MoE、Moirai） | 直接实验 + 设计 | 中；但 week02 F3 显示稀疏不一定让 TSFM 相对变差 |
| 异常值 / 急性变化被平滑 | Gu et al. 2024 Table 4；Chronos Fig 12b；Sundial App C.1 | 独立评测 + 作者分析 | 中，可在高危 ESI 组检验 |
| 平坦序列精度损失（如 SpO₂） | Chronos Fig 16b | 作者分析 | 中，可按变量检验 |
| 单变量丢失体征间关系 | Gu et al. 2024 Fig 4；Chronos-2 Sec 5.2 | 独立评测 | 中 |
| 老年 / 性别 / ESI 亚组差 | 无 | 无证据 | 只能从数据侧解释 |
| 跨院偏移 | Pucher et al. 2026（基于摘要，迁移性好）vs week02 F2（嵌入跨院不如手工特征） | 独立评测 + 项目内实验 | 方向不一致 |

## 与 MC-MED 的匹配评估

与 MC-MED 差异最大的是 VisionTS、LightGTS、Lag-Llama、Time-MoE；最接近的是 MIRA（数据层面）和 VIMTS（输入设计层面，但不是零样本基础模型）。两个评级分开看：预训练分布相似度看语料里有没有床旁生理与急诊数据，输入设计适配度看模型能不能直接吃下 15 点、带缺失、多变量的输入。

> 图：预训练分布相似度 × 输入设计适配度二维定位（交互图见在线报告；评分见 xlsx『预训练分布vsMC-MED』工作表）

| Model | 预训练偏长 / 短 | Medical | Irregular | 高频生命体征 | ED | 主要不匹配 |
| --- | --- | --- | --- | --- | --- | --- |
| MIRA | 中等（≤512） | Yes | Yes | ICU 体征（频率未报告）+ 100 Hz 波形 | 不明确 | 成人 ICU（MIMIC-III 2001–2012）而非到院 15 分钟；单变量；与 MIMIC-IV-ED 可能重叠 |
| Time-MoE | 长（≤4096） | Partial | No | No | No | 90.5% 气象；缺失段被切掉 |
| Sundial | 长（2880） | Partial | No | 只有 ECG 波形 | No | 15 点不足 1 个 patch；作者称高频无保证 |
| TimesFM 1.0 | 中等（512） | No | No | No | No | Wiki / Trends 为主；归一化只靠 ≤15 点 |
| TimesFM 2.5 / 3.0 | 长（16k / 15,360） | Not reported | Not reported | Not reported | Not reported | 无论文；3.0 权重非商用 |
| Timer-XL | 长（2880） | Partial | Not reported | Partial（心率、PPG） | No | patch 96；最佳 lookback 在日到月量级 |
| VisionTS | 长（1728–4032） | No | No | No | No | 要按周期折图，15 分钟体征没有周期 |
| VIMTS | 按数据集（ICU 24 h） | Partial | Yes | ICU 体征（目标集） | No | 需在 MC-MED 训练；patch 需重设 |
| Aurora | 不明确 | Partial | No | Not reported | Not reported | 依赖文本模态；通道独立 |
| LightGTS | 中等（约 528） | Partial | No | No | No | 周期 tokenization；FFT 周期不准时性能受损 |
| Chronos | 中等（512） | No | No | No | No | 平坦序列（如 SpO₂）精度下降；指数趋势失败 |
| Chronos-2 | 长（8192） | Not reported | No | Not reported | Not reported | 多变量能力全来自合成数据 |
| Moirai 1.x | 长（1000–5000） | Partial | No | No | No | 约 57% 模拟建筑数据；分钟级 patch ≥32 |
| Moirai 2.0 | 不明确 | Not reported | No | Not reported | Not reported | 单变量；含内部遥测 |

没有一个模型在 "高频生命体征" 一列有 1 分钟监护数值的明确证据，也没有一个在 ED 一列为 Yes。

## 独立临床评测与项目已有结果

唯一读到原文、且场景最接近 MC-MED 的独立评测是 Gu et al.（ML4H 2024）：在 eICU 与 MIMIC-III 床旁体征上，多数 TSFM 的零样本表现不如从头训练的传统模型。其余独立评测只读到摘要，方向不完全一致。

| 论文 | 数据与设定 | 主要发现 | 阅读范围 |
| --- | --- | --- | --- |
| Gu et al.，ML4H 2024（PMLR 259:401–419） | eICU 6,199 患者、MIMIC-III Waveform 1,089 患者；5 分钟重采样；历史 6 h、预测 3 h；HR、SBP、DBP、RR、SpO₂ | 零样本多数不如从头训练（eICU HR MAE：GRU 4.462、TimesFM 5.228、Chronos-S 4.807、Lag-Llama 7.365，Table 3）；异常值检测差（Table 4）；NEWS2 变化检测与传统方法相当（Table 5）；历史越长多数越好（Fig 3）；Moirai 用五项体征明显改善（Fig 4） | 正文与 Tables 1–6 原文 |
| Pucher et al.，Artif Intell Med 2026（doi:10.1016/j.artmed.2026.103473） | 埃森大学医院 + 2 家地区医院 + MIMIC-IV；6 个临床用例 | 零样本 "frequently approached" 优化后的专用模型；跨医院迁移性更好 | 基于摘要 |
| Pucher et al.，AI4TS 2025 | 德国大学医院 EHR + 2 个外部验证集 | 专用模型多数场景更准；零样本在外部集上 competitive | 基于摘要 |
| Syed et al.，ICML 2026 立场论文 | 7 个 TSFM × 72 个数据集 × 6 个领域 | "substantial cross-domain variability"；主张医疗单独做基准 | 基于摘要 |
| Al Attrach et al.，ICLR 2026 研讨会 | MIMIC-IV 不规则事件 | 近期窗口 8 个事件时缓存的基础模型摘要使 AUROC 相对 +6.5%，256 个事件时 +0.1%（不显著） | 基于摘要 |

与项目已有结果对照（只用聚合量）：

| 已有结果 | 口径 | 与本调研的关系 |
| --- | --- | --- |
| week02 F1：零样本体征预测中 TimesFM 系列领先，MIRA 见过 MIMIC 也没领先 | 公开数据 | MIRA 的医疗语料优势没有转化为零样本预测优势；TimesFM 1.0 覆盖短上下文的训练设计可能有关（假设） |
| week02 F3：稀疏到每变量 1 个值，TSFM 探针相对 LR 仍 +0.041 AUPRC | 公开数据 | 短 / 稀疏窗口不一定让 TSFM 相对变差 |
| week02 F4：零标签 "预测轨迹 → 预警" AUROC 0.55–0.59 | 公开数据 | 与 "论文的 zero-shot 是数值预测" 一致 |
| 合作同学 MC-MED decomp\_60 汇总：XGBoost AUPRC 0.317；MIRA-Large 0.218；VIMTS-Adapter 0.159；TimesFM 3.0 0.146 | N=1,328、事件 224（16.87%）；与冻结 benchmark 测试集（5,236，患病率 12.0%）口径不同；无置信区间 | 数据相似度最高的 MIRA 在三者中最高，但输入设计适配度最高的 VIMTS 并不高；三个点不足以检验任何假设 |

## 对本项目的建议

解释 MC-MED 上的 TSFM 结果时，先用数据侧的聚合量（实际 token 数、窗口内有效观测点数、各亚组观测密度）把假设变成可检验的，再决定写 "与某假设一致"。下表是供实验侧选用的假设；做不做、怎么做由研究者决定。

| 假设 | 调研证据 | 需要的聚合量或对比 |
| --- | --- | --- |
| H1 有效 token 太少：patch ≥15 的模型在 15 分钟窗口里只有 1 个填充 token | Sundial Table 5、TimesFM Sec 4、Timer-XL Table 11、Moirai App B.1；Timer-XL Sec 1 | 点级 token 模型（MIRA、Chronos、Time-MoE）与 patch 模型各自相对基线的差距；按窗口内有效观测点数分层 |
| H2 缺失模式不匹配：预训练几乎没见过带缺失的输入 | Time-MoE App C、Moirai App A、Moirai 2.0 Sec 4；TimesFM 2.0 要求插值 | 现有 drop20 / drop40 / continuous5min 测试集上，TSFM 与传统模型的 Δ 对比 |
| H3 归一化统计量不稳：只有 15 个点估均值方差 | TimesFM Sec 5、Sundial Sec 4.1.1、Chronos Fig 16b | 按变量（尤其 SpO₂）或窗口内方差分层的表现 |
| H4 单变量模型丢失体征间关系 | Gu et al. 2024 Fig 4；Chronos-2 Sec 5.2 | 多变量模型与通道独立模型对比 |
| H5 亚组差异来自数据侧而非预训练 | 所有模型论文都没有患者亚组 | Age / Gender / ESI 各亚组的观测密度、实际输入长度、事件率、基线体征分布 |
| H6 急性 / 高危轨迹被平滑 | Gu et al. 2024 Table 4；Chronos Fig 12b；Sundial App C.1 | 高危 ESI 组的灵敏度与校准 |

结果解释的写法：

- 不写："因为预训练没有 ED 数据，所以 TimesFM 3.0 表现差。"
- 可以写："TimesFM 3.0 在 0–15 分钟窗口上 AUPRC 低于 XGBoost。这一结果与 '输入远短于模型预训练与评测所用上下文（15,360）' 的假设一致（依据：模型卡；Timer-XL Sec 1 的作者陈述），本研究未直接检验上下文长度的作用。"
- 设计推断（如 "只形成 1 个 token"）不能写成 "论文发现"。

研究者决定（11-06，两部分合并共 6 项）：

1. **输入窗口：视情况延长。** MC-MED 输入的稀疏程度原本按旧版 GD / GAM 设定，新版数据的生命体征与检验更密，所以先查新版 GD / GAM 是否满足条件（检查项见下）。延长会改变既定 benchmark 设定，需登记为新版本；延长前，上下文相关的解释仍只写 "与假设一致"。
2. **VIMTS 放在不规则时序专用模型组**，与 GRU-D、mTAND、Raindrop 等同组比较，不归入基础模型组；zero-shot 口径只用于其余基础模型。
3. **老年从 65 岁起算，按 65–74 / ≥75 切分**；其余按建议：子集主指标为 AUROC + 校准，AUPRC 与患病率并列，每个子集至少约 30 个事件。这一口径只用于子集审计，项目 D70（≥60 岁主分析、≥65 岁亚组）不变；子集表另报 ≥60 以便对齐（研究者 11-06 确认）。
4. **MIRA 分开考虑**：MIMIC-IV / MIMIC-IV-ED 上的结果单独成表并标注预训练重叠，不与其他模型合并排名。
5. **子集发现与确认（按建议）**：在验证集上做数据驱动的子集发现，在冻结测试集上确认，切分方式登记在案。
6. **标签变体与分组阈值（按建议）**：主分析用原标签与单一阈值；去掉 SpO2 分量的标签、年龄校正阈值、分组阈值都只作敏感性分析。

**延长窗口前的密度检查（建议；在本地对 GD / GAM 运行，只交回聚合量）：**

- **每例观测数**：各生命体征 / 检验在候选窗口内的每例观测数中位数与 IQR，分 GD / GAM、新旧版本；候选窗口长度需研究者定。
- **覆盖率**：窗口内至少 1 次、至少 3 次观测的就诊比例（每个变量）。
- **观测间隔**：相邻两次观测间隔的中位数与 IQR，用来决定 MC-MED 降采样或 drop 的强度。
- **同时观测**：核心体征在窗口内都有观测的就诊比例，即多变量模型的可用样本量。
- **按年龄分层**：以上各项按 <65 / 65–74 / ≥75 分层，因为观测密度随年龄变化本身就是子集差异来源（C3）。
- **判定**：若新版 GD / GAM 在更长窗口内仍有足够观测，就把 MC-MED 窗口延长到相应长度，并按新版密度重设降采样与 drop；"足够" 的阈值需研究者定。

## 局限与配套文件

本调研有 5 类局限，对应字段在 xlsx 里都标了阅读范围。

- **第一部分的阅读范围**：33 篇中 14 篇只读到摘要（ESI 分诊、预警评分、脉搏血氧、Meng、Guo、Barda、Pfohl、Locati 等）；PMC 与 Europe PMC 网页在本环境被拦截，部分全文经 PubMed 工具取得；MC-BEC 附录与 Lett 2025 补充表未读。MC-BEC Table 5 性别差值与显示值不符，Lett 2025 预印本与正式版部分百分比有出入，引用前需核对原文。S2、S6 是设计推断，S3 把 ICU 证据迁移到急诊。
- **未读到原文**：Chronos-2 Table 6（训练数据清单）与附录、Aurora ICLR 版附录、Time-MoE App D 与 Table 10 后半、Moirai 2.0 Sec 6 与附录、GIFT-Eval App D/E、VisionTS 附录 B.9。
- **无论文**：TimesFM 2.5 / 3.0、Chronos-Bolt 只有模型卡与 README；独立评测除 Gu et al. 外只读到摘要。
- **推算与判断**："15 点约等于几个 token" 按 patch 长度推算；D1–D5 与两个评级是本调研的判断规则，研究者可以改。BIDMC32HR 原始来源为重症监护患者一条凭记忆，需核对原数据集说明。
- **论文内部不一致**：MIRA Sec 3.3 称含流行病与心理健康数据，Table 7 没有；正文称 7 个 OOD 数据集，Table 2 只有 6 个。Timer-XL 的 UTSD 点数正文写 10 亿，Table 9 为 868.8M。LightGTS 正文 N=10，App A.4 为 N=4。

配套文件（项目共享目录 tsfm\_survey\_20261105 与 G:\\BaseModel\\research\\tsfm-survey-20261105\\）：

| 文件 | 内容 |
|---|---|
| FOUNDATION_MODEL_SURVEY.xlsx | 20 个工作表。11-06 新增 10 个：子集缺陷证据、原因机制 C1–C7、子集发现方法、对策证据 F1–F8、MC-MED 子集审计方案、子集假设 S1–S6、审计步骤、需研究者决定（含 11-06 决定）、窗口密度检查、来源_子集调研；其余 10 个为 11-05 的时序基础模型调研 |
| csv/ | 同上，每个工作表一个 UTF-8 CSV（20 个） |
| FOUNDATION_MODEL_SURVEY.md | 完整调研文本：A 部分子集缺陷，B 部分逐模型详细记录 |
| ONE_PAGE_CONCLUSION.md | 一页结论（A 子集缺陷 + B 时序基础模型） |
| REPORT.md | 本报告的 Markdown 导出 |
| tsfm_survey_demo.html | 演示版，离线可直接打开 |

来源（第二部分：主要论文与模型卡）：

- [MIRA](https://arxiv.org/abs/2506.07584) · [Time-MoE](https://arxiv.org/abs/2409.16040) · [Sundial](https://arxiv.org/abs/2502.00816) · [TimesFM](https://arxiv.org/abs/2310.10688) · [TimesFM 代码与模型卡](https://github.com/google-research/timesfm) · [Timer-XL](https://arxiv.org/abs/2410.04803) · [Timer](https://arxiv.org/abs/2402.02368)
- [VisionTS](https://arxiv.org/abs/2408.17253) · [VisionTS++](https://arxiv.org/abs/2508.04379) · [VIMTS](https://arxiv.org/abs/2505.22815) · [Aurora](https://arxiv.org/abs/2509.22295) · [LightGTS](https://arxiv.org/abs/2506.06005)
- [Chronos](https://arxiv.org/abs/2403.07815) · [Chronos-2](https://arxiv.org/abs/2510.15821) · [Moirai](https://arxiv.org/abs/2402.02592) · [Moirai-MoE](https://arxiv.org/abs/2410.10469) · [Moirai 2.0](https://arxiv.org/abs/2511.11698) · [MOMENT](https://arxiv.org/abs/2402.03885) · [Lag-Llama](https://arxiv.org/abs/2310.08278) · [GIFT-Eval](https://arxiv.org/abs/2410.10393)
- Gu et al. 2024（ML4H，PMLR 259:401–419） · [Pucher et al. 2026](https://doi.org/10.1016/j.artmed.2026.103473) · [PULSE-ICU](https://arxiv.org/abs/2511.22199)

来源（第一部分：子集缺陷；各篇阅读范围见 xlsx『来源_子集调研』）：

- MC-MED 与急诊基准：[MC-BEC](https://arxiv.org/abs/2311.04937) · [MC-MED（Sci Data 2025）](https://doi.org/10.1038/s41597-025-05419-5) · [MC-MED PhysioNet](https://physionet.org/content/mc-med/1.0.0/) · [SignalMC-MED](https://arxiv.org/abs/2603.09940) · [Xie 2022 MIMIC-IV-ED 基准](https://arxiv.org/abs/2111.11017)
- 分组表现与公平：[Lett 2025](https://doi.org/10.1001/jamanetworkopen.2025.12947) · [FAIM](https://arxiv.org/abs/2403.05235) · [Röösli 2022](https://doi.org/10.1038/s41597-021-01110-7) · [Meng 2022](https://doi.org/10.1038/s41598-022-11012-2) · [Guo 2022](https://doi.org/10.1038/s41598-022-06484-1) · [Zhang 2021](https://arxiv.org/abs/2103.11163) · [Seyyed-Kalantari 2021](https://pubmed.ncbi.nlm.nih.gov/34893776/) · [Oakden-Rayner 2020](https://arxiv.org/abs/1909.12475)
- 测量过程与测量误差：[Shi 2025](https://doi.org/10.1186/s12911-025-03058-9) · [Agniel 2018](https://doi.org/10.1136/bmj.k1479) · [Jeanselme 2022](https://proceedings.mlr.press/v193/jeanselme22a.html) · [Wong 2021](https://doi.org/10.1001/jamanetworkopen.2021.31674) · [Mettler 2024](https://www.medrxiv.org/content/10.1101/2024.03.28.24305036v1) · [Pradhan 2025](https://doi.org/10.3389/fmed.2025.1606254)
- 分诊与老年：[Platts-Mills 2010](https://doi.org/10.1111/j.1553-2712.2010.00670.x) · [Grossmann 2014](https://doi.org/10.1371/journal.pone.0106203) · [Sax 2023](https://doi.org/10.1001/jamanetworkopen.2023.3404) · [Kemp 2020](https://doi.org/10.1186/s12873-020-00379-y) · [Martín-Conty 2024](https://doi.org/10.1093/qjmed/hcae031)
- 子集发现、指标与对策：[AFISP](https://doi.org/10.1038/s41746-024-01275-6) · [McDermott 2024](https://arxiv.org/abs/2401.06091) · [SubpopBench（Yang 2023）](https://proceedings.mlr.press/v202/yang23s.html) · [Domino](https://arxiv.org/abs/2203.14960) · [Barda 2021](https://doi.org/10.1093/jamia/ocaa283) · [Pfohl 2021](https://doi.org/10.1016/j.jbi.2020.103621) · [Chen 2018](https://arxiv.org/abs/1805.12002) · [Tan 2026](https://arxiv.org/abs/2604.03478) · [Locati 2026](https://icml.cc/virtual/2026/71757)
