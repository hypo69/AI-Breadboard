# Gemini CLI Provider (`core/ai/providers/gemini_cli`)

## Overview
The `gemini_cli` provider enables direct CLI-driven inference via the local `gemini` command line utility, supporting session persistence and direct terminal interaction.

## Usage
```python
from core.ai.providers.gemini_cli import GeminiCliChatBase

provider = GeminiCliChatBase(model_name="gemini-2.5-flash")
response = await provider.ask("Generate unit tests for auth module.")
```
