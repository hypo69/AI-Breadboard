# launchers

Server startup scripts for AI Breadboard. Each launcher targets a specific runtime configuration.

## Files

- `run.py` — Interactive main launcher; prompts for host/port or accepts `--host`, `--port`, `--non-interactive`
- `run_unicorn.py` — Dedicated Uvicorn launcher for production-grade ASGI serving
- `run_light_server.py` — Lightweight mode launcher with reduced component loading
- `run_foundry.py` — Launcher that starts Microsoft AI Foundry alongside the FastAPI server
- `Run-Agy.ps1` — PowerShell wrapper for AGY provider startup
- `Run-Foundry.ps1` — PowerShell wrapper for Foundry startup
- `Run-Ollama.ps1` — PowerShell wrapper for Ollama service lifecycle management
- `Run-GeminiCli.ps1` — PowerShell wrapper for Gemini CLI mode
- `Run-LightServer.ps1` — PowerShell wrapper for light server mode
- `Run-TelegramBot.ps1` — PowerShell wrapper for standalone Telegram bot service
- `Run-WindowsAdmin.ps1` — Standalone microservice launcher for Windows System Administrator (port 8100)
- `Run-NetworkTerminal.ps1` — Standalone microservice launcher for Network Analyzer Terminal (port 8101)
- `Run-SystemInspector.ps1` — Standalone microservice launcher for System & Hardware Inspector (port 8102)
- `Run-TradingTerminal.ps1` — Standalone microservice launcher for Exchange Trading Terminal (port 8103)
- `Run-CloudflaredMonitor.ps1` — Standalone microservice launcher for Cloudflare Tunnel Monitor (port 8104)
- `Run-Apps.ps1` — Universal multi-app orchestrator to start/stop/check all `/apps` microservices
- `Run-Terminals.ps1` — PowerShell wrapper for multi-terminal workspace (Windows Terminal split-panes or tabs)
- `Run-Unicorn.ps1` — PowerShell wrapper for Uvicorn mode
- `run_tests.ps1` — PowerShell script for running the test suite

## Usage

```powershell
# Windows (recommended)
./run.ps1

# Cross-platform via Python
python launchers/run.py
python launchers/run.py --host 0.0.0.0 --port 8000 --non-interactive
```

## Dependencies

All launchers rely on `scripts/cli/paths.py`, `scripts/cli/config.py`, and `scripts/cli/utils.py` for cross-platform path resolution and configuration loading.

## Windows Embedded App Window & Routing

### Embedded Edge App Mode
On Windows systems, `run.ps1` and `Run-Unicorn.ps1` automatically open the admin interface in an **embedded, standalone App window** (`msedge.exe --app="..."`) rather than opening a tab inside the default external browser:
- **No browser chrome:** No tab bar, address bar, or external browser extensions.
- **Isolated profile:** Session cookies, caches, and localStorage are isolated within `%APPDATA%/AI-Breadboard/browser_profile`.
- **Graceful fallback:** Falls back to default system browser invocation if Edge executable is not located.

### Admin URL Routing: Tunnel vs. Localhost
- **Tunnel / External Domain (`kino.davidka.net/admin` / `davidka.net/admin`):**
  When Cloudflare Tunnel is enabled (`use_cloudflared: true`) and `client_url` is configured in `config.json`, the launcher directs the app window to the public domain through the tunnel.
- **Direct Localhost (`http://localhost:8000/admin` / `https://localhost:8000/admin`):**
  When Cloudflare Tunnel is disabled (`use_cloudflared: false` in `config.json` or `.env`), the launcher automatically binds to `0.0.0.0:8000` and opens `localhost:8000/admin` in the standalone application window without invoking `cloudflared` or directing traffic to external tunnel URLs.
