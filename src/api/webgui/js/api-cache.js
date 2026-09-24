/**
 * api-cache.js - Универсальный кеш-слой для всех API-запросов веб-интерфейса
 * 
 * Предоставляет единую точку входа для всех HTTP-запросов с автоматическим кешированием,
 * используя современные стратегии: Cache-First, Network-First, Stale-While-Revalidate.
 * 
 * АРХИТЕКТУРА:
 * - L1 Cache: In-Memory (быстрый доступ)
 * - L2 Cache: IndexedDB (персистентный)
 * - L3 Fallback: Direct network (если кеш недоступен)
 * 
 * ПРИМЕНЕНИЕ:
 * Используется всеми вкладками веб-интерфейса для оптимизации загрузки данных,
 * снижения нагрузки на API и обеспечения offline-режима.
 * 
 * @author hypo69
 * @version 1.0.0
 * @since 2026-09-24
 */

import { browserCache, STORES } from './browser-cache.js';

// Глобальные стратегии кеширования для разных типов данных
export const CACHE_STRATEGIES = {
  // Статические справочники (модели, конфигурации) - долгое TTL
  STATIC: { ttl: 60 * 60 * 1000, strategy: 'cache-first' },           // 1 час
  
  // Редко меняющиеся данные (hardware spec, user profiles) - средний TTL
  SEMI_STATIC: { ttl: 30 * 60 * 1000, strategy: 'cache-first' },      // 30 минут
  
  // Часто меняющиеся данные (системные метрики, статусы) - короткий TTL
  DYNAMIC: { ttl: 5 * 1000, strategy: 'stale-while-revalidate' },     // 5 секунд
  
  // Реалтайм данные (live telemetry, сенсоры) - минимальный TTL
  REALTIME: { ttl: 3 * 1000, strategy: 'network-first' },             // 3 секунды
  
  // Критичные данные (security status, errors) - всегда из сети
  CRITICAL: { ttl: 0, strategy: 'network-first' }                     // Нет кеша
};

// Автоматические правила сопоставления URL → стратегия
const URL_PATTERNS = [
  // Статические данные
  { pattern: /\/api\/v1\/models/, strategy: CACHE_STRATEGIES.STATIC, tag: 'models' },
  { pattern: /\/api\/config/, strategy: CACHE_STRATEGIES.STATIC, tag: 'config' },
  { pattern: /\/api\/plugins/, strategy: CACHE_STRATEGIES.SEMI_STATIC, tag: 'plugins' },
  
  // Hardware и системные спецификации
  { pattern: /\/api\/v1\/system\/hardware/, strategy: CACHE_STRATEGIES.SEMI_STATIC, tag: 'hardware' },
  { pattern: /\/api\/v1\/windows-backup/, strategy: CACHE_STRATEGIES.SEMI_STATIC, tag: 'backup' },
  
  // Динамические системные данные
  { pattern: /\/api\/v1\/system\/summary/, strategy: CACHE_STRATEGIES.DYNAMIC, tag: 'system-summary' },
  { pattern: /\/api\/system-control\/status/, strategy: CACHE_STRATEGIES.DYNAMIC, tag: 'control-status' },
  
  // Реалтайм телеметрия
  { pattern: /\/api\/v1\/system\/sensors/, strategy: CACHE_STRATEGIES.REALTIME, tag: 'sensors' },
  { pattern: /\/api\/v1\/system\/processes/, strategy: CACHE_STRATEGIES.REALTIME, tag: 'processes' },
  
  // RAG и чат (частые обновления)
  { pattern: /\/api\/chat/, strategy: CACHE_STRATEGIES.DYNAMIC, tag: 'chat' },
  { pattern: /\/api\/rag/, strategy: CACHE_STRATEGIES.DYNAMIC, tag: 'rag' }
];

/**
 * Определение стратегии кеширования по URL
 * @param {string} url - URL запроса
 * @returns {Object} { ttl, strategy, tag }
 */
function getCacheStrategy(url) {
  for (const rule of URL_PATTERNS) {
    if (rule.pattern.test(url)) {
      return { ...rule.strategy, tag: rule.tag };
    }
  }
  // По умолчанию: stale-while-revalidate с TTL 1 минута
  return { ttl: 60 * 1000, strategy: 'stale-while-revalidate', tag: 'default' };
}

/**
 * Генерация ключа кеша из URL и параметров
 * @param {string} url - URL запроса
 * @param {Object} options - Опции запроса (method, body)
 * @returns {string} Уникальный ключ кеша
 */
function generateCacheKey(url, options = {}) {
  const method = options.method || 'GET';
  const body = options.body ? `-${btoa(options.body).substring(0, 32)}` : '';
  return `${method}:${url}${body}`;
}

/**
 * Универсальная функция для выполнения HTTP-запросов с автоматическим кешированием
 * 
 * @param {string} url - URL запроса
 * @param {Object} options - Опции запроса
 * @param {Object} cacheOptions - Опции кеширования (переопределяют автоматику)
 * @returns {Promise<any>} Результат запроса
 * 
 * @example
 * // Автоматическое определение стратегии
 * const data = await cachedApiFetch('/api/v1/system/hardware');
 * 
 * @example
 * // Ручное переопределение стратегии
 * const data = await cachedApiFetch('/api/custom', {}, {
 *   ttl: 10000,
 *   strategy: 'cache-first',
 *   tag: 'custom-data'
 * });
 */
/**
 * Оборачивает результат в полиморфный объект, поддерживающий как прямое обращение к полям,
 * так и стандартный интерфейс Response (res.ok, res.status, res.json()).
 * @param {any} data 
 * @returns {any}
 */
function wrapCachedData(data) {
  if (data && typeof data === 'object') {
    try {
      if (!('ok' in data)) {
        Object.defineProperty(data, 'ok', { value: true, writable: true, configurable: true, enumerable: false });
      }
      if (!('status' in data)) {
        Object.defineProperty(data, 'status', { value: 200, writable: true, configurable: true, enumerable: false });
      }
      if (typeof data.json !== 'function') {
        Object.defineProperty(data, 'json', { value: async () => data, writable: true, configurable: true, enumerable: false });
      }
    } catch (_) {}
  }
  return data;
}

/**
 * Универсальная функция для выполнения HTTP-запросов с автоматическим кешированием
 * 
 * @param {string} url - URL запроса
 * @param {Object} options - Опции запроса
 * @param {Object} cacheOptions - Опции кеширования (переопределяют автоматику)
 * @returns {Promise<any>} Результат запроса (поддерживает как прямое чтение, так и res.ok / await res.json())
 */
export async function cachedApiFetch(url, options = {}, cacheOptions = {}) {
  // Определяем стратегию автоматически или используем переданную
  const autoStrategy = getCacheStrategy(url);
  const { 
    ttl = autoStrategy.ttl, 
    strategy = autoStrategy.strategy, 
    tag = autoStrategy.tag,
    forceNetwork = false 
  } = cacheOptions;
  
  const cacheKey = generateCacheKey(url, options);
  const cache = browserCache;
  
  // Дожидаемся готовности базы, но не блокируем если есть ошибка
  if (cache) {
    try {
      await cache.ready();
    } catch (_) {}
  }
  
  // CACHE-FIRST: сначала проверяем кеш, потом сеть
  if (cache && strategy === 'cache-first' && !forceNetwork) {
    try {
      const cached = await cache.get(STORES.API_CACHE, cacheKey);
      if (cached !== null && cached !== undefined) {
        return wrapCachedData(cached);
      }
    } catch (_) {}
  }
  
  // STALE-WHILE-REVALIDATE: показываем кеш, обновляем в фоне
  if (cache && strategy === 'stale-while-revalidate' && !forceNetwork) {
    try {
      const cached = await cache.get(STORES.API_CACHE, cacheKey);
      if (cached !== null && cached !== undefined) {
        // Фоновое асинхронное обновление
        directFetch(url, options)
          .then(fresh => cache.set(STORES.API_CACHE, cacheKey, fresh, { ttl, tags: [tag, 'api-cache'] }))
          .catch(err => console.debug(`[API Cache] Background update skipped for ${url}:`, err));
        return wrapCachedData(cached);
      }
    } catch (_) {}
  }
  
  // NETWORK-FIRST или первый запрос: сначала сеть, потом кеш как fallback
  try {
    const fresh = await directFetch(url, options);
    
    // Сохраняем в кеш (если TTL > 0)
    if (cache && ttl > 0) {
      cache.set(STORES.API_CACHE, cacheKey, fresh, { ttl, tags: [tag, 'api-cache'] }).catch(() => {});
    }
    
    return wrapCachedData(fresh);
  } catch (err) {
    // При ошибке сети пытаемся вернуть устаревший кеш
    if (cache) {
      try {
        const staleCache = await cache.get(STORES.API_CACHE, cacheKey);
        if (staleCache !== null && staleCache !== undefined) {
          console.warn(`[API Cache] Network failed, returning STALE cache: ${url}`);
          return wrapCachedData(staleCache);
        }
      } catch (_) {}
    }
    throw err;
  }
}

/**
 * Прямой HTTP-запрос без кеширования
 * @param {string} url - URL запроса
 * @param {Object} options - Опции fetch
 * @returns {Promise<any>}
 */
async function directFetch(url, options = {}) {
  const opts = { ...options };
  if (opts.body && typeof opts.body === 'string') {
    opts.headers = {
      'Content-Type': 'application/json',
      ...(opts.headers || {})
    };
  }
  
  if (window.api && typeof window.api.fetch === 'function') {
    const r = await window.api.fetch(url, opts);
    return wrapCachedData(r);
  }
  
  const res = await fetch(url, opts);
  if (!res.ok) {
    let errMsg = `HTTP ${res.status}`;
    try {
      const errJson = await res.json();
      if (errJson && errJson.detail) {
        errMsg += ` (${typeof errJson.detail === 'object' ? JSON.stringify(errJson.detail) : errJson.detail})`;
      }
    } catch (_) {}
    throw new Error(errMsg);
  }
  const json = await res.json();
  return wrapCachedData(json);
}

/**
 * Инвалидация кеша по тегу (например, после обновления данных)
 * @param {string} tag - Тег для инвалидации
 * @returns {Promise<number>} Количество удаленных записей
 * 
 * @example
 * // Очистить весь кеш моделей после обновления
 * await invalidateCacheByTag('models');
 */
export async function invalidateCacheByTag(tag) {
  if (!browserCache || !browserCache.isDbReady) return 0;
  const count = await browserCache.invalidateByTag(STORES.API_CACHE, tag);
  console.log(`[API Cache] 🗑️ Invalidated ${count} entries with tag: ${tag}`);
  return count;
}

/**
 * Очистка всего API-кеша
 * @returns {Promise<boolean>}
 */
export async function clearAllApiCache() {
  if (!browserCache || !browserCache.isDbReady) return false;
  await browserCache.clearStore(STORES.API_CACHE);
  console.log('[API Cache] 🗑️ All API cache cleared');
  return true;
}

/**
 * Получение статистики кеша
 * @returns {Promise<Object>}
 */
export async function getApiCacheStats() {
  if (!browserCache || !browserCache.isDbReady) {
    return { available: false, metrics: null };
  }
  
  const stats = await browserCache.getDetailedStats();
  const apiStore = stats.stores[STORES.API_CACHE] || {};
  
  return {
    available: true,
    metrics: stats.metrics,
    apiCache: {
      count: apiStore.count || 0,
      sizeMB: apiStore.sizeMB || '0.00',
      hitRate: stats.metrics.hits + stats.metrics.misses > 0 
        ? Math.round((stats.metrics.hits / (stats.metrics.hits + stats.metrics.misses)) * 100)
        : 0
    },
    storage: stats.storageEstimate
  };
}

// Экспорт в глобальный контекст для доступности из всех вкладок
if (typeof window !== 'undefined') {
  window.cachedApiFetch = cachedApiFetch;
  window.invalidateCacheByTag = invalidateCacheByTag;
  window.clearAllApiCache = clearAllApiCache;
  window.getApiCacheStats = getApiCacheStats;
  window.CACHE_STRATEGIES = CACHE_STRATEGIES;
}

export default cachedApiFetch;
