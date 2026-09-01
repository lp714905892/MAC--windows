@echo off
setlocal EnableExtensions
set "PYTHON_CMD="
where py >nul 2>&1
if not errorlevel 1 set "PYTHON_CMD=py"
if not defined PYTHON_CMD (
    where python >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=python"
)
if not defined PYTHON_CMD (
    echo [错误] 找不到 Python，请安装 Python 并勾选 Add python.exe to PATH。
    if not defined CI pause
    exit /b 1
)
%PYTHON_CMD% -m pip install --upgrade pyinstaller
if errorlevel 1 exit /b 1
%PYTHON_CMD% -m PyInstaller --noconfirm --clean --onefile --windowed --name MAC地址采集工具 mac_collector.py
if errorlevel 1 exit /b 1
echo 构建完成：dist\MAC地址采集工具.exe
if not defined CI pause
