# Руководство по интеграции Google Workspace (Gmail, Google Drive, Google Docs)

Практическое руководство по подключению и сценариям работы с экосистемой Google в AI Breadboard.

---

## 🎯 Назначение

Навык и интеграции Google Workspace позволяют:
1. **Разбирать и категоризировать входящую почту (Gmail)**: получать умные дайджесты, фильтровать письма и генерировать черновики ответов.
2. **Работать с Google Диском**: выполнять поиск по документам, скачивать файлы и экспортировать Google Документы/Таблицы.
3. **Автоматически синхронизировать файлы с базой знаний RAG**: парсить и чанковать документы из облака в локальный векторный индекс.

---

## 🔑 Предварительная настройка: OAuth 2.0 Credentials

Для безопасного подключения без передачи паролей используется стандартный протокол Google OAuth 2.0:

1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/).
2. Создайте новый проект (или выберите существующий).
3. В разделе **APIs & Services** включите:
   - **Gmail API**
   - **Google Drive API**
   - **Google Docs API**
4. Перейдите в **Credentials** ➔ **Create Credentials** ➔ **OAuth client ID**:
   - Application type: `Desktop app` (Настольное приложение).
5. Скачайте полученный JSON-файл и сохраните его в корне проекта как `credentials.json` (путь можно переопределить через переменную окружения `GOOGLE_CREDENTIALS_PATH`).

---

## 🛠️ Основные сценарии и CLI-команды

### 1. Умный поиск и разбор почты (Gmail)
Скрипт `gmail_manager.py` позволяет выполнять поиск по фильтрам Gmail:

```powershell
# Поиск последних 5 непрочитанных писем
python .agents/skills/google-workspace/scripts/gmail_manager.py --query "is:unread" --limit 5

# Поиск писем от конкретного адресата
python .agents/skills/google-workspace/scripts/gmail_manager.py --query "from:partner@example.com" --limit 10
```

### 2. Поиск и работа с Google Диском
Скрипт `gdrive_manager.py` поддерживает поиск и автоконвертацию облачных форматов (Google Docs ➔ `.docx`, Google Sheets ➔ `.xlsx`, Google Slides ➔ `.pdf`):

```powershell
# Поиск файлов, содержащих в имени слово "Отчет"
python .agents/skills/google-workspace/scripts/gdrive_manager.py --query "name contains 'Отчет'" --limit 10
```

### 3. Автоматическая синхронизация папки Google Диска с RAG
Скрипт `sync_drive_rag.py` объединяет облачное хранилище с пайплайном `rag-cleaner`:

```powershell
python .agents/skills/google-workspace/scripts/sync_drive_rag.py --query "trashed = false" --dest "data/gdrive_sync" --output "data/gdrive_rag.jsonl"
```

---

## ⚡ Интерактивное подключение через MCP

Для прямого взаимодействия с Google Диском в режиме чата через протокол MCP добавьте конфигурацию в `mcp_config.json`:

```json
{
  "mcpServers": {
    "gdrive": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-gdrive"],
      "env": {
        "CLIENT_ID": "<ВАШ_CLIENT_ID>",
        "CLIENT_SECRET": "<ВАШ_CLIENT_SECRET>"
      }
    }
  }
}
```

---

## 🔒 Безопасность и хранение токенов

- Файлы `credentials.json` и `token.json` содержат чувствительные токены и **никогда не должны попадать в публичный репозиторий Git** (они добавлены в `.gitignore`).
- Обновление refresh-токенов происходит автоматически в модуле `google_auth.py`.
