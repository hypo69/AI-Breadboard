/**
 * =============================================================================
 * Process Name: Windows Modules - Pixelrag Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля pixelRag.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/~webgui/rag_tab/modules/pixelRag.js?v=20261001_v1" type="module"></script>
 *
 * File: pixelRag.js
 * Project: ai-breadboard
 * Package: windows/api/~webgui/rag_tab/modules
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-01 13:04:40
 * =============================================================================
 */

import { formatBytes, escapeHtml } from './utils.js';

/**
 * Load and display PixelRAG system status, FAISS index metrics, and image counts.
 *
 * @returns {Promise<void>}
 */
export async function loadPixelRagStatus() {
  try {
    const res = await fetch('/api/rag/pixel/status');
    if (!res.ok) return;

    const data = await res.json();
    const imagesEl = document.getElementById('pixel-stat-images');
    const chunksEl = document.getElementById('pixel-stat-chunks');
    const sizeEl = document.getElementById('pixel-stat-size');
    const providerEl = document.getElementById('pixel-stat-provider');
    const updatedEl = document.getElementById('pixel-stat-updated');
    const statusEl = document.getElementById('pixel-stat-status');

    if (imagesEl) imagesEl.textContent = data.total_images || 0;
    if (chunksEl) chunksEl.textContent = data.total_chunks || 0;
    if (sizeEl) sizeEl.textContent = `${(data.total_size_mb || 0).toFixed(2)} MB`;
    if (providerEl) providerEl.textContent = data.provider || 'FAISS / PixelRAGi18n.t('auto__if_statusel_statusel_textcontent_data_sources_text_chunks_0_data_sources_images_0_if_updatedel_if_data_last_built_at_data_last_built_at_0_const_d_new_date_data_last_built_at_1000_updatedel_textcontent_d_tolocalestring_else_updatedel_textcontent__a530ea')Индекс готов';
      }
    }
  } catch (err) {
    console.debug('[PixelRAG] Failed to load status:', err);
  }
}

/**
 * Upload and index image files into PixelRAG.
 *
 * @param {File[]} files - List of image files.
 * @returns {Promise<void>}
 */
export async function uploadAndIndexPixelImages(files) {
  if (!files || files.length === 0) return;

  const progressContainer = document.getElementById('pixel-upload-progress');
  const progressBar = document.getElementById('pixel-upload-progress-bar');
  const percentText = document.getElementById('pixel-upload-percent');
  const statusAlert = document.getElementById('pixel-upload-status-alert');

  if (progressContainer) progressContainer.classList.remove('d-none');
  if (statusAlert) statusAlert.classList.add('d-none');
  if (progressBar) progressBar.style.width = '20%';
  if (percentText) percentText.textContent = '20%';

  const formData = new FormData();
  files.forEach((file) => {
    formData.append('files', file, file.name);
  });

  try {
    if (progressBar) progressBar.style.width = '60%';
    if (percentText) percentText.textContent = '60%';

    const res = await fetch('/api/rag/pixel/index', {
      method: 'POST',
      body: formData,
    });

    if (progressBar) progressBar.style.width = '100%';
    if (percentText) percentText.textContent = '100%i18n.t('auto__const_data_await_res_json_if_res_ok_throw_new_error_data_detail_http_res_status_if_statusalert_statusalert_classname__e738a1')alert alert-success p-2 small mb-0i18n.t('auto__statusalert_textcontent_data_indexed_count_files_length_statusalert_classlist_remove__5fa5e2')d-none');
    }

    await loadPixelRagStatus();
  } catch (err) {
    console.error('[PixelRAG] Indexing error:', err);
    if (statusAlert) {
      statusAlert.className = 'alert alert-danger p-2 small mb-0i18n.t('auto__statusalert_textcontent_err_message_statusalert_classlist_remove__93d53f')d-none');
    }
  } finally {
    setTimeout(() => {
      if (progressContainer) progressContainer.classList.add('d-none');
    }, 2000);
  }
}

/**
 * Execute smart query analysis via QueryRouter.
 *
 * @returns {Promise<void>}
 */
export async function analyzePixelQuery() {
  const input = document.getElementById('pixel-analyze-query-input');
  const resultBox = document.getElementById('pixel-analyze-result');
  const routingTypeEl = document.getElementById('pixel-routing-type');
  const confidenceEl = document.getElementById('pixel-routing-confidence');
  const reasonEl = document.getElementById('pixel-routing-reason');

  if (!input || !input.value.trim()) return;
  const query = input.value.trim();

  try {
    const res = await fetch(`/api/rag/pixel/analyze-query?query=${encodeURIComponent(query)}`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const data = await res.json();
    if (resultBox) resultBox.classList.remove('d-none');
    if (routingTypeEl) {
      routingTypeEl.textContent = data.routing_type?.toUpperCase() || 'HYBRID';
      routingTypeEl.className = data.routing_type === 'visual' ? 'badge bg-warning text-dark' : data.routing_type === 'text' ? 'badge bg-info' : 'badge bg-primaryi18n.t('auto__if_confidenceel_confidenceel_textcontent_math_round_data_confidence_1_0_100_if_reasonel_reasonel_textcontent_data_reason__eba515')Авто-определение по ключевым признакам'}`;
  } catch (err) {
    console.error('[PixelRAG] Analysis failed:', err);
  }
}

/**
 * Execute semantic visual search inside PixelRAG.
 *
 * @returns {Promise<void>}
 */
export async function executePixelRagSearch() {
  const queryInput = document.getElementById('pixel-search-query');
  const topKSelect = document.getElementById('pixel-search-topk');
  const minScoreSelect = document.getElementById('pixel-search-minscore');
  const routingToggle = document.getElementById('pixel-search-routing-toggle');
  const resultsContainer = document.getElementById('pixel-search-results');

  if (!queryInput || !resultsContainer) return;
  const query = queryInput.value.trim();
  if (!query) {
    queryInput.focus();
    return;
  }

  const topK = parseInt(topKSelect?.value || '5', 10);
  const minScore = parseFloat(minScoreSelect?.value || '0.0');
  const useRouting = routingToggle ? routingToggle.checked : true;

  resultsContainer.innerHTML = `
    <div class="text-center py-4 text-muted">
      <div class="spinner-border spinner-border-sm text-primary me-2" role="status"></div>
      <span>Поиск по визуальным индексам и текстовым чанкам...</span>
    </div>
  `;

  try {
    const res = await fetch('/api/rag/pixel/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: query,
        top_k: topK,
        min_score: minScore,
        use_routing: useRouting,
        version_filter: 'latest',
      }),
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `HTTP ${res.status}`);
    }

    const data = await res.json();
    const results = data.results || [];

    if (results.length === 0) {
      resultsContainer.innerHTML = `
        <div class="text-center text-muted py-4">
          <i class="bi bi-search fs-3 d-block mb-1 opacity-50i18n.t('auto__i_span_escapehtml_query_span_div_return_resultscontainer_innerhtml_div_class__096358')d-flex justify-content-between align-items-center mb-2 pb-2 border-bottom">
        <span class="small text-mutedi18n.t('auto__strong_results_length_strong_span_class__29178e')badge bg-secondary">${data.routing_type}</span>)</span>
        <span class="small text-mutedi18n.t('auto__data_query_confidence_100_tofixed_0_span_div_div_class__0c443d')d-flex flex-column gap-2">
        ${results.map((r, i) => {
          const scorePercent = Math.min(100, Math.round((r.score || 0) * 100));
          const isVisual = r.source_type === 'pixel' || r.source_type === 'image';
          const typeBadge = isVisual
            ? '<span class="badge bg-warning text-dark"><i class="bi bi-image me-1"></i>Visual</span>'
            : '<span class="badge bg-info"><i class="bi bi-file-text me-1"></i>Text</span>';

          return `
            <div class="card bg-body border-secondary-subtle p-2">
              <div class="d-flex justify-content-between align-items-center mb-1">
                <span class="fw-bold small text-primary text-truncate" style="max-width: 70%;">
                  #${i + 1} ${escapeHtml(r.doc_name || i18n.t('auto___32b74a'))}
                </span>
                <div class="d-flex align-items-center gap-1">
                  ${typeBadge}
                  <span class="badge bg-success-subtle text-success border border-success-subtle">
                    Score: ${(r.score || 0).toFixed(3)} (${scorePercent}%)
                  </span>
                </div>
              </div>
              <div class="small text-body-secondary font-monospace" style="font-size: 0.8rem; white-space: pre-wrap;">
                ${escapeHtml(r.text || '')}
              </div>
              ${r.source_path ? `<div class="small text-muted mt-1 text-truncate" style="font-size: 0.72rem;"><i class="bi bi-link-45deg"></i> ${escapeHtml(r.source_path)}</div>` : ''}
            </div>
          `;
        }).join('')}
      </div>
    `;
  } catch (err) {
    console.error('[PixelRAG] Search error:', err);
    resultsContainer.innerHTML = `
      <div class="alert alert-danger p-2 small mb-0">
        <i class="bi bi-exclamation-triangle me-1"></i> Ошибка поиска: ${escapeHtml(err.message)}
      </div>
    `;
  }
}
