# ed_ts_bench 执行方案：MC-MED 与 MIMIC-IV-ED 的基线与子集发现（2026-11-03）

只含聚合量。锁定前写成，锁定后不改；要改就另立新版本。

- 上位计划：`MC-MED与MIMIC-IV-ED_时序模型子集诊断_本周计划_20261102-1108.md`（本目录；服务器 `docs/basemodel/plan/week06/`）
- 决定：D103–D107（研究者 2026-11-03"按建议锁定"；计划 §8，服务器 `docs/basemodel/plan/week02/研究者决策记录_20261005.md`）
- 代码：服务器 `basemodel/experiments/ed_ts_bench/`；测试 `basemodel/tests/test_ed_ts_bench.py`（虚构数据，20 项）
- 锁定：`logs/2026-11-03/ed_ts_bench_plan_lock.txt`

## 1 要回答的问题

在两个急诊任务上，LR、LightGBM 与 BRITS、mTAND、Raindrop 在哪些预先登记的子集上明显比补集差？表现差是所有模型共有（子集本身难），还是只有时序模型差（可以考虑给模型打补丁）？

本方案只做**发现**。补丁和它的确认评价另立方案。

## 2 数据

| | MC-MED | MIMIC-IV-ED |
|---|---|---|
| 来源 | 冻结的 `measurement_policy_benchmark_v1`（只读，与 `mp_benchmark_v1` 相同），只用 Original 观测 | `build_mimic_ed.py` 按 D103 构建到 `derived/ed_ts_bench/mimic_ed_d103/` |
| 任务 | `decomp_60`：到床后 0–15 min → 之后 60 min 失代偿 | 到院后 0–2 h → 之后 12 h 内进 ICU 或院内死亡 |
| 变量（D107） | HR、RR、SpO₂、SBP、DBP、MAP | HR、RR、SpO₂、SBP、DBP、体温（°F） |
| 切分 | benchmark 原切分 42,983 / 5,451 / 5,236 | subject_id 哈希 8:1:1 |
| 发现集（D105） | 验证集 + 测试集 MRN 哈希 A 半（`datasets.mrn_half`，盐 `ed_ts_bench_mcmed_confirm`） | 验证集 |
| 封存 | 测试集 B 半：本方案不在上面算任何指标 | 测试集：保存预测，不算任何指标 |

## 3 模型

| 模型 | MC-MED | MIMIC-IV-ED | 设置 |
|---|---|---|---|
| LR | 新训，1 次 | 新训，1 次 | 窗口摘要特征（下文）；训练集中位数插补 + 缺失指示 + 标准化；L2，C=1 |
| LightGBM | 新训，seed 2026–2030 | 新训，seed 2026–2030 | 学习率 0.05，31 叶，min_child_samples 50，行列采样 0.8，最多 3,000 棵，验证集平均精度早停 100 轮 |
| BRITS / mTAND / Raindrop | 用 10-21/10-22 已训练的 5 个 seed（`derived/mp_benchmark_v1/`） | 新训，seed 2026–2030 | 超参数与 MC-MED 相同（`configs/seq_*_mimic_ed.json`）；训练循环与模型类直接复用 `mp_benchmark_v1`（验证集 AUPRC 早停、pos_weight 加权 BCE） |
| FF-LSTM / GRU-D | 梁睿颖已有结果，等她用同一脚本出子集表 | 等梁睿颖（计划 §10 第 6 问） | — |

窗口摘要特征：每个变量取窗口内末值、均值、最小、最大、次数、末次观测到窗口末的分钟数；从未观测的变量值为缺失、次数为 0。

## 4 评价

1. 每个 run 在自己的验证集预测上拟合一次 Platt 再校准（D106），用于发现集。
2. 发现集总体：AUROC、AUPRC、原始与校准后的 Brier。
3. 子集（D104，`configs/subgroups_*_v1.json`）：年龄、性别、ESI 1–2 / 3–5、到达方式、呼吸系统主诊断、观测密度（训练集三分位）、密度 × ESI。子集与补集都至少 30 个阳性、子集至少 30 个阴性才报指标。
4. 子集减补集的 AUROC 差和校准后 Brier 差；按患者（MRN / subject_id）聚类 bootstrap 1,000 次，种子 2026，95% 区间。
5. **"表现差"**：AUROC 差的 95% 区间上限 < 0，且在该模型过半数的 seed 上成立（LR 只有 1 次，即该次成立）。
6. **归类**（计划 §6.2），以 LightGBM 为树模型参照：
   - LightGBM 与所有时序模型都差 → "所有模型都差（含树模型）"；
   - LightGBM 不差、至少一个时序模型差 → "树模型不差、时序模型差"；
   - 其余情况按实际组合写出。

## 5 需要研究者知悉的实现决定（B 档，可复核）

1. **MIMIC-IV-ED 去掉不合理值**：HR 1–300、RR 1–80、SpO₂ 1–100、SBP 20–300、DBP 5–250、体温 77–113 °F 以外的值在构建前删除（核查报告 §4.3 已列出行数）。因此纳入人数会比核查时的 387,249 略少。
2. **BRITS 在 MIMIC-IV-ED 上用 5 分钟网格**（2 h 共 24 步），时间间隔以分钟计；MC-MED 是 1 分钟网格 16 步。2 h 内中位只有 1–2 个时点，1 分钟网格 120 步几乎全空，训练慢 5 倍。
3. **类别不平衡**：LR、LightGBM 不加权；时序模型沿用 MC-MED 的 pos_weight 加权。两者都在验证集上 Platt 再校准，所以 Brier 可以比较；pos_weight 的原始 Brier 会偏差，只作附表。
4. **Raindrop 的 max_len** 取训练集单次就诊最多的不同时点数；验证集或测试集超出时报错，不截断（与 10-21 方案相同）。
5. **验证集上的 Platt 是样本内拟合**：MIMIC-IV-ED 的发现集就是验证集，校准后 Brier 偏乐观，但对各子集一视同仁；AUROC 不受影响。
6. FF-LSTM、GRU-D 的 MIMIC-IV-ED 结果和 MC-MED 子集表要等梁睿颖，本方案先不含。

## 6 运行与产物

```bash
cd /home/ud202482579/wangyiming/basemodel
.venv/bin/python -m pytest tests/test_ed_ts_bench.py -q -p no:cacheprovider
.venv/bin/python -m experiments.ed_ts_bench.build_mimic_ed
.venv/bin/python -m experiments.ed_ts_bench.tabular --task mcmed --model lr --seed 2026          # lgbm 跑 2026–2030；mimic_ed 同
.venv/bin/python -m experiments.ed_ts_bench.run_seq --model brits --mode smoke                    # mtand、raindrop 同
.venv/bin/python -m experiments.ed_ts_bench.run_seq --model brits --mode train --seed 2026 --device cuda:0
.venv/bin/python -m experiments.ed_ts_bench.run_subgroups --task mcmed                             # mimic_ed 同
```

- 逐例产物：`derived/ed_ts_bench/`（`mimic_ed_d103/`、`preds/<task>/<model>/seed<seed>/`），目录 700、文件 600。
- 日志与聚合表：`logs/<日期>/ed_ts_bench_*`。
- 结果报告（只含聚合量）：`docs/basemodel/result/week06/`，本机 `docs/实验/`。

## 7 不做的

- 不在 MC-MED 测试集 B 半、MIMIC-IV-ED 测试集上算任何指标。
- 不调超参数，不换任务口径；同一判据连续两次操作化失败就停下来报告。
- 不实现补丁。
