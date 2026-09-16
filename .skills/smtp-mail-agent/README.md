# 📧 SMTP Mail Agent (Навык работы с SMTP почтой)

Навык для отправки электронных писем, проверки доступности почтового сервера и формирования MIME-сообщений (HTML, Plain Text, вложения, CC, BCC) через протокол SMTP.

Параметры авторизации и учетные данные изолированно хранятся в файле `secrets.json`.

---

## 🎯 Возможности

- **Безопасное хранение секретов:** Параметры подключения (`host`, `port`, `username`, `password`, `use_tls`, `use_ssl`) хранятся локально в `secrets.json` и игнорируются системой контроля версий.
- **Гибкая отправка:** Поддержка простого текста, HTML-писем, одновременной отправки копий (`--cc`) и скрытых копий (`--bcc`).
- **Файловые вложения:** Автоматическое определение MIME-типов и прикрепление произвольного числа файлов любого формата.
- **Диагностика соединения:** Автономный скрипт `test_connection.py` для быстрой проверки доступности SMTP-сервера и валидности авторизационных данных.
- **Поддержка любых провайдеров:** Корректная работа с Gmail, Яндекс, Mail.ru, Outlook/Exchange, а также локальными и корпоративными SMTP-релеями.

---

## 📁 Структура навыка

```text
.agents/skills/smtp-mail-agent/
├── SKILL.md                 # Инструкции и метаданные для LLM-агента
├── README.md                # Документация навыка на русском языке
├── secrets.json.example     # Шаблон файла конфигурации
├── scripts/
│   ├── __init__.py          # Экспорт SmtpClient, SmtpConfig, load_smtp_config
│   ├── smtp_core.py         # Основная логика работы с SMTP и MIME
│   ├── test_connection.py   # CLI-утилита проверки соединения
│   └── send_mail.py         # CLI-утилита отправки писем
└── references/
    └── configuration.md     # Справка по настройке для популярных почтовых сервисов
```

---

## 🚀 Использование

### 1. Настройка учетных данных

Скопируйте шаблон и укажите ваши параметры подключения:
```powershell
cp .agents/skills/smtp-mail-agent/secrets.json.example .agents/skills/smtp-mail-agent/secrets.json
```

Отредактируйте `.agents/skills/smtp-mail-agent/secrets.json`:
```json
{
  "smtp": {
    "host": "smtp.gmail.com",
    "port": 587,
    "use_tls": true,
    "use_ssl": false,
    "username": "user@gmail.com",
    "password": "your-app-password",
    "from_email": "user@gmail.com",
    "from_name": "AI Breadboard Assistant",
    "timeout": 30
  }
}
```

### 2. Проверка подключения

```powershell
python .agents/skills/smtp-mail-agent/scripts/test_connection.py
```

Вывод в JSON-формате:
```powershell
python .agents/skills/smtp-mail-agent/scripts/test_connection.py --json
```

### 3. Отправка писем

**Простое письмо:**
```powershell
python .agents/skills/smtp-mail-agent/scripts/send_mail.py --to recipient@example.com --subject "Тестовое письмо" --body "Привет! Это сообщение отправлено через SMTP-агента."
```

**HTML-письмо с вложением и копией:**
```powershell
python .agents/skills/smtp-mail-agent/scripts/send_mail.py `
  --to recipient@example.com `
  --cc boss@example.com `
  --subject "Отчет о выполнении задачи" `
  --html "<h2>Отчет готов</h2><p>Подробности во вложении.</p>" `
  --attach "data/report.pdf" `
  --json
```

---

## 🔒 Безопасность

- Файл `secrets.json` включен в глобальный `.gitignore`.
- Пароли и токены никогда не выводятся в открытом виде в логах и консоли.
