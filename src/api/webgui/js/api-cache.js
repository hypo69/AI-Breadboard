/**
 * APICache - Система кеширования API ответов
 * 
 * Кеширует GET запросы на клиенте, инвалидирует кеш при изменениях.
 * Снижает нагрузку на сервер и ускоряет интерфейс.
 * 
 * Usage:
 *   const cache = new APICache();
 *   cache.set('/api/users', data, 5 * 60 * 1000);  // 5 минут
 *   const cached = cache.get('/api/users');
 *   cache.invalidate(/\/api\/users/);  // Pattern-based invalidation
 */

class APICache {
  constructor() {
    this.store = new Map(); // { key: { data, expiresAt, timestamp } }
    this.defaultTTL = 5 * 60 * 1000; // 5 минут по умолчанию
  }

  /**
   * Сохранить данные в кеш
   * @param {string} key - Ключ (обычно URL)
   * @param {any} data - Данные для кеширования
   * @param {number} ttl - Time to live в миллисекундах (опционально)
   */
  set(key, data, ttl = this.defaultTTL) {
    const expiresAt = Date.now() + ttl;
    this.store.set(key, {
      data: JSON.parse(JSON.stringify(data)), // Глубокая копия
      expiresAt,
      timestamp: Date.now(),
      ttl
    });
    console.log(`[APICache] Cached: ${key} (TTL: ${ttl}ms)`);
  }

  /**
   * Получить данные из кеша если они актуальны
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
      console.log(`[APICache] Expired: ${key}`);
      return null;
    }

    console.log(`[APICache] Hit: ${key}`);
    return cached.data;
  }

  /**
   * Проверить есть ли валидный кеш
   */
  has(key) {
    return this.get(key) !== null;
  }

  /**
   * Инвалидировать кеш по паттерну (RegExp)
   * Используется для очистки кеша при обновлении данных
   * 
   * @param {string|RegExp} pattern - Паттерн для инвалидации
   * @example
   *   cache.invalidate(/\/api\/users/);  // Очистить все кеши /api/users*
   *   cache.invalidate('/api/users');    // Точное совпадение
   */
  invalidate(pattern) {
    let keysToDelete = [];

    if (pattern instanceof RegExp) {
      keysToDelete = Array.from(this.store.keys()).filter(key => 
        pattern.test(key)
      );
    } else if (typeof pattern === 'string') {
      // Точное совпадение или startsWith
      keysToDelete = Array.from(this.store.keys()).filter(key => 
        key === pattern || key.startsWith(pattern)
      );
    }

    keysToDelete.forEach(key => {
      this.store.delete(key);
      console.log(`[APICache] Invalidated: ${key}`);
    });

    return keysToDelete.length;
  }

  /**
   * Очистить весь кеш
   */
  clear() {
    const count = this.store.size;
    this.store.clear();
    console.log(`[APICache] Cleared ${count} entries`);
  }

  /**
   * Получить информацию о кеше (для отладки)
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
 * APIFetcher - Обертка над fetch с поддержкой кеширования
 * 
 * Автоматически кеширует GET запросы и инвалидирует кеш при
 * изменении данных (POST/PUT/DELETE)
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
   *   - useCache (bool): использовать ли кеш (для GET по умолчанию true)
   *   - ttl (number): TTL в миллисекундах
   *   - invalidatePatterns (array): паттерны для инвалидации при успехе
   */
  async fetch(url, options = {}, cacheOptions = {}) {
    const method = (options.method || 'GET').toUpperCase();
    const isGetRequest = method === 'GET' || method === 'HEAD';
    const useCache = cacheOptions.useCache !== false && isGetRequest;

    // Пытаемся получить из кеша для GET запросов
    if (useCache) {
      const cached = this.cache.get(url);
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
      this.cache.set(url, data, ttl);
    }

    // Инвалидируем кеш для POST/PUT/DELETE запросов
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
  get(url, options = {}) {
    return this.fetch(url, { ...options, method: 'GET' }, { useCache: true });
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
window.APICache = APICache;
window.APIFetcher = APIFetcher;

export { APICache, APIFetcher };
