/**
 * =============================================================================
 * Process Name: Windows Messenger - Sw Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля sw.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/webgui/messenger/sw.js?v=20261001_v1" type="module"></script>
 *
 * File: sw.js
 * Project: ai-breadboard
 * Package: windows/api/webgui/messenger
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-01 13:04:40
 * =============================================================================
 */

const CACHE_NAME = 'ai-breadboard-messenger-v1';
const ASSETS = [
  './',
  './index.html',
  './style.css',
  './app.js',
  './manifest.json',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
  );
});

self.addEventListener('fetch', (event) => {
  // Network first, cache fallback
  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});
