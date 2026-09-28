# 📁 File History AI Search — Семантический поиск по истории файлов Windows

Модуль **File History AI Search** предназначен для автоматического выявления истории взаимодействия с файлами в операционной системе Windows, векторизации и построения RAG-индекса, регулярного автообновления и сверхбыстрого семантического поиска.

---

## 💡 Основные возможности

1. **Сбор истории файлов Windows (`WindowsFileHistoryCollector`)**:
   - Сканирование конфигураций и каталогов **Windows File History** (`Config1.xml`, `Catalog1.xml`).
   - Парсинг открытых файлов из ярлыков **Recent Files** (`%APPDATA%\Microsoft\Windows\Recent\*.lnk`).
   - Запрос SQLite базы активности **Windows Activity History** (`ActivitiesCache.db`).
   - Фолбэк-сканирование недавно измененных файлов ФС в пользовательских директориях.

2. **RAG-индексация и семантический поиск (`FileHistoryRAGService`)**:
   - Построение векторного RAG-индекса через встроенный класс `GeminiRAG` (`src.ai.gemini.rag`).
   - Инкрементальная индексация и хранение в `data/file_history_rag/`.
   - Семантический поиск с фильтрацией по источникам и ранжированием по релевантности.

3. **Периодическое автообновление (`FileHistoryScheduler`)**:
   - Автоматический фоновый планировщик регулярного сканирования и индексации (по умолчанию каждые 15 минут).
   - Поддержка фонового демона и ручного принудительного триггера.

4. **REST API & CLI**:
   - FastAPI маршруты `/api/windows/file-history/*`.
   - Интерфейс командной строки `python -m apps.windows.file_history_ai_search`.

---

## 🚀 Использование CLI

```powershell
# Сканирование текущих файлов в операционной системе Windows
python -m apps.windows.file_history_ai_search scan

# Построение и пересчет RAG-индекса
python -m apps.windows.file_history_ai_search index

# Быстрый семантический поиск
python -m apps.windows.file_history_ai_search search "отчет по продажам за 2025" --top-k 5

# Проверка текущего статуса индекса
python -m apps.windows.file_history_ai_search status

# Запуск фонового планировщика обновления RAG (каждые 15 минут)
python -m apps.windows.file_history_ai_search daemon --interval 15
```

---

## 🔌 REST API Endpoints

- `GET /api/windows/file-history/scan` — Получить текущие элементы истории файлов.
- `POST /api/windows/file-history/index` — Перестроить/обновить RAG-индекс.
- `POST /api/windows/file-history/search` — Быстрый семантический поиск (POST JSON).
- `GET /api/windows/file-history/search?query=...` — Поиск через GET запрос.
- `GET /api/windows/file-history/status` — Получить статус индекса и планировщика.
- `POST /api/windows/file-history/scheduler/start` — Запустить периодическое обновление.
- `POST /api/windows/file-history/scheduler/stop` — Остановить планировщик.

---

## 🧪 Тестирование

```powershell
pytest apps/windows/file_history_ai_search/tests/ -v
```
