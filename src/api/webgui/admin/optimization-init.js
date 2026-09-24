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
import { RequestManager } from '../js/request-manager.js';

// ============================================================================
// 1. ИНИЦИАЛИЗАЦИЯ СИСТЕМ ОПТИМИЗАЦИИ
// ============================================================================

const tabLoader = new LazyTabLoader();
const apiCache = new APICache();
const apiFetcher = new APIFetcher(apiCache);
const requestManager = new RequestManager();

// Экспортируем в глобальный скоп для доступа из других модулей
window.optimizationModule = {
  tabLoader,
  apiCache,
  apiFetcher,
  requestManager,
  stats: {
    tabsLoaded: new Set(),
    apiCallsUsed: 0,
    cachedCallsUsed: 0,
    requestsDebounced: 0
  }
};

console.log('[Optimization] System initialized');

// ============================================================================
// 2. ПЕРЕХВАТ API.FETCH ОБЕРТКА
// ============================================================================

// Сохраняем оригинальный fetch
const originalApiFetch = window.api?.fetch;

// Переопределяем window.api.fetch для использования кеша
if (window.api && originalApiFetch) {
  window.api.fetch = async function(url, options = {}) {
    const method = (options.method || 'GET').toUpperCase();
    const isGetRequest = method === 'GET' || method === 'HEAD';

    // Для GET запросов проверяем кеш
    if (isGetRequest) {
      const cached = apiCache.get(url);
      if (cached) {
        window.optimizationModule.stats.cachedCallsUsed++;
        console.log(`[Optimization] API call from cache: ${method} ${url}`);
        return cached;
      }
    }

    // Делаем реальный запрос
    window.optimizationModule.stats.apiCallsUsed++;
    const result = await originalApiFetch.call(this, url, options);

    // Кешируем для GET запросов (5 минут TTL)
    if (isGetRequest) {
      apiCache.set(url, result, 5 * 60 * 1000); // 5 минут
    } else {
      // Для POST/PUT/DELETE инвалидируем релевантный кеш
      const basePath = url.split('?')[0];
      
      // Умная инвалидация - очищаем кеш связанных GET запросов
      if (method === 'POST' || method === 'PUT' || method === 'DELETE') {
        // Инвалидируем основной путь и все его вариации
        const pattern = new RegExp(`${basePath.replace(/\/$/, '')}.*`);
        const invalidatedCount = apiCache.invalidate(pattern);
        if (invalidatedCount > 0) {
          console.log(`[Optimization] Invalidated ${invalidatedCount} cache entries for ${basePath}`);
        }

        // Для пользователей - инвалидируем список пользователей
        if (basePath.includes('/users/')) {
          apiCache.invalidate(/\/api\/admin\/users/);
          apiCache.invalidate(/\/api\/users/);
        }

        // Для конфигурации - инвалидируем конфиги
        if (basePath.includes('/config/')) {
          apiCache.invalidate(/\/api\/config/);
          apiCache.invalidate(/\/api\/admin\/config/);
        }

        // Для плагинов - инвалидируем список плагинов
        if (basePath.includes('/plugins')) {
          apiCache.invalidate(/\/api\/plugins/);
          apiCache.invalidate(/\/api\/admin\/plugins/);
        }

        // Для модели - инвалидируем список моделей
        if (basePath.includes('/models') || basePath.includes('/chat')) {
          apiCache.invalidate(/\/api\/chat\/models/);
          apiCache.invalidate(/\/api\/models/);
        }
      }
    }

    return result;
  };
}

// ============================================================================
// 3. ПЕРЕДЕЛКА ИНИЦИАЛИЗАЦИИ ВКЛАДОК (LAZY LOADING)
// ============================================================================

export async function initLazyTabLoading(tabDefinitions) {
  console.log('[Optimization] Initializing lazy tab loading...');

  // Регистрируем все вкладки в системе ленивой загрузки
  tabDefinitions.forEach(({ tabName, htmlUrl, jsUrl }) => {
    tabLoader.registerTab(tabName, htmlUrl, jsUrl);
  });

  // Перехватываем loadTab чтобы применять автопатч
  const originalLoadTab = tabLoader.loadTab.bind(tabLoader);
  tabLoader.loadTab = async function(tabName) {
    const result = await originalLoadTab(tabName);
    
    // Применяем дебаунс автопатч к загруженной вкладке
    if (result && window.TabDebounceAutoPatch) {
      setTimeout(() => {
        try {
          window.TabDebounceAutoPatch.autoPatchTab(tabName, {
            searchEnabled: true,
            autoSaveEnabled: true,
            refreshEnabled: true
          });
        } catch (e) {
          console.warn(`[Optimization] Failed to apply debounce patch to ${tabName}:`, e);
        }
      }, 100);
    }
    
    return result;
  };

  // Определяем стартовые вкладки (только те, которые разрешены в профиле)
  const allPriorityTabs = ['about-system', 'chat', 'admin', 'users'];
  const allowedTabNames = new Set(tabDefinitions.map(def => def.tabName));
  const priorityTabs = allPriorityTabs.filter(name => allowedTabNames.has(name));

  // Вкладки, исключенные из автоматической фоновой предзагрузки (загружаются только по клику)
  const excludedFromPreload = ['trading'];
  const restTabs = tabDefinitions
    .map(def => def.tabName)
    .filter(name => !priorityTabs.includes(name) && !excludedFromPreload.includes(name));

  // Фаза 1: Загружаем приоритетные вкладки
  console.log(`[Optimization] Phase 1: Loading priority tabs: ${priorityTabs.join(', ')}`);
  await tabLoader.loadMultiple(priorityTabs);
  priorityTabs.forEach(tab => window.optimizationModule.stats.tabsLoaded.add(tab));

  // Фаза 2: Предзагружаем остальные вкладки в фоне (асинхронно)
  console.log(`[Optimization] Phase 2: Preloading remaining ${restTabs.length} tabs in background...`);
  setTimeout(() => {
    tabLoader.preloadMultiple(restTabs);
    restTabs.forEach(tab => {
      tabLoader.loadTab(tab).then(() => {
        window.optimizationModule.stats.tabsLoaded.add(tab);
      });
    });
  }, 2000);

  return { priorityTabs, restTabs };
}

// ============================================================================
// 4. ИНТЕГРАЦИЯ С ПЕРЕКЛЮЧАТЕЛЕМ ВКЛАДОК
// ============================================================================

export function enhanceTabSwitching(originalSwitchTab) {
  return async function switchTabOptimized(targetId) {
    if (!targetId) return;

    const cleanId = targetId.startsWith('#') ? targetId.slice(1) : targetId;
    const tabName = cleanId.replace(/^tab-/, '');

    console.log(`[Optimization] Switching to tab: ${tabName}`);

    // Если вкладка еще не загружена - загружаем ее
    if (!tabLoader.isLoaded(tabName)) {
      console.log(`[Optimization] Tab not loaded yet, loading: ${tabName}`);
      await tabLoader.loadTab(tabName);
      window.optimizationModule.stats.tabsLoaded.add(tabName);
    }

    // Вызываем оригинальную функцию переключения
    if (typeof originalSwitchTab === 'function') {
      originalSwitchTab.call(this, targetId);
    }

    // Сохраняем состояние вкладки в localStorage
    localStorage.setItem('admin:lastActiveTab', cleanId);
  };
}

// ============================================================================
// 5. ВОССТАНОВЛЕНИЕ ПОСЛЕДНЕЙ ВКЛАДКИ
// ============================================================================

export async function restoreLastTab(fallbackTab = 'tab-chat') {
  // Используем TabStatePersistence если она доступна
  let lastTab = null;
  
  if (window.tabPersistence && typeof window.tabPersistence.getLastActiveTab === 'function') {
    lastTab = window.tabPersistence.getLastActiveTab();
  } else {
    // Fallback на старый метод для совместимости
    lastTab = localStorage.getItem('admin:lastActiveTab');
  }
  
  if (lastTab && document.getElementById(lastTab)) {
    console.log(`[Optimization] Restoring last tab: ${lastTab}`);
    const tabName = lastTab.replace(/^tab-/, '');
    
    if (!tabLoader.isLoaded(tabName)) {
      await tabLoader.loadTab(tabName);
      window.optimizationModule.stats.tabsLoaded.add(tabName);
    }
    
    if (typeof window.switchTab === 'function') {
      window.switchTab(lastTab);
    }
    return true;
  }

  // Fallback на стартовую вкладку
  if (typeof window.switchTab === 'function') {
    window.switchTab(fallbackTab);
  }
  return false;
}

// ============================================================================
// 6. УТИЛИТЫ ДЛЯ ДЕБАУНСИНГА И БАТЧИНГА
// ============================================================================

export function createSearchDebounce(searchFn, delay = 500) {
  return (query) => {
    window.optimizationModule.stats.requestsDebounced++;
    return requestManager.debounce('search-query', () => searchFn(query), delay);
  };
}

export function createAutoSaveDebounce(saveFn, delay = 1000) {
  return (data) => {
    window.optimizationModule.stats.requestsDebounced++;
    return requestManager.debounce('autosave-data', () => saveFn(data), delay);
  };
}

// ============================================================================
// 7. ФУНКЦИИ ОТЛАДКИ И СТАТИСТИКИ
// ============================================================================

export function getOptimizationStats() {
  return {
    ...window.optimizationModule.stats,
    cacheStats: apiCache.getStats(),
    requestManagerStats: requestManager.getStats(),
    tabsPreloaded: Array.from(window.optimizationModule.stats.tabsLoaded)
  };
}

export function printOptimizationStats() {
  const stats = getOptimizationStats();
  console.group('📊 Optimization Statistics');
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
