from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


def base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def _candidates(name: str) -> list[Path]:
    root = base_dir()
    candidates = [
        root / "runtime" / name,
        root / name,
        root / "_internal" / name,
        root / "_internal" / "runtime" / name,
    ]
    if hasattr(sys, "_MEIPASS"):
        candidates.insert(0, Path(sys._MEIPASS) / "runtime" / name)
        candidates.insert(1, Path(sys._MEIPASS) / name)
    return candidates


def executable(name: str, fallback: str | None = None) -> str:
    for candidate in _candidates(name):
        if candidate.exists():
            return str(candidate)
    found = shutil.which(Path(name).stem)
    return found or fallback or name


def ffmpeg_dir() -> str:
    root = base_dir()
    for folder in (root / "runtime", root / "ffmpeg-9.0.1-essentials_build" / "bin", root / "ffmpeg", root):
        if (folder / "ffmpeg.exe").exists() or (folder / "ffmpeg").exists():
            return str(folder)
    ffmpeg = shutil.which("ffmpeg")
    return str(Path(ffmpeg).parent) if ffmpeg else str(root)


def ytdlp() -> str:
    return executable("yt-dlp.exe", "yt-dlp")


def ffmpeg() -> str:
    return executable("ffmpeg.exe", "ffmpeg")


def ffprobe() -> str:
    return executable("ffprobe.exe", "ffprobe")


def engine_status() -> dict[str, bool]:
    return {"yt-dlp": Path(ytdlp()).exists(), "ffmpeg": Path(ffmpeg()).exists(), "ffprobe": Path(ffprobe()).exists()}
