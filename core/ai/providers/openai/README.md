# OpenAI Compatible Provider (`core/ai/providers/openai`)

## Overview
The `openai` provider enables communication with any OpenAI-compatible API endpoint (LocalAI, vLLM, LM Studio, OpenAI, Azure OpenAI).

## Usage
```python
from core.ai.providers.openai import OpenAICompatChat

provider = OpenAICompatChat(model_name="gpt-4o", base_url="https://api.openai.com/v1")
response = await provider.ask("Hello world")
```
