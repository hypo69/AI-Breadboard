# Плагин Telegram Channel RAG & Fast Search (telegram_channel_rag)

## Назначение
Модульный плагин для сбора сообщений из каналов Telegram, построения векторного индекса RAG и быстрого поиска с возвратом прямых ссылок на сообщения.

## Структура
- `plugins/developer-plugins/telegram_channel_rag/`
  - `data/telegram_rag`: Хранилище индекса

## Запуск
```powershell
# Примеры через административные действия
```

## API
- `fetch_and_index`: Скрапинг и индексация сообщений.
- `search`: Семантический поиск.
- `get_index_status`: Статус индекса.
