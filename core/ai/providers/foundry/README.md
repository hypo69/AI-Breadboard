# Microsoft Foundry Local Provider (`core/ai/providers/foundry`)

## Overview
The `foundry` provider connects to **Microsoft Foundry Local** via its local OpenAI-compatible REST server (default `http://localhost:54837`).

## Key Features
- **Local Multi-Model Support**: Phi-4, Qwen 2.5, DeepSeek, Mistral.
- **Hardware Optimization**: Direct execution against DirectML, CUDA, or CPU backends.
- **Streaming Support**: Full Server-Sent Events (SSE) token streaming.

## Usage
```python
from core.ai.providers.foundry import FoundryChatBase

provider = FoundryChatBase(model_id="phi-4", base_url="http://localhost:54837")
response = await provider.ask("Hello from Foundry Local")
```
