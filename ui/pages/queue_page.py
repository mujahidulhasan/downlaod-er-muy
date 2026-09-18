from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget
from ui.components.queue_card import QueueCard

class QueuePage(QWidget):
    def __init__(self, manager):
        super().__init__(); self.manager = manager; layout = QVBoxLayout(self); title = QLabel("Download Queue"); title.setObjectName("PageTitle"); layout.addWidget(title); controls = QHBoxLayout();
        for text, callback in (("Pause", manager.pause), ("Resume", manager.resume), ("Clear Completed", manager.clear_completed)): button = QPushButton(text); button.clicked.connect(callback); controls.addWidget(button)
        controls.addStretch(); layout.addLayout(controls); self.cards = QVBoxLayout(); layout.addLayout(self.cards); layout.addStretch()
    def refresh(self, tasks):
        while self.cards.count(): self.cards.takeAt(0).widget().deleteLater()
        for task in tasks: self.cards.addWidget(QueueCard(task, self.manager.retry, self.manager.cancel, self.manager.remove))
