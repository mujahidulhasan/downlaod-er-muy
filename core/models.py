from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

STATUSES = {"Queued", "Downloading", "Merging", "Paused", "Completed", "Failed", "Incomplete", "Skipped", "Cancelled"}

@dataclass
class DownloadTask:
    id: str
    url: str
    title: str
    folder: str
    quality: str = "1080p Full HD (MP4)"
    audio_quality: str = "320 kbps"
    subtitles: bool = False
    thumbnail: bool = False
    source: str = "single"
    playlist_index: int | None = None
    status: str = "Queued"
    progress: float = 0.0
    speed: str = ""
    eta: str = ""
    detail: str = "Queued"
    output_file: str = ""
    error: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DownloadTask":
        values = {key: data[key] for key in cls.__dataclass_fields__ if key in data}
        if values.get("status") in {"Downloading", "Merging"}:
            values["status"] = "Paused"
            values["detail"] = "Interrupted; ready to resume"
        return cls(**values)

@dataclass
class HistoryEntry:
    task_id: str
    title: str
    url: str
    date: str
    status: str
    quality: str
    output_file: str = ""
    file_size: int = 0
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
