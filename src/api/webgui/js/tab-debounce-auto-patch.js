/**
 * Tab Debounce Auto-Patch - Автоматическое применение дебаунса к табам
 * 
 * Этот модуль автоматически улучшает дебаунс в:
 * - Поиске (все табы с поиском)
 * - Автосохранении (инструкции, конфиги)
 * - Real-time обновлениях (статусы, счетчики)
 */

import { RequestManager } from './request-manager.js';

const tabRequestManagers = new Map(); // { tabName: RequestManager }

/**
 * Получить или создать RequestManager для вкладки
 */
function getTabRequestManager(tabName) {
  if (!tabRequestManagers.has(tabName)) {
    tabRequestManagers.set(tabName, new RequestManager());
  }
  return tabRequestManagers.get(tabName);
}

/**
 * Авто-патч поиска в любой вкладке
 * Находит input с id *-search-input и применяет дебаунс
 */
export function autoPatchSearchInputs(tabName) {
  const manager = getTabRequestManager(tabName);
  
  // Ищем все input'ы поиска в текущей вкладке
  const searchInputs = document.querySelectorAll('[id*="search-input"]:not([data-debounce-patched])');
  
  searchInputs.forEach(input => {
    if (!input.id) return;
    
    const debounceKey = `${tabName}-${input.id}`;
    let originalHandler = null;

    // Сохраняем оригинальный обработчик если есть
    if (input.oninput) {
      originalHandler = input.oninput;
    }

    input.addEventListener('input', (e) => {
      const value = e.target.value;
      
      manager.debounce(
        debounceKey,
        () => {
          // Вызываем оригинальный обработчик если был
          if (originalHandler) {
            originalHandler.call(input, e);
          }
          console.log(`[AutoPatch] Search debounced in ${tabName}: "${value}"`);
        },
        500
      ).catch(error => {
        console.error(`[AutoPatch] Search error in ${tabName}:`, error);
      });
    });

    input.setAttribute('data-debounce-patched', 'true');
    console.log(`[AutoPatch] Patched search input: ${input.id} in tab: ${tabName}`);
  });
}

/**
 * Авто-патч для текстаревей (инструкции, конфиги)
 * Находит textarea и применяет дебаунс для автосохранения
 */
export function autoPatchAutoSaveTextareas(tabName, saveFn = null) {
  const manager = getTabRequestManager(tabName);
  
  const textareas = document.querySelectorAll(`#tab-${tabName} textarea[id*="save"]:not([data-autosave-patched])`);
  
  textareas.forEach(textarea => {
    if (!textarea.id) return;

    const debounceKey = `${tabName}-autosave-${textarea.id}`;

    textarea.addEventListener('change', (e) => {
      const content = e.target.value;
      
      manager.debounce(
        debounceKey,
        async () => {
          if (saveFn) {
            await saveFn(content);
          }
          console.log(`[AutoPatch] Auto-saved content in ${tabName}`);
        },
        1000
      ).catch(error => {
        console.error(`[AutoPatch] Auto-save error in ${tabName}:`, error);
      });
    });

    textarea.setAttribute('data-autosave-patched', 'true');
    console.log(`[AutoPatch] Patched auto-save textarea: ${textarea.id} in tab: ${tabName}`);
  });
}

/**
 * Авто-патч для real-time обновлений
 * Находит кнопки обновления и применяет throttle
 */
export function autoPatchRefreshButtons(tabName) {
  const manager = getTabRequestManager(tabName);
  
  const refreshBtns = document.querySelectorAll(
    `#tab-${tabName} button[id*="refresh"]:not([data-throttle-patched]), 
     #tab-${tabName} button[id*="refresh-btn"]:not([data-throttle-patched])`
  );
  
  refreshBtns.forEach(btn => {
    if (!btn.id) return;

    const originalOnClick = btn.onclick;
    const throttleKey = `${tabName}-refresh-${btn.id}`;

    btn.onclick = manager.throttle(
      throttleKey,
      async () => {
        if (originalOnClick) {
          await originalOnClick.call(btn);
        }
        console.log(`[AutoPatch] Refresh throttled in ${tabName}`);
      },
      2000
    );

    btn.setAttribute('data-throttle-patched', 'true');
    console.log(`[AutoPatch] Patched refresh button: ${btn.id} in tab: ${tabName}`);
  });
}

/**
 * Комплексный патч для всей вкладки
 */
export function autoPatchTab(tabName, options = {}) {
  console.log(`[AutoPatch] Patching tab: ${tabName}`);
  
  const { searchEnabled = true, autoSaveEnabled = true, refreshEnabled = true } = options;

  if (searchEnabled) {
    autoPatchSearchInputs(tabName);
  }

  if (autoSaveEnabled) {
    autoPatchAutoSaveTextareas(tabName, options.saveFn);
  }

  if (refreshEnabled) {
    autoPatchRefreshButtons(tabName);
  }

  console.log(`[AutoPatch] Completed patching tab: ${tabName}`);
}

/**
 * Получить статистику дебаунса для вкладки
 */
export function getTabDebounceStats(tabName) {
  const manager = tabRequestManagers.get(tabName);
  if (!manager) return null;
  return manager.getStats();
}

/**
 * Получить статистику дебаунса для всех вкладок
 */
export function getAllDebounceStats() {
  const stats = {};
  tabRequestManagers.forEach((manager, tabName) => {
    stats[tabName] = manager.getStats();
  });
  return stats;
}

// Экспортируем глобально
window.TabDebounceAutoPatch = {
  autoPatchSearchInputs,
  autoPatchAutoSaveTextareas,
  autoPatchRefreshButtons,
  autoPatchTab,
  getTabDebounceStats,
  getAllDebounceStats
};

