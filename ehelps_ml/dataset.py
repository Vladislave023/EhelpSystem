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
    profile = _select_generation_profile(
        diagnosis=diagnosis,
        knowledge_base=knowledge_base,
        randomizer=randomizer,
    )
    row: dict[str, float] = {}

    for feature_name in feature_names:
        feature = knowledge_base.features[feature_name]
        target_range = _select_range_for_feature(
            knowledge_base=knowledge_base,
            diagnosis=diagnosis,
            feature=feature,
        )
        sampled_value = _sample_feature_value(
            knowledge_base=knowledge_base,
            diagnosis=diagnosis,
            feature=feature,
            target_range=target_range,
            profile=profile,
            randomizer=randomizer,
        )
        row[feature_name] = sampled_value

    return row


def _select_generation_profile(
    *,
    diagnosis: Diagnosis,
    knowledge_base: KnowledgeBase,
    randomizer: random.Random,
) -> str:
    roll = randomizer.random()

    if diagnosis.name == knowledge_base.healthy_diagnosis_name:
        if roll < 0.75:
            return "healthy_core"
        if roll < 0.95:
            return "healthy_boundary"
        return "healthy_noisy"

    if roll < 0.55:
        return "core"
    if roll < 0.8:
        return "boundary"
    return "noisy"


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


def _sample_feature_value(
    *,
    knowledge_base: KnowledgeBase,
    diagnosis: Diagnosis,
    feature: Feature,
    target_range: ValueRange,
    profile: str,
    randomizer: random.Random,
) -> float:
    is_healthy = diagnosis.name == knowledge_base.healthy_diagnosis_name
    is_diagnostic_feature = feature.name in diagnosis.feature_ranges

    if profile in {"healthy_core", "core"}:
        if is_diagnostic_feature:
            return _sample_range_center(target_range, randomizer)
        return _sample_range_center(feature.normal_values, randomizer)

    if profile in {"healthy_boundary", "boundary"}:
        if is_diagnostic_feature:
            return _sample_range_edge(target_range, randomizer)
        return _sample_range_edge(feature.normal_values, randomizer)

    if is_healthy:
        if randomizer.random() < 0.15:
            return _sample_allowed_outside_normal(feature, randomizer)
        return _sample_range_value(feature.normal_values, randomizer)

    if is_diagnostic_feature:
        if randomizer.random() < 0.6:
            return _sample_range_edge(target_range, randomizer)
        return _sample_range_value(target_range, randomizer)

    if randomizer.random() < 0.25:
        return _sample_allowed_outside_normal(feature, randomizer)

    return _sample_range_value(feature.normal_values, randomizer)


def _sample_range_value(value_range: ValueRange, randomizer: random.Random) -> float:
    if value_range.kind == "I":
        lower = int(round(value_range.lower))
        upper = int(round(value_range.upper))
        return int(randomizer.randint(lower, upper))

    if value_range.lower == value_range.upper:
        return round(value_range.lower, 3)

    return round(randomizer.uniform(value_range.lower, value_range.upper), 3)


def _sample_range_center(value_range: ValueRange, randomizer: random.Random) -> float:
    if value_range.lower == value_range.upper:
        return _sample_range_value(value_range, randomizer)

    span = value_range.upper - value_range.lower
    margin = span * 0.2
    centered_range = ValueRange(
        kind=value_range.kind,
        lower=value_range.lower + margin,
        upper=value_range.upper - margin,
    )
    return _sample_range_value(centered_range, randomizer)


def _sample_range_edge(value_range: ValueRange, randomizer: random.Random) -> float:
    if value_range.lower == value_range.upper:
        return _sample_range_value(value_range, randomizer)

    span = value_range.upper - value_range.lower
    edge_span = max(span * 0.15, 0.001)

    if randomizer.random() < 0.5:
        edge_range = ValueRange(
            kind=value_range.kind,
            lower=value_range.lower,
            upper=min(value_range.lower + edge_span, value_range.upper),
        )
    else:
        edge_range = ValueRange(
            kind=value_range.kind,
            lower=max(value_range.upper - edge_span, value_range.lower),
            upper=value_range.upper,
        )

    return _sample_range_value(edge_range, randomizer)


def _sample_allowed_outside_normal(feature: Feature, randomizer: random.Random) -> float:
    allowed_range = feature.allowed_values
    normal_range = feature.normal_values

    candidate_ranges: list[ValueRange] = []
    if allowed_range.lower < normal_range.lower:
        candidate_ranges.append(
            ValueRange(
                kind=allowed_range.kind,
                lower=allowed_range.lower,
                upper=normal_range.lower,
            )
        )
    if normal_range.upper < allowed_range.upper:
        candidate_ranges.append(
            ValueRange(
                kind=allowed_range.kind,
                lower=normal_range.upper,
                upper=allowed_range.upper,
            )
        )

    valid_ranges = [
        value_range
        for value_range in candidate_ranges
        if value_range.lower < value_range.upper
        or value_range.kind == "I" and int(round(value_range.lower)) <= int(round(value_range.upper))
    ]
    if not valid_ranges:
        return _sample_range_value(normal_range, randomizer)

    return _sample_range_edge(randomizer.choice(valid_ranges), randomizer)
