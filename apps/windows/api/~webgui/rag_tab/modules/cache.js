/**
 * =============================================================================
 * Process Name: Windows Modules - Cache Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля cache.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/~webgui/rag_tab/modules/cache.js?v=20261001_v1" type="module"></script>
 *
 *   JavaScript Import:
 *     import { CACHE_TAG, updateRagCacheStatus } from '/windows/api/~webgui/rag_tab/modules/cache.js';
 *
 * File: cache.js
 * Project: ai-breadboard
 * Package: windows/api/~webgui/rag_tab/modules
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-01 13:04:40
 * =============================================================================
 */

import { cachedApiFetch, clearCacheByTag } from '../../js/api-cache.js';

export const CACHE_TAG = 'rag';

/**
 * Cached fetch wrapper for RAG tab
 * @param {string} url - API endpoint
 * @param {object} options - Fetch options
 * @returns {Promise<Response>}
 */
export async function ragCachedFetch(url, options = {}) {
  // Merge cache tags
  const tags = options.tags || [];
  if (!tags.includes(CACHE_TAG)) {
    tags.push(CACHE_TAG);
  }
  
  return cachedApiFetch(url, { ...options, tags });
}

/**
 * Clear all RAG cache
 * @returns {Promise<void>}
 */
export async function clearRagCache() {
  await clearCacheByTag(CACHE_TAG);
  console.log('RAG cache cleared');
}

/**
 * Update cache status UI
 */
export function updateRagCacheStatus() {
  const badge = document.getElementById('rag-cache-badge');
  const ratio = document.getElementById('rag-cache-ratio');
  if (!badge || !ratio) return;

  try {
    const stats = window.apiCacheStats || { hits: 0, total: 0 };
    const hitRate = stats.total > 0 ? Math.round((stats.hits / stats.total) * 100) : 0;
    ratio.textContent = `${hitRate}%`;
    
    // Color coding
    badge.className = 'badge cache-badge';
    if (hitRate >= 70) {
      badge.classList.add('bg-success-subtle', 'text-success');
    } else if (hitRate >= 40) {
      badge.classList.add('bg-warning-subtle', 'text-warning');
    } else {
      badge.classList.add('bg-secondary-subtle', 'text-secondary');
    }
  } catch (err) {
    console.debug('Failed to update RAG cache status:', err);
  }
}
