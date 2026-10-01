/**
 * =============================================================================
 * Process Name: AI-Breadboard UI - Api-Cache Script
 * =============================================================================
 * Description:
 *   Клиентский веб-скрипт модуля api-cache.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/src/api/webgui/js/api-cache.js?v=20261001_v1" type="module"></script>
 *
 * File: api-cache.js
 * Project: ai-breadboard
 * Package: src/api/webgui/js
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-01 13:13:56
 * =============================================================================
 */

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

import { browserCache, STORES } from './browser-cache.jsi18n.t('auto__export_const_cache_strategies_ttl_static_ttl_60_60_1000_strategy__41141d')cache-firsti18n.t('auto__1_hardware_spec_user_profiles_ttl_semi_static_ttl_30_60_1000_strategy__b28d4e')cache-firsti18n.t('auto__30_ttl_dynamic_ttl_5_1000_strategy__9a66b8')stale-while-revalidatei18n.t('auto__5_live_telemetry_ttl_realtime_ttl_3_1000_strategy__ea64d2')network-firsti18n.t('auto__3_security_status_errors_critical_ttl_0_strategy__cc85cd')network-firsti18n.t('auto__url_const_url_patterns_pattern_api_v1_models_strategy_cache_strategies_static_tag__19f1d5')models' },
  { pattern: /\/api\/config/, strategy: CACHE_STRATEGIES.STATIC, tag: 'config' },
  { pattern: /\/api\/plugins/, strategy: CACHE_STRATEGIES.SEMI_STATIC, tag: 'pluginsi18n.t('auto__hardware_pattern_api_v1_system_hardware_strategy_cache_strategies_semi_static_tag__a9d5a4')hardware' },
  { pattern: /\/api\/v1\/windows-backup/, strategy: CACHE_STRATEGIES.SEMI_STATIC, tag: 'backupi18n.t('auto__pattern_api_v1_system_summary_strategy_cache_strategies_dynamic_tag__b8216b')system-summary' },
  { pattern: /\/api\/system-control\/status/, strategy: CACHE_STRATEGIES.DYNAMIC, tag: 'control-statusi18n.t('auto__pattern_api_v1_system_sensors_strategy_cache_strategies_realtime_tag__4decd1')sensors' },
  { pattern: /\/api\/v1\/system\/processes/, strategy: CACHE_STRATEGIES.REALTIME, tag: 'processesi18n.t('auto__rag_pattern_api_chat_strategy_cache_strategies_dynamic_tag__54ecdb')chat' },
  { pattern: /\/api\/rag/, strategy: CACHE_STRATEGIES.DYNAMIC, tag: 'ragi18n.t('auto__url_param_string_url_url_returns_object_ttl_strategy_tag_function_getcachestrategy_url_for_const_rule_of_url_patterns_if_rule_pattern_test_url_return_rule_strategy_tag_rule_tag_stale_while_revalidate_ttl_1_return_ttl_60_1000_strategy__c07dd6')stale-while-revalidate', tag: 'defaulti18n.t('auto__url_param_string_url_url_param_object_options_method_body_returns_string_function_generatecachekey_url_options_const_method_options_method__d90647')GET';
  const body = options.body ? `-${btoa(options.body).substring(0, 32)}` : 'i18n.t('auto__return_method_url_body_http_param_string_url_url_param_object_options_param_object_cacheoptions_returns_promise_any_example_const_data_await_cachedapifetch__f9ef30')/api/v1/system/hardwarei18n.t('auto__example_const_data_await_cachedapifetch__819470')/api/custom', {}, {
 *   ttl: 10000,
 *   strategy: 'cache-first',
 *   tag: 'custom-datai18n.t('auto__response_res_ok_res_status_res_json_param_any_data_returns_any_function_wrapcacheddata_data_if_data_typeof_data__86bbf9')object') {
    try {
      if (!('ok' in data)) {
        Object.defineProperty(data, 'ok', { value: true, writable: true, configurable: true, enumerable: false });
      }
      if (!('status' in data)) {
        Object.defineProperty(data, 'status', { value: 200, writable: true, configurable: true, enumerable: false });
      }
      if (typeof data.json !== 'function') {
        Object.defineProperty(data, 'jsoni18n.t('auto__value_async_data_writable_true_configurable_true_enumerable_false_catch_return_data_http_param_string_url_url_param_object_options_param_object_cacheoptions_returns_promise_any_res_ok_await_res_json_export_async_function_cachedapifetch_url_options_cacheoptions_const_autostrategy_getcachestrategy_url_const_ttl_autostrategy_ttl_strategy_autostrategy_strategy_tag_autostrategy_tag_forcenetwork_false_cacheoptions_const_cachekey_generatecachekey_url_options_const_cache_browsercache_if_cache_try_await_cache_ready_catch_cache_first_if_cache_strategy__e5dc54')cache-firsti18n.t('auto__forcenetwork_try_const_cached_await_cache_get_stores_api_cache_cachekey_if_cached_null_cached_undefined_return_wrapcacheddata_cached_catch_stale_while_revalidate_if_cache_strategy__93ff1a')stale-while-revalidatei18n.t('auto__forcenetwork_try_const_cached_await_cache_get_stores_api_cache_cachekey_if_cached_null_cached_undefined_directfetch_url_options_then_fresh_cache_set_stores_api_cache_cachekey_fresh_ttl_tags_tag__c7a630')api-cachei18n.t('auto__catch_err_console_debug_api_cache_background_update_skipped_for_url_err_return_wrapcacheddata_cached_catch_network_first_fallback_try_const_fresh_await_directfetch_url_options_ttl_0_if_cache_ttl_0_cache_set_stores_api_cache_cachekey_fresh_ttl_tags_tag__3c958d')api-cachei18n.t('auto__catch_return_wrapcacheddata_fresh_catch_err_if_cache_try_const_stalecache_await_cache_get_stores_api_cache_cachekey_if_stalecache_null_stalecache_undefined_console_warn_api_cache_network_failed_returning_stale_cache_url_return_wrapcacheddata_stalecache_catch_throw_err_http_param_string_url_url_param_object_options_fetch_returns_promise_any_async_function_directfetch_url_options_const_opts_options_if_opts_body_typeof_opts_body__21a816')string') {
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
        errMsg += ` (${typeof errJson.detail === 'objecti18n.t('auto__json_stringify_errjson_detail_errjson_detail_catch_throw_new_error_errmsg_const_json_await_res_json_return_wrapcacheddata_json_param_string_tag_returns_promise_number_example_await_invalidatecachebytag__b6278a')modelsi18n.t('auto__export_async_function_invalidatecachebytag_tag_if_browsercache_browsercache_isdbready_return_0_const_count_await_browsercache_invalidatebytag_stores_api_cache_tag_console_log_api_cache_invalidated_count_entries_with_tag_tag_return_count_api_returns_promise_boolean_export_async_function_clearallapicache_if_browsercache_browsercache_isdbready_return_false_await_browsercache_clearstore_stores_api_cache_console_log__483259')[API Cache] 🗑️ All API cache clearedi18n.t('auto__return_true_returns_promise_object_export_async_function_getapicachestats_if_browsercache_browsercache_isdbready_return_available_false_metrics_null_const_stats_await_browsercache_getdetailedstats_const_apistore_stats_stores_stores_api_cache_return_available_true_metrics_stats_metrics_apicache_count_apistore_count_0_sizemb_apistore_sizemb__a8df25')0.00i18n.t('auto__hitrate_stats_metrics_hits_stats_metrics_misses_0_math_round_stats_metrics_hits_stats_metrics_hits_stats_metrics_misses_100_0_storage_stats_storageestimate_if_typeof_window__342813')undefined') {
  window.cachedApiFetch = cachedApiFetch;
  window.invalidateCacheByTag = invalidateCacheByTag;
  window.clearAllApiCache = clearAllApiCache;
  window.getApiCacheStats = getApiCacheStats;
  window.CACHE_STRATEGIES = CACHE_STRATEGIES;
}

export default cachedApiFetch;
