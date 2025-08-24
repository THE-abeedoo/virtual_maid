@echo off
chcp 437 >nul

:: Get absolute path of script directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo ========================================
echo VirtualMaid 2025 Auto-Installation Script
echo ========================================
echo.
echo Current working directory: "%CD%"
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% equ 1 (
    echo ERROR: Python environment not detected
    echo Please install Python 3.11 recommended or other versions first
    echo Download address: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python environment detected successfully
python --version

:: Check if requirements.txt exists
if not exist "requirements.txt" (
    echo ERROR: requirements.txt file not found
    echo Please ensure you are running this script in the correct directory
    echo Current directory: "%CD%"
    pause
    exit /b 1
)

echo.
echo Installing dependencies...
echo.

:: Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

:: Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

if %errorlevel% equ 1 (
    echo.
    echo Dependency installation failed, trying with domestic mirror source...
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
    
    if %errorlevel% equ 1 (
        echo.
        echo Dependency installation still failed
        echo Please check network connection or install dependencies manually
        pause
        exit /b 1
    )
)

echo.
echo Dependencies installation completed!
echo.
echo Installation successful! Now you can run run.bat to start the program
echo.
pause
