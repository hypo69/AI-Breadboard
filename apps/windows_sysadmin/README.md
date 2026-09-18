# 🪟 Windows System Administrator & File Deletion Auditor

Интерактивный комплекс для системного администрирования Windows, мониторинга пользовательских сессий, управления Active Directory, а также аудита файловой системы и регистрации удаления файлов (Windows Security Auditing Event ID 4663, 4660, SACL, `auditpol` и мониторинг в реальном времени `ReadDirectoryChangesW`).

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

- **Аудит удаления файлов (Security Auditing)** — фиксация точного пути к объекту, процесса-инициатора (`ProcessName`, `PID`), учетной записи пользователя (`SubjectUserName`, `Domain`) и дескриптора (`HandleId`) через корреляцию событий `4663` и `4660`.
- **Управление политиками аудита (auditpol)** — проверка и переключение подкатегории аудита `File System` (Success / Failure).
- **Инспекция и настройка SACL** — проверка наличия правил аудита удаления (`Delete`, `DeleteSubdirectoriesAndFiles`) для целевых каталогов и их автоматическая установка.
- **Мониторинг изменений в реальном времени** — отслеживание создания, изменения, удаления и переименования файлов через WinAPI `ReadDirectoryChangesW` без задержек системного журнала.
- **Мониторинг пользовательских сессий** — просмотр активных пользователей, времени входа, IP-адресов, количества процессов и отключение сессий.
- **Статус Active Directory** — проверка подключения к домену и контроллеру.
- **FastAPI REST API & Web GUI Tab** — полная интеграция в панель администратора AI Breadboard (`windows_admin_tab`).

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
python -m apps.windows_sysadmin --file-audit-status

# Включить системный аудит файловой системы (auditpol /set /subcategory:'File System')
python -m apps.windows_sysadmin --set-audit-policy

# Настроить SACL аудита удаления на целевой каталог
python -m apps.windows_sysadmin --configure-sacl "C:\Users\onela\AppData\Local\AI-Breadboard"

# Посмотреть список удалений за последние 24 часа
python -m apps.windows_sysadmin --deletions --hours 24
```

---

## Архитектура

```
apps/windows_sysadmin/
├── src/
│   ├── state.py              # Бизнес-логика: SystemAdminState, UserSession, SecurityEvent
│   ├── file_auditor.py       # Движок аудита файлов: WindowsFileAuditor, auditpol, SACL, события 4663/4660
│   └── directory_watcher.py  # Мониторинг в реальном времени: WinAPI ReadDirectoryChangesW
├── tui.py                    # TUI-рендерер и интерактивный dashboard
├── router.py                 # FastAPI endpoints для REST API (/api/sysadmin/*)
├── __main__.py               # Точка входа (CLI + standalone server)
├── __init__.py               # Экспорт пакета
└── config.json               # Конфигурация сервера (порт 8100)
```

---

## Установка

```bash
cd apps/windows_sysadmin
pip install -r ../../requirements.txt
```

---

## Использование

### Интерактивный dashboard (TUI)

```bash
python -m apps.windows_sysadmin
```

### FastAPI сервер

```bash
python -m apps.windows_sysadmin --mode server
```

По умолчанию сервер запускается на `http://127.0.0.1:8100`.

---

## FastAPI endpoints

### Общее состояние
- `GET /api/sysadmin/status` — общий статус хоста, пользователей и политики `file_audit`.
- `GET /api/sysadmin/users` — список активных сессий пользователей.
- `GET /api/sysadmin/events` — общие события безопасности.
- `POST /api/sysadmin/users/{username}/disconnect` — отключение сессии пользователя.

### Аудит файловой системы и удалений
- `GET /api/sysadmin/file-audit/policy` — проверка статуса `auditpol /subcategory:'File System'`.
- `POST /api/sysadmin/file-audit/policy` — включение/отключение системного аудита `File System`.
- `GET /api/sysadmin/file-audit/folder-sacl?path=<PATH>` — проверка SACL на указанной папке.
- `POST /api/sysadmin/file-audit/folder-sacl` — настройка SACL аудита удаления на папку.
- `GET /api/sysadmin/file-audit/deletions?hours=24` — извлечение и сопоставление событий 4663/4660 из Security Log.
- `GET /api/sysadmin/file-audit/live-events` — поток событий реального времени (`ReadDirectoryChangesW`).

---

## Лицензия

© 2026 hypo69. Все права защищены.
