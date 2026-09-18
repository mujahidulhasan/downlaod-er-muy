from PySide6.QtWidgets import QLabel

class StatusBadge(QLabel):
    def __init__(self, status="Queued"):
        super().__init__(status); self.setProperty("status", status)
    def set_status(self, status): self.setText(status); self.setProperty("status", status); self.style().unpolish(self); self.style().polish(self)
