/**
 * =============================================================================
 * Process Name: AI-Breadboard UI - Main Script
 * =============================================================================
 * Description:
 *   Клиентский веб-скрипт модуля main.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/src/api/webgui/user_assistant_tab/main.js?v=20261001_v1" type="module"></script>
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: src/api/webgui/user_assistant_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-01 13:13:56
 * =============================================================================
 */

// =============================================================================
// Process Name: User Assistant Web Tab Module
// =============================================================================
// Description:
//   Client-side JavaScript controller for the User Assistant
//   administrative web interface tab.
//
// File: main.js
// Project: ai-breadboard
// Package: src.api.webinterface.user_assistant_tab
// Author: hypo69
// Copyright: © 2026 hypo69
// =============================================================================

(function() {
  let isAssistantInitialized = false;

  async function fetchAgenda() {
    try {
      const res = await fetch('/api/v1/assistant/agenda');
      if (!res.ok) return;
      const data = await res.json();
      
      const eventsCountEl = document.getElementById('assistant-events-count');
      const unreadCountEl = document.getElementById('assistant-unread-count');
      const filesCountEl = document.getElementById('assistant-files-count');
      const eventsBadge = document.getElementById('assistant-events-badge');
      const mailBadge = document.getElementById('assistant-mail-badge');
      const eventsList = document.getElementById('assistant-events-list');
      const mailList = document.getElementById('assistant-mail-listi18n.t('auto__const_events_data_events_const_emails_data_unread_emails_const_files_data_recent_files_if_eventscountel_eventscountel_innertext_events_length_if_unreadcountel_unreadcountel_innertext_emails_length_if_filescountel_filescountel_innertext_files_length_if_eventsbadge_eventsbadge_innertext_events_length_if_mailbadge_mailbadge_innertext_emails_length_if_eventslist_if_events_length_0_eventslist_innerhtml__90f964')<div class="p-3 text-muted text-center small">Нет запланированных событий на сегодня.</div>';
        } else {
          eventsList.innerHTML = events.map(e => `
            <div class="assistant-list-item d-flex justify-content-between align-items-center">
              <div>
                <div class="fw-semibold text-light">${e.summary || i18n.t('auto___32b74a')}</div>
                <div class="text-secondary small">⏰ ${e.start || i18n.t('auto___7bd841')} ${e.location ? '📍 ' + e.location : ''}</div>
              </div>
            </div>
          `).join('');
        }
      }

      if (mailList) {
        if (emails.length === 0) {
          mailList.innerHTML = '<div class="p-3 text-muted text-center small">Нет новых непрочитанных сообщений.</div>';
        } else {
          mailList.innerHTML = emails.map(m => `
            <div class="assistant-list-item d-flex justify-content-between align-items-center">
              <div>
                <div class="fw-semibold text-light">${m.subject || i18n.t('auto___43b108')}</div>
                <div class="text-secondary small">👤 ${m.from || i18n.t('auto___3f2757')} &bull; ${m.snippet || ''}</div>
              </div>
            </div>
          `).join('');
        }
      }
    } catch (e) {
      console.error('[UserAssistantTab] Failed to fetch agenda:', e);
    }
  }

  function initUserAssistantTab() {
    fetchAgenda();
    if (!isAssistantInitialized) {
      const refreshBtn = document.getElementById('btn-assistant-refresh');
      if (refreshBtn) refreshBtn.addEventListener('click', fetchAgenda);

      const configBtn = document.getElementById('btn-assistant-config');
      if (configBtn) {
        configBtn.addEventListener('click', () => {
          if (typeof window.openAppConfigModal === 'function') {
            window.openAppConfigModal('user_assistant');
          }
        });
      }
      isAssistantInitialized = true;
    }
  }

  window.initUserAssistantTab = initUserAssistantTab;
})();
