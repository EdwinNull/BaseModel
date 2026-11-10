# ed_ts_bench 补丁 1：把 ESI 与年龄作为静态输入（执行方案，2026-11-03）

只含聚合量。锁定前写成，锁定后不改；要改就另立新版本。

- 上位：`MC-MED与MIMIC-IV-ED_时序模型子集诊断_本周计划_20261102-1108.md`；第一版执行方案 `ed_ts_bench_执行方案_20261103.md`；子集发现结果第二版 `result/急诊监督模型/ed_ts_bench_子集发现结果_20261103.md` §5
- 决定：D108（研究者 2026-11-03 从结果报告 §5 的候选里选"加 ESI 与年龄输入"）；D109（确认集评价）是草案，待研究者锁定（§6）
- 代码：服务器 `basemodel/experiments/ed_ts_bench/` 的 `static.py`、`tabular_static.py`、`run_seq_static.py`、`patch_eval.py`；测试 `basemodel/tests/test_ed_ts_bench_patch1.py`（虚构数据，6 项）。第一版锁定的文件一个都没改
- 锁定：`logs/2026-11-03/ed_ts_bench_patch1_plan_lock.txt`

## 1 要回答的问题

子集发现第二版显示：MIMIC-IV-ED 上按 ESI、年龄、到达方式分组的校准偏差，五个模型一样大；≥80 岁、急救车送达等子集所有模型都差。一个直接的解释是 D107 只给了 6 项体征，ESI 和年龄都不是输入。

补丁 1 要看：加入这两个静态输入以后，(a) 总体表现，(b) 组内校准，(c) 原来稳定变差的子集，各有什么变化；时序模型和树模型受益是否一样。

## 2 改了什么（D108）

- **输入集 v2 = D107 的 6 项体征 + 年龄 + ESI。** D107 的输入集保留为对照，下文叫"补丁前"。
- **两个库、五个模型都做**（Claude 的执行安排，研究者可改）：MC-MED 用 visits.csv 的 `Age`、`Triage_acuity`；MIMIC-IV-ED 用构建好的 `age`、`acuity`（来自 triage 表）。
- **两个变量在预测时点之前都已知。** MIMIC-IV-ED 的分诊在到院时（窗口第 0 分钟），年龄按到院年份算；MC-MED 的分诊在到床之前。不引入窗口之后的信息。
- **不变的：** 任务口径（D103、`decomp_60`）、切分、发现集与封存（D105）、Platt 再校准（D106）、子集登记表（D104）、超参数、seed、训练循环。

## 3 编码与模型接入（B 档，可复核）

1. **静态向量 7 维：** 年龄按训练集均值、标准差标准化；ESI 1–5 独热编码；另加一列"ESI 缺失"。MC-MED 的年龄已被数据集扰动 ±2 岁，照原样用。
2. **LR、LightGBM：** 7 列接在窗口摘要特征后面，其余设置与补丁前相同。
3. **时序模型用后融合**（静态向量不进序列编码器）：
   - BRITS：拼到前向、后向两个方向的最终隐藏状态后面，再进各自的线性头；
   - mTAND：拼到 GRU 汇总向量后面，再进分类 MLP；
   - Raindrop：先线性映射成 n_features 维，再拼到池化表示后面进 MLP（与 Raindrop 参考代码静态分支的结构相同）。
4. **补丁前后同 seed 是配对的。** 补丁模型先按父类建好再换头，同一 seed 下骨干的初始权重与补丁前完全相同（测试里逐个参数核对过），训练时的打乱顺序也相同。
5. **配置文件沿用。** MIMIC-IV-ED 用 `configs/seq_*_mimic_ed.json`；MC-MED 用 `mp_benchmark_v1/configs/*.json`，输入按 `mp_benchmark_v1.run_model.load_data` 的同一做法构建（只用 Original 观测）。
6. 不调超参数；Raindrop 的轮数上限仍是 30（与补丁前一致）。

## 4 模型与运行

| 模型 | MC-MED | MIMIC-IV-ED |
|---|---|---|
| LR | 1 次（seed 2026） | 1 次（seed 2026） |
| LightGBM | seed 2026–2030 | seed 2026–2030 |
| BRITS / mTAND / Raindrop | seed 2026–2030 | seed 2026–2030 |

共 42 个 run。预测写到 `derived/ed_ts_bench/preds/<task>/<model>_static/seed<seed>/`（目录 700、文件 600），验证集与测试集都存，测试集不算任何指标。

## 5 发现集上的评价（开发用，随本方案锁定）

都在 D105 的发现集上：MC-MED 是验证集 + 测试集 A 半，MIMIC-IV-ED 是验证集。每个 run 在自己的验证集预测上拟合一次 Platt。

1. **子集发现重做。** 补丁后的五个模型走与第一版相同的子集评价和归类（同一登记表、同一判据），看哪些子集不再稳定变差。
2. **配对比较**（同模型、同 seed，补丁后减补丁前），总体和每个子集都算：
   - AUROC 差，按患者聚类 bootstrap 1,000 次（种子 2026，两个 run 用同一组重抽样）给 95% 区间；"提升"指区间下限 > 0，且在过半数 seed 上成立（LR 只有一次，即该次成立）；
   - 校准后 Brier 差，区间做法同上；
   - 补丁前后的观察/预期比，以及 |log(观察/预期)| 的均值（描述性）。
3. **看结果前先写下重点看的格子：**
   - MIMIC-IV-ED：ESI 1–2、ESI 3–5、年龄三组、急救车/直升机送达、密度 × ESI 四格的观察/预期比；
   - 两库原来稳定变差的子集的 AUROC：MIMIC-IV-ED 7 个；MC-MED 的 ≤15、≤15 × ESI 3–5、≤15 × ESI 1–2。
4. **读法。** 在按 ESI、年龄切出的子集内部，ESI 是常数、年龄范围也窄，加入它们主要改善校准和总体排序，组内 AUROC 不一定变。这是预期，不能据此说补丁无效。
5. 发现集不等于确认：MIMIC-IV-ED 的发现集就是验证集，早停也用它，补丁前后都带同样的乐观偏差。

## 6 确认集评价（D109，草案，待研究者锁定；锁定前不做）

封存的确认集只评价一次（D105）。建议如下：

1. **范围：** MC-MED 测试集 B 半；MIMIC-IV-ED 测试集。用已经存好的测试集预测（补丁前后都存了），不重训。
2. **确认的内容：**
   - 补丁前：发现集上稳定变差的子集，在确认集上是否仍然变差（判据同 §5）；
   - 补丁后减补丁前：总体 AUROC、AUPRC、校准后 Brier，以及 §5.3 列出的格子。
3. **主要指标（建议）：** 各模型总体 AUROC 的配对差（95% 区间）；次要指标是 §5.3 格子的观察/预期比和子集 AUROC。
4. **时机要研究者定。** 确认集只能用一次：如果还打算做别的补丁（例如删观测增强），建议在发现集上都做完、选定以后一起确认；补丁 1 单独先确认，之后的补丁就没有干净的确认集了。

## 7 运行命令

```bash
cd /home/ud202482579/wangyiming/basemodel
.venv/bin/python -m pytest tests/test_ed_ts_bench_patch1.py tests/test_ed_ts_bench.py -q -p no:cacheprovider
.venv/bin/python -m experiments.ed_ts_bench.run_seq_static --task mcmed --model brits --mode smoke          # 两库 × 三个模型
.venv/bin/python -m experiments.ed_ts_bench.tabular_static --task mimic_ed --model lgbm --seed 2026           # lr 只跑 2026；mcmed 同
.venv/bin/python -m experiments.ed_ts_bench.run_seq_static --task mimic_ed --model brits --mode train --seed 2026 --device cuda:0
.venv/bin/python -m experiments.ed_ts_bench.patch_eval --task mimic_ed --out-dir ../logs/<日期>                 # mcmed 同
.venv/bin/python -m experiments.ed_ts_bench.report_md --task patch1_mimic_ed --log-dir ../logs/<日期>           # 补丁后的子集表
```

聚合结果写在 `logs/<日期>/ed_ts_bench_subgroups_patch1_<task>_*` 和 `ed_ts_bench_patch1_paired_<task>_*`；结果报告写到 `docs/basemodel/result/week06/`，本机 `docs/实验/`。

## 8 不做的

- D109 锁定前，不在 MC-MED 测试集 B 半、MIMIC-IV-ED 测试集上算任何指标。
- 不调超参数，不加到达方式等其他静态变量。
- 不改 D103–D106。
