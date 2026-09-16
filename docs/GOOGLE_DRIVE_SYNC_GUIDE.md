# Руководство по синхронизации данных на Google Drive

## Обзор

Этот модуль позволяет автоматически синхронизировать все накапливающиеся данные (базы данных, RAG индексы, логи, секреты и конфигурации) на Google Drive для облачного хранения и резервного копирования.

## Возможности

✓ **Автоматическая синхронизация** - Регулярная синхронизация по расписанию (по умолчанию каждые 6 часов)
✓ **Ручная синхронизация** - Можно запустить синхронизацию в любой момент
✓ **Выборочная синхронизация** - Синхронизировать отдельные файлы или директории
✓ **Интеграция с REST API** - Управление через HTTP запросы
✓ **Безопасное хранение** - Секреты и конфиги хранятся отдельно с контролем доступа
✓ **Логирование** - Полная история всех операций синхронизации

## Структура данных на Google Drive

```
AI-Breadboard-Sync/
├── data/                    # Основные данные
│   ├── news_service.db
│   ├── rag_documents/
│   ├── rag_index/
│   ├── telegram_rag/
│   └── users/
├── logs/                    # Логи приложения
│   ├── cloudflared.log
│   ├── telegram_bot.log
│   ├── uvicorn_*.log
│   └── ...
├── secrets/                 # Конфиги и секреты (защищённые)
│   ├── google_*.json
│   ├── gemini_keys.json
│   └── ...
└── configs/                 # Конфигурационные файлы
    ├── config.json
    ├── .env
    └── .env.example
```

## Предварительные требования

### 1. Google Cloud проект и сервис-аккаунт

#### Шаг 1: Создать Google Cloud проект
- Перейти на [Google Cloud Console](https://console.cloud.google.com/)
- Создать новый проект (или использовать существующий)
- Активировать Google Drive API

#### Шаг 2: Создать сервис-аккаунт
1. Перейти в "Service Accounts" в Google Cloud Console
2. Создать новый сервис-аккаунт
3. Предоставить роль "Editor"
4. Создать JSON ключ
5. Скопировать JSON файл в `src/secrets/google_sa_account_service_account.json`

#### Шаг 3: Поделиться папкой с сервис-аккаунтом
1. Создать папку на Google Drive (или использовать существующую)
2. Получить email сервис-аккаунта из JSON файла
3. Поделиться папкой с этим email адресом

### 2. Установка зависимостей

```bash
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
pip install schedule  # Для планировщика
pip install fastapi uvicorn  # Для REST API
```

## Использование

### Инициализация синхронизации

```bash
python scripts/setup_google_drive_sync.py --init
```

Это проверит подключение, создаст папку синхронизации на Google Drive и подготовит систему.

### Немедленная синхронизация

```bash
python scripts/setup_google_drive_sync.py --sync-now
```

Все данные будут синхронизированы прямо сейчас.

### Запуск автоматического планировщика

```bash
python scripts/setup_google_drive_sync.py --start-scheduler
```

Планировщик будет запущен в фоновом режиме и выполнять синхронизацию по расписанию.

### Проверка статуса

```bash
python scripts/setup_google_drive_sync.py --status
```

## REST API Эндпоинты

### Получить статус синхронизации
```http
GET /api/sync/status
```

### Запустить планировщик
```http
POST /api/sync/start
Content-Type: application/json

{
  "sync_interval_hours": 6,
  "include_data": true,
  "include_logs": true,
  "include_secrets": true,
  "include_configs": true
}
```

### Остановить планировщик
```http
POST /api/sync/stop
```

### Выполнить синхронизацию
```http
POST /api/sync/sync-now
```

### Синхронизировать директорию
```http
POST /api/sync/sync-directory
Content-Type: application/json

{
  "local_path": "data/rag_index",
  "folder_name": "rag_index",
  "recursive": true
}
```

### Синхронизировать файл
```http
POST /api/sync/sync-file
Content-Type: application/json

{
  "file_path": "config.json",
  "folder_name": "configs"
}
```

### Получить информацию о Google Drive
```http
GET /api/sync/drive-info
```

### Проверить подключение
```http
POST /api/sync/test-connection
```

## Интеграция с приложением

### Использование в Python коде

```python
from src.integrations.google_drive_sync import GoogleDriveSync

# Создание сервиса синхронизации
sync = GoogleDriveSync()

# Синхронизация директории
sync.sync_directory("data", sync.root_folder_id)

# Загрузка файла
sync.upload_file("config.json", sync.root_folder_id)
```

### Использование планировщика

```python
from src.integrations.sync_scheduler import get_scheduler, start_sync_scheduler

# Запуск планировщика
start_sync_scheduler(sync_interval_hours=6)

# Выполнить синхронизацию сейчас
scheduler = get_scheduler()
scheduler.sync_now()
```

### Интеграция с FastAPI

```python
from fastapi import FastAPI
from src.integrations.sync_api import include_sync_routes

app = FastAPI()

# Подключить маршруты синхронизации
include_sync_routes(app)
```

## Конфигурация

Конфигурация хранится в `sync_config.json`:

```json
{
  "service_account_file": "src/secrets/google_sa_account_service_account.json",
  "sync_interval_hours": 6,
  "sync_on_startup": false,
  "include_data": true,
  "include_logs": true,
  "include_secrets": true,
  "include_configs": true,
  "exclude_patterns": ["*.pyc", "__pycache__", ".git"]
}
```

## Безопасность

### Рекомендации

1. **Сервис-аккаунт**: Храните JSON ключ безопасно, не коммитьте в репозиторий
2. **Права доступа**: Используйте минимальные необходимые права для сервис-аккаунта
3. **Секреты**: Отдельно контролируйте доступ к папке с секретами на Google Drive
4. **Логирование**: Проверяйте логи на предмет ошибок и несанкционированного доступа

### Исключение чувствительных файлов

Если нужно исключить определённые файлы из синхронизации, добавьте их в `exclude_patterns` в конфигурации.

## Мониторинг и уведомления

### Логирование

Все операции логируются в:
- `sync_setup.log` - Логи скрипта инициализации
- Системное логирование приложения

### Проверка статуса

```python
from src.integrations.google_drive_sync import GoogleDriveSync

sync = GoogleDriveSync()
status = sync.get_sync_status()
print(status)
```

## Решение проблем

### Ошибка: "Файл сервис-аккаунта не найден"

**Решение**: Убедитесь, что JSON ключ находится в `src/secrets/google_sa_account_service_account.json`

### Ошибка: "Нет доступа к Google Drive"

**Решение**: 
- Проверьте, что сервис-аккаунту предоставлены права на Google Drive
- Убедитесь, что папка поделена с email сервис-аккаунта

### Ошибка: "Синхронизация не началась"

**Решение**:
- Проверьте интернет соединение
- Запустите `python scripts/setup_google_drive_sync.py --test-connection`
- Проверьте логи в `sync_setup.log`

### Большие файлы синхронизируются медленно

**Решение**: Это нормально. Google Drive API имеет ограничения на скорость. Для больших файлов используйте фоновую синхронизацию.

## Расширение функциональности

### Добавление уведомлений на Telegram

```python
from src.integrations.sync_scheduler import SyncScheduler

class TelegramSyncScheduler(SyncScheduler):
    def _send_sync_notification(self, results, duration):
        # Отправка в Telegram
        send_telegram_message(f"Синхронизация завершена: {results}")
```

### Добавление фильтрации данных

```python
# Синхронизация только недавно изменённых файлов
sync.sync_directory(
    "data",
    sync.root_folder_id,
    exclude_patterns=["*.pyc", "__pycache__"],
    filter_recent=True  # Только файлы за последние 24 часа
)
```

## Примеры использования

### Пример 1: Автоматическая синхронизация при запуске приложения

```python
from src.integrations.sync_scheduler import start_sync_scheduler
import time

# При запуске приложения
start_sync_scheduler(sync_interval_hours=6)

# Приложение продолжает работать, синхронизация происходит в фоне
```

### Пример 2: Синхронизация после сохранения важного файла

```python
from src.integrations.sync_scheduler import ManualSyncHandler

handler = ManualSyncHandler()

# После сохранения конфига
handler.sync_single_file("config.json", "configs")
```

### Пример 3: Получение статуса синхронизации в приложении

```python
import requests

response = requests.get("http://localhost:8000/api/sync/status")
status = response.json()
print(f"Последняя синхронизация: {status['last_sync_time']}")
```

## Часто задаваемые вопросы

**Q: Как часто синхронизируются данные?**
A: По умолчанию каждые 6 часов. Можно изменить в конфигурации.

**Q: Что произойдёт, если интернет отключится?**
A: Синхронизация будет повторена при восстановлении соединения.

**Q: Можно ли синхронизировать только определённые директории?**
A: Да, используйте `/api/sync/sync-directory` для выборочной синхронизации.

**Q: Безопасно ли хранить секреты на Google Drive?**
A: Да, если у вас есть контроль доступа к аккаунту Google Drive и использован сервис-аккаунт с ограниченными правами.

**Q: Как удалить данные с Google Drive?**
A: Просто удалите папку `AI-Breadboard-Sync` в Google Drive.

## Поддержка

Для вопросов и проблем:
1. Проверьте раздел "Решение проблем" выше
2. Проверьте логи приложения
3. Откройте issue в репозитории

## Лицензия

Этот модуль является частью AI-Breadboard и распространяется под той же лицензией.
