@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set "PYTHON_DIR=%~dp0python"
set "PTH_FILE=%PYTHON_DIR%\python313._pth"

:: If embedded Python exists, launch directly
if exist "%PYTHON_DIR%\pythonw.exe" goto :launch

:: ============================================
::  First-time setup
:: ============================================
set "PYTHON_VERSION=3.13.2"
set "PYTHON_ZIP=python-%PYTHON_VERSION%-embed-amd64.zip"
set "PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/%PYTHON_ZIP%"
set "GET_PIP_URL=https://bootstrap.pypa.io/get-pip.py"

echo ============================================
echo  SoftDeck 최초 설치
echo ============================================
echo.

if not exist "%PYTHON_DIR%" mkdir "%PYTHON_DIR%"

echo [1/5] Python %PYTHON_VERSION% 다운로드 중...
powershell -Command "& { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%PYTHON_DIR%\%PYTHON_ZIP%' }"
if not exist "%PYTHON_DIR%\%PYTHON_ZIP%" (
    echo 다운로드 실패! 인터넷 연결을 확인하세요.
    pause
    exit /b 1
)

echo [2/5] 압축 해제 중...
powershell -Command "Expand-Archive -Path '%PYTHON_DIR%\%PYTHON_ZIP%' -DestinationPath '%PYTHON_DIR%' -Force"
if errorlevel 1 (
    echo 압축 해제 실패!
    pause
    exit /b 1
)

echo [3/5] Python 경로 설정 중...
if not exist "%PTH_FILE%" (
    echo %PTH_FILE% 파일을 찾을 수 없습니다!
    pause
    exit /b 1
)
powershell -Command "(Get-Content '%PTH_FILE%') -replace '^#import site', 'import site' | Set-Content '%PTH_FILE%'"
echo ..>> "%PTH_FILE%"

echo [4/5] pip 설치 중...
powershell -Command "& { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%GET_PIP_URL%' -OutFile '%PYTHON_DIR%\get-pip.py' }"
if not exist "%PYTHON_DIR%\get-pip.py" (
    echo get-pip.py 다운로드 실패!
    pause
    exit /b 1
)
"%PYTHON_DIR%\python.exe" "%PYTHON_DIR%\get-pip.py" --no-warn-script-location
if errorlevel 1 (
    echo pip 설치 실패!
    pause
    exit /b 1
)

echo [5/5] 패키지 설치 중...
"%PYTHON_DIR%\python.exe" -m pip install -r "%~dp0requirements.txt" --no-warn-script-location
if errorlevel 1 (
    echo 패키지 설치 실패!
    pause
    exit /b 1
)

del "%PYTHON_DIR%\%PYTHON_ZIP%" 2>nul
del "%PYTHON_DIR%\get-pip.py" 2>nul

echo.
echo 설치 완료!
echo.

:launch
start "" "%PYTHON_DIR%\pythonw.exe" "%~dp0main.py"
