from ehelps_backend.application.facade import ExpertSystemFacade


def main() -> None:
    facade = ExpertSystemFacade.default()
    snapshot = facade.get_snapshot()

    print("Статистика базы знаний:")
    for label, value in snapshot.statistics.items():
        print(f"- {label}: {value}")
    print()

    result = facade.evaluate_patient_state(
        {
            "Глубина повреждения": 2.5,
            "Площадь повреждения": 4.0,
            "Наличие кровотечения": 1,
            "Интенсивность боли": 7,
            "Покраснение кожи": 0,
            "Наличие волдырей": 0,
            "Отёк": 0,
            "Наличие гематомы": 0,
            "Наличие инородного тела": 0,
        }
    )

    print("Диагноз:", result["diagnosis_name"])
    print("Лечение:", result["treatment_name"] or "не требуется")
    print("Действия:")
    for action in result["actions"]:
        print(f"- {action}")
    print()
    print(result["explanation"])


if __name__ == "__main__":
    main()
