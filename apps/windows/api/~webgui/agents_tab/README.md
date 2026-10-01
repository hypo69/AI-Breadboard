# `webinterface/agents_tab` — ReAct AI Agent Workbench

## Purpose
Interactive workbench for creating, testing, and debugging autonomous ReAct AI agents, MCP tool assignments, and iterative reasoning chains.

---

## Capabilities
- **Agent CRUD**: Configure agent system instructions, temperature, top-k tools, and target model providers.
- **Tool Sandbox**: Inspect and test available LangChain tools, MCP servers, and skills.
- **Reasoning Trace Viewer**: Visualizes intermediate thought, action, observation, and final answer steps.

---

## Files
- `index.html`: Agent workbench interface.
- `main.js`: Agent management controller connecting to `/api/agents`.
- `style.css`: Visual styling for reasoning traces.
