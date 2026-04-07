from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from ehelps_backend.application.editor import KnowledgeBaseEditorService
from ehelps_backend.domain.exceptions import EntityInUseError
from ehelps_backend.infrastructure.json_repository import JsonKnowledgeBaseRepository


class KnowledgeBaseEditorServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        sample_path = Path(__file__).resolve().parents[1] / "data" / "sample_knowledge_base.json"
        self.repo_path = Path(self.temp_dir.name) / "knowledge_base.json"
        shutil.copyfile(sample_path, self.repo_path)
        self.editor = KnowledgeBaseEditorService(JsonKnowledgeBaseRepository(self.repo_path))

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_can_add_feature_and_persist_it(self) -> None:
        self.editor.add_feature(
            name="Температура кожи",
            allowed_values="R[0;100]",
            normal_values="R[36;37]",
        )
        self.editor.reload()

        feature_names = [feature.name for feature in self.editor.list_features()]
        self.assertIn("Температура кожи", feature_names)

    def test_can_add_full_treatment_chain(self) -> None:
        self.editor.add_action("Дезинфицировать пинцет")
        self.editor.add_treatment("Подготовка инструмента", "Подготовить стерильный инструмент.")
        self.editor.save_protocol("Подготовка инструмента", ["Дезинфицировать пинцет"])
        self.editor.add_diagnosis(
            name="подготовка к удалению",
            feature_ranges={"Наличие инородного тела": "I[1;1]"},
            treatment_name="Подготовка инструмента",
        )
        self.editor.reload()

        diagnosis_names = [diagnosis.name for diagnosis in self.editor.list_diagnoses()]
        protocol_names = [protocol.treatment_name for protocol in self.editor.list_protocols()]

        self.assertIn("подготовка к удалению", diagnosis_names)
        self.assertIn("Подготовка инструмента", protocol_names)

    def test_cannot_delete_feature_used_in_diagnosis(self) -> None:
        with self.assertRaises(EntityInUseError):
            self.editor.delete_feature("Интенсивность боли")
