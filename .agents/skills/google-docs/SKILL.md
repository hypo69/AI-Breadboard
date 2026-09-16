---
name: google-docs
description: Specialized Google Docs and Sheets Agent for creating, reading, and updating documents and spreadsheets.
description_i18n:
  en: Specialized Google Docs and Sheets Agent for creating, reading, and updating documents and spreadsheets.
  ru: Специализированный агент для работы с Google Документами и Google Таблицами (создание, чтение, поиск, добавление строк и редактирование).
---

# 📝 Google Docs & Sheets Agent

Интеллектуальный агент для работы с документами **Google Docs** и таблицами **Google Sheets**.

---

## 🎯 Назначение и Сценарии
1. **Google Docs**: создание новых документов, чтение текста, добавление параграфов и отчетов.
2. **Google Sheets**:
   - Получение метаданных книги и структуры листов.
   - Чтение ячеек и диапазонов (`read_range`).
   - Поиск данных по ячейкам (`search`).
   - Добавление новых строк данных (`append_rows`).
   - Обновление конкретных ячеек (`update_range`).

---

## 🔐 Авторизация
Использует системный плагин **`google_oauth`** и токены из пула аккаунтов.

---

## 🚀 CLI Команды

### Google Docs:
```powershell
# Создание документа
py .agents/skills/google-docs/scripts/gdocs_manager.py create --title "Отчет о тестировании"

# Чтение содержимого документа
py .agents/skills/google-docs/scripts/gdocs_manager.py read --id "<DOC_ID>"

# Добавление текста в документ
py .agents/skills/google-docs/scripts/gdocs_manager.py append --id "<DOC_ID>" --text "Новый раздел: Результаты анализа..."
```

### Google Sheets:
```powershell
# Информация о книге и листах
py .agents/skills/google-docs/scripts/gsheets_manager.py info --id "<SPREADSHEET_ID>"

# Чтение диапазона
py .agents/skills/google-docs/scripts/gsheets_manager.py read --id "<SPREADSHEET_ID>" --range "Лист1!A1:D10"

# Поиск по таблице
py .agents/skills/google-docs/scripts/gsheets_manager.py search --id "<SPREADSHEET_ID>" --query "Иванов"

# Добавление строки
py .agents/skills/google-docs/scripts/gsheets_manager.py append --id "<SPREADSHEET_ID>" --range "Лист1!A1" --data "[\"2026-09-16\", \"Задача 1\", \"Завершено\"]"
```
