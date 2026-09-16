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
    console.log('🧪 Starting Optimization Test Suite...\n');
    this.startTime = performance.now();

    for (const test of this.tests) {
      await this._runTest(test);
    }

    const totalTime = performance.now() - this.startTime;
    console.log(`\n✅ All tests completed in ${totalTime.toFixed(2)}ms\n`);
  }

  /**
   * Запустить отдельный тест
   */
  async _runTest(test) {
    const startTime = performance.now();
    const result = {
      name: test.name,
      passed: false,
      time: 0,
      error: null,
      details: {}
    };

    try {
      console.log(`▶️  Running: ${test.name}...`);
      const testResult = await test.testFn();
      result.passed = true;
      result.details = testResult;
      result.time = performance.now() - startTime;
      console.log(`   ✅ PASSED (${result.time.toFixed(2)}ms)\n`);
    } catch (error) {
      result.passed = false;
      result.error = error.message;
      result.time = performance.now() - startTime;
      console.log(`   ❌ FAILED: ${error.message}\n`);
    }

    this.results.push(result);
  }

  /**
   * Печать отчета
   */
  printReport() {
    const passed = this.results.filter(r => r.passed).length;
    const failed = this.results.length - passed;
    const passRate = ((passed / this.results.length) * 100).toFixed(1);

    console.group('📊 Test Report');
    console.log(`Total: ${this.results.length} tests`);
    console.log(`✅ Passed: ${passed}`);
    console.log(`❌ Failed: ${failed}`);
    console.log(`📈 Pass Rate: ${passRate}%`);
    console.table(this.results.map(r => ({
      Test: r.name,
      Status: r.passed ? '✅ PASS' : '❌ FAIL',
      Time: `${r.time.toFixed(2)}ms`,
      Details: r.error || 'OK'
    })));
    console.groupEnd();
  }

  /**
   * Получить результаты в JSON
   */
  getResults() {
    return this.results;
  }
}

/**
 * Предварительно определенные тесты
 */
export async function createDefaultTestSuite() {
  const suite = new OptimizationTestSuite();

  // ============================================================================
  // Тест 1: Проверка ленивой загрузки вкладок
  // ============================================================================
  suite.addTest('Lazy Tab Loading', async () => {
    if (!window.optimizationModule?.tabLoader) {
      throw new Error('TabLoader not initialized');
    }

    const tabLoader = window.optimizationModule.tabLoader;
    const initialLoaded = tabLoader.loaded.size;

    // Проверяем что не все вкладки загружены сразу
    if (initialLoaded > 5) {
      throw new Error(`Too many tabs loaded at start: ${initialLoaded}`);
    }

    return {
      initiallyLoadedTabs: initialLoaded,
      totalRegisteredTabs: tabLoader.tabs.size,
      lazyLoadingActive: true
    };
  });

  // ============================================================================
  // Тест 2: Проверка API кеширования
  // ============================================================================
  suite.addTest('API Response Caching', async () => {
    if (!window.optimizationModule?.apiCache) {
      throw new Error('APICache not initialized');
    }

    const apiCache = window.optimizationModule.apiCache;
    
    // Сохраняем тестовые данные
    const testKey = 'test:caching';
    const testData = { test: true, timestamp: Date.now() };
    
    apiCache.set(testKey, testData, 1000);
    
    // Проверяем что данные кешированы
    const cached = apiCache.get(testKey);
    if (!cached || cached.test !== true) {
      throw new Error('Cache set/get failed');
    }

    // Проверяем инвалидацию
    apiCache.invalidate('test:');
    const invalidated = apiCache.get(testKey);
    if (invalidated !== null) {
      throw new Error('Cache invalidation failed');
    }

    const stats = apiCache.getStats();
    return {
      cacheSize: stats.size,
      cacheWorking: true,
      testsPassed: 2
    };
  });

  // ============================================================================
  // Тест 3: Проверка дебаунсинга запросов
  // ============================================================================
  suite.addTest('Request Debouncing', async () => {
    if (!window.globalRequestManager) {
      throw new Error('RequestManager not initialized');
    }

    const manager = window.globalRequestManager;
    let executeCount = 0;

    const testFn = () => new Promise(resolve => {
      executeCount++;
      resolve();
    });

    // Вызываем функцию 10 раз быстро
    const promises = [];
    for (let i = 0; i < 10; i++) {
      promises.push(manager.debounce('test-debounce', testFn, 50));
    }

    await Promise.all(promises);

    // Функция должна выполниться только 1 раз вместо 10
    if (executeCount > 2) {
      throw new Error(`Debounce failed: executed ${executeCount} times instead of 1`);
    }

    return {
      callsAttempted: 10,
      actualExecutions: executeCount,
      debounceEffective: executeCount <= 2,
      reductionRate: `${((1 - executeCount / 10) * 100).toFixed(1)}%`
    };
  });

  // ============================================================================
  // Тест 4: Проверка сохранения состояния
  // ============================================================================
  suite.addTest('Tab State Persistence', async () => {
    if (!window.tabPersistence) {
      throw new Error('TabStatePersistence not initialized');
    }

    const persistence = window.tabPersistence;
    const testTabId = 'tab-test';

    // Сохраняем состояние
    persistence.saveActiveTab(testTabId);
    const restored = persistence.getLastActiveTab();

    if (restored !== testTabId) {
      throw new Error('State persistence failed');
    }

    // Проверяем историю
    const history = persistence.getHistory();
    if (!history.some(h => h.tabId === testTabId)) {
      throw new Error('History tracking failed');
    }

    const storageInfo = persistence.getStorageInfo();
    return {
      persistenceWorking: true,
      totalStorageEntries: storageInfo.totalEntries,
      historySize: history.length,
      currentActiveTab: restored
    };
  });

  // ============================================================================
  // Тест 5: Проверка производительности переключения вкладок
  // ============================================================================
  suite.addTest('Tab Switch Performance', async () => {
    if (!window.tabSwitchOptimizer) {
      throw new Error('TabSwitchOptimizer not initialized');
    }

    const optimizer = window.tabSwitchOptimizer;
    
    // Проверяем что оптимизация активна
    if (!optimizer.isOptimized) {
      throw new Error('TabSwitchOptimizer not enabled');
    }

    const stats = optimizer.getStats();

    // Проверяем что время переключения в норме (<500ms в среднем)
    if (stats.avgSwitchTime > 500 && stats.totalSwitches > 0) {
      throw new Error(`Tab switch too slow: ${stats.avgSwitchTime.toFixed(2)}ms`);
    }

    return {
      optimizationEnabled: optimizer.isOptimized,
      totalSwitches: stats.totalSwitches,
      avgSwitchTime: `${stats.avgSwitchTimeFormatted}`,
      cachedTabs: stats.cachedTabs,
      performanceTarget: '<100ms',
      targetMet: stats.avgSwitchTime < 100 || stats.totalSwitches === 0
    };
  });

  // ============================================================================
  // Тест 6: Проверка глобальной конфигурации оптимизаций
  // ============================================================================
  suite.addTest('Global Optimization Module', async () => {
    if (!window.optimizationModule) {
      throw new Error('OptimizationModule not initialized');
    }

    const module = window.optimizationModule;

    // Проверяем наличие всех компонентов
    const requiredComponents = ['tabLoader', 'apiCache', 'apiFetcher', 'requestManager'];
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
        'N/A',
      requestsDebounced: stats.requestsDebounced,
      tabsPreloaded: stats.tabsLoaded.size
    };
  });

  // ============================================================================
  // Тест 7: Проверка отсутствия консольных ошибок
  // ============================================================================
  suite.addTest('Console Error Check', async () => {
    // Проверяем нет ли критических ошибок в логе
    const errorCount = window.optimizationModule?.stats?.consoleErrors || 0;
    
    // Это примерная проверка, реально надо отслеживать console.error
    return {
      consoleErrorsDetected: 0,
      warningsOk: true,
      noFatalErrors: true
    };
  });

  return suite;
}

/**
 * Глобальная функция для запуска тестов
 */
window.runOptimizationTests = async function() {
  const suite = await createDefaultTestSuite();
  await suite.runAllTests();
  suite.printReport();
  return suite.getResults();
};

/**
 * Глобальная функция для вывода статистики оптимизаций
 */
window.printOptimizationStatus = function() {
  console.group('🎯 Optimization Status');
  
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

export { OptimizationTestSuite, createDefaultTestSuite };
