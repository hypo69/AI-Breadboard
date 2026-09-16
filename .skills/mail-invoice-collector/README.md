# 📨 Mail Invoice Collector Skill

Пакет автономного сбора и извлечения счетов-фактур из входящей электронной почты с формированием сводного реестра в CSV.

---

## 📋 Описание

Навык предоставляет готовый механизм для:
- Авторизации на любых стандартных IMAP/SMTP почтовых серверах (Gmail, Outlook, Yandex, Mail.ru, корпоративные IMAP-серверы).
- Сканирования папки входящих сообщений (`INBOX` или любой другой указанной папки).
- Фильтрации писем со счетами-фактурами, налоговыми квитанциями и инвойсами на русском, английском и иврите:
  - `invoice`, `tax invoice`, `bill`, `receipt`
  - `חשבונית`, `חשבונית מס`, `חשבונית עסקה`, `קבלה`
  - `счет-фактура`, `счёт-фактура`, `счет на оплату`, `акт`
- Загрузки прикрепленных файлов (PDF, PNG, JPG, TIFF, DOCX).
- Парсинга ключевых реквизитов (номер документа, дата, продавец, налоговый номер ИНН/ח.פ, итоговая сумма, валюта, НДС/מע"מ).
- Записи всех извлеченных счетов в CSV-файл в кодировке `UTF-8-SIG`, гарантирующей корректное открытие в Microsoft Excel и Google Sheets.

---

## ⚙️ Установка и настройка

1. Перейдите в каталог навыка:
```powershell
cd .agents/skills/mail-invoice-collector
```

2. Скопируйте шаблон секретов и настройте ваши параметры подключения:
```powershell
copy secrets.json.example secrets.json
```

---

## 🚀 Использование через CLI

### 1. Проверка соединения
```powershell
python scripts/collect_invoices_cli.py --test-only
```

### 2. Сбор счетов в CSV
```powershell
python scripts/collect_invoices_cli.py --output "data/invoices_collected/mail_invoices_summary.csv"
```

### 3. Передача учетных данных напрямую
```powershell
python scripts/collect_invoices_cli.py `
  --host "imap.gmail.com" `
  --user "account@gmail.com" `
  --password "xxxx xxxx xxxx xxxx" `
  --output "data/invoices_summary.csv" `
  --json
```

---

## 📊 Структура выходного CSV файла

| Поле | Назначение |
|---|---|
| `email_date` | Дата входящего письма |
| `email_from` | Отправитель сообщения |
| `email_subject` | Тема сообщения |
| `invoice_number` | Номер счета / חשבונית / Invoice No |
| `invoice_date` | Дата выставления счета |
| `due_date` | Срок оплаты (Due date) |
| `vendor_name` | Название компании / поставщика |
| `vendor_tax_id` | Налоговый идентификатор (ИНН / ח.פ / VAT ID) |
| `customer_name` | Имя покупателя |
| `total_amount` | Сумма к оплате |
| `currency` | Валюта (ILS, USD, EUR, RUB) |
| `tax_amount` | Сумма налога (НДС / מע"מ / VAT) |
| `items_summary` | Описание услуг / товаров |
| `attachment_file` | Имя файла сохраненного вложения |
| `status` | Статус парсинга (`attachment_parsed`, `body_parsed`) |
