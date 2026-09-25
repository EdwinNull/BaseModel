# 首次调研论文库

> 当前入口：请从 [合并阅读索引](阅读索引.md) 开始。精读文档已按 `类别/论文目录/阅读笔记.md` 组织在 [时序基础模型](时序基础模型/README.md)、[强化学习/后训练奖惩机制](强化学习_后训练奖惩机制/README.md) 和 [数据集](数据集/README.md) 中；证据与筛选记录在 [调研证据](调研证据/README.md)。
>
> 以下为迁移前论文库说明，包含已在 [历史身份核对](../首次调研阅读/00_论文身份核对.md) 中否定的题名和结论，只用于追溯，不能作为当前调研依据。

## 当前文件树

```text
paper/首次调研/
├── 阅读索引.md
├── 时序基础模型/
│   ├── README.md
│   └── 01_Chronos/ ... 08_TSPFN/
│       ├── 阅读笔记.md（或保留原编号的阅读笔记）
│       └── images/method-flow.svg
├── 强化学习_后训练奖惩机制/
│   ├── README.md
│   └── 01_Sepsis_Deep_RL/ ... 11_CPO/
│       ├── 阅读笔记.md（或保留原编号的阅读笔记）
│       └── images/method-flow.svg
├── 数据集/
│   ├── README.md
│   └── 01_FluSight/ ... 05_HiRID/
│       ├── 阅读笔记.md
│       └── images/flow.svg
├── 调研证据/
│   ├── report.md
│   ├── sources.jsonl
│   └── 证据/                 # 第二轮定向检索的全文
└── 原始PDF/                  # 首次调研下载的 24 份 PDF
    └── README.md
```

## 📚 概述

本目录包含了针对**老年人流感预测**项目进行的首次文献调研，收集了24篇最新的学术论文（2023-2026年），涵盖医学时序预测、基础模型和强化学习后训练方法。

## 📊 统计信息

- **论文总数**: 24篇
- **总大小**: 63MB
- **下载日期**: 2024年9月22日
- **来源**: arXiv.org

## 📁 文件结构

```
paper/首次调研/
├── README.md                              # 本文件
├── 论文清单.md                            # 详细的论文清单和分类
├── 01_Phi-3-Mini.pdf                     # 通用小型基础模型
├── 02_Qwen2.5.pdf
├── 03_Mistral-7B.pdf
├── 04_BioGPT.pdf                         # 医学专用基础模型
├── 05_ClinicalBERT.pdf
├── 06_MedAlpaca.pdf
├── 07_PMC-LLaMA.pdf
├── 08_Chronos.pdf                        # 时序专用模型 ⭐
├── 09_TimesFM.pdf
├── 10_Lag-Llama.pdf
├── 11_Moment.pdf
├── 12_RL-Clinical-Time-Series.pdf        # 强化学习方法 ⭐
├── 13_Reward-Shaping-Medical-TS.pdf      # 奖励设计 ⭐⭐⭐
├── 14_TD-Learning-Clinical.pdf
├── 15_RLHF-Medical-Prediction.pdf        # 对齐方法 ⭐
├── 16_Constitutional-AI-Medical.pdf
├── 17_DPO-Time-Series.pdf
├── 18_Counterfactual-Reward.pdf
├── 19_Epidemic-Forecasting-RL.pdf        # 流感预测 ⭐⭐⭐
├── 20_Few-Shot-RL-Clinical.pdf
├── 21_Safe-RL-Healthcare.pdf
├── 22_Curriculum-Learning-Medical.pdf
├── 23_Foundation-Models-Time-Series.pdf  # 综述 ⭐
└── 24_RL-Healthcare-Survey.pdf           # 综述 ⭐
```

## 🎯 核心论文推荐

### 必读Top 5（针对老年人流感预测项目）

1. **19_Epidemic-Forecasting-RL.pdf** (598K)
   - 流行病预测的强化学习方法
   - 包含老年人群特定奖励设计
   - arXiv: 2410.08756

2. **13_Reward-Shaping-Medical-TS.pdf** (18M)
   - 医学时序模型的多目标奖励框架
   - 平衡准确性、校准、安全性和公平性
   - arXiv: 2409.12847

3. **08_Chronos.pdf** (2.8M)
   - Amazon时序基础模型
   - 零样本预测能力，适合快速原型
   - arXiv: 2403.07815

4. **12_RL-Clinical-Time-Series.pdf** (439K)
   - 临床结果驱动的延迟奖励设计
   - PPO算法应用于脓毒症预测
   - arXiv: 2410.15523

5. **15_RLHF-Medical-Prediction.pdf** (536K)
   - 人类反馈对齐临床优先级
   - Bradley-Terry奖励模型
   - arXiv: 2405.18932

## 📖 阅读路线图

### 第一阶段：建立基础（3-5天）
```
综述论文
├── 23_Foundation-Models-Time-Series.pdf
└── 24_RL-Healthcare-Survey.pdf

核心技术
├── 08_Chronos.pdf (时序模型)
└── 05_ClinicalBERT.pdf (特征编码)
```

### 第二阶段：深入方法（1周）
```
强化学习框架
├── 12_RL-Clinical-Time-Series.pdf
├── 13_Reward-Shaping-Medical-TS.pdf ⭐⭐⭐
├── 19_Epidemic-Forecasting-RL.pdf ⭐⭐⭐
└── 15_RLHF-Medical-Prediction.pdf
```

### 第三阶段：优化技巧（3-5天）
```
对齐与安全
├── 17_DPO-Time-Series.pdf
├── 16_Constitutional-AI-Medical.pdf
└── 21_Safe-RL-Healthcare.pdf

训练策略
├── 20_Few-Shot-RL-Clinical.pdf
└── 22_Curriculum-Learning-Medical.pdf
```

## 🔬 论文分类

### 按类型分类

- **基础模型** (8篇): 01-07
- **时序模型** (4篇): 08-11
- **强化学习** (9篇): 12-20
- **训练技巧** (2篇): 21-22
- **综述论文** (2篇): 23-24

### 按应用场景分类

- **流感/传染病预测**: 19
- **ICU患者预测**: 12, 13, 14
- **时序预测通用**: 08, 09, 10, 11, 23
- **医学文本理解**: 04, 05, 06, 07
- **训练方法论**: 15, 16, 17, 20, 21, 22, 24

## 💡 关键技术点

### 1. 时序预测模型
- **Chronos** (Amazon): T5架构，零样本能力
- **TimesFM** (Google): 200M参数，轻量高效
- **Lag-Llama**: 概率预测，支持协变量
- **Moment**: 多任务统一框架

### 2. 奖励函数设计
```python
# 老年人流感预测奖励函数（论文19）
R_flu = w1·R_accuracy + w2·R_early + w3·R_peak + w4·R_public_health

老年人特定惩罚:
- 低估老年人风险: -2.0
- 延迟高危人群预警: -1.5 × weeks_delayed
- 疫苗接种时机错误: -0.8
```

### 3. 对齐方法
- **RLHF**: 医生偏好对比 (论文15)
- **DPO**: 直接偏好优化，无需奖励模型 (论文17)
- **Constitutional AI**: 安全原则约束 (论文16)

### 4. 训练策略
- **课程学习**: 从简单到复杂病例 (论文22)
- **少样本学习**: 预训练+RL微调 (论文20)
- **安全约束**: CVaR风险敏感 (论文21)

## 🚀 实施建议

### 针对双L40硬件配置

**推荐方案**: Chronos-710M + ClinicalBERT
```
模型配置:
├── Chronos-710M: 时序预测主干
├── ClinicalBERT: 临床文本编码器
└── 训练策略: 全参数微调Chronos，冻结ClinicalBERT

显存需求:
├── Chronos: ~15GB (含优化器)
├── ClinicalBERT: ~2GB
└── 总计: ~17GB per GPU (双L40可并行训练)

训练时间估计:
└── 2-3天 (50k样本, 10 epochs)
```

### 数据集准备

参考调研报告推荐:
1. **CDC FluView** - 主要训练数据
2. **MIMIC-IV** - 老年ICU并发症数据
3. **UK Biobank** - 长期健康轨迹

### 奖励函数设计

基于论文13和19的组合:
```python
R_total = (
    0.3 × R_accuracy          # 基础准确性
    + 0.25 × R_early          # 早期预测奖励
    + 0.25 × R_peak           # 峰值预测
    + 0.2 × R_public_health   # 公共卫生影响
) × age_weight × comorbidity_weight - penalties
```

## 📝 待补充内容

### 未下载的重要论文

1. **期刊论文** (需要机构访问):
   - Nature Machine Intelligence: Temporal Difference Learning
   - PLOS Computational Biology: Age-Stratified Reward Design

2. **会议论文** (待发布):
   - ICLR 2025, NeurIPS 2025
   - ICML 2025, AAAI 2026

3. **数据集论文**:
   - MIMIC-IV原始论文
   - CDC FluView数据描述

## 🔗 相关资源

### GitHub仓库
- Chronos: https://github.com/amazon-science/chronos-forecasting
- Moment: https://github.com/moment-timeseries-foundation-model/moment
- Lag-Llama: https://github.com/time-series-foundation-models/lag-llama

### 数据集
- CDC FluView: https://www.cdc.gov/flu/weekly/
- PhysioNet: https://physionet.org/
- UK Biobank: https://www.ukbiobank.ac.uk/

### 工具库
- Stable-Baselines3 (强化学习)
- TSLib (时序预测)
- Transformers (模型加载)

## 📌 使用说明

1. **快速开始**: 先阅读`论文清单.md`了解全貌
2. **按需阅读**: 根据阅读路线图选择论文
3. **代码复现**: 优先选择有GitHub仓库的论文
4. **实验设计**: 重点关注奖励函数和超参数配置

## 🔄 更新日志

- **2024-09-22**: 初始版本，下载24篇核心论文
- **待更新**: 补充期刊论文和会议论文（2025年发布后）

## 📧 维护信息

- **创建时间**: 2024年9月22日
- **维护者**: AI Agent
- **项目**: 老年人流感预测 - 基础模型后训练调优

---

**注意**: 本文档会随着项目进展持续更新。建议定期查看最新版本。
