# 终点可判定性计数与核验工具

真实导出由研究者运行。助手仅测试虚构数据；M2 聚合计数返回后再锁定终点和核验分层。

输入需要包含10月30日加入的 `prediction_instances`、10月31日加入的 `respiratory_support` 和 `geriatric`。项目已记录完整结构的版本是 `std_v3_20261031_5`（规则集 `guideline2025_v0.6`）；也可在当前flucase重新导出相同规则集的完整std_v3，并包含分域视图。10月29日旧包即使文件名写着std_v3，也可能没有这些后续新增表，不能用于本脚本。不要只改旧zip文件名。

从 BaseModel 仓库根目录运行：

```bash
flucase/backend/.venv/bin/python -m pytest scripts/endpoint_audit -q -p no:cacheprovider
flucase/backend/.venv/bin/python scripts/endpoint_audit/endpoint_observability_counts.py \
  "data/export/<std_v3导出>.zip" --out "tmp/终点可判定性计数_20261108.md"
```

Windows 将 `bin/python` 换成 `Scripts/python.exe`。不调用网络、在线模型或 GPU。读入 parquet/csv/xlsx std_v3；必须包含 prediction_instances、encounters、events、severity_timeline、respiratory_support、vitals、labs、geriatric、outcomes 九张表。缺表、校验和不一致、版本不一致、就诊或证据挂接异常直接报错。

`--out` 给出的 Markdown 和相邻 `.provenance.json` 可交回。报告的非零计数作区间发布以避免跨表互补推算；区间跨越 G1/G2 门槛时由研究者本机查看。报告不含逐患者编号、值、时间或文本。

需要在本机保留精确聚合表时，可加 `--local-counts "data/endpoint_audit_20261108/精确聚合表.json"`。它仍只含聚合计数，但仅供研究者本机检查，不交回；文件以600权限创建并拒绝覆盖。

列映射、候选假设、尚未验证的内容和临床核验的下一步，见 `docs/终点核验/D165后_终点核验_列映射与执行交接_20261108.md`。核验池覆盖 primary 与 physiologic 的索引风险集并集；某口径排除的实例不计入该口径准确度与发生率分母。跨核验层重复患者在生成临床任务前报错，需要研究者先登记联合聚类方案。

核验工具的命令入口：

```bash
flucase/backend/.venv/bin/python scripts/endpoint_audit/review_tools.py prepare --help
flucase/backend/.venv/bin/python scripts/endpoint_audit/review_tools.py sample --help
flucase/backend/.venv/bin/python scripts/endpoint_audit/review_tools.py summarise --help
```

M2 后用 `prepare` 读取研究者确定的分院密度切点 JSON，指定 endpoint、phase 和 seed，在 `data/` 内生成 `sampling_population.csv` 和 `review_design.json`。切点JSON的院区键就是本次参加核验的院区，可按G1/G2结果只选一院；设计中另写入sites作核对。前者只给研究者看各层确切人数，后者初始配额均为0，并写入导出 SHA256。研究者填写各层配额后再运行 `sample`；导出版本变动时必须重做设计。

抽样 design JSON 必须显式含 `export_sha256`、`endpoint`（ladder/common/verified）、`phase`（pilot/full）、`seed`、分院 `density_cut` 和分院分层 `allocations`。分层键为 `event/<新发类别>`、`physiologic_only/<新发类别>`、unknown、negative_high、negative_low。每个实际存在的层必须写出样本数，包括 0；试点每院 10 事件、10 无事件，全量时事件、生理类独有事件、未知层必须抽取全部。此设计在 M2 后填写，不预先猜测各层人数。

人工表单列和受控取值见 `review_tools.FORM_FIELDS/FORM_ALLOWED`。reviewer 为 A、B 或 consensus；需要裁定时追加 consensus 行，不覆盖原始双评。`summarise --reviews filled_A.csv filled_B.csv consensus.csv` 可直接读取多个文件，无分歧时省略consensus。表、清单和钥匙都留在 `data/` 内，输出只交回聚合 Markdown。baseline_basis、quality_notes自由文本不进入聚合报告。

无导出也可用 `review_tools.py template --out-dir docs/终点核验/endpoint_audit_空表_20261108` 生成空白CSV和中文字段字典。操作说明、三个虚构培训例子、A1–A7待决策表和C1–C3答复卡见 `docs/终点核验/D165后_盲评操作说明与待决策表_20261108.md`。

表单分开记录 `first_upgrade_time/time_precision` 和 `first_deterioration_time/deterioration_time_precision`。前者描述支持升级，后者用于核查恶化终点时间，诊断类事件不能用升级时间替代。`baseline_execution` 核对基线支持是否执行，`hfnc_confirmed` 核对高流量是否属实，`rr_documentation_quality` 由评阅者按原始证据判断；缺依据选 unknown，不凭数值是否整齐直接断言模板化。

T7 是预测前的记录覆盖：尿素等检验的采样时间不能证明结果已经可见。缺少数值的记录不计作评分输入；氧流量及单位、FiO2 获得方法、主诉全文与结果可见时间的结构缺项会在报告中说明。

T2另含基线支持分层、排除明确基线治疗受限的敏感性、同指标此前正常的生理候选及D126呼吸命中证据。生理候选使用physiologic风险集，旧三口径仍原样保留。第八节附病例构成记录表；COM类别数含功能状态及家庭支持，D0可含D79合并，都不能自动解释为预测时点的临床疾病数或入院严重程度。

`descriptive.py` 提供精确二项区间、已锁定参考构成下的直接标化边界和流感季折算；调用需有真实计数与已登记口径。二项区间适用于独立二分类单位，重复患者的正式推断须沿用已锁定聚类设计。没有自动设定标化层、忽略未知或计算模型分数。
