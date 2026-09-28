/**
 * Admin Interface Main - Оркестратор
 * 
 * Главный модуль для инициализации административного интерфейса.
 * Все реальная реализация находится в модулях, этот файл только оркестрирует.
 * 
 * Модули:
 * - auth-handler.js: Аутентификация и проверка пароля
 * - tab-manager.js: Управление вкладками и навигацией
 * - ui-handler.js: Модали, уведомления, помощь
 * - init-interface.js: Инициализация компонентов
 * - apps-sync.js: Синхронизация приложений
 */

// ============================================================================
// ИМПОРТ МОДУЛЕЙ
// ============================================================================

import { setupAuthHandlers, verifyPassword } from './modules/auth-handler.js';
import { setupTabManagement, onTabSwitched } from './modules/tab-manager.js';
import { setupUIHandlers, showHelpModal, showNotification, showChatLogicModal } from './modules/ui-handler.js';
import { 
  initializeInterface, 
  setupGlobalFunctions, 
  setupLanguageSelector, 
  setupThemeSelector 
} from './modules/init-interface.js';
import { syncApplicationsVisibility } from './modules/apps-sync.jsi18n.t('auto__let_tabloader_null_let_apifetcher_null_async_function_initadmininterface_console_log__23556e')🚀 [AdminInterface] Starting initialization...i18n.t('auto__try_1_console_log__2099b9')[AdminInterface] Step 1: Initializing core components...i18n.t('auto__await_initializeinterface_setupglobalfunctions_setuplanguageselector_setupthemeselector_2_ui_console_log__8f9de3')[AdminInterface] Step 2: Setting up UI handlers...i18n.t('auto__registerglobalfunctions_setupuihandlers_setupauthhandlers_3_console_log__5a171c')[AdminInterface] Step 3: Setting up tab management...i18n.t('auto__setuptabmanagement_4_console_log__4aa4ef')[AdminInterface] Step 4: Syncing applications visibility...i18n.t('auto__await_syncapplicationsvisibility_5_console_log__0d542f')[AdminInterface] Step 5: Initializing optimizations...i18n.t('auto__await_initializeoptimizations_6_api_console_log__7a4b96')[AdminInterface] Step 6: Setting up API client...');
    setupAPIClient();
    
    console.log('✅ [AdminInterface] Initialization complete!');
    
  } catch (error) {
    console.error('❌ [AdminInterface] Initialization error:', error);
    showNotification(i18n.t('auto___ff6b83') + error.message, 'dangeri18n.t('auto__function_registerglobalfunctions_window_switchtab_switchtab_window_ontabswitched_ontabswitched_window_showhelpmodal_showhelpmodal_window_shownotification_shownotification_window_showchatlogicmodal_showchatlogicmodal_window_verifypassword_verifypassword_async_function_switchtab_targetid_if_targetid_return_const_cleanid_targetid_startswith__5ed247')#') ? targetId.slice(1) : targetId;
  const tabName = cleanId.replace(/^tab-/, 'i18n.t('auto__console_log_admininterface_switching_to_tab_tabname_lazytabloader_if_tabloader_typeof_tabloader_isloaded__05874b')functioni18n.t('auto__if_tabloader_isloaded_tabname_console_log_admininterface_loading_tab_tabname_await_tabloader_loadtab_tabname_updatetabui_cleanid_callback_if_typeof_window_ontabswitched__e3f731')functioni18n.t('auto__window_ontabswitched_cleanid_console_log_admininterface_tab_switched_tabname_ui_function_updatetabui_cleanid_const_tabid_cleanid_startswith__acb6d6')tab-i18n.t('auto__cleanid_tab_cleanid_document_queryselectorall__504a7c')#mainTabContent > .tab-pane, body > .container-fluid > .tab-content > .tab-pane, [role="tabpanel"]').forEach(tab => {
    tab.classList.remove('active', 'show');
    tab.setAttribute('aria-hidden', 'truei18n.t('auto__const_targettab_document_getelementbyid_tabid_document_getelementbyid_cleanid_if_targettab_targettab_classlist_add__7bdd4f')active', 'show');
    targetTab.setAttribute('aria-hidden', 'falsei18n.t('auto__document_queryselectorall__d43cda')#mainTabs .list-group-item, #mainTabs .dropdown-item, #mainTabs [data-tab], #mainTabs [data-bs-target]').forEach(item => {
    const itemTarget = item.getAttribute('data-tab') || item.getAttribute('data-bs-target')?.replace('#', '');
    if (itemTarget === tabId || itemTarget === cleanId) {
      item.classList.add('active');
      item.setAttribute('aria-selected', 'true');
    } else {
      item.classList.remove('active');
      item.setAttribute('aria-selected', 'falsei18n.t('auto__dropdown_toggle_document_queryselectorall__40b83e')#mainTabs .dropdown').forEach(dropdown => {
    const toggle = dropdown.querySelector('.dropdown-toggle');
    const hasActiveChild = dropdown.querySelector('.dropdown-item.active, .list-group-item.active');
    if (toggle) {
      if (hasActiveChild) {
        toggle.classList.add('active');
      } else {
        toggle.classList.remove('activei18n.t('auto__async_function_initializeoptimizations_lazy_init_patch_js_if_window_optimizationmodule_tabloader_window_optimizationmodule_tabloader_apifetcher_window_optimizationmodule_apifetcher_console_log__885138')[AdminInterface] Optimizations initialized');
  } else {
    console.warn('[AdminInterface] Optimization module not foundi18n.t('auto__api_function_setupapiclient_if_window_api_console_warn__413ad2')[AdminInterface] API client not found, skipping setupi18n.t('auto__return_api_main_js_console_log__b04560')[AdminInterface] API client readyi18n.t('auto__load_if_document_readystate__1d9054')loading') {
  document.addEventListener('DOMContentLoaded', initAdminInterface);
} else {
  initAdminInterface();
}

console.log('📦 [AdminInterface] Module loaded and ready');

// ============================================================================
// ЭКСПОРТЫ (для модульного использования)
// ============================================================================

export {
  initAdminInterface,
  switchTab,
  setupAuthHandlers,
  setupTabManagement,
  setupUIHandlers,
  syncApplicationsVisibility,
  initializeInterface,
  setupGlobalFunctions
};
