@echo off
chcp 65001 >nul

:: ��ȡ�ű�����Ŀ¼�ľ���·��
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo ========================================
echo VirtualMaid 2025 �����ű�
echo ========================================
echo.
echo ? ��ǰ����Ŀ¼��%CD%
echo.

:: ���Լ��Python��ִ���ļ�
set PYTHON_CMD=python
python --version >nul 2>&1
if errorlevel 1 (
    set PYTHON_CMD=python3
    python3 --version >nul 2>&1
    if errorlevel 1 (
        echo ? ����δ��⵽Python����
        echo �������� setup.bat ��װ����
        pause
        exit /b 1
    )
)

:: ���main.py�Ƿ����
if not exist "main.py" (
    echo ? ����δ�ҵ� main.py �ļ�
    echo ��ȷ������ȷ��Ŀ¼�����д˽ű�
    echo ��ǰĿ¼��%CD%
    echo �����ļ���%SCRIPT_DIR%main.py
    pause
    exit /b 1
)

:: ��������Ƿ��Ѱ�װ
echo ? ���������...
%PYTHON_CMD% -c "import sounddevice, librosa, soundfile, pyrubberband, requests, openai, translate" >nul 2>&1
if errorlevel 1 (
    echo ? ������δ��ȫ��װ
    echo ���ڳ����Զ���װ����...
    %PYTHON_CMD% -m pip install sounddevice librosa soundfile pyrubberband requests openai translate
    if errorlevel 1 (
        echo ? �Զ���װʧ�ܣ��������� setup.bat ��װ����
        pause
        exit /b 1
    )
)

echo ? ����������
echo.
echo ? �������� VirtualMaid 2025...
echo.

:: ��������
%PYTHON_CMD% main.py

:: ��������쳣�˳�����ʾ������Ϣ
if errorlevel 1 (
    echo.
    echo ? �������г���������룺%errorlevel%
    echo ���������ļ��������Ƿ���ȷ
    echo.
    pause
)
