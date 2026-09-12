# 📋 Следующие шаги для запуска Google Drive Sync

## ⚡ Быстрый старт (15 минут)

### 1. Подготовить Google Account (10 минут)

**Прочитать**: [GOOGLE_SETUP_INSTRUCTIONS.md](GOOGLE_SETUP_INSTRUCTIONS.md)

**Краткий процесс**:
1. Google Cloud Console → Создать проект
2. Активировать Google Drive API
3. Создать Service Account
4. Скачать JSON ключ
5. Скопировать в `src/secrets/google_sa_account_service_account.json`

### 2. Установить зависимости (2 минуты)

```bash
pip install -r req/sync_requirements.txt
```

### 3. Инициализировать (1 минута)

```powershell
.\sync.ps1 init
```

Скрипт проверит подключение и создаст папку на Google Drive.

### 4. Синхронизировать (зависит от объёма)

```powershell
# Один раз
.\sync.ps1 sync

# Или автоматически (рекомендуется)
.\sync.ps1 start
```

---

## 📚 Документация по ролям

### 👤 Для конечного пользователя
Прочитайте в этом порядке:
1. **[README_SYNC.md](README_SYNC.md)** - Что это такое
2. **[GOOGLE_DRIVE_SYNC_SETUP.md](GOOGLE_DRIVE_SYNC_SETUP.md)** - Как запустить
3. Используйте команды `.\sync.ps1 sync` или `.\sync.ps1 start`

### 👨‍💻 Для разработчика
Прочитайте в этом порядке:
1. **[README_SYNC.md](README_SYNC.md)** - Общий обзор
2. **[docs/GOOGLE_DRIVE_SYNC_GUIDE.md](docs/GOOGLE_DRIVE_SYNC_GUIDE.md)** - Полное руководство
3. **[SYNC_IMPLEMENTATION_SUMMARY.md](SYNC_IMPLEMENTATION_SUMMARY.md)** - Технические детали
4. Используйте Python API или REST API

### 🏗️ Для архитектора/DevOps
Прочитайте:
1. **[SYNC_IMPLEMENTATION_SUMMARY.md](SYNC_IMPLEMENTATION_SUMMARY.md)** - Архитектура
2. **[docs/GOOGLE_DRIVE_SYNC_GUIDE.md](docs/GOOGLE_DRIVE_SYNC_GUIDE.md)** - Все возможности
3. **[GOOGLE_SETUP_INSTRUCTIONS.md](GOOGLE_SETUP_INSTRUCTIONS.md)** - Подготовка среды

---

## 🎯 Использование в коде

### FastAPI приложение

```python
from fastapi import FastAPI
from src.integrations.sync_api import include_sync_routes

app = FastAPI()

# Подключить эндпоинты синхронизации
include_sync_routes(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

Затем используйте:
- `GET http://localhost:8000/api/sync/status`
- `POST http://localhost:8000/api/sync/sync-now`
- Просмотрите документацию: `http://localhost:8000/docs`

### Запуск с автоматической синхронизацией

```python
from src.integrations import start_sync_scheduler

# В main() или при запуске приложения
if __name__ == "__main__":
    # Запустить синхронизацию в фоне
    start_sync_scheduler(sync_interval_hours=6)
    
    # Запустить приложение
    # app.run()  или другой запуск
```

### Ручная синхронизация

```python
from src.integrations import GoogleDriveSync

# Синхронизировать все данные
sync = GoogleDriveSync()
sync.sync_all_data()

# Или синхронизировать только данные
sync.sync_directory("data", sync.root_folder_id)

# Или загрузить один файл
sync.upload_file("config.json", sync.root_folder_id)
```

---

## 🔧 Конфигурация

Отредактируйте `sync_config.json` для:
- Изменения интервала синхронизации
- Отключения отдельных компонентов
- Исключения определённых файлов

Пример - синхронизировать каждый час вместо 6 часов:
```json
{
  "sync_interval_hours": 1
}
```

---

## 🚨 Важные моменты

### ⚠️ Безопасность JSON ключа

- ✅ **ДА**: Скопируйте в `src/secrets/google_sa_account_service_account.json`
- ❌ **НЕ КОММИТЬТЕ** в git (`.gitignore` уже это содержит)
- ❌ **НЕ ДЕЛИТЕСЬ** с кем-либо
- ✅ **ПЕРИОДИЧЕСКИ** ротируйте ключи

### 🔗 Папка на Google Drive

После инициализации будет создана папка:
```
📁 AI-Breadboard-Sync/
   ├── data/
   ├── logs/
   ├── secrets/
   └── configs/
```

URL к папке:
```
https://drive.google.com/drive/folders/[FOLDER_ID]
```

### 📊 Мониторинг

Проверяйте статус синхронизации:
```powershell
.\sync.ps1 status
```

Это покажет:
- Когда произошла последняя синхронизация
- Когда будет следующая
- ID папки на Google Drive

---

## 🐛 Решение проблем

### "Файл не найден" при инициализации

**Решение**: Убедитесь, что JSON ключ находится в:
```
src/secrets/google_sa_account_service_account.json
```

### "Нет доступа к Google Drive"

**Решение**:
1. Проверьте, что Google Drive API активирована
2. Проверьте, что JSON ключ корректный
3. Убедитесь, что интернет соединение активно

### Медленная синхронизация

**Это нормально** для больших объёмов данных. Google Drive API имеет ограничения на скорость.

**Решение**: Используйте режим ручной синхронизации для больших файлов или разделите на несколько операций.

### Синхронизация не запускается

**Решение**:
1. Проверьте логи: `sync_setup.log`
2. Запустите инициализацию заново: `.\sync.ps1 init`
3. Проверьте конфигурацию: `sync_config.json`

---

## 💡 Советы и трюки

### Синхронизировать только определённую папку

```python
from src.integrations import GoogleDriveSync

sync = GoogleDriveSync()
sync.ensure_sync_folder()
sync.sync_directory("data/rag_index", sync.root_folder_id)
```

### Синхронизировать только один файл

```python
from src.integrations import ManualSyncHandler

handler = ManualSyncHandler()
handler.sync_single_file("config.json", "configs")
```

### Получить статус синхронизации

```python
from src.integrations import get_scheduler

scheduler = get_scheduler()
status = scheduler.get_status()
print(f"Последняя синхронизация: {status['last_sync_time']}")
print(f"Следующая синхронизация: {status['next_sync_time']}")
```

### Остановить автоматическую синхронизацию

```powershell
# Найти процесс Python и остановить его
# Или в коде:
from src.integrations import stop_sync_scheduler
stop_sync_scheduler()
```

---

## 📞 Получение помощи

### Документация

| Документ | Содержит |
|----------|----------|
| README_SYNC.md | Краткое описание и команды |
| GOOGLE_DRIVE_SYNC_SETUP.md | Пошаговая инструкция (5 минут) |
| GOOGLE_SETUP_INSTRUCTIONS.md | Как создать Google Service Account |
| docs/GOOGLE_DRIVE_SYNC_GUIDE.md | Полное руководство со всеми возможностями |
| SYNC_IMPLEMENTATION_SUMMARY.md | Технический отчёт |

### Логирование

- `sync_setup.log` - Логи инициализации
- `sync_state.json` - Состояние синхронизации
- Системное логирование приложения

### Проверка подключения

```powershell
# Проверить, работает ли Google Drive API
.\sync.ps1 status

# Или через Python
python -c "from src.integrations import GoogleDriveSync; sync = GoogleDriveSync(); print(sync.drive_service is not None)"
```

---

## ✅ Чек-лист для запуска

- [ ] Прочитал GOOGLE_SETUP_INSTRUCTIONS.md
- [ ] Создал Google Service Account
- [ ] Скачал JSON ключ
- [ ] Скопировал JSON в `src/secrets/google_sa_account_service_account.json`
- [ ] Установил зависимости: `pip install -r req/sync_requirements.txt`
- [ ] Инициализировал: `.\sync.ps1 init`
- [ ] Синхронизировал: `.\sync.ps1 sync`
- [ ] Проверил статус: `.\sync.ps1 status`
- [ ] (Опционально) Запустил автоматический режим: `.\sync.ps1 start`

---

## 🎯 Типичная рабочая процесс

### День 1: Установка (15 минут)
1. Подготовить Google Account
2. Установить зависимости
3. Инициализировать синхронизацию

### День 2+: Использование
1. Данные автоматически синхронизируются каждые 6 часов
2. Можно проверить статус: `.\sync.ps1 status`
3. Можно выполнить ручную синхронизацию: `.\sync.ps1 sync`

### Обслуживание (раз в месяц)
1. Проверить размер папки на Google Drive
2. Проверить логи синхронизации
3. При необходимости ротировать Google ключ

---

## 🚀 Готово!

Вы готовы использовать Google Drive Sync. Начните с документации в зависимости от вашей роли и следуйте инструкциям.

**Первый шаг**: Откройте [GOOGLE_SETUP_INSTRUCTIONS.md](GOOGLE_SETUP_INSTRUCTIONS.md) 📖
