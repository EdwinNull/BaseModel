# 检索日志

**日期：** 2026-09-23

## 本地基础

- 阅读 `paper/首次调研/调研证据/report.md` 与身份核对。第一轮错配题名不进入本报告。
- 全文抽查引子论文：2503.08271v2、2506.10630v4、2511.08616v2、2605.21295v1、2608.10149v1。
- 复核 medR 清洗全文 `2602.03305.clean.txt` 的公式、筛选指标和附录超参。

## 主代理检索

1. arXiv：`ti:"time series" AND all:reinforcement AND all:reward`，2026-09-23，23 条。保留 TimeRFT、PostTime、TimeSRL、REATS、LangTime、Time-R1。
2. arXiv：`all:"medical time series" AND all:"foundation model"`，4 条。保留 MIRA、TSPFN、联邦微调、FORMED。
3. arXiv：`all:"offline reinforcement learning" AND all:reward AND (sepsis OR ICU OR clinical)`，14 条。保留 medR、通气、几何悲观、OGSRL、CORMPO、Luo 2024。
4. arXiv id_list 摘要批：2605.29401、2605.00015、2510.01116、2410.03794、2602.08655、2506.14375、2511.06111、2505.16242、2405.18556。
5. 下载并打开 PDF：2605.00015、2605.29401、2506.14375、2602.08655、2505.16242、2511.06111。2410.03794 仅用摘要。
6. 摘要页核验：2608.08010、2602.07830、2501.15942、2609.12277。ar5iv HTML 核验 2506.00711。
7. OpenAlex 匿名检索返回 429 或空结果，不作为新增来源。
8. 后续 arXiv API 返回 HTTP 429。停止继续分页，改用已打开全文和摘要页。

## 子代理

- 通用时序后训练代理完成，提供 GTN-R、VeriTime、TimeHF、QoQ-Med 等候选。主代理只保留已打开摘要页或 HTML 的条目。
- 医学时序基础模型代理完成。MOTOR、Delphi-2M、ETHOS、SurvivEHR、MedFound、病历轨迹强化学习采用其带来的标识，并抽查了其中四条的摘要页或既有全文。
- 临床奖励代理在初稿后返回。主代理用 PubMed `efetch` 复核 PMID 38526681、42471397、40098600，并从 `PubmedData/ArticleIdList` 取 DOI，避免参考文献 DOI 混入。三者支持治疗奖励终点不统一、离线评估敏感，没有提供流感预测奖励公式，故追加为 S027–S029。其余子代理条目未逐篇打开全文，不新增为公式来源。Track B 阴性结果与主检索一致：未找到把预测误差、校准或老年漏报写成强化学习奖励的 2023–2026 临床预测论文。
- 综述代理若在此后返回，只在出现新的奖励机制类别时追加，不覆盖已核验公式。

## 停搜

两轮定向检索之后，新结果重复六类预测奖励和三类临床奖惩，没有出现流感转重的强化学习后训练论文。arXiv 限流使继续分页的收益低于误引风险。未全文核验的候选明确标为摘要级或不写入公式。
