from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from ehelps_backend.application.facade import ExpertSystemFacade
from ehelps_backend.domain.exceptions import InvalidPatientStateError
from ehelps_backend.infrastructure.json_repository import JsonKnowledgeBaseRepository


class DiagnosisServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        sample_path = Path(__file__).resolve().parents[1] / "data" / "sample_knowledge_base.json"
        self.repo_path = Path(self.temp_dir.name) / "knowledge_base.json"
        shutil.copyfile(sample_path, self.repo_path)
        self.facade = ExpertSystemFacade(JsonKnowledgeBaseRepository(self.repo_path))

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_returns_healthy_diagnosis_for_normal_values(self) -> None:
        result = self.facade.evaluate_patient_state(
            {
                "Глубина повреждения": 0,
                "Площадь повреждения": 0,
                "Наличие кровотечения": 0,
                "Интенсивность боли": 0,
                "Жжение кожи": 0,
                "Линейная форма повреждения": 0,
                "Покраснение кожи": 0,
                "Наличие волдырей": 0,
                "Нарушение целостности кожи": 0,
                "Ограничение подвижности": 0,
                "Отёк": 0,
                "Наличие гематомы": 0,
                "Наличие инородного тела": 0,
                "Точечное повреждение": 0,
            }
        )

        self.assertEqual(result["diagnosis_name"], "здоров")
        self.assertEqual(result["actions"], [])
        self.assertIsNone(result["treatment_name"])

    def test_returns_deep_cut_for_matching_values(self) -> None:
        result = self.facade.evaluate_patient_state(
            {
                "Глубина повреждения": 2.5,
                "Площадь повреждения": 4.0,
                "Наличие кровотечения": 1,
                "Интенсивность боли": 7,
                "Жжение кожи": 0,
                "Линейная форма повреждения": 1,
                "Покраснение кожи": 0,
                "Наличие волдырей": 0,
                "Нарушение целостности кожи": 1,
                "Ограничение подвижности": 0,
                "Отёк": 0,
                "Наличие гематомы": 0,
                "Наличие инородного тела": 0,
                "Точечное повреждение": 0,
            }
        )

        self.assertEqual(result["diagnosis_name"], "глубокий порез")
        self.assertEqual(result["treatment_name"], "остановка кровотечения")
        self.assertGreater(len(result["actions"]), 0)

    def test_raises_for_unknown_feature(self) -> None:
        with self.assertRaises(InvalidPatientStateError):
            self.facade.evaluate_patient_state(
                {
                    "Глубина повреждения": 0,
                    "Площадь повреждения": 0,
                    "Наличие кровотечения": 0,
                    "Интенсивность боли": 0,
                    "Жжение кожи": 0,
                    "Линейная форма повреждения": 0,
                    "Покраснение кожи": 0,
                    "Наличие волдырей": 0,
                    "Нарушение целостности кожи": 0,
                    "Ограничение подвижности": 0,
                    "Отёк": 0,
                    "Наличие гематомы": 0,
                    "Наличие инородного тела": 0,
                    "Точечное повреждение": 0,
                    "Лишний признак": 1,
                }
            )
