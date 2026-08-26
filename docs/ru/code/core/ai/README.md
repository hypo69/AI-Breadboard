# Модуль `core.ai` — Интеграция с AI-моделями

## Назначение
Пакет `core.ai` инкапсулирует логику взаимодействия с нейросетевыми моделями и агентами:
- `unified_chat.py`: единый роутер и фасад (`UnifiedChatModel`) для диспетчеризации запросов к Gemini SDK, Gemini CLI, Foundry, AGY, Ollama.
- `model_manager.py`: централизованный менеджер пула моделей, фильтрация неподдерживаемых версий и кэширование.
- `gemini_cli_chat.py`: интеграция с локальным терминальным агентом Google Gemini CLI.
- `gemini/`: модуль работы с Google Gemini SDK API, локальным кэшем и пользовательскими RAG-индексами.
- `foundry_chat.py`: клиент Microsoft AI Foundry.
- `agy_chat.py`: интеграция с Antigravity AGY SDK.
- `ollama_chat.py`: интеграция с локальными моделями Ollama.
- `langchain_agent.py`, `langchain_tools.py`, `langchain_prompts.py`: агентная оркестрация медиатеки на базе LangChain.
- `mcp_client.py`: интеграция с серверами протокола Model Context Protocol (MCP).
- `voice_pipeline.py`: конвейер обработки голосовых запросов и управления воспроизведением.\n