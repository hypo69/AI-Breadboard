# Google User Desktop Web Tab (`google_desktop_tab`)

Интерактивный веб-интерфейс для приложения **Google User Desktop** (`apps/google_user_desktop`) в экосистеме **AI Breadboard**.

---

## 📋 Описание модуля

Данный модуль предоставляет встроенную вкладку для веб-интерфейса (`src/api/webgui`), позволяющую в реальном времени взаимодействовать со всеми 4 интегрированными сервисами **Google Workspace**:

1. **Gmail**: Мониторинг свежих входящих сообщений.
2. **Google Calendar**: Просмотр предстоящих событий с возможностью перехода в оригинальный календарь.
3. **Google Docs & Sheets**: Список текстовых документов и электронных таблиц с интерактивным модальным просмотром текста.
4. **Google Drive**: Обзор файлов пользователя с информацией о типах MIME и размерах.
5. **Управление аккаунтами**: Быстрое переключение активной учетной записи из пула авторизованных аккаунтов.

---

## 📁 Структура модуля

```
src/api/webgui/google_desktop_tab/
├── README.md      # Документация модуля на русском языке
├── index.html     # HTML-шаблон вкладки с адаптивными карточками и модальным окном
└── main.js        # JavaScript контроллер и клиент API (/api/google-desktop/*)
```

---

## 🌐 Используемые REST API Эндпоинты

- `GET /api/google-desktop/status` — Получение агрегированного статуса ресурсов.
- `GET /api/google-desktop/accounts` — Загрузка списка доступных и активного Google аккаунтов.
- `POST /api/google-desktop/accounts/select?account_name=...` — Переключение активного аккаунта.
- `GET /api/google-desktop/mail/messages?limit=20` — Получение писем Gmail.
- `GET /api/google-desktop/calendar/events?limit=20` — Получение событий Календаря.
- `GET /api/google-desktop/docs/list?limit=20` — Загрузка списка Документов и Таблиц.
- `GET /api/google-desktop/docs/{document_id}` — Чтение содержимого документа.
- `GET /api/google-desktop/drive/files?limit=20` — Список файлов с Google Диска.
- `POST /api/google-desktop/sync` — Фоновое принудительное обновление данных.

---

## 🚀 Интеграция в меню WebGUI

Вкладка зарегистрирована в реестре приложения `/apps`:
- `id`: `google_user_desktop`
- `tabId`: `tab-google-desktop`
- `html`: `/html/google_desktop_tab/index.html`
- `js`: `/html/google_desktop_tab/main.js`
