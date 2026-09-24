# API Cache System — Быстрый старт за 5 минут

> Начните использовать кеширование в своей вкладке за 5 минут

## 🚀 Шаг 1: Замените fetch на cachedApiFetch

### Было (без кеша)

```javascript
async function loadData() {
  const response = await fetch('/api/v1/data');
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const data = await response.json();
  return data;
}
```

### Стало (с кешем)

```javascript
async function loadData() {
  // Автоматическая стратегия + кеширование
  const data = await cachedApiFetch('/api/v1/data');
  return data;
}
```

**Готово!** Ваши запросы теперь кешируются автоматически.

---

## 🎯 Шаг 2: Выберите стратегию (опционально)

Если вам нужна конкретная стратегия:

```javascript
// Cache-First — для статики (модели, конфиги)
const models = await cachedApiFetch('/api/v1/models', {}, {
  strategy: 'cache-first',
  ttl: 60 * 60 * 1000 // 1 час
});

// Network-First — для критичных данных
const sensors = await cachedApiFetch('/api/v1/sensors', {}, {
  strategy: 'network-first',
  ttl: 3000 // 3 секунды
});

// Stale-While-Revalidate — для динамики (лучший UX)
const summary = await cachedApiFetch('/api/v1/summary', {}, {
  strategy: 'stale-while-revalidate',
  ttl: 5000 // 5 секунд
});
```

---

## 🗑️ Шаг 3: Инвалидируйте после обновлений

```javascript
// Сохранение данных (POST/PUT)
async function saveModel(model) {
  await cachedApiFetch('/api/v1/models', {
    method: 'POST',
    body: JSON.stringify(model)
  });
  
  // Очистить кеш моделей
  await invalidateCacheByTag('models');
}
```

---

## 📊 Шаг 4: Добавьте индикатор (опционально)

### HTML

```html
<span class="badge bg-success" id="cache-badge">
  💾 Cache: Ready
</span>
```

### JavaScript

```javascript
// Обновлять каждые 5 секунд
setInterval(async () => {
  const stats = await getApiCacheStats();
  document.getElementById('cache-badge').textContent = 
    `💾 Cache: ${stats.apiCache.hitRate}% hit`;
}, 5000);
```

---

## ✅ Готово!

Теперь ваша вкладка использует кеширование:

- ✅ Быстрая загрузка из кеша (0-5ms)
- ✅ Автоматическое обновление в фоне
- ✅ Offline-режим
- ✅ Меньше нагрузки на API

---

## 🧪 Тестирование

Откройте консоль браузера (F12) и выполните:

```javascript
await testApiCache();
```

Если все работает, вы увидите:

```
🎉 All tests passed! API Cache System is working correctly.
```

---

## 📚 Дополнительно

- **[Полная документация](api-cache.md)**
- **[Примеры использования](examples.md)**
- **[Тестирование](TESTING.md)**

---

**Готово за 5 минут!** 🎊
