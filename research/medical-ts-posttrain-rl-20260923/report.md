# 医学时序大模型后训练与强化学习奖惩机制：2023–2026 调研

**编制日期：** 2026-09-23  
**研究问题：** 近几年医学时序大模型的后训练做了什么，强化学习或偏好优化的奖惩机制如何设计，哪些可以迁到老年人流感个体转重预测？  
**范围：** 2023-01-01 至 2026-09-23。医学时序基础模型的后训练；时序预测模型的可验证奖励；临床轨迹离线强化学习的奖励、惩罚与约束。通用时序论文只作机制对照。  
**用途：** 在 2026-09-22 的数据与小模型调研之上，固定后训练实验不要误用治疗策略奖励。

## 结论先行

医学时序基础模型的后训练，到 2026 年 9 月仍然以继续预训练、监督微调、提示调优和联邦微调为主。真正把模型当成策略、用可验证奖励做强化学习后训练的工作已经出现，但几乎都不在流感或转重预测上。[S014][S015][S017][S020]

预测模型和治疗模型用的不是同一种奖励。预测侧的有效奖励是有界的、逐步的、相对基线的误差信号；把无界的负均方误差直接送进组相对策略优化，会让优势估计塌掉。[S005][S006][S007] 治疗侧的有效奖励把生理改善、观测新鲜度和干预成本拆开，并用数据覆盖惩罚或安全成本限制离线外推。[S008][S009][S010] 这两套不能互相替换。没有动作和状态转移时，不应把转重预测写成马尔可夫决策过程。

对老年人流感转重，当前可执行的后训练是小模型监督微调，外加校准和年龄层漏报成本作为评估，而不是作为强化学习奖励。只有在模型输出要驱动监护升级、床位或抗病毒等序贯行动时，才单开一条离线强化学习线，并先做离线评估的敏感性检查。[S013]

## 范围与方法

本轮从本地已核验全文出发，包括 LangTime、Time-R1、VTA、TimeSRL、REATS 和 medR，再检索 arXiv、OpenAlex 和 PubMed。arXiv 在后半段返回 429，因此 2026 年 8 月以后的部分新论文只核到摘要页，公式结论只来自已打开的全文。OpenAlex 匿名检索多次限流，未用作独立结论。检索式和停搜原因见 [research-log.md](research-log.md)。

“后训练”在本报告中指预训练之后的适应：监督微调、指令微调、联邦微调、偏好优化和强化学习微调。预训练目标本身不算后训练，但时间到事件似然、竞争风险等目标会被记录，因为它们常被误写成奖励。

## 一、医学时序基础模型实际在后训练什么

### 多数模型停在生成式预训练或监督适应

已核验的医学时序基础模型分成三类，三类都还没有把转重风险写成可验证奖励。

| 类型 | 代表 | 后训练实际做什么 | 不是什么 |
|---|---|---|---|
| 密集生理信号 | MIRA；约 8M Chronos 的 ECG/ICG 联邦微调；FORMED | 预测或分类损失，参数高效适配，联邦平均 | 临床奖励或偏好模型 [S014][S015][S016] |
| 离散临床事件 | MOTOR、Delphi-2M、ETHOS、SurvivEHR | 时间到事件、竞争风险或下一事件似然；有的零样本，有的少量微调 | 强化学习 [S017][S018][S019][S025] |
| 多模态临床基础模型 | QoQ-Med；MedFound | 指令微调后的领域加权 GRPO；诊断偏好对齐 | 病程数值预测 [S021][S026] |

MIRA 处理不规则间隔、多频率和连续外推，是个体病程表示的相关预训练模型，但已读材料没有强化学习后训练。[S014] 联邦微调论文说明小 Chronos 可以在 ECG 和心阻抗图上做本地或联邦预测微调；非独立同分布时，本地微调可以优于联邦平均。[S015] 这支持“双 L40 先做小模型监督后训练”，不支持“双 L40 可以跑临床强化学习预训练”。

事件模型更接近转重的时间结构。MOTOR 用删失时间到事件似然，而不是分类交叉熵。[S017] Delphi-2M 在英国生物银行学习疾病发生率和时间，并在丹麦人群上做无参数更新的外部验证。[S018] ETHOS 的作者明确把零样本下一事件预测当作替代标注微调的路线。[S019] SurvivEHR 先做竞争风险预训练，再为更长预后做微调。[S025] 这些目标已经包含删失和竞争事件，比把“72 小时内是否转重”压成一个二分类标签更接近临床时间。它们仍然是监督或自监督似然，不是奖励。

### 已经出现的医学强化学习后训练很少，且不在流感上

两条 2025–2026 的工作把强化学习用到了医学模型上，任务都不是个体转重。

TimeSRL 是目前最接近“医学行为时序 + 可验证奖励”的全文。它不让模型直接从步数、睡眠等数值回归焦虑或抑郁分数，而是先把窗口写成自然语言摘要，再只根据摘要预测 PHQ-4 子量表。两个阶段共用一个模型，用组相对策略优化更新整条轨迹。格式错误或无法解析的输出奖励为 0；合法整数分数的奖励是

$$r(p,y)=\exp\left(-\frac{(p-y)^2}{2\sigma^2}\right).$$

作者明确拒绝精确匹配奖励，因为序数分数差 1 分仍应有梯度。[S004] 训练在四张 H100 上跑三个 epoch。这不能外推为双 L40 可跑，也不能把大学生被动感知的结果写成老年流感效果。可迁移的是结构：结局可验证、中间解释没有金标准时，用结局奖励训练解释，而不是人工写一套不可检验的“临床推理分”。

另一篇 2026 年 9 月 10 日的预印本把电子病历基础模型当成生成策略，用强化学习续写患者轨迹。摘要写的奖励是“time-aware, rollout-sensitive”，用来处理有限 rollout 和时间上尚未定论的结局。摘要没有给出公式、队列或模型规模。[S020] 它证明“病历基础模型的强化学习后训练”这条线已经有人做，不能当作可复现配方。

QoQ-Med 在图像、心电图和文本上做指令微调，再用领域感知的组相对策略优化。归一化之后，稀有专科和更难的模态簇会得到更大的优势权重，避免常见、容易的样本淹没梯度。[S021] 这是奖励加权，不是临床成本。对流感项目，对应物是年龄层或医院层的样本重加权，而且应先放在评估和监督损失里检验，而不是直接搬到策略梯度。

MedFound 是 176B 的诊断语言模型，摘要只说有统一偏好对齐，没有给出直接偏好优化或人类反馈强化学习的公式，也不是时序模型。[S026]

## 二、时序预测的强化学习后训练：奖励怎么写才不会塌

### 共同训练骨架

2025–2026 的预测后训练反复出现同一骨架：监督热身，再做无评论家的组相对策略优化或其变体。监督阶段负责格式和粗预测；强化学习阶段用可自动核对的未来值给分，不训练一个单独的人类偏好奖励模型。[S002][S003][S005][S006][S007]

这个选择有原因。预测有未来观测，奖励可以验证。人类偏好标注贵，而且预测误差的排序通常可以由规则直接算出。TimeHF 是例外，它在工业补货模型里加入名为 time-series policy optimization 的人类反馈阶段，但摘要没有给出奖励定义，文中的准确率提升也不能当独立证据。[S024]

### 六种已经写进全文或摘要的奖励

**多维有界误差，再惩罚偏离参考策略。** LangTime 的 TimePPO 把预测和参考策略的输出都拿来打分。奖励是若干误差维度的加权和，经温度和 tanh 压到有界区间，再减去与参考预测的均方误差：

$$R(\hat y_t)=\tanh\left(\tau\sum_i R_i(\hat y_t,y_t)w_i\right)-\beta\,\mathrm{MSE}(\hat y_t,\hat y^{\mathrm{ref}}_t).$$

价值函数假设模型会重复上一步输出，用来估计长期回报。损失里还有一项对齐税，防止强化学习把监督预测损失冲掉。消融显示去掉均方根、绝对误差或分布差异中的任一项都会变差。相对监督微调的提升通常很小，例如 ETTh1 平均均方误差从 0.440 到 0.435。[S001] 这是机制证据，不是“强化学习必然大幅超过微调”的证据。

**逐步精度、局部波动和频率，而不是整段一个分数。** TimeRFT 直接微调时序基础模型，而不是把序列写成文本。主骨干是 Moirai-MoE，并在 Toto 和 Chronos-2 上做了兼容性实验。奖励在每个预测块、每个变量上计算。精度项是按未来序列均值和标准差归一化后的指数误差。只有精度时，模型会倾向过平滑。波动项用预测块与真实块的 softmax 分布之间的 KL 散度：

$$r^{\mathrm{var}}_{t,d}=\exp\left(-D_{\mathrm{KL}}[\varphi(\hat y'_{t,d})\,\|\,\varphi(y'_{t,d})]\right).$$

频率项补长程结构。作者把真实未来也放进奖励组，避免组内没有好样本时优势方向随机；再用分段压缩防止真实标签的满分把策略拉崩。报告的权重是精度 0.9、波动 0.1、频率 0.01。实验在一张 96GB 显卡上完成，不能据此承诺双 48GB L40 同样可跑，但说明小模型强化学习微调不必假设百亿参数。[S006]

**相对基础预测的改进，而不是绝对误差。** PostTime 用 Gemma-3-4B 修改 TimesFM-2.5 的预测，决定修改、保留或忽略。绝对误差的指数奖励在同一提示的一组采样里几乎没有区分度：组内奖励标准差均值只有 0.0171，27.97% 的组接近零方差。作者改成相对基础预测的改进比例，并裁剪到 0 到 1。组内标准差升到 0.0719，近零方差组降到 4.66%。主结果里，监督微调已经带来大部分下降，强化学习是较小的追加。[S007] 对转重预测，若基础模型已经是强的生存或校准模型，奖励应衡量“是否比该基线更校准、更少漏报”，而不是再优化一个绝对交叉熵。

**倒数误差会放大接近最优的差别，也会在零误差处爆炸。** REATS 批评把负均方误差直接当组成奖励：一个很差的样本会抬高组内标准差，使接近最优的候选在归一化后挤成几乎相同的优势。倒数映射 \(1/(1+k\delta)\) 把差距压进 0 到 1，并在靠近 oracle 时拉开差距。文中 \(k=20\)，格式错误罚 0.5，主实验用 1.7B 模型。[S005] VTA 的 Time-GRPO 则直接用均方误差的倒数作为准确性奖励，另加格式奖励；倒数在误差接近 0 时无界，这正是 REATS 试图避免的几何问题。[S003] 两者都说明：回归任务不能照搬数学题的 0/1 奖励，也不能假设任何单调变换在组归一化后等价。

**过程可验证奖励仍然稀少。** VeriTime 的摘要描述用可核对的中间推理标注构造多目标奖励，而不是只给最终预测打分。[S023] TimeSRL 相反，奖励只在最终分数上计算，中间摘要靠共享参数间接受训。[S004] 没有人工过程标注时，后者更现实；有可检验的中间事件时，前者更可审计。流感转重的可检验中间事件是氧疗升级、乳酸或 SOFA 变化，不是模型自己写的一段解释。

**分布塌缩需要正则，而不是再加一个误差项。** GTN-R 把一种失败命名为 suboptimal collapse：早期采不到靠近真实序列的轨迹时，强化学习会把概率质量推离真实值。它用真实值邻域做正则，声称可插入多种强化学习过程。摘要没有公式。[S022] 这与 TimeRFT 把真实未来放进奖励组是同一问题的两种处理。[S006]

### 预测奖励的失败模式

全文里反复出现的失败，比单个 SOTA 数字更值得迁移。

- 无界负误差加组归一化，会使优势估计被异常样本主导。[S005]
- 绝对误差在强基线附近没有组内区分度。[S007]
- 只优化点误差会得到过平滑、趋势错误的预测。[S006]
- 精确匹配奖励对序数或近邻结果没有梯度。[S004]
- 没有监督热身时，直接强化学习会破坏输出格式。[S002][S004]
- 合成思维链若先看到真实标签，会把后见之明写进推理。PostTime 比较了直接拟合真值、带真值提示的轨迹和预测时可见的轨迹，前两者更差。[S007]
- 人类偏好或另一个大模型写的奖励，不能替代可核对的未来观测。[S008][S024]

## 三、临床轨迹强化学习的奖惩、约束和离线评估

这条文献优化的是动作：补液、升压药、通气设置、撤机或设备流量。它不是转重分类器的损失。保留它，是因为项目若进入“预测之后的资源或治疗建议”，这些是目前写得最具体的临床奖惩。

### 稀疏结局、稠密过程和过度治疗

medR 把既有临床奖励分成三类。稀疏结局奖励只在生存或死亡时给分，信用分配差。稠密过程奖励用中间生理变化，但特征和权重常常是手工的，终末奖励又往往压过过程信号。两类相加仍可能出现作者所称的 Pyrrhic Victory：策略为了生存代理而过度干预。[S008]

medR 的奖励不是对动作直接打分，而是健康势的时间差分减去动作成本：

$$R=\gamma\Phi(s_{t+1},t+1)-\Phi(s_t,t)-\lambda C(a_t),$$

$$\Phi(s_t,t)=\delta(t)\sum_f \omega_f S_f(v_{t,f}) U_f(\Delta t_{t,f}).$$

\(\delta(t)\) 随住院时间衰减，抑制无意义地延长 ICU。\(U_f\) 随该特征距当前时刻的间隔下降，陈旧的正常心率不应得到与新鲜测量相同的信用。\(C(a)\) 按干预幅度计成本。附录证明势函数项会望远镜求和，不改变最优策略；动作成本不会望远镜求和，因此在同样的生理终点里偏好更少干预，并等价于带干预成本约束的拉格朗日。[S008] 这是本轮临床奖励里最完整的公式。

奖励本身也要筛选。作者用三条离线适应度：累积奖励与生存及 SOFA 稳定的相关、累积奖励与测量间隔不确定度的负相关、以及以较小干预维持稳态的能力。大语言模型生成候选奖励代码，临床医生复核特征；在线试错被明确排除。[S008] 文中报告相对临床行为策略的加权重要性采样提升 77.3%、66.7% 和 60.3%。这些是回顾性策略价值估计，不是患者结局试验。折扣因子 0.99，特征共识阈值 0.6，每次生成 20 个候选函数。策略网络只有 2 到 3 层、16 到 32 单元，与基础模型后训练不是同一计算规模。[S008]

通气论文给出另一个临床终点选择。作者和临床医生认为死亡混杂太多，主目标改为 28 天无通气天数：死亡为 0，存活则按脱离通气的天数计，观察期内再插管会扣减。奖励是该天数相对最大窗口的比例，可放在终末步或每一步。生理区间奖励是第二目标。离散动作先限制在临床实际出现过的组合，避免离线算法给未见过的危险设置虚高的 Q 值。[S009]

循环支持撤机论文把奖励写成生理分减去大幅度动作变化惩罚，再加上稳定撤机分。分布外动作由密度守卫惩罚。真实患者数据不公开，评估依赖 transformer 数字孪生。[S012] 数字孪生若与策略共享偏差，离线提升不能当成外部验证。

### 惩罚和约束不是奖励的同义词

近期安全离线强化学习把“不要离开数据”写成惩罚或硬约束，而不是再加一个生存分。

几何悲观惩罚在状态—动作嵌入里计算 k 近邻距离，距离超过数据集分位数后，从原始奖励中扣除：

$$r_{\mathrm{geo}}(s,a)=r(s,a)-\lambda_{\mathrm{adapt}}\max(0,U(s,a)).$$

作者在 MIMIC-III 脓毒症上报告，普通 IQL 塌缩到行为克隆，加入该惩罚后终末动作与临床医生的一致率从 75% 升到 86.4%，且可在笔记本 GPU 上训练。[S010] 一致率不是获益。它只说明惩罚把策略拉回数据支持。

OGSRL 批评只惩罚未见动作的保守 Q 学习：动作可以在分布内，后续状态轨迹仍会离开数据。它同时用分布外守卫限制可探索区域，并用生理安全成本表达医学边界。摘要中的 78% 死亡率估计下降和 51% 奖励上升，是 MIMIC-III 脓毒症上的离线估计。[S011]

2024 年的立场论文用公开脓毒症数据做了超过 17,000 次评估实验。排序随评估指标和马尔可夫决策过程定义明显变化，部分设置下强化学习不优于朴素或监督基线。[S013] 同一问题也出现在正式期刊里。荷兰 ICU 的通气强化学习把气体交换作为中间奖励、死亡和状态持续时间作为终末奖励；作者设计的交叉离线评估显示，44% 在一种中间/终末权重下看起来有效的策略，在权重改变后不再成立。[S027] 2026 年的脓毒症强化学习范围综述纳入 72 项回顾性研究，其中 58 项使用 MIMIC；奖励定义差异很大，所谓超过临床医生的结果并不能可靠评价。[S028]

因此，任何“WIS 更高”的临床奖励论文都不能单独作为部署依据。换一个终末定义、折扣或行为策略估计，排序可以反转。JAMA 的 OVISS 研究是这条线里外部验证最强的一例：3,608 例推导，内部验证后再用 227 家医院的 10,217 例患者检验血管加压素启动规则，评估使用加权重要性采样和逆概率加权回归。[S029] 它说明多中心离线评估可以做，但摘要没有给出可迁移的奖励公式，任务也不是转重预测。

## 四、对老年人流感转重预测，什么能迁、什么不能迁

项目主任务仍是个体级预测：在索引时刻 \(t_0\) 之前可见的生命体征、检验、氧疗和事件，预测未来固定窗口内的 ICU、通气、升压药、SOFA 恶化或死亡。下面的迁移只服务这个任务。治疗强化学习留到动作日志存在之后。

| 机制 | 可迁移的部分 | 必须改写或禁止的部分 | 证据 |
|---|---|---|---|
| 小模型监督后训练 | 先做 Chronos、MIRA 或 MOMENT 的微调，记录序列长度、精度和峰值显存 | 不要把联邦或零样本结果写成流感效果 | [S014][S015] |
| 时间到事件似然 | 用删失和竞争风险处理转重与出院、死亡 | 不要把生存似然叫作强化学习奖励 | [S017][S025] |
| 有界、逐步、相对基线的误差奖励 | 若以后做概率预测的强化学习微调，奖励应衡量相对强基线的校准和分位数改进，并惩罚过平滑 | 不要使用无界负 Brier 或负对数损失直接做组归一化 | [S005][S006][S007] |
| 序数高斯奖励 | 若终点是有序严重度而不是二分类，精确匹配奖励信息不足 | PHQ-4 的 \(\sigma\) 不能直接用于 SOFA | [S004] |
| 观测新鲜度 | 作为输入掩码、缺失指示或评估分层，检查陈旧检验是否被当成当前稳定 | 不要在没有动作的模型里减去用药成本 | [S008] |
| 年龄层重加权 | 先在验证集上报告 65 岁以上的灵敏度、校准和决策曲线 | QoQ-Med 的领域温度是诊断任务的优势缩放，不是老年漏报的临床成本 | [S021] |
| 分布外惩罚 | 仅在后续治疗或资源策略中，限制未见过的动作和后续状态 | 不能用来证明预测模型安全 | [S010][S011] |
| 加权重要性采样 | 仅在独立的策略评估里，并报告行为策略覆盖和指标敏感性 | 不能代替 AUROC、AUPRC、Brier 或外部医院验证 | [S008][S013] |

建议的实验顺序因此不变，只把奖励文献放在正确的阶段。

1. 固定 \(t_0\)、复合终点、预测窗口、竞争风险和禁止使用的未来治疗信息。
2. 用监督或生存损失微调小模型。评估里单列老年层漏报、校准和提前量。这一步不需要强化学习。
3. 若概率预测需要强化学习微调，先复现一个通用配方的失败模式：无界负误差、绝对误差奖励塌缩、只优化点误差导致过平滑。通过后再设计相对基线的有界奖励。[S005][S006][S007]
4. 只有动作、状态转移和决策日志定义完成，才引用 medR、无通气天数和几何惩罚，建立单独的约束马尔可夫决策过程。上线前按 Luo 等人的警告做指标和状态定义敏感性分析。[S008][S009][S010][S013]

## 证据与置信度

| 编号 | 结论 | 主要证据 | 反证或限制 | 置信度 |
|---|---|---|---|---|
| C001 | 医学时序基础模型的主流后训练仍是监督、时间到事件或参数高效适应，不是强化学习 | [S014][S015][S016][S017][S018][S019][S025] | 新预印本可能在摘要之外包含未检出的强化学习附录 | 高 |
| C002 | 医学模型的强化学习后训练已经出现，但任务是行为评分、病历续写或跨模态诊断，不是流感转重 | [S004][S020][S021] | [S020] 只有摘要 | 中 |
| C003 | 时序预测强化学习后训练的主导算法是监督热身加组相对策略优化变体，奖励必须可验证 | [S001][S002][S003][S005][S006] | [S024] 使用人类反馈，但公式未核验 | 高 |
| C004 | 直接把误差当奖励会不稳定；有界化、参考策略惩罚或真实值邻域正则是已发表的对策 | [S001][S005][S006][S022] | 各公式的最优形式没有跨医学数据的独立复现 | 中 |
| C005 | 组归一化会取消简单线性缩放，并被异常样本或强基线附近的小差异破坏 | [S005][S007] | 仅在两组作者的基准上演示 | 中 |
| C006 | 没有中间金标准时，可以用最终可验证结局训练中间表示；这不等于中间推理已被临床验证 | [S004][S020][S021] | [S020] 未给公式 | 中 |
| C007 | 小模型强化学习微调可以在单卡或双 A100 量级完成，但不能外推为任意双 L40 配置可行 | [S006][S007] | 未在 L40 上复现 | 中 |
| C008 | 临床治疗奖励应分离生理改善、观测质量和干预成本，死亡不应自动作为唯一终点 | [S008][S009][S012] | 这些是治疗任务 | 高 |
| C009 | 离线临床策略还需要动作或后续状态的分布外惩罚，以及独立的安全成本 | [S009][S010][S011][S012] | 安全指标多为离线或与临床行为的一致性 | 中 |
| C010 | 回顾性策略价值对终末定义和决策过程表述敏感，不能单独证明临床获益 | [S008][S011][S013][S027][S028][S029] | 无直接反证；限制来自评估设计本身。OVISS 改善了外部验证，但没有取消这一限制 | 高 |

## 分歧与不确定处

预测奖励文献内部并不一致。VTA 使用无界倒数均方误差，REATS 明确反对这种几何；Time-R1 先设计多目标结构奖励，后文又把均方误差作为主准确性奖励。[S002][S003][S005] 目前没有跨数据集的消融证明哪一种映射普遍更好。可迁移的是问题，不是某一个常数。

临床奖励也没有共识终点。medR 用稳态势和 SOFA，通气论文用无通气天数，撤机论文用血流相关稳定分，荷兰 ICU 研究同时用气体交换和死亡。[S008][S009][S012][S027] Luo 等人表明，换终点和换马尔可夫决策过程定义后，算法排序会变；交叉离线评估和脓毒症综述给出了同样方向的证据。[S013][S027][S028] 因此本报告不推荐“把某一篇的 WIS 提升复制到流感”。

病历基础模型强化学习后训练的最直接论文只有摘要，队列未公开。[S020] 它可能在正式版本中改变奖励定义。GTN-R、VeriTime 和 TimeHF 同样只核到摘要，不进入公式建议。[S022][S023][S024]

## 局限与证据缺口

- 没有找到同时满足“2024–2026、医学时序基础模型、明确后训练奖励公式、流感或老年转重、可在双 L40 复现”的论文。这是领域缺口，不是检索遗漏可以补上的结论。
- arXiv 在 2026-09-23 后半段限流。部分 2026 年 8–9 月论文没有下载全文。
- OpenAlex 匿名接口限流，PubMed 结果依赖子代理摘录。期刊论文的作者全名和页码没有逐一回到出版社页面复核的，已标成摘要级。
- 子代理还发现空气质量类别不对称奖励、金融后见偏好优化和校准评分规则比较。它们与机制相关，但全文未在本轮打开，故不写入公式建议。
- 本地第一轮清单中的“医学奖励塑形”“临床 RLHF”“流行病强化学习”等题名已被身份核对否定。本报告不引用那些文件名。

## 对后续实验的含义

证据支持的下一步不是实现一个临床强化学习奖励。证据支持的是：用生存或竞争风险损失完成小模型后训练；把老年层漏报和校准写成评估协议；若要尝试预测侧强化学习，先在公开时序基准上复现奖励塌缩，再把奖励定义成相对强基线的有界改进。治疗侧的势函数、无通气天数和几何惩罚只进入单独的决策层设计，并且必须带离线评估敏感性分析。

## 参考文献

[S001] Niu, W., Xie, Z., Sun, Y., et al. (2025). LangTime: A Language-Guided Unified Model for Time Series Forecasting with Proximal Policy Optimization. arXiv. https://arxiv.org/abs/2503.08271

[S002] Zhou, Y., Luo, Y., Cheng, M., et al. (2025). Time Series Forecasting via Reasoning: A Slow-Thinking Approach with Reinforcement Fine-Tuned LLMs. arXiv. https://arxiv.org/abs/2506.10630

[S003] Koa, K. J. L., Chen, J., Ma, Y., et al. (2026). Reasoning on Time-Series for Financial Technical Analysis. ICLR 2026 / arXiv. https://arxiv.org/abs/2511.08616

[S004] Fan, Y., Xu, L., Wu, M., et al. (2026). TimeSRL: Generalizable Time-Series Behavioral Modeling via Semantic RL-Tuned LLMs. arXiv. https://arxiv.org/abs/2605.21295

[S005] Zhang, X., Xu, C., Sun, H., et al. (2026). REATS: LLM Reasoning-based Ensemble Learning for Adaptive Time Series Forecasting. arXiv. https://arxiv.org/abs/2608.10149

[S006] Li, S., Chen, Y., Zhu, Z., et al. (2026). TimeRFT: Stimulating Generalizable Time Series Forecasting for TSFMs via Reinforcement Finetuning. arXiv. https://arxiv.org/abs/2605.00015

[S007] Liu, H., Zhou, Y., Sen, R., Prakash, B. A., & Das, A. (2026). Rethinking Post-Training Recipes for Multimodal Time-Series Forecasting. arXiv. https://arxiv.org/abs/2605.29401

[S008] medR authors. (2026). medR: Reward Engineering for Clinical Offline Reinforcement Learning via Tri-Drive Potential Functions. arXiv. https://arxiv.org/abs/2602.03305

[S009] Yousuf, M. H., Li, J., Vahdati, S., et al. (2025). Advancing Safe Mechanical Ventilation Using Offline RL With Hybrid Actions and Clinically Aligned Rewards. arXiv. https://arxiv.org/abs/2506.14375

[S010] Wanjari, S. (2026). From Robotics to Sepsis Treatment: Offline RL via Geometric Pessimism. arXiv. https://arxiv.org/abs/2602.08655

[S011] Yan, R., Shen, X., Wachi, A., et al. (2025). Offline Guarded Safe Reinforcement Learning for Medical Treatment Optimization Strategies. arXiv. https://arxiv.org/abs/2505.16242

[S012] Tumay, A., Sun, S., Yu, R., et al. (2025). Guardian-regularized Safe Offline Reinforcement Learning for Smart Weaning of Mechanical Circulatory Devices. ML4H 2025 / arXiv. https://arxiv.org/abs/2511.06111

[S013] Luo, Z., Pan, Y., Watkinson, P., & Zhu, T. (2024). Reinforcement Learning in Dynamic Treatment Regimes Needs Critical Reexamination. arXiv. https://arxiv.org/abs/2405.18556

[S014] Li et al. (2025). MIRA: Medical Time Series Foundation Model for Real-World Health Data. arXiv. https://arxiv.org/abs/2506.07584

[S015] Ali et al. (2025). Fine-Tuning Foundation Models with Federated Learning for Privacy Preserving Medical Time Series Forecasting. arXiv. https://arxiv.org/abs/2502.09744

[S016] Huang, N., Wang, H., He, Z., & Zitnik, M. (2024). Repurposing Foundation Model for Generalizable Medical Time Series Classification. arXiv. https://arxiv.org/abs/2410.03794

[S017] Steinberg, E., Fries, J., Xu, Y., & Shah, N. (2023). MOTOR: A Time-To-Event Foundation Model For Structured Medical Records. arXiv. https://arxiv.org/abs/2301.03150

[S018] Delphi-2M authors. (2025). Learning the natural history of human disease with generative transformers. Nature. https://doi.org/10.1038/s41586-025-09529-3

[S019] ETHOS authors. (2024). Zero shot health trajectory prediction using transformer. npj Digital Medicine. https://doi.org/10.1038/s41746-024-01235-0

[S020] Xiao, Y., Zhang, S., Singh, C., Naumann, T., et al. (2026). Reinforcement Learning over Patient Trajectories for Clinical Reasoning in EHR Foundation Models. arXiv. https://arxiv.org/abs/2609.12277

[S021] Dai, W., Chen, P., Ekbote, C., & Liang, P. P. (2025). QoQ-Med: Building Multimodal Clinical Foundation Models with Domain-Aware GRPO Training. arXiv. https://arxiv.org/abs/2506.00711

[S022] Zhang, J., Zhang, X., Song, Z., Zheng, C., et al. (2026). Ground-Truth Neighborhood Regularization for Reinforcement Learning Post-Training of Time Series Foundation Models. arXiv. https://arxiv.org/abs/2608.08010

[S023] Zhou, J., Li, D., Li, B., et al. (2026). Time Series Reasoning via Process-Verifiable Thinking Data Synthesis and Scheduling for Tailored LLM Reasoning. arXiv. https://arxiv.org/abs/2602.07830

[S024] Qi, Y., Hu, H., Lei, D., et al. (2025). TimeHF: Billion-Scale Time Series Models Guided by Human Feedback. arXiv. https://arxiv.org/abs/2501.15942

[S025] SurvivEHR authors. (2026). SurvivEHR: a competing risks, time-to-event foundation model. npj Digital Medicine. https://doi.org/10.1038/s41746-026-02709-z

[S026] MedFound authors. (2025). A generalist medical language model for disease diagnosis assistance. Nature Medicine. https://doi.org/10.1038/s41591-024-03416-6

[S027] Roggeveen et al. (2024). Reinforcement learning for intensive care medicine: actionable clinical insights from novel approaches to reward shaping and off-policy model evaluation. Intensive Care Medicine Experimental. https://doi.org/10.1186/s40635-024-00614-x

[S028] Sepsis RL review authors. (2026). Reinforcement learning for treatment decision-making in sepsis: a scoping review. npj Digital Medicine. https://doi.org/10.1038/s41746-026-03034-1

[S029] OVISS investigators. (2025). Optimal Vasopressin Initiation in Septic Shock: The OVISS Reinforcement Learning Study. JAMA. https://doi.org/10.1001/jama.2025.3046

## 附录：检索覆盖

已检索 arXiv 的时序强化学习、医学时序基础模型和临床离线强化学习；PubMed 的电子病历与心电图基础模型；OpenAlex 因限流未形成独立证据。全文打开的核心机制论文包括五篇本地引子论文、medR，以及 TimeRFT、PostTime、通气奖励、几何悲观惩罚、OGSRL 和 CORMPO。2026-09-23 的 arXiv 429 使 GTN-R、VeriTime、TimeHF 和病历轨迹强化学习论文停留在摘要级。停止原因是新检索不再增加新的奖励机制类别，只增加同一类别的未读变体。完整记录见 [research-log.md](research-log.md) 与 [sources.jsonl](sources.jsonl)。
