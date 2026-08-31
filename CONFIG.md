# Configuration AI Breadboard (Кроссплатформенная)

Этот документ описывает систему конфигурации AI Breadboard и как она работает на Windows, Linux и macOS.

## Файлы конфигурации

### 1. `config.json` — Основная Configuration приложения

Содержит Parameters сервера, моделей ИИ, провайдеров и логирования.

**Особенности:**
- Не содержит жестко закодированных путей
- Кроссплатформенна по умолчанию
- Пути определяются автоматически через `scripts/cli/paths.py`
- Все Parameters портируемы между платформами

**Пример:**
```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8000,
    "use_ssl": true
  },
  "ai": {
    "use_foundry": true,
    "foundry_model_id": "qwen2.5-1.5b"
  }
}
```

### 2. `.env` — Переменные окружения

Хранит чувствительные данные (API ключи, пароли).

**Пример (.env):**
```bash
# Gemini API ключи (через запятую)
GEMINI_API_KEY_NAMES=key1,key2,key3
GEMINI_API_KEY_key1=sk-...
GEMINI_API_KEY_key2=sk-...

# Другие Parameters
USE_SSL=true
USE_FOUNDRY=true
MODE=DEV
```

**Важно:**
- `.env` файл НЕ должен добавляться в git (см. `.gitignore`)
- Создавайте локально на каждой машине
- Использует формат `KEY=VALUE` (один параметр на строку)

### 3. `install/install.json` — Configuration установки

Содержит Parameters для инсталляторов и сведения о проекте.

**Структура:**
```json
{
  "defaults": {
    "language": "en",
    "python_min_version": "3.10",
    "repo_url": "https://github.com/hypo69/AI-Breadboard"
  },
  "paths": {
    "cert_file": "localhost+2.pem",
    "env_file": ".env",
    "config_file": "config.json"
  },
  "verify": {
    "modules": ["fastapi", "uvicorn", "dotenv"]
  }
}
```

## Кроссплатформенная система путей

### Как работает?

1. **Автоматическое определение**
   ```python
   from scripts.cli.paths import get_paths
   
   paths = get_paths()
   # Автоматически Returns правильные пути для ОС
   print(paths.data_dir)    # ~/.local/share/AI-Breadboard (Linux)
   print(paths.certs_dir)   # ~/.certs (Windows)
   ```

2. **Иерархия источников**
   - Переменная окружения `AIBREADBOARD_DIR` (если установлена)
   - Автоматическое определение по `config.json` или `main.py`
   - Fallback на текущую директорию

### Пути по платформам

#### Windows

| Назначение | Путь |
|-----------|------|
| Данные | `%LOCALAPPDATA%\AI-Breadboard` |
| Конфиг | `%LOCALAPPDATA%\AI-Breadboard\config` |
| Кэш | `%LOCALAPPDATA%\AI-Breadboard\Cache` |
| SSL сертификаты | `%USERPROFILE%\.certs` |
| Бинарники | `%USERPROFILE%\.local\bin` |

#### Linux

| Назначение | Путь |
|-----------|------|
| Данные | `~/.local/share/AI-Breadboard` |
| Конфиг | `~/.config/AI-Breadboard` |
| Кэш | `~/.cache/AI-Breadboard` |
| SSL сертификаты | `~/.local/share/ca-certificates` |
| Бинарники | `~/.local/bin` |

#### macOS

| Назначение | Путь |
|-----------|------|
| Данные | `~/Library/Application Support/AI-Breadboard` |
| Конфиг | `~/Library/Preferences/AI-Breadboard` |
| Кэш | `~/Library/Caches/AI-Breadboard` |
| SSL сертификаты | `~/Library/Certs` |
| Бинарники | `~/.local/bin` |

## Работа с конфигурацией через API

### ConfigManager class

```python
from scripts.cli.config import get_config_manager

cfg = get_config_manager()

# Загрузить всю конфигурацию
config = cfg.load_config()

# Получить значение по пути (через точку)
port = cfg.get_config_value("server.port", 8000)

# Установить значение
cfg.set_config_value("server.port", 8080)

# Работа с .env файлом
cfg.set_env_var("API_KEY", "secret")
api_key = cfg.get_env_var("API_KEY")
```

### Получить переменные окружения

```python
from scripts.cli.config import get_config_manager

cfg = get_config_manager()

# Получить с приоритетом: система > .env > default
value = cfg.get_env_var("GEMINI_API_KEY", "default")
```

## Переменные окружения

### Системные переменные

```bash
# Обязательно устанавливаются при запуске
AIBREADBOARD_DIR        # Корень проекта
ASSIST_DIR              # То же самое
PYTHONUTF8=1            # UTF-8 для Python
PYTHONPATH              # Пути для импорта модулей

# Опционально
USE_SSL=true            # Включить HTTPS
USE_FOUNDRY=true        # Использовать Microsoft Foundry
MODE=DEV                # DEV или PROD
```

### Переменные API ключей

```bash
# Gemini API (list ключей через запятую)
GEMINI_API_KEY_NAMES=key1,key2,key3
GEMINI_API_KEY_key1=sk-...
GEMINI_API_KEY_key2=sk-...

# Другие провайдеры
AGY_API_KEY=your-key
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-...
```

## Examples использования

### Пример 1: Получить URL сервера кроссплатформенно

```python
from scripts.cli.config import get_config_manager
from scripts.cli.utils import find_available_port

cfg = get_config_manager()

# Получить конфиг
host = cfg.get_config_value("server.host", "0.0.0.0")
port = cfg.get_config_value("server.port", 8000)
use_ssl = cfg.get_config_value("server.use_ssl", False)

# Построить URL
protocol = "https" if use_ssl else "http"
url = f"{protocol}://{host}:{port}"
print(f"Server: {url}")  # http://0.0.0.0:8000
```

### Пример 2: Проверить и изменить конфиг

```python
from scripts.cli.config import get_config_manager

cfg = get_config_manager()

# Проверить текущий порт
current_port = cfg.get_config_value("server.port")
print(f"Current port: {current_port}")

# Изменить на 8080
cfg.set_config_value("server.port", 8080)
print("Port changed to 8080")

# Проверить новое значение
new_port = cfg.get_config_value("server.port")
print(f"New port: {new_port}")
```

### Пример 3: Работа с .env файлом

```python
from scripts.cli.config import get_config_manager

cfg = get_config_manager()

# Установить API ключ
cfg.set_env_var("GEMINI_API_KEY", "sk-your-key")

# Получить с приоритетом
api_key = cfg.get_env_var("GEMINI_API_KEY")

# Сохранить в .env файл
cfg.set_env_var("USE_SSL", "true")
```

## Миграция конфигурации между платформами

### Windows → Linux

1. **Скопировать config.json:**
   ```bash
   scp user@windows-machine:/path/to/config.json ~/AI-Breadboard/config.json
   ```

2. **Скопировать .env:**
   ```bash
   scp user@windows-machine:/path/to/.env ~/AI-Breadboard/.env
   ```

3. **Готово!** Пути автоматически адаптируются.

### Linux → macOS

Аналогично — всё работает благодаря кроссплатформенной системе путей.

## Check конфигурации

### Использовать assist CLI

```bash
# Показать всю конфигурацию
assist config show

# Получить значение
assist config get server.port

# Установить значение
assist config set server.port 8080
```

### Программно

```python
import json
from pathlib import Path

config_path = Path("config.json")
config = json.loads(config_path.read_text())

# Проверить
print(json.dumps(config, indent=2))
```

## Рекомендации

1. **Не коммитьте .env файл** — используйте `.env.example`
2. **Используйте ConfigManager** для работы с конфигурацией в коде
3. **Не жестко кодируйте пути** — используйте `scripts/cli/paths.py`
4. **Тестируйте на разных ОС** перед миграцией конфига
5. **Храните чувствительные данные в .env**, не в config.json

## Дополнительная Info

- [scripts/cli/README.md](./scripts/cli/README.md) — Документация по CLI модулям
- [scripts/cli/paths.py](./scripts/cli/paths.py) — Система управления путями
- [scripts/cli/config.py](./scripts/cli/config.py) — ConfigManager class
- [config.crossplatform.example.json](./config.crossplatform.example.json) — Пример конфигурации

## Контакты

Если у вас есть вопросы о конфигурации:
- GitHub Issues: https://github.com/hypo69/AI-Breadboard/issues
- GitHub Discussions: https://github.com/hypo69/AI-Breadboard/discussions
