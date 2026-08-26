# MCP Серверы проекта ai-assistant (`.mcp/`)

В данной директории расположены локальные **MCP-серверы** (Model Context Protocol), построенные на базе библиотеки `FastMCP` (`mcp.server.fastmcp`) и Node.js. Они позволяют внешним агентам и LLM-клиентам (Claude Desktop, Cursor, Antigravity, VS Code и локальным скриптам) стандартизированно взаимодействовать с сервисами ai-assistant.

---

## 📋 Список серверов

| Сервер | Файл | Описание | Основные инструменты (Tools) |
|---|---|---|---|
| **LangChain Breadboard Agent** | [`langchain_mcp_server.py`](file:///c:/ai-assistant/.mcp/langchain_mcp_server.py) | Автономный ReAct-агент (веб-поиск, RAG, вычисления Python) | `agent_query`, `agent_web_search`, `agent_rag_search`, `agent_python_eval` |
| **Gemini Search Grounding** | [`gemini_search_mcp_server.py`](file:///c:/ai-assistant/.mcp/gemini_search_mcp_server.py) | Прямой поиск Google с Grounding и автоматической ротацией пула API-ключей | `gemini_web_search`, `gemini_key_pool_status` |
| **Gemini CLI Search** | [`gemini_cli_search_mcp_server.py`](file:///c:/ai-assistant/.mcp/gemini_cli_search_mcp_server.py) | Поиск через локальный терминальный агент Google Gemini CLI | `gemini_cli_web_search` |
| **Antigravity Search** | [`agy_search_mcp_server.py`](file:///c:/ai-assistant/.mcp/agy_search_mcp_server.py) | Агентный веб-поиск через встроенные инструменты Google Antigravity | `agy_web_search` |
| **FastAPI Client** | [`fastapi_mcp_server.py`](file:///c:/ai-assistant/.mcp/fastapi_mcp_server.py) | Интеграция с локальным FastAPI бэкендом | `fastapi_chat`, `fastapi_media_list` |
| **Unicorn Manager** | [`unicorn_mcp_server.py`](file:///c:/ai-assistant/.mcp/unicorn_mcp_server.py) | Управление процессами Uvicorn / Unicorn | `unicorn_start`, `unicorn_stop`, `unicorn_status` |
| **Auto-Commits Helper** | [`auto_commits.py`](file:///c:/ai-assistant/.mcp/auto_commits.py) | Автоматическое версионирование и коммиты при изменениях | Фоновый наблюдатель изменений файлов |
| **Playwright MCP** | [`playwright/`](file:///c:/ai-assistant/.mcp/playwright) | Node/Express оркестратор для прямого взаимодействия с браузером | Эндпоинты `POST /precommit`, `POST /apply` |

---

## 🚀 Запуск серверов

### 1. Gemini Search Grounding MCP Server (Python / FastMCP)
```bash
python .mcp/gemini_search_mcp_server.py
```

### 2. Antigravity Search MCP Server (Python / FastMCP)
```bash
python .mcp/agy_search_mcp_server.py
```

### 3. LangChain Breadboard MCP Server (Python / FastMCP)
```bash
python .mcp/langchain_mcp_server.py
```

### 4. FastAPI Client MCP Server (Python / FastMCP)
```bash
python .mcp/fastapi_mcp_server.py
```

### 5. Unicorn Manager MCP Server (Python / FastMCP)
```bash
python .mcp/unicorn_mcp_server.py
```

---

## ⚙️ Подключение к MCP-клиентам (например, Claude Desktop / Cursor)

В файл конфигурации `claude_desktop_config.json` или `cursor-mcp.json`:

```json
{
  "mcpServers": {
    "ai-assistant-gemini-search": {
      "command": "C:\\ai-assistant\\venv\\Scripts\\python.exe",
      "args": ["C:\\ai-assistant\\.mcp\\gemini_search_mcp_server.py"]
    },
    "ai-assistant-agy-search": {
      "command": "C:\\ai-assistant\\venv\\Scripts\\python.exe",
      "args": ["C:\\ai-assistant\\.mcp\\agy_search_mcp_server.py"]
    },
    "ai-assistant-langchain": {
      "command": "C:\\ai-assistant\\venv\\Scripts\\python.exe",
      "args": ["C:\\ai-assistant\\.mcp\\langchain_mcp_server.py"]
    },
    "ai-assistant-fastapi": {
      "command": "C:\\ai-assistant\\venv\\Scripts\\python.exe",
      "args": ["C:\\ai-assistant\\.mcp\\fastapi_mcp_server.py"]
    },
    "ai-assistant-unicorn": {
      "command": "C:\\ai-assistant\\venv\\Scripts\\python.exe",
      "args": ["C:\\ai-assistant\\.mcp\\unicorn_mcp_server.py"]
    }
  }
}
```

---

## 🛡️ Стандарты разработки MCP-серверов
1. Все Python MCP-серверы используют единый стандартный стек: `from mcp.server.fastmcp import FastMCP`.
2. Логирование выполняется строго через `from core.logger import logger`.
3. Конфигурация считывается из `config.json` в корне проекта.
4. Отсутствие прямого использования `None` / `is None` в соответствии с `GEMINI.md`.
5. Все публичные инструменты оформлены через декоратор `@mcp.tool()` с явными тайпхинтами и docstring на русском языке.
