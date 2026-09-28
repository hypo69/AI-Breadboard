# Google User Desktop Workspace (`apps/google_user_desktop`)

Автономное приложение для подсистемы **AI Breadboard**, объединяющее интеграцию с **Google Mail (Gmail)**, **Google Calendar**, **Google Docs/Sheets** и **Google Drive** в единый консольный и REST API интерфейс.

---

## 📋 Возможности приложения

1. **Единый узел интеграции Google Workspace**:
   - Агрегирование данных из нескольких аккаунтов Google OAuth2 / Service Account.
   - Поддержка выбора активного аккаунта из пула `google_accounts_state`.
2. **Google Mail (Gmail)**:
   - Просмотр недавних входящих сообщений (список, отправитель, тема, дата, короткое описание).
3. **Google Calendar**:
   - Мониторинг ближайших предстоящих событий из основного календаря.
4. **Google Docs & Sheets**:
   - Список недавних текстовых документов и электронных таблиц с прямыми веб-ссылками.
   - Чтение содержимого конкретного документа через API.
5. **Google Drive**:
   - Обзор файлов пользователя на Google Диске (размеры, MIME-типы, время модификации).
6. **Интерфейсы**:
   - **CLI**: Поддержка быстрой выдачи статуса, сообщений, событий и списков документов/файлов в текстовом и JSON форматах.
   - **REST API (FastAPI)**: Полный набор HTTP эндпоинтов с префиксом `/api/google-desktop`.
   - **TUI (Rich)**: Интерактивный консольный дашборд для наглядного мониторинга состояния в реальном времени.

---

## 📁 Структура приложения

```
apps/google_user_desktop/
├── README.md           # Документация приложения на русском языке
├── __init__.py         # Фасадный импорт пакета
├── __main__.py         # Точка входа CLI командной строки
├── config.json         # Настройки сервера и лимиты элементов
├── routers/
│   ├── __init__.py
│   └── router.py       # FastAPI роутер /api/google-desktop
├── src/
│   ├── __init__.py
│   └── state.py        # Класс GoogleUserDesktopState и модели данных
└── tui.py              # Консольный интерфейс дашборда на Rich
```

---

## 🚀 Варианты запуска

### 1. CLI команды
```powershell
# Получить быстрый статус и количество ресурсов
py -m apps.google_user_desktop --status

# Получить статус в формате JSON
py -m apps.google_user_desktop --status --json

# Просмотреть входящие письма Gmail
py -m apps.google_user_desktop --mail --limit 10

# Просмотреть события Календаря
py -m apps.google_user_desktop --calendar

# Просмотреть документы Docs
py -m apps.google_user_desktop --docs

# Просмотреть файлы на Диске
py -m apps.google_user_desktop --drive
```

### 2. Standalone FastAPI сервер
```powershell
py -m apps.google_user_desktop --mode server --port 8106
```
Документация Swagger будет доступна по адресу: `http://localhost:8106/docs`.

### 3. Интерактивный консольный дашборд (TUI)
```powershell
py -m apps.google_user_desktop --mode dashboard
```

---

## 🌐 API Эндпоинты

- `GET /api/google-desktop/status`: Общий статус подключения аккаунта и количество ресурсов.
- `GET /api/google-desktop/accounts`: Список доступных аккаунтов Google в пуле.
- `POST /api/google-desktop/accounts/select`: Выбор активного аккаунта.
- `GET /api/google-desktop/mail/messages`: Получение входящих писем Gmail.
- `GET /api/google-desktop/calendar/events`: Получение событий Календаря.
- `GET /api/google-desktop/docs/list`: Получение списка Документов и Таблиц.
- `GET /api/google-desktop/docs/{document_id}`: Просмотр содержимого конкретного документа.
- `GET /api/google-desktop/drive/files`: Получение списка файлов с Google Диска.
- `POST /api/google-desktop/sync`: Принудительная синхронизация данных всех 4-х сервисов.
