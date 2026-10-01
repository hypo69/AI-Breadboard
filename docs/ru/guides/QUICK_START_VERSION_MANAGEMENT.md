# Быстрый старт: Управление версиями и обновления

## TL;DR (Самое важное)

```bash
# Проверить наличие обновлений
python main.py --check-update

# Автоматически обновиться (если есть обновления)
export AUTO_UPDATE=true
python main.py
```

## Где хранятся логи и резервные копии?

Все логи и резервные копии хранятся в системной временной папке:

**Windows:**
```
C:\Users\<username>\AppData\Local\Temp\ai-breadboard\
├── logs/        (логи приложения)
├── backups/     (резервные копии)
└── updates/     (история обновлений)
```

**Linux:**
```
/tmp/ai-breadboard/
├── logs/        (логи приложения)
├── backups/     (резервные копии)
└── updates/     (история обновлений)
```

**macOS:**
```
/var/folders/XX/XXX...XXX/T/ai-breadboard/
├── logs/        (логи приложения)
├── backups/     (резервные копии)
└── updates/     (история обновлений)
```

## Основные команды

### 1. Проверить версию приложения

```bash
python main.py --check-update
```

**Вывод:**
```
INFO: Текущая версия: v1.0.0
INFO: Удалённая версия: v1.0.1
INFO: A newer version is available: v1.0.1 (current: v1.0.0).
Do you want to update the code from origin and restart? [y/N]:
```

### 2. Запустить приложение с автоматическим обновлением

```bash
# Одноразово
python main.py --check-update-and-run

# Постоянно (через переменную окружения)
export AUTO_UPDATE=true
python main.py

# Только в этот раз (Windows PowerShell)
$env:AUTO_UPDATE='true'; python main.py
```

### 3. Использовать REST API для управления версиями

```bash
# Проверить обновления через API
curl http://localhost:8000/api/version/check

# Выполнить update через API
curl -X POST http://localhost:8000/api/version/update \
  -H "Content-Type: application/json" \
  -d '{"branch": "main", "auto_backup": true}'

# Просмотреть резервные копии
curl http://localhost:8000/api/version/backups

# Получить полный status
curl http://localhost:8000/api/version/status
```

## Examples в коде

### Пример 1: Проверить обновления в Python скрипте

```python
from core.version_manager import get_version_manager

vm = get_version_manager()

# Проверить обновления
check = vm.check_updates()

if check['is_update_available']:
    print(f"Доступно update: {check['current_version']} → {check['remote_version']}")
else:
    print(f"Приложение актуально: {check['current_version']}")
```

### Пример 2: Выполнить update с резервной копией

```python
import asyncio
from core.version_manager import get_version_manager

async def safe_update():
    vm = get_version_manager()
    
    # Выполнить update (автоматически создаст резервную копию)
    result = await vm.update_application(
        branch="main",
        auto_backup=True
    )
    
    if result['success']:
        print(f"✓ Update successfully: {result['version']}")
        print(f"  Резервная копия: {result['backup_path']}")
    else:
        print(f"✗ Error обновления: {result['message']}")

asyncio.run(safe_update())
```

### Пример 3: Восстановление из резервной копии

```python
from pathlib import Path
from core.version_manager import get_version_manager

vm = get_version_manager()

# Получить list резервных копий
backup_dir = Path.home() / '.../ai-breadboard/backups'
backups = list(backup_dir.iterdir())

if backups:
    # Восстановить из последней резервной копии
    latest_backup = sorted(backups)[-1]
    success = vm.restore_from_backup(latest_backup)
    
    if success:
        print(f"✓ Восстановление из {latest_backup.name}")
    else:
        print(f"✗ Error восстановления")
```

### Пример 4: Использование FastAPI клиента

```python
import httpx
import asyncio

async def check_and_update():
    async with httpx.AsyncClient() as client:
        # Проверить обновления
        response = await client.get("http://localhost:8000/api/version/check")
        status = response.json()
        
        print(f"Текущая версия: {status['current_version']}")
        print(f"Удалённая версия: {status['remote_version']}")
        print(f"Update доступно: {status['is_update_available']}")
        
        if status['is_update_available']:
            # Выполнить update
            response = await client.post(
                "http://localhost:8000/api/version/update",
                json={"branch": "main", "auto_backup": True}
            )
            result = response.json()
            print(f"\nРезультат обновления:")
            print(f"  Success: {result['success']}")
            print(f"  Версия: {result['version']}")
            if result['backup_path']:
                print(f"  Резервная копия: {result['backup_path']}")

asyncio.run(check_and_update())
```

## Автоматизация обновлений

### Windows Scheduler

1. Создать bat файл `update_app.bat`:
```batch
@echo off
cd C:\path\to\ai-breadboard
set AUTO_UPDATE=true
python main.py --check-update
```

2. Добавить задачу в Windows Scheduler:
```powershell
$trigger = New-ScheduledTaskTrigger -AtStartup
$action = New-ScheduledTaskAction -Execute "C:\path\to\update_app.bat"
Register-ScheduledTask -TaskName "AI-Breadboard-Update" -Trigger $trigger -Action $action -RunLevel Highest
```

### Linux/macOS Cron

Добавить в crontab:
```bash
# Проверять обновления каждый день в 3:00 AM
0 3 * * * cd /path/to/ai-breadboard && AUTO_UPDATE=true python main.py --check-update >> /var/log/ai-breadboard-update.log 2>&1
```

### Docker

В Dockerfile:
```dockerfile
# Проверить обновления при запуске контейнера
ENTRYPOINT ["sh", "-c", "AUTO_UPDATE=true python main.py"]
```

## Решение проблем

### Проблема: "Git не установлен"
```
Error: Git command failed: 'git' is not recognized
```

**Решение:** Установить git с https://git-scm.com

### Проблема: "Нет прав для обновления"
```
Error: Permission denied when writing to backup directory
```

**Решение:** Проверить права доступа к системной temp папке:
```bash
# Linux/macOS
chmod 755 /tmp/ai-breadboard/

# Windows (PowerShell as Admin)
icacls "C:\Users\<user>\AppData\Local\Temp\ai-breadboard" /grant:r "$env:USERNAME`:(OI)(CI)F"
```

### Проблема: "Недостаточно дискового пространства"
```
Error: No space left on device
```

**Решение:** Очистить старые резервные копии:
```python
from core.version_manager import get_version_manager

vm = get_version_manager()
deleted = vm.cleanup_old_backups(keep_count=2)
print(f"Удалено старых копий: {deleted}")
```

### Проблема: "Конфликт при объединении"
```
Error: Merge conflict detected
```

**Решение:** Резервная копия была автоматически восстановлена. Вручную разрешить конфликт:
```bash
# В директории репозитория
git status  # Посмотреть конфликты
# Разрешить конфликты вручную
git add .
git commit -m "Resolved merge conflicts"
```

## Переменные окружения

```bash
# Включить автоматическое update
export AUTO_UPDATE=true

# Использовать специальную ветку для обновлений
export GIT_BRANCH=develop

# Установить GitHub токен для приватных репозиториев
export GITHUB_TOKEN=ghp_xxxxxxxxxxxx

# Отключить проверку версий
export AUTO_UPDATE=false
```

## Структура файлов резервной копии

```
backup_20260831_120530/
├── config.json                 # Конфиг приложения
├── .env                       # Переменные окружения
├── requirements.txt           # Python зависимости
├── core/                      # Основной код
│   ├── version_manager.py
│   ├── logger/
│   ├── ai/
│   └── ...
├── .backup_info.json          # МетаInfo о резервной копии
└── [другие файлы проекта]
```

## Запись логов обновлений

Каждое update записывается в файл:

```json
{
  "timestamp": "2026-08-31T12:05:30.123456",
  "from_version": "v1.0.0",
  "to_version": "v1.0.1",
  "backup_path": "/tmp/ai-breadboard/backups/backup_20260831_120530",
  "branch": "main",
  "status": "success"
}
```

Файлы находятся в:
- Windows: `C:\Users\<user>\AppData\Local\Temp\ai-breadboard\updates\`
- Linux: `/tmp/ai-breadboard/updates/`

## Мониторинг обновлений

Использовать REST API для мониторинга:

```python
import httpx
import asyncio
from datetime import datetime

async def monitor_updates():
    async with httpx.AsyncClient() as client:
        while True:
            # Check каждый час
            response = await client.get("http://localhost:8000/api/version/status")
            status = response.json()
            
            print(f"[{datetime.now()}] Версия: {status['current_version']}")
            print(f"  Update доступно: {status['is_update_available']}")
            print(f"  Резервных копий: {status['backup_count']}")
            
            await asyncio.sleep(3600)  # 1 час

asyncio.run(monitor_updates())
```

## Дополнительная Info

- 📖 [Полная документация](CROSSPLATFORM_LOGGING_AND_UPDATE_GUIDE.md)
- 🔧 Исходный код: `core/version_manager.py`
- 🌐 API эндпоинты: `core/fastapi/router_version.py`
- 📝 Логирование: `core/logger/logger.py`
