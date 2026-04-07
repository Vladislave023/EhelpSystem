from __future__ import annotations

import re

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
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


class FeaturesPage(QWidget):
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
        title = QLabel("Признаки")
        title.setObjectName("PageTitle")
        title_block.addWidget(title)

        self.subtitle = QLabel("Загрузка данных из базы знаний")
        self.subtitle.setObjectName("MutedText")
        title_block.addWidget(self.subtitle)
        header_layout.addLayout(title_block, 1)

        reload_button = QPushButton("Обновить")
        reload_button.clicked.connect(self.refresh)
        header_layout.addWidget(reload_button)

        delete_button = QPushButton("Удалить выбранный")
        delete_button.setObjectName("DangerButton")
        delete_button.clicked.connect(self.delete_selected_feature)
        header_layout.addWidget(delete_button)

        layout.addLayout(header_layout)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(
            ["Название признака", "Допустимые значения", "Нормальные значения"]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(self.table, 1)

        form_card = QFrame()
        form_card.setObjectName("SectionCard")
        layout.addWidget(form_card)

        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(18, 18, 18, 18)
        form_layout.setSpacing(14)

        form_title = QLabel("Добавить признак")
        form_title.setObjectName("SectionTitle")
        form_layout.addWidget(form_title)

        template_row = QHBoxLayout()
        template_row.setSpacing(12)

        self.template_combo = QComboBox()
        self.template_combo.addItem("Готовый шаблон...")
        self.template_combo.currentIndexChanged.connect(self.apply_template)
        template_row.addWidget(self.template_combo, 1)

        template_hint = QLabel(
            "Выберите шаблон, чтобы автоматически заполнить поля."
        )
        template_hint.setObjectName("MutedText")
        template_row.addWidget(template_hint, 2)

        form_layout.addLayout(template_row)

        row = QHBoxLayout()
        row.setSpacing(12)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Название признака")
        row.addWidget(self.name_input, 2)

        self.allowed_input = QLineEdit()
        self.allowed_input.setPlaceholderText("Допустимые значения, например R[0;10]")
        row.addWidget(self.allowed_input, 1)

        self.normal_input = QLineEdit()
        self.normal_input.setPlaceholderText("Нормальные значения, например R[0;0]")
        row.addWidget(self.normal_input, 1)

        add_button = QPushButton("Добавить")
        add_button.setObjectName("PrimaryButton")
        add_button.clicked.connect(self.add_feature)
        row.addWidget(add_button)

        form_layout.addLayout(row)

        hint = QLabel(
            "Поддерживаются форматы I[a;b], R[a;b], одно число 0 и короткая запись 0;1."
        )
        hint.setObjectName("MutedText")
        form_layout.addWidget(hint)

        scope_hint = QLabel(
            "Чтобы признак использовался при анализе, добавьте его в правила диагнозов."
        )
        scope_hint.setObjectName("MutedText")
        scope_hint.setWordWrap(True)
        form_layout.addWidget(scope_hint)

        self.refresh()

    def refresh(self) -> None:
        self.editor.reload()
        features = self.editor.list_features()

        self.table.setRowCount(len(features))
        for row_index, feature in enumerate(features):
            self._set_cell(row_index, 0, feature.name)
            self._set_cell(row_index, 1, str(feature.allowed_values))
            self._set_cell(row_index, 2, str(feature.normal_values))

        self.table.resizeColumnsToContents()
        self.subtitle.setText(f"Всего признаков: {len(features)}")
        self._reload_templates(features)

    def add_feature(self) -> None:
        name = self.name_input.text().strip()
        allowed_values = self._normalize_range_input(self.allowed_input.text().strip())
        normal_values = self._normalize_range_input(self.normal_input.text().strip())

        if not name or not allowed_values or not normal_values:
            self._show_error("Заполните все поля для нового признака.")
            return

        try:
            self.editor.add_feature(
                name=name,
                allowed_values=allowed_values,
                normal_values=normal_values,
            )
        except (DomainError, ValueError) as error:
            self._show_error(str(error))
            return

        self.name_input.clear()
        self.allowed_input.clear()
        self.normal_input.clear()
        self.template_combo.setCurrentIndex(0)
        self.refresh()

    def delete_selected_feature(self) -> None:
        selected_ranges = self.table.selectionModel().selectedRows()
        if not selected_ranges:
            self._show_error("Сначала выберите строку с признаком.")
            return

        feature_name = self.table.item(selected_ranges[0].row(), 0).text()

        try:
            self.editor.delete_feature(feature_name)
        except DomainError as error:
            self._show_error(str(error))
            return

        self.refresh()

    def _set_cell(self, row: int, column: int, text: str) -> None:
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.table.setItem(row, column, item)

    def apply_template(self, index: int) -> None:
        if index <= 0:
            return

        self.name_input.setText(self.template_combo.currentData(Qt.UserRole + 1)["name"])
        self.allowed_input.setText(
            self.template_combo.currentData(Qt.UserRole + 1)["allowed_values"]
        )
        self.normal_input.setText(
            self.template_combo.currentData(Qt.UserRole + 1)["normal_values"]
        )

    def _reload_templates(self, features) -> None:
        current_data = self.template_combo.currentData(Qt.UserRole + 1)
        current_name = current_data["name"] if isinstance(current_data, dict) else None

        self.template_combo.blockSignals(True)
        self.template_combo.clear()
        self.template_combo.addItem("Готовый шаблон...")

        for feature in features:
            self.template_combo.addItem(feature.name)
            self.template_combo.setItemData(
                self.template_combo.count() - 1,
                {
                    "name": feature.name,
                    "allowed_values": str(feature.allowed_values),
                    "normal_values": str(feature.normal_values),
                },
                Qt.UserRole + 1,
            )

        if current_name is not None:
            for index in range(1, self.template_combo.count()):
                item_data = self.template_combo.itemData(index, Qt.UserRole + 1)
                if item_data["name"] == current_name:
                    self.template_combo.setCurrentIndex(index)
                    break
            else:
                self.template_combo.setCurrentIndex(0)
        else:
            self.template_combo.setCurrentIndex(0)

        self.template_combo.blockSignals(False)

    def _normalize_range_input(self, value: str) -> str:
        stripped = value.replace(" ", "")
        if not stripped:
            return stripped

        if stripped.startswith(("I[", "R[")):
            return stripped

        single_number_match = re.fullmatch(r"-?\d+(?:\.\d+)?", stripped)
        if single_number_match:
            kind = "R" if "." in stripped else "I"
            return f"{kind}[{stripped};{stripped}]"

        short_range_match = re.fullmatch(r"(-?\d+(?:\.\d+)?)[;,](-?\d+(?:\.\d+)?)", stripped)
        if short_range_match:
            left, right = short_range_match.groups()
            kind = "R" if "." in left or "." in right else "I"
            return f"{kind}[{left};{right}]"

        return stripped

    def _show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Ошибка", message)
