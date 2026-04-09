from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
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


class DiagnosticsPage(QWidget):
    def __init__(self, facade: ExpertSystemFacade, parent=None) -> None:
        super().__init__(parent)
        self.facade = facade
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
        title = QLabel("Диагностика")
        title.setObjectName("PageTitle")
        title_block.addWidget(title)

        subtitle = QLabel("Введите наблюдаемые значения признаков и запустите анализ.")
        subtitle.setObjectName("MutedText")
        title_block.addWidget(subtitle)
        header_layout.addLayout(title_block, 1)

        fill_button = QPushButton("Заполнить пример")
        fill_button.clicked.connect(self.fill_example_values)
        header_layout.addWidget(fill_button)

        clear_button = QPushButton("Очистить")
        clear_button.clicked.connect(self.clear_inputs)
        header_layout.addWidget(clear_button)

        run_button = QPushButton("Определить состояние")
        run_button.setObjectName("PrimaryButton")
        run_button.clicked.connect(self.run_diagnostics)
        header_layout.addWidget(run_button)

        layout.addLayout(header_layout)

        form_card = QFrame()
        form_card.setObjectName("SectionCard")
        layout.addWidget(form_card)

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

        self.form_grid = QGridLayout(scroll_content)
        self.form_grid.setContentsMargins(0, 0, 0, 0)
        self.form_grid.setHorizontalSpacing(14)
        self.form_grid.setVerticalSpacing(12)

        result_card = QFrame()
        result_card.setObjectName("SectionCard")
        layout.addWidget(result_card)

        result_layout = QVBoxLayout(result_card)
        result_layout.setContentsMargins(18, 18, 18, 18)
        result_layout.setSpacing(12)

        result_title = QLabel("Результат")
        result_title.setObjectName("SectionTitle")
        result_layout.addWidget(result_title)

        self.result_summary = QLabel("Результат еще не рассчитан.")
        self.result_summary.setObjectName("ResultValue")
        self.result_summary.setWordWrap(True)
        result_layout.addWidget(self.result_summary)

        self.result_treatment = QLabel("")
        self.result_treatment.setObjectName("ResultValue")
        self.result_treatment.setWordWrap(True)
        result_layout.addWidget(self.result_treatment)

        self.actions_label = QLabel("Рекомендуемые действия")
        self.actions_label.setObjectName("SectionTitle")
        result_layout.addWidget(self.actions_label)

        self.actions_text = QLabel("После анализа здесь появится список действий.")
        self.actions_text.setObjectName("MutedText")
        self.actions_text.setWordWrap(True)
        result_layout.addWidget(self.actions_text)

        self.explanation_title = QLabel("Обоснование")
        self.explanation_title.setObjectName("SectionTitle")
        result_layout.addWidget(self.explanation_title)

        self.explanation_text = QLabel("Система покажет, почему был выбран именно этот диагноз.")
        self.explanation_text.setObjectName("MutedText")
        self.explanation_text.setWordWrap(True)
        result_layout.addWidget(self.explanation_text)

        self.refresh()

    def refresh(self) -> None:
        snapshot = self.facade.get_snapshot()

        while self.form_grid.count():
            item = self.form_grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.inputs.clear()

        for row_index, feature in enumerate(snapshot.features):
            name_label = QLabel(feature.name)
            self.form_grid.addWidget(name_label, row_index, 0)

            value_input = QLineEdit()
            value_input.setPlaceholderText(
                f"Введите значение, допустимо: {feature.allowed_values}"
            )
            self.form_grid.addWidget(value_input, row_index, 1)
            self.inputs[feature.name] = value_input

            range_label = QLabel(
                f"Допустимо: {feature.allowed_values} | Норма: {feature.normal_values}"
            )
            range_label.setObjectName("MutedText")
            range_label.setWordWrap(True)
            self.form_grid.addWidget(range_label, row_index, 2)

        self.form_grid.setColumnStretch(1, 1)
        self.form_grid.setColumnStretch(2, 1)

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

        self.result_summary.setText("Результат еще не рассчитан.")
        self.result_treatment.setText("")
        self.actions_text.setText("После анализа здесь появится список действий.")
        self.explanation_text.setText(
            "Система покажет, почему был выбран именно этот диагноз."
        )

    def run_diagnostics(self) -> None:
        try:
            values = {
                feature_name: self._parse_numeric(input_widget.text().strip())
                for feature_name, input_widget in self.inputs.items()
            }
            result = self.facade.evaluate_patient_state(values)
        except (DomainError, ValueError) as error:
            QMessageBox.critical(self, "Ошибка анализа", str(error))
            return

        diagnosis_name = result["diagnosis_name"]
        treatment_name = result["treatment_name"] or "не требуется"
        treatment_description = result["treatment_description"] or ""
        actions = result["actions"]
        explanation = result["explanation"]

        self.result_summary.setText(f"Определено состояние: {diagnosis_name}")
        self.result_treatment.setText(
            f"Рекомендуемое лечение: {treatment_name}"
            + (f"\n{treatment_description}" if treatment_description else "")
        )
        self.actions_text.setText(
            "\n".join(f"- {action}" for action in actions) if actions else "Действия не требуются."
        )
        self.explanation_text.setText(explanation)

    @staticmethod
    def _parse_numeric(value: str) -> float:
        if not value:
            raise ValueError("Заполните все значения признаков перед анализом.")

        normalized = value.replace(",", ".")
        return float(normalized)
