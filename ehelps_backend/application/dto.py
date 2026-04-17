from __future__ import annotations

from dataclasses import asdict, dataclass

from ehelps_backend.application.services import DiagnosticAnalysis, HypothesisAnalysis
from ehelps_backend.domain.entities import DecisionResult, Diagnosis, Feature, Protocol, Treatment
from ehelps_ml.prediction import MlPredictionResult


@dataclass(frozen=True, slots=True)
class FeatureDTO:
    name: str
    allowed_values: str
    normal_values: str


@dataclass(frozen=True, slots=True)
class TreatmentDTO:
    name: str
    description: str


@dataclass(frozen=True, slots=True)
class DiagnosisDTO:
    name: str
    feature_ranges: dict[str, str]
    treatment_name: str | None


@dataclass(frozen=True, slots=True)
class ProtocolDTO:
    treatment_name: str
    actions: list[str]


@dataclass(frozen=True, slots=True)
class DecisionResultDTO:
    diagnosis_name: str
    treatment_name: str | None
    treatment_description: str | None
    actions: list[str]
    explanation: str


@dataclass(frozen=True, slots=True)
class HypothesisFeatureCheckDTO:
    feature_name: str
    patient_value: float
    expected_range: str
    matches: bool


@dataclass(frozen=True, slots=True)
class HypothesisAnalysisDTO:
    diagnosis_name: str
    exact_match: bool
    matched_features: list[HypothesisFeatureCheckDTO]
    rejected_features: list[HypothesisFeatureCheckDTO]


@dataclass(frozen=True, slots=True)
class ExpertAnalysisDTO:
    diagnosis_name: str | None
    treatment_name: str | None
    treatment_description: str | None
    actions: list[str]
    explanation: str
    exact_match: bool
    hypotheses: list[HypothesisAnalysisDTO]
    status_message: str


@dataclass(frozen=True, slots=True)
class MlPredictionOptionDTO:
    diagnosis_name: str
    score: float | None


@dataclass(frozen=True, slots=True)
class MlAnalysisDTO:
    available: bool
    model_name: str | None
    predicted_diagnosis: str | None
    confidence: float | None
    options: list[MlPredictionOptionDTO]
    message: str


@dataclass(frozen=True, slots=True)
class DiagnosticAnalysisDTO:
    expert: ExpertAnalysisDTO
    ml: MlAnalysisDTO


@dataclass(frozen=True, slots=True)
class KnowledgeBaseSnapshotDTO:
    features: list[FeatureDTO]
    actions: list[str]
    treatments: list[TreatmentDTO]
    diagnoses: list[DiagnosisDTO]
    protocols: list[ProtocolDTO]
    statistics: dict[str, int]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_feature_dto(feature: Feature) -> FeatureDTO:
    return FeatureDTO(
        name=feature.name,
        allowed_values=str(feature.allowed_values),
        normal_values=str(feature.normal_values),
    )


def build_treatment_dto(treatment: Treatment) -> TreatmentDTO:
    return TreatmentDTO(
        name=treatment.name,
        description=treatment.description,
    )


def build_diagnosis_dto(diagnosis: Diagnosis) -> DiagnosisDTO:
    return DiagnosisDTO(
        name=diagnosis.name,
        feature_ranges={
            feature_name: str(value_range)
            for feature_name, value_range in diagnosis.feature_ranges.items()
        },
        treatment_name=diagnosis.treatment_name,
    )


def build_protocol_dto(protocol: Protocol) -> ProtocolDTO:
    return ProtocolDTO(
        treatment_name=protocol.treatment_name,
        actions=protocol.actions[:],
    )


def build_decision_result_dto(result: DecisionResult) -> DecisionResultDTO:
    return DecisionResultDTO(
        diagnosis_name=result.diagnosis_name,
        treatment_name=result.treatment_name,
        treatment_description=result.treatment_description,
        actions=result.actions[:],
        explanation=result.explanation,
    )


def build_hypothesis_analysis_dto(hypothesis: HypothesisAnalysis) -> HypothesisAnalysisDTO:
    return HypothesisAnalysisDTO(
        diagnosis_name=hypothesis.diagnosis_name,
        exact_match=hypothesis.exact_match,
        matched_features=[
            HypothesisFeatureCheckDTO(
                feature_name=check.feature_name,
                patient_value=check.patient_value,
                expected_range=check.expected_range,
                matches=check.matches,
            )
            for check in hypothesis.matched_features
        ],
        rejected_features=[
            HypothesisFeatureCheckDTO(
                feature_name=check.feature_name,
                patient_value=check.patient_value,
                expected_range=check.expected_range,
                matches=check.matches,
            )
            for check in hypothesis.rejected_features
        ],
    )


def build_expert_analysis_dto(analysis: DiagnosticAnalysis) -> ExpertAnalysisDTO:
    result = analysis.decision_result
    exact_match = result is not None
    return ExpertAnalysisDTO(
        diagnosis_name=result.diagnosis_name if result is not None else None,
        treatment_name=result.treatment_name if result is not None else None,
        treatment_description=result.treatment_description if result is not None else None,
        actions=result.actions[:] if result is not None else [],
        explanation=(
            result.explanation
            if result is not None
            else "Экспертная система не нашла точный диагноз. Смотрите результаты опровержения гипотез."
        ),
        exact_match=exact_match,
        hypotheses=[build_hypothesis_analysis_dto(item) for item in analysis.hypotheses],
        status_message=(
            "Точный диагноз найден."
            if exact_match
            else "Точный диагноз не найден, показаны ближайшие гипотезы."
        ),
    )


def build_ml_analysis_dto(result: MlPredictionResult) -> MlAnalysisDTO:
    return MlAnalysisDTO(
        available=result.available,
        model_name=result.model_name,
        predicted_diagnosis=result.predicted_diagnosis,
        confidence=result.confidence,
        options=[
            MlPredictionOptionDTO(
                diagnosis_name=item.diagnosis_name,
                score=item.score,
            )
            for item in result.options
        ],
        message=result.message,
    )


def build_diagnostic_analysis_dto(
    expert_analysis: DiagnosticAnalysis,
    ml_result: MlPredictionResult,
) -> DiagnosticAnalysisDTO:
    return DiagnosticAnalysisDTO(
        expert=build_expert_analysis_dto(expert_analysis),
        ml=build_ml_analysis_dto(ml_result),
    )
