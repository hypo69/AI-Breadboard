# Ollama Provider (`core/ai/providers/ollama`)

## Overview
The `ollama` provider communicates with the local Ollama daemon (`http://localhost:11434`) for local LLM inference.

## Key Features
- Dynamic model listing (`/api/tags`)
- Asynchronous streaming (`/api/generate` and `/api/chat`)
- Model pull and management capabilities

## Usage
```python
from core.ai.providers.ollama import OllamaChatBase

provider = OllamaChatBase(model_id="llama3.1", api_url="http://localhost:11434")
response = await provider.ask("Explain async programming in Python.")
```
