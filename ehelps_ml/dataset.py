from __future__ import annotations

import csv
import random
from dataclasses import dataclass
from pathlib import Path

from ehelps_backend.domain.entities import Diagnosis, Feature, KnowledgeBase
from ehelps_backend.domain.value_objects import ValueRange


@dataclass(frozen=True, slots=True)
class DatasetSummary:
    num_objects: int
    num_features: int
    num_classes: int
    feature_names: list[str]
    class_names: list[str]


def generate_synthetic_dataset(
    knowledge_base: KnowledgeBase,
    *,
    samples_per_class: int = 250,
    seed: int = 42,
) -> tuple[list[dict[str, float]], list[str], DatasetSummary]:
    randomizer = random.Random(seed)
    feature_names = sorted(knowledge_base.features)
    class_names = [diagnosis.name for diagnosis in knowledge_base.diagnoses]

    rows: list[dict[str, float]] = []
    labels: list[str] = []

    for diagnosis in knowledge_base.diagnoses:
        for _ in range(samples_per_class):
            row = _generate_row_for_diagnosis(
                knowledge_base=knowledge_base,
                diagnosis=diagnosis,
                feature_names=feature_names,
                randomizer=randomizer,
            )
            rows.append(row)
            labels.append(diagnosis.name)

    summary = DatasetSummary(
        num_objects=len(rows),
        num_features=len(feature_names),
        num_classes=len(class_names),
        feature_names=feature_names,
        class_names=class_names,
    )
    return rows, labels, summary


def save_dataset_csv(
    path: Path,
    rows: list[dict[str, float]],
    labels: list[str],
    *,
    label_column: str = "diagnosis",
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) + [label_column] if rows else [label_column]

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row, label in zip(rows, labels, strict=True):
            writer.writerow({**row, label_column: label})


def _generate_row_for_diagnosis(
    *,
    knowledge_base: KnowledgeBase,
    diagnosis: Diagnosis,
    feature_names: list[str],
    randomizer: random.Random,
) -> dict[str, float]:
    row: dict[str, float] = {}

    for feature_name in feature_names:
        feature = knowledge_base.features[feature_name]
        value_range = _select_range_for_feature(
            knowledge_base=knowledge_base,
            diagnosis=diagnosis,
            feature=feature,
        )
        row[feature_name] = _sample_range_value(value_range, randomizer)

    return row


def _select_range_for_feature(
    *,
    knowledge_base: KnowledgeBase,
    diagnosis: Diagnosis,
    feature: Feature,
) -> ValueRange:
    if diagnosis.name == knowledge_base.healthy_diagnosis_name:
        return feature.normal_values

    if feature.name in diagnosis.feature_ranges:
        return diagnosis.feature_ranges[feature.name]

    return feature.normal_values


def _sample_range_value(value_range: ValueRange, randomizer: random.Random) -> float:
    if value_range.kind == "I":
        lower = int(round(value_range.lower))
        upper = int(round(value_range.upper))
        return int(randomizer.randint(lower, upper))

    if value_range.lower == value_range.upper:
        return round(value_range.lower, 3)

    return round(randomizer.uniform(value_range.lower, value_range.upper), 3)
