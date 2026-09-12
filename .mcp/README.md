# Model Context Protocol (MCP) Servers (`.mcp/`)

## Purpose
Hosts local **MCP Servers** built using `FastMCP` (`mcp.server.fastmcp`) and Node.js. These servers expose standardized tools and resources to external AI clients (Antigravity, Claude Desktop, Cursor, VS Code, and automated agents).

All servers are **кроссплатформенные** (cross-platform) и работают на Windows, Linux и macOS.

---

## Registered MCP Servers

| Server | Entry Point | Primary Tools | Platform Support |
|---|---|---|---|
| **LangChain Breadboard Agent** | `langchain_mcp_server.py` | `agent_query`, `agent_web_search`, `agent_rag_search`, `agent_python_eval` | ✅ Win/Linux/macOS |
| **Gemini Search Grounding** | `gemini_search_mcp_server.py` | `gemini_web_search`, `gemini_key_pool_status` | ✅ Win/Linux/macOS |
| **Gemini CLI Search** | `gemini_cli_search_mcp_server.py` | `gemini_cli_web_search` | ✅ Win/Linux/macOS |
| **Antigravity Search** | `agy_search_mcp_server.py` | `agy_web_search` | ✅ Win/Linux/macOS |
| **FastAPI Client** | `fastapi_mcp_server.py` | `fastapi_chat`, `fastapi_media_list` | ✅ Win/Linux/macOS |
| **Unicorn Manager** | `unicorn_mcp_server.py` | `unicorn_start`, `unicorn_stop`, `unicorn_status` | ✅ Win/Linux/macOS |
| **Auto-Commits Helper** | `auto_commits.py` | Background watcher | ✅ Win/Linux/macOS |
| **Playwright MCP** | `playwright/` | `POST /precommit`, `POST /apply` | ✅ Win/Linux/macOS |

---

## Running MCP Servers

### Python MCP Servers (кроссплатформенные)

```bash
# Linux/macOS
python3 .mcp/gemini_search_mcp_server.py
python3 .mcp/langchain_mcp_server.py
python3 .mcp/fastapi_mcp_server.py

# Windows (cmd или PowerShell)
python .mcp\gemini_search_mcp_server.py
python .mcp\langchain_mcp_server.py
python .mcp\fastapi_mcp_server.py
```

### Node.js MCP Server

```bash
# Playwright MCP
cd .mcp/playwright
npm install
npm start
```

---

## MCP Client Configuration

Example for different clients:

### Claude Desktop (`claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "aibreadboard-gemini-search": {
      "command": "python3",
      "args": ["/path/to/AI-Breadboard/.mcp/gemini_search_mcp_server.py"],
      "cwd": "/path/to/AI-Breadboard"
    },
    "aibreadboard-langchain": {
      "command": "python3",
      "args": ["/path/to/AI-Breadboard/.mcp/langchain_mcp_server.py"],
      "cwd": "/path/to/AI-Breadboard"
    }
  }
}
```

### VS Code Cursor (`cursor-mcp.json` или `.cursor/config`)

```json
{
  "mcpServers": {
    "aibreadboard": {
      "command": "python3",
      "args": ["/path/to/AI-Breadboard/.mcp/langchain_mcp_server.py"],
      "environment": {
        "AIBREADBOARD_DIR": "/path/to/AI-Breadboard",
        "PYTHONPATH": "/path/to/AI-Breadboard"
      }
    }
  }
}
```

---

## Кроссплатформенные особенности

### 1. Управление путями

Все MCP серверы используют `pathlib.Path` для кроссплатформенной работы:

```python
from pathlib import Path

# Вместо Windows-специфичного пути
# config_path = "C:\\Users\\user\\config.json"

# Используйте (работает везде):
config_path = Path(__file__).parent.parent / "config.json"
```

### 2. Вспомогательный Module `config_helper.py`

Для упрощения работы с конфигурацией используйте встроенный `config_helper`:

```python
from .config_helper import (
    get_project_root,
    load_config,
    get_config_value,
    get_server_url,
    get_env_var,
    get_certs_dir,
    get_data_dir,
    is_port_open,
)

# Кроссплатформенно получить URL сервера
server_url = get_server_url()  # Автоматически: http://localhost:8000

# Получить конфиг значение
port = get_config_value("server.port", 8000)

# Получить директорию SSL сертификатов
certs_dir = get_certs_dir()  # ~/.certs (Windows), ~/Library/Certs (macOS), ~/.local/share/ca-certificates (Linux)
```

### 3. Переменные окружения

Все MCP серверы должны использовать переменные окружения для конфигурации:

```python
import os

# Получить путь проекта из переменной окружения
project_dir = os.environ.get("AIBREADBOARD_DIR", ".")

# Использовать PYTHONPATH
python_path = os.environ.get("PYTHONPATH", "")
```

### 4. Управление процессами

При запуске внешних процессов используйте `subprocess` вместо Windows-специфичных команд:

```python
import subprocess
import sys

# ❌ Неправильно (только Windows)
# os.system("taskkill /PID 1234")

# ✅ Правильно (кроссплатформенно)
import signal
os.kill(pid, signal.SIGTERM)  # Linux/macOS
# или
subprocess.run(["kill", pid])  # Unix
```

---

## Engineering Standards for MCP Servers

1. **All Python MCP servers use `from mcp.server.fastmcp import FastMCP`.**
   - Стандартизированная реализация для кроссплатформенности

2. **Logging через `from core.logger import logger`.**
   - Единообразное логирование на всех платформах

3. **Configuration parameters read from root `config.json` via `config_helper.py`.**
   - Кроссплатформенная работа с конфигурацией

4. **Tools registered with `@mcp.tool()` decorator with explicit type annotations and docstrings.**
   - Стандартный формат для всех MCP инструментов

5. **Path handling using `pathlib.Path` only.**
   - Не использовать строковые конкатенации путей

6. **Process management via `subprocess` module.**
   - Кроссплатформенная работа с процессами

7. **Environment variables for sensitive data.**
   - Configuration через `.env` и переменные окружения

---

## Examples использования config_helper

### Пример 1: Получить URL сервера

```python
from .config_helper import get_server_url

base_url = get_server_url()
# Результат: http://localhost:8000 или https://localhost:8000 (если SSL включен)
```

### Пример 2: Кроссплатформенные пути

```python
from .config_helper import get_certs_dir, get_data_dir

certs = get_certs_dir()
# Windows: C:\Users\user\.certs
# Linux: /home/user/.local/share/ca-certificates
# macOS: /Users/user/Library/Certs

data = get_data_dir()
# Windows: C:\Users\user\AppData\Local\AI-Breadboard
# Linux: /home/user/.local/share/AI-Breadboard
# macOS: /Users/user/Library/Application Support/AI-Breadboard
```

### Пример 3: Работа с .env

```python
from .config_helper import get_env_var

api_key = get_env_var("GEMINI_API_KEY")
# Ищет в: 1) переменные окружения, 2) .env файл, 3) None
```

---

## Миграция на кроссплатформенность

Если вы пишете новый MCP сервер:

**Старое (Windows-специфичное):**
```python
config_path = r"C:\Users\user\AI-Breadboard\config.json"
if os.name == "nt":
    import subprocess
    subprocess.run(["taskkill", "/F", "/PID", str(pid)])
```

**Новое (кроссплатформенное):**
```python
from pathlib import Path
from .config_helper import get_project_root, load_config

config_path = get_project_root() / "config.json"
config = load_config()

import os
os.kill(pid, 9)  # Работает везде
```

---

## Тестирование на разных платформах

```bash
# Linux
python3 .mcp/gemini_search_mcp_server.py

# macOS
python3 .mcp/gemini_search_mcp_server.py

# Windows (cmd)
python .mcp\gemini_search_mcp_server.py

# Windows (PowerShell)
python .mcp/gemini_search_mcp_server.py  # Путем слэши тоже работают
```

Все серверы должны работать без изменений на любой платформе.
