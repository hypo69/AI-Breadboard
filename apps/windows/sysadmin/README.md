# 🪟 Windows System Administrator & Multi-Directory File Auditor

Интерактивный комплекс для системного администрирования Windows, мониторинга пользовательских сессий, управления Active Directory, а также аудита файловой системы и регистрации удаления файлов (Windows Security Auditing Event ID 4663, 4660, SACL, `auditpol` и мониторинг изменений в реальном времени `ReadDirectoryChangesW` с поддержкой одновременного наблюдения за множеством каталогов).

## 📋 Оглавление
- [Возможности](#возможности)
- [Аудит файловой системы и удаления файлов](#аудит-файловой-системы-и-удаления-файлов)
- [Архитектура](#архитектура)
- [Установка](#установка)
- [Использование](#использование)
- [FastAPI endpoints](#fastapi-endpoints)
- [Конфигурация](#конфигурация)

---

## Возможности

- **Множественный мониторинг в реальном времени (Multi-Directory Real-Time Watcher)** — одновременное потоковое отслеживание нескольких папок через WinAPI `ReadDirectoryChangesW` с агрегацией событий в единый поток и фиксацией в CSV.
- **Интерактивный проводник папок и дисков** — выбор каталогов из системы в модальном окне с навигацией по логическим дискам (`C:`, `D:`, `E:`), хлебными крошками и быстрыми пресетами.
- **Аппаратные и программные сенсоры дисков** — определение накопителей отслеживаемых папок, сбор I/O (KB/s, IOPS), мониторинг температур через LHM и расчет темпа операций (events/sec, created/sec, deleted/sec).
- **Аудит удаления файлов (Security Auditing)** — фиксация точного пути к объекту, процесса-инициатора (`ProcessName`, `PID`), учетной записи пользователя (`SubjectUserName`, `Domain`) и дескриптора (`HandleId`) через корреляцию событий `4663` и `4660`.
- **Управление политиками аудита (auditpol)** — проверка и переключение подкатегории аудита `File System` (Success / Failure).
- **Инспекция и настройка SACL** — проверка наличия правил аудита удаления (`Delete`, `DeleteSubdirectoriesAndFiles`) для целевых каталогов и их автоматическая установка.
- **Мониторинг пользовательских сессий** — просмотр активных пользователей, времени входа, IP-адресов, количества процессов и отключение сессий.
- **Статус Active Directory** — проверка подключения к домену и контроллеру.
- **FastAPI REST API & Web GUI Tab** — полная интеграция в панель System Inspector AI Breadboard (`system_inspector_tab`).

---

## Аудит файловой системы и удаления файлов

### 1. Как работает механизм аудита в Windows

| Event ID | Назначение | Особенности |
|---|---|---|
| **4663** | Попытка доступа к объекту с маской `DELETE` (`0x10000`) | Содержит имя файла/папки (`ObjectName`), процесс (`ProcessName`, `PID`), пользователя и `HandleId`. |
| **4660** | Объект был удалён | Подтверждает факт удаления, содержит `HandleId`, связывается с `4663`. |
| **4656** | Запрошен дескриптор доступа к объекту | Фиксирует запрос дескриптора на удаление. |
| **4658** | Дескриптор объекта закрыт | Завершение сессии работы с файлом. |

### 2. Активация через CLI

```powershell
# Проверить статус политики аудита
python -m apps.windows.sysadmin --file-audit-status

# Включить системный аудит файловой системы (auditpol /set /subcategory:'File System')
python -m apps.windows.sysadmin --set-audit-policy

# Настроить SACL аудита удаления на целевой каталог
python -m apps.windows.sysadmin --configure-sacl "C:\Users\onela\AppData\Local\AI-Breadboard"

# Посмотреть список удалений за последние 24 часа
python -m apps.windows.sysadmin --deletions --hours 24
```

---

## Архитектура

```
apps/windows/sysadmin/
├── src/
│   ├── state.py              # Бизнес-логика: SystemAdminState, UserSession, SecurityEvent
│   ├── file_auditor.py       # Движок аудита файлов: WindowsFileAuditor, auditpol, SACL, события 4663/4660
│   ├── directory_watcher.py  # Мониторинг в реальном времени: Multi-Directory WinAPI ReadDirectoryChangesW
│   └── watcher_telemetry.py  # Аппаратные и программные сенсоры телеметрии дисков и темпа I/O
├── tui.py                    # TUI-рендерер и интерактивный dashboard
├── router.py                 # FastAPI endpoints для REST API (/api/sysadmin/*)
├── __main__.py               # Точка входа (CLI + standalone server)
├── __init__.py               # Экспорт пакета
└── config.json               # Конфигурация сервера и список watch_directories
```

---

## Установка

```bash
cd apps/windows/sysadmin
pip install -r ../../../requirements.txt
```

---

## Использование

### Интерактивный dashboard (TUI)

```bash
python -m apps.windows.sysadmin
```

### FastAPI сервер

```bash
python -m apps.windows.sysadmin --mode server
```

По умолчанию сервер запускается на `http://127.0.0.1:8100`.

---

## FastAPI endpoints

### Общее состояние
- `GET /api/sysadmin/status` — общий статус хоста, пользователей и политики `file_audit`.
- `GET /api/sysadmin/users` — список активных сессий пользователей.
- `GET /api/sysadmin/events` — общие события безопасности.
- `POST /api/sysadmin/users/{username}/disconnect` — отключение сессии пользователя.

### Проводник файловой системы (Folder Browser)
- `GET /api/sysadmin/filesystem/drives` — список доступных логических дисков (`C:`, `D:`, `E:`) с размером и свободным местом.
- `GET /api/sysadmin/filesystem/browse?path=<PATH>` — получение списка подкаталогов по указанному пути.

### Аудит файловой системы и Multi-Directory Live Watcher
- `GET /api/sysadmin/file-audit/watch-dirs` — получение списка всех текущих отслеживаемых папок.
- `POST /api/sysadmin/file-audit/watch-dirs` — установка и сохранение нового списка отслеживаемых директорий.
- `POST /api/sysadmin/file-audit/watch-dirs/add` — добавление отдельной папки в мониторинг.
- `POST /api/sysadmin/file-audit/watch-dirs/remove` — удаление папки из мониторинга.
- `GET /api/sysadmin/file-audit/live-events` — поток событий реального времени (`ReadDirectoryChangesW`).
- `GET /api/sysadmin/file-audit/telemetry` — программные метрики темпа и аппаратные сенсоры дисков.
- `GET /api/sysadmin/file-audit/policy` — проверка статуса `auditpol /subcategory:'File System'`.
- `POST /api/sysadmin/file-audit/policy` — включение/отключение системного аудита `File System`.
- `GET /api/sysadmin/file-audit/folder-sacl?path=<PATH>` — проверка SACL на указанной папке.
- `POST /api/sysadmin/file-audit/folder-sacl` — настройка SACL аудита удаления на папку.
- `GET /api/sysadmin/file-audit/deletions?hours=24` — извлечение и сопоставление событий 4663/4660 из Security Log.

---

## Лицензия

© 2026 hypo69. Все права защищены.
