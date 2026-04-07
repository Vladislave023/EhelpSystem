from __future__ import annotations

from dataclasses import dataclass, field

from ehelps_backend.domain.exceptions import InvalidKnowledgeBaseError
from ehelps_backend.domain.value_objects import ValueRange


@dataclass(frozen=True, slots=True)
class Feature:
    name: str
    allowed_values: ValueRange
    normal_values: ValueRange


@dataclass(frozen=True, slots=True)
class Diagnosis:
    name: str
    feature_ranges: dict[str, ValueRange]
    treatment_name: str | None = None


@dataclass(frozen=True, slots=True)
class Treatment:
    name: str
    description: str


@dataclass(frozen=True, slots=True)
class Protocol:
    treatment_name: str
    actions: list[str]


@dataclass(frozen=True, slots=True)
class PatientState:
    values: dict[str, float]


@dataclass(frozen=True, slots=True)
class DecisionResult:
    diagnosis_name: str
    treatment_name: str | None
    treatment_description: str | None
    actions: list[str]
    explanation: str


@dataclass(slots=True)
class KnowledgeBase:
    features: dict[str, Feature]
    diagnoses: list[Diagnosis]
    actions: set[str]
    treatments: dict[str, Treatment]
    protocols: dict[str, Protocol]
    healthy_diagnosis_name: str = "здоров"
    _diagnosis_index: dict[str, Diagnosis] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        self._diagnosis_index = {diagnosis.name: diagnosis for diagnosis in self.diagnoses}

        if self.healthy_diagnosis_name not in self._diagnosis_index:
            raise InvalidKnowledgeBaseError(
                f"В базе знаний отсутствует обязательный диагноз '{self.healthy_diagnosis_name}'."
            )

        if len(self._diagnosis_index) != len(self.diagnoses):
            raise InvalidKnowledgeBaseError("Названия диагнозов должны быть уникальными.")

        for feature in self.features.values():
            if not feature.allowed_values.contains_range(feature.normal_values):
                raise InvalidKnowledgeBaseError(
                    f"Нормальные значения признака '{feature.name}' должны быть "
                    f"подмножеством допустимых значений {feature.allowed_values}."
                )

        for diagnosis in self.diagnoses:
            for feature_name, value_range in diagnosis.feature_ranges.items():
                if feature_name not in self.features:
                    raise InvalidKnowledgeBaseError(
                        f"Диагноз '{diagnosis.name}' ссылается на неизвестный признак '{feature_name}'."
                    )

                feature = self.features[feature_name]
                if not feature.allowed_values.contains_range(value_range):
                    raise InvalidKnowledgeBaseError(
                        f"Диапазон {value_range} для признака '{feature_name}' "
                        f"в диагнозе '{diagnosis.name}' выходит за допустимые значения "
                        f"{feature.allowed_values}."
                    )

            if diagnosis.name == self.healthy_diagnosis_name:
                if diagnosis.feature_ranges:
                    raise InvalidKnowledgeBaseError(
                        f"Диагноз '{self.healthy_diagnosis_name}' не должен содержать правил признаков."
                    )
                if diagnosis.treatment_name is not None:
                    raise InvalidKnowledgeBaseError(
                        f"Диагноз '{self.healthy_diagnosis_name}' не должен иметь назначенного лечения."
                    )
                continue

            if not diagnosis.feature_ranges:
                raise InvalidKnowledgeBaseError(
                    f"Диагноз '{diagnosis.name}' должен содержать хотя бы один признак."
                )

            if diagnosis.treatment_name is None:
                raise InvalidKnowledgeBaseError(
                    f"Для диагноза '{diagnosis.name}' должно быть задано лечение."
                )

            if diagnosis.treatment_name not in self.treatments:
                raise InvalidKnowledgeBaseError(
                    f"Для диагноза '{diagnosis.name}' указано неизвестное лечение "
                    f"'{diagnosis.treatment_name}'."
                )

            if diagnosis.treatment_name not in self.protocols:
                raise InvalidKnowledgeBaseError(
                    f"Для лечения '{diagnosis.treatment_name}', назначенного диагнозу "
                    f"'{diagnosis.name}', отсутствует протокол помощи."
                )

        for treatment_name, protocol in self.protocols.items():
            if treatment_name not in self.treatments:
                raise InvalidKnowledgeBaseError(
                    f"Протокол ссылается на неизвестное лечение '{treatment_name}'."
                )

            if len(set(protocol.actions)) != len(protocol.actions):
                raise InvalidKnowledgeBaseError(
                    f"Протокол лечения '{treatment_name}' содержит повторяющиеся действия."
                )

            unknown_actions = [action for action in protocol.actions if action not in self.actions]
            if unknown_actions:
                raise InvalidKnowledgeBaseError(
                    f"Протокол лечения '{treatment_name}' содержит неизвестные действия: "
                    + ", ".join(sorted(set(unknown_actions)))
                )

            used_by_diagnoses = [
                diagnosis.name
                for diagnosis in self.diagnoses
                if diagnosis.treatment_name == treatment_name
            ]
            if used_by_diagnoses and not protocol.actions:
                raise InvalidKnowledgeBaseError(
                    f"Протокол лечения '{treatment_name}' не должен быть пустым, "
                    f"потому что он используется диагнозами: {', '.join(used_by_diagnoses)}."
                )

    def iter_non_healthy_diagnoses(self) -> list[Diagnosis]:
        return [
            diagnosis
            for diagnosis in self.diagnoses
            if diagnosis.name != self.healthy_diagnosis_name
        ]
