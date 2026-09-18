from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

_VIDEO_RE = re.compile(r"https?://(?:www\.)?(?:youtube\.com/watch\?[^\s<>]+|youtu\.be/[^\s<>]+|youtube\.com/shorts/[^\s<>]+)", re.I)
_PLAYLIST_RE = re.compile(r"https?://(?:www\.)?youtube\.com/(?:playlist\?[^\s<>]+|watch\?[^\s<>]*list=[^\s<>]+)", re.I)


@dataclass(frozen=True)
class ParsedUrls:
    urls: list[str]
    duplicates_removed: int
    playlists_ignored: int


def _normalize(raw: str) -> str | None:
    value = raw.rstrip(".,;!?)]}>")
    parsed = urlparse(value)
    host = parsed.netloc.lower().removeprefix("www.")
    if host == "youtu.be":
        video_id = parsed.path.strip("/").split("/")[0]
    elif host == "youtube.com" and parsed.path == "/watch":
        video_id = parse_qs(parsed.query).get("v", [""])[0]
    elif host == "youtube.com" and parsed.path.startswith("/shorts/"):
        video_id = parsed.path.split("/", 2)[2].split("/", 1)[0]
    else:
        return None
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        return None
    return f"https://www.youtube.com/watch?v={video_id}"


def extract_video_urls(text: str) -> ParsedUrls:
    urls: list[str] = []
    seen: set[str] = set()
    duplicates = 0
    playlists = len(_PLAYLIST_RE.findall(text))
    for raw in _VIDEO_RE.findall(text):
        if "playlist" in raw.lower() or "list=" in raw.lower():
            playlists += 1
            continue
        normalized = _normalize(raw)
        if not normalized:
            continue
        if normalized in seen:
            duplicates += 1
            continue
        seen.add(normalized)
        urls.append(normalized)
    return ParsedUrls(urls, duplicates, playlists)
