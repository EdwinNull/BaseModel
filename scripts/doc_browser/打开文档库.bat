@echo off
chcp 65001 >nul
rem Windows：双击启动文档库并打开浏览器；关掉这个窗口即退出
cd /d "%~dp0"
python server.py %*
pause
