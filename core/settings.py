from __future__ import annotations

import json
import os
from pathlib import Path

APP_DATA_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local")) / "4KVideoDownloader"
STATE_FILE = APP_DATA_DIR / "downloads_state.json"
SETTINGS_FILE = APP_DATA_DIR / "app_settings.json"
DEFAULT_OUT_DIR = Path.home() / "Downloads"


def load_settings() -> dict:
    try:
        return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"default_save_folder": str(DEFAULT_OUT_DIR), "theme": "dark"}


def save_settings(data: dict) -> None:
    try:
        APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
        SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except OSError:
        pass


def load_state() -> list[dict]:
    try:
        tasks = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        for task in tasks:
            if task.get("status") in {"Downloading", "Merging"}:
                task["status"] = "Interrupted"
                task["detail"] = "Interrupted"
        return tasks
    except (OSError, json.JSONDecodeError):
        return []


def save_state(tasks: list[dict]) -> None:
    try:
        APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(tasks, indent=2), encoding="utf-8")
    except OSError:
        pass
