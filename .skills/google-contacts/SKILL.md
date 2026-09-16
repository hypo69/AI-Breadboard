---
name: google-contacts
description: Specialized Google Contacts (People API) Agent for searching address books, fetching contact details, phone numbers, emails, and creating new contacts.
description_i18n:
  en: Specialized Google Contacts (People API) Agent for searching address books, fetching contact details, phone numbers, emails, and creating new contacts.
  ru: Специализированный агент Google Контактов для поиска в адресной книге, получения телефонов, почты и создания новых контактов.
---

# 👥 Google Contacts Agent

Интеллектуальный агент для работы с **Google Contacts (People API)** в экосистеме AI-Breadboard.

---

## 🎯 Назначение и Сценарии
1. **Поиск контактов**: быстрый поиск по имени, фамилии, адресу почты или телефону.
2. **Получение карточки**: просмотр детальных данных (организация, должности, номера, адреса).
3. **Создание контакта**: сохранение новых абонентов и деловых партнеров в адресную книгу Google.

---

## 🔐 Авторизация
Использует системный плагин **`google_oauth`** и токены пула аккаунтов.

---

## 🚀 CLI Команды

```powershell
# Список контактов
py .agents/skills/google-contacts/scripts/gcontacts_manager.py list --limit 10

# Поиск контакта по имени или фамилии
py .agents/skills/google-contacts/scripts/gcontacts_manager.py search --query "Иван"

# Создание нового контакта
py .agents/skills/google-contacts/scripts/gcontacts_manager.py create `
  --first "Иван" `
  --last "Петров" `
  --email "ivan.petrov@company.com" `
  --phone "+79991234567" `
  --org "Технологии Будущего"
```
