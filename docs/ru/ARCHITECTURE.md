# Архитектура портирования AI Breadboard

Полное описание архитектуры кроссплатформенного решения.

## 📐 Общая архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface                           │
│  assist | assist.cmd | assist_cross.ps1 (CLI обертки)       │
│  run | run.cmd (Server обертки)                             │
│  install.sh | install.cmd (Install обертки)                │
└────────────┬────────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────────┐
│              Core Python Modules (scripts/cli/)             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │   assist.py  │ │  installer.py│ │    run*.py   │        │
│  │   (CLI)      │ │  (Installer) │ │  (Launchers) │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
│         │                │                │                  │
│         └────────────────┼────────────────┘                  │
│                          │                                   │
│         ┌────────────────▼────────────────┐                  │
│         │    Platform Abstraction Layer   │                  │
│         │  ┌──────┐  ┌──────┐  ┌──────┐  │                  │
│         │  │paths │  │config│  │utils │  │                  │
│         │  │ .py  │  │ .py  │  │ .py  │  │                  │
│         │  └──────┘  └──────┘  └──────┘  │                  │
│         └────────────────────────────────┘                  │
└────────────┬─────────────────────────────────────────────────┘
             │
┌────────────▼─────────────────────────────────────────────────┐
│              OS-Specific Execution Layer                     │
│  ┌──────────────────┐ ┌──────────────────┐                   │
│  │    Windows       │ │   Linux/macOS    │                   │
│  │  ┌────────────┐  │ │  ┌────────────┐  │                   │
│  │  │subprocess  │  │ │  │subprocess  │  │                   │
│  │  │socket      │  │ │  │socket      │  │                   │
│  │  │configparser│  │ │  │.env parser │  │                   │
│  │  └────────────┘  │ │  │systemd     │  │                   │
│  └──────────────────┘ │  └────────────┘  │                   │
│                       └──────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

## 🗂️ Слои архитектуры

### Слой 1: User Interface (Обертки)

**Назначение:** Предоставить единый интерфейс для всех платформ

**Компоненты:**
- `assist` (Linux/macOS bash обертка)
- `assist.cmd` (Windows batch обертка)
- `assist_cross.ps1` (PowerShell обертка для совместимости)
- `run`, `run.cmd` (Server обертки)
- `install.sh`, `install.cmd` (Installer обертки)

**Ответственность:**
- Обнаружение Python интерпретатора (venv или глобальный)
- Установка переменных окружения (AIBREADBOARD_DIR, PYTHONPATH)
- Вызов Python модулей

**Преимущества:**
- ✅ Пользователь видит одинаковые команды везде
- ✅ Автоматическая адаптация к окружению
- ✅ Обработка ошибок на уровне оберток

### Слой 2: Core Python Modules

**Назначение:** Реализовать основную функциональность кроссплатформенно

**Компоненты:**

#### `assist.py` — Главный CLI (2500+ строк)
```python
# Команды
assist start      # Запустить сервер
assist stop       # Остановить сервер
assist status     # Показать status
assist config ...  # Управление конфигурацией
assist logs ...    # Показать логи
assist test        # Запустить тесты
assist providers   # Показать провайдеров
```

Использует все модули platform abstraction layer:
- `paths.get_paths()` — получить кроссплатформенные пути
- `config.get_config_manager()` — получить конфиг
- `utils.*` — кроссплатформенные утилиты

#### `installer.py` — Moduleный установщик
```python
# Этапы установки
1. Check Python
2. Создание venv
3. Установка зависимостей (pip)
4. Генерация SSL сертификатов
5. Установка CLI в PATH
6. Check установки
7. Loading моделей (опционально)
```

Поддерживает:
- Пропуск этапов: `--skip-venv`, `--skip-deps`, `--skip-ssl`, `--skip-models`
- Выбор языка: `--lang ru|en|es|he`
- Выбор директории: `--install-dir /path`

#### `run*.py` — Лончеры серверов
```python
launchers/
├── run.py                 # Главный (интерактивный)
├── run_unicorn.py         # uvicorn специализированный
├── run_light_server.py    # облегченный режим
└── run_foundry.py         # Microsoft Foundry
```

Каждый поддерживает:
- Интерактивный режим (выбор параметров)
- CLI Parameters: `--host`, `--port`, `--non-interactive`
- Автоматическое обнаружение свободного порта

### Слой 3: Platform Abstraction Layer

**Назначение:** Скрыть различия между платформами за единым интерфейсом

**Компоненты:**

#### `paths.py` — Управление путями
```python
class CrossPlatformPaths:
    data_dir: Path        # Данные приложения
    config_dir: Path      # Configuration
    cache_dir: Path       # Кэш
    certs_dir: Path       # SSL сертификаты
    bin_dir: Path         # Бинарники
```

**Логика определения:**
1. Проверить `AIBREADBOARD_DIR` переменную окружения
2. Найти `config.json` или `main.py` в текущей директории
3. Использовать `platformdirs` для OS-специфичных путей
4. Fallback на текущую директорию

**Пути по платформам:**

| Platform | data_dir | config_dir | certs_dir |
|----------|----------|-----------|-----------|
| Windows | `%LOCALAPPDATA%\AI-Breadboard` | `%LOCALAPPDATA%\AI-Breadboard\config` | `%USERPROFILE%\.certs` |
| Linux | `~/.local/share/AI-Breadboard` | `~/.config/AI-Breadboard` | `~/.local/share/ca-certificates` |
| macOS | `~/Library/Application Support/AI-Breadboard` | `~/Library/Preferences/AI-Breadboard` | `~/Library/Certs` |

#### `config.py` — Управление конфигурацией
```python
class ConfigManager:
    def load_config() -> dict
    def get_config_value(key: str, default=None) -> Any
    def set_config_value(key: str, value: Any) -> None
    def get_env_var(key: str, default=None) -> str
    def set_env_var(key: str, value: str) -> None
```

**Источники конфигурации (приоритет):**
1. Переменные окружения системы
2. Файл `.env`
3. Файл `config.json`
4. Значения по умолчанию

**Использование:**
```python
cfg = get_config_manager()
port = cfg.get_config_value("server.port", 8000)
cfg.set_env_var("API_KEY", "secret")
```

#### `utils.py` — Кроссплатформенные утилиты
```python
def find_available_port(start_port=8000) -> int
def is_port_open(host: str, port: int) -> bool
def kill_process(pid: int, force: bool = False) -> bool
def get_system_info() -> dict
def get_python_executable() -> Path
def add_to_path(directory: Path) -> None
```

### Слой 4: OS-Specific Execution

**Назначение:** Выполнить операции специфичные для ОС

**Компоненты:**
- `subprocess.Popen()` — запуск процессов (кроссплатформенно)
- `socket` Module — check портов (кроссплатформенно)
- `configparser` + `pathlib` — работа с файлами (кроссплатформенно)
- `systemd` сервисы — автозапуск на Linux (Linux специфичный)

## 🔄 Поток выполнения

### Пример 1: `assist start`

```
1. User: assist start
   ↓
2. assist (bash обертка)
   - Найти Python интерпретатор
   - Установить AIBREADBOARD_DIR
   - Вызвать: python scripts/cli/assist.py start
   ↓
3. assist.py:main()
   - Парсить аргументы
   - Вызвать: cmd_start()
   ↓
4. cmd_start()
   - Получить пути: get_paths()
   - Получить конфиг: get_config_manager()
   - Найти свободный порт: find_available_port()
   - Запустить сервер: subprocess.Popen()
   - Записать PID в файл
   ↓
5. Сервер запущен на http://localhost:8000
```

### Пример 2: `install.sh`

```
1. User: bash install.sh --lang ru
   ↓
2. install.sh (bash обертка)
   - Проверить Python
   - Вызвать: python scripts/cli/installer.py --lang ru
   ↓
3. installer.py:main()
   - Инициализировать установщик
   - Вызвать: run_installation()
   ↓
4. run_installation()
   - Этап 1: Check Python version
   - Этап 2: Создание venv (python -m venv)
   - Этап 3: Установка зависимостей (pip install)
   - Этап 4: Генерация SSL сертификатов
   - Этап 5: Добавление CLI в PATH
   - Этап 6: Check установки
   - Этап 7: Loading моделей (опционально)
   ↓
5. Установка завершена
```

## 🌍 Кроссплатформенность — Как это работает

### Пример: Получение пути к данным

```python
# Код одинаковый везде
from scripts.cli.paths import get_paths

paths = get_paths()
data_dir = paths.data_dir

# Результат разный для каждой ОС:
# Windows: Path("C:\\Users\\user\\AppData\\Local\\AI-Breadboard")
# Linux:   Path("/home/user/.local/share/AI-Breadboard")
# macOS:   Path("/Users/user/Library/Application Support/AI-Breadboard")
```

**Магия:**
1. `pathlib.Path` работает везде
2. `/` оператор работает везде (переводится в `\` на Windows)
3. `~` расширяется везде
4. `platformdirs` знает OS-специфичные пути

### Пример: Запуск процесса

```python
# Код одинаковый везде
import subprocess

proc = subprocess.Popen(
    [python_exe, "main.py"],
    cwd=project_dir,
    env=env_vars
)
pid = proc.pid

# Работает везде благодаря:
# - subprocess использует native OS API
# - Не нужны ни WinAPI, ни POSIX вызовы напрямую
```

## 🔌 Integration компонентов

### Зависимости между модулями

```
assist.py
  ├── depends: paths.py, config.py, utils.py
  └── используется: все команды (start, stop, config, etc)

installer.py
  ├── depends: paths.py, config.py, utils.py
  └── этапы установки (venv, pip, ssl, path, check, models)

run.py / run_*.py
  ├── depends: paths.py, config.py, utils.py
  └── launchers для FastAPI, Unicorn, Light, Foundry

paths.py
  ├── depends: pathlib (stdlib), platformdirs (pip)
  └── используется: assist.py, installer.py, run*.py

config.py
  ├── depends: json (stdlib), pathlib (stdlib), paths.py
  └── используется: assist.py, installer.py, run*.py

utils.py
  ├── depends: subprocess (stdlib), socket (stdlib), pathlib (stdlib)
  └── используется: assist.py, installer.py, run*.py
```

## 🎯 Ключевые решения архитектуры

### 1. Почему Python модули, а не shell скрипты?

**Преимущества Python:**
- ✅ Кроссплатформенность (windows/linux/macos)
- ✅ Лучше читаемость и поддерживаемость
- ✅ Встроенные модули для сложной логики
- ✅ Лучше обработка ошибок
- ✅ Простой синтаксис

**Недостатки shell:**
- ❌ Разные синтаксисы (bash vs cmd vs PowerShell)
- ❌ Сложнее обработка ошибок
- ❌ Сложнее работа с JSON/конфигом
- ❌ Медленнее

### 2. Почему отдельные обертки (bash/batch)?

**Преимущества:**
- ✅ Пользователь видит привычные команды
- ✅ Автоматическое обнаружение окружения
- ✅ Установка переменных окружения
- ✅ Обработка Path к Python

**Пример проблемы:**
```python
# Без обертки пользователь должен делать:
python3 scripts/cli/assist.py start

# С оберткой:
assist start
```

### 3. Почему платформо-абстрактный слой?

**Преимущества:**
- ✅ Один код работает везде
- ✅ Нет `if platform == "Windows"` по всему коду
- ✅ Легко добавить поддержку новых платформ
- ✅ Легко тестировать

**Пример:**
```python
# Плохо (разбросано по коду)
if os.name == 'nt':
    venv_path = Path(f"{project}\\venv\\Scripts\\python.exe")
else:
    venv_path = Path(f"{project}/venv/bin/python")

# Хорошо (в одном месте)
paths = get_paths()
venv_python = paths.venv_python
```

## 🔐 Безопасность

### 1. Управление API ключами

```
config.json (public)          → Отсутствуют ключи
.env (gitignored)             → Все ключи здесь
Переменные окружения          → System-level (не git)
```

### 2. Управление путями

- ✅ Используется `pathlib.Path` (безопасно от injection)
- ✅ Нет string concatenation для путей
- ✅ Пути в пределах проекта

### 3. Процессы

- ✅ Используется `subprocess.Popen()` (не shell=True)
- ✅ Аргументы как list (не string)
- ✅ Переменные окружения явно установлены

## 🚀 Production readiness

### На Windows

- ✅ batch установщик
- ✅ batch обертки для команд
- ✅ Полная поддержка venv

### На Linux

- ✅ bash установщик и обертки
- ✅ systemd user services (автозапуск)
- ✅ journalctl логирование

### На macOS

- ✅ bash установщик и обертки (как Linux)
- ✅ launchd поддержка (опционально)

## 📊 Статистика кода

```
scripts/cli/
  ├── paths.py:       ~400 строк
  ├── config.py:      ~300 строк
  ├── utils.py:       ~250 строк
  ├── assist.py:      ~2500 строк
  └── installer.py:   ~1000 строк
  Total:              ~4450 строк

launchers/
  ├── run.py:         ~400 строк
  ├── run_unicorn.py: ~250 строк
  ├── run_light_server.py: ~200 строк
  └── run_foundry.py: ~200 строк
  Total:              ~1050 строк

Обертки:
  ├── bash:           ~300 строк (assist, run, install.sh)
  └── batch:          ~300 строк (assist.cmd, run.cmd, install.cmd)
  Total:              ~600 строк

systemd:
  ├── *.service:      ~200 строк
  └── install.sh:     ~150 строк
  Total:              ~350 строк

Grand Total:         ~6450 строк кода
```

## 🎓 Examples использования архитектуры

### Пример: Добавить новую команду в CLI

```python
# 1. Добавить в assist.py
def cmd_mycommand(args):
    """Новая команда"""
    paths = get_paths()           # Получить пути
    cfg = get_config_manager()    # Получить конфиг
    
    # Выполнить логику
    value = cfg.get_config_value("my.setting")
    
    # Использовать абстрактные компоненты
    port = find_available_port()
    
    return True

# 2. Добавить в main()
parser.add_parser('mycommand', help='Моя команда')

# 3. Готово! Работает везде
assist mycommand
```

### Пример: Добавить новый лончер

```python
# launchers/run_new_server.py
from scripts.cli.paths import get_paths
from scripts.cli.config import get_config_manager
from scripts.cli.utils import find_available_port

paths = get_paths()
cfg = get_config_manager()
port = find_available_port(8000)

# Запустить новый сервер
# Код написан один раз, работает везде
```

---

## Выводы

✅ **Архитектура портирования:**
- Moduleная и расширяемая
- Полностью кроссплатформенная
- Production-ready
- Легко тестируемая
- Хорошо документирована

✅ **Слои:**
1. User Interface (обертки)
2. Core Modules (Python)
3. Platform Abstraction (paths, config, utils)
4. OS-Specific Execution (subprocess, socket, etc)

✅ **Результат:**
- Один код работает везде
- Пользователь видит одинаковые команды
- Минимальная переработка исходного кода
- Готово к production использованию
