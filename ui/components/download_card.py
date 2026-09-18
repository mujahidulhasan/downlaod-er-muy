from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

class DownloadCard(QFrame):
    def __init__(self, title, detail):
        super().__init__(); self.setObjectName("Surface"); layout = QVBoxLayout(self); layout.addWidget(QLabel(title)); label = QLabel(detail); label.setObjectName("Muted"); layout.addWidget(label)
