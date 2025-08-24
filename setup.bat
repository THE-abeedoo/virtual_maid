@echo off
chcp 65001 >nul

:: 获取脚本所在目录的绝对路径
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo ========================================
echo VirtualMaid 2025 自动安装脚本
echo ========================================
echo.
echo 当前工作目录：%CD%
echo.

:: 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未检测到Python环境
    echo 请先安装Python 3.11^(推荐^)或其它版本
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python环境检测成功
python --version

:: 检查requirements.txt是否存在
if not exist "requirements.txt" (
    echo 错误：未找到 requirements.txt 文件
    echo 请确保在正确的目录下运行此脚本
    echo 当前目录：%CD%
    pause
    exit /b 1
)

echo.
echo 正在安装依赖包...
echo.

:: 升级pip
echo 升级pip...
python -m pip install --upgrade pip

:: 安装依赖包
echo 安装依赖包...
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo 依赖安装失败，尝试使用国内镜像源...
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
    
    if errorlevel 1 (
        echo.
        echo 依赖安装仍然失败
        echo 请检查网络连接或手动安装依赖
        pause
        exit /b 1
    )
)

echo.
echo 依赖安装完成！
echo.
echo 安装成功！现在可以运行 run.bat 启动程序
echo.
pause
