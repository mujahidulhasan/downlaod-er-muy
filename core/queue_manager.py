from __future__ import annotations

import threading, uuid
from collections.abc import Callable
from .downloader import run_download
from .history import HistoryStore
from .models import DownloadTask
from .settings import load_queue, save_queue

class QueueManager:
    def __init__(self) -> None:
        self.tasks = [DownloadTask.from_dict(item) for item in load_queue()]; self.history = HistoryStore(); self.paused = False; self.running = False; self._lock = threading.Lock(); self._cancelled: set[str] = set(); self._listeners: list[Callable[[DownloadTask | None], None]] = []
    def subscribe(self, listener): self._listeners.append(listener)
    def _notify(self, task=None):
        save_queue([item.to_dict() for item in self.tasks])
        for listener in self._listeners: listener(task)
    def add(self, tasks): self.tasks.extend(tasks); self._notify(); self.start()
    def create(self, url, title, folder, **kwargs): return DownloadTask(id=str(uuid.uuid4()), url=url, title=title, folder=folder, **kwargs)
    def start(self):
        if not self.running and not self.paused: threading.Thread(target=self._loop, daemon=True).start()
    def _loop(self):
        with self._lock:
            self.running = True
            while not self.paused:
                task = next((item for item in self.tasks if item.status == "Queued"), None)
                if task is None: break
                run_download(task, lambda: self.paused, lambda: task.id in self._cancelled, self._updated); self.history.record(task); self._notify(task)
            self.running = False; self._notify()
    def _updated(self, task): self._notify(task)
    def pause(self):
        self.paused = True
        for task in self.tasks:
            if task.status in {"Queued", "Downloading", "Merging"}: task.status, task.detail = "Paused", "Paused"
        self._notify()
    def resume(self):
        self.paused = False
        for task in self.tasks:
            if task.status in {"Paused", "Failed", "Incomplete"}: task.status, task.detail = "Queued", "Queued"
        self._notify(); self.start()
    def cancel(self, task_id):
        self._cancelled.add(task_id)
        for task in self.tasks:
            if task.id == task_id and task.status != "Completed":
                process = getattr(task, "_process", None)
                if process:
                    try: process.kill()
                    except OSError: pass
                task.status, task.detail = "Cancelled", "Cancelled"
        self._notify()
    def retry(self, task_id):
        self._cancelled.discard(task_id)
        for task in self.tasks:
            if task.id == task_id: task.status, task.error, task.detail = "Queued", "", "Queued"
        self._notify(); self.start()
    def remove(self, task_id): self.tasks = [task for task in self.tasks if task.id != task_id]; self._notify()
    def clear_completed(self): self.tasks = [task for task in self.tasks if task.status != "Completed"]; self._notify()
