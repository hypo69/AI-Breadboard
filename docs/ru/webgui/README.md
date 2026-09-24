# Документация веб-интерфейса AI-Breadboard

> **Версия:** 3.1  
> **Последнее обновление:** 24 сентября 2026

## 📚 Содержание документации

### 🎯 Основные компоненты

1. **[Quick Start (5 минут)](QUICKSTART.md)** — Быстрый старт для разработчиков

2. **[API Cache System](api-cache.md)** — Универсальная система кеширования
   - Автоматическое кеширование всех API-запросов
   - 3 стратегии: Cache-First, Network-First, Stale-While-Revalidate
   - Многоуровневое хранилище (Memory + IndexedDB)
   - Offline-режим и фоновое обновление

2. **Browser Cache Manager** — Низкоуровневый менеджер кеша
   - IndexedDB для персистентного хранения
   - In-Memory кеш для быстрого доступа
   - TTL, теги, инвалидация

3. **Tab Core** — Система управления вкладками
   - Lifecycle hooks (init, activate, deactivate)
   - Tab Poller для периодических обновлений
   - Приоритет навигации над процессами

---

## 🚀 Быстрый старт

### Использование API Cache в новой вкладке

```javascript
// 1. Импортируем (опционально, доступно глобально)
import { cachedApiFetch } from './js/api-cache.js';

// 2. Используем вместо обычного fetch
async function loadData() {
  // Автоматическая стратегия по URL
  const data = await cachedApiFetch('/api/v1/your-endpoint');
  renderData(data);
}

// 3. Инвалидация после обновления
async function saveData(newData) {
  await cachedApiFetch('/api/v1/save', {
    method: 'POST',
    body: JSON.stringify(newData)
  });
  
  // Очистить кеш тега
  await invalidateCacheByTag('your-tag');
}
```

### Миграция существующей вкладки

**Было:**
```javascript
async function apiFetch(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return await res.json();
}
```

**Стало:**
```javascript
async function apiFetch(url, options = {}) {
  // Используем cachedApiFetch, если доступно
  if (window.cachedApiFetch) {
    return await window.cachedApiFetch(url, options);
  }
  // Fallback на прямой fetch
  const res = await fetch(url, options);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return await res.json();
}
```

---

## 📊 Статистика и мониторинг

### Добавление индикатора кеша

```html
<!-- В вашей вкладке -->
<span class="badge" id="cache-status-badge">💾 Cache: Loading...</span>
```

```javascript
// JavaScript
async function updateCacheStatus() {
  const stats = await getApiCacheStats();
  if (stats.available) {
    document.getElementById('cache-status-badge').textContent = 
      `💾 Cache: ${stats.apiCache.hitRate}% hit`;
  }
}

// Обновление каждые 5 секунд
setInterval(updateCacheStatus, 5000);
```

---

## 🎨 UI Компоненты

### Кнопка "Очистить кеш"

```html
<button id="btn-clear-cache" class="btn btn-sm btn-outline-warning">
  <i class="bi bi-trash3"></i> Очистить кеш
</button>
```

```javascript
document.getElementById('btn-clear-cache').onclick = async () => {
  await invalidateCacheByTag('your-tab-tag');
  await refreshData();
  showToast('Кеш очищен', 'success');
};
```

---

## 🔧 Конфигурация

### Добавление custom endpoints

В `src/api/webgui/js/api-cache.js`:

```javascript
const URL_PATTERNS = [
  // Добавьте свой паттерн
  { 
    pattern: /\/api\/v1\/my-endpoint/, 
    strategy: CACHE_STRATEGIES.DYNAMIC, 
    tag: 'my-data' 
  }
];
```

---

## 📖 Полная документация

- **[API Cache System (полное руководство)](api-cache.md)**
- **Architecture Overview** (в разработке)
- **Tab Lifecycle** (в разработке)
- **Performance Optimization** (в разработке)

---

## 💡 Лучшие практики

### ✅ DO

1. Используйте `cachedApiFetch()` для всех API-запросов
2. Добавляйте теги для группировки данных
3. Инвалидируйте кеш после мутаций (POST/PUT/DELETE)
4. Мониторьте hit rate для оптимизации

### ❌ DON'T

1. Не кешируйте критичные данные надолго (auth, payments)
2. Не используйте cache-first для мутаций
3. Не игнорируйте ошибки сети в production
4. Не злоупотребляйте `forceNetwork` (только для refresh)

---

## 🐛 Отладка

### Включение debug-логов

```javascript
// В консоли браузера
localStorage.setItem('DEBUG_API_CACHE', 'true');
```

### Проверка IndexedDB

1. Откройте DevTools (F12)
2. Перейдите в **Application → Storage → IndexedDB**
3. Найдите **AI_Breadboard_DB → api_cache**

---

## 🤝 Вклад

Если вы добавляете новую вкладку:

1. Используйте `cachedApiFetch()` вместо `fetch()`
2. Выберите подходящую стратегию кеширования
3. Добавьте тег для инвалидации
4. Обновите документацию

---

## 📧 Контакты

- **GitHub:** [AI-Breadboard Repository](https://github.com/hypo69/hypo)
- **Документация:** [docs/ru/webgui/](.)
- **Issues:** [GitHub Issues](https://github.com/hypo69/hypo/issues)

---

**© 2026 AI-Breadboard Team. MIT License.**
