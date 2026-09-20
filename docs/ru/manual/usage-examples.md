# Примеры использования

Практические сценарии работы с AI-Breadboard. Все примеры предполагают запущенный сервер (`.\run.ps1`).

---

## Чат с моделью через CLI

```powershell
# Выбрать провайдера и модель
assist select provider gemini
assist select model gemini-2.0-flash

# Отправить запрос
assist model ask "Объясни разницу между RAG и fine-tuning"

# Переключиться на локальную модель
assist select provider ollama
assist select model ollama:llama3.1
assist model ask "Привет, как дела?"
```

---

## Загрузка документов в базу знаний

```powershell
# Через REST API
curl -X POST http://localhost:8000/api/user/files/upload `
  -H "Cookie: auth_token=<токен>" `
  -F "file=@report.pdf" `
  -F "subfolder=rag"
```

После загрузки создайте RAG-коллекцию и проиндексируйте файл:

```powershell
# Создать коллекцию
curl -X POST http://localhost:8000/api/user/rags `
  -H "Content-Type: application/json" `
  -d '{"name": "Мои документы", "description": "Рабочие отчёты"}'

# Построить индекс
curl -X POST http://localhost:8000/api/user/rags/<rag_id>/build `
  -H "Content-Type: application/json" `
  -d '{"provider": "local_tfidf"}'
```

---

## Диаризация аудиозаписи

Загрузите запись совещания — получите транскрипцию с разбивкой по собеседникам, summary и action items:

```powershell
curl -X POST http://localhost:8000/api/audio/diarize `
  -F "file=@meeting.mp3" `
  -F "language=ru"
```

Сохранить результат в базу знаний:

```powershell
curl -X POST http://localhost:8000/api/audio/save-to-rag `
  -H "Content-Type: application/json" `
  -d '{"title": "Совещание 2026-09-14", "summary": "...", "transcript": [...]}'
```

---

## Поиск по Telegram-каналу

1. В Admin UI (`/admin` → Plugins → `telegram_channel_rag`) укажите имя канала и нажмите **Fetch & Rebuild RAG Index**
2. После индексации используйте поиск:

```powershell
curl -X POST http://localhost:8000/api/admin/plugins/telegram_channel_rag/action `
  -H "Content-Type: application/json" `
  -d '{"action_id": "search", "params": {"query": "анонс нового релиза"}}'
```

Каждый результат содержит прямую ссылку `https://t.me/channel/<message_id>`.

---

## Синхронизация с Google Docs

```powershell
# Синхронизировать Google Docs в RAG-коллекцию
curl -X POST http://localhost:8000/api/user/rags/<rag_id>/sync-google-docs `
  -H "Content-Type: application/json" `
  -d '{"query": "mimeType = '\''application/vnd.google-apps.document'\'' and trashed = false"}'
```

---

## Управление умным домом через IFTTT

```powershell
# Через Admin UI: Plugins → ifttt → trigger_event
curl -X POST http://localhost:8000/api/admin/plugins/ifttt/action `
  -H "Content-Type: application/json" `
  -d '{"action_id": "trigger_event", "params": {"event": "lights_off", "value1": "bedroom"}}'
```

---

## Обработка счёта (invoice)

```powershell
curl -X POST http://localhost:8000/api/admin/plugins/invoice_processor/action `
  -H "Content-Type: application/json" `
  -d '{"action_id": "parse_invoice", "params": {"file_path": "data/invoices/invoice_001.pdf"}}'
```

Возвращает структурированные поля: сумма, дата, контрагент, реквизиты.

---

## Анализ логов сервера

```powershell
# Через навык log-analyzer
assist model ask "Проанализируй последние ошибки сервера"

# Или через Admin UI: Plugins → log_analyzer → Generate Health Report
```

---

## Запуск агента с навыками

```python
# Пример вызова через REST API
import httpx

response = httpx.post("http://localhost:8000/api/agents/run", json={
    "agent": "react",
    "model": "gemini-2.0-flash",
    "task": "Найди последние новости по теме 'AI agents' и сделай краткое резюме",
    "skills": ["news-reader", "rag-search-manager"]
})
print(response.json())
```

---

## Мониторинг почты и пересылка в WhatsApp (`mail-watcher` & `whatsapp`)

Автоматическое отслеживание важных писем от конкретного адресата (руководителя, партнера или сервиса) и пересылка их текста в WhatsApp:

### 1. Разовая проверка с выводом превью
```powershell
python .agents/skills/mail-watcher/scripts/mail_watcher_cli.py --sender "boss@company.com" --check-once
```

### 2. Фоновый мониторинг с пересылкой в WhatsApp
```powershell
# Проверка почты каждые 60 секунд, отправка всплывающего окна Toast и пересылка текста письма в WhatsApp
python .agents/skills/mail-watcher/scripts/mail_watcher_cli.py `
  --sender "director@company.com" `
  --interval 60 `
  --whatsapp "+79991234567" `
  --toast
```

### 3. Отправка сообщений в WhatsApp через AI-агента
```python
# Использование инструмента агентом
from src.ai.agents.tools import mail_watch_check_sender, whatsapp_send_message

# Проверить почту и переслать новые письма
mail_watch_check_sender.invoke({
    "sender": "partner@domain.com",
    "unread_only": True,
    "forward_whatsapp": "+79991234567"
})
```

---

Смотрите также: [Каталог навыков](../skills/catalog.md) · [Каталог плагинов](../plugins/catalog.md) · [Конфигурация](secrets.md)
