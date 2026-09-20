# Модуль `src.ai.agents`

Пакет автономных агентов и LangChain-инструментов платформы **AI Breadboard**.

---

## 🤖 Системные агенты

Каждый агент объявляется в виде JSON-манифеста в директории `src/ai/agents/`:

### 1. `Mail Watcher Agent` (`mail_watcher_agent.json`)
- **Назначение:** Автономный агент для мониторинга входящей почты по IMAP, поиска писем от заданного адресата, генерации структурированных дайджестов и автоматической пересылки в WhatsApp.
- **Подключенные инструменты:**
  - `mail_watch_check_sender`
  - `mail_watch_test_connection`
  - `whatsapp_send_message`
  - `whatsapp_test_connection`

### 2. `Mail Invoice Collector Agent` (`mail_invoice_agent.json`)
- **Назначение:** Агент для сбора входящих счетов-фактур, квитанций и инвойсов на трех языках (RU, EN, HE) и формирования сводной таблицы CSV.
- **Подключенные инструменты:** `mail_invoices_collect`, `mail_invoices_test_connection`.

### 3. `Smart Home Agent` (`smart_home_agent.json`)
- **Назначение:** Управление сценариями умного дома и IoT-устройствами через IFTTT.

---

## 🛠️ Набор инструментов (LangChain Tools)

Инструменты объявляются в `src/ai/agents/tools.py` с использованием декоратора `@tool`:

### Мониторинг почты и WhatsApp:
- `mail_watch_check_sender(sender, unread_only=True, mark_as_read=False, max_emails=30, folder='INBOX', notify_toast=False, forward_whatsapp='')` — проверка почты от целевого адресата с опциональной пересылкой в WhatsApp.
- `mail_watch_test_connection()` — проверка связи с IMAP-сервером.
- `whatsapp_send_message(to, message)` — отправка текстового сообщения в WhatsApp на номер в международном формате.
- `whatsapp_test_connection()` — проверка валидности токенов Meta WhatsApp Cloud API / Green API.

### Поиск и RAG:
- `web_search(query)` — актуальный поиск в интернете.
- `rag_search(query, top_k=5)` — семантический поиск по локальной базе знаний.

### Системная диагностика:
- `system_logs_analyzer(days=20, level='Critical,Error', channel='System,Application')` — анализ событий Windows Event Log.
