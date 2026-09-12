# Кроссплатформенный установщик AI Breadboard

Новая система установки на Python, заменяющая старые PowerShell скрипты.

## Возможности

- ✅ Windows, Linux, macOS поддержка
- ✅ Moduleная архитектура
- ✅ Интернационализация (RU, EN, ES, HE)
- ✅ Автоматическое определение путей
- ✅ Гибкие опции установки
- ✅ Check зависимостей

## Использование

### Linux / macOS

```bash
# Сделать скрипт исполняемым
chmod +x install.sh

# Запустить установку (по умолчанию на английском)
./install.sh

# Установка на русском языке
./install.sh --lang ru

# Установка в пользовательскую директорию
./install.sh --install-dir /opt/ai-breadboard

# Пропустить загрузку моделей
./install.sh --skip-models

# Все Parameters сразу
./install.sh --lang ru --install-dir ~/.ai-breadboard --skip-models
```

### Windows

```batch
# Запустить установку
install.cmd

# Или через PowerShell
python scripts\cli\installer.py

# С параметрами
python scripts\cli\installer.py --lang ru --skip-models
```

### Python (кроссплатформенно)

```bash
# Или просто использовать Python напрямую
python scripts/cli/installer.py

# С помощью Python (работает везде)
python scripts/cli/installer.py --lang en
python scripts/cli/installer.py --lang ru --install-dir /custom/path
```

## Parameters

```
--lang {en|ru|es|he}       Язык установки (по умолчанию: en)
--install-dir PATH         Директория установки (по умолчанию: ~/AI-Breadboard)
--skip-models             Пропустить загрузку моделей ИИ
--skip-venv               Пропустить создание виртуального окружения
--skip-deps               Пропустить установку зависимостей
--skip-certs              Пропустить настройку SSL сертификатов
```

## Что происходит во время установки?

1. **Создание venv** — Python виртуальное окружение
2. **Установка зависимостей** — FastAPI, Uvicorn, LLM библиотеки и т.д.
3. **SSL сертификаты** — Генерация сертификатов для HTTPS
4. **CLI Configuration** — Добавление `assist` команды в PATH
5. **Check** — Верификация всех компонентов
6. **Модели** — Loading моделей ИИ (опционально)

## Структура директории после установки

```
~/AI-Breadboard/
├── venv/                    # Виртуальное окружение Python
├── launchers/               # Лончеры (run.py, etc)
├── scripts/
│   ├── cli/                 # CLI утилиты
│   └── dev/                 # Dev скрипты
├── core/                    # Основные модули
├── tests/                   # Тесты
├── config.json              # Configuration
├── .env                     # Переменные окружения
├── assist                   # CLI ассистент (Linux/macOS)
├── assist.cmd               # CLI ассистент (Windows)
├── run.py                   # Лончер сервера
├── main.py                  # FastAPI приложение
└── requirements.txt         # Зависимости
```

## Переменные окружения

После установки можно использовать:

```bash
# Автоматически добавлено в ~/.bashrc / ~/.zshrc
export AIBREADBOARD_DIR=/home/user/AI-Breadboard
export PYTHONPATH=$AIBREADBOARD_DIR

# Теперь можно использовать assist откуда угодно
assist status
assist start
```

## Пример полной установки

```bash
# 1. Клонировать репо
git clone https://github.com/hypo69/AI-Breadboard.git
cd AI-Breadboard

# 2. Запустить установщик (на русском)
chmod +x install.sh
./install.sh --lang ru

# 3. Активировать venv (опционально, если не автоматизировано)
source venv/bin/activate

# 4. Запустить сервер
python run.py

# 5. Или использовать assist команду
assist start
```

## Проблемы и решения

### Python не найден

```bash
# Убедитесь, что Python 3.10+ установлен
python3 --version

# Если не установлен:
# Linux (Debian/Ubuntu):
sudo apt-get install python3.10 python3.10-dev python3.10-venv

# Linux (Fedora/RHEL):
sudo dnf install python3.10 python3.10-devel

# macOS (с Homebrew):
brew install python@3.10

# Windows:
# Скачайте с https://www.python.org/downloads/
```

### Error "Permission denied" на Linux

```bash
chmod +x install.sh
chmod +x assist
chmod +x run
```

### Error при установке pip пакетов

```bash
# Обновить pip
python3 -m pip install --upgrade pip

# Установить wheel и setuptools
python3 -m pip install wheel setuptools

# Затем повторить установку
./install.sh
```

### Проблемы с SSL сертификатами

```bash
# Установить mkcert (опционально, для самоподписанных сертификатов)

# macOS:
brew install mkcert

# Linux (Debian):
sudo apt-get install mkcert

# Windows (с Choco):
choco install mkcert

# Затем переустановить:
./install.sh
```

## Структура кода установщика

```
scripts/cli/
├── installer.py           # Главный установщик
├── paths.py               # Управление путями
├── config.py              # Управление конфигурацией
└── utils.py               # Утилиты (pip, venv, etc)
```

## Миграция со старого install.ps1

**Старое:**
```powershell
# Только Windows
.\install.ps1

# Специфичные для Windows пути
$env:LOCALAPPDATA\AI Breadboard
```

**Новое:**
```bash
# Работает везде
./install.sh          # Linux/macOS
install.cmd           # Windows
python scripts/cli/installer.py  # Везде

# Автоматически выбирает правильные пути для ОС
```

## Дополнительная Info

- [CrossPlatformPaths](./paths.py) — система управления путями
- [ConfigManager](./config.py) — управление конфигурацией
- [Utils](./utils.py) — кроссплатформенные утилиты

## Контакты

Если у вас есть вопросы или проблемы при установке:
- Создайте Issue: https://github.com/hypo69/AI-Breadboard/issues
- Обсудите в Discussions: https://github.com/hypo69/AI-Breadboard/discussions
