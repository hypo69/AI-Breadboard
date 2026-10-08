/**
 * =============================================================================
 * Process Name: Windows Js - Ai Table Modal (Legacy Forwarder)
 * =============================================================================
 * Description:
 *   Мост обратной совместимости к выделенному модулю ai_modal_dialog/main.js.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/html/js/ai_table_modal.js?v=20261008_v5"></script>
 *
 * File: ai_table_modal.js
 * Project: ai-breadboard
 * Package: src.api.webgui.js
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-08 12:25:00
 * =============================================================================
 */

// Legacy forwarder for Universal AI Modal Dialog
// Code migrated to: /html/ai_modal_dialog/main.js

if (!window.AIModalDialog) {
  const script = document.createElement('script');
  script.src = '/html/ai_modal_dialog/main.js?v=20261008_v1';
  document.head.appendChild(script);
}
