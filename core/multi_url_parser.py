from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

_URL_RE = re.compile(r"https?://(?:www\.)?(?:youtube\.com/watch\?[^\s<>]+|youtu\.be/[^\s<>]+|youtube\.com/shorts/[^\s<>]+)", re.I)
_PLAYLIST_RE = re.compile(r"https?://(?:www\.)?youtube\.com/(?:playlist\?[^\s<>]+|watch\?[^\s<>]*[?&]list=[^\s<>]+)", re.I)
@dataclass(frozen=True)
class ParseResult:
    urls: list[str]
    duplicates_removed: int
    playlists_ignored: int

def normalize_url(raw: str) -> str | None:
    parsed = urlparse(raw.rstrip(".,;!?)]}>")); host = parsed.netloc.lower().removeprefix("www.")
    if host == "youtu.be": video_id = parsed.path.strip("/").split("/")[0]
    elif host == "youtube.com" and parsed.path == "/watch": video_id = parse_qs(parsed.query).get("v", [""])[0]
    elif host == "youtube.com" and parsed.path.startswith("/shorts/"): video_id = parsed.path.split("/", 2)[2].split("/", 1)[0]
    else: return None
    return f"https://www.youtube.com/watch?v={video_id}" if re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id) else None

def extract_video_urls(text: str) -> ParseResult:
    seen: set[str] = set(); urls: list[str] = []; duplicates = 0; playlists = len(_PLAYLIST_RE.findall(text))
    for raw in _URL_RE.findall(text):
        if "list=" in raw.lower(): continue
        url = normalize_url(raw)
        if not url: continue
        if url in seen: duplicates += 1
        else: seen.add(url); urls.append(url)
    return ParseResult(urls, duplicates, playlists)
