# Решение проблем

Здесь собраны типичные ошибки и способы их устранения. Если проблема не описана — смотрите логи и открывайте issue на GitHub.

---

## PowerShell: «выполнение скриптов отключено»

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force
```

---

## Порт 8000 занят

`run.ps1` освобождает порт автоматически. Если нужно вручную:

```powershell
netstat -ano | findstr :8000
taskkill /PID <PID> /F
# или через CLI
assist stop
```

---

## Python не найден

Установите Python 3.10+ с [python.org](https://www.python.org/downloads/), отметив **«Add python.exe to PATH»** при установке.

Проверка:
```powershell
python --version
py --version
```

---

## Предупреждение SSL в браузере

Нажмите «Дополнительно» → «Перейти на localhost (небезопасно)», или добавьте сертификат в доверенные:

```powershell
certutil -addstore -f "Root" $env:USERPROFILE\.certs\localhost+2.pem
```

Перегенерировать сертификаты:
```powershell
.\install\Install-SslCertificate.ps1
```

---

## Ошибка импорта зависимостей

```powershell
# Убедитесь, что venv активирован
.\venv\Scripts\Activate.ps1

# Переустановите зависимости
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

---

## Gemini API: лимит исчерпан

Система автоматически ротирует ключи из пула. Добавьте дополнительные ключи в `.env`:

```ini
GEMINI_API_KEY_1=ключ_1
GEMINI_API_KEY_2=ключ_2
```

Проверить статус ключей:
```powershell
assist status
```

---

## Foundry или Ollama не запускаются

```powershell
# Проверить статус
.\launchers\Run-Foundry.ps1 -Action status
.\launchers\Run-Ollama.ps1 -Action status

# Запустить вручную
.\launchers\Run-Foundry.ps1 -Action start
.\launchers\Run-Ollama.ps1 -Action start
```

Если локальные провайдеры не нужны, отключите их в `config.json`:
```json
{ "ai": { "use_foundry": false, "use_ollama": false } }
```

---

## Файлы логов

| Файл | Содержимое |
|---|---|
| `logs/uvicorn_*.log` | Консольный вывод сервера |
| `ai-breadboard/logs/fastapi.log` | Маршрутизация запросов FastAPI |
| `ai-breadboard/logs/info.log` | Системные события |
| `ai-breadboard/logs/errors.log` | Ошибки |
| `ai-breadboard/logs/gemini.log` | Запросы к Gemini API |
| `logs/foundry_stdout.log` | Вывод Microsoft AI Foundry |
| `logs/ollama_stdout.log` | Вывод Ollama |
| `logs/telegram_bot.log` | Telegram-бот |

```powershell
assist logs 100   # последние 100 строк через CLI
```

---

## Полезные команды диагностики

```powershell
assist status          # статус сервера, портов, моделей
assist providers       # список провайдеров и их доступность
assist config show     # текущий config.json
pytest tests/ -x -q   # запуск тестов
```

---

Смотрите также: [Конфигурация](secrets.md) · [Запуск сервера](RUN.md) · [Начало работы](getting-started.md)
