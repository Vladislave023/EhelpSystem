from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib


@dataclass(frozen=True, slots=True)
class MlPredictionOption:
    diagnosis_name: str
    score: float | None


@dataclass(frozen=True, slots=True)
class MlPredictionResult:
    available: bool
    model_name: str | None
    predicted_diagnosis: str | None
    confidence: float | None
    options: list[MlPredictionOption]
    message: str


@dataclass(slots=True)
class MlPredictionService:
    model_path: Path

    @classmethod
    def default(cls) -> "MlPredictionService":
        base_dir = Path(__file__).resolve().parents[1]
        return cls(base_dir / "artifacts" / "ml" / "injury_classifier.joblib")

    def predict(self, values: dict[str, float]) -> MlPredictionResult:
        if not self.model_path.exists():
            return MlPredictionResult(
                available=False,
                model_name=None,
                predicted_diagnosis=None,
                confidence=None,
                options=[],
                message=(
                    "ML-модель пока недоступна. Сначала обучите ее через "
                    "скрипт train_model.py."
                ),
            )

        try:
            artifact = joblib.load(self.model_path)
        except Exception as error:
            return MlPredictionResult(
                available=False,
                model_name=None,
                predicted_diagnosis=None,
                confidence=None,
                options=[],
                message=f"Не удалось загрузить ML-модель: {error}",
            )

        model = artifact["model"]
        feature_names = artifact["feature_names"]
        model_name = artifact.get("model_name") or type(model).__name__
        row = [[float(values.get(feature_name, 0.0)) for feature_name in feature_names]]

        predicted_diagnosis = str(model.predict(row)[0])
        options: list[MlPredictionOption] = []
        confidence: float | None = None

        if hasattr(model, "predict_proba"):
            probabilities = model.predict_proba(row)[0]
            class_names = list(getattr(model, "classes_", artifact.get("class_names", [])))
            ranked = sorted(
                zip(class_names, probabilities, strict=True),
                key=lambda item: item[1],
                reverse=True,
            )
            options = [
                MlPredictionOption(
                    diagnosis_name=str(class_name),
                    score=round(float(score), 4),
                )
                for class_name, score in ranked[:3]
            ]
            if options:
                confidence = options[0].score
        else:
            options = [MlPredictionOption(diagnosis_name=predicted_diagnosis, score=None)]

        return MlPredictionResult(
            available=True,
            model_name=model_name,
            predicted_diagnosis=predicted_diagnosis,
            confidence=confidence,
            options=options,
            message="ML-прогноз рассчитан на основе обученной модели.",
        )
