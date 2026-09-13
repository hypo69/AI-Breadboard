
# Google Drive Sync Admin Panel Integration

## 📋 Описание

Добавлена новая вкладка "Google Drive Synchronization" в администраторскую панель для управления синхронизацией данных на Google Drive прямо из веб-интерфейса.

## 🎯 Компоненты интеграции

### REST API

- **Модуль**: `src/fastapi/router_sync.py`
- **Эндпоинты**:
  - `GET /api/admin/sync/status` - Статус синхронизации
  - `GET /api/admin/sync/stats` - Статистика хранилища
  - `GET /api/admin/sync/drive-info` - Информация о Google Drive папке
  - `GET /api/admin/sync/config` - Текущая конфигурация
  - `POST /api/admin/sync/start` - Запустить планировщик
  - `POST /api/admin/sync/stop` - Остановить планировщик
  - `POST /api/admin/sync/sync-now` - Выполнить синхронизацию
  - `POST /api/admin/sync/test-connection` - Проверить подключение
  - `POST /api/admin/sync/config` - Обновить конфигурацию

### Фронтенд компоненты

- **HTML**: `src/fastapi/webinterface/admin/sync.html` - Полная вкладка (standalone)
- **JavaScript**: `src/fastapi/webinterface/admin/sync-tab.js` - JS класс для интеграции
- **Интеграция в main.py**: Автоматически подключается через `include_router`

## 🚀 Использование

### Доступ к админ-панели

1. Перейти на `http://localhost:8000/admin` (или ваш хост)
2. Войти с парольом ADMIN_PASSWORD
3. Найти новую вкладку "Google Drive Synchronization" (☁️ иконка)

### Управление синхронизацией через админ-панель

#### 📊 Статус синхронизации

- Текущий статус планировщика (Running/Inactive)
- Время последней синхронизации
- Время следующей синхронизации
- Интервал синхронизации
- Прямая ссылка на Google Drive папку

#### 💾 Статистика хранилища

- Общий размер синхронизированных данных
- Количество файлов
- Количество папок
- Количество ошибок

#### 🎮 Управление

- **Запустить/остановить планировщик** - Автоматическая синхронизация
- **Синхронизировать сейчас** - Выбрать тип данных для синхронизации:
  - All Data - все (данные, логи, конфиги, секреты)
  - Data Only - базы данных и RAG индексы
  - Logs Only - логи приложения
  - Secrets Only - конфиги и ключи
  - Configs Only - конфиг файлы
- **Проверить подключение** - Тест соединения с Google Drive
- **Изменить интервал** - Настроить интервал между синхронизациями (1-24 часов)

#### 📋 Лог активности

- История недавних операций синхронизации
- Временные метки операций

## 🔧 Интеграция в существующую админ-панель

### Вариант 1: Добавить вкладку в index.html

Если вы хотите интегрировать вкладку в существующий index.html:

1. Добавить вкладку в меню:

```html
<button class="dropdown-item d-flex align-items-center gap-2" 
        data-tab="tab-sync" 
        data-bs-target="#tab-sync" 
        type="button">
  ☁️ Google Drive Sync
</button>
```

2. Добавить контейнер вкладки:

```html
<div class="tab-pane fade" id="tab-sync" role="tabpanel">
  <!-- Содержимое загружается JS -->
</div>
```

3. Подключить JS модуль:

```html
<script src="/admin/sync-tab.js"></script>
```

### Вариант 2: Использовать как отдельный компонент

Вкладка уже полностью функциональна как самостоятельный компонент:

```html
<!-- Загрузить HTML компонент в iframe -->
<iframe src="/admin/sync.html" width="100%" height="100%"></iframe>
```

## 📖 API Примеры

### Получить статус синхронизации

```bash
curl http://localhost:8000/api/admin/sync/status
```

Ответ:

```json
{
  "is_running": true,
  "last_sync_time": "2026-09-12T15:30:00",
  "next_sync_time": "2026-09-12T21:30:00",
  "sync_interval_hours": 6,
  "root_folder_id": "1AbC2dEf3gH4iJk5lMnOpQrStUvWxYz",
  "sync_enabled": true
}
```

### Запустить синхронизацию

```bash
curl -X POST http://localhost:8000/api/admin/sync/sync-now \
  -H "Content-Type: application/json" \
  -d '{"sync_type": "all"}'
```

Ответ:

```json
{
  "status": "syncing",
  "message": "Synchronization of all started in background"
}
```

### Получить статистику

```bash
curl http://localhost:8000/api/admin/sync/stats
```

Ответ:

```json
{
  "total_size_mb": 254.32,
  "files_count": 1842,
  "folders_count": 45,
  "last_24h_syncs": 4,
  "sync_errors": 0
}
```

## 🔐 Аутентификация

Все эндпоинты защищены проверкой администратора через cookie `admin_password_verified`.

Для локального доступа (127.0.0.1, localhost) проверка может быть упрощена в соответствии с конфигурацией приложения.

## ⚙️ Конфигурация

Конфигурация хранится в `sync_config.json`:

```json
{
  "service_account_file": "src/secrets/google_sa_account_service_account.json",
  "sync_interval_hours": 6,
  "include_data": true,
  "include_logs": true,
  "include_secrets": true,
  "include_configs": true
}
```

Изменения конфигурации через API сохраняются автоматически.

## 📊 Обновления в реальном времени

Админ-панель автоматически обновляет:

- Статус синхронизации каждые 5 секунд
- Статистику хранилища каждые 30 секунд
- Логи активности в реальном времени

## 🐛 Решение проблем

### Ошибка подключения к Google Drive

1. Проверьте, что `sync_config.json` существует и содержит путь к service account
2. Убедитесь, что JSON ключ находится в `src/secrets/google_sa_account_service_account.json`
3. Проверьте логи приложения на ошибки при инициализации

### API возвращает 503

Google Drive синхронизация не настроена. Убедитесь:

- Установлены зависимости: `pip install -r req/sync_requirements.txt`
- Подготовлен Google Service Account
- Запущено приложение с синхром-модулями

### Синхронизация не начинается

1. Проверьте статус планировщика в админ-панели
2. Убедитесь, что интернет соединение активно
3. Посмотрите в `sync_setup.log` на предмет ошибок
4. Проверьте права доступа на папке на Google Drive

## 📝 Структура компонентов

```text
src/fastapi/
├── router_sync.py              # REST API эндпоинты
└── webinterface/admin/
    ├── sync.html               # Полная вкладка (standalone)
    └── sync-tab.js             # JS класс для интеграции

main.py                         # Включение роутера
src/fastapi/__init__.py         # Экспорт init_sync_router
```

## 🔄 Интеграция с основным приложением

Роутер автоматически включен в основное приложение:

```python
from src.fastapi import init_sync_router
app.include_router(init_sync_router())
```

Синхронизация доступна по адресам:

- REST API: `/api/admin/sync/*`
- Веб-интерфейс: `/admin` (вкладка "Google Drive Synchronization")

## 💡 Примеры использования

### Программное управление синхронизацией

```python
from src.fastapi.router_sync import GoogleDriveSync, get_scheduler

# Инициализировать синхронизацию
sync = GoogleDriveSync()
sync.sync_all_data()

# Запустить автоматический планировщик
scheduler = get_scheduler()
scheduler.start()
```

### Создание кастомных эндпоинтов

```python
from fastapi import APIRouter
from src.integrations import GoogleDriveSync

custom_router = APIRouter()

@custom_router.post("/api/custom/backup")
async def create_backup():
    sync = GoogleDriveSync()
    results = sync.sync_all_data()
    return {"status": "backed up", "results": results}
```

## 📚 Дополнительные ресурсы

- [Полное руководство по синхронизации](GOOGLE_DRIVE_SYNC_GUIDE.md)
- [Быстрая настройка](GOOGLE_DRIVE_SYNC_SETUP.md)
- [Результаты тестирования](TEST_RESULTS.md)
- [REST API документация](docs/GOOGLE_DRIVE_SYNC_GUIDE.md)

## ✅ Чек-лист

- ✅ REST API эндпоинты реализованы
- ✅ Веб-интерфейс вкладки создана
- ✅ Интеграция с main.py выполнена
- ✅ Аутентификация настроена
- ✅ Auto-refresh реализован
- ✅ Обработка ошибок добавлена
- ✅ Документация полная

## 🎉 Готово

Администраторская вкладка для управления Google Drive синхронизацией полностью готова к использованию!
