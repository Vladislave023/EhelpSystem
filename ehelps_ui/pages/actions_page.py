from __future__ import annotations

from functools import partial

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ehelps_backend.application.editor import KnowledgeBaseEditorService
from ehelps_backend.domain.exceptions import DomainError


class ActionsPage(QWidget):
    def __init__(self, editor: KnowledgeBaseEditorService, parent=None) -> None:
        super().__init__(parent)
        self.editor = editor

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        card = QFrame()
        card.setObjectName("PageCard")
        root.addWidget(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(18)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        title_block = QVBoxLayout()
        title = QLabel("Действия")
        title.setObjectName("PageTitle")
        title_block.addWidget(title)

        self.subtitle = QLabel("Список действий первой помощи.")
        self.subtitle.setObjectName("MutedText")
        title_block.addWidget(self.subtitle)
        header_layout.addLayout(title_block, 1)

        refresh_button = QPushButton("Обновить")
        refresh_button.clicked.connect(self.refresh)
        header_layout.addWidget(refresh_button)

        layout.addLayout(header_layout)

        table_card = QFrame()
        table_card.setObjectName("SectionCard")
        layout.addWidget(table_card, 1)

        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(18, 18, 18, 18)
        table_layout.setSpacing(14)

        table_title = QLabel("Действия")
        table_title.setObjectName("SectionTitle")
        table_layout.addWidget(table_title)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Действие", ""])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.table.setColumnWidth(1, 56)
        table_layout.addWidget(self.table, 1)

        form_card = QFrame()
        form_card.setObjectName("SectionCard")
        layout.addWidget(form_card)

        form_layout = QHBoxLayout(form_card)
        form_layout.setContentsMargins(18, 18, 18, 18)
        form_layout.setSpacing(12)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Введите действие...")
        self.name_input.returnPressed.connect(self.add_action)
        form_layout.addWidget(self.name_input, 1)

        add_button = QPushButton("Добавить")
        add_button.setObjectName("PrimaryButton")
        add_button.clicked.connect(self.add_action)
        form_layout.addWidget(add_button)

        self.refresh()

    def refresh(self) -> None:
        self.editor.reload()
        actions = self.editor.list_actions()

        self.table.setRowCount(len(actions))
        for row_index, action_name in enumerate(actions):
            item = QTableWidgetItem(action_name)
            item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.table.setItem(row_index, 0, item)

            delete_button = QPushButton("×")
            delete_button.setObjectName("DangerButton")
            delete_button.clicked.connect(partial(self.delete_action, action_name))
            self.table.setCellWidget(row_index, 1, delete_button)

        self.subtitle.setText(f"Всего действий: {len(actions)}")
        self.table.resizeRowsToContents()

    def add_action(self) -> None:
        name = self.name_input.text().strip()
        if not name:
            self._show_error("Введите действие первой помощи.")
            return

        try:
            self.editor.add_action(name)
        except DomainError as error:
            self._show_error(str(error))
            return

        self.name_input.clear()
        self.refresh()

    def delete_action(self, action_name: str) -> None:
        try:
            self.editor.delete_action(action_name)
        except DomainError as error:
            self._show_error(str(error))
            return

        self.refresh()

    def _show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Ошибка", message)
