import sys
from src.gui import MainWindow
from pathlib import Path
from PySide6.QtWidgets import QApplication

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(Path('style/ct_app_style.qss').read_text())
    window = MainWindow()
    window.show()
    app.exec()