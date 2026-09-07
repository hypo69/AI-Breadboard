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
      statusAlert.className = 'alert alert-success p-2 small mb-0';
      statusAlert.textContent = `Успешно загружено файлов: ${data.uploaded?.length || 0}`;
      statusAlert.classList.remove('d-none');
    }

    await loadRagDocuments();
    await loadRagStatus();
  } catch (err) {
    console.error('[RAG] Upload error:', err);
    if (statusAlert) {
      statusAlert.className = 'alert alert-danger p-2 small mb-0';
      statusAlert.textContent = `Ошибка загрузки: ${err.message}`;
      statusAlert.classList.remove('d-none');
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
    const res = await fetch('/api/rag/status');
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
    const res = await fetch('/api/rag/documents');
    if (!res.ok) return;
    const data = await res.json();
    const docs = data.documents || [];

    if (badge) badge.textContent = `${docs.length} файлов`;
    if (docs.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-3">Документы не загружены.</td></tr>';
      return;
    }

    tbody.innerHTML = docs.map(d => {
      const statusBadge = d.status === 'indexed'
        ? '<span class="badge bg-success">Индексирован</span>'
        : (d.status === 'error' ? '<span class="badge bg-danger">Ошибка</span>' : '<span class="badge bg-warning text-dark">Ожидание</span>');

      return `
        <tr>
          <td class="ps-3 text-truncate" style="max-width: 200px;" title="${escapeHtml(d.name)}">
            <i class="bi bi-file-earmark-code me-1 text-primary"></i> ${escapeHtml(d.name)}
          </td>
          <td>${formatBytes(d.size_bytes)}</td>
          <td><span class="badge bg-secondary-subtle text-secondary">${d.chunks_count || 0}</span></td>
          <td>${statusBadge}</td>
          <td class="text-end pe-3">
            <button class="btn btn-outline-danger btn-sm p-1 py-0" onclick="window.deleteRagDocument('${escapeHtml(d.name)}')" title="Удалить">
              <i class="bi bi-trash"></i>
            </button>
          </td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    console.error('[RAG] Error loading documents:', err);
  }
}

/**
 * Delete a specific document from global RAG.
 *
 * @param {string} filename - Name of the document to delete.
 * @returns {Promise<void>}
 */
export async function deleteRagDocument(filename) {
  if (!confirm(`Удалить документ «${filename}» из базы знаний?`)) return;
  try {
    const res = await fetch(`/api/rag/documents/${encodeURIComponent(filename)}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    await loadRagDocuments();
    await loadRagStatus();
  } catch (err) {
    alert(`Ошибка удаления: ${err.message}`);
  }
}

/**
 * Trigger global RAG index build.
 *
 * @returns {Promise<void>}
 */
export async function buildRagIndex() {
  const buildBtn = document.getElementById('btn-build-rag-index');
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
      statusEl.className = 'small mt-2 text-center text-success fw-semibold';
      statusEl.textContent = `✓ Индекс успешно построен. Всего чанков: ${data.result?.total_chunks || 0}`;
    }

    await loadRagStatus();
    await loadRagDocuments();
  } catch (err) {
    console.error('[RAG] Build error:', err);
    if (statusEl) {
      statusEl.className = 'small mt-2 text-center text-danger';
      statusEl.textContent = `✗ Ошибка индексации: ${err.message}`;
    }
  } finally {
    if (buildBtn) buildBtn.disabled = false;
  }
}

/**
 * Execute semantic query against global RAG index.
 *
 * @returns {Promise<void>}
 */
export async function executeRagSearch() {
  const queryInput = document.getElementById('rag-search-query');
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
      resultsContainer.innerHTML = `<div class="text-center text-muted py-4"><i class="bi bi-search fs-3 d-block mb-1 opacity-50"></i>По запросу «${escapeHtml(query)}» ничего не найдено.</div>`;
      return;
    }

    resultsContainer.innerHTML = results.map(r => `
      <div class="card mb-2 border shadow-sm">
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
