# LibreHardwareMonitor Core

Модуль ядра приложения `apps.librehardwaremonitor.core`.

## Содержимое
- `lhm_service.py`: класс `LhmService` и функция `parse_sensor_value`.
  - Взаимодействие с REST API LHM (`:8085/data.json`).
  - Парсинг и извлечение чисел/единиц измерения из строк сенсоров.
  - Поиск датчиков по паттернам компонентов и категорий.
  - Плоский обход дерева оборудования.
  - Фоновый запуск процесса с флагом `DETACHED_PROCESS` на Windows.
