# Кроссплатформенная система CLI

Этот Module содержит кроссплатформенные утилиты для работы AI-Breadboard на Windows, Linux и macOS.

## Структура

### `paths.py` - Система управления путями
Автоматически определяет правильные пути для каждой платформы:

```python
from scripts.cli.paths import get_paths, init_paths

# Инициализировать пути и окружение
paths = init_paths()

# Получить пути, адаптированные для платформы
print(paths.data_dir)      # ~/.local/share/AI-Breadboard (Linux) или %LOCALAPPDATA%\AI-Breadboard (Windows)
print(paths.config_dir)    # ~/.config/AI-Breadboard (Linux) или %LOCALAPPDATA%\AI-Breadboard\config (Windows)
print(paths.certs_dir)     # ~/.local/share/ca-certificates (Linux) или %USERPROFILE%\.certs (Windows)
print(paths.bin_dir)       # ~/.local/bin (Linux/macOS) или %USERPROFILE%\.local\bin (Windows)
print(paths.project_root)  # Корень проекта
```

### `config.py` - Управление конфигурацией
Reads и writes JSON конфигурации и .env файлы:

```python
from scripts.cli.config import get_config_manager

cfg = get_config_manager()

# Загрузить конфигурацию
config = cfg.load_config()

# Получить значение по пути
port = cfg.get_config_value("server.port", 8000)

# Установить значение
cfg.set_config_value("server.port", 8080)

# Работа с .env файлом
cfg.set_env_var("API_KEY", "secret")
api_key = cfg.get_env_var("API_KEY")
```

### `utils.py` - Кроссплатформенные утилиты

#### Управление портами
```python
from scripts.cli.utils import find_available_port, is_port_open, get_process_on_port, kill_process

# Найти свободный порт
port = find_available_port(start_port=8000)

# Проверить, занят ли порт
if is_port_open(8000):
    pid, name = get_process_on_port(8000)
    kill_process(pid, force=True)
```

#### Переменные окружения
```python
from scripts.cli.utils import ensure_in_path, add_to_env_var

# Добавить бинарник в PATH
ensure_in_path(Path("/usr/local/bin/assist"))

# Добавить переменную окружения
add_to_env_var("PYTHONPATH", "/path/to/project")
```

#### Выполнение команд
```python
from scripts.cli.utils import run_command, which

# Выполнить команду
result = run_command(["python", "--version"])

# Найти команду в PATH
python_path = which("python")
```

## Кроссплатформенные различия

### Windows
- Данные: `%LOCALAPPDATA%\AI-Breadboard`
- Конфиг: `%LOCALAPPDATA%\AI-Breadboard\config`
- Кэш: `%LOCALAPPDATA%\AI-Breadboard\Cache`
- Сертификаты: `%USERPROFILE%\.certs`
- Бинарники: `%USERPROFILE%\.local\bin`

### Linux
- Данные: `~/.local/share/AI-Breadboard`
- Конфиг: `~/.config/AI-Breadboard`
- Кэш: `~/.cache/AI-Breadboard`
- Сертификаты: `~/.local/share/ca-certificates`
- Бинарники: `~/.local/bin`

### macOS
- Данные: `~/Library/Application Support/AI-Breadboard`
- Конфиг: `~/Library/Preferences/AI-Breadboard`
- Кэш: `~/Library/Caches/AI-Breadboard`
- Сертификаты: `~/Library/Certs`
- Бинарники: `~/.local/bin`

## Зависимости

```
platformdirs>=4.0.0  # Кроссплатформенные пути
typer>=0.12.0        # CLI фреймворк
python-dotenv>=1.0.0 # Loading .env
```

## Examples использования

### Пример 1: Initialization приложения
```python
from scripts.cli.paths import init_paths
from scripts.cli.config import get_config_manager

# Инициализировать пути и окружение
paths = init_paths()

# Загрузить конфигурацию
config = get_config_manager().load_config()

print(f"Проект: {paths.project_root}")
print(f"Данные: {paths.data_dir}")
print(f"Порт: {config['server']['port']}")
```

### Пример 2: Запуск сервера на свободном порту
```python
from scripts.cli.paths import init_paths
from scripts.cli.config import get_config_manager
from scripts.cli.utils import find_available_port, kill_process, get_process_on_port
import subprocess

paths = init_paths()
cfg = get_config_manager()

default_port = cfg.get_config_value("server.port", 8000)

# Если порт занят, найти свободный
if proc := get_process_on_port(default_port):
    print(f"Порт {default_port} занят процессом {proc[1]} (PID: {proc[0]})")
    kill_process(proc[0], force=False)
    port = find_available_port(start_port=default_port)
else:
    port = default_port

# Запустить сервер
cfg.set_config_value("server.port", port)
subprocess.run(["python", "-m", "uvicorn", "main:app", "--port", str(port)])
```

### Пример 3: Добавить команду в PATH
```python
from pathlib import Path
from scripts.cli.utils import ensure_in_path

# Создать симлинк на assist скрипт
assist_script = Path("/usr/local/bin/assist")
if not assist_script.exists():
    ensure_in_path(assist_script)
    print(f"Команда добавлена в PATH: {assist_script}")
```

## Миграция со старых PowerShell скриптов

### Старое (PowerShell):
```powershell
$projectDir = "C:\Users\onela\AppData\Local\AI Breadboard"
$venvPython = Join-Path $projectDir "venv\Scripts\python.exe"
$env:AIBREADBOARD_DIR = "$projectDir"
```

### Новое (Python):
```python
from scripts.cli.paths import init_paths

paths = init_paths()
print(paths.project_root)    # Автоматически определено
print(paths.venv_python)    # Адаптирован для ОС
```

## Замечания по использованию

1. **Всегда вызывайте `init_paths()`** при запуске приложения для установки переменных окружения
2. **Используйте `Path` вместо строк** для работы с файлами
3. **Используйте `get_config_manager()`** для работы с конфигурацией
4. **Не жестко кодируйте пути** - используйте `get_paths()`
5. **Проверяйте платформу через `sys.platform`** для платформо-специфичного кода

## Тестирование на разных платформах

```bash
# Linux
python -c "from scripts.cli.paths import get_paths; print(get_paths().data_dir)"

# Должно вывести: /home/user/.local/share/AI-Breadboard
```

```powershell
# Windows
python -c "from scripts.cli.paths import get_paths; print(get_paths().data_dir)"

# Должно вывести: C:\Users\user\AppData\Local\AI-Breadboard
```
