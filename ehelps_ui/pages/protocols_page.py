from __future__ import annotations

from functools import partial

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ehelps_backend.application.editor import KnowledgeBaseEditorService
from ehelps_backend.domain.entities import Protocol
from ehelps_backend.domain.exceptions import DomainError


class ProtocolsPage(QWidget):
    def __init__(self, editor: KnowledgeBaseEditorService, parent=None) -> None:
        super().__init__(parent)
        self.editor = editor
        self.protocols_by_treatment: dict[str, Protocol] = {}

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
        title = QLabel("Протоколы помощи")
        title.setObjectName("PageTitle")
        title_block.addWidget(title)

        self.subtitle = QLabel("Настройка состава действий для выбранного лечения.")
        self.subtitle.setObjectName("MutedText")
        title_block.addWidget(self.subtitle)
        header_layout.addLayout(title_block, 1)

        refresh_button = QPushButton("Обновить")
        refresh_button.clicked.connect(self.refresh)
        header_layout.addWidget(refresh_button)

        layout.addLayout(header_layout)

        selector_card = QFrame()
        selector_card.setObjectName("SectionCard")
        layout.addWidget(selector_card)

        selector_layout = QVBoxLayout(selector_card)
        selector_layout.setContentsMargins(18, 18, 18, 18)
        selector_layout.setSpacing(12)

        selector_label = QLabel("Выберите название лечения")
        selector_label.setObjectName("SectionTitle")
        selector_layout.addWidget(selector_label)

        self.treatment_combo = QComboBox()
        self.treatment_combo.currentIndexChanged.connect(self.on_treatment_changed)
        selector_layout.addWidget(self.treatment_combo)

        table_card = QFrame()
        table_card.setObjectName("SectionCard")
        layout.addWidget(table_card, 1)

        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(18, 18, 18, 18)
        table_layout.setSpacing(14)

        table_title = QLabel("Действия первой помощи")
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

        self.action_combo = QComboBox()
        self.action_combo.setEditable(True)
        self.action_combo.setInsertPolicy(QComboBox.NoInsert)
        self.action_combo.lineEdit().setPlaceholderText("Действие")
        form_layout.addWidget(self.action_combo, 1)

        add_button = QPushButton("Добавить")
        add_button.setObjectName("PrimaryButton")
        add_button.clicked.connect(self.add_action_to_protocol)
        form_layout.addWidget(add_button)

        self.refresh()

    def refresh(self) -> None:
        self.editor.reload()
        treatments = self.editor.list_treatments()
        protocols = self.editor.list_protocols()
        self.protocols_by_treatment = {
            protocol.treatment_name: protocol for protocol in protocols
        }

        current_treatment = self.current_treatment_name()

        self.treatment_combo.blockSignals(True)
        self.treatment_combo.clear()
        self.treatment_combo.addItem("— Выберите лечение —", None)
        for treatment in treatments:
            self.treatment_combo.addItem(treatment.name, treatment.name)

        if current_treatment is not None:
            for index in range(self.treatment_combo.count()):
                if self.treatment_combo.itemData(index) == current_treatment:
                    self.treatment_combo.setCurrentIndex(index)
                    break
            else:
                self.treatment_combo.setCurrentIndex(0)
        else:
            self.treatment_combo.setCurrentIndex(0)
        self.treatment_combo.blockSignals(False)

        self.on_treatment_changed()

    def current_treatment_name(self) -> str | None:
        return self.treatment_combo.currentData()

    def on_treatment_changed(self) -> None:
        treatment_name = self.current_treatment_name()
        protocol = self.protocols_by_treatment.get(treatment_name) if treatment_name else None
        actions = protocol.actions[:] if protocol is not None else []

        self.table.setRowCount(len(actions))
        for row_index, action_name in enumerate(actions):
            item = QTableWidgetItem(action_name)
            item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.table.setItem(row_index, 0, item)

            delete_button = QPushButton("×")
            delete_button.setObjectName("DangerButton")
            delete_button.clicked.connect(partial(self.remove_action_from_protocol, action_name))
            self.table.setCellWidget(row_index, 1, delete_button)

        if treatment_name is None:
            self.subtitle.setText("Выберите лечение, чтобы собрать протокол помощи.")
        else:
            self.subtitle.setText(
                f"Протокол для лечения «{treatment_name}». Действий: {len(actions)}"
            )

        self._reload_available_actions(actions)
        self.table.resizeRowsToContents()

    def add_action_to_protocol(self) -> None:
        treatment_name = self.current_treatment_name()
        if treatment_name is None:
            self._show_error("Сначала выберите название лечения.")
            return

        action_name = self.action_combo.currentText().strip()
        if not action_name:
            self._show_error("Выберите действие первой помощи.")
            return

        current_actions = self._current_protocol_actions()
        if action_name in current_actions:
            self._show_error("Это действие уже добавлено в протокол.")
            return

        current_actions.append(action_name)
        self._save_protocol(treatment_name, current_actions)

    def remove_action_from_protocol(self, action_name: str) -> None:
        treatment_name = self.current_treatment_name()
        if treatment_name is None:
            return

        current_actions = self._current_protocol_actions()
        current_actions = [item for item in current_actions if item != action_name]
        self._save_protocol(treatment_name, current_actions)

    def _current_protocol_actions(self) -> list[str]:
        actions: list[str] = []
        for row_index in range(self.table.rowCount()):
            item = self.table.item(row_index, 0)
            if item is not None:
                actions.append(item.text())
        return actions

    def _save_protocol(self, treatment_name: str, actions: list[str]) -> None:
        try:
            self.editor.save_protocol(treatment_name, actions)
        except DomainError as error:
            self._show_error(str(error))
            return

        self.refresh()
        for index in range(self.treatment_combo.count()):
            if self.treatment_combo.itemData(index) == treatment_name:
                self.treatment_combo.setCurrentIndex(index)
                break

    def _reload_available_actions(self, used_actions: list[str]) -> None:
        all_actions = self.editor.list_actions()
        available_actions = [action for action in all_actions if action not in used_actions]
        current_text = self.action_combo.currentText()

        self.action_combo.blockSignals(True)
        self.action_combo.clear()
        for action_name in available_actions:
            self.action_combo.addItem(action_name)

        if current_text and current_text in available_actions:
            self.action_combo.setCurrentText(current_text)
        elif self.action_combo.count():
            self.action_combo.setCurrentIndex(0)
        else:
            self.action_combo.setEditText("")
        self.action_combo.blockSignals(False)

    def _show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Ошибка", message)
