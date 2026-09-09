---
name: google-workspace
description: Google Workspace integration (Gmail, Google Drive, Google Sheets, Google Docs) for email triage, document search, spreadsheets manipulation, and RAG ingestion.
description_i18n:
  en: Google Workspace integration (Gmail, Google Drive, Google Sheets, Google Docs) for email triage, document search, spreadsheets manipulation, and RAG ingestion.
  ru: Интеграция с Google Workspace (Gmail, Google Диск, Google Таблицы, Google Документы) для сортировки писем, поиска документов, работы с таблицами и RAG.
---

# 🌐 Google Workspace (Drive, Sheets, Docs & Gmail) Skill

Навык для прямой интеграции ассистента с сервисами **Google Workspace** (Google Drive, Google Sheets, Google Docs, Gmail).

---

## 🎯 Назначение и Сценарии

1. **Google Sheets (Таблицы)**: чтение диапазонов ячеек, добавление строк, поиск по таблицам, получение структуры листов.
2. **Email Triage & Digest (Разбор почты)**: поиск непрочитанных писем, создание черновиков ответов в Gmail.
3. **Drive & Docs**: поиск файлов, выгрузка Google Docs / Sheets в локальные форматы (.docx, .xlsx, .pdf).
4. **Drive RAG Ingestion (Синхронизация базы знаний)**: экспорт Google Docs/PDF и автоматическая индексация через `rag-cleaner`.

---

## 🔐 Авторизация

Модуль `google_auth.py` автоматически обнаруживает и поддерживает два режима:
1. **Service Account (Уровень проекта)**:
   - Переменная `GOOGLE_APPLICATION_CREDENTIALS` или `GOOGLE_SERVICE_ACCOUNT_JSON` в `.env`.
   - Файлы `service_account.json` / `google_service_account.json` в корне проекта.
   - Работает бесшовно в фоновом режиме (рекомендуется для Sheets и Drive).
2. **OAuth 2.0 Client (Пользовательский доступ)**:
   - Файлы `credentials.json` + `token.json` в корне проекта.

---

## 🚀 Скрипты и CLI

### 1. Работа с Google Таблицами (Sheets):
```powershell
# Информация о книге и листах:
python .agents/skills/google-workspace/scripts/gsheets_manager.py info --id "<SPREADSHEET_ID>"

# Чтение диапазона ячеек:
python .agents/skills/google-workspace/scripts/gsheets_manager.py read --id "<SPREADSHEET_ID>" --range "Sheet1!A1:E20"

# Поиск текста в таблице:
python .agents/skills/google-workspace/scripts/gsheets_manager.py search --id "<SPREADSHEET_ID>" --query "Ваш_Запрос"

# Добавление строки в таблицу:
python .agents/skills/google-workspace/scripts/gsheets_manager.py append --id "<SPREADSHEET_ID>" --range "Sheet1!A1" --data "[\"Значение1\", \"Значение2\", \"Значение3\"]"
```

### 2. Поиск файлов на Google Диске:
```powershell
python .agents/skills/google-workspace/scripts/gdrive_manager.py --query "name contains 'Report'" --limit 10
```

### 3. Поиск писем и дайджест (Gmail):
```powershell
python .agents/skills/google-workspace/scripts/gmail_manager.py --query "is:unread" --limit 10
```

### 4. Автоматическая синхронизация Google Drive с RAG-пайплайном:
```powershell
python .agents/skills/google-workspace/scripts/sync_drive_rag.py --query "mimeType = 'application/vnd.google-apps.document'" --dest "data/gdrive_docs" --output "data/gdrive_rag.jsonl"
```

---

## ⚙️ Настройка MCP (Model Context Protocol)

Для интерактивного вызова инструментов Google Drive из среды Antigravity добавьте в конфигурацию MCP (`mcp_config.json`):

```json
{
  "mcpServers": {
    "gdrive": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-gdrive"],
      "env": {
        "CLIENT_ID": "<YOUR_CLIENT_ID>",
        "CLIENT_SECRET": "<YOUR_CLIENT_SECRET>"
      }
    }
  }
}
```

