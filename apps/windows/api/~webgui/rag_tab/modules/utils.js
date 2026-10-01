/**
 * =============================================================================
 * Process Name: Windows Modules - Utils Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля utils.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/~webgui/rag_tab/modules/utils.js?v=20261001_v1" type="module"></script>
 *
 *   JavaScript Import:
 *     import { formatBytes, escapeHtml, traverseEntry } from '/windows/api/~webgui/rag_tab/modules/utils.js';
 *
 * File: utils.js
 * Project: ai-breadboard
 * Package: windows/api/~webgui/rag_tab/modules
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-01 13:04:40
 * =============================================================================
 */

/**
 * Format bytes into human-readable string (B, KB, MB, GB).
 *
 * @param {number} bytes - Size in bytes.
 * @returns {string} Formatted size string.
 */
export function formatBytes(bytes) {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

/**
 * Escape HTML special characters to prevent XSS.
 *
 * @param {string} text - Raw string.
 * @returns {string} Escaped HTML string.
 */
export function escapeHtml(text) {
  if (!text) return '';
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

/**
 * Recursively traverse a file system entry.
 *
 * @param {FileSystemEntry} entry - FileSystem entry.
 * @param {string} path - Current relative path.
 * @returns {Promise<File[]>} Array of files with relative paths.
 */
export function traverseEntry(entry, path = '') {
  return new Promise((resolve) => {
    if (entry.isFile) {
      entry.file((file) => {
        const relPath = path ? `${path}/${file.name}` : file.name;
        Object.defineProperty(file, 'customRelativePath', {
          value: relPath,
          writable: true
        });
        resolve([file]);
      }, () => resolve([]));
    } else if (entry.isDirectory) {
      const dirReader = entry.createReader();
      const entries = [];
      const readEntries = () => {
        dirReader.readEntries(async (result) => {
          if (!result.length) {
            const currentPath = path ? `${path}/${entry.name}` : entry.name;
            const promises = entries.map(e => traverseEntry(e, currentPath));
            const nestedFiles = await Promise.all(promises);
            resolve(nestedFiles.flat());
          } else {
            entries.push(...result);
            readEntries();
          }
        }, () => resolve([]));
      };
      readEntries();
    } else {
      resolve([]);
    }
  });
}

/**
 * Extract all files from a DataTransfer object recursively.
 *
 * @param {DataTransfer} dataTransfer - Drag and drop DataTransfer object.
 * @returns {Promise<File[]>} Array of files.
 */
export async function getAllFilesFromDataTransfer(dataTransfer) {
  if (!dataTransfer) return [];
  const items = dataTransfer.items;
  if (items && items.length > 0 && items[0].webkitGetAsEntry) {
    const queue = [];
    for (let i = 0; i < items.length; i++) {
      const entry = items[i].webkitGetAsEntry();
      if (entry) queue.push(traverseEntry(entry));
    }
    const results = await Promise.all(queue);
    return results.flat();
  }
  if (dataTransfer.files && dataTransfer.files.length > 0) {
    return Array.from(dataTransfer.files);
  }
  return [];
}
