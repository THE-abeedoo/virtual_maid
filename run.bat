@echo off
chcp 65001 >nul
echo ========================================
echo VirtualMaid 2025 启动脚本
echo ========================================
echo.

:: 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未检测到Python环境
    echo 请先运行 setup.bat 安装环境
    pause
    exit /b 1
)

:: 检查main.py是否存在
if not exist "main.py" (
    echo ❌ 错误：未找到 main.py 文件
    echo 请确保在正确的目录下运行此脚本
    pause
    exit /b 1
)

:: 检查依赖是否已安装
echo 🔍 检查依赖包...
python -c "import sounddevice, librosa, soundfile, pyrubberband, requests, openai, translate" >nul 2>&1
if errorlevel 1 (
    echo ❌ 依赖包未完全安装
    echo 请先运行 setup.bat 安装依赖
    pause
    exit /b 1
)

echo ✅ 环境检查完成
echo.
echo 🚀 正在启动 VirtualMaid 2025...
echo.

:: 启动程序
python main.py

:: 如果程序异常退出，显示错误信息
if errorlevel 1 (
    echo.
    echo ❌ 程序运行出错，错误代码：%errorlevel%
    echo 请检查配置文件和依赖是否正确
    echo.
    pause
)
