# 检索日志

**日期：** 2026-10-30

## 本地基础

- 读 `paper/首次调研/数据集/数据集对比.md`：前轮只覆盖 MIMIC-IV、eICU、HiRID、PTB-XL、FluSight/NHSN，没有流感专病个体数据。
- 读 `plans/阶段汇总与交接/基础模型实验执行计划_医院数据与公开数据_20260927.md` §2–§4：服务器已有 MIMIC-IV 3.1、eICU-CRD 2.0、MC-MED 1.0.0；流感识别口径（ICD-10 J09–J11 / ICD-9 487–488、检测阳性）；MIMIC-IV-ED 未下载（计划项 D1）。
- 读 `plans/数据工程与flucase/数据集验收与数据底座_执行计划_20261029.md`：医院侧问题（GAM 门急诊缺年龄、GD 43% 诊断流感无阳性检测），说明公开流感个体数据的需求仍在。

## 检索式（WebSearch，standard，2026-10-30）

1. `Global Influenza Hospital Surveillance Network GIHSN data access request individual patient data` → GIHSN 网络论文（S067）。
2. `Homekit2020 benchmark wearable influenza dataset Synapse access` → CHIL 2023 论文、GitHub（S068、S069）。
3. `Vivli baloxavir FLAGSTONE CAPSTONE-2 individual participant data request Roche Shionogi` → Vivli 请求 8896（S073）。
4. `YODA project pimodivir hospitalized influenza trial data available` → 只有试验本身，无 YODA 条目。
5. `FluSurv-NET individual-level data request restricted access CDC` → **未找到**外部申请个体数据的通道，只有 FluView 聚合。
6. `China Kadoorie Biobank data access influenza pneumonia hospitalisation ICD-10 endpoints` → CKB 肺炎住院研究、编码论文（S087）。
7. `GEO GSE111368 MOSAIC ...` → 确认 MOSAIC 论文与 GSE111368（S083）。
8. `MIMIC-IV influenza patients cohort ...`、`"MIMIC-IV" influenza ICU patients mortality nomogram ...`、`serum bicarbonate 30-day mortality critically ill influenza patients MIMIC-IV` → 276 例 ICU 流感（S085，索引页）。
9. `"eICU" influenza patients ICU mortality prediction cohort` → **未找到**用 eICU 做流感队列的研究。
10. `AccessClinicalData@NIAID influenza trial data hospitalized IVIG INSIGHT FLU` → FLU-IVIG 试验；门户本身 403。
11. `ISARIC IDDO data platform influenza severe acute respiratory infection data access request` → ISARIC 数据访问页（S082）。
12. `N3C enclave influenza patients cohort ...` → 全是 COVID，**未找到**流感队列。
13. `PhysioNet influenza dataset respiratory virus` + PhysioNet 站内搜索 → 无流感库（S097）。
14. `Dryad OR figshare OR "Mendeley Data" dataset hospitalized influenza patients ...` → **未找到**住院流感个体原始数据存档。
15. `All of Us Research Program data access international researchers ...` → S091。
16. `UK Biobank influenza hospitalisation ... J09 J10 J11 older adults` → 只找到 HES/CPRD 研究（S095），UK Biobank 本身未核实。
17. `NHAMCS public use data file emergency department influenza ...` → S090。
18. `HCUP National Inpatient Sample influenza hospitalizations elderly ...` → S094。
19. `China Kadoorie Biobank data access policy ...` → S086。
20. `国家流感中心 流感监测周报 数据 下载`、`国家人口健康科学数据中心 流感 数据集` → 周报 PDF（S093）；人口健康数据中心**未找到**流感数据集条目。
21. `WHO FluNet FluID data download ...` → S092。
22. `Homekit2020 participants number influenza positive PCR ...` → 5,196 人（S070，摘要级）。
23. `INSIGHT network data sharing policy ... FLU 002 FLU 003` → 只有研究描述（FLU 002/003 共 1,365 例，2009 H1N1），**未找到**数据申请流程。
24. `ClinicalStudyDataRequest.com CSDR transition to Vivli GSK` → S081（二手，未核实）。
25. `FluSurv-NET older adults ... 2024-25 season` → MMWR 全文（S088）。
26. `ImmPort influenza natural infection hospitalized adults ...` → DR59 说明（S096）。

## 结构化查询

- ClinicalTrials.gov API v2 单条记录：NCT03684044、NCT02949011、NCT03376321、NCT03381196、NCT02287467、NCT01314911（取赞助方、入组数、年龄、IPD 共享声明）。
- ClinicalTrials.gov API v2 检索（S080）：流感 + 声明共享 IPD + 干预性 + 含老年 + 住院/重症/高危 + 已完成或终止 → 141 条，去掉疫苗后 12 条，其中住院流感治疗试验 5 条。

## 全文核验

- PMC 全文：GIHSN（PMC11906252，数据可用性声明）、MOSAIC（PMC5985949，严重度定义与采样时点）。
- CDC MMWR mm7434a1：老年分层 ICU / IMV / 死亡比例（表）。
- FLAGSTONE 方案（ClinicalTrials.gov `Prot_000.pdf`，CP40617 第 2 版，`pdftotext` 提取）：入组条件（NEWS2≥4、需氧或流感并发症、发病≤96 h）；6 级序数量表住院期间每天早上记录；体征（呼吸、脉搏、SpO2、血压、体温，吸氧者记流量/FiO2）Day 1–10 每天 4 次，之后住院者每天 1 次；次要终点含 IMV、ICU、"临床失败"（死亡/IMV/ICU）、Day 7 与 Day 28 死亡。
- 官方页面：ISARIC 数据访问页、YODA 站内搜索、Homekit2020 README、PhysioNet 站内搜索。

## 服务器实测（2026-10-30）

- 先读服务器 `W/CLAUDE.md` 和已有结果（数据对齐与质量报告的"公开数据统一状态"、B1v2、9-27 MIMIC-ED 流感 QC、9-28 eICU B5），只补缺的部分。
- 名称探查（字典级聚合）：`W/logs/2026-10-30/probe_flu_names_mcmed_eicu.txt`。
- 计数脚本 `W/basemodel/scripts/data_audit/count_public_flu_cohorts.py`（sha256 37897494…f936a），用时约 170 s；输出 `W/logs/2026-10-30/public_flu_cohort_counts.{json,log,md}`（json sha256 e79cd8b5…04d13）。没有写逐病人文件。
- 核对：9-27 的 MIMIC ICD 候选比本次少 133 次住院，原因是漏了 J09；MC-MED 没有缺年龄的就诊。

## 未能打开

- GEO（NCBI 浏览器验证页）、AccessClinicalData@NIAID（403）、CKB 政策页（403）、Vivli 请求页（404）、ouci 索引页（403）。相关条目在 sources.jsonl 标为 `search_snippet`。

## 本轮没查的

- 欧洲 ICU 库（SICdb、AmsterdamUMCdb）里的流感例数；日本 DPC/JMDC、韩国 HIRA/NHIS、台湾 NHIRD、香港 CDARS 等本国限定数据；OpenSAFELY；GISAID 病人状态字段；UK Biobank 申请细节。
- WebSearch 只返回美国索引，中文资源覆盖弱。
