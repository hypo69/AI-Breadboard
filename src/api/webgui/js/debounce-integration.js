/**
 * Debounce Integration - Интеграция дебаунсинга в популярные операции
 * 
 * Этот модуль предоставляет готовые функции дебаунса/батчинга для:
 * - Поиска пользователей
 * - Поиска плагинов
 * - Автосохранения инструкций
 * - Обновления статуса
 */

import { RequestManager } from './request-manager.js';

// Создаем глобальный экземпляр request manager
const globalRequestManager = new RequestManager();

window.globalRequestManager = globalRequestManager;

/**
 * Дебаунс поиска пользователей (500ms)
 */
export function createUserSearchDebounce(searchFn) {
  return (query) => {
    if (window.optimizationModule?.stats) {
      window.optimizationModule.stats.requestsDebounced++;
    }
    return globalRequestManager.debounce(
      'user-search',
      () => searchFn(query),
      500
    );
  };
}

/**
 * Дебаунс поиска плагинов (500ms)
 */
export function createPluginSearchDebounce(searchFn) {
  return (query) => {
    if (window.optimizationModule?.stats) {
      window.optimizationModule.stats.requestsDebounced++;
    }
    return globalRequestManager.debounce(
      'plugin-search',
      () => searchFn(query),
      500
    );
  };
}

/**
 * Дебаунс автосохранения инструкций (1000ms)
 */
export function createInstructionAutoSaveDebounce(saveFn) {
  return (content) => {
    if (window.optimizationModule?.stats) {
      window.optimizationModule.stats.requestsDebounced++;
    }
    return globalRequestManager.debounce(
      'instruction-autosave',
      () => saveFn(content),
      1000
    );
  };
}

/**
 * Дебаунс обновления статуса (2000ms)
 */
export function createStatusUpdateDebounce(updateFn) {
  return (status) => {
    if (window.optimizationModule?.stats) {
      window.optimizationModule.stats.requestsDebounced++;
    }
    return globalRequestManager.debounce(
      'status-update',
      () => updateFn(status),
      2000
    );
  };
}

/**
 * Создает throttle функцию для real-time обновлений (1000ms)
 */
export function createRealtimeUpdateThrottle(updateFn) {
  return globalRequestManager.throttle(
    'realtime-update',
    updateFn,
    1000
  );
}

/**
 * Батчинг загрузки пользователей по ID
 * Вместо 5 отдельных запросов - один запрос с массивом ID
 */
export function createUserBatchLoader(loadFn) {
  return (userId) => {
    if (window.optimizationModule?.stats) {
      window.optimizationModule.stats.requestsDebounced++;
    }
    return globalRequestManager.batch(
      'user-batch-load',
      async (userIds) => {
        return loadFn(userIds);
      },
      userId,
      50 // Батч отправляется через 50ms
    );
  };
}

/**
 * Дублирование запросов - если один и тот же запрос идет дважды,
 * используем результат первого
 */
export function createDedupeFetch(url, fetchFn) {
  const dedupeKey = `fetch:${url}`;
  return () => {
    if (window.optimizationModule?.stats) {
      window.optimizationModule.stats.requestsDebounced++;
    }
    return globalRequestManager.deduplicate(dedupeKey, fetchFn);
  };
}

/**
 * Вспомогательная функция для измерения эффективности
 */
export function logDebouncingStats() {
  const stats = globalRequestManager.getStats();
  console.group('📊 Debouncing Statistics');
  console.log('Pending Debounces:', stats.pendingDebounces);
  console.log('Pending Requests:', stats.pendingRequests);
  console.log('Cached Results:', stats.cachedResults);
  console.table(stats.cacheKeys.slice(0, 5));
  console.groupEnd();
}

// Делаем доступным из консоли
window.logDebouncingStats = logDebouncingStats;

export default {
  createUserSearchDebounce,
  createPluginSearchDebounce,
  createInstructionAutoSaveDebounce,
  createStatusUpdateDebounce,
  createRealtimeUpdateThrottle,
  createUserBatchLoader,
  createDedupeFetch,
  logDebouncingStats,
  globalRequestManager
};
