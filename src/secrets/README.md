# `src.secrets` Module — Secrets & API Key Management

## Overview
The `src.secrets` module manages Google Gemini and AI provider credentials, rotation pools, and runtime statuses.

---

## Storage Schema (`src/secrets/gemini_keys.json`)

All keys are stored in `src/secrets/gemini_keys.json` with the following structure:

```json
{
  "key_name": {
    "value": "AIzaSy...",
    "last_run": "2026-09-08T15:45:00+00:00",
    "status": "active"
  }
}
```

### Statuses:
- `"active"`: The API key is ready and available for generation requests.
- `"exhausted"`: The key hit daily quota limit (HTTP 429) and is temporarily quarantined with auto-recovery after 24h.
- `"disabled"`: The key was manually turned off.

---

## Dynamic Environment Substitution

When keys are loaded, rotated, or when quota exhaustion occurs, the module dynamically selects the active key from the pool and injects it into:
- `os.environ["GEMINI_API_KEY"]`

Antigravity (AGY) provider credentials are read preferentially from `AGY_API_KEY` with fallback to the Gemini rotation pool.
