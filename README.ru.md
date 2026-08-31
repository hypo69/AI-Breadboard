# `Mодельная плата` для исследования различных языковых моделей

[![Documentation Status](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://hypo69.github.io/aibreadboard/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

AI Breadboard — интерактивная тестовая среда для изучения, тестирования и сравнения моделей от разных провайдеров: Google Gemini, Microsoft AI Foundry, Antigravity AGY, Ollama, OpenAI, DeepSeek, Hugging Face и ONNX, объединённых единым интерфейсом сокетов.

Создается для разработчиков, которые хотят попробовать современные AI-модели без глубокого погружения в их устройство и без написания большого количества кода. Подключайте разные модели, экспериментируйте с ними и сразу смотрите на результат.

---


## 🏗️ Архитектура

```
┌────────────────────────────────────────────────────────────────────────┐
│                             Веб-интерфейс                              │
│                       ┌───────────────────────┐                        │
│                       │      Веб-UI (/)       │                        │
│                       └───────────┬───────────┘                        │
│                                   │                                    │
│                         ┌─────────▼──────────┐                         │
│                         │   FastAPI Сервер   │                         │
│                         └─────────┬──────────┘                         │
│    ┌──────────────────────────────┴──────────────────────────────┐     │
│    │                                                             │     │
│┌───▼────────────────────────┐                   ┌────────────────▼────┐│
││  AI Оркестратор            │                   │  RAG и Хранилище    ││
││ • model_manager.py         │<----------------->│ • RAG Поиск         ││
││ • unified_chat.py          │                   │ • Векторный индекс  ││
││                            │                   | • База знаний       ││
││ Провайдеры:                │                   │ • media.db          ││
││  Foundry / ONNX / HF       │                   └─────────────────────┘│
││  OpenAI API format models  |
||  Gemini / AGY              │                                          │
││  Gemini CLI / Ollama / etc.│                                          │
│└────────────────────────────┘                                          │
└────────────────────────────────────────────────────────────────────────┘
```


## 🤖 Оркестратор провайдеров (системное ядро)

Центральный компонент — `core/ai/model_manager.py` — управляет жизненным циклом моделей всех провайдеров: запрашивает доступные модели при запуске, кэширует их в памяти и автоматически исключает из ротации неработающие модели.

`core/ai/unified_chat.py` служит единственной унифицированной точкой входа для всех вызовов моделей, направляя запросы к соответствующему адаптеру провайдера на основе префикса имени модели.

### Поддерживаемые провайдеры

| Провайдер | Префикс модели | Адаптер | Описание |
|---|---|---|---|
| **Microsoft AI Foundry** | `foundry:<model_id>` | `foundry_chat.py` | Локальный сервер, совместимый с OpenAI (`Run-Foundry.ps1`) |
| **Microsoft ONNX (Olive)** | `onnx:<model_id>` | `onnx_chat.py` | Локальный инференс ONNX/Olive с ускорением DirectML / CPU / CUDA |
| **Hugging Face** | `hf:<model_id>` | `hf_chat.py` | Локальный инференс модели через Hugging Face Transformers |
| **OpenAI-совместимые API** | `openai:<model_id>`, `deepseek:<model_id>`, `lmstudio:<model_id>` | `openai_compat_chat.py` | Облачные и локальные сервисы (OpenAI, DeepSeek, Groq, LM Studio) |
| **Google Gemini SDK** | `gemini-*` (без префикса) | `core/ai/gemini/` | Прямая интеграция SDK Google GenAI с пулингом API-ключей |
| **Google Gemini CLI** | `gemini_cli:<model_id>` | `gemini_cli_chat.py` | Локальный агент на основе подпроцесса (`gemini -p ... -m ...`) |
| **Antigravity AGY** | `agy-<model_id>` | `agy_chat.py` | Antigravity SDK, работающий поверх моделей Gemini |
| **Ollama** | `ollama:<model_id>` | `ollama_chat.py` | Локальный сервер инференса Ollama |

### Конвейер маршрутизации запросов

```
Запрос пользователя → UnifiedChatModel._get_active_model(model_name)
    ├── "foundry:qwen2.5-..."   → FoundryChatBase       → http://localhost:54837/v1
    ├── "onnx:qwen2.5-..."      → ONNXChatBase          → Microsoft ONNX Runtime / Olive (DirectML)
    ├── "hf:Qwen/..."           → HFChatBase            → Hugging Face Transformers
    ├── "openai:gpt-4o"         → OpenAICompatChat      → OpenAI / DeepSeek / LM Studio API
    ├── "gemini_cli:gemini-..." → GeminiCliChatBase     → подпроцесс gemini CLI
    ├── "agy-gemini-..."        → AgyChatBase           → google.antigravity SDK
    ├── "ollama:llama3.1"       → OllamaChatBase        → http://localhost:11434
    └── "gemini-flash-..."      → GoogleGenerativeAI    → Google GenAI SDK
```


---




# Установка на локальный компьютер.
## Требования к оборудованию

Для простых исследований и экспериментов с AI-моделями не требуется мощный компьютер. Достаточно обычного настольного ПК со следующей конфигурацией:

* **Процессор:** Intel Core i5 10-го поколения или новее
* **Оперативная память:** 32 ГБ
* **Дисковое пространство:** около 10 ТБ
* **Видеокарта:** не требуется для базовых экспериментов
- **Python:** 3.10+ (рекомендуется 3.12 или 3.13)
- **PowerShell 7+**
- **API-ключи:** Ключ API Google Gemini (для Gemini SDK и AGY)




## Windows
### Вариант 1: Скрипт в одну строку (PowerShell, рекомендуется для Windows)

```powershell
irm https://raw.githubusercontent.com/hypo69/AI-Breadboard/master/install.ps1 | iex
```

Эта команда:
- Скачивает установочный скрипт из GitHub
- Запускает полный автоматический рабочий процесс установки
- Создаёт `%LOCALAPPDATA%\AI-Breadboard` с `venv`
- Устанавливает все зависимости из `requirements.txt`
- Генерирует SSL-сертификаты для локального HTTPS
- Регистрирует глобальную команду `assist` в PowerShell и PATH

**После установки** запустите `./run.ps1` для запуска сервера.



### Вариант 2: Интерактивный установщик

#### Пошаговый процесс

1. **Клонируйте репозиторий:**
   ```powershell
   git clone https://github.com/hypo69/AI-Breadboard.git
   cd AI-Breadboard
   ```

2. **Запустите установщик:**
   ```powershell
   .\install.ps1
   ```

3. **Руководство по установке:**

   **Шаг 0: Выбор языка**
   - Выберите язык установочного интерфейса: русский (RU), английский (EN), испанский (ES) или иврит (HE)
   - Выбор сохраняется в `config.json` для будущих сессий

   **Шаг 1: Разблокировка файлов**
   - Удаляет «Метку веба» (MOTW) Windows со всех файлов проекта
   - Windows добавляет метаданные MOTW к файлам, загруженным из интернета, помечая их как ненадёжные
   - Без разблокировки PowerShell блокирует выполнение скриптов `.ps1` с ошибкой: "execution of scripts is disabled on this system"
   - Некоторые функции Python/Node.js могут работать неправильно

   **Шаг 2: Настройка виртуальной среды**
   - Ищет Python 3.10+ через launcher `py`, команды `python` или `python3`
   - Пропускает заглушки Python из Microsoft Store
   - Создаёт чистую директорию `venv` или использует существующую валидную среду
   - Версия Python и путь сохраняются в `config.json`

   **Шаг 3: Обновление инструментов пакетов**
   - Обновляет `pip`, `setuptools` и `wheel` до последних версий
   - Обеспечивает современное оснащение для установки зависимостей

   **Шаг 4: Установка зависимостей**
   ```
   [1] Полная установка (Core + AI + Utils) — РЕКОМЕНДУЕТСЯ
   [2] Только основной сервер
   [3] Core + AI модули
   [4] Полная установка + Тесты и Документация (Dev)
   [5] Пропустить установку зависимостей
   ```
   - Устанавливает из `requirements-core.txt`, `requirements-ai.txt` и `requirements-utils.txt`
   - Создаёт `requirements.txt` с объединёнными зависимостями
   - Может быть настроен для продакшена или разработки

   **Шаг 5: Генерация SSL-сертификатов**
   - Проверяет наличие `%USERPROFILE%\.certs\localhost+2.pem` и `localhost+2-key.pem`
   - Если не найдены, запускает `install_ssl_cert.ps1` для генерации локальных SSL-сертификатов
   - Включает HTTPS-доступ к `http://localhost:3000`

   **Шаг 6: Регистрация глобальной команды**
   - Создаёт скрипты `assist.ps1`, `assist.cmd` и `assist` (bash)
   - Устанавливает в `%USERPROFILE%\.local\bin\` (или `~/.local/bin/` на Linux/macOS)
   - Добавляет путь в переменную окружения PATH
   - Регистрирует функцию `assist` в профилях PowerShell (`$PROFILE`)

   **Шаг 7: Финальная проверка**
   - Тестирует импорты основных модулей: `fastapi`, `uvicorn`, `pydantic`, `aiofiles`, `cryptography`
   - Записывает результаты в консоль
   - Сохраняет статус установки в `config.json`

4. **Сообщение об окончании:**
   ```
   ╔═══════════════════════════════════════════════════════════════╗
   ║         УСТАНОВКА ai-breadboard УСПЕШНО ЗАВЕРШЕНА!                 ║
   ║  Запуск сервера:  ./run.ps1                                   ║
   ╚═══════════════════════════════════════════════════════════════╝
   ```

---

### Вариант 3: Ручная установка

#### Шаг 1: Клонирование репозитория

```bash
# Windows
git clone https://github.com/hypo69/AI-Breadboard.git C:\aibreadboard
cd C:\aibreadboard

# Linux / macOS
git clone https://github.com/hypo69/AI-Breadboard.git ~/aibreadboard
cd ~/aibreadboard
```

#### Шаг 2: Создание виртуальной среды

```powershell
# Windows
python -m venv venv
.\venv\Scripts\Activate.ps1
```

```bash
# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

#### Шаг 3: Обновление инструментов пакетов

```bash
pip install --upgrade pip setuptools wheel
```

#### Шаг 4: Установка зависимостей

```bash
# Полная установка (рекомендуется)
pip install -r requirements.txt

# Или выборочные подмножества
pip install -r req/requirements-core.txt
pip install -r req/requirements-ai.txt
pip install -r req/requirements-utils.txt
```

#### Шаг 5: Генерация SSL-сертификатов

```powershell
# Windows
.\install_ssl_cert.ps1

# Или вручную с помощью mkcert
mkcert -install
mkcert localhost 127.0.0.1 ::1
```

Сертификаты будут сохранены в `%USERPROFILE%\.certs\`.

#### Шаг 6: Регистрация глобальной команды `assist`

```powershell
# Windows
.\assist.ps1 install-profile
```

Это создаст `~\.local\bin\assist.ps1` и зарегистрирует его в профилях PowerShell.

---

### Структура зависимостей (`req/`)

| Файл | Содержимое | Случай использования |
|---|---|---|
| `requirements-core.txt` | FastAPI, Uvicorn, Pydantic, JWT, aiohttp, httpx | Минимальная функциональность сервера |
| `requirements-ai.txt` | LangChain, LangGraph, Google GenAI, FAISS, ChromaDB, MCP | AI/ML функции |
| `requirements-utils.txt` | Pandas, Pillow, BeautifulSoup4 | Утилиты |
| `requirements-test.txt` | pytest, pytest-asyncio, coverage | Тестирование разработки |
| `requirements-docs.txt` | MkDocs, Material theme | Построение документации |
| `requirements.txt` | Все объединённые | Полная установка |

---

### ⚙️ Конфигурация

**`config.json`** — Нечувствительные к безопасности параметры:
- `server` — хост, порт, настройки SSL
- `ai` — значения по умолчанию для моделей, параметры Foundry/AGY/Gemini CLI, списки неподдерживаемых моделей
- `langchain`, `agents` — конфиги ReAct-агентов, определения инструментов MCP

**`.env`** — Секретные учётные данные:
```bash
cp .env.example .env
```
```ini
GEMINI_API_KEY=ваш_ключ_api_gemini_здесь
JWT_SECRET=ваш_супер_секретный_jwt_ключ
```

---

## 🎯 Настройка после установки

### Глобальная команда `assist`

После установки команда `assist` доступна глобально:

| Команда | Описание |
|---|---|
| `assist start` | Запустить основной сервер (`run.ps1`) |
| `assist start unicorn` | Запустить через FastAPI/Uvicorn |
| `assist start light` | Запустить лёгкий сервер |
| `assist start foundry` | Запустить локальный AI Foundry |
| `assist stop` | Остановить сервер и освободить порт 3000 |
| `assist test` | Запустить набор pytest |

### Выбор и загрузка моделей (Новое в v2.0)

После установки вы можете выбрать и загрузить модели для локальных провайдеров:

**Пошаговый процесс:**

1. **Запустите интерактивный установщик** (или повторно запустите `install.ps1`):
   ```powershell
   .\install.ps1
   ```

2. **Выберите модели локальных провайдеров** на шаге 8:
   - Скрипт получает список доступных моделей от Ollama, Foundry, ONNX
   - Выберите модели для загрузки по номеру(ам) или диапазону (например, `1-3`)
   - Модели загружаются через их нативные команды

3. **Поддерживаемые локальные провайдеры:**
   | Провайдер | Команда | Префикс модели |
   |---|---|---|
   | Ollama | `ollama pull` | `ollama:<model_id>` |
   | Foundry | Автоматическая загрузка | `foundry:<model_id>` |
   | ONNX | Автоматическая загрузка (Transformers) | `onnx:<model_id>` |
   | HuggingFace | Автоматическая загрузка (Transformers) | `hf:<model_id>` |

4. **Запустите сервер:**
   ```powershell
   ./run.ps1
   ```

**Пример сессии:**
```
[8/8] Выбор и загрузка моделей для локальных провайдеров...

Доступные модели для Ollama:
  [1] llama3.1
  [2] qwen2.5-1.5b-instruct-generic-cpu:4
  [3] mistral-small

Выберите модели для загрузки (номера через запятую или диапазон 1-3) [Enter = пропустить]: 1,2

Загрузка модели Ollama (llama3.1)...
[OK] Модель llama3.1 успешно загружена

Загрузка модели Foundry (qwen2.5-1.5b-instruct-generic-cpu:4)...
[INFO] Foundry загружает модели автоматически при первом использовании
[OK] Модель qwen2.5-1.5b-instruct-generic-cpu:4 успешно загружена
```

### Доступ к веб-интерфейсуок AI-провайдеров и моделей |
| `assist logs [N]` | Просмотр последних N строк логов (по умолчанию: 40) |
| `assist config show` | Показать текущий `config.json` |
| `assist config get <ключ>` | Получить значение конфига |
| `assist config set <ключ> <значение>` | Установить значение конфига |
| `assist test` | Запустить набор pytest |

### Доступ к веб-интерфейсу

- **Главная панель:** `http://localhost:3000/`
- **Документация API:** `http://localhost:3000/docs`
- **Документация Redoc:** `http://localhost:3000/redoc`

---

## 🔍 Устранение неполадок

### Ошибка политики выполнения

Если PowerShell показывает "выполнение скриптов отключено":

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force
```

### Порт 3000 уже занят

```powershell
# Убить процесс на порту 3000
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Или использовать assist
assist stop
```

### Python не найден

Установите Python 3.10+ с [python.org](https://www.python.org/downloads/), обязательно отметив **"Add python.exe to PATH"** во время установки.

### Предупреждение SSL-сертификата

Браузер предупреждает о самоподписанном сертификате:
1. Нажмите "Дополнительно" → "Перейти на localhost (небезопасно)"
2. Или установите сертификат в Trusted Root CA Windows:
   ```powershell
   certutil -addstore -f "Root" $env:USERPROFILE\.certs\localhost+2.pem
   ```

### Файлы логов

Проверьте логи в директории `logs/`:
- `fastapi.log` — маршрутизация запросов FastAPI
- `info.log` — системные события
- `errors.log` — ошибки
- `uvicorn_*.log` — консольный вывод сервера

---

### ▶️ Запуск приложения

```powershell
# Запускатель Windows (рекомендуется)
./run.ps1
```

`run.ps1` автоматически проверяет доступность порта, запускает Microsoft AI Foundry при настройке и запускает FastAPI с SSL и авто-перезагрузкой.

```bash
# Прямое выполнение
.\venv\Scripts\python.exe main.py
```

---

## 🖥️ Веб-=endpoints

| Интерфейс | URL | Описание |
|---|---|---|
| 🏠 **Главная панель** | `http://localhost:3000/` | Интерактивный чат, модели, RAG, агенты, логи |
| 📄 **API Swagger Docs** | `http://localhost:3000/docs` | Интерактивная OpenAPI документация |

---

## 🛠️ Технологический стек

- **Backend:** Python 3.10+, FastAPI, Uvicorn, AsyncIO, Server-Sent Events (SSE)
- **AI Оркестратор:** `model_manager.py` + `unified_chat.py` — маршрутизация провайдеров по Foundry, Gemini CLI, AGY, Gemini SDK, Ollama, ONNX, Hugging Face
- **Поиск и RAG:** SQLite (`media.db`), FAISS, Sentence-Transformers
- **Frontend:** HTML5, CSS3, Vanilla JavaScript (ES Modules, i18next)
- **Сеть и безопасность:** mkcert локальный SSL

---
## 📖 Документация

### Архитектура проекта и руководство по запуску

- **[English: Detailed Startup Guide](en/code/start-engine.md)** - Complete explanation of `run.ps1` workflow, component responsibilities, and system impact
- **[Русский: Детальное руководство по запуску](ru/code/start-engine.md)** - Подробное описание процесса запуска, ответственности компонентов и влияния на систему

### Справка по CLI-командам

- **[English: CLI Commands](en/code/cli-commands.md)** - Complete reference for `assist` command-line interface
- **[Русский: CLI-команды](ru/code/cli-commands.md)** - Полный справочник по интерфейсу командной строки `assist`


## 📄 Лицензия

MIT © 2026 hypo69