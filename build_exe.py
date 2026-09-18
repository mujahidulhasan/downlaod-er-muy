from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / "runtime"
ASSETS = ROOT / "assets"


def main() -> int:
    required = [RUNTIME / name for name in ("yt-dlp.exe", "ffmpeg.exe", "ffprobe.exe")]
    missing = [path.name for path in required if not path.exists()]
    if missing:
        print("BUILD FAILED: missing runtime files: " + ", ".join(missing)); return 1
    if not (ASSETS / "app_icon.ico").exists():
        print(f"BUILD FAILED: missing icon: {ASSETS / 'app_icon.ico'}"); return 1
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(ROOT / "requirements.txt")])
        for folder in (ROOT / "build", ROOT / "dist"):
            if folder.exists(): shutil.rmtree(folder)
        subprocess.check_call([sys.executable, "-m", "PyInstaller", "--noconfirm", str(ROOT / "4K_Video_Downloader.spec")], cwd=ROOT)
    except subprocess.CalledProcessError as error:
        print(f"BUILD FAILED with exit code {error.returncode}"); return error.returncode or 1
    output = ROOT / "dist" / "4K Video Downloader Pro" / "4K Video Downloader Pro.exe"
    if not output.exists(): print(f"BUILD FAILED: executable missing at {output}"); return 1
    print("====================================\nBUILD SUCCESSFUL\n====================================")
    print(f"Output: {output.parent}"); return 0

if __name__ == "__main__": raise SystemExit(main())
