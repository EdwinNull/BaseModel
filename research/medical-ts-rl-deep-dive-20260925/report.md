# 医学时序大模型后训练与强化学习：数据集、基线模型与奖惩机制（深入轮）

**编制日期：** 2026-09-25  
**研究问题：** 医学时序大模型的后训练与强化学习，论文实际用了哪些公开数据集、哪些基准模型，奖惩机制怎么写？  
**范围：** 只含医学时序：ECG/EMG/EEG 等生理信号、ICU 与 EHR 纵向记录、可穿戴行为序列、血糖连续监测。2017–2026，重点 2025–2026。通用时序 RL 已在 09-23 报告（S001–S007、S022–S024）中覆盖，本轮不重复。  
**承接：** 来源 S001–S029 见 [09-23 报告](../medical-ts-posttrain-rl-20260923/report.md)；本轮新增 S030–S066，明细见 [sources.jsonl](sources.jsonl)，检索过程见 [research-log.md](research-log.md)。

## 结论先行

**第一，医学时序大模型的 RL 后训练已经成型。** 2025–2026 出现了一批把 LLM 或多模态 LLM 当策略、在医学时序上做强化学习的全文工作，覆盖 ECG（TimeMaster、ECG-R1、MedTVT-R1、QoQ-Med）、EHR 纵向记录（EHR-R1、EHRMind、EAG-RL）、可穿戴行为序列（TimeSRL），以及把 LLM 当治疗策略的 SepsisAgent。配方高度一致：监督微调热身，再用 GRPO 或 DAPO，奖励由"可自动核对的结局分"加"格式分"组成，不训练单独的人类偏好奖励模型。[S030][S032][S033][S021][S034][S035][S036][S004][S037]

**第二，相对 09-23 报告的更新：预测侧的风险 RL 已经在 EHR 上出现。** EAG-RL 在 MIMIC-IV 住院死亡和 30 天再入院上用 GRPO 训练 7B 模型，奖励是概率的对数得分加一个间隔奖励，再加与专家模型注意力特征的 Jaccard 对齐；EHR-R1 对 18 个风险预测任务直接用 F1 作奖励。[S036][S034] 它们仍然不是流感或老年转重，但任务形式（EHR 时序 → 未来结局概率）与本项目同构，是目前最近的参照。

**第三，奖惩机制可以分成三层。** 结局层（指示函数、Jaccard、F1、序数高斯、对数得分）、过程层（证据覆盖、专家特征对齐、LLM 评审软分）、约束层（格式、指南违规、分布外、动作成本）。医学时序 LLM 论文几乎都只用结局层加格式；真正用可核对外部证据做过程奖励的只有 ECG-R1 和 EAG-RL。[S032][S036][S030]

**第四，时效奖励是转重预警最值得借用的设计。** PhysioNet 2019 效用函数在发病前 12 小时到发病后 3 小时的窗口内奖励阳性预测，峰值 1 分在发病前 6 小时；漏报从发病前 6 小时起线性扣到发病后 3 小时的 −2 分；误报每小时 −0.05 分。[S047] EARLIEST 和 Stop&Hop 用"停下时预测正确 +1、错误 −1，再惩罚等待"的方式训练停时策略，后者在 PhysioNet 2012 死亡预测上验证。[S048][S049]

**第五，治疗侧离线 RL 的奖励十年变化不大。** 仍以终末生存（±1、±15、±100）加中间 SOFA/乳酸或治疗靶区间为主。Raghu 等 2017 年的中间奖励（C0=−0.025、C1=−0.125、C2=−2）在 2026 年的 SepsisAgent 中被原样复用。[S051][S037] 近两年的变化是加入动作成本、指南违规、分布外惩罚，以及用 LLM 编码病历文本扩充状态（MORE-CLEAR）。[S038][S062]

**第六，数据高度集中，外部验证稀少。** EHR/ICU 线几乎都用 MIMIC-III/IV，ECG 线用 MIMIC-IV-ECG 与 PTB-XL。跨中心公开组合只有 YAIB 支持的 MIMIC-III/IV、eICU、HiRID、AmsterdamUMCdb；本轮论文中做了外部队列的只有 MORE-CLEAR（首尔大学医院，私有）。[S046][S038]

**第七，基线清单在各线相当固定。** LLM 线必比 GPT-4o 和"同底座只做 SFT"；时序 LLM 线比 PatchTST、TimesNet、DLinear 等；不规则 ICU 线比 GRU-D、mTAND、Warpformer；ICU 预测比 LR、LightGBM、GRU、TCN、Transformer；离线 RL 比临床医生策略、BCQ、CQL、DDQN，并用 WIS、DR、FQE 做离线评估。[S030][S045][S046][S038][S037]

**第八，底座不大，但没有一篇的配置装得进双 L40。** 已报告的医学时序 RL 后训练底座多在 1B–8B，总显存从 160GB（EHRMind，2×A100-80GB）到 640GB（MedTVT-R1，8×A800）。单卡 48GB 与 L40 相同的只有 TimeMaster（RTX A6000，3B）和 EAG-RL（48GB 卡，7B），但它们都用了 4 张卡。[S030][S036][S035][S033] 双 L40（2×48GB = 96GB）跑 1–4B 底座加 LoRA 的 GRPO，需要减小组大小、序列长度或用梯度累积，必须实测。

对本项目的含义：现有路线（先固定 `t0` 与终点，再做监督或生存后训练）不变；在它之后，新增一条有文献依据的"预测侧 LLM-RL"实验线，奖励用**有界的适当评分规则**，老年漏报代价留在阈值和决策曲线里处理，不写进奖励权重（理由见第五节推导）。

## 一、研究图谱：三条线

| 线 | 策略在决定什么 | 代表 | 与转重预测的关系 |
|---|---|---|---|
| A. 医学时序大模型 RL 后训练 | 生成推理与答案（诊断、风险、分数） | TimeMaster、ECG-R1、MedTVT-R1、QoQ-Med、EHR-R1、EHRMind、EAG-RL、TimeSRL、EHR-FM 轨迹 RL | 可直接迁移：把转重风险写成可验证输出 |
| B. 预测/预警侧 RL（非 LLM） | 何时报警、何时停止观察、何时开检验 | EARLIEST、Stop&Hop、ICU 检验医嘱 RL、PhysioNet 2019 效用 | 可迁移到"何时发出转重预警" |
| C. 治疗侧离线 RL | 补液、升压药、通气、氧疗、给药 | Raghu、AI Clinician、肝素、撤机、血糖、DeepVent、COVID-19 氧疗、MORE-CLEAR、SepsisAgent、medR | 只在预测之后有序贯行动时单列 |

SepsisAgent 横跨 A 与 C：LLM 是策略，动作是治疗。[S037] OpenTSLM、GEM、PULSE 属于只做监督微调的医学时序 LLM，不在 RL 之列，但它们是 A 线论文的常用对照或数据来源。[S031][S039][S040]

## 二、奖惩机制：只含医学时序

### 2.1 结局层：可验证奖励（A 线）

| 形式 | 公式 | 论文 | 设计理由与风险 |
|---|---|---|---|
| 指示函数 | r = 0.1·r_fmt + 0.9·𝟙[ĉ = c*] | TimeMaster；EHRMind（精确匹配） | 最简单；类别不平衡时，"总答阴性"也能拿到高期望奖励（本报告推论） |
| 集合 Jaccard | R_J = \|L_C ∩ L_G\| / \|L_C ∪ L_G\|，并集为空时 0 | MedTVT-R1（R = R_F + R_J）；ECG-R1（诊断集合） | 多标签诊断、共病；部分正确有部分分 |
| 按任务 ACC/F1 | R_acc = ACC（决策类）或 F1（风险类），λ_fmt = λ_acc = 1 | EHR-R1 | 单样本单标签时 F1 退化为对错判断，对罕见结局同样偏向阴性（推论） |
| 序数高斯 | r = exp(−(p − y)² / 2σ²)，解析失败为 0 | TimeSRL（PHQ-4，0–6 分） | 近邻答案也有梯度；σ 需按量表尺度重设 |
| 对数得分 + 间隔 | R_cls = log(y*·ŷ + (1−y*)(1−ŷ)) + Δ；Δ = β(ŷ−0.5)（正例且 ŷ>0.5），β(0.5−ŷ)（负例且 ŷ<0.5），否则 0 | EAG-RL | 对数得分是严格适当评分规则，直接奖励校准；ŷ 趋于 0 或 1 时无界，组归一化下会被极端样本主导（与 S005 的发现一致），需裁剪 |
| 时间感知、rollout 敏感 | 摘要未给公式 | EHR-FM 轨迹 RL | 处理有限 rollout 与尚未发生的结局；摘要级，不复用 |

来源：[S030][S035][S033][S032][S034][S004][S036][S020]

### 2.2 过程层：证据与对齐

- **证据覆盖（ECG-R1 的 EDER）。** 对诊断协议的每一步 k，用 DeepSeek-V3.1 从参考报告中抽取至多 3 个、每个不超过 6 个词的关键证据短语，奖励为 r_step^(k) = |match(E_k(y), ỹ^(k))| / |E_k(y)|，再对各步取平均，总奖励 R = R_format + R_accuracy + λ·R_EDER。RL 用 DAPO，ε_low = 0.2、ε_high = 0.3，样本 3,948 条。[S032] 这是本轮唯一"逐步核对医学证据"的奖励。
- **专家注意力对齐（EAG-RL）。** R_att 是模型推理中引用的特征集合与专家 EHR 模型 Concare 高亮特征集合的 Jaccard，总奖励 R = 0.6·R_cls + 0.4·R_att。[S036] 它用一个强监督模型替代人工过程标注。
- **LLM 评审软分（TimeMaster）。** 只在分类正确时，由 GPT-4o 对具体性、恰当性、相关性、深度四维打分取平均；主实验权重设为 0，只在案例研究中启用。[S030]

### 2.3 约束层：格式与结构

所有 A 线论文都有格式奖励：TimeMaster 检查 XML 标签嵌套和顺序；ECG-R1 只要求 `<think>` 非空；MedTVT-R1 和 EHR-R1 检查 `<think>`/`<answer>` 或"提取—推理—结果"三段结构；TimeSRL 对无法解析的输出直接给 0 分。[S030][S032][S033][S034][S004] 格式分通常只占 0.1 或以二值相加，作用是防止 RL 破坏 SFT 学到的输出结构。

### 2.4 时效层：预警与停时（B 线）

**PhysioNet 2019 效用函数**（官方评分代码常数）：[S047]

| 情形 | 相对发病时刻 t_s 的效用 |
|---|---|
| 阳性预测、患者会发病 | t < t_s−12h：−0.05；t_s−12h 到 t_s−6h：从 0 线性升到 1；t_s−6h 到 t_s+3h：从 1 线性降到 0 |
| 阴性预测、患者会发病 | t ≤ t_s−6h：0；t_s−6h 到 t_s+3h：从 0 线性降到 −2 |
| 阳性预测、患者不发病 | −0.05 |
| 阴性预测、患者不发病 | 0 |

总分按 (U − U_不预测) / (U_最优 − U_不预测) 归一化，最优为 1，从不报警为 0。数据含三个医院系统 40,336 名患者、40 个逐小时变量。

**停时策略。** EARLIEST 用 RNN 判别器加 RL 控制器决定何时停下分类。[S048] Stop&Hop 用 GRU-D 编码不规则前缀，停下时预测正确奖励 +1、错误 −1，并对"等待"的概率加可调惩罚，用 REINFORCE 训练；真实数据为 PhysioNet 2012 住院死亡（4,000 名患者、42 个变量、阳性 13.8%）。[S049]

**带成本的检验医嘱。** ICU 检验医嘱 RL 用向量奖励 r_t = [r_SOFA, r_treat, r_info, −r_cost]：SOFA 变化、是否触发治疗、预测误差带来的信息增益、随距上次检验时间指数衰减的检验成本，用 Pareto 最优的拟合 Q 迭代求解。[S050]

### 2.5 治疗层：生理与结局（C 线）

| 类型 | 公式或设置 | 论文 |
|---|---|---|
| 只有终末 | 90 天生存 ±100 | AI Clinician [S053] |
|  | ICU 生存 ±15 | Raghu MLHC 版 [S052]；COVID-19 氧疗（DDPG，1,372 例，0–60 L/min）[S059] |
|  | 90 天生存 ±1，γ = 0.98 | MORE-CLEAR（CQL，α = 2）[S038]；DeepVent 终末项 [S058] |
|  | 转入生存态 +1，其余 0 | ICU-Sepsis 基准 MDP（716 状态、25 动作）[S060] |
| 终末 + SOFA/乳酸 | r = C0·𝟙(SOFA 不变且 > 0) + C1·ΔSOFA + C2·tanh(Δ乳酸)，C0 = −0.025，C1 = −0.125，C2 = −2；终末 ±15 | Raghu 研讨会版 [S051]；SepsisAgent 复用并加指南违规惩罚 −λ_g·P_g [S037] |
| 终末 + 严重度评分差 | 修改版 APACHE II（去掉 FiO₂、呼吸频率、红细胞压积）的归一化变化量 | DeepVent（动作 7×7×7：潮气量、FiO₂、PEEP）[S058] |
| 治疗靶区间 | 肝素：r = 2/(1+e^−(aPTT−60)) − 2/(1+e^−(aPTT−100)) − 1，60–100 秒内接近 1 | Nemati 2016（MIMIC-II，4,470 例；公式经综述转引）[S054][S066] |
|  | 血糖：r = −10·(3.5506·(ln g)^0.8353 − 3.7932)²，越出 10–1,000 mg/dL 时 −1e5 | Fox 2020（SAC-RNN）[S056]；Emerson 2023（BCQ/CQL/TD3-BC）[S057] |
|  | 撤机：生命体征落在区间内的阈值奖励、变化超过 0.2 的突变惩罚、成功拔管或失败自主呼吸试验/再插管项 | Prasad 2017 [S055] |
| 势函数 | R = γΦ(s′) − Φ(s) − λC(a) | medR [S008] |
| 临床终点 | 28 天无通气天数比例 | 通气离线 RL [S009] |
| 成本 | r = −SOFA − λ·升压药 | MedGym（连续时间脓毒症环境）[S062] |

Fox 等报告，把奖励改成"时间在范围内"或"距目标血糖的距离"效果更差，负 Magni 风险因对低血糖惩罚更重而胜出。[S056] MedGym 发现 SOFA 下降并不保证乳酸安全，治疗有效与安全需分开评估。[S062]

### 2.6 优势层：组内重加权

QoQ-Med 的 DRPO 不改奖励本身，而是把优势除以领域温度与簇温度，T = max(√N·μ, ε)，N 为该领域或簇的样本数、μ 为平均奖励；奖励为 0.6·F1 + 0.2·IoU + 0.2·辅助分。样本少、平均奖励低的领域获得更大梯度，心电图和超声的增益最大。[S021]

### 2.7 失败模式（本轮新增，补充 09-23 报告的七条）

- LLM 零样本做治疗规划时，思维链会让小模型更激进地给胰岛素，增加低血糖风险；7B 到 70B 没有继续提升。[S063]
- 只用终末奖励时，ICU-Sepsis 中随机策略与临床医生策略的回报同为 0.78，最优为 0.88，可学习空间很窄。[S060]
- 4 小时步长是历史惯例；1–2 小时步长在离线脓毒症 RL 中更好更稳。[S064]
- 世界模型单独接入 LLM 并不稳定提升决策，需要 SFT → 行为克隆 → RL 分阶段训练。[S037]
- 过程奖励依赖另一个 LLM 抽取证据（ECG-R1）或另一个模型的注意力（EAG-RL），奖励的正确性受制于这个"裁判"。[S032][S036]

## 三、公开数据集：论文实际用了什么

### 3.1 EHR / ICU 纵向记录

| 数据集 | 规模与粒度 | 访问 | 本轮论文中的用途 | 对本项目 |
|---|---|---|---|---|
| MIMIC-III | 单中心 ICU，逐小时聚合为主 | 凭证 + DUA | 脓毒症 RL：Raghu（Sepsis-3 共 17,898 例）[S052]、ICU-Sepsis（约 17,000）[S060]、MORE-CLEAR（11,114）[S038]、MedGym [S062]、几何悲观与 OGSRL [S010][S011]；通气 DeepVent [S058]、撤机 [S055]；检验医嘱 [S050]；不规则分类基准（24,681）[S045] | 治疗 RL 的历史基准；转重开发优先用 MIMIC-IV |
| MIMIC-IV | 单中心住院 + ICU，含时间戳事件 | 凭证 + DUA | EHR-R1 的 EHR-Ins/EHR-Bench（42 任务，24h 窗口）[S034]；EAG-RL 死亡/再入院（8,750/200）[S036]；SepsisAgent（20,092 次 ICU 住院）[S037]；MORE-CLEAR（10,203）[S038]；MedTVT-QA [S033]；RealICU 长上下文基准 [S043] | **主开发集**（与 09-22、09-23 结论一致） |
| eICU-CRD | 美国多中心 ICU | 凭证 + DUA | YAIB 支持 [S046]；AI Clinician 用 eICU 做独立验证 [S053] | 跨医院外部验证 |
| HiRID | 高时间分辨率 ICU | 凭证 + DUA | YAIB 支持 [S046] | 高频不规则评测 |
| AmsterdamUMCdb | 荷兰 ICU | 申请 | YAIB 支持 [S046] | **新增的第二个外部验证候选**（欧洲人群） |
| PhysioNet 2012 | 约 4,000–12,000 次 ICU 住院前 48h，41–42 变量 | 开放 | Stop&Hop 早期分类 [S049]；LLM vs 不规则时序模型基准 [S045] | 不规则时序方法的快速对照集 |
| PhysioNet 2019 | 40,336 名患者、3 个医院系统、40 个逐小时变量 | 开放 | 早期脓毒症预测与效用函数 [S047] | **时效效用函数的模板**；可做预警流程演练 |
| EHRSHOT | 斯坦福纵向 EHR（6,739 名患者、4,100 万事件） | 申请 | EHR-R1 零样本/少样本 [S034]；EHRMind 诊断任务 [S035] | EHR 基础模型与 LLM 的公共比较场 |
| MIMIC-II | 老版本 ICU | 已停止发放 | 肝素给药 RL（4,470 例）[S054] | 仅历史参考 |

### 3.2 生理信号与可穿戴

| 数据集 | 内容 | 用于 | 对本项目 |
|---|---|---|---|
| MIMIC-IV-ECG | 与 MIMIC-IV 可链接的 12 导联 ECG | ECG-R1 协议 CoT 30k 条 [S032]；MedTVT-QA [S033] | 可与住院轨迹链接，入院 ECG 可作为转重的辅助模态 |
| PTB-XL | 21,801 条 10 秒 12 导联 ECG | ECG-QA → OpenTSLM ECG-QA-CoT [S041][S031]；QoQ-Med [S021] | ECG 编码器预训练与管线测试 |
| ECG-Grounding / ECGInstruct / ECGBench | 细粒度诊断–参数对应；百万级指令；9 数据集基准 | GEM、PULSE、ECG-R1 的训练与评测 [S039][S040][S032] | 仅 ECG 支线 |
| CPSC 2018 | 中国生理信号挑战赛 ECG | QoQ-Med [S021] | 中文人群 ECG 参考 |
| TimerBed-ECG / EMG | ECG 43,673 条 4 类；EMG 205 条 3 类 | TimeMaster [S030] | 验证 RL 配方的小型分类集 |
| SleepEDF | 30 秒 EEG 睡眠分期 | OpenTSLM Sleep-CoT [S031] | 无直接用途 |
| GLOBEM、College Experience | 被动感知行为序列 + 每周 PHQ-4 | TimeSRL [S004] | 跨队列泛化方法参考 |
| HAR 五库、ExtraSensory | 加速度等可穿戴 | OpenTSLM HAR-CoT [S031]；Stop&Hop [S049] | 无直接用途 |

### 3.3 模拟器与基准环境

| 环境 | 构成 | 奖励 | 用于 |
|---|---|---|---|
| UVA/Padova（SimGlucose） | 30 名虚拟 1 型糖尿病患者 | 负 Magni 风险 / LBGI–HBGI | Fox、Emerson、DTR-Bench、LLM 规划器研究 [S056][S057][S061][S063] |
| ICU-Sepsis | MIMIC-III 构建的表格 MDP，716 状态 × 25 动作 | 生存 +1 | 算法基准 [S060] |
| DTR-Bench | 化疗、放化疗、Oberst 脓毒症、SimGlucose 四环境 | 各环境自定义（见 2.5） | 13 种 RL 算法对比 [S061] |
| MedGym | MIMIC-III 拟合的连续时间脓毒症环境 | −SOFA − λ·升压药 | 离散/连续时间、安全约束算法对比 [S062] |

私有数据只作参照：首尔大学医院脓毒症（599 例）[S038]、NYU COVID-19 氧疗（1,372 例）[S059]、同济医院 TJH [S036]。

## 四、基准模型：论文常用的底座与对照

### 4.1 后训练底座与算力

| 论文 | 底座 | 训练方式 | 报告的 GPU |
|---|---|---|---|
| TimeMaster [S030] | Qwen2.5-VL-3B | SFT + GRPO（G = 5，β = 0.001） | 4×A100-80GB 或 RTX A6000-48GB |
| MedTVT-R1 [S033] | LLaMA-3.2-1B + LoRA r8 | PT → SFT → GRPO（G = 8） | 8×A800-80GB |
| ECG-R1 [S032] | Qwen3-VL-8B + ECG-CoCa | SFT + DAPO | 未披露 |
| QoQ-Med [S021] | Qwen2.5-VL-7B/32B | DRPO | 未抽取 |
| EHR-R1 [S034] | Qwen3-1.7B/8B、Qwen2.5-72B | 领域适应 → 推理 SFT → GRPO | 72B 的 GRPO 用 128 卡 |
| EHRMind [S035] | Llama-3-3B | SFT + GRPO（k = 12） | 2×A100-80GB + FSDP 卸载 |
| EAG-RL [S036] | Qwen2.5-3B/7B、Llama3.1-8B | MCTS 轨迹 SFT + GRPO | 4 张 48GB 卡 |
| TimeSRL [S004] | Qwen3-4B | 两阶段 GRPO | 4×H100 |
| SepsisAgent [S037] | Qwen3-4B-Instruct | SFT → 行为克隆 → 世界模型内 GRPO | 未抽取 |
| OpenTSLM（仅 SFT）[S031] | Llama-3.2-1B/3B、Gemma-3-270M/1B | 课程式 SFT + LoRA | Flamingo-3B 约 60GB（5 条 1 万点序列） |

规律：Qwen 家族占多数，1B–8B 是主流区间；超过 30B 的只有 EHR-R1 与 QoQ-Med 的大号版本。

### 4.2 对照基线

| 类别 | 常见模型 | 出现在 |
|---|---|---|
| 闭源/通用 LLM | GPT-4o（最常见）、GPT-5.x、Gemini-3-Pro/Flash、o3/o3-mini/o4-mini、DeepSeek-R1/V3.2、Claude-3.5-Sonnet | [S030][S031][S032][S034][S035][S021][S004][S037] |
| 开源通用 LLM | Qwen2.5/Qwen3 同系列（含 235B）、Llama-3.x、GPT-OSS-120B、InternVL3、GLM-4.1V、MiMo-VL | [S032][S033][S034][S037] |
| 医学 LLM/MLLM | MedGemma 4B/27B、HuatuoGPT-o1/Vision、OpenBioLLM、Baichuan-M2、MedVLM-R1、Chiron-o1、LLaVA-Med、Med-R1、QoQ-Med | [S032][S034][S036][S021] |
| ECG 专用 MLLM | GEM、PULSE | [S032] |
| 时序 LLM | Time-LLM、S²IP-LLM、CALF、FSCA、Time-MQA、VL-Time、数值分词 LLM | [S045][S030][S031] |
| 时序基础模型 | MOMENT、UniTS、Chronos-2（作 OpenTSLM 编码器）；09-22 报告中的 Chronos、TimesFM、Lag-Llama、MIRA | [S045][S031] |
| 经典深度时序 | Transformer、Autoformer、Informer、FEDformer、PatchTST、iTransformer、TimesNet、DLinear | [S030] |
| 不规则 ICU 时序 | GRU-D、mTAND、Warpformer、Concare（EAG-RL 的专家模型） | [S049][S045][S036] |
| ICU 预测表格/序列 | LR、Elastic Net、LightGBM、GRU、LSTM、TCN、Transformer；XGBoost、SVR、MLP | [S046][S004] |
| RL 训练算法对照 | 仅 SFT（几乎所有论文）、GRPO vs DAPO、PPO、RLOO、Reinforce++、ReMax | [S036][S021] |
| 离线/在线 RL | 临床医生策略、随机/零剂量、DDQN/Dueling-DDQN + PER、AI Clinician、WD3QNE、BCQ、CQL、IQL、TD3-BC、Guarded CQL、PPO/TRPO-Lagrangian、SAC-RNN、PID、DQN/C51/SAC/TD3/DDPG、连续时间 TACOS | [S052][S037][S038][S057][S010][S062][S056][S061] |
| 离线策略评估 | WIS、DR、FQE、WPDIS、OPERA、BDESR | [S037][S038][S052] |

### 4.3 基线对比里的反向证据

LLM 在医学时序上并未稳定超过专门模型。HEARTS 用 16 个数据集、110 个任务评测 16 个 LLM，结论是 LLM 大幅落后于专门模型。[S042] ICU 不规则时序基准中，LLM 方法需要至少 10 倍训练时间才达到可比结果，少样本时 Warpformer 更好。[S045] YAIB 发现数据集、队列定义和预处理对结果的影响往往大于模型类别。[S046] 同时，多数 A 线论文的主要对照是未微调的 LLM，很少与 LightGBM、GRU-D 这类强监督基线正面比较；EAG-RL 的测试集只有 200 人、17 例死亡。[S036] 因此 A 线论文中的大幅提升，不能直接当作"LLM-RL 胜过传统风险模型"的证据。

## 五、迁移到老年流感转重预测

### 5.1 迁移矩阵（在 09-23 报告第四节基础上更新）

| 机制 | 可以迁移 | 必须改写或禁止 | 证据 |
|---|---|---|---|
| SFT 热身 + GRPO + 格式分 | 作为预测侧 LLM-RL 的训练骨架 | 必须先有同底座的 SFT 与生存/监督基线 | [S030][S034][S036] |
| 概率型结局奖励 | 用有界的适当评分规则奖励风险概率 | 不用无界对数得分直接做组归一化；不用单样本 F1 或 0/1 奖励罕见结局 | [S036][S034][S005] |
| 过程奖励 | 用 `t0` 前可核对的事件（SpO₂ 下降、氧疗升级、呼吸频率）或强监督模型的重要特征做对齐 | 不用 `t0` 之后的事件；不把 LLM 自评当证据 | [S032][S036] |
| 时效效用 | 按 PhysioNet 2019 的分段形式重设转重预警窗口，作评估；若有报警部署，再作停时策略奖励 | 窗口常数（−12/−6/+3 小时）是脓毒症的，必须与临床重新约定 | [S047][S049] |
| 组内重加权 | 年龄层、医院层样本少时，借鉴 DRPO 在优势层重加权 | 不等同于临床漏报代价 | [S021] |
| 治疗奖励 | 呼吸道感染可参考 COVID-19 氧疗（±15）、无通气天数、SOFA/乳酸 | 只在有动作日志的独立决策层使用，并做离线评估敏感性分析 | [S059][S009][S051][S013] |

### 5.2 奖励设计推导：为什么老年漏报代价不写进奖励权重

以下是本报告的推导，不是文献结论。

设风险输出为 p，真实结局 y ∈ {0,1}，某类患者的真实风险为 q。若奖励用 Brier 型适当评分 S(p, y) = 1 − (p − y)²，期望奖励 q·S(p,1) + (1−q)·S(p,0) 在 p = q 时最大，模型被奖励说真话。若为了少漏报给正例乘以权重 w > 1，期望奖励变为 w·q·S(p,1) + (1−q)·S(p,0)，对 p 求导置零得

  p* = w·q / (w·q + 1 − q)。

例如 q = 0.10、w = 3 时，p* = 0.25：模型被训练成系统性高估 2.5 倍。这会破坏 09-22 报告要求的 Brier、ECE 与校准曲线。对数得分同理。所以：

- **奖励**只放适当评分规则，保持概率校准。有界形式可用 1 − (p − y)²（取值 [0,1]），或把 EAG-RL 的对数得分中的 ŷ 裁剪到 [0.01, 0.99]。
- **老年漏报代价**放在决策阈值、决策曲线和 65+/75+ 分层的灵敏度要求里，这与 09-23 报告"作为评估而不是奖励"的结论一致。
- 罕见结局会让同一提示下的一组采样奖励几乎相同、优势为零（PostTime 在强基线附近观察到同类塌缩）。[S007] 可在 RL 批次中对阳性过采样（改变的是样本分布，需在报告中说明并做校准回检），或用"相对强基线的评分改进"作奖励。

一个可执行的草案（待消融）：

  R = 0.1·R_fmt + 0.9·[1 − (p − y)²] + λ·R_evid，

其中 R_evid 是模型推理中引用的 `t0` 前异常事件与参考事件集合的 Jaccard（参考集来自规则抽取或 LightGBM 的重要特征），λ 从 0 起做消融。

### 5.3 更新后的实验顺序

1. **数据与标签**（不变）：MIMIC-IV 开发，固定 `t0`、复合终点、24/48/72 小时窗口、竞争风险与禁用的 `t0` 后信息；用 YAIB 的队列与预处理代码向 eICU、HiRID、AmsterdamUMCdb 外推。[S046]
2. **监督基线**（不变，扩充基线表）：LR/LightGBM/GRU/TCN/Transformer（YAIB 组合）、GRU-D/mTAND/Warpformer、MOMENT/Chronos/MIRA 加风险头、生存模型。
3. **预测侧 LLM-RL**（新增）：Qwen3-1.7B/4B 或 Llama-3.2-3B，先 SFT，再 GRPO（组大小 5–8，参照 TimeMaster 与 MedTVT-R1）。对照：同底座仅 SFT、0/1 奖励 GRPO、EAG-RL 式对数奖励、零样本 GPT-4o 与 Qwen3。评估：AUROC、AUPRC、Brier、ECE、65+/75+ 分层、按转重时刻重设的效用分数。
4. **预警策略**（条件启用）：只有当部署形式是重复报警时，才用效用分数训练停时策略。[S047][S049]
5. **治疗决策层**（边界不变）：动作日志与状态转移明确后，再引用第二节 2.5 的奖励，并按 Luo 等的方法做指标与 MDP 定义敏感性分析。[S013]

双 L40 的算力判断：TimeMaster 与 EAG-RL 说明单卡 48GB 能参与 3B–7B 的 GRPO，但两者都用 4 张卡，总显存是双 L40 的两倍。[S030][S036] 1–4B 底座加 LoRA、梯度检查点、较短序列和较小的组是合理起点；实际峰值显存与每步耗时必须在 L40 上实测后再排期。

## 六、证据与置信度

| 编号 | 结论 | 主要证据 | 反证或限制 | 置信度 |
|---|---|---|---|---|
| C011 | 医学时序 LLM/MLLM 的 RL 后训练已形成"SFT 热身 + GRPO/DAPO + 可验证结局奖励 + 格式奖励"的主流配方 | [S030][S032][S033][S034][S035][S036][S004][S021] | 多为 2025–2026 预印本；只有 ECG-R1、MedTVT-R1 进入顶会 | 高 |
| C012 | 预测侧风险 RL 已在 EHR 上出现，但不在流感或老年转重 | [S036][S034][S020] | EAG-RL 测试集仅 200 人；S020 只有摘要 | 中 |
| C013 | 可核对外部证据的过程奖励只见于少数论文 | [S032][S036][S030] | 证据由另一个模型抽取或提供 | 中 |
| C014 | 时效奖励在医学时序中已有成熟定义（PhysioNet 2019 效用、停时策略、带成本的检验医嘱） | [S047][S048][S049][S050] | 均非 LLM；窗口常数针对脓毒症 | 高 |
| C015 | 治疗侧奖励以终末生存 + SOFA/乳酸或靶区间为主，近年增加成本、指南与分布外约束 | [S051][S052][S053][S054][S055][S056][S057][S058][S059][S037][S038][S062] | Nemati 公式为二手转引；AI Clinician 正文未打开 | 高 |
| C016 | 数据集集中于 MIMIC-III/IV 与 MIMIC-IV-ECG/PTB-XL，外部验证稀少 | [S038][S046][S032][S033][S028] | 本轮样本以英文预印本为主 | 高 |
| C017 | 各线基线清单相当固定 | [S030][S031][S045][S046][S038][S037] | 不同论文的基线实现与调参不一致 | 高 |
| C018 | LLM 方法在医学时序上尚未稳定超过专门模型，训练成本更高 | [S042][S045][S063] | A 线论文多报告对未微调 LLM 的大幅提升，但很少对比强监督基线 | 中 |
| C019 | 1–8B 底座在 160GB–640GB 总显存上完成 RL 后训练；单卡 48GB 可参与 3B–7B 的 GRPO，但无一篇在 96GB 总显存内完成 | [S030][S036][S035][S033][S004] | 没有 L40 实测；多模态与长序列显存差异大 | 中 |
| C020 | 给适当评分奖励加非对称类权重，会让最优输出偏离真实概率 | 本报告 5.2 推导 | 数学推导，未见医学时序论文专门讨论 | 高（推导） |

## 七、分歧、缺口与局限

- **流感/老年转重仍无直接论文。** 三条线各检索两轮，没有找到对流感或肺炎患者转重做 LLM-RL 后训练的工作；最近的呼吸道感染 RL 是 COVID-19 氧疗（治疗侧）。[S059]
- **EEG、睡眠、血糖的 LLM-RL 后训练未找到全文可核的论文。** 睡眠与可穿戴方向目前以预训练（SleepFM、SensorLM）和 SFT（OpenTSLM）为主；血糖只有零样本 LLM 规划研究。[S031][S063]
- **奖励"裁判"本身未经验证。** ECG-R1 的证据短语由 DeepSeek-V3.1 抽取，EAG-RL 的对齐目标是 Concare 的注意力，TimeMaster 的软分由 GPT-4o 给出。[S032][S036][S030]
- **治疗侧评估仍是离线估计。** SepsisAgent、MORE-CLEAR、COVID-19 氧疗报告的获益都来自 WIS、DR、FQE 或模型模拟，不是前瞻结局。[S037][S038][S059] 09-23 报告 C010 的判断不变。
- **摘要级来源不进入公式建议：** S020、S039–S044、S048、S053、S064、S065。Nemati 的肝素奖励经综述 S066 转引。
- **首轮遗留：** 根目录 `医学时序预测模型调研报告.md` 第 3 节列出的"Outcome-Driven Rewards""Reward Shaping for Medical TS FM""Epidemic Forecasting with RL""Age-Stratified Reward Design"等条目及其奖励公式，已被身份核对否定，本报告与展示页均不引用。

## 参考文献（本轮新增）

[S030] Zhang, J., Feng, L., Guo, X., Wu, Y., et al. (2025). TimeMaster: Training Time-Series Multimodal LLMs to Reason via Reinforcement Learning. arXiv. https://arxiv.org/abs/2506.13705

[S031] Langer, P., Kaar, T., Rosenblattl, M., Xu, M. A., et al. (2025). OpenTSLM: Time-Series Language Models for Reasoning over Multivariate Medical Text- and Time-Series Data. arXiv. https://arxiv.org/abs/2510.02410

[S032] Jin, J., Wang, H., Wu, X., Fang, X., et al. (2026). ECG-R1: Protocol-Guided and Modality-Agnostic MLLM for Reliable ECG Interpretation. ICML 2026 / arXiv. https://arxiv.org/abs/2602.04279

[S033] Zhang, Y., Yuan, K., Lu, H., Yue, Y., et al. (2025). MedTVT-R1: A Multimodal LLM Empowering Medical Reasoning and Diagnosis. CVPR 2026 / arXiv. https://arxiv.org/abs/2506.18512

[S034] Liao, Y., Wu, C., Liu, J., Jiang, S., et al. (2025). EHR-R1: A Reasoning-Enhanced Foundational Language Model for Electronic Health Record Analysis. arXiv. https://arxiv.org/abs/2510.25628

[S035] Lin, J., Wu, Z., & Sun, J. (2025). Training LLMs for EHR-Based Reasoning Tasks via Reinforcement Learning. arXiv. https://arxiv.org/abs/2505.24105

[S036] Fang, Y., Guo, Y., Gao, J., Ding, H., et al. (2025). Toward Better EHR Reasoning in LLMs: Reinforcement Learning with Expert Attention Guidance. arXiv. https://arxiv.org/abs/2508.13579

[S037] Wu, M., Yan, Y., Cai, Z., Ji, K., et al. (2026). Agentifying Patient Dynamics within LLMs through Interacting with Clinical World Model. arXiv. https://arxiv.org/abs/2605.14723

[S038] MORE-CLEAR authors. (2026). Large language model-augmented offline reinforcement learning framework for sepsis management in critical care. npj Digital Medicine. https://doi.org/10.1038/s41746-026-02611-8

[S039] Lan, X., Wu, F., He, K., Zhao, Q., et al. (2025). GEM: Empowering MLLM for Grounded ECG Understanding with Time Series and Images. NeurIPS 2025 / arXiv. https://arxiv.org/abs/2503.06073

[S040] Liu, R., Bai, Y., Yue, X., & Zhang, P. (2024). Teach Multimodal LLMs to Comprehend Electrocardiographic Images. arXiv. https://arxiv.org/abs/2410.19008

[S041] Oh, J., Lee, G., Bae, S., Kwon, J., et al. (2023). ECG-QA: A Comprehensive Question Answering Dataset Combined With Electrocardiogram. NeurIPS 2023 Datasets and Benchmarks. https://arxiv.org/abs/2306.15681

[S042] Li, S., Xiao, S., Joshi, M., Metwally, A., et al. (2026). HEARTS: Benchmarking LLM Reasoning on Health Time Series. arXiv. https://arxiv.org/abs/2603.06638

[S043] Shen, C., Shen, W., Susetzky, T., et al. (2026). RealICU: Do LLM Agents Understand Long-Context ICU Data? A Benchmark Beyond Behavior Imitation. arXiv. https://arxiv.org/abs/2605.13542

[S044] Jang, H., Chu, G., Kim, C., Park, J., et al. (2026). TRIAGE: Dialectical Reasoning for Explainable Risk Prediction on Irregularly Sampled Medical Time Series with LLMs. arXiv. https://arxiv.org/abs/2606.09030

[S045] Zheng, F., Wu, Y., Mascolo, C., & Dang, T. (2026). Rethinking Large Language Models For Irregular Time Series Classification In Critical Care. ICASSP 2026 / arXiv. https://arxiv.org/abs/2601.16516

[S046] van de Water, R., Schmidt, H., Elbers, P., Thoral, P., et al. (2023). Yet Another ICU Benchmark: A Flexible Multi-Center Framework for Clinical ML. arXiv. https://arxiv.org/abs/2306.05109

[S047] Reyna, M. A., et al. (2019). Early Prediction of Sepsis from Clinical Data: The PhysioNet/Computing in Cardiology Challenge 2019. PhysioNet. https://physionet.org/content/challenge-2019/1.0.0/ ；评分代码 https://github.com/physionetchallenges/evaluation-2019

[S048] Hartvigsen, T., Sen, C., Kong, X., & Rundensteiner, E. (2019). Adaptive-Halting Policy Network for Early Classification. KDD 2019. https://doi.org/10.1145/3292500.3330974

[S049] Hartvigsen, T., Gerych, W., Thadajarassiri, J., Kong, X., et al. (2022). Stop&Hop: Early Classification of Irregular Time Series. CIKM 2022. https://arxiv.org/abs/2208.09795

[S050] Cheng, L.-F., Prasad, N., & Engelhardt, B. E. (2018). An Optimal Policy for Patient Laboratory Tests in Intensive Care Units. arXiv. https://arxiv.org/abs/1808.04679

[S051] Raghu, A., Komorowski, M., Ahmed, I., Celi, L., et al. (2017). Deep Reinforcement Learning for Sepsis Treatment. NIPS 2017 ML4H Workshop / arXiv. https://arxiv.org/abs/1711.09602

[S052] Raghu, A., Komorowski, M., Celi, L. A., Szolovits, P., et al. (2017). Continuous State-Space Models for Optimal Sepsis Treatment: a Deep Reinforcement Learning Approach. MLHC 2017. https://arxiv.org/abs/1705.08422

[S053] Komorowski, M., Celi, L. A., Badawi, O., et al. (2018). The Artificial Intelligence Clinician learns optimal treatment strategies for sepsis in intensive care. Nature Medicine, 24, 1716–1720. https://doi.org/10.1038/s41591-018-0213-5

[S054] Nemati, S., Ghassemi, M. M., & Clifford, G. D. (2016). Optimal medication dosing from suboptimal clinical examples: a deep reinforcement learning approach. IEEE EMBC. https://pubmed.ncbi.nlm.nih.gov/28268938/

[S055] Prasad, N., Cheng, L.-F., Chivers, C., Draugelis, M., et al. (2017). A Reinforcement Learning Approach to Weaning of Mechanical Ventilation in Intensive Care Units. UAI 2017. https://arxiv.org/abs/1704.06300

[S056] Fox, I., Lee, J., Pop-Busui, R., & Wiens, J. (2020). Deep Reinforcement Learning for Closed-Loop Blood Glucose Control. MLHC 2020. https://arxiv.org/abs/2009.09051

[S057] Emerson, H., Guy, M., & McConville, R. (2023). Offline Reinforcement Learning for Safer Blood Glucose Control in People with Type 1 Diabetes. Journal of Biomedical Informatics. https://arxiv.org/abs/2204.03376

[S058] Kondrup, F., Jiralerspong, T., Lau, E., de Lara, N., et al. (2023). Towards Safe Mechanical Ventilation Treatment Using Deep Offline Reinforcement Learning. IAAI 2023. https://arxiv.org/abs/2210.02552

[S059] Zheng, H., Zhu, J., Xie, W., & Zhong, J. (2021). Reinforcement Learning Assisted Oxygen Therapy for COVID-19 Patients Under Intensive Care. arXiv. https://arxiv.org/abs/2105.08923

[S060] Choudhary, K., Gupta, D., & Thomas, P. S. (2024). ICU-Sepsis: A Benchmark MDP Built from Real Medical Data. RLC 2024. https://arxiv.org/abs/2406.05646

[S061] Luo, Z., Zhu, M., Liu, F., Li, J., et al. (2024). DTR-Bench: An in silico Environment and Benchmark Platform for Reinforcement Learning Based Dynamic Treatment Regime. arXiv. https://arxiv.org/abs/2405.18610

[S062] Wang, Y., Kawano, K., Fujisawa, Y., Zhou, Y., et al. (2026). A Unified Benchmark for Dynamic Medical Treatment Reinforcement Learning (MedGym). arXiv. https://arxiv.org/abs/2606.01028

[S063] Luo, Z., & Zhu, T. (2025). Are Large Language Models Dynamic Treatment Planners? An In Silico Study from a Prior Knowledge Injection Angle. arXiv. https://arxiv.org/abs/2508.04755

[S064] Sun, Y., & Tang, S. (2025). Exploring Time-Step Size in Reinforcement Learning for Sepsis Treatment. arXiv. https://arxiv.org/abs/2511.20913

[S065] Parker, F., Chan, N., Zhang, C., & Ghobadi, K. (2025). Eliciting Chain-of-Thought Reasoning for Time Series Analysis using Reinforcement Learning. arXiv. https://arxiv.org/abs/2510.01116

[S066] Liu, S., Ngiam, K. Y., & Feng, M. (2019). Deep Reinforcement Learning for Clinical Decision Support: A Brief Survey. arXiv. https://arxiv.org/abs/1907.09475
