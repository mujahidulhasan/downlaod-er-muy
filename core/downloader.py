from __future__ import annotations

import json
import os
import re
import subprocess
import time
from pathlib import Path

from .runtime import ffmpeg, ffmpeg_dir, ffprobe, ytdlp


def verify_file(path: str | None, audio_only: bool = False) -> tuple[bool, str]:
    if not path or not os.path.exists(path) or os.path.getsize(path) == 0:
        return False, "File missing or empty"
    for suffix in (".part", ".ytdl"):
        if os.path.exists(path + suffix):
            return False, "Incomplete download"
    probe = ffprobe()
    if not Path(probe).exists():
        return True, "Valid (FFprobe skipped)"
    try:
        result = subprocess.run([probe, "-v", "error", "-show_entries", "stream=codec_type", "-of", "json", path], capture_output=True, text=True, timeout=15)
        streams = json.loads(result.stdout).get("streams", [])
        types = {stream.get("codec_type") for stream in streams}
        needed = {"audio"} if audio_only else {"audio", "video"}
        return (needed <= types, "Valid" if needed <= types else "Missing media stream")
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        return False, f"Verification failed: {str(exc)[:40]}"


def build_command(task: dict) -> list[str]:
    quality = task.get("quality", "1080p Full HD (MP4)")
    command = [ytdlp(), "--ffmpeg-location", ffmpeg_dir(), "--newline", "--progress"]
    if "MP3" in quality:
        command += ["-f", "bestaudio/best", "-x", "--audio-format", "mp3", "--audio-quality", "320K" if "320" in quality else "128K"]
    else:
        limit = next((value for value in ("2160", "1440", "1080", "720", "480", "360", "240") if value in quality), "1080")
        if "Original" in quality:
            format_spec = f"bv*[height<={limit}]+ba/b[height<={limit}]/bv*+ba/b"
        else:
            format_spec = f"bv*[height<={limit}]+ba/b[height<={limit}]/bv*+ba/b"
        command += ["-f", format_spec, "--merge-output-format", "mp4"]
    output = os.path.join(task["folder"], "%(title)s.%(ext)s")
    command += ["-o", output, "--no-write-info-json", "--no-write-comments", "--no-write-description"]
    if task.get("thumb"):
        command += ["--write-thumbnail", "--convert-thumbnails", "jpg"]
    if task.get("subs"):
        command += ["--write-subs", "--sub-langs", "en,bn"]
    else:
        command += ["--no-write-subs", "--no-write-auto-subs"]
    return command + [task["url"]]


def run_download(task: dict, pause_requested, on_update) -> None:
    task["status"] = "Downloading"
    Path(task["folder"]).mkdir(parents=True, exist_ok=True)
    process = None
    output_file: str | None = None
    errors: list[str] = []
    try:
        env = os.environ.copy()
        env["PATH"] = ffmpeg_dir() + os.pathsep + env.get("PATH", "")
        process = subprocess.Popen(build_command(task), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", env=env, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        task["process"] = process
        for line in process.stdout or []:
            line = line.strip()
            if line:
                errors.append(line)
                errors = errors[-8:]
            if pause_requested():
                process.kill()
                task["status"], task["detail"] = "Paused", "Paused"
                return
            progress = re.search(r"(\d+(?:\.\d+)?)%", line)
            speed = re.search(r"at\s+([\d.]+\s*[kKMGT]?i?B/s)", line)
            eta = re.search(r"ETA\s+(\d+:\d+(?::\d+)?)", line)
            if progress:
                task["progress"] = float(progress.group(1))
                task["speed"] = speed.group(1) if speed else ""
                task["eta"] = eta.group(1) if eta else ""
                task["detail"] = f"{task['progress']:.1f}%"
                on_update(task)
            if "Destination:" in line:
                output_file = line.split("Destination:", 1)[1].strip()
            if any(marker in line for marker in ("[Merger]", "[ffmpeg]", "[ExtractAudio]")):
                task["status"], task["detail"] = "Merging", "Merging with FFmpeg"
                on_update(task)
        process.wait()
        if task.get("cancel_requested"):
            task["status"], task["detail"] = "Cancelled", "Cancelled"
            return
        if process.returncode != 0:
            task["status"] = "Error"
            task["detail"] = next((line[:80] for line in reversed(errors) if "ERROR" in line.upper()), "Download failed")
            return
        if not output_file:
            extension = "mp3" if "MP3" in task.get("quality", "") else "mp4"
            candidates = sorted(Path(task["folder"]).glob(f"*.{extension}"), key=lambda item: item.stat().st_mtime, reverse=True)
            output_file = str(candidates[0]) if candidates else None
        valid, reason = verify_file(output_file, "MP3" in task.get("quality", ""))
        task["status"] = "Completed" if valid else "Incomplete"
        task["progress"] = 100.0 if valid else task.get("progress", 0)
        task["detail"] = "Completed" if valid else f"Validation failed: {reason}"
    except Exception as exc:
        task["status"], task["detail"] = "Error", str(exc)[:80]
    finally:
        task.pop("process", None)
        on_update(task)
