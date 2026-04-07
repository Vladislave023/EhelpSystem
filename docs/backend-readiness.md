# Готовность backend

## Что уже готово

- доменная модель предметной области;
- валидация базы знаний;
- решатель диагноза и протокола помощи;
- CRUD-логика редактора знаний;
- JSON-хранилище с атомарным сохранением;
- фасад `ExpertSystemFacade` для будущего UI;
- пример базы знаний;
- базовые `unittest`-сценарии.

## Что использовать как точку интеграции

Для интерфейса лучше работать не напрямую с доменными сущностями, а через:

- `ExpertSystemFacade`
- `KnowledgeBaseEditorService`

### Для чтения данных

- `ExpertSystemFacade.get_snapshot()`

Возвращает полный снимок базы знаний:

- признаки;
- действия;
- лечения;
- диагнозы;
- протоколы;
- статистику.

### Для диагностики пациента

- `ExpertSystemFacade.evaluate_patient_state(values)`

На вход получает словарь:

```python
{
    "Глубина повреждения": 2.5,
    "Площадь повреждения": 4.0,
    ...
}
```

На выход возвращает словарь с результатом:

- `diagnosis_name`
- `treatment_name`
- `treatment_description`
- `actions`
- `explanation`

### Для редактора знаний

`KnowledgeBaseEditorService` поддерживает:

- `add/update/delete_feature`
- `add/update/delete_action`
- `add/update/delete_treatment`
- `add/update/delete_diagnosis`
- `save_protocol`
- `delete_protocol`
- `list_*`
- `validate_integrity`

## Что осталось до UI

Backend уже достаточно собран для подключения оконного интерфейса. Следующий слой может быть одним из двух:

1. Прямое подключение `PySide6` к `ExpertSystemFacade` и `KnowledgeBaseEditorService`.
2. Промежуточный controller-слой между UI и application-сервисами.

Для курсовой достаточно первого варианта.

## Как проверить после установки Python

После установки Python 3.11+ в корне проекта можно будет использовать demo-сценарий backend:

```powershell
python demo_backend.py
```

или

```powershell
py -3 demo_backend.py
```

Для запуска тестов:

```powershell
python -m unittest discover -s tests -v
```

Для запуска desktop UI:

```powershell
python main.py
```
