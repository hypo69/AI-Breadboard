/**
 * =============================================================================
 * Process Name: AI-Breadboard UI - Tab-Loader Script
 * =============================================================================
 * Description:
 *   Клиентский веб-скрипт модуля tab-loader.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/src/api/webgui/js/tab-loader.js?v=20261001_v1" type="module"></script>
 *
 * File: tab-loader.js
 * Project: ai-breadboard
 * Package: src/api/webgui/js
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-01 13:13:56
 * =============================================================================
 */

/**
 * LazyTabLoader - Система ленивой загрузки вкладок
 * 
 * Управляет загрузкой вкладок по требованию, кешировани в памяти
 * и минимизирует первоначальную нагрузку на интерфейс.
 * 
 * Usage:
 *   const loader = new LazyTabLoader();
 *   loader.registerTab('chat', '/html/chat/index.html', '/html/chat/main.js');
 *   await loader.loadTab('chati18n.t('auto__loader_isloaded__f0ed57')chati18n.t('auto__true_class_lazytabloader_constructor_this_tabs_new_map_this_loaded_new_set_this_loading_new_map_this_cache_new_map_registertab_tabname_htmlurl_jsurl_null_if_this_tabs_has_tabname_this_tabs_set_tabname_htmlurl_jsurl_initialized_false_async_loadtab_tabname_if_this_tabs_has_tabname_console_warn_lazytabloader_tab_a089dc')${tabName}i18n.t('auto_not_registered_return_false_if_this_loading_has_tabname_return_this_loading_get_tabname_if_this_loaded_has_tabname_return_true_const_loadpromise_this_performload_tabname_this_loading_set_tabname_loadpromise_try_const_result_await_loadpromise_this_loaded_add_tabname_return_result_finally_this_loading_delete_tabname_preloadtab_tabname_if_this_loaded_has_tabname_this_loading_has_tabname_this_loadtab_tabname_catch_e_console_error_lazytabloader_failed_to_preload_tabname_e_isloaded_tabname_return_this_loaded_has_tabname_async_performload_tabname_const_tab_this_tabs_get_tabname_if_tab_return_false_try_loader_this_showloading_tabname_html_const_response_await_fetch_tab_htmlurl_if_response_ok_throw_new_error_http_response_status_const_html_await_response_text_html_const_container_document_getelementbyid_tab_tabname_if_container_throw_new_error_container_tab_tabname_not_found_container_innerhtml_html_this_cache_set_tabname_html_js_if_tab_jsurl_await_this_loadandexecutescript_tabname_tab_jsurl_loader_this_hideloading_tabname_init_const_initfuncname_this_getinitfunctionname_tabname_if_typeof_window_initfuncname__d8eed7')functioni18n.t('auto__console_log_lazytabloader_calling_initfuncname_for_tabname_try_await_window_initfuncname_catch_err_console_error_lazytabloader_error_executing_initfuncname_err_console_log_lazytabloader_successfully_loaded_tab_tabname_return_true_catch_e_console_error_lazytabloader_error_loading_tab_tabname_e_this_showerror_tabname_e_message_return_false_loadandexecutescript_tabname_jsurl_return_new_promise_resolve_reject_const_script_document_createelement__052e03')script');
      script.src = jsUrl;
      script.type = 'modulei18n.t('auto__script_onload_console_log_lazytabloader_loaded_js_for_tabname_resolve_script_onerror_err_console_warn_lazytabloader_note_no_js_loaded_for_tabname_from_jsurl_resolve_js_document_body_appendchild_script_getinitfunctionname_tabname_const_camelname_tabname_replace_a_z_g_c_c_touppercase_return_e81c36')init' + camelName.charAt(0).toUpperCase() + camelName.slice(1) + 'Tab';
  }

  /**
   * Показывает индикатор загрузки на вкладке
   */
  _showLoading(tabName) {
    const container = document.getElementById(`tab-${tabName}`);
    if (container) {
      container.innerHTML = `
        <div class="d-flex justify-content-center align-items-center" style="height: 300px;">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hiddeni18n.t('auto__span_div_div_hideloading_tabname_loader_showerror_tabname_errormessage_const_container_document_getelementbyid_tab_tabname_if_container_container_innerhtml_div_class__384a23')alert alert-danger m-3" role="alerti18n.t('auto__strong_strong_errormessage_br_small_class__00effb')text-muted">Вкладка: ${tabName}</small>
        </div>
      `;
    }
  }

  /**
   * Очищает кеш и загруженные вкладки
   */
  clear() {
    this.loaded.clear();
    this.cache.clear();
    this.loading.clear();
  }

  /**
   * Выгружает конкретную вкладку из памяти
   */
  unload(tabName) {
    this.loaded.delete(tabName);
    this.cache.delete(tabName);
    const container = document.getElementById(`tab-${tabName}`);
    if (container) {
      container.innerHTML = '';
    }
  }

  /**
   * Вспомогательный метод: загрузить несколько вкладок параллельно
   */
  async loadMultiple(tabNames) {
    return Promise.all(tabNames.map(name => this.loadTab(name)));
  }

  /**
   * Вспомогательный метод: предзагрузить несколько вкладок в фоне
   */
  preloadMultiple(tabNames) {
    tabNames.forEach(name => this.preloadTab(name));
  }
}

// Экспортируем глобально
window.LazyTabLoader = LazyTabLoader;

export default LazyTabLoader;
