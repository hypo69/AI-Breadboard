# Telegram Bot & Mini App Plugin (`telegram_bot`)

## Overview

The `telegram_bot` plugin encapsulates all Telegram functionality for the **AI Breadboard** platform:
- Interactive Telegram bot lifecycle management using `python-telegram-bot`.
- Remote Control Mini App integration (`/rc` web app launch button in chat).
- Streaming text-to-speech (TTS) voice narration directly delivered into Telegram chats.
- User account linking between Telegram ID and web profiles via one-time 8-character tokens.
- Notification dispatch to administrators.
- Direct conversational AI queries routed to active AI models (Google Gemini or local Foundry models).

## Architecture

The plugin resides under `plugins/telegram_bot/` and inherits from `BasePlugin` (`plugins/base.py`):
```text
plugins/telegram_bot/
├── __init__.py      # Package export & plugin(ai_model=None) factory
├── plugin.py        # TelegramBotPlugin(BasePlugin) implementation
├── bot.py           # TelegramBotEngine (python-telegram-bot application lifecycle)
├── tts.py           # Voice narration and streaming TTS audio handler
├── config.json      # Default configuration file
└── README.md        # English documentation
```

## Configuration

Settings can be managed via `config.json`, the Web UI **Admin -> Plugins** tab, or `.env`:

| Key | Type | Description | Default |
|---|---|---|---|
| `token` | `string` | Telegram Bot token obtained from `@BotFather` | `""` (or `TELEGRAM_BOT_TOKEN` in `.env`) |
| `admin_ids` | `list_string` | Comma-separated list of Telegram user IDs for admin rights | `[]` |
| `notifications_enabled` | `boolean` | Whether download and system alerts are sent to Telegram | `true` |
| `api_base_url` | `string` | Base URL of local FastAPI server for Mini App & TTS | `"http://127.0.0.1:8000"` |

## Bot Commands

| Command | Arguments | Description |
|---|---|---|
| `/start` | None | Greets user, provides help, and displays the **Remote Control (Mini App)** button |
| `/help` | None | Displays detailed help and instructions |
| `/status` | None | Checks bot status, active AI model, and system diagnostics |
| `/link` | `<TOKEN>` | Links Telegram chat ID to AI Breadboard web account using token generated in profile |
| `/tts` | `<text>` | Converts provided text to voice note using adaptive TTS pipeline |

## Admin UI Actions

Through the **Plugins** management tab in the Admin Web Interface, administrators can execute:
- **Start Bot:** Initiates the Telegram polling loop.
- **Stop Bot:** Shuts down the running polling loop cleanly.
- **Check Status:** Retrieves live JSON status on token configuration, active connection, and registered admin count.
- **Test Message:** Sends a test ping to the first configured administrator Telegram ID.

## Running the Bot

### 1. Via Launcher (Dedicated Process)
```powershell
.\launchers\Run-TelegramBot.ps1 -Action start
```

### 2. Via Unified Launcher with Switch
```powershell
.\run.ps1 -EnableTelegramBot
```

### 3. Programmatic Usage in Python
```python
from plugins import load_plugins

plugins = load_plugins()
tg_plugin = plugins.get("telegram_bot")

if tg_plugin and tg_plugin.enabled:
    await tg_plugin.start()
```

## Backward Compatibility

Existing imports referencing `integrations.telegram.handle_telegram_voiceover_request` are automatically forwarded to `plugins.telegram_bot.tts.handle_telegram_voiceover_request`.
