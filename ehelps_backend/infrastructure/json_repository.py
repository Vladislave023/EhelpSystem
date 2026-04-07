from __future__ import annotations

import json
from pathlib import Path

from ehelps_backend.domain.entities import Diagnosis, Feature, KnowledgeBase, Protocol, Treatment
from ehelps_backend.domain.value_objects import ValueRange


class JsonKnowledgeBaseRepository:
    def __init__(self, path: Path) -> None:
        self.path = path

    @classmethod
    def default(cls) -> "JsonKnowledgeBaseRepository":
        base_dir = Path(__file__).resolve().parents[2]
        return cls(base_dir / "data" / "sample_knowledge_base.json")

    def load(self) -> KnowledgeBase:
        payload = json.loads(self.path.read_text(encoding="utf-8"))

        features = {
            item["name"]: Feature(
                name=item["name"],
                allowed_values=ValueRange.from_expression(item["allowed_values"]),
                normal_values=ValueRange.from_expression(item["normal_values"]),
            )
            for item in payload["features"]
        }

        treatments = {
            item["name"]: Treatment(
                name=item["name"],
                description=item["description"],
            )
            for item in payload["treatments"]
        }

        diagnoses = [
            Diagnosis(
                name=item["name"],
                feature_ranges={
                    feature_name: ValueRange.from_expression(range_expression)
                    for feature_name, range_expression in item["feature_ranges"].items()
                },
                treatment_name=item.get("treatment_name"),
            )
            for item in payload["diagnoses"]
        ]

        protocols = {
            item["treatment_name"]: Protocol(
                treatment_name=item["treatment_name"],
                actions=item["actions"],
            )
            for item in payload["protocols"]
        }

        return KnowledgeBase(
            features=features,
            diagnoses=diagnoses,
            actions=set(payload["actions"]),
            treatments=treatments,
            protocols=protocols,
        )

    def save(self, knowledge_base: KnowledgeBase) -> None:
        payload = {
            "features": [
                {
                    "name": feature.name,
                    "allowed_values": str(feature.allowed_values),
                    "normal_values": str(feature.normal_values),
                }
                for feature in sorted(
                    knowledge_base.features.values(),
                    key=lambda feature: feature.name,
                )
            ],
            "actions": sorted(knowledge_base.actions),
            "treatments": [
                {
                    "name": treatment.name,
                    "description": treatment.description,
                }
                for treatment in sorted(
                    knowledge_base.treatments.values(),
                    key=lambda treatment: treatment.name,
                )
            ],
            "diagnoses": [
                {
                    "name": diagnosis.name,
                    "feature_ranges": {
                        feature_name: str(value_range)
                        for feature_name, value_range in diagnosis.feature_ranges.items()
                    },
                    "treatment_name": diagnosis.treatment_name,
                }
                for diagnosis in knowledge_base.diagnoses
            ],
            "protocols": [
                {
                    "treatment_name": protocol.treatment_name,
                    "actions": protocol.actions,
                }
                for protocol in sorted(
                    knowledge_base.protocols.values(),
                    key=lambda protocol: protocol.treatment_name,
                )
            ],
        }

        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        temp_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temp_path.replace(self.path)
