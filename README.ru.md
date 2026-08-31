# aibreadboard — Интерактивная Breadboard для AI-языковых моделей

[![Documentation Status](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://hypo69.github.io/aibreadboard/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**AI Breadboard** — это интерактивная тестовая платформа и «breadboard», предназначенная для изучения, тестирования и сравнения различных AI-моделей (Google Gemini, Microsoft AI Foundry, Antigravity AGY, Ollama, OpenAI/DeepSeek, Hugging Face, ONNX) в единой среде со стандартным интерфейсом сокетов.

---

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

### Методы управления моделями

- `model_manager.get_available_models(provider)`: Получить список активных моделей для провайдера (из кэша).
- `model_manager.actualize_all_models()`: Параллельно разогревать кэши моделей всех провайдеров при запуске сервера.
- `model_manager.add_unsupported_model(provider, model_name)`: Автоматически исключать неработающие модели из ротации (сохраняется в `config.json`).

---

## 🚀 Ключевые возможности

- 🤖 **Оркестратор провайдеров:** Единый интерфейс для Foundry, ONNX, Hugging Face, OpenAI/DeepSeek, Gemini CLI, AGY, Gemini SDK и Ollama.
- 🧠 **Потоковый RAG-поиск:** Векторный поиск по `media.db` с потоковой передачей шагов рассуждения через Server-Sent Events (SSE).
- 🧩 **Расширяемая система плагинов:** Модульные сканеры дисков, обработчики метаданных и хуки инструментов агентов.
- 🎙️ **Многодвижковой TTS:** Синтез речи с поддержкой Edge-TTS, gTTS и локальной передачи аудио.

---

## 📖 Документация

### Архитектура проекта и руководство по запуску

- **[English: Detailed Startup Guide](en/code/start-engine.md)** - Complete explanation of `run.ps1` workflow, component responsibilities, and system impact
- **[Русский: Детальное руководство по запуску](ru/code/start-engine.md)** - Подробное описание процесса запуска, ответственности компонентов и влияния на систему

### Справка по CLI-командам

- **[English: CLI Commands](en/code/cli-commands.md)** - Complete reference for `assist` command-line interface
- **[Русский: CLI-команды](ru/code/cli-commands.md)** - Полный справочник по интерфейсу командной строки `assist`

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
││ • model_manager.py         │                   │ • RAG Поиск         ││
││ • unified_chat.py          │                   │ • Векторный индекс  ││
││                            │                   �� • База знаний       ││
││ Провайдеры:                │                   │ • media.db          ││
││  Foundry / ONNX / HF       │                   └─────────────────────┘│
││  OpenAI / Gemini / AGY     │                                          │
││  Gemini CLI / Ollama       │                                          │
│└────────────────────────────┘                                          │
└────────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Быстрый старт

### Предварительные требования

- **ОС:** Windows 10/11, Linux или macOS
- **Python:** 3.10+ (рекомендуется 3.12 или 3.13)
- **API-ключи:** Ключ API Google Gemini (для Gemini SDK и AGY)
- **Дополнительно:** Microsoft AI Foundry, Gemini CLI (`npm install -g @google/gemini-cli`)

---

## 📦 Рабочий процесс установки

### Обзор

AI Breadboard предоставляет **три метода установки**:
1. **Скрипт в одну строку** — автоматическая установка (рекомендуется для Windows)
2. **Интерактивный установщик** — пошаговое руководство по настройке с выбором языка
3. **Ручная установка** — полный контроль над каждым шагом

Все методы создают виртуальную среду, устанавливают зависимости, генерируют SSL-сертификаты и регистрируют глобальную команду `assist`.

---

### Вариант 1: Скрипт в одну строку (PowerShell, рекомендуется для Windows)

```powershell
irm https://raw.githubusercontent.com/hypo69/AI-Breadboard/master/install.ps1 | iex
```

Эта команда:
- Скачивает установочный скрипт из GitHub
- Запускает полный автоматический рабочий процесс установки
- Создаёт `%USERPROFILE%\AppData\Local\AI-Breadboard` с `venv`
- Устанавливает все зависимости из `requirements.txt`
- Генерирует SSL-сертификаты для локального HTTPS
- Регистрирует глобальную команду `assist` в PowerShell и PATH

**После установки** запустите `./run.ps1` для запуска сервера.

---

### Вариант 2: Интерактивный установщик (веб-интерфейс)

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

#### Шаг 2: Созда��ие виртуальной среды

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
| `assist restart` | Быстрый перезапуск сервера |
| `assist status` | Проверить статус сервера и порты |
| `assist providers` | Список AI-провайдеров и моделей |
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

## 📄 Лицензия

MIT © 2026 hypo69