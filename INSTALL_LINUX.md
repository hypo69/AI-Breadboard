# Установка AI Breadboard на Linux

Полное руководство по установке AI Breadboard на Linux (Ubuntu, Debian, Fedora, Arch и другие дистрибутивы).

## Требования

### Минимальные требования
- **ОС:** Linux (любой современный дистрибутив)
- **Python:** 3.10 или выше
- **RAM:** 2GB (рекомендуется 4GB+)
- **Диск:** 5GB свободного места (для venv и моделей)
- **Сеть:** Интернет для загрузки зависимостей

### Проверить Python

```bash
# Проверить версию Python
python3 --version
# Должно быть: Python 3.10.x или выше

# Если Python не установлен, см. раздел "Установка Python"
```

## Шаг 1: Установка Python

### Ubuntu / Debian

```bash
# Обновить индекс пакетов
sudo apt-get update

# Установить Python 3.10+
sudo apt-get install python3.10 python3.10-dev python3.10-venv python3-pip

# Установить необходимые пакеты
sudo apt-get install git curl build-essential libssl-dev libffi-dev
```

### Fedora / RHEL / CentOS

```bash
# Установить Python 3.10+
sudo dnf install python3.10 python3.10-devel python3.10-venv python3-pip

# Установить необходимые пакеты
sudo dnf install git curl gcc libssl-devel libffi-devel
```

### Arch Linux

```bash
# Установить Python и необходимые пакеты
sudo pacman -S python python-pip git base-devel

# Python уже 3.11+ на Arch
```

### openSUSE

```bash
# Установить Python 3.10+
sudo zypper install python310 python310-devel python310-venv python3-pip

# Установить необходимые пакеты
sudo zypper install git gcc libssl-devel libffi-devel
```

## Шаг 2: Клонировать репозиторий

```bash
# Клонировать репо
git clone https://github.com/hypo69/AI-Breadboard.git

# Перейти в директорию проекта
cd AI-Breadboard
```

## Шаг 3: Запустить установщик

### Вариант A: Автоматическая установка (рекомендуется)

```bash
# Сделать скрипт исполняемым
chmod +x install.sh

# Запустить установку (по умолчанию на английском)
./install.sh

# Или на русском языке
./install.sh --lang ru

# С установкой в пользовательскую директорию
./install.sh --lang ru --install-dir ~/.ai-breadboard
```

### Вариант B: Установка через Python напрямую

```bash
# Установка на английском
python3 scripts/cli/installer.py

# Установка на русском
python3 scripts/cli/installer.py --lang ru

# Пропустить загрузку моделей
python3 scripts/cli/installer.py --skip-models
```

## Шаг 4: Активировать виртуальное окружение

```bash
# Активировать venv
source venv/bin/activate

# Проверить что активирован (должен быть префикс (venv))
which python
```

## Шаг 5: Первый запуск

### Запустить FastAPI сервер

```bash
# Интерактивный запуск
python launchers/run.py

# Или использовать bash обертку
./run

# Или с конкретными параметрами
python launchers/run.py --host 127.0.0.1 --port 8000 --non-interactive
```

### Тестировать сервер

```bash
# В другом терминале проверить status
assist status

# Или напрямую
curl http://localhost:8000/docs
```

## Шаг 6: Configuration (опционально)

### Создать .env файл

```bash
# Скопировать пример (если существует)
cp .env.example .env

# Отредактировать .env файл с API ключами
nano .env
```

### Стандартные переменные

```bash
# Gemini API ключи
GEMINI_API_KEY_NAMES=key1,key2
GEMINI_API_KEY_key1=sk-...
GEMINI_API_KEY_key2=sk-...

# Parameters сервера
USE_SSL=true
MODE=DEV
```

## Дополнительные конфигурации

### Настроить systemd сервисы (автозапуск)

```bash
# Перейти в папку systemd
cd systemd

# Сделать скрипт исполняемым
chmod +x install.sh

# Установить systemd сервисы
./install.sh

# Включить автозапуск
systemctl --user enable ai-breadboard-server.service

# Запустить сервис
systemctl --user start ai-breadboard-server.service
```

### Проверить логи systemd

```bash
# Логи FastAPI сервера
journalctl --user -u ai-breadboard-server.service -f

# Логи за последний час
journalctl --user --since "1 hour ago" | grep ai-breadboard
```

### Добавить `assist` в PATH (опционально)

```bash
# Если не добавилось автоматически
sudo ln -s $(pwd)/assist /usr/local/bin/assist

# Или для пользовательского уровня
mkdir -p ~/.local/bin
ln -s $(pwd)/assist ~/.local/bin/assist

# Добавить ~/.local/bin в PATH (если не добавлено)
echo 'export PATH="~/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## Check установки

### Базовые проверки

```bash
# 1. Проверить Python в venv
python --version
# Должно быть: Python 3.10.x или выше

# 2. Проверить модули
python -c "import fastapi, uvicorn, dotenv; print('OK')"

# 3. Проверить assist команду
assist status
# Должен показать status сервера

# 4. Проверить путь проекта
echo $AIBREADBOARD_DIR
# Должен показать путь до AI-Breadboard
```

### Запустить тесты (если есть)

```bash
# Активировать venv
source venv/bin/activate

# Запустить тесты
assist test

# Или напрямую через pytest
python -m pytest tests/
```

## Examples использования

### Пример 1: Простой запуск сервера

```bash
# Перейти в директорию проекта
cd ~/AI-Breadboard

# Активировать venv
source venv/bin/activate

# Запустить сервер
python launchers/run.py

# Сервер будет доступен на http://localhost:8000
```

### Пример 2: Запуск с пользовательским портом

```bash
# Запустить на порту 9000
python launchers/run.py --host 0.0.0.0 --port 9000
```

### Пример 3: Работа с CLI

```bash
# Показать status
assist status

# Запустить сервер
assist start

# Остановить сервер
assist stop

# Показать конфигурацию
assist config show

# Получить значение
assist config get server.port

# Установить значение
assist config set server.port 9000

# Показать логи
assist logs 50
```

### Пример 4: Запуск MCP серверов

```bash
# Запустить LangChain MCP сервер
python .mcp/langchain_mcp_server.py

# Запустить Gemini Search MCP сервер
python .mcp/gemini_search_mcp_server.py

# Запустить FastAPI MCP клиент
python .mcp/fastapi_mcp_server.py
```

## Проблемы и решения

### Проблема: "Python не найден"

```bash
# Решение: Установить Python
sudo apt-get install python3.10  # Debian/Ubuntu
sudo dnf install python3.10      # Fedora

# Или использовать полный путь
/usr/bin/python3.10 scripts/cli/installer.py
```

### Проблема: "Permission denied"

```bash
# Решение: Дать права на исполнение
chmod +x install.sh
chmod +x assist
chmod +x run
chmod +x systemd/install.sh
```

### Проблема: "Module не найден"

```bash
# Решение 1: Установить модули
pip install -r requirements.txt

# Решение 2: Убедиться что в venv
source venv/bin/activate
which python  # Должно показать .../venv/bin/python

# Решение 3: Переустановить
pip install -r requirements.txt --force-reinstall
```

### Проблема: "Порт уже в использовании"

```bash
# Найти процесс на порту
lsof -i :8000

# Завершить процесс
kill -9 <PID>

# Или использовать другой порт
python launchers/run.py --port 8001
```

### Проблема: "SSL сертификаты не найдены"

```bash
# Решение: Установить mkcert
sudo apt-get install mkcert          # Debian/Ubuntu
sudo dnf install mkcert              # Fedora

# Или использовать Python для генерации
python scripts/cli/installer.py
# Выберите "3" для установки сертификатов
```

### Проблема: "systemd сервис не запускается"

```bash
# Проверить status
systemctl --user status ai-breadboard-server.service

# Показать логи ошибок
journalctl --user -u ai-breadboard-server.service -n 20

# Проверить синтаксис файла .service
systemd-analyze verify ~/.config/systemd/user/ai-breadboard-server.service

# Переустановить сервисы
cd systemd
bash install.sh
systemctl --user daemon-reload
```

## Update

### Обновить код из репозитория

```bash
# Перейти в директорию проекта
cd ~/AI-Breadboard

# Обновить код
git pull origin master

# Обновить зависимости
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Переустановить если были большие изменения
./install.sh --skip-venv
```

## Следующие шаги

1. ✅ Установка завершена!
2. 📖 Прочитайте [CONFIG.md](./CONFIG.md) для конфигурации
3. 📖 Прочитайте [MIGRATION_TO_LINUX.md](./MIGRATION_TO_LINUX.md) для деталей портирования
4. 🚀 Запустите сервер: `./run`
5. 📝 Создайте `.env` файл с API ключами
6. 🔧 Настройте systemd сервисы для автозапуска (опционально)
7. 📚 Изучите [README.md](./README.md) для полной документации

## Контакты

Если у вас есть вопросы или проблемы:
- GitHub Issues: https://github.com/hypo69/AI-Breadboard/issues
- GitHub Discussions: https://github.com/hypo69/AI-Breadboard/discussions
- Email: hypo69@yandex.com (автор проекта)

## Лицензия

Проект распространяется под лицензией [MIT](./LICENSE).

---

**Первая установка завершена!** 🎉

Проект готов к использованию. Начните с запуска:
```bash
./run
```

Сервер будет доступен на `http://localhost:8000`
