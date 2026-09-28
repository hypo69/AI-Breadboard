/**
 * test-api-cache.js - Простой тестовый скрипт для проверки API Cache System
 * 
 * ИСПОЛЬЗОВАНИЕ:
 * 1. Откройте веб-интерфейс
 * 2. Откройте консоль браузера (F12)
 * 3. Выполните: testApiCache()
 */

export async function testApiCache() {
  console.log('=== 🧪 API Cache System Test Suite ===\n');
  
  const results = {
    passed: 0,
    failed: 0,
    tests: []
  };
  
  function logTest(name, passed, message) {
    const icon = passed ? '✅' : '❌i18n.t('auto__console_log_icon_name_message_results_tests_push_name_passed_message_if_passed_results_passed_else_results_failed_test_1_browsercache_try_const_cacheavailable_window_browsercache_typeof_window_browsercache_ready__9ff03c')function';
    logTest('Cache Availability', cacheAvailable, cacheAvailable ? 'BrowserCache is available' : 'BrowserCache NOT available');
  } catch (e) {
    logTest('Cache Availabilityi18n.t('auto__false_error_e_message_test_2_cachedapifetch_try_const_apifetchavailable_typeof_window_cachedapifetch__00b467')function';
    logTest('API Fetch Function', apiFetchAvailable, apiFetchAvailable ? 'cachedApiFetch() is available' : 'cachedApiFetch() NOT available');
  } catch (e) {
    logTest('API Fetch Functioni18n.t('auto__false_error_e_message_test_3_indexeddb_try_if_window_browsercache_const_isready_await_window_browsercache_ready_logtest__9c876e')IndexedDB Ready', isReady, isReady ? 'IndexedDB is ready' : 'IndexedDB initialization failed');
    } else {
      logTest('IndexedDB Ready', false, 'BrowserCache not available');
    }
  } catch (e) {
    logTest('IndexedDB Readyi18n.t('auto__false_error_e_message_test_4_cache_first_try_console_log__33cd18')\n--- Testing Cache-First Strategy ---');
    const testUrl = '/api/v1/modelsi18n.t('auto__miss_console_log__53af2a')Request 1: Should be MISS (network)i18n.t('auto__const_start1_performance_now_await_window_cachedapifetch_testurl_const_time1_performance_now_start1_tofixed_2_hit_console_log__1f9f5a')Request 2: Should be HIT (cache)');
    const start2 = performance.now();
    await window.cachedApiFetch(testUrl);
    const time2 = (performance.now() - start2).toFixed(2);
    
    const speedup = (time1 / time2).toFixed(1);
    logTest('Cache-First Speed', time2 < time1, `Network: ${time1}ms, Cache: ${time2}ms (${speedup}x faster)`);
  } catch (e) {
    logTest('Cache-First Speedi18n.t('auto__false_error_e_message_test_5_try_console_log__1d204c')\n--- Testing Tag Invalidation ---i18n.t('auto__if_window_browsercache_await_window_browsercache_set__46898c')api_cache', 'test-key-1', { data: 'test1' }, { tags: ['test-tag'] });
      await window.browserCache.set('api_cache', 'test-key-2', { data: 'test2' }, { tags: ['test-tagi18n.t('auto__const_count_await_window_invalidatecachebytag__78158c')test-tag');
      logTest('Tag Invalidation', count === 2, `Invalidated ${count} entries (expected 2)`);
    } else {
      logTest('Tag Invalidation', false, 'BrowserCache not available');
    }
  } catch (e) {
    logTest('Tag Invalidationi18n.t('auto__false_error_e_message_test_6_try_console_log__51faf0')\n--- Testing Statistics ---');
    const stats = await window.getApiCacheStats();
    const hasMetrics = stats.available && stats.metrics && typeof stats.metrics.hits === 'number';
    logTest('Cache Statistics', hasMetrics, `Hit rate: ${stats.apiCache?.hitRate || 0}%, Entries: ${stats.apiCache?.count || 0}`);
  } catch (e) {
    logTest('Cache Statisticsi18n.t('auto__false_error_e_message_test_7_forcenetwork_try_console_log__9d85d1')\n--- Testing Force Network ---');
    const testUrl = '/api/v1/system/summaryi18n.t('auto__await_window_cachedapifetch_testurl_const_start_performance_now_await_window_cachedapifetch_testurl_forcenetwork_true_const_time_performance_now_start_tofixed_2_logtest__e4db7d')Force Network', time > 10, `Force network request took ${time}ms (should be > 10ms)`);
  } catch (e) {
    logTest('Force Networki18n.t('auto__false_error_e_message_console_log__58597b')\n=== 📊 Test Results ===');
  console.log(`Total: ${results.tests.length} tests`);
  console.log(`✅ Passed: ${results.passed}`);
  console.log(`❌ Failed: ${results.failed}`);
  console.log(`Success rate: ${((results.passed / results.tests.length) * 100).toFixed(1)}%`);
  
  if (results.failed === 0) {
    console.log('\n🎉 All tests passed! API Cache System is working correctly.');
  } else {
    console.warn('\n⚠️ Some tests failed. Check the logs above for details.i18n.t('auto__return_results_if_typeof_window__9ac819')undefinedi18n.t('auto__window_testapicache_testapicache_debug_if_typeof_window__5e4f9d')undefined' && localStorage.getItem('DEBUG_API_CACHE') === 'true') {
  console.log('🔍 DEBUG_API_CACHE enabled, running tests on load...');
  setTimeout(() => testApiCache(), 2000);
}

export default testApiCache;
