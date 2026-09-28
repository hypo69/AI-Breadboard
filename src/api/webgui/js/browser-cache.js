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

const DB_NAME = 'AI_Breadboard_DBi18n.t('auto__const_db_version_1_indexeddb_export_const_stores_api_cache__576b5b')api_cache',
  RAG_EMBEDDINGS: 'rag_embeddings',
  CHAT_HISTORY: 'chat_history',
  MEDIA_BLOBS: 'media_blobs',
  MODELS_REGISTRY: 'models_registry',
  KEY_VALUE: 'key_valuei18n.t('auto__export_class_browsercachemanager_param_object_options_param_number_options_defaultttl_1_3600000_param_number_options_maxmemoryentries_l1_constructor_options_this_defaultttl_options_defaultttl_60_60_1000_1_this_maxmemoryentries_options_maxmemoryentries_200_this_memorycache_new_map_l1_cache_key_value_expiresat_storename_tags_this_db_null_this_isdbready_false_this_initpromise_this_initindexeddb_this_stats_hits_0_misses_0_writes_0_deletes_0_10_if_typeof_window__c955a8')undefinedi18n.t('auto__window_setinterval_this_cleanupexpired_10_60_1000_indexeddb_private_async_initindexeddb_if_typeof_window__163384')undefined' || !window.indexedDB) {
      console.warn(i18n.t('auto__browsercache_indexeddb_fallback__e7972e'));
      console.warn(i18n.t('auto__browsercache__d7bbb5'));
      console.warn(i18n.t('auto__browsercache_1_pwa_edge_app_url__f064b3'));
      console.warn(i18n.t('auto__browsercache_2__88ff63'));
      console.warn(i18n.t('auto__browsercache_3_user_data_dir_5691ae'));
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
          console.log(i18n.t('auto__browsercache_indexeddb__daf56a'), DB_VERSION);
        };

        request.onsuccess = (event) => {
          this.db = event.target.result;
          this.isDbReady = true;
          console.log(i18n.t('auto__browsercache_indexeddb__5a2d7f'), DB_NAME);
          console.log(i18n.t('auto__browsercache__a24f07'), this._getUserDataDir());
          this.cleanupExpired().catch(() => {});
          resolve(this.db);
        };

        request.onerror = (event) => {
          console.error(i18n.t('auto__browsercache_indexeddb__47db9e'), event.target.error);
          console.error(i18n.t('auto__browsercache__c18dde'));
          console.error(i18n.t('auto__browsercache_1_user_data_dir_57bbba'));
          console.error(i18n.t('auto__browsercache_2_indexeddb__c5f425'));
          this.isDbReady = false;
          resolve(null);
        };
      } catch (err) {
        console.error(i18n.t('auto__browsercache_indexeddb__f7d503'), err);
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
          const transaction = this.db.transaction([storeName], 'readwritei18n.t('auto__const_store_transaction_objectstore_storename_const_request_store_put_record_request_onsuccess_resolve_true_request_onerror_e_reject_e_target_error_return_true_catch_err_console_warn_browsercache_indexeddb_storename_key_err_return_true_l1_l2_param_string_storename_param_string_key_returns_promise_any_null_async_get_storename_stores_key_value_key_if_key_return_null_await_this_ready_const_now_date_now_const_memkey_storename_key_1_l1_in_memory_cache_const_memrecord_this_memorycache_get_memkey_if_memrecord_if_memrecord_expiresat_0_now_memrecord_expiresat_this_memorycache_delete_memkey_this_delete_storename_key_catch_this_stats_misses_return_null_this_stats_hits_return_memrecord_value_2_l2_indexeddb_if_this_isdbready_this_db_try_const_record_await_new_promise_resolve_reject_const_transaction_this_db_transaction_storename__2a5bc8')readonlyi18n.t('auto__const_store_transaction_objectstore_storename_const_request_store_get_key_request_onsuccess_resolve_request_result_request_onerror_e_reject_e_target_error_if_record_this_stats_misses_return_null_if_record_expiresat_0_now_record_expiresat_this_delete_storename_key_catch_this_stats_misses_return_null_l1_this_setmemorycache_memkey_record_this_stats_hits_return_record_value_catch_err_console_warn_browsercache_indexeddb_storename_key_err_this_stats_misses_return_null_async_has_storename_stores_key_value_key_const_val_await_this_get_storename_key_return_val_null_param_string_storename_param_string_key_async_delete_storename_stores_key_value_key_if_key_return_false_await_this_ready_const_memkey_storename_key_this_memorycache_delete_memkey_this_stats_deletes_if_this_isdbready_this_db_try_await_new_promise_resolve_reject_const_transaction_this_db_transaction_storename__0e4115')readwritei18n.t('auto__const_store_transaction_objectstore_storename_const_request_store_delete_key_request_onsuccess_resolve_true_request_onerror_e_reject_e_target_error_return_true_catch_err_console_warn_browsercache_indexeddb_storename_key_err_return_true__c8957c')models', 'chat_session_1i18n.t('auto__param_string_storename_param_string_tag_async_invalidatebytag_storename_stores_key_value_tag_await_this_ready_l1_for_const_memkey_record_of_this_memorycache_entries_if_memkey_startswith_storename_record_tags_record_tags_includes_tag_this_memorycache_delete_memkey_if_this_isdbready_this_db_return_0_let_count_0_try_count_await_new_promise_resolve_reject_const_transaction_this_db_transaction_storename__9b6fdb')readwrite');
        const store = transaction.objectStore(storeName);
        const index = store.index('tagsi18n.t('auto__const_request_index_getallkeys_tag_request_onsuccess_const_keys_request_result_keys_foreach_k_store_delete_k_resolve_keys_length_request_onerror_e_reject_e_target_error_console_log_browsercache_count__043a38')${tag}i18n.t('auto___1309b9')${storeName}i18n.t('auto__catch_err_console_warn_browsercache__5eccda')${tag}i18n.t('auto__err_return_count_param_string_storename_param_string_regexp_pattern_async_invalidatebypattern_storename_stores_key_value_pattern_await_this_ready_const_isregexp_pattern_instanceof_regexp_const_testmatch_key_isregexp_pattern_test_key_key_pattern_key_startswith_pattern_l1_for_const_memkey_of_this_memorycache_entries_if_memkey_startswith_storename_const_rawkey_memkey_replace_storename__9fe131')');
        if (testMatch(rawKey)) {
          this.memoryCache.delete(memKey);
        }
      }
    }

    if (!this.isDbReady || !this.db) return 0;

    let deletedCount = 0;
    try {
      deletedCount = await new Promise((resolve, reject) => {
        const transaction = this.db.transaction([storeName], 'readwritei18n.t('auto__const_store_transaction_objectstore_storename_const_request_store_opencursor_request_onsuccess_event_const_cursor_event_target_result_if_cursor_if_testmatch_cursor_key_cursor_delete_deletedcount_cursor_continue_else_resolve_deletedcount_request_onerror_e_reject_e_target_error_console_log_browsercache_deletedcount__e32068')${storeName}i18n.t('auto__catch_err_console_warn_browsercache__2cf4b4')${storeName}i18n.t('auto__err_return_deletedcount_param_string_storename_async_clearstore_storename_stores_key_value_await_this_ready_l1_for_const_memkey_of_this_memorycache_entries_if_memkey_startswith_storename_this_memorycache_delete_memkey_if_this_isdbready_this_db_try_await_new_promise_resolve_reject_const_transaction_this_db_transaction_storename__c1a10a')readwritei18n.t('auto__const_store_transaction_objectstore_storename_const_request_store_clear_request_onsuccess_resolve_true_request_onerror_e_reject_e_target_error_console_log_browsercache__5dae6a')${storeName}i18n.t('auto__return_true_catch_err_console_warn_browsercache__b3110a')${storeName}i18n.t('auto__err_return_true_async_clearall_this_memorycache_clear_for_const_storename_of_object_values_stores_await_this_clearstore_storename_console_log__7c9b5f')[BrowserCache] Все хранилища браузерного кеша очищены.i18n.t('auto__async_cleanupexpired_await_this_ready_const_now_date_now_l1_for_const_memkey_record_of_this_memorycache_entries_if_record_expiresat_0_now_record_expiresat_this_memorycache_delete_memkey_if_this_isdbready_this_db_return_0_let_totaldeleted_0_for_const_storename_of_object_values_stores_try_const_deletedinstore_await_new_promise_resolve_reject_const_transaction_this_db_transaction_storename__8cf8d1')readwrite');
          const store = transaction.objectStore(storeName);
          const index = store.index('expiresAti18n.t('auto__const_range_idbkeyrange_bound_1_now_const_request_index_opencursor_range_let_count_0_request_onsuccess_event_const_cursor_event_target_result_if_cursor_cursor_delete_count_cursor_continue_else_resolve_count_request_onerror_e_reject_e_target_error_totaldeleted_deletedinstore_catch_e_if_totaldeleted_0_console_log_browsercache_totaldeleted_return_totaldeleted_async_getdetailedstats_await_this_ready_const_stats_metrics_this_stats_memorycachesize_this_memorycache_size_stores_storageestimate_usage_0_quota_0_usagemb__896243')0.00',
        quotaMB: '0.00i18n.t('auto__percentused_0_ispersisted_false_navigator_storage_api_if_typeof_navigator__52c4a1')undefined' && navigator.storage && navigator.storage.estimate) {
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
        console.warn(i18n.t('auto__browsercache_navigator_storage_estimate__699b30'), err);
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
          stats.stores[storeName] = { count: 0, sizeBytes: 0, sizeKB: '0', sizeMB: '0i18n.t('auto__return_stats_async_requestpersistence_if_typeof_navigator__8155bf')undefinedi18n.t('auto__navigator_storage_navigator_storage_persist_const_ispersisted_await_navigator_storage_persist_console_log_browsercache_ispersisted__1f8649')Одобрено' : i18n.t('auto___b0a5f2')}`);
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
          const transaction = this.db.transaction([storeName], 'readonlyi18n.t('auto__const_store_transaction_objectstore_storename_const_request_store_getall_request_onsuccess_resolve_request_result_request_onerror_e_reject_e_target_error_exportresult_stores_storename_records_catch_err_console_warn_browsercache_storename_err_return_exportresult_param_object_data_async_importdata_data_if_data_data_stores_return_false_await_this_ready_for_const_storename_records_of_object_entries_data_stores_if_object_values_stores_includes_storename_continue_if_array_isarray_records_continue_for_const_record_of_records_if_record_record_key_await_this_set_storename_record_key_record_value_ttl_record_expiresat_math_max_0_record_expiresat_date_now_0_tags_record_tags_console_log__da1984')[BrowserCache] Импорт данных успешно завершен.i18n.t('auto__return_true_l1_in_memory_cache_lru_eviction_private_setmemorycache_key_record_if_this_memorycache_size_this_maxmemoryentries_const_firstkey_this_memorycache_keys_next_value_if_firstkey_this_memorycache_delete_firstkey_this_memorycache_set_key_record_private_estimatesize_value_if_value_null_value_undefined_return_0_if_typeof_value__ba64b3')string') return value.length * 2;
    if (typeof value === 'number') return 8;
    if (typeof value === 'boolean') return 4;
    if (typeof Blob !== 'undefined' && value instanceof Blob) return value.size;
    if (typeof ArrayBuffer !== 'undefinedi18n.t('auto__value_instanceof_arraybuffer_return_value_bytelength_try_return_json_stringify_value_length_2_catch_return_1024_user_data_dir_private_getuserdatadir_pwa_const_ispwa_window_matchmedia__36b4ac')(display-mode: standalone)').matches;
    return isPWA ? i18n.t('auto__pwa__f7dd6a') : i18n.t('auto___522c32');
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
