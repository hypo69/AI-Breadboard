---
name: ifttt-controller
description: Smart home and automation controller via IFTTT Maker Webhooks. Triggers IoT devices, smart lighting, appliances, notifications, and custom applets.
description_i18n:
  en: Smart home and automation controller via IFTTT Maker Webhooks. Triggers IoT devices, smart lighting, appliances, notifications, and custom applets.
  ru: Контроллер умного дома и автоматизации через IFTTT Maker Webhooks. Управляет IoT-устройствами, освещением, техникой, оповещениями и пользовательскими апплетами.
---

# IFTTT Smart Home Controller

This skill enables AI Breadboard agents to interact with smart home devices, lighting, climate, appliances, and notifications through the **IFTTT Smart Home Plugin** (`plugins/ifttt`).

## 🚀 Quick Start

### 1. Triggering Events via AI Agent Tool
The assistant invokes the `ifttt_trigger_event` tool with the event name and optional parameters:
```python
await ifttt_trigger_event(
    event_name="living_room_light_on",
    value1="warm_white",
    value2="80%"
)
```

### 2. Standalone CLI Script
Execute smart home triggers from terminal or automation scripts:
```bash
python skills/ifttt-controller/scripts/trigger_event.py --event movie_mode --value1 "active"
```

### 3. Programmatic Usage in Python
```python
from plugins.ifttt import send_ifttt_event

await send_ifttt_event(
    event_name="ac_cool",
    value1="22C",
    value2="high"
)
```

## 📂 Structure
- `plugins/ifttt/`: Core modular plugin (`plugin.py`, `client.py`, `config.json`).
- `scripts/trigger_event.py`: CLI script for triggering IFTTT events.
- `references/smart_home_scenarios.md`: Architectural scenarios and smart home recipes.
- `src/fastapi/router_ifttt.py`: Inbound and outbound FastAPI REST endpoints.
