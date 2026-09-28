# Router User Storage

Этот плагин **user_storage** теперь содержит роутер `router_user_storage.py`.

## Что делает роутер
- Управляет пользовательским хранилищем файлов и каталогов.
- Предоставляет API `/api/user/storage` для загрузки, скачивания, удаления и листинга файлов.
- Обеспечивает проверки прав доступа и ограничения на размер файлов.

## Основные эндпоинты
| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/api/user/storage` | Список файлов/каталогов пользователя. |
| `POST` | `/api/user/storage/upload` | Загрузка нового файла. |
| `GET` | `/api/user/storage/{path}` | Скачать файл по указанному пути. |
| `DELETE` | `/api/user/storage/{path}` | Удалить файл/каталог. |

## Как подключить
В `plugin.py` роутер импортируется и регистрируется в FastAPI:
```python
from plugins.user_plugins.user_storage.routers.router_user_storage import router
app.include_router(router)
```

---
*Документация написана на русском языке согласно `GEMINI.md`.*
