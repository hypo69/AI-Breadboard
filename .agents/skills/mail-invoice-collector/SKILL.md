---
name: mail-invoice-collector
description: Connects to email mailbox via IMAP/SMTP parameters, scans incoming emails for invoices/receipts (invoices, חשבונית, счета-фактуры), extracts financial metadata, and aggregates them into a unified CSV table.
description_i18n:
  en: Connects to email mailbox via IMAP/SMTP parameters, scans incoming emails for invoices/receipts (invoices, חשבונית, счета-фактуры), extracts financial metadata, and aggregates them into a unified CSV table.
  ru: Подключается к почтовому ящику по заданным параметрам (IMAP/SMTP), находит во входящих письмах счета-фактуры (invoices, חשבונית, счета), извлекает реквизиты и формирует сводную таблицу в формате CSV.
---

# 📨 Mail Invoice Collector Skill

Навык для подключения к почтовому ящику (через IMAP с поддержкой SSL/TLS), поиска входящих счетов-фактур, квитанций и инвойсов на трех языках (**Русский**, **Английский**, **Иврит**) и сохранения извлеченных данных в сводный файл CSV.

---

## 🎯 Назначение и триггеры активации

Активируйте этот навык, если пользователь или агент запрашивает:
1. Подключиться к почтовому ящику по параметрам (хост, порт, логин, пароль / app password).
2. Найти во входящих письмах счета-фактуры, квитанции или инвойсы (`invoices`, `счета-фактуры`, `חשבונית`, `קבלה`).
3. Скачать вложенные документы (PDF, сканы, изображения) и извлечь реквизиты: номер счета, дату, компанию-поставщика, налоговый номер (ИНН/ח.פ), сумму, НДС/מע"מ и валюту.
4. Экспортировать все найденные счета в единый CSV файл (`invoices_summary.csv`).

---

## 🚀 Протокол выполнения

### Шаг 1. Передача параметров подключения
Параметры могут передаваться тремя способами:
1. **Напрямую в аргументах CLI**:
   `--host imap.example.com --user my@email.com --password "secret"`
2. **Через файл `secrets.json`**:
   Скопируйте `secrets.json.example` в `secrets.json` в директории навыка.
3. **Через переменные окружения**:
   `MAIL_IMAP_HOST`, `MAIL_USERNAME`, `MAIL_PASSWORD`.

### Шаг 2. Проверка соединения (опционально)
```powershell
python .agents/skills/mail-invoice-collector/scripts/collect_invoices_cli.py --test-only
```

### Шаг 3. Сбор счетов и генерация CSV
```powershell
# Стандартный запуск со сбором последних входящих писем:
python .agents/skills/mail-invoice-collector/scripts/collect_invoices_cli.py --output "data/invoices_collected/invoices.csv"

# Запуск с явной передачей параметров подключения:
python .agents/skills/mail-invoice-collector/scripts/collect_invoices_cli.py --host "imap.gmail.com" --user "user@gmail.com" --password "app_password" --output "data/invoices.csv" --json
```

---

## 🛠️ Структура и модули

- `scripts/mail_client.py`: Клиент подключения к IMAP, загрузка конфигурации, поиск писем и сохранение вложений.
- `scripts/invoice_parser.py`: Мультиязычный парсер финансовых реквизитов (RU, EN, HE).
- `scripts/collector.py`: Оркестратор сбора данных и экспорта в UTF-8-SIG CSV.
- `scripts/collect_invoices_cli.py`: Точка входа командной строки.
- `secrets.json.example`: Шаблон конфигурации почты.

---

## 🔒 Безопасность

> [!IMPORTANT]
> - Никогда не передавайте пароли открытым текстом в репозиторий.
> - `secrets.json` исключен из контроля версий через `.gitignore`.
> - Рекомендуется использовать специальные пароли приложений (App Passwords) вместо основного пароля аккаунта.
