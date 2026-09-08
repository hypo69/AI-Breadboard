---
name: google-workspace
description: Google Workspace integration (Gmail, Google Drive, Google Docs) for email triage, document search, and RAG ingestion.
---

# 🌐 Google Workspace & Drive Skill

Навык для прямой интеграции ассистента с сервисами **Google Workspace** (Gmail, Google Drive, Google Docs).

---

## 🎯 Назначение и Сценарии

1. **Email Triage & Digest (Разбор почты)**: поиск непрочитанных, выделение важного, создание черновиков ответов.
2. **Drive RAG Ingestion (Синхронизация базы знаний)**: экспорт Google Docs/PDF и индексация через `rag-cleaner`.
3. **Файловый менеджмент**: поиск файлов по содержимому и названиям на Google Диске.

---

## 🚀 Скрипты и CLI

### 1. Поиск писем и дайджест:
```powershell
python .agents/skills/google-workspace/scripts/gmail_manager.py --query "is:unread" --limit 10
```

### 2. Поиск файлов на Диске:
```powershell
python .agents/skills/google-workspace/scripts/gdrive_manager.py --query "name contains 'Report'" --limit 10
```

### 3. Автоматическая синхронизация Google Drive с RAG-пайплайном:
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
