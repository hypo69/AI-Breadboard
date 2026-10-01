/**
 * =============================================================================
 * Process Name: Windows Modules - Codebaserag Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля codebaseRag.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/~webgui/rag_tab/modules/codebaseRag.js?v=20261001_v1" type="module"></script>
 *
 *   JavaScript Import:
 *     import { updateCodebaseStatsDisplay } from '/windows/api/~webgui/rag_tab/modules/codebaseRag.js';
 *
 * File: codebaseRag.js
 * Project: ai-breadboard
 * Package: windows/api/~webgui/rag_tab/modules
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-01 13:04:40
 * =============================================================================
 */

import { escapeHtml } from './utils.js';
import { ragCachedFetch, CACHE_TAG } from './cache.js';

let cachedCodebaseIndexes = [];

/**
 * Fetch list of available codebase AST indexes and populate index selector.
 *
 * @returns {Promise<void>}
 */
export async function loadCodebaseIndexes() {
  const select = document.getElementById('codebase-active-index-select');
  if (!select) return;

  try {
    const res = await ragCachedFetch('/api/rag/codebase/indexes', {
      tags: ['rag-codebase']
    });
    if (!res.ok) return;
    const data = await res.json();
    cachedCodebaseIndexes = data.indexes || [];

    if (cachedCodebaseIndexes.length === 0) {
      select.innerHTML = '<option value="codebase">codebase (По умолчанию)</option>';
    } else {
      const curVal = select.value;
      select.innerHTML = cachedCodebaseIndexes.map(idx => {
        const scopeBadge = idx.scope === 'user' ? '👤 ' : '🌐 ';
        const label = `${scopeBadge}${idx.name} (${idx.total_chunks || 0} чанков)`;
        return `<option value="${escapeHtml(idx.name)}">${escapeHtml(label)}</option>`;
      }).join('');

      if (curVal && cachedCodebaseIndexes.some(i => i.name === curVal)) {
        select.value = curVal;
      }
    }
    updateCodebaseStatsDisplay();
  } catch (err) {
    console.error('[Codebase RAG] Error loading indexes:', err);
  }
}

/**
 * Update UI counters for the currently selected codebase index.
 */
export function updateCodebaseStatsDisplay() {
  const select = document.getElementById('codebase-active-index-select');
  const statChunks = document.getElementById('codebase-stat-chunks');
  const statSymbols = document.getElementById('codebase-stat-symbolsi18n.t('auto__if_select_return_const_currentname_select_value_const_item_cachedcodebaseindexes_find_i_i_name_currentname_if_item_if_statchunks_statchunks_textcontent_item_total_chunks_0_if_statsymbols_statsymbols_textcontent_item_total_symbols_0_ast_build_or_rebuild_codebase_ast_and_semantic_index_for_a_target_directory_returns_promise_void_export_async_function_buildcodebaserag_const_btn_document_getelementbyid__9e82be')btn-build-codebase-rag');
  const alertEl = document.getElementById('codebase-build-status-alert');
  const rootInput = document.getElementById('codebase-project-root-input');
  const nameInput = document.getElementById('codebase-index-name-input');
  const dirsInput = document.getElementById('codebase-include-dirs-input');

  const projectRoot = rootInput?.value?.trim() || '.';
  const indexName = nameInput?.value?.trim() || 'codebase';
  const includeDirs = (dirsInput?.value || '').split(',').map(s => s.trim()).filter(Boolean);

  if (btn) btn.disabled = true;
  if (alertEl) {
    alertEl.className = 'alert alert-info p-2 small mt-3 mb-0';
    alertEl.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Анализ AST и построение индексов...';
    alertEl.classList.remove('d-none');
  }

  try {
    const res = await fetch('/api/rag/codebase/build', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        project_root: projectRoot,
        index_name: indexName,
        include_dirs: includeDirs,
      }),
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || data.error || `HTTP ${res.status}`);

    const stats = data.result || {};
    if (alertEl) {
      alertEl.className = 'alert alert-success p-2 small mt-3 mb-0i18n.t('auto__alertel_innerhtml_strong_escapehtml_indexname_strong_br_stats_total_files_0_stats_total_chunks_0_ast_stats_total_symbols_0_stats_elapsed_seconds_0_await_loadcodebaseindexes_const_select_document_getelementbyid__48e173')codebase-active-index-select');
    if (select) select.value = indexName;
    updateCodebaseStatsDisplay();
  } catch (err) {
    console.error('[Codebase RAG] Build error:', err);
    if (alertEl) {
      alertEl.className = 'alert alert-danger p-2 small mt-3 mb-0i18n.t('auto__alertel_textcontent_err_message_finally_if_btn_btn_disabled_false_execute_semantic_query_against_codebase_chunks_returns_promise_void_export_async_function_executecodebasesearch_const_queryinput_document_getelementbyid__b471c6')codebase-search-query');
  const select = document.getElementById('codebase-active-index-select');
  const resultsContainer = document.getElementById('codebase-search-results');
  const btn = document.getElementById('btn-codebase-search');

  const query = queryInput?.value?.trim();
  if (!query) return;

  const indexName = select?.value || 'codebase';
  if (btn) btn.disabled = true;
  if (resultsContainer) {
    resultsContainer.innerHTML = '<div class="text-center py-4 text-primary"><span class="spinner-border spinner-border-sm me-2"></span> Поиск по коду...</div>';
  }

  try {
    const res = await fetch('/api/rag/codebase/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query,
        index_name: indexName,
        top_k: 5
      }),
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);

    const results = data.results || [];
    if (results.length === 0) {
      resultsContainer.innerHTML = `<div class="text-center text-muted py-4i18n.t('auto__escapehtml_query_div_return_resultscontainer_innerhtml_results_map_r_return_div_class__22b57b')card mb-2 border shadow-sm">
          <div class="card-header py-1 px-2 bg-body-secondary d-flex justify-content-between align-items-center">
            <span class="small fw-semibold text-truncate">
              <i class="bi bi-code-slash me-1 text-primary"></i> ${escapeHtml(r.id)}
            </span>
            <span class="badge bg-info">Score: ${r.similarity_score || 0}</span>
          </div>
          <div class="card-body p-2 font-monospace small bg-body-tertiary" style="white-space: pre-wrap; font-size: 0.8rem; max-height: 140px; overflow-y: auto;">${escapeHtml(r.text)}</div>
        </div>
      `;
    }).join('');
  } catch (err) {
    if (resultsContainer) {
      resultsContainer.innerHTML = `<div class="alert alert-danger p-2 small mb-0">Ошибка: ${escapeHtml(err.message)}</div>`;
    }
  } finally {
    if (btn) btn.disabled = false;
  }
}

/**
 * Execute symbol lookup in codebase AST symbols table.
 *
 * @returns {Promise<void>}
 */
export async function executeSymbolLookup() {
  const symbolInput = document.getElementById('codebase-symbol-query');
  const select = document.getElementById('codebase-active-index-select');
  const resultsContainer = document.getElementById('codebase-symbol-results');
  const btn = document.getElementById('btn-codebase-symbol-search');

  const symbol = symbolInput?.value?.trim();
  if (!symbol) return;

  const indexName = select?.value || 'codebase';
  if (btn) btn.disabled = true;
  if (resultsContainer) {
    resultsContainer.innerHTML = '<div class="text-center py-4 text-success"><span class="spinner-border spinner-border-sm me-2"></span> Поиск символов в AST...</div>';
  }

  try {
    const res = await fetch('/api/rag/codebase/symbols', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        symbol,
        index_name: indexName,
        limit: 10
      }),
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);

    const results = data.results || [];
    if (results.length === 0) {
      resultsContainer.innerHTML = `<div class="text-center text-muted py-4i18n.t('auto__escapehtml_symbol_ast_div_return_resultscontainer_innerhtml_results_map_s_return_div_class__949fb0')card mb-2 border border-success-subtle shadow-sm">
          <div class="card-header py-1 px-2 bg-success-subtle text-success-emphasis d-flex justify-content-between align-items-center">
            <span class="small fw-semibold">
              <i class="bi bi-tag-fill me-1"></i> ${escapeHtml(s.symbol)}
            </span>
            <span class="badge bg-success">${escapeHtml(s.type)}</span>
          </div>
          <div class="card-body p-2 small">
            <div><strong>Path:</strong> <code>${escapeHtml(s.path)}</code></div>
            <div><strong>Signature:</strong> <code>${escapeHtml(s.signature || '')}</code></div>
            ${s.docstring ? `<div class="mt-1 text-muted"><em>${escapeHtml(s.docstring)}</em></div>` : ''}
            ${s.related_symbols?.length ? `<div class="mt-1 small text-secondary">Related: ${escapeHtml(s.related_symbols.slice(0, 8).join(', '))}</div>` : ''}
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
