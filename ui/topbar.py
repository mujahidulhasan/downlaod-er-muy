from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton

class Topbar(QFrame):
    def __init__(self, mini_mode):
        super().__init__(); self.setObjectName("Topbar"); row = QHBoxLayout(self); row.setContentsMargins(14,9,14,9); self.title = QLabel("Home"); self.title.setObjectName("PageTitle"); row.addWidget(self.title); row.addStretch(); search = QLineEdit(); search.setPlaceholderText("Search downloads..."); search.setMaximumWidth(220); row.addWidget(search); mini = QPushButton("Mini"); mini.clicked.connect(mini_mode); row.addWidget(mini)
    def set_title(self, title): self.title.setText(title)
