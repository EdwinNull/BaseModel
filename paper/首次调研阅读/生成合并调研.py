from pathlib import Path
import html
import shutil

root = Path(__file__).parent
cats = {
    '时序基础模型': '面向数值时序预测、表示学习或流感概率预测的基础模型与直接基线。',
    '强化学习_后训练奖惩机制': '仅保留奖励、惩罚、偏好、约束或离线评估可在论文中定位的条目。',
    '数据集': '按可直接下载、凭证访问和版本化公共监测数据区分。',
}

for name, desc in cats.items():
    d = root / name
    d.mkdir(exist_ok=True)
    (d / 'README.md').write_text(f'# {name}\n\n{desc}\n\n每个子目录均含独立精读文档和 SVG 方法/数据流图。\n')

def svg(path, title, nodes):
    groups = []
    for i, (head, body) in enumerate(nodes):
        x = 26 + i * 294
        groups.append(f'''<g><rect x="{x}" y="100" width="248" height="126" rx="12" fill="#e8f2ef" stroke="#176b5b" stroke-width="2"/>
<text x="{x+124}" y="143" text-anchor="middle" font-size="19" font-weight="600">{html.escape(head)}</text>
<text x="{x+124}" y="176" text-anchor="middle" font-size="15">{html.escape(body)}</text></g>''')
    arrows = ''.join(f'<path d="M{274+i*294} 163 H{294+i*294}" stroke="#176b5b" stroke-width="3" marker-end="url(#arrow)"/>' for i in range(3))
    path.write_text(f'''<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="t d" viewBox="0 0 1200 275"><title id="t">{html.escape(title)}流程图</title><desc id="d">{html.escape(title)}的四步输入、处理和输出流程。</desc><defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0 0 L9 3 L0 6 Z" fill="#176b5b"/></marker></defs><g font-family="system-ui, sans-serif" fill="#202321"><text x="26" y="42" font-size="24" font-weight="600">{html.escape(title)}</text>{''.join(groups)}{arrows}</g></svg>''')

def write_note(category, slug, title, meta, abstract, question, data, steps, mechanism, results, limits, project, code, source):
    d = root / category / slug
    (d / 'images').mkdir(parents=True, exist_ok=True)
    svg(d / 'images' / 'flow.svg', title, steps)
    numbered = '\n'.join(f'{i}. **{a}**：{b}' for i, (a, b) in enumerate(steps, 1))
    (d / '阅读笔记.md').write_text(f'''---
tags: [papers/首次调研, papers/{category}]
date: 2026-09-22
---
# {title}

## 核心信息
{meta}
- 代码 / 项目: {code}
- 证据来源: {source}

## 原文摘要翻译
{abstract}

## 创新点
{question}

## 一句话总结
{question}

## 研究问题
{question}

## 数据与任务定义
{data}

## 方法主线
### 输入输出流
![{title}流程图](images/flow.svg)

> 图：依据本文实际的数据流和模块关系重绘；箭头表示计算或证据传递，不表示未经验证的临床因果关系。

{numbered}

### 模型与训练机制
{mechanism}

## 关键结果
{results}

## 深度分析
{project}

## 局限
{limits}

## 我的笔记
- 复现时固定数据版本、预测时点、训练/验证/测试的时间边界和随机种子。
- 双 L40 只作为后训练资源条件；记录每张卡的峰值显存、序列长度、精度和可训练参数比例。
- 对医疗结果同时报告性能、校准、覆盖和数据覆盖边界，不能仅用单一分数判断可部署性。

## 引用
{source}
''')

# Second-round sources that did not have first-round deep notes.
write_note('时序基础模型', '06_MIRA', 'MIRA：连续时间医学时序基础模型',
'''- 标题: MIRA: Medical Time Series Foundation Model for Real-World Health Data
- 年份: 2025（当前检索到的 arXiv 版本为 v7）
- 论文链接: https://arxiv.org/abs/2506.07584''',
'''本文提出 MIRA，一种针对真实医疗时序预测的基础模型。针对不规则采样、不同频率和缺失值，模型组合连续时间旋转位置编码、按频率路由的专家层和基于 Neural ODE 的连续动力学外推。作者称其在大规模公开医疗时序上预训练，并在分布内和分布外预测中优于零样本和微调基线。''',
'如何让一个预测器同时处理不规则观测、不同采样频率和任意目标时间点，而不是把医疗记录强行重采样为规则网格？',
'输入为带时间戳、变量标识和缺失模式的医疗观察；输出为任意未来时间点的数值预测。论文称预训练语料超过 4540 亿时间点，当前版本未给出足以排定双 L40 后训练的明确最小模型显存。',
[('不规则医疗观察', '数值、时间戳、变量与缺失'), ('连续时间表征', 'CT-RoPE + 频率专家路由'), ('潜在动力学外推', 'Neural ODE 到目标时间'), ('未来值与误差', '任意时点预测和评测')],
'CT-RoPE 将真实时间间隔注入位置相位；频率专家把不同采样节律路由到不同参数子路径；Neural ODE 在潜在空间连续推进状态。三者分别处理时间间隔、频率异质性和任意预测时点，不能只概括为“一个 Transformer”。',
'作者在摘要报告：相对其他零样本和微调基线，分布外和分布内预测误差平均降低约 8% 和 6%。这些是作者报告的聚合结论，具体任务、切分和最小 checkpoint 需要以官方代码再核验。',
'对项目最有价值的是不规则事件的时间编码方式。建议先做最小 checkpoint 的推理和 LoRA 试跑，再比较与 Chronos 的规则窗口预处理；若流感数据本身是周度规则序列，MIRA 的复杂连续时间模块未必带来收益。',
'当前下载版本的更新日期晚于初始提交，且模型尺寸、许可证和双 L40 微调峰值内存尚未被本调研充分核实。医学跨域结果也不等于老年流感年龄分层有效。',
'https://github.com/Microsoft/MIRA',
'[第二轮调研 S001；全文 p.1–4](../第二轮调研/证据/2506.07584.pdf)')

write_note('时序基础模型', '07_Chronos_医学微调', 'Chronos 的医学联邦/本地微调',
'''- 标题: Fine-Tuning Foundation Models with Federated Learning for Privacy Preserving Medical Time Series Forecasting
- 年份: 2025
- 论文链接: https://arxiv.org/abs/2502.09744''',
'''本文研究在 ECG 和阻抗心动图数据上使用联邦学习微调时序基础模型。结果表明，联邦微调是否优于本地微调取决于客户端数据分布；在非独立同分布场景中，本地微调可能更好。''',
'医疗机构不能共享原始时序数据时，协同微调小型时序基础模型是否比各机构独立微调更有效？',
'作者选用约 8M 参数的 Chronos，并在 ECG、ICG 预测任务上比较零样本、本地微调与 FedAvg、FedProx、Fed-LA。每个客户端的切分方式和异质性是实验自变量。',
[('医院本地 ECG/ICG', '原始数据留在客户端'), ('小型 Chronos', '约 8M 参数预测器'), ('本地或联邦更新', '10 轮；聚合或独立适配'), ('64 点预测', '比较误差与异质性')],
'联邦方案向客户端下发当前全局权重，客户端在本地更新再上传参数变化，服务器聚合。该论文不是 LoRA 论文，也没有给出双 L40 峰值内存；其价值是证明小模型医学微调与数据异质性之间的关系。',
'在一些设置中联邦学习优于零样本和本地基线；非独立同分布条件下，本地微调优于联邦微调。论文因此明确否定“联邦必然改善基础模型微调”的假设。',
'这是双 L40 首个实验的直接模板：先选择 Chronos 小版本，分别跑本地微调与按医院/地区模拟的异质切分。老年流感的地区差异可用相同对照，但必须保持每个预测时点的数据可见性。',
'只有 ECG/ICG，未验证流感；FL 通信、隐私攻击面和训练资源没有完整量化。结果受客户端划分规则影响。',
'https://github.com/amazon-science/chronos-forecasting',
'[第二轮调研 S004；全文 p.4–7](../第二轮调研/证据/2502.09744.pdf)')

write_note('时序基础模型', '08_TSPFN', 'TSPFN：小型生理时序上下文学习模型',
'''- 标题: TSPFN: A Temporal Tabular Foundation Model for Physiological Time Series Classification
- 年份: 2026
- 论文链接: https://arxiv.org/abs/2608.31013''',
'''本文把 TabPFN 的上下文学习思想改造到生理时序分类，通过显式的时间与通道表征建模样本内依赖。作者以约 14 万条真实 EEG、ECG 与 ICU 序列预训练，报告在多种生理分类基准上取得稳定的跨域表现。''',
'小样本医疗时序分类能否通过上下文中的支持样本完成，而不为每个任务进行梯度微调？',
'预训练集包括 TUEV、TUAB、PTB-XL、HiRID 等，约 14 万样本；下游含 eICU 等五个分类数据集。模型约 7.3M 参数，论文在一张 H200 上预训练。',
[('支持集和查询序列', '多尺度时间—通道表格化'), ('TSPFN 编码器', '通道 RoPE 与时序表征'), ('上下文推断', '不更新参数的类别后验'), ('分类输出', 'AUROC 等跨域比较')],
'模型保留 Prior-Data Fitted Network 的“支持集—查询集”训练形式，但将时间和通道顺序写入输入，不再把变量视为可任意置换的表格列。其定位是分类，不是预测未来连续值。',
'论文将 TSPFN 与同为 7.3M 的 TabPFN、356K TCN、约 7.5M LaBraM 等比较，报告五个验证集上更稳定的表现；预训练与通道时序编码消融均有贡献。',
'7.3M 参数使下游推断和少量适配对双 L40 非常轻量，但单 H200 预训练不应被误读为本地可复现预训练。适合作为“少样本临床表示”支线，对主流感预测应保持 P2。',
'不预测未来、没有概率预测和后训练奖励机制；公开生理数据的访问条件并不完全相同。',
'https://github.com/Jeremstym/TSPFN',
'[第二轮调研 S002；全文 p.1–7](../第二轮调研/证据/2608.31013.pdf)')

write_note('强化学习_后训练奖惩机制', '08_medR', 'medR：三驱动临床离线强化学习奖励',
'''- 标题: medR: Reward Engineering for Clinical Offline Reinforcement Learning via Tri-Drive Potential Functions
- 年份: 2026
- 论文链接: https://arxiv.org/abs/2602.03305''',
'''本文针对临床离线强化学习的奖励工程，提出由生存、可信度和能力三种驱动组成的势函数。系统用大语言模型协助选择临床特征与函数结构，再用离线指标筛选候选奖励；其目标是在不在线试错的情况下，减少稀疏结局、陈旧测量和过度干预造成的错误策略。''',
'如何把临床稳定、观测是否新鲜和干预是否过度同时写成可审计的离线 RL 奖励，而不是仅对生存结局加一个手工权重？',
'输入为不规则患者状态、观测时间间隔和治疗动作；输出为动作价值或策略。任务覆盖脓毒症、通气等临床治疗，评价使用 WIS 和作者定义的生存、可信度、能力适应度。',
[('患者状态与时间间隔', '生理值、缺失和测量新鲜度'), ('三驱动势函数', '稳定度 + 可信度 − 动作成本'), ('离线策略学习', '固定临床轨迹，无在线探索'), ('奖励筛选与 OPE', 'WIS 和三类适应度')],
'核心形式为 $R\' = R + \\gamma\\Phi(s\')-\\Phi(s)-C(a)$。生存项奖励接近稳态；可信度项随某特征距当前时刻的间隔衰减；能力项按干预幅度惩罚。势函数项和动作成本是不同作用：前者塑形状态变化，后者显式限制高剂量/低效率动作。',
'作者报告完整三驱动奖励在三项临床任务上的 WIS 优于其比较奖励，并提供 95% 自助法区间。消融显示去掉特征选择或任一驱动会损失部分适应度；这些都是离线、模型内指标。',
'这是奖惩机制的首读论文。可迁移的是“目标、观测质量、行动成本分开建模”的方法；对流感预测，应把第三项改为可检验的预测成本或公平约束，而不是把补液剂量成本直接移植。',
'尚未证明策略能改善真实患者结局；LLM 生成的特征与权重也需要临床审查。若没有真实序贯行动，流感预测不应伪装成 RL。',
'论文未给出可核实的官方实现仓库；以 arXiv 附录代码和复现清单为准。',
'[第二轮调研 S003；全文 p.3–9、附录](../第二轮调研/证据/2602.03305.pdf)')

write_note('强化学习_后训练奖惩机制', '09_GNN_Sepsis_Offline_RL', '图表示脓毒症离线强化学习：近 L40 硬件证据',
'''- 标题: Exploring a Graph-based Approach to Offline Reinforcement Learning for Sepsis Treatment
- 年份: 2025，EWRL
- 论文链接: https://arxiv.org/abs/2509.03393''',
'''本文将 MIMIC-III 脓毒症患者的时间戳数据表示为动态异构图，用 GraphSAGE 或 GATv2 编码患者状态，再以 dBCQ 学习离线治疗策略。研究重点是图表示对策略学习的影响，而不是设计新的临床奖励。''',
'复杂医疗记录能否用动态异构图编码，使离线 BCQ 比传统向量状态更有效？',
'MIMIC-III 脓毒症队列按 4 小时聚合；先训练编码器—解码器预测下一状态，再将潜表示给 dBCQ。作者报告使用三张 46GB L40，BCQ GPU 训练约 2.5 小时，GNN 自动编码器约 30 小时。',
[('4 小时患者图快照', '变量、治疗、时间和关系'), ('GNN 编码器', 'GraphSAGE/GATv2 潜状态'), ('dBCQ 离线策略', '从固定轨迹选剂量动作'), ('WIS 评估', '策略价值与覆盖边界')],
'表示学习与策略学习分离：编码器与解码器用下一状态预测训练；冻结后把潜状态输入 Q 网络。WIS 通过目标与行为策略的概率比加权回报，依赖行为策略估计和支持集覆盖。',
'GNN 表示可以形成具有竞争力的 WIS 曲线，但编码器重构误差与下游策略 WIS 不严格对应。作者也承认只用 MIMIC-III，WIS 的临床意义有限。',
'它为双 L40 附近的离线 RL 开销提供最具体的证据，适合先估算工程预算。对流感工作，只在将预测转为资源配置行动后才需要这类状态—动作建模。',
'单数据集、回顾性 WIS、行为策略估计误差和未观测混杂都限制结论；不包含可迁移的奖励函数创新。',
'论文未定位官方代码仓库。',
'[第二轮调研 S005；全文 p.4–10](../第二轮调研/证据/2509.03393.pdf)')

datasets = [
('01_FluSight', 'CDC FluSight Hub：版本化流感概率预测目标', 'CDC FluSight Forecast Hub', '周度 NHSN 流感住院目标、概率分位数提交和版本化目标数据。', '公开下载', '预测目标与分位数文件', '冻结预测日数据版本', '训练/滚动回测', 'WIS、MAE、覆盖率', 'FluSight 是老年流感预测的主目标入口；需另行确认 65+/75+ 分层目标和辅助信号许可。', '数据后续修订会造成泄漏；默认目标并非年龄分层。', 'https://github.com/cdcgov/FluSight-forecast-hub', '[第二轮调研 S014](../第二轮调研/report.md)'),
('02_PTB_XL', 'PTB-XL：公开 ECG 波形基准', 'PTB-XL, a large publicly available electrocardiography dataset', '21801 条 10 秒 12 导 ECG，来自 18869 名患者；含报告与标签。', '可直接下载', 'ECG 波形与诊断标签', '采样、导联和标签映射', '训练/验证/测试划分', '分类/表征指标', '适合波形预训练或生理时序管线验证，不是流感传播或住院预测数据。', '任务和人群与流感不同，不能从 ECG AUROC 推出流感预测有效。', 'https://physionet.org/content/ptb-xl/', '[第二轮调研 S010](../第二轮调研/report.md)'),
('03_MIMIC_IV', 'MIMIC-IV：凭证访问的纵向 ICU/EHR 数据', 'MIMIC-IV Clinical Database', '去标识化住院与 ICU 纵向 EHR，含检验、用药和生命体征等事件。', '凭证访问与数据使用协议', '临床事件与时间戳', '完成课程、申请访问、定义时间窗', '不规则临床预测或策略数据', '时间切分与外部验证', '可用于不规则事件、临床风险预测和 RL 状态构造。', '不是无门槛公开数据；去标识时间与单中心性质限制外推。', 'https://physionet.org/content/mimiciv/', '[第二轮调研 S011](../第二轮调研/report.md)'),
('04_eICU', 'eICU-CRD：多中心 ICU 外部验证资源', 'eICU Collaborative Research Database', '多中心 ICU EHR，可支持跨医院泛化和医院异质性分析。', '凭证访问、课程与 DUA', '多中心临床事件', '申请访问并对齐变量', '按医院/时间切分', '外部泛化与校准', '适合验证从 MIMIC 单中心迁移的模型是否稳健。', '不同医院记录实践不同；不等于社区流感监测。', 'https://physionet.org/content/eicu-crd/', '[第二轮调研 S012](../第二轮调研/report.md)'),
('05_HiRID', 'HiRID：高时间分辨 ICU 不规则时序', 'HiRID: a high time-resolution ICU dataset', '高分辨率 ICU 观察数据，突出不规则采样和密集生理时间序列。', '凭证访问与 DUA', '高频 ICU 观察', '申请访问与变量质量审计', '连续时间/缺失建模', '预测误差与缺失鲁棒性', '适合检验 MIRA 等连续时间模型的医学时间编码。', '访问受限，站点和任务与流感周度预测不同。', 'https://physionet.org/content/hirid/', '[第二轮调研 S013](../第二轮调研/report.md)'),
]
for slug, title, original, abstract, access, n1, n2, n3, n4, project, limits, code, source in datasets:
    write_note('数据集', slug, title, f'- 标题: {original}\n- 获取状态: {access}', abstract, f'该资源解决的是“{title}”的数据可获得性与可复现任务定义问题。', abstract, [(n1, '原始时间序列或事件'), (n2, '访问、许可和质量审计'), (n3, '任务构造与严格切分'), (n4, '指标、版本和复现记录')], '数据集不是模型。关键机制是数据版本、可见时间边界、变量定义和切分规则；这些决定模型结果是否可比较。', '数据集文档提供资源规模或访问状态，而非一篇模型论文的性能排名。使用前应先运行缺失率、时间戳、年龄字段和版本差异审计。', project, limits, code, source)

# Copy first-round curated notes plus their image directories into the new taxonomy.
copy_plan = {
    '时序基础模型': [('08_08_Chronos','01_Chronos'), ('09_09_TimesFM','02_TimesFM'), ('10_10_Lag_Llama','03_Lag_Llama'), ('11_11_Moment','04_MOMENT'), ('19_19_Flusion','05_Flusion')],
    '强化学习_后训练奖惩机制': [('12_12_Sepsis_Deep_RL','01_Sepsis_Deep_RL'), ('13_13_Potential_Reward_Shaping','02_Potential_Reward_Shaping'), ('14_14_Sepsis_Uncertainty_Offline_RL','03_Sepsis_Uncertainty'), ('15_15_InstructGPT_RLHF','04_InstructGPT_RLHF'), ('16_16_Constitutional_AI','05_Constitutional_AI'), ('17_17_DPO','06_DPO'), ('18_18_Doubly_Robust_OPE','07_DR_OPE'), ('20_20_CQL','10_CQL'), ('21_21_CPO','11_CPO')],
}
for category, pairs in copy_plan.items():
    for src, dst in pairs:
        source = root / src
        target = root / category / dst
        if target.exists(): shutil.rmtree(target)
        shutil.copytree(source, target)
        old = next(target.glob('*阅读笔记.md'))
        text = old.read_text()
        text = text.replace('# ', '# ', 1)
        text = text.replace('\n## 核心信息', '\n> **纳入说明**：本条目经过第一轮身份修复后，按实际论文主题纳入本分类；它并不自动证明老年流感预测有效。\n\n## 核心信息', 1)
        old.write_text(text)

print('curated taxonomy generated')
