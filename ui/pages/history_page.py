from PySide6.QtWidgets import QLabel, QListWidget, QPushButton, QVBoxLayout, QWidget
class HistoryPage(QWidget):
    def __init__(self, store):
        super().__init__(); self.store = store; layout = QVBoxLayout(self); title = QLabel("History"); title.setObjectName("PageTitle"); layout.addWidget(title); clear = QPushButton("Clear History"); clear.clicked.connect(self.clear); layout.addWidget(clear); self.list = QListWidget(); layout.addWidget(self.list)
    def refresh(self): self.list.clear(); self.list.addItems([f"{item.title}  |  {item.status}  |  {item.quality}" for item in self.store.entries])
    def clear(self): self.store.clear(); self.refresh()
