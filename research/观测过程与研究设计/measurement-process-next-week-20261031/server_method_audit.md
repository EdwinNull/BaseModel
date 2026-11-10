# 服务器方法与结果审计

日期：2026-10-31。只读核验已有聚合报告、决策记录与代码；未训练、未读取患者级内容。路径相对 `ud202482579@202.114.0.141:/home/ud202482579/wangyiming/`。由只读审计代理核验，主代理据其审计记录落盘。行号为本轮快照位置。

## 关键结论与定位

| 来源 | 核验位置 | 发现及限制 |
|---|---|---|
| `docs/basemodel/result/week02/B1v2_MIMIC逐小时队列重建与泄漏审计_20261004.md` | 41、50、104–105、112、124、165 | 37,252 landmarks/6,023 stays/5,531人；Y24 3,453阳性；患者切分3,877/549/1,105；2020–2022已在随机train/val/test中；早期landmark包含ICU前回看时段。泄漏检查通过不替代口径复核 |
| `docs/basemodel/result/week02/V2_eICU队列与逐小时视图_20261005.md` | 25、55、72 | 64,338 landmarks/9,923 stays/9,398人/195院；36 tune/159 eval；26名患者跨侧；Y24代理/来源并非完全相同 |
| `docs/basemodel/result/week02/F2_冻结嵌入转重风险_验证集_20261004.md` | 242、267、282–283、296、307 | ≥65岁分析，手工LGBM MIMIC AP .319/AUROC .755，eICU AP .201/AUROC .715；12冻结嵌入外部ΔAP −.013至−.054；计数协调大幅改善LR；医院难分类不意味着风险迁移好 |
| `docs/basemodel/result/week02/F3_观测密度压力测试_验证集_20261004.md` | 171、191、201 | L0→L4，LR AP .271→.174，LGBM .319→.208，主TSFM探针 .319→.215；原“稀疏时优势消失”的H-F3未成立；matched/mismatched有代价 |
| `docs/basemodel/result/week02/AL1_GAM-GD分布偏移与协调_20261004.md` | 31、40、49、66、102 | 记录过程医院AUROC .96–.97，时间精度1；年龄定义也暴露医院；协调需折内拟合；域可分不等于有害 |
| `docs/basemodel/result/week02/AL4_无监督域适应基准_跨中心与跨年龄_20261005.md` | 21、56、71、104、125 | target无标签包括eval；≥65岁eval source+Platt AP .128、DSAN .169、TENT .116，弱于F2强树 .201；校准标签预算不对称；弱CNN骨干，属于直推适应 |
| `docs/basemodel/result/week02/P1_测试集评价_MIMIC与eICU_20261005.md` | 22、25、47–48、60、95、97、131 | 48h上下文→12h轨迹；eICU部分变量大量缺失；患者bootstrap/Holm；点误差奖励coverage .09–.13，proper约.773；RL较SFT源WQL改善约.4%，外部无明显附加收益；事件奖励未评价 |
| 本地 `result/观测过程建模/mp_benchmark_v1_三模型结果报告_wangyiming_20261021.md` | 6、319–335 | §12为5seed，前文仍3seed；drop40五模型ΔAP −.016/−.036/−.033/−.024/−.024；BRITS continuous5min −.011；15run原始Brier .183–.231，常数参考 .106；seed波动不等于样本bootstrap区间 |

## 代码接口与输入边界

以下相对服务器 `basemodel/`。

| 文件 | 行 | 作用/审计结果 |
|---|---:|---|
| `experiments/public_thour_v2/views.py` | 65、85、98、121 | 24h回看；capped ffill；原始mask；值摘要、n_obs、hours_since_last、missing和静态特征 |
| `experiments/fc_bench/f2_probe.py` | 40–43、46、60 | 只删10通道数值摘要，保留M/化验/静态特征；PCA源train拟合；LR选C、LGBM5seed。F2并非P-only/M-only实验 |
| `experiments/fc_bench/f2_external.py` | 107、200、248 | 原记录数改观测小时数；tune标签拟合Platt用于eval |
| `experiments/fc_bench/f2_controls.py` | 62、81 | GRU/TCN/GRU-D框架 |
| `experiments/rw_gam2gd/evaluate.py` | 86、99、120 | 等频10箱ECE、风险指标、传入groups的聚类配对bootstrap |
| `experiments/mp_benchmark_v1/inputs.py` | 59、76 | 网格/不规则输入；每变体重算mask/gap/length |
| `experiments/mp_benchmark_v1/engine.py` | 65、93、97–98、145 | 等宽10箱ECE；Original Val AP选checkpoint；pos_weight=(N−pos)/pos；Original Val选F1阈值后冻结 |
| MC-MED `common/metrics.py` | 26–36 | 实际按CSN行bootstrap，标题patient-level不准确；重复就诊应按患者处理 |
| `experiments/align_bench/al4_uda.py` | 188、200、210、220、240、381、398 | UDA/TENT均用全部target含eval无标签X；source-only参照用tune标签Platt；患者bootstrap不涵盖医院抽样不确定性 |
| `experiments/common_eval/forecast.py` | 115、150 | WQL/CRPS/coverage与患者聚类；不能当Y24分类评价 |

F2校准有logit截断且斜率未约束正，不能笼统说所有校准保持排序。P2中AP代理校准后排序变化的疑点尚未进一步核实，不作定论。

## 医院数据与旧A4

本地 `docs/数据标准/数据集说明/数据集说明书_Healthsheet_v0.1_20261031.md`：3/49行为std_v3_20261031_5；109行主分析GD355/GAM129；177行O1候选事件23/10；87/188行人工review=0；94行GD医嘱与GAM护理文字来源差异；131行中心/流感季混杂；139行为住院预测时点t0+24h与时间类型；189行标签规则改变使GD基线重症比例91%→56%，反映操作定义敏感。

本地 `result/医院队列与终点/A4桥接_只用编码队列重跑_结果_20261030.md`：80行包含未链接stay按阴性、E0′同名不同义、仅首日体征、旧对齐等限制；86行两院已评价三次。旧A4仅作探索和版本比较，不是最新标准化数据的正式外部验证。

## 对后续研究的直接影响

冻结任务、标签、输入、环境、信息使用与统计单位；以同库多医院为主要试点。数值摘要臂不能叫纯生理；随机删不能代表真实换院全部因果效果。先用强表格对照和一套序列模型，报告支持、信息损失、原始概率评分与校准。Y24按通气/升压药/死亡拆分；GD/GAM用于来源、时间与标签审计；P1/RL与扩嵌入库不设为主论文必需。

本审计没有独立重跑已有指标。汇总数字为报告结果；代码核查支持其输入/指标/选择规则解释，不能取代数据与结果的完整可复现验证。
