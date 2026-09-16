---
name: storage-controller
description: Storage and drive management. Use for scanning drives, retrieving list of connected storages, and updating CONNECTED_DRIVES environment configuration.
description_i18n:
  en: Storage and drive management. Use for scanning drives, retrieving list of connected storages, and updating CONNECTED_DRIVES environment configuration.
  ru: Управление подключенными хранилищами (дисками). Используйте для сканирования дисков, получения списка подключенных хранилищ и обновления переменной окружения CONNECTED_DRIVES.
---

# Storage Controller

Этот навык предоставляет инструменты для управления состоянием подключенных дисков.

## Рабочие процессы

### 1. Сканирование дисков
Если нужно обновить list доступных дисков:
`python -m plugins.media_organizer.core.drive_scanner`

### 2. Получение текущих дисков
Для получения строки с дисками в формате `S:\,N:\`:
`python -c "import os; print(os.environ.get('CONNECTED_DRIVES', ''))"`

### 3. Integration
Этот навык используется при запуске серверов (run.ps1, Run-LightServer.ps1) и доступен через FastAPI эндпоинт `/api/control/rescan`.
