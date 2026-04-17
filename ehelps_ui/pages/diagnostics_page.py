from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ehelps_backend.application.facade import ExpertSystemFacade
from ehelps_backend.domain.exceptions import DomainError


def format_range_for_display(expression: str) -> str:
    compact = expression.replace(" ", "")
    binary_labels = {
        "I[0;0]": "только 0 (нет)",
        "I[1;1]": "только 1 (да)",
        "I[0;1]": "0 или 1",
    }
    return binary_labels.get(compact, expression)


class DiagnosticsPage(QWidget):
    def __init__(
        self,
        facade: ExpertSystemFacade,
        *,
        on_analysis_ready: Callable[[dict[str, float], dict[str, object]], None] | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.facade = facade
        self.on_analysis_ready = on_analysis_ready
        self.inputs: dict[str, QLineEdit] = {}

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
        title = QLabel("Исходные данные")
        title.setObjectName("PageTitle")
        title_block.addWidget(title)

        subtitle = QLabel(
            "Введите наблюдаемые признаки состояния пациента. Пустые поля считаются равными 0."
        )
        subtitle.setObjectName("MutedText")
        subtitle.setWordWrap(True)
        title_block.addWidget(subtitle)
        header_layout.addLayout(title_block, 1)

        fill_button = QPushButton("Заполнить пример")
        fill_button.clicked.connect(self.fill_example_values)
        header_layout.addWidget(fill_button)

        clear_button = QPushButton("Очистить")
        clear_button.clicked.connect(self.clear_inputs)
        header_layout.addWidget(clear_button)

        run_button = QPushButton("Получить результат")
        run_button.setObjectName("PrimaryButton")
        run_button.clicked.connect(self.run_analysis)
        header_layout.addWidget(run_button)

        layout.addLayout(header_layout)

        note_card = QFrame()
        note_card.setObjectName("SectionCard")
        layout.addWidget(note_card)

        note_layout = QVBoxLayout(note_card)
        note_layout.setContentsMargins(18, 18, 18, 18)
        note_layout.setSpacing(8)

        note_title = QLabel("Как работает анализ")
        note_title.setObjectName("SectionTitle")
        note_layout.addWidget(note_title)

        note_text = QLabel(
            "После расчета система покажет результат экспертной системы, ML-прогноз и "
            "опровержение гипотез по каждому близкому диагнозу."
        )
        note_text.setObjectName("MutedText")
        note_text.setWordWrap(True)
        note_layout.addWidget(note_text)

        form_card = QFrame()
        form_card.setObjectName("SectionCard")
        layout.addWidget(form_card, 1)

        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(18, 18, 18, 18)
        form_layout.setSpacing(14)

        form_title = QLabel("Признаки состояния")
        form_title.setObjectName("SectionTitle")
        form_layout.addWidget(form_title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        form_layout.addWidget(scroll)

        scroll_content = QWidget()
        scroll.setWidget(scroll_content)

        self.form_layout = QVBoxLayout(scroll_content)
        self.form_layout.setContentsMargins(0, 0, 0, 0)
        self.form_layout.setSpacing(12)

        self.refresh()

    def refresh(self) -> None:
        snapshot = self.facade.get_snapshot()

        while self.form_layout.count():
            item = self.form_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.inputs.clear()

        for feature in snapshot.features:
            row_card = QFrame()
            row_card.setObjectName("SectionCard")
            self.form_layout.addWidget(row_card)

            row_layout = QVBoxLayout(row_card)
            row_layout.setContentsMargins(14, 12, 14, 12)
            row_layout.setSpacing(8)

            top_row = QHBoxLayout()
            top_row.setSpacing(12)

            name_label = QLabel(feature.name)
            name_label.setMinimumWidth(240)
            top_row.addWidget(name_label)

            value_input = QLineEdit()
            value_input.setPlaceholderText(
                f"Введите значение, например {feature.normal_values}"
            )
            value_input.setMinimumWidth(260)
            top_row.addWidget(value_input, 1)
            self.inputs[feature.name] = value_input

            range_label = QLabel(
                "Допустимо: "
                f"{format_range_for_display(feature.allowed_values)}"
                " | Норма: "
                f"{format_range_for_display(feature.normal_values)}"
            )
            range_label.setObjectName("MutedText")
            range_label.setWordWrap(True)
            row_layout.addLayout(top_row)
            row_layout.addWidget(range_label)

        self.form_layout.addStretch(1)

    def fill_example_values(self) -> None:
        example = {
            "Глубина повреждения": "2.5",
            "Площадь повреждения": "4.0",
            "Наличие кровотечения": "1",
            "Интенсивность боли": "7",
            "Покраснение кожи": "0",
            "Наличие волдырей": "0",
            "Отёк": "0",
            "Наличие гематомы": "0",
            "Наличие инородного тела": "0",
        }

        for feature_name, input_widget in self.inputs.items():
            input_widget.setText(example.get(feature_name, "0"))

    def clear_inputs(self) -> None:
        for input_widget in self.inputs.values():
            input_widget.clear()

    def run_analysis(self) -> None:
        try:
            values = {
                feature_name: self._parse_numeric(input_widget.text().strip())
                for feature_name, input_widget in self.inputs.items()
            }
            analysis = self.facade.analyze_patient_state(values)
        except (DomainError, ValueError) as error:
            self._show_error("Ошибка анализа", str(error))
            return

        if self.on_analysis_ready is not None:
            self.on_analysis_ready(values, analysis)

    @staticmethod
    def _parse_numeric(value: str) -> float:
        if not value:
            return 0.0

        normalized = value.replace(",", ".")
        return float(normalized)

    def _show_error(self, title: str, message: str) -> None:
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Critical)
        dialog.setWindowTitle(title)
        dialog.setText(message)
        dialog.setStandardButtons(QMessageBox.Ok)
        dialog.setStyleSheet(
            """
            QMessageBox {
                background: #fffaf2;
            }
            QMessageBox QLabel {
                color: #1d2426;
                background: transparent;
                min-width: 360px;
            }
            QMessageBox QPushButton {
                background: #f0e6d8;
                color: #1d2426;
                border: 1px solid #d8c7b1;
                border-radius: 14px;
                padding: 10px 18px;
                min-width: 88px;
                font-weight: 600;
            }
            QMessageBox QPushButton:hover {
                background: #eadbc7;
            }
            """
        )
        dialog.exec()
