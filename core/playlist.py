from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass

from .runtime import ytdlp


@dataclass(frozen=True)
class PlaylistEntry:
    index: int
    title: str
    url: str
    valid: bool


def load_playlist(url: str) -> list[PlaylistEntry]:
    process = subprocess.run([ytdlp(), "--flat-playlist", "-j", "-i", url], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    entries: list[PlaylistEntry] = []
    fallback_index = 1
    for line in process.stdout.splitlines():
        if not line.startswith("{"):
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        video_id = item.get("id") or item.get("url")
        title = item.get("title", f"Video {fallback_index}")
        valid = bool(video_id) and title not in {"[Private video]", "[Deleted video]", "[Unavailable video]"}
        target = video_id if str(video_id).startswith("http") else f"https://www.youtube.com/watch?v={video_id}" if video_id else ""
        entries.append(PlaylistEntry(int(item.get("playlist_index") or fallback_index), title, target, valid))
        fallback_index += 1
    return entries
