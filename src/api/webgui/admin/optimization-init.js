/**
 * Optimization Init - Интеграция систем оптимизации в админку
 * 
 * Этот скрипт инициализирует:
 * - Ленивую загрузку вкладок
 * - Кеширование API
 * - Дебаунсинг запросов
 * - Сохранение состояния вкладок
 */

import LazyTabLoader from '../js/tab-loader.js';
import { APICache, APIFetcher } from '../js/api-cache.js';
import { RequestManager } from '../js/request-manager.jsi18n.t('auto__1_const_tabloader_new_lazytabloader_const_apicache_new_apicache_const_apifetcher_new_apifetcher_apicache_const_requestmanager_new_requestmanager_window_optimizationmodule_tabloader_apicache_apifetcher_requestmanager_stats_tabsloaded_new_set_apicallsused_0_cachedcallsused_0_requestsdebounced_0_console_log__c2d6bc')[Optimization] System initializedi18n.t('auto__2_api_fetch_fetch_const_originalapifetch_window_api_fetch_window_api_fetch_if_window_api_originalapifetch_window_api_fetch_async_function_url_options_const_method_options_method__595967')GET').toUpperCase();
    const isGetRequest = method === 'GET' || method === 'HEADi18n.t('auto__get_if_isgetrequest_const_cached_apicache_get_url_if_cached_window_optimizationmodule_stats_cachedcallsused_console_log_optimization_api_call_from_cache_method_url_return_cached_window_optimizationmodule_stats_apicallsused_const_result_await_originalapifetch_call_this_url_options_get_5_ttl_if_isgetrequest_apicache_set_url_result_5_60_1000_5_else_post_put_delete_const_basepath_url_split__c096ee')?i18n.t('auto__0_get_if_method__f34068')POST' || method === 'PUT' || method === 'DELETEi18n.t('auto__const_pattern_new_regexp_basepath_replace__5713fa')i18n.t('auto__const_invalidatedcount_apicache_invalidate_pattern_if_invalidatedcount_0_console_log_optimization_invalidated_invalidatedcount_cache_entries_for_basepath_if_basepath_includes__e459c9')/users/i18n.t('auto__apicache_invalidate_api_admin_users_apicache_invalidate_api_users_if_basepath_includes__e4a062')/config/i18n.t('auto__apicache_invalidate_api_config_apicache_invalidate_api_admin_config_if_basepath_includes__a97bd9')/pluginsi18n.t('auto__apicache_invalidate_api_plugins_apicache_invalidate_api_admin_plugins_if_basepath_includes__b03042')/models') || basePath.includes('/chati18n.t('auto__apicache_invalidate_api_chat_models_apicache_invalidate_api_models_return_result_3_lazy_loading_export_async_function_initlazytabloading_tabdefinitions_console_log__2ded0a')[Optimization] Initializing lazy tab loading (on-demand mode)...i18n.t('auto__tabdefinitions_foreach_tabname_htmlurl_jsurl_tabloader_registertab_tabname_htmlurl_jsurl_loadtab_const_originalloadtab_tabloader_loadtab_bind_tabloader_tabloader_loadtab_async_function_tabname_const_result_await_originalloadtab_tabname_if_result_window_tabdebounceautopatch_settimeout_try_window_tabdebounceautopatch_autopatchtab_tabname_searchenabled_true_autosaveenabled_true_refreshenabled_true_catch_e_console_warn_optimization_failed_to_apply_debounce_patch_to_tabname_e_100_return_result_const_allowedtabnames_tabdefinitions_map_def_def_tabname_console_log_optimization_registered_allowedtabnames_length_tabs_for_on_demand_loading_return_registeredtabs_allowedtabnames_4_export_function_enhancetabswitching_originalswitchtab_return_async_function_switchtaboptimized_targetid_if_targetid_return_const_cleanid_targetid_startswith__bd0a86')#') ? targetId.slice(1) : targetId;
    const tabName = cleanId.replace(/^tab-/, 'i18n.t('auto__console_log_optimization_switching_to_tab_tabname_if_tabloader_isloaded_tabname_console_log_optimization_tab_not_loaded_yet_loading_on_demand_tabname_await_tabloader_loadtab_tabname_window_optimizationmodule_stats_tabsloaded_add_tabname_if_typeof_originalswitchtab__b43888')functioni18n.t('auto__originalswitchtab_call_this_targetid_localstorage_localstorage_setitem__053f33')admin:lastActiveTabi18n.t('auto__cleanid_5_export_async_function_restorelasttab_fallbacktab__4af02b')tab-about-systemi18n.t('auto__url_const_hash_location_hash_replace__4b9022')#', 'i18n.t('auto__let_initialtab_hash_null_persistence_if_initialtab_if_window_tabpersistence_typeof_window_tabpersistence_getlastactivetab__4d6baf')function') {
      initialTab = window.tabPersistence.getLastActiveTab();
    } else {
      initialTab = localStorage.getItem('admin:lastActiveTab');
    }
  }

  const targetTabId = (initialTab && document.getElementById(initialTab.startsWith('tab-') ? initialTab : `tab-${initialTab}`))
    ? (initialTab.startsWith('tab-') ? initialTab : `tab-${initialTab}`)
    : fallbackTab;

  const tabName = targetTabId.replace(/^tab-/, '');
  console.log(`[Optimization] Loading strictly initial active tab: ${tabName}`);

  if (!tabLoader.isLoaded(tabName)) {
    await tabLoader.loadTab(tabName);
    window.optimizationModule.stats.tabsLoaded.add(tabName);
  }

  if (typeof window.switchTab === 'functioni18n.t('auto__window_switchtab_targettabid_return_targettabid_6_export_function_createsearchdebounce_searchfn_delay_500_return_query_window_optimizationmodule_stats_requestsdebounced_return_requestmanager_debounce__088e52')search-query', () => searchFn(query), delay);
  };
}

export function createAutoSaveDebounce(saveFn, delay = 1000) {
  return (data) => {
    window.optimizationModule.stats.requestsDebounced++;
    return requestManager.debounce('autosave-datai18n.t('auto__savefn_data_delay_7_export_function_getoptimizationstats_return_window_optimizationmodule_stats_cachestats_apicache_getstats_requestmanagerstats_requestmanager_getstats_tabspreloaded_array_from_window_optimizationmodule_stats_tabsloaded_export_function_printoptimizationstats_const_stats_getoptimizationstats_console_group__5146ef')📊 Optimization Statistics');
  console.log('API Calls:', stats.apiCallsUsed);
  console.log('Cached Calls:', stats.cachedCallsUsed);
  console.log('Cache Hit Rate:', (stats.cachedCallsUsed / (stats.apiCallsUsed + stats.cachedCallsUsed) * 100).toFixed(1) + '%');
  console.log('Requests Debounced:', stats.requestsDebounced);
  console.log('Tabs Preloaded:', stats.tabsPreloaded);
  console.log('Cache Entries:', stats.cacheStats.size);
  console.groupEnd();
}

// Делаем доступной из консоли для отладки
window.printOptimizationStats = printOptimizationStats;
window.getOptimizationStats = getOptimizationStats;

// Выводим статистику каждые 30 секунд (опционально, для отладки)
// Раскомментировать в production если нужна мониторинг
// setInterval(() => {
//   console.clear();
//   printOptimizationStats();
// }, 30000);

export default {
  initLazyTabLoading,
  enhanceTabSwitching,
  restoreLastTab,
  createSearchDebounce,
  createAutoSaveDebounce,
  getOptimizationStats,
  printOptimizationStats,
  tabLoader,
  apiCache,
  apiFetcher,
  requestManager
};
