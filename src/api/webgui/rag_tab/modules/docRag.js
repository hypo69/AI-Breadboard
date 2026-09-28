/**
 * =============================================================================
 * Process Name: Global Document RAG Management
 * =============================================================================
 * Description:
 *   Handles file/folder uploading, document indexing, RAG status retrieval,
 *   document deletion, and semantic query execution for global document RAG.
 *
 * File: docRag.js
 * Project: AI Breadboard
 * Module: RAGTab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * =============================================================================
 */

import { formatBytes, escapeHtml } from './utils.js';
import { ragCachedFetch, CACHE_TAG } from './cache.js';

/**
 * Upload one or multiple files to the global document RAG storage.
 *
 * @param {File[]} files - List of files to upload.
 * @returns {Promise<void>}
 */
export async function uploadFiles(files) {
  if (!files || files.length === 0) return;

  const progressContainer = document.getElementById('rag-upload-progress-container');
  const progressBar = document.getElementById('rag-upload-progress-bar');
  const percentText = document.getElementById('rag-upload-percent');
  const statusAlert = document.getElementById('rag-upload-status-alert');

  if (progressContainer) progressContainer.classList.remove('d-none');
  if (statusAlert) statusAlert.classList.add('d-none');
  if (progressBar) progressBar.style.width = '0%';
  if (percentText) percentText.textContent = '0%';

  const formData = new FormData();
  files.forEach((file) => {
    const uploadName = file.customRelativePath || file.webkitRelativePath || file.name;
    formData.append('files', file, uploadName);
  });

  try {
    if (progressBar) progressBar.style.width = '50%';
    if (percentText) percentText.textContent = '50%';

    const res = await fetch('/api/rag/upload', {
      method: 'POST',
      body: formData,
    });

    if (progressBar) progressBar.style.width = '100%';
    if (percentText) percentText.textContent = '100%';

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || `Upload failed (HTTP ${res.status})`);

    if (statusAlert) {
      statusAlert.className = 'alert alert-success p-2 small mb-0i18n.t('auto__statusalert_textcontent_data_uploaded_length_0_statusalert_classlist_remove__eb89e3')d-none');
    }

    await loadRagDocuments();
    await loadRagStatus();
  } catch (err) {
    console.error('[RAG] Upload error:', err);
    if (statusAlert) {
      statusAlert.className = 'alert alert-danger p-2 small mb-0i18n.t('auto__statusalert_textcontent_err_message_statusalert_classlist_remove__c09e27')d-none');
    }
  } finally {
    setTimeout(() => {
      if (progressContainer) progressContainer.classList.add('d-none');
    }, 1500);
  }
}

/**
 * Fetch and display global RAG index status and stats.
 *
 * @returns {Promise<void>}
 */
export async function loadRagStatus() {
  try {
    const res = await ragCachedFetch('/api/rag/status', {
      tags: ['rag-status']
    });
    if (!res.ok) return;
    const data = await res.json();
    const st = data.data || {};

    const statDocs = document.getElementById('rag-stat-docs');
    const statChunks = document.getElementById('rag-stat-chunks');
    const statDim = document.getElementById('rag-stat-dim');
    const statUpdated = document.getElementById('rag-stat-updated');
    const providerBadge = document.getElementById('rag-provider-badge');

    if (statDocs) statDocs.textContent = st.total_documents || 0;
    if (statChunks) statChunks.textContent = st.total_chunks || 0;
    if (statDim) statDim.textContent = st.vector_dimension || 0;
    if (statUpdated) {
      statUpdated.textContent = st.last_built_at
        ? new Date(st.last_built_at * 1000).toLocaleTimeString()
        : '—';
    }
    if (providerBadge) {
      const provName = st.provider === 'gemini' ? 'Google Gemini Embeddings' : 'Local TF-IDF';
      providerBadge.textContent = `Provider: ${provName}`;
    }
  } catch (err) {
    console.error('[RAG] Error loading status:', err);
  }
}

/**
 * Fetch and render the list of uploaded global RAG documents.
 *
 * @returns {Promise<void>}
 */
export async function loadRagDocuments() {
  const tbody = document.getElementById('rag-documents-tbody');
  const badge = document.getElementById('rag-docs-badge');
  if (!tbody) return;

  try {
    const res = await ragCachedFetch('/api/rag/documents', {
      tags: ['rag-documentsi18n.t('auto__if_res_ok_return_const_data_await_res_json_const_docs_data_documents_if_badge_badge_textcontent_docs_length_if_docs_length_0_tbody_innerhtml__8521bc')<tr><td colspan="5" class="text-center text-muted py-3">Документы не загружены.</td></tr>';
      return;
    }

    tbody.innerHTML = docs.map((d, idx) => {
      const statusBadge = d.status === 'indexed'
        ? '<span class="badge bg-success">Индексирован</span>'
        : (d.status === 'error' ? '<span class="badge bg-danger">Ошибка</span>' : '<span class="badge bg-warning text-dark">Ожидание</span>');

      return `
        <tr class="rag-doc-row" data-idx="${idx}" style="cursor: pointer;" title=i18n.t('auto__ai_rag_f0ee95')>
          <td class="ps-3 text-truncate" style="max-width: 200px;" title="${escapeHtml(d.name)}">
            <i class="bi bi-file-earmark-code me-1 text-primary"></i> ${escapeHtml(d.name)}
          </td>
          <td>${formatBytes(d.size_bytes)}</td>
          <td><span class="badge bg-secondary-subtle text-secondary">${d.chunks_count || 0}</span></td>
          <td>${statusBadge}</td>
          <td class="text-end pe-3">
            <button class="btn btn-outline-danger btn-sm p-1 py-0 btn-del-rag-doc" data-name="${escapeHtml(d.name)}" title=i18n.t('auto___86ea33')>
              <i class="bi bi-trash"></i>
            </button>
          </td>
        </tr>
      `;
    }).join('');

    tbody.querySelectorAll('.rag-doc-row').forEach(row => {
      row.onclick = (evt) => {
        if (evt.target.closest('.btn-del-rag-doc')) return;
        const idx = parseInt(row.getAttribute('data-idx'), 10);
        const d = docs[idx];
        if (!d) return;

        if (window.AITableModal) {
          window.AITableModal.show({
            icon: '🧠i18n.t('auto__title_d_name_subtitle_formatbytes_d_size_bytes_d_chunks_count_0_tabletype__14fe3b')rag_doc',
            badges: [
              { text: d.status || 'Indexed', class: d.status === 'indexed' ? 'badge bg-success' : 'badge bg-secondary' },
              { text: `${d.chunks_count || 0} chunks`, class: 'badge bg-info text-dark' }
            ],
            metadata: [
              { label: i18n.t('auto___41d472'), value: d.name },
              { label: i18n.t('auto___6f09e9'), value: d.status || 'Indexed' },
              { label: i18n.t('auto___fdc486'), value: String(d.chunks_count || 0) },
              { label: i18n.t('auto___b2683b'), value: formatBytes(d.size_bytes) },
              { label: i18n.t('auto___4140fb'), value: d.updated_at || d.created_at || 'N/A' },
              { label: i18n.t('auto___98ded8'), value: d.source_path || d.name, isCode: true, fullWidth: true }
            ],
            rawTitle: i18n.t('auto___3e0497'),
            rawContent: JSON.stringify(d, null, 2),
            requestData: {
              name: d.name,
              chunks_count: d.chunks_count,
              size: formatBytes(d.size_bytes),
              status: d.status
            }
          });
        }
      };
    });

    tbody.querySelectorAll('.btn-del-rag-doc').forEach(btn => {
      btn.onclick = (evt) => {
        evt.stopPropagation();
        const docName = btn.getAttribute('data-name');
        deleteRagDocument(docName);
      };
    });
  } catch (err) {
    console.error('[RAG] Error loading documents:i18n.t('auto__err_delete_a_specific_document_from_global_rag_param_string_filename_name_of_the_document_to_delete_returns_promise_void_export_async_function_deleteragdocument_filename_if_confirm_filename_return_try_const_res_await_fetch_api_rag_documents_encodeuricomponent_filename_method__2ef265')DELETEi18n.t('auto__window_showtoast_filename__006e95')successi18n.t('auto__await_loadragdocuments_await_loadragstatus_catch_err_window_showtoast_err_message__c841a8')dangeri18n.t('auto__alert_err_message_trigger_global_rag_index_build_returns_promise_void_export_async_function_buildragindex_const_buildbtn_document_getelementbyid__d336a6')btn-build-rag-index');
  const statusEl = document.getElementById('rag-build-status');
  const providerSelect = document.getElementById('rag-provider-select');
  const apiKeyInput = document.getElementById('rag-api-key-input');
  const chunkSizeInput = document.getElementById('rag-chunk-size');
  const chunkOverlapInput = document.getElementById('rag-chunk-overlap');

  if (buildBtn) buildBtn.disabled = true;
  if (statusEl) {
    statusEl.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Построение векторного индекса...';
  }

  try {
    const res = await fetch('/api/rag/build', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        provider: providerSelect?.value || 'auto',
        api_key: apiKeyInput?.value?.trim() || '',
        chunk_size: parseInt(chunkSizeInput?.value || '500', 10),
        chunk_overlap: parseInt(chunkOverlapInput?.value || '50', 10),
      }),
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);

    if (statusEl) {
      statusEl.className = 'small mt-2 text-center text-success fw-semiboldi18n.t('auto__statusel_textcontent_data_result_total_chunks_0_await_loadragstatus_await_loadragdocuments_catch_err_console_error__27fdef')[RAG] Build error:', err);
    if (statusEl) {
      statusEl.className = 'small mt-2 text-center text-dangeri18n.t('auto__statusel_textcontent_err_message_finally_if_buildbtn_buildbtn_disabled_false_execute_semantic_query_against_global_rag_index_returns_promise_void_export_async_function_executeragsearch_const_queryinput_document_getelementbyid__c417e9')rag-search-query');
  const topKSelect = document.getElementById('rag-top-k');
  const minScoreInput = document.getElementById('rag-min-score');
  const resultsContainer = document.getElementById('rag-search-results');
  const searchBtn = document.getElementById('btn-rag-search');
  const apiKeyInput = document.getElementById('rag-api-key-input');

  const query = queryInput?.value?.trim();
  if (!query) return;

  if (searchBtn) searchBtn.disabled = true;
  if (resultsContainer) {
    resultsContainer.innerHTML = '<div class="text-center py-4 text-primary"><span class="spinner-border spinner-border-sm me-2"></span> Идет семантический поиск...</div>';
  }

  try {
    const res = await fetch('/api/rag/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query,
        top_k: parseInt(topKSelect?.value || '5', 10),
        min_score: parseFloat(minScoreInput?.value || '0.0'),
        api_key: apiKeyInput?.value?.trim() || '',
      }),
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);

    const results = data.results || [];
    if (results.length === 0) {
      resultsContainer.innerHTML = `<div class="text-center text-muted py-4"><i class="bi bi-search fs-3 d-block mb-1 opacity-50i18n.t('auto__i_escapehtml_query_div_return_resultscontainer_innerhtml_results_map_r_div_class__63c097')card mb-2 border shadow-sm">
        <div class="card-header py-1 px-2 bg-body-secondary d-flex justify-content-between align-items-center">
          <span class="small fw-semibold text-truncate" style="max-width: 70%;">
            <i class="bi bi-file-earmark-text me-1 text-primary"></i> ${escapeHtml(r.doc_name)} (#${r.chunk_index})
          </span>
          <span class="badge bg-secondary">Score: ${r.score}</span>
        </div>
        <div class="card-body p-2 font-monospace small bg-body-tertiary" style="white-space: pre-wrap; font-size: 0.8rem; max-height: 120px; overflow-y: auto;">${escapeHtml(r.text)}</div>
      </div>
    `).join('');
  } catch (err) {
    if (resultsContainer) {
      resultsContainer.innerHTML = `<div class="alert alert-danger p-2 small mb-0">Ошибка: ${escapeHtml(err.message)}</div>`;
    }
  } finally {
    if (searchBtn) searchBtn.disabled = false;
  }
}
