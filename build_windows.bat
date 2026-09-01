@echo off
setlocal EnableExtensions

rem 优先使用 Windows 的 py 启动器；没有时改用 python 命令。
set "PYTHON_CMD="
where py >nul 2>&1
if not errorlevel 1 set "PYTHON_CMD=py"
if not defined PYTHON_CMD (
    where python >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=python"
)

if not defined PYTHON_CMD (
    echo [错误] 找不到 Python。请从 https://www.python.org/downloads/windows/ 安装 Python，
    echo 并在安装界面勾选 Add python.exe to PATH，然后重新运行本文件。
    if not defined CI pause
    exit /b 1
)

echo 使用 %PYTHON_CMD% 安装 PyInstaller...
%PYTHON_CMD% -m pip install --upgrade pyinstaller
if errorlevel 1 (
    echo [错误] PyInstaller 安装失败，请检查网络连接或 Python 安装状态。
    if not defined CI pause
    exit /b 1
)

%PYTHON_CMD% -m PyInstaller --noconfirm --clean --onefile --windowed --name MAC地址采集工具 mac_collector.py
if errorlevel 1 (
    echo [错误] EXE 构建失败。
    if not defined CI pause
    exit /b 1
)

echo.
echo 构建完成：dist\MAC地址采集工具.exe
if not defined CI pause
