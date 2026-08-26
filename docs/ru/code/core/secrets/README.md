# Secrets and API Key Management (`core/secrets`)

## Overview
The `core.secrets` module manages sensitive credentials, API keys for AI models (Google Gemini, Microsoft AI Foundry, OpenAI, etc.), and their runtime state (status, quota exhaustion cooldowns, rotation).

## Key Components
- **`api_key_state.py`**: Core logic for loading, rotating, and tracking API key quotas.
  - **`load_api_keys(names=None, skip_exhausted=True)`**: Returns active, non-exhausted API keys.
  - **`mark_exhausted(key_name)`**: Sets a 24-hour exhaustion cooldown on a key upon encountering quota limits (HTTP 429).
  - **`update_last_run(key_name)`**: Records the last usage timestamp of a key.
  - **`next_available_in()`**: Returns remaining cooldown seconds until the earliest key resets.
  - **`save_api_key(name, api_key, status)`**: Persists new or updated API keys.

## Storage Locations & Priority
1. `core/secrets/gemini_keys.json` (Structured JSON storage with quota metadata)
2. `core/ai/gemini/secrets.json` (Legacy secrets storage)
3. `.env` file (`GEMINI_API_KEY`, `GOOGLE_API_KEY`, `GEMINI_API_KEYS`, `AGY_API_KEY`)
4. Environment variables in the host process

## Key File Format (`gemini_keys.json`)
```json
{
  "key_name": {
    "api_key": "AIzaSy...",
    "status": "active",
    "last_run": "2026-08-04T12:00:00+00:00",
    "exhausted_at": null
  }
}
```
