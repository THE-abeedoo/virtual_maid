@echo off
chcp 65001 >nul

:: ��ȡ�ű�����Ŀ¼�ľ���·��
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo ========================================
echo VirtualMaid 2025 �Զ���װ�ű�
echo ========================================
echo.
echo ��ǰ����Ŀ¼��%CD%
echo.

:: ���Python�Ƿ�װ
python --version >nul 2>&1
if errorlevel 1 (
    echo ����δ��⵽Python����
    echo ���Ȱ�װPython 3.11^(�Ƽ�^)�������汾
    echo ���ص�ַ��https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python�������ɹ�
python --version

:: ���requirements.txt�Ƿ����
if not exist "requirements.txt" (
    echo ����δ�ҵ� requirements.txt �ļ�
    echo ��ȷ������ȷ��Ŀ¼�����д˽ű�
    echo ��ǰĿ¼��%CD%
    pause
    exit /b 1
)

echo.
echo ���ڰ�װ������...
echo.

:: ����pip
echo ����pip...
python -m pip install --upgrade pip

:: ��װ������
echo ��װ������...
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ������װʧ�ܣ�����ʹ�ù��ھ���Դ...
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
    
    if errorlevel 1 (
        echo.
        echo ������װ��Ȼʧ��
        echo �����������ӻ��ֶ���װ����
        pause
        exit /b 1
    )
)

echo.
echo ������װ��ɣ�
echo.
echo ��װ�ɹ������ڿ������� run.bat ��������
echo.
pause
