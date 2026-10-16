# flucase 测试教程生成脚本

2026-10-16 全角色测试时写的：每份教程是一个 Python 文件（`gd.py`、`gam.py`、`newcenter.py`、`researcher.py`、`others.py`），写成 JSON 后由 `render.js`（npm 包 `docx`）渲染成 .docx，再用 LibreOffice 转 PDF，输出复制到 `docs/flucase/`。

- 截图：`tmp/flucase_tutorial/shots/<名字>.png`（1440×900，正式模式、虚构数据；`tmp/` 已 gitignore，只留本机）。教程里按名字引用，换截图只要同名覆盖。
- 虚构测试文件：`tmp/flucase_tutorial/files/`（系统自带样例，加上改一个值、改工作表名、无关表、坏文件、虚构 XZ 医院导出）。
- 截图用 ego-browser 拍：`ego_lib.mjs` 里有登录、截图（关动画、等 1 秒）、按文字点击等函数；测试服务按 `ego_lib.mjs` 里的 `BASE`（默认 `http://127.0.0.1:8765`，正式模式、空数据目录），测试账号密码统一为 `PW`。
- 行内标记：`**粗体**`、`` `代码` ``；每一步用 `step(no, title, do=[...], see=[...], figs=[(截图名, 说明[, 裁剪框])], note=..., tip=..., code=...)`。
- 生成：`bash scripts/flucase_tutorials/build.sh`（或只生成某几份：`… build.sh gd gam`）。文件名里的日期改 `common.py` 的 `DATE`。
