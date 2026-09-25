# 医学时序调研 HTML 报告 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 交付可直接打开的完整、详细、图文并茂的中文调研 HTML 报告。

**Architecture:** 单文件 HTML，内嵌 CSS、SVG 和少量无依赖 JS；引用本地已核验报告及来源清单。静态内容离线可读，JS 只增强导航和筛选。

**Tech Stack:** HTML5、CSS、内嵌 SVG、原生 JavaScript。

**Spec:** `docs/superpowers/specs/2026-09-25-medical-timeseries-report.md`

## Global Constraints

- 主证据为 `research/medical-ts-posttrain-rl-20260923/report.md` 及 `paper/首次调研/` 的第二轮数据与模型对比。
- 不把群体级流感预测等同个体转重；不把治疗策略奖励写成分类损失。
- 单文件离线可用，响应式、可打印、键盘可操作。

---

### Task 1: 内容结构与证据

**Files:** Create `医学时序预测模型调研报告.html`

- [x] 提炼已核验结论，落实章节、正文和可点击的 S 编号来源。
- [x] 对历史报告和证据局限给出清晰边界。
- [x] 检查关键表述与来源清单一致。

### Task 2: 图表与交互

**Files:** Modify `医学时序预测模型调研报告.html`

- [x] 绘制任务架构、患者时间轴、方法迁移与实验路线的解释性图示。
- [x] 完成排版、响应式与打印样式、目录、筛选和返回顶部。
- [x] 浏览器检验宽屏与窄屏阅读及交互。

### Task 3: 验证

**Files:** Read `医学时序预测模型调研报告.html`

- [x] 静态核对本地路径、锚点、HTML 结构与证据 ID。
- [x] 实测页面无脚本报错、可离线访问、打印布局无明显截断。

不创建提交；验收后直接交付文件路径。
