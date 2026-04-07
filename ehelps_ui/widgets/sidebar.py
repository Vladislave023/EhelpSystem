from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QButtonGroup, QFrame, QVBoxLayout, QPushButton, QLabel


@dataclass(frozen=True, slots=True)
class SidebarItem:
    key: str
    title: str


class Sidebar(QFrame):
    page_selected = Signal(str)

    def __init__(self, items: list[SidebarItem], parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("SidebarCard")
        self._buttons: dict[str, QPushButton] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 20, 18, 20)
        layout.setSpacing(12)

        title = QLabel("Разделы")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        note = QLabel("База знаний\nи сценарии помощи")
        note.setObjectName("SidebarNote")
        layout.addWidget(note)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        for item in items:
            button = QPushButton(item.title)
            button.setCheckable(True)
            button.setObjectName("NavButton")
            button.clicked.connect(lambda checked=False, page_key=item.key: self.page_selected.emit(page_key))
            self.button_group.addButton(button)
            self._buttons[item.key] = button
            layout.addWidget(button)

        layout.addStretch(1)

    def set_current(self, key: str) -> None:
        button = self._buttons[key]
        button.setChecked(True)
