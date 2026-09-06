// ── RAG_TAB MAIN.JS ─────────────────────────────────────────────────────────

(function () {
  let isInitialized = false;

  function initRagTab() {
    if (isInitialized) {
      loadRagStatus();
      loadRagDocuments();
      return;
    }
    isInitialized = true;
    setupEventListeners();
    loadRagStatus();
    loadRagDocuments();
  }

  // Register global initializer so main.js can trigger it if needed
  window.initRagTab = initRagTab;

  function setupEventListeners() {
    const refreshBtn = document.getElementById('btn-refresh-rag');
    if (refreshBtn) {
      refreshBtn.addEventListener('click', () => {
        loadRagStatus();
        loadRagDocuments();
      });
    }

    const fileInput = document.getElementById('rag-file-input');
    const dropzone = document.getElementById('rag-dropzone');

    if (fileInput) {
      fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files.length > 0) {
          uploadFiles(Array.from(e.target.files));
          fileInput.value = '';
        }
      });
    }

    if (dropzone) {
      ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
          e.preventDefault();
          e.stopPropagation();
          dropzone.classList.add('border-primary', 'bg-primary', 'bg-opacity-10');
        }, false);
      });

      ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
          e.preventDefault();
          e.stopPropagation();
          dropzone.classList.remove('border-primary', 'bg-primary', 'bg-opacity-10');
        }, false);
      });

      dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        if (dt && dt.files && dt.files.length > 0) {
          uploadFiles(Array.from(dt.files));
        }
      }, false);
    }

    const buildBtn = document.getElementById('btn-build-rag-index');
    if (buildBtn) {
      buildBtn.addEventListener('click', buildRagIndex);
    }

    const searchBtn = document.getElementById('btn-rag-search');
    const searchInput = document.getElementById('rag-search-query');
    if (searchBtn) {
      searchBtn.addEventListener('click', executeRagSearch);
    }
    if (searchInput) {
      searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          executeRagSearch();
        }
      });
    }
  }

  async function uploadFiles(files) {
    if (!files || files.length === 0) return;

    const progressContainer = document.getElementById('rag-upload-progress-container');
    const progressBar = document.getElementById('rag-upload-progress-bar');
    const progressPercent = document.getElementById('rag-upload-percent');
    const alertBox = document.getElementById('rag-upload-status-alert');

    if (progressContainer) progressContainer.classList.remove('d-none');
    if (progressBar) progressBar.style.width = '20%';
    if (progressPercent) progressPercent.textContent = '20%';
    if (alertBox) alertBox.classList.add('d-none');

    const formData = new FormData();
    files.forEach(f => formData.append('files', f));

    try {
      if (progressBar) progressBar.style.width = '60%';
      if (progressPercent) progressPercent.textContent = '60%';

      const res = await fetch('/api/rag/upload', {
        method: 'POST',
        body: formData,
      });

      if (progressBar) progressBar.style.width = '100%';
      if (progressPercent) progressPercent.textContent = '100%';

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Upload error');

      showAlert('success', `✓ Успешно загружено файлов: ${data.uploaded ? data.uploaded.length : files.length}`);
      await loadRagDocuments();
      await loadRagStatus();
    } catch (err) {
      console.error('[RAG] Upload failed:', err);
      showAlert('danger', `Ошибка загрузки: ${err.message}`);
    } finally {
      setTimeout(() => {
        if (progressContainer) progressContainer.classList.add('d-none');
      }, 1200);
    }
  }

  function showAlert(type, message) {
    const alertBox = document.getElementById('rag-upload-status-alert');
    if (!alertBox) return;
    alertBox.className = `alert alert-${type} p-2 small mb-0`;
    alertBox.textContent = message;
    alertBox.classList.remove('d-none');
    setTimeout(() => {
      alertBox.classList.add('d-none');
    }, 5000);
  }

  async function loadRagStatus() {
    try {
      const res = await fetch('/api/rag/status');
      if (!res.ok) return;
      const json = await res.json();
      const st = json.data || {};

      const statDocs = document.getElementById('rag-stat-docs');
      const statChunks = document.getElementById('rag-stat-chunks');
      const statDim = document.getElementById('rag-stat-dim');
      const statUpdated = document.getElementById('rag-stat-updated');
      const providerBadge = document.getElementById('rag-provider-badge');

      if (statDocs) statDocs.textContent = st.total_documents || 0;
      if (statChunks) statChunks.textContent = st.total_chunks || 0;
      if (statDim) statDim.textContent = st.dimension || 0;
      if (statUpdated) {
        if (st.last_built_at && st.last_built_at > 0) {
          const date = new Date(st.last_built_at * 1000);
          statUpdated.textContent = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) + ' ' + date.toLocaleDateString();
        } else {
          statUpdated.textContent = 'Не создан';
        }
      }
      if (providerBadge) {
        providerBadge.textContent = `Provider: ${st.provider || 'local_tfidf'}`;
      }
    } catch (err) {
      console.error('[RAG] loadRagStatus error:', err);
    }
  }

  async function loadRagDocuments() {
    const tbody = document.getElementById('rag-documents-tbody');
    const badge = document.getElementById('rag-docs-badge');
    if (!tbody) return;

    try {
      const res = await fetch('/api/rag/documents');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const docs = data.documents || [];

      if (badge) badge.textContent = `${docs.length} файлов`;

      if (docs.length === 0) {
        tbody.innerHTML = `
          <tr>
            <td colspan="5" class="text-center text-muted py-3">
              Документы не загружены. Загрузите файлы в блоке слева.
            </td>
          </tr>
        `;
        return;
      }

      tbody.innerHTML = docs.map(doc => {
        const sizeKb = (doc.size_bytes / 1024).toFixed(1) + ' KB';
        let statusBadge = '<span class="badge bg-secondary">Pending</span>';
        if (doc.status === 'indexed') {
          statusBadge = '<span class="badge bg-success">Indexed</span>';
        } else if (doc.status === 'error') {
          statusBadge = `<span class="badge bg-danger" title="${doc.error_message}">Error</span>`;
        }

        return `
          <tr>
            <td class="ps-3 fw-semibold text-truncate" style="max-width: 200px;" title="${doc.name}">
              <i class="bi bi-file-earmark-text me-1 text-primary"></i> ${doc.name}
            </td>
            <td><small class="text-muted">${sizeKb}</small></td>
            <td><span class="badge bg-info bg-opacity-75">${doc.chunks_count || 0}</span></td>
            <td>${statusBadge}</td>
            <td class="text-end pe-3">
              <button class="btn btn-outline-danger btn-sm p-1 rounded-circle" title="Удалить файл" onclick="window.deleteRagDocument('${encodeURIComponent(doc.name)}')">
                <i class="bi bi-trash"></i>
              </button>
            </td>
          </tr>
        `;
      }).join('');
    } catch (err) {
      console.error('[RAG] loadRagDocuments error:', err);
      tbody.innerHTML = `<tr><td colspan="5" class="text-center text-danger py-2">Ошибка загрузки списка: ${err.message}</td></tr>`;
    }
  }

  window.deleteRagDocument = async function (encodedName) {
    const filename = decodeURIComponent(encodedName);
    if (!confirm(`Удалить документ "${filename}" из базы знаний?`)) return;

    try {
      const res = await fetch(`/api/rag/documents/${encodeURIComponent(filename)}`, {
        method: 'DELETE',
      });
      if (!res.ok) throw new Error('Delete error');
      await loadRagDocuments();
      await loadRagStatus();
    } catch (err) {
      alert(`Не удалось удалить файл: ${err.message}`);
    }
  };

  async function buildRagIndex() {
    const buildBtn = document.getElementById('btn-build-rag-index');
    const statusText = document.getElementById('rag-build-status');
    const provider = document.getElementById('rag-provider-select')?.value || 'auto';
    const apiKey = document.getElementById('rag-api-key-input')?.value || '';
    const chunkSize = parseInt(document.getElementById('rag-chunk-size')?.value || '500', 10);
    const chunkOverlap = parseInt(document.getElementById('rag-chunk-overlap')?.value || '50', 10);

    if (buildBtn) {
      buildBtn.disabled = true;
      buildBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Построение индекса...';
    }
    if (statusText) {
      statusText.className = 'small mt-2 text-center text-primary';
      statusText.textContent = 'Идет обработка и векторизация документов...';
    }

    try {
      const res = await fetch('/api/rag/build', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider,
          api_key: apiKey,
          chunk_size: chunkSize,
          chunk_overlap: chunkOverlap,
        }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Build error');

      if (statusText) {
        statusText.className = 'small mt-2 text-center text-success fw-bold';
        statusText.textContent = `✓ Индекс успешно построен! (${data.result?.total_chunks || 0} чанков)`;
      }
      await loadRagDocuments();
      await loadRagStatus();
    } catch (err) {
      console.error('[RAG] Build error:', err);
      if (statusText) {
        statusText.className = 'small mt-2 text-center text-danger';
        statusText.textContent = `Ошибка построения: ${err.message}`;
      }
    } finally {
      if (buildBtn) {
        buildBtn.disabled = false;
        buildBtn.innerHTML = '<i class="bi bi-hammer me-1"></i> Построить / Перестроить индекс';
      }
    }
  }

  async function executeRagSearch() {
    const queryInput = document.getElementById('rag-search-query');
    const topKSelect = document.getElementById('rag-top-k');
    const minScoreInput = document.getElementById('rag-min-score');
    const apiKey = document.getElementById('rag-api-key-input')?.value || '';
    const resultsContainer = document.getElementById('rag-search-results');
    const searchBtn = document.getElementById('btn-rag-search');

    const query = queryInput ? queryInput.value.trim() : '';
    if (!query) {
      if (queryInput) queryInput.focus();
      return;
    }

    if (searchBtn) searchBtn.disabled = true;
    if (resultsContainer) {
      resultsContainer.innerHTML = `
        <div class="text-center py-4 text-primary">
          <span class="spinner-border spinner-border-sm me-2"></span> Идет семантический поиск...
        </div>
      `;
    }

    try {
      const res = await fetch('/api/rag/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          top_k: parseInt(topKSelect?.value || '5', 10),
          min_score: parseFloat(minScoreInput?.value || '0.0'),
          api_key: apiKey,
        }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Search error');

      const results = data.results || [];
      if (results.length === 0) {
        resultsContainer.innerHTML = `
          <div class="text-center text-muted py-4">
            <i class="bi bi-search fs-3 d-block mb-1 opacity-50"></i>
            По запросу «${escapeHtml(query)}» ничего не найдено с заданным порогом сходства.
          </div>
        `;
        return;
      }

      resultsContainer.innerHTML = results.map((r, i) => {
        const scorePercent = Math.round((r.score || 0) * 100);
        let scoreBadgeClass = 'bg-secondary';
        if (scorePercent >= 75) scoreBadgeClass = 'bg-success';
        else if (scorePercent >= 50) scoreBadgeClass = 'bg-info';
        else if (scorePercent >= 30) scoreBadgeClass = 'bg-warning text-dark';

        return `
          <div class="card mb-2 border shadow-sm">
            <div class="card-header py-1 px-2 bg-body-secondary d-flex justify-content-between align-items-center">
              <span class="small fw-semibold text-truncate" style="max-width: 70%;">
                <i class="bi bi-file-earmark-text me-1 text-primary"></i> ${escapeHtml(r.doc_name)} <span class="text-muted">(#${r.chunk_index})</span>
              </span>
              <span class="badge ${scoreBadgeClass}">Score: ${r.score}</span>
            </div>
            <div class="card-body p-2 font-monospace small bg-body-tertiary" style="white-space: pre-wrap; font-size: 0.8rem; max-height: 120px; overflow-y: auto;">
${escapeHtml(r.text)}
            </div>
          </div>
        `;
      }).join('');
    } catch (err) {
      console.error('[RAG] Search error:', err);
      if (resultsContainer) {
        resultsContainer.innerHTML = `<div class="alert alert-danger p-2 small mb-0">Ошибка поиска: ${escapeHtml(err.message)}</div>`;
      }
    } finally {
      if (searchBtn) searchBtn.disabled = false;
    }
  }

  function escapeHtml(text) {
    if (!text) return '';
    return String(text)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // Auto-init on script load
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initRagTab);
  } else {
    initRagTab();
  }
})();
