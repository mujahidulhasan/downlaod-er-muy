from PySide6.QtWidgets import QMessageBox, QWidget

def show_error(parent: QWidget, message: str) -> None: QMessageBox.critical(parent, "4K Video Downloader Pro", message)
def show_info(parent: QWidget, message: str) -> None: QMessageBox.information(parent, "4K Video Downloader Pro", message)
