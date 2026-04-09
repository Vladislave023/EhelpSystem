from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ehelps_backend.application.editor import KnowledgeBaseEditorService
from ehelps_backend.domain.entities import Diagnosis
from ehelps_backend.domain.exceptions import DomainError


def format_range_for_display(expression: str) -> str:
    compact = expression.replace(" ", "")
    binary_labels = {
        "I[0;0]": "I[0;0]  (только 0 = нет)",
        "I[1;1]": "I[1;1]  (только 1 = да)",
        "I[0;1]": "I[0;1]  (0 = нет, 1 = да)",
    }
    return binary_labels.get(compact, expression)


class DiagnosesPage(QWidget):
    def __init__(self, editor: KnowledgeBaseEditorService, parent=None) -> None:
        super().__init__(parent)
        self.editor = editor
        self.current_diagnosis_name: str | None = None

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
        title_block = QVBoxLayout()
        title = QLabel("Диагнозы")
        title.setObjectName("PageTitle")
        title_block.addWidget(title)

        self.subtitle = QLabel("Настройка правил определения состояний.")
        self.subtitle.setObjectName("MutedText")
        title_block.addWidget(self.subtitle)
        header_layout.addLayout(title_block, 1)

        refresh_button = QPushButton("Обновить")
        refresh_button.clicked.connect(self.refresh)
        header_layout.addWidget(refresh_button)

        delete_button = QPushButton("Удалить диагноз")
        delete_button.setObjectName("DangerButton")
        delete_button.clicked.connect(self.delete_current_diagnosis)
        header_layout.addWidget(delete_button)

        layout.addLayout(header_layout)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        layout.addWidget(splitter, 1)

        left_card = QFrame()
        left_card.setObjectName("SectionCard")
        left_card.setMinimumWidth(260)
        splitter.addWidget(left_card)

        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(18, 18, 18, 18)
        left_layout.setSpacing(14)

        left_title = QLabel("Список диагнозов")
        left_title.setObjectName("SectionTitle")
        left_layout.addWidget(left_title)

        self.diagnosis_list = QListWidget()
        self.diagnosis_list.itemSelectionChanged.connect(self.on_diagnosis_selected)
        left_layout.addWidget(self.diagnosis_list, 1)

        self.new_name_input = QLineEdit()
        self.new_name_input.setPlaceholderText("Название нового диагноза")
        left_layout.addWidget(self.new_name_input)

        add_button = QPushButton("Добавить диагноз")
        add_button.setObjectName("PrimaryButton")
        add_button.clicked.connect(self.add_diagnosis)
        left_layout.addWidget(add_button)

        right_card = QFrame()
        right_card.setObjectName("SectionCard")
        right_card.setMinimumWidth(520)
        splitter.addWidget(right_card)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(18, 18, 18, 18)
        right_layout.setSpacing(14)

        info_title = QLabel("Параметры диагноза")
        info_title.setObjectName("SectionTitle")
        right_layout.addWidget(info_title)

        top_form = QGridLayout()
        top_form.setHorizontalSpacing(12)
        top_form.setVerticalSpacing(10)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Название диагноза")
        top_form.addWidget(QLabel("Название"), 0, 0)
        top_form.addWidget(self.name_input, 0, 1)

        self.treatment_combo = QComboBox()
        top_form.addWidget(QLabel("Лечение"), 1, 0)
        top_form.addWidget(self.treatment_combo, 1, 1)

        save_button = QPushButton("Сохранить изменения")
        save_button.setObjectName("PrimaryButton")
        save_button.clicked.connect(self.save_diagnosis)
        top_form.addWidget(save_button, 0, 2, 2, 1)
        top_form.setColumnStretch(1, 1)

        right_layout.addLayout(top_form)

        self.rules_table = QTableWidget(0, 2)
        self.rules_table.setHorizontalHeaderLabels(
            ["Признак диагноза", "Диапазон значений"]
        )
        self.rules_table.verticalHeader().setVisible(False)
        self.rules_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.rules_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.rules_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.rules_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.rules_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.rules_table.itemSelectionChanged.connect(self.on_rule_selected)
        right_layout.addWidget(self.rules_table, 1)

        rule_form = QHBoxLayout()
        rule_form.setSpacing(12)

        self.feature_combo = QComboBox()
        rule_form.addWidget(self.feature_combo, 1)

        self.range_input = QLineEdit()
        self.range_input.setPlaceholderText("Например I[1;1] или R[0.1;5]")
        rule_form.addWidget(self.range_input, 1)

        self.rule_button = QPushButton("Добавить правило")
        self.rule_button.clicked.connect(self.add_or_update_rule)
        rule_form.addWidget(self.rule_button)

        remove_rule_button = QPushButton("Удалить правило")
        remove_rule_button.clicked.connect(self.remove_selected_rule)
        rule_form.addWidget(remove_rule_button)

        right_layout.addLayout(rule_form)

        self.hint = QLabel(
            "Для диагноза укажите значимые признаки и диапазоны их значений. "
            "Остальные признаки будут считаться нормальными."
        )
        self.hint.setObjectName("MutedText")
        self.hint.setWordWrap(True)
        right_layout.addWidget(self.hint)

        self.refresh()

    def refresh(self) -> None:
        self.editor.reload()
        diagnoses = self.editor.list_diagnoses()
        features = self.editor.list_features()
        treatments = self.editor.list_treatments()

        self.diagnosis_list.clear()
        for diagnosis in diagnoses:
            item = QListWidgetItem(diagnosis.name)
            self.diagnosis_list.addItem(item)

        self.feature_combo.clear()
        for feature in features:
            self.feature_combo.addItem(feature.name)

        self.treatment_combo.clear()
        self.treatment_combo.addItem("Без лечения", None)
        for treatment in treatments:
            self.treatment_combo.addItem(treatment.name, treatment.name)

        self.subtitle.setText(f"Всего диагнозов: {len(diagnoses)}")

        if self.current_diagnosis_name is not None:
            for index in range(self.diagnosis_list.count()):
                if self.diagnosis_list.item(index).text() == self.current_diagnosis_name:
                    self.diagnosis_list.setCurrentRow(index)
                    break
            else:
                self.current_diagnosis_name = None

        if self.current_diagnosis_name is None and self.diagnosis_list.count():
            self.diagnosis_list.setCurrentRow(0)
        elif not self.diagnosis_list.count():
            self.clear_form()

    def on_diagnosis_selected(self) -> None:
        selected_items = self.diagnosis_list.selectedItems()
        if not selected_items:
            self.current_diagnosis_name = None
            self.clear_form()
            return

        diagnosis_name = selected_items[0].text()
        self.current_diagnosis_name = diagnosis_name
        diagnosis = self._get_diagnosis_by_name(diagnosis_name)
        self.load_diagnosis(diagnosis)

    def load_diagnosis(self, diagnosis: Diagnosis) -> None:
        self.name_input.setText(diagnosis.name)
        self.rules_table.setRowCount(0)
        self.range_input.clear()
        self.rule_button.setText("Добавить правило")

        for feature_name, value_range in diagnosis.feature_ranges.items():
            row = self.rules_table.rowCount()
            self.rules_table.insertRow(row)
            self._set_rule_cell(row, 0, feature_name)
            self._set_rule_cell(row, 1, format_range_for_display(str(value_range)), str(value_range))

        treatment_name = diagnosis.treatment_name
        for index in range(self.treatment_combo.count()):
            if self.treatment_combo.itemData(index) == treatment_name:
                self.treatment_combo.setCurrentIndex(index)
                break

    def clear_form(self) -> None:
        self.name_input.clear()
        self.rules_table.setRowCount(0)
        self.treatment_combo.setCurrentIndex(0)
        self.range_input.clear()
        self.rule_button.setText("Добавить правило")

    def add_diagnosis(self) -> None:
        name = self.new_name_input.text().strip()
        if not name:
            QMessageBox.critical(self, "Ошибка", "Введите название диагноза.")
            return

        treatment_name = self.treatment_combo.currentData()
        if name == "здоров":
            treatment_name = None

        try:
            self.editor.add_diagnosis(
                name=name,
                feature_ranges={},
                treatment_name=treatment_name,
            )
        except DomainError as error:
            QMessageBox.critical(self, "Ошибка", str(error))
            return

        self.new_name_input.clear()
        self.current_diagnosis_name = name
        self.refresh()

    def save_diagnosis(self) -> None:
        if self.current_diagnosis_name is None:
            QMessageBox.critical(self, "Ошибка", "Сначала выберите диагноз.")
            return

        new_name = self.name_input.text().strip()
        if not new_name:
            QMessageBox.critical(self, "Ошибка", "Название диагноза не должно быть пустым.")
            return

        feature_ranges: dict[str, str] = {}
        for row in range(self.rules_table.rowCount()):
            feature_name = self.rules_table.item(row, 0).text().strip()
            value_range = (
                self.rules_table.item(row, 1).data(Qt.UserRole)
                or self.rules_table.item(row, 1).text()
            ).strip()
            if not feature_name or not value_range:
                QMessageBox.critical(self, "Ошибка", "Заполните все правила диагноза.")
                return
            feature_ranges[feature_name] = value_range

        treatment_name = self.treatment_combo.currentData()
        if self.current_diagnosis_name == "здоров" or new_name == "здоров":
            treatment_name = None

        try:
            self.editor.update_diagnosis(
                self.current_diagnosis_name,
                new_name=new_name,
                feature_ranges=feature_ranges,
                treatment_name=treatment_name,
            )
        except (DomainError, ValueError) as error:
            QMessageBox.critical(self, "Ошибка", str(error))
            return

        self.current_diagnosis_name = new_name
        self.refresh()

    def delete_current_diagnosis(self) -> None:
        if self.current_diagnosis_name is None:
            QMessageBox.critical(self, "Ошибка", "Сначала выберите диагноз.")
            return

        try:
            self.editor.delete_diagnosis(self.current_diagnosis_name)
        except DomainError as error:
            QMessageBox.critical(self, "Ошибка", str(error))
            return

        self.current_diagnosis_name = None
        self.refresh()

    def add_or_update_rule(self) -> None:
        feature_name = self.feature_combo.currentText().strip()
        value_range = self.range_input.text().strip()

        if not feature_name or not value_range:
            QMessageBox.critical(self, "Ошибка", "Выберите признак и задайте диапазон.")
            return

        for row in range(self.rules_table.rowCount()):
            if self.rules_table.item(row, 0).text() == feature_name:
                self._set_rule_cell(row, 1, format_range_for_display(value_range), value_range)
                self.range_input.clear()
                self.rules_table.clearSelection()
                self.rule_button.setText("Добавить правило")
                return

        row = self.rules_table.rowCount()
        self.rules_table.insertRow(row)
        self._set_rule_cell(row, 0, feature_name)
        self._set_rule_cell(row, 1, format_range_for_display(value_range), value_range)
        self.range_input.clear()
        self.rules_table.clearSelection()
        self.rule_button.setText("Добавить правило")

    def remove_selected_rule(self) -> None:
        selected_rows = self.rules_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.critical(self, "Ошибка", "Сначала выберите правило.")
            return

        self.rules_table.removeRow(selected_rows[0].row())
        self.range_input.clear()
        self.rules_table.clearSelection()
        self.rule_button.setText("Добавить правило")

    def on_rule_selected(self) -> None:
        selected_rows = self.rules_table.selectionModel().selectedRows()
        if not selected_rows:
            self.range_input.clear()
            self.rule_button.setText("Добавить правило")
            return

        row = selected_rows[0].row()
        feature_name = self.rules_table.item(row, 0).text()
        value_range = self.rules_table.item(row, 1).data(Qt.UserRole) or self.rules_table.item(
            row, 1
        ).text()

        for index in range(self.feature_combo.count()):
            if self.feature_combo.itemText(index) == feature_name:
                self.feature_combo.setCurrentIndex(index)
                break

        self.range_input.setText(value_range)
        self.rule_button.setText("Обновить правило")

    def _get_diagnosis_by_name(self, name: str) -> Diagnosis:
        for diagnosis in self.editor.list_diagnoses():
            if diagnosis.name == name:
                return diagnosis
        raise ValueError(f"Диагноз '{name}' не найден.")

    def _set_rule_cell(
        self,
        row: int,
        column: int,
        text: str,
        raw_value: str | None = None,
    ) -> None:
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        if raw_value is not None:
            item.setData(Qt.UserRole, raw_value)
        self.rules_table.setItem(row, column, item)
