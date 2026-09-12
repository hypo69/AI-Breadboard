# Google Gemini Provider (`core/ai/providers/gemini`)

## Overview
The `gemini` provider manages cloud-based multi-modal inference via Google Generative AI APIs (Gemini 2.5/3.0/3.7 series), multi-key quota rotation, embeddings, and grounding capabilities.

---

## Capabilities
- **Chat / Reasoning**: `gemini-3.7-flash`, `gemini-2.5-pro`, `gemini-flash-latest`
- **Vision & Multi-modal**: Text, images, audio, video analysis
- **Embeddings**: Vector embeddings for RAG pipelines
- **Code Execution & Tools**: Function calling and structured tool dispatch

---

## Configuration & Environment
Configure API keys in `.env`:
```env
GEMINI_API_KEY_1=AIzaSy...
GEMINI_API_KEY_2=AIzaSy...
```

---

## Usage Example
```python
from core.ai.providers.gemini import GeminiChatBase

provider = GeminiChatBase(model_name="gemini-3.7-flash")
response = await provider.ask("Explain the KISS principle in software engineering.")
```
