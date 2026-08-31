# systemd User Services для AI Breadboard (Linux)

Этот набор systemd user services позволяет автоматически запускать компоненты AI Breadboard при загрузке системы.

## Поддерживаемые сервисы

| Сервис | Название | Назначение |
|--------|----------|-----------|
| `ai-breadboard-server.service` | FastAPI Server | Главный веб-сервер приложения |
| `ai-breadboard-mcp-langchain.service` | MCP LangChain Agent | Агент с поддержкой RAG и web search |
| `ai-breadboard-mcp-gemini.service` | MCP Gemini Search | Поиск через Google Gemini API |
| `ai-breadboard-foundry.service` | Microsoft Foundry | Локальный LLM сервер (если установлен) |

## Установка

### 1. Копировать сервисы в ~/.config/systemd/user/

```bash
# Создать директорию если её нет
mkdir -p ~/.config/systemd/user/

# Копировать сервис-файлы
cp systemd/*.service ~/.config/systemd/user/

# Или использовать скрипт установки
bash systemd/install.sh
```

### 2. Перезагрузить systemd daemon

```bash
systemctl --user daemon-reload
```

### 3. Включить автозапуск (опционально)

```bash
# Включить сервис при загрузке
systemctl --user enable ai-breadboard-server.service

# Включить несколько сервисов
systemctl --user enable ai-breadboard-server.service ai-breadboard-mcp-langchain.service
```

### 4. Запустить сервис

```bash
# Запустить FastAPI сервер
systemctl --user start ai-breadboard-server.service

# Запустить MCP LangChain агент
systemctl --user start ai-breadboard-mcp-langchain.service

# Запустить все сервисы сразу
systemctl --user start ai-breadboard-server.service ai-breadboard-mcp-langchain.service ai-breadboard-mcp-gemini.service
```

## Управление сервисами

### Проверить status

```bash
# Status одного сервиса
systemctl --user status ai-breadboard-server.service

# List всех сервисов AI Breadboard
systemctl --user list-units | grep ai-breadboard

# List всех включенных сервисов
systemctl --user list-unit-files | grep ai-breadboard
```

### Просмотр логов

```bash
# Логи FastAPI сервера (последние 50 строк)
journalctl --user -u ai-breadboard-server.service -n 50

# Логи в реальном времени
journalctl --user -u ai-breadboard-server.service -f

# Логи всех сервисов за последний час
journalctl --user --since "1 hour ago" | grep ai-breadboard
```

### Остановка и переLoading

```bash
# Остановить сервис
systemctl --user stop ai-breadboard-server.service

# Перезагрузить сервис
systemctl --user restart ai-breadboard-server.service

# Перезагрузить конфигурацию (если изменили .service файл)
systemctl --user daemon-reload
systemctl --user restart ai-breadboard-server.service

# Остановить все сервисы
systemctl --user stop ai-breadboard-*.service
```

### Отключить автозапуск

```bash
systemctl --user disable ai-breadboard-server.service
```

## Настройка путей

По умолчанию сервисы ожидают установку в `~/AI-Breadboard/`.

Если установка в другой директории, отредактируйте файлы `.service`:

```bash
# Отредактировать сервис
nano ~/.config/systemd/user/ai-breadboard-server.service

# Измените:
# WorkingDirectory=%h/AI-Breadboard
# На нужную директорию

# Перезагрузить systemd
systemctl --user daemon-reload
```

## Parameters сервисов

### Type=simple vs Type=notify

- `simple` — сервис запускается и работает в фоне
- `notify` — сервис sends уведомление systemd о готовности (требуется python-systemd)

### Restart=on-failure

Сервис будет автоматически перезагружен если упадет с кодом ошибки.

### RestartSec=10

Задержка в 10 секунд перед перезагрузкой после сбоя.

### Ограничения ресурсов

Раскомментируйте в `ai-breadboard-server.service`:

```ini
# Максимум памяти: 2GB
MemoryLimit=2G

# CPU квота: 50% одного ядра
CPUQuota=50%
```

## Examples использования

### Пример 1: Автозапуск FastAPI сервера при загрузке

```bash
# Включить автозапуск
systemctl --user enable ai-breadboard-server.service

# Проверить status
systemctl --user status ai-breadboard-server.service

# Просмотр логов при загрузке
journalctl --user -u ai-breadboard-server.service -f
```

### Пример 2: Запуск нескольких сервисов

```bash
# Запустить FastAPI сервер и MCP агенты
systemctl --user start ai-breadboard-server.service
systemctl --user start ai-breadboard-mcp-langchain.service
systemctl --user start ai-breadboard-mcp-gemini.service

# Проверить что все работают
systemctl --user status ai-breadboard-*.service
```

### Пример 3: Мониторинг в реальном времени

```bash
# Видеть логи всех сервисов в реальном времени
journalctl --user -f | grep ai-breadboard
```

## Проблемы и решения

### "Failed to start service: Permission denied"

```bash
# Убедитесь, что файлы `.service` имеют правильные права доступа
ls -la ~/.config/systemd/user/ai-breadboard-*.service
# Должны быть: -rw-r--r--

# Установить правильные права
chmod 644 ~/.config/systemd/user/ai-breadboard-*.service
```

### Сервис не запускается

```bash
# Проверить логи
journalctl --user -u ai-breadboard-server.service -n 20

# Проверить синтаксис файла .service
systemd-analyze verify ~/.config/systemd/user/ai-breadboard-server.service

# Проверить что Python доступен
~/.config/systemd/user/ai-breadboard-server.service --user exec /home/user/AI-Breadboard/venv/bin/python --version
```

### "Service cannot access data directory"

Убедитесь что:
1. Директория AI-Breadboard существует
2. Пользователь имеет права доступа к директории
3. Путь в `.service` файле правильный

```bash
# Проверить что директория существует
test -d ~/AI-Breadboard && echo "OK" || echo "NOT FOUND"

# Проверить права доступа
ls -ld ~/AI-Breadboard
# Должно быть: drwxr-xr-x

# Если нет, установить права
chmod 755 ~/AI-Breadboard
```

## Дополнительная Info

### Документация systemd

- [systemd.service(5)](https://man7.org/linux/man-pages/man5/systemd.service.5.html)
- [systemd User Services](https://wiki.archlinux.org/title/Systemd/User)
- [systemd.unit(5)](https://man7.org/linux/man-pages/man5/systemd.unit.5.html)

### Команды systemctl

```bash
# Основные команды
systemctl --user start <service>           # Запустить
systemctl --user stop <service>            # Остановить
systemctl --user restart <service>         # Перезагрузить
systemctl --user reload <service>          # Перезагрузить конфигурацию
systemctl --user status <service>          # Status
systemctl --user enable <service>          # Включить автозапуск
systemctl --user disable <service>         # Отключить автозапуск
systemctl --user is-active <service>       # Проверить активен ли
systemctl --user is-enabled <service>      # Проверить включен ли автозапуск
systemctl --user list-units --all          # List всех юнитов
systemctl --user list-unit-files           # List всех юнит-файлов
systemctl --user daemon-reload             # Перезагрузить daemon

# Логи
journalctl --user -u <service>             # Логи сервиса
journalctl --user -u <service> -n 50       # Последние 50 строк
journalctl --user -u <service> -f          # Логи в реальном времени
journalctl --user --since "1 hour ago"     # Логи за час
```

### Timer сервисы

Можно создать timer сервисы для периодического запуска задач:

```bash
# Создать файл ai-breadboard-cleanup.timer
[Unit]
Description=AI Breadboard Cleanup Timer
Requires=ai-breadboard-cleanup.service

[Timer]
OnBootSec=10min
OnUnitActiveSec=24h
Persistent=true

[Install]
WantedBy=timers.target
```

## Контакты

Если у вас есть вопросы или проблемы:
- GitHub Issues: https://github.com/hypo69/AI-Breadboard/issues
- GitHub Discussions: https://github.com/hypo69/AI-Breadboard/discussions
