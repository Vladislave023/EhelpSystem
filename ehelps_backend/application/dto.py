from __future__ import annotations

from dataclasses import asdict, dataclass

from ehelps_backend.domain.entities import DecisionResult, Diagnosis, Feature, Protocol, Treatment


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
