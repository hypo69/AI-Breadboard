# AI Breadboard — Быстрый старт (Windows/Linux/macOS)

Портированный проект полностью поддерживает Windows, Linux и macOS. Инструкции одинаковые для всех платформ.

## 🚀 Установка (все платформы)

### Вариант 1: Автоматическая (рекомендуется)

**На Linux/macOS:**
```bash
chmod +x install.sh
bash install.sh --lang ru
```

**На Windows:**
```batch
install.cmd
```

### Вариант 2: Ручная через Python

**Все платформы:**
```bash
# Создать виртуальное окружение
python3 -m venv venv

# Активировать (выбрать для вашей ОС)
source venv/bin/activate          # Linux/macOS
venv\Scripts\activate.bat          # Windows

# Установить зависимости
pip install -r requirements.txt

# Запустить установщик
python scripts/cli/installer.py --lang ru
```

## 🎮 Первый запуск

### Через обертку (рекомендуется)

```bash
./run                    # Linux/macOS
run.cmd                  # Windows
```

Выберите Parameters интерактивно или используйте опции:
```bash
./run --host 0.0.0.0 --port 8000 --non-interactive
```

### Через Python напрямую

```bash
python launchers/run.py
```

## 📋 Основные команды

Используйте `assist` CLI:

```bash
# Показать status сервера
assist status

# Запустить сервер
assist start

# Остановить сервер
assist stop

# Показать конфигурацию
assist config show

# Получить значение конфига
assist config get server.port

# Установить значение конфига
assist config set server.port 8080

# Показать логи (последние 50 строк)
assist logs 50

# Запустить тесты
assist test

# Показать информацию о провайдерах
assist providers
```

## 🔧 Configuration

### .env файл (API ключи)

Создайте или отредактируйте файл `.env`:

```bash
# Gemini API ключи
GEMINI_API_KEY_NAMES=main
GEMINI_API_KEY_main=sk-your-key-here

# Другие Parameters (опционально)
USE_SSL=true
MODE=DEV
```

### config.json

Основная Configuration приложения. Пути автоматически определяются для вашей ОС.

Чтобы увидеть пути для вашей платформы:
```bash
python -c "from scripts.cli.paths import get_paths; p = get_paths(); print(f'Data: {p.data_dir}')"
```

## 🌐 Доступ к серверу

После запуска сервер будет доступен на:

```
http://localhost:8000          # API
http://localhost:8000/docs     # Swagger документация
http://localhost:8000/redoc    # ReDoc документация
```

## 📚 Документация

### Основные документы

- **[INSTALL_LINUX.md](./INSTALL_LINUX.md)** — Полная инструкция для Linux
- **[CONFIG.md](./CONFIG.md)** — Работа с конфигурацией
- **[MIGRATION_TO_LINUX.md](./MIGRATION_TO_LINUX.md)** — Миграция со старых скриптов
- **[PORTING_SUMMARY.md](./PORTING_SUMMARY.md)** — Итоги портирования

### Moduleная документация

- **[scripts/cli/README.md](./scripts/cli/README.md)** — Модули CLI
- **[scripts/cli/INSTALLER_README.md](./scripts/cli/INSTALLER_README.md)** — Установщик
- **[.mcp/README.md](./.mcp/README.md)** — MCP серверы
- **[systemd/README.md](./systemd/README.md)** — Linux systemd сервисы

## 🔌 systemd сервисы (Linux)

Для автоматического запуска при загрузке:

```bash
# Перейти в папку systemd
cd systemd

# Установить сервисы
bash install.sh

# Включить автозапуск
systemctl --user enable ai-breadboard-server.service

# Запустить
systemctl --user start ai-breadboard-server.service

# Просмотр логов
journalctl --user -u ai-breadboard-server.service -f
```

## 🐛 Проблемы и решения

### Python не найден
```bash
# Ubuntu/Debian
sudo apt-get install python3.10 python3.10-venv

# Fedora
sudo dnf install python3.10 python3.10-devel

# macOS
brew install python@3.10
```

### Permission denied на скриптах
```bash
chmod +x install.sh assist run systemd/install.sh
```

### Module не найден
```bash
# Переактивировать venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate.bat  # Windows

# Переустановить зависимости
pip install -r requirements.txt --force-reinstall
```

### Порт уже в использовании
```bash
# Использовать другой порт
./run --port 8001

# Или найти процесс на порту
lsof -i :8000  # Linux/macOS
netstat -ano | findstr :8000  # Windows
```

## 🔑 Ключевые особенности портирования

✅ **Кроссплатформенность**
- Windows, Linux, macOS поддерживаются полностью
- Одинаковые команды везде
- Пути автоматически адаптируются

✅ **Минимальная переработка**
- Только обертки переписаны на Python/Bash
- Логика осталась той же
- Совместимость с существующим кодом

✅ **Moduleная архитектура**
- Каждый лончер — отдельный скрипт
- Установщик поддерживает пропуск этапов
- Поддержка интернационализации (RU, EN, ES, HE)

✅ **Production-ready**
- systemd сервисы для Linux
- Логирование через journal
- Ограничения ресурсов (CPU, Memory)

## 📊 Структура проекта

```
AI-Breadboard/
├── scripts/cli/               # Кроссплатформенные Python модули
│   ├── assist.py             # Главный CLI
│   ├── paths.py              # Управление путями
│   ├── config.py             # Configuration
│   ├── utils.py              # Утилиты
│   └── installer.py          # Установщик
├── launchers/                 # Python лончеры
│   ├── run.py                # Главный лончер
│   ├── run_unicorn.py        # Unicorn сервер
│   ├── run_light_server.py   # Light режим
│   └── run_foundry.py        # Microsoft Foundry
├── systemd/                   # Linux сервисы
│   ├── *.service             # systemd service файлы
│   └── install.sh            # Установщик сервисов
├── .mcp/                      # MCP серверы (обновлены)
├── assist, run               # Bash обертки (Linux/macOS)
├── assist.cmd, run.cmd       # Batch обертки (Windows)
├── install.sh, install.cmd   # Установщики
├── config.json               # Configuration приложения
├── .env                       # API ключи и переменные
└── docs/                      # Документация

Нью компоненты:
- scripts/cli/               6 Python модулей
- systemd/                   4 service файла
- launchers/                 4 лончера
- Документация:              7+ markdown файлов
```

## 🚀 Следующие шаги

1. ✅ Прочитайте [INSTALL_LINUX.md](./INSTALL_LINUX.md) для полных инструкций
2. ✅ Создайте `.env` файл с вашими API ключами
3. ✅ Запустите сервер: `./run` (Linux/macOS) или `run.cmd` (Windows)
4. ✅ Проверьте status: `assist status`
5. ✅ На Linux: включите systemd сервис для автозапуска

## 📞 Контакты

- **GitHub Issues:** https://github.com/hypo69/AI-Breadboard/issues
- **GitHub Discussions:** https://github.com/hypo69/AI-Breadboard/discussions
- **Author:** hypo69@yandex.com

---

**Проект полностью готов к использованию на Windows, Linux и macOS!** 🎉

Все пути автоматически определяются. Команды одинаковые везде. Наслаждайтесь!
