# 🔐 Руководство по настройке secrets.json для SMTP-агента

Файл `secrets.json` должен располагаться в корне навыка (`.agents/skills/smtp-mail-agent/secrets.json`) либо передаваться через аргумент `--secrets`.

> [!IMPORTANT]
> Никогда не коммитьте `secrets.json` в Git-репозиторий! Файл добавлен в `.gitignore`.

---

## 📋 Формат файла `secrets.json`

```json
{
  "smtp": {
    "host": "smtp.gmail.com",
    "port": 587,
    "use_tls": true,
    "use_ssl": false,
    "username": "your-email@gmail.com",
    "password": "xxxx xxxx xxxx xxxx",
    "from_email": "your-email@gmail.com",
    "from_name": "AI Breadboard Assistant",
    "timeout": 30
  }
}
```

---

## ⚙️ Популярные провайдеры

### 1. Gmail (Google Workspace)
- **Host**: `smtp.gmail.com`
- **Port**: `587` (с `use_tls: true`) или `465` (с `use_ssl: true`)
- **Username**: Ваш полный адрес `@gmail.com`
- **Password**: **Пароль приложения (App Password)**.
  - Включите 2-Step Verification в Google Account.
  - Перейдите в [Google App Passwords](https://myaccount.google.com/apppasswords).
  - Сгенерируйте пароль для приложения «Почта» и вставьте 16-значный код в поле `password`.

### 2. Яндекс.Почта
- **Host**: `smtp.yandex.ru`
- **Port**: `465` (`use_ssl: true`, `use_tls: false`)
- **Username**: Ваш логин или адрес `@yandex.ru`
- **Password**: **Пароль приложения Яндекс ID**.
  - Перейдите в Яндекс ID ➔ Безопасность ➔ Пароли приложений.
  - Создайте пароль типа «Почта» (IMAP/SMTP).

### 3. Mail.ru
- **Host**: `smtp.mail.ru`
- **Port**: `465` (`use_ssl: true`, `use_tls: false`) или `587` (`use_tls: true`)
- **Username**: Полный адрес `@mail.ru` (или `@bk.ru`, `@inbox.ru`)
- **Password**: **Пароль для внешних приложений**.
  - Настройки Mail.ru ➔ Безопасность ➔ Пароли для внешних приложений.

### 4. Microsoft Outlook / Office 365
- **Host**: `smtp.office365.com`
- **Port**: `587` (`use_tls: true`, `use_ssl: false`)
- **Username**: Ваш рабочий или личный email Microsoft
- **Password**: Пароль учетной записи или App Password.

---

## 🛠️ Проверка конфигурации

После создания `secrets.json` выполните тест соединения:
```powershell
python .agents/skills/smtp-mail-agent/scripts/test_connection.py
```
