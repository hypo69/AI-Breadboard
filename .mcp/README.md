# Model Context Protocol (MCP) Servers (`.mcp/`)

## Purpose
Hosts local **MCP Servers** built using `FastMCP` (`mcp.server.fastmcp`) and Node.js. These servers expose standardized tools and resources to external AI clients (Antigravity, Claude Desktop, Cursor, VS Code, and automated agents).

---

## Registered MCP Servers

| Server | Entry Point | Primary Tools | Description |
|---|---|---|---|
| **LangChain Breadboard Agent** | `langchain_mcp_server.py` | `agent_query`, `agent_web_search`, `agent_rag_search`, `agent_python_eval` | ReAct agent with RAG access, web search, and Python code evaluation. |
| **Gemini Search Grounding** | `gemini_search_mcp_server.py` | `gemini_web_search`, `gemini_key_pool_status` | Google Search grounding with automatic API key pool rotation. |
| **Gemini CLI Search** | `gemini_cli_search_mcp_server.py` | `gemini_cli_web_search` | Subprocess queries to the local Gemini CLI agent. |
| **Antigravity Search** | `agy_search_mcp_server.py` | `agy_web_search` | Web search powered by Google Antigravity SDK. |
| **FastAPI Client** | `fastapi_mcp_server.py` | `fastapi_chat`, `fastapi_media_list` | Interface to local AI Breadboard REST APIs. |
| **Unicorn Manager** | `unicorn_mcp_server.py` | `unicorn_start`, `unicorn_stop`, `unicorn_status` | Process management for Uvicorn / FastAPI server. |
| **Auto-Commits Helper** | `auto_commits.py` | Background watcher | Tracks file changes and assists with commit checkpoints. |
| **Playwright MCP** | `playwright/` | `POST /precommit`, `POST /apply` | Browser automation and DOM inspection harness. |

---

## Running MCP Servers

```bash
# Gemini Search Grounding
python .mcp/gemini_search_mcp_server.py

# Antigravity Search
python .mcp/agy_search_mcp_server.py

# LangChain Breadboard Agent
python .mcp/langchain_mcp_server.py

# FastAPI Client
python .mcp/fastapi_mcp_server.py
```

---

## MCP Client Configuration

Example snippet for `claude_desktop_config.json` or `cursor-mcp.json`:

```json
{
  "mcpServers": {
    "aibreadboard-gemini-search": {
      "command": "python",
      "args": [".mcp/gemini_search_mcp_server.py"]
    },
    "aibreadboard-langchain": {
      "command": "python",
      "args": [".mcp/langchain_mcp_server.py"]
    },
    "aibreadboard-fastapi": {
      "command": "python",
      "args": [".mcp/fastapi_mcp_server.py"]
    }
  }
}
```

---

## Engineering Standards for MCP Servers
1. All Python MCP servers use `from mcp.server.fastmcp import FastMCP`.
2. Logging is handled through `from core.logger import logger`.
3. Configuration parameters are read from root `config.json`.
4. Tools are registered with the `@mcp.tool()` decorator with explicit type annotations and docstrings.
