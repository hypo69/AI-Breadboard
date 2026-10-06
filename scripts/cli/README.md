# Модуль `scripts/cli` — Кроссплатформенные CLI-модули

Кроссплатформенные утилиты Python, обеспечивающие работу консольного интерфейса AI Breadboard (`manage_tools.py`, `assist`) на Windows, Linux и macOS.

## Структура файлов

- [`assist.py`](assist.py) — Главная точка входа интерактивного CLI (`start`, `stop`, `status`, `config`, `logs`, `providers` и др.).
- [`paths.py`](paths.py) — Датакласс `CrossPlatformPaths`: автоматическое определение путей к данным, конфигурациям, кэшу, сертификатам и бинарникам для текущей ОС.
- [`config.py`](config.py) — `ConfigManager`: чтение и запись `config.json` и `.env` с поддержкой dot-нотации ключей.
- [`utils.py`](utils.py) — Управление портами, контроль процессов, манипуляция PATH и кроссплатформенные хелперы `subprocess`.
- [`installer.py`](installer.py) — Модульный интерактивный установщик с поддержкой локализации (RU, EN, ES, HE).
- [`terminal_manager.py`](terminal_manager.py) — Менеджер профилей терминалов и сборщик макетов Windows Terminal (`wt.exe`).
- [`commands/`](commands/) — Обработчики подкоманд для `manage_tools.py` (`agents`, `db`, `docs`, `network`, `plugins`, `rag`, `skills`, `sys_param`, `telemetry`).

## Использование в коде

```python
from scripts.cli.paths import get_paths
from scripts.cli.config import get_config_manager
from scripts.cli.utils import find_available_port

paths = get_paths()
cfg = get_config_manager()

port = cfg.get_config_value("server.port", 8000)
free_port = find_available_port(start_port=port)
```

## Пути платформы

| Платформа | `data_dir` | `certs_dir` |
|---|---|---|
| Windows | `%LOCALAPPDATA%\AI-Breadboard` | `%USERPROFILE%\.certs` |
| Linux | `~/.local/share/AI-Breadboard` | `~/.local/share/ca-certificates` |
| macOS | `~/Library/Application Support/AI-Breadboard` | `~/Library/Certs` |
