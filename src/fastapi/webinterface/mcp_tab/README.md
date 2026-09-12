# MCP Servers Tab Component

## Overview
The **MCP Servers Tab** (`src/fastapi/webinterface/mcp_tab/`) provides an interactive administrative dashboard for managing Model Context Protocol (MCP) servers within AI Breadboard. It allows administrators to register, edit, toggle, inspect, and test MCP servers running via `stdio`, `sse`, and `streamable_http` transports.

## Features
- **Server Registry:** List and manage configured MCP servers persisted in `config.json` (`langchain.mcp_servers`).
- **Presets & Templates:** Quick configuration templates for Playwright browser automation, filesystem operations, associative memory graph, SQLite query execution, and remote SSE servers.
- **Connection Testing:** On-demand live connection probing with tool schema discovery and latency metrics.
- **Tools Aggregator:** Centralized view of all tools exposed by enabled MCP servers.
- **View Modes:** Responsive card view and compact table view with search and filter capabilities.

## Structure
- `index.html` — Bootstrap 5 component template and modals.
- `main.js` — Client-side `McpTabManager` controller coordinating REST calls with `/api/admin/mcp/*`.
- `README.md` — Component documentation.

## API Endpoints
- `GET /api/admin/mcp/servers` — Retrieve list of configured MCP servers.
- `POST /api/admin/mcp/servers` — Register a new MCP server.
- `PUT /api/admin/mcp/servers/{server_id}` — Update server configuration.
- `DELETE /api/admin/mcp/servers/{server_id}` — Remove MCP server.
- `POST /api/admin/mcp/servers/{server_id}/toggle` — Toggle server enabled state.
- `POST /api/admin/mcp/servers/{server_id}/test` — Test server connection and retrieve tools.
- `GET /api/admin/mcp/tools` — Retrieve all tools from all enabled MCP servers.
