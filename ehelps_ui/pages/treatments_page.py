from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
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


class TreatmentsPage(QWidget):
    def __init__(self, editor: KnowledgeBaseEditorService, parent=None) -> None:
        super().__init__(parent)
        self.editor = editor
        self.current_treatment_name: str | None = None

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
        title = QLabel("Названия лечения")
        title.setObjectName("PageTitle")
        title_block.addWidget(title)

        self.subtitle = QLabel("Список терминов лечения из базы знаний.")
        self.subtitle.setObjectName("MutedText")
        title_block.addWidget(self.subtitle)
        header_layout.addLayout(title_block, 1)

        refresh_button = QPushButton("Обновить")
        refresh_button.clicked.connect(self.refresh)
        header_layout.addWidget(refresh_button)

        delete_button = QPushButton("Удалить выбранное")
        delete_button.setObjectName("DangerButton")
        delete_button.clicked.connect(self.delete_selected_treatment)
        header_layout.addWidget(delete_button)

        layout.addLayout(header_layout)

        self.table = QTableWidget(0, 1)
        self.table.setHorizontalHeaderLabels(["Название лечения"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.itemSelectionChanged.connect(self.on_treatment_selected)
        layout.addWidget(self.table, 1)

        form_card = QFrame()
        form_card.setObjectName("SectionCard")
        layout.addWidget(form_card)

        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(18, 18, 18, 18)
        form_layout.setSpacing(14)

        form_title = QLabel("Редактирование названия лечения")
        form_title.setObjectName("SectionTitle")
        form_layout.addWidget(form_title)

        row = QHBoxLayout()
        row.setSpacing(12)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Введите название лечения")
        row.addWidget(self.name_input, 1)

        add_button = QPushButton("Добавить")
        add_button.setObjectName("PrimaryButton")
        add_button.clicked.connect(self.add_treatment)
        row.addWidget(add_button)

        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self.save_treatment)
        row.addWidget(save_button)

        form_layout.addLayout(row)

        hint = QLabel(
            "Поле описания скрыто: в текущей онтологии используется только название лечения."
        )
        hint.setObjectName("MutedText")
        hint.setWordWrap(True)
        form_layout.addWidget(hint)

        self.refresh()

    def refresh(self) -> None:
        self.editor.reload()
        treatments = self.editor.list_treatments()

        self.table.setRowCount(len(treatments))
        for row_index, treatment in enumerate(treatments):
            item = QTableWidgetItem(treatment.name)
            item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.table.setItem(row_index, 0, item)

        self.subtitle.setText(f"Всего названий лечения: {len(treatments)}")
        self.table.resizeColumnsToContents()

        if self.current_treatment_name is not None:
            for row_index in range(self.table.rowCount()):
                if self.table.item(row_index, 0).text() == self.current_treatment_name:
                    self.table.selectRow(row_index)
                    break
            else:
                self.current_treatment_name = None
                self.name_input.clear()
        elif self.table.rowCount():
            self.table.selectRow(0)
        else:
            self.name_input.clear()

    def on_treatment_selected(self) -> None:
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            self.current_treatment_name = None
            self.name_input.clear()
            return

        row_index = selected_rows[0].row()
        self.current_treatment_name = self.table.item(row_index, 0).text()
        self.name_input.setText(self.current_treatment_name)

    def add_treatment(self) -> None:
        name = self.name_input.text().strip()
        if not name:
            self._show_error("Введите название лечения.")
            return

        try:
            self.editor.add_treatment(name=name, description="")
        except DomainError as error:
            self._show_error(str(error))
            return

        self.current_treatment_name = name
        self.refresh()

    def save_treatment(self) -> None:
        if self.current_treatment_name is None:
            self._show_error("Сначала выберите название лечения.")
            return

        new_name = self.name_input.text().strip()
        if not new_name:
            self._show_error("Название лечения не должно быть пустым.")
            return

        try:
            self.editor.update_treatment(
                self.current_treatment_name,
                new_name=new_name,
            )
        except DomainError as error:
            self._show_error(str(error))
            return

        self.current_treatment_name = new_name
        self.refresh()

    def delete_selected_treatment(self) -> None:
        if self.current_treatment_name is None:
            self._show_error("Сначала выберите название лечения.")
            return

        try:
            self.editor.delete_treatment(self.current_treatment_name)
        except DomainError as error:
            self._show_error(str(error))
            return

        self.current_treatment_name = None
        self.refresh()

    def _show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Ошибка", message)
