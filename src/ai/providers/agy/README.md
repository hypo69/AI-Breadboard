# AGY Provider (`core/ai/providers/agy`)

## Overview
The `agy` provider coordinates execution through the local Antigravity (AGY) agentic runtime and subprocess interfaces.

## Capabilities
- **Chat & Tool Dispatch**: Integrates with local Antigravity sidecar and agent protocols.
- **Session Continuity**: Multi-turn conversation context preserved locally.

## Usage
```python
from core.ai.providers.agy import AgyChatBase

provider = AgyChatBase(system_prompt="You are a helpful coding assistant.")
response = await provider.ask("Provide refactoring recommendations.")
```
