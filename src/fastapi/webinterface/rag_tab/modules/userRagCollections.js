/**
 * =============================================================================
 * Process Name: Workspace Multi-RAG Collections Management
 * =============================================================================
 * Description:
 *   Manages user workspace RAG collections listing, selection, modal creation,
 *   and collection deletion.
 *
 * File: userRagCollections.js
 * Project: AI Breadboard
 * Module: RAGTab
 * Author: hypo69
 * Copyright: © 2026 hypo69
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
          <span><i class="bi bi-diagram-3 me-1"></i>${col.total_chunks || 0} чанков</span>
          <span><i class="bi bi-file-earmark me-1"></i>${(col.files || []).length} файлов</span>
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
    if (descEl) descEl.textContent = col.description || 'Без описания';
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
  } catch (err) {
    console.error('Failed to load user RAG details:', err);
  }
}

/**
 * Create a new user workspace RAG collection via API.
 *
 * @returns {Promise<void>}
 */
export async function createUserRag() {
  const nameInput = document.getElementById('new-rag-name');
  const descInput = document.getElementById('new-rag-desc');
  const minChunkInput = document.getElementById('new-rag-min-chunk');
  const maxChunkInput = document.getElementById('new-rag-max-chunk');
  const btn = document.getElementById('btn-confirm-create-rag');

  const name = nameInput?.value.trim();
  if (!name) {
    alert('Пожалуйста, укажите имя коллекции.');
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

    const modalEl = document.getElementById('modal-create-user-rag');
    if (modalEl && window.bootstrap?.Modal) {
      const modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
      modal.hide();
    }

    if (nameInput) nameInput.value = '';
    if (descInput) descInput.value = '';

    await loadUserRags();
    if (data.collection?.id) {
      selectUserRag(data.collection.id);
    }
  } catch (err) {
    alert(`Ошибка создания коллекции: ${err.message}`);
  } finally {
    if (btn) btn.disabled = false;
  }
}

/**
 * Delete the currently active workspace collection.
 *
 * @returns {Promise<void>}
 */
export async function deleteActiveUserRag() {
  if (!activeUserRagId) return;

  const confirmed = confirm(`Вы уверены, что хотите удалить коллекцию «${activeUserRagId}»?`);
  if (!confirmed) return;

  try {
    const res = await fetch(`/api/user/rags/${encodeURIComponent(activeUserRagId)}`, {
      method: 'DELETE'
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    activeUserRagId = null;
    await loadUserRags();
  } catch (err) {
    alert(`Ошибка удаления коллекции: ${err.message}`);
  }
}
