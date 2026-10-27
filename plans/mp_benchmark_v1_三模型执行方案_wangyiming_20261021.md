# 观测删减敏感性实验 benchmark v1：BRITS / mTAND / Raindrop 执行方案（wangyiming 部分）

日期：2026-10-21
上位文件：`六模型观测删减敏感性实验_任务说明_正式版.md`（同目录，下称"正式版"）。本文只写王一鸣负责的三个模型怎样落实正式版，不改变正式版的任何口径。

## 1. 不变的口径（直接沿用正式版）

- 数据：只读冻结 benchmark `/home/ud202482579/liangruiying/MC-BEC-Reproduction/outputs/measurement_policy_benchmark_v1/`。2026-10-21 `sha256sum -c DATA_CHECKSUMS.sha256` 8 个文件全部 OK。
- 任务、标签、队列：`manifest_final.parquet` 的 `decomp_60`；train 42,983 / val 5,451 / test 5,236，不删 visit。
- 六项生命体征；输入窗口 0–15 min；不加其他变量。
- 一个模型只训练一次（Original Train），按 Original Validation AUPRC 选 checkpoint 和早停；阈值取 Original Validation 上 F1 最大的点，冻结后用于四套 test。
- 四套 test（original / drop20 / drop40 / continuous5min）由同一个 checkpoint 打分，各自从自己的观测文件重新计算 mask、时间间隔、时间戳和长度。
- 标准化：每个变量用 Original Train 原始观测行的 mean/std，只拟合一次。
- 指标：AUPRC（主）、AUROC、ΔAUPRC、ΔAUROC、Mean/Median/P90 Δp、Flip Rate、Brier；另报 ECE（10 个等宽分箱）。以 CSN 为单位做 paired bootstrap，1,000 次，给出 95% CI。

## 2. 与梁睿颖分支共用的实现（保证六模型可比）

逐字复制她的 `common/benchmark.py`、`common/metrics.py`，来源与 sha256 记在 `experiments/mp_benchmark_v1/common/PROVENANCE.sha256`。因此以下几项与 LSTM/GRU-D 分支完全相同：

- 1 min 网格：`bin = floor(minutes_from_roomed)`，15.0 归入第 15 格；同一格内取均值；无记录保持缺失（只有 BRITS 用网格）。
- 标准化器、队列与标签检查、AUROC/AUPRC/Brier、Δp、Flip Rate、paired bootstrap 的代码。
- 损失函数的类别加权：`BCEWithLogitsLoss(pos_weight = 阴性数 / 阳性数，Original Train)`，与 LSTM 分支相同。
- 阈值选择：在验证集全部不同概率值上穷举 F1。
- bootstrap 随机种子固定 2026，使各模型、各训练 seed 的重采样下标相同。

## 3. 三个模型的输入表示与结构

| | BRITS | mTAND | Raindrop |
|---|---|---|---|
| 输入表示 | 1 min 网格 16×6，mask，时间间隔 δ（分钟）；正向和时间反转两套 | 每个 visit 自己的不同观测时间戳（不网格化），值 + mask，时间按固定窗口缩放 t/15 | 每个 visit 自己的不同观测时间戳（不网格化），补齐到 max_len = Original Train 中每个 visit 不同时间戳数的最大值（实测 21），位置编码用分钟 |
| 缺失 / 不规则机制 | 双向 RITS 插补（历史回归 + 特征回归 + 衰减）与分类联合学习 | 多时间注意力：从观测时间点到 128 个固定参考时间点 | 观测传播 + 时间位置编码 + Transformer，按真实长度做掩码均值池化 |
| 实现 | PyPOTS 1.5 `BackboneBRITS` 原样调用，加两个方向各一个线性头；概率取两方向均值 | 按 mTAND 参考代码 `multiTimeAttention` + `enc_mtan_classif`（mTAND-Enc）移植 | 按 PyPOTS 1.5 `BackboneRaindrop` 写成批量纯 PyTorch 版（见 §4.3） |
| 主要超参数 | hidden 64；重构权重 0.3；一致性损失 0.1 | hidden 256，embed_time 128，1 头，128 个参考点，MLP 300-300 | d_ob 4（d_model 24），d_pe 16，2 层 2 头，FFN 48，dropout 0.2 |
| 优化 | Adam，lr 1e-3，batch 64 | Adam，lr 1e-4，batch 50 | Adam，lr 1e-4，batch 128，ReduceLROnPlateau（按验证 AUPRC，factor 0.1，patience 1） |
| 训练预算 | 最多 30 epoch，patience 6（与 LSTM 分支相同） | 同左 | 同左 |

超参数取各方法论文或参考代码的常用设置，不在本数据上调参。正式版允许用 Original Validation 调参，这里不调，以减少选择路径。

## 4. 需要研究者知悉的实现决定（B 档，可复核）

1. **类别不平衡**：三个模型都用 pos_weight 加权 BCE，与 LSTM 分支一致，没有用各方法原有的处理（Raindrop 原版是上采样阳性，BRITS、mTAND 原版不加权）。pos_weight 会把预测概率整体推高，因此 Brier、ECE 会偏差，Δp 的绝对大小也受影响。六模型统一口径时需要一起确认。
2. **mTAND 变体**：用判别式 mTAND-Enc，不用带 VAE 重构的 mTAND-Full。参考代码按每个 batch 的最大时间归一化时间，那样一个 visit 的预测会受同 batch 其他 visit 影响，破坏配对比较，所以改为固定窗口 t/15。
3. **Raindrop 的图结构实际是退化的**：PyPOTS（以及其所移植的官方 `Raindrop_v2`）调用观测传播层时用 `use_beta=False`、全连接传感器图、边权全为 1。逐行推导后，该层的消息就是 `relu(lin_value(x_i))`，对入边的 softmax 权重求和恰好等于 1，所以变量之间实际不传递消息，时间位置编码在这一层也不起作用。变量之间的关系只通过 Transformer 中每个时间点拼接的 24 维表示间接建模。本实现按原样复现这一点（不自行"修好"），用批量运算代替逐样本循环；单元测试 `test_dense_raindrop_matches_pypots_backbone` 用 PyPOTS 原版（测试专用的 torch_geometric，装在 `_pyg_ref/`，不进共享 venv）对比池化表示，误差 < 1e-5。论文或 PPT 中描述 Raindrop 为"建模变量间关系"时，需要说明这一实现层面的事实。
4. **BRITS 是离线双向模型**：用到了 0–15 min 窗口内的"未来"观测（窗口内），符合正式版 §14 固定 landmark 的离线设定，不能表述为在线预测。
5. **Raindrop 的 max_len 只由 Original Train 决定**（21）；val、test 的最大长度为 18，都没有超出。代码规定若超出就报错，而不是截断。
6. **batch 无关性**：三个模型在推理时，单个 visit 单独预测与放进 batch 中预测，结果之差 ≤ 2e-6（冒烟测试中实测），所以 Δp 只反映该 visit 自身输入的变化。

## 5. Seed 计划

- 主结果：training seed 2026（正式版最低要求）。
- 预登记附加 seed：2027、2028（正式版第三优先级）。三个模型都很小，在 seed 2026 完成后直接跑；每个 seed 单独报告，不挑 seed。若因故没跑完，结果标注为 pilot single-seed experiment。

## 6. 产物位置

- 代码：`basemodel/experiments/mp_benchmark_v1/`（`run_model.py`、`engine.py`、`inputs.py`、`models/`、`configs/`）；测试：`basemodel/tests/test_mp_benchmark_v1.py`。
- 逐患者产物（`best_model.pt`、`pred_val_original.csv`、`pred_{original,drop20,drop40,continuous5min}.csv`、`scaler.npz`）以及 `run_config.json`、`results.json`、`bootstrap_results.json`、`validation_threshold.json`、`training_log.csv`：`basemodel/derived/mp_benchmark_v1/<model>/seed<seed>/`（目录 700、文件 600）。文件名与 JSON 结构同 LSTM 分支。
- 日志：`logs/2026-10-21/mp_<model>_seed<seed>.log`；方案锁：`logs/2026-10-21/mp_benchmark_v1_plan_lock.txt`。
- 结果报告（只含聚合量）：`docs/basemodel/result/week04/`。

## 7. 运行命令

```bash
cd /home/ud202482579/wangyiming/basemodel
.venv/bin/python -m pytest tests/test_mp_benchmark_v1.py -q -p no:cacheprovider
.venv/bin/python -m experiments.mp_benchmark_v1.run_model --model brits --mode smoke
.venv/bin/python -m experiments.mp_benchmark_v1.run_model --model brits --mode train --seed 2026 --device cuda:0
```

`--mode train` 在目标目录已有 `pred_original.csv` 时拒绝运行，确保四套 test 只评价一次。

## 8. 10-22 追加：与梁睿颖分支对齐（研究者决定）

研究者（王一鸣）2026-10-22 决定以下四项。登记在运行之前；代码、配置、超参数、阈值规则、训练预算都不变（sha256 与 10-21 锁定一致）。

1. **seed 与 LSTM / GRU-D 分支完全对齐**：追加 training seed 2029、2030，三个模型各 2 个 run，共 6 个。seed 2026–2028 的结果保持不变，不重跑。汇总改为 5 个 seed 的 mean ± SD（ddof=1）；seed 2026 仍是带 bootstrap CI 的主结果。
2. **汇总表与梁睿颖 `aggregate_five_seed.py` 同格式**：`five_seed_all_results.csv`、`five_seed_mean_std.csv`、`policy_shift_degradation_five_seed.csv`、`paired_seed_model_comparison.csv`、`five_seed_sanity.json` 的列名、变体名和计算公式都与之相同（AUROC、AUPRC、Brier 用 sklearn；|Δp| 取绝对值；Correlation 为 Pearson；Flip Rate 按冻结阈值、`>=` 判定）。模型名写 BRITS、mTAND、Raindrop。只读对方已经生成的聚合 CSV，不读对方的逐患者预测。
3. **模型间比较统一为"按 seed 配对的差值"**（沿用对方方法，扩大覆盖）：对每个 seed、每种扰动，计算 Δ指标(模型) − Δ指标(FF-LSTM)，指标为 ΔAUROC 和 ΔAUPRC；覆盖 drop20、drop40、continuous5min 三种扰动和所有已完成的模型；报告 5 个 seed 的 mean ± SD，以及差值 < 0 的 seed 数。另按对方 `condition` 的定义，统计每个模型相对 FF-LSTM"原始更强、且同一扰动下 AUROC 与 AUPRC 都下降更多"的 seed 数。n = 5，不做显著性检验。该方法经梁睿颖确认后用于六模型汇总。
4. **校准口径**：v1 不改，所有 Brier、ECE、ΔBrier 标注"pos_weight 加权口径下"。是否登记 v1.1（在 Original Validation 上六个模型统一再校准）由研究者与梁睿颖商定后再做，本次不运行。

运行：`run_seeds.sh` v3 只把日志目录改为按运行当天日期（`logs/2026-10-22/`），其余不变。汇总 CSV（只含聚合量）放 `docs/basemodel/result/week04/mp_benchmark_v1_five_seed_summary/`。
