# 🚀 Google Drive Sync для AI-Breadboard

**Автоматическая синхронизация всех данных на Google Drive**

> Ваши базы данных, RAG индексы, логи, конфиги и секреты теперь автоматически сохраняются в облаке 📦

## ⚡ Быстрый старт (3 шага)

### 1. Установить зависимости
```powershell
pip install -r req/sync_requirements.txt
```

### 2. Инициализировать синхронизацию
```powershell
.\sync.ps1 init
```

### 3. Синхронизировать данные
```powershell
# Один раз
.\sync.ps1 sync

# Или автоматически
.\sync.ps1 start
```

**Готово!** ✓ Ваши данные теперь на Google Drive

## 📚 Полная документация

- **[Быстрая настройка](GOOGLE_DRIVE_SYNC_SETUP.md)** - 5 минут до первой синхронизации
- **[Полное руководство](docs/GOOGLE_DRIVE_SYNC_GUIDE.md)** - Все возможности и примеры
- **[Итоговый отчёт](SYNC_IMPLEMENTATION_SUMMARY.md)** - Что было создано

## 🎯 Что синхронизируется

```
📁 data/              - Базы данных, RAG индексы
📝 logs/              - Логи приложения
🔑 secrets/           - Конфиги и ключи
⚙️ configs/           - Конфигурационные файлы
```

## 💻 Команды Windows

### PowerShell
```powershell
.\sync.ps1 init       # Инициализация
.\sync.ps1 sync       # Синхронизировать
.\sync.ps1 start      # Автоматический режим
.\sync.ps1 status     # Статус
```

### CMD
```cmd
sync.cmd init         # Инициализация
sync.cmd sync         # Синхронизировать
sync.cmd start        # Автоматический режим
sync.cmd status       # Статус
```

## 🐧 Linux/Mac

```bash
python scripts/setup_google_drive_sync.py --init
python scripts/setup_google_drive_sync.py --sync-now
python scripts/setup_google_drive_sync.py --start-scheduler
python scripts/setup_google_drive_sync.py --status
```

## 🔗 REST API

Если у вас есть FastAPI приложение:

```python
from src.integrations.sync_api import include_sync_routes
from fastapi import FastAPI

app = FastAPI()
include_sync_routes(app)
```

Затем используйте:
- `GET /api/sync/status` - Статус
- `POST /api/sync/sync-now` - Синхронизировать
- `POST /api/sync/start` - Запустить
- `POST /api/sync/stop` - Остановить

## 🐍 Python API

```python
from src.integrations import (
    GoogleDriveSync,
    start_sync_scheduler,
    get_scheduler,
)

# Синхронизация
sync = GoogleDriveSync()
sync.sync_all_data()

# Планировщик
start_sync_scheduler(sync_interval_hours=6)
scheduler = get_scheduler()
scheduler.sync_now()
```

## 🤔 Часто задаваемые вопросы

**Q: Это безопасно?**
A: Да! Используется Google сервис-аккаунт с ограниченными правами. Секреты находятся в отдельной защищённой папке.

**Q: Как часто синхронизируются данные?**
A: По умолчанию каждые 6 часов. Можно изменить в `sync_config.json`.

**Q: Сколько места?**
A: Зависит от размера данных. Обычно 100MB-1GB. Проверьте квоту Google Drive.

**Q: Что если интернет отключится?**
A: Синхронизация повторится при восстановлении соединения.

**Q: Можно ли отключить синхронизацию логов?**
A: Да, отредактируйте `sync_config.json` и установите `"include_logs": false`.

## 📞 Поддержка

- 📖 [GOOGLE_DRIVE_SYNC_SETUP.md](GOOGLE_DRIVE_SYNC_SETUP.md) - Инструкции
- 📚 [docs/GOOGLE_DRIVE_SYNC_GUIDE.md](docs/GOOGLE_DRIVE_SYNC_GUIDE.md) - Полное руководство
- 🐛 Проверьте `sync_setup.log` для диагностики

## 📦 Файлы проекта

```
📁 src/integrations/
   ├── google_drive_sync.py    # Основной модуль
   ├── sync_scheduler.py       # Планировщик
   ├── sync_api.py             # REST API
   └── __init__.py             # Экспорт

📁 scripts/
   └── setup_google_drive_sync.py   # Скрипт управления

📁 docs/
   └── GOOGLE_DRIVE_SYNC_GUIDE.md   # Полное руководство

📁 req/
   └── sync_requirements.txt        # Зависимости

📁 .kiro/hooks/
   └── auto-sync-on-config-save.json   # Автоматизация

📄 sync.ps1              # PowerShell скрипт
📄 sync.cmd              # Batch скрипт
📄 sync_config.json      # Конфигурация
📄 GOOGLE_DRIVE_SYNC_SETUP.md   # Быстрая настройка
📄 README_SYNC.md        # Этот файл
```

## 🎯 Следующие шаги

1. ✅ Установите зависимости
2. ✅ Подготовьте Google сервис-аккаунт
3. ✅ Инициализируйте: `.\sync.ps1 init`
4. ✅ Запустите синхронизацию: `.\sync.ps1 sync`
5. ✅ (Опционально) Включите автоматический режим: `.\sync.ps1 start`

---

**Готово!** Ваши данные теперь автоматически синхронизируются с Google Drive 🎉

Для полной информации смотрите [GOOGLE_DRIVE_SYNC_SETUP.md](GOOGLE_DRIVE_SYNC_SETUP.md)
