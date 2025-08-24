@echo off
chcp 65001 >nul

:: 获取脚本所在目录的绝对路径
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo ========================================
echo VirtualMaid 2025 启动脚本
echo ========================================
echo.
echo ? 当前工作目录：%CD%
echo.

:: 尝试检测Python可执行文件
set PYTHON_CMD=python
python --version >nul 2>&1
if errorlevel 1 (
    set PYTHON_CMD=python3
    python3 --version >nul 2>&1
    if errorlevel 1 (
        echo ? 错误：未检测到Python环境
        echo 请先运行 setup.bat 安装环境
        pause
        exit /b 1
    )
)

:: 检查main.py是否存在
if not exist "main.py" (
    echo ? 错误：未找到 main.py 文件
    echo 请确保在正确的目录下运行此脚本
    echo 当前目录：%CD%
    echo 期望文件：%SCRIPT_DIR%main.py
    pause
    exit /b 1
)

:: 检查依赖是否已安装
echo ? 检查依赖包...
%PYTHON_CMD% -c "import sounddevice, librosa, soundfile, pyrubberband, requests, openai, translate" >nul 2>&1
if errorlevel 1 (
    echo ? 依赖包未完全安装
    echo 正在尝试自动安装依赖...
    %PYTHON_CMD% -m pip install sounddevice librosa soundfile pyrubberband requests openai translate
    if errorlevel 1 (
        echo ? 自动安装失败，请先运行 setup.bat 安装依赖
        pause
        exit /b 1
    )
)

echo ? 环境检查完成
echo.
echo ? 正在启动 VirtualMaid 2025...
echo.

:: 启动程序
%PYTHON_CMD% main.py

:: 如果程序异常退出，显示错误信息
if errorlevel 1 (
    echo.
    echo ? 程序运行出错，错误代码：%errorlevel%
    echo 请检查配置文件和依赖是否正确
    echo.
    pause
)
