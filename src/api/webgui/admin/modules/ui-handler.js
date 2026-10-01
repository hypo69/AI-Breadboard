/**
 * =============================================================================
 * Process Name: AI-Breadboard UI - Ui-Handler Script
 * =============================================================================
 * Description:
 *   Клиентский веб-скрипт модуля ui-handler.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/src/api/webgui/admin/modules/ui-handler.js?v=20261001_v1" type="module"></script>
 *
 *   JavaScript Import:
 *     import { setupUIHandlers, showHelpModal, showChatLogicModal } from '/src/api/webgui/admin/modules/ui-handler.js';
 *
 * File: ui-handler.js
 * Project: ai-breadboard
 * Package: src/api/webgui/admin/modules
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-01 13:13:56
 * =============================================================================
 */

/**
 * UI Handler Module - Работа с модалями, уведомлениями и помощью
 */

let helpContent = {};

export function setupUIHandlers() {
  initHelpContent();
  setupModalHandlers();
}

function initHelpContent() {
  helpContent = {
    'overviewi18n.t('auto__h4_h4_p_ai_breadboard_ai_rag_p__da1ad2')google_oauthi18n.t('auto__h4_google_oauth_h4_p_gmail_drive_sheets_docs_oauth_2_0_service_accounts_p__7943c8')ai_modelsi18n.t('auto__h4_h4_p_gemini_openai_groq_ollama_foundry_directml_p__e73c40')gdrive_synci18n.t('auto__h4_google_drive_sync_h4_p_google_drive_p__0650aa')rag_knowledgei18n.t('auto__h4_rag_h4_p_pdf_word_txt_csv_json_p__44bba4')ragi18n.t('auto__h4_rag_h4_p_strong_1_rag_strong_p_p_strong_2_strong_code_json_code_code_txt_code_code_md_code_code_pdf_code_rag_p_p_strong_3_rag_strong_p__0834f8')voice_ttsi18n.t('auto__h4_h4_p_whisper_webspeech_edge_tts_p__632d68')plugins_skillsi18n.t('auto__h4_mcp_h4_p_telegram_ifttt_mcp_p__d059a6')storage_disksi18n.t('auto__h4_h4_p_p__754fb0')troubleshootingi18n.t('auto__h4_faq_h4_p_p_window_help_content_helpcontent_function_setupmodalhandlers_help_modal_const_helpbtn_document_getelementbyid__9a44e7')help-btn');
  if (helpBtn) {
    helpBtn.addEventListener('click', () => {
      showHelpModal('overview');
    });
  }

  // Chat logic modal
  const chatLogicBtn = document.getElementById('chat-logic-btn');
  if (chatLogicBtn) {
    chatLogicBtn.addEventListener('click', () => {
      showChatLogicModal();
    });
  }
}

export function showHelpModal(key) {
  const content = helpContent[key] || i18n.t('auto__p_p__b6cdfb');
  const contentDiv = document.getElementById('help-modal-content');
  if (contentDiv) {
    contentDiv.innerHTML = content;
  }
  
  const modal = document.getElementById('help-modal');
  if (modal) {
    const m = new bootstrap.Modal(modal);
    m.show();
  }
}

export function showChatLogicModal() {
  const modalEl = document.getElementById('chat-logic-modal');
  if (modalEl) {
    const modal = new bootstrap.Modal(modalEl);
    modal.show();
  }
}

export function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.className = `alert alert-${type} position-fixed top-0 end-0 m-3`;
  notification.style.zIndex = '9999';
  notification.style.maxWidth = '400px';
  notification.textContent = message;
  document.body.appendChild(notification);
  
  setTimeout(() => {
    notification.remove();
  }, 5000);
}

export { initHelpContent, setupModalHandlers };
