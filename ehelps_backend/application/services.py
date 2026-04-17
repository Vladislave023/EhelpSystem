from __future__ import annotations

from dataclasses import dataclass

from ehelps_backend.domain.entities import DecisionResult, Diagnosis, KnowledgeBase, PatientState
from ehelps_backend.domain.exceptions import DiagnosisNotFoundError, InvalidPatientStateError


@dataclass(frozen=True, slots=True)
class HypothesisFeatureCheck:
    feature_name: str
    patient_value: float
    expected_range: str
    matches: bool


@dataclass(frozen=True, slots=True)
class HypothesisAnalysis:
    diagnosis_name: str
    exact_match: bool
    matched_features: list[HypothesisFeatureCheck]
    rejected_features: list[HypothesisFeatureCheck]


@dataclass(frozen=True, slots=True)
class DiagnosticAnalysis:
    decision_result: DecisionResult | None
    hypotheses: list[HypothesisAnalysis]


@dataclass(slots=True)
class DiagnosisService:
    knowledge_base: KnowledgeBase

    def evaluate(self, patient_state: PatientState) -> DecisionResult:
        analysis = self.analyze(patient_state)
        if analysis.decision_result is not None:
            return analysis.decision_result
        raise DiagnosisNotFoundError(self._build_no_match_message(analysis.hypotheses))

    def analyze(self, patient_state: PatientState) -> DiagnosticAnalysis:
        self._validate_patient_state(patient_state)

        hypotheses = self._build_hypotheses(patient_state)
        if self._is_healthy(patient_state):
            return DiagnosticAnalysis(
                decision_result=self._build_healthy_result(),
                hypotheses=hypotheses,
            )

        for diagnosis in self.knowledge_base.iter_non_healthy_diagnoses():
            if self._matches_diagnosis(patient_state, diagnosis):
                return DiagnosticAnalysis(
                    decision_result=self._build_result(diagnosis, patient_state),
                    hypotheses=hypotheses,
                )

        return DiagnosticAnalysis(
            decision_result=None,
            hypotheses=hypotheses,
        )

    def _validate_patient_state(self, patient_state: PatientState) -> None:
        if not patient_state.values:
            raise InvalidPatientStateError("Состояние пациента не должно быть пустым.")

        expected_features = set(self.knowledge_base.features)
        provided_features = set(patient_state.values)

        missing_features = sorted(expected_features - provided_features)
        unknown_features = sorted(provided_features - expected_features)

        if missing_features:
            raise InvalidPatientStateError(
                "Не заполнены признаки пациента: " + ", ".join(missing_features)
            )

        if unknown_features:
            raise InvalidPatientStateError(
                "Обнаружены неизвестные признаки: " + ", ".join(unknown_features)
            )

        for feature_name, raw_value in patient_state.values.items():
            feature = self.knowledge_base.features[feature_name]
            if not feature.allowed_values.contains(raw_value):
                raise InvalidPatientStateError(
                    f"Значение {raw_value} для признака '{feature_name}' "
                    f"не входит в допустимый диапазон {feature.allowed_values}."
                )

    def _is_healthy(self, patient_state: PatientState) -> bool:
        for feature_name, raw_value in patient_state.values.items():
            feature = self.knowledge_base.features[feature_name]
            if not feature.normal_values.contains(raw_value):
                return False
        return True

    def _matches_diagnosis(self, patient_state: PatientState, diagnosis: Diagnosis) -> bool:
        for feature_name, allowed_values in diagnosis.feature_ranges.items():
            patient_value = patient_state.values[feature_name]
            if not allowed_values.contains(patient_value):
                return False
        return True

    def _build_healthy_result(self) -> DecisionResult:
        explanation = (
            "Результат определения состояния пациента: 'здоров'.\n"
            "Основание выбора: все введенные значения признаков находятся "
            "в пределах нормальных значений."
        )
        return DecisionResult(
            diagnosis_name="здоров",
            treatment_name=None,
            treatment_description=None,
            actions=[],
            explanation=explanation,
        )

    def _build_result(self, diagnosis: Diagnosis, patient_state: PatientState) -> DecisionResult:
        treatment_name = diagnosis.treatment_name
        treatment_description = None
        actions: list[str] = []

        if treatment_name is not None:
            treatment = self.knowledge_base.treatments[treatment_name]
            protocol = self.knowledge_base.protocols.get(treatment_name)
            treatment_description = treatment.description
            actions = protocol.actions[:] if protocol is not None else []

        matched_lines = []
        for feature_name, allowed_values in diagnosis.feature_ranges.items():
            matched_lines.append(
                f"- {feature_name}: {patient_state.values[feature_name]} "
                f"соответствует {allowed_values}"
            )

        explanation_parts = [
            f"Результат определения состояния пациента: '{diagnosis.name}'.",
            "Основание выбора: значения признаков пациента соответствуют правилу диагноза:",
            *matched_lines,
        ]

        if treatment_name is not None:
            explanation_parts.append(f"Рекомендуемое лечение: '{treatment_name}'.")

        return DecisionResult(
            diagnosis_name=diagnosis.name,
            treatment_name=treatment_name,
            treatment_description=treatment_description,
            actions=actions,
            explanation="\n".join(explanation_parts),
        )

    def _build_hypotheses(self, patient_state: PatientState) -> list[HypothesisAnalysis]:
        hypotheses: list[HypothesisAnalysis] = []

        for diagnosis in self.knowledge_base.iter_non_healthy_diagnoses():
            matched_features: list[HypothesisFeatureCheck] = []
            rejected_features: list[HypothesisFeatureCheck] = []

            for feature_name, allowed_values in diagnosis.feature_ranges.items():
                patient_value = patient_state.values[feature_name]
                check = HypothesisFeatureCheck(
                    feature_name=feature_name,
                    patient_value=patient_value,
                    expected_range=str(allowed_values),
                    matches=allowed_values.contains(patient_value),
                )
                if check.matches:
                    matched_features.append(check)
                else:
                    rejected_features.append(check)

            hypotheses.append(
                HypothesisAnalysis(
                    diagnosis_name=diagnosis.name,
                    exact_match=not rejected_features,
                    matched_features=matched_features,
                    rejected_features=rejected_features,
                )
            )

        hypotheses.sort(
            key=lambda item: (
                len(item.rejected_features),
                -len(item.matched_features),
                item.diagnosis_name,
            )
        )
        return hypotheses

    def _build_no_match_message(self, hypotheses: list[HypothesisAnalysis]) -> str:
        best_matches = hypotheses[:2]

        message_lines = [
            "Не удалось определить точный диагноз по введенным признакам.",
        ]

        if best_matches:
            message_lines.append("Ближайшие варианты и причины несовпадения:")
            for hypothesis in best_matches:
                for check in hypothesis.rejected_features:
                    message_lines.append(
                        f"- {hypothesis.diagnosis_name}: признак '{check.feature_name}' "
                        f"имеет значение {check.patient_value}, ожидается {check.expected_range}"
                    )

        return "\n".join(message_lines)
