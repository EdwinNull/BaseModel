# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目定位

老年人流感"转重"预测：医学时序基础模型的后训练 / 强化学习奖惩机制调研与实验。项目文档均为中文，回复与新写文档也用中文。

工作分两处：

| 位置 | 内容 |
|---|---|
| 本机仓库（本目录） | 调研报告、论文精读、实验计划、汇报 PPT、数据对齐说明；少量辅助脚本。**这里没有实验代码**；研究者的真实数据放在 gitignore 的 `data/`（D35），Claude 不读 |
| 服务器 `ud202482579@202.114.0.141`（已配免密 SSH） | 所有实验代码、数据、环境与运行。工作区 `/home/ud202482579/wangyiming`（下文记为 `W`），所有操作只在 `W` 内进行 |

服务器 `W/CLAUDE.md` 是实验侧的权威规范（A/B/C 决策分级、医学时序检查清单、日志规范等），在服务器上做实验前先读它；`W/basemodel/README.md` 和 `W/basemodel/experiments/rw_gam2gd/README.md` 说明代码结构与运行命令。

## 服务器侧结构（活跃路线 `W/basemodel/`）

- `alignment/`：医院数据（GAM 广安门旧数据 → GD 广东省中医院新数据）对齐为统一数据模型 CDM（encounters / events / treatments / complications / imaging / notes / crf_view 宽表）。`alignment/derive.py` 中的规则只是"候选列"，不是最终标签。`alignment_public/` 为公开数据（MIMIC-IV、eICU、MC-MED）侧。
- `experiments/rw_gam2gd/`：旧数据训练 → 新数据外部验证。`cohort.py` 的 `TaskConfig` 管理全部口径（终点、索引时点 t0、观察期、标签模式）；`features.py` 只取 `[input_start, t0)` 内观测；`models.py`（URB-65、LR、LightGBM、TabPFN v2、MIRA 冻结嵌入、Qwen3-8B 零样本）；`evaluate.py`（AUROC/AUPRC/Brier/校准/患者聚类 bootstrap）；`run_experiment.py` 串起整个流程；`configs/*.json` 为实验配置（`smoke_template.json` 只做冒烟测试）。
- `derived/`：逐患者派生数据与预测（目录 700、文件 600，不得拷出服务器）；`models_cache/`：TabPFN v2 权重。
- 文档：`W/docs/basemodel/{plan,result,research}/weekNN/`；日志：`W/logs/YYYY-MM-DD/`。
- 旧项目（GEM-MIRA 等）已归档到 `W/archive/projects_20260927/`，只读引用。
- GPU：2 × NVIDIA L40（46 GB）。

## 常用命令

服务器命令都在 `W/basemodel/` 下用项目 venv（系统 `python3` 没有 pandas）：

```bash
ssh ud202482579@202.114.0.141 'cd /home/ud202482579/wangyiming/basemodel && <命令>'

.venv/bin/python -m pytest -q tests                                       # 全部单元测试（虚构数据）
.venv/bin/python -m pytest tests/test_rw_gam2gd.py -q -p no:cacheprovider # 单个测试文件
.venv/bin/python -m pytest tests/test_rw_gam2gd.py -q -k <名字>           # 单个测试
.venv/bin/python -m experiments.rw_gam2gd.run_experiment \
    --config experiments/rw_gam2gd/configs/<名字>.json --run-id <名字>_<日期>   # 正式实验
.venv/bin/python -m experiments.rw_gam2gd.run_experiment \
    --config experiments/rw_gam2gd/configs/smoke_template.json --run-id SMOKE_permuted_<日期> --smoke  # 冒烟（指标无意义）
.venv/bin/python scripts/data_audit/scan_code_identifiers.py              # 标识符自查，应为 0 命中
```

pip 安装需用 `-i https://mirrors.aliyun.com/pypi/simple/`；服务器连不上 HuggingFace xet 存储，权重需在本机下载后上传。

本机辅助脚本（在仓库根目录运行）：

```bash
python scripts/download_models.py        # 下载 MOMENT-1-large、chronos-t5-large 到 models/
bash scripts/upload_models.sh            # rsync 上传到服务器 W/（upload_models.py、upload_models_scp.sh 仍是占位配置）
bash scripts/check_upload_status.sh      # 检查服务器上的模型
python PPT/build_data_alignment_presentation.py   # 由 数据对齐五页.pptx 生成 _结构与示例版.pptx（python-pptx）
```

`scripts/evaluate_patch.py` 是对服务器 `experiments/rw_gam2gd/evaluate.py` 的就地补丁，需在服务器 `basemodel/` 下执行。

## 必须遵守的规则（摘自服务器 CLAUDE.md 与实验计划）

- **A 档决策归研究者**：转重定义、纳排标准、索引时点与窗口、标签、切分、主要指标、阈值、模型路线、最终结论。先做完不依赖该决策的部分，再带实测证据交回研究者；不得自行换定义把流程跑通，同一判据连续两次操作化失败即停下报告。
- **实验流程**：写/更新方案 → 锁定（方案、配置、代码 sha256 写入 `logs/<日期>/<实验>_plan_lock.txt`）→ 运行 → 报告。外部验证集只评价一次，改口径须登记为新版本。
- **数据纪律**：医院数据含可识别信息。服务器上只在 `data/real_world/` 只读使用，逐患者数据只放 `basemodel/derived/`；文档只放聚合量。PhysioNet 公开数据（MIMIC-IV、eICU、MC-MED）不得拷出服务器，也不得发给任何在线 LLM/API，只用本地模型。测试、注释、日志只用虚构姓名与号码。
  - 研究者本机（D34、D35，2026-10-13）：已取消"医院原始数据不出服务器"。原始 Excel 和 flucase 的数据都放在本仓库的 `data/`（已 gitignore，严禁提交；不放进 `flucase/`，那是另一个仓库）。医院数据同样不得发给任何在线 LLM/API（含 Claude）。
  - flucase 改为数据收集系统（D39–D43，2026-10-14，待登记到服务器决策记录）：医生导入本院 Excel，flucase 自己的读取器直接读成病例库，**不做对齐**（不调用服务器对齐代码、不生成 CDM、不用化名对照表），系统内不化名、不做隐私审计拦截。规划与进度见 `plans/flucase数据收集系统重构_规划_20261014.md`；旧的 §4A 对齐路线（D36）被取代，`pipeline/legacy/` 只作移植参考，对照检查通过后删除。
  - Claude 不读任何真实病例内容：不打开、不列出、不打印本仓库 `data/` 下的文件（旧路径 `~/flucase_real` 同理）；在仓库根目录跑 `grep -r`、`find` 等递归命令时排除 `data/`；开发和测试只用虚构数据，真实数据上的检查由研究者执行、只回报计数。
- 服务器上临时文件不写 `/tmp`、`/dev/shm`，放在 `W` 内；日志写 `W/logs/YYYY-MM-DD/`，不散落在根目录。
- 长时训练/实验运行期间不做查询或 sleep 轮询，估算时长后等待。
- 文献工作：结论需可追溯到来源（标题、页码、章节、图表）；不得编造 DOI/作者/结果；只读摘要时标注"基于摘要"。历史论文清单曾出现题名与 PDF 不符，使用前看 `paper/首次调研阅读/00_论文身份核对.md`。

## 本机仓库内容

- `README.md`：阅读入口；本仓库目前只是研究材料，不含经验证的临床模型。
- `research/`：多轮调研报告（每轮含 `brief.md`、`report.md`、`research-log.md`、`sources.jsonl`）与合并展示页 HTML。
- `paper/`：论文库、精读笔记（按 时序基础模型 / 强化学习_后训练奖惩机制 / 数据集 分类）；`生成合并调研.py` 生成笔记骨架与 SVG 流程图。
- `plans/`：实验方案与执行计划（与服务器 `W/docs/basemodel/plan/week01/` 同步，两处内容应一致）。
- `docs/`：按主题分子文件夹（`数据对齐/`、`实验/`、`汇报/`、`flucase/`，索引见 `docs/README.md`）；`docs/数据对齐/数据对齐.md`：各数据源规模、CDM 表结构与示例；flucase 演示页在 `docs/flucase/`。
- 第三方 PDF、全文提取、检索记录、`tmp/`、`*.plan.json`、`lint.json` 只保留在本地，不入库（见 `.gitignore`）；`models/` 中的权重也不应提交。
