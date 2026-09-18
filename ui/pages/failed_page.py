from PySide6.QtWidgets import QLabel, QListWidget, QVBoxLayout, QWidget
class FailedPage(QWidget):
    def __init__(self):
        super().__init__(); layout = QVBoxLayout(self); title = QLabel("Failed Downloads"); title.setObjectName("PageTitle"); layout.addWidget(title); self.list = QListWidget(); layout.addWidget(self.list)
    def refresh(self, tasks): self.list.clear(); self.list.addItems([f"{task.title}  |  {task.status}  |  {task.error or task.detail}" for task in tasks if task.status in {"Failed", "Incomplete", "Skipped", "Cancelled"}])
