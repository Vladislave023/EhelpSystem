from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import joblib
from sklearn.base import clone
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

from ehelps_backend.infrastructure.json_repository import JsonKnowledgeBaseRepository
from ehelps_ml.dataset import DatasetSummary, generate_synthetic_dataset, save_dataset_csv


@dataclass(frozen=True, slots=True)
class TrainingArtifacts:
    dataset_path: Path
    model_path: Path
    metrics_path: Path
    report_path: Path
    confusion_matrix_path: Path
    feature_importances_path: Path


@dataclass(frozen=True, slots=True)
class TrainingResult:
    model_name: str
    train_size: int
    test_size: int
    accuracy: float
    macro_f1: float
    dataset_summary: DatasetSummary
    classes: list[str]
    model_params: dict[str, object]
    artifacts: TrainingArtifacts


def train_and_export(
    *,
    repository: JsonKnowledgeBaseRepository | None = None,
    output_dir: Path | None = None,
    samples_per_class: int = 250,
    test_size: float = 0.2,
    random_state: int = 42,
) -> TrainingResult:
    repository = repository or JsonKnowledgeBaseRepository.default()
    output_dir = output_dir or Path("artifacts") / "ml"
    output_dir.mkdir(parents=True, exist_ok=True)

    knowledge_base = repository.load()
    rows, labels, summary = generate_synthetic_dataset(
        knowledge_base,
        samples_per_class=samples_per_class,
        seed=random_state,
    )

    dataset_path = output_dir / "synthetic_dataset.csv"
    save_dataset_csv(dataset_path, rows, labels)

    feature_names = summary.feature_names
    x = [[row[feature_name] for feature_name in feature_names] for row in rows]
    y = labels

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )

    candidate_models = _build_candidate_models(random_state)
    model_comparison = _evaluate_candidate_models(candidate_models, x_train, y_train)
    best_entry = max(model_comparison, key=lambda item: (item["cv_accuracy"], item["cv_f1_macro"]))

    model = clone(candidate_models[best_entry["model_name"]])
    model.fit(x_train, y_train)

    predictions = model.predict(x_test)
    accuracy = accuracy_score(y_test, predictions)
    macro_f1 = f1_score(y_test, predictions, average="macro")
    classes = sorted(set(y))

    model_path = output_dir / "injury_classifier.joblib"
    metrics_path = output_dir / "metrics.json"
    report_path = output_dir / "classification_report.txt"
    confusion_matrix_path = output_dir / "confusion_matrix.csv"
    feature_importances_path = output_dir / "feature_importances.csv"

    joblib.dump(
        {
            "model": model,
            "feature_names": feature_names,
            "class_names": classes,
            "model_name": best_entry["model_name"],
        },
        model_path,
    )

    feature_importances = _extract_feature_importances(model, feature_names)

    metrics_payload = {
        "model_name": best_entry["model_name"],
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "train_size": len(x_train),
        "test_size": len(x_test),
        "dataset_summary": asdict(summary),
        "classes": classes,
        "model_params": model.get_params(),
        "model_comparison": model_comparison,
        "feature_importances": feature_importances,
        "evaluation_warning": (
            "Метрики рассчитаны на синтетическом датасете, сгенерированном из базы знаний, поэтому "
            "точность может быть завышена относительно реальных клинических случаев."
        ),
    }
    metrics_path.write_text(
        json.dumps(metrics_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    report_path.write_text(
        classification_report(y_test, predictions, digits=4),
        encoding="utf-8",
    )

    matrix = confusion_matrix(y_test, predictions, labels=classes)
    with confusion_matrix_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["actual/predicted", *classes])
        for class_name, row in zip(classes, matrix.tolist(), strict=True):
            writer.writerow([class_name, *row])

    with feature_importances_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["feature_name", "importance"])
        for item in feature_importances:
            writer.writerow([item["feature_name"], item["importance"]])

    return TrainingResult(
        model_name=best_entry["model_name"],
        train_size=len(x_train),
        test_size=len(x_test),
        accuracy=accuracy,
        macro_f1=macro_f1,
        dataset_summary=summary,
        classes=classes,
        model_params=model.get_params(),
        artifacts=TrainingArtifacts(
            dataset_path=dataset_path,
            model_path=model_path,
            metrics_path=metrics_path,
            report_path=report_path,
            confusion_matrix_path=confusion_matrix_path,
            feature_importances_path=feature_importances_path,
        ),
    )


def _build_candidate_models(random_state: int) -> dict[str, object]:
    return {
        "DecisionTreeClassifier": DecisionTreeClassifier(
            max_depth=8,
            min_samples_leaf=2,
            random_state=random_state,
        ),
        "RandomForestClassifier": RandomForestClassifier(
            n_estimators=250,
            max_depth=10,
            min_samples_split=4,
            min_samples_leaf=2,
            random_state=random_state,
        ),
        "GradientBoostingClassifier": GradientBoostingClassifier(
            n_estimators=150,
            learning_rate=0.08,
            max_depth=3,
            random_state=random_state,
        ),
        "KNeighborsClassifier": Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                ("classifier", KNeighborsClassifier(n_neighbors=7, weights="distance")),
            ]
        ),
    }


def _evaluate_candidate_models(
    candidate_models: dict[str, object],
    x_train: list[list[float]],
    y_train: list[str],
) -> list[dict[str, object]]:
    comparison: list[dict[str, object]] = []

    for model_name, model in candidate_models.items():
        accuracy_scores = cross_val_score(model, x_train, y_train, cv=5, scoring="accuracy")
        f1_scores = cross_val_score(model, x_train, y_train, cv=5, scoring="f1_macro")
        comparison.append(
            {
                "model_name": model_name,
                "cv_accuracy": round(float(accuracy_scores.mean()), 4),
                "cv_accuracy_std": round(float(accuracy_scores.std()), 4),
                "cv_f1_macro": round(float(f1_scores.mean()), 4),
                "cv_f1_macro_std": round(float(f1_scores.std()), 4),
            }
        )

    comparison.sort(key=lambda item: (item["cv_accuracy"], item["cv_f1_macro"]), reverse=True)
    return comparison


def _extract_feature_importances(model: object, feature_names: list[str]) -> list[dict[str, float]]:
    importances: list[float]

    if hasattr(model, "feature_importances_"):
        importances = list(model.feature_importances_)
    elif isinstance(model, Pipeline) and hasattr(model.named_steps.get("classifier"), "feature_importances_"):
        importances = list(model.named_steps["classifier"].feature_importances_)
    else:
        uniform_importance = round(1.0 / len(feature_names), 6) if feature_names else 0.0
        return [
            {
                "feature_name": feature_name,
                "importance": uniform_importance,
            }
            for feature_name in feature_names
        ]

    return [
        {
            "feature_name": feature_name,
            "importance": round(float(importance), 6),
        }
        for feature_name, importance in sorted(
            zip(feature_names, importances, strict=True),
            key=lambda item: item[1],
            reverse=True,
        )
    ]
