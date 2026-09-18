from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout
from .progress_card import ProgressCard

class QueueCard(QFrame):
    def __init__(self, task, retry, cancel, remove):
        super().__init__(); self.task_id = task.id; self.setObjectName("Surface"); row = QHBoxLayout(self); body = QVBoxLayout(); self.card = ProgressCard(task); body.addWidget(self.card); row.addLayout(body, 1)
        for text, callback in (("Retry", retry), ("Cancel", cancel), ("Remove", remove)):
            button = QPushButton(text); button.clicked.connect(lambda checked=False, value=task.id: callback(value)); row.addWidget(button)
    def update_task(self, task): self.card.update_task(task)
