# `src/ai/agents` — Модуль автономных ReAct-агентов

Этот пакет реализует **слой исполняемых AI-агентов** платформы AI Breadboard.
Агенты работают по паттерну **ReAct** (Reasoning + Acting): получают запрос,
самостоятельно выбирают инструменты, вызывают их в цикле и возвращают
структурированный результат.

---

## Содержание

- [Структура пакета](#структура-пакета)
- [Как это работает](#как-это-работает)
- [Системные агенты](#системные-агенты)
- [Каталог инструментов](#каталог-инструментов)
- [MCP-клиент](#mcp-клиент)
- [Как создать своего агента](#как-создать-своего-агента)
- [Как зарегистрировать агента в Admin UI](#как-зарегистрировать-агента-в-admin-ui)
- [Правила и ограничения](#правила-и-ограничения)

---

## Структура пакета

```
src/ai/agents/
├── __init__.py                  # Публичный API пакета
├── agent.py                     # MediaSearchAgent — общий агент поиска
├── travel_agent.py              # TravelAgent — поиск авиабилетов
├── system_logs_agent.py         # SystemLogsAgent — анализ Windows Event Log
├── tools.py                     # Все @tool-функции (~20 инструментов)
├── prompts.py                   # Системные промпты для каждого типа агента
├── mcp_client.py                # MCPClientManager — подключение MCP-серверов
│
│   # JSON-манифесты агентов (читаются Admin UI через router_agents.py)
├── web_search_gemini.json
├── web_search_gemini_cli.json
├── web_search_agy.json
├── travel_agent.json
├── system_logs_agent.json
├── google_workspace_agent.json
├── mail_watcher_agent.json
├── mail_invoice_agent.json
├── playwright_agent.json
└── smart_home_agent.json
```

---

## Как это работает

```
Запрос пользователя
        │
        ▼
  Агент (Agent class)
  ├── _get_llm()          — ленивая инициализация LLM (Gemini / Ollama)
  ├── _build_system_prompt() — сборка промпта из prompts.py
  └── search() / run()
        │
        ▼
  create_react_agent(llm, tools, prompt)   ← LangGraph
        │
        ▼
  ReAct-цикл (до max_steps итераций):
  ┌─────────────────────────────────────┐
  │  Thought → Action → Observation     │
  │  (LLM решает, какой tool вызвать)   │
  └─────────────────────────────────────┘
        │
        ▼
  Парсинг ответа → dict { action, ... }
```

Агент получает **нативные инструменты** из `tools.py` и опционально
**MCP-инструменты** через `MCPClientManager` (Playwright, Gemini Search и др.).

---

## Системные агенты

### `MediaSearchAgent` (`agent.py`)

Общий агент поиска. Используется как базовый шаблон и для поиска медиаконтента.

| Параметр | Значение |
|---|---|
| Инструменты | `web_search`, `rag_search`, `python_eval`, `file_read` |
| Метод запуска | `await agent.search(query)` → `dict` |
| Потоковый режим | `agent.search_stream(query)` → `AsyncIterator[dict]` |
| Формат ответа | `{ "action": "info" \| "torrent" \| "player" \| "error", ... }` |

---

### `TravelAgent` (`travel_agent.py`)

Автономный агент поиска авиабилетов и планирования маршрутов.

| Параметр | Значение |
|---|---|
| Инструменты | `flight_search`, `flight_price_calculator`, `web_search`, `rag_search`, `python_eval`, `file_read` |
| Метод запуска | `await agent.search(query)` → `dict` |
| Потоковый режим | `agent.search_stream(query)` → `AsyncIterator[dict]` |
| Формат ответа | `{ "action": "flight_results" \| "error", "text": "Markdown-отчёт" }` |

Агент выдаёт три категории рекомендаций: 🟢 самый дешёвый, ⚡ самый быстрый,
⭐ оптимальный по цене/качеству.

---

### `SystemLogsAgent` (`system_logs_agent.py`)

SRE-агент для анализа журналов Windows Event Log. Не использует LangGraph —
работает напрямую через `system_logs_analyzer` + LLM.

| Параметр | Значение |
|---|---|
| Инструменты | `system_logs_analyzer` |
| Метод запуска | `await agent.run(user_query, active_llm)` → `str` (Markdown) |
| Парсинг периода | Автоматически извлекает «20 дней», «две недели» из текста запроса |
| Формат ответа | Markdown-отчёт: сводка → критические инциденты → RCA → план устранения |

---

### Агенты, управляемые только через JSON-манифест

Следующие агенты не имеют отдельного Python-класса — они конфигурируются
декларативно и запускаются через `router_agents.py` с выбранной LLM:

| Файл | Агент | Инструменты |
|---|---|---|
| `web_search_gemini.json` | Gemini Search Grounding | `web_search` |
| `web_search_gemini_cli.json` | Gemini CLI Search | `web_search` |
| `web_search_agy.json` | AGY Web Search | `web_search` |
| `google_workspace_agent.json` | Google Workspace Assistant | `gmail_search`, `gmail_create_draft`, `gdrive_list_files`, `gdrive_download_file`, `gsheets_*` |
| `mail_watcher_agent.json` | Mail Watcher | `mail_watch_check_sender`, `mail_watch_test_connection`, `whatsapp_send_message` |
| `mail_invoice_agent.json` | Mail Invoice Collector | `mail_invoices_collect`, `mail_invoices_test_connection` |
| `smart_home_agent.json` | Smart Home Agent | `ifttt_trigger_event` |
| `playwright_agent.json` | Playwright Browser Agent | MCP Playwright tools |

---

## Каталог инструментов

Все инструменты объявлены в `tools.py` через декоратор `@tool` из `langchain_core.tools`.

### Поиск и данные

| Инструмент | Описание |
|---|---|
| `web_search(query)` | Поиск в интернете через текущую AI-модель платформы |
| `rag_search(query, top_k=5)` | Семантический поиск по локальной базе знаний |
| `python_eval(code)` | Безопасное выполнение математических выражений Python |
| `file_read(file_path)` | Чтение текстового файла проекта (до 10 000 символов) |

### Авиабилеты и путешествия

| Инструмент | Описание |
|---|---|
| `flight_search(origin, destination, date, ...)` | Поиск рейсов с прямыми ссылками на Google Flights, Aviasales, Skyscanner |
| `flight_price_calculator(base_price, ...)` | Точный расчёт стоимости с багажом, налогами, скидками |

### Google Workspace

| Инструмент | Описание |
|---|---|
| `gmail_search(query, limit, account_name)` | Поиск писем в Gmail |
| `gmail_create_draft(to, subject, body, ...)` | Создание черновика письма |
| `gdrive_list_files(query, limit, ...)` | Список файлов на Google Диске |
| `gdrive_download_file(file_id, ...)` | Скачивание / экспорт файла с Диска |
| `gsheets_info(spreadsheet_id, ...)` | Структура Google Таблицы |
| `gsheets_read(spreadsheet_id, range_name, ...)` | Чтение диапазона ячеек |
| `gsheets_search(spreadsheet_id, query, ...)` | Поиск по таблице |
| `gsheets_append(spreadsheet_id, range_name, values_json, ...)` | Добавление строк |

### Системная диагностика

| Инструмент | Описание |
|---|---|
| `system_logs_analyzer(days, level, channel, ...)` | Анализ Windows Event Log с кластеризацией инцидентов |

### Почта и мессенджеры

| Инструмент | Описание |
|---|---|
| `mail_invoices_collect(output_csv, max_emails, folder)` | Сбор счетов-фактур из IMAP |
| `mail_invoices_test_connection()` | Проверка IMAP-подключения (mail-invoice-collector) |
| `mail_watch_check_sender(sender, ...)` | Поиск писем от отправителя с пересылкой в WhatsApp |
| `mail_watch_test_connection(account)` | Проверка IMAP-подключения (mail-watcher) |
| `whatsapp_send_message(to, message)` | Отправка сообщения в WhatsApp |
| `whatsapp_test_connection()` | Проверка WhatsApp API |

### Умный дом

| Инструмент | Описание |
|---|---|
| `ifttt_trigger_event(event_name, value1, ...)` | Триггер события IFTTT Webhooks |

---

## MCP-клиент

`MCPClientManager` (`mcp_client.py`) — асинхронный контекстный менеджер,
который подключается к MCP-серверам из секции `langchain.mcp_servers` в
`config.json` и возвращает LangChain-совместимые инструменты.

```python
async with MCPClientManager() as mcp:
    mcp_tools = await mcp.get_tools()
    all_tools = native_tools + mcp_tools
```

Поддерживаемые транспорты: `stdio`, `sse`, `streamable_http`.

Тестирование отдельного сервера:

```python
result = await MCPClientManager.test_server_connection(
    server_id="playwright",
    server_cfg={"transport": "stdio", "command": "npx", "args": ["@playwright/mcp"]}
)
# result: { "status": "ok", "tools_count": 12, "latency_ms": 340.5, ... }
```

---

## Как создать своего агента

### Шаг 1 — Добавить промпт в `prompts.py`

```python
MY_AGENT_SYSTEM_PROMPT = """Вы — специализированный агент платформы AI Breadboard.
Ваша задача: <опишите задачу>.

Доступные инструменты:
- web_search: поиск актуальной информации
- rag_search: поиск по базе знаний

Отвечайте структурированно на русском языке.
"""
```

### Шаг 2 — Создать класс агента

Создайте файл `src/ai/agents/my_agent.py`:

```python
# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any, AsyncIterator, Dict

from logger import logger
from src.utils.jjson import j_loads_ns
from .prompts import MY_AGENT_SYSTEM_PROMPT, TOOL_SELECTION_GUIDELINES
from .tools import web_search, rag_search, python_eval
from .mcp_client import MCPClientManager


class MyAgent:
    """Агент для <описание задачи>."""

    def __init__(self, config_path: Path = Path('config.json'), ai_model: Any = None) -> None:
        self.config = j_loads_ns(config_path)
        self.ai_model = ai_model

        langchain_cfg = getattr(self.config, 'langchain', object())
        self.llm_type = getattr(langchain_cfg, 'default_llm', 'gemini')
        self.max_steps = getattr(langchain_cfg, 'max_agent_steps', 15)
        self.timeout = getattr(langchain_cfg, 'search_timeout_seconds', 60)
        self._llm = None
        self._langchain_cfg = langchain_cfg

        # Выберите только нужные инструменты
        self.native_tools = [web_search, rag_search, python_eval]

        logger.info(f'[MyAgent] Инициализирован: llm={self.llm_type}')

    def _get_llm(self) -> Any:
        """Ленивая инициализация LLM."""
        if self._llm is not None:
            return self._llm

        if self.llm_type == 'gemini':
            from langchain_google_genai import ChatGoogleGenerativeAI
            model_name = getattr(self._langchain_cfg, 'gemini_model', 'gemini-2.5-flash')
            api_key = os.environ.get('GEMINI_API_KEY', '')
            if not api_key:
                from src.ai.gemini.gemini_api_key_state import load_api_keys
                loaded, _, _ = load_api_keys()
                api_key = next((k for k in loaded if k.startswith('AIzaSy')), loaded[0] if loaded else '')
            self._llm = ChatGoogleGenerativeAI(
                model=model_name, google_api_key=api_key, temperature=0.1
            )
        else:
            from langchain_ollama import ChatOllama
            self._llm = ChatOllama(
                model=getattr(self._langchain_cfg, 'ollama_model', 'qwen2.5:7b'),
                base_url=getattr(self._langchain_cfg, 'ollama_base_url', 'http://localhost:11434'),
                temperature=0.1,
            )
        return self._llm

    def _build_system_prompt(self) -> str:
        return '\n\n'.join([MY_AGENT_SYSTEM_PROMPT, TOOL_SELECTION_GUIDELINES])

    async def run(self, query: str) -> Dict[str, Any]:
        """Выполнить запрос через ReAct-цикл."""
        try:
            from langgraph.prebuilt import create_react_agent

            llm = self._get_llm()
            all_tools = list(self.native_tools)

            # Опционально: подключить MCP-инструменты
            try:
                async with MCPClientManager() as mcp:
                    mcp_tools = await mcp.get_tools()
                    if mcp_tools:
                        all_tools.extend(mcp_tools)
            except Exception as e:
                logger.warning(f'[MyAgent] MCP недоступен: {e}')

            try:
                agent = create_react_agent(llm, all_tools, prompt=self._build_system_prompt())
            except TypeError:
                agent = create_react_agent(llm, all_tools, state_modifier=self._build_system_prompt())

            result = await asyncio.wait_for(
                agent.ainvoke({'messages': [('user', query)]}),
                timeout=self.timeout,
            )

            messages = result.get('messages', [])
            content = getattr(messages[-1], 'content', '') if messages else ''
            return {'action': 'result', 'text': content}

        except asyncio.TimeoutError:
            return {'action': 'error', 'data': {'message': f'Таймаут ({self.timeout}с)'}}
        except Exception as e:
            logger.error(f'[MyAgent] Ошибка: {e}')
            return {'action': 'error', 'data': {'message': str(e)}}

    async def run_stream(self, query: str) -> AsyncIterator[Dict[str, Any]]:
        """Потоковый запуск с промежуточными статусами."""
        yield {'status': '🔍 Анализирую запрос...'}
        result = await self.run(query)
        yield {'status': '✅ Готово'}
        yield {'result': result}
```

### Шаг 3 — Добавить инструмент (если нужен новый)

Добавьте в `tools.py`:

```python
from langchain_core.tools import tool

@tool
async def my_custom_tool(param: str) -> str:
    """Описание инструмента — LLM читает этот docstring для выбора инструмента.

    Args:
        param: Описание параметра.
    """
    try:
        # логика инструмента
        return f"Результат: {param}"
    except Exception as e:
        logger.error(f'[my_custom_tool] Ошибка: {e}')
        return f'{{"error": "{e}"}}'
```

**Правила написания инструментов:**
- Декоратор `@tool` обязателен — без него LangGraph не увидит инструмент
- `docstring` — это то, что LLM читает при выборе инструмента; пишите чётко
- Всегда возвращайте `str` (JSON-строку для структурированных данных)
- Оборачивайте тело в `try/except` и возвращайте `{"error": "..."}` при сбое
- Синхронные инструменты — `def`, асинхронные — `async def`

### Шаг 4 — Экспортировать из `__init__.py`

```python
# В __init__.py добавьте:
from .my_agent import MyAgent
from .tools import my_custom_tool

__all__ = [
    ...,
    "MyAgent",
    "my_custom_tool",
]
```

### Шаг 5 — Создать JSON-манифест для Admin UI

Создайте `src/ai/agents/my_agent.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "id": "my_agent",
  "name": "My Custom Agent",
  "description": "Краткое описание — отображается в Admin UI",
  "is_system": false,
  "enabled": true,
  "provider": "gemini",
  "model": "gemini-2.5-flash",
  "temperature": 0.2,
  "max_steps": 15,
  "timeout_seconds": 60,
  "tools": ["web_search", "rag_search", "my_custom_tool"],
  "system_prompt": "Вы — специализированный агент. Ваша задача: ..."
}
```

После перезапуска сервера агент появится в Admin UI → вкладка **Agents**.

---

## Как зарегистрировать агента в Admin UI

`router_agents.py` автоматически сканирует все `*.json`-файлы в этой директории.
Никакой дополнительной регистрации не требуется — достаточно создать файл.

Управление через REST API:

```
GET    /api/agents          — список всех агентов
POST   /api/agents          — создать агента
PUT    /api/agents/{id}     — обновить агента
DELETE /api/agents/{id}     — удалить (только is_system: false)
POST   /api/agents/test     — тест-запуск агента
POST   /api/agents/generate-prompt  — AI-генерация промпта
GET    /api/agents/tools    — каталог доступных инструментов
GET    /api/agents/providers — список провайдеров и моделей
```

---

## Правила и ограничения

### Архитектурные правила

- **Один агент — одна задача.** Не делайте универсальных агентов с 15+ инструментами.
  Оптимальный набор: 3–6 инструментов.
- **Ленивая инициализация LLM.** Создавайте `_llm` только при первом вызове `_get_llm()`,
  не в `__init__`. Это ускоряет старт сервера.
- **Таймаут обязателен.** Всегда оборачивайте `agent.ainvoke()` в `asyncio.wait_for()`.
  Значение берите из `config.json → langchain.search_timeout_seconds`.
- **Возвращайте dict, не строку.** Метод `run()` / `search()` должен возвращать
  `dict` с ключом `action` для единообразия обработки на стороне API.

### Правила для инструментов

- Не импортируйте тяжёлые зависимости на уровне модуля — только внутри функции.
- Инструменты, работающие с внешними сервисами (Gmail, IFTTT), должны
  обрабатывать отсутствие конфигурации и возвращать `{"error": "..."}`.
- Не добавляйте инструменты с побочными эффектами (запись в БД, отправка почты)
  без явного параметра-подтверждения.

### Правила для JSON-манифестов

- `id` должен совпадать с именем файла без `.json`
- `is_system: true` — защищает агента от удаления через Admin UI
- `tools` — список id инструментов из `tools.py`; используется Admin UI для
  отображения, но не влияет на Python-класс агента напрямую

### Совместимость LangGraph

`create_react_agent` менял сигнатуру между версиями. Всегда используйте
паттерн с fallback:

```python
try:
    agent = create_react_agent(llm, tools, prompt=system_prompt)
except TypeError:
    agent = create_react_agent(llm, tools, state_modifier=system_prompt)
```

---

## Связанные документы

- [`docs/ru/guides/creating-agents.md`](../../../../docs/ru/guides/creating-agents.md) — общее введение в агенты
- [`docs/ru/guides/standard-agents.md`](../../../../docs/ru/guides/standard-agents.md) — руководство по Python ReAct-агентам
- [`docs/ru/api/agents.md`](../../../../docs/ru/api/agents.md) — справочник REST API агентов
- [`docs/ru/cook-book/ch06_agents_and_mcp.md`](../../../../docs/ru/cook-book/ch06_agents_and_mcp.md) — рецепты агентов и MCP
- [`src/api/router_agents.py`](../../api/router_agents.py) — FastAPI-роутер агентов
- [`src/skills/registry.py`](../../skills/registry.py) — реестр навыков (альтернативный способ расширения)
