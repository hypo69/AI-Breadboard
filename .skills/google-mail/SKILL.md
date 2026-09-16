---
name: google-mail
description: Specialized Google Mail (Gmail) Agent for searching, fetching, reading email threads, drafting and sending emails.
description_i18n:
  en: Specialized Google Mail (Gmail) Agent for searching, fetching, reading email threads, drafting and sending emails.
  ru: Специализированный агент Gmail для поиска, чтения писем, составления черновиков и отправки сообщений.
---

# ✉️ Google Mail (Gmail) Agent

Интеллектуальный агент для работы с сервисом **Gmail** в экосистеме AI-Breadboard.

---

## 🎯 Назначение и Сценарии
1. **Поиск писем**: поиск по отправителю, теме, ярлыкам (`is:unread`, `from:boss@example.com`, `has:attachment`).
2. **Анализ содержимого**: получение полного текста, заголовков и сниппетов входящей почты.
3. **Создание черновиков**: генерация и подготовка черновиков ответов.
4. **Отправка писем**: автоматическая или подтверждаемая отправка сообщений.

---

## 🔐 Авторизация
Агент использует системный плагин **`google_oauth`** и пул токенов из `src/secrets/google_accounts.json` / `google_oauth_tokens/`.

---

## 🚀 CLI Команды

```powershell
# Поиск непрочитанных писем
py .agents/skills/google-mail/scripts/gmail_manager.py search --query "is:unread" --limit 5

# Поиск писем от конкретного отправителя
py .agents/skills/google-mail/scripts/gmail_manager.py search --query "from:support@google.com"

# Создание черновика
py .agents/skills/google-mail/scripts/gmail_manager.py draft --to "client@example.com" --subject "Отчет по проекту" --body "Здравствуйте! Отправляю обновленный статус."

# Прямая отправка письма
py .agents/skills/google-mail/scripts/gmail_manager.py send --to "client@example.com" --subject "Встреча" --body "Встреча подтверждена."
```
