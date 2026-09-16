# Справочник конфигурации: `config.json`

Файл `config.json` является **центральным публичным конфигурационным файлом** проекта **AI-Breadboard**. Он определяет параметры запуска веб-сервера, маршрутизацию AI-провайдеров, настройки ONNX/DirectML, поисковых движков, MCP-серверов и автономных агентов.

> [!IMPORTANT]
> **Разделение конфигурации и секретов:**  
> `config.json` версионируется в Git и содержит **только публичные настройки и параметры архитектуры**. Приватные токены и ключи API хранятся в файле [`.env`](../../../.env.example) и защищенном пуле [`src/secrets/gemini_keys.json`](secrets.md#2-управление-ключами-google-gemini-пул-ротации). Все файлы, содержащие пароли, API-ключи или другую чувствительную информацию, **ДОЛЖНЫ** называться `secrets.json`. Использование других имен для новых файлов с чувствительными данными запрещено.

---

## 📑 Содержание

1. [Секция `server` (Параметры веб-сервера и сети)](#1-секция-server)
2. [Секция `apps` (Встроенные приложения и терминалы)](#2-секция-apps)
3. [Секция `telegram` (Интеграция с Telegram)](#3-секция-telegram)
4. [Секция `ai` (Провайдеры моделей и ротация ключей)](#4-секция-ai)
5. [Секция `huggingface` (Локальные модели Transformers)](#5-секция-huggingface)
6. [Секция `onnx` (DirectML & ONNX Runtime)](#6-секция-onnx)
7. [Секция `openai_compat` (OpenAI-совместимые API)](#7-секция-openai_compat)
8. [Секция `tts` (Синтез речи)](#8-секция-tts)
9. [Секция `logging` (Логирование и анализатор)](#9-секция-logging)
10. [Секция `pprint` (Форматирование вывода JSON)](#10-секция-pprint)
11. [Секция `rag` (Retrieval-Augmented Generation)](#11-секция-rag)
12. [Секция `ifttt` (Параметры Webhooks умного дома)](#12-секция-ifttt)
13. [Секция `web_search` (Движки веб-поиска)](#13-секция-web_search)
14. [Секция `langchain` (MCP-серверы и агентный стек)](#14-секция-langchain)
15. [Секция `agents` (Автономные агенты)](#15-секция-agents)
16. [Секция `plugins` (Плагины)](#16-секция-plugins)
17. [Секция `storage` (Хранилище данных)](#17-секция-storage)
18. [Секция `user_settings` (Пользовательские настройки)](#18-секция-user_settings)

---

## 1. Секция `server`

Настройки FastAPI/Uvicorn бэкенда, сетевых интерфейсов, туннелей и режимов запуска.

```json
"server": {
  "host": "0.0.0.0",
  "port": 8000,
  "workers": 1,
  "reload": false,
  "use_ssl": true,
  "mode": "DEV",
  "debug": true,
  "auto_launch": {
    "enabled": false,
    "delay_seconds": 5
  },
  "auto_start_assist_cli": false,
  "enable_assist": false,
  "enable_oauth": true,
  "enable_telegram_bot": true,
  "use_cloudflared": true,
  "user_domain": "kino.davidka.net",
  "client_url": "https://kino.davidka.net"
}
```

| Параметр | Тип | Значение по умолчанию | Описание |
|---|---|---|---|
| `host` | `string` | `"0.0.0.0"` | IP-адрес сетевого интерфейса для прослушивания (`"0.0.0.0"` — все доступные интерфейсы, `"127.0.0.1"` — только локальный доступ). |
| `port` | `integer` | `8000` | TCP-порт, на котором запускается веб-сервер. |
| `workers` | `integer` | `1` | Количество рабочих процессов Uvicorn. |
| `reload` | `boolean` | `false` | Режим автоматической перезагрузки сервера при изменении исходного кода (Hot Reload). |
| `use_ssl` | `boolean` | `true` | Использование протокола HTTPS со сгенерированными SSL-сертификатами из директории `certs/`. |
| `mode` | `string` | `"DEV"` | Режим окружения приложения: `"DEV"` (разработка) или `"PROD"` (продакшн). |
| `debug` | `boolean` | `true` | Включение детализированных отладочных сообщений и расширенных трейсбеков. |
| `auto_launch.enabled` | `boolean` | `false` | Автоматически открывать интерфейс приложения в веб-браузере по умолчанию при старте сервера. |
| `auto_launch.delay_seconds` | `integer` | `5` | Задержка в секундах перед открытием браузера (необходима для полной инициализации сервисов). |
| `auto_start_assist_cli` | `boolean` | `false` | Автоматический запуск интерактивной командной строки Assist CLI при старте сервера. |
| `enable_assist` | `boolean` | `false` | Включение фоновой службы ассистента. |
| `enable_oauth` | `boolean` | `true` | Включение механизма авторизации пользователей через Google OAuth 2.0. |
| `enable_telegram_bot` | `boolean` | `true` | Фоновый запуск Telegram-бота при старте FastAPI сервера. |
| `enable_apps` | `boolean` | `true` | Включение панели вспомогательных системных инструментов и терминалов. |
| `use_cloudflared` | `boolean` | `true` | Использование туннеля Cloudflare Tunnel (`cloudflared`) для публикации приложения в интернет. |
| `user_domain` | `string` | `"kino.davidka.net"` | Доменное имя хоста, назначенное в туннеле Cloudflare. |
| `client_url` | `string` | `"https://kino.davidka.net"` | Базовый URL клиентского фронтенда для формирования ссылок редиректа OAuth и вебхуков. |

---

## 2. Секция `apps`

Параметры доступности вспомогательных приложений, системных терминалов и автономных микросервисов (`/apps`). Секция поддерживает форматы списков `enabled`/`disabled`, плоского массива или булевых флагов.

```json
"apps": {
  "enabled": [
    "chat",
    "windows_admin",
    "system_inspector",
    "system_control_center",
    "system_log_viewer",
    "network_terminal",
    "trading_terminal",
    "user_assistant",
    "gcloud_monitor",
    "website_monitor",
    "cloudflared_monitor"
  ],
  "disabled": []
}
```

| Параметр | Тип | Описание |
|---|---|---|
| `enabled` | `array[string]` | Список идентификаторов или алиасов активных приложений (`"chat"`, `"windows_admin"`, `"system_inspector"`, `"system_control_center"`, `"system_log_viewer"`, `"network_terminal"`, `"trading_terminal"`, `"user_assistant"`, `"gcloud_monitor"`, `"website_monitor"`, `"cloudflared_monitor"`). |
| `disabled` | `array[string]` | Список явно отключенных приложений (имеет наивысший приоритет над `enabled`). |
| `enable_all` | `boolean` | Резервный флаг доступности всех приложений при отсутствии списков `enabled`/`disabled`. |

---

## 3. Секция `telegram`

Настройки интеграции с Telegram-ботом.

```json
"telegram": {
  "bot_name": "ai_breadboard_bot"
}
```

| Параметр | Тип | Описание |
|---|---|---|
| `bot_name` | `string` | Имя (username) бота в Telegram. Секретный токен авторизации задается в `.env` переменной `TELEGRAM_BOT_TOKEN`. |

---

## 4. Секция `ai`

Управление AI-провайдерами, локальными и облачными бэкендами, пулом ключей Google Gemini и черным списком моделей.

```json
"ai": {
  "use_foundry": true,
  "foundry_base_url": "http://localhost:57708",
  "foundry_model_id": "qwen2.5-1.5b",
  "use_ollama": true,
  "ollama_base_url": "http://localhost:11434",
  "ollama_model_id": "llama3.1",
  "preload_silero": false,
  "use_agy": true,
  "agy_model_id": "agy-gemini-3.5-flash-lite",
  "use_gemini_cli": true,
  "gemini_cli_model_id": "gemini-3.1-flash-lite",
  "gemini_api_key_names": "*",
  "realtime_streaming": true,
  "unsupported_models": { ... }
}
```

| Параметр | Тип | Описание |
|---|---|---|
| `use_foundry` | `boolean` | Включение интеграции с локальным рантаймом Microsoft Foundry Local. |
| `foundry_base_url` | `string` | REST API эндпоинт локального демона Microsoft Foundry. |
| `foundry_model_id` | `string` | Имя/идентификатор модели по умолчанию для Foundry (например, `"qwen2.5-1.5b"`). |
| `use_ollama` | `boolean` | Включение интеграции с локальным сервером Ollama. |
| `ollama_base_url` | `string` | REST API эндпоинт локального сервиса Ollama (по умолчанию `"http://localhost:11434"`). |
| `ollama_model_id` | `string` | Модель Ollama по умолчанию (например, `"llama3.1"`). |
| `preload_silero` | `boolean` | Предварительная загрузка весов модели Silero (VAD/TTS) в память при старте. |
| `use_agy` | `boolean` | Включение встроенного провайдера Antigravity CLI (AGY). |
| `agy_model_id` | `string` | Модель по умолчанию для вызовов AGY (например, `"agy-gemini-3.5-flash-lite"`). |
| `use_gemini_cli` | `boolean` | Включение провайдера Google Gemini CLI. |
| `gemini_cli_model_id` | `string` | Идентификатор модели по умолчанию для Gemini CLI. |
| `gemini_api_key_names` | `string` | Фильтрация используемых ключей из пула `src/secrets/gemini_keys.json`. `"*"` — все активные ключи; либо список псевдонимов через запятую (например, `"key1,key2"`). |
| `realtime_streaming` | `boolean` | Включение потокового вывода генерации токенов в реальном времени (Server-Sent Events / SSE). |
| `unsupported_models` | `object` | Списки устаревших или неподдерживаемых моделей по провайдерам (`gemini`, `foundry`, `ollama` и др.), которые скрываются в UI и исключаются из валидации. |

---

## 5. Секция `huggingface`

Конфигурация прямого инференса моделей экосистемы HuggingFace Transformers.

```json
"huggingface": {
  "enabled": true,
  "default_model": "Qwen/Qwen2.5-0.5B-Instruct",
  "cache_dir": ""
}
```

| Параметр | Тип | Описание |
|---|---|---|
| `enabled` | `boolean` | Включение/отключение локального бэкенда HuggingFace Transformers. |
| `default_model` | `string` | Репозиторий и название модели по умолчанию на HuggingFace Hub. |
| `cache_dir` | `string` | Пользовательская папка для сохранения весов моделей. Если передана пустая строка `""`, используется стандартный системный кэш (`~/.cache/huggingface/hub`). |

---

## 6. Секция `onnx`

Параметры ускорения вычислений через ONNX Runtime и DirectML для графических процессоров (AMD, Intel, NVIDIA, NPU).

```json
"onnx": {
  "enabled": true,
  "models_dir": "models/onnx",
  "execution_provider": "DirectMLExecutionProvider",
  "default_model": "phi-3.5-mini-instruct-onnx",
  "device_id": 0,
  "olive_precision": "int4"
}
```

| Параметр | Тип | Описание |
|---|---|---|
| `enabled` | `boolean` | Включение инференса через ONNX Runtime. |
| `models_dir` | `string` | Относительный путь к локальному каталогу с ONNX-моделями. |
| `execution_provider` | `string` | Провайдер выполнения ONNX Runtime (например, `"DirectMLExecutionProvider"` для GPU/DirectX, `"CPUExecutionProvider"` для процессора). |
| `default_model` | `string` | Название директории ONNX модели по умолчанию. |
| `device_id` | `integer` | Номер графического адаптера DirectML (индекс устройства `0`, `1` и т.д.). |
| `olive_precision` | `string` | Точность квантования весов Microsoft Olive (`"int4"`, `"int8"`, `"fp16"`). |

---

## 7. Секция `openai_compat`

Подключение и регистрация любых сторонних сервисов с REST API, совместимым со спецификацией OpenAI `/v1/chat/completions`.

```json
"openai_compat": {
  "providers": {
    "openai": {
      "base_url": "https://api.openai.com/v1",
      "models": ["gpt-4o", "gpt-4o-mini"]
    },
    "deepseek": {
      "base_url": "https://api.deepseek.com/v1",
      "models": ["deepseek-chat", "deepseek-reasoner"]
    },
    "lmstudio": {
      "base_url": "http://localhost:1234/v1",
      "models": []
    }
  }
}
```

| Параметр | Тип | Описание |
|---|---|---|
| `providers` | `object` | Словарь настроек провайдеров. Каждый ключ (например, `"deepseek"`, `"lmstudio"`) содержит: |
| `providers.<name>.base_url` | `string` | Базовый эндпоинт API (например, `"http://localhost:1234/v1"`). |
| `providers.<name>.models` | `array[string]` | Список моделей, доступных для выбора в UI и агентах. Если передан пустой список `[]`, модели опрашиваются динамически через эндпоинт `/v1/models`. |

---

## 8. Секция `tts`

Настройки синтеза речи (Text-to-Speech).

```json
"tts": {
  "default_voice": "ru-RU-DmitryNeural"
}
```

| Параметр | Тип | Описание |
|---|---|---|
| `default_voice` | `string` | Идентификатор голосового профиля по умолчанию (например, Microsoft Edge TTS `"ru-RU-DmitryNeural"` или `"ru-RU-SvetlanaNeural"`). |

---

## 9. Секция `logging`

Параметры журналирования и интеллектуального анализа логов.

```json
"logging": {
  "enable_log_analyzer": false,
  "max_size_mb": 10.0
}
```

| Параметр | Тип | Описание |
|---|---|---|
| `enable_log_analyzer` | `boolean` | Включение фонового анализатора логов с кластеризацией ошибок и генерацией отчетов. |
| `max_size_mb` | `float` | Максимальный размер отдельного лог-файла в мегабайтах до выполнения ротации. |

---

## 10. Секция `pprint`

Параметры красивого форматирования JSON при сериализации и логировании.

```json
"pprint": {
  "json_indent": 6
}
```

| Параметр | Тип | Описание |
|---|---|---|
| `json_indent` | `integer` | Размер отступа в пробелах при сериализации JSON-документов. |

---

## 11. Секция `rag`

Параметры подсистемы Retrieval-Augmented Generation (поиск по базе знаний и медиатеке).

```json
"rag": {
  "mode": "rag+model"
}
```

| Параметр | Тип | Описание |
|---|---|---|
| `mode` | `string` | Режим работы RAG пайплайна: <br>• `"rag+model"` — обогащение запроса найденным контекстом с последующей генерацией LLM;<br>• `"rag_only"` — возврат только найденных релевантных фрагментов базы без генерации;<br>• `"model_only"` — прямой ответ LLM без поиска в базе RAG. |

---

## 12. Секция `ifttt`

Параметры глобальной интеграции со службой вебхуков умного дома IFTTT.

```json
"ifttt": {
  "enabled": true,
  "timeout_seconds": 10
}
```

| Параметр | Тип | Описание |
|---|---|---|
| `enabled` | `boolean` | Включение сервиса отправки вебхуков IFTTT. |
| `timeout_seconds` | `integer` | Таймаут ожидания HTTP-ответа от IFTTT API в секундах. |

---

## 13. Секция `web_search`

Конфигурация движков поиска в реальном интернете и логики фоллбэка.

```json
"web_search": {
  "engine": "gemini_cli",
  "gemini_model": "gemini-2.5-flash",
  "gemini_cli_model": "gemini-3.1-flash-lite",
  "agy_model": "agy-flash",
  "fallback_on_rag_not_found": true
}
```

| Параметр | Тип | Описание |
|---|---|---|
| `engine` | `string` | Поисковый движок по умолчанию: `"gemini_cli"`, `"gemini"` (Google Grounding), или `"agy"`. |
| `gemini_model` | `string` | Модель Gemini для прямого поиска через Google Search Grounding. |
| `gemini_cli_model` | `string` | Модель для поискового агента Gemini CLI. |
| `agy_model` | `string` | Модель для поискового агента Antigravity AGY. |
| `fallback_on_rag_not_found` | `boolean` | Автоматически выполнять веб-поиск в интернете, если в локальной базе RAG ничего не найдено по запросу пользователя. |

---

## 14. Секция `langchain`

Настройки агентного фреймворка LangChain / LangGraph и серверов протокола **Model Context Protocol (MCP)**.

```json
"langchain": {
  "enabled": true,
  "default_llm": "gemini",
  "gemini_model": "gemini-2.5-flash",
  "ollama_model": "qwen2.5:7b",
  "ollama_base_url": "http://localhost:11434",
  "mcp_servers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"],
      "transport": "stdio"
    },
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch"],
      "transport": "stdio"
    },
    "brave_search": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "transport": "stdio",
      "env": {
        "BRAVE_API_KEY": ""
      }
    }
  },
  "max_agent_steps": 15,
  "search_timeout_seconds": 60
}
```

| Параметр | Тип | Описание |
|---|---|---|
| `enabled` | `boolean` | Включение подсистемы LangChain и поддержки MCP-инструментов. |
| `default_llm` | `string` | Базовый провайдер для LangChain агентов (`"gemini"`, `"ollama"`). |
| `gemini_model` | `string` | Идентификатор модели Gemini для агентных цепочек. |
| `ollama_model` | `string` | Модель Ollama для локального запуска агентов. |
| `ollama_base_url` | `string` | URL сервера Ollama для LangChain. |
| `mcp_servers` | `object` | Реестр внешних серверов MCP. Каждый сервер содержит `command`, `args`, `transport` (`"stdio"` / `"sse"`) и опциональный словарь `env`. |
| `max_agent_steps` | `integer` | Лимит шагов рассуждения/вызовов инструментов агента за один запрос. |
| `search_timeout_seconds` | `integer` | Максимальное время ожидания ответа от инструментов поиска и MCP в секундах. |

---

## 15. Секция `agents`

Реестр предопределенных и пользовательских интеллектуальных агентов системы.

```json
"agents": {
  "items": [
    {
      "id": "travel_agent",
      "name": "Flight & Travel Agent",
      "description": "Автономный агент поиска авиабилетов и планирования путешествий...",
      "is_system": true,
      "enabled": true,
      "provider": "gemini",
      "model": "gemini-2.5-flash",
      "temperature": 0.2,
      "max_steps": 15,
      "timeout_seconds": 60,
      "tools": ["flight_search", "flight_price_calculator", "web_search", "rag_search", "python_eval"],
      "system_prompt": "Вы — интеллектуальный агент по поиску авиабилетов..."
    },
    {
      "id": "web_search_gemini",
      "name": "Gemini Search Grounding",
      "is_system": true,
      "enabled": true,
      "provider": "gemini",
      "model": "gemini-2.5-flash",
      "tools": ["web_search"]
    },
    {
      "id": "web_search_gemini_cli",
      "name": "Gemini CLI Searcher",
      "is_system": true,
      "enabled": true,
      "provider": "gemini_cli",
      "model": "gemini-3.1-flash-lite",
      "tools": ["web_search"]
    },
    {
      "id": "web_search_agy",
      "name": "Antigravity AGY Searcher",
      "is_system": true,
      "enabled": true,
      "provider": "agy",
      "model": "agy-gemma-4-26b-a4b-it",
      "tools": ["web_search"]
    },
    {
      "id": "playwright_agent",
      "name": "Playwright Browser Agent",
      "is_system": true,
      "enabled": true,
      "provider": "gemini",
      "model": "gemini-2.5-flash",
      "tools": ["web_search"]
    },
    {
      "id": "google_workspace_agent",
      "name": "Google Workspace Assistant",
      "is_system": true,
      "enabled": true,
      "provider": "gemini",
      "model": "gemini-2.5-flash",
      "tools": ["gmail_search", "gmail_create_draft", "gdrive_list_files", "gdrive_download_file", "gsheets_info", "gsheets_read", "gsheets_search", "gsheets_append"]
    },
    {
      "id": "smart_home_agent",
      "name": "Smart Home & IFTTT Controller",
      "is_system": true,
      "enabled": true,
      "provider": "gemini",
      "model": "gemini-2.5-flash",
      "tools": ["ifttt_trigger_event", "web_search", "rag_search"]
    }
  ]
}
```

### Параметры каждого агента в массиве `items`:

| Поле | Тип | Описание |
|---|---|---|
| `id` | `string` | Уникальный идентификатор агента в системе (slug). |
| `name` | `string` | Отображаемое имя агента в интерфейсе. |
| `description` | `string` | Подробное описание назначения и возможностей агента. |
| `is_system` | `boolean` | Флаг системного агента. Системные агенты встроены в ядро платформы и защищены от случайного удаления. |
| `enabled` | `boolean` | Флаг активности агента. Отключенные агенты не отображаются в списке доступных в чате. |
| `provider` | `string` | AI-провайдер для инференса агента (`"gemini"`, `"gemini_cli"`, `"agy"`, `"ollama"`, `"foundry"`). |
| `model` | `string` | Название языковой модели, используемой агентом. |
| `temperature` | `float` | Температура генерации (от `0.0` — максимальная строгость до `1.0` — высокая креативность). |
| `max_steps` | `integer` | Максимальное количество итераций ReAct-цикла агента. |
| `timeout_seconds` | `integer` | Таймаут выполнения задачи агентом в секундах. |
| `tools` | `array[string]` | Список идентификаторов доступных инструментов (`"web_search"`, `"rag_search"`, `"flight_search"`, `"ifttt_trigger_event"`, `"python_eval"` и др.). |
| `system_prompt` | `string` | Системный промпт, задающий роль, ограничения и стиль форматирования ответов агента. |

---

## 16. Секция `plugins`

Управление загрузкой и параметрами модульных плагинов платформы (`plugins/`). Поддерживает списки `enabled`/`disabled` и индивидуальные настройки плагинов.

```json
"plugins": {
  "enabled": [
    "application_log_analyzer",
    "facebook",
    "gdrive_sync",
    "generate_rag_from_codebase",
    "google_workspace",
    "ifttt",
    "invoice_processor",
    "news_feed",
    "rag_cleaner",
    "telegram_bot",
    "telegram_channel_rag",
    "user_storage"
  ],
  "disabled": []
}
```

| Параметр | Тип | Описание |
|---|---|---|
| `enabled` | `array[string]` | Список активных системных и пользовательских плагинов. Если указан, только перечисленные плагины будут загружаться в активном состоянии (`instance.enabled = True`). |
| `disabled` | `array[string]` | Список отключенных плагинов. Имеет наивысший приоритет над `enabled` и отключает соответствующие плагины. |
| `<plugin_name>` | `object` | Индивидуальный словарь конфигурации конкретного плагина с пользовательскими полями (`config`). |

---

## 17. Секция `storage`

```json
"storage": {
  "users_dir": "data/users"
}
```

| Параметр | Тип | Описание |
|---|---|---|
| `users_dir` | `string` | Относительный путь к каталогу для хранения профилей пользователей, истории диалогов и пользовательских настроек. |

---

## 18. Секция `user_settings`

```json
"user_settings": {
  "language": "en"
}
```

| Параметр | Тип | Описание |
|---|---|---|
| `language` | `string` | Язык интерфейса по умолчанию (`"en"`, `"ru"`). |

---

## 🔗 Связанная документация

- [Руководство по разделению конфигурации и секретов (`configuration.md`)](configuration.md)
- [Инструкция по установке и настройке окружения (`installation.md`)](installation.md)
- [Руководство по запуску сервисов (`RUN.md`)](RUN.md)
