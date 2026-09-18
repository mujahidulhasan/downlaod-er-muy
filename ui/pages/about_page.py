from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
class AboutPage(QWidget):
    def __init__(self):
        super().__init__(); layout = QVBoxLayout(self); title = QLabel("About 4K Video Downloader Pro"); title.setObjectName("PageTitle"); layout.addWidget(title); text = QLabel("A native Qt desktop downloader powered by yt-dlp, FFmpeg, and FFprobe."); text.setObjectName("Muted"); layout.addWidget(text); layout.addStretch()
