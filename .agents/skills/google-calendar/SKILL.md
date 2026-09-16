---
name: google-calendar
description: Specialized Google Calendar Agent for checking schedules, finding agenda, creating, modifying, and deleting events and meetings.
description_i18n:
  en: Specialized Google Calendar Agent for checking schedules, finding agenda, creating, modifying, and deleting events and meetings.
  ru: Специализированный агент Google Календаря для просмотра расписания, планирования встреч и управления событиями.
---

# 📅 Google Calendar Agent

Интеллектуальный агент для работы с **Google Calendar** в экосистеме AI-Breadboard.

---

## 🎯 Назначение и Сценарии
1. **Просмотр расписания**: получение списка предстоящих встреч на день или диапазон дат.
2. **Создание событий**: назначение встреч с указанием темы, времени начала/конца, описания и списка email участников.
3. **Удаление событий**: отмена и очистка ненужных записей календаря.

---

## 🔐 Авторизация
Использует системный плагин **`google_oauth`** и настроенный пул аккаунтов.

---

## 🚀 CLI Команды

```powershell
# Список предстоящих событий
py .agents/skills/google-calendar/scripts/gcalendar_manager.py list --limit 5

# Создание встречи с участниками
py .agents/skills/google-calendar/scripts/gcalendar_manager.py create `
  --summary "Синхронизация по релизу" `
  --start "2026-09-17T11:00:00+03:00" `
  --end "2026-09-17T12:00:00+03:00" `
  --desc "Обсуждение архитектуры и статуса сервисов Google" `
  --attendees "dev@example.com,lead@example.com"

# Удаление события
py .agents/skills/google-calendar/scripts/gcalendar_manager.py delete --id "<EVENT_ID>"
```
