from PySide6.QtWidgets import QFrame, QLabel, QProgressBar, QVBoxLayout

class ProgressCard(QFrame):
    def __init__(self, task):
        super().__init__(); self.setObjectName("Surface"); layout = QVBoxLayout(self); self.title = QLabel(task.title); self.progress = QProgressBar(); self.progress.setValue(int(task.progress)); self.detail = QLabel(task.detail); self.detail.setObjectName("Muted"); layout.addWidget(self.title); layout.addWidget(self.progress); layout.addWidget(self.detail)
    def update_task(self, task): self.title.setText(task.title); self.progress.setValue(int(task.progress)); self.detail.setText(f"{task.status}  {task.detail}  {task.speed}  ETA {task.eta}")
