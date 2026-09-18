from __future__ import annotations

import json, os, re, subprocess
from pathlib import Path
from typing import Callable
from .models import DownloadTask
from .runtime import ffmpeg_dir, ffprobe, ytdlp

def build_command(task: DownloadTask) -> list[str]:
    command = [ytdlp(), "--ffmpeg-location", ffmpeg_dir(), "--newline", "--progress"]
    if "MP3" in task.quality: command += ["-f", "bestaudio/best", "-x", "--audio-format", "mp3", "--audio-quality", task.audio_quality]
    else:
        limit = next((value for value in ("2160", "1440", "1080", "720", "480", "360", "240") if value in task.quality), "1080"); command += ["-f", f"bv*[height<={limit}]+ba/b[height<={limit}]/bv*+ba/b", "--merge-output-format", "mp4"]
    command += ["-o", str(Path(task.folder) / "%(title)s.%(ext)s"), "--no-write-info-json", "--no-write-comments", "--no-write-description"]
    command += ["--write-thumbnail", "--convert-thumbnails", "jpg"] if task.thumbnail else ["--no-write-thumbnail", "--no-embed-thumbnail"]
    command += ["--write-subs", "--sub-langs", "en,bn"] if task.subtitles else ["--no-write-subs", "--no-write-auto-subs"]
    return command + [task.url]

def validate_output(path: str, audio_only: bool = False) -> tuple[bool, str]:
    if not path or not Path(path).exists() or Path(path).stat().st_size == 0: return False, "Output file missing or empty"
    if any(Path(path + suffix).exists() for suffix in (".part", ".ytdl")): return False, "Incomplete temporary file remains"
    probe = ffprobe()
    if not Path(probe).exists(): return True, "Valid; FFprobe unavailable"
    try:
        result = subprocess.run([probe, "-v", "error", "-show_entries", "stream=codec_type", "-of", "json", path], capture_output=True, text=True, timeout=15); types = {item.get("codec_type") for item in json.loads(result.stdout).get("streams", [])}; required = {"audio"} if audio_only else {"audio", "video"}; return required <= types, "Valid" if required <= types else "Required media stream missing"
    except (OSError, ValueError, subprocess.SubprocessError) as exc: return False, f"FFprobe validation failed: {str(exc)[:50]}"

def run_download(task: DownloadTask, is_paused: Callable[[], bool], is_cancelled: Callable[[], bool], on_update: Callable[[DownloadTask], None]) -> None:
    task.status = "Downloading"; task.detail = "Starting"; on_update(task); Path(task.folder).mkdir(parents=True, exist_ok=True); process = None; output_file = ""; errors: list[str] = []
    try:
        env = os.environ.copy(); env["PATH"] = ffmpeg_dir() + os.pathsep + env.get("PATH", ""); process = subprocess.Popen(build_command(task), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", env=env, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)); task._process = process
        for line in process.stdout or []:
            line = line.strip(); errors = (errors + [line])[-8:] if line else errors
            if is_cancelled(): process.kill(); task.status, task.detail = "Cancelled", "Cancelled"; return
            if is_paused(): process.kill(); task.status, task.detail = "Paused", "Paused"; return
            if "Destination:" in line: output_file = line.split("Destination:", 1)[1].strip()
            progress = re.search(r"(\d+(?:\.\d+)?)%", line)
            if progress:
                task.progress = float(progress.group(1)); task.speed = (re.search(r"at\s+([\d.]+\s*[kKMGT]?i?B/s)", line) or ["", ""])[1]; task.eta = (re.search(r"ETA\s+(\d+:\d+(?::\d+)?)", line) or ["", ""])[1]; task.detail = f"{task.progress:.1f}%"; on_update(task)
            if any(marker in line for marker in ("[Merger]", "[ffmpeg]", "[ExtractAudio]")): task.status, task.detail = "Merging", "Processing with FFmpeg"; on_update(task)
        process.wait()
        if is_cancelled(): task.status, task.detail = "Cancelled", "Cancelled"; return
        if is_paused(): task.status, task.detail = "Paused", "Paused"; return
        if process.returncode != 0: task.status, task.error = "Failed", next((line[:100] for line in reversed(errors) if "ERROR" in line.upper()), "yt-dlp failed"); task.detail = task.error; return
        if not output_file:
            extension = "mp3" if "MP3" in task.quality else "mp4"; matches = sorted(Path(task.folder).glob(f"*.{extension}"), key=lambda item: item.stat().st_mtime, reverse=True); output_file = str(matches[0]) if matches else ""
        valid, reason = validate_output(output_file, "MP3" in task.quality); task.output_file = output_file; task.status = "Completed" if valid else "Incomplete"; task.progress = 100 if valid else task.progress; task.detail = "Completed" if valid else reason
    except Exception as exc: task.status, task.error, task.detail = "Failed", str(exc)[:100], str(exc)[:100]
    finally:
        if hasattr(task, "_process"): delattr(task, "_process")
        on_update(task)
