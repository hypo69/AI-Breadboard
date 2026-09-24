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
    const icon = passed ? '✅' : '❌';
    console.log(`${icon} ${name}: ${message}`);
    results.tests.push({ name, passed, message });
    if (passed) results.passed++;
    else results.failed++;
  }
  
  // Test 1: Проверка доступности browserCache
  try {
    const cacheAvailable = window.browserCache && typeof window.browserCache.ready === 'function';
    logTest('Cache Availability', cacheAvailable, cacheAvailable ? 'BrowserCache is available' : 'BrowserCache NOT available');
  } catch (e) {
    logTest('Cache Availability', false, `Error: ${e.message}`);
  }
  
  // Test 2: Проверка доступности cachedApiFetch
  try {
    const apiFetchAvailable = typeof window.cachedApiFetch === 'function';
    logTest('API Fetch Function', apiFetchAvailable, apiFetchAvailable ? 'cachedApiFetch() is available' : 'cachedApiFetch() NOT available');
  } catch (e) {
    logTest('API Fetch Function', false, `Error: ${e.message}`);
  }
  
  // Test 3: Проверка готовности IndexedDB
  try {
    if (window.browserCache) {
      const isReady = await window.browserCache.ready();
      logTest('IndexedDB Ready', isReady, isReady ? 'IndexedDB is ready' : 'IndexedDB initialization failed');
    } else {
      logTest('IndexedDB Ready', false, 'BrowserCache not available');
    }
  } catch (e) {
    logTest('IndexedDB Ready', false, `Error: ${e.message}`);
  }
  
  // Test 4: Тест Cache-First стратегии
  try {
    console.log('\n--- Testing Cache-First Strategy ---');
    const testUrl = '/api/v1/models';
    
    // Первый запрос (должен быть MISS)
    console.log('Request 1: Should be MISS (network)');
    const start1 = performance.now();
    await window.cachedApiFetch(testUrl);
    const time1 = (performance.now() - start1).toFixed(2);
    
    // Второй запрос (должен быть HIT)
    console.log('Request 2: Should be HIT (cache)');
    const start2 = performance.now();
    await window.cachedApiFetch(testUrl);
    const time2 = (performance.now() - start2).toFixed(2);
    
    const speedup = (time1 / time2).toFixed(1);
    logTest('Cache-First Speed', time2 < time1, `Network: ${time1}ms, Cache: ${time2}ms (${speedup}x faster)`);
  } catch (e) {
    logTest('Cache-First Speed', false, `Error: ${e.message}`);
  }
  
  // Test 5: Тест инвалидации по тегу
  try {
    console.log('\n--- Testing Tag Invalidation ---');
    
    // Добавляем тестовую запись
    if (window.browserCache) {
      await window.browserCache.set('api_cache', 'test-key-1', { data: 'test1' }, { tags: ['test-tag'] });
      await window.browserCache.set('api_cache', 'test-key-2', { data: 'test2' }, { tags: ['test-tag'] });
      
      // Инвалидируем
      const count = await window.invalidateCacheByTag('test-tag');
      logTest('Tag Invalidation', count === 2, `Invalidated ${count} entries (expected 2)`);
    } else {
      logTest('Tag Invalidation', false, 'BrowserCache not available');
    }
  } catch (e) {
    logTest('Tag Invalidation', false, `Error: ${e.message}`);
  }
  
  // Test 6: Получение статистики
  try {
    console.log('\n--- Testing Statistics ---');
    const stats = await window.getApiCacheStats();
    const hasMetrics = stats.available && stats.metrics && typeof stats.metrics.hits === 'number';
    logTest('Cache Statistics', hasMetrics, `Hit rate: ${stats.apiCache?.hitRate || 0}%, Entries: ${stats.apiCache?.count || 0}`);
  } catch (e) {
    logTest('Cache Statistics', false, `Error: ${e.message}`);
  }
  
  // Test 7: Тест forceNetwork
  try {
    console.log('\n--- Testing Force Network ---');
    const testUrl = '/api/v1/system/summary';
    
    // Обычный запрос
    await window.cachedApiFetch(testUrl);
    
    // Принудительный запрос из сети
    const start = performance.now();
    await window.cachedApiFetch(testUrl, {}, { forceNetwork: true });
    const time = (performance.now() - start).toFixed(2);
    
    logTest('Force Network', time > 10, `Force network request took ${time}ms (should be > 10ms)`);
  } catch (e) {
    logTest('Force Network', false, `Error: ${e.message}`);
  }
  
  // Итоги
  console.log('\n=== 📊 Test Results ===');
  console.log(`Total: ${results.tests.length} tests`);
  console.log(`✅ Passed: ${results.passed}`);
  console.log(`❌ Failed: ${results.failed}`);
  console.log(`Success rate: ${((results.passed / results.tests.length) * 100).toFixed(1)}%`);
  
  if (results.failed === 0) {
    console.log('\n🎉 All tests passed! API Cache System is working correctly.');
  } else {
    console.warn('\n⚠️ Some tests failed. Check the logs above for details.');
  }
  
  return results;
}

// Экспорт в глобальную область
if (typeof window !== 'undefined') {
  window.testApiCache = testApiCache;
}

// Автоматический запуск при включенном DEBUG режиме
if (typeof window !== 'undefined' && localStorage.getItem('DEBUG_API_CACHE') === 'true') {
  console.log('🔍 DEBUG_API_CACHE enabled, running tests on load...');
  setTimeout(() => testApiCache(), 2000);
}

export default testApiCache;
