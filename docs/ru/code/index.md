# ⚙️ Техническая документация исходного кода (docs/ru/code)

В этом каталоге собрана полная русскоязычная документация по исходному коду, модулям, API-эндпоинтам и утилитам проекта **AI Breadboard**.

---

## 🗂️ Навигатор по подсистемам

### 1. Ядро системы (`core/`)
Главный сервисный уровень бэкенда:
- [**Обзор `core`**](core/README.md) — архитектура ядра и правила проектирования.
- [**AI Orchestrator (`core.ai`)**](core/ai/README.md) — единая точка входа `UnifiedChatModel`, маршрутизация по провайдерам, менеджер моделей `ModelManager`.
- [**Google Gemini SDK (`core.ai.gemini`)**](core/ai/gemini/README.MD) — клиент Gemini API, ротация пула ключей, отказоустойчивость и вызов инструментов.
- [**RAG Subsystem (`core.rag`)**](core/rag/README.md) — доменно-независимая архитектура RAG-First, движок `RAGEngine`, `RulesRAG`, `UserRAG`.
- [**FastAPI Routers (`core.fastapi`)**](core/fastapi/README.md) — роутеры HTTP, WebSocket и SSE эндпоинтов.
- [**Secrets & API Keys (`core.secrets`)**](core/secrets/README.md) — отслеживание квот, блокировка на 24 часа при 429, round-robin ключей.
- [**Skills Registry (`core.skills`)**](core/skills/README.md) — автоматическое обнаружение и загрузка навыков (`SKILL.md`).
- [**TTS Engines (`core.tts`)**](core/tts/README.md) — синтез речи Microsoft Edge, Google TTS, Silero.
- [**Logger (`core.logger`)**](core/logger/README.MD) — синглтон-логгер, цветная консоль, файлы и JSON.
- [**External Clients (`core.clients`)**](core/clients/README.md) — адаптеры Foundry, Ollama, Telegram.
- [**User Manager (`core.user_manager`)**](core/user_manager/README.md) — база пользователей SQLite, профили и роли.
- [**Utils & Converters (`core.utils`)**](core/utils/README.md) — переиспользуемые функции, [конверторы данных](core/utils/convertors/README.md).

---

### 2. Веб-интерфейс (`webinterface/`)
Фронтенд-модули и пользовательские панели:
- [**Обзор веб-интерфейса**](webinterface/README.md) — архитектура, локализация i18n, Bootstrap 5 и ES Modules.
- [**Административная панель**](webinterface/admin/README.md) & [**Вкладка Admin**](webinterface/admin_tab/README.md) — системные настройки и мониторинг.
- [**Интерактивный чат с ИИ**](webinterface/chat/README.md) — потоковый чат с переключателем моделей и распознаванием тегов.
- [**Вкладка моделей**](webinterface/models_tab/README.md) — выбор моделей, настройка гиперпараметров, мониторинг ключей.
- [**ReAct-агенты**](webinterface/agents_tab/README.md) — верстак сборки и тестирования агентов.
- [**RAG и поиск**](webinterface/search_tab/README.md) — семантический поиск по медиатеке с выводом шагов рассуждения.
- [**Медиаплеер**](webinterface/cosmicplayer/README.md) — стриминг видео с поддержкой продолжения серий.
- [**Пульт ДУ**](webinterface/rc/README.md) — мобильный веб-пульт управления воспроизведением через WebSocket.
- [**Источники и аудит дисков**](webinterface/sources_tab/README.md) — сканирование медиабиблиотеки, аудит целостности и дубликатов.
- [**Синтез речи (TTS)**](webinterface/tts_tab/README.md) — выбор голосов и параметров воспроизведения.
- [**Управление пользователями**](webinterface/users_tab/README.md) — создание учетных записей и распределение прав.
- [**Инструкции и промпты**](webinterface/instructions_tab/README.md) — редактор и версионирование системных инструкций.
- [**Пользовательский интерфейс (Mini App)**](webinterface/user/README.md) — легкий мобильный интерфейс.
- [**Справка**](webinterface/help/README.md) — руководство пользователя и подсказки.

---

### 3. Серверы Model Context Protocol (`.mcp/`)
Шлюзы протокола MCP для внешних AI-ассистентов (Claude Desktop, Cursor, Antigravity):
- [**Обзор MCP-серверов**](.mcp/README.md):
  - `gemini_search_mcp_server.py` — веб-поиск с Google Grounding.
  - `agy_search_mcp_server.py` — поиск через Antigravity SDK.
  - `langchain_mcp_server.py` — ReAct-агент с доступом к RAG и Python.
  - `fastapi_mcp_server.py` — клиент к локальному бэкенду.
  - `unicorn_mcp_server.py` — управление процессами сервера.
  - `playwright/` — автоматизация браузера.

---

### 4. Навыки агентов (`.agents/skills/`, `.gemini/skills/`)
Модульные навыки:
- [**Навык `file-saver`**](.agents/skills/file-saver/README.md) — безопасное сохранение файлов на диск.
- [**Навык `web-chat-cli`**](.agents/skills/web-chat-cli/README.md) — консольный интерфейс чата с моделью.

---

### 5. Инструкции, промпты и Codex (`.ai/`)
Централизованный хаб знаний:
- [**Единый источник инструкций**](.ai/instructions/README.md) — стандарты `CODE_RULES.md`, регламенты и воркфлоу.
- [**База знаний Codex**](.ai/instructions/knowledge/codex/README.md) — архитектурная декомпозиция и карта проекта.
- [**Системные промпты**](.ai/prompts/README.md) — инструкции для чата и диктора, [архив версий чата](.ai/prompts/chat/versions/README.md) и [диктора](.ai/prompts/narrator/versions/README.md).
- [**Инструменты ИИ**](.ai/tools/README.md) — скрипты для агентов ([RAG пересборщик](.ai/tools/ai/README.md), [аудит зависимостей](.ai/tools/setup/README.md)).

---

### 6. Установка, зависимости и сопровождение
- [**Корневой README**](README.MD) — концепция макетной платы и быстрый старт.
- [**Модульный установщик (`install/`)**](install/README.md) — архитектура развертывания, сертификаты SSL, регистрация в PATH.
- [**Зависимости (`req/`)**](req/README.md) — модульные файлы `requirements-*.txt`.
- [**Инструменты разработчика (`scripts/`)**](scripts/README.md) — [утилиты разработки](scripts/dev/README.md) и [регламентное обслуживание](scripts/maintenance/README.md).
- [**Тестовый набор (`tests/`)**](tests/README.md) — модульные, интеграционные тесты и фикстуры Pytest.
- [**Песочница (`SANDBOX/`)**](SANDBOX/README.md) — прототипы и [простой ассистент](SANDBOX/AI%20Assistant/Simple%20Assistant/README.md).
