from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QListWidget, QPushButton, QVBoxLayout, QWidget
from core.playlist import enumerate_playlist
import threading

class PlaylistSignals(QObject): loaded = Signal(object); failed = Signal(str)
class PlaylistPage(QWidget):
    def __init__(self, submit):
        super().__init__(); self.submit = submit; self.entries = []; self.signals = PlaylistSignals(); self.signals.loaded.connect(self.render); self.signals.failed.connect(self.failed); layout = QVBoxLayout(self); title = QLabel("Playlist"); title.setObjectName("PageTitle"); layout.addWidget(title); note = QLabel("Playlist enumeration is separate from Multiple Videos and preserves original indexes."); note.setObjectName("Muted"); layout.addWidget(note); row = QHBoxLayout(); self.url = QLineEdit(); self.url.setPlaceholderText("https://www.youtube.com/playlist?list=..."); row.addWidget(self.url, 1); load = QPushButton("Load Playlist"); load.clicked.connect(self.load); row.addWidget(load); layout.addLayout(row); self.summary = QLabel("No playlist loaded"); self.summary.setObjectName("Muted"); layout.addWidget(self.summary); self.list = QListWidget(); layout.addWidget(self.list, 1); self.quality = QComboBox(); self.quality.addItems(["720p HD (MP4)","1080p Full HD (MP4)","2K Quad HD (1440p MP4)","4K Ultra HD (2160p MP4)","MP3 Audio (320 kbps)"]); layout.addWidget(self.quality); download = QPushButton("Download Selected"); download.setObjectName("Primary"); download.clicked.connect(lambda: self.submit(self.entries, self.quality.currentText())); layout.addWidget(download)
    def load(self): self.summary.setText("Loading playlist..."); threading.Thread(target=self.worker, args=(self.url.text().strip(),), daemon=True).start()
    def worker(self, url):
        try: self.signals.loaded.emit(enumerate_playlist(url))
        except Exception as exc: self.signals.failed.emit(str(exc))
    def render(self, entries): self.entries = entries; self.list.clear(); self.list.addItems([f"{'Ready' if item.valid else 'Skipped'}  #{item.index:02d}  {item.title}" for item in entries]); self.summary.setText(f"{len(entries)} entries  |  {sum(item.valid for item in entries)} available")
    def failed(self, message): self.summary.setText(f"Playlist error: {message[:100]}")
