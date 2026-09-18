# 4K Video Downloader Pro

Native Windows desktop downloader built with Python, PySide6, yt-dlp, FFmpeg, FFprobe, and PyInstaller.

## Runtime files

Place the manually supplied binaries here:

```text
runtime/yt-dlp.exe
runtime/ffmpeg.exe
runtime/ffprobe.exe
assets/app_icon.ico
```

## Run

```text
python app.py
```

## Build on Windows

Double-click `build.bat`. It creates an isolated `.venv`, installs requirements, validates runtime files, and builds:

```text
dist/4K Video Downloader Pro/4K Video Downloader Pro.exe
```
