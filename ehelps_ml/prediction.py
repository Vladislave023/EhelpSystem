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
            options = _build_probability_options(class_names, probabilities)
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


def _build_probability_options(
    class_names: list[str],
    probabilities: object,
) -> list[MlPredictionOption]:
    ranked = sorted(
        (
            (str(class_name), float(score))
            for class_name, score in zip(class_names, probabilities, strict=True)
        ),
        key=lambda item: item[1],
        reverse=True,
    )
    if not ranked:
        return []

    total = sum(score for _, score in ranked)
    if total <= 0:
        uniform_basis_points = 10000 // len(ranked)
        remainder = 10000 - uniform_basis_points * len(ranked)
        scaled = [uniform_basis_points for _ in ranked]
        for index in range(remainder):
            scaled[index] += 1
        return [
            MlPredictionOption(diagnosis_name=diagnosis_name, score=scaled_score / 10000)
            for (diagnosis_name, _), scaled_score in zip(ranked, scaled, strict=True)
        ]

    normalized = [(diagnosis_name, score / total) for diagnosis_name, score in ranked]
    scaled = [int(score * 10000) for _, score in normalized]
    remainder = 10000 - sum(scaled)

    fractions = sorted(
        (
            (score * 10000 - int(score * 10000), index)
            for index, (_, score) in enumerate(normalized)
        ),
        reverse=True,
    )
    for _, index in fractions[:remainder]:
        scaled[index] += 1

    return [
        MlPredictionOption(diagnosis_name=diagnosis_name, score=scaled_score / 10000)
        for (diagnosis_name, _), scaled_score in zip(normalized, scaled, strict=True)
    ]
