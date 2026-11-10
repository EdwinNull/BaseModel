# 调研与核验记录

## 2026-10-31：本地与服务器审计

读取 v1.1、最新 std_v3 质量成绩单/Healthsheet、MC-MED 5-seed 报告、A4 与决策记录。SSH 只读检查 W/docs、代码、计划锁与资源快照；聚合快照及 SHA256 在 evidence/manifest.json。未打开逐患者数据或预测，未运行训练。

核心独立分工：服务器方法审计（P/F/AL、输入视图、指标、目标域使用）；文献身份/全文假设核验；理论与合作实验设计审查。各审计备忘保存在本目录。

追加读取用户指定 docx：officecli view text 获得段落，ZIP/XML 读取两张表并保存 evidence/MC_colleague.txt。保留原文，未修改文档。源文档 SHA256 8357bc5da4676af72b2d51a8a4d5983d7f77a33c2c4cf8f6e4c401c50f71c7a7。摘要中的 FINAL_COMPLETE_RESULTS 未独立取得，因此 v2 数字均标合作摘要报告。

找到并读取 9 月对应 TEST_PREREG.md；与早先 B10 PREREG 分开保存。TEST_PREREG 有部分未勾选状态，不能把找到协议等同于完整签署链验证。依据 TEST_READOUT 与偏差登记保留可用结果、排除失效 shift 轨。

## 文献检索与访问

定向检索 8 篇：系统性记录偏移、clinical presence shift、missingness shift、EHR 过程偏差、anchor ICU、ARM、counterfactual invariance、proper scoring。具体 endpoint、参数、返回数量、版本、访问范围在 literature_sources.jsonl；不是穷尽性系统综述。

来源包括 arXiv API/公开 HTML、PMLR 正式论文、PMC/BMJ 与勘误、Crossref 与 UW 开放技术报告。核验 formal title 与 arXiv title、预印本身份、原始任务和理论假设。Zhou 的已发表再掩码算法改变了新颖性判断；Jeanselme 的 transfer loss 与假设收窄了可借用结论；proper scoring 的公开阅读版本为 2004 技术报告，2007 正式版只核题录。

## 证据整合与停止规则

两轮针对性核验已覆盖本周决策：任务是否相同、测试触达历史、输入与时间语义、统计单位、最直接方法先行工作、合作 timing swap 的可识别范围。不继续扩文献数量；新外部库只列后续访问准备，不虚构多库结果。

外部文献以 S001—S008 入 sources.jsonl；本地/服务器证据以 E01—E12 入 evidence-index.json（保存真实路径与 hash，不伪造 HTTP 链接）。报告紧邻结论引用，claim-evidence.md 记录判断强度与待补证据。

## 交付检验

生成后运行外部来源引用校验、本地证据路径/hash/引用核查、SVG/HTML静态审计；浏览器实际检查桌面与窄屏布局、图文、目录跳转和 console。具体结果见 qa/verification.md。
