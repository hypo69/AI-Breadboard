/**
 * Users Tab Debounce Patch
 * 
 * Применяет улучшенный дебаунс к поиску пользователей,
 * используя RequestManager для снижения нагрузки на сервер
 */

import { createUserSearchDebounce } from '../js/debounce-integration.jsi18n.t('auto__if_window_inituserstab_const_originalinituserstab_window_inituserstab_window_inituserstab_async_function_await_originalinituserstab_apply_this_arguments_console_log__e53712')[UsersDebouncePatch] Patching users tab search...i18n.t('auto__settimeout_const_searchinput_document_getelementbyid__43260d')users-search-inputi18n.t('auto__if_searchinput_window_globalrequestmanager_const_listeners_searchinput_eventlisteners_input_searchinput_replacewith_searchinput_clonenode_true_const_newsearchinput_document_getelementbyid__a1c626')users-search-inputi18n.t('auto__newsearchinput_addeventlistener__38f835')input', (e) => {
          const val = e.target.value;
          const searchClear = document.getElementById('users-search-clear');
          
          if (searchClear) {
            searchClear.classList.toggle('d-nonei18n.t('auto__val_window_globalrequestmanager_debounce__63911a')user-search-optimizedi18n.t('auto__async_state_if_window_updateusersearch_window_updateusersearch_val_trim_500_catch_e_console_error__65455b')Search debounce error:i18n.t('auto__e_const_searchclear_document_getelementbyid__6da7e1')users-search-clear');
        if (searchClear) {
          searchClear.onclick = () => {
            newSearchInput.value = '';
            searchClear.classList.add('d-none');
            if (window.updateUserSearch) {
              window.updateUserSearch('');
            }
          };
        }

        console.log('[UsersDebouncePatch] Users tab search patched with RequestManager debouncei18n.t('auto__500_users_tab_if_document_getelementbyid__030b6f')users-search-input')) {
  console.log('[UsersDebouncePatch] Users tab already loaded, applying patch immediately...');
  
  const searchInput = document.getElementById('users-search-input');
  const searchClear = document.getElementById('users-search-cleari18n.t('auto__const_debouncedsearch_createusersearchdebounce_async_query_console_log_usersdebouncepatch_executing_debounced_search_for_query_ui_if_window_updateusersearch_await_window_updateusersearch_query_searchinput_replacewith_searchinput_clonenode_true_const_newsearchinput_document_getelementbyid__872b8e')users-search-input');

  newSearchInput.addEventListener('input', (e) => {
    const val = e.target.value;
    
    if (searchClear) {
      searchClear.classList.toggle('d-none', !val);
    }

    debouncedSearch(val.trim());
  });

  if (searchClear) {
    searchClear.addEventListener('click', () => {
      newSearchInput.value = '';
      searchClear.classList.add('d-none');
      debouncedSearch('');
    });
  }

  console.log('[UsersDebouncePatch] Search debouncing initialized');
}

export {};
