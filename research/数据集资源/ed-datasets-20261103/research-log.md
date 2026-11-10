# 检索日志

**日期：** 2026-11-03

## 检索式（WebSearch）

1. `public emergency department dataset timestamped vital signs PhysioNet credentialed access ED visits`（extended）→ MIMIC-IV-ED、MC-MED、MIMIC-IV-Ext-MDS-ED、MIETIC。
2. `Scientific Data emergency department dataset release triage vital signs outcomes open access 2023 2024 2025`（extended）→ 只有 MC-MED（2025）和 Xie 等 2022；**未找到**其他急诊数据描述论文。
3. `NHAMCS emergency department public use file variables triage vital signs single visit`（standard）→ NBER/CDC 文档（S127）。
4. `Hong Haimovich Taylor 2018 predicting hospital admission emergency department triage dataset publicly available github`（standard）→ S125、S126。
5. `open emergency department dataset Korea OR Taiwan OR China OR Europe vital signs time series public release machine learning`（extended）→ **未找到**；返回的 VitalDB 是手术数据。
6. `MIMIC-IV-Ext-MDS-ED multimodal decision support emergency department benchmark diagnoses deterioration ECG Alcaraz`（standard）→ PhysioNet 项目页地址与 arXiv 2407.17856（S124）。

## 页面读取（WebFetch）

- `physionet.org/content/?topic=emergency`：列出 10 个项目（S123）。
- `physionet.org/content/mc-med/1.0.1/`：版本说明、采样、许可（S122）。
- `github.com/yaleemmlc/admissionprediction`：数据文件、规模、许可（S125）。
- `physionet.org/content/mimic-iv-ext-mds-ed/1.0.0/` 与不带版本号的地址都返回 404；正确地址是 `physionet.org/content/multimodal-emergency-benchmark/`（检索得到，未打开）。
- Nature 上的 MC-MED 数据论文跳转登录，未读。

## 没做的

- 中文渠道未查。
- MDS-ED 只看到检索摘要，未读项目页与论文正文。
