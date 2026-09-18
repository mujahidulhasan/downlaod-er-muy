from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

COLORS = {"background": "#0B0F14", "surface": "#111820", "elevated": "#171F29", "input": "#1C2530", "border": "#293441", "primary": "#F5F7FA", "secondary": "#8B98A7", "accent": "#3B82F6", "success": "#22C55E", "warning": "#F59E0B", "error": "#EF4444"}

def apply_dark_palette(app: QApplication) -> None:
    palette = QPalette(); palette.setColor(QPalette.Window, QColor(COLORS["background"])); palette.setColor(QPalette.Base, QColor(COLORS["input"])); palette.setColor(QPalette.Text, QColor(COLORS["primary"])); palette.setColor(QPalette.ButtonText, QColor(COLORS["primary"])); app.setPalette(palette)
