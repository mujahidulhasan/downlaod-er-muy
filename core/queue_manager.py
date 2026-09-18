from __future__ import annotations

import threading
from PySide6.QtCore import QObject, Signal

from .downloader import run_download
from .settings import load_state, save_state


class QueueManager(QObject):
    changed = Signal()
    task_updated = Signal(dict)
    message = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.tasks = load_state()
        self.running = False
        self.paused = False
        self.active_process = None
        self.lock = threading.Lock()

    def persist(self) -> None:
        clean = [{key: value for key, value in task.items() if key != "process"} for task in self.tasks]
        save_state(clean)
        self.changed.emit()

    def add(self, tasks: list[dict]) -> None:
        self.tasks.extend(tasks)
        self.persist()
        self.start()

    def start(self) -> None:
        if self.running or self.paused:
            return
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self) -> None:
        with self.lock:
            self.running = True
            while not self.paused:
                pending = next((task for task in self.tasks if task.get("status") == "Queued"), None)
                if pending is None:
                    break
                run_download(pending, lambda: self.paused, self._updated)
                self.persist()
            self.running = False
            self.changed.emit()

    def _updated(self, task: dict) -> None:
        self.task_updated.emit({key: value for key, value in task.items() if key != "process"})
        self.changed.emit()
        self.persist()

    def pause(self) -> None:
        self.paused = True
        for task in self.tasks:
            process = task.get("process")
            if process:
                try:
                    process.kill()
                except OSError:
                    pass
            if task.get("status") in {"Queued", "Downloading", "Merging"}:
                task["status"] = "Paused"
                task["detail"] = "Paused"
        self.persist()

    def resume(self) -> None:
        self.paused = False
        for task in self.tasks:
            if task.get("status") in {"Paused", "Interrupted", "Error", "Incomplete"}:
                task.pop("cancel_requested", None)
                task["status"] = "Queued"
                task["detail"] = "Queued"
        self.persist()
        self.start()

    def cancel(self, task_id: str) -> None:
        for task in self.tasks:
            if task.get("id") == task_id:
                task["cancel_requested"] = True
                process = task.get("process")
                if process:
                    try:
                        process.kill()
                    except OSError:
                        pass
                task["status"] = "Cancelled"
                task["detail"] = "Cancelled"
        self.persist()

    def reset(self) -> None:
        self.pause()
        self.tasks.clear()
        self.persist()
