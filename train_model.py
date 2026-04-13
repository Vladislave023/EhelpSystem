from __future__ import annotations

from ehelps_ml.training import train_and_export


def main() -> None:
    result = train_and_export()

    print("Обучение завершено.")
    print(f"Модель: {result.model_name}")
    print(f"Объектов в выборке: {result.dataset_summary.num_objects}")
    print(f"Признаков: {result.dataset_summary.num_features}")
    print(f"Классов: {result.dataset_summary.num_classes}")
    print(f"Train/Test: {result.train_size}/{result.test_size}")
    print(f"Accuracy: {result.accuracy:.4f}")
    print(f"Macro F1: {result.macro_f1:.4f}")
    print()
    print("Артефакты:")
    print(f"- Датасет: {result.artifacts.dataset_path}")
    print(f"- Модель: {result.artifacts.model_path}")
    print(f"- Метрики: {result.artifacts.metrics_path}")
    print(f"- Отчет: {result.artifacts.report_path}")
    print(f"- Confusion matrix: {result.artifacts.confusion_matrix_path}")
    print(f"- Важности признаков: {result.artifacts.feature_importances_path}")
    print()
    print(
        "Примечание: метрики считаются на синтетических данных и остаются оптимистичнее,"
        " чем на реальных клинических случаях."
    )


if __name__ == "__main__":
    main()
