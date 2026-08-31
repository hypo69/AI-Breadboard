# Кроссплатформенное логирование и система обновлений

## Резюме
Реализована полная кроссплатформенная поддержка логирования и механизм автоматического обновления приложения с резервным копированием.

## 1. Кроссплатформенное логирование

### Проблема
Ранее логи и временные файлы сохранялись в локальной папке `__root__/tmp`, что не является кроссплатформенным решением.

### Решение
Все логи и временные файлы теперь сохраняются в системной temp директории:
- **Windows**: `%TEMP%\ai-breadboard\`
- **Linux/macOS**: `/tmp/ai-breadboard/`

### Исправленные файлы

#### 1. **core/logger/logger.py**
```python
# Было:
self.log_files_path: Path = __root__ / 'tmp' / 'logs'

# Стало:
self.log_files_path: Path = Path(tempfile.gettempdir()) / 'ai-breadboard' / 'logs'
```

#### 2. **core/logger/log_analyzer.py**
```python
# Было:
LOG_DIR: Path = __root__ / 'tmp' / 'logs'
REPORTS_DIR: Path = __root__ / 'tmp' / 'reports'

# Стало:
LOG_DIR: Path = Path(tempfile.gettempdir()) / 'ai-breadboard' / 'logs'
REPORTS_DIR: Path = Path(tempfile.gettempdir()) / 'ai-breadboard' / 'reports'
```

#### 3. **core/fastapi/router_logs.py**
```python
# Было:
LOG_DIR = __root__ / 'tmp' / 'logs'
REPORTS_DIR = __root__ / 'tmp' / 'reports'

# Стало:
LOG_DIR = Path(tempfile.gettempdir()) / 'ai-breadboard' / 'logs'
REPORTS_DIR = Path(tempfile.gettempdir()) / 'ai-breadboard' / 'reports'
```

#### 4. **core/rag/rules_rag.py**
```python
# Было:
_TMP_RAG_DIR: Path = __root__ / "tmp" / "rag"

# Стало:
_TMP_RAG_DIR: Path = Path(tempfile.gettempdir()) / 'ai-breadboard' / 'rag'
```

### Структура директорий в temp

```
<TEMP>/ai-breadboard/
├── logs/                    # Логи приложения
│   ├── info.log
│   ├── debug.log
│   ├── errors.log
│   ├── log.json
│   ├── fastapi.log
│   ├── gemini.log
│   ├── playwright.log
│   └── yt_dlp.log
├── reports/                 # Отчёты анализа логов
├── rag/                     # RAG данные
├── updates/                 # Логи обновлений
│   └── update_YYYYMMDD_HHMMSS.json
└── backups/                 # Резервные копии
    └── backup_YYYYMMDD_HHMMSS/
        ├── config.json
        ├── .env
        ├── core/
        ├── requirements.txt
        └── .backup_info.json
```

## 2. Механизм обновления приложения

### Новый Module: `core/version_manager.py`

Полнофункциональный менеджер версий с поддержкой:
- Check текущей версии через git теги
- Check доступных обновлений на удалённом репозитории
- Автоматическое создание резервных копий перед обновлением
- Скачивание и применение обновлений
- Восстановление из резервной копии при ошибке
- Очистка старых резервных копий

### Основные функции

#### 1. **VersionManager.check_updates()** - Check обновлений
```python
from core.version_manager import get_version_manager

vm = get_version_manager()
result = vm.check_updates()
print(result)
# {
#     "status": "update_available",
#     "current_version": "v1.0.0",
#     "remote_version": "v1.0.1",
#     "is_update_available": True,
#     "current_commit": "abc1234",
#     "remote_commit": "def5678"
# }
```

#### 2. **VersionManager.backup_files()** - Создание резервной копии
```python
backup_path = vm.backup_files()
print(backup_path)  # Path('/.../ai-breadboard/backups/backup_20260831_120530')
```

#### 3. **VersionManager.fetch_updates()** - Скачивание обновлений
```python
success = vm.fetch_updates()
```

#### 4. **VersionManager.merge_updates()** - Объединение обновлений
```python
success, message = vm.merge_updates(branch="main")
```

#### 5. **VersionManager.update_application()** - Полное update
```python
result = await vm.update_application(branch="main", auto_backup=True)
# {
#     "success": True,
#     "status": "up_to_date",
#     "message": "Update выполнено successfully",
#     "version": "v1.0.1",
#     "backup_path": "/.../backup_..."
# }
```

#### 6. **VersionManager.restore_from_backup()** - Восстановление
```python
success = vm.restore_from_backup(backup_path)
```

#### 7. **VersionManager.cleanup_old_backups()** - Очистка старых копий
```python
deleted_count = vm.cleanup_old_backups(keep_count=5)
```

## 3. API Endpoints для управления версиями

### Новый FastAPI роутер: `core/fastapi/router_version.py`

#### 1. Check обновлений
```bash
GET /api/version/check

Response:
{
  "status": "update_available",
  "current_version": "v1.0.0",
  "remote_version": "v1.0.1",
  "is_update_available": true,
  "message": null
}
```

#### 2. Выполнение обновления
```bash
POST /api/version/update

Request:
{
  "branch": "main",
  "auto_backup": true
}

Response:
{
  "success": true,
  "status": "up_to_date",
  "message": "Update выполнено successfully",
  "version": "v1.0.1",
  "backup_path": "/.../backup_..."
}
```

#### 3. List резервных копий
```bash
GET /api/version/backups

Response:
[
  {
    "path": "/.../backup_20260831_120530",
    "timestamp": "2026-08-31T12:05:30",
    "version": "v1.0.0",
    "files_count": 25
  }
]
```

#### 4. Восстановление из резервной копии
```bash
POST /api/version/restore/backup_20260831_120530

Response:
{
  "success": true,
  "message": "Successfully restored from backup: backup_20260831_120530"
}
```

#### 5. Очистка старых резервных копий
```bash
POST /api/version/cleanup-backups?keep_count=5

Response:
{
  "success": true,
  "message": "Deleted 2 old backups",
  "deleted_count": 2
}
```

#### 6. Полный status версии
```bash
GET /api/version/status

Response:
{
  "status": "up_to_date",
  "current_version": "v1.0.0",
  "remote_version": "v1.0.0",
  "is_update_available": false,
  "current_commit": "abc1234",
  "remote_commit": "abc1234",
  "timestamp": "2026-08-31T12:05:30",
  "backup_count": 5,
  "backup_dir": "/.../ai-breadboard/backups",
  "update_log_dir": "/.../ai-breadboard/updates"
}
```

## 4. Использование при старте приложения

### Автоматическая check версии
При запуске приложение автоматически checks наличие обновлений и логирует результат.

### Запуск с проверкой обновления
```bash
python main.py --check-update
```
Checks обновления и предлагает пользователю обновиться (в интерактивном режиме).

### Запуск с обновлением и стартом
```bash
python main.py --check-update-and-run
```
Checks обновления, применяет их (если доступны) и запускает приложение.

### Автоматическое update через переменную окружения
```bash
export AUTO_UPDATE=true
python main.py
```
Автоматически применяет обновления без подтверждения пользователя.

## 5. Integration в main.py

### Обновлённая function `prompt_and_perform_update()`
- Использует VersionManager для проверки версии
- Автоматически creates резервную копию перед обновлением
- При ошибке восстанавливает из резервной копии
- Имеет fallback на старую реализацию если VersionManager недоступен

### Check версии при старте (`startup_event()`)
- Checks обновления при запуске приложения
- Логирует информацию об актуальности версии
- Предлагает команду для обновления если доступна новая версия

## 6. Особенности и преимущества

✅ **Кроссплатформенность** - работает на Windows, Linux, macOS
✅ **Автоматическое резервное копирование** - перед каждым обновлением
✅ **Восстановление при ошибке** - автоматический откат при проблемах
✅ **Полная история обновлений** - все обновления логируются
✅ **API для управления** - REST endpoints для удалённого управления
✅ **Очистка старых резервных копий** - автоматическое удаление старых копий
✅ **Потокобезопасность** - работает корректно в многопоточной среде
✅ **Подробное логирование** - все операции записываются в логи

## 7. Examples использования

### Check и применение обновления в Python
```python
import asyncio
from core.version_manager import get_version_manager

async def update_app():
    vm = get_version_manager()
    
    # Check обновлений
    check = vm.check_updates()
    print(f"Update available: {check['is_update_available']}")
    
    if check['is_update_available']:
        # Выполнить update
        result = await vm.update_application(branch="main")
        if result['success']:
            print(f"Updated to {result['version']}")
        else:
            print(f"Update failed: {result['message']}")

asyncio.run(update_app())
```

### Использование из API
```python
import requests

# Check обновлений
response = requests.get("http://localhost:8000/api/version/check")
print(response.json())

# Выполнить update
response = requests.post(
    "http://localhost:8000/api/version/update",
    json={"branch": "main", "auto_backup": True}
)
print(response.json())

# List резервных копий
response = requests.get("http://localhost:8000/api/version/backups")
for backup in response.json():
    print(f"Backup: {backup['path']}")
```

## 8. Миграция с локальной tmp папки

Если у вас есть старые логи в `__root__/tmp`, они будут продолжать работать, но новые логи будут сохраняться в системную temp директорию. Рекомендуется очистить старую папку после проверки.

## Заключение

Реализована полнофункциональная система управления версиями с поддержкой кроссплатформенного логирования и безопасного обновления приложения. Все компоненты тестированы и готовы к использованию в production.
