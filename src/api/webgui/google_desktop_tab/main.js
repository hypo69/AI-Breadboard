/**
 * google_desktop_tab/main.js — Веб-модуль управления Google User Desktop в AI Breadboard.
 */

(function () {
  'use strict';

  function formatBytes(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }

  function formatDate(isoStr) {
    if (!isoStr) return '-';
    try {
      const d = new Date(isoStr);
      if (isNaN(d.getTime())) return isoStr;
      return d.toLocaleString('ru-RU', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch (e) {
      return isoStr;
    }
  }

  async function fetchStatus() {
    try {
      const res = await fetch('/api/google-desktop/status');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      updateStatusUI(data);
    } catch (err) {
      console.error('[GoogleDesktopTab] Failed to fetch status:', err);
    }
  }

  function updateStatusUI(data) {
    const acc = data.account || {};
    const nameEl = document.getElementById('gdesktop-acc-name');
    const statusEl = document.getElementById('gdesktop-acc-status');
    const mailCountEl = document.getElementById('gdesktop-mail-count');
    const calCountEl = document.getElementById('gdesktop-calendar-count');
    const docsDriveCountEl = document.getElementById('gdesktop-docs-drive-count');
    const lastRefreshedEl = document.getElementById('gdesktop-last-refreshed');

    if (nameEl) nameEl.textContent = acc.name || 'Не выбран';
    if (statusEl) {
      statusEl.textContent = acc.status || 'unconfigured';
      statusEl.className = acc.status === 'active' ? 'badge bg-success' : 'badge bg-warning text-dark';
    }

    if (mailCountEl) mailCountEl.textContent = data.mail_count || 0;
    if (calCountEl) calCountEl.textContent = data.calendar_events_count || 0;
    if (docsDriveCountEl) docsDriveCountEl.textContent = `${data.docs_count || 0} / ${data.drive_files_count || 0}`;

    if (lastRefreshedEl) {
      lastRefreshedEl.textContent = `Обновлено: ${formatDate(data.last_refreshed)}`;
    }
  }

  async function fetchAccounts() {
    try {
      const res = await fetch('/api/google-desktop/accounts');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const selectEl = document.getElementById('gdesktop-account-select');
      if (!selectEl) return;

      selectEl.innerHTML = '';
      const accounts = data.accounts || [];
      const active = data.active_account || {};

      if (accounts.length === 0) {
        const opt = document.createElement('option');
        opt.value = '';
        opt.textContent = 'Нет аккаунтов (unconfigured)';
        selectEl.appendChild(opt);
        return;
      }

      accounts.forEach((a) => {
        const opt = document.createElement('option');
        opt.value = a.name;
        opt.textContent = `${a.name} (${a.email || a.type})${a.is_default ? ' ★' : ''}`;
        if (a.name === active.name) {
          opt.selected = true;
        }
        selectEl.appendChild(opt);
      });
    } catch (err) {
      console.error('[GoogleDesktopTab] Failed to fetch accounts:', err);
    }
  }

  async function selectAccount(accName) {
    if (!accName) return;
    try {
      const res = await fetch(`/api/google-desktop/accounts/select?account_name=${encodeURIComponent(accName)}`, {
        method: 'POST',
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      await refreshAllData();
      if (window.toast) window.toast.success('Google Desktop', `Активный аккаунт изменен на ${accName}`);
    } catch (err) {
      console.error('[GoogleDesktopTab] Failed to select account:', err);
      if (window.toast) window.toast.error('Ошибка выбора аккаунта', err.message);
    }
  }

  async function fetchMail() {
    const tbody = document.getElementById('gdesktop-mail-tbody');
    if (!tbody) return;
    try {
      const res = await fetch('/api/google-desktop/mail/messages?limit=20');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const msgs = data.messages || [];
      if (msgs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center py-3 text-muted">Входящие сообщения отсутствуют.</td></tr>';
        return;
      }
      tbody.innerHTML = msgs
        .map(
          (m) => `
        <tr>
          <td class="fw-semibold text-info text-truncate" style="max-width: 200px;">${escapeHtml(m.sender || 'Неизвестно')}</td>
          <td class="text-light fw-bold">${escapeHtml(m.subject || '(Без темы)')}</td>
          <td class="text-secondary small">${escapeHtml(formatDate(m.date))}</td>
          <td class="text-muted small text-truncate" style="max-width: 350px;">${escapeHtml(m.snippet || '')}</td>
        </tr>
      `
        )
        .join('');
    } catch (err) {
      console.error('[GoogleDesktopTab] Failed to fetch mail:', err);
      tbody.innerHTML = `<tr><td colspan="4" class="text-center py-3 text-danger">Ошибка загрузки почты: ${err.message}</td></tr>`;
    }
  }

  async function fetchCalendar() {
    const tbody = document.getElementById('gdesktop-calendar-tbody');
    if (!tbody) return;
    try {
      const res = await fetch('/api/google-desktop/calendar/events?limit=20');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const events = data.events || [];
      if (events.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center py-3 text-muted">Предстоящие события отсутствуют.</td></tr>';
        return;
      }
      tbody.innerHTML = events
        .map(
          (e) => `
        <tr>
          <td class="fw-bold text-light">${escapeHtml(e.summary || 'Без названия')}</td>
          <td class="text-info small">${escapeHtml(formatDate(e.start_time))}</td>
          <td class="text-secondary small">${escapeHtml(formatDate(e.end_time))}</td>
          <td class="text-muted small text-truncate" style="max-width: 180px;">${escapeHtml(e.location || '-')}</td>
          <td class="text-center">
            ${
              e.html_link
                ? `<a href="${e.html_link}" target="_blank" class="btn btn-xs btn-outline-info rounded-pill py-0 px-2" title="Открыть в Google Calendar"><i class="bi bi-box-arrow-up-right"></i></a>`
                : '-'
            }
          </td>
        </tr>
      `
        )
        .join('');
    } catch (err) {
      console.error('[GoogleDesktopTab] Failed to fetch calendar events:', err);
      tbody.innerHTML = `<tr><td colspan="5" class="text-center py-3 text-danger">Ошибка загрузки событий: ${err.message}</td></tr>`;
    }
  }

  async function fetchDocs() {
    const tbody = document.getElementById('gdesktop-docs-tbody');
    if (!tbody) return;
    try {
      const res = await fetch('/api/google-desktop/docs/list?limit=20');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const docs = data.documents || [];
      if (docs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center py-3 text-muted">Документы не найдены.</td></tr>';
        return;
      }
      tbody.innerHTML = docs
        .map(
          (d) => `
        <tr>
          <td class="fw-bold text-light">${escapeHtml(d.name || 'Без названия')}</td>
          <td class="text-secondary small text-truncate" style="max-width: 220px;">${escapeHtml(d.mime_type || '')}</td>
          <td class="text-secondary small">${escapeHtml(formatDate(d.modified_time))}</td>
          <td class="text-center">
            <div class="btn-group btn-group-sm">
              <button class="btn btn-xs btn-outline-primary rounded-start py-0 px-2 btn-view-doc" data-doc-id="${d.id}" data-doc-name="${escapeHtml(
            d.name
          )}" title="Просмотреть текст"><i class="bi bi-eye"></i> Текст</button>
              ${
                d.web_view_link
                  ? `<a href="${d.web_view_link}" target="_blank" class="btn btn-xs btn-outline-secondary rounded-end py-0 px-2" title="Открыть в браузер"><i class="bi bi-box-arrow-up-right"></i></a>`
                  : ''
              }
            </div>
          </td>
        </tr>
      `
        )
        .join('');

      tbody.querySelectorAll('.btn-view-doc').forEach((btn) => {
        btn.addEventListener('click', () => {
          const docId = btn.getAttribute('data-doc-id');
          const docName = btn.getAttribute('data-doc-name');
          openDocumentViewer(docId, docName);
        });
      });
    } catch (err) {
      console.error('[GoogleDesktopTab] Failed to fetch docs:', err);
      tbody.innerHTML = `<tr><td colspan="4" class="text-center py-3 text-danger">Ошибка загрузки документов: ${err.message}</td></tr>`;
    }
  }

  async function fetchDrive() {
    const tbody = document.getElementById('gdesktop-drive-tbody');
    if (!tbody) return;
    try {
      const res = await fetch('/api/google-desktop/drive/files?limit=20');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const files = data.files || [];
      if (files.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center py-3 text-muted">Файлы на Google Диске отсутствуют.</td></tr>';
        return;
      }
      tbody.innerHTML = files
        .map(
          (f) => `
        <tr>
          <td class="fw-bold text-light">${escapeHtml(f.name || 'Без названия')}</td>
          <td class="text-secondary small text-truncate" style="max-width: 220px;">${escapeHtml(f.mime_type || '')}</td>
          <td class="text-info small font-monospace">${formatBytes(f.size_bytes)}</td>
          <td class="text-secondary small">${escapeHtml(formatDate(f.modified_time))}</td>
          <td class="text-center">
            ${
              f.web_view_link
                ? `<a href="${f.web_view_link}" target="_blank" class="btn btn-xs btn-outline-info rounded-pill py-0 px-2" title="Открыть на Google Диске"><i class="bi bi-box-arrow-up-right"></i></a>`
                : '-'
            }
          </td>
        </tr>
      `
        )
        .join('');
    } catch (err) {
      console.error('[GoogleDesktopTab] Failed to fetch drive files:', err);
      tbody.innerHTML = `<tr><td colspan="5" class="text-center py-3 text-danger">Ошибка загрузки файлов: ${err.message}</td></tr>`;
    }
  }

  async function openDocumentViewer(docId, docName) {
    const modalEl = document.getElementById('gdesktopDocViewerModal');
    const titleEl = document.getElementById('gdesktop-doc-modal-title');
    const bodyEl = document.getElementById('gdesktop-doc-modal-body');
    if (!modalEl || !bodyEl) return;

    if (titleEl) titleEl.textContent = docName || `Документ ${docId}`;
    bodyEl.textContent = 'Загрузка содержимого...';

    const modal = new bootstrap.Modal(modalEl);
    modal.show();

    try {
      const res = await fetch(`/api/google-desktop/docs/${encodeURIComponent(docId)}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      bodyEl.textContent = data.content || '(Документ пуст)';
    } catch (err) {
      bodyEl.textContent = `Ошибка загрузки содержимого документа: ${err.message}`;
    }
  }

  async function triggerSync() {
    const syncBtn = document.getElementById('btn-gdesktop-sync');
    if (syncBtn) {
      syncBtn.disabled = true;
      syncBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Синхронизация...';
    }
    try {
      const res = await fetch('/api/google-desktop/sync', { method: 'POST' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (data.state) updateStatusUI(data.state);
      await refreshAllData();
      if (window.toast) window.toast.success('Синхронизация завершена', 'Данные Google Workspace принудительно обновлены');
    } catch (err) {
      console.error('[GoogleDesktopTab] Sync failed:', err);
      if (window.toast) window.toast.error('Ошибка синхронизации', err.message);
    } finally {
      if (syncBtn) {
        syncBtn.disabled = false;
        syncBtn.innerHTML = '<i class="bi bi-cloud-arrow-down-fill me-1"></i> Синхронизация';
      }
    }
  }

  async function refreshAllData() {
    await Promise.all([fetchStatus(), fetchAccounts(), fetchMail(), fetchCalendar(), fetchDocs(), fetchDrive()]);
  }

  function escapeHtml(str) {
    if (typeof str !== 'string') return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function initGoogleDesktopTab() {
    console.log('[GoogleDesktopTab] Initializing Google User Desktop tab...');

    const refreshBtn = document.getElementById('btn-gdesktop-refresh');
    if (refreshBtn) {
      refreshBtn.onclick = () => refreshAllData();
    }

    const syncBtn = document.getElementById('btn-gdesktop-sync');
    if (syncBtn) {
      syncBtn.onclick = () => triggerSync();
    }

    const selectEl = document.getElementById('gdesktop-account-select');
    if (selectEl) {
      selectEl.onchange = (e) => selectAccount(e.target.value);
    }

    refreshAllData();
  }

  window.initGoogleDesktopTab = initGoogleDesktopTab;
})();
