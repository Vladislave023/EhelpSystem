from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from ehelps_backend.application.facade import ExpertSystemFacade
from ehelps_backend.domain.exceptions import InvalidPatientStateError
from ehelps_backend.infrastructure.json_repository import JsonKnowledgeBaseRepository
from ehelps_ml.prediction import MlPredictionService


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

    def test_analyze_returns_refutation_for_non_exact_burn_case(self) -> None:
        analysis = self.facade.analyze_patient_state(
            {
                "Глубина повреждения": 0,
                "Площадь повреждения": 0,
                "Наличие кровотечения": 0,
                "Интенсивность боли": 6,
                "Жжение кожи": 1,
                "Линейная форма повреждения": 0,
                "Покраснение кожи": 1,
                "Наличие волдырей": 1,
                "Нарушение целостности кожи": 0,
                "Ограничение подвижности": 0,
                "Отёк": 0,
                "Наличие гематомы": 0,
                "Наличие инородного тела": 0,
                "Точечное повреждение": 0,
            }
        )

        self.assertFalse(analysis["expert"]["exact_match"])
        self.assertIsNone(analysis["expert"]["diagnosis_name"])
        self.assertGreater(len(analysis["expert"]["hypotheses"]), 0)

        top_hypothesis = analysis["expert"]["hypotheses"][0]
        self.assertIn(top_hypothesis["diagnosis_name"], {"ожог I степени", "ожог II степени"})
        self.assertGreater(len(top_hypothesis["matched_features"]), 0)
        self.assertGreater(len(top_hypothesis["rejected_features"]), 0)
        self.assertTrue(
            all("ожог" in item["diagnosis_name"] for item in analysis["expert"]["hypotheses"])
        )

    def test_exact_cut_analysis_only_keeps_cut_hypotheses(self) -> None:
        analysis = self.facade.analyze_patient_state(
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

        self.assertEqual(analysis["expert"]["diagnosis_name"], "глубокий порез")
        self.assertTrue(
            all("порез" in item["diagnosis_name"] for item in analysis["expert"]["hypotheses"])
        )

    def test_ml_prediction_returns_all_probabilities_with_total_one(self) -> None:
        prediction = MlPredictionService.default().predict(
            {
                "Глубина повреждения": 2.5,
                "Жжение кожи": 0,
                "Интенсивность боли": 7,
                "Линейная форма повреждения": 1,
                "Наличие волдырей": 0,
                "Наличие гематомы": 0,
                "Наличие инородного тела": 0,
                "Наличие кровотечения": 1,
                "Нарушение целостности кожи": 1,
                "Ограничение подвижности": 0,
                "Отёк": 0,
                "Площадь повреждения": 4.0,
                "Покраснение кожи": 0,
                "Точечное повреждение": 0,
            }
        )

        if not prediction.available:
            self.skipTest(prediction.message)

        self.assertEqual(len(prediction.options), 7)
        self.assertTrue(all(option.score is not None for option in prediction.options))
        self.assertAlmostEqual(
            sum(option.score for option in prediction.options if option.score is not None),
            1.0,
            places=4,
        )
