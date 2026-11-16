# 文档库：本机研究文档浏览器

在浏览器里翻阅仓库的 docs、PPT、research、plans 等目录：左侧目录树，右侧按文件类型直接预览，支持文件名和全文搜索，右下角有能自己查资料的 AI 助手。服务只监听本机 127.0.0.1，只写本目录的 `config.json`、系统缓存目录和存 API key 的配置目录，不改动被浏览的文件。Mac 和 Windows 通用，只需要 Python 3.9 以上（只用标准库）。

## 启动

Mac 双击 `打开文档库.command`，Windows 双击 `打开文档库.bat`，会自动打开浏览器；关掉弹出的终端窗口即退出。也可以在仓库根目录运行：

```bash
python3 scripts/doc_browser/server.py
```

默认地址是 http://127.0.0.1:8765/ 。端口被占用时加 `--port 8800`；已经开着一个文档库时再启动，只会打开浏览器。`--no-browser` 不自动打开浏览器。第一次从 Finder 双击 `.command`，macOS 可能要求确认来源，右键选“打开”一次即可。

## 能看什么

| 文件 | 预览方式 |
|---|---|
| Markdown | 渲染成网页，带右侧本页目录；仓库内相对链接点了直接跳转，图片正常显示；支持表格、任务列表、脚注、`$$…$$` 和 `\[…\]` 公式、Mermaid 图 |
| PDF | 内置的 PDF.js 阅读器：缩略图与大纲、页内搜索、缩放、选中复制文字、放映模式，外观跟随文档库的浅色/深色 |
| PPT / PPTX、DOC、RTF | LibreOffice 在后台转成 PDF，再用同一个阅读器显示；幻灯片默认整页适配，宽窗口里左侧带缩略图。每个文件第一次打开要几秒到十几秒，之后读缓存 |
| DOCX | 浏览器内直接渲染；点“PDF 版式”改看 LibreOffice 的排版结果 |
| XLSX / XLS、CSV / TSV | 表格，带行号和冻结表头，数字列右对齐；GBK 编码的 CSV 会自动识别并注明 |
| HTML | 在隔离的框架里运行，脚本和样式照常生效，但碰不到文档库本身 |
| 图片、SVG | 居中显示，点击切换原始大小 |
| 代码、JSON、文本 | 语法高亮和行号；单行 JSON 会格式化后显示并注明 |

每个文件页都有收藏、复制路径、在 Finder（资源管理器）中显示、用默认程序打开四个按钮。首页列出各目录的规模和文件类型分布、最近修改的文件、收藏和最近查看。

## 搜索

按 `⌘K`（Windows 上 `Ctrl+K`）或 `/` 打开搜索框，`Tab` 在“文件名”和“全文”之间切换。全文搜索覆盖 Markdown、文本与代码、网页、Word、PPT、Excel 共享字符串和 PDF；多个词用空格分开，要求同时出现。结果里每条命中都标了行号或 PPT/PDF 页码，点进去 Markdown 会高亮关键词并定位，PPT 和 PDF 会翻到对应页并高亮页内的关键词。没能建立全文索引的文件（超过 10 MB 的纯文本、损坏的 Office 文件、缺少 pdftotext 时的 PDF）会在结果上方列出原因。

## AI 助手

右下角的按钮或 `⌘J`（Windows 上 `Ctrl+J`）打开助手面板，`Esc` 关闭，拖左上角可以改大小。它按 OpenAI 兼容协议（Chat Completions + function calling）调用模型，自己决定先搜什么、读哪几页，最多 12 轮工具调用后作答，回答里的出处是可点的链接，点了翻到对应文件的那一页并高亮关键词。面板里能看到每一步查了什么（“查阅了 N 步”），可以随时停止。

没有做向量库 RAG。文档库已经有全文索引，模型拿到的是这几个工具，效果相当于让它自己翻目录、搜关键词、逐页阅读：

| 工具 | 作用 |
|---|---|
| `search_docs` | 搜全文索引，返回命中文件和带页码/行号的片段 |
| `read_doc` | 读一个文件：PDF 和 PPT 按页，其他按行，一次约 12000 字，没读完会告诉模型下次从哪开始 |
| `list_dir` | 列目录 |
| `web_search` | 联网搜索（可关） |
| `fetch_url` | 打开网页或在线 PDF；只能打开在对话、文档或搜索结果里原样出现过的网址，网页里的恶意指令没法让模型把内容拼进新网址发出去 |

提问时默认附带当前文档：路径、PDF/PPT 正在看的页码，以及在文档里选中的文字（输入框上方的标签显示会附带什么，点一下可以取消）。

**设置**（面板右上角齿轮）：

- 模型服务商：内置 OpenAI、DeepSeek、通义千问、Kimi、智谱 GLM、硅基流动、OpenRouter、Ollama 的预设，也可以填任意兼容接口的地址。填好 API key 后点“获取列表”从 `/models` 拉模型名。可以配多家，点一下切换。
- API key 存在 Mac 的 `~/Library/Application Support/basemodel-doc-browser/keys.json`（Windows 是 `%APPDATA%\basemodel-doc-browser\keys.json`），权限 600，不进仓库，界面上只显示后四位。
- 联网搜索：用某家服务商的内置网页搜索（OpenAI Responses 接口的 `web_search` 工具，要求该账号和模型支持），或用 Tavily（另填 Tavily 的 key），或关闭。

**哪些内容不会发给模型**：仓库的 `data/`（真实病例数据）写死屏蔽；`config.json` 里 `assistant.exclude` 的文件也屏蔽，默认是课题任务书和会议记录，规则按仓库相对路径做通配匹配，只能编辑 `config.json` 修改。被屏蔽的文件搜索时不出现，读取时直接拒绝；当前打开的文档被屏蔽时，面板会提示，提问也不附带它的选中文字。除此之外，模型读到的文档内容都会发给所选的服务商，联网搜索的查询词会发给搜索服务。

## 增删目录

点左侧“目录”旁的调节按钮，可以添加、移除、调整顺序，保存后写入 `config.json`。目录要写成相对仓库根目录的路径（例如 `result`、`paper/首次调研阅读`），不能互相包含。文档里有链接指向尚未加入的目录时，链接显示为灰色虚线，点进去可以一键把那个目录加进来。也可以直接编辑 `config.json`，改完刷新页面；`exclude` 是按文件名匹配的排除规则。

切回浏览器窗口时会自动重新扫描，别处新建或修改的文件马上能看到；右上角的刷新按钮可以手动重扫。

## 外部程序

PPT 预览依赖 LibreOffice，PDF 全文搜索依赖 pdftotext（poppler）。启动时终端会打印两者是否找到，“管理目录”弹窗里也能看到。缺了哪个，对应的功能会明确提示，其他功能照常。Windows 上 LibreOffice 装在默认位置即可自动找到；pdftotext 需要在 PATH 里。

转换出的 PDF 和抽取的 PDF 文字缓存在 Mac 的 `~/Library/Caches/basemodel-doc-browser/`（Windows 是 `%LOCALAPPDATA%\basemodel-doc-browser\`），可以随时删除，下次打开会重新生成。

## 文件与依赖

`server.py` 是服务端，`assistant.py` 是 AI 助手（工具、对话循环、key 存取，只用 `urllib` 调接口，跟随系统代理），`static/` 是前端（`app.js`、`app.css`、`assistant.js`、`assistant.css`、`index.html`，无构建步骤）。`test_server.py` 和 `test_assistant.py` 是边界测试，全部用虚构文件、不连外网（`python3 -m pytest -q scripts/doc_browser`）。

`static/vendor/` 里是固定版本的开源库，全部离线可用：markdown-it 15.0.3（MIT）、markdown-it-task-lists 2.1.1（ISC）、markdown-it-footnote 4.0.0（MIT）、DOMPurify 3.4.17（MPL-2.0 / Apache-2.0）、highlight.js 11.12.0（BSD-3-Clause）、KaTeX 0.19.1（MIT）、Mermaid 12.2.0（MIT）、docx-preview 0.4.1（Apache-2.0）、JSZip 3.10.1（MIT）、SheetJS 0.20.3（Apache-2.0）、PDF.js 6.4.299（Apache-2.0）。升级时用 npm 装到临时目录，再把对应的 dist 文件拷进来。

PDF.js 放在 `static/vendor/pdfjs/`，来自官方发布包 `pdfjs-6.4.299-dist.zip`，保留 `build/` 与 `web/` 的原有结构（阅读器按相对路径找字体、字符映射和 wasm），去掉了 source map、调试器和示例 PDF，界面语言只留 `en-US` 与 `zh-CN`（同时改了 `web/locale/locale.json`），共约 8 MB。升级时照此重做一遍。文档库通过 PDF.js 启动前发出的 `webviewerloaded` 事件设定外观、外链开新标签页并停用它自己的偏好存储，代码在 `app.js` 的 `pdfViewer` 附近。

为什么没有直接用现成的文件管理器：评估过 FileBrowser Quantum、copyparty 等，它们面向文件管理和分享，不支持 Markdown 里仓库相对链接的跳转、PPT 预览以及 PPT/Word 内容的全文搜索，而这三项是翻阅本仓库最常用的。
