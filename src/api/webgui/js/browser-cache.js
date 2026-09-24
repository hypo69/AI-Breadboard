/**
 * browser-cache.js - Универсальный менеджер браузерного кеша и долговременного хранилища
 * 
 * Предоставляет многоуровневое хранилище (L1 In-Memory + L2 IndexedDB + L3 Fallback)
 * для эффективного хранения больших объемов клиентских данных:
 * - Ответы API и справочники
 * - RAG-индексы, эмбеддинги и поисковые чанки
 * - История чатов и сообщений ассистентов
 * - Аудиофайлы TTS и медиа-блобы (Blob / ArrayBuffer)
 * - Реестры моделей и системные конфигурации
 * 
 * Включает автоматическую очистку по TTL, групповую инвалидацию по тегам,
 * мониторинг дисковой квоты браузера и персистентность.
 * 
 * ПРИМЕЧАНИЕ: Приложение запускается в своем окне через Edge --app=url,
 * что может ограничивать доступ к Storage API. Проверьте консоль браузера
 * на наличие предупреждений о недоступности IndexedDB.
 */

const DB_NAME = 'AI_Breadboard_DB';
const DB_VERSION = 1;

// Стандартные хранилища объектов IndexedDB
export const STORES = {
  API_CACHE: 'api_cache',
  RAG_EMBEDDINGS: 'rag_embeddings',
  CHAT_HISTORY: 'chat_history',
  MEDIA_BLOBS: 'media_blobs',
  MODELS_REGISTRY: 'models_registry',
  KEY_VALUE: 'key_value'
};

export class BrowserCacheManager {
  /**
   * Инициализация менеджера браузерного кеша
   * @param {Object} options - Параметры конфигурации
   * @param {number} options.defaultTTL - Время жизни по умолчанию (в мс, 1 час = 3600000)
   * @param {number} options.maxMemoryEntries - Максимальное число записей в L1 памяти
   */
  constructor(options = {}) {
    this.defaultTTL = options.defaultTTL || 60 * 60 * 1000; // 1 час
    this.maxMemoryEntries = options.maxMemoryEntries || 200;
    this.memoryCache = new Map(); // L1 Cache: key -> { value, expiresAt, storeName, tags }
    this.db = null;
    this.isDbReady = false;
    this.initPromise = this._initIndexedDB();
    
    // Метрики
    this.stats = {
      hits: 0,
      misses: 0,
      writes: 0,
      deletes: 0
    };

    // Периодическая фоновая очистка просроченных записей каждые 10 минут
    if (typeof window !== 'undefined') {
      window.setInterval(() => this.cleanupExpired(), 10 * 60 * 1000);
    }
  }

  /**
   * Инициализация базы данных IndexedDB
   * @private
   */
  async _initIndexedDB() {
    if (typeof window === 'undefined' || !window.indexedDB) {
      console.warn('[BrowserCache] IndexedDB недоступен в текущем окружении. Используется fallback на память.');
      console.warn('[BrowserCache] Возможные причины:');
      console.warn('[BrowserCache] 1. Приложение запущено в PWA-окне (Edge --app=url)');
      console.warn('[BrowserCache] 2. Ограничения безопасности браузера');
      console.warn('[BrowserCache] 3. Поврежденный user-data-dir');
      this.isDbReady = false;
      return null;
    }

    return new Promise((resolve) => {
      try {
        const request = indexedDB.open(DB_NAME, DB_VERSION);

        request.onupgradeneeded = (event) => {
          const db = event.target.result;
          
          Object.values(STORES).forEach((storeName) => {
            if (!db.objectStoreNames.contains(storeName)) {
              const store = db.createObjectStore(storeName, { keyPath: 'key' });
              store.createIndex('expiresAt', 'expiresAt', { unique: false });
              store.createIndex('updatedAt', 'updatedAt', { unique: false });
              store.createIndex('tags', 'tags', { unique: false, multiEntry: true });
            }
          });
          console.log('[BrowserCache] Структура IndexedDB успешно обновлена до версии', DB_VERSION);
        };

        request.onsuccess = (event) => {
          this.db = event.target.result;
          this.isDbReady = true;
          console.log('[BrowserCache] IndexedDB успешно подключена:', DB_NAME);
          console.log('[BrowserCache] Данные будут сохраняться в профиле пользователя:', this._getUserDataDir());
          this.cleanupExpired().catch(() => {});
          resolve(this.db);
        };

        request.onerror = (event) => {
          console.error('[BrowserCache] Ошибка открытия IndexedDB:', event.target.error);
          console.error('[BrowserCache] Проверьте:');
          console.error('[BrowserCache] 1. Есть ли права на запись в user-data-dir');
          console.error('[BrowserCache] 2. Не заблокирован ли IndexedDB политикой браузера');
          this.isDbReady = false;
          resolve(null);
        };
      } catch (err) {
        console.error('[BrowserCache] Исключение при инициализации IndexedDB:', err);
        this.isDbReady = false;
        resolve(null);
      }
    });
  }

  /**
   * Ожидание готовности базы данных
   */
  async ready() {
    await this.initPromise;
    return this.isDbReady;
  }

  /**
   * Сохранить значение в кеш (L1 память + L2 IndexedDB)
   * @param {string} storeName - Имя хранилища (из STORES)
   * @param {string} key - Уникальный ключ
   * @param {any} value - Данные (объект, массив, строка, Blob, ArrayBuffer)
   * @param {Object} options - Опции записи (ttl, tags, persist)
   * @returns {Promise<boolean>}
   */
  async set(storeName = STORES.KEY_VALUE, key, value, options = {}) {
    if (!key) return false;
    await this.ready();

    const ttl = options.ttl !== undefined ? options.ttl : this.defaultTTL;
    const now = Date.now();
    const expiresAt = ttl > 0 ? now + ttl : 0; // 0 = бессрочно
    const tags = Array.isArray(options.tags) ? options.tags : (options.tags ? [options.tags] : []);
    
    const record = {
      key,
      value,
      expiresAt,
      createdAt: now,
      updatedAt: now,
      tags,
      size: this._estimateSize(value)
    };

    // 1. Сохранение в L1 In-Memory Cache
    const memKey = `${storeName}:${key}`;
    this._setMemoryCache(memKey, record);
    this.stats.writes++;

    // Если persist = false, сохраняем только в L1 памяти
    if (options.persist === false) {
      return true;
    }

    // 2. Сохранение в L2 IndexedDB
    if (this.isDbReady && this.db) {
      try {
        await new Promise((resolve, reject) => {
          const transaction = this.db.transaction([storeName], 'readwrite');
          const store = transaction.objectStore(storeName);
          const request = store.put(record);

          request.onsuccess = () => resolve(true);
          request.onerror = (e) => reject(e.target.error);
        });
        return true;
      } catch (err) {
        console.warn(`[BrowserCache] Ошибка записи в IndexedDB (${storeName}/${key}):`, err);
      }
    }

    return true;
  }

  /**
   * Получить значение из кеша (L1 -> L2)
   * @param {string} storeName - Имя хранилища
   * @param {string} key - Ключ
   * @returns {Promise<any|null>}
   */
  async get(storeName = STORES.KEY_VALUE, key) {
    if (!key) return null;
    await this.ready();

    const now = Date.now();
    const memKey = `${storeName}:${key}`;

    // 1. Проверяем L1 In-Memory Cache
    const memRecord = this.memoryCache.get(memKey);
    if (memRecord) {
      if (memRecord.expiresAt > 0 && now > memRecord.expiresAt) {
        this.memoryCache.delete(memKey);
        this.delete(storeName, key).catch(() => {});
        this.stats.misses++;
        return null;
      }
      this.stats.hits++;
      return memRecord.value;
    }

    // 2. Проверяем L2 IndexedDB
    if (this.isDbReady && this.db) {
      try {
        const record = await new Promise((resolve, reject) => {
          const transaction = this.db.transaction([storeName], 'readonly');
          const store = transaction.objectStore(storeName);
          const request = store.get(key);

          request.onsuccess = () => resolve(request.result);
          request.onerror = (e) => reject(e.target.error);
        });

        if (!record) {
          this.stats.misses++;
          return null;
        }

        // Проверяем срок действия
        if (record.expiresAt > 0 && now > record.expiresAt) {
          this.delete(storeName, key).catch(() => {});
          this.stats.misses++;
          return null;
        }

        // Добавляем в L1 для ускорения повторных обращений
        this._setMemoryCache(memKey, record);
        this.stats.hits++;
        return record.value;
      } catch (err) {
        console.warn(`[BrowserCache] Ошибка чтения из IndexedDB (${storeName}/${key}):`, err);
      }
    }

    this.stats.misses++;
    return null;
  }

  /**
   * Проверить наличие актуального ключа в кеше
   */
  async has(storeName = STORES.KEY_VALUE, key) {
    const val = await this.get(storeName, key);
    return val !== null;
  }

  /**
   * Удалить запись из кеша
   * @param {string} storeName - Имя хранилища
   * @param {string} key - Ключ
   */
  async delete(storeName = STORES.KEY_VALUE, key) {
    if (!key) return false;
    await this.ready();

    const memKey = `${storeName}:${key}`;
    this.memoryCache.delete(memKey);
    this.stats.deletes++;

    if (this.isDbReady && this.db) {
      try {
        await new Promise((resolve, reject) => {
          const transaction = this.db.transaction([storeName], 'readwrite');
          const store = transaction.objectStore(storeName);
          const request = store.delete(key);

          request.onsuccess = () => resolve(true);
          request.onerror = (e) => reject(e.target.error);
        });
        return true;
      } catch (err) {
        console.warn(`[BrowserCache] Ошибка удаления из IndexedDB (${storeName}/${key}):`, err);
      }
    }
    return true;
  }

  /**
   * Инвалидировать записи по тегу (например: 'models', 'chat_session_1')
   * @param {string} storeName - Имя хранилища
   * @param {string} tag - Тег для поиска
   */
  async invalidateByTag(storeName = STORES.KEY_VALUE, tag) {
    await this.ready();

    // Удаляем из L1
    for (const [memKey, record] of this.memoryCache.entries()) {
      if (memKey.startsWith(`${storeName}:`) && record.tags && record.tags.includes(tag)) {
        this.memoryCache.delete(memKey);
      }
    }

    if (!this.isDbReady || !this.db) return 0;

    let count = 0;
    try {
      count = await new Promise((resolve, reject) => {
        const transaction = this.db.transaction([storeName], 'readwrite');
        const store = transaction.objectStore(storeName);
        const index = store.index('tags');
        const request = index.getAllKeys(tag);

        request.onsuccess = () => {
          const keys = request.result || [];
          keys.forEach((k) => store.delete(k));
          resolve(keys.length);
        };
        request.onerror = (e) => reject(e.target.error);
      });
      console.log(`[BrowserCache] Инвалидировано ${count} записей по тегу '${tag}' в '${storeName}'`);
    } catch (err) {
      console.warn(`[BrowserCache] Ошибка инвалидации по тегу '${tag}':`, err);
    }
    return count;
  }

  /**
   * Инвалидировать записи по регулярному выражению или префиксу ключа
   * @param {string} storeName - Имя хранилища
   * @param {string|RegExp} pattern - Регулярное выражение или строка префикса
   */
  async invalidateByPattern(storeName = STORES.KEY_VALUE, pattern) {
    await this.ready();

    const isRegExp = pattern instanceof RegExp;
    const testMatch = (key) => isRegExp ? pattern.test(key) : (key === pattern || key.startsWith(pattern));

    // Очистка L1
    for (const [memKey] of this.memoryCache.entries()) {
      if (memKey.startsWith(`${storeName}:`)) {
        const rawKey = memKey.replace(`${storeName}:`, '');
        if (testMatch(rawKey)) {
          this.memoryCache.delete(memKey);
        }
      }
    }

    if (!this.isDbReady || !this.db) return 0;

    let deletedCount = 0;
    try {
      deletedCount = await new Promise((resolve, reject) => {
        const transaction = this.db.transaction([storeName], 'readwrite');
        const store = transaction.objectStore(storeName);
        const request = store.openCursor();

        request.onsuccess = (event) => {
          const cursor = event.target.result;
          if (cursor) {
            if (testMatch(cursor.key)) {
              cursor.delete();
              deletedCount++;
            }
            cursor.continue();
          } else {
            resolve(deletedCount);
          }
        };
        request.onerror = (e) => reject(e.target.error);
      });
      console.log(`[BrowserCache] Инвалидировано ${deletedCount} записей по паттерну в '${storeName}'`);
    } catch (err) {
      console.warn(`[BrowserCache] Ошибка инвалидации по паттерну в '${storeName}':`, err);
    }
    return deletedCount;
  }

  /**
   * Полностью очистить указанное хранилище
   * @param {string} storeName - Имя хранилища
   */
  async clearStore(storeName = STORES.KEY_VALUE) {
    await this.ready();

    // Очистка L1
    for (const [memKey] of this.memoryCache.entries()) {
      if (memKey.startsWith(`${storeName}:`)) {
        this.memoryCache.delete(memKey);
      }
    }

    if (this.isDbReady && this.db) {
      try {
        await new Promise((resolve, reject) => {
          const transaction = this.db.transaction([storeName], 'readwrite');
          const store = transaction.objectStore(storeName);
          const request = store.clear();

          request.onsuccess = () => resolve(true);
          request.onerror = (e) => reject(e.target.error);
        });
        console.log(`[BrowserCache] Хранилище '${storeName}' полностью очищено.`);
        return true;
      } catch (err) {
        console.warn(`[BrowserCache] Ошибка очистки хранилища '${storeName}':`, err);
      }
    }
    return true;
  }

  /**
   * Очистить абсолютно все хранилища
   */
  async clearAll() {
    this.memoryCache.clear();
    for (const storeName of Object.values(STORES)) {
      await this.clearStore(storeName);
    }
    console.log('[BrowserCache] Все хранилища браузерного кеша очищены.');
  }

  /**
   * Очистить просроченные записи во всех хранилищах
   */
  async cleanupExpired() {
    await this.ready();
    const now = Date.now();

    // L1
    for (const [memKey, record] of this.memoryCache.entries()) {
      if (record.expiresAt > 0 && now > record.expiresAt) {
        this.memoryCache.delete(memKey);
      }
    }

    if (!this.isDbReady || !this.db) return 0;

    let totalDeleted = 0;
    for (const storeName of Object.values(STORES)) {
      try {
        const deletedInStore = await new Promise((resolve, reject) => {
          const transaction = this.db.transaction([storeName], 'readwrite');
          const store = transaction.objectStore(storeName);
          const index = store.index('expiresAt');
          const range = IDBKeyRange.bound(1, now);
          const request = index.openCursor(range);
          let count = 0;

          request.onsuccess = (event) => {
            const cursor = event.target.result;
            if (cursor) {
              cursor.delete();
              count++;
              cursor.continue();
            } else {
              resolve(count);
            }
          };
          request.onerror = (e) => reject(e.target.error);
        });
        totalDeleted += deletedInStore;
      } catch (e) {
        // Игнорируем возможные локальные ошибки курсора
      }
    }

    if (totalDeleted > 0) {
      console.log(`[BrowserCache] Фоновый сборщик мусора удалил ${totalDeleted} просроченных записей.`);
    }
    return totalDeleted;
  }

  /**
   * Получить детальную статистику использования кеша и дисковой квоты
   */
  async getDetailedStats() {
    await this.ready();
    const stats = {
      metrics: { ...this.stats },
      memoryCacheSize: this.memoryCache.size,
      stores: {},
      storageEstimate: {
        usage: 0,
        quota: 0,
        usageMB: '0.00',
        quotaMB: '0.00',
        percentUsed: 0,
        isPersisted: false
      }
    };

    // Оценка дискового пространства через navigator.storage API
    if (typeof navigator !== 'undefined' && navigator.storage && navigator.storage.estimate) {
      try {
        const estimate = await navigator.storage.estimate();
        const usage = estimate.usage || 0;
        const quota = estimate.quota || 0;
        const usageMB = (usage / (1024 * 1024)).toFixed(2);
        const quotaMB = (quota / (1024 * 1024)).toFixed(2);
        const percentUsed = quota > 0 ? ((usage / quota) * 100).toFixed(2) : 0;
        
        let isPersisted = false;
        if (navigator.storage.persisted) {
          isPersisted = await navigator.storage.persisted();
        }

        stats.storageEstimate = {
          usage,
          quota,
          usageMB,
          quotaMB,
          percentUsed: Number(percentUsed),
          isPersisted
        };
      } catch (err) {
        console.warn('[BrowserCache] Не удалось получить navigator.storage.estimate:', err);
      }
    }

    // Подсчет записей и объема по каждому хранилищу
    if (this.isDbReady && this.db) {
      for (const storeName of Object.values(STORES)) {
        try {
          const storeData = await new Promise((resolve) => {
            const transaction = this.db.transaction([storeName], 'readonly');
            const store = transaction.objectStore(storeName);
            const countReq = store.count();
            const allReq = store.getAll();

            let count = 0;
            let totalBytes = 0;

            countReq.onsuccess = () => { count = countReq.result || 0; };
            allReq.onsuccess = () => {
              const records = allReq.result || [];
              records.forEach(r => {
                totalBytes += r.size || this._estimateSize(r.value);
              });
              resolve({ count, sizeBytes: totalBytes });
            };
            allReq.onerror = () => resolve({ count: 0, sizeBytes: 0 });
          });

          stats.stores[storeName] = {
            count: storeData.count,
            sizeBytes: storeData.sizeBytes,
            sizeKB: (storeData.sizeBytes / 1024).toFixed(2),
            sizeMB: (storeData.sizeBytes / (1024 * 1024)).toFixed(2)
          };
        } catch (e) {
          stats.stores[storeName] = { count: 0, sizeBytes: 0, sizeKB: '0', sizeMB: '0' };
        }
      }
    }

    return stats;
  }

  /**
   * Запросить у браузера постоянное хранилище (защита от случайной очистки)
   */
  async requestPersistence() {
    if (typeof navigator !== 'undefined' && navigator.storage && navigator.storage.persist) {
      const isPersisted = await navigator.storage.persist();
      console.log(`[BrowserCache] Запрос персистентности хранилища: ${isPersisted ? 'Одобрено' : 'Отклонено'}`);
      return isPersisted;
    }
    return false;
  }

  /**
   * Экспортировать данные хранилищ в JSON-структуру
   * @param {Array<string>} storeNames - Список хранилищ для экспорта
   */
  async exportData(storeNames = [STORES.API_CACHE, STORES.MODELS_REGISTRY, STORES.CHAT_HISTORY]) {
    await this.ready();
    const exportResult = {
      version: DB_VERSION,
      timestamp: Date.now(),
      exportedAt: new Date().toISOString(),
      stores: {}
    };

    if (!this.isDbReady || !this.db) {
      console.warn('[BrowserCache] Cannot export data: IndexedDB not ready');
      return exportResult;
    }

    for (const storeName of storeNames) {
      try {
        const records = await new Promise((resolve, reject) => {
          const transaction = this.db.transaction([storeName], 'readonly');
          const store = transaction.objectStore(storeName);
          const request = store.getAll();
          request.onsuccess = () => resolve(request.result || []);
          request.onerror = (e) => reject(e.target.error);
        });
        exportResult.stores[storeName] = records;
      } catch (err) {
        console.warn(`[BrowserCache] Ошибка экспорта из ${storeName}:`, err);
      }
    }

    return exportResult;
  }

  /**
   * Импортировать данные в хранилища
   * @param {Object} data - Экспортированный объект данных
   */
  async importData(data) {
    if (!data || !data.stores) return false;
    await this.ready();

    for (const [storeName, records] of Object.entries(data.stores)) {
      if (!Object.values(STORES).includes(storeName)) continue;
      if (!Array.isArray(records)) continue;

      for (const record of records) {
        if (record && record.key) {
          await this.set(storeName, record.key, record.value, {
            ttl: record.expiresAt ? Math.max(0, record.expiresAt - Date.now()) : 0,
            tags: record.tags || []
          });
        }
      }
    }
    console.log('[BrowserCache] Импорт данных успешно завершен.');
    return true;
  }

  /**
   * Добавить запись в L1 In-Memory Cache с контролем размера (LRU eviction)
   * @private
   */
  _setMemoryCache(key, record) {
    if (this.memoryCache.size >= this.maxMemoryEntries) {
      const firstKey = this.memoryCache.keys().next().value;
      if (firstKey) this.memoryCache.delete(firstKey);
    }
    this.memoryCache.set(key, record);
  }

  /**
   * Приблизительная оценка размера объекта в байтах
   * @private
   */
  _estimateSize(value) {
    if (value === null || value === undefined) return 0;
    if (typeof value === 'string') return value.length * 2;
    if (typeof value === 'number') return 8;
    if (typeof value === 'boolean') return 4;
    if (typeof Blob !== 'undefined' && value instanceof Blob) return value.size;
    if (typeof ArrayBuffer !== 'undefined' && value instanceof ArrayBuffer) return value.byteLength;
    try {
      return JSON.stringify(value).length * 2;
    } catch {
      return 1024;
    }
  }
  
  /**
   * Попытка получить путь к user-data-dir (для отладки)
   * @private
   */
  _getUserDataDir() {
    // В браузере этот путь недоступен из-за ограничений безопасности
    // Но мы можем попытаться определить, запущено ли приложение в PWA-окне
    const isPWA = window.matchMedia('(display-mode: standalone)').matches;
    return isPWA ? '[PWA-окно - путь недоступен]' : '[Обычное окно]';
  }
}

// Создаем глобальный singleton экземпляр
export const browserCache = new BrowserCacheManager();

// Регистрация в глобальном объекте window для доступности во всех вкладках и скриптах
if (typeof window !== 'undefined') {
  window.BrowserCacheManager = BrowserCacheManager;
  window.browserCache = browserCache;
  window.BROWSER_STORES = STORES;
}

export default browserCache;
