# 一次性官方 test 评价：冻结方案与预写判定（TEST_PREREG）

| 项 | 值 |
|---|---|
| 日期 | 2026-09-12（本文件写于任何 test 读数之前） |
| 授权 | 研究者 2026-09-12 明确授权**一次性**打开官方 `split_chrono_test` |
| 版本 | v1.0，签署后不得修改；如需修改须另立 v2 并说明为何未消费 test |
| 机读清单 | `13_test_final/TEST_FROZEN_MANIFEST.json`（由 `gen_test_manifest.py` 从各卡真实产物导出，含 hash） |
| 唯一评价次数 | **一次**。读数落盘后不得再以任何理由重跑、换模型、换编码或换窗口 |

## 0. 已签署的研究决策（本轮裁决记录，逐条可追溯）

| 裁决项 | 决定 | 影响 |
|---|---|---|
| 打开官方 test | **授权一次性打开** | 本文件即其前置冻结包 |
| `R` 缺失哨兵 | **`R_B`（无记录→显式 120 min）进主分析；`R_A` 作敏感性** | 主表用 `R_B`；`R_A` 只作并列敏感性，不择优 |
| `decomp_D120` | **保留任务与标签，作并列探索性；不重设队列/患病率** | 报阳性数、区间与「不判定」，**不得**写「无效应」 |
| B6 是否重跑 | **不重跑**；B8 为正式可复现稳健性证据 | 见 `08_protocol_audit/targeted_rerun_list.csv` RR-01 |
| 统一队列 LSTM 重训 | **暂缓**，不纳入 test 前工作 | 架构比较不属本轮主问题 |
| B10 继续搜索 2h 配置 | **停止搜索**，冻结首个工程配置 | 否证性结果不再被 HPO 翻案 |
| 外部验证 | 只登记为后续路线，不作本轮交付 | 单中心 + 人工删点 ≠ 跨院验证 |

**主问题（唯一）**：在固定 ED 2 小时预测点上，记录最新性是否提供**超出 presence、记录量
与最近数值**的可复现增量；当末端监测中断时，该增量与绝对性能如何变化。

## 1. 前置门槛：test 数据层必须由新代码重建，并先通过复现验收

**事实**：官方 chrono test 有 12,020 次就诊，但**全部派生产物都不含 test 行**——
`wave6/cache/cohort_a2h.parquet` 只有 train+val（93,358 行），因为
`wave6/src/cohort6.py:77` 有一行硬过滤 `tv = v[v.split.isin(["train","val"])]`；
`c0_static.parquet`、`events_*.npz`、`view_*_features.parquet`、
`cohort_manifest.parquet`、`labels.parquet` 与 test 的交集均为 **0**。

因此 test 读数之前必须完成（顺序固定，任一失败即**停止且不打开 test**）：

1. **T-0 队列重建（含 test）**：新增 test-inclusive 队列构建器，不改动
   `cohort6.py` 的 train/val 行为（原文件保持原样，新建变体）。
2. **T-1 逐位复现验收（硬门槛）**：用新构建器重算 train+val，必须与既有
   `cohort_a2h.parquet` / `cohort_manifest.parquet` / `labels.parquet` /
   `view_dense_features.parquet` / `events_*.npz` **逐位相同**
   （行数、CSN 顺序、标签、门控行数、特征值 `max|diff| = 0`；浮点列容差 0）。
   不通过 ⇒ 说明重建代码与冻结管线不等价，**禁止读 test**，先修到通过为止。
3. **T-2 test 侧特征构建**：C0 / C1 数值摘要 / C2 行为 / `O_core_v2`+`R` /
   C3 事件 token / 1 min 网格，全部沿用既有门控与列定义；
   **train-fit 变换器一律在 train 行上拟合**（不得用 test 行拟合任何 scaler、
   插补值、词表或 HPO）。
4. **T-3 身份登记**：test 队列/标签/视图 hash、行数、阳性数、覆盖率写入 manifest；
   test 的 MRN 与 train/val 主队列 MRN 集合必须**互斥**（患者级隔离核验）。

> 这一步不是形式主义：test 数据层是**新写的代码**，若它悄悄偏离冻结管线，
> 一次性 test 就会被一个不可比的读数消费掉。T-1 是唯一能自动抓住这种偏离的门。

## 2. 冻结的模型、特征与选择规则（全部沿用已签字的卡片，不新增）

| 层 | 内容 | 冻结来源 |
|---|---|---|
| 主任务 | `dispo_T3`（正类＝非 Discharge，Observation 并入收治） | Wave6 冻结定义 |
| 并列任务 | `decomp_D120`（事件判据预测 `(t_w, t_w+120min]` 恶化），**低功效并列** | 同上 |
| 锚点 | `index_time = visits.Arrival_time`；`t_w = index_time + 120 min` | 同上 |
| 主要失配强度 | **只有 `term20`**（删 `(t_w−20, t_w]` 全部真实 Monitor 行；种子 `zlib.crc32`） | `10_b8/PREREG.md` |
| 主哨兵 | `R_B`＝无记录显式 120 min；`R_A` 作敏感性并列 | 研究者裁决 |
| 表格臂 | Logistic（L2=1.0）与 LightGBM（HPO 参数**沿用已冻结的 `b1_hp_cache` 键**，`hpo_seed=0`，不在 test 上重搜） | `09_b7`/`10_b8` run_record |
| 事件臂 | B9 同一 set encoder 的 `E00/E10/E01/E11` + `B_only` 锚 + `Count_LGBM` 参照 | `11_b9/PREREG.md` |
| 方法臂 | B10 `OP_GRUD_ED` / `OP_ReTAMamba` / `_identityGate` / `_obsOnly`，配置冻结不搜索 | `12_b10/PREREG.md` |
| seeds | `{0,1,2,3,4}`（`D.SEEDS`），`seed_at` 派生三类随机源 | `ds_common` |
| 早停 | B10 用 **train 内部**分层子集；B9/神经臂沿用各卡已登记规则 | 各卡 PREREG |
| bootstrap | 10,000 次配对，`seed_base = 20260906`，visit 级为主、MRN 聚类为次，全臂全条件共用重采样索引 | `ds_fastboot` |
| 指标 | `average_precision_score` 口径；次指标 AUROC / Brier / ECE(10, 固定边界) / 校准斜率 | 统一评价器 |
| 判据 | 三栏分列：对 0 的 Holm p；实质阈值＝CI95 下界 > +0.005；TOST 双侧 ±0.005 | `verdict_round3` |
| 拟合规模 | 沿用各卡既有规模，**不因 test 而增删臂或改 seed 数** | 各卡 PREREG |

**禁止事项（写死）**：不得根据 val 或 test 的任何读数选择模型、编码、窗口、阈值或子集；
不得把 `decomp_D120` 用于推翻或确认 `dispo_T3` 的机制结论；不得因 test 不利而回到 val
重挑 `R_A`、其他模型或其他失配强度；不得重开已冻结的 HPO。

## 3. 预写的 test 判定规则（读数前固定，读数后不改）

**Tier 1（确认性主结果）**

- `T1-A`：`dispo_T3` 上 `F7_R_vs_base`（`R_B`，全队列，LR 与 LightGBM 两模型）。
- `T1-B`：同任务上 `F7_R_noNS`（去掉确定性重复 N/S 后）与四通道全可见子集读数。
- `T1-C`：`term20` 的 `ΔR(term20)`、`DiD(term20−dense)`（matched 与 shift 两轨）
  以及**绝对 AP 损失**（三者必须并列呈现）。

**判定映射**

1. **方向、区间与校正后结论与 val 基本一致**（即 `T1-A` 对 0 校正后显著为正，
   且 `T1-C` 的 matched 轨 DiD 与 shift 轨读数复现同样的「匹配可保留、固定模型会退化」
   模式）⇒ 可以把
   **「记录最新性是稳定的记录行为候选特征」**作为主结果汇报，
   并按 `T1-A` 的实际 CI95 下界决定是否写「超过 +0.005 实质阈值」。
2. **test 不支持** ⇒ 报告为「**val 探索性信号未能获得外部确认**」，
   并原样给出 test 数值；**不得**回到 val 重挑哨兵/模型/窗口，**不得**改判据。
3. **部分支持**（例如 LR 复现而 LightGBM 不复现，或 matched 复现而 shift 不复现）
   ⇒ 按实际复现的**条件与模型**限定表述范围，不合并成一句笼统结论。
4. `decomp_D120` 无论结果如何都只作**并列低功效读数**：报阳性数与区间，
   等价只写「±0.005 内未检出差异」，不写「无效应」，也不参与 Tier 1 的成败判定。
5. **Tier 2**（`F9_content`/`F9_time`/`F10_primary`）：test 只用于检验
   「val 上的否证性/等价读数是否外部复现」。若 test 上出现 > +0.005 的反向差异，
   记为「val 等价不外推」，**不得**据此改写成「事件信息/ReTAMamba 有效」的新发现
   （那是事后翻案，属预注册违规）。
6. 全部结论一律标注：单中心 MC-MED、人工末端删点 ≠ 真实跨院监测中断。

## 4. 落盘与回传

产物写入 `result/Week5/13_test_final/`：test cohort/label/view manifest、
逐例预测（留训练机）、`table_F11_test_*.csv`、判定 JSON、
以及 `TEST_READOUT.md`（一次性读数记录，含时间与 hash）。
可共享聚合报告写入 `docs/GEM-MIRA/research/results/` 后 `publish`；
只有本机 pull 校验成功才可称「已回传」。

## 5. 签字状态

- [x] 研究者已授权一次性打开 test（2026-09-12）
- [x] 主哨兵、任务定位、B6、B10 配置、LSTM、外部验证六项裁决已记录（§0）
- [ ] **T-1 逐位复现验收通过**（未通过前不得读 test）
- [ ] 本文件 v1.0 由研究者确认后即为最终版；此后任何改动须另立版本并说明 test 未消费

---

## 修正案 A1（2026-09-12 深夜，**在任何 test 读数之前**；只缩减范围，不放宽判据）

| 项 | 变更 | 理由 |
|---|---|---|
| Tier-2 的 **B9** | **从本次一次性 test 读数中剔除** | T-1 逐位复现验收中，`b9_ev_tokens` 在 train/val 上**未通过**（78,418 个 CSN 中 77,956 个 token 内容不一致），且与「`c3_events` 逐位相同 + `vocab_sha` 相同」构成矛盾，夜间未定位到原因。详见 `T1_未决项_b9_tokens.md`。特征来源不可证明同源时，test 读数没有解释基础 |
| Tier-1 与 **B10** | 照常（待研究者复核 T-1 证据后执行） | 二者依赖的 `cohort_manifest / labels / c0_static / view_*_features / events_*` 全部 ✓ 逐位复现 |
| 恢复条件 | 解决该矛盾并重跑 `verify_t1_layer.py` 得 `T1_pass=true` 后，B9 可**单独注册一次** test 读数 | 不得以「先读了再说」的方式绕过 |

本修正案不新增任何对比、不更改任何阈值或判定规则、不消费 test（`test_consumed` 仍为 `false`）。
