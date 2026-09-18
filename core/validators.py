from __future__ import annotations

from urllib.parse import parse_qs, urlparse


def is_video_url(url: str) -> bool:
    parsed = urlparse(url.strip())
    host = parsed.netloc.lower().removeprefix("www.")
    if host == "youtu.be":
        return bool(parsed.path.strip("/"))
    return host in {"youtube.com", "m.youtube.com"} and parsed.path in {"/watch", "/shorts"} and bool(parse_qs(parsed.query).get("v"))


def is_playlist_url(url: str) -> bool:
    parsed = urlparse(url.strip())
    return parsed.netloc.lower().removeprefix("www.") == "youtube.com" and (parsed.path == "/playlist" or "list" in parse_qs(parsed.query))
