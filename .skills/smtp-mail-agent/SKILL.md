---
name: smtp-mail-agent
description: Autonomous SMTP email agent for dispatching messages, HTML reports, attachments, and testing SMTP server connections with credentials stored securely in secrets.json.
description_i18n:
  en: Autonomous SMTP email agent for dispatching messages, HTML reports, attachments, and testing SMTP server connections with credentials stored securely in secrets.json.
  ru: Автономный агент для отправки электронных писем, HTML-отчетов, файлов с вложениями и диагностики SMTP-соединений с хранением учетных данных в secrets.json.
---

# 📧 SMTP Mail Agent Skill

Навык для работы с электронной почтой по протоколу SMTP. Обеспечивает отправку текстовых и HTML-сообщений, прикрепление файлов, указание копий (CC/BCC) и диагностику подключения.

Учетные данные хранятся изолированно в `secrets.json`.

---

## 🎯 Назначение и триггеры активации

Активируйте этот навык, если пользователь или рабочий процесс требует:
1. Отправить электронное письмо (уведомление, отчет, файл, алерт).
2. Проверить доступность и авторизацию на почтовом SMTP-сервере.
3. Сформировать и отправить HTML-письмо с таблицами, графиками или файлами во вложении.
4. Разослать сообщение нескольким получателям или отправить копии (CC / BCC).

---

## 🚀 Протокол выполнения

### Шаг 1. Проверка наличия конфигурации `secrets.json`
Убедитесь, что в директории навыка существует файл `secrets.json`.
Если файл отсутствует, предупредите пользователя и предложите создать его на основе `secrets.json.example` (см. `references/configuration.md`).

### Шаг 2. Тестирование соединения (при необходимости или перед серией отправок)
Выполните скрипт диагностики:
```powershell
python .agents/skills/smtp-mail-agent/scripts/test_connection.py --json
```

### Шаг 3. Отправка сообщения
Используйте CLI-скрипт `send_mail.py` с соответствующими параметрами:

```powershell
# Текстовое письмо:
python .agents/skills/smtp-mail-agent/scripts/send_mail.py --to "user@example.com" --subject "Тема" --body "Текст сообщения" --json

# HTML-сообщение с вложением:
python .agents/skills/smtp-mail-agent/scripts/send_mail.py --to "user@example.com" --subject "Отчет" --html "<h1>Отчет</h1>" --attach "path/to/file.pdf" --json
```

---

## 🛠️ Скрипты и инструменты

- **`scripts/test_connection.py`**: Проверка соединения и учетных данных.
- **`scripts/send_mail.py`**: Отправка сообщений (Plain, HTML, Attachments, CC, BCC).
- **`scripts/smtp_core.py`**: Программный модуль `SmtpClient` и `load_smtp_config`.

---

## 🔒 Безопасность

> [!IMPORTANT]
> - Никогда не выводите пароли или секретные токены из `secrets.json` в чат пользователю.
> - Файл `secrets.json` защищен от коммитов через `.gitignore`.
