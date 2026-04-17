from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


def format_numeric(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{value:g}"


class DiagnosticResultPage(QWidget):
    def __init__(
        self,
        *,
        on_back_requested: Callable[[], None] | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.on_back_requested = on_back_requested

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
        title = QLabel("Результат диагностики")
        title.setObjectName("PageTitle")
        title_block.addWidget(title)

        self.subtitle = QLabel("Сначала заполните исходные данные и запустите анализ.")
        self.subtitle.setObjectName("MutedText")
        self.subtitle.setWordWrap(True)
        title_block.addWidget(self.subtitle)
        header_layout.addLayout(title_block, 1)

        back_button = QPushButton("Вернуться к вводу")
        back_button.clicked.connect(self._go_back)
        header_layout.addWidget(back_button)

        layout.addLayout(header_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        layout.addWidget(scroll, 1)

        content = QWidget()
        scroll.setWidget(content)

        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(18)

        self.summary_card = self._create_section_card("Введенные значения")
        self.summary_text = QLabel("Результат еще не рассчитан.")
        self.summary_text.setObjectName("MutedText")
        self.summary_text.setWordWrap(True)
        self.summary_card.layout().addWidget(self.summary_text)

        self.expert_card = self._create_section_card("Экспертная система")
        self.expert_status = QLabel("Ожидание расчета.")
        self.expert_status.setObjectName("ResultValue")
        self.expert_status.setWordWrap(True)
        self.expert_card.layout().addWidget(self.expert_status)

        self.expert_details = QLabel("")
        self.expert_details.setObjectName("MutedText")
        self.expert_details.setWordWrap(True)
        self.expert_card.layout().addWidget(self.expert_details)

        self.expert_actions = QLabel("")
        self.expert_actions.setObjectName("MutedText")
        self.expert_actions.setWordWrap(True)
        self.expert_card.layout().addWidget(self.expert_actions)

        self.explanation_text = QLabel("")
        self.explanation_text.setObjectName("MutedText")
        self.explanation_text.setWordWrap(True)
        self.expert_card.layout().addWidget(self.explanation_text)

        self.hypotheses_card = self._create_section_card("Алгоритм опровержения гипотез")
        self.hypotheses_container = QVBoxLayout()
        self.hypotheses_container.setSpacing(12)
        self.hypotheses_card.layout().addLayout(self.hypotheses_container)

        self.ml_card = self._create_section_card("ML-прогноз")
        self.ml_status = QLabel("ML-результат еще не рассчитан.")
        self.ml_status.setObjectName("ResultValue")
        self.ml_status.setWordWrap(True)
        self.ml_card.layout().addWidget(self.ml_status)

        self.ml_details = QLabel("")
        self.ml_details.setObjectName("MutedText")
        self.ml_details.setWordWrap(True)
        self.ml_card.layout().addWidget(self.ml_details)

        self.ml_options = QLabel("")
        self.ml_options.setObjectName("MutedText")
        self.ml_options.setWordWrap(True)
        self.ml_card.layout().addWidget(self.ml_options)

        self.clear_result()

    def clear_result(self) -> None:
        self.subtitle.setText("Сначала заполните исходные данные и запустите анализ.")
        self.summary_text.setText("Результат еще не рассчитан.")
        self.expert_status.setText("Ожидание расчета.")
        self.expert_details.clear()
        self.expert_actions.clear()
        self.explanation_text.clear()
        self.ml_status.setText("ML-результат еще не рассчитан.")
        self.ml_details.clear()
        self.ml_options.clear()
        self._clear_hypotheses()

    def set_analysis(self, values: dict[str, float], analysis: dict[str, object]) -> None:
        self.subtitle.setText(
            "Сравнение результата экспертной системы и модели машинного обучения."
        )
        self.summary_text.setText(
            "\n".join(
                f"- {feature_name}: {format_numeric(raw_value)}"
                for feature_name, raw_value in values.items()
            )
        )

        expert = analysis["expert"]
        if expert["exact_match"]:
            self.expert_status.setText(
                f"Экспертная система определила диагноз: {expert['diagnosis_name']}"
            )
            details_lines = [
                f"Лечение: {expert['treatment_name'] or 'не требуется'}",
            ]
            if expert["treatment_description"]:
                details_lines.append(expert["treatment_description"])
            self.expert_details.setText("\n".join(details_lines))
            self.expert_actions.setText(
                "\n".join(f"- {action}" for action in expert["actions"])
                if expert["actions"]
                else "Действия не требуются."
            )
        else:
            self.expert_status.setText("Экспертная система не нашла точный диагноз.")
            self.expert_details.setText(expert["status_message"])
            self.expert_actions.setText("Используйте результаты опровержения гипотез ниже.")

        self.explanation_text.setText(expert["explanation"])
        self._render_hypotheses(expert["hypotheses"])

        ml = analysis["ml"]
        if not ml["available"]:
            self.ml_status.setText("ML-прогноз недоступен.")
            self.ml_details.setText(ml["message"])
            self.ml_options.clear()
            return

        status = f"ML-модель ({ml['model_name']}) прогнозирует: {ml['predicted_diagnosis']}"
        if ml["confidence"] is not None:
            status += f" | уверенность: {ml['confidence']:.2%}"
        self.ml_status.setText(status)
        self.ml_details.setText(ml["message"])
        self.ml_options.setText(
            "\n".join(
                self._format_ml_option(item["diagnosis_name"], item["score"])
                for item in ml["options"]
            )
        )

    def _render_hypotheses(self, hypotheses: list[dict[str, object]]) -> None:
        self._clear_hypotheses()

        if not hypotheses:
            placeholder = QLabel("Гипотезы пока не рассчитаны.")
            placeholder.setObjectName("MutedText")
            placeholder.setWordWrap(True)
            self.hypotheses_container.addWidget(placeholder)
            return

        for hypothesis in hypotheses:
            hypothesis_card = QFrame()
            hypothesis_card.setObjectName("SectionCard")
            hypothesis_layout = QVBoxLayout(hypothesis_card)
            hypothesis_layout.setContentsMargins(14, 12, 14, 12)
            hypothesis_layout.setSpacing(8)

            title = QLabel(
                f"{hypothesis['diagnosis_name']}"
                + ("  | точное совпадение" if hypothesis["exact_match"] else "")
            )
            title.setObjectName("SectionTitle")
            hypothesis_layout.addWidget(title)

            matched_lines = [
                self._format_feature_check(item)
                for item in hypothesis["matched_features"]
            ]
            rejected_lines = [
                self._format_feature_check(item)
                for item in hypothesis["rejected_features"]
            ]

            matched_label = QLabel(
                "Подошло:\n"
                + ("\n".join(f"- {line}" for line in matched_lines) if matched_lines else "- нет совпавших признаков")
            )
            matched_label.setObjectName("MutedText")
            matched_label.setWordWrap(True)
            hypothesis_layout.addWidget(matched_label)

            rejected_label = QLabel(
                "Не подошло:\n"
                + (
                    "\n".join(f"- {line}" for line in rejected_lines)
                    if rejected_lines
                    else "- опровержений нет"
                )
            )
            rejected_label.setObjectName("MutedText")
            rejected_label.setWordWrap(True)
            hypothesis_layout.addWidget(rejected_label)

            self.hypotheses_container.addWidget(hypothesis_card)

        self.hypotheses_container.addStretch(1)

    def _clear_hypotheses(self) -> None:
        while self.hypotheses_container.count():
            item = self.hypotheses_container.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _create_section_card(self, title_text: str) -> QFrame:
        card = QFrame()
        card.setObjectName("SectionCard")
        self.content_layout.addWidget(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        title = QLabel(title_text)
        title.setObjectName("SectionTitle")
        layout.addWidget(title)
        return card

    @staticmethod
    def _format_feature_check(item: dict[str, object]) -> str:
        return (
            f"{item['feature_name']}: {format_numeric(float(item['patient_value']))} "
            f"при ожидаемом диапазоне {item['expected_range']}"
        )

    @staticmethod
    def _format_ml_option(diagnosis_name: str, score: float | None) -> str:
        if score is None:
            return f"- {diagnosis_name}"
        return f"- {diagnosis_name}: {score:.2%}"

    def _go_back(self) -> None:
        if self.on_back_requested is not None:
            self.on_back_requested()
