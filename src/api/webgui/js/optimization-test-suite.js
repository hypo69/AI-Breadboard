/**
 * Optimization Test Suite - Комплексное тестирование оптимизаций
 * 
 * Тестирует:
 * - Ленивую загрузку вкладок
 * - Кеширование API
 * - Дебаунсинг запросов
 * - Сохранение состояния
 * - Производительность переключения
 * 
 * Usage:
 *   const tester = new OptimizationTestSuite();
 *   await tester.runAllTests();
 *   tester.printReport();
 */

class OptimizationTestSuite {
  constructor() {
    this.tests = [];
    this.results = [];
    this.startTime = null;
  }

  /**
   * Добавить тест
   */
  addTest(name, testFn) {
    this.tests.push({ name, testFn });
  }

  /**
   * Запустить все тесты
   */
  async runAllTests() {
    console.log('🧪 Starting Optimization Test Suite...\ni18n.t('auto__this_starttime_performance_now_for_const_test_of_this_tests_await_this_runtest_test_const_totaltime_performance_now_this_starttime_console_log_n_all_tests_completed_in_totaltime_tofixed_2_ms_n_async_runtest_test_const_starttime_performance_now_const_result_name_test_name_passed_false_time_0_error_null_details_try_console_log_running_test_name_const_testresult_await_test_testfn_result_passed_true_result_details_testresult_result_time_performance_now_starttime_console_log_passed_result_time_tofixed_2_ms_n_catch_error_result_passed_false_result_error_error_message_result_time_performance_now_starttime_console_log_failed_error_message_n_this_results_push_result_printreport_const_passed_this_results_filter_r_r_passed_length_const_failed_this_results_length_passed_const_passrate_passed_this_results_length_100_tofixed_1_console_group__da9358')📊 Test Report');
    console.log(`Total: ${this.results.length} tests`);
    console.log(`✅ Passed: ${passed}`);
    console.log(`❌ Failed: ${failed}`);
    console.log(`📈 Pass Rate: ${passRate}%`);
    console.table(this.results.map(r => ({
      Test: r.name,
      Status: r.passed ? '✅ PASS' : '❌ FAIL',
      Time: `${r.time.toFixed(2)}ms`,
      Details: r.error || 'OKi18n.t('auto__console_groupend_json_getresults_return_this_results_export_async_function_createdefaulttestsuite_const_suite_new_optimizationtestsuite_1_suite_addtest__0636ee')Lazy Tab Loading', async () => {
    if (!window.optimizationModule?.tabLoader) {
      throw new Error('TabLoader not initializedi18n.t('auto__const_tabloader_window_optimizationmodule_tabloader_const_initialloaded_tabloader_loaded_size_if_initialloaded_5_throw_new_error_too_many_tabs_loaded_at_start_initialloaded_return_initiallyloadedtabs_initialloaded_totalregisteredtabs_tabloader_tabs_size_lazyloadingactive_true_2_api_suite_addtest__601e12')API Response Caching', async () => {
    if (!window.optimizationModule?.apiCache) {
      throw new Error('APICache not initializedi18n.t('auto__const_apicache_window_optimizationmodule_apicache_const_testkey__cf6fcd')test:cachingi18n.t('auto__const_testdata_test_true_timestamp_date_now_apicache_set_testkey_testdata_1000_const_cached_apicache_get_testkey_if_cached_cached_test_true_throw_new_error__eeb314')Cache set/get failedi18n.t('auto__apicache_invalidate__d22f33')test:');
    const invalidated = apiCache.get(testKey);
    if (invalidated !== null) {
      throw new Error('Cache invalidation failedi18n.t('auto__const_stats_apicache_getstats_return_cachesize_stats_size_cacheworking_true_testspassed_2_3_suite_addtest__ebbb49')Request Debouncing', async () => {
    if (!window.globalRequestManager) {
      throw new Error('RequestManager not initializedi18n.t('auto__const_manager_window_globalrequestmanager_let_executecount_0_const_testfn_new_promise_resolve_executecount_resolve_10_const_promises_for_let_i_0_i_10_i_promises_push_manager_debounce__da5149')test-debouncei18n.t('auto__testfn_50_await_promise_all_promises_1_10_if_executecount_2_throw_new_error_debounce_failed_executed_executecount_times_instead_of_1_return_callsattempted_10_actualexecutions_executecount_debounceeffective_executecount_2_reductionrate_1_executecount_10_100_tofixed_1_4_suite_addtest__33233d')Tab State Persistence', async () => {
    if (!window.tabPersistence) {
      throw new Error('TabStatePersistence not initialized');
    }

    const persistence = window.tabPersistence;
    const testTabId = 'tab-testi18n.t('auto__persistence_saveactivetab_testtabid_const_restored_persistence_getlastactivetab_if_restored_testtabid_throw_new_error__580956')State persistence failedi18n.t('auto__const_history_persistence_gethistory_if_history_some_h_h_tabid_testtabid_throw_new_error__126162')History tracking failedi18n.t('auto__const_storageinfo_persistence_getstorageinfo_return_persistenceworking_true_totalstorageentries_storageinfo_totalentries_historysize_history_length_currentactivetab_restored_5_suite_addtest__77ed11')Tab Switch Performance', async () => {
    if (!window.tabSwitchOptimizer) {
      throw new Error('TabSwitchOptimizer not initializedi18n.t('auto__const_optimizer_window_tabswitchoptimizer_if_optimizer_isoptimized_throw_new_error__b8a8bf')TabSwitchOptimizer not enabledi18n.t('auto__const_stats_optimizer_getstats_500ms_if_stats_avgswitchtime_500_stats_totalswitches_0_throw_new_error_tab_switch_too_slow_stats_avgswitchtime_tofixed_2_ms_return_optimizationenabled_optimizer_isoptimized_totalswitches_stats_totalswitches_avgswitchtime_stats_avgswitchtimeformatted_cachedtabs_stats_cachedtabs_performancetarget__df5578')<100msi18n.t('auto__targetmet_stats_avgswitchtime_100_stats_totalswitches_0_6_suite_addtest__378310')Global Optimization Module', async () => {
    if (!window.optimizationModule) {
      throw new Error('OptimizationModule not initializedi18n.t('auto__const_module_window_optimizationmodule_const_requiredcomponents__9f848b')tabLoader', 'apiCache', 'apiFetcher', 'requestManager'];
    const missingComponents = requiredComponents.filter(comp => !module[comp]);

    if (missingComponents.length > 0) {
      throw new Error(`Missing components: ${missingComponents.join(', ')}`);
    }

    const stats = module.stats;
    return {
      componentsInitialized: requiredComponents.length,
      apiCallsUsed: stats.apiCallsUsed,
      cachedCallsUsed: stats.cachedCallsUsed,
      cacheHitRate: stats.apiCallsUsed > 0 ? 
        `${((stats.cachedCallsUsed / (stats.apiCallsUsed + stats.cachedCallsUsed)) * 100).toFixed(1)}%` : 
        'N/Ai18n.t('auto__requestsdebounced_stats_requestsdebounced_tabspreloaded_stats_tabsloaded_size_7_suite_addtest__6708ad')Console Error Checki18n.t('auto__async_const_errorcount_window_optimizationmodule_stats_consoleerrors_0_console_error_return_consoleerrorsdetected_0_warningsok_true_nofatalerrors_true_return_suite_window_runoptimizationtests_async_function_const_suite_await_createdefaulttestsuite_await_suite_runalltests_suite_printreport_return_suite_getresults_window_printoptimizationstatus_function_console_group__276524')🎯 Optimization Status');
  
  if (window.optimizationModule) {
    console.log('✅ Optimization Module:', 'Active');
    console.log('   - LazyTabLoader:', window.optimizationModule.tabLoader ? 'Enabled' : 'Disabled');
    console.log('   - APICache:', window.optimizationModule.apiCache ? 'Enabled' : 'Disabled');
    console.log('   - RequestManager:', window.optimizationModule.requestManager ? 'Enabled' : 'Disabled');
  } else {
    console.log('❌ Optimization Module:', 'Not initialized');
  }

  if (window.tabPersistence) {
    console.log('✅ Tab Persistence:', 'Active');
  } else {
    console.log('❌ Tab Persistence:', 'Not initialized');
  }

  if (window.tabSwitchOptimizer) {
    console.log('✅ Tab Switch Optimizer:', window.tabSwitchOptimizer.isOptimized ? 'Active' : 'Inactive');
  } else {
    console.log('❌ Tab Switch Optimizer:', 'Not initialized');
  }

  console.groupEnd();
};

export { OptimizationTestSuite };

