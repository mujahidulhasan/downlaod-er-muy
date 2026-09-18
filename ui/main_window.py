from __future__ import annotations

import os
import threading
import uuid
from pathlib import Path

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QPushButton, QProgressBar, QScrollArea, QSizePolicy, QStackedWidget, QTextEdit, QVBoxLayout, QWidget)

from core.multi_url_parser import extract_video_urls
from core.playlist import load_playlist
from core.queue_manager import QueueManager
from core.runtime import engine_status
from core.settings import load_settings, save_settings

QUALITY = ["1080p Full HD (MP4)", "720p HD (MP4)", "480p SD (MP4)", "360p SD (MP4)", "240p SD (MP4)", "2K Quad HD (1440p MP4)", "4K Ultra HD (2160p MP4)", "MP3 Audio (320 kbps)", "MP3 Audio (128 kbps)"]


def button(text: str, slot, primary: bool = False) -> QPushButton:
    control = QPushButton(text)
    control.setObjectName("Primary" if primary else "")
    control.clicked.connect(slot)
    return control


class PlaylistSignals(QObject):
    loaded = Signal(object)
    failed = Signal(str)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.settings = load_settings()
        self.manager = QueueManager()
        self.multi_items: list[dict] = []
        self.playlist_items: list[dict] = []
        self.signals = PlaylistSignals()
        self.signals.loaded.connect(self._playlist_loaded)
        self.signals.failed.connect(self._show_message)
        self.setWindowTitle("4K Video Downloader Pro")
        self.setMinimumSize(900, 620)
        self.resize(1050, 700)
        root = Path(__file__).resolve().parents[1]
        icon = next((candidate for candidate in (root / "assets" / "app_icon.ico", root / "app_icon.ico") if candidate.exists()), None)
        if icon:
            self.setWindowIcon(QIcon(str(icon)))
        self._build()
        self.manager.changed.connect(self.refresh_queue)
        self.refresh_queue()

    def _build(self) -> None:
        root = QWidget()
        layout = QHBoxLayout(root)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(14)
        self.sidebar = self._sidebar()
        layout.addWidget(self.sidebar)
        content = QVBoxLayout()
        content.setSpacing(12)
        content.addWidget(self._topbar())
        self.pages = QStackedWidget()
        self.pages.addWidget(self._single_page())
        self.pages.addWidget(self._multi_page())
        self.pages.addWidget(self._playlist_page())
        self.pages.addWidget(self._queue_page())
        self.pages.addWidget(self._history_page())
        self.pages.addWidget(self._failed_page())
        self.pages.addWidget(self._settings_page())
        content.addWidget(self.pages, 1)
        content.addWidget(self._statusbar())
        layout.addLayout(content, 1)
        self.setCentralWidget(root)

    def _sidebar(self) -> QFrame:
        frame = QFrame(); frame.setObjectName("Sidebar"); frame.setFixedWidth(210)
        layout = QVBoxLayout(frame); layout.setContentsMargins(16, 18, 16, 16)
        brand = QLabel("4K VIDEO\nDOWNLOADER PRO"); brand.setObjectName("Brand"); layout.addWidget(brand); layout.addSpacing(22)
        self.nav_buttons = []
        groups = [("DOWNLOAD", [("Single Video", 0), ("Multiple Videos", 1), ("Playlist", 2)]), ("LIBRARY", [("Download Queue", 3), ("History", 4), ("Failed", 5)]), ("SYSTEM", [("Settings", 6)])]
        for title, entries in groups:
            label = QLabel(title); label.setObjectName("Muted"); layout.addWidget(label)
            for name, index in entries:
                nav = QPushButton(name); nav.setObjectName("Nav"); nav.setProperty("active", index == 0); nav.clicked.connect(lambda checked=False, i=index: self.show_page(i)); layout.addWidget(nav); self.nav_buttons.append(nav)
            layout.addSpacing(10)
        layout.addStretch()
        mini = button("Mini Mode", self.toggle_mini_mode); layout.addWidget(mini)
        return frame

    def _topbar(self) -> QFrame:
        frame = QFrame(); frame.setObjectName("TopBar"); row = QHBoxLayout(frame); row.setContentsMargins(14, 9, 14, 9)
        self.top_title = QLabel("Single Video"); self.top_title.setObjectName("PageTitle"); row.addWidget(self.top_title); row.addStretch()
        self.search = QLineEdit(); self.search.setPlaceholderText("Search downloads..."); self.search.setMaximumWidth(220); row.addWidget(self.search)
        row.addWidget(button("Mini", self.toggle_mini_mode)); return frame

    def _surface(self, title: str, subtitle: str = "") -> tuple[QFrame, QVBoxLayout]:
        frame = QFrame(); frame.setObjectName("Surface"); layout = QVBoxLayout(frame); layout.setContentsMargins(22, 20, 22, 20); layout.setSpacing(12)
        heading = QLabel(title); heading.setObjectName("PageTitle"); layout.addWidget(heading)
        if subtitle:
            note = QLabel(subtitle); note.setObjectName("Muted"); layout.addWidget(note)
        return frame, layout

    def _single_page(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(4, 8, 4, 8)
        frame, form = self._surface("Download Video", "Paste a YouTube video URL and choose the output format.")
        self.single_url = QLineEdit(); self.single_url.setPlaceholderText("https://www.youtube.com/watch?v=..."); form.addWidget(QLabel("Video URL")); form.addWidget(self.single_url)
        row = QHBoxLayout(); self.single_quality = QComboBox(); self.single_quality.addItems(QUALITY); row.addWidget(self.single_quality, 1); self.single_folder = QLineEdit(self.settings.get("default_save_folder", str(Path.home() / "Downloads"))); row.addWidget(self.single_folder, 2); row.addWidget(button("Change", self.choose_folder)); form.addLayout(row)
        options = QHBoxLayout(); self.single_thumb = QCheckBox("Download cover"); self.single_subs = QCheckBox("Download subtitles"); options.addWidget(self.single_thumb); options.addWidget(self.single_subs); options.addStretch(); form.addLayout(options); form.addWidget(button("Download Video", self.add_single, True)); layout.addWidget(frame); layout.addStretch(); return page

    def _multi_page(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(4, 8, 4, 8)
        frame, form = self._surface("Multiple Videos", "Paste arbitrary text. Only individual YouTube video URLs are extracted; playlists are ignored here.")
        self.multi_text = QTextEdit(); self.multi_text.setPlaceholderText("Paste notes, titles, and video URLs here..."); form.addWidget(self.multi_text)
        row = QHBoxLayout(); row.addWidget(button("Extract URLs", self.extract_multi)); self.multi_quality = QComboBox(); self.multi_quality.addItems(QUALITY); row.addWidget(self.multi_quality); form.addLayout(row)
        self.multi_summary = QLabel("No videos detected"); self.multi_summary.setObjectName("Muted"); form.addWidget(self.multi_summary)
        self.multi_list = QListWidget(); form.addWidget(self.multi_list, 1); form.addWidget(button("Download Selected", self.add_multi, True)); layout.addWidget(frame); return page

    def _playlist_page(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(4, 8, 4, 8)
        frame, form = self._surface("Playlist", "Load one playlist through yt-dlp. Unavailable entries remain visible and are skipped independently.")
        row = QHBoxLayout(); self.playlist_url = QLineEdit(); self.playlist_url.setPlaceholderText("Playlist URL"); row.addWidget(self.playlist_url, 1); row.addWidget(button("Load Playlist", self.load_playlist)); form.addLayout(row)
        self.playlist_summary = QLabel("No playlist loaded"); self.playlist_summary.setObjectName("Muted"); form.addWidget(self.playlist_summary)
        self.playlist_list = QListWidget(); form.addWidget(self.playlist_list, 1); form.addWidget(button("Download Selected", self.add_playlist, True)); layout.addWidget(frame); return page

    def _queue_page(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(4, 8, 4, 8)
        frame, form = self._surface("Download Queue", "Monitor progress and control the active queue.")
        controls = QHBoxLayout(); controls.addWidget(button("Pause All", self.manager.pause)); controls.addWidget(button("Resume All", self.manager.resume)); controls.addWidget(button("Cancel Selected", self.cancel_selected_queue)); controls.addWidget(button("Reset Queue", self.manager.reset)); controls.addStretch(); form.addLayout(controls)
        self.queue_list = QListWidget(); form.addWidget(self.queue_list, 1); layout.addWidget(frame); return page

    def _history_page(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(4, 8, 4, 8); frame, form = self._surface("History", "Completed downloads remain available in your local state."); self.history_list = QListWidget(); form.addWidget(self.history_list); layout.addWidget(frame); return page

    def _failed_page(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(4, 8, 4, 8); frame, form = self._surface("Failed Downloads", "Retry an error or incomplete item from the queue."); self.failed_list = QListWidget(); form.addWidget(self.failed_list); layout.addWidget(frame); return page

    def _settings_page(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(4, 8, 4, 8); frame, form = self._surface("Settings", "Application preferences and engine status."); row = QHBoxLayout(); self.settings_folder = QLineEdit(self.settings.get("default_save_folder", "")); row.addWidget(self.settings_folder, 1); row.addWidget(button("Change", self.choose_settings_folder)); row.addWidget(button("Save", self.save_preferences, True)); form.addWidget(QLabel("Default download directory")); form.addLayout(row); status = engine_status(); form.addWidget(QLabel("Engine: " + "  ".join(f"{key} {'Ready' if value else 'Missing'}" for key, value in status.items()))); layout.addWidget(frame); layout.addStretch(); return page

    def _statusbar(self) -> QFrame:
        frame = QFrame(); frame.setObjectName("StatusBar"); row = QHBoxLayout(frame); row.setContentsMargins(12, 6, 12, 6); self.status_label = QLabel("Ready"); self.status_label.setObjectName("Muted"); row.addWidget(self.status_label); row.addStretch(); self.stats_label = QLabel(); self.stats_label.setObjectName("Muted"); row.addWidget(self.stats_label); return frame

    def show_page(self, index: int) -> None:
        self.pages.setCurrentIndex(index); self.top_title.setText(["Single Video", "Multiple Videos", "Playlist", "Download Queue", "History", "Failed", "Settings"][index])
        for position, nav in enumerate(self.nav_buttons): nav.setProperty("active", position == index); nav.style().unpolish(nav); nav.style().polish(nav)

    def choose_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder", self.single_folder.text());
        if folder: self.single_folder.setText(folder)

    def choose_settings_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder", self.settings_folder.text());
        if folder: self.settings_folder.setText(folder)

    def save_preferences(self) -> None:
        self.settings["default_save_folder"] = self.settings_folder.text(); save_settings(self.settings); self.single_folder.setText(self.settings_folder.text()); self.status_label.setText("Settings saved")

    def _task(self, url: str, title: str, quality: str, folder: str, **extra) -> dict:
        return {"id": str(uuid.uuid4()), "url": url, "title": title, "quality": quality, "folder": folder, "thumb": False, "subs": False, "status": "Queued", "progress": 0.0, "speed": "", "eta": "", "detail": "Queued", **extra}

    def add_single(self) -> None:
        if not self.single_url.text().strip(): return self._show_message("Enter a video URL")
        task = self._task(self.single_url.text().strip(), "Single Video", self.single_quality.currentText(), self.single_folder.text(), thumb=self.single_thumb.isChecked(), subs=self.single_subs.isChecked())
        self.manager.add([task]); self.show_page(3)

    def extract_multi(self) -> None:
        parsed = extract_video_urls(self.multi_text.toPlainText()); self.multi_items = [{"url": url, "title": f"Video {url.rsplit('=', 1)[-1]}", "quality": self.multi_quality.currentText()} for url in parsed.urls]
        self.multi_list.clear(); self.multi_list.addItems([f"{index:02d}  {item['title']}" for index, item in enumerate(self.multi_items, 1)]); self.multi_summary.setText(f"{len(parsed.urls)} videos detected  |  {parsed.duplicates_removed} duplicates removed  |  {parsed.playlists_ignored} playlists ignored")

    def add_multi(self) -> None:
        tasks = [self._task(item["url"], item["title"], item["quality"], self.single_folder.text(), source="multiple") for item in self.multi_items]
        if tasks: self.manager.add(tasks); self.show_page(3)

    def load_playlist(self) -> None:
        url = self.playlist_url.text().strip()
        if not url: return self._show_message("Enter a playlist URL")
        self.playlist_summary.setText("Loading playlist...")
        threading.Thread(target=self._load_playlist_worker, args=(url,), daemon=True).start()

    def _load_playlist_worker(self, url: str) -> None:
        try: self.signals.loaded.emit(load_playlist(url))
        except Exception as exc: self.signals.failed.emit(str(exc)[:100])

    def _playlist_loaded(self, entries) -> None:
        self.playlist_items = [{"index": entry.index, "title": entry.title, "url": entry.url, "valid": entry.valid, "quality": self.single_quality.currentText()} for entry in entries]; self.playlist_list.clear()
        for item in self.playlist_items: self.playlist_list.addItem(f"{'Ready' if item['valid'] else 'Skipped'}   #{item['index']:02d}  {item['title']}")
        self.playlist_summary.setText(f"{len(entries)} entries loaded  |  {sum(item['valid'] for item in self.playlist_items)} available")

    def add_playlist(self) -> None:
        tasks = [self._task(item["url"], item["title"], item["quality"], self.single_folder.text(), playlist_index=item["index"], source="playlist") for item in self.playlist_items if item["valid"]]
        if tasks: self.manager.add(tasks); self.show_page(3)

    def cancel_selected_queue(self) -> None:
        row = self.queue_list.currentRow()
        if 0 <= row < len(self.manager.tasks):
            self.manager.cancel(self.manager.tasks[row].get("id", ""))

    def refresh_queue(self) -> None:
        tasks = self.manager.tasks; counts = {}
        for task in tasks: counts[task.get("status", "Queued")] = counts.get(task.get("status", "Queued"), 0) + 1
        self.stats_label.setText("  ".join(f"{key}: {value}" for key, value in sorted(counts.items())) or "Queue empty")
        if not hasattr(self, "queue_list"): return
        self.queue_list.clear(); self.history_list.clear(); self.failed_list.clear()
        for task in tasks:
            line = f"{task.get('title', 'Video')}  |  {task.get('status', 'Queued')}  |  {task.get('detail', '')}"
            item = QListWidgetItem(line); self.queue_list.addItem(item)
            if task.get("status") == "Completed": self.history_list.addItem(line)
            if task.get("status") in {"Error", "Incomplete", "Skipped"}: self.failed_list.addItem(line)

    def toggle_mini_mode(self) -> None:
        self.setWindowFlag(Qt.WindowStaysOnTopHint, not bool(self.windowFlags() & Qt.WindowStaysOnTopHint)); self.show(); self.resize(390, 190 if self.width() > 500 else 700)

    def _show_message(self, message: str) -> None:
        self.status_label.setText(message)


def run() -> None:
    app = QApplication.instance() or QApplication([])
    app.setStyleSheet((Path(__file__).with_name("styles.qss")).read_text(encoding="utf-8"))
    window = MainWindow(); window.show(); app.exec()
