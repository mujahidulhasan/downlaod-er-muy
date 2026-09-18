@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "VENV=%~dp0.venv"
set "PYTHON="

where py >nul 2>&1
if not errorlevel 1 set "PYTHON=py -3"
if not defined PYTHON (
    where python >nul 2>&1
    if not errorlevel 1 set "PYTHON=python"
)
if not defined PYTHON (
    echo BUILD FAILED: Python 3 was not found on PATH.
    exit /b 1
)

if not exist "%VENV%\Scripts\python.exe" (
    echo Creating build virtual environment...
    %PYTHON% -m venv "%VENV%"
    if errorlevel 1 (
        echo BUILD FAILED: could not create the virtual environment.
        exit /b 1
    )
)

call "%VENV%\Scripts\activate.bat"
python build_exe.py
if errorlevel 1 (
    echo.
    echo ====================================
    echo BUILD FAILED
    echo ====================================
    exit /b 1
)

echo.
echo ====================================
echo BUILD SUCCESSFUL
echo ====================================
echo Output: dist\4K Video Downloader Pro\
echo ====================================
pause
exit /b 0
