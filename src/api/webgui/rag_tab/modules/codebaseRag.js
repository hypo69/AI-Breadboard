/**
 * =============================================================================
 * Process Name: Codebase AST RAG Management
 * =============================================================================
 * Description:
 *   Handles project codebase indexing, AST symbol extraction, semantic code
 *   search, and AST symbol lookup across workspace projects.
 *
 * File: codebaseRag.js
 * Project: AI Breadboard
 * Module: RAGTab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * =============================================================================
 */

import { escapeHtml } from './utils.js';

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
    const res = await fetch('/api/rag/codebase/indexes');
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
  const statSymbols = document.getElementById('codebase-stat-symbols');
  if (!select) return;

  const currentName = select.value;
  const item = cachedCodebaseIndexes.find(i => i.name === currentName);
  if (item) {
    if (statChunks) statChunks.textContent = `${item.total_chunks || 0} чанков`;
    if (statSymbols) statSymbols.textContent = `${item.total_symbols || 0} символов AST`;
  }
}

/**
 * Build or rebuild codebase AST and semantic index for a target directory.
 *
 * @returns {Promise<void>}
 */
export async function buildCodebaseRag() {
  const btn = document.getElementById('btn-build-codebase-rag');
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
      alertEl.className = 'alert alert-success p-2 small mt-3 mb-0';
      alertEl.innerHTML = `
        <strong>✓ Индекс «${escapeHtml(indexName)}» успешно создан!</strong><br>
        Файлов: ${stats.total_files || 0} | Чанков: ${stats.total_chunks || 0} | Символов AST: ${stats.total_symbols || 0} (${stats.elapsed_seconds || 0}с)
      `;
    }

    await loadCodebaseIndexes();
    const select = document.getElementById('codebase-active-index-select');
    if (select) select.value = indexName;
    updateCodebaseStatsDisplay();
  } catch (err) {
    console.error('[Codebase RAG] Build error:', err);
    if (alertEl) {
      alertEl.className = 'alert alert-danger p-2 small mt-3 mb-0';
      alertEl.textContent = `Ошибка сборки: ${err.message}`;
    }
  } finally {
    if (btn) btn.disabled = false;
  }
}

/**
 * Execute semantic query against codebase chunks.
 *
 * @returns {Promise<void>}
 */
export async function executeCodebaseSearch() {
  const queryInput = document.getElementById('codebase-search-query');
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
      resultsContainer.innerHTML = `<div class="text-center text-muted py-4">По запросу «${escapeHtml(query)}» совпадений не найдено.</div>`;
      return;
    }

    resultsContainer.innerHTML = results.map(r => {
      return `
        <div class="card mb-2 border shadow-sm">
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
      resultsContainer.innerHTML = `<div class="text-center text-muted py-4">Символ «${escapeHtml(symbol)}» не найден в AST-индексе.</div>`;
      return;
    }

    resultsContainer.innerHTML = results.map(s => {
      return `
        <div class="card mb-2 border border-success-subtle shadow-sm">
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
