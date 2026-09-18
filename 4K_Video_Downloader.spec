# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
root = Path(SPECPATH)
runtime = root / "runtime"
assets = root / "assets"
binaries = [(str(runtime / name), "runtime") for name in ("yt-dlp.exe", "ffmpeg.exe", "ffprobe.exe")]
datas = [(str(root / "ui" / "styles" / "styles.qss"), "ui/styles"), (str(assets / "app_icon.ico"), "assets")]
a = Analysis([str(root / "app.py")], pathex=[str(root)], binaries=binaries, datas=datas, hiddenimports=[], hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name="4K Video Downloader Pro", debug=False, bootloader_ignore_signals=False, strip=False, upx=True, console=False, icon=str(assets / "app_icon.ico"))
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=True, name="4K Video Downloader Pro")
