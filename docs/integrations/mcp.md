# MCP интеграция

## Что такое MCP?

MCP (Model Context Protocol) — это протокол для интеграции моделей AI с внешними инструментами.

## Доступные серверы

### 1. fastapi_mcp_server.py

FastAPI интеграция для MCP.

**Команды:**
- `get_docs` — получение документации
- `run_test` — запуск тестов
- `get_status` — статус сервера

### 2. unicorn_mcp_server.py

Uvicorn интеграция для MCP.

**Команды:**
- `restart_server` — перезапуск сервера
- `get_logs` — получение логов
- `get_stats` — статистика сервера

## Настройка MCP

### 1. Установка uvx

```bash
pip install uv
```

### 2. Настройка mcp.json

```json
{
  "mcpServers": {
    "fastapi": {
      "command": "uvx",
      "args": ["fastapi_mcp_server.py"],
      "env": {
        "LOG_LEVEL": "INFO"
      }
    },
    "unicorn": {
      "command": "uvx",
      "args": ["unicorn_mcp_server.py"],
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

## Использование MCP

### 1. Подключение к MCP серверу

```python
from mcp import Client, create_client

client = create_client("fastapi")

# Вызов команды
result = await client.call("get_status")
print(result)
```

### 2. MCP инструменты

| Инструмент | Описание |
|------------|----------|
| `fastapi_docs` | Получение FastAPI документации |
| `fastapi_test` | Запуск тестов |
| `unicorn_restart` | Перезапуск сервера |
| `unicorn_logs` | Получение логов |

---

[← Меню](../index.md) | [Gemini →](gemini.md)