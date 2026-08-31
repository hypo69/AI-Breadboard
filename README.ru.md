# `Стенд` для исследования различных языковых моделей

[![Documentation Status](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://hypo69.github.io/aibreadboard/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

AI Breadboard — интерактивная тестовая среда для изучения, тестирования и сравнения моделей от разных провайдеров: Google Gemini, Microsoft AI Foundry, Antigravity AGY, Ollama, OpenAI, DeepSeek, Hugging Face и ONNX, объединённых единым интерфейсом сокетов.

Сделана для разработчиков, которые хотят попробовать современные AI-модели без глубокого погружения в их устройство и без написания большого количества кода. Просто подключайте разные модели, экспериментируйте с ними и сразу смотрите на результат.

---

## 🏗️ Архитектура

```text
┌──────────────────────────────────────────────────────────────────────────────────┐
│                              ИНТЕРФЕЙСЫ ДОСТУПА                                  │
├──────────────────────────────────────┬───────────────────────────────────────────┤
│        Веб-интерфейс                 │           CLI-интерфейс                   │
│   ┌─────────────────────────┐        │   ┌──────────────────────────────┐        │
│   │   Веб-UI (/)            │        │   │  assist model ask "msg"      │        │
│   │   • Чат                 │        │   │  • Запросы к моделям         │        │
│   │   • RAG Поиск           │        │   │  • Управление провайдерами   │        │
│   │   • Агенты              │        │   │  • Системные промпты         │        │
│   └────────────┬────────────┘        │   └──────────────┬───────────────┘        │
│                │                     │                  │                        │
│         ┌──────▼──────┐              │           ┌──────▼─────┐                  │
│         │ FastAPI     │              │           │  Python    │                  │
│         │ Server      │              │           │  Scripts   │                  │
│         └──────┬──────┘              │           │ (assist)   │                  │
│                │                     │           └─────┬──────┘                  │
└────────────────┼─────────────────────┴─────────────────┼─────────────────────────┘
                 │                                       │
                 └───────────────────┬───────────────────┘
                                     │
                                     │
                        ┌────────────▼──────────────────┐
                        │   RAG И ХРАНИЛИЩЕ             │
                        │ • RAG Поиск                   │
                        │ • Векторный индекс            │
                        │ • База знаний (media.db)      │
                        └───────────────────────────────┘
                                      |  
                        ┌─────────────▼─────────────────┐
                        │       AI ОРКЕСТРАТОР          │
                        │       unified_chat.py         │
                        │       model_manager.py        │
                        └─────────────┬─────────────────┘
                                      │
             ┌───────────────────────┬┴─────────────────────────┐
             │                       │                          │
        ┌────▼──────────┐    ┌────────▼────────┐     ┌──────────▼──────┐
        │ 💾 ЛОКАЛЬНЫЕ  │    │ 🌐 ЛОКАЛЬНЫЕ   │     │ ☁️ ОБЛАЧНЫЕ      │
        │   МОДЕЛИ      │    │  СЕРВЕРЫ        │     │     API         │
        │               │    │                 │     │                 │
        │ • ONNX        │    │ • Foundry       │     │ • Gemini SDK    │
        │ • HuggingFace │    │ • Ollama        │     │ • Gemini CLI    │
        │ • Transformers|    │ • LM Studio     │     │ • OpenAI        │
        │               │    │ (OpenAI compat) │     │ • DeepSeek      │
        │ На диске      │    │                 │     │ • Groq          │
        │ (RAM/VRAM)    │    │ Локально        │     │ • AGY           │
        │               │    │ запущенные      │     │                 │
        └───────────────┘    └─────────────────┘     │ Требуют API ключ│
                                                     └─────────────────┘



```

**Легенда:**

- 💾 **Локальные модели** — Модели на диске, инференс в памяти (RAM/VRAM)
- 🌐 **Локальные серверы** — Инференс-серверы, запущенные локально на машине
- ☁️ **Облачные API** — Запросы отправляются на удалённые серверы (требуют интернет и API-ключи)

## 🤖 Оркестратор провайдеров (системное ядро)

Центральный компонент — `core/ai/model_manager.py` — управляет жизненным циклом моделей всех провайдеров: запрашивает доступные модели при запуске, кэширует их в памяти и автоматически исключает из ротации неработающие модели.

`core/ai/unified_chat.py` служит единственной унифицированной точкой входа для всех вызовов моделей, направляя запросы к соответствующему адаптеру провайдера на основе префикса имени модели.

### Поддерживаемые провайдеры

| Провайдер | Префикс | Адаптер | Тип | Описание |
|---|---|---|---|---|
| **Microsoft AI Foundry** | `foundry:<model_id>` | `foundry_chat.py` | 🌐 Локальный сервер | OpenAI-совместимый сервер на порту 54837 (моди установки Microsoft AI Foundry) |
| **Ollama** | `ollama:<model_id>` | `ollama_chat.py` | 🌐 Локальный сервер | Инференс-сервер на <http://localhost:11434> |
| **Microsoft ONNX (Olive)** | `onnx:<model_id>` | `onnx_chat.py` | 💾 Локальный инференс | Модели на диске, ускорение DirectML/CPU/CUDA |
| **Hugging Face** | `hf:<model_id>` | `hf_chat.py` | 💾 Локальный инференс | Модели на диске через HuggingFace Transformers |
| **OpenAI** | `openai:<model_id>` | `openai_compat_chat.py` | ☁️ Облачный API | Cloud API (gpt-4o, gpt-4-turbo и др.) |
| **DeepSeek** | `deepseek:<model_id>` | `openai_compat_chat.py` | ☁️ Облачный API | DeepSeek Cloud API (deepseek-chat, deepseek-reasoner) |
| **LM Studio** | `lmstudio:<model_id>` | `openai_compat_chat.py` | 🌐 Локальный сервер | OpenAI-совместимый локальный сервер (http://localhost:1234) |
| **Google Gemini SDK** | `gemini-*` | `core/ai/gemini/` | ☁️ Облачный API | Direct Google GenAI SDK с пулингом ключей |
| **Gemini CLI** | `gemini_cli:<model_id>` | `gemini_cli_chat.py` | ☁️ Облачный API | Локальный CLI-агент для Google Gemini |
| **Antigravity AGY** | `agy-<model_id>` | `agy_chat.py` | ☁️ Облачный API | AGY SDK поверх моделей Gemini |

### Классификация провайдеров

**💾 Локальный инференс** (модели на диске):

- ONNX + Microsoft Olive (DirectML/CUDA/CPU ускорение)
- Hugging Face Transformers
- Быстро, приватно, не требует интернета, требует RAM/VRAM

**🌐 Локальные серверы** (инференс-серверы на машине):

- Microsoft AI Foundry (OpenAI-совместимый)
- Ollama (популярный выбор для локального запуска)
- LM Studio (UI + OpenAI API)
- Требуют запущенного сервера, не требуют интернета, приватно

**☁️ Облачные API** (запросы в интернет):

- Google Gemini SDK
- Google Gemini CLI
- OpenAI, DeepSeek, Groq и др.
- Требуют API-ключи и интернет, мощные, оплачиваемые (обычно с бесплатным лимитом)

### Конвейер маршрутизации запросов

```text
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

# Установка на локальный компьютер

## Требования к оборудованию

Для простых исследований и экспериментов с AI-моделями не требуется мощный компьютер. Достаточно обычного настольного ПК со следующей конфигурацией:

- **Процессор:** Intel Core i5 10-го поколения или новее
* **Оперативная память:**- **Оперативная память:**- **Оперативная память:**- **Оперативная память:**- **Оперативная память:**- **Оперативная память:**- **Оперативная память:**- **Оперативная память:**- **Оперативная память:**- **Оперативная память:**- **Оперативная память:**- **Оперативная память:**- **Оперативная память:**- **Оперативная память:**- **Оперативная память:**- **Оперативная память:** 


  - Для облачных провайдеров (Gemini, OpenAI): 4 ГБ минимум
  - Для ONNX/HuggingFace моделей: 8+ ГБ в зависимости от размера модели
  - Для Ollama (большие модели): 16+ ГБ рекомендуется

- **Дисковое пространство:**
  - Базовая установка: 2-5 ГБ
  - С локальными моделями (Ollama, ONNX, HF): зависит от выбора моделей (обычно 5-30 ГБ на модель)
- **Видеокарта:** не требуется (ускорение достигается через CPU/DirectML)
- **Python:** 3.10+ (рекомендуется 3.11, 3.12 или 3.13)
- **PowerShell:** 5.1+ встроенный (Windows) или PowerShell 7+ рекомендуется
- **Поддерживаемые языки установки:** Русский (RU) и Английский (EN) с полной локализацией. Испанский (ES) и Иврит (HE) в разработке (доступны названия языков)
- **API-ключи:** [Ключ API Google Gemini (для Gemini SDK и AGY))](https://aistudio.google.com/api-keys)

<small><i>В Google API есть бесплатный лимит на токены, ограниченный количеством запросов в минуту и сутки, размером запроса и выбором моделей. На нашем стенде мы будем использовать GEMINI CLI для служебных целей. В коде я предусмотрел создание пула ключей, которые автоматически подменяются при достижении лимитов. Со своих родствеников я стряс деясяток ключей - все равно они им без надобности.</i></small>

## Windows

*(В Windows желательно открывать терминал PowerShell от имени администратора)*

### Вариант 1: Скрипт в одну строку

```powershell
irm https://raw.githubusercontent.com/hypo69/AI-Breadboard/master/install.ps1 | iex
```

Эта команда:

- Downloads установочный скрипт из GitHub
- Запускает полный автоматический рабочий процесс установки

### Вариант 2: Клонирование репозитория

1. **Клонируйте репозиторий:**
   ```powershell
   git clone https://github.com/hypo69/AI-Breadboard.git
   cd AI-Breadboard
   ```

2. **Запустите установщик:**
   ```powershell
   .\install.ps1
   ```

**Процесс установки работает с Moduleной архитектурой:**

- `install.ps1` — главный оркестратор
- `install/Install-I18n.ps1` — локализация (RU, EN, ES, HE)
- `install/Install-Directory.ps1` — выбор директории установки
- `install/Install-Venv.ps1` — создание виртуальной среды
- `install/Install-Deps.ps1` — установка зависимостей из `install/req/`
- `install/Install-Certs.ps1` — генерация SSL-сертификатов
- `install/Install-Cli.ps1` — регистрация команды `assist`
- `install/Install-Verify.ps1` — check основных модулей
- `install/Install-Models.ps1` — выбор и Loading моделей

Каждый Module логирует свою работу в `tmp/logs/install.log`.

Неважно куда вы клонируете репозиторий, программа по умолчанию установится в пути:

```powershell
%LOCALAPPDATA%\AI Breadboard
```

**При запуске install.ps1 вы сможете выбрать:**

1. Стандартное место (`%LOCALAPPDATA%\AI Breadboard`)
2. Собственный путь (введите любой путь)

Выбор сохраняется в переменную окружения `AIBREADBOARD_DIR` и используется при каждом запуске.

## Линуксы

# **Руководство по установке (Шаги 1-8):**

   **Шаг 1: Разблокировка файлов**

   - Deletes «Метку веба» (MOTW) Windows со всех файлов проекта
   - Windows добавляет метаданные MOTW к файлам, загруженным из интернета, помечая их как ненадёжные
   - Без разблокировки PowerShell блокирует выполнение скриптов `.ps1` с ошибкой: "execution of scripts is disabled on this system"
   - Некоторые функции Python/Node.js могут работать неправильно

   **Шаг 2: Настройка виртуальной среды**

   - Ищет Python 3.10+ через launcher `py`, команды `python` или `python3`
   - Пропускает заглушки Python из Microsoft Store
   - Creates чистую директорию `venv` или использует существующую валидную среду
   - Версия Python и путь сохраняются в `config.json`

   **Шаг 3: Update инструментов пакетов**

   - Обновляет `pip`, `setuptools` и `wheel` до последних версий
   - Обеспечивает современное оснащение для установки зависимостей

   **Шаг 4: Установка зависимостей**

   ```text

   [1] Полная установка (Core + AI + Utils) — РЕКОМЕНДУЕТСЯ
   [2] Только основной сервер
   [3] Core + AI модули
   [4] Полная установка + Тесты и Документация (Dev)
   [5] Пропустить установку зависимостей
   ```

   - Sets из `install/req/requirements-core.txt`, `install/req/requirements-ai.txt`, `install/req/requirements-media.txt` и `install/req/requirements-utils.txt`
   - Creates `requirements.txt` с объединёнными зависимостями
   - Может быть настроен для продакшена или разработки

   **Шаг 5: Генерация SSL-сертификатов**

   - Checks наличие `%USERPROFILE%\.certs\localhost+2.pem` и `localhost+2-key.pem`
   - Если не найдены, запускает `install_ssl_cert.ps1` для генерации локальных SSL-сертификатов
   - Включает HTTPS-доступ к `http://localhost:8000`

   **Шаг 6: Регистрация глобальной команды**

   - Creates скрипты `assist.ps1`, `assist.cmd` и `assist` (bash)
   - Sets в `%USERPROFILE%\.local\bin\` (или `~/.local/bin/` на Linux/macOS)
   - Добавляет путь в переменную окружения PATH
   - Регистрирует функцию `assist` в профилях PowerShell (`$PROFILE`)
   - Sets переменную окружения `AIBREADBOARD_DIR` на корневую папку проекта

   **Шаг 7: Финальная check**

   - Тестирует импорты основных модулей: `fastapi`, `uvicorn`, `pydantic`, `aiofiles`, `cryptography`
   - Записывает результаты в консоль
   - Saves status установки в `config.json`

   **Шаг 8: Выбор и Loading моделей**

   - Receives list доступных моделей от локальных провайдеров (Ollama, Foundry, ONNX)
   - Позволяет пользователю выбрать модели для загрузки
   - Loads модели через их нативные команды

4. **Сообщение об окончании:**
   ```text
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

#### Шаг 3: Update инструментов пакетов

```bash
pip install --upgrade pip setuptools wheel
```

#### Шаг 4: Установка зависимостей

```bash
# Полная установка (рекомендуется)
pip install -r requirements.txt

# Или выборочные подмножества
pip install -r install/req/requirements-core.txt
pip install -r install/req/requirements-ai.txt
pip install -r install/req/requirements-media.txt
pip install -r install/req/requirements-utils.txt
```

#### Шаг 5: Генерация SSL-сертификатов

```powershell
# Windows
.\install_ssl_cert.ps1

# Или вручную с помощью mkcert
mkcert -install
mkcert localhost 127.0.0.1 ::1
```

Сертификаты будут сохранены в `%USERPROFILE%\.certs\` (Windows).

**На Linux/macOS сертификаты будут в соответствующих системных расположениях** — см. подробнее в [CONFIG.md](CONFIG.md).

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
| `requirements-media.txt` | Обработка медиа (изображения, видео, аудио) | Поддержка RAG с медиа-контентом |
| `requirements-utils.txt` | Pandas, Pillow, BeautifulSoup4 | Утилиты обработки данных |
| `requirements-test.txt` | pytest, pytest-asyncio, coverage | Тестирование разработки |
| `requirements-docs.txt` | MkDocs, Material theme | Построение документации |
| `requirements.txt` | Все объединённые | Полная установка |

---

### ⚙️ Configuration

**`config.json`** — Нечувствительные к безопасности Parameters:

- `server` — хост, порт, настройки SSL
- `ai` — значения по умолчанию для моделей, Parameters Foundry/AGY/Gemini CLI, списки неподдерживаемых моделей
- `langchain`, `agents` — конфиги ReAct-агентов, определения инструментов MCP

**`.env`** — Секретные учётные данные и переменные окружения:

```bash
cp .env.example .env
```

Основные переменные окружения:

```ini
# API ключи
GEMINI_API_KEY=ваш_ключ_api_gemini_здесь
JWT_SECRET=ваш_супер_секретный_jwt_ключ

# Локальные провайдеры
USE_FOUNDRY=false
FOUNDRY_BASE_URL=http://localhost:54837
FOUNDRY_MODEL_ID=qwen2.5-1.5b-instruct-generic-cpu:4
FOUNDRY_API_KEY=ваш_ключ_api_foundry_здесь (если нужен)

# Системные переменные (устанавливаются автоматически)
AIBREADBOARD_DIR=%LOCALAPPDATA%\AI Breadboard (корневая папка проекта)
ASSIST_DIR=то же самое
PYTHONUTF8=1 (для поддержки UTF-8 в Python)
```

**Важно:** Переменная окружения `AIBREADBOARD_DIR` устанавливается автоматически при установке и используется `run.ps1`, `assist.ps1` и внутренним Python кодом для определения корневой папки проекта. Если вы устанавливаете приложение в нестандартное место, убедитесь, что эта переменная установлена правильно.

---

## 🎯 Настройка после установки

### Глобальная команда `assist`

После установки команда `assist` доступна глобально для управления сервером и моделями.

**Для полного справочника всех команд выполните:**

```powershell
assist help
```

или

```powershell
assist -h
```

**Основные команды:**

| Команда | Описание |
|---|---|
| **Запуск / Остановка** | |
| `assist start` | Запустить основной сервер (FastAPI + Uvicorn) |
| `assist start run` | Запустить через `run.ps1` |
| `assist start unicorn` | Запустить через FastAPI/Uvicorn напрямую |
| `assist start light` | Запустить лёгкий сервер (без некоторых компонентов) |
| `assist start foundry` | Запустить локальный Microsoft AI Foundry |
| `assist stop` | Остановить сервер и процессы |
| `assist restart` | Перезапустить сервер |
| **Status и Info** | |
| `assist status` | Проверить status сервера, портов и моделей |
| `assist providers` | Показать list всех провайдеров ИИ и их status |
| `assist models` | Алиас для `assist providers` |
| `assist current` | Показать текущие настройки (активный провайдер и модель) |
| **Управление провайдерами и моделями** | |
| `assist list providers` | Показать доступных провайдеров |
| `assist list models` | Показать модели выбранного провайдера |
| `assist select provider <name>` | Выбрать провайдера (gemini, gemini_cli, agy, foundry, ollama, hf, onnx, openai) |
| `assist select model <name>` | Выбрать модель из текущего провайдера |
| `assist model ask "<message>"` | Отправить запрос к текущей модели |
| **Системные промпты** | |
| `assist create-prompt` | Создать новый системный промпт |
| `assist edit-prompt` | Редактировать текущий промпт |
| `assist edit-prompt view` | Посмотреть текущий промпт |
| `assist edit-prompt delete` | Удалить текущий промпт |
| **Configuration и логирование** | |
| `assist config show` | Показать текущий `config.json` |
| `assist config get <ключ>` | Получить значение из конфига |
| `assist config set <ключ> <значение>` | Установить значение в конфиге |
| `assist logs [N]` | Просмотр последних N строк логов (по умолчанию: 40) |
| **Тестирование и регистрация** | |
| `assist test` | Запустить набор pytest |
| `assist install-profile` | Зарегистрировать команду `assist` глобально в PowerShell |
| **Интерактивная среда** | |
| `assist shell` | Открыть интерактивную оболочку Python для прямого взаимодействия с кодом |

### Выбор и Loading моделей (Новое в v2.0)

После установки вы можете выбрать и загрузить модели для локальных провайдеров:

**Пошаговый процесс:**

1. **Запустите интерактивный установщик** (или повторно запустите `install.ps1`):
   ```powershell
   .\install.ps1
   ```

2. **Выберите модели локальных провайдеров** на шаге 8:
   - Скрипт receives list доступных моделей от Ollama, Foundry, ONNX
   - Выберите модели для загрузки по номеру(ам) или диапазону (например, `1-3`)
   - Модели загружаются через их нативные команды

3. **Поддерживаемые локальные провайдеры:**

   | Провайдер | Команда | Префикс модели |
   |---|---|---|
   | Ollama | `ollama pull` | `ollama:<model_id>` |
   | Foundry | Автоматическая Loading | `foundry:<model_id>` |
   | ONNX | Автоматическая Loading (Transformers) | `onnx:<model_id>` |
   | HuggingFace | Автоматическая Loading (Transformers) | `hf:<model_id>` |

4. **Запустите сервер:**
   ```powershell
   ./run.ps1
   ```

**Пример сессии:**

```text

[8/8] Выбор и Loading моделей для локальных провайдеров...

Доступные модели для Ollama:
  [1] llama3.1
  [2] qwen2.5-1.5b-instruct-generic-cpu:4
  [3] mistral-small

Выберите модели для загрузки (номера через запятую или диапазон 1-3) [Enter = пропустить]: 1,2

Loading модели Ollama (llama3.1)...
[OK] Модель llama3.1 successfully загружена

Loading модели Foundry (qwen2.5-1.5b-instruct-generic-cpu:4)...
[INFO] Foundry loads модели автоматически при первом использовании
[OK] Модель qwen2.5-1.5b-instruct-generic-cpu:4 successfully загружена
```

### Доступ к веб-интерфейсуок AI-провайдеров и моделей |

| `assist logs [N]` | Просмотр последних N строк логов (по умолчанию: 40) |
| `assist config show` | Показать текущий `config.json` |
| `assist config get <ключ>` | Получить значение конфига |
| `assist config set <ключ> <значение>` | Установить значение конфига |
| `assist test` | Запустить набор pytest |

### Доступ к веб-интерфейсу

**Основной сервер AI-Breadboard:**

- **Главная панель:** `http://localhost:8000/`
- **Документация API:** `http://localhost:8000/docs`
- **Документация Redoc:** `http://localhost:8000/redoc`

**Локальные провайдеры (если установлены):**

- **AI Foundry:** `http://localhost:54837/` (OpenAI-совместимый API)
- **Ollama:** `http://localhost:11434/` (локальный инференс-сервер)

---

## 🔍 Устранение неполадок

### Error политики выполнения

Если PowerShell показывает "выполнение скриптов отключено":

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force
```

### Порт 8000 уже занят

```powershell
# Убить процесс на порту 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Или использовать assist
assist stop
```

### Python не найден

Установите Python 3.10+ с [python.org](https://www.python.org/downloads/), обязательно отметив **"Add python.exe to PATH"** во время установки.

### Warning SSL-сертификата

Браузер предупреждает о самоподписанном сертификате:

1. Нажмите "Дополнительно" → "Перейти на localhost (небезопасно)"
2. Или установите сертификат в Trusted Root CA Windows:
   ```powershell
   certutil -addstore -f "Root" $env:USERPROFILE\.certs\localhost+2.pem
   ```

### Файлы логов

**Логи установки** сохраняются в `tmp/logs/install.log` во время выполнения install.ps1.

**Логи приложения** при запуске сервера (./run.ps1):

- `tmp/logs/fastapi.log` — маршрутизация запросов FastAPI
- `tmp/logs/info.log` — системные события
- `tmp/logs/errors.log` — ошибки
- `tmp/logs/uvicorn_*.log` — консольный вывод сервера

Проверьте логи в директории `logs/` вашей установки (обычно `%LOCALAPPDATA%\AI Breadboard\logs\`).

---

### ▶️ Запуск приложения

```powershell
# Запускатель Windows (рекомендуется)
./run.ps1
```

`run.ps1` автоматически checks доступность порта, запускает Microsoft AI Foundry при настройке и запускает FastAPI с SSL и авто-перезагрузкой.

```bash
# Прямое выполнение
.\venv\Scripts\python.exe main.py
```

---

## 🖥️ Веб-endpoints

| Интерфейс | URL | Описание |
|---|---|---|
| 🏠 **Главная панель** | `http://localhost:8000/` | Интерактивный чат, модели, RAG, агенты, логи |
| 📄 **API Swagger Docs** | `http://localhost:8000/docs` | Интерактивная OpenAPI документация |

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