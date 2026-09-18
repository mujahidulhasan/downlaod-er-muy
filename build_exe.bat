@echo off
title Build 4K Video Downloader Standalone EXE
cd /d "%~dp0"

where py >nul 2>&1
if %errorlevel% equ 0 (
    py -3 build_exe.py
    goto end
)

where python >nul 2>&1
if %errorlevel% equ 0 (
    python build_exe.py
    goto end
)

if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" build_exe.py
    goto end
)

if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" build_exe.py
    goto end
)

if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" build_exe.py
    goto end
)

if exist "C:\Python312\python.exe" (
    "C:\Python312\python.exe" build_exe.py
    goto end
)

if exist "C:\Python311\python.exe" (
    "C:\Python311\python.exe" build_exe.py
    goto end
)

if exist "C:\Python310\python.exe" (
    "C:\Python310\python.exe" build_exe.py
    goto end
)

echo [!] Python was not found in PATH or standard installation directories.
echo Please ensure Python is installed and added to PATH.

:end
pause
