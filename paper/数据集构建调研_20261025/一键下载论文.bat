@echo off
chcp 65001 >nul
cd /d "%~dp0"
where python >nul 2>nul && (python download_papers.py %*) || (py -3 download_papers.py %*)
echo.
pause
