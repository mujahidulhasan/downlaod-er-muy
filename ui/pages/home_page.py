from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

class HomePage(QWidget):
    def __init__(self, quick_download, recent_provider):
        super().__init__(); layout = QVBoxLayout(self); layout.setSpacing(14); title = QLabel("Welcome back"); title.setObjectName("PageTitle"); layout.addWidget(title); note = QLabel("A focused workspace for reliable video downloads."); note.setObjectName("Muted"); layout.addWidget(note)
        row = QHBoxLayout(); self.quick_url = QLineEdit(); self.quick_url.setPlaceholderText("Paste a video URL"); row.addWidget(self.quick_url, 1); button = QPushButton("Download"); button.setObjectName("Primary"); button.clicked.connect(lambda: quick_download(self.quick_url.text())); row.addWidget(button); layout.addLayout(row)
        stats = QGridLayout(); self.stat_labels = {}
        for index, name in enumerate(("Active", "Queued", "Completed", "Failed")):
            card = QFrame(); card.setObjectName("Surface"); card_layout = QVBoxLayout(card); value = QLabel("0"); value.setObjectName("PageTitle"); card_layout.addWidget(value); label = QLabel(name); label.setObjectName("Muted"); card_layout.addWidget(label); self.stat_labels[name] = value; stats.addWidget(card, 0, index)
        layout.addLayout(stats); recent = QLabel("Recent downloads"); recent.setObjectName("PageTitle"); layout.addWidget(recent); self.recent = QLabel("No recent downloads"); self.recent.setObjectName("Muted"); layout.addWidget(self.recent); layout.addStretch(); self.recent_provider = recent_provider
    def refresh(self, tasks):
        counts = {name: 0 for name in self.stat_labels}
        for task in tasks:
            status = task.status; counts["Active"] += status in {"Downloading", "Merging"}; counts["Queued"] += status == "Queued"; counts["Completed"] += status == "Completed"; counts["Failed"] += status in {"Failed", "Incomplete"}
        for name, value in counts.items(): self.stat_labels[name].setText(str(value))
        recent = [task.title for task in tasks if task.status == "Completed"][:5]; self.recent.setText("\n".join(recent) if recent else "No recent downloads")
