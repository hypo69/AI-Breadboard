---
name: mail-watcher
description: Connects to email mailbox via IMAP, monitors incoming emails from a specified sender, extracts message contents, and dispatches notifications (console, Windows Toast, JSON, AI alerts).
description_i18n:
  en: Connects to email mailbox via IMAP, monitors incoming emails from a specified sender, extracts message contents, and dispatches notifications (console, Windows Toast, JSON, AI alerts).
  ru: Подключается к почтовому ящику по IMAP, отслеживает входящие письма от заданного отправителя, извлекает содержимое и выдает оповещения (консоль, Windows Toast, JSON, AI-уведомления).
---

# 📬 Mail Watcher Skill

Навык для подключения к почтовому ящику через протокол IMAP (с поддержкой SSL/TLS), отслеживания входящих писем от определенного адресата (по email, имени или маске), сохранения состояния прочитанных сообщений и генерации оповещений.

---

## 🎯 Назначение и триггеры активации

Активируйте этот навык, если пользователь или агент запрашивает:
1. Проверить почту на наличие новых писем от конкретного человека или сервиса (например, от `boss@company.com`, `notifications@github.com`, банка или клиента).
2. Запустить фоновый мониторинг почтового ящика с проверкой раз в N секунд/минут.
3. Получить уведомление (всплывающее Windows Toast, в консоли или через AI-агента) при поступлении письма от указанного адресата.
4. Проверить статус подключения к почтовому серверу.

---

## 🚀 Протокол использования

### Шаг 1. Передача параметров подключения
Параметры могут передаваться тремя способами:
1. **Через файл `secrets.json`** в директории навыка (`.agents/skills/mail-watcher/secrets.json`):
   ```json
   {
     "host": "imap.gmail.com",
     "port": 993,
     "use_ssl": true,
     "username": "user@gmail.com",
     "password": "your_app_password",
     "folder": "INBOX"
   }
   ```
2. **Через аргументы CLI**:
   `--host imap.example.com --user my@email.com --password "secret"`
3. **Через переменные окружения**:
   `MAIL_IMAP_HOST`, `MAIL_USERNAME`, `MAIL_PASSWORD`.

### Шаг 2. Проверка подключения (опционально)
```powershell
python .agents/skills/mail-watcher/scripts/mail_watcher_cli.py --test-connection
```

### Шаг 3. Разовая проверка писем от отправителя
```powershell
# Проверка новых писем от конкретного адресата
python .agents/skills/mail-watcher/scripts/mail_watcher_cli.py --sender "boss@company.com" --check-once

# Проверка только непрочитанных с показом всплывающего уведомления Windows Toast
python .agents/skills/mail-watcher/scripts/mail_watcher_cli.py --sender "boss@company.com" --unread-only --toast

# Проверка с автоматической пересылкой содержимого письма в WhatsApp
python .agents/skills/mail-watcher/scripts/mail_watcher_cli.py --sender "boss@company.com" --whatsapp "+79991234567" --check-once

# Вывод в формате JSON
python .agents/skills/mail-watcher/scripts/mail_watcher_cli.py --sender "boss@company.com" --json
```

### Шаг 4. Запуск циклического мониторинга
```powershell
# Проверка каждые 60 секунд с пересылкой в WhatsApp и показом Toast
python .agents/skills/mail-watcher/scripts/mail_watcher_cli.py --sender "boss@company.com" --interval 60 --whatsapp "+79991234567" --toast
```

---

## 🛠️ Модули и структура

- `scripts/mail_watcher.py`: Основной класс `MailWatcher`, модели `MailWatcherConfig`, `WatchedMessage`, управление IMAP-соединением, фильтрация, отслеживание состояния и отправка уведомлений.
- `scripts/mail_watcher_cli.py`: Точка входа командной строки.
- `secrets.json.example`: Шаблон конфигурации почтового ящика.

---

## 🔒 Безопасность

> [!IMPORTANT]
> - Никогда не сохраняйте пароли в коде. Используйте `secrets.json` (исключен в `.gitignore`) или переменные окружения.
> - Для сервисов вроде Gmail, Yandex, Mail.ru используйте специальные **пароли приложений** (App Passwords).
