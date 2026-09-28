/**
 * Lazy Init Patch - Патч для переключения на ленивую загрузку вкладок
 * 
 * Этот скрипт перехватывает инициализацию main.js и использует
 * LazyTabLoader вместо стандартной загрузки всех вкладок сразу
 */

import { 
  initLazyTabLoading, 
  enhanceTabSwitching, 
  restoreLastTab 
} from './optimization-init.js';
import { autoPatchTab } from '../js/tab-debounce-auto-patch.js';
import TabStatePersistence from '../js/tab-state-persistence.js';
import TabSwitchOptimizer from '../js/tab-switch-optimizer.js';

console.log('[LazyInitPatch] Patching admin interface initialization...i18n.t('auto__persistence_const_tabpersistence_new_tabstatepersistence__69b93d')admini18n.t('auto__window_tabpersistence_tabpersistence_main_js_window_addeventlistener__5c5688')load', async () => {
  console.log('[LazyInitPatch] Window load event, initializing lazy loading...i18n.t('auto__main_js_await_new_promise_resolve_settimeout_resolve_100_switchtab_if_window_switchtab_typeof_window_switchtab__324746')functioni18n.t('auto__const_originalswitchtab_window_switchtab_const_switchoptimizer_new_tabswitchoptimizer_switchoptimizer_enabledomcaching_enhanced_lazy_loading_let_enhancedswitchtab_enhancetabswitching_originalswitchtab_optimizer_const_optimizedswitchtab_switchoptimizer_optimizeswitching_enhancedswitchtab_window_switchtab_async_function_targetid_await_optimizedswitchtab_call_this_targetid_if_targetid_const_cleanid_targetid_startswith__ca33f5')#') ? targetId.slice(1) : targetId;
        tabPersistence.saveActiveTab(cleanId);
      }
    };
    
    console.log('[LazyInitPatch] Enhanced switchTab with on-demand lazy loading and persistencei18n.t('auto__const_alltabdefinitions_tabname__e30d7f')chat', htmlUrl: `/html/chat/index.html`, jsUrl: `/html/chat/main.js` },
    { tabName: 'voice', htmlUrl: `/html/voice_tab/index.html`, jsUrl: `/html/voice_tab/main.js` },
    { tabName: 'ttsi18n.t('auto__htmlurl_html_tts_tab_index_html_jsurl_html_tts_tab_main_js_tabname__ef3e4c')rag', htmlUrl: `/html/rag_tab/index.html`, jsUrl: `/html/rag_tab/main.js` },
    { tabName: 'models', htmlUrl: `/html/models_tab/index.html`, jsUrl: `/html/models_tab/main.js` },
    { tabName: 'agents', htmlUrl: `/html/agents_tab/index.html`, jsUrl: `/html/agents_tab/main.js` },
    { tabName: 'skills', htmlUrl: `/html/skills_tab/index.html`, jsUrl: `/html/skills_tab/main.js` },
    { tabName: 'mcp', htmlUrl: `/html/mcp_tab/index.html`, jsUrl: `/html/mcp_tab/main.js` },
    { tabName: 'observability', htmlUrl: `/html/system_inspector_tab/index.html?v=20260926_v1`, jsUrl: `/html/system_inspector_tab/main.js?v=20260926_v1` },
    { tabName: 'telegram-rag', htmlUrl: `/html/telegram_rag_tab/index.html`, jsUrl: `/html/telegram_rag_tab/main.js` },
    { tabName: 'sources', htmlUrl: `/html/sources_tab/index.html`, jsUrl: `/html/sources_tab/main.js` },
    { tabName: 'searchi18n.t('auto__htmlurl_html_search_tab_index_html_jsurl_html_search_tab_main_js_tabname__c5536c')admin', htmlUrl: `/html/admin_tab/index.html`, jsUrl: `/html/admin_tab/main.js` },
    { tabName: 'users', htmlUrl: `/html/users_tab/index.html`, jsUrl: `/html/users_tab/main.js` },
    { tabName: 'plugins', htmlUrl: `/html/plugins_tab/index.html`, jsUrl: `/html/plugins_tab/main.js` },
    { tabName: 'google-accounts', htmlUrl: `/html/google_accounts_tab/index.html`, jsUrl: `/html/google_accounts_tab/main.js` },
    { tabName: 'instructions', htmlUrl: `/html/instructions_tab/index.html`, jsUrl: `/html/instructions_tab/main.js` },
    { tabName: 'news', htmlUrl: `/html/news_tab/index.html`, jsUrl: `/html/news_tab/main.js` },
    { tabName: 'logs', htmlUrl: `/html/logs/index.html`, jsUrl: `/html/logs/main.js` },
    { tabName: 'helpi18n.t('auto__htmlurl_html_help_index_html_jsurl_html_help_main_js_id_tabname__72bbf0')trading', appId: 'trading_terminal', htmlUrl: `/html/trading_tab/index.html`, jsUrl: `/html/trading_tab/main.js` },
    { tabName: 'network', appId: 'network_terminal', htmlUrl: `/html/network_tab/index.html`, jsUrl: `/html/network_tab/main.js` },
    { tabName: 'system-inspector', appId: 'system_inspector', htmlUrl: `/html/system_inspector_tab/index.html?v=20260926_v1`, jsUrl: `/html/system_inspector_tab/main.js?v=20260926_v1` },
    { tabName: 'about-system', appId: 'about_system', htmlUrl: `/html/about_system_tab/index.html?v=20260926_v1`, jsUrl: `/html/about_system_tab/main.js?v=20260926_v1` },
    { tabName: 'windows-admin', appId: 'windows_sysadmin', htmlUrl: `/html/windows_admin_tab/index.html`, jsUrl: `/html/windows_admin_tab/main.js` },
    { tabName: 'cloudflared', appId: 'cloudflared_monitor', htmlUrl: `/html/cloudflared_tab/index.html`, jsUrl: `/html/cloudflared_tab/main.js` },
    { tabName: 'google-desktop', appId: 'google_user_desktop', htmlUrl: `/html/google_desktop_tab/index.html?v=20260928_v2`, jsUrl: `/html/google_desktop_tab/main.js?v=20260928_v2` },
    { tabName: 'user-assistant', appId: 'user_assistant', htmlUrl: `/html/user_assistant_tab/index.html`, jsUrl: `/html/user_assistant_tab/main.js` },
    { tabName: 'gcloud', appId: 'gcloud_monitor', htmlUrl: `/html/gcloud_tab/index.html`, jsUrl: `/html/gcloud_tab/main.js` },
    { tabName: 'website-monitor', appId: 'website_monitor', htmlUrl: `/html/website_monitor_tab/index.html`, jsUrl: `/html/website_monitor_tab/main.js` },
    { tabName: 'system-control', appId: 'system_control_center', htmlUrl: `/html/system_control_tab/index.html?v=20260924_v1`, jsUrl: `/html/system_control_tab/main.js?v=20260924_v1` },
    { tabName: 'system-logs', appId: 'system_log_viewer', htmlUrl: `/html/system_logs_tab/index.html`, jsUrl: `/html/system_logs_tab/main.js` },
    { tabName: 'software-audit', appId: 'software_audit', htmlUrl: `/html/software_audit_tab/index.html`, jsUrl: `/html/software_audit_tab/main.js` },
    { tabName: 'registry-viewer', appId: 'registry_viewer', htmlUrl: `/html/registry_viewer_tab/index.html`, jsUrl: `/html/registry_viewer_tab/main.js` },
    { tabName: 'startup-auditor', appId: 'windows_startup_auditor', htmlUrl: `/html/startup_auditor_tab/index.html`, jsUrl: `/html/startup_auditor_tab/main.js` },
    { tabName: 'windows-backup', appId: 'windows_backup_manager', htmlUrl: `/html/windows_backup_tab/index.html?v=20260924_v2`, jsUrl: `/html/windows_backup_tab/main.js?v=20260924_v2` },
    { tabName: 'wikipedia-research', appId: 'wikipedia_research', htmlUrl: `/html/wikipedia_research_tab/index.html`, jsUrl: `/html/wikipedia_research_tab/main.js` },
    { tabName: 'process-leaks', appId: 'process_leaks', htmlUrl: `/html/process_leaks_tab/index.html?v=20260924_v1`, jsUrl: `/html/process_leaks_tab/main.js?v=20260924_v1` },
    { tabName: 'forensics', appId: 'forensics', htmlUrl: `/html/forensics_tab/index.html?v=20260924_v1`, jsUrl: `/html/forensics_tab/main.js?v=20260924_v1` },
    { tabName: 'throttling', appId: 'throttling', htmlUrl: `/html/throttling_tab/index.html?v=20260924_v1`, jsUrl: `/html/throttling_tab/main.js?v=20260924_v1` },
    { tabName: 'storage-wear', appId: 'storage_wear', htmlUrl: `/html/storage_wear_tab/index.html?v=20260924_v1`, jsUrl: `/html/storage_wear_tab/main.js?v=20260924_v1` },
    { tabName: 'peripherals', appId: 'peripheralsi18n.t('auto__htmlurl_html_peripherals_tab_index_html_v_20260924_v1_jsurl_html_peripherals_tab_main_js_v_20260924_v1_try_run_dashboard_run_tc_su_let_appsstatus_window_appsstatusmap_null_if_appsstatus_try_const_res_await_window_api_window_api_fetch__122660')/api/apps/status') : fetch('/api/apps/status').then(r => r.json()));
        appsStatus = res?.apps || null;
      } catch (err) {
        console.warn('[LazyInitPatch] Could not fetch apps status for profile filtering:i18n.t('auto__err_const_activetabdefinitions_alltabdefinitions_filter_tab_if_tab_appid_appsstatus_const_appinfo_appsstatus_tab_appid_object_values_appsstatus_find_a_a_id_tab_appid_a_tab_tab_tab_tabname_if_appinfo_appinfo_enabled_false_return_false_return_true_await_initlazytabloading_activetabdefinitions_console_log_lazyinitpatch_lazy_loading_initialized_activetabdefinitions_length_tabs_registered_on_demand_const_restored_await_restorelasttab__11e3e7')tab-about-system');
    console.log(`[LazyInitPatch] Initial active tab loaded: ${restored}`);

  } catch (error) {
    console.error('[LazyInitPatch] Error during initialization:', error);
  }
});

console.log('[LazyInitPatch] Patch loaded successfully');

export {};
