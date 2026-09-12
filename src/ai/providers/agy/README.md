# AGY Provider (`src/ai/providers/agy`)

## Overview
The `agy` provider coordinates execution through the Google Antigravity (AGY) agentic runtime, harness processes, and SDK interfaces (`google.antigravity`).

---

## Architecture & Lifecycle

### 1. Persistent Agent Session
- **Long-Running Process**: Uses a persistent `Agent` instance (`self._agent`) kept alive across streaming and chat invocations.
- **Session Continuity**: Multi-turn dialogue context is maintained natively inside the running agent trajectory without re-spawning subprocesses or resetting connection channels on idle state (`STATE_FULLY_IDLE`).
- **Lazy Initialization & Thread-Safety**: Employs `asyncio.Lock` to initialize the session on first demand (`await agent.__aenter__()`) and reuses it for subsequent requests.
- **Safe Lifecycle Teardown**: Automatically shuts down (`close()`) upon model configuration changes, system prompt updates, or explicit conversation reset (`clear_history()`).

### 2. Streaming Output
- `chat_stream(q, ...)` streams incremental token chunks (`AsyncGenerator[str, None]`) in real-time as received from the agent harness.
- Handles error boundaries gracefully, resetting state and recovering on subsequent calls if unexpected harness disconnects occur.

---

## Usage Example

```python
from src.ai.providers.agy.chat import AgyChatBase

# Initialize adapter with desired model and system prompt
chat = AgyChatBase(model_id="agy-flash", system_prompt="You are a helpful assistant.")

# Stream responses over a persistent session
async for token in chat.chat_stream("Hello! How are you?"):
    print(token, end="", flush=True)

# Explicitly close when session is done
await chat.close()
```

---

## Unit Testing
Unit tests validating persistent session retention and streaming generation are located in [`tests/test_agy_chat.py`](../../../tests/test_agy_chat.py).
