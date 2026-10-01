# Конфигурация подсистемы телеметрии Windows (`config.json`)

Файл [`config.json`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/apps/windows/telemetry/config.json) является центральным конфигурационным файлом для системы сбора, буферизации, аудита и мониторинга телеметрии Windows в проекте AI-Breadboard.

Управление загрузкой, валидацией и модификацией параметров осуществляется модулем [`telemetry_config.py`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/apps/windows/telemetry/telemetry_config.py) (класс `TelemetryConfigManager`).

---

## 📑 Содержание

1. [Основные параметры и буферизация](#1-основные-параметры-и-буферизация)
2. [Режимы сбора и интервалы](#2-режимы-сбора-и-интервалы)
3. [Управление процессами](#3-управление-процессами)
4. [Тяжелые коллекторы и автопереключение](#4-тяжелые-коллекторы-и-автопереключение)
5. [Логгеры приложений (`loggers`)](#5-логгеры-приложений-loggers)
6. [Конфигурация сенсоров (`sensors`)](#6-конфигурация-сенсоров-sensors)
7. [Опции телеметрии (`telemetry_options`)](#7-опции-телеметрии-telemetry_options)
8. [Низкоуровневый сборщик Windows (`w64_collector`)](#8-низкоуровневый-сборщик-windows-w64_collector)

---

## 1. Основные параметры и буферизация

Параметры буферизации предотвращают избыточную нагрузку на SQLite базу данных путем пакетного сброса данных, а также обеспечивают сохранность телеметрии при нестабильной работе ПК.

| Параметр | Тип | Значение по умолчанию | Описание |
|---|---|---|---|
| `mode` | `string` | `"hybrid"` | Общий режим работы: `"minimal"`, `"hybrid"`, `"full"`. |
| `buffer_mode` | `string` | `"memory"` | Режим накопления данных: `"memory"`, `"file"`, `"direct"`. |
| `buffer_size` | `integer` | `50` | Максимальное количество записей в буфере перед автоматическим сбросом в БД. |
| `flush_interval_seconds` | `float` | `30.0` | Интервал таймера автоматического сброса буфера в БД (в секундах). |
| `buffer_file` | `string` | `"telemetry_buffer.jsonl"` | Имя файла для сохранения буфера на диске в аварийном режиме сбоев. |
| `max_db_size_mb` | `float` | `50.0` | Предельный размер базы данных SQLite (включая WAL/SHM). При превышении запускается ступенчатая очистка. |
| `retention_days` | `integer` | `7` | Срок хранения сырых снимков и детальных событий телеметрии (в днях). |
| `db_cleanup_interval_seconds` | `float` | `300.0` | Периодичность автоматической проверки размера и очистки БД (в секундах). |
| `auto_vacuum_enabled` | `boolean` | `true` | Разрешение дефрагментации и сжатия SQLite (`VACUUM`) при усечении переполненной БД. |

### 💡 Режимы буферизации (`buffer_mode`):
- **`"memory"` (накопление в RAM)**: Все события, снимки и показания датчиков накапливаются в оперативной памяти. Сброс в SQLite выполняется пачкой (`executemany` в рамках одной WAL-транзакции) по таймеру или по достижении `buffer_size`.
- **`"file"` (аварийный/отказоустойчивый режим)**: При частых сбоях, перезагрузках или нестабильном питании ПК данные немедленно пишутся на диск в append-only JSONL файл с `os.fsync`. При заполнении буфера или по таймеру данные пачкой переносятся в SQLite, а файл очищается. При перезапуске системы остаточный JSON-буфер автоматически импортируется в БД.
- **`"direct"` (прямая запись)**: Буферизация отключена; каждая запись немедленно фиксируется в SQLite.

---

## 2. Режимы сбора и интервалы

| Параметр | Тип | По умолчанию | Описание |
|---|---|---|---|
| `interval_seconds` | `float` | `6.0` | Базовый интервал опроса легковесных метрик (CPU, RAM, сеть, быстрые датчики). |
| `heavy_interval_seconds` | `float` | `90.0` | Интервал опроса тяжелых датчиков (WMI, SMART дисков, LibreHardwareMonitor). |
| `fast_interval_seconds` | `float` | `30.0` | Интервал быстрого режима при детальной диагностике. |
| `fast_duration_days` | `integer` | `2` | Максимальная длительность быстрого режима (в днях). |
| `aggregation_interval_seconds` | `float` | `3600` | Интервал почасовой агрегации показаний сенсоров в БД (1 час). |
| `max_file_size_mb` | `float` | `50` | Максимальный размер лог-файлов до ротации (в МБ). |
| `enable_autolog` | `boolean` | `true` | Флаг автоматической фоновой записи метрик. |
| `default_interval` | `string` | `"1 minute"` | Интервал по умолчанию для логгеров приложений. |

---

## 3. Управление процессами

| Параметр | Тип | По умолчанию | Описание |
|---|---|---|---|
| `process_mode` | `string` | `"top_n"` | Режим сохранения процессов: `"top_n"` (только наиболее активные) или `"all"` (все процессы). |
| `top_processes` | `integer` | `10` | Количество сохраняемых процессов с наибольшей нагрузкой CPU/RAM. |
| `low_priority` | `boolean` | `true` | Автоматическое понижение приоритета фонового процесса сбора для исключения влияния на систему. |

---

## 4. Тяжелые коллекторы и автопереключение

| Параметр | Тип | По умолчанию | Описание |
|---|---|---|---|
| `heavy_disk_scan_interval_seconds` | `float` | `43200` | Интервал глубокого сканирования состояния накопителей (12 часов). |
| `heavy_mode_max_duration_days` | `float` | `5` | Предельная длительность непрерывной работы тяжелого режима. |
| `heavy_mode_auto_switch_enabled` | `boolean` | `true` | Автоматический возврат в гибридный/легкий режим по истечении лимита времени. |
| `heavy_collectors.hardware_sensors` | `boolean` | `true` | Опрос аппаратных датчиков напряжений, вентиляторов и температур. |
| `heavy_collectors.storage_smart` | `boolean` | `true` | Опрос SMART-атрибутов и степени износа накопителей. |
| `heavy_collectors.network_ping` | `boolean` | `true` | Проверка задержки и доступности интернет-хостов. |
| `heavy_collectors.inventory_wmi` | `boolean` | `true` | Полный сбор оборудования через WMI. |

---

## 5. Логгеры приложений (`loggers`)

Секция задает периодичность и статус активности фоновых логгеров модулей системы:

| Логгер | Интервал по умолчанию | Описание |
|---|---|---|
| `system_inspector` | `5 seconds` | Инспектор системных ресурсов и общей нагрузки ОС. |
| `hardware_monitor` | `5 seconds` | Монитор аппаратных компонентов и датчиков. |
| `librehardwaremonitor` | `5 seconds` | Интеграция с LibreHardwareMonitor DLL / OpenHardwareMonitor. |
| `windows_sysadmin` | `1 minute` | Мониторинг служб, задач и системного окружения. |
| `windows_defender` | `1 hour` | Состояние антивируса и журнала угроз Defender. |
| `windows_startup_auditor` | `1 hour` | Аудит программ автозагрузки, планировщика и сервисов. |
| `windows_backup_manager` | `6 hours` | Мониторинг резервных копий и целостности архивов. |
| `registry_viewer` | `1 hour` | Отслеживание изменений критических ветвей реестра. |
| `software_audit` | `1 hour` | Аудит установленного и неиспользуемого ПО. |
| `website_monitor` | `5 minutes` | Мониторинг доступности внешних сайтов и API. |
| `gcloud_monitor` | `5 minutes` | Метрики облачной инфраструктуры Google Cloud. |
| `cloudflared_monitor` | `30 seconds` | Статус туннелей Cloudflare. |
| `trading_terminal` | `10 seconds` | Состояние торговых соединений и котировок. |
| `user_assistant` | `5 minutes` | Журнал работы ассистента. |
| `helpdesk` | `1 minute` | Очередь тикетов и обращений. |

---

## 6. Конфигурация сенсоров (`sensors`)

Каждый блок определяет активность (`enabled`), интервал опроса (`interval_seconds`) и собираемые метрики (`metrics`):

| Сенсор | Интервал | Метрики |
|---|---|---|
| `cpu` | `5.0 с` | `temperature`, `load`, `clocks` |
| `gpu` | `10.0 с` | `temperature`, `load`, `memory`, `power` |
| `ram` | `10.0 с` | `usage`, `swap` |
| `disk` | `30.0 с` | `usage`, `io` |
| `network` | `10.0 с` | `throughput`, `connections` |
| `sensors` | `10.0 с` | `temperature`, `fan`, `voltage` |
| `internet` | `120.0 с` | `ping`, `download`, `upload`, `dns` |
| `storage` | `32000.0 с` | `smart_attributes`, `temperature`, `wear_level` |
| `device_flapping` | `30.0 с` | `connect_events`, `disconnect_events`, `flapping_count` |

---

## 7. Опции телеметрии (`telemetry_options`)

| Параметр | Тип | Значение | Описание |
|---|---|---|---|
| `collect_serial_numbers` | `boolean` | `true` | Сбор серийных номеров оборудования (диски, материнская плата, BIOS). |
| `collect_hardware_inventory`| `boolean` | `true` | Полный аудит инвентаря устройств. |
| `collect_file_events` | `boolean` | `true` | Отслеживание файловых аномалий в наблюдаемых каталогах. |
| `max_file_size_mb` | `integer` | `50` | Лимит размера JSONL-файла журнала измерений. |
| `watch_directories` | `array` | `["C:\\Users\\"]` | Список директорий для отслеживания файловых изменений. |

---

## 8. Низкоуровневый сборщик Windows (`w64_collector`)

Интеграция с нативными подсистемами мониторинга Windows и трассировкой событий ETW (Event Tracing for Windows):

| Параметр | Тип | Описание |
|---|---|---|
| `enabled` | `boolean` | Общая активность модуля W64. |
| `enable_file_monitoring` | `boolean` | Мониторинг изменений в файловой системе через ReadDirectoryChangesW. |
| `enable_process_monitoring` | `boolean` | Отслеживание создания и завершения процессов (WMI/ETW). |
| `enable_registry_monitoring`| `boolean` | Перехват изменений реестра (RegNotifyChangeKeyValue). |
| `enable_network_monitoring` | `boolean` | Мониторинг сетевых соединений и открытых портов. |
| `enable_event_log_monitoring`| `boolean` | Чтение системных журналов Windows Event Log. |
| `enable_process_trace` | `boolean` | Низкоуровневая ETW-трассировка процессов. |
| `enable_disk_trace` | `boolean` | ETW-трассировка операций блочного ввода-вывода дисков. |
| `enable_network_trace` | `boolean` | ETW-трассировка сетевых пакетов TCP/IP. |
| `enable_registry_trace` | `boolean` | ETW-трассировка операций с ключами реестра. |
