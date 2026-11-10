# 交付核验记录

核验日期：2026-10-31。核验范围是计划文档、证据台账与图文页，不代表计划中的新实验已执行。

| 检查 | 结果 |
|---|---|
| 主文结构 | 14个主要部分，覆盖七天任务、阅读、预期产物、验收、结果分支和长期安排 |
| 文献台账 | `validate_evidence.py`：8条来源，0 errors、0 warnings |
| 本地引用 | 104个HTML链接、77个ID检查通过；本地文件和文内目标均存在，无重复ID |
| 本地证据 | 12组、16个文件的SHA256与台账一致；原始合作DOCX未改动 |
| 图示 | 5个SVG逐个 `audit_visual.py`：各0 errors、0 warnings；HTML内嵌内容与最终SVG逐字一致 |
| HTML静态检查 | 0 errors、1 warning：固定宽图表可能影响窄屏；已进行下述实际浏览器验证 |
| 桌面 | 1280px视口，document.scrollWidth=1280；目录14项、图示5张，正文无整体横向溢出 |
| 窄屏 | 390px视口，document.scrollWidth=390；图表在各自容器内横向滚动，正文正常换行 |
| 交互 | 鼠标收起目录、Enter展开目录、点击第7节锚点均成功；窄屏表格方向键右移40px |
| SVG浏览器边界 | 5图所有text的getBBox均在对应viewBox内；目视检查图3协议、周计划、首页和窄屏表格 |
| Console | 开启Runtime/Log后加载，缓冲事件未发现错误 |

静态检查的宽度警告属于保留图表字号的设计选择：图表使用有焦点的局部滚动容器，页面加入了可见阅读提示。实际桌面/窄屏检查均无正文横向溢出，因此保留这一警告并记录验证。

窄屏键盘检查初次等待超时，原因是CLI新一轮恢复了1710px桌面视口，表格当时无横向溢出。重新在同一轮设定390px视口后，方向键滚动成功；没有更改文档内容来掩盖测试失败。

复核中统一了图3的逐院support/query协议、树模型重拟合与神经共同checkpoint的区别、源val用途和跨院患者处理边界。构建脚本仅渲染主文，不再重复插入正文段落。

可追溯文件：`structural.json`、`browser.json`、`artifact-sha256.json`。截图：`desktop.png`、`desktop-week.png`、`desktop-split.png`、`mobile.png`、`mobile-table.png`。首页桌面截图摄于最终增加阅读提示前；最终协议截图与窄屏首页已重拍。

执行的主要校验命令：

```text
python3 build_report.py
python3 /Users/edwinnull/.agents/skills/deep-research/scripts/validate_evidence.py --report report.md --sources sources.jsonl --log research-log.md
python3 /Users/edwinnull/.codex/skills/visual-concept-explainer/scripts/audit_visual.py <每个SVG及HTML>
```

浏览器使用本轮唯一Ego TaskSpace 2完成检查。工具提示Ego Lite有可用更新，本次未升级。
