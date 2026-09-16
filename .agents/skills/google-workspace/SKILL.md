---
name: google-workspace
description: Universal Google Workspace Master Coordinator for Gmail, Google Drive, Google Sheets, Google Docs, Google Calendar, and Google Contacts.
description_i18n:
  en: Universal Google Workspace Master Coordinator for Gmail, Google Drive, Google Sheets, Google Docs, Google Calendar, and Google Contacts.
  ru: Главный координатор сервисов Google Workspace (Почта Gmail, Диск, Таблицы, Документы, Календарь, Контакты).
---

# 🌐 Google Workspace Master Coordinator

Единый координационный центр и мульти-агент для всех сервисов **Google Workspace** в экосистеме AI-Breadboard.

---

## 🧩 Поддерживаемые сервисы и специализированные агенты:

1. ✉️ **Gmail (`google-mail`)**: чтение, поиск писем, дайджест, черновики, отправка ответов.
2. 📁 **Google Drive (`google-drive`)**: навигация по папкам, скачивание и загрузка файлов, конвертация Docs/Sheets/Slides, RAG-индексация.
3. 📝 **Google Docs & Sheets (`google-docs`)**: создание и чтение текстов Google Документов, поиск и модификация ячеек Google Таблиц.
4. 📅 **Google Calendar (`google-calendar`)**: анализ расписания, планирование и отмена встреч, управление участниками.
5. 👥 **Google Contacts (`google-contacts`)**: поиск персон, синхронизация телефонных номеров, адресов и организаций.

---

## 🔐 Системный OAuth Плагин
Вся авторизация и управление токенами осуществляется централизованно системным плагином **`google_oauth`** (`plugins/system-plugins/google_oauth`). Токены и секреты хранятся в `src/secrets/google_accounts.json` и `src/secrets/google_oauth_tokens/`.

---

## 🚀 Комплексные сценарии и вызовы

### Сценарий 1: Назначить встречу контакту и уведомить по почте
1. Поиск контакта: `py .agents/skills/google-contacts/scripts/gcontacts_manager.py search --query "Иван"`
2. Создание события в календаре: `py .agents/skills/google-calendar/scripts/gcalendar_manager.py create --summary "Обсуждение проекта" --start "2026-09-17T15:00:00+03:00" --end "2026-09-17T16:00:00+03:00" --attendees "ivan@example.com"`
3. Отправка подтверждения по Gmail: `py .agents/skills/google-mail/scripts/gmail_manager.py send --to "ivan@example.com" --subject "Встреча по проекту" --body "Здравствуйте! Событие добавлено в ваш Google Календарь на 17 сентября в 15:00."`

### Сценарий 2: Синхронизация файлов Google Drive в базу знаний RAG
```powershell
py .agents/skills/google-drive/scripts/sync_drive_rag.py --query "mimeType = 'application/vnd.google-apps.document'" --dest "data/gdrive_docs" --output "data/gdrive_rag.jsonl"
```
