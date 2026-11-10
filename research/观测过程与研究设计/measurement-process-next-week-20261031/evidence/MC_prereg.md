# B10 预注册（观测过程 benchmark 方案 §8）—— 运行前登记，运行后不改

登记时间：2026-09-11（正式拟合前）。卡片目录：`12_b10`。
上游冻结定义全部沿用 `ds_common.py` 再导出的 Wave6 契约，本卡片**不改变**任何 A 档量。

## 1. 预注册假设与证伪条件

- **H-B10**：`OP_ReTAMamba` 相对参考模型 `OP_GRUD_ED` 在 `dense` 或 `term20` 上
  存在 `> +0.005` 的 AP 增量，且在 `term20` 上无额外大幅退化。
- **主对比**：`G = AP(OP_ReTAMamba, c) − AP(OP_GRUD_ED, c)`，`c ∈ {dense, term20}`，
  2 任务 × 2 条件 = **4 项，同一 Holm 族 `F10_primary`**。
- **实质阈值**：`±0.005`（`TOST_MARGIN`）。正向 / 超实质界 / TOST 等价三栏分列，
  全部走 `verdict_round3.analyse_v3` 的 §2 更正口径。
- **证伪**：两条件均通过 `±0.005` TOST 等价 → 记「该适配未见实质增益」；
  若额外收益只在预处理不一致或输入支持域不一致下出现，不得记为方法收益。
  不得据单个最大 seed 立论（主效应点估计为 5 seed 的 AP 差均值）。

## 2. 臂（模型）与拟合数

| 臂 | 作用 | 训练条件 | 评估条件 | 拟合数 |
|---|---|---|---|---:|
| `OP_GRUD_ED` | 预定参考模型（GRU-D 组件 + 独立 ED 头） | dense | dense, term20 | 20 |
| `OP_ReTAMamba` | 首选近期方法（2h 短窗适配） | dense | dense, term20 | 20 |
| `OP_ReTAMamba_identityGate` | 恒等 gate 机制消融 | dense | dense, term20 | 20 |
| `OP_ReTAMamba_obsOnly` | 同支持域消融（只喂真实观测事件） | dense | dense, term20 | 20 |

`2 任务 × 5 seeds = 10` 每臂。核心主对比只需前两臂（方案 §8 的 30 次下限由
`3 模型版本 × 2 任务 × 5 seeds` 满足；第 4 臂是登记过的同支持域消融，
不构成新的选择自由度）。全部沿用 dense 训练，**不做 tail20 重训**（那是 B8 的问题）。

- 探索族 `F10_gate`：`identityGate − ReTAMamba` 在 2 任务 × 2 条件 = 4 项，
  **另列一族**，只作机制归因，不替代整体模型比较。
- 探索族 `F10_support`：`obsOnly − ReTAMamba` 同上 4 项，另列一族。
- 除以上三族外不新增任何比较；不因结果补阈值、不换主强度、不加臂。

## 3. 统一数据契约（两编码器完全一致）

**C1 数值视图：1 min 网格，121 槽 × 4 通道（HR/RR/SpO2/Perf）**（方案 §8 逐条落实）

- 槽 0 = `Arrival_time`（`index_time`）时刻；槽 `j (1..120)` = `(j−1, j]` 分钟窗；
  末槽右端即 `t_w = index_time + 120 min`。
- 同槽多点取**该槽内最后一条真实值**，并**另存该槽真实点数** `CNT`（不声称保留槽内全部动态）。
- 只读取 `真实记录时间 ≤ t_w` 的 Monitor 行；`raw_row_id` 全程留存仅作追踪。
- `M[t,c]=1` 当且仅当该槽有 ≥1 条真实观测。LOCF 填充的 carry-over 值 `M=0`，
  与「纯 padding」无关：网格对每例恒为 121 槽，**不存在 batch 维 padding**。
- `DT[t,c] = t − t_last_real,c`（分钟）；该通道此前无真实观测时取 `t − 0`（自到达槽起算）
  并保持 `M=0`。此约定在运行前固定，不凭结果更换。
- 网格化是**表示变换**：原始行 ID 与 native 审计量（N/S/R）一并留存，不覆盖 native 口径。

**背景块 `B = C0 + NUM + O_core_v2 + R`**（与 B9 的 `B` 同一列定义、同一实现）

- `NUM`、`M`、`O_core_v2`、`R` 全部由**同一个 retained 视图**重算（方案 §8 第 188 行）；
  `dense` 与 `term20` 各自的背景来自各自保留的行集合。`native` 仅作审计，不入任何受损模型。
- C0 在两条件间逐元素一致。scaler **只在 dense train 上拟合一次**并冻结，
  term20 为 shift 推理（不允许临时添列、不允许在受损视图上重拟合）。

**干预 `term20`**：与 B8 完全同一实现（`phase_b8.sim_mask`，
删除所有满足 `(t_w−20, t_w]` 的真实 Monitor 行；rng 种子 `zlib.crc32(cond)`），
不引入第二种末端缺口定义。本卡片不删除 C3。

## 4. 模型准入与适配登记（待签方案，不声称数据已支持最优）

`OP_ReTAMamba` 候选适配（相对论文 48h 默认值的偏离全部在此列明）：

| 项 | 论文默认 | 本卡片固定值 | 理由 |
|---|---|---|---|
| `max_hour` | 48.0 | **2.0** | `t_w = index+120min`；时刻归一化随之为 `[0,2]h → [−1,1]` |
| `temporal_scales` | `"60,120,240"` | **`"5,15,30"`** | 2h 下才有多尺度；原尺度仅 `2+1+1=4` 槽 |
| 聚合槽数 S | 84 | **`24+8+4 = 36`** | 与方案 §8 第 185 行一致 |
| `token_budget` | 32 | **16** | 32 ≥ 4 会旁路 router；16 < 36 才检验真实激活 |
| L（网格事件数） | 48×17 | **121×4 = 484** | 同一 1 min 网格喂两编码器 |
| `tokenization_mode` | dense | dense（`obsOnly` 臂为 observed_only） | 见 §2 第 4 臂 |
| `pool_type` / `use_weaving` / `scale_drop` | last / False / 0.0 | **attn / False / 0.0** | 与模型.py 默认一致；weaving 关闭 |
| PCA | 无 | **无** | 本路径不含 PhysioStack 的 PCA 问题，不混淆两模型 |
| `keep_first_last` | False | **False** | 不因边界强制保留而虚增增益 |

- **`mamba_ssm` / `causal_conv1d` 在本机不可安装**（无外网、无 `nvcc`）。
  已登记的执行偏差：`MambaBackbone` 的 selective-SSM 用等价的纯 PyTorch 递推实现
  （零阶保持离散化 `ΔA=exp(Δ·A)`、`h ← ΔA·h + ΔB·x`、`y = C·h + D·x`），
  `causal depthwise conv1d` 用 `F.conv1d` + `groups=d_inner`。
  该实现以合成序列与 `selective_state_update` 逐步对照验收，**不声称复现作者 CUDA 内核的
  数值位级一致**，只声称同一离散化语义。
- 恒等 gate 消融：`decay_mode="fixed", fixed_decay=0.0` ⇒ `rel = m + (1−m)·1 = 1`，
  即**相同位置支持上权重恒为 1，其余模块不变**（方案 §8 第 189 行）。
  注意 `use_rel_gate=False` **不是**恒等权重（它是 0/1 硬 mask），故不用它做恒等消融。
- `use_dt_emb=True` 保持默认。因此本卡片**只**能说「无 dt embedding」意义上的差别，
  不得把 identityGate 臂称作「无最新性」。
- 论文默认 `train.py` 的 HPO 结果（lr / weight_decay / dropout 等）不照搬：
  两编码器使用**相同且小**的统一预算（§5），不各自搜参。

`OP_GRUD_ED` 构成（使用已核对的 `MultitaskTransportability/models/RNN/grud.py` 的 GRU-D 组件）：

- `GRUDCell` 逐式沿用：`decay = exp(−clamp(Linear(Δt), 0, 1000))`；`h ← h·decay`；
  标准 GRU 更新 `ñ = tanh(i_n + r⊙h_n)`，`h' = ñ + z⊙(h − ñ)`。
- 输入为**同一** 1 min 网格：`input = X`（LOCF），`ie = DT`（每通道自上次真实观测的时间），
  `length = 121`。读出固定取第 120 槽（即 `t_w`）的隐状态 —— 不继承 survival 目标、
  不使用下一观测作为标签、不使用 `ie_to`。
- 源码事实一并登记：仓库内 `GRUD` 的 `num_layers` 参数被保存但**未堆叠**（单层单向），
  且其 `mask` 入参未参与计算。本卡片沿用单层语义，不擅自加深（属方法变更需另注册）。

## 5. 统一训练/评价协议

- seeds `{0,1,2,3,4}`（`D.SEEDS`），`D.seed_at(seed)` 派生 python/numpy/torch 三类随机源；
  覆盖 `param_init / dropout / batch_order / pos_weight_seed`。
- 两编码器**同一** 网格批、同一 batch=256、同一 `epochs≤40` 与 `patience=5`、
  同一 `lr=1e-3`、`weight_decay=1e-5`、`BCEWithLogitsLoss(pos_weight=train 比值)`。
- 融合头对两编码器**逐维一致**：编码器输出投影到 `d_emb=64`，
  背景 `Linear(n_static, 64)+tanh`，LayerNorm 后 `Linear(128, 96)+ReLU+Dropout(0.3)+Linear(96,1)`。
- 选点：仅按 **train 内部** 的 AP 早停（train 20% 分层切出的内部 early-stop 子集），
  **不使用 val 选 epoch**；val 只做一次性读出。理由：同一 val 已被多轮卡片反复使用，
  本卡片不再向 val 索取模型选择自由度。`best_state` 快照不被后续训练覆盖，
  回载后必须复算出同一指标（验收 g8）。
- 主指标 `average_precision_score`（与既有评价器同一口径，不与梯形 PR 积分混用）；
  次指标 AUROC、Brier、ECE(10 bins 固定边界)、校准斜率。
- 效应点估计 = 原样本上 5 seed 的 AP 差均值；每族 10,000 次配对 bootstrap，
  所有臂、条件、seed 共用同一重采样索引；visit 为主、MRN 聚类为次。
- **test 全程封存**：`SPLITS_USED = [train, val]`，任何入口不得解析 test 路径。

## 6. 验收（正式拟合前必须全绿，失败即中止对应模块）

`accept_b10.py --stage pre`，逐项实跑并写 `acceptance_b10.json`：

| 门 | 内容 |
|---|---|
| g1 | 未来信息不变性：篡改 `t_w` 之后的 Monitor 行不改变任何网格值、背景列与分数 |
| g2 | 视图外信息不变性：term20 被删行改写不影响 retained 网格与 train-fit 统计 |
| g3 | train-fit 边界：改 val 极值不改变 dense scaler / 背景统计 |
| g4 | 缺失语义：`M=0` 的 LOCF carry 与 `M=1` 刚观测可区分；mask 不是数值 0 的别名 |
| g5 | padding/batch 独立性：换 batch 大小与行序，逐 CSN 分数在 `1e-5` 容差内不变 |
| g7 | 模块消费：改 DT 或抹掉 M 必须改变 ReTAMamba 分数；恒等 gate 与正常 gate 分数必须不同 |
| g8 | checkpoint：best 快照回载复算同一 AP |
| g9 | 身份追溯：列、模型、预处理、队列、标签、view、split、seed 与 code hash 可追溯 |
| g10 | test 封存：删除 test 路径仍可完成 train/val；开发入口不可读取 test |
| g11 | router 真实激活：日志确认实际输入 token 长度与选中数量（`<S`），否则不得作任何 router 结论 |
| g12 | SSM 参照一致性：纯 PyTorch selective-SSM 与独立写法的逐步递推在 `1e-5` 内一致 |

## 7. 停止条件

- 队列/标签 hash 与 `cohort_manifest` 不一致；某臂 val 患者集合与其余臂不同；
- 网格或背景出现 `t_w` 之后的信息；term20 干预未改变任何样本却继续解释机制；
- 两编码器输入支持域不一致却宣称「同一数据视图」（须由 g11/`obsOnly` 臂定位）；
- GPU 账本达到剩余额度与 8 GPU·h 的较小值。

## 8. 已知限制（运行前登记）

1. 所有结论仍属**探索性**：同一 val 已被 B1–B9 反复使用；本卡片不打开 test。
2. 纯 PyTorch SSM 与作者 CUDA 内核的位级差异未量化（只保证同一离散化语义）。
3. `{5,15,30}` min 尺度与 `budget=16` 是**首个工程配置**，不是最优性声明。
4. `OP_GRUD_ED` 是「已核对 GRU-D 组件 + 本项目 ED 头」的组合体，
   不等价于任何论文里报告的完整模型；原 M4/M5 不改名、不重跑。
5. 1 min 网格化会抹平槽内动态；`CNT` 只记点数不记抖动。
