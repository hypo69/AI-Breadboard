# `core.clients` Module — External Service Clients

## Purpose
The `core.clients` package provides dedicated client adapters for connecting to third-party services, local model daemons, and external communication gateways.

---

## Components

| File | Target Service | Description |
|---|---|---|
| `foundry.py` | Microsoft AI Foundry | Async HTTP client communicating with local or hosted OpenAI-compatible Foundry servers (`http://localhost:54837/v1`). |
| `ollama.py` | Ollama | REST client querying local Ollama instances (`http://localhost:11434`) for model listing, generate, and chat endpoints. |
| `tg_tts_handler.py` | Telegram Bot API | Audio processing and voice synthesis pipeline for Telegram bots and Mini Apps. |

---

## Architectural Guidelines

- All network requests use asynchronous HTTP clients (`aiohttp` or `httpx`) with explicit timeout configurations.
- Endpoint connection errors must be caught and raised as typed exceptions or logged gracefully through `core.logger.logger`.
- No sensitive credentials or fixed URLs are hardcoded; configs are sourced from `config.json` and `.env`.
