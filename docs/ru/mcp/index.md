# 🔌 MCP Серверы AI Breadboard (Model Context Protocol)

## 📋 Обзор

Подсистема **MCP** (`.mcp/`) предоставляет набор серверов протокола **Model Context Protocol (MCP)** для интеграции возможностей AI-Breadboard с внешними AI-ассистентами и средами разработки, такими как **Claude Desktop**, **Cursor**, **VS Code**, **Google Antigravity** и **LangChain**.

MCP стандартизирует подключение инструментов, ресурсов и промптов через протокол JSON-RPC (через `stdio` или SSE).

---

## 🏗️ Архитектура подсистемы MCP

```mermaid
graph TD
    Client[AI Клиенты: Claude Desktop / Cursor / Antigravity] -->|JSON-RPC stdio / SSE| Hub[MCP Серверы (.mcp/)]
    
    subgraph MCPServers ["Серверы MCP (.mcp/)"]
        M1["gemini_search_mcp_server.py / gemini_cli_search_mcp_server.py"]
        M2["agy_search_mcp_server.py"]
        M3["fastapi_mcp_server.py"]
        M4["unicorn_mcp_server.py"]
        M5["langchain_mcp_server.py"]
        M6["auto_commits.py"]
        M7["playwright (Browser Automation)"]
    end
    
    Hub --> M1
    Hub --> M2
    Hub --> M3
    Hub --> M4
    Hub --> M5
    Hub --> M6
    Hub --> M7
    
    MCPServers --> Core[Ядро AI-Breadboard / RAG / Провайдеры]
```

---

## 🚀 Быстрый старт

### Настройка конфигурации клиента

Для автоматической генерации или обновления конфигурационных файлов MCP-клиентов используется утилита:

```powershell
# Генерация конфигурации для Claude Desktop / Cursor
py .mcp/config_helper.py --generate
```

---

## 📚 Навигация по разделу

- [Каталог MCP серверов](catalog.md) — детальный список всех серверов и доступных в них инструментов.
- [Руководство по настройке и интеграции](guide.md) — инструкции по подключению серверов к Claude Desktop, Cursor и Antigravity.
- [Обзор навыков](../skills/index.md) — интеграция инструментов через навыки.
- [Архитектура системы](../architecture/index.md) — общая организация платформы.