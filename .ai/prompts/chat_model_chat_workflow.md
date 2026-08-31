# Workflow Чат-Модели: От пользователя к ответу

## Обзор процесса

Этот документ описывает полный цикл обработки запросов от пользователя через систему чат-модели с RAG-контекстом.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ПОЛНЫЙ WORKFLOW ЧАТА                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. Входящий запрос                                                          │
│     └──> /api/chat (POST)                                                    │
│     └──> ChatRequest (message, history, generation_config)                   │
│                                                                              │
│  2. Check режима отладки                                                  │
│     └──> debug_mode == true → formation полного промпта                   │
│     └──> debug_mode == false → стандартная обработка                         │
│                                                                              │
│  3. Получение данных пользователя                                           │
│     └──> auth_token → user_id из БД                                         │
│     └──> anon_<IP> для гостевых пользователей                                │
│     └──> Настройки пользователя (model, system_instruction, tts_voice)       │
│                                                                              │
│  4. Loading контекста через RAG                                            │
│     └──> search_user_context(user_id, api_key, query, top_k=3, threshold=0.4)│
│     └──> Поиск похожих запросов в истории пользователя                       │
│     └──> Formation user_context_str из найденных фрагментов               │
│                                                                              │
│  5. Loading профиля предпочтений                                           │
│     └──> get_recommendation_context(user_id)                                 │
│     └──> Получение истории просмотров и предпочтений                         │
│                                                                              │
│  6. Formation финального системного инструкта                            │
│     └──> system_instruction (из настроек)                                    │
│     └──> voice_gender_instruction (коррекция рода по голосу)                 │
│     └──> user_context_str (из RAG)                                           │
│     └──> pref_context (из профиля)                                           │
│                                                                              │
│  7. Маршрутизация плагинов                                                  │
│     └──> Check media-запросов (_is_media_query)                           │
│     └──> Извлечение chat_mode (story/download)                              │
│     └──> Последовательная check плагинов                                  │
│                                                                              │
│  8. Обработка плагинами                                                     │
│     └──> plugin.can_handle(request.message)                                  │
│     └──> plugin.handle(request.message, **kwargs)                            │
│     └──> Stream или single response                                          │
│     └──> index_user_query (fire-and-forget)                                  │
│                                                                              │
│  9. Генерация через AI-модель                                               │
│     └──> chat_stream(message, system_instruction, history)                   │
│     └──> Два этапа для RC режима (chat + voice)                             │
│                                                                              │
│  10. Индексация ответа                                                      │
│     └──> index_user_query(user_id, api_key, query, response)                 │
│     └──> В фоновом потоке (не блокирует ответ)                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Детализация этапов

### 1. Входящий запрос

**Endpoint:** `POST /api/chat`

**Request Body:**
```json
{
  "message": "String запроса пользователя",
  "history": [
    {"role": "user", "parts": ["Предыдущий вопрос"]},
    {"role": "model", "parts": ["Предыдущий ответ"]}
  ],
  "generation_config": {
    "debug_mode": false,
    "chat_mode": "story",
    "is_rc": false
  }
}
```

### 2. Check режима отладки

Если `debug_mode == true`:
- Формируется полный промпт со всеми инструкциями
- Отправляется в ответ вместо вызова модели
- Позволяет видеть, что именно отправляется в модель

### 3. Получение данных пользователя

**Источники:**
- `auth_token` из cookies → JWT → user_id
- `anon_<client_ip>` для гостевых пользователей
- Настройки из базы:
  - `model` — выбранная модель
  - `system_instruction` — пользовательская инструкция
  - `tts_voice` — голос для озвучки

### 4. Loading контекста через RAG

**Function:** `search_user_context(user_id, api_key, query, top_k=3, threshold=0.4)`

**Путь:** `src/ai/gemini/user_query_rag.py`

**Процесс:**
1. Получение RAG-базы пользователя: `get_user_rag(user_id, api_key)`
2. Вычисление эмбеддинга запроса через Gemini API
3. Поиск по FAISS-индексу: top_k=3, threshold=0.4
4. Formation `user_context_str` из найденных фрагментов

**Формат документа в RAG:**
```
Пользователь спросил: {query}
Ответ модели: {response}
```

### 5. Loading профиля предпочтений

**Function:** `get_recommendation_context(user_id)`

**Источники:**
- История просмотров медиа
- Предпочтения в жанрах
- Лайки/дизлайки

**Формат:** String с описанием предпочтений пользователя

### 6. Formation системного инструкта

**Составные части:**
```python
final_system_instruction = (
    f"{system_instruction}\n\n"
    f"{voice_gender_instruction}\n\n"
    f"{user_context_str}\n\n"
    f"{pref_context}"
)
```

**voice_gender_instruction:**
- Мужской голос → женский род ответа
- Женский голос → мужской род ответа

### 7. Маршрутизация плагинов

**Определение типа запроса:**
```python
is_media = rag_plugin._is_media_query(request.message)
```

**Пропуск плагинов:**
- `yt_dlp` в режиме `story`
- `rag` для не-media запросов
- Другие плагины для media запросов

### 8. Обработка плагинами

**Порядок проверки:**
1. `can_handle(request.message)` → True
2. `handle(request.message, **kwargs)`
3. Stream response или single response
4. `index_user_query` (fire-and-forget)

**Конструкция ответа:**
```python
if inspect.isasyncgen(response):
    async for chunk in response:
        yield {"text": chunk}
else:
    yield {"text": str(response)}
```

### 9. Генерация через AI-модель

**Два режима:**

**a) Single response:**
```python
response = await active_model.chat_stream(request.message, **kwargs)
```

**b) RC mode (chat + voice):**
```python
# Этап 1: chat или voice
response_1 = await active_model.chat_stream(request.message, generation_config={'response_type': 'chat'})

# Этап 2: voice или chat
q2 = f"{request.message}\n\nОпираясь на твой предыдущий ответ:\n{response_1}\n\nСгенерируй версию для диктора."
response_2 = await active_model.chat_stream(q2, generation_config={'response_type': 'voice'})
```

**Формат ответа модели:**
```
[CHAT]
<markdown для чата>

[VOICE]
<текст для диктора>
```

### 10. Индексация ответа

**Function:** `index_user_query(user_id, api_key, query, response)`

**Путь:** `src/ai/gemini/user_query_rag.py`

**Процесс:**
1. Check длины запроса (> 10 символов)
2. Прореживание при переполнении (> 500 документов)
3. Добавление документа в RAG-базу
4. Fire-and-forget (не блокирует ответ)

**Структура документа:**
```json
{
  "id": "user_id_md5_hash",
  "text": "Пользователь спросил: {query}\nОтвет модели: {response}",
  "meta": {
    "user_id": "user_id",
    "timestamp": 1234567890,
    "q": "query",
    "response": "response"
  }
}
```

---

## Технические детали

### API ключи

**Получение ключа:**
```python
from plugins.media_organizer.core.media_rag_functions import _get_gemini_api_key
api_key = _get_gemini_api_key()
```

**Роутер ключей:**
- `GET /api/keys` — list всех ключей
- `POST /api/keys` — добавление ключа
- `DELETE /api/keys/{name}` — удаление ключа
- `PATCH /api/keys/{name}` — update статуса
- `POST /api/keys/{name}/reset-quota` — сброс квоты

### Пути к файлам

**Системные инструкции:**
- `prompts/chat/system_instruction.md`
- `prompts/media_organizer/system_instruction.md`
- `prompts/narrator/narrator_style.md`
- `prompts/narrator/tts_rules.md`

**RAG индексы:**
- `rag/rules.index` — системные правила (sentence-transformers)
- `rag/documents.json` — корпус системных правил
- `src/ai/gemini/user_rags/user_rag_{user_id}.db` — пользовательские RAG (Gemini)

### Модели

**Gemini:**
- `gemini-3.1-flash-lite`
- `gemini-2.5-flash`
- `gemini-2.0-flash`
- `gemini-1.5-flash`
- `gemini-1.5-pro`

**Foundry:**
- `qwen3-0.6b-generic-cpu:4`

**Agy:**
- `agy-flash`
- `agy-pro`

---

## Ошибки и обработка

**Частые ошибки:**

1. **Отсутствие auth_token:**
   - Пользователь `anon_<IP>`
   - Ограниченные функции

2. **Исчерпание квоты:**
   - `429 RESOURCE_EXHAUSTED`
   - Автоматическое переключение ключей
   - Ожидание разблокировки (24 часа)

3. **Service unavailable (503):**
   - Автоматическое переключение модели
   - Exponential backoff (2^attempt)

4. **Ошибки авторизации (401):**
   - Check ключа
   - Перек��ючение на следующий ключ

---

## Мониторинг

**Статистика RAG:**
```python
from src.ai.gemini.user_query_rag import get_user_rag_stats
stats = get_user_rag_stats(user_id, api_key)
# {"user_id": "...", "count": 100, "db_path": "...", "db_size_kb": 512.3}
```

**Логирование:**
- `src.logger.logger` — все важные события
- `logger.error()` — ошибки
- `logger.warning()` — предупреждения
- `logger.info()` — Info
