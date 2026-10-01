/**
 * =============================================================================
 * Process Name: AI-Breadboard UI - Sw Script
 * =============================================================================
 * Description:
 *   Клиентский веб-скрипт модуля sw.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/src/api/webgui/messenger/sw.js?v=20261001_v1" type="module"></script>
 *
 * File: sw.js
 * Project: ai-breadboard
 * Package: src/api/webgui/messenger
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-01 13:13:56
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
