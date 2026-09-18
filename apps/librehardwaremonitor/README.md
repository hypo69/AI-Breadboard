# LibreHardwareMonitor App

Приложение для диагностики и мониторинга аппаратного обеспечения через LibreHardwareMonitor (LHM) в составе экосистемы **AI Breadboard**.

## Возможности
- Опрос встроенного Web REST JSON API LibreHardwareMonitor (`http://localhost:8085/data.json`).
- Нормализация и преобразование сырого дерева сенсоров в плоский структурированный список.
- Рекурсивный поиск датчиков по именам компонентов и типам оборудования.
- Формирование системной сводки (температуры и загрузка CPU, GPU, оперативной памяти).
- Управление процессом `LibreHardwareMonitor.exe` (фоновый запуск, проверка наличия бинарника через `UtilityDiscovery`).
- Автономный запуск в режиме REST API сервера FastAPI или CLI-утилиты.

## Быстрый запуск

### Запуск через CLI
```powershell
# Проверка статуса сервиса и бинарника
py -m apps.librehardwaremonitor

# Получение краткой системной сводки
py -m apps.librehardwaremonitor --summary

# Поиск конкретного сенсора
py -m apps.librehardwaremonitor --find CPU "CPU Package"

# Получение плоского списка всех сенсоров
py -m apps.librehardwaremonitor --metrics

# Фоновый запуск LibreHardwareMonitor.exe
py -m apps.librehardwaremonitor --launch

# Запуск выделенного HTTP сервера приложения
py -m apps.librehardwaremonitor --server --port 8126
```

### REST API Эндпоинты
| Метод | Эндпоинт | Описание |
| :--- | :--- | :--- |
| `GET` | `/api/v1/lhm/status` | Статус Web API LHM, путь к бинарнику и руководство по установке |
| `GET` | `/api/v1/lhm/summary` | Сводка ключевых показателей системы (CPU/GPU/RAM) |
| `GET` | `/api/v1/lhm/metrics` | Плоский список сенсоров с нормализованными числовыми значениями |
| `GET` | `/api/v1/lhm/sensors` | Полное сырое дерево датчиков от LHM |
| `POST`| `/api/v1/lhm/launch` | Фоновый запуск процесса `LibreHardwareMonitor.exe` |
