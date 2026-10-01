/**
 * =============================================================================
 * Process Name: Windows Core - Event-Bus Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля event-bus.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/~webgui/core/event-bus.js?v=20261001_v1" type="module"></script>
 *
 *   JavaScript Import:
 *     import { eventBus } from '/windows/api/~webgui/core/event-bus.js';
 *
 * File: event-bus.js
 * Project: ai-breadboard
 * Package: windows/api/~webgui/core
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-01 13:04:40
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
