# launchers

Server startup scripts for AI Breadboard. Each launcher targets a specific runtime configuration.

## Files

- `run.py` — Interactive main launcher; prompts for host/port or accepts `--host`, `--port`, `--non-interactive`
- `run_unicorn.py` — Dedicated Uvicorn launcher for production-grade ASGI serving
- `run_light_server.py` — Lightweight mode launcher with reduced component loading
- `run_foundry.py` — Launcher that starts Microsoft AI Foundry alongside the FastAPI server
- `Run-Agy.ps1` — PowerShell wrapper for AGY provider startup
- `Run-Foundry.ps1` — PowerShell wrapper for Foundry startup
- `Run-GeminiCli.ps1` — PowerShell wrapper for Gemini CLI mode
- `Run-LightServer.ps1` — PowerShell wrapper for light server mode
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
