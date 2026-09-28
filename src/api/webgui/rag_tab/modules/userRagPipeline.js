/**
 * =============================================================================
 * Process Name: Workspace Multi-RAG Pipeline and Search
 * =============================================================================
 * Description:
 *   Handles workspace storage file checklist, cleaning and TF-IDF build
 *   pipeline, semantic search, and quick upload to user storage.
 *
 * File: userRagPipeline.js
 * Project: AI Breadboard
 * Module: RAGTab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * =============================================================================
 */

import { formatBytes, escapeHtml } from './utils.js';
import { getActiveUserRagId, loadUserRags, selectUserRag } from './userRagCollections.js';

/**
 * Fetch files from user storage and render checkbox selection list.
 *
 * @param {string[]} attachedFiles - Array of filenames currently attached to this collection.
 * @returns {Promise<void>}
 */
export async function loadUserStorageFiles(attachedFiles) {
  const checklistContainer = document.getElementById('user-rag-files-checklist');
  if (!checklistContainer) return;

  try {
    const res = await fetch('/api/user/files?subfolder=files');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const files = data.files || [];

    if (files.length === 0) {
      checklistContainer.innerHTML = `
        <div class="text-muted small p-2 text-centeri18n.t('auto__br_div_return_checklistcontainer_innerhtml_files_map_f_const_ischecked_attachedfiles_length_0_attachedfiles_includes_f_name_return_label_class__7df445')d-flex align-items-center justify-content-between p-1 px-2 rounded hover-bg border-bottom border-light-subtle small cursor-pointer">
          <div class="d-flex align-items-center gap-2">
            <input class="form-check-input mt-0" type="checkbox" value="${escapeHtml(f.name)}" ${isChecked ? 'checked' : ''}>
            <span class="text-truncate font-monospace" style="max-width: 280px;">${escapeHtml(f.name)}</span>
          </div>
          <span class="text-muted small">${formatBytes(f.size_bytes)}</span>
        </label>
      `;
    }).join('');
  } catch (err) {
    checklistContainer.innerHTML = `<div class="alert alert-danger p-2 small mb-0">Ошибка списка файлов: ${escapeHtml(err.message)}</div>`;
  }
}

/**
 * Build active collection index through cleaner and TF-IDF pipeline.
 *
 * @returns {Promise<void>}
 */
export async function buildActiveUserRag() {
  const activeUserRagId = getActiveUserRagId();
  if (!activeUserRagId) return;

  const btn = document.getElementById('btn-build-active-rag');
  const statusAlert = document.getElementById('user-rag-build-status-alert');
  const checkboxes = document.querySelectorAll('#user-rag-files-checklist input[type="checkbox"]:checked');
  const selectedFiles = Array.from(checkboxes).map(cb => cb.value);

  if (btn) btn.disabled = true;
  if (statusAlert) {
    statusAlert.className = 'alert alert-info p-2 small mt-2 mb-0 d-block';
    statusAlert.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Выполняется очистка (rag_cleaner) и индексация документов...';
  }

  try {
    const res = await fetch(`/api/user/rags/${encodeURIComponent(activeUserRagId)}/build`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        files: selectedFiles.length > 0 ? selectedFiles : null,
        provider: 'local_tfidf'
      })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);

    if (statusAlert) {
      statusAlert.className = 'alert alert-success p-2 small mt-2 mb-0 d-blocki18n.t('auto__statusalert_innerhtml_strong_data_chunks_count_strong_strong_data_processed_files_length_0_strong_await_loaduserrags_catch_err_if_statusalert_statusalert_classname__c48ae8')alert alert-danger p-2 small mt-2 mb-0 d-blocki18n.t('auto__statusalert_textcontent_rag_err_message_finally_if_btn_btn_disabled_false_perform_semantic_search_in_the_active_workspace_collection_returns_promise_void_export_async_function_executeactiveuserragsearch_const_activeuserragid_getactiveuserragid_if_activeuserragid_return_const_queryinput_document_getelementbyid__0b1612')active-rag-search-query');
  const resultsContainer = document.getElementById('active-rag-search-results');
  const btn = document.getElementById('btn-active-rag-search');
  const query = queryInput?.value.trim();

  if (!query) return;
  if (btn) btn.disabled = true;
  if (resultsContainer) {
    resultsContainer.innerHTML = '<div class="text-center text-muted small py-3"><span class="spinner-border spinner-border-sm me-1"></span>Поиск...</div>';
  }

  try {
    const res = await fetch(`/api/user/rags/${encodeURIComponent(activeUserRagId)}/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: query,
        top_k: 5,
        min_score: 0.0
      })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);

    const results = data.results || [];
    if (results.length === 0) {
      resultsContainer.innerHTML = '<div class="text-center text-muted small py-3">Ничего не найдено по данному запросу.</div>';
      return;
    }

    resultsContainer.innerHTML = results.map((item) => {
      const scorePercent = Math.round((item.score || 0) * 100);
      return `
        <div class="card mb-2 border border-secondary-subtle bg-body">
          <div class="card-header py-1 px-2 d-flex justify-content-between align-items-center bg-body-tertiary">
            <span class="small fw-semibold text-truncate" style="max-width: 70%;">
              <i class="bi bi-file-earmark-text text-primary me-1"></i> ${escapeHtml(item.source_file || '')}
            </span>
            <span class="badge bg-primary-subtle text-primary border border-primary-subtle">${scorePercent}% match</span>
          </div>
          <div class="card-body p-2 small">
            <div class="text-secondary font-monospace" style="font-size: 0.8rem; white-space: pre-wrap;">${escapeHtml(item.text)}</div>
          </div>
        </div>
      `;
    }).join('');
  } catch (err) {
    if (resultsContainer) {
      resultsContainer.innerHTML = `<div class="alert alert-danger p-2 small mb-0">Ошибка поиска: ${escapeHtml(err.message)}</div>`;
    }
  } finally {
    if (btn) btn.disabled = false;
  }
}

/**
 * Handle quick file upload directly into user workspace storage.
 *
 * @param {Event} event - Input change event.
 * @returns {Promise<void>}
 */
export async function handleQuickUploadToUserStorage(event) {
  const files = event.target.files;
  if (!files || files.length === 0) return;

  const statusAlert = document.getElementById('user-rag-build-status-alert');
  if (statusAlert) {
    statusAlert.className = 'alert alert-info p-2 small mt-2 mb-0 d-block';
    statusAlert.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>Загрузка ${files.length} файл(ов)...`;
  }

  try {
    for (const file of files) {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('subfolder', 'files');

      const res = await fetch('/api/user/files/upload', {
        method: 'POSTi18n.t('auto__body_formdata_if_res_ok_throw_new_error_file_name_if_statusalert_statusalert_classname__49419c')alert alert-success p-2 small mt-2 mb-0 d-blocki18n.t('auto__statusalert_innerhtml_strong_files_length_strong_const_activeuserragid_getactiveuserragid_if_activeuserragid_selectuserrag_activeuserragid_catch_err_if_statusalert_statusalert_classname__77e65c')alert alert-danger p-2 small mt-2 mb-0 d-block';
      statusAlert.textContent = err.message;
    }
  } finally {
    event.target.value = '';
  }
}

/**
 * Synchronize Google Docs & Drive files directly into the active collection and build index.
 *
 * @returns {Promise<void>}
 */
export async function syncGoogleDocsIntoActiveRag() {
  const activeUserRagId = getActiveUserRagId();
  if (!activeUserRagId) {
    window.showToast?.(i18n.t('auto__rag__751889'), 'warning') || alert(i18n.t('auto__rag__751889'));
    return;
  }

  const queryInput = document.getElementById('import-gdocs-query');
  const accountInput = document.getElementById('import-gdocs-account');
  const statusAlert = document.getElementById('import-gdocs-status-alert');
  const btn = document.getElementById('btn-confirm-import-gdocs');

  const query = queryInput?.value.trim() || "mimeType = 'application/vnd.google-apps.document' and trashed = false";
  const accountName = accountInput?.value.trim() || undefined;

  if (btn) btn.disabled = true;
  if (statusAlert) {
    statusAlert.className = 'alert alert-info py-2 small mb-0 d-block';
    statusAlert.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Экспорт Google Docs и построение RAG индекса...';
  }

  try {
    const res = await fetch(`/api/user/rags/${encodeURIComponent(activeUserRagId)}/sync-google-docs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: query,
        account_name: accountName
      })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);

    if (statusAlert) {
      statusAlert.className = 'alert alert-success py-2 small mb-0 d-blocki18n.t('auto__statusalert_innerhtml_strong_data_downloaded_files_length_0_strong_strong_data_chunks_count_0_strong_await_loaduserrags_await_selectuserrag_activeuserragid_settimeout_const_modalel_document_getelementbyid__3305a5')modal-import-gdocs');
      if (modalEl && window.bootstrap?.Modal) {
        const modal = bootstrap.Modal.getInstance(modalEl);
        if (modal) modal.hide();
      }
    }, 1500);

  } catch (err) {
    if (statusAlert) {
      statusAlert.className = 'alert alert-danger py-2 small mb-0 d-block';
      statusAlert.textContent = `Ошибка синхронизации: ${err.message}`;
    }
  } finally {
    if (btn) btn.disabled = false;
  }
}

