# 模型补丁第四轮（D154）：TabPFN + LightGBM 平均的增益来源与改进·执行方案（2026-11-08）

状态：已锁定（11-08，冒烟后锁定，锁定文件 `logs/2026-11-08/model_patch_r4_plan_lock.txt`）；改动另立版本。本机 `plans/` 与服务器 `docs/basemodel/plan/week06/` 两处内容一致。

## 0 起因与依据

- **研究者 11-07 的要求：** 每轮完成后深度分析结果，继续调研，设想并实施新的或改进的方法。
- **第三轮（D153）结果**（`result/急诊监督模型/模型补丁第三轮_结果_20261108.md`）：
  - Q4：TabPFN 与 LightGBM 的等权 logit 平均（tabpfn_lgbm）在从未用于评价的 S 集上复现。两库、三个 n 全部"优于" LightGBM：MC-MED +0.0066 到 +0.0104，MIMIC-IV-ED +0.0050 到 +0.0084。它也高于 TabPFN 本身。
  - 跨库先验：对齐后在 MC-MED 上 AUROC 仍只有 0.62–0.64，作偏置会拖累。这条线暂停。
  - TabPFN 的 softmax 温度默认 0.9，会把概率推向两端，对应它校准斜率 < 1、观察/预期比 > 1。平均后的模型部分继承了这一点（MC-MED 观察/预期 1.08–1.18）。
- **还没回答的两件事：**
  1. 增益从哪里来？是 TabPFN 特有，还是任何"第二个模型"平均进来都一样？如果是后者，目标医院可以不依赖 GPU 和 TabPFN。
  2. 等权平均是事先固定的。按小样本内部数据学习组合方式，或者校正温度，能不能更好？
- **检索要点（11-08，基于检索摘要与官方文档，未读全文）：**
  - Jayawardhana 等（arXiv 2502.02672，2025）提出 PFN-Boost：以 TabPFN 的预测作为梯度提升决策树的起点，再用树修正。摘要报告它在除极小样本外的各种规模下表现最好。我们尚未核对它在训练集上如何取 TabPFN 分数；本方案用交叉拟合，避免样本内分数过于乐观。
  - Phillips 等（Int J Epidemiol 2023；arXiv 2204.06139）讨论 super learner 的设定：二分类结局按有效样本量（约为 5 × 少数类例数，以 n 为上限）决定学习器库的大小与交叉验证折数，有效样本量小时宜用更少、更简单的组合。这一条依据二手摘要，公式未核对原文。
    - 本项目 MIMIC-IV-ED n = 1,000 约 55 个事件，有效样本量约 275。所以组合方式只学 1 个权重加 2 个再校准系数，不做多学习器的自由堆叠。
  - TabPFN 官方文档：`softmax_temperature` 越低概率越尖锐；`tuning_config={"calibrate_temperature": True}` 可按留出数据调温度。服务器上的版本也提供每个子模型的原始 logit（`predict_raw_logits`）。
  - McDowell 等（arXiv 2605.21742，2026）：PFN 在类别不平衡数据上偏向多数类，阈值调整和降采样有效。这与本项目 TabPFN 观察/预期 > 1 的方向一致，只作背景。
- **服务器上的核对（虚构数据）：** 用每个子模型原始 logit 的差 z = l₁ − l₀，按 mean(sigmoid(z / 0.9)) 计算，与 `predict_proba` 的最大差 1.2e−7。所以一次 GPU 预测就能得到不同温度下的概率。

## 1 问题

| 编号 | 问题 | 主要比较 |
|---|---|---|
| Q5 | 在小样本内部学习组合方式，能否比等权平均更好？ | stack − tabpfn_lgbm、pfnboost − tabpfn_lgbm；2 库 × 3 个 n，共 12 个 |
| Q6 | 平均的增益是否 TabPFN 特有？ | tabpfn_lgbm − lgbm_bag、tabpfn_lgbm − lgbm_lr；2 库 × 3 个 n，共 12 个 |

- 主要比较共 24 个，一起做 Holm。
- 校准（温度、再校准）放在次要比较里，只做描述。
- **本轮不做：** 换结局或终点；改 n 的网格；改 TabPFN 的 `n_estimators`；微调 TabPFN；跨库先验。

## 2 数据与评价集

- **不变：** 终点、索引时点、窗口、标签、切分、纳排都不变。确认集不读（D111）。
- **抽样与第二、三轮相同：** 沿用 `configs/patch5_small_v1.json` 的目标池、抽样、内部 5 折、LightGBM 网格、LR 的 C 网格、TabPFN 设置。
- **评价集：** 直接用第三轮的 `derived/ed_ts_bench/xfer_r3/main/<库>/eval_features.parquet`，行顺序也相同：
  - MC-MED：S（21,235 次，主要）、disc（8,085 次，次要）；
  - MIMIC-IV-ED：S（40,000 次，主要）、repro（2,000 次，只用于复现核对）。
  - S 集第二次用于评价。本轮问的是新问题，但看过第三轮结果后再用同一集合，结论仍是探索性的（D111）。
- **复现核对：**
  - 本轮重拟合的 lgbm（种子同第三轮）与第三轮预测比较，容差 1e−6。
  - TabPFN 在温度 0.9 下按原始 logit 算出的概率与第三轮比较，容差 1e−5。线程设置与第三轮相同（每进程 BLAS / OpenMP 4 线程），写入锁定文件。

## 3 各臂（每库、每次抽样）

| 臂 | 做法 |
|---|---|
| lgbm | 同第三轮（种子 2026 + r） |
| lgbm_bag | 5 个 LightGBM 的 logit 平均，种子 2026 + r + 1000k（k = 0…4），每个种子各自在内部 5 折上选网格与轮数。k = 0 即 lgbm |
| lr | L2 logistic 回归，C 在内部 5 折上选（第二轮的 `fit_lr`） |
| lgbm_lr | lgbm 与 lr 的等权 logit 平均 |
| tabpfn | 同第三轮（温度 0.9），由原始 logit 计算 |
| tabpfn_t1 | 同一次拟合，温度 1.0 |
| tabpfn_tcal | 同一次拟合，温度在抽样内部按交叉拟合的原始 logit 选：网格 0.50、0.55 … 3.00，取对数损失最小者 |
| tabpfn_lgbm | tabpfn 与 lgbm 的等权 logit 平均（第三轮的 Q4 臂） |
| tabpfn_lgbm_lr | tabpfn、lgbm、lr 三者等权 logit 平均 |
| avg_rcl | tabpfn_lgbm 的 logit 再做 logistic 再校准（截距 + 斜率），系数在交叉拟合的预测上估计 |
| stack | 组合 logit = α · tabpfn + (1 − α) · lgbm，α ∈ {0, 0.1, …, 1}；对每个 α 在交叉拟合的预测上估再校准系数，取对数损失最小的 α，并列时取最接近 0.5 的 |
| pfnboost | LightGBM 以 TabPFN 的 logit 为 `init_score` 提升：训练行用交叉拟合的 logit，评价集用整份抽样拟合的 logit。网格与选法同第二轮 src_lgbm，"不加树"也是候选 |

- **交叉拟合：** 用与 LightGBM 选参相同的内部 5 折。
  - TabPFN：每折用其余 4 折拟合（随机种子同整份拟合），预测该折，记录 4 个子模型的原始 logit。
  - LightGBM：用 k = 0 那次选出的组合与轮数，每折用其余 4 折拟合，预测该折。
- **已知的乐观偏差：**
  - LightGBM 的交叉拟合预测用的是在全部折上选出的组合，常见做法，偏差小。
  - pfnboost 在内部选参时，训练行的起点来自看过验证折标签的 TabPFN。这是二阶泄漏，可能让它略多选树。评价集不受影响。
- 评价集上的预测一律来自整份抽样上的拟合。

## 4 评价

- **指标与统计量：** 同第三轮。AUROC（主要）、AUPRC、Brier、校准斜率、观察/预期；20 次抽样配对差均值；评价集按患者整群 bootstrap（B = 1000，种子 2026）；Holm；"优于 / 差于"需区间不含 0、Holm p < 0.05、≥ 11/20 次抽样同向。
- **主要比较（24 个，S 集）：** 见 §1。
- **次要（只描述）：**
  - 主要比较在 MC-MED 发现集上的同样比较；
  - lgbm_bag − lgbm、lr − lgbm、lgbm_lr − lgbm、tabpfn_lgbm − lgbm、tabpfn_lgbm_lr − tabpfn_lgbm、pfnboost − tabpfn、stack − avg_rcl；
  - tabpfn_t1 − tabpfn、tabpfn_tcal − tabpfn、avg_rcl − tabpfn_lgbm（再校准不改变排序，看的是校准指标）；
  - 各臂的校准斜率、观察/预期、Brier；
  - α、温度、再校准系数的分布；pfnboost 选"不加树"的次数与轮数。
- **读法（看结果前写定）：**
  1. **Q5 中 stack 或 pfnboost 在两库都至少有一个 n"优于"：** 存在比等权平均更好的组合方式。报告哪一种、在哪些 n，作为候选改进交研究者（A 档）。
  2. **Q5 全部"持平"：** 等权平均已经够用。它最简单、没有选择偏差，继续作为候选默认做法。
  3. **Q5 有"差于"：** 在这种样本量下学习组合方式会过拟合，保留等权。
  4. **Q6 两个对照在两库都被"优于"：** 增益需要 TabPFN。
  5. **Q6 某库某个对照"持平"或"优于"tabpfn_lgbm：** 在该库，不用 TabPFN、换一个便宜的第二模型也能拿到相同增益。报告是哪个对照、在哪些 n。
  6. **校准（描述）：** 若 tabpfn_tcal 或 avg_rcl 让观察/预期落在 0.95–1.05、校准斜率落在 0.9–1.1，且 AUROC 不降，就建议在小样本流程中加入这一步。

## 5 冒烟与锁定

- **冒烟：**
  - 每库 2 次抽样，只做 n = 1,000。
  - 评价集用第三轮冒烟的评价集（`xfer_r3/smoke/<库>/`，T 池里冒烟抽样之外的约 2,000 次就诊）。
  - 产物在 `derived/ed_ts_bench/ens_r4/smoke/`，前缀 `SMOKE_`，指标不看。
- **锁定：** 方案、配置、代码、队列脚本、测试的 sha256；所依赖的第二、三轮代码与配置、TabPFN 权重；线程相关环境变量。写入 `logs/2026-11-08/model_patch_r4_plan_lock.txt`。

## 6 计算

- **GPU（先跑）：** 每次抽样 1 次整份 TabPFN 拟合与评价集预测（MC-MED 约 2.9 万行，MIMIC-IV-ED 4.2 万行），另加 5 次折内拟合（每次预测 ≤ 1,000 行）。4 条队列分两张卡。估计约 1 小时。
- **CPU（等 GPU 完成后）：** 每次抽样 5 次 LightGBM 选参、1 次 pfnboost 选参、5 次交叉拟合、1 次 LR 选参。5 个进程，每个 4 线程。估计 20–40 分钟。
- **线程：** 每进程 BLAS / OpenMP 4 线程，与第三轮相同。

## 7 产物

- **代码**（服务器 `W/basemodel/experiments/ed_ts_bench/`）：
  - `patch7_ens.py`：TabPFN 原始 logit 与交叉拟合、各臂；
  - `patch7_ens_eval.py`：评价；
  - 配置 `configs/patch7_ens_v1.json`；队列 `run_patch7_queue.sh`（`gpu <k>`、`cpu`、`eval`）；
  - 测试 `tests/test_model_patch_r4.py`（虚构数据）。
- **逐例数据**（目录 700、文件 600）：`derived/ed_ts_bench/ens_r4/<main|smoke>/<库>/`，内容为 TabPFN 原始 logit（评价集与交叉拟合）、各抽样各臂的预测。
- **聚合输出**（`W/logs/2026-11-08/`）：`model_patch_r4_{per_draw,paired,summary,arm_info}.csv`、`model_patch_r4_meta.json`（含复现核对）、运行日志 `model_patch_r4_{cpu,gpu0–3,eval}.log`。
- **报告：** `docs/实验/模型补丁第四轮_结果_<日期>.md`（服务器 `docs/basemodel/result/week06/`）。
