# Справочник консольных скриптов проекта

В корневой директории проекта `ai-assistant` расположен набор служебных скриптов на Python и PowerShell для управления базой данных медиатеки, синхронизации с торрент-клиентом qBittorrent, диагностики и запуска сервисов.

**Точка входа:** `manage_tools.py` — единый CLI для всех скриптов.

Все скрипты должны запускаться из активированного виртуального окружения проекта:
```powershell
# Активация venv в PowerShell
.\venv\Scripts\Activate.ps1
```

---

## 0. Универсальный CLI (Рекомендуется)

### `manage_tools.py`

Единая точка входа для всех инструментов. Поддерживает 6 групп команд.

**Формат:**
```powershell
py manage_tools.py <группа> <команда> [аргументы...]
```

**Группы команд:**

| Группа | Команды | Описание |
|--------|---------|----------|
| `media` | `scan`, `complete` | Сканирование и заполнение медиатеки |
| `torrents` | `assign`, `ids`, `state`, `path`, `clear`, `orchestrator` | Синхронизация с qBittorrent |
| `db` | `update`, `sizes`, `fill` | Обслуживание базы данных |
| `check` | `db`, `data`, `media_type`, `series` | Базовая диагностика |
| `audit` | `disk`, `media` | Глубокая проверка целостности |
| `knowledge` | `extract`, `add`, `init` | Управление знаниями проекта |

**Примеры:**
```powershell
# Сканирование медиатеки
py manage_tools.py media scan --disk "диск 2" --path "E:"

# Привязка торрентов к медиа
py manage_tools.py torrents ids --disk "ДИСК 1"

# Обновление размеров
py manage_tools.py db sizes E: L:

# Аудит диска
py manage_tools.py audit disk "ДИСК 1"

# Извлечение знаний из чатов
py manage_tools.py knowledge extract --file chat.md
```

Для подробной справки по любой команде используйте `--help` или см. соответствующие разделы ниже.

---

## 1. Управление медиатекой (Media Organizer)

### `manage_tools.py media scan`
Основная точка входа для сканирования дисков, разметки медиа через Gemini и составления отчетов. Эквивалент `run_media_organizer.py` через CLI.

**Примеры:**
```powershell
# Интерактивный режим (запрос имени диска)
py manage_tools.py media scan

# Полное сканирование конкретного диска
py manage_tools.py media scan --disk "диск 2" --path "E:"

# Разметка одного тайтла
py manage_tools.py media scan --title "The Bear" --type series --disk "диск 2"

# Сброс и полное пересканирование
py manage_tools.py media scan --force --disk "1" "2" --path "E:" "L:"

# Ревизия файлов
py manage_tools.py media scan --audit --path "E:"

# Специализированные режимы
py manage_tools.py media scan --rebuild --disk "диск 2"
py manage_tools.py media scan --web  # запуск веб-интерфейса
```

**Примечание:** Дополнительные аргументы (после `--`) передаются в `run_media_organizer.py`.

### `manage_tools.py media complete`
Заполнение пропущенных метаданных в медиатеке.

**Примеры:**
```powershell
py manage_tools.py media complete
py manage_tools.py media complete --disk "ДИСК 1"
py manage_tools.py media complete --title "Фауда"
```

---

## 2. Интеграция с qBittorrent

Для работы этих скриптов необходимо, чтобы в файле `config.json` в секции `qbittorrent` были настроены параметры подключения (`host`, `port`, `user`, `pass`), а сам клиент qBittorrent был запущен.

### `manage_tools.py torrents assign`
Сопоставляет активные торренты в qBittorrent с записями в SQLite БД по названию и назначает им категории (например, Кино, Сериалы).
* **Использование:**
  ```powershell
  py manage_tools.py torrents assign
  ```
* **Принцип работы**: Использует fuzzy-matching (коэффициент перекрытия токенов). Порог совпадения — `0.5`. При совпадении автоматически создает категорию в qBittorrent и присваивает ее торренту.

### `manage_tools.py torrents ids`
Интеллектуальное сопоставление медиафайлов на диске с раздачами в qBittorrent через Gemini API.
* **Использование:**
  ```powershell
  # Обработать все диски
  py manage_tools.py torrents ids
  # Обработать только конкретный диск
  py manage_tools.py torrents ids --disk "ДИСК 1"
  # Холостой запуск без изменения БД
  py manage_tools.py torrents ids --dry-run
  ```

### `manage_tools.py torrents state`
Запускает принудительную перепроверку хеша (Force Recheck) в qBittorrent для всех торрентов, которые привязаны к медиатеке в БД (имеют непустой `torrent_id`).
* **Использование:**
  ```powershell
  py manage_tools.py torrents state
  ```

### `manage_tools.py torrents path`
Синхронизирует пути сохранения торрентов в qBittorrent с путями файлов, зарегистрированными в БД медиатеки. Полезно, если файлы были перемещены на другой диск или в другую папку в процессе упорядочивания медиатеки.
* **Использование:**
  ```powershell
  py manage_tools.py torrents path
  ```
* **Принцип работы**: Ожидаемый путь сохранения торрента устанавливается как родительская директория медиафайла из БД. Если пути расходятся, скрипт вызывает `set_location` в qBittorrent.

### `manage_tools.py torrents clear`
Служебный скрипт для полной очистки категорий и тегов у всех раздач в qBittorrent.
* **Использование:**
  ```powershell
  py manage_tools.py torrents clear
  ```

### `manage_tools.py torrents orchestrator`
Оркестратор торрентов — комплексный скрипт для автоматического управления раздачами.
* **Использование:**
  ```powershell
  py manage_tools.py torrents orchestrator
  ```

---

## 3. Обслуживание базы данных и хранилищ

### `manage_tools.py db update`
Служебный скрипт для обновления схемы базы данных SQLite (`plugins/media_organizer/data/media.db`).
* **Использование:**
  ```powershell
  py manage_tools.py db update
  ```
* **Принцип работы**: Создает резервную копию `media.db.backup`, переименовывает старую таблицу `media` в `media_old`, после чего создает новые пустые таблицы `media`, `series_episodes` и `duplicates` с обновленной структурой.

### `manage_tools.py db sizes`
Обновляет размеры файлов медиатеки в БД (колонка `media_size` таблицы `media`) и актуализирует информацию о свободном месте на жестких дисках в таблице `storage`.
* **Использование:**
  ```powershell
  # Обновить размеры по всем дискам из БД
  py manage_tools.py db sizes
  # Обновить только для конкретных букв дисков и записать их статистику
  py manage_tools.py db sizes E: L:
  ```

### `manage_tools.py db fill`
Заполнение пропущенных метаданных через `fill_missing_metadata.py`.
* **Использование:**
  ```powershell
  py manage_tools.py db fill
  py manage_tools.py db fill --disk "ДИСК 1"
  ```

---

## 4. Диагностика и проверка данных

Скрипты для быстрого сбора информации о состоянии БД:

### `manage_tools.py check db`
Выводит список таблиц и структуру колонок таблиц `media` и `series_episodes`.

### `manage_tools.py check data`
Выводит первые 3 строки таблицы `media`, первые 5 строк `series_episodes` и количество дубликатов в JSON-виде.

### `manage_tools.py check media_type`
Выводит количество записей в таблице `media`, сгруппированных по типам (`movie`, `series`, `anime`, `NULL`).

### `manage_tools.py check series`
Выводит первые 5 записей с типом `series` из базы данных.

**Также доступны оригинальные скрипты:**
* `list_models.py` — выводит список всех доступных в аккаунте моделей Google Gemini.
* `get_schema.py` — выводит SQL-запрос создания таблицы `media` (ее актуальную схему в БД).

---

## 5. Аудит и проверка целостности

### `manage_tools.py audit disk`
Скрипт для глубокого аудита медиатеки на конкретных дисках. Проверяет соответствие файлов на диске и записей в БД.

* **Использование:**
  ```powershell
  py manage_tools.py audit disk "Диск 1" "Диск 2"
  py manage_tools.py audit disk "ДИСК 1" --auto-fix
  py manage_tools.py audit disk "ДИСК 1" --yes
  ```
* **Особенности**:
  - Позиционные аргументы: список имён дисков из `DISK_MAP` внутри скрипта.
  - Флаг `--yes` (`-y`): автоматическая обработка обнаруженных новых файлов через AI (без подтверждения).
  - Флаг `--auto-fix`: автоматическое исправление данных при обнаружении расхождений.
  - Безопасность: пропускает диски, не найденные в `DISK_MAP` или с несуществующими путями.

### `manage_tools.py audit media`
Аудит медиафайлов — проверка целостности записей в БД.
* **Использование:**
  ```powershell
  py manage_tools.py audit media
  py manage_tools.py audit media --path "E:"
  ```

---

## 6. Управление знаниями

### `manage_tools.py knowledge extract`
Извлечение знаний из архивов чатов с помощью Gemini API.
* **Использование:**
  ```powershell
  py manage_tools.py knowledge extract --file doc/chats/chat_379dea55_archive.md
  ```

### `manage_tools.py knowledge add`
Ручное добавление записи в реестр знаний.
* **Использование:**
  ```powershell
  py manage_tools.py knowledge add --topic "Тема" --summary "Описание" --decision "Решение 1" --file "main.py"
  ```

### `manage_tools.py knowledge init`
Инициализация пустого реестра знаний.
* **Использование:**
  ```powershell
  py manage_tools.py knowledge init
  ```

Дополнительно: `manage_knowledge.py` — оригинальный скрипт с расширенными возможностями.

---

## 7. Скрипты запуска сервисов (Лончеры)

Все лончеры в **корне проекта** `C:\ai-assistant\`. Полная документация: `.ai_instructions/knowledge/LAUNCHER_GUIDE.md`

| Лончер | Что запускает | Пример запуска |
|--------|--------------|----------------|
| `run.ps1` | Всё сразу: Foundry + uvicorn | `.\run.ps1` |
| `Run-Unicorn.ps1` | FastAPI сервер (`main.py`) через uvicorn | `.\Run-Unicorn.ps1` |
| `Run-Foundry.ps1` | Azure AI Foundry (локальная LLM) | `.\Run-Foundry.ps1 -Action start` |
| `Run-LightServer.ps1` | Лёгкий HTTP-сервер | `.\Run-LightServer.ps1` |
| `install.ps1` / `install.cmd` | Установка зависимостей и venv | `.\install.ps1` |
| `install_ssl_cert.ps1` | Генерация локального SSL-сертификата | `.\install_ssl_cert.ps1` |
| `run_tests.ps1` | Запуск тестов pytest | `.\run_tests.ps1 -Coverage` |

**Для агентов ИИ:** `& "C:\ai-assistant\Run-<ServiceName>.ps1"`

---

## 8. Рекомендации по автоматическому запуску для ИИ-ассистентов (AI Execution Guidelines)

ИИ-ассистенты (включая pair programming агентов) могут и должны самостоятельно принимать решение о запуске консольных скриптов проекта без явного указания пользователя в следующих сценариях:

### 8.1 Синхронизация данных после файловых операций
Если в ходе выполнения задачи ИИ-ассистент производил переименование, перенос или удаление медиафайлов/директорий:
* **MUST**: Запустить `py manage_tools.py db sizes` для пересчета размеров в БД и обновления свободного места в таблице `storage`.
* **SHOULD**: Запустить `py manage_tools.py torrents path`, чтобы qBittorrent узнал о новых путях расположения файлов.
* **MAY**: Запустить `py manage_tools.py audit media <пути>` для проверки отсутствия расхождений между диском и БД.

### 8.2 Добавление или обновление торрентов
При добавлении новых раздач в qBittorrent или привязке существующих к медиатеке:
* **SHOULD**: Запустить `py manage_tools.py torrents assign` для автоматической разметки категорий на основе названий из БД.
* **MAY**: Запустить `py manage_tools.py torrents state` для запуска принудительной проверки (Force Recheck) перенесенных раздач.

### 8.3 Изменение схемы базы данных
Если ИИ-ассистент внес изменения в структуру таблиц SQLite в коде (например, в классе `MediaDatabase`):
* **MUST**: Запустить `py manage_tools.py db update` для миграции структуры таблиц.

### 8.4 Диагностика при решении проблем с медиатекой
Если пользователь сообщает об ошибках поиска, неверном отображении типов или пустых полях:
* **SHOULD**: Запустить `py manage_tools.py check media_type` или `py manage_tools.py check data` для быстрого сбора статистики по типам данных и проверки наличия записей в таблицах.
* **MAY**: Запустить `py manage_tools.py check db` для верификации текущей схемы БД на диске.

### 8.5 Использование CLI (Рекомендовано)
* Всегда начинайте с `manage_tools.py` — это единая точка входа.
* Используйте `--help` для получения справки: `py manage_tools.py --help`
* Структура: `py manage_tools.py <группа> <команда> [аргументы...]`

---

## 9. Структура директорий проекта (актуально на 2026-08-24)

```
C:\ai-assistant\
├── 📄 run.ps1 + Run-*.ps1    # Лончеры — ВСЕГДА в корне
├── 📄 main.py                # FastAPI приложение
├── 📄 manage_tools.py        # Универсальный CLI агентов ИИ
├── 📄 header.py              # Определение __root__ (используется main.py)
├── 📁 core/                   # Основной код (ai/, fastapi/, tts/, utils/...)
├── 📁 plugins/               # Плагины (media_organizer, langchain_media...)
├── 📁 tools/                 # Служебные инструменты
│   ├── 📁 ai/                # RAG-инструменты, поиск по коду
│   └── 📁 setup/             # Утилиты настройки кодовой базы
├── 📁 tmp/                   # Временные файлы и отчёты (tmp/reports/, tmp/logs/, tmp/rag/)
├── 📁 __skills/              # Навыки агентов (Antigravity)
├── 📁 tests/                 # Тесты pytest (38 файлов)
├── 📁 .gemini/               # Конфигурация Gemini AI
└── 📁 .ai_instructions/      # Инструкции для ИИ
```

### Инструменты ИИ (tools/ai/)

| Инструмент | Команда |
|------------ |---------|
| Пересборка RAG кодовой базы | `py tools/ai/rebuild_dev_rag.py` |
| Пересборка RAG медиатеки | `py tools/ai/rebuild_rag.py` |
| Поиск по коду | `py tools/ai/search_code.py --query "..."` |
| Обновление документации | `py tools/ai/update_docs.py` |
| Упаковка навыка | `py tools/ai/package_skill.py <name>` |

### Правила расположения файлов

- **Лончеры `Run-*.ps1`** → всегда в корне
- **AI-инструменты** → `tools/ai/`
- **Отчёты CI/аудита** → `tmp/reports/`
- **Отчёты по дискам** → `tmp/media_reports/`
- **RAG подсистема** → `core/rag/`
- **Документация лончеров** → `.ai_instructions/knowledge/LAUNCHER_GUIDE.md`


## 8. Рекомендации по автоматическому запуску для ИИ-ассистентов (AI Execution Guidelines)

ИИ-ассистенты (включая pair programming агентов) могут и должны самостоятельно принимать решение о запуске консольных скриптов проекта без явного указания пользователя в следующих сценариях:

### 8.1 Синхронизация данных после файловых операций
Если в ходе выполнения задачи ИИ-ассистент производил переименование, перенос или удаление медиафайлов/директорий:
* **MUST**: Запустить `py manage_tools.py db sizes` для пересчета размеров в БД и обновления свободного места в таблице `storage`.
* **SHOULD**: Запустить `py manage_tools.py torrents path`, чтобы qBittorrent узнал о новых путях расположения файлов.
* **MAY**: Запустить `py manage_tools.py audit media <пути>` для проверки отсутствия расхождений между диском и БД.

### 8.2 Добавление или обновление торрентов
При добавлении новых раздач в qBittorrent или привязке существующих к медиатеке:
* **SHOULD**: Запустить `py manage_tools.py torrents assign` для автоматической разметки категорий на основе названий из БД.
* **MAY**: Запустить `py manage_tools.py torrents state` для запуска принудительной проверки (Force Recheck) перенесенных раздач.

### 8.3 Изменение схемы базы данных
Если ИИ-ассистент внес изменения в структуру таблиц SQLite в коде (например, в классе `MediaDatabase`):
* **MUST**: Запустить `py manage_tools.py db update` для миграции структуры таблиц.

### 8.4 Диагностика при решении проблем с медиатекой
Если пользователь сообщает об ошибках поиска, неверном отображении типов или пустых полях:
* **SHOULD**: Запустить `py manage_tools.py check media_type` или `py manage_tools.py check data` для быстрого сбора статистики по типам данных и проверки наличия записей в таблицах.
* **MAY**: Запустить `py manage_tools.py check db` для верификации текущей схемы БД на диске.

### 8.5 Использование CLI (Рекомендовано)
* Всегда начинайте с `manage_tools.py` — это единая точка входа.
* Используйте `--help` для получения справки: `py manage_tools.py --help`
* Структура: `py manage_tools.py <группа> <команда> [аргументы...]`

