# 来源与核验记录

检索日期：2026-10-07。用途：为本地／服务器既有成果选择年底投稿方向。本文献检索是定向研究与竞争审查，不是达到 PRISMA 标准的系统综述；没有证据证明检索穷尽所有论文。

本地与服务器引用索引见 [report.md](report.md)。只使用聚合文档、代码和数据字典；未向公共检索服务提交患者数据。

**最直接的竞争与方法依据**

| 编号 | 来源 | 本次核验层级 | 关键用途 |
|---|---|---|---|
| R1 | [Reinforcement Learning over Predictive Distributions for LLM Regression](https://arxiv.org/abs/2605.20740)，DAR；[v2 全文](https://arxiv.org/html/2605.20740v2) | 原站元数据＋全文 §2、附录 A/C/F/I；首次 2026-05-20，v2 2026-10-06 | CRPS＋留一贡献、点奖励方差收缩、有限 K 偏差均已有先例；原文聚焦标量、非时间回归 |
| R2 | [Uncalibrated Reasoning: GRPO Induces Overconfidence for Stochastic Outcomes](https://arxiv.org/abs/2508.11800) | 原站元数据＋全文理论／实验；首次 2025-08-15 | 标准差归一化、随机事件概率过度自信；需区分事件概率报告与生理值采样分布 |
| R3 | [Ground-Truth Neighborhood Regularization for Reinforcement Learning Post-Training of Time Series Foundation Models](https://arxiv.org/abs/2608.08010)，GTN-R | 原站元数据＋全文机制／实验；首次 2026-08-08 | TSFM suboptimal collapse 和邻域正则；与预测区间和真实未来不确定性失真有所区别 |
| R4 | [Strictly Proper Scoring Rules, Prediction, and Estimation](https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jasa.pdf)，Gneiting & Raftery，JASA 2007；[DOI](https://doi.org/10.1198/016214506000001437) | 作者站原文 PDF／全文文本；重点第 1、4–6 节 | CRPS、能量分、适当性与覆盖／sharpness 的理论依据 |
| R5 | [Fair scores for ensemble forecasts](https://doi.org/10.1002/qj.2270)，Ferro | Crossref 元数据；出版社全文页 403，未在本次读到全文 | 有限集合公平评分为既有方法；不据本次检索扩展其具体定理条件 |
| R6 | [Back to Basics: Revisiting REINFORCE Style Optimization for Learning from Human Feedback in LLMs](https://arxiv.org/abs/2402.14740)，2024-02-22 | 原站摘要／元数据 | REINFORCE、RLOO 的既有工作背景；本次不据摘要声称具体医疗结果 |
| R7 | [Rewarding the Unlikely: Lifting GRPO Beyond Distribution Sharpening](https://arxiv.org/abs/2506.02355)，2025-06-03 | 原站摘要及全文 | 形式证明中的 rank bias；与概率校准相关但任务不同 |
| R8 | [Verifiable Rewards for Calibrated Probabilistic Forecasting](https://arxiv.org/abs/2607.00164)，2026-06-30 | 原站摘要；另读原站全文主要任务／方法 | 概率报告的 RLVR 不等于生理轨迹采样；proper reward 不自动保证实际优化校准 |
| R9 | [Multivariate Quantile Function Forecaster](https://arxiv.org/abs/2202.11316)，2022-02-23 | 原站摘要／元数据 | 多步预测用 energy score 已有先例；直接训练基线的重要性 |
| R10 | [Diffusion Fine-tuning with Rewarded Moment Matching Distillation](https://arxiv.org/abs/2606.30414)，2026-06-29 | 原站摘要／元数据 | GenCast 的 CRPS 后训练／蒸馏与校准，属于相关科学预测先例 |
| R11 | [Proper Scoring Rule-based Diffusion for Probabilistic Weather Forecasting](https://arxiv.org/abs/2609.38632)，2026-09-29 | 原站摘要／元数据 | 最新 proper-score 科学时序训练与微调竞争；未复核其全文结果 |
| R12 | [TRIPOD+AI statement](https://www.bmj.com/content/385/bmj-2023-078378)，BMJ 2024 | 期刊原文网页 | 预测模型透明报告、校准及评价资料与训练资料区分；按本文任务适用范围使用 |
| R13 | [PROBAST+AI](https://www.bmj.com/content/388/bmj-2024-082505)，BMJ 2025 | 期刊原文网页 | 参与者、预测变量、结局、分析四域的偏倚审查 |

**进一步核验的相关工作**

- [TimeRFT: Stimulating Generalizable Time Series Forecasting for TSFMs via Reinforcement Finetuning](https://arxiv.org/abs/2605.00015)：本次摘要／元数据；原站 API 的 published 为 2026-04-18，不根据编号自行推定日期。重点是时间分步奖励及适应，不据摘要断言它已解决医疗概率校准。
- [PostTime](https://arxiv.org/abs/2605.29401)、[REATS](https://arxiv.org/abs/2608.10149)：本次核验标题与摘要；属于本地已有调研的预测后训练／奖励设计路线，不是 CRPS＋留一贡献最直接的先例。
- [Post-Training in Time Series Foundation Models: A Unifying Framework](https://arxiv.org/abs/2607.20002)：本次原站摘要；用于术语与研究空间定位，非原创实验证据。
- [Ensemble-size-dependence of deep-learning post-processing methods that minimize an (un)fair score: motivating examples and a proof-of-concept solution](https://arxiv.org/abs/2602.15830)：本次摘要；提醒公平评分的条件独立成员假设和 K 敏感性。
- [Decision-Aware Training for Sample-Based Generative Models](https://arxiv.org/abs/2607.01171)：本次摘要；energy score 与决策成本结合已有先例，不能简单把临床成本加权当原创。

arXiv 原站展示不等于同行评议通过。本报告不把上述预印本自动称为已在特定会议录用，也未自行复现其公开性能数字。

**数据与期刊官方页面**

| 编号 | 页面 | 核实结果与限制 |
|---|---|---|
| D1 | [MC-MED v1.0.0](https://physionet.org/content/mc-med/1.0.0/) | 原站说明为 Stanford ED 2020–2022、118,385 次成人就诊，包含连续体征与临床资料；该页提醒有更新版本。这里引用的是服务器已有版本的说明，未下载患者数据；这些总规模不是可直接用于特定预测任务的样本数 |
| J1 | [BMC Medical Informatics and Decision Making：Aims and scope](https://link.springer.com/journal/12911/aims-and-scope)；[期刊首页](https://link.springer.com/journal/12911) | 原站可访问。范围含医疗信息技术／机器学习评价；强调科学有效性；首页列出 Science Citation Index Expanded。未独立登录 Clarivate 主目录；投稿时仍需核单位目录与实时状态 |
| J2 | [PLOS ONE：Criteria for Publication](https://journals.plos.org/plosone/s/criteria-for-publication) | 原站可访问。明确考虑阴性／无显著差异结果，要求重复研究有充分理由；并非豁免研究贡献与技术质量 |
| J3 | [Computer Methods and Programs in Biomedicine：范围](https://www.sciencedirect.com/journal/computer-methods-and-programs-in-biomedicine/about/aims-and-scope) | 官方页访问 403；仅列为后续评估候选，未借该次访问声称已核验最新范围／时长／费用 |
| J4 | [Journal of Biomedical Informatics：范围](https://www.sciencedirect.com/journal/journal-of-biomedical-informatics/about/aims-and-scope) | 官方页访问 403；同上 |

**检索方法及边界**

使用 arXiv 官方 API 定向检索与原站全文，辅以作者原文 PDF、BMJ、PhysioNet、Crossref 与期刊官网。Google 文本检索返回受限页面，未把空白搜索当作“没有相关工作”。代表检索式包括：

```
"time series" AND ("reinforcement learning" OR "post-training")
AND (probabilistic OR calibration OR distribution)

("energy score" OR "CRPS")
AND ("policy gradient" OR "reinforcement learning" OR "fine-tuning")

"GRPO" AND ("proper scoring" OR "leave-one-out" OR "bias")

"clinical" AND "time series"
AND ("foundation models" OR "probabilistic forecasting")
```

结合本地参考文献进行题名／标识符定向核查。搜索会混入缩写同名和任务不同的条目，报告仅保留实际相关来源；未以检索结果总数当作文献覆盖率。

中间公共检索快照保存在本地忽略目录 `tmp/yearend_research_20261007/`，不包含患者信息；长期可追溯的主要来源及限制已记录在本文件，不依赖临时快照才能阅读结论。
