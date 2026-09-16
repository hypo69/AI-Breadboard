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
      const mailList = document.getElementById('assistant-mail-list');

      const events = data.events || [];
      const emails = data.unread_emails || [];
      const files = data.recent_files || [];

      if (eventsCountEl) eventsCountEl.innerText = events.length;
      if (unreadCountEl) unreadCountEl.innerText = emails.length;
      if (filesCountEl) filesCountEl.innerText = files.length;
      if (eventsBadge) eventsBadge.innerText = `${events.length} событий`;
      if (mailBadge) mailBadge.innerText = `${emails.length} писем`;

      if (eventsList) {
        if (events.length === 0) {
          eventsList.innerHTML = '<div class="p-3 text-muted text-center small">Нет запланированных событий на сегодня.</div>';
        } else {
          eventsList.innerHTML = events.map(e => `
            <div class="assistant-list-item d-flex justify-content-between align-items-center">
              <div>
                <div class="fw-semibold text-light">${e.summary || 'Без названия'}</div>
                <div class="text-secondary small">⏰ ${e.start || 'Весь день'} ${e.location ? '📍 ' + e.location : ''}</div>
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
                <div class="fw-semibold text-light">${m.subject || 'Без темы'}</div>
                <div class="text-secondary small">👤 ${m.from || 'Неизвестный'} &bull; ${m.snippet || ''}</div>
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
