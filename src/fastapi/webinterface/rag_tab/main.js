/**
 * =============================================================================
 * Process Name: RAG Tab Master Coordinator
 * =============================================================================
 * Description:
 *   Entry point and coordinator for the Knowledge Base & RAG interface.
 *   Dispatches events to specialized submodules.
 *
 * File: main.js
 * Project: AI Breadboard
 * Module: RAGTab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * =============================================================================
 */

import { getAllFilesFromDataTransfer } from './modules/utils.js';
import {
  uploadFiles,
  loadRagStatus,
  loadRagDocuments,
  deleteRagDocument,
  buildRagIndex,
  executeRagSearch
} from './modules/docRag.js';
import {
  loadCodebaseIndexes,
  updateCodebaseStatsDisplay,
  buildCodebaseRag,
  executeCodebaseSearch,
  executeSymbolLookup
} from './modules/codebaseRag.js';
import {
  loadUserRags,
  createUserRag,
  deleteActiveUserRag
} from './modules/userRagCollections.js';
import {
  buildActiveUserRag,
  executeActiveUserRagSearch,
  handleQuickUploadToUserStorage
} from './modules/userRagPipeline.js';

let isInitialized = false;

/**
 * Initialize all RAG tab components, event listeners, and data feeds.
 *
 * @returns {Promise<void>}
 */
export async function initRagTab() {
  if (isInitialized) {
    loadUserRags();
    loadRagStatus();
    loadRagDocuments();
    loadCodebaseIndexes();
    return;
  }
  isInitialized = true;
  setupEventListeners();
  loadUserRags();
  loadRagStatus();
  loadRagDocuments();
  loadCodebaseIndexes();
}

// Expose globals for external tab orchestrators and inline handlers
window.initRagTab = initRagTab;
window.deleteRagDocument = deleteRagDocument;

/**
 * Register DOM event listeners for buttons, inputs, dropzones, and keyboard events.
 */
function setupEventListeners() {
  const refreshBtn = document.getElementById('btn-refresh-rag');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', () => {
      loadUserRags();
      loadRagStatus();
      loadRagDocuments();
      loadCodebaseIndexes();
    });
  }

  // --- User Workspace RAG Listeners ---
  const confirmCreateRagBtn = document.getElementById('btn-confirm-create-rag');
  if (confirmCreateRagBtn) {
    confirmCreateRagBtn.addEventListener('click', createUserRag);
  }

  const buildActiveRagBtn = document.getElementById('btn-build-active-rag');
  if (buildActiveRagBtn) {
    buildActiveRagBtn.addEventListener('click', buildActiveUserRag);
  }

  const deleteActiveRagBtn = document.getElementById('btn-delete-active-rag');
  if (deleteActiveRagBtn) {
    deleteActiveRagBtn.addEventListener('click', deleteActiveUserRag);
  }

  const searchActiveRagBtn = document.getElementById('btn-active-rag-search');
  const searchActiveRagInput = document.getElementById('active-rag-search-query');
  if (searchActiveRagBtn) {
    searchActiveRagBtn.addEventListener('click', executeActiveUserRagSearch);
  }
  if (searchActiveRagInput) {
    searchActiveRagInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') executeActiveUserRagSearch();
    });
  }

  const quickUploadInput = document.getElementById('user-rag-quick-upload-input');
  if (quickUploadInput) {
    quickUploadInput.addEventListener('change', handleQuickUploadToUserStorage);
  }

  const selectAllBtn = document.getElementById('btn-select-all-user-files');
  if (selectAllBtn) {
    selectAllBtn.addEventListener('click', () => {
      const checkboxes = document.querySelectorAll('#user-rag-files-checklist input[type="checkbox"]');
      const anyUnchecked = Array.from(checkboxes).some(cb => !cb.checked);
      checkboxes.forEach(cb => cb.checked = anyUnchecked);
    });
  }

  // --- Global Document RAG Listeners ---
  const fileInput = document.getElementById('rag-file-input');
  const folderInput = document.getElementById('rag-folder-input');
  const dropzone = document.getElementById('rag-dropzone');

  if (fileInput) {
    fileInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files.length > 0) {
        uploadFiles(Array.from(e.target.files));
        fileInput.value = '';
      }
    });
  }

  if (folderInput) {
    folderInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files.length > 0) {
        uploadFiles(Array.from(e.target.files));
        folderInput.value = '';
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

    dropzone.addEventListener('drop', async (e) => {
      const dt = e.dataTransfer;
      if (dt) {
        const files = await getAllFilesFromDataTransfer(dt);
        if (files && files.length > 0) {
          uploadFiles(files);
        }
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
      if (e.key === 'Enter') executeRagSearch();
    });
  }

  // --- Codebase RAG Listeners ---
  const btnRefreshCodebase = document.getElementById('btn-refresh-codebase-indexes');
  if (btnRefreshCodebase) {
    btnRefreshCodebase.addEventListener('click', loadCodebaseIndexes);
  }

  const btnBuildCodebase = document.getElementById('btn-build-codebase-rag');
  if (btnBuildCodebase) {
    btnBuildCodebase.addEventListener('click', buildCodebaseRag);
  }

  const btnCodeSearch = document.getElementById('btn-codebase-search');
  const inputCodeSearch = document.getElementById('codebase-search-query');
  if (btnCodeSearch) {
    btnCodeSearch.addEventListener('click', executeCodebaseSearch);
  }
  if (inputCodeSearch) {
    inputCodeSearch.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') executeCodebaseSearch();
    });
  }

  const btnSymbolSearch = document.getElementById('btn-codebase-symbol-search');
  const inputSymbolSearch = document.getElementById('codebase-symbol-query');
  if (btnSymbolSearch) {
    btnSymbolSearch.addEventListener('click', executeSymbolLookup);
  }
  if (inputSymbolSearch) {
    inputSymbolSearch.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') executeSymbolLookup();
    });
  }

  const activeIndexSelect = document.getElementById('codebase-active-index-select');
  if (activeIndexSelect) {
    activeIndexSelect.addEventListener('change', updateCodebaseStatsDisplay);
  }
}

// Auto-initialize when loaded or DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initRagTab);
} else {
  initRagTab();
}
