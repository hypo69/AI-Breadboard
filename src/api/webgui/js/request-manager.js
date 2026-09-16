/**
 * RequestManager - Умное управление запросами
 * 
 * Предотвращает дублирующиеся запросы через дебаунсинг и батчинг
 * 
 * Usage:
 *   const manager = new RequestManager();
 *   manager.debounce('search-users', async () => {
 *     const result = await api.search(term);
 *   }, 500);
 */

class RequestManager {
  constructor() {
    this.debounceTimers = new Map(); // { key: timeoutId }
    this.pendingRequests = new Map(); // { key: Promise }
    this.requestCache = new Map(); // { key: result }
  }

  /**
   * Дебаунс функции - откладывает выполнение, если вызов повторяется
   * 
   * @param {string} key - Уникальный ключ для дебаунса
   * @param {function} fn - Функция для выполнения
   * @param {number} delay - Задержка в миллисекундах
   * @returns {Promise} - Результат выполнения функции
   */
  debounce(key, fn, delay = 300) {
    return new Promise((resolve, reject) => {
      // Отмены предыдущий таймер если был
      if (this.debounceTimers.has(key)) {
        clearTimeout(this.debounceTimers.get(key));
      }

      // Устанавливаем новый таймер
      const timeoutId = setTimeout(async () => {
        try {
          const result = await fn();
          this.requestCache.set(key, result);
          resolve(result);
        } catch (error) {
          reject(error);
        } finally {
          this.debounceTimers.delete(key);
        }
      }, delay);

      this.debounceTimers.set(key, timeoutId);
    });
  }

  /**
   * Отмена дебаунса
   */
  cancelDebounce(key) {
    if (this.debounceTimers.has(key)) {
      clearTimeout(this.debounceTimers.get(key));
      this.debounceTimers.delete(key);
    }
  }

  /**
   * Отмена всех дебаунсов
   */
  cancelAll() {
    this.debounceTimers.forEach(timeoutId => clearTimeout(timeoutId));
    this.debounceTimers.clear();
  }

  /**
   * Батчинг - объединяет несколько запросов в один
   * 
   * @param {string} key - Уникальный ключ батча
   * @param {function} batchFn - Функция которая выполняет батч операцию
   * @param {any} item - Элемент для добавления в батч
   * @param {number} flushDelay - Задержка перед отправкой батча
   */
  batch(key, batchFn, item, flushDelay = 100) {
    if (!this.pendingRequests.has(key)) {
      this.pendingRequests.set(key, { items: [], promise: null });
    }

    const batch = this.pendingRequests.get(key);
    batch.items.push(item);

    if (!batch.promise) {
      batch.promise = new Promise((resolve, reject) => {
        setTimeout(async () => {
          try {
            const items = batch.items;
            this.pendingRequests.delete(key);
            
            console.log(`[RequestManager] Batching ${items.length} items for ${key}`);
            const result = await batchFn(items);
            resolve(result);
          } catch (error) {
            this.pendingRequests.delete(key);
            reject(error);
          }
        }, flushDelay);
      });
    }

    return batch.promise;
  }

  /**
   * Throttle функции - вызывает функцию максимум один раз за period ms
   * 
   * @param {string} key - Уникальный ключ для throttle
   * @param {function} fn - Функция для выполнения
   * @param {number} period - Минимальный интервал между вызовами
   * @returns {function} - Завернутая функция
   */
  throttle(key, fn, period = 1000) {
    let lastCall = 0;
    let timeoutId = null;

    return async (...args) => {
      const now = Date.now();
      const timeSinceLastCall = now - lastCall;

      if (timeSinceLastCall >= period) {
        lastCall = now;
        return fn.apply(this, args);
      } else {
        // Запланируем вызов на конец периода
        if (timeoutId) clearTimeout(timeoutId);
        
        return new Promise((resolve) => {
          timeoutId = setTimeout(() => {
            lastCall = Date.now();
            fn.apply(this, args).then(resolve);
          }, period - timeSinceLastCall);
        });
      }
    };
  }

  /**
   * Дублирование запросов - если один и тот же запрос идет дважды,
   * вернуть результат первого вместо создания второго
   * 
   * @param {string} key - Уникальный ключ запроса
   * @param {function} fn - Функция для выполнения
   * @returns {Promise}
   */
  deduplicate(key, fn) {
    // Если такой запрос уже в процессе - вернуть его
    if (this.pendingRequests.has(key)) {
      console.log(`[RequestManager] Deduplicating request: ${key}`);
      return this.pendingRequests.get(key);
    }

    // Выполнить запрос
    const promise = fn();
    this.pendingRequests.set(key, promise);

    promise
      .then(result => {
        this.requestCache.set(key, result);
        return result;
      })
      .finally(() => {
        this.pendingRequests.delete(key);
      });

    return promise;
  }

  /**
   * Получить кешированный результат
   */
  getCache(key) {
    return this.requestCache.get(key) || null;
  }

  /**
   * Очистить кеш
   */
  clearCache() {
    this.requestCache.clear();
  }

  /**
   * Получить статистику
   */
  getStats() {
    return {
      pendingDebounces: this.debounceTimers.size,
      pendingRequests: this.pendingRequests.size,
      cachedResults: this.requestCache.size,
      debounceKeys: Array.from(this.debounceTimers.keys()),
      requestKeys: Array.from(this.pendingRequests.keys()),
      cacheKeys: Array.from(this.requestCache.keys())
    };
  }
}

/**
 * Вспомогательные функции для использования в компонентах
 */
const RequestManagerHelper = {
  /**
   * Создать дебаунс функцию поиска
   */
  createSearchDebounce(searchFn, delay = 500) {
    const manager = new RequestManager();
    return (query) => manager.debounce('search', () => searchFn(query), delay);
  },

  /**
   * Создать дебаунс функцию для автосохранения
   */
  createAutoSaveDebounce(saveFn, delay = 1000) {
    const manager = new RequestManager();
    return (data) => manager.debounce('autosave', () => saveFn(data), delay);
  },

  /**
   * Создать throttle функцию для обновления статуса
   */
  createStatusUpdateThrottle(updateFn, period = 2000) {
    const manager = new RequestManager();
    return manager.throttle('status-update', updateFn, period);
  }
};

// Экспортируем глобально
window.RequestManager = RequestManager;
window.RequestManagerHelper = RequestManagerHelper;

export { RequestManager, RequestManagerHelper };
