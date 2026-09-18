from __future__ import annotations

import os
from pathlib import Path


def short_path(value: str, limit: int = 55) -> str:
    return value if len(value) <= limit else "..." + value[-limit + 3:]


def file_size(path: str) -> int:
    try:
        return Path(path).stat().st_size
    except OSError:
        return 0


def open_path(path: str) -> None:
    if os.name == "nt":
        os.startfile(path)  # type: ignore[attr-defined]
    elif os.name == "posix":
        import subprocess
        subprocess.Popen(["xdg-open", path])
