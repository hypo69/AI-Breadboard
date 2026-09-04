# Hugging Face Provider (`core/ai/providers/huggingface`)

## Overview
The `huggingface` provider runs local transformer models directly in-process or via Hugging Face Inference Endpoints.

## Usage
```python
from core.ai.providers.huggingface import HFChatBase

provider = HFChatBase(model_id="google/gemma-2-2b-it")
response = await provider.ask("Summarize the text.")
```
