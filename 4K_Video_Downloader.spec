# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

root = Path(SPECPATH)


def first_existing(*paths):
    return next((path for path in paths if path.exists()), None)


runtime_sources = {
    "yt-dlp.exe": first_existing(root / "runtime" / "yt-dlp.exe", root / "yt-dlp.exe"),
    "ffmpeg.exe": first_existing(root / "runtime" / "ffmpeg.exe", root / "ffmpeg.exe", root / "ffmpeg-9.0.1-essentials_build" / "bin" / "ffmpeg.exe"),
    "ffprobe.exe": first_existing(root / "runtime" / "ffprobe.exe", root / "ffprobe.exe", root / "ffmpeg-9.0.1-essentials_build" / "bin" / "ffprobe.exe"),
}
binaries = [(str(source), "runtime") for source in runtime_sources.values() if source]

a = Analysis(
    [str(root / "app.py")],
    pathex=[str(root)],
    binaries=binaries,
    datas=[
        (str(root / "ui" / "styles.qss"), "ui"),
        (str(root / "app_icon.ico"), "assets"),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="4K Video Downloader Pro",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=str(root / "app_icon.ico"),
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=True, name="4K Video Downloader Pro")
