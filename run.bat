batch
@echo off
chcp 437 >nul

:: Get absolute path of script directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo ========================================
echo VirtualMaid 2025 Startup Script
echo ========================================
echo.
echo Current working directory: "%CD%"
echo.

:: Try to detect Python executable
set "PYTHON_CMD=python"
python --version >nul 2>&1
if %errorlevel% equ 1 (
    set "PYTHON_CMD=python3"
    python3 --version >nul 2>&1
    if %errorlevel% equ 1 (
        echo ERROR: Python environment not detected
        echo Please run setup.bat first to install environment
        pause
        exit /b 1
    )
)

:: Check if main.py exists
if not exist "main.py" (
    echo ERROR: main.py file not found
    echo Please ensure you are running this script in the correct directory
    echo Current directory: "%CD%"
    echo Expected file: "%SCRIPT_DIR%main.py"
    pause
    exit /b 1
)

:: Check if dependencies are installed
echo Checking dependencies...
%PYTHON_CMD% -c "import sounddevice, librosa, soundfile, pyrubberband, requests, openai, translate" >nul 2>&1
if %errorlevel% equ 1 (
    echo Dependencies not fully installed
    echo Attempting to auto-install dependencies...
    %PYTHON_CMD% -m pip install sounddevice librosa soundfile pyrubberband requests openai translate
    if %errorlevel% equ 1 (
        echo Auto-installation failed, please run setup.bat first
        pause
        exit /b 1
    )
)

echo Environment check completed
echo.
echo Starting VirtualMaid 2025...
echo.

:: Start the program
%PYTHON_CMD% main.py

:: If program exits abnormally, show error message
if %errorlevel% equ 1 (
    echo.
    echo Program run error, error code: %errorlevel%
    echo Please check if configuration files and dependencies are correct
    echo.
    pause
)
