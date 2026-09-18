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
    reason: str = ""

def enumerate_playlist(url: str) -> list[PlaylistEntry]:
    process = subprocess.Popen([ytdlp(), "--flat-playlist", "--dump-single-json", "--skip-download", "-i", url], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    entries: list[PlaylistEntry] = []
    for line in process.stdout or []:
        try: payload = json.loads(line)
        except json.JSONDecodeError: continue
        raw_entries = payload.get("entries") if isinstance(payload, dict) else None
        for item in raw_entries or ([payload] if isinstance(payload, dict) else []):
            if not item: continue
            index = int(item.get("playlist_index") or len(entries) + 1); title = item.get("title") or "Unavailable video"; video_id = item.get("id") or item.get("url")
            valid = bool(video_id) and title not in {"[Private video]", "[Deleted video]", "[Unavailable video]"}; target = str(video_id) if str(video_id).startswith("http") else f"https://www.youtube.com/watch?v={video_id}" if video_id else ""
            entries.append(PlaylistEntry(index, title, target, valid, "Unavailable" if not valid else ""))
    process.wait(); return entries
