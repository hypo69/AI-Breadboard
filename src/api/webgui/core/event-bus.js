/**
 * =============================================================================
 * Process Name: AI-Breadboard UI - Event-Bus Script
 * =============================================================================
 * Description:
 *   Клиентский веб-скрипт модуля event-bus.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/src/api/webgui/core/event-bus.js?v=20261001_v1" type="module"></script>
 *
 *   JavaScript Import:
 *     import { eventBus } from '/src/api/webgui/core/event-bus.js';
 *
 * File: event-bus.js
 * Project: ai-breadboard
 * Package: src/api/webgui/core
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-01 13:13:56
 * =============================================================================
 */

/**
 * CoreEventBus – лёгкая шина событий на базе EventTarget.
 */
class CoreEventBus extends EventTarget {
  on(event, listener) { this.addEventListener(event, listener); }
  off(event, listener) { this.removeEventListener(event, listener); }
  emit(event, detail = null) { this.dispatchEvent(new CustomEvent(event, { detail })); }
}

export const eventBus = new CoreEventBus();
