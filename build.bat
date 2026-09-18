@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "VENV=%~dp0.venv"
where py >nul 2>&1 && set "PYTHON=py -3"
if not defined PYTHON where python >nul 2>&1 && set "PYTHON=python"
if not defined PYTHON (echo BUILD FAILED: Python 3 not found on PATH.& exit /b 1)
if not exist "%VENV%\Scripts\python.exe" (%PYTHON% -m venv "%VENV%" || (echo BUILD FAILED: venv creation failed.& exit /b 1))
call "%VENV%\Scripts\activate.bat"
python build_exe.py
if errorlevel 1 (echo BUILD FAILED.& exit /b 1)
echo ====================================
echo BUILD SUCCESSFUL
echo Output: dist\4K Video Downloader Pro\
echo ====================================
pause
