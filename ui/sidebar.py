from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout

class Sidebar(QFrame):
    def __init__(self, navigate, mini_mode):
        super().__init__(); self.setObjectName("Sidebar"); self.setFixedWidth(210); layout = QVBoxLayout(self); layout.setContentsMargins(16,18,16,16); brand = QLabel("4K VIDEO\nDOWNLOADER PRO"); brand.setObjectName("Brand"); layout.addWidget(brand); layout.addSpacing(22); self.buttons = []
        groups = [("WORKSPACE", [("Home",0),("Single Video",1),("Multiple Videos",2),("Playlist",3)]),("LIBRARY",[("Queue",4),("History",5),("Failed",6)]),("SYSTEM",[("Settings",7),("About",8)])]
        for title, items in groups:
            label = QLabel(title); label.setObjectName("SectionLabel"); layout.addWidget(label)
            for text, index in items:
                button = QPushButton(text); button.setObjectName("Nav"); button.clicked.connect(lambda checked=False, value=index: navigate(value)); layout.addWidget(button); self.buttons.append(button)
            layout.addSpacing(8)
        layout.addStretch(); mini = QPushButton("Mini Mode"); mini.clicked.connect(mini_mode); layout.addWidget(mini)
    def activate(self, index):
        for position, button in enumerate(self.buttons): button.setProperty("active", position == index); button.style().unpolish(button); button.style().polish(button)
