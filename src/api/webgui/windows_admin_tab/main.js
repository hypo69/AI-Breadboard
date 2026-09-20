// =============================================================================
// Process Name: Windows System Administrator Web Tab Module
// =============================================================================
// Description:
//   Client-side JavaScript controller for the Windows System Administrator
//   administrative web interface tab with File Deletion Auditing (4663/4660) & Live Changes.
//
// File: main.js
// Project: ai-breadboard
// Package: src.api.webinterface.windows_admin_tab
// Author: hypo69
// Copyright: © 2026 hypo69
// =============================================================================

(function() {
  let isWinAdminInitialized = false;

  async function fetchStatus() {
    try {
      const res = await fetch('/api/sysadmin/status');
      if (!res.ok) return;
      const data = await res.json();
      
      const hostEl = document.getElementById('winadmin-hostname');
      const userCountEl = document.getElementById('winadmin-user-count');
      const adStatusEl = document.getElementById('winadmin-ad-status');
      const eventsCountEl = document.getElementById('winadmin-events-count');

      if (hostEl) hostEl.innerText = `${data.hostname || 'LOCAL'} / ${data.domain || 'WORKGROUP'}`;
      if (userCountEl) userCountEl.innerText = data.user_count || 0;
      if (adStatusEl) adStatusEl.innerText = data.ad_connected ? 'Подключен' : 'Локальный хост';
      if (eventsCountEl) eventsCountEl.innerText = data.event_count || 0;
    } catch (e) {
      console.error('[WinAdminTab] Failed to fetch status:', e);
    }
  }

  async function fetchUsers() {
    try {
      const res = await fetch('/api/sysadmin/users');
      if (!res.ok) return;
      const data = await res.json();
      const users = data.users || [];
      
      const tbody = document.getElementById('winadmin-users-tbody');
      const badge = document.getElementById('winadmin-users-badge');
      if (badge) badge.innerText = `${users.length} сессий`;

      if (tbody) {
        if (users.length === 0) {
          tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted p-3">Нет активных сессий</td></tr>';
          return;
        }
        tbody.innerHTML = users.map((u, idx) => `
          <tr class="winadmin-user-row" data-idx="${idx}" style="cursor: pointer;" title="Нажмите для AI-аудита прав пользователя">
            <td class="fw-semibold text-white"><i class="bi bi-person me-1"></i> ${u.username}</td>
            <td class="font-monospace">${u.session_id}</td>
            <td><span class="badge ${u.status === 'Active' ? 'bg-success-subtle text-success' : 'bg-secondary'}">${u.status}</span></td>
            <td class="font-monospace text-muted">${u.ip_address || '127.0.0.1'}</td>
            <td style="text-align: right;">
              <button class="btn btn-sm btn-outline-danger py-0 px-2 btn-disconnect-user" data-user="${u.username}">
                Отключить
              </button>
            </td>
          </tr>
        `).join('');

        tbody.querySelectorAll('.winadmin-user-row').forEach(row => {
          row.onclick = (evt) => {
            if (evt.target.closest('.btn-disconnect-user')) return;
            const idx = parseInt(row.getAttribute('data-idx'), 10);
            const u = users[idx];
            if (!u) return;

            if (window.AITableModal) {
              window.AITableModal.show({
                icon: '👤',
                title: u.username,
                subtitle: `Сессия: ${u.session_id} | Статус: ${u.status}`,
                tableType: 'user',
                badges: [
                  { text: u.status || 'Active', class: u.status === 'Active' ? 'badge bg-success' : 'badge bg-secondary' }
                ],
                metadata: [
                  { label: 'Имя пользователя', value: u.username },
                  { label: 'ID сессии', value: String(u.session_id) },
                  { label: 'Статус сессии', value: u.status },
                  { label: 'IP адрес клиента', value: u.ip_address || '127.0.0.1' },
                  { label: 'Время входа', value: u.logon_time || 'N/A' }
                ],
                rawTitle: 'Параметры сессии пользователя',
                rawContent: JSON.stringify(u, null, 2),
                requestData: {
                  username: u.username,
                  session_id: u.session_id,
                  ip_address: u.ip_address
                }
              });
            }
          };
        });

        tbody.querySelectorAll('.btn-disconnect-user').forEach(btn => {
          btn.onclick = async (evt) => {
            evt.stopPropagation();
            const user = btn.getAttribute('data-user');
            if (confirm(`Отключить сессию пользователя ${user}?`)) {
              await fetch(`/api/sysadmin/users/${user}/disconnect`, { method: 'POST' });
              fetchUsers();
              fetchStatus();
            }
          };
        });
      }
    } catch (e) {
      console.error('[WinAdminTab] Failed to fetch users:', e);
    }
  }

  async function fetchEvents() {
    try {
      const res = await fetch('/api/sysadmin/events?hours=24');
      if (!res.ok) return;
      const data = await res.json();
      const events = data.events || [];
      
      const tbody = document.getElementById('winadmin-events-tbody');
      const badge = document.getElementById('winadmin-events-badge');
      if (badge) badge.innerText = `${events.length} записей`;

      if (tbody) {
        if (events.length === 0) {
          tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted p-3">События не зафиксированы</td></tr>';
          return;
        }
        const displayEvents = events.slice(0, 30);
        tbody.innerHTML = displayEvents.map((e, idx) => `
          <tr class="winadmin-event-row" data-idx="${idx}" style="cursor: pointer;" title="Нажмите для AI-диагностики события">
            <td class="font-monospace text-muted small">${e.timestamp?.slice(11, 19) || ''}</td>
            <td class="font-monospace fw-semibold text-info">${e.event_id}</td>
            <td><span class="badge ${e.level === 'Warning' ? 'bg-warning-subtle text-warning' : (e.level === 'Error' ? 'bg-danger-subtle text-danger' : 'bg-info-subtle text-info')}">${e.level}</span></td>
            <td class="small text-light">${e.source}: ${e.description}</td>
          </tr>
        `).join('');

        tbody.querySelectorAll('.winadmin-event-row').forEach(row => {
          row.onclick = () => {
            const idx = parseInt(row.getAttribute('data-idx'), 10);
            const e = displayEvents[idx];
            if (!e) return;

            if (window.AITableModal) {
              window.AITableModal.show({
                icon: '📋',
                title: `Событие #${e.event_id} (${e.source})`,
                subtitle: `Уровень: ${e.level} | ${e.timestamp || ''}`,
                tableType: 'generic',
                badges: [
                  { text: e.level || 'Info', class: 'badge bg-info text-dark' }
                ],
                metadata: [
                  { label: 'Event ID', value: String(e.event_id) },
                  { label: 'Источник / Provider', value: e.source },
                  { label: 'Уровень важности', value: e.level },
                  { label: 'Время регистрации', value: e.timestamp }
                ],
                rawTitle: 'Текст сообщения журнала',
                rawContent: e.description || '',
                requestData: {
                  event_id: e.event_id,
                  source: e.source,
                  level: e.level,
                  description: e.description
                }
              });
            }
          };
        });
      }
    } catch (e) {
      console.error('[WinAdminTab] Failed to fetch events:', e);
    }
  }

  async function fetchFileDeletions() {
    try {
      const res = await fetch('/api/sysadmin/file-audit/deletions?hours=24&limit=100&deletions_only=true');
      if (!res.ok) return;
      const data = await res.json();
      const events = data.events || [];
      
      const tbody = document.getElementById('winadmin-deletions-tbody');
      const badge = document.getElementById('winadmin-deletions-badge');
      const countEl = document.getElementById('winadmin-deletions-count');

      if (badge) badge.innerText = `${events.length} удалений`;
      if (countEl) countEl.innerText = events.length;

      if (tbody) {
        if (events.length === 0) {
          tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted p-3">События удаления (4663/4660) не зафиксированы или аудит не включен</td></tr>';
          return;
        }
        tbody.innerHTML = events.slice(0, 30).map((e, idx) => `
          <tr class="winadmin-deletion-row" data-idx="${idx}" style="cursor: pointer;" title="Нажмите для детального AI-расследования удаления">
            <td class="font-monospace text-muted small">${e.timestamp?.slice(11, 19) || ''}</td>
            <td class="font-monospace fw-semibold ${e.event_id === 4660 ? 'text-danger' : 'text-warning'}">${e.event_id}</td>
            <td class="font-monospace text-truncate text-white" style="max-width: 260px;" title="${e.object_name}">${e.object_name.split('\\').pop() || e.object_name}</td>
            <td class="small text-info text-truncate" style="max-width: 140px;" title="${e.process_name}">${e.process_name ? e.process_name.split('\\').pop() : 'N/A'}</td>
            <td class="small text-muted">${e.subject_user_name || 'SYSTEM'}</td>
          </tr>
        `).join('');

        tbody.querySelectorAll('.winadmin-deletion-row').forEach(row => {
          row.onclick = () => {
            const idx = parseInt(row.getAttribute('data-idx'), 10);
            const e = events[idx];
            if (!e) return;

            if (window.AITableModal) {
              window.AITableModal.show({
                icon: '🗑️',
                title: `Удаление: ${e.object_name.split('\\').pop() || e.object_name}`,
                subtitle: `Event ID: ${e.event_id} | ${e.timestamp}`,
                tableType: 'security_event',
                badges: [
                  { text: `Event ${e.event_id}`, class: e.event_id === 4660 ? 'badge bg-danger' : 'badge bg-warning text-dark' },
                  { text: e.status || 'Success', class: 'badge bg-success' }
                ],
                metadata: [
                  { label: 'Целевой объект', value: e.object_name },
                  { label: 'Тип объекта', value: e.object_type || 'File' },
                  { label: 'Процесс-инициатор', value: e.process_name || 'Не указан' },
                  { label: 'PID процесса', value: e.process_id ? String(e.process_id) : 'N/A' },
                  { label: 'Пользователь', value: `${e.subject_domain_name}\\${e.subject_user_name}` },
                  { label: 'Дескриптор HandleId', value: e.handle_id || 'N/A' },
                  { label: 'Маска доступа', value: e.access_mask || 'DELETE (0x10000)' }
                ],
                rawTitle: 'Полное сообщение Security Log',
                rawContent: e.raw_message || JSON.stringify(e, null, 2),
                requestData: e
              });
            }
          };
        });
      }
    } catch (e) {
      console.error('[WinAdminTab] Failed to fetch deletion events:', e);
    }
  }

  let currentWatchDir = '';

  async function fetchLiveFileEvents() {
    try {
      const res = await fetch('/api/sysadmin/file-audit/live-events?limit=30');
      if (!res.ok) return;
      const data = await res.json();
      const events = data.events || [];
      currentWatchDir = data.watch_dir || '';
      
      const dirPathEl = document.getElementById('winadmin-watch-dir-path');
      if (dirPathEl) {
        dirPathEl.innerText = currentWatchDir ? (currentWatchDir.split('\\').pop() || currentWatchDir) : 'Рабочая папка';
        const badge = document.getElementById('winadmin-watch-dir-badge');
        if (badge) badge.title = `Отслеживаемая директория:\n${currentWatchDir}\n(Нажмите для смены папки)`;
      }

      const tbody = document.getElementById('winadmin-live-tbody');
      if (tbody) {
        if (events.length === 0) {
          tbody.innerHTML = `<tr><td colspan="3" class="text-center text-muted p-2">Ожидание изменений в папке <code>${currentWatchDir || 'проекта'}</code>...</td></tr>`;
          return;
        }
        tbody.innerHTML = events.map((e, idx) => `
          <tr class="winadmin-live-row" data-idx="${idx}" style="cursor: pointer;" title="Нажмите для AI-диагностики события">
            <td class="font-monospace text-muted small">${e.timestamp?.slice(11, 19) || ''}</td>
            <td><span class="badge ${e.is_deletion ? 'bg-danger' : (e.action === 'Created' ? 'bg-success' : 'bg-secondary')}">${e.action}</span></td>
            <td class="font-monospace text-truncate small" style="max-width: 240px;" title="${e.path}">${e.path.split('\\').pop() || e.path}</td>
          </tr>
        `).join('');

        tbody.querySelectorAll('.winadmin-live-row').forEach(row => {
          row.onclick = () => {
            const idx = parseInt(row.getAttribute('data-idx'), 10);
            const e = events[idx];
            if (!e) return;

            if (window.AITableModal) {
              window.AITableModal.show({
                icon: '⚡',
                title: `Файловое событие: ${e.action}`,
                subtitle: `${e.path.split('\\').pop() || e.path} | ${e.timestamp}`,
                tableType: 'file_event',
                badges: [
                  { text: e.action, class: e.is_deletion ? 'badge bg-danger' : (e.action === 'Created' ? 'badge bg-success' : 'badge bg-info text-dark') },
                  { text: 'WinAPI ReadDirectoryChangesW', class: 'badge bg-dark border border-secondary text-info' }
                ],
                metadata: [
                  { label: 'Действие', value: e.action },
                  { label: 'Полный путь', value: e.path },
                  { label: 'Время события', value: e.timestamp },
                  { label: 'Признак удаления', value: e.is_deletion ? 'Да (Файл удален/переименован)' : 'Нет' },
                  { label: 'Отслеживаемый корень', value: currentWatchDir }
                ],
                rawTitle: 'Детали события WinAPI',
                rawContent: JSON.stringify(e, null, 2),
                requestData: e
              });
            }
          };
        });
      }
    } catch (e) {
      console.error('[WinAdminTab] Failed to fetch live file events:', e);
    }
  }

  async function promptChangeWatchDir() {
    const defaultVal = currentWatchDir || 'C:\\Users\\onela\\AppData\\Local\\AI-Breadboard';
    const newPath = prompt('Укажите абсолютный путь к папке для мониторинга в реальном времени:\n(Путь будет сохранен в config.json)', defaultVal);
    if (!newPath || newPath.trim() === '' || newPath.trim() === currentWatchDir) return;

    try {
      const res = await fetch('/api/sysadmin/file-audit/watch-dir', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: newPath.trim() })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        alert(`✅ ${data.message}`);
        fetchLiveFileEvents();
      } else {
        alert(`❌ Ошибка: ${data.detail || data.error || 'Не удалось сменить директорию'}`);
      }
    } catch (err) {
      alert(`❌ Ошибка подключения: ${err.message}`);
    }
  }

  function showLiveWatcherHelpModal() {
    if (window.AITableModal) {
      window.AITableModal.show({
        icon: 'ℹ️',
        title: 'Справка: Real-Time Live Watcher',
        subtitle: 'Низкоуровневый мониторинг файловой системы Windows через WinAPI ReadDirectoryChangesW',
        tableType: 'help',
        badges: [
          { text: 'WinAPI', class: 'badge bg-info text-dark' },
          { text: 'Real-Time Streaming', class: 'badge bg-success' },
          { text: 'Рекурсивно', class: 'badge bg-warning text-dark' }
        ],
        metadata: [
          { label: 'Технология', value: 'WinAPI ReadDirectoryChangesW (нативный вызов ядра Windows kernel32.dll)' },
          { label: 'Область слежения', value: 'Выбранная папка и ВСЕ её подкаталоги рекурсивно (bWatchSubtree = True)' },
          { label: 'Текущий путь', value: currentWatchDir || 'Рабочая папка проекта' },
          { label: 'Хранение настроек', value: 'apps/windows_sysadmin/config.json (ключ watch_directory)' }
        ],
        rawTitle: 'Подробное руководство по панели мониторинга',
        rawContent: `# Панель Real-Time Live Watcher

### 1. Что это такое?
Это компонент модуля Windows SysAdmin для мгновенного перехвата операций файловой системы в режиме реального времени без обращения к журналам событий Windows Security Log (где требуется включение SACL/auditpol).

### 2. Типы отслеживаемых действий:
- Created: Создание нового файла или папки (FILE_ACTION_ADDED).
- Modified: Модификация содержимого, атрибутов или размера файла (FILE_ACTION_MODIFIED).
- Deleted: Удаление файла или папки с диска (FILE_ACTION_REMOVED).
- Renamed: Переименование объекта (старое и новое имя).

### 3. Почему видны файлы History-journal, Cache_Data, f_000xxx?
ReadDirectoryChangesW регистрирует ЛЮБЫЕ изменения внутри указанной папки. Если внутри директории работает браузер, Electron, WebView2 или SQLite базы данных:
- *-journal, *-wal: Это временные журналы транзакций баз данных SQLite/LevelDB.
- Cache_Data, f_000xxx: Это кэш веб-движка и сетевых запросов.

### 4. Как сменить отслеживаемую папку?
1. Нажмите кнопку «Папка» в заголовке панели (или кликните по бэджу с путем).
2. Введите желаемый путь (например, D:\\Shared, C:\\Users\\...\\Downloads).
3. Путь автоматически сохранится в конфиге и мониторинг переключится мгновенно.`,
        requestData: {
          current_watch_dir: currentWatchDir,
          engine: 'ReadDirectoryChangesW'
        }
      });
    } else {
      alert('Мониторинг файловой системы Real-Time Live Watcher работает на базе WinAPI ReadDirectoryChangesW.\nТекущая папка: ' + currentWatchDir);
    }
  }

  function initWindowsAdminTab() {
    console.log('[WinAdminTab] Initializing Windows Sysadmin & File Deletion Auditing tab...');
    fetchStatus();
    fetchUsers();
    fetchEvents();
    fetchFileDeletions();
    fetchLiveFileEvents();

    if (!isWinAdminInitialized) {
      const refreshBtn = document.getElementById('btn-winadmin-refresh');
      const configBtn = document.getElementById('btn-winadmin-config');
      const enableAuditBtn = document.getElementById('btn-enable-auditpol');
      const configureSaclBtn = document.getElementById('btn-configure-project-sacl');
      const changeWatchDirBtn = document.getElementById('btn-winadmin-change-watch-dir');
      const watchDirBadge = document.getElementById('winadmin-watch-dir-badge');
      const liveHelpBtn = document.getElementById('btn-winadmin-live-help');

      if (refreshBtn) {
        refreshBtn.onclick = () => {
          fetchStatus();
          fetchUsers();
          fetchEvents();
          fetchFileDeletions();
          fetchLiveFileEvents();
        };
      }

      if (changeWatchDirBtn) {
        changeWatchDirBtn.onclick = promptChangeWatchDir;
      }
      if (watchDirBadge) {
        watchDirBadge.onclick = promptChangeWatchDir;
      }
      if (liveHelpBtn) {
        liveHelpBtn.onclick = showLiveWatcherHelpModal;
      }

      if (enableAuditBtn) {
        enableAuditBtn.onclick = async () => {
          if (confirm('Включить системный аудит файловой системы (auditpol /set /subcategory:File System)?')) {
            try {
              const res = await fetch('/api/sysadmin/file-audit/policy', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enable_success: true, enable_failure: true })
              });
              const data = await res.json();
              alert(data.success ? 'Аудит файловой системы успешно активирован!' : `Ошибка: ${data.error || 'Сбой'}`);
              fetchStatus();
            } catch (err) {
              alert(`Ошибка выполнения: ${err.message}`);
            }
          }
        };
      }

      if (configureSaclBtn) {
        configureSaclBtn.onclick = async () => {
          const targetPath = prompt('Укажите путь к папке для настройки SACL аудита удаления:', 'c:\\Users\\onela\\AppData\\Local\\AI-Breadboard');
          if (targetPath) {
            try {
              const res = await fetch('/api/sysadmin/file-audit/folder-sacl', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path: targetPath, principal: 'Everyone', enable: true })
              });
              const data = await res.json();
              alert(data.Success ? `SACL успешно настроен для ${targetPath}!` : `Ошибка: ${data.Error || 'Сбой'}`);
              fetchStatus();
              fetchFileDeletions();
            } catch (err) {
              alert(`Ошибка: ${err.message}`);
            }
          }
        };
      }

      if (configBtn) {
        configBtn.onclick = () => {
          if (typeof window.openAppConfigModal === 'function') {
            window.openAppConfigModal('windows_sysadmin', 'Windows System Administrator');
          }
        };
      }

      isWinAdminInitialized = true;
    }
  }

  window.initWindowsAdminTab = initWindowsAdminTab;
})();
