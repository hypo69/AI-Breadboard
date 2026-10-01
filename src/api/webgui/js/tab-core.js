/**
 * =============================================================================
 * Process Name: AI-Breadboard UI - Tab-Core Script
 * =============================================================================
 * Description:
 *   Клиентский веб-скрипт модуля tab-core.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/src/api/webgui/js/tab-core.js?v=20261001_v1" type="module"></script>
 *
 *   JavaScript Import:
 *     import { normalizeTabId, setupTabClicks } from '/src/api/webgui/js/tab-core.js';
 *
 * File: tab-core.js
 * Project: ai-breadboard
 * Package: src/api/webgui/js
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-01 13:13:56
 * =============================================================================
 */

/**
 * tab-core.js — Единая система управления вкладками, их жизненным циклом и поллингом.
 * Архитектура: UI_ARCHITECTURE.md
 * 
 * Правило: Только открытая АКТИВНАЯ вкладка выполняет периодические опросы API.
 * При неактивности вкладки или скрытии страницы (visibilitychange) все таймеры засыпают.
 * 
 * Приоритет переключения: кнопки навигации имеют самый высокий приоритет.
 * Если что-то запущено внутри вкладки, переключение происходит немедленно без ожидания.
 */

const OFFCANVAS_IDS = ['leftSideNavOffcanvas', 'appsSideNavOffcanvasi18n.t('auto__let_currentactivetabid_null_const_registeredpollers_new_map_const_processingflags_new_map_isprocessing__05f3bc')tab-xxx'.
 * @param {string} tabId 
 * @returns {string}
 */
export function normalizeTabId(tabId) {
  if (!tabId) return '';
  return tabId.startsWith('tab-i18n.t('auto__tabid_tab_tabid_param_string_tabid_returns_boolean_export_function_istabactive_tabid_const_normid_normalizetabid_tabid_if_typeof_document__682162')undefined' && document.hidden) {
    return false;
  }
  if (currentActiveTabId) {
    return currentActiveTabId === normId;
  }
  const pane = document.getElementById(normId);
  return pane ? pane.classList.contains('activei18n.t('auto__false_param_object_poller_function_stoppoller_poller_if_poller_timerid_clearinterval_poller_timerid_poller_timerid_null_param_object_poller_param_boolean_immediate_function_startpoller_poller_immediate_false_stoppoller_poller_if_poller_enabled_istabactive_poller_tabid_return_const_runtick_async_if_poller_enabled_istabactive_poller_tabid_poller_inflight_return_poller_inflight_true_try_await_poller_pollfn_catch_err_console_warn_tabpoller_pollfn_poller_id_err_finally_poller_inflight_false_if_immediate_runtick_poller_timerid_setinterval_runtick_poller_intervalms_poller_param_string_tabid_id__d13733')tab-about-systemi18n.t('auto___8bad5b')about-systemi18n.t('auto__param_function_pollfn_api_param_number_intervalms_1000_param_object_options_pollerid_immediate_true_enabled_true_returns_string_pollerid_export_function_registertabpoller_tabid_pollfn_intervalms_3000_options_const_normtabid_normalizetabid_tabid_const_pollerid_options_pollerid_normtabid_default_unregistertabpoller_pollerid_const_poller_id_pollerid_tabid_normtabid_pollfn_intervalms_math_max_1000_intervalms_enabled_options_enabled_false_timerid_null_inflight_false_registeredpollers_set_pollerid_poller_if_istabactive_normtabid_poller_enabled_startpoller_poller_options_immediate_false_return_pollerid_id_param_string_pollerid_export_function_unregistertabpoller_pollerid_if_registeredpollers_has_pollerid_const_poller_registeredpollers_get_pollerid_stoppoller_poller_registeredpollers_delete_pollerid_param_string_tabid_export_function_unregisteralltabpollers_tabid_const_normtabid_normalizetabid_tabid_for_const_id_poller_of_registeredpollers_entries_if_poller_tabid_normtabid_stoppoller_poller_registeredpollers_delete_id_live_param_string_pollerid_param_boolean_enabled_export_function_settabpollerenabled_pollerid_enabled_const_poller_registeredpollers_get_pollerid_if_poller_return_poller_enabled_enabled_if_poller_enabled_istabactive_poller_tabid_startpoller_poller_true_else_stoppoller_poller_const_tab_aliases__104c61')tab-process-leaks': { parentTab: 'tab-about-system', subtab: 'subtab-leaks' },
  'tab-forensics': { parentTab: 'tab-about-system', subtab: 'subtab-forensics' },
  'tab-throttling': { parentTab: 'tab-about-system', subtab: 'subtab-throttling' },
  'tab-storage-wear': { parentTab: 'tab-about-system', subtab: 'subtab-wear' },
  'tab-peripherals': { parentTab: 'tab-about-system', subtab: 'subtab-peripheralsi18n.t('auto__param_string_tabid_export_function_switchtab_tabid_if_tabid_return_const_rawid_normalizetabid_tabid_const_alias_tab_aliases_rawid_tab_aliases_tabid_const_id_alias_alias_parenttab_rawid_const_prevtabid_currentactivetabid_1_if_prevtabid_prevtabid_id_window_chatservice_stop_try_window_chatservice_stop_catch_e_2_if_prevtabid_prevtabid_id_for_const_poller_of_registeredpollers_values_if_poller_tabid_prevtabid_stoppoller_poller_currentactivetabid_id_3_ui_dom_zero_delay_document_queryselectorall__c36a41')[data-tab]').forEach(btn =>
    btn.classList.toggle('active', btn.dataset.tab === rawId || btn.dataset.tab === id)
  );

  document.querySelectorAll('#mainTabContent .tab-pane').forEach(pane => {
    const isTarget = (pane.id === id);
    pane.classList.toggle('show', isTarget);
    pane.classList.toggle('active', isTarget);
  });

  // Если это подвкладка, активируем ее внутри родительской страницы
  if (alias && alias.subtab) {
    setTimeout(() => {
      const subBtn = document.querySelector(`.about-subtab-btn[data-subtab="${alias.subtab}"]`);
      if (subBtn) subBtn.click();
    }, 20);
  }

  // 4. Бейдж заголовка
  const badge = document.getElementById('active-tab-title-badge');
  const activeBtn = document.querySelector(`[data-tab="${rawId}"]`) || document.querySelector(`[data-tab="${id}"]`);
  if (badge && activeBtn) badge.innerHTML = activeBtn.innerHTML;

  // 5. Быстро закрыть offcanvas меню
  OFFCANVAS_IDS.forEach(ocId => {
    const el = document.getElementById(ocId);
    if (el) bootstrap.Offcanvas.getInstance(el)?.hide();
  });

  // 6. Обновить URL hash
  try {
    history.replaceState(null, null, `#${rawId}`);
  } catch (e) {}

  // 7. Запуск опросников новой активной вкладки
  for (const poller of registeredPollers.values()) {
    if (poller.tabId === id && poller.enabled) {
      startPoller(poller, true);
    }
  }

  // 8. Неблокирующий вызов Lifecycle hooks через requestAnimationFrame / setTimeout
  const name = id.replace(/^tab-/, '').replace(/-([a-z])/g, (_, c) => c.toUpperCase());
  const prevName = prevTabId ? prevTabId.replace(/^tab-/, 'i18n.t('auto__replace_a_z_g_c_c_touppercase_null_if_prevtabid_prevtabid_id_const_deactivatefn_window_deactivate_prevname_0_touppercase_prevname_slice_1_tab_if_typeof_deactivatefn__b8a725')function') {
      setTimeout(() => {
        try { deactivateFn(); } catch (err) { console.debug('deactivate hook error:', err); }
      }, 0);
    }
    document.dispatchEvent(new CustomEvent('tab:deactivatedi18n.t('auto__detail_tabid_prevtabid_name_prevname_requestanimationframe_const_initfn_window_init_name_0_touppercase_name_slice_1_tab_if_typeof_initfn__a18f54')function') {
      try { initFn(); } catch (err) { console.debug('init tab hook error:', err); }
    }
    
    const activateFn = window[`activate${name[0].toUpperCase() + name.slice(1)}Tab`];
    if (typeof activateFn === 'function') {
      try { activateFn(); } catch (err) { console.debug('activate tab hook error:', err); }
    }
    
    document.dispatchEvent(new CustomEvent('tab:activated', { detail: { tabId: id, name } }));
  });
}

/**
 * Загружает разметку и скрипт вкладки по требованию (Lazy Load).
 * @param {string} tabName 
 * @param {string} htmlUrl 
 * @param {string} jsUrl 
 */
export async function loadTab(tabName, htmlUrl, jsUrl) {
  const container = document.getElementById(`tab-${tabName}`);
  if (!container) return;
  
  // Показываем мгновенный скелетон/спиннер, если контейнер еще пуст
  if (!container.innerHTML.trim()) {
    container.innerHTML = `
      <div class="d-flex flex-column align-items-center justify-content-center py-5 text-muted" style="min-height: 200px;">
        <div class="spinner-border text-primary mb-2" role="status" style="width: 2rem; height: 2rem;"></div>
        <span class="small fw-medium">Загрузка раздела...</span>
      </div>
    `;
  }

  try {
    const r = await fetch(htmlUrl);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    container.innerHTML = await r.text();
    await new Promise(resolve => {
      const s = document.createElement('script');
      s.src = jsUrl;
      s.onload = s.onerror = resolve;
      document.body.appendChild(s);
    });
    const name = tabName.replace(/-([a-z])/g, (_, c) => c.toUpperCase());
    window[`init${name[0].toUpperCase() + name.slice(1)}Tab`]?.();
  } catch (e) {
    container.innerHTML = `<div class="alert alert-danger m-3">Ошибка загрузки ${tabName}: ${e.message}</div>`;
  }
}

/**
 * Устанавливает единый слушатель кликов по элементам с data-tab.
 */
export function setupTabClicks() {
  document.addEventListener('click', e => {
    const btn = e.target.closest('button[data-tab], a[data-tab]');
    if (btn && btn.dataset.tab) {
      if (typeof window.switchTab === 'functioni18n.t('auto__window_switchtab_btn_dataset_tab_else_switchtab_btn_dataset_tab_if_typeof_document__04ee8b')undefined') {
  document.addEventListener('visibilitychangei18n.t('auto__if_document_hidden_for_const_poller_of_registeredpollers_values_stoppoller_poller_else_if_currentactivetabid_for_const_poller_of_registeredpollers_values_if_poller_tabid_currentactivetabid_poller_enabled_startpoller_poller_true_processing_param_string_tabid_id_param_boolean_isprocessing_export_function_settabprocessing_tabid_isprocessing_const_normid_normalizetabid_tabid_processingflags_set_normid_isprocessing_processing_param_string_tabid_id_export_function_resettabprocessing_tabid_const_normid_normalizetabid_tabid_processingflags_delete_normid_window_if_typeof_window__533fb4')undefined') {
  window.switchTab = switchTab;
  window.switchToTab = switchTab;
  window.loadTab = loadTab;
  window.setupTabClicks = setupTabClicks;
  window.normalizeTabId = normalizeTabId;
  window.isTabActive = isTabActive;
  window.registerTabPoller = registerTabPoller;
  window.unregisterTabPoller = unregisterTabPoller;
  window.unregisterAllTabPollers = unregisterAllTabPollers;
  window.setTabPollerEnabled = setTabPollerEnabled;
  window.setTabProcessing = setTabProcessing;
  window.resetTabProcessing = resetTabProcessing;
}
