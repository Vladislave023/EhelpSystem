from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field, replace
from typing import Callable, Final

from ehelps_backend.domain.entities import Diagnosis, Feature, KnowledgeBase, Protocol, Treatment
from ehelps_backend.domain.exceptions import (
    EntityConflictError,
    EntityInUseError,
    EntityNotFoundError,
    InvalidEditorOperationError,
)
from ehelps_backend.domain.value_objects import ValueRange
from ehelps_backend.infrastructure.json_repository import JsonKnowledgeBaseRepository


UNSET: Final = object()


@dataclass(slots=True)
class KnowledgeBaseEditorService:
    repository: JsonKnowledgeBaseRepository
    knowledge_base: KnowledgeBase = field(init=False)

    def __post_init__(self) -> None:
        self.reload()

    def reload(self) -> None:
        self.knowledge_base = self.repository.load()

    def list_features(self) -> list[Feature]:
        return sorted(self.knowledge_base.features.values(), key=lambda feature: feature.name)

    def list_actions(self) -> list[str]:
        return sorted(self.knowledge_base.actions)

    def list_treatments(self) -> list[Treatment]:
        return sorted(self.knowledge_base.treatments.values(), key=lambda treatment: treatment.name)

    def list_diagnoses(self) -> list[Diagnosis]:
        return [
            replace(diagnosis, feature_ranges=diagnosis.feature_ranges.copy())
            for diagnosis in self.knowledge_base.diagnoses
        ]

    def list_protocols(self) -> list[Protocol]:
        return [
            replace(protocol, actions=protocol.actions[:])
            for protocol in sorted(
                self.knowledge_base.protocols.values(),
                key=lambda protocol: protocol.treatment_name,
            )
        ]

    def validate_integrity(self) -> None:
        self.knowledge_base.validate()

    def get_statistics(self) -> dict[str, int]:
        return {
            "features": len(self.knowledge_base.features),
            "diagnoses": len(self.knowledge_base.diagnoses),
            "actions": len(self.knowledge_base.actions),
            "treatments": len(self.knowledge_base.treatments),
            "protocols": len(self.knowledge_base.protocols),
        }

    def add_feature(self, name: str, allowed_values: str, normal_values: str) -> None:
        self._assert_name_is_free(self.knowledge_base.features, name, "Признак")

        def mutator() -> None:
            self.knowledge_base.features[name] = Feature(
                name=name,
                allowed_values=self._parse_range(allowed_values),
                normal_values=self._parse_range(normal_values),
            )

        self._mutate_and_persist(mutator)

    def update_feature(
        self,
        current_name: str,
        *,
        new_name: str | None = None,
        allowed_values: str | None = None,
        normal_values: str | None = None,
    ) -> None:
        feature = self._get_feature(current_name)
        target_name = new_name or current_name

        if target_name != current_name and target_name in self.knowledge_base.features:
            raise EntityConflictError(f"Признак '{target_name}' уже существует.")

        def mutator() -> None:
            updated_feature = Feature(
                name=target_name,
                allowed_values=self._parse_range(allowed_values)
                if allowed_values is not None
                else feature.allowed_values,
                normal_values=self._parse_range(normal_values)
                if normal_values is not None
                else feature.normal_values,
            )

            del self.knowledge_base.features[current_name]
            self.knowledge_base.features[target_name] = updated_feature

            if target_name != current_name:
                self._rename_feature_in_diagnoses(current_name, target_name)

        self._mutate_and_persist(mutator)

    def delete_feature(self, name: str) -> None:
        self._get_feature(name)
        usages = [
            diagnosis.name
            for diagnosis in self.knowledge_base.diagnoses
            if name in diagnosis.feature_ranges
        ]
        if usages:
            raise EntityInUseError(
                f"Признак '{name}' используется в диагнозах: {', '.join(usages)}."
            )

        def mutator() -> None:
            del self.knowledge_base.features[name]

        self._mutate_and_persist(mutator)

    def add_action(self, name: str) -> None:
        if name in self.knowledge_base.actions:
            raise EntityConflictError(f"Действие '{name}' уже существует.")

        def mutator() -> None:
            self.knowledge_base.actions.add(name)

        self._mutate_and_persist(mutator)

    def update_action(self, current_name: str, *, new_name: str) -> None:
        self._get_action(current_name)
        if new_name != current_name and new_name in self.knowledge_base.actions:
            raise EntityConflictError(f"Действие '{new_name}' уже существует.")

        def mutator() -> None:
            self.knowledge_base.actions.remove(current_name)
            self.knowledge_base.actions.add(new_name)

            for treatment_name, protocol in list(self.knowledge_base.protocols.items()):
                updated_actions = [
                    new_name if action == current_name else action for action in protocol.actions
                ]
                self.knowledge_base.protocols[treatment_name] = replace(
                    protocol,
                    actions=updated_actions,
                )

        self._mutate_and_persist(mutator)

    def delete_action(self, name: str) -> None:
        self._get_action(name)
        usages = [
            protocol.treatment_name
            for protocol in self.knowledge_base.protocols.values()
            if name in protocol.actions
        ]
        if usages:
            raise EntityInUseError(
                f"Действие '{name}' используется в протоколах: {', '.join(sorted(usages))}."
            )

        def mutator() -> None:
            self.knowledge_base.actions.remove(name)

        self._mutate_and_persist(mutator)

    def add_treatment(self, name: str, description: str) -> None:
        self._assert_name_is_free(self.knowledge_base.treatments, name, "Лечение")

        def mutator() -> None:
            self.knowledge_base.treatments[name] = Treatment(name=name, description=description)

        self._mutate_and_persist(mutator)

    def update_treatment(
        self,
        current_name: str,
        *,
        new_name: str | None = None,
        description: str | None = None,
    ) -> None:
        treatment = self._get_treatment(current_name)
        target_name = new_name or current_name

        if target_name != current_name and target_name in self.knowledge_base.treatments:
            raise EntityConflictError(f"Лечение '{target_name}' уже существует.")

        def mutator() -> None:
            updated_treatment = Treatment(
                name=target_name,
                description=description if description is not None else treatment.description,
            )

            del self.knowledge_base.treatments[current_name]
            self.knowledge_base.treatments[target_name] = updated_treatment

            for index, diagnosis in enumerate(self.knowledge_base.diagnoses):
                if diagnosis.treatment_name == current_name:
                    self.knowledge_base.diagnoses[index] = replace(
                        diagnosis,
                        treatment_name=target_name,
                    )

            if current_name in self.knowledge_base.protocols:
                protocol = self.knowledge_base.protocols.pop(current_name)
                self.knowledge_base.protocols[target_name] = replace(
                    protocol,
                    treatment_name=target_name,
                )

        self._mutate_and_persist(mutator)

    def delete_treatment(self, name: str) -> None:
        self._get_treatment(name)
        diagnoses = [
            diagnosis.name
            for diagnosis in self.knowledge_base.diagnoses
            if diagnosis.treatment_name == name
        ]
        if diagnoses:
            raise EntityInUseError(
                f"Лечение '{name}' назначено диагнозам: {', '.join(diagnoses)}."
            )

        if name in self.knowledge_base.protocols:
            raise EntityInUseError(
                f"Лечение '{name}' используется в протоколе помощи и не может быть удалено."
            )

        def mutator() -> None:
            del self.knowledge_base.treatments[name]

        self._mutate_and_persist(mutator)

    def add_diagnosis(
        self,
        name: str,
        *,
        feature_ranges: dict[str, str],
        treatment_name: str | None = None,
    ) -> None:
        if any(diagnosis.name == name for diagnosis in self.knowledge_base.diagnoses):
            raise EntityConflictError(f"Диагноз '{name}' уже существует.")

        if treatment_name is not None:
            self._get_treatment(treatment_name)

        def mutator() -> None:
            diagnosis = Diagnosis(
                name=name,
                feature_ranges=self._parse_feature_ranges(feature_ranges),
                treatment_name=treatment_name,
            )
            self.knowledge_base.diagnoses.append(diagnosis)

        self._mutate_and_persist(mutator)

    def update_diagnosis(
        self,
        current_name: str,
        *,
        new_name: str | None = None,
        feature_ranges: dict[str, str] | None = None,
        treatment_name: str | None | object = UNSET,
    ) -> None:
        diagnosis, diagnosis_index = self._get_diagnosis(current_name)
        target_name = new_name or current_name

        if (
            target_name != current_name
            and any(item.name == target_name for item in self.knowledge_base.diagnoses)
        ):
            raise EntityConflictError(f"Диагноз '{target_name}' уже существует.")

        if diagnosis.name == self.knowledge_base.healthy_diagnosis_name:
            if target_name != current_name:
                raise InvalidEditorOperationError("Диагноз 'здоров' нельзя переименовать.")
            if treatment_name is not UNSET and treatment_name is not None:
                raise InvalidEditorOperationError("Диагнозу 'здоров' нельзя назначить лечение.")

        if isinstance(treatment_name, str):
            self._get_treatment(treatment_name)

        def mutator() -> None:
            updated_diagnosis = replace(
                diagnosis,
                name=target_name,
                feature_ranges=self._parse_feature_ranges(feature_ranges)
                if feature_ranges is not None
                else diagnosis.feature_ranges.copy(),
                treatment_name=diagnosis.treatment_name
                if treatment_name is UNSET
                else treatment_name,
            )
            self.knowledge_base.diagnoses[diagnosis_index] = updated_diagnosis

        self._mutate_and_persist(mutator)

    def delete_diagnosis(self, name: str) -> None:
        diagnosis, diagnosis_index = self._get_diagnosis(name)

        if diagnosis.name == self.knowledge_base.healthy_diagnosis_name:
            raise InvalidEditorOperationError("Диагноз 'здоров' нельзя удалить.")

        def mutator() -> None:
            del self.knowledge_base.diagnoses[diagnosis_index]

        self._mutate_and_persist(mutator)

    def save_protocol(self, treatment_name: str, actions: list[str]) -> None:
        self._get_treatment(treatment_name)

        if len(set(actions)) != len(actions):
            raise InvalidEditorOperationError(
                f"Протокол лечения '{treatment_name}' содержит повторяющиеся действия."
            )

        for action_name in actions:
            self._get_action(action_name)

        def mutator() -> None:
            self.knowledge_base.protocols[treatment_name] = Protocol(
                treatment_name=treatment_name,
                actions=actions[:],
            )

        self._mutate_and_persist(mutator)

    def delete_protocol(self, treatment_name: str) -> None:
        if treatment_name not in self.knowledge_base.protocols:
            raise EntityNotFoundError(
                f"Протокол для лечения '{treatment_name}' не найден."
            )

        diagnoses = [
            diagnosis.name
            for diagnosis in self.knowledge_base.diagnoses
            if diagnosis.treatment_name == treatment_name
        ]
        if diagnoses:
            raise EntityInUseError(
                f"Протокол лечения '{treatment_name}' используется диагнозами: "
                f"{', '.join(diagnoses)}."
            )

        def mutator() -> None:
            del self.knowledge_base.protocols[treatment_name]

        self._mutate_and_persist(mutator)

    def _mutate_and_persist(self, mutator: Callable[[], None]) -> None:
        snapshot = deepcopy(self.knowledge_base)
        try:
            mutator()
            self.knowledge_base.validate()
            self.repository.save(self.knowledge_base)
        except Exception:
            self.knowledge_base = snapshot
            raise

    def _rename_feature_in_diagnoses(self, current_name: str, target_name: str) -> None:
        for index, diagnosis in enumerate(self.knowledge_base.diagnoses):
            if current_name not in diagnosis.feature_ranges:
                continue

            updated_ranges: dict[str, ValueRange] = {}
            for feature_name, value_range in diagnosis.feature_ranges.items():
                updated_ranges[target_name if feature_name == current_name else feature_name] = (
                    value_range
                )

            self.knowledge_base.diagnoses[index] = replace(
                diagnosis,
                feature_ranges=updated_ranges,
            )

    def _parse_feature_ranges(self, feature_ranges: dict[str, str]) -> dict[str, ValueRange]:
        parsed_ranges: dict[str, ValueRange] = {}

        for feature_name, expression in feature_ranges.items():
            self._get_feature(feature_name)
            parsed_ranges[feature_name] = self._parse_range(expression)

        return parsed_ranges

    @staticmethod
    def _parse_range(expression: str) -> ValueRange:
        return ValueRange.from_expression(expression)

    @staticmethod
    def _assert_name_is_free(items: dict[object, object], name: str, label: str) -> None:
        if name in items:
            raise EntityConflictError(f"{label} '{name}' уже существует.")

    def _get_feature(self, name: str) -> Feature:
        try:
            return self.knowledge_base.features[name]
        except KeyError as error:
            raise EntityNotFoundError(f"Признак '{name}' не найден.") from error

    def _get_action(self, name: str) -> str:
        if name not in self.knowledge_base.actions:
            raise EntityNotFoundError(f"Действие '{name}' не найдено.")
        return name

    def _get_treatment(self, name: str) -> Treatment:
        try:
            return self.knowledge_base.treatments[name]
        except KeyError as error:
            raise EntityNotFoundError(f"Лечение '{name}' не найдено.") from error

    def _get_diagnosis(self, name: str) -> tuple[Diagnosis, int]:
        for index, diagnosis in enumerate(self.knowledge_base.diagnoses):
            if diagnosis.name == name:
                return diagnosis, index
        raise EntityNotFoundError(f"Диагноз '{name}' не найден.")
