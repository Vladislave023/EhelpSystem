from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

from ehelps_backend.infrastructure.json_repository import JsonKnowledgeBaseRepository
from ehelps_ml.dataset import DatasetSummary, generate_synthetic_dataset, save_dataset_csv


@dataclass(frozen=True, slots=True)
class TrainingArtifacts:
    dataset_path: Path
    model_path: Path
    metrics_path: Path
    report_path: Path
    confusion_matrix_path: Path


@dataclass(frozen=True, slots=True)
class TrainingResult:
    model_name: str
    train_size: int
    test_size: int
    accuracy: float
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

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=8,
        min_samples_split=4,
        min_samples_leaf=2,
        random_state=random_state,
    )
    model.fit(x_train, y_train)

    predictions = model.predict(x_test)
    accuracy = accuracy_score(y_test, predictions)
    classes = sorted(set(y))

    model_path = output_dir / "injury_classifier.joblib"
    metrics_path = output_dir / "metrics.json"
    report_path = output_dir / "classification_report.txt"
    confusion_matrix_path = output_dir / "confusion_matrix.csv"

    joblib.dump(
        {
            "model": model,
            "feature_names": feature_names,
            "class_names": classes,
        },
        model_path,
    )

    metrics_payload = {
        "model_name": "RandomForestClassifier",
        "accuracy": accuracy,
        "train_size": len(x_train),
        "test_size": len(x_test),
        "dataset_summary": asdict(summary),
        "classes": classes,
        "model_params": model.get_params(),
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

    return TrainingResult(
        model_name="RandomForestClassifier",
        train_size=len(x_train),
        test_size=len(x_test),
        accuracy=accuracy,
        dataset_summary=summary,
        classes=classes,
        model_params=model.get_params(),
        artifacts=TrainingArtifacts(
            dataset_path=dataset_path,
            model_path=model_path,
            metrics_path=metrics_path,
            report_path=report_path,
            confusion_matrix_path=confusion_matrix_path,
        ),
    )
