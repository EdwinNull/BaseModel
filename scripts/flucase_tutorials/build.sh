#!/bin/bash
# 生成 flucase 测试教程（.docx + .pdf），复制到 docs/flucase/。
# 用法（BaseModel 根目录）：bash scripts/flucase_tutorials/build.sh [gd gam newcenter researcher others]（不写 = 全部）
# 依赖：python3（PIL、numpy）、node（第一次自动把 npm 包 docx 装到 tmp/flucase_tutorial/node）、LibreOffice（soffice）、pdfinfo
# 截图在 tmp/flucase_tutorial/shots/（gitignore，只留本机）；文件名日期改 common.py 的 DATE。
set -e
S="$(cd "$(dirname "$0")" && pwd)"; R="$(cd "$S/../.." && pwd)"; W="$R/tmp/flucase_tutorial"
PY="${PYTHON:-python3}"
mkdir -p "$W/out" "$W/pdftmp" "$W/node"
[ -d "$W/node/node_modules/docx" ] || npm install --prefix "$W/node" docx --no-audit --no-fund >/dev/null
export NODE_PATH="$W/node/node_modules"
names="${*:-gd gam newcenter researcher others}"
for n in $names; do
  spec=$("$PY" "$S/$n.py" | tail -1)
  name=$(basename "$spec" .json)
  node "$S/render.js" "$spec" "$W/out/$name.docx" >/dev/null 2>&1
  node "$S/render.js" "$spec" "$W/pdftmp/$name.docx" pdf >/dev/null 2>&1   # 换成本机有的中文字体再转 PDF
  soffice --headless --convert-to pdf --outdir "$W/out" "$W/pdftmp/$name.docx" >/dev/null 2>&1
  cp "$W/out/$name.docx" "$W/out/$name.pdf" "$R/docs/flucase/"
  echo "$name：$(pdfinfo "$W/out/$name.pdf" | awk '/Pages/{print $2}') 页"
done
