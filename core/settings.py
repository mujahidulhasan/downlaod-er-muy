from __future__ import annotations

import json
import os
from pathlib import Path

APP_DATA_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local")) / "4KVideoDownloader"
SETTINGS_FILE = APP_DATA_DIR / "settings.json"
STATE_FILE = APP_DATA_DIR / "queue.json"
DEFAULTS = {"default_folder": str(Path.home() / "Downloads"), "default_quality": "1080p Full HD (MP4)", "audio_quality": "320 kbps", "subtitles": False, "theme": "dark", "notifications": True, "keep_history": True}

def load_settings() -> dict:
    try: data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError): data = {}
    return {**DEFAULTS, **data}

def save_settings(settings: dict) -> None:
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True); SETTINGS_FILE.write_text(json.dumps(settings, indent=2), encoding="utf-8")

def load_queue() -> list[dict]:
    try: return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError): return []

def save_queue(tasks: list[dict]) -> None:
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True); STATE_FILE.write_text(json.dumps(tasks, indent=2), encoding="utf-8")
