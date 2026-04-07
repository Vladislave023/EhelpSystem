from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from ehelps_ui.main_window import MainWindow
from ehelps_ui.theme import APP_STYLESHEET


def run() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("EhelpS")
    app.setStyleSheet(APP_STYLESHEET)

    window = MainWindow()
    window.show()

    return app.exec()
