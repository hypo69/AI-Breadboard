# scripts/cli — Cross-Platform CLI Modules

Cross-platform Python utilities powering the AI Breadboard CLI on Windows, Linux, and macOS.

## Files

- `assist.py` — Main CLI entry point; implements all `assist` subcommands (start, stop, status, config, logs, providers, etc.)
- `paths.py` — `CrossPlatformPaths` dataclass; auto-detects OS-specific data, config, cache, certs, and bin directories
- `config.py` — `ConfigManager`; reads/writes `config.json` and `.env` with dot-notation key access
- `utils.py` — Port management, process control, PATH manipulation, and cross-platform subprocess helpers
- `installer.py` — Modular installer with i18n support (RU, EN, ES, HE) and skippable stages
- `__init__.py` — Package root

## Usage

```python
from scripts.cli.paths import get_paths
from scripts.cli.config import get_config_manager
from scripts.cli.utils import find_available_port

paths = get_paths()
cfg = get_config_manager()

port = cfg.get_config_value("server.port", 8000)
free_port = find_available_port(start_port=port)
```

## Platform paths

| Platform | data_dir | certs_dir |
|----------|----------|-----------|
| Windows  | `%LOCALAPPDATA%\AI-Breadboard` | `%USERPROFILE%\.certs` |
| Linux    | `~/.local/share/AI-Breadboard` | `~/.local/share/ca-certificates` |
| macOS    | `~/Library/Application Support/AI-Breadboard` | `~/Library/Certs` |

## Dependencies

- `platformdirs` — OS-specific path resolution
- `python-dotenv` — `.env` file loading
- `typer` — CLI framework

## Related

- `launchers/` — Server startup scripts that consume these modules
- `install/` — PowerShell/Bash installers that bootstrap the environment
- `INSTALLER_README.md` — Detailed installer documentation
