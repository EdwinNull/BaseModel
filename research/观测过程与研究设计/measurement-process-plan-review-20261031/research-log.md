# 检索记录（2026-10-31）

对象：`plans/观测过程建模/医学时序预测_生理状态与记录过程分解_初步计划_20261031.md` 的可行性分析。报告见 `plans/观测过程建模/医学时序预测_生理状态与记录过程分解_可行性分析_20261031.md`。

## 仓库内读过的材料（只读聚合量，未打开 data/）

- CLAUDE.md、README.md、docs/claude_project/01、02
- result/阶段汇总与交接/实验进度.md、A4桥接_只用编码队列重跑_结果_20261030.md、前瞻样本量情景_20261031.md、mp_benchmark_v1_三模型结果报告_wangyiming_20261021.md、week02实验结果深度解析_演示_20261007.html（抽文字）
- docs/数据标准/质量验收/质量成绩单_std_v3_20261031_5.md、数据集说明书_Healthsheet_v0.1_20261031.md
- plans/观测过程建模/六模型观测删减敏感性_任务说明.md（六模型任务说明）、零样本决策读出J线_参照MedJev_实验计划_20261029.md（前 60 行）
- research/数据集资源/influenza-datasets-20261030/report.md（前 120 行）
- PPT/成品/方法专题/观测过程预测.pptx（抽文字，09-14 汇报）
- 引子论文/ 5 篇 arXiv 的首页（LangTime、Time-R1 慢思考、VTA、TimeSRL、REATS；都是 LLM / RL 时序预测，与本计划关系弱）

## 网络检索（WebSearch / WebFetch）

| 查询或页面 | 结果 |
|---|---|
| Yamamoto 2026 medRxiv observation-process features | 找到并读摘要（S01） |
| Shi, Hubbard, Fong, Pirracchio 2025 BMC MIDM | 找到，读文章页（S02） |
| Sisk / Sperrin / Peek missing indicators | S07–S09；“Missing data should be handled differently for prediction…”（Sperrin 2020）未能检索确认，报告未引用 |
| clinical presence shift / DeepJoint | S10、S11 |
| Beaulieu-Jones 2021、Kamran 2024 NEJM AI | S05、S06 |
| Zhou 2023 missingness shift、Subbaswamy 2019、Nestor 2019 | S12–S14 |
| measurement policy shift clinical time series 2025–2026 | Elwes IJCAI 2026 摘要（泛化 benchmark，未涉及测量策略，未引用）；S15（Londschien 2025/2026）；S17（Vallée 2026） |
| Rockenschaub / YAIB | S16（arXiv 2303.15354 的期刊版本未核，未引用） |
| Debray 2015、van Klaveren 2016、Collins 2016、Williamson 2023、Seymour 2012 | S18–S22 |
| MC-MED、Zigong、ICU 数据库概况 | S24–S26 |
| Haut & Pronovost 2011 JAMA surveillance bias | 只找到二手报道，未引用 |
| 计划 §11 九个 DOI | Crossref 逐条核对（S28），结果见报告附录 B |

## 玩具模拟

`toy/ponly_leak_sim.py`、`ponly_leak_sim2.py`、`ponly_leak_sim3.py`，只用合成数据；输出 `toy/output.txt`。

## v1.1 追加（研究者答复后）

研究者答复：CCF-A；重点仍是后训练（SFT、一致性微调都算，RL 可选）；“投出还是录用”由导师定；MC-MED 合写作补充；OPL-MT-MNAR 作对照基线；9 月 MC-MED benchmark 可并入（材料在服务器）；GAM / GD 伦理已批、覆盖发表。

| 查询或页面 | 结果 |
|---|---|
| KDD / NeurIPS / ICML / IJCAI 2027 截稿 | S36（第三方汇总，估计日期） |
| test-time adaptation / fine-tuning robust to missingness shift, clinical TSFM | 无直接对应工作；ICTP（CIKM'25）、TabPFN-TS 插补研究与本题无关，未引用 |
| missingness augmentation / domain generalization EHR 2025 | S31、S32；JMIR 2025 缺失方法比较未细读，未引用 |
| RL post-training clinical robustness | S29（最直接竞争者）、S30；CalTwin（alphaxiv 2607.26752）未读，未引用 |
| ARM、counterfactual invariance | S33、S34 |

玩具模拟追加 `toy/ponly_leak_sim4.py`（后训练式增强的概念验证）与 `toy/ponly_leak_sim5.py`（另一种策略结构）。
