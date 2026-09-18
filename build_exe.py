from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def find_runtime(name: str) -> Path | None:
    candidates = [
        ROOT / "runtime" / name,
        ROOT / name,
        ROOT / "ffmpeg-9.0.1-essentials_build" / "bin" / name,
    ]
    return next((candidate for candidate in candidates if candidate.exists()), None)


def main() -> int:
    required = ["yt-dlp.exe", "ffmpeg.exe", "ffprobe.exe"]
    missing = [name for name in required if find_runtime(name) is None]
    if missing:
        print("BUILD FAILED: missing required runtime binaries:")
        for name in missing:
            print(f"  - {name} (expected in runtime\\, project root, or FFmpeg bin folder)")
        return 1
    if not (ROOT / "app_icon.ico").exists():
        print(f"BUILD FAILED: missing application icon: {ROOT / 'app_icon.ico'}")
        return 1

    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(ROOT / "requirements.txt")])
        for folder in (ROOT / "build", ROOT / "dist"):
            if folder.exists():
                shutil.rmtree(folder)
        subprocess.check_call([sys.executable, "-m", "PyInstaller", "--noconfirm", str(ROOT / "4K_Video_Downloader.spec")], cwd=ROOT)
    except subprocess.CalledProcessError as error:
        print(f"BUILD FAILED: command exited with code {error.returncode}")
        return error.returncode or 1

    output = ROOT / "dist" / "4K Video Downloader Pro" / "4K Video Downloader Pro.exe"
    if not output.exists():
        print(f"BUILD FAILED: expected executable was not created: {output}")
        return 1
    print("====================================")
    print("BUILD SUCCESSFUL")
    print("====================================")
    print(f"Output: {output.parent}")
    print("====================================")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
