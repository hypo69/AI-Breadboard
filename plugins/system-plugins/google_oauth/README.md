# Router Google OAuth (Google Accounts)

Этот плагин **google_oauth** теперь содержит роутер `router_google_accounts.py`.

## Что делает роутер
- Предоставляет набор REST‑эндпоинтов `/api/google/accounts` для управления несколькими аккаунтами Google.
- Поддерживает CRUD‑операции (создание, чтение, обновление, удаление) аккаунтов OAuth2 и сервис‑аккаунтов.
- Позволяет задавать аккаунт по умолчанию, сбрасывать статус и проверять подключение.

## Основные эндпоинты
| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/api/google/accounts` | Список всех аккаунтов. |
| `POST` | `/api/google/accounts` | Создать новый аккаунт (OAuth2 либо Service Account). |
| `POST` | `/api/google/accounts/{name}/upload` | Загрузить файл с учётными данными сервис‑аккаунта. |
| `POST` | `/api/google/accounts/{name}/default` | Сделать аккаунт активным по умолчанию. |
| `POST` | `/api/google/accounts/{name}/reset-status` | Сбросить статус (например, «exhausted» → «active»). |
| `POST` | `/api/google/accounts/{name}/test` | Проверить возможность подключения к Google API. |
| `DELETE` | `/api/google/accounts/{name}` | Удалить аккаунт. |

## Как подключить
В `plugin.py` роутер импортируется и регистрируется в FastAPI:
```python
from plugins.system_plugins.google_oauth.routers.router_google_accounts import router
app.include_router(router)
```

---
*Все комментарии и документация написаны на русском языке в соответствии с `GEMINI.md`.*
