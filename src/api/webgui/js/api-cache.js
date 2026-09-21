/**
 * APICache - Расширенная система кеширования API ответов
 * 
 * Кеширует GET запросы на клиенте с поддержкой L1 Memory и L2 IndexedDB (через BrowserCacheManager),
 * инвалидирует кеш при изменениях (POST/PUT/DELETE).
 * Снижает нагрузку на сервер и ускоряет отклик интерфейса.
 * 
 * Usage:
 *   const cache = new APICache();
 *   await cache.set('/api/users', data, 5 * 60 * 1000);  // 5 минут
 *   const cached = await cache.get('/api/users');
 *   cache.invalidate(/\/api\/users/);  // Pattern-based invalidation
 */

import { browserCache, STORES } from './browser-cache.js';

class APICache {
  constructor(options = {}) {
    this.store = new Map(); // { key: { data, expiresAt, timestamp } }
    this.defaultTTL = options.defaultTTL || 5 * 60 * 1000; // 5 минут по умолчанию
    this.usePersistentStorage = options.usePersistent !== false;
    this.storeName = STORES.API_CACHE;
  }

  /**
   * Сохранить данные в кеш
   * @param {string} key - Ключ (обычно URL)
   * @param {any} data - Данные для кеширования
   * @param {number} ttl - Time to live в миллисекундах (опционально)
   * @param {Object} options - Дополнительные параметры (tags, persist)
   */
  set(key, data, ttl = this.defaultTTL, options = {}) {
    const expiresAt = Date.now() + ttl;
    const clonedData = JSON.parse(JSON.stringify(data));
    
    // Сохранение в память L1
    this.store.set(key, {
      data: clonedData,
      expiresAt,
      timestamp: Date.now(),
      ttl
    });

    // Асинхронно сохраняем в IndexedDB L2
    if (this.usePersistentStorage && browserCache) {
      browserCache.set(this.storeName, key, clonedData, {
        ttl,
        tags: options.tags || ['api'],
        persist: options.persist !== false
      }).catch(err => {
        console.warn(`[APICache] Ошибка сохранения в IndexedDB для ${key}:`, err);
      });
    }

    console.log(`[APICache] Cached: ${key} (TTL: ${ttl}ms)`);
  }

  /**
   * Получить данные из кеша если они актуальны (синхронный поиск в L1)
   * @param {string} key - Ключ (обычно URL)
   * @returns {any|null} - Данные или null если кеша нет или он истек
   */
  get(key) {
    const cached = this.store.get(key);
    
    if (!cached) {
      return null;
    }

    // Проверяем срок действия
    if (Date.now() > cached.expiresAt) {
      this.store.delete(key);
      if (this.usePersistentStorage && browserCache) {
        browserCache.delete(this.storeName, key).catch(() => {});
      }
      console.log(`[APICache] Expired: ${key}`);
      return null;
    }

    console.log(`[APICache] Hit: ${key}`);
    return cached.data;
  }

  /**
   * Асинхронное получение из кеша (сначала L1 память, затем L2 IndexedDB)
   * @param {string} key - Ключ
   * @returns {Promise<any|null>}
   */
  async getAsync(key) {
    // 1. Проверяем синхронно в L1
    const l1Data = this.get(key);
    if (l1Data !== null) {
      return l1Data;
    }

    // 2. Проверяем в IndexedDB L2
    if (this.usePersistentStorage && browserCache) {
      try {
        const l2Data = await browserCache.get(this.storeName, key);
        if (l2Data !== null) {
          // Восстанавливаем в память L1
          this.store.set(key, {
            data: l2Data,
            expiresAt: Date.now() + this.defaultTTL,
            timestamp: Date.now(),
            ttl: this.defaultTTL
          });
          console.log(`[APICache] Hit from IndexedDB: ${key}`);
          return l2Data;
        }
      } catch (err) {
        console.warn(`[APICache] Ошибка чтения IndexedDB для ${key}:`, err);
      }
    }

    return null;
  }

  /**
   * Проверить есть ли валидный кеш
   */
  has(key) {
    return this.get(key) !== null;
  }

  /**
   * Инвалидировать кеш по паттерну (RegExp или строка)
   * @param {string|RegExp} pattern - Паттерн для инвалидации
   */
  invalidate(pattern) {
    let keysToDelete = [];

    if (pattern instanceof RegExp) {
      keysToDelete = Array.from(this.store.keys()).filter(key => 
        pattern.test(key)
      );
    } else if (typeof pattern === 'string') {
      keysToDelete = Array.from(this.store.keys()).filter(key => 
        key === pattern || key.startsWith(pattern)
      );
    }

    keysToDelete.forEach(key => {
      this.store.delete(key);
      console.log(`[APICache] Invalidated in Memory: ${key}`);
    });

    if (this.usePersistentStorage && browserCache) {
      browserCache.invalidateByPattern(this.storeName, pattern).catch(() => {});
    }

    return keysToDelete.length;
  }

  /**
   * Очистить весь кеш API
   */
  clear() {
    const count = this.store.size;
    this.store.clear();
    if (this.usePersistentStorage && browserCache) {
      browserCache.clearStore(this.storeName).catch(() => {});
    }
    console.log(`[APICache] Cleared ${count} entries`);
  }

  /**
   * Получить информацию о кеше
   */
  getStats() {
    return {
      size: this.store.size,
      entries: Array.from(this.store.entries()).map(([key, value]) => ({
        key,
        expiresIn: Math.max(0, value.expiresAt - Date.now()),
        expired: Date.now() > value.expiresAt,
        ttl: value.ttl,
        dataSize: JSON.stringify(value.data).length
      }))
    };
  }

  /**
   * Установить новый TTL по умолчанию
   */
  setDefaultTTL(ttl) {
    this.defaultTTL = ttl;
  }
}

/**
 * APIFetcher - Обертка над fetch с поддержкой многоуровневого кеширования
 */
class APIFetcher {
  constructor(cache = null) {
    this.cache = cache || new APICache();
    this.defaultHeaders = {
      'Content-Type': 'application/json'
    };
  }

  /**
   * Выполнить fetch с автоматическим кешированием
   * @param {string} url - URL запроса
   * @param {object} options - Опции fetch (method, body, headers и т.д.)
   * @param {object} cacheOptions - Опции кеширования
   */
  async fetch(url, options = {}, cacheOptions = {}) {
    const method = (options.method || 'GET').toUpperCase();
    const isGetRequest = method === 'GET' || method === 'HEAD';
    const useCache = cacheOptions.useCache !== false && isGetRequest;

    // Пытаемся получить из кеша (сначала L1, затем L2 IndexedDB)
    if (useCache) {
      const cached = await this.cache.getAsync(url);
      if (cached) {
        console.log(`[APIFetcher] Returning from cache: ${url}`);
        return cached;
      }
    }

    // Выполняем fetch
    console.log(`[APIFetcher] Fetching: ${method} ${url}`);
    const response = await fetch(url, {
      ...options,
      headers: {
        ...this.defaultHeaders,
        ...(options.headers || {})
      }
    });

    if (!response.ok) {
      let msg = response.statusText;
      try {
        const data = await response.json();
        if (data && data.detail) {
          msg = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
        }
      } catch {}
      throw new Error(`${response.status} ${msg}`);
    }

    const data = await response.json();

    // Кешируем GET запросы
    if (useCache) {
      const ttl = cacheOptions.ttl || this.cache.defaultTTL;
      this.cache.set(url, data, ttl, {
        tags: cacheOptions.tags,
        persist: cacheOptions.persist
      });
    }

    // Инвалидируем кеш для мутирующих запросов (POST/PUT/DELETE)
    if (cacheOptions.invalidatePatterns) {
      cacheOptions.invalidatePatterns.forEach(pattern => {
        this.cache.invalidate(pattern);
      });
    }

    return data;
  }

  /**
   * GET запрос (кешируется)
   */
  get(url, options = {}, cacheOptions = {}) {
    return this.fetch(url, { ...options, method: 'GET' }, { useCache: true, ...cacheOptions });
  }

  /**
   * POST запрос (не кешируется, инвалидирует кеш)
   */
  post(url, body, options = {}, invalidatePatterns = []) {
    return this.fetch(
      url,
      { ...options, method: 'POST', body: JSON.stringify(body) },
      { useCache: false, invalidatePatterns }
    );
  }

  /**
   * PUT запрос (не кешируется, инвалидирует кеш)
   */
  put(url, body, options = {}, invalidatePatterns = []) {
    return this.fetch(
      url,
      { ...options, method: 'PUT', body: JSON.stringify(body) },
      { useCache: false, invalidatePatterns }
    );
  }

  /**
   * DELETE запрос (не кешируется, инвалидирует кеш)
   */
  delete(url, options = {}, invalidatePatterns = []) {
    return this.fetch(
      url,
      { ...options, method: 'DELETE' },
      { useCache: false, invalidatePatterns }
    );
  }

  /**
   * Очистить весь кеш
   */
  clearCache() {
    this.cache.clear();
  }

  /**
   * Получить статистику кеша
   */
  getCacheStats() {
    return this.cache.getStats();
  }
}

// Экспортируем глобально
if (typeof window !== 'undefined') {
  window.APICache = APICache;
  window.APIFetcher = APIFetcher;
}

export { APICache, APIFetcher };
