# Быстрая настройка синхронизации на Google Drive

## 🚀 Начало работы (5 минут)

### Шаг 1: Установка зависимостей

```bash
pip install -r req/sync_requirements.txt
```

### Шаг 2: Подготовка сервис-аккаунта Google

1. **Создайте Google Cloud проект**:
   - Перейдите на https://console.cloud.google.com/
   - Создайте новый проект

2. **Активируйте Google Drive API**:
   - В поле поиска введите "Google Drive API"
   - Нажмите "Enable"

3. **Создайте сервис-аккаунт**:
   - Перейдите в "Service Accounts" в левом меню
   - Нажмите "Create Service Account"
   - Заполните имя и описание
   - Нажмите "Create and Continue"
   - Предоставьте роль "Editor"
   - Нажмите "Continue" и "Done"

4. **Создайте JSON ключ**:
   - Найдите созданный сервис-аккаунт в списке
   - Перейдите в таб "Keys"
   - Нажмите "Add Key" → "Create new key"
   - Выберите "JSON"
   - Ключ автоматически скачается

5. **Скопируйте ключ**:
   - Скопируйте скачанный JSON файл в:
     ```
     src/secrets/google_sa_account_service_account.json
     ```

### Шаг 3: Инициализация синхронизации

#### На Windows (PowerShell):
```powershell
.\sync.ps1 init
```

#### На Windows (CMD):
```cmd
sync.cmd init
```

#### На Linux/Mac:
```bash
python scripts/setup_google_drive_sync.py --init
```

**Что произойдёт**:
- ✓ Проверка подключения к Google Drive API
- ✓ Создание папки "AI-Breadboard-Sync" на Google Drive
- ✓ Подготовка системы к синхронизации

## 🔄 Использование

### Синхронизировать данные сейчас

#### Windows (PowerShell):
```powershell
.\sync.ps1 sync
```

#### Windows (CMD):
```cmd
sync.cmd sync
```

#### Linux/Mac:
```bash
python scripts/setup_google_drive_sync.py --sync-now
```

**Что синхронизируется**:
- 📁 `data/` - Базы данных, RAG индексы, пользовательские данные
- 📝 `logs/` - Логи приложения (cloudflared, telegram_bot, uvicorn и т.д.)
- 🔑 `src/secrets/` - Ключи и конфигурации (защищённые)
- ⚙️ `config.json`, `.env` - Конфигурационные файлы

### Автоматическая синхронизация (рекомендуется)

#### Windows (PowerShell):
```powershell
.\sync.ps1 start
```

#### Windows (CMD):
```cmd
sync.cmd start
```

#### Linux/Mac:
```bash
python scripts/setup_google_drive_sync.py --start-scheduler
```

**Что происходит**:
- 🔁 Синхронизация автоматически запускается каждые 6 часов
- ⏰ Также синхронизируется каждый день в полночь
- 🛡️ Продолжает работать в фоновом режиме
- 📊 Нажмите `Ctrl+C` для остановки

### Проверить статус синхронизации

#### Windows (PowerShell):
```powershell
.\sync.ps1 status
```

#### Windows (CMD):
```cmd
sync.cmd status
```

#### Linux/Mac:
```bash
python scripts/setup_google_drive_sync.py --status
```

## 🔗 Интеграция с приложением

### Автоматический запуск при старте приложения

Добавьте в `main.py`:

```python
from src.integrations.sync_scheduler import start_sync_scheduler

# При запуске приложения
if __name__ == "__main__":
    # Запустить синхронизацию в фоне
    start_sync_scheduler(sync_interval_hours=6)
    
    # Запустить приложение
    # ... ваш код ...
```

### REST API управления

Если у вас есть FastAPI приложение:

```python
from fastapi import FastAPI
from src.integrations.sync_api import include_sync_routes

app = FastAPI()

# Подключить эндпоинты синхронизации
include_sync_routes(app)

# Теперь доступны эндпоинты:
# GET /api/sync/status
# POST /api/sync/start
# POST /api/sync/stop
# POST /api/sync/sync-now
```

## 📊 Структура на Google Drive

После синхронизации на Google Drive появится папка:

```
AI-Breadboard-Sync/
├── data/
│   ├── news_service.db
│   ├── rag_documents/
│   ├── rag_index/
│   ├── telegram_rag/
│   └── users/
├── logs/
│   ├── cloudflared.log
│   ├── telegram_bot.log
│   ├── uvicorn_20260912_*.log
│   └── ...
├── secrets/
│   ├── google_*.json
│   ├── gemini_keys.json
│   └── ...
└── configs/
    ├── config.json
    ├── .env
    └── .env.example
```

## ⚙️ Конфигурация

Конфигурация находится в `sync_config.json`:

```json
{
  "service_account_file": "src/secrets/google_sa_account_service_account.json",
  "sync_interval_hours": 6,                    // Интервал синхронизации
  "sync_on_startup": false,                    // Синхронизировать при запуске
  "include_data": true,                        // Включить данные
  "include_logs": true,                        // Включить логи
  "include_secrets": true,                     // Включить секреты
  "include_configs": true,                     // Включить конфиги
  "exclude_patterns": [...],                   // Исключённые файлы
  "drive_folder_name": "AI-Breadboard-Sync"   // Имя папки на Google Drive
}
```

### Изменение интервала синхронизации

Отредактируйте `sync_config.json` и измените `sync_interval_hours`.

Например, для синхронизации каждый час:
```json
{
  "sync_interval_hours": 1
}
```

## 🔐 Безопасность

### ✅ Рекомендации

1. **Никогда не коммитьте JSON ключ**:
   ```bash
   # .gitignore уже содержит:
   src/secrets/
   ```

2. **Используйте минимальные права**:
   - Для сервис-аккаунта используйте роль "Editor" только для папки синхронизации

3. **Защищайте `.env`**:
   - Не делитесь содержимым `.env` файла
   - Используйте отдельные аккаунты Google для разработки и production

## 🐛 Решение проблем

### "Файл сервис-аккаунта не найден"

**Решение**: Убедитесь, что JSON ключ находится в `src/secrets/google_sa_account_service_account.json`

### "Нет доступа к Google Drive API"

**Решение**:
1. Проверьте, что Google Drive API активирована в Google Cloud Console
2. Убедитесь, что в JSON файле правильные данные

### "Синхронизация не начинается"

**Решение**:
1. Проверьте интернет соединение
2. Запустите инициализацию: `.\sync.ps1 init`
3. Проверьте логи в консоли

### Медленная синхронизация больших файлов

**Это нормально**. Google Drive API имеет ограничения на скорость загрузки.

## 📚 Дополнительно

- Полное руководство: [GOOGLE_DRIVE_SYNC_GUIDE.md](docs/GOOGLE_DRIVE_SYNC_GUIDE.md)
- REST API: `/docs` (если запущено FastAPI приложение)
- Логи: `sync_setup.log`

## ❓ Часто задаваемые вопросы

**Q: Будут ли синхронизированы секреты?**
A: Да, но они находятся в отдельной папке `secrets/` на Google Drive. Убедитесь, что только вы имеете доступ.

**Q: Сколько места займёт?**
A: Зависит от размера ваших данных. Обычно 100MB-1GB.

**Q: Можно ли отключить синхронизацию логов?**
A: Да, отредактируйте `sync_config.json` и установите `"include_logs": false`

**Q: Что если я хочу синхронизировать только определённые файлы?**
A: Используйте REST API эндпоинт `/api/sync/sync-file`

## 🚀 Следующие шаги

1. ✅ Установите зависимости: `pip install -r req/sync_requirements.txt`
2. ✅ Подготовьте сервис-аккаунт Google
3. ✅ Инициализируйте синхронизацию: `.\sync.ps1 init`
4. ✅ Запустите первую синхронизацию: `.\sync.ps1 sync`
5. ✅ (Опционально) Запустите автоматический планировщик: `.\sync.ps1 start`

**Готово!** Ваши данные теперь синхронизируются с Google Drive 🎉
