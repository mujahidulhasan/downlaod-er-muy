from __future__ import annotations

from pathlib import Path
from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QFileDialog, QLabel, QMainWindow, QStackedWidget, QVBoxLayout, QWidget
from core.models import DownloadTask
from core.queue_manager import QueueManager
from core.runtime import status
from core.settings import load_settings, save_settings
from ui.sidebar import Sidebar
from ui.topbar import Topbar
from ui.pages.about_page import AboutPage
from ui.pages.failed_page import FailedPage
from ui.pages.history_page import HistoryPage
from ui.pages.home_page import HomePage
from ui.pages.multiple_video_page import MultipleVideoPage
from ui.pages.playlist_page import PlaylistPage
from ui.pages.queue_page import QueuePage
from ui.pages.settings_page import SettingsPage
from ui.pages.single_video_page import SingleVideoPage

class QueueBridge(QObject):
    changed = Signal()
    def notify(self, task=None): self.changed.emit()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.settings = load_settings(); self.manager = QueueManager(); self.bridge = QueueBridge(); self.manager.subscribe(self.bridge.notify); self.bridge.changed.connect(self.refresh); self.setWindowTitle("4K Video Downloader Pro"); self.setMinimumSize(900, 620); self.resize(1100, 720)
        root = Path(__file__).resolve().parents[1]; icon = root / "assets" / "app_icon.ico"
        if icon.exists(): self.setWindowIcon(QIcon(str(icon)))
        self.sidebar = Sidebar(self.show_page, self.toggle_mini_mode); self.topbar = Topbar(self.toggle_mini_mode); self.stack = QStackedWidget(); self.pages = [HomePage(self.quick_download, lambda: self.manager.tasks), SingleVideoPage(self.settings, self.add_single), MultipleVideoPage(self.add_multiple), PlaylistPage(self.add_playlist), QueuePage(self.manager), HistoryPage(self.manager.history), FailedPage(), SettingsPage(self.settings, self.save_preferences), AboutPage()]
        for page in self.pages: self.stack.addWidget(page)
        content = QVBoxLayout(); content.setSpacing(12); content.addWidget(self.topbar); content.addWidget(self.stack, 1); engine = QLabel("  ".join(f"{key}: {'Ready' if value else 'Missing'}" for key, value in status().items())); engine.setObjectName("Muted"); content.addWidget(engine)
        root_widget = QWidget(); root_layout = QVBoxLayout(root_widget); root_layout.setContentsMargins(14,14,14,14); root_layout.addLayout(self._main_layout(content)); self.setCentralWidget(root_widget); self.refresh()
    def _main_layout(self, content):
        from PySide6.QtWidgets import QHBoxLayout
        layout = QHBoxLayout(); layout.setSpacing(14); layout.addWidget(self.sidebar); layout.addLayout(content, 1); return layout
    def show_page(self, index):
        self.stack.setCurrentIndex(index); titles = ["Home", "Single Video", "Multiple Videos", "Playlist", "Queue", "History", "Failed", "Settings", "About"]; self.topbar.set_title(titles[index]); self.sidebar.activate(index)
    def toggle_mini_mode(self):
        mini = self.width() > 500; self.sidebar.setVisible(not mini); self.setWindowFlag(Qt.WindowStaysOnTopHint, mini); self.resize(410, 210) if mini else self.resize(1100, 720); self.show()
    def quick_download(self, url):
        if url.strip(): self.add_single(url, self.settings["default_quality"], self.settings["default_folder"], self.settings["subtitles"], False)
    def add_single(self, url, quality, folder, subtitles, thumbnail):
        if not url: return
        self.manager.add([self.manager.create(url, "Single Video", folder, quality=quality, subtitles=subtitles, thumbnail=thumbnail)]); self.show_page(4)
    def add_multiple(self, urls, quality):
        tasks = [self.manager.create(url, f"Video {url.rsplit('=', 1)[-1]}", self.settings["default_folder"], quality=quality, source="multiple") for url in urls]
        if tasks: self.manager.add(tasks); self.show_page(4)
    def add_playlist(self, entries, quality):
        tasks = [self.manager.create(entry.url, entry.title, self.settings["default_folder"], quality=quality, source="playlist", playlist_index=entry.index) for entry in entries if entry.valid]
        if tasks: self.manager.add(tasks); self.show_page(4)
    def save_preferences(self, settings): self.settings = settings; save_settings(settings); self.pages[1].folder.setText(settings["default_folder"])
    def refresh(self):
        self.pages[0].refresh(self.manager.tasks); self.pages[4].refresh(self.manager.tasks); self.pages[5].refresh(); self.pages[6].refresh(self.manager.tasks)
    def closeEvent(self, event): self.manager.paused = True; event.accept()

def run():
    app = QApplication.instance() or QApplication([]); root = Path(__file__).resolve().parent; app.setStyleSheet((root / "styles" / "styles.qss").read_text(encoding="utf-8")); window = MainWindow(); window.show(); app.exec()
