# Тестирование API Cache System

> Руководство по проверке работоспособности системы кеширования

## 🧪 Быстрый тест

### 1. Откройте веб-интерфейс

```
https://localhost:8000/admin
```

### 2. Откройте консоль браузера

Нажмите `F12` → вкладка **Console**

### 3. Запустите тестовый набор

```javascript
await testApiCache();
```

### Ожидаемый результат

```
=== 🧪 API Cache System Test Suite ===

✅ Cache Availability: BrowserCache is available
✅ API Fetch Function: cachedApiFetch() is available
✅ IndexedDB Ready: IndexedDB is ready

--- Testing Cache-First Strategy ---
Request 1: Should be MISS (network)
Request 2: Should be HIT (cache)
✅ Cache-First Speed: Network: 45.30ms, Cache: 2.10ms (21.6x faster)

--- Testing Tag Invalidation ---
✅ Tag Invalidation: Invalidated 2 entries (expected 2)

--- Testing Statistics ---
✅ Cache Statistics: Hit rate: 67%, Entries: 12

--- Testing Force Network ---
✅ Force Network: Force network request took 38.50ms (should be > 10ms)

=== 📊 Test Results ===
Total: 7 tests
✅ Passed: 7
❌ Failed: 0
Success rate: 100.0%

🎉 All tests passed! API Cache System is working correctly.
```

---

## 🔍 Ручное тестирование

### Проверка IndexedDB

1. Откройте DevTools (F12)
2. Перейдите в **Application** → **Storage** → **IndexedDB**
3. Найдите **AI_Breadboard_DB**
4. Проверьте хранилища:
   - `api_cache` — API-запросы
   - `chat_history` — История чатов
   - `models_registry` — Реестр моделей
   - `rag_embeddings` — RAG эмбеддинги
   - `media_blobs` — Медиа-файлы

### Проверка Cache Hit Rate

```javascript
// Получить статистику
const stats = await getApiCacheStats();

console.log('Hit Rate:', stats.apiCache.hitRate, '%');
console.log('Total Entries:', stats.apiCache.count);
console.log('Cache Size:', stats.apiCache.sizeMB, 'MB');
console.log('Storage Used:', stats.storage.percentUsed, '%');
```

### Проверка стратегий

```javascript
// 1. Cache-First (должен быть HIT при повторном запросе)
console.log('Test 1: Cache-First');
await cachedApiFetch('/api/v1/models'); // MISS (первый раз)
await cachedApiFetch('/api/v1/models'); // HIT (второй раз)

// 2. Network-First (всегда свежие данные)
console.log('Test 2: Network-First');
await cachedApiFetch('/api/v1/system/sensors'); // Всегда из сети

// 3. Stale-While-Revalidate (возвращает кеш, обновляет в фоне)
console.log('Test 3: Stale-While-Revalidate');
await cachedApiFetch('/api/v1/system/summary'); // Кеш + фоновое обновление
```

---

## 🎯 Тестирование производительности

### Сравнение с/без кеша

```javascript
// БЕЗ кеша (прямой fetch)
console.time('Without Cache');
await fetch('/api/v1/system/hardware').then(r => r.json());
console.timeEnd('Without Cache');
// Without Cache: 125.45ms

// С кешем (первый запрос)
console.time('With Cache (cold)');
await cachedApiFetch('/api/v1/system/hardware');
console.timeEnd('With Cache (cold)');
// With Cache (cold): 118.30ms

// С кешем (повторный запрос)
console.time('With Cache (hot)');
await cachedApiFetch('/api/v1/system/hardware');
console.timeEnd('With Cache (hot)');
// With Cache (hot): 3.20ms

// Выигрыш: ~40x быстрее!
```

### Нагрузочное тестирование

```javascript
// 100 параллельных запросов
async function loadTest() {
  const promises = [];
  for (let i = 0; i < 100; i++) {
    promises.push(cachedApiFetch('/api/v1/system/summary'));
  }
  
  console.time('Load Test');
  await Promise.all(promises);
  console.timeEnd('Load Test');
  
  const stats = await getApiCacheStats();
  console.log('Hit Rate after load:', stats.apiCache.hitRate, '%');
}

await loadTest();
```

---

## 🐛 Отладка проблем

### Проблема: Кеш не работает

**Проверка 1:** IndexedDB доступен?

```javascript
console.log('IndexedDB available:', !!window.indexedDB);
console.log('BrowserCache ready:', await window.browserCache?.ready());
```

**Решение:** Если IndexedDB недоступен:
- Проверьте, что браузер не в режиме инкогнито
- Проверьте права на запись в user-data-dir
- Проверьте настройки безопасности браузера

---

### Проблема: Низкий Hit Rate

**Проверка 2:** Какие запросы промахиваются?

```javascript
// Включить детальное логирование
localStorage.setItem('DEBUG_API_CACHE', 'true');
location.reload();

// Смотрим логи в консоли
// [API Cache] ❌ MISS → stored: /api/endpoint
```

**Решение:**
- Проверьте, что URL не меняется динамически (query params)
- Проверьте TTL стратегии (может быть слишком короткий)
- Убедитесь, что используется `cachedApiFetch`, а не прямой `fetch`

---

### Проблема: Устаревшие данные

**Проверка 3:** Какая стратегия используется?

```javascript
// Принудительно обновить данные
await cachedApiFetch('/api/endpoint', {}, { forceNetwork: true });

// Или инвалидировать по тегу
await invalidateCacheByTag('your-tag');
```

**Решение:**
- Для критичных данных используйте `network-first` или `forceNetwork`
- Уменьшите TTL для часто меняющихся данных
- Инвалидируйте кеш после мутаций (POST/PUT/DELETE)

---

## 📊 Мониторинг в production

### Добавление метрик

```javascript
// Периодический мониторинг
setInterval(async () => {
  const stats = await getApiCacheStats();
  
  // Отправка метрик в систему мониторинга
  sendMetric('cache.hit_rate', stats.apiCache.hitRate);
  sendMetric('cache.size_mb', parseFloat(stats.apiCache.sizeMB));
  sendMetric('cache.entries', stats.apiCache.count);
  
  // Алерт при низком hit rate
  if (stats.apiCache.hitRate < 50) {
    console.warn('[Monitoring] Low cache hit rate:', stats.apiCache.hitRate);
  }
}, 60000); // Каждую минуту
```

---

## ✅ Чеклист перед релизом

- [ ] Все тесты проходят (`await testApiCache()`)
- [ ] Hit Rate > 70% для типичных сценариев
- [ ] IndexedDB работает в PWA-окне
- [ ] Кеш инвалидируется после мутаций
- [ ] Нет утечек памяти (проверить в Performance Monitor)
- [ ] Offline-режим работает (отключить сеть и проверить)
- [ ] Логи кеша отключены в production (убрать `DEBUG_API_CACHE`)

---

## 📚 Дополнительные ресурсы

- **[Полная документация](api-cache.md)**
- **[Примеры использования](examples.md)**
- **[Быстрый старт](README.md)**

---

**© 2026 AI-Breadboard Team**
