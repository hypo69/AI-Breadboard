---
name: google-drive
description: Specialized Google Drive Agent for searching files, downloading, exporting Docs/Sheets/PDFs, uploading files, and RAG knowledge base ingestion.
description_i18n:
  en: Specialized Google Drive Agent for searching files, downloading, exporting Docs/Sheets/PDFs, uploading files, and RAG knowledge base ingestion.
  ru: Специализированный агент Google Диска для поиска файлов, экспорта, загрузки и синхронизации с базой знаний RAG.
---

# 📁 Google Drive Agent

Интеллектуальный агент для работы с хранилищем **Google Drive** в экосистеме AI-Breadboard.

---

## 🎯 Назначение и Сценарии
1. **Поиск файлов**: поиск файлов и папок по имени, типу (`mimeType`), дате изменения.
2. **Экспорт и Скачивание**: конвертация Google Docs в `.docx`, Google Sheets в `.xlsx`, слайдов в `.pdf`, выгрузка бинарных файлов.
3. **Загрузка файлов**: загрузка локальных отчетов, логов, архивов на Google Drive в заданные папки.
4. **Синхронизация с RAG**: автоматическая выгрузка документов организации и индексация в векторную базу знаний.

---

## 🔐 Авторизация
Агент использует системный плагин **`google_oauth`** и токены из `src/secrets/google_accounts.json`.

---

## 🚀 CLI Команды

```powershell
# Список файлов на Диске
py .agents/skills/google-drive/scripts/gdrive_manager.py list --limit 10

# Поиск файлов по имени
py .agents/skills/google-drive/scripts/gdrive_manager.py list --query "name contains 'Отчет'"

# Скачивание документа
py .agents/skills/google-drive/scripts/gdrive_manager.py download --id "<FILE_ID>" --mime "application/vnd.google-apps.document" --dest "data/docs/report.docx"

# Загрузка локального файла
py .agents/skills/google-drive/scripts/gdrive_manager.py upload --file "data/exports/summary.pdf"

# Синхронизация папки с базой RAG
py .agents/skills/google-drive/scripts/sync_drive_rag.py --query "mimeType = 'application/vnd.google-apps.document'" --dest "data/gdrive_docs" --output "data/gdrive_chunks.jsonl"
```
