from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class PlaceholderPage(QWidget):
    def __init__(self, title: str, description: str, parent=None) -> None:
        super().__init__(parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setObjectName("PageCard")
        root.addWidget(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(16)

        page_title = QLabel(title)
        page_title.setObjectName("PageTitle")
        layout.addWidget(page_title)

        description_label = QLabel(description)
        description_label.setObjectName("MutedText")
        description_label.setWordWrap(True)
        layout.addWidget(description_label)

        inner_card = QFrame()
        inner_card.setObjectName("SectionCard")
        layout.addWidget(inner_card, 1)

        inner_layout = QHBoxLayout(inner_card)
        inner_layout.setContentsMargins(24, 24, 24, 24)

        message = QLabel("Экран будет подключен следующим шагом.")
        message.setAlignment(Qt.AlignCenter)
        message.setObjectName("MutedText")
        inner_layout.addWidget(message)
