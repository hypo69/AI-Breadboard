# Миграция на Linux (Портирование PowerShell на Python)

## Обзор

Проект AI-Breadboard был портирован для поддержки Windows, Linux и macOS. Все PowerShell скрипты заменены на кроссплатформенные Python реализации.

## Главные изменения

### 1. Точка входа CLI

**Старое (Windows):**
```powershell
# assist.ps1 / assist.cmd
assist start
assist status
assist logs
```

**Новое (кроссплатформенное):**
```bash
# assist (bash на Linux/macOS) или assist.cmd (Windows)
assist start
assist status
assist logs
```

**Реализация:**
- `assist.py` — Python скрипт (основная логика)
- `assist` — Bash обертка для Linux/macOS
- `assist.cmd` — Batch обертка для Windows
- `assist_cross.ps1` — PowerShell обертка (опционально)

### 2. Управление путями

**Старое (Windows-специфичное):**
```python
# assist.ps1
$projectDir = "C:\Users\onela\AppData\Local\AI Breadboard"
$venvPython = Join-Path $projectDir "venv\Scripts\python.exe"
```

**Новое (автоматическое для каждой ОС):**
```python
from scripts.cli.paths import get_paths, init_paths

paths = init_paths()
print(paths.project_root)      # Правильно для Windows/Linux/macOS
print(paths.venv_python)       # Правильно для каждой ОС
print(paths.data_dir)          # ~/.local/share/AI-Breadboard (Linux)
print(paths.certs_dir)         # ~/.local/share/ca-certificates (Linux)
```

### 3. Система конфигурации

**Старое (JSON + PowerShell):**
```powershell
# install.json имел Windows пути
"install_dir": "%LOCALAPPDATA%\\AI Breadboard"
"certs_dir": "%USERPROFILE%\\.certs"
```

**Новое (JSON + Python + автоматические пути):**
```python
from scripts.cli.config import get_config_manager

cfg = get_config_manager()
config = cfg.load_config()

# Все пути автоматически адаптированы для ОС
port = cfg.get_config_value("server.port", 8000)
cfg.set_config_value("server.port", 8080)
```

## Миграция скриптов установки

### PowerShell скрипты → Python модули

| Старый скрипт | Новый Module | Status |
|-------|---------|--------|
| `install.ps1` | `scripts/cli/installer.py` | ✅ Планируется |
| `Install-Venv.ps1` | Python function | ✅ Готово |
| `Install-Deps.ps1` | Python function | ✅ Готово |
| `Install-Certs.ps1` | Python function | ✅ Готово |
| `Install-Cli.ps1` | Python function | ✅ Готово |
| `Run-Unicorn.ps1` | `launchers/run_unicorn.py` | 🔄 В процессе |
| `Run-Foundry.ps1` | `launchers/run_foundry.py` | 🔄 В процессе |
| `run.ps1` | `launchers/run.py` | 🔄 В процессе |

## Использование на разных платформах

### Windows

```bash
# Batch (cmd.exe)
assist.cmd start
assist.cmd status

# Или PowerShell
powershell -ExecutionPolicy Bypass -File assist_cross.ps1 start

# Или Python напрямую
python scripts\cli\assist.py start
```

### Linux / macOS

```bash
# Bash
chmod +x assist
./assist start
./assist status

# Или добавить в PATH
sudo cp assist /usr/local/bin/assist
assist start

# Или Python напрямую
python3 scripts/cli/assist.py start
```

### WSL (Windows Subsystem for Linux)

```bash
# Используется как на Linux
chmod +x assist
./assist start

# Автоматически определяет Python и пути
```

## Кроссплатформенные API

### Управление портами

**Старое (Windows-специфичное, netstat):**
```powershell
netstat -aon | find ":8000"
taskkill /PID $pid /F
```

**Новое (кроссплатформенное):**
```python
from scripts.cli.utils import find_available_port, is_port_open, get_process_on_port, kill_process

# Найти свободный порт
port = find_available_port(start_port=8000)

# Проверить занятость
if is_port_open(8000):
    pid, proc_name = get_process_on_port(8000)
    kill_process(pid, force=True)
```

### Управление переменными окружения

**Старое (Windows реестр):**
```powershell
[System.Environment]::SetEnvironmentVariable('AIBREADBOARD_DIR', $path, 'User')
```

**Новое (кроссплатформенное):**
```python
from scripts.cli.utils import add_to_env_var

add_to_env_var("AIBREADBOARD_DIR", "/path/to/project")
# Автоматически добавляет в ~/.bashrc, ~/.zshrc или Windows реестр
```

### Выполнение команд

**Старое (PowerShell):**
```powershell
subprocess.call(["powershell", "-ExecutionPolicy", "Bypass", "-File", "script.ps1"])
```

**Новое (кроссплатформенное Python):**
```python
from scripts.cli.utils import run_command, which

result = run_command(["python", "script.py"])

# Найти команду в PATH
python_path = which("python3")
```

## Файловая структура

### Новые директории

```
scripts/cli/
├── __init__.py              # Module CLI
├── assist.py                # Главный Python скрипт
├── paths.py                 # Кроссплатформенная система путей
├── config.py                # Управление конфигурацией
├── utils.py                 # Кроссплатформенные утилиты
├── installer.py             # (Планируется) Система установки
└── README.md                # Документация

launchers/
├── run.py                   # (Планируется) Запуск сервера
├── run_unicorn.py           # (Планируется) FastAPI через uvicorn
├── run_light_server.py      # (Планируется) Облегченный сервер
└── run_foundry.py           # (Планируется) Foundry запуск
```

### Обновленные файлы

```
install/
├── install.json             # ✅ Обновлен для кроссплатформенности
└── req/
    ├── requirements-core.txt    # ✅ Добавлены platformdirs, typer
    ├── requirements-ai.txt
    └── ...

config.json                 # ✅ Используется через ConfigManager

.env                        # ✅ Кроссплатформенный формат

assist.cmd                  # ✅ Обновлен (Windows)
assist                      # ✅ Новый (Linux/macOS)
assist_cross.ps1            # ✅ Новый (PowerShell обертка)
assist.ps1                  # ❌ Устарел, используйте assist_cross.ps1
```

## Миграция пользовательского кода

### Импорты

**Если вы использовали старые пути:**
```python
# Старое
from header import __root__
__root__ / ".assist_state"
__root__ / "venv" / "Scripts" / "python.exe"
```

**Новое:**
```python
# Новое
from scripts.cli.paths import get_paths

paths = get_paths()
paths.data_dir / "assist_state"
paths.venv_python  # Автоматически правильно для ОС
```

### Работа с конфигурацией

**Старое:**
```python
import json
with open("config.json", "r") as f:
    config = json.load(f)
```

**Новое:**
```python
from scripts.cli.config import get_config_manager

cfg = get_config_manager()
config = cfg.load_config()
port = cfg.get_config_value("server.port", 8000)
cfg.set_config_value("server.port", 8080)
```

### Управление процессами

**Старое (только Windows):**
```python
import subprocess
subprocess.run(["taskkill", "/PID", str(pid)])  # Только Windows
```

**Новое (кроссплатформенное):**
```python
from scripts.cli.utils import kill_process

kill_process(pid, force=True)  # Работает на Windows, Linux, macOS
```

## Установка на Linux

### Требования

```bash
# Ubuntu / Debian
sudo apt-get install python3.10-dev python3-pip python3-venv

# Fedora / RHEL
sudo dnf install python3-devel python3-pip python3-venv

# Arch
sudo pacman -S python python-pip
```

### Установка проекта

```bash
# 1. Клонировать репо
git clone https://github.com/hypo69/AI-Breadboard.git
cd AI-Breadboard

# 2. Создать виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Добавить assist в PATH (опционально)
chmod +x assist
sudo cp assist /usr/local/bin/assist

# 5. Тестировать
assist status
assist providers
```

### Первый запуск

```bash
# Проверить status
assist status

# Запустить сервер
assist start

# Показать логи
assist logs 50

# Остановить сервер
assist stop
```

## Проблемы и решения

### Python не найден

**Проблема:** `Python не найден` при запуске `assist`

**Решение:**
```bash
# 1. Убедитесь, что Python установлен
python3 --version

# 2. Или используйте полный путь
/usr/bin/python3 scripts/cli/assist.py start
```

### Порт уже занят

**Проблема:** `Address already in use`

**Решение:**
```bash
# Найти процесс
assist status

# Если сервер уже запущен, остановить его
assist stop

# Или использовать другой порт
assist config set server.port 8080
assist start
```

### Проблемы с путями на WSL

**Проблема:** Пути не правильно определены

**Решение:**
```bash
# Установить переменную окружения явно
export AIBREADBOARD_DIR="/home/user/AI-Breadboard"
assist status
```

## Обратная совместимость

Старые скрипты PowerShell остаются для совместимости:
- `assist.ps1` — используйте вместо этого `assist_cross.ps1` или `assist`
- `run.ps1` — используйте `assist start` вместо этого
- `install.ps1` — будет заменен на `install.py`

## Планы на будущее

- ✅ Фаза 1: Кроссплатформенная система путей и конфигурации
- 🔄 Фаза 2: Портирование всех лончеров (run.ps1 → run.py)
- 🔄 Фаза 3: Портирование системы установки (install.ps1 → install.py)
- 🔄 Фаза 4: MCP серверы кроссплатформенные
- 📋 Фаза 5: systemd user services для Linux
- 📋 Фаза 6: Docker контейнер для легкого развертывания

## Контакты и помощь

Если у вас есть вопросы по миграции или проблемы, создайте Issue на GitHub:
https://github.com/hypo69/AI-Breadboard/issues

## Дополнительная Info

- [Документация по scripts/cli/](./scripts/cli/README.md)
- [CrossPlatformPaths API](./scripts/cli/paths.py)
- [ConfigManager API](./scripts/cli/config.py)
- [Utils API](./scripts/cli/utils.py)
