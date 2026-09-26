# 检索日志

**日期：** 2026-09-25

## 本地基础

- 通读 `README.md`、`paper/首次调研/`（阅读索引、数据集对比、模型对比、身份核对）与 `research/medical-ts-posttrain-rl-20260923/report.md`。确认 S001–S029 的覆盖范围：通用时序 RL 奖励、临床离线 RL 奖惩、医学时序基础模型的非 RL 后训练。
- 确认缺口：医学时序 **LLM/MLLM** 的 RL 后训练（ECG、EHR、可穿戴）、预测侧/预警侧 RL、经典治疗 RL 的奖励常数、各论文的数据集与基线清单。

## 检索式（WebSearch，2026-09-25）

1. `TimeMaster reinforcement learning time-series multimodal LLM GRPO TimerBed ECG` → TimeMaster、SenTSR-Bench、COUNTS。
2. `ECG reasoning large language model reinforcement learning GRPO reward` / `ECG-R1 ... verifiable reward PTB-XL MIMIC-IV-ECG` → ECG-R1、MedTVT-R1、EHRMind、GEM。
3. `OpenTSLM time series language models medical ...` → OpenTSLM（仅 SFT，作为无 RL 对照）。
4. `EHR-R1 ...`、`"Training LLMs for EHR-Based Reasoning Tasks via RL"` → EHR-R1、EHRMind、EAG-RL。
5. `wearable sensor time series LLM RL GRPO sleep staging`、`EEG LLM RL GRPO`、`CGM LLM RL GRPO` → HEARTS、SleepFM、SensorLM 等；**未找到**全文可核的 EEG、睡眠或血糖 LLM-RL 后训练论文。
6. `LLM sepsis ICU treatment RL offline MIMIC LLM policy` → MORE-CLEAR、SepsisAgent。
7. `LLM GRPO clinical risk prediction MIMIC-IV mortality ...` → TRIAGE、LLM4EHR、RealICU（均无 RL 训练）。
8. `RL early warning deterioration reward timeliness`、`EARLIEST ...`、`Stop&Hop ...`、`PhysioNet 2019 utility` → EARLIEST、Stop&Hop、PhysioNet 2019 效用函数。
9. `ICU-Sepsis benchmark MDP`、`DTR-Bench ...` → ICU-Sepsis、DTR-Bench、MedGym、LLM 作为 DTR 规划器。
10. 经典治疗奖励：Raghu 2017、Nemati 2016、Emerson 2023、Fox 2020、DeepVent、Prasad 2017、Cheng 2019、COVID-19 氧疗 RL、AI Clinician。
11. `influenza OR pneumonia OR COVID-19 deterioration prediction LLM fine-tuning RL` → **未找到**流感或肺炎转重的 LLM-RL 后训练论文；找到 COVID-19 氧疗离线 RL（治疗侧）。

## 全文核验

- arXiv HTML（WebFetch 定向抽取公式、数据、基线、算力）：2506.13705、2602.04279、2506.18512、2510.25628、2510.02410、2505.24105、2508.13579、2605.14723、2506.00711（补读 S021）、2601.16516、2306.05109、2406.05646、2405.18610、2606.01028、2508.04755。
- arXiv PDF（curl 下载 + `pdftotext` 检索原文）：1705.08422、1711.09602、2204.03376、2009.09051、2210.02552、1704.06300、1808.04679、2208.09795、2605.21295、2105.08923、1907.09475（Nemati 公式的二手来源）。
- PMC 全文：MORE-CLEAR（PMC13269913）。
- 官方页面与代码：PhysioNet/CinC 2019 数据页；`physionetchallenges/evaluation-2019/evaluate_sepsis_score.py`（效用函数常数与分段斜率）。
- 元数据：arXiv API `id_list` 一次核对 32 篇的题名、作者、日期与会议注记；Europe PMC API 核对 AI Clinician 摘要。

## 纠错记录

- 一处搜索摘要把 S020 的作者写成其他人；arXiv 页面核对后仍为 Xiao, Zhang, Singh, Naumann, Poon, Gao, Liu，维持 09-23 报告的著录。
- Raghu 等 2017 有两个版本：MLHC 版（1705.08422）只有终末 ±15；SOFA/乳酸中间奖励出自 NIPS 2017 研讨会扩展版（1711.09602）。两者分别著录为 S052、S051。
- MedGym 的 arXiv v3 题名改为 "A Unified Benchmark for Dynamic Medical Treatment Reinforcement Learning"；本轮按 v3 著录，正文沿用 MedGym 简称。

## 排除

- HealthTimeLLM-R1（Springer 会议章节）：出版社页面需登录，只见检索摘要，不纳入。
- 纯医学文本 RL（心脏 QA 的 rubric 奖励 2606.05174、医学 QA 测试时 RL 2609.16660）、医学视频 GRPO（2512.06581）：不是时序。
- AI Clinician 队列规模：摘要未给，本轮未打开正文，不写具体人数。
- OhioT1DM、VentAI 等常见名字：本轮未打开原文，不写入表格。

## 停搜

三条线（医学时序 LLM-RL、预测/预警 RL、治疗离线 RL）各自再检索两轮后，新结果只重复已有奖励族（结局可验证、过程证据、格式、时效、生理/结局、成本约束），不再出现新类别；流感/老年转重的 RL 后训练仍为阴性结果。
