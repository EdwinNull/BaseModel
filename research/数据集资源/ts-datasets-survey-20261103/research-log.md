# 检索日志

**日期：** 2026-11-03

## 本地基础

- 读 `research/观测过程与研究设计/measurement-process-next-week-20261031/report.md` §2–§3、`colleague_design_review.md`：MC-MED 上已跑的管线名单与合作摘要数字。
- 读服务器 `basemodel/experiments/mp_benchmark_v1/common/benchmark.py`：MC-MED `decomp_60` 的六项体征为 HR、RR、SpO2、SBP、DBP、MAP，输入 0–15 min。

## 原文获取

arXiv 与 PMLR 的 PDF 用 WebFetch 下载后，放进 scratchpad 单独目录，用 `pdftotext` 提取文字后用 grep 定位章节：

- 1606.01865v2（GRU-D）、1805.10572v1（BRITS）、2101.10318（mTAND）、2110.05357v2（Raindrop）、1909.12064v3（SeFT）、PMLR v235 zhang24bw（t-PatchGNN）、2311.04937v1（MC-BEC，NeurIPS 2023 D&B 版 PDF）。

HTML 版用 WebFetch 直接读（超过 10 万字符的只读了前 10 万）：

- 2303.12799v2（ViTST）、2505.22815v1（VIMTS）、2506.07584v7（MIRA）、2310.10688v4（TimesFM）、2604.21235v1（OPL-MT-MNAR）、PMC9610299（Xie 等 2022）。

## 检索式（WebSearch，standard）

1. `OPL MNAR irregular multivariate time series observation process learning clinical` → 2604.21235（S111）。
2. `VIMTS irregular medical time series vision adapter` → ICML 2025 VIMTS（S108）；顺带 ViTST。
3. `MIRA medical time series foundation model real-world health data arXiv 2025` → 2506.07584（S109）。
4. `"IMTS is Worth Time" Channel Patches Visual Masked Autoencoders arXiv` → 2505.22815。
5. `TimesFM 2.5 OR "TimesFM 3" google-research timesfm context length release` → 只查到 2.5（S115，第三方页面）；**未找到** "TimesFM 3.0"。
6. `t-PatchGNN irregular multivariate time series forecasting transformable patching ...` → PMLR 页面（S107）。
7. `Xie 2022 Benchmarking emergency department prediction models ... MIMIC-IV-ED Scientific Data` → S112。
8. `MC-MED multimodal clinical monitoring emergency department dataset Scientific Data 2025 Kansal benchmark tasks` → PhysioNet 页面、MC-BEC（S113、S114）。

## 没做的

- 未通读全文；只核对数据集、实验设置、子集相关段落。
- 未覆盖 ContiFormer、Warpformer 等。
- Nature 上的 MC-MED 数据论文跳转登录，未读全文（S116 基于检索摘要）。
