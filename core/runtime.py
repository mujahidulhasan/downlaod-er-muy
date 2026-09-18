from __future__ import annotations

import shutil
import sys
from pathlib import Path

def application_dir() -> Path:
    return Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[1]

def _paths(name: str) -> list[Path]:
    root = application_dir(); paths = [root / "runtime" / name, root / name, root / "_internal" / "runtime" / name, root / "_internal" / name]
    if hasattr(sys, "_MEIPASS"): paths = [Path(sys._MEIPASS) / "runtime" / name, Path(sys._MEIPASS) / name] + paths
    return paths

def resolve(name: str) -> str:
    for path in _paths(name):
        if path.exists(): return str(path)
    return shutil.which(Path(name).stem) or name

def ytdlp() -> str: return resolve("yt-dlp.exe")
def ffmpeg() -> str: return resolve("ffmpeg.exe")
def ffprobe() -> str: return resolve("ffprobe.exe")
def ffmpeg_dir() -> str: return str(Path(ffmpeg()).parent)
def status() -> dict[str, bool]: return {key: Path(resolve(value)).exists() for key, value in (("yt-dlp", "yt-dlp.exe"), ("ffmpeg", "ffmpeg.exe"), ("ffprobe", "ffprobe.exe"))}
