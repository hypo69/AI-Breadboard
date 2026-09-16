# Архитектура интеграции Google Workspace (Gmail, Drive, Sheets, Docs)

Документация по архитектуре интеграции сервисов Google Workspace в стек AI-агентов, оркестрацию моделей и веб-интерфейс платформы AI Breadboard.

---

## 1. Обзор архитектуры

Интеграция с Google Workspace позволяет языковым моделям и ReAct-агентам автономно взаимодействовать с корпоративными сервисами Google:
- **Gmail**: поиск, чтение входящих писем и создание черновиков.
- **Google Диск**: поиск, листинг, выгрузка и экспорт документов Google Docs / Sheets в стандартные локальные форматы (`.docx`, `.xlsx`, `.pdf`).
- **Google Таблицы (Sheets)**: инспекция структуры книги, чтение диапазонов ячеек, текстовый поиск по ячейкам и добавление новых строк.
- **RAG-индексация**: автоматическая выгрузка документов с Диска для индексации через `rag-cleaner`.

---

## 2. Модель авторизации и пул аккаунтов (`src/secrets`)

Для управления доступом к нескольким аккаунтам Google используется модуль `src.secrets.google_accounts_state` и хранилище секретов `src/secrets/`:

1. **Пул аккаунтов (`src/secrets/google_accounts.json`)**:
   - Позволяет подключать несколько аккаунтов (например: `work`, `personal`, `analytics`).
   - Автоматическая ротация при исчерпании лимитов или квот (`mark_account_exhausted` / `reset_account_status`).
   - Выбор аккаунта по умолчанию (`default_account`) или прямое указание `account_name` в запросах.
   - Структура конфигурации:
     ```json
     {
       "default_account": "work",
       "accounts": {
         "work": {
           "email": "user@company.com",
           "type": "oauth2",
           "credentials_file": "src/secrets/google_work_oauth2.json",
           "token_file": "src/secrets/tokens/work_token.json",
           "status": "active"
         }
       }
     }
     ```

2. **Форматы учетных данных**:
   - **OAuth 2.0 Client (`credentials.json` + `tokens/<name>_token.json`)**: для работы с личной и корпоративной почтой Gmail, Диском и Таблицами.
   - **Service Account (`service_account.json`)**: для фонового серверного взаимодействия с Google Sheets и Drive.

3. **Связка с `google_auth.py`**:
   - Модуль `.agents/skills/google-workspace/scripts/google_auth.py` автоматически опрашивает менеджер пула `src.secrets.google_accounts_state` с возможностью выбора аккаунта через `account_name`.


---

## 3. Набор инструментов LangChain (`src.ai.agents.tools`)

Все инструменты реализованы как нативные функции LangChain с декоратором `@tool` и защитной обработкой ошибок:

| Инструмент | Описание | Основные параметры |
|---|---|---|
| **`gmail_search`** | Поиск и чтение писем по фильтрам | `query: str` (напр. `'is:unread'`), `limit: int` |
| **`gmail_create_draft`** | Создание черновика письма в Gmail | `to: str`, `subject: str`, `body: str` |
| **`gdrive_list_files`** | Поиск и листинг файлов/папок на Google Диске | `query: str`, `limit: int` |
| **`gdrive_download_file`** | Экспорт/выгрузка файлов в локальную директорию | `file_id: str`, `mime_type: str`, `dest_path: str` |
| **`gsheets_info`** | Получение структуры и списка листов таблицы | `spreadsheet_id: str` |
| **`gsheets_read`** | Чтение значений ячеек в диапазоне A1 | `spreadsheet_id: str`, `range_name: str` |
| **`gsheets_search`** | Поиск строк в таблице по текстовому запросу | `spreadsheet_id: str`, `query: str`, `range_name: str` |
| **`gsheets_append`** | Добавление строки данных в таблицу | `spreadsheet_id: str`, `range_name: str`, `values_json: str` |

---

## 4. Системный агент `Google Workspace Assistant`

В конфигурации платформы зарегистрирован специализированный агент:
- **ID**: `google_workspace_agent`
- **Конфигурация (`config.json`)**:
  ```json
  {
    "id": "google_workspace_agent",
    "name": "Google Workspace Assistant",
    "description": "Агент для работы с почтой Gmail, файлами на Google Диске, Google Таблицами и Документами",
    "is_system": true,
    "enabled": true,
    "provider": "gemini",
    "model": "gemini-2.5-flash",
    "temperature": 0.2,
    "max_steps": 15,
    "timeout_seconds": 60,
    "tools": [
      "gmail_search",
      "gmail_create_draft",
      "gdrive_list_files",
      "gdrive_download_file",
      "gsheets_info",
      "gsheets_read",
      "gsheets_search",
      "gsheets_append"
    ]
  }
  ```
- **Системный промпт**: `WORKSPACE_AGENT_SYSTEM_PROMPT` в [`src/ai/agents/prompts.py`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/src/ai/agents/prompts.py).

---

## 5. Интеграция с Web UI (`agents_metadata.json`)

Инструменты Google Workspace зарегистрированы в файле метаданных `src/fastapi/agents_metadata.json` под категорией `google_workspace`. Это позволяет:
- Выбирать любые инструменты Google Workspace во вкладке **Agents** веб-интерфейса при создании кастомных агентов.
- Получать структурированное описание параметров для генератора промптов (AI Architect).

---

## 6. Безопасность и обработка ошибок (Graceful Degradation)

- Если учетные данные Google не настроены, инструменты не вызывают сбой агента (panic / unhandled exception), а возвращают информативное JSON-сообщение об ошибке авторизации.
- Это позволяет агенту корректно объяснить пользователю необходимость настройки файлов `credentials.json` или `.env`.
