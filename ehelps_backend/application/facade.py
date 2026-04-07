from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass, field

from ehelps_backend.application.dto import (
    KnowledgeBaseSnapshotDTO,
    build_decision_result_dto,
    build_diagnosis_dto,
    build_feature_dto,
    build_protocol_dto,
    build_treatment_dto,
)
from ehelps_backend.application.editor import KnowledgeBaseEditorService
from ehelps_backend.application.services import DiagnosisService
from ehelps_backend.domain.entities import PatientState
from ehelps_backend.infrastructure.json_repository import JsonKnowledgeBaseRepository


@dataclass(slots=True)
class ExpertSystemFacade:
    repository: JsonKnowledgeBaseRepository
    editor: KnowledgeBaseEditorService = field(init=False)

    def __post_init__(self) -> None:
        self.editor = KnowledgeBaseEditorService(self.repository)

    @classmethod
    def default(cls) -> "ExpertSystemFacade":
        return cls(JsonKnowledgeBaseRepository.default())

    def reload(self) -> None:
        self.editor.reload()

    def get_snapshot(self) -> KnowledgeBaseSnapshotDTO:
        return KnowledgeBaseSnapshotDTO(
            features=[build_feature_dto(feature) for feature in self.editor.list_features()],
            actions=self.editor.list_actions(),
            treatments=[
                build_treatment_dto(treatment) for treatment in self.editor.list_treatments()
            ],
            diagnoses=[
                build_diagnosis_dto(diagnosis) for diagnosis in self.editor.list_diagnoses()
            ],
            protocols=[
                build_protocol_dto(protocol) for protocol in self.editor.list_protocols()
            ],
            statistics=self.editor.get_statistics(),
        )

    def evaluate_patient_state(self, values: dict[str, float]) -> dict[str, object]:
        self.editor.reload()
        diagnosis_service = DiagnosisService(self.editor.knowledge_base)
        result = diagnosis_service.evaluate(PatientState(values=values))
        return asdict(build_decision_result_dto(result))
