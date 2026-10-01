/**
 * =============================================================================
 * Process Name: Windows Js - Tab-Debounce-Auto-Patch Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля tab-debounce-auto-patch.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/~webgui/js/tab-debounce-auto-patch.js?v=20261001_v1" type="module"></script>
 *
 *   JavaScript Import:
 *     import { autoPatchAutoSaveTextareas, autoPatchRefreshButtons, autoPatchTab } from '/windows/api/~webgui/js/tab-debounce-auto-patch.js';
 *
 * File: tab-debounce-auto-patch.js
 * Project: ai-breadboard
 * Package: windows/api/~webgui/js
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-01 13:04:40
 * =============================================================================
 */

/**
 * Tab Debounce Auto-Patch - Автоматическое применение дебаунса к табам
 * 
 * Этот модуль автоматически улучшает дебаунс в:
 * - Поиске (все табы с поиском)
 * - Автосохранении (инструкции, конфиги)
 * - Real-time обновлениях (статусы, счетчики)
 */

import { RequestManager } from './request-manager.jsi18n.t('auto__const_tabrequestmanagers_new_map_tabname_requestmanager_requestmanager_function_gettabrequestmanager_tabname_if_tabrequestmanagers_has_tabname_tabrequestmanagers_set_tabname_new_requestmanager_return_tabrequestmanagers_get_tabname_input_id_search_input_export_function_autopatchsearchinputs_tabname_const_manager_gettabrequestmanager_tabname_input_c8ae6f')ы поиска в текущей вкладке
  const searchInputs = document.querySelectorAll('[id*="search-input"]:not([data-debounce-patched])i18n.t('auto__searchinputs_foreach_input_if_input_id_return_const_debouncekey_tabname_input_id_let_originalhandler_null_if_input_oninput_originalhandler_input_oninput_input_addeventlistener__c6a337')input', (e) => {
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

