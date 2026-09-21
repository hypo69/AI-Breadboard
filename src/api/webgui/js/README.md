# Подсистема клиентского браузерного кеширования (Browser Cache & Storage)

Модуль предоставляет универсальную, производительную и многоуровневую систему управления кешем и долговременным хранилищем данных на стороне браузера в рамках веб-интерфейса AI Breadboard.

## Архитектура хранилища

Система построена по многоуровневой архитектуре (**Multi-tier Cache & Storage**):

1. **L1 In-Memory Cache (`Map` с LRU вытеснением)** — сверхбыстрый синхронный доступ для горячих данных текущей вкладки.
2. **L2 Persistent IndexedDB (`AI_Breadboard_DB`)** — надежное асинхронное хранилище сотен мегабайт и гигабайт структурированных и бинарных данных (JSON-объекты, массивы векторов, `Blob`, `ArrayBuffer`).
3. **L3 LocalStorage / SessionStorage Fallback** — легковесное резервное хранилище для мелких настроек.

---

## Поддерживаемые хранилища (Object Stores)

| Название хранилища | Константа | Назначение |
|---|---|---|
| `api_cache` | `STORES.API_CACHE` | Кеширование ответов REST API, справочников и статусов серверов |
| `rag_embeddings` | `STORES.RAG_EMBEDDINGS` | Векторные эмбеддинги, чанки документов и поисковые индексы RAG |
| `chat_history` | `STORES.CHAT_HISTORY` | Локальная история сообщений, контекст диалогов и промпты |
| `media_blobs` | `STORES.MEDIA_BLOBS` | Аудиодорожки синтеза речи (TTS), изображения и медиафайлы |
| `models_registry` | `STORES.MODELS_REGISTRY` | Схемы и конфигурации моделей ИИ (Windows AI, Ollama, Gemini) |
| `key_value` | `STORES.KEY_VALUE` | Универсальное хранилище ключ-значение с TTL |

---

## Примеры использования

### 1. Сохранение и чтение данных через `browserCache`
```javascript
import { browserCache, STORES } from './browser-cache.js';

// Запись с TTL 2 часа и тегами
await browserCache.set(STORES.RAG_EMBEDDINGS, 'doc_chunk_123', {
  text: 'Текст фрагмента базы знаний...',
  vector: [0.123, -0.456, 0.789]
}, {
  ttl: 2 * 60 * 60 * 1000,
  tags: ['rag_collection_1']
});

// Чтение данных
const chunk = await browserCache.get(STORES.RAG_EMBEDDINGS, 'doc_chunk_123');

// Удаление записи
await browserCache.delete(STORES.RAG_EMBEDDINGS, 'doc_chunk_123');

// Инвалидация группы записей по тегу
await browserCache.invalidateByTag(STORES.RAG_EMBEDDINGS, 'rag_collection_1');
```

### 2. Сохранение бинарных данных (Audio TTS Blob)
```javascript
// Сохранение аудио дорожки
await browserCache.set(STORES.MEDIA_BLOBS, 'tts_speech_msg_42', audioBlob, {
  ttl: 24 * 60 * 60 * 1000 // 24 часа
});

// Получение аудио дорожки
const cachedBlob = await browserCache.get(STORES.MEDIA_BLOBS, 'tts_speech_msg_42');
if (cachedBlob) {
  const audioUrl = URL.createObjectURL(cachedBlob);
  new Audio(audioUrl).play();
}
```

### 3. Автоматическое кеширование API запросов через `APIFetcher`
```javascript
import { APIFetcher } from './api-cache.js';

const fetcher = new APIFetcher();

// Автоматически проверяет L1/L2 кеш и сохраняет в IndexedDB
const models = await fetcher.get('/api/models', {}, {
  ttl: 10 * 60 * 1000, // 10 минут
  tags: ['models']
});
```

---

## Мониторинг квот и управление

Модуль включает:
- Проверку доступной дисковой квоты браузера через `navigator.storage.estimate()`.
- Фоновый сборщик мусора (`cleanupExpired()`), удаляющий устаревшие записи по индексу `expiresAt`.
- Запрос постоянного хранилища (`navigator.storage.persist()`), предотвращающий сброс кеша при нехватке места на диске.
- UI модальное окно `#cacheManagerModal` для управления, очистки, экспорта в JSON и импорта.
