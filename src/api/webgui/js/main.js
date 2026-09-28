/**
 * js/main.js — оркестратор главной страницы (run.ps1, маршрут /)
 * Архитектура: UI_ARCHITECTURE.md
 */

import { initI18n, switchLang, applyTranslations } from './i18n.js';
import { initTheme } from './theme.js';
import { initUserSettings } from './userSettings.js';
import { initActivityTracker } from './activityTracker.js';
import { initCacheUI } from './cache-ui.js';
import { switchTab, loadTab, setupTabClicks } from './tab-core.js';
import './api-cache.jsi18n.t('auto__api_import_564f4f')./test-api-cache.jsi18n.t('auto__window_switchtab_switchtab_window_switchtotab_switchtab_window_applytranslations_applytranslations_htmlurl_jsurl_const_tabs__d78f80')chat':           ['/html/chat/index.html',                 '/html/chat/main.js'],
  'rag':            ['/html/rag_tab/index.html',              '/html/rag_tab/main.js'],
  'telegram-rag':   ['/html/telegram_rag_tab/index.html',     '/html/telegram_rag_tab/main.js'],
  'news':           ['/html/news_tab/index.html',             '/html/news_tab/main.js'],
  'voice':          ['/html/voice_tab/index.html',            '/html/voice_tab/main.js'],
  'plugins':        ['/html/plugins_tab/index.html',          '/html/plugins_tab/main.js'],
  'admin':          ['/html/admin_tab/index.html',            '/html/admin_tab/main.js'],
  'help':           ['/html/help/index.html',                 '/html/help/main.js'],
  'process-leaks':  ['/html/process_leaks_tab/index.html',    '/html/process_leaks_tab/main.js'],
  'forensics':      ['/html/forensics_tab/index.html',        '/html/forensics_tab/main.js'],
  'throttling':     ['/html/throttling_tab/index.html',       '/html/throttling_tab/main.js'],
  'storage-wear':   ['/html/storage_wear_tab/index.html',     '/html/storage_wear_tab/main.js'],
  'peripherals':    ['/html/peripherals_tab/index.html',      '/html/peripherals_tab/main.js'],
  'system-logs':    ['/html/system_logs_tab/index.html',      '/html/system_logs_tab/main.jsi18n.t('auto__lazy_const_loaded_new_set_async_function_lazyload_tabname_if_loaded_has_tabname_tabs_tabname_return_loaded_add_tabname_const_v_date_now_const_html_js_tabs_tabname_await_loadtab_tabname_html_v_v_js_v_v_applytranslations_switchtab_const_switchtab_switchtab_export_function_switchmaintab_tabid_if_tabid_return_1_ui_switchtab_tabid_2_const_name_tabid_startswith__a23548')tab-i18n.t('auto__tabid_slice_4_tabid_if_loaded_has_name_tabs_name_lazyload_name_catch_err_console_warn_main_lazyload_name_err_window_switchtab_switchmaintab_window_switchtotab_switchmaintab_window_openpluginfromdropdown_function_pluginname_if_pluginname_return_const_n_pluginname_tolowercase_replace_g__99c4ce')_');
  if (n === 'telegram_channel_rag' || n === 'telegram_rag') {
    window.switchTab('tab-telegram-rag'); return;
  }
  if (n === 'news_feed' || n === 'news' || n === 'smart_news') {
    window.switchTab('tab-news'); return;
  }
  window.switchTab('tab-pluginsi18n.t('auto__const_sel_window_selectplugin_pluginname_sel_settimeout_sel_200_async_function_init_1_inittheme_2_i18n_const_lang_localstorage_getitem__376466')app_language') || 'ru';
  await initI18n(lang);
  document.querySelectorAll('.lang-selector').forEach(sel => {
    sel.value = lang;
    sel.addEventListener('changei18n.t('auto__e_switchlang_e_target_value_3_await_initusersettings_initactivitytracker_initcacheui_4_setuptabclicks_5_await_lazyload__3a05a1')chati18n.t('auto__applytranslations_6_try_const_r_await_fetch__fde3f2')/api/admin/pluginsi18n.t('auto__if_r_ok_const_data_await_r_json_window_syncplugintabsvisibility_data_plugins_catch_7_hash_const_hash_location_hash_replace__c795c7')#', '');
  await switchMainTab(hash || 'tab-chati18n.t('auto__8_websocket_initcomputerstream_websocket_remote_transcript_function_initcomputerstream_const_proto_location_protocol__293188')https:' ? 'wss:' : 'ws:';
  const ws = new WebSocket(`${proto}//${location.host}/api/control/ws?role=computer`);
  ws.onmessage = e => {
    try {
      const msg = JSON.parse(e.data);
      if (msg.event === 'transcript') window.handleRemoteTranscript?.(msg.text);
    } catch {}
  };
  ws.onclose = () => setTimeout(initComputerStream, 3000);
}



document.readyState === 'loading'
  ? document.addEventListener('DOMContentLoaded', init)
  : init();
