/**
 * =============================================================================
 * Process Name: Windows Modules - Userragcollections Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля userRagCollections.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/~webgui/rag_tab/modules/userRagCollections.js?v=20261001_v1" type="module"></script>
 *
 *   JavaScript Import:
 *     import { getActiveUserRagId, setActiveUserRagId, renderUserRagsList } from '/windows/api/~webgui/rag_tab/modules/userRagCollections.js';
 *
 * File: userRagCollections.js
 * Project: ai-breadboard
 * Package: windows/api/~webgui/rag_tab/modules
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-01 13:04:40
 * =============================================================================
 */

import { escapeHtml } from './utils.js';
import { loadUserStorageFiles } from './userRagPipeline.js';

let activeUserRagId = null;
let userCollections = [];

/**
 * Get the currently active collection ID.
 *
 * @returns {string|null} Active RAG ID or null.
 */
export function getActiveUserRagId() {
  return activeUserRagId;
}

/**
 * Set the active collection ID.
 *
 * @param {string|null} id - Target collection ID.
 */
export function setActiveUserRagId(id) {
  activeUserRagId = id;
}

/**
 * Fetch all user workspace RAG collections and render sidebar list.
 *
 * @returns {Promise<void>}
 */
export async function loadUserRags() {
  const listContainer = document.getElementById('user-rags-list-container');
  if (!listContainer) return;

  try {
    const res = await fetch('/api/user/rags');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    userCollections = data.collections || [];
    renderUserRagsList(userCollections);

    if (userCollections.length > 0) {
      if (!activeUserRagId || !userCollections.some(c => c.id === activeUserRagId)) {
        selectUserRag(userCollections[0].id);
      } else {
        selectUserRag(activeUserRagId);
      }
    } else {
      activeUserRagId = null;
      showUserRagEmptyState();
    }
  } catch (err) {
    listContainer.innerHTML = `<div class="alert alert-danger p-2 small mb-0">Ошибка загрузки коллекций: ${escapeHtml(err.message)}</div>`;
  }
}

/**
 * Render the collection cards in the left sidebar.
 *
 * @param {Array<object>} collections - List of collection summary objects.
 */
export function renderUserRagsList(collections) {
  const listContainer = document.getElementById('user-rags-list-container');
  if (!listContainer) return;

  if (collections.length === 0) {
    listContainer.innerHTML = `
      <div class="text-center text-muted py-4 small">
        <i class="bi bi-folder-x fs-3 d-block mb-1 opacity-50"></i>
        Нет созданных коллекций.<br>Нажмите «+ Создать» выше.
      </div>
    `;
    return;
  }

  listContainer.innerHTML = collections.map(col => {
    const isActive = col.id === activeUserRagId;
    const statusBadgeClass = col.status === 'indexed'
      ? 'bg-success'
      : (col.status === 'cleaning' ? 'bg-warning text-dark' : (col.status === 'error' ? 'bg-danger' : 'bg-secondary'));

    return `
      <div class="card p-2 cursor-pointer user-rag-item ${isActive ? 'border-primary bg-primary-subtle' : 'border-secondary-subtle bg-body-tertiary'}"
           data-rag-id="${escapeHtml(col.id)}" style="cursor: pointer; transition: all 0.15s ease-in-out;">
        <div class="d-flex justify-content-between align-items-center mb-1">
          <strong class="text-truncate small" style="max-width: 140px;">${escapeHtml(col.name || col.id)}</strong>
          <span class="badge ${statusBadgeClass} small" style="font-size: 0.7rem;">${escapeHtml(col.status || 'created')}</span>
        </div>
        <div class="d-flex justify-content-between align-items-center small text-muted" style="font-size: 0.75rem;">
          <span><i class="bi bi-diagram-3 me-1i18n.t('auto__i_col_total_chunks_0_span_span_i_class__144614')bi bi-file-earmark me-1"></i>${(col.files || []).length} файлов</span>
        </div>
      </div>
    `;
  }).join('');

  listContainer.querySelectorAll('.user-rag-item').forEach(el => {
    el.addEventListener('click', () => {
      const ragId = el.getAttribute('data-rag-id');
      if (ragId) selectUserRag(ragId);
    });
  });
}

/**
 * Display placeholder empty state when no collection is selected.
 */
export function showUserRagEmptyState() {
  const emptyState = document.getElementById('user-rag-empty-state');
  const detailContainer = document.getElementById('user-rag-detail-container');
  if (emptyState) emptyState.classList.remove('d-none');
  if (detailContainer) detailContainer.classList.add('d-none');
}

/**
 * Select a workspace collection and load its metadata and file checklist.
 *
 * @param {string} ragId - ID of the collection to select.
 * @returns {Promise<void>}
 */
export async function selectUserRag(ragId) {
  activeUserRagId = ragId;
  const emptyState = document.getElementById('user-rag-empty-state');
  const detailContainer = document.getElementById('user-rag-detail-container');
  if (emptyState) emptyState.classList.add('d-none');
  if (detailContainer) detailContainer.classList.remove('d-none');

  document.querySelectorAll('.user-rag-item').forEach(el => {
    if (el.getAttribute('data-rag-id') === ragId) {
      el.classList.add('border-primary', 'bg-primary-subtle');
      el.classList.remove('border-secondary-subtle', 'bg-body-tertiary');
    } else {
      el.classList.remove('border-primary', 'bg-primary-subtle');
      el.classList.add('border-secondary-subtle', 'bg-body-tertiary');
    }
  });

  try {
    const res = await fetch(`/api/user/rags/${encodeURIComponent(ragId)}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const col = data.collection;

    const titleEl = document.getElementById('active-rag-title');
    const descEl = document.getElementById('active-rag-desc');
    const statusBadge = document.getElementById('active-rag-status-badge');
    const chunksEl = document.getElementById('active-rag-stat-chunks');
    const filesEl = document.getElementById('active-rag-stat-files');
    const updatedEl = document.getElementById('active-rag-stat-updated');

    if (titleEl) titleEl.textContent = col.name || col.id;
    if (descEl) descEl.textContent = col.description || i18n.t('auto___9852df');
    if (statusBadge) {
      statusBadge.textContent = col.status || 'created';
      statusBadge.className = `badge ${col.status === 'indexed' ? 'bg-success' : (col.status === 'cleaning' ? 'bg-warning text-dark' : (col.status === 'error' ? 'bg-danger' : 'bg-secondary'))}`;
    }
    if (chunksEl) chunksEl.textContent = col.total_chunks || 0;
    if (filesEl) filesEl.textContent = (col.files || []).length;
    if (updatedEl) {
      updatedEl.textContent = col.updated_at ? new Date(col.updated_at * 1000).toLocaleString() : '—';
    }

    await loadUserStorageFiles(col.files || []);
    await loadRagEntries(ragId);
  } catch (err) {
    console.error('Failed to load user RAG details:', err);
  }
}

/**
 * Fetch and render chunk/QA entries for the active collection.
 *
 * @param {string} ragId - Collection identifier.
 * @param {string} query - Optional filter query.
 * @returns {Promise<void>}
 */
export async function loadRagEntries(ragId = activeUserRagId, query = '') {
  const container = document.getElementById('user-rag-entries-container');
  if (!container || !ragId) return;

  container.innerHTML = '<div class="text-center text-muted small py-2"><div class="spinner-border spinner-border-sm text-primary me-1"></div>Загрузка записей...</div>';

  try {
    const url = `/api/user/rags/${encodeURIComponent(ragId)}/entries?q=${encodeURIComponent(query)}&limit=100`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderRagEntries(data.entries || [], data.total || 0);
  } catch (err) {
    container.innerHTML = `<div class="alert alert-danger p-2 small mb-0">Ошибка загрузки записей: ${escapeHtml(err.message)}</div>`;
  }
}

/**
 * Render entries inside the collection container.
 *
 * @param {Array<object>} entries - List of chunk/QA items.
 * @param {number} total - Total entries count.
 */
export function renderRagEntries(entries, total) {
  const container = document.getElementById('user-rag-entries-container');
  if (!container) return;

  if (!entries || entries.length === 0) {
    container.innerHTML = `
      <div class="text-center text-muted py-3 small">
        <i class="bi bi-chat-left-dots fs-4 d-block mb-1 opacity-50"></i>
        В этой коллекции пока нет записей.<br>
        Нажмите «+ Добавить Q&A» или соберите RAG из файлов выше.
      </div>
    `;
    return;
  }

  container.innerHTML = entries.map((entry, idx) => {
    const chunkId = entry.chunk_id || `chunk_${idx}`;
    const docType = entry.doc_type || 'chunk';
    const isQa = docType === 'qa' || entry.meta?.is_qa;
    const badgeClass = isQa ? 'bg-primary' : 'bg-info text-dark';
    const badgeLabel = isQa ? 'Q&A' : (entry.source_file || i18n.t('auto___94b8df'));

    let displayContent = entry.content || '';
    let questionText = entry.meta?.question || '';
    let answerText = entry.meta?.answer || '';

    if (!questionText && displayContent.includes(i18n.t('auto___9bf735')) && displayContent.includes(i18n.t('auto___fa5ebc'))) {
      const parts = displayContent.split(i18n.t('auto__n__01e1c0'));
      questionText = parts[0].replace(i18n.t('auto___9bf735'), '').trim();
      answerText = (parts[1] || '').trim();
    }

    return `
      <div class="card p-2 border border-secondary-subtle bg-body-tertiary position-relative rag-entry-card" data-chunk-id="${escapeHtml(chunkId)}">
        <div class="d-flex justify-content-between align-items-start mb-1">
          <div class="d-flex align-items-center gap-1 flex-wrap">
            <span class="badge ${badgeClass} small" style="font-size: 0.7rem;">${escapeHtml(badgeLabel)}</span>
            <small class="text-muted font-monospace" style="font-size: 0.72rem;">#${escapeHtml(chunkId)}</small>
          </div>
          <button class="btn btn-outline-danger btn-sm py-0 px-2 rounded-pill btn-delete-entry" data-chunk-id="${escapeHtml(chunkId)}" title=i18n.t('auto__rag_a7f90e')>
            <i class="bi bi-trash"></i>
          </button>
        </div>
        ${questionText ? `
          <div class="small fw-bold text-primary mb-1"><i class="bi bi-question-circle me-1"></i>${escapeHtml(questionText)}</div>
          <div class="small text-secondary font-monospace bg-body p-2 rounded border" style="white-space: pre-wrap; font-size: 0.78rem;">${escapeHtml(answerText || displayContent)}</div>
        ` : `
          <div class="small text-secondary font-monospace bg-body p-2 rounded border" style="white-space: pre-wrap; font-size: 0.78rem;">${escapeHtml(displayContent)}</div>
        `}
      </div>
    `;
  }).join('');

  container.querySelectorAll('.btn-delete-entry').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const chunkId = btn.getAttribute('data-chunk-id');
      if (chunkId) deleteRagEntry(chunkId);
    });
  });
}

/**
 * Add a new custom Q&A pair entry to the active collection.
 *
 * @returns {Promise<void>}
 */
export async function addQaEntry() {
  if (!activeUserRagId) {
    window.showToast?.(i18n.t('auto__rag__0503f8'), 'warning') || alert(i18n.t('auto__rag__0503f8'));
    return;
  }

  const qInput = document.getElementById('new-qa-question');
  const aInput = document.getElementById('new-qa-answer');
  const btn = document.getElementById('btn-confirm-add-qa');

  const question = qInput?.value.trim() || '';
  const answer = aInput?.value.trim() || '';

  if (!answer) {
    window.showToast?.(i18n.t('auto___5acaf9'), 'warning') || alert(i18n.t('auto___5acaf9'));
    return;
  }

  if (btn) btn.disabled = true;
  try {
    const res = await fetch(`/api/user/rags/${encodeURIComponent(activeUserRagId)}/entries`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, answer })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);

    const modalEl = document.getElementById('modal-add-qa-entry');
    if (modalEl && window.bootstrap?.Modal) {
      const modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
      modal.hide();
    }

    if (qInput) qInput.value = '';
    if (aInput) aInput.value = '';

    window.showToast?.(i18n.t('auto_q_a__a800e6'), 'successi18n.t('auto__await_selectuserrag_activeuserragid_await_loaduserrags_catch_err_window_showtoast_q_a_err_message__b8d668')dangeri18n.t('auto__alert_q_a_err_message_finally_if_btn_btn_disabled_false_delete_a_specific_chunk_qa_entry_from_the_active_collection_param_string_chunkid_chunk_identifier_returns_promise_void_export_async_function_deleteragentry_chunkid_if_activeuserragid_chunkid_return_const_confirmed_confirm_chunkid_if_confirmed_return_try_const_res_await_fetch_api_user_rags_encodeuricomponent_activeuserragid_entries_encodeuricomponent_chunkid_method__697e46')DELETE'
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    window.showToast?.(i18n.t('auto___6a5625'), 'successi18n.t('auto__await_selectuserrag_activeuserragid_await_loaduserrags_catch_err_window_showtoast_err_message__ed65ff')dangeri18n.t('auto__alert_err_message_create_a_new_user_workspace_rag_collection_via_api_returns_promise_void_export_async_function_createuserrag_const_nameinput_document_getelementbyid__850637')new-rag-name');
  const descInput = document.getElementById('new-rag-desc');
  const minChunkInput = document.getElementById('new-rag-min-chunk');
  const maxChunkInput = document.getElementById('new-rag-max-chunk');
  const btn = document.getElementById('btn-confirm-create-rag');

  const name = nameInput?.value.trim();
  if (!name) {
    window.showToast?.(i18n.t('auto___175897'), 'warning') || alert(i18n.t('auto___175897'));
    return;
  }

  if (btn) btn.disabled = true;
  try {
    const res = await fetch('/api/user/rags', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: name,
        description: descInput?.value.trim() || '',
        min_chunk_len: parseInt(minChunkInput?.value || '20', 10),
        max_chunk_len: parseInt(maxChunkInput?.value || '1500', 10)
      })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);

    const srcType = document.querySelector('input[name="new-rag-source-type"]:checked')?.value || 'local';

    const modalEl = document.getElementById('modal-create-user-rag');
    if (modalEl && window.bootstrap?.Modal) {
      const modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
      modal.hide();
    }

    if (nameInput) nameInput.value = '';
    if (descInput) descInput.value = 'i18n.t('auto__window_showtoast__78229b')${name}i18n.t('auto___61c9c5')success');
    await loadUserRags();
    const createdId = data.collection?.id;
    if (createdId) {
      selectUserRag(createdId);
      if (srcType === 'gdocs') {
        const importModalEl = document.getElementById('modal-import-gdocsi18n.t('auto__if_importmodalel_window_bootstrap_modal_const_importmodal_bootstrap_modal_getinstance_importmodalel_new_bootstrap_modal_importmodalel_importmodal_show_catch_err_window_showtoast_err_message__2c275b')dangeri18n.t('auto__alert_err_message_finally_if_btn_btn_disabled_false_delete_the_currently_active_workspace_collection_returns_promise_void_export_async_function_deleteactiveuserrag_if_activeuserragid_return_const_confirmed_confirm_activeuserragid_if_confirmed_return_try_const_res_await_fetch_api_user_rags_encodeuricomponent_activeuserragid_method__bce173')DELETEi18n.t('auto__if_res_ok_throw_new_error_http_res_status_window_showtoast__99a05f')${activeUserRagId}i18n.t('auto___e7697e')successi18n.t('auto__activeuserragid_null_await_loaduserrags_catch_err_window_showtoast_err_message__6aed96')danger') || alert(`Ошибка удаления коллекции: ${err.message}`);
  }
}

