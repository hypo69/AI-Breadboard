# Router Sync (Google Drive Sync)

Плагин **gdrive_sync** теперь содержит роутер `router_sync.py`.

## Что делает роутер
- Обеспечивает синхронизацию файлов между локальной файловой системой и Google Drive.
- Предоставляет набор REST‑эндпоинтов `/api/gdrive/sync` для запуска, контроля и мониторинга синхронизации.
- Поддерживает операции:
  - `POST /api/gdrive/sync/start` – начать процесс синхронизации.
  - `GET /api/gdrive/sync/status` – получить текущий статус (время последнего запуска, количество обработанных файлов, ошибки).
  - `POST /api/gdrive/sync/stop` – принудительно остановить процесс.
  - `GET /api/gdrive/sync/logs` – получить логи последней синхронизации.

## Как подключить
В `plugin.py` роутер импортируется и регистрируется в FastAPI:
```python
from plugins.system_plugins.gdrive_sync.routers.router_sync import router
app.include_router(router)
```

---
*Вся документация написана на русском языке в соответствии с `GEMINI.md`.*
