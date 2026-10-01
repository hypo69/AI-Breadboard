/**
 * =============================================================================
 * Process Name: Windows User Directories Tab - Main Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля main.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/~webgui/user_directories_tab/main.js?v=20261001_v1" type="module"></script>
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: windows/api/~webgui/user_directories_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-01 13:04:40
 * =============================================================================
 */

/**
 * user_directories_tab/main.js — Модуль управления пользовательскими директориями и хранилищем
 * AI Breadboard
 */

let state = {
  users: [],
  selectedUserId: null,
  selectedUserName: '',
  currentSubfolder: '',
  searchQuery: '',
  extFilter: 'i18n.t('auto__files_previewfile_null_orphaneddirs_export_async_function_inituserdirectoriestab_const_root_document_getelementbyid__e8943c')user-directories-tab-rooti18n.t('auto__if_root_return_setupeventlisteners_await_refreshdata_function_setupeventlisteners_const_refreshbtn_document_getelementbyid__c0ba79')btn-refresh-user-dirsi18n.t('auto__if_refreshbtn_refreshbtn_onclick_refreshdata_const_searchinput_document_getelementbyid__326985')user-dirs-search-input');
  const searchClear = document.getElementById('user-dirs-search-clear');
  if (searchInput) {
    let timeout = null;
    searchInput.oninput = () => {
      clearTimeout(timeout);
      state.searchQuery = searchInput.value.trim();
      if (searchClear) {
        searchClear.classList.toggle('d-none', !state.searchQuery);
      }
      timeout = setTimeout(() => {
        applyFilters();
      }, 300);
    };
  }

  if (searchClear && searchInput) {
    searchClear.onclick = () => {
      searchInput.value = '';
      state.searchQuery = '';
      searchClear.classList.add('d-nonei18n.t('auto__applyfilters_const_extselect_document_getelementbyid__6b1727')user-dirs-ext-filteri18n.t('auto__if_extselect_extselect_onchange_state_extfilter_extselect_value_if_state_selecteduserid_loaduserfiles_state_selecteduserid_const_subfoldergroup_document_getelementbyid__45a429')subfolder-filter-group');
  if (subfolderGroup) {
    subfolderGroup.addEventListener('click', (e) => {
      const btn = e.target.closest('button[data-subfolder]');
      if (!btn) return;
      subfolderGroup.querySelectorAll('button').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.currentSubfolder = btn.dataset.subfolder || 'i18n.t('auto__if_state_selecteduserid_loaduserfiles_state_selecteduserid_const_openorphanedbtn_document_getelementbyid__aed453')btn-open-orphaned-dirs-modal');
  if (openOrphanedBtn) {
    openOrphanedBtn.onclick = () => openOrphanedModal();
  }

  const refreshOrphanedBtn = document.getElementById('btn-modal-refresh-orphaned');
  if (refreshOrphanedBtn) {
    refreshOrphanedBtn.onclick = () => loadOrphanedDirs();
  }

  const cleanAllOrphanedBtn = document.getElementById('btn-modal-clean-all-orphanedi18n.t('auto__if_cleanallorphanedbtn_cleanallorphanedbtn_onclick_cleanorphaneddirs_const_previewdeletebtn_document_getelementbyid__7f2304')btn-preview-delete-filei18n.t('auto__if_previewdeletebtn_previewdeletebtn_onclick_if_state_previewfile_state_selecteduserid_deletefile_state_selecteduserid_state_previewfile_relative_path_async_function_refreshdata_await_promise_all_loadsummary_loaduserslist_loadorphanedbadge_async_function_loadsummary_try_const_res_await_fetch__42b2e6')/api/admin/user-directories/summary');
    if (!res.ok) return;
    const data = await res.json();
    if (data.status === 'ok' && data.summary) {
      const s = data.summary;
      const elUsers = document.getElementById('metric-total-users');
      const elStorage = document.getElementById('metric-total-storage');
      const elFiles = document.getElementById('metric-total-files');
      const elOrphaned = document.getElementById('metric-orphaned-size');

      if (elUsers) elUsers.textContent = s.total_users || 0;
      if (elStorage) elStorage.textContent = s.total_storage_formatted || '0 B';
      if (elFiles) elFiles.textContent = s.total_files_count || 0;
      if (elOrphaned) elOrphaned.textContent = s.orphaned_formatted || '0 B';
    }
  } catch (err) {
    console.warn(i18n.t('auto___bc2c6d'), err);
  }
}

/**
 * Загрузка бейджа осиротевших каталогов
 */
async function loadOrphanedBadge() {
  try {
    const res = await fetch('/api/admin/user-directories/orphaned');
    if (!res.ok) return;
    const data = await res.json();
    if (data.status === 'ok') {
      const badge = document.getElementById('badge-orphaned-count');
      if (badge) badge.textContent = data.total || 0;
    }
  } catch (err) {
    console.warn(i18n.t('auto___8e3836'), err);
  }
}

/**
 * Загрузка списка пользователей с метриками хранилища
 */
async function loadUsersList() {
  const usersListEl = document.getElementById('user-dirs-users-list');
  const countBadge = document.getElementById('users-badge-count');
  const statusLabel = document.getElementById('user-dirs-status-label');

  try {
    if (statusLabel) statusLabel.textContent = i18n.t('auto___b64271');
    const res = await fetch('/api/admin/user-directories/usersi18n.t('auto__if_res_ok_throw_new_error_http_res_status_const_data_await_res_json_state_users_data_users_if_countbadge_countbadge_textcontent_state_users_length_if_statuslabel_statuslabel_textcontent_state_users_length_renderuserslist_if_state_selecteduserid_state_users_some_u_u_id_state_selecteduserid_selectuser_state_selecteduserid_else_if_state_users_length_0_selectuser_state_users_0_id_catch_err_console_error__fc8d0c')Ошибка загрузки пользователей:', err);
    if (usersListEl) {
      usersListEl.innerHTML = `
        <div class="text-center py-4 text-danger small">
          <i class="bi bi-exclamation-triangle fs-4 d-block mb-1"></i>
          Не удалось загрузить список пользователей: ${err.message}
        </div>
      `;
    }
  }
}

/**
 * Рендеринг списка пользователей в левой колонке
 */
function renderUsersList() {
  const usersListEl = document.getElementById('user-dirs-users-list');
  if (!usersListEl) return;

  const query = state.searchQuery.toLowerCase();
  const filteredUsers = state.users.filter(u => {
    if (!query) return true;
    return (
      (u.name && u.name.toLowerCase().includes(query)) ||
      (u.email && u.email.toLowerCase().includes(query)) ||
      String(u.id).includes(query)
    );
  });

  if (filteredUsers.length === 0) {
    usersListEl.innerHTML = `
      <div class="text-center py-4 text-muted small">
        Пользователи не найдены
      </div>
    `;
    return;
  }

  usersListEl.innerHTML = filteredUsers.map(u => {
    const isSelected = u.id === state.selectedUserId;
    const activeClass = isSelected ? 'active border-primary' : '';
    const roleBadge = u.is_admin
      ? '<span class="badge bg-warning text-dark me-1">admin</span>'
      : '<span class="badge bg-secondary me-1">user</span>';

    const diskWarning = u.quota_percent > 85 ? 'bg-danger' : u.quota_percent > 60 ? 'bg-warning' : 'bg-primary';

    return `
      <a href="javascript:void(0)" 
         class="list-group-item list-group-item-action p-2.5 user-select-item ${activeClass}" 
         data-user-id="${u.id}">
        <div class="d-flex w-100 justify-content-between align-items-center mb-1">
          <div class="d-flex align-items-center gap-1.5 text-truncate">
            <span class="badge bg-dark border text-info" style="font-size: 0.72rem;">#${u.id}</span>
            <strong class="text-truncate small ${isSelected ? 'text-white' : ''}">${escapeHtml(u.name)}</strong>
          </div>
          <div>${roleBadge}</div>
        </div>
        <div class="text-truncate small text-muted mb-1.5" style="font-size: 0.76rem;">
          ${escapeHtml(u.email || '-')}
        </div>
        <div class="d-flex justify-content-between align-items-center small mb-1" style="font-size: 0.74rem;">
          <span class="text-muted"><i class="bi bi-files me-1i18n.t('auto__i_u_files_count_span_span_class__89a3b3')fw-semibold text-info">${u.size_formatted}</span>
        </div>
        <div class="progress" style="height: 4px;" title=i18n.t('auto__u_quota_percent__a6f5f2')>
          <div class="progress-bar ${diskWarning}" role="progressbar" style="width: ${u.quota_percent}%;"></div>
        </div>
      </a>
    `;
  }).join('i18n.t('auto__userslistel_queryselectorall__1ddc83').user-select-itemi18n.t('auto__foreach_item_item_onclick_const_uid_parseint_item_dataset_userid_10_selectuser_uid_function_selectuser_userid_state_selecteduserid_userid_const_user_state_users_find_u_u_id_userid_state_selectedusername_user_user_name_userid_const_userslistel_document_getelementbyid__490665')user-dirs-users-list');
  if (usersListEl) {
    usersListEl.querySelectorAll('.user-select-item').forEach(item => {
      const uid = parseInt(item.dataset.userId, 10);
      item.classList.toggle('active', uid === userId);
      item.classList.toggle('border-primaryi18n.t('auto__uid_userid_const_titleel_document_getelementbyid__f41549')explorer-user-title');
  const pathBadge = document.getElementById('explorer-user-path-badge');
  if (titleEl) {
    titleEl.innerHTML = `<i class="bi bi-folder-fill text-warning me-1"></i> Хранилище: <strong>${escapeHtml(state.selectedUserName)}</strong> (#${userId})`;
  }
  if (pathBadge && user) {
    pathBadge.classList.remove('d-nonei18n.t('auto__pathbadge_textcontent_data_users_userid_loaduserfiles_userid_async_function_loaduserfiles_userid_const_tbody_document_getelementbyid__45a100')user-files-table-body');
  const footerStats = document.getElementById('explorer-footer-stats');
  const footerQuota = document.getElementById('explorer-footer-quota');

  if (tbody) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" class="text-center py-4 text-muted">
          <div class="spinner-border spinner-border-sm text-primary me-2"></div>
          Загрузка файлов пользователя...
        </td>
      </tr>
    `;
  }

  try {
    let url = `/api/admin/user-directories/users/${userId}/tree?`;
    const params = new URLSearchParams();
    if (state.currentSubfolder) params.append('subfolder', state.currentSubfolder);
    if (state.searchQuery) params.append('q', state.searchQuery);
    if (state.extFilter) params.append('extensioni18n.t('auto__state_extfilter_const_res_await_fetch_url_params_tostring_if_res_ok_throw_new_error_http_res_status_const_data_await_res_json_state_files_data_items_if_footerstats_footerstats_innerhtml_strong_data_total_items_0_strong_strong_data_total_size_formatted__48eeae')0 Bi18n.t('auto__strong_const_user_state_users_find_u_u_id_userid_if_footerquota_user_footerquota_innerhtml_strong_user_size_formatted_user_quota_formatted_strong_user_quota_percent_renderuserfilestable_catch_err_console_error__a46ea0')Ошибка загрузки файлов:', err);
    if (tbody) {
      tbody.innerHTML = `
        <tr>
          <td colspan="6" class="text-center py-4 text-danger small">
            Ошибка загрузки файлов: ${err.message}
          </td>
        </tr>
      `;
    }
  }
}

/**
 * Рендеринг таблицы файлов пользователя
 */
function renderUserFilesTable() {
  const tbody = document.getElementById('user-files-table-body');
  if (!tbody) return;

  if (state.files.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" class="text-center py-5 text-muted small">
          <i class="bi bi-inbox fs-3 d-block mb-1 text-secondary"></i>
          В выбранном разделе нет файлов
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = state.files.map(f => {
    const isDir = f.is_dir;
    const icon = isDir
      ? '<i class="bi bi-folder-fill text-warning fs-6"></i>'
      : getFileIcon(f.extension);

    const subfolderBadge = f.subfolder === 'root'
      ? '<span class="badge bg-secondary-subtle text-secondary border">root</span>'
      : `<span class="badge bg-info-subtle text-info border border-info-subtle">${escapeHtml(f.subfolder)}</span>`;

    return `
      <tr>
        <td class="text-center">${icon}</td>
        <td>
          <div class="fw-semibold text-truncate text-white" style="max-width: 260px;" title="${escapeHtml(f.relative_path)}">
            ${escapeHtml(f.name)}
          </div>
          <div class="text-muted small font-monospace" style="font-size: 0.72rem;">
            ${escapeHtml(f.relative_path)}
          </div>
        </td>
        <td class="text-center">${subfolderBadge}</td>
        <td class="text-center font-monospace small">${f.size_formatted}</td>
        <td class="small text-muted font-monospace" style="font-size: 0.76rem;">${f.modified_formatted}</td>
        <td class="text-center">
          <div class="btn-group btn-group-sm" role="group">
            ${!isDir ? `
              <button class="btn btn-xs btn-outline-info btn-preview-file" 
                      data-path="${escapeHtml(f.relative_path)}" 
                      title=i18n.t('auto___fbf997')>
                <i class="bi bi-eye"></i>
              </button>
              <a href="/api/admin/user-directories/users/${state.selectedUserId}/file/download?path=${encodeURIComponent(f.relative_path)}" 
                 class="btn btn-xs btn-outline-success" 
                 title=i18n.t('auto___b42155') 
                 download>
                <i class="bi bi-download"></i>
              </a>
            ` : ''}
            <button class="btn btn-xs btn-outline-danger btn-delete-file" 
                    data-path="${escapeHtml(f.relative_path)}" 
                    data-is-dir="${isDir}"
                    title=i18n.t('auto___86ea33')>
              <i class="bi bi-trash3"></i>
            </button>
          </div>
        </td>
      </tr>
    `;
  }).join('i18n.t('auto__tbody_queryselectorall__7df08d').btn-preview-filei18n.t('auto__foreach_btn_btn_onclick_const_path_btn_dataset_path_openfilepreview_state_selecteduserid_path_tbody_queryselectorall__9a43cc').btn-delete-file').forEach(btn => {
    btn.onclick = () => {
      const path = btn.dataset.path;
      const isDir = btn.dataset.isDir === 'true';
      const promptText = isDir
        ? `Вы уверены, что хотите удалить директорию "${path}i18n.t('auto___b30093')${path}"?`;
      if (confirm(promptText)) {
        deleteFile(state.selectedUserId, path);
      }
    };
  });
}

/**
 * Иконка по расширению файла
 */
function getFileIcon(ext) {
  const e = (ext || '').toLowerCase();
  switch (e) {
    case 'pdf':
      return '<i class="bi bi-file-earmark-pdf-fill text-danger fs-6"></i>';
    case 'txt':
    case 'md':
    case 'log':
      return '<i class="bi bi-file-earmark-text-fill text-info fs-6"></i>';
    case 'json':
    case 'xml':
    case 'yaml':
    case 'yml':
      return '<i class="bi bi-file-earmark-code-fill text-warning fs-6"></i>';
    case 'csv':
    case 'tsv':
    case 'xlsx':
      return '<i class="bi bi-file-earmark-spreadsheet-fill text-success fs-6"></i>';
    case 'png':
    case 'jpg':
    case 'jpeg':
    case 'webp':
    case 'gif':
    case 'svg':
      return '<i class="bi bi-file-earmark-image-fill text-primary fs-6"></i>';
    case 'mp3':
    case 'wav':
    case 'ogg':
      return '<i class="bi bi-file-earmark-music-fill text-purple fs-6"></i>';
    case 'py':
    case 'js':
    case 'sh':
    case 'ps1':
      return '<i class="bi bi-filetype-py text-warning fs-6"></i>';
    default:
      return '<i class="bi bi-file-earmark-fill text-secondary fs-6"></i>i18n.t('auto__async_function_openfilepreview_userid_path_const_modalel_document_getelementbyid__d13cfe')modal-file-preview');
  if (!modalEl) return;

  const titleEl = document.getElementById('modal-file-preview-title');
  const pathEl = document.getElementById('preview-file-path');
  const sizeEl = document.getElementById('preview-file-size');
  const typeEl = document.getElementById('preview-file-type');
  const contentWrapper = document.getElementById('preview-content-wrapper');
  const downloadLink = document.getElementById('btn-preview-download-filei18n.t('auto__if_titleel_titleel_textcontent_path_split__bb8acf')/').pop()}`;
  if (pathEl) pathEl.textContent = `data/users/${userId}/${path}`;
  if (sizeEl) sizeEl.textContent = '...';
  if (typeEl) typeEl.textContent = '...';
  if (contentWrapper) {
    contentWrapper.innerHTML = `
      <div class="text-center py-4 text-muted">
        <div class="spinner-border spinner-border-sm text-primary me-2i18n.t('auto__div_div_if_downloadlink_downloadlink_href_api_admin_user_directories_users_userid_file_download_path_encodeuricomponent_path_const_modal_bootstrap_modal_getorcreateinstance_modalel_modal_show_try_const_res_await_fetch_api_admin_user_directories_users_userid_file_preview_path_encodeuricomponent_path_if_res_ok_throw_new_error_http_res_status_const_data_await_res_json_state_previewfile_data_if_sizeel_sizeel_textcontent_data_size_formatted_if_typeel_typeel_textcontent_data_mime_type_data_extension_if_contentwrapper_if_data_is_image_contentwrapper_innerhtml_div_class__1ed0ec')text-center p-2">
            <img src="${data.content}" class="img-fluid rounded border border-secondary shadow" style="max-height: 400px; object-fit: contain;">
          </div>
        `;
      } else {
        contentWrapper.textContent = data.content || i18n.t('auto___dd0cba');
      }
    }
  } catch (err) {
    console.error(i18n.t('auto___8aaf74'), err);
    if (contentWrapper) {
      contentWrapper.innerHTML = `<div class="text-danger p-3">Ошибка загрузки содержимого: ${err.message}</div>`;
    }
  }
}

/**
 * Удаление файла или папки
 */
async function deleteFile(userId, path) {
  try {
    const res = await fetch(`/api/admin/user-directories/users/${userId}/file?path=${encodeURIComponent(path)}`, {
      method: 'DELETE',
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `HTTP ${res.status}`);
    }

    showAlert(`Файл "${path}" успешно удален`, 'successi18n.t('auto__const_previewmodalel_document_getelementbyid__ec28d1')modal-file-previewi18n.t('auto__if_previewmodalel_const_modal_bootstrap_modal_getinstance_previewmodalel_if_modal_modal_hide_await_loaduserfiles_userid_await_loadsummary_await_loaduserslist_catch_err_console_error__a11f5a')Ошибка удаления файла:i18n.t('auto__err_showalert_err_message__c31ef1')dangeri18n.t('auto__async_function_openorphanedmodal_const_modalel_document_getelementbyid__20a887')modal-orphaned-user-dirsi18n.t('auto__if_modalel_return_const_modal_bootstrap_modal_getorcreateinstance_modalel_modal_show_await_loadorphaneddirs_async_function_loadorphaneddirs_const_tbody_document_getelementbyid__f70453')modal-orphaned-dirs-tbody');
  const countEl = document.getElementById('modal-orphaned-count');
  const sizeEl = document.getElementById('modal-orphaned-size');
  const filesEl = document.getElementById('modal-orphaned-files');

  if (tbody) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" class="text-center py-4 text-muted">
          <div class="spinner-border spinner-border-sm text-warning me-2"></div> Сканирование...
        </td>
      </tr>
    `;
  }

  try {
    const res = await fetch('/api/admin/user-directories/orphaned');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    state.orphanedDirs = data.orphaned_dirs || [];

    if (countEl) countEl.textContent = data.total || 0;
    if (sizeEl) sizeEl.textContent = data.total_size_formatted || '0 B';
    if (filesEl) filesEl.textContent = data.total_files || 0;

    const badge = document.getElementById('badge-orphaned-count');
    if (badge) badge.textContent = data.total || 0;

    renderOrphanedDirsTable();
  } catch (err) {
    console.error(i18n.t('auto___136886'), err);
    if (tbody) {
      tbody.innerHTML = `
        <tr>
          <td colspan="6" class="text-center py-3 text-danger small">
            Ошибка сканирования: ${err.message}
          </td>
        </tr>
      `;
    }
  }
}

/**
 * Рендеринг таблицы осиротевших каталогов
 */
function renderOrphanedDirsTable() {
  const tbody = document.getElementById('modal-orphaned-dirs-tbody');
  if (!tbody) return;

  if (state.orphanedDirs.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" class="text-center py-4 text-success small">
          <i class="bi bi-check-circle fs-4 d-block mb-1i18n.t('auto__i_td_tr_return_tbody_innerhtml_state_orphaneddirs_map_d_tr_td_div_class__7dbeba')fw-bold font-monospace text-warning small">${escapeHtml(d.dir_name)}</div>
        <div class="text-muted small" style="font-size: 0.72rem;">${escapeHtml(d.full_path)}</div>
      </td>
      <td><span class="badge bg-secondary-subtle text-secondary border">${escapeHtml(d.reason)}</span></td>
      <td class="text-center font-monospace">${d.files_count}</td>
      <td class="text-center font-monospace small">${d.size_formatted}</td>
      <td class="small text-muted font-monospace" style="font-size: 0.76rem;">${d.modified_formatted}</td>
      <td class="text-center">
        <button class="btn btn-xs btn-outline-danger btn-clean-single-orphaned" 
                data-dir="${escapeHtml(d.dir_name)}" 
                title=i18n.t('auto___20d14d')>
          <i class="bi bi-trash3"></i>
        </button>
      </td>
    </tr>
  `).join('');

  tbody.querySelectorAll('.btn-clean-single-orphaned').forEach(btn => {
    btn.onclick = () => {
      const dirName = btn.dataset.dir;
      if (confirm(`Удалить осиротевший каталог "${dirName}"?`)) {
        cleanOrphanedDirs([dirName]);
      }
    };
  });
}

/**
 * Очистка осиротевших каталогов (конкретных или всех)
 */
async function cleanOrphanedDirs(dirsList = null) {
  if (!dirsList && !confirm(i18n.t('auto___559e29'))) {
    return;
  }

  try {
    const payload = dirsList ? { dirs: dirsList } : {};
    const res = await fetch('/api/admin/user-directories/orphaned/clean', {
      method: 'POST',
      headers: { 'Content-Type': 'application/jsoni18n.t('auto__body_json_stringify_payload_if_res_ok_throw_new_error_http_res_status_const_data_await_res_json_showalert_data_deleted_count_data_freed_formatted__cd7680')success');

    await loadOrphanedDirs();
    await loadSummary();
  } catch (err) {
    console.error(i18n.t('auto___b56cfb'), err);
    showAlert(`Ошибка очистки каталогов: ${err.message}`, 'dangeri18n.t('auto__function_applyfilters_renderuserslist_if_state_selecteduserid_loaduserfiles_state_selecteduserid_alert_function_showalert_message_type__a209e0')info') {
  const alertBox = document.getElementById('user-dirs-alert-box');
  const alertMsg = document.getElementById('user-dirs-alert-message');
  if (!alertBox || !alertMsg) return;

  alertBox.className = `alert alert-${type} alert-dismissible fade show mb-3 shadow-sm`;
  alertMsg.textContent = message;
  alertBox.classList.remove('d-none');

  setTimeout(() => {
    alertBox.classList.add('d-nonei18n.t('auto__6000_html_function_escapehtml_text_if_text_return_4564a9')';
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;',
  };
  return String(text).replace(/[&<>"']/g, m => map[m]);
}

// Экспорт по умолчанию
export default initUserDirectoriesTab;
