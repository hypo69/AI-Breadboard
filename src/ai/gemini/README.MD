# Google Gemini AI Integration (`core.ai.gemini`)

## Overview
The `core/ai/gemini` module delivers an enterprise-grade high-level client (`GoogleGenerativeAI`) for Google Gemini models via the official `google-genai` SDK.

The module incorporates self-healing resilience: automatic multi-key quota rotation, 24-hour rate limit backoff (HTTP 429), dynamic model downgrading upon server errors (HTTP 503), model fallback for missing models (HTTP 404), and autonomous agentic tool calling loops.

---

## Key Capabilities

1. **API Key Pool Management:**
   - Multi-key rotation based on last access timestamp (`last_run`).
   - Automated 24-hour quarantine for quota-exhausted keys (`mark_exhausted`).
   - Immediate exclusion of invalid keys (HTTP 401).
2. **Dynamic Fault Tolerance:**
   - Automatic fallback to supported models on 404 errors.
   - Exponential backoff and model downgrade upon transient 503 unavailability.
   - Optional blocking sleep until key reset (`sleep_on_exhausted`).
3. **Inference & Streaming:**
   - Direct stateless queries (`ask`).
   - Stateful conversational sessions with history (`chat`).
   - Async streaming generation (`chat_stream`).
   - Multimodal inputs (`describe_image`) and file uploads (`upload_file`).
   - Text vector embeddings generation (`embed`).
4. **Agentic Tool Dispatching:**
   - Built-in Google Search Grounding support.
   - Automated dispatch loops for custom Python callable tools (`ask_with_tools`, `ask_with_tools_stream`).

---

## Usage Examples

### Stateless Prompt
```python
import asyncio
from core.ai.gemini import GoogleGenerativeAI

async def main():
    ai = GoogleGenerativeAI(system_instruction="You are a senior electronics testbench assistant.")
    answer = await ai.ask("What is a pull-up resistor used for?")
    print(answer)

asyncio.run(main())
```

### Conversational Session
```python
async def chat_session():
    ai = GoogleGenerativeAI(save_history_chat=True)
    r1 = await ai.chat("Recommend 3 sci-fi movies featuring AI companions.")
    print("AI:", r1)
    r2 = await ai.chat("Which of these is the newest?")
    print("AI:", r2)
```

### Streaming Tokens
```python
async def stream_output():
    ai = GoogleGenerativeAI()
    async for chunk in ai.chat_stream("Summarize the history of microprocessors:"):
        print(chunk, end="", flush=True)
```
