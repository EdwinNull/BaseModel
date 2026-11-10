# 检索与核对记录

## 2026-11-08（服务器时钟）

### 范围

研究者问：有没有论文针对"常数输入退化"？问题拆成四个子问题，见 `brief.md`。检索用 WebSearch（标准模式，少数用扩展模式）和 WebFetch。检索词只含通用学术关键词，没有发送任何数据或数字。

这是定向检索，不是系统综述：没有系统检索 Google Scholar、Semantic Scholar 或会议目录。

### 检索方向与关键词（摘要）

1. **直接问题**：constant / zero-variance / flat input、short context、single observation 与 time series foundation model 的组合；instance normalization 与 degenerate、zero variance。没有找到直接研究的论文。
2. **归一化与统计量**：over-stationarization、RevIN、"normalization statistics as tokens / covariates"、scale embedding。找到 S01–S05、S07、S08。
3. **平直预测**：flat forecasts、forecast collapse、mean reversion foundation model。找到 S06，并引用项目文献库中的 S19。
4. **临床稀疏与测量过程**：informative missingness、irregular clinical time series foundation model、ICU foundation model zero-shot、repeated vital signs emergency department。找到 S11、S13、S15–S17，并引用项目文献库中的 S09、S10、S14、S18。

### 原文核对

| 来源 | 读取方式 | 读到的范围 |
|---|---|---|
| S03 Lag-Llama | WebFetch 返回二进制 PDF，改用 Read 读保存的 PDF 第 4–5 页 | §4.4，Eq. 3–4 |
| S05 UniTok | arXiv HTML | §3、§3.2，Eq. 1 |
| S11 ICareFM | medRxiv 网页返回 403，改读保存的 PDF 第 1–2 页；11-08 用 pdftotext 复核摘要原句 | 摘要、引言开头 |
| S17 Quinten 等 | 期刊网页 | 设计、主要结果 |
| 其余 | arXiv 摘要页或检索摘要 | 只有摘要 |

本项目文献库已核对过的条目直接引用：
- S09、S10、S19：`research/时序基础模型与子集/tsfm-survey-20261105/REPORT.md`、`research/时序基础模型与子集/tsfm-survey-20261105/csv/失效模式证据.csv`。
- S14、S18：`research/观测过程与研究设计/measurement-process-next-week-20261031/literature_audit.md` 的 L04、L03。

### 写报告时的复核（11-08）

报告初稿写完后，逐条回到检索与读取结果核对细节，改了以下几处：
- S01 的会议出处只来自检索结果里的 NeurIPS 海报页链接，那一页没有打开。原写"由海报页确认"，改为如实说明。
- S11 初稿写"ICU / 急诊住院"，原文摘要只写 patient stays。改为"住院（patient stays）"，并按原句补上数据来自美国、多个欧洲国家和中国。
- S09 作者只核对到第一作者 Gu，删掉了初稿里的第二作者；补上项目文献库的总体结论：零样本多数不如从头训练。
- S17 补上呼吸频率的 AUC 增量小、缺失多，以及作者"证据主要在 MAP"的结论。
- 加入 S18（项目文献库 L03）：说明把测量过程作为输入会引入院间缺失偏移。

### 没有采用的条目

| 条目 | 原因 |
|---|---|
| Tiny-TSM 用滚动均值、标准差作为输入 | 只在检索摘要里出现；S20 摘要只写了"因果输入归一化" |
| Mantis 保留未归一化的原始分支 | 摘要页没写 |
| Foundation Inference Models（arXiv 2402.07594）说近常数函数的归一化参数被噪声主导 | 摘要页没写 |
| OpenReview kQDzqIkXLO | 页面需要浏览器验证，打不开 |
| SeesawNet、CANet、IN-Flow、CDFM 等归一化变体 | 只在检索结果里出现，没读；都是训练期改进，与零样本常数输入的关系不明 |
| 可穿戴 HRV 预印本 arXiv 2607.20027 | 只有检索摘要 |

### 停止规则

四个子问题都有了答案，回答也一致：没有直接研究这个问题的论文，相关工作分三条线。再扩大检索范围不会改变给研究者的结论，所以停止。如果要写成论文的相关工作，需要再做一轮系统检索，并读 S06、S11、S12 的方法部分全文。
