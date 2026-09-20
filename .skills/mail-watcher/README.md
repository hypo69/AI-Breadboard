# 📬 Навык Mail Watcher (Мониторинг писем от заданного отправителя)

Навык для подключения к почтовому ящику (через IMAP с поддержкой SSL/TLS), мониторинга входящих писем от заданного адресата, сохранения состояния обработанных сообщений и формирования оповещений (консоль, Windows Toast, JSON, интеграция с LLM).

---

## 📋 Возможности

- **Фильтрация по отправителю**: точное совпадение адреса, поиск по части email или отображаемому имени отправителя.
- **Поддержка фильтра непрочитанных**: обработка только новых/непрочитанных писем (`UNSEEN`) либо всей истории.
- **Дедупликация и состояние**: локальное сохранение обработанных UID писем в файл состояния, чтобы исключить дублирование уведомлений при повторных проверках.
- **Мультиязычный декодер**: корректное декодирование RFC 2047 заголовков и текстовых частей тела (UTF-8, Windows-1251, ISO-8859-8 и др.).
- **Оповещения**:
  - Вывод в консоль / логгер.
  - Windows Toast Notification (всплывающие системные уведомления Windows).
  - JSON-вывод для автоматизации и вызовов AI-агентами.
- **Режимы работы**: разовая проверка (`--check-once`) или постоянный опрос ящика с настраиваемым интервалом (`--interval`).

---

## ⚙️ Конфигурация

Параметры подключения загружаются из следующих источников (в порядке приоритета):
1. Аргументы командной строки (`--host`, `--user`, `--password`, `--port`, `--folder`).
2. Файл `secrets.json` в директории навыка (`.agents/skills/mail-watcher/secrets.json`).
3. Переменные окружения: `MAIL_IMAP_HOST`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_IMAP_PORT`, `MAIL_FOLDER`.

### Пример `secrets.json`
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

---

## 💻 Примеры использования CLI

```powershell
# 1. Проверка соединения
python .agents/skills/mail-watcher/scripts/mail_watcher_cli.py --test-connection

# 2. Разовая проверка писем от конкретного адресата
python .agents/skills/mail-watcher/scripts/mail_watcher_cli.py --sender "client@domain.com" --check-once

# 3. Проверка непрочитанных с всплывающим уведомлением Windows
python .agents/skills/mail-watcher/scripts/mail_watcher_cli.py --sender "director@company.com" --unread-only --toast

# 4. Фоновый мониторинг раз в минуту
python .agents/skills/mail-watcher/scripts/mail_watcher_cli.py --sender "boss@work.com" --interval 60 --toast
```
