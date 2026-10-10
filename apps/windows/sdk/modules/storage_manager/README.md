# 💾 Windows Storage Manager & Raw Block Cloner

Модуль управления физическими накопителями, посекторного клонирования (диск-в-диск), создания raw-образов и прямой низкоуровневой диагностики блочных устройств Windows (`\\.\PhysicalDriveX`) через WinAPI (`CreateFileW`, `ReadFile`, `WriteFile`, `DeviceIoControl`).

---

## 🚀 Возможности

1. **Прямой посекторный ввод-вывод (WinAPI Direct Block I/O)**:
   - Обход буферизации файловой системы (`FILE_FLAG_NO_BUFFERING`).
   - Чтение и запись произвольных LBA секторов физического диска.
   - Детальный HEX и ASCII дамп секторов (MBR, GPT, VBR, скрытые сектора).

2. **Посекторное клонирование (Raw & Smart Clone)**:
   - `raw` режим: абсолютная посекторная копия всего диска (ESP, MSR, Recovery, NTFS/ReFS, неразмеченная область).
   - `smart` режим: анализ таблицы разделов GPT/MBR и выборочное копирование только используемых разделов и критических секторов.

3. **Создание и восстановление raw-образов**:
   - `disk.image.create` — создание посекторного образа диска в файл (`.img`/`.raw`).
   - `disk.image.restore` — запись образа обратно на блочное устройство.

4. **Контроль целостности и хеширование**:
   - `disk.hash` — потоковый расчет SHA-256 хеша диапазона секторов.
   - `disk.verify` — посекторная верификация дисков или диска с образом.

5. **Безопасность SafeOps**:
   - Симуляция операций (`dry_run=True`) по умолчанию.
   - Защита системного диска (`PhysicalDrive0` / Windows Boot) от случайной перезаписи без флага `force_system_drive` и явного подтверждения.
   - Асинхронный мониторинг фоновых задач (прогресс, скорость МБ/с, ETA, отмена).

---

## 📡 REST API Эндпоинты (`/api/v1/storage`)

| Метод | Маршрут | Описание |
|---|---|---|
| `GET` | `/api/v1/storage/disks` | Список всех физических блочных дисков (`disk.list`) |
| `GET` | `/api/v1/storage/disks/{disk_id}` | Детальная геометрия, разметка MBR/GPT и SMART (`disk.info`) |
| `POST` | `/api/v1/storage/disks/{disk_id}/read` | Прямое чтение секторов и HEX дамп (`disk.read`) |
| `POST` | `/api/v1/storage/disks/{disk_id}/write` | Прямая запись секторов (`disk.write`) |
| `POST` | `/api/v1/storage/disks/{source}/clone` | Запуск клонирования диск-в-диск (`disk.clone`) |
| `POST` | `/api/v1/storage/disks/{disk_id}/image` | Создание raw-образа диска (`disk.image.create`) |
| `POST` | `/api/v1/storage/disks/{disk_id}/restore` | Восстановление диска из образа (`disk.image.restore`) |
| `POST` | `/api/v1/storage/disks/{disk_id}/verify` | Посекторная верификация диска (`disk.verify`) |
| `POST` | `/api/v1/storage/disks/{disk_id}/hash` | Вычисление SHA-256 хеша секторов (`disk.hash`) |
| `GET` | `/api/v1/storage/tasks` | Список фоновых задач |
| `GET` | `/api/v1/storage/tasks/{task_id}` | Прогресс и статус задачи |
| `DELETE` | `/api/v1/storage/tasks/{task_id}` | Отмена выполняющейся задачи |
| `GET` | `/api/v1/storage/report` | Сводный отчет о накопителях и томах |
| `GET` | `/api/v1/storage/volumes` | Список логических томов |
| `GET` | `/api/v1/storage/fs/features` | Состояние TRIM, 8.3 имен, сжатия |

---

## 🖥️ Использование через CLI

```powershell
# Сводный TUI дашборд
py -m apps.windows.sdk.modules.storage_manager

# Список накопителей в формате JSON
py -m apps.windows.sdk.modules.storage_manager list --json

# Детальная инспекция геометрии и разделов PhysicalDrive0
py -m apps.windows.sdk.modules.storage_manager info 0

# Чтение и дамп LBA 0 (MBR)
py -m apps.windows.sdk.modules.storage_manager read 0 --lba 0 --count 1

# Симуляция клонирования PhysicalDrive1 в PhysicalDrive2 (Dry-Run)
py -m apps.windows.sdk.modules.storage_manager clone --source 1 --target 2 --mode raw --dry-run

# Создание raw-образа диска
py -m apps.windows.sdk.modules.storage_manager image --disk 1 --out D:\backup.img --dry-run

# Расчет SHA-256 хеша первых 2048 секторов диска 0
py -m apps.windows.sdk.modules.storage_manager hash 0 --lba 0 --count 2048

# Запуск выделенного REST API микросервиса
py -m apps.windows.sdk.modules.storage_manager server --port 8120
```
