#!/bin/bash
# macOS：双击启动文档库并打开浏览器；关掉这个终端窗口即退出
cd "$(dirname "$0")" || exit 1
exec python3 server.py "$@"
