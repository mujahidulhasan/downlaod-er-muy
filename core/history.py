from __future__ import annotations

import json
from pathlib import Path

from .models import DownloadTask, HistoryEntry
from .settings import APP_DATA_DIR
from .utils import file_size

HISTORY_FILE = APP_DATA_DIR / "history.json"

class HistoryStore:
    def __init__(self) -> None:
        self.entries = self._load()

    def _load(self) -> list[HistoryEntry]:
        try:
            return [HistoryEntry(**item) for item in json.loads(HISTORY_FILE.read_text(encoding="utf-8"))]
        except (OSError, json.JSONDecodeError, TypeError):
            return []

    def _save(self) -> None:
        APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
        HISTORY_FILE.write_text(json.dumps([entry.to_dict() for entry in self.entries], indent=2), encoding="utf-8")

    def record(self, task: DownloadTask) -> None:
        if task.status not in {"Completed", "Failed", "Incomplete", "Skipped", "Cancelled"}:
            return
        self.entries = [entry for entry in self.entries if entry.task_id != task.id]
        self.entries.insert(0, HistoryEntry(task.id, task.title, task.url, task.created_at, task.status, task.quality, task.output_file, file_size(task.output_file), task.error))
        self._save()

    def remove(self, task_id: str) -> None:
        self.entries = [entry for entry in self.entries if entry.task_id != task_id]
        self._save()

    def clear(self) -> None:
        self.entries.clear()
        self._save()
