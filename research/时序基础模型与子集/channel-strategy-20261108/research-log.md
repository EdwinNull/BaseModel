# 检索与核对记录

## 2026-11-08

### 范围

定向检索，不是系统综述。检索用 WebSearch（标准与扩展模式），核对用 WebFetch 读 arXiv 摘要页和会议页。检索词只用通用学术关键词，不发送任何数据。

### 检索方向

1. **CI 与 CD 的取舍**：channel independent vs dependent、capacity robustness trade-off。找到 C01。
2. **学习何时保持个性、何时融合**：adaptive channel fusion、channel clustering、channel mask、gated cross-variate、channel-aware adapter。找到 C02–C06、C10–C12。
3. **基础模型的多变量处理**：Moirai any-variate、Timer-XL multivariate、Chronos-2 group attention。找到 C07、C08；Timer-XL 已在本项目的模型调研中（`research/时序基础模型与子集/tsfm-survey-20261105/`）。
4. **临床不规则数据的通道策略**：channel independence clinical time series。找到 C13，以及 GRU-D、Raindrop 等已在本项目使用或调研过的方法。

### 核对

| 来源 | 读取方式 | 结果 |
|---|---|---|
| C01 | arXiv 摘要页 | 读到摘要。检索结果中有一句把 CI、CD 的容量与稳健性说反了，以摘要页原文为准：CD 容量高、不稳健 |
| C02、C03、C05 | arXiv 摘要页 | 读到摘要 |
| C04 | arXiv 摘要页 | 读到摘要。v4（2026-05-28）改了题目，列为 ICASSP 2026；初版是 NeurIPS 2024 研讨会论文。摘要写的是"相似度矩阵"，不是检索结果说的"相关矩阵" |
| C06 | ICML 2026 会议页 | 读到摘要。四个基础模型的名字和具体增益，页面上没有给出 |
| C07 | arXiv 摘要页 | 读到摘要；另外读了服务器上 Chronos-2 源码的 InstanceNorm、`predict`、`fit` |
| C08 | arXiv 摘要页 | any-variate attention 的细节摘要里没写，未核实 |
| C12 | AAAI 期刊页 | 页面被拦截，只有检索摘要 |
| C09–C11 | 只有检索摘要 | — |

### 研究者读过的那一篇

研究者说的那篇（学习什么时候保持各通道个性、什么时候融合）没能确定是哪一篇。最接近的候选：
- C06 ChaTSFM（门控修正）
- C03 C-LoRA（个性适配器 + 共享 CD）
- C02 CCM（按簇共享）
- C05 DUET（软聚类 + 掩码）
- C04 PCD（通道掩码）

可行性实验里的 gate 臂按"CI 输出 + 门控的 CD 修正"实现，门值按就诊、按通道学习。这一设计与 C06、C03 最接近。

### 停止规则

三个子问题都有了答案：CI / CD 的取舍有解释；能自己决定融合的方法有五类；基础模型的多变量接口有现成实现。可行性实验的结论不依赖再多找几篇方法论文，所以停止检索。
