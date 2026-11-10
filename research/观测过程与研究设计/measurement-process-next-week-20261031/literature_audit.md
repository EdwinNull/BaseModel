# 下周最小方法试点：8 篇关键文献核验与实现约束

- 核验日期：2026-10-31。
- 范围：定向复核 v1.1 计划中的 8 篇关键文献；不是穷尽性检索，不能据此声称“首次”或“截至今日没有其他工作”。
- 读法：优先公开全文的方法、假设和结果；没有将题录或摘要当作全文。机器可读来源与检索参数见 `literature_sources.jsonl`。
- 下周按 11 月 2–8 日安排：周一审计与锁协议；周二策略估计与支持审计；周三顺序删观测、匹配随机删减与模拟单元检查；周四 LR/LightGBM 的 M0/M1/M2 及分类后训练接口；周五仅在检查通过后运行一个骨干的试点；周六稳健性评价；周日门槛决策。M3/M4 下周只形成设计约束。
- 数据边界：没有打开 `data/`，没有读逐患者内容。下述外部论文的样本量属于已发表公共信息。

## 先改研究定位，再实现

**值得检验的贡献是：在可见历史与共同支持限制下，用结构化时序记录稀疏化，对预训练预测模型做后训练，是否比强度和结构匹配的随机删减更稳健。** 目前文献不能支持“找到了纯生理表示”“因果分解了医院偏差”或“恢复了真实换院的反事实结局”。

1. **“按相对测量率给源数据再掩码”已有直接先行方法。** Zhou 等 AISTATS 2023 §6 Algorithm 1 在目标更稀疏的 UCAR 情形已提出额外掩码源数据，使其分布与目标一致。只删不加、比率掩码本身不足以构成新颖性。可能的推进在历史依赖与联合时序结构、可实现性边界、后训练算法和实证收益；这些仍待证明。
2. **删除记录是一种模型输入干预。** 固定了原患者、治疗路径与结局后，不能解释为真实改变医院测量策略的全部效果。测量影响后续治疗和结局时，两者不同。
3. **适当评分是清晰的主目标，但不是完整目标的自动校准保证。** BCE/Brier 对各自训练分布适当；加入一致性或域惩罚后，总目标未必仍以原条件概率为唯一最优解，必须评价原始 log loss/Brier 和校准。
4. **同一患者删掉信息，合理的风险后验也可能变化。** Veitch 的“无关因素”不变性不能直接推出所有稀疏视图预测相等。M3 后置，先在已知真值的模拟中找出何时不变、何时应回缩。
5. **无标签环境上下文不等于纯策略。** ARM 支持利用无标签同域批次适应；它没有证明临床测量描述子能自动区分病例构成与医生行为。M4 需要病例构成敏感性与独立支持集设计。
6. **最近预印本应按可复现程度分配基线资源。** Zhang & Li 的正文提供概念和汇总数值，但缺少足够复现细节；优先实现透明 DANN/IRM 类对照。Londschien 提供明确数据与代码链接，更适合落实强表格基线。

## 文献与本周交付的对应

| 编号 | 核验文献 | 状态及实际阅读深度 | 对下周的直接用途 |
|---|---|---|---|
| L01 | Zhang & Li, *Learning Clinical Representations Under Systematic Distribution Shift* | arXiv:2603.07348v1，2026-03-07；核验到预印本，无期刊信息。已读公开全文主文的方法、结果与讨论 | 周一界定贡献；周四/周日登记 DANN/IRM 后续基线及复现差异 |
| L02 | Jeanselme et al., *Prediction of Survival Outcomes under Clinical Presence Shift: A Joint Neural Network Architecture* | arXiv:2508.05472v1，2025-08-07；核验到预印本。已读 §4–7、Table 1 和代码入口 | 周一同测试集比较；周二小扰动理论边界；周日联合建模对照设计 |
| L03 | Zhou, Balakrishnan & Lipton, *Domain Adaptation under Missingness Shift* | AISTATS 2023，PMLR 206:9577–9606。已读正式论文 §1–6 与算法相应段落；未逐行复核附录证明 | 周二策略估计与支持边界；周三 UCAR 正/负对照、顺序删减和匹配随机基线 |
| L04 | Agniel, Kohane & Weber, *Biases in electronic health record data due to processes within the healthcare system: retrospective observational study* | BMJ 2018;361:k1479。已读全文方法、结果、讨论，并核勘误正文 | 周一记录过程特征定义；周三时间与频率统计验收 |
| L05 | Londschien et al., *Domain Generalization and Adaptation in Intensive Care with Anchor Regression* | arXiv:2507.21783v2，2026-02-28 更新；原提交 2025-07-29；核验到预印本。已读 §2–4、§5–6 相关部分及代码入口 | 周一按患者与域切分；周四/周日 anchor 强基线；周六选择/评价分离 |
| L06 | Zhang et al., *Adaptive Risk Minimization: Learning to Adapt to Domain Shift* | NeurIPS 2021；读 arXiv:2007.02931v4，2021-12-01。已读 §3–5、Table 1、附录 B/C/F 相关段落 | 周四预留 M4 接口；周日形成独立无标签支持集与支持量消融设计 |
| L07 | Veitch et al., *Counterfactual Invariance to Spurious Correlations in Text Classification* | NeurIPS 2021 正式标题经会议页核验；实际读 arXiv:2106.00545v3，2021-11-02，标题为 *Counterfactual Invariance to Spurious Correlations: Why and How to Pass Stress Tests*。已读 Definition 1.1、§3–4、§6 相关段落；未复核全部证明 | 周一/三列可不变/不可不变场景；周日形成 M3 设计约束 |
| L08 | Gneiting & Raftery, *Strictly Proper Scoring Rules, Prediction, and Estimation* | JASA 2007;102(477):359–378。正式出版题录由 Crossref 核验；公开阅读版本是 2004 年 UW Technical Report 463 的 §1、§3、§4.3，不能称已读 2007 正式版全文 | 周四/五 BCE/Brier 主目标；周六评分符号和 Monte Carlo 口径；周日限制总目标的理论表述 |

## 每篇必须落实的一件事

### L01：最近的概念邻近工作，不是可直接复现的数值标尺

- 链接：[预印本](https://arxiv.org/abs/2603.07348v1) · [全文](https://arxiv.org/html/2603.07348v1)。作者 Yuanyun Zhang、Shi Li。
- 方法：监督适当评分 + 环境对抗分类器 + 跨环境最优线性预测器差异惩罚。四家医院系统三训一测，约 40M 多模态编码器；表 2 报告监督模型 AUROC 0.819、所提方法 0.842。
- 本轮所读正文没有给出医院名称、队列规模、完整拆分、详细超参、重复种子/区间或代码。因此可以注明“参考其原则实现的 DANN/IRM 类基线”，不能把自建实现写成忠实复现。
- **验收问题**：相同骨干、信息集、源标签、训练预算下，M2 是否优于透明的不变学习基线？是否同时保留预测充分性和原始概率评分？
- **不可直接沿用**：其 `p(y|z)` 不受环境影响的假设不适用于所有治疗/流程结局。正文无条件环境对抗目标也不能自动推出 `h(X) ⟂ E | Y`，更不能据此证明学到“纯生理”。下周不新增该大模型训练。

### L02：联合建模是对照路线，周末效应不是纯测量干预

- 链接：[预印本/全文](https://arxiv.org/html/2508.05472v1) · [论文给出的代码](https://github.com/Jeanselme/MultitaskTransportability)。作者 Vincent Jeanselme、Glen Martin、Matthew Sperrin、Niels Peek、Brian Tom、Jessica Barrett。
- DeepJoint 用共享 LSTM，同时拟合下次观测间隔、缺失标记和 DeepSurv 生存模型。MIMIC-III 31,692 人、21 类检验，首 24 h 记录预测后续生存；比较周内训练→周末测试和周末训练→同一周末测试，并匹配训练患者数。
- **可直接借鉴**：迁移模型和本域参照在同一测试人群上比较；输入相同的 Feature 臂隔离“联合建模”收益。下周 M0/M1/M2 必须共享患者、输入变量、checkpoint 和预算。
- Table 1 的总体 transfer loss，DeepJoint 与 Feature 都为 0.011（std 均 0.009）；7/30 天有差异，但不足以据此宣称对所有跨院偏移取得明显优势。其生存任务不能当作本项目 Y24 数值基准。
- **验收问题**：先看同输入的 M2−M1，再看是否增加过程预测任务有效；不要用“加了更多过程信息”的模型对“没有这些信息”的模型来证明优化方法更好。
- **理论边界**：§5.3 明示无穷小扰动、梯度 iid、平均梯度为零等条件；不能当作任意离散删记录或大型跨院变化的稳健性保证。2025 长文与 2022 DeepJoint workshop 版本分开引用。

### L03：最直接约束“移植”新颖性与可实现性的已发表工作

- 链接：[正式论文页](https://proceedings.mlr.press/v206/zhou23b.html) · [PDF](https://proceedings.mlr.press/v206/zhou23b/zhou23b.pdf)。作者 Helen Zhou、Sivaraman Balakrishnan、Zachary C. Lipton。
- 固定干净 `(X,Y)`，只改变缺失机制。主理论聚焦没有缺失指示的 UCAR：各维恒定、独立的漏报机制；已知/未知绝对漏报率、相对漏报率识别与目标线性预测器调整均有明确区分。
- **已有算法**：§6 在目标比源更稀疏时，估计相对缺失率，再给源记录额外掩码以产生目标样本；这与本项目最简单的比率 thinning 直接相关。
- **周二验收**：明确策略估计的可见历史、支持分母及目标更密的不可生成部分。顺序策略必须区分源历史与删后历史，不能用未观测的当前真值估计可部署策略。
- **周三验收**：mask 为源 mask 子集、保留数值及时间戳不变；UCAR、足够支持且参数已知/可估时，模拟算法能重现目标记录分布和风险；再加入历史依赖、隐变量触发加测、成组开单、源不够密等场景，分别报告失配而不是宣称理论仍成立。
- **范围纠正**：其 Proposition 1 在有缺失指示时约为 covariate shift，还要求 MCAR 或仅依赖完全观测变量；不是“只要加 missing indicator，任意临床 MNAR 就消失”。

### L04：记录过程有信号的充分背景，不是纯偏差识别证据

- 链接：[全文](https://pmc.ncbi.nlm.nih.gov/articles/PMC5925441/) · [DOI](https://doi.org/10.1136/bmj.k1479) · [勘误](https://www.bmj.com/content/363/bmj.k4416)。作者 Denis Agniel、Isaac S. Kohane、Griffin M. Weber。
- 两家波士顿医院 669,452 人、272 类检验。三个分母不能混写：233/272 是“是否开立与生存相关”；118/174 是“过程变量比生理数值预测更好”；76/210 是“检验间隔是最强的单变量”。
- 2018 勘误（DOI 10.1136/bmj.k4416）仅指出图 3b 纵轴范围应为 0.6–1.0；本轮核到的勘误未改上述汇总数字。
- **周一/三验收**：测量率、钟点、星期、距上次测量、变量共测和零测量窗口分别有清晰分母；既比较边际率，也比较间隔、成组与时序结构。
- **验收问题**：这些特征能区分医院，是否仍可能包含患者严重度、护理地点、昼夜生理变化？论文支持“过程信号有预测信息”，不支持“这些信号全是应删除的噪声”或因果归因。

### L05：有开源实现的强表格对照，不能只打败弱神经骨干

- 链接：[v2 全文](https://arxiv.org/html/2507.21783v2) · [anchorboosting](https://github.com/mlondschien/anchorboosting) · [协调管线](https://github.com/ratschlab/icarefm)。作者 Malte Londschien、Manuel Burger、Gunnar Rätsch、Peter Bühlmann。仅核验论文内所列代码链接，未克隆或运行。
- 9 个 ICU 数据库约 40 万患者。线性 anchor regression 之外提出基于 LightGBM 的 anchor boosting，分类使用 probit link 和 score residual 惩罚。DG 与“有目标标签的 refit”分开；后者不是无标签适应基线。
- **可借鉴**：患者级 85/15 切分、留一环境选择、正式 OOD 目标与开发目标分离；分类用负对数似然选超参。本文也发现环境难度、噪声和普通正则化会影响跨域比较。
- **周四/周日验收**：下周 M0/M1/M2 先使用既有 LR/LightGBM；登记 anchor 对照所需输入、域与超参。后续 neural M2 的收益必须同时与强手工树模型比较。
- **周六验收问题**：只用 tune 医院选参数后，最差医院/平均医院结果是否同向？是否因某些医院本来更难而把绝对误差当“偏移大小”？
- **不可沿用的保证**：作者明示非线性 anchor boosting 没有线性方法同样的完整鲁棒性保证；“违反外生性仍有经验收益”不是证明任何医院策略估计都因果有效。

### L06：无标签环境上下文的通用先行方法

- 链接：[NeurIPS 正式页面](https://proceedings.neurips.cc/paper_files/paper/2021/hash/c705112d1ec18b97acac7e2d63973424-Abstract.html) · [实际阅读的 arXiv v4 PDF](https://arxiv.org/pdf/2007.02931v4) · [代码](https://github.com/henrikmarklund/arm)。作者 Marvin Zhang、Henrik Marklund、Nikita Dhawan、Abhishek Gupta、Sergey Levine、Chelsea Finn。
- ARM-CML 在同域训练批次中为每个输入计算 context，再取平均供预测器条件化；训练时直接优化适应后的表现，部署只需无标签批次。原实验为图像分类；Table 1 有部分数据集不如其他 ARM 变体，附录还讨论在 DomainBed/WILDS 部分任务上无收益。
- **M4 设计约束**：同医院无标签支持患者与评价患者分开；若未来使用转导式同批查询上下文，必须单列该协议。医院 descriptor 应有支持患者数、时间范围、稳定性和缺失维度标记。
- **验收问题**：支持量从少到多是否改善稳定性？打乱 context、只给病例构成摘要、只给测量过程摘要的结果如何？患者严重度与 prevalence 变化能否让所谓“策略 descriptor”改变？
- 该文支持“无标签条件化值得测试”，不能证明医院上下文是纯策略，更没有给本项目的医疗收益保证。下周预留接口和设计，不把 M4 加入 M2 核心对比。

### L07：不变性必须先写出哪些变化与结局无关

- 链接：[NeurIPS 正式页面](https://proceedings.neurips.cc/paper_files/paper/2021/hash/8710ef761bbb29a6f9d12e4ef8e4379c-Abstract.html) · [实际阅读的 arXiv v3 全文](https://arxiv.org/html/2106.00545v3)。作者 Victor Veitch、Alexander D’Amour、Steve Yadlowsky、Jacob Eisenstein。正式会议标题与 arXiv v3 标题不同，版本信息见上表。
- Definition 1.1 在改变无关因素的反事实输入间要求预测相同；§3.2 的独立性签名依赖因果方向与混杂/选择结构，而且是必要而不充分条件。§4 鲁棒性结论限制了因果兼容的目标分布并保持 `P(Y)`。
- **M3 设计约束**：把“改变记录编码但保留同等充分信息”与“删除预测所需生理信息”分开；后者最优概率可合理回缩。先在可计算 Bayes 真值的模拟上测强制一致性是否损害 Brier/log loss。
- **验收问题**：`λ=0`、小 λ、强 λ 的概率评分与跨视图变化是否存在权衡？退化到常数风险的模型也很一致，是否被原始概率评分识别？
- 不将对称 KL 视为该文已证明有效的临床方法；不将医院分类接近随机当作反事实不变或生理解耦的证明。下周只输出可允许的一致性场景和候选损失，不进入主训练。

### L08：把预测目标、损失和评价对象写成同一件事

- 链接：[正式 DOI](https://doi.org/10.1198/016214506000001437) · [实际阅读的 2004 技术报告](https://stat.uw.edu/sites/default/files/files/reports/2004/tr463.pdf)。作者 Tilmann Gneiting、Adrian E. Raftery。
- 二元风险以未做标签依赖加权的 BCE/log loss 或 Brier 为主；多维连续未来轨迹可用 energy score。负向损失为 `E||X-y||^α − 0.5 E||X-X′||^α`，`0<α<2` 且相应矩有限；报告所用正负方向与 Monte Carlo 估计方式。
- 对 Bernoulli 随机变量、α=1 的 energy loss 正好等于二元 Brier `(p-y)^2`；不能把给 Y24 换“能量分”写成新方法。连续轨迹分布预测与二元结局预测是不同的估计对象。
- **周四/五验收**：所有臂共享主损失、原始概率输出与同一预算；不以 class weight/focal loss 后的数值直接解释为真实风险。混合策略视图上适当不自动意味着原医院分布或新医院分布都校准。
- **周六验收**：raw ΔBrier、Δlog loss 与同患者配对区间为主，同时报告原始指标；医院间技巧分若归一化，必须明示参考 prevalence 和分母，不能用归一化比率替代主结论。

## 周日写作门槛

| 得到的证据 | 可以写 | 不能写 |
|---|---|---|
| M2 比总量和变量×时段匹配 M1 更好，区间有解释力 | 结构化时序删观测在本次开发协议下提供额外收益 | 已解决医院偏差、已适用于任意真实策略变化 |
| M2 与 M1 接近且区间窄 | 低成本随机删已经解释主要增强收益，应收窄方法主张 | 换复杂骨干或堆 M3/M4 就等于已找到新方法 |
| 区间宽或事件不足 | 本轮未判定，说明需要哪些医院/患者与计算预算 | 失败已证明无效；或方向性均值已证明有效 |
| 原始跨院性能差与模拟删记录效应不同 | 两种估计对象不同，分别报告 | PEF 是因果归因比例或任何方法的收益上限 |
| 医院探针难以分类 | 该探针未检测到医院信息 | 表示只剩生理信息、实现因果解耦 |

公开全文的核验足以改变下周的优先级：先修 oracle 与支持问题，再做强随机删对照和 M2；M3/M4/RL 不应掩盖 M2 是否有独立贡献这一判断。
