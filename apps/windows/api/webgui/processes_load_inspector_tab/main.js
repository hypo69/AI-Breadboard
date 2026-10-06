/**
 * =============================================================================
 * Process Name: Windows Processes Load Inspector Tab - Main Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля инспектора активности процессов
 *   (сетевая активность и мониторинг изменений файлов в реальном времени).
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/webgui/processes_load_inspector_tab/main.js?v=20261006_v1" type="module"></script>
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: windows/api/webgui/processes_load_inspector_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-06 14:25:00
 * =============================================================================
 */

(function() {
  let isProcPaused = false;
  let cachedTopProcesses = [];

  let isNetPaused = false;
  let currentNetFilter = 'internet';
  let cachedNetworkActivities = [];

  let currentWatchDir = '';
  let currentWatchDirs = [];
  let stagedWatchDirs = [];
  let currentBrowserPath = 'C:\\';
  let cachedDrives = [];
  let _currentUiRefreshSeconds = 2;

  let currentExclusions = {
    enabled: true,
    paths: [],
    extensions: [],
    patterns: [],
    processes: [],
    filtered_count: 0
  };

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // =============================================================================
  // 0. Top Host Processes (Live Stream)
  // =============================================================================

  async function fetchTopProcesses() {
    try {
      const res = await fetch('/api/v1/system/summary?process_limit=50');
      if (res.ok) {
        const snap = await res.json();
        const processes = snap.top_processes || snap.processes || [];
        renderProcessTable(processes);
      }
    } catch (e) {
      console.warn('[ProcessesLoadInspectorTab] Failed to fetch top processes:', e);
    }
  }

  function renderProcessTable(processes) {
    if (processes) {
      cachedTopProcesses = processes;
    }
    if (isProcPaused) return;

    const filterInput = document.getElementById('sys-proc-search');
    const filter = (filterInput?.value || '').toLowerCase().trim();
    const tbody = document.getElementById('sys-proc-tbody');
    const countBadge = document.getElementById('proc-top-count-badge');
    if (!tbody) return;

    const rawList = Array.isArray(cachedTopProcesses) ? cachedTopProcesses : [];
    const filtered = rawList.filter(p => {
      if (!filter) return true;
      return (
        String(p.pid).includes(filter) ||
        (p.name || '').toLowerCase().includes(filter) ||
        (p.username && p.username.toLowerCase().includes(filter))
      );
    });

    if (countBadge) {
      countBadge.textContent = `${filtered.length} процессов`;
    }

    if (filtered.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4 text-muted small">Процессы не найдены</td></tr>';
      return;
    }

    tbody.innerHTML = filtered.map((p, idx) => {
      let cpuClass = '';
      if (p.cpu_percent > 40) cpuClass = 'badge-cpu-high';
      else if (p.cpu_percent > 15) cpuClass = 'badge-cpu-med';

      return `
        <tr class="sys-proc-row" data-idx="${idx}" style="cursor: pointer;" title="Нажмите для детальной AI-диагностики процесса">
          <td class="font-monospace fw-semibold text-info">${p.pid}</td>
          <td style="font-weight: 600; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--text-color);" title="${escapeHtml(p.name || '')}">${escapeHtml(p.name || '')}</td>
          <td class="text-muted">${escapeHtml(p.status || 'running')}</td>
          <td style="text-align: right;" class="${cpuClass}">${Number(p.cpu_percent || 0).toFixed(1)}%</td>
          <td style="text-align: right;" class="font-monospace text-success fw-semibold">${Number(p.memory_mb || 0).toFixed(1)} MB</td>
          <td style="text-align: right;" class="font-monospace text-warning fw-semibold">${p.num_threads || 1}</td>
          <td class="text-muted">${escapeHtml(p.username || 'SYSTEM')}</td>
        </tr>
      `;
    }).join('');

    tbody.querySelectorAll('.sys-proc-row').forEach(row => {
      row.onclick = () => {
        const idx = parseInt(row.getAttribute('data-idx'), 10);
        const p = filtered[idx];
        if (!p) return;

        if (window.AITableModal) {
          window.AITableModal.show({
            icon: '⚙️',
            title: p.name,
            subtitle: `PID: ${p.pid} | ${p.username || 'SYSTEM'}`,
            tableType: 'process',
            badges: [
              { text: `PID ${p.pid}`, class: 'badge bg-info text-dark' },
              { text: p.status || 'running', class: 'badge bg-success' }
            ],
            metadata: [
              { label: 'Имя процесса', value: p.name },
              { label: 'Process ID (PID)', value: String(p.pid) },
              { label: 'Пользователь / Учетная запись', value: p.username || 'SYSTEM' },
              { label: 'Статус', value: p.status || 'Выполняется' },
              { label: 'Загрузка CPU', value: `${Number(p.cpu_percent || 0).toFixed(1)}%` },
              { label: 'Оперативная память', value: `${Number(p.memory_mb || 0).toFixed(1)} MB` },
              { label: 'Количество потоков', value: String(p.num_threads || 1) },
              { label: 'Исполняемый путь', value: p.exe || p.executable_path || 'Системный процесс Windows', isCode: true, fullWidth: true }
            ],
            rawTitle: 'Команда запуска / Аргументы',
            rawContent: Array.isArray(p.cmdline) ? p.cmdline.join(' ') : (p.cmdline || p.exe || ''),
            requestData: {
              pid: p.pid,
              cpu_percent: p.cpu_percent,
              memory_mb: p.memory_mb,
              username: p.username,
              status: p.status
            }
          });
        }
      };
    });
  }

  // =============================================================================
  // 1. Network Activity of Programs (Интернет & Сокеты)
  // =============================================================================

  async function fetchNetworkActivity() {
    try {
      const res = await fetch('/api/v1/system/network-activity?limit=100');
      if (res.ok) {
        const data = await res.json();
        renderNetworkActivityTable(data);
      }
    } catch (e) {
      console.warn('[ProcessesLoadInspectorTab] Failed to fetch network activity:', e);
    }
  }

  function renderNetworkActivityTable(activities) {
    if (activities) {
      cachedNetworkActivities = activities;
    }
    if (isNetPaused) return;

    const tbody = document.getElementById('proc-net-tbody');
    if (!tbody) return;

    const searchInput = document.getElementById('proc-net-search');
    const filterText = (searchInput?.value || '').toLowerCase().trim();
    const countBadge = document.getElementById('proc-netact-count-badge');
    const connsBadge = document.getElementById('proc-netact-conns-badge');

    const rawList = Array.isArray(cachedNetworkActivities) ? cachedNetworkActivities : [];

    let filtered = rawList.filter(item => {
      if (currentNetFilter === 'internet' && !item.is_internet) return false;
      if (currentNetFilter === 'listen' && item.status !== 'LISTEN') return false;

      if (filterText) {
        return (
          String(item.pid).includes(filterText) ||
          (item.name || '').toLowerCase().includes(filterText) ||
          (item.user || '').toLowerCase().includes(filterText) ||
          (item.remote_address || '').toLowerCase().includes(filterText) ||
          (item.local_address || '').toLowerCase().includes(filterText) ||
          (item.service_type || '').toLowerCase().includes(filterText) ||
          (item.sent_summary || '').toLowerCase().includes(filterText) ||
          (item.recv_summary || '').toLowerCase().includes(filterText)
        );
      }
      return true;
    });

    const uniqueProcs = new Set(filtered.map(i => i.pid)).size;
    if (countBadge) countBadge.textContent = `${uniqueProcs} программ`;
    if (connsBadge) connsBadge.textContent = `${filtered.length} сокетов`;

    if (filtered.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-muted small">Нет активных сетевых соединений по выбранному фильтру</td></tr>';
      return;
    }

    tbody.innerHTML = filtered.map((item, idx) => {
      const isListen = item.status === 'LISTEN';
      const statusBadgeClass = isListen
        ? 'badge bg-secondary-subtle text-light border border-secondary'
        : item.status === 'ESTABLISHED'
        ? 'badge bg-success-subtle text-success border border-success'
        : 'badge bg-warning-subtle text-warning border border-warning';

      const protoBadge = item.protocol === 'UDP'
        ? '<span class="badge bg-primary text-white" style="font-size: 0.65rem;">UDP</span>'
        : '<span class="badge bg-dark border border-secondary text-info" style="font-size: 0.65rem;">TCP</span>';

      const isExtBadge = item.is_internet
        ? '<span class="badge bg-primary-subtle text-primary border border-primary px-1" style="font-size: 0.62rem;" title="Внешний сервер в сети Интернет">WAN</span>'
        : '<span class="badge bg-secondary px-1" style="font-size: 0.62rem;" title="Локальный сокет Loopback">LAN</span>';

      const formatNetKb = (kb) => {
        if (!kb || kb <= 0) return '0 KB';
        if (kb >= 1024 * 1024) return (kb / (1024 * 1024)).toFixed(2) + ' GB';
        if (kb >= 1024) return (kb / 1024).toFixed(1) + ' MB';
        return kb.toFixed(1) + ' KB';
      };

      const formatNetRate = (rate) => {
        if (!rate || rate <= 0.05) return '';
        if (rate >= 1024) return (rate / 1024).toFixed(1) + ' MB/s';
        return rate.toFixed(1) + ' KB/s';
      };

      const deltaSentStr = (item.delta_sent_kb && item.delta_sent_kb > 0)
        ? `▲ +${formatNetKb(item.delta_sent_kb)}${item.sent_rate_kbs > 0.05 ? ' (' + formatNetRate(item.sent_rate_kbs) + ')' : ''}`
        : '▲ 0 KB';
      const deltaRecvStr = (item.delta_recv_kb && item.delta_recv_kb > 0)
        ? `▼ +${formatNetKb(item.delta_recv_kb)}${item.recv_rate_kbs > 0.05 ? ' (' + formatNetRate(item.recv_rate_kbs) + ')' : ''}`
        : '▼ 0 KB';

      const totalSentStr = formatNetKb(item.sent_kb || 0);
      const totalRecvStr = formatNetKb(item.recv_kb || 0);

      return `
        <tr class="proc-net-row" data-idx="${idx}" style="cursor: pointer;" title="Нажмите для детальной диагностики сетевого соединения">
          <td>
            <div class="fw-bold text-truncate" style="max-width: 165px; color: var(--text-color);" title="${escapeHtml(item.name)}">${escapeHtml(item.name)}</div>
            <div class="small text-muted" style="font-size: 0.70rem;">PID: <span class="font-monospace text-info">${item.pid}</span> ${item.user ? '• ' + escapeHtml(item.user) : ''}</div>
          </td>
          <td>
            <div class="d-flex align-items-center gap-1">
              ${isExtBadge}
              <span class="font-monospace fw-semibold text-truncate" style="max-width: 195px; color: var(--text-color);" title="${escapeHtml(item.remote_address)}">
                ${escapeHtml(item.remote_address !== '-' ? item.remote_address : item.local_address)}
              </span>
            </div>
            <div class="small text-muted font-monospace" style="font-size: 0.68rem;">Local: ${escapeHtml(item.local_address)}</div>
          </td>
          <td>
            <div class="d-flex align-items-center gap-1 mb-0.5">
              ${protoBadge}
              <span class="fw-semibold text-truncate" style="max-width: 110px; font-size: 0.74rem; color: var(--nav-active);" title="${escapeHtml(item.service_type)}">${escapeHtml(item.service_type)}</span>
            </div>
          </td>
          <td style="text-align: center;">
            <span class="${statusBadgeClass}" style="font-size: 0.68rem;">${escapeHtml(item.status)}</span>
          </td>
          <td>
            <div class="d-flex align-items-center justify-content-between gap-1 mb-1">
              <span class="badge bg-warning-subtle text-warning border border-warning px-1.5 py-0.5" style="font-size: 0.68rem;" title="Отправлено за измеряемый период">
                ${deltaSentStr}
              </span>
              <span class="text-muted font-monospace" style="font-size: 0.66rem;" title="Всего отправлено/записано">
                Σ ${totalSentStr}
              </span>
            </div>
            <div class="d-flex align-items-start gap-1">
              <i class="bi bi-arrow-up-right text-warning mt-0.5" style="font-size: 0.70rem;"></i>
              <div class="text-truncate" style="max-width: 250px; font-size: 0.72rem; color: var(--text-muted);" title="${escapeHtml(item.sent_summary)}">
                ${escapeHtml(item.sent_summary)}
              </div>
            </div>
          </td>
          <td>
            <div class="d-flex align-items-center justify-content-between gap-1 mb-1">
              <span class="badge bg-success-subtle text-success border border-success px-1.5 py-0.5" style="font-size: 0.68rem;" title="Скачано/получено за измеряемый период">
                ${deltaRecvStr}
              </span>
              <span class="text-muted font-monospace" style="font-size: 0.66rem;" title="Всего скачано/прочитано">
                Σ ${totalRecvStr}
              </span>
            </div>
            <div class="d-flex align-items-start gap-1">
              <i class="bi bi-arrow-down-left text-success mt-0.5" style="font-size: 0.70rem;"></i>
              <div class="text-truncate" style="max-width: 250px; font-size: 0.72rem; color: var(--text-muted);" title="${escapeHtml(item.recv_summary)}">
                ${escapeHtml(item.recv_summary)}
              </div>
            </div>
          </td>
        </tr>
      `;
    }).join('');

    tbody.querySelectorAll('.proc-net-row').forEach(row => {
      row.onclick = () => {
        const idx = parseInt(row.getAttribute('data-idx'), 10);
        const item = filtered[idx];
        if (!item) return;

        const formatNetKb = (kb) => {
          if (!kb || kb <= 0) return '0 KB';
          if (kb >= 1024 * 1024) return (kb / (1024 * 1024)).toFixed(2) + ' GB';
          if (kb >= 1024) return (kb / 1024).toFixed(1) + ' MB';
          return kb.toFixed(1) + ' KB';
        };

        const formatNetRate = (rate) => {
          if (!rate || rate <= 0.05) return '';
          if (rate >= 1024) return (rate / 1024).toFixed(1) + ' MB/s';
          return rate.toFixed(1) + ' KB/s';
        };

        if (window.AITableModal) {
          window.AITableModal.show({
            icon: '🌐',
            title: `${item.name} (${item.service_type})`,
            subtitle: `PID: ${item.pid} | ${item.remote_address}`,
            tableType: 'network',
            badges: [
              { text: `PID ${item.pid}`, class: 'badge bg-info text-dark' },
              { text: item.protocol, class: 'badge bg-primary' },
              { text: item.status, class: 'badge bg-success' },
              { text: item.is_internet ? 'Интернет (WAN)' : 'Локально (LAN)', class: item.is_internet ? 'badge bg-warning text-dark' : 'badge bg-secondary' }
            ],
            metadata: [
              { label: 'Программа / Процесс', value: item.name },
              { label: 'Process ID (PID)', value: String(item.pid) },
              { label: 'Пользователь системы', value: item.user || 'SYSTEM' },
              { label: 'Удаленный адрес (Remote)', value: item.remote_address },
              { label: 'Локальный сокет (Local)', value: item.local_address },
              { label: 'Протокол / Служба', value: `${item.protocol} • ${item.service_type}` },
              { label: 'Статус соединения', value: item.status },
              { label: 'Скачано за период (Прием)', value: `${formatNetKb(item.delta_recv_kb || 0)} ${item.recv_rate_kbs > 0.05 ? '(' + formatNetRate(item.recv_rate_kbs) + ')' : ''}` },
              { label: 'Всего скачано / получено', value: formatNetKb(item.recv_kb || 0) },
              { label: 'Отправлено за период', value: `${formatNetKb(item.delta_sent_kb || 0)} ${item.sent_rate_kbs > 0.05 ? '(' + formatNetRate(item.sent_rate_kbs) + ')' : ''}` },
              { label: 'Всего отправлено', value: formatNetKb(item.sent_kb || 0) },
              { label: 'Что шлет (Отправка)', value: item.sent_summary, fullWidth: true },
              { label: 'Что принимает (Прием)', value: item.recv_summary, fullWidth: true }
            ],
            rawTitle: 'Сетевой дамп подключения',
            rawContent: JSON.stringify(item, null, 2),
            requestData: item
          });
        }
      };
    });
  }

  // =============================================================================
  // 2. Real-Time File Changes (WinAPI ReadDirectoryChangesW)
  // =============================================================================

  async function fetchLiveFileEvents() {
    try {
      const [resEvents, resTelem] = await Promise.all([
        fetch('/api/sysadmin/file-audit/live-events?limit=30'),
        fetch('/api/sysadmin/file-audit/telemetry').catch(() => null)
      ]);

      if (resTelem && resTelem.ok) {
        const telem = await resTelem.json();
        const elRate = document.getElementById('proc-watcher-rate');
        const elCr = document.getElementById('proc-watcher-cr');
        const elMod = document.getElementById('proc-watcher-mod');
        const elDel = document.getElementById('proc-watcher-del');
        const elDrive = document.getElementById('proc-watcher-drive');
        const elDriveModel = document.getElementById('proc-watcher-drive-model');
        const elDriveTemp = document.getElementById('proc-watcher-temp');
        const elDiskR = document.getElementById('proc-watcher-r-kbs');
        const elDiskW = document.getElementById('proc-watcher-w-kbs');
        const elSecMatches = document.getElementById('proc-watcher-sec-matches');
        const elStatus = document.getElementById('proc-watcher-sensor-status');

        if (elRate) elRate.textContent = (telem.events_rate_per_sec || 0).toFixed(1);
        if (elCr) elCr.textContent = (telem.created_rate_per_sec || 0).toFixed(1);
        if (elMod) elMod.textContent = (telem.modified_rate_per_sec || 0).toFixed(1);
        if (elDel) elDel.textContent = (telem.deleted_rate_per_sec || 0).toFixed(1);

        if (elDrive) {
          const drivesStr = (telem.drive_letters && telem.drive_letters.length)
            ? telem.drive_letters.join(', ')
            : (telem.drive_letter || 'C:');
          elDrive.textContent = drivesStr;
        }
        if (elDriveModel) elDriveModel.textContent = telem.drive_model || 'Storage';
        if (elDriveTemp) elDriveTemp.textContent = telem.drive_temperature_c !== null && telem.drive_temperature_c !== undefined ? `${telem.drive_temperature_c} °C` : '-- °C';
        if (elDiskR) elDiskR.textContent = Math.round(telem.disk_read_kbs || 0);
        if (elDiskW) elDiskW.textContent = Math.round(telem.disk_write_kbs || 0);
        if (elSecMatches) elSecMatches.textContent = telem.security_audit_matched_count || 0;

        if (elStatus) {
          if (telem.burst_deletions_alert) {
            elStatus.className = 'badge bg-danger-subtle text-danger border border-danger px-2 py-1';
            elStatus.textContent = '🚨 Всплеск удалений';
          } else if (telem.high_activity_alert) {
            elStatus.className = 'badge bg-warning-subtle text-warning border border-warning px-2 py-1';
            elStatus.textContent = '⚡ Высокий I/O';
          } else {
            elStatus.className = 'badge bg-success-subtle text-success border border-success px-2 py-1';
            elStatus.textContent = '🟢 Штатный режим';
          }
        }
      }

      if (!resEvents || !resEvents.ok) return;
      const data = await resEvents.json();
      const events = data.events || [];

      if (data.filtered_count !== undefined) {
        const filteredEl = document.getElementById('proc-watcher-filtered-count');
        if (filteredEl) filteredEl.textContent = data.filtered_count;
      }

      currentWatchDirs = data.watch_dirs || (data.watch_dir ? [data.watch_dir] : []);
      currentWatchDir = currentWatchDirs[0] || data.watch_dir || '';

      const dirPathEl = document.getElementById('proc-watch-dir-path');
      const badge = document.getElementById('proc-watch-dir-badge');
      if (dirPathEl) {
        if (currentWatchDirs.length === 0) {
          dirPathEl.innerText = 'Папки не выбраны';
        } else if (currentWatchDirs.length === 1) {
          const singleName = currentWatchDirs[0].split('\\').pop() || currentWatchDirs[0];
          dirPathEl.innerText = singleName;
        } else {
          const firstNames = currentWatchDirs.slice(0, 2).map(p => p.split('\\').pop() || p).join(', ');
          dirPathEl.innerText = `${currentWatchDirs.length} папок: ${firstNames}${currentWatchDirs.length > 2 ? '...' : ''}`;
        }
      }
      if (badge) {
        badge.title = `Отслеживаемые каталоги (${currentWatchDirs.length}):\n${currentWatchDirs.join('\n')}\n\n(Нажмите для настройки и выбора папок)`;
      }

      const tbody = document.getElementById('proc-watcher-tbody');
      if (tbody) {
        if (events.length === 0) {
          const labelDirs = currentWatchDirs.length > 0 ? currentWatchDirs.join(', ') : 'проекта';
          tbody.innerHTML = `<tr><td colspan="4" class="text-center text-muted p-2">Ожидание изменений в папках <code>${labelDirs}</code>...</td></tr>`;
          return;
        }
        tbody.innerHTML = events.map((e, idx) => {
          const rootDirHint = e.watch_dir ? (e.watch_dir.split('\\').pop() || e.watch_dir) : '';
          const procDisplay = e.process_name
            ? `<span class="badge bg-dark border border-secondary text-info font-monospace text-truncate d-inline-block" style="max-width: 165px; font-size: 0.72rem;" title="Программа: ${escapeHtml(e.process_name)}${e.process_id ? ` (PID: ${e.process_id})` : ''}"><i class="bi bi-cpu me-1"></i>${escapeHtml(e.process_name)}${e.process_id ? ` [${e.process_id}]` : ''}</span>`
            : `<span class="text-muted" style="font-size: 0.72rem;">—</span>`;
          return `
            <tr class="proc-live-row" data-idx="${idx}" style="cursor: pointer;" title="Нажмите для AI-диагностики события">
              <td class="font-monospace text-muted small">${e.timestamp?.slice(11, 19) || ''}</td>
              <td>
                <span class="badge ${e.is_deletion ? 'bg-danger' : (e.action === 'Created' ? 'bg-success' : 'bg-secondary')}">${e.action}</span>
                ${rootDirHint && currentWatchDirs.length > 1 ? `<span class="badge bg-dark border border-secondary text-muted ms-1" style="font-size: 0.65rem;" title="Корень: ${escapeHtml(e.watch_dir)}">${rootDirHint}</span>` : ''}
              </td>
              <td>${procDisplay}</td>
              <td class="font-monospace small" style="word-break: break-all; color: var(--text-color);" title="${escapeHtml(e.path)}">${escapeHtml(e.path)}</td>
            </tr>
          `;
        }).join('');

        tbody.querySelectorAll('.proc-live-row').forEach(row => {
          row.onclick = () => {
            const idx = parseInt(row.getAttribute('data-idx'), 10);
            const e = events[idx];
            if (!e) return;

            if (window.AITableModal) {
              window.AITableModal.show({
                icon: '⚡',
                title: `Файловое событие: ${e.action}`,
                subtitle: `${e.path} | ${e.timestamp}`,
                tableType: 'file_event',
                badges: [
                  { text: e.action, class: e.is_deletion ? 'badge bg-danger' : (e.action === 'Created' ? 'badge bg-success' : 'badge bg-info text-dark') },
                  { text: e.process_name ? `Программа: ${e.process_name}` : 'WinAPI ReadDirectoryChangesW', class: 'badge bg-dark border border-secondary text-info' },
                  { text: 'WinAPI', class: 'badge bg-secondary' }
                ],
                metadata: [
                  { label: 'Действие', value: e.action },
                  { label: 'Полный путь к файлу', value: e.path },
                  { label: 'Программа / Процесс', value: e.process_name ? `${e.process_name}${e.process_id ? ` (PID: ${e.process_id})` : ''}` : 'Фоновый процесс / завершен' },
                  { label: 'Время события', value: e.timestamp },
                  { label: 'Признак удаления', value: e.is_deletion ? 'Да (Файл удален/переименован)' : 'Нет' },
                  { label: 'Папка события', value: e.watch_dir || currentWatchDir },
                  { label: 'Все отслеживаемые папки', value: currentWatchDirs.join('; ') }
                ],
                rawTitle: 'Детали события WinAPI & Process Info',
                rawContent: JSON.stringify(e, null, 2),
                requestData: e
              });
            }
          };
        });
      }
    } catch (e) {
      console.error('[ProcessesLoadInspectorTab] Failed to fetch live file events:', e);
    }
  }

  // =============================================================================
  // 3. Multi-Directory Watcher & Folder Explorer Modal Logic
  // =============================================================================

  function showWatchDirsAlert(msg, type = 'success') {
    const alertEl = document.getElementById('modal-proc-dirs-alert');
    if (!alertEl) return;
    alertEl.className = `alert alert-${type} py-2 px-3 small mb-3`;
    alertEl.innerHTML = msg;
    alertEl.classList.remove('d-none');
    if (type === 'success') {
      setTimeout(() => {
        alertEl.classList.add('d-none');
      }, 3500);
    }
  }

  function renderModalActiveDirsList() {
    const container = document.getElementById('modal-proc-dirs-active-list');
    const countBadge = document.getElementById('modal-proc-dirs-count');
    const hintEl = document.getElementById('modal-proc-dirs-footer-hint');

    if (!container) return;

    if (countBadge) countBadge.textContent = String(stagedWatchDirs.length);
    if (hintEl) hintEl.textContent = `Выбрано папок для мониторинга: ${stagedWatchDirs.length}`;

    if (stagedWatchDirs.length === 0) {
      container.innerHTML = `
        <div class="text-center text-muted small py-3">
          <i class="bi bi-folder-x me-1"></i> Список пуст. Выберите папки в проводнике ниже или воспользуйтесь быстрыми пресетами.
        </div>
      `;
      return;
    }

    container.innerHTML = stagedWatchDirs.map((dirPath, idx) => {
      const folderName = dirPath.split('\\').pop() || dirPath;
      const driveLetter = (dirPath.slice(0, 2)).toUpperCase();
      return `
        <div class="p-1.5 px-2 rounded d-flex align-items-center justify-content-between gap-2" style="background: var(--bg-color); border: 1px solid var(--border-color);">
          <div class="d-flex align-items-center gap-2 text-truncate" style="max-width: 82%;">
            <i class="bi bi-folder-check text-warning fs-6"></i>
            <span class="badge bg-secondary font-monospace" style="font-size: 0.68rem;">${driveLetter}</span>
            <div class="text-truncate">
              <span class="fw-bold small" style="color: var(--text-color);">${escapeHtml(folderName)}</span>
              <span class="small text-muted font-monospace d-block text-truncate" style="font-size: 0.72rem;" title="${escapeHtml(dirPath)}">${escapeHtml(dirPath)}</span>
            </div>
          </div>
          <button class="btn btn-xs btn-outline-danger rounded-pill px-2 py-0.5" onclick="window._procRemoveStagedWatchDir(${idx})" title="Удалить из списка мониторинга">
            <i class="bi bi-trash3"></i>
          </button>
        </div>
      `;
    }).join('');
  }

  window._procRemoveStagedWatchDir = function(index) {
    if (index >= 0 && index < stagedWatchDirs.length) {
      const removed = stagedWatchDirs.splice(index, 1)[0];
      renderModalActiveDirsList();
      showWatchDirsAlert(`Папка удалена из списка: <code>${escapeHtml(removed)}</code>`, 'info');
    }
  };

  function addDirToStaged(pathToAdd) {
    if (!pathToAdd || !pathToAdd.trim()) return;
    const cleanPath = pathToAdd.trim();
    if (stagedWatchDirs.includes(cleanPath)) {
      showWatchDirsAlert(`Папка уже есть в списке: <code>${escapeHtml(cleanPath)}</code>`, 'warning');
      return;
    }
    stagedWatchDirs.push(cleanPath);
    renderModalActiveDirsList();
    showWatchDirsAlert(`Папка добавлена: <code>${escapeHtml(cleanPath)}</code>`, 'success');
  }

  async function loadSystemDrives() {
    const drivesBar = document.getElementById('modal-proc-drives-bar');
    if (!drivesBar) return;

    try {
      const res = await fetch('/api/sysadmin/filesystem/drives');
      if (res.ok) {
        const data = await res.json();
        cachedDrives = data.drives || [];
      }
    } catch (e) {
      console.warn('[ProcessesLoadInspectorTab] Failed to fetch system drives:', e);
      cachedDrives = [{ mountpoint: 'C:\\', free_gb: 0 }];
    }

    if (cachedDrives.length === 0) {
      cachedDrives = [{ mountpoint: 'C:\\', free_gb: 0 }];
    }

    drivesBar.innerHTML = cachedDrives.map(d => {
      const label = d.mountpoint || 'C:\\';
      const freeTxt = d.free_gb ? `${d.free_gb} GB free` : '';
      return `
        <button class="btn btn-xs btn-outline-secondary rounded-pill px-2 py-0.5 proc-drive-btn font-monospace" data-drive="${escapeHtml(label)}" title="${escapeHtml(label)} ${freeTxt}">
          <i class="bi bi-hdd me-1"></i>${escapeHtml(label)}
        </button>
      `;
    }).join('');

    drivesBar.querySelectorAll('.proc-drive-btn').forEach(btn => {
      btn.onclick = () => {
        const drv = btn.getAttribute('data-drive');
        if (drv) loadFolderBrowser(drv);
      };
    });
  }

  function renderBreadcrumbs(currentPath) {
    const bcContainer = document.getElementById('modal-proc-folder-breadcrumbs');
    if (!bcContainer) return;

    const parts = currentPath.replace(/\\+$/, '').split('\\');
    let builtPath = '';
    const crumbsHtml = parts.map((part, idx) => {
      if (idx === 0) {
        builtPath = part + '\\';
      } else {
        builtPath = builtPath + (builtPath.endsWith('\\') ? '' : '\\') + part;
      }
      const clickPath = builtPath;
      const isLast = idx === parts.length - 1;
      return `
        <span class="d-inline-flex align-items-center">
          ${idx > 0 ? '<span class="text-muted mx-1">/</span>' : ''}
          <a href="#" class="proc-breadcrumb-link text-decoration-none ${isLast ? 'fw-bold text-info' : ''}" style="color: var(--text-color);" data-path="${escapeHtml(clickPath)}">
            ${escapeHtml(part || 'Корень')}
          </a>
        </span>
      `;
    }).join('');

    bcContainer.innerHTML = crumbsHtml;

    bcContainer.querySelectorAll('.proc-breadcrumb-link').forEach(link => {
      link.onclick = (e) => {
        e.preventDefault();
        const p = link.getAttribute('data-path');
        if (p) loadFolderBrowser(p);
      };
    });
  }

  async function loadFolderBrowser(targetPath) {
    const inputPath = document.getElementById('modal-proc-folder-path-input');
    const browserList = document.getElementById('modal-proc-folder-browser-list');
    if (!targetPath) targetPath = 'C:\\';
    currentBrowserPath = targetPath;

    if (inputPath) inputPath.value = targetPath;
    renderBreadcrumbs(targetPath);

    if (!browserList) return;
    browserList.innerHTML = `<div class="text-center text-muted small py-3"><span class="spinner-border spinner-border-sm me-1"></span> Загрузка директорий...</div>`;

    try {
      const res = await fetch(`/api/sysadmin/filesystem/browse?path=${encodeURIComponent(targetPath)}`);
      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `HTTP ${res.status}`);
      }

      const data = await res.json();
      const dirs = data.directories || [];

      if (dirs.length === 0) {
        browserList.innerHTML = `<div class="text-center text-muted small py-3">В этой директории нет доступных подпапок</div>`;
        return;
      }

      browserList.innerHTML = dirs.map(d => {
        const isAlreadySelected = stagedWatchDirs.includes(d.path);
        return `
          <div class="p-1 px-2 rounded d-flex align-items-center justify-content-between gap-2 proc-folder-browser-item" style="background: var(--surface-1); border: 1px solid var(--border-color); cursor: pointer;">
            <div class="d-flex align-items-center gap-2 text-truncate flex-grow-1 proc-nav-to-folder" data-path="${escapeHtml(d.path)}" title="Нажмите для перехода в папку">
              <i class="bi ${d.has_subdirs ? 'bi-folder2 text-warning' : 'bi-folder text-warning'}"></i>
              <span class="small text-light text-truncate">${escapeHtml(d.name)}</span>
              <span class="small text-muted font-monospace ms-auto me-2" style="font-size: 0.68rem;">${d.modified || ''}</span>
            </div>
            <button class="btn btn-xs ${isAlreadySelected ? 'btn-success' : 'btn-outline-info'} rounded-pill px-2 py-0.5 proc-add-folder-btn" data-path="${escapeHtml(d.path)}" title="Добавить в отслеживаемые">
              <i class="bi ${isAlreadySelected ? 'bi-check2' : 'bi-plus-lg'} me-1"></i>${isAlreadySelected ? 'Выбрана' : 'Следить'}
            </button>
          </div>
        `;
      }).join('');

      browserList.querySelectorAll('.proc-nav-to-folder').forEach(el => {
        el.onclick = () => {
          const p = el.getAttribute('data-path');
          if (p) loadFolderBrowser(p);
        };
      });

      browserList.querySelectorAll('.proc-add-folder-btn').forEach(btn => {
        btn.onclick = (e) => {
          e.stopPropagation();
          const p = btn.getAttribute('data-path');
          if (p) {
            addDirToStaged(p);
            btn.className = 'btn btn-xs btn-success rounded-pill px-2 py-0.5 proc-add-folder-btn';
            btn.innerHTML = '<i class="bi bi-check2 me-1"></i>Выбрана';
          }
        };
      });

    } catch (e) {
      console.warn('[ProcessesLoadInspectorTab] Failed to browse folder:', e);
      browserList.innerHTML = `<div class="text-danger small py-2 px-2"><i class="bi bi-exclamation-triangle me-1"></i> Ошибка доступа: ${escapeHtml(e.message)}</div>`;
    }
  }

  // =============================================================================
  // 4. Exclusions & Filters Management
  // =============================================================================

  function showExclusionsAlert(msg, type = 'success') {
    const alertEl = document.getElementById('modal-proc-exclusions-alert');
    if (!alertEl) return;
    alertEl.className = `alert alert-${type} py-2 px-3 small mb-3`;
    alertEl.innerHTML = msg;
    alertEl.classList.remove('d-none');
    if (type === 'success' || type === 'info') {
      setTimeout(() => {
        alertEl.classList.add('d-none');
      }, 3500);
    }
  }

  function renderExclusionsLists() {
    const totalCount = (currentExclusions.paths?.length || 0) +
      (currentExclusions.extensions?.length || 0) +
      (currentExclusions.patterns?.length || 0) +
      (currentExclusions.processes?.length || 0);

    const tabBadge = document.getElementById('modal-proc-exclusions-tab-count');
    const headerBadge = document.getElementById('proc-exclusions-count-badge');
    if (tabBadge) tabBadge.textContent = String(totalCount);
    if (headerBadge) headerBadge.textContent = String(totalCount);

    const switchEl = document.getElementById('switch-proc-exclusions-active');
    const statusBadge = document.getElementById('badge-proc-exclusions-status');
    if (switchEl) switchEl.checked = Boolean(currentExclusions.enabled);
    if (statusBadge) {
      if (currentExclusions.enabled) {
        statusBadge.className = 'badge bg-success';
        statusBadge.textContent = 'ВКЛ';
      } else {
        statusBadge.className = 'badge bg-danger-subtle text-danger border border-danger fw-bold';
        statusBadge.textContent = 'ВЫКЛ';
      }
    }

    const filteredTotalEl = document.getElementById('modal-proc-exclusions-filtered-total');
    if (filteredTotalEl) filteredTotalEl.textContent = String(currentExclusions.filtered_count || 0);

    // Paths list
    const pathsContainer = document.getElementById('list-proc-ex-paths');
    const pathsBadge = document.getElementById('badge-proc-ex-paths-count');
    if (pathsBadge) pathsBadge.textContent = String(currentExclusions.paths?.length || 0);
    if (pathsContainer) {
      if (!currentExclusions.paths || currentExclusions.paths.length === 0) {
        pathsContainer.innerHTML = `<div class="text-muted small text-center py-2">Нет исключенных папок</div>`;
      } else {
        pathsContainer.innerHTML = currentExclusions.paths.map(p => `
          <div class="d-flex align-items-center justify-content-between gap-1.5 p-1 px-2 rounded mb-1" style="background: var(--bg-color); border: 1px solid var(--border-color);">
            <span class="small font-monospace text-light text-truncate" style="font-size: 0.72rem;" title="${escapeHtml(p)}">${escapeHtml(p)}</span>
            <button class="btn btn-xs btn-outline-danger py-0 px-1 rounded-pill" onclick="window._procRemoveExclusionItem('paths', '${escapeHtml(p.replace(/\\/g, '\\\\'))}')" title="Удалить">✕</button>
          </div>
        `).join('');
      }
    }

    // Extensions list
    const extsContainer = document.getElementById('list-proc-ex-extensions');
    const extsBadge = document.getElementById('badge-proc-ex-extensions-count');
    if (extsBadge) extsBadge.textContent = String(currentExclusions.extensions?.length || 0);
    if (extsContainer) {
      if (!currentExclusions.extensions || currentExclusions.extensions.length === 0) {
        extsContainer.innerHTML = `<div class="text-muted small text-center py-2">Нет исключенных расширений</div>`;
      } else {
        extsContainer.innerHTML = `<div class="d-flex flex-wrap gap-1">` + currentExclusions.extensions.map(e => `
          <span class="badge bg-dark border border-secondary text-info d-inline-flex align-items-center gap-1 font-monospace" style="font-size: 0.75rem;">
            ${escapeHtml(e)}
            <button type="button" class="btn-close btn-close-white" style="font-size: 0.5rem;" onclick="window._procRemoveExclusionItem('extensions', '${escapeHtml(e)}')" title="Удалить"></button>
          </span>
        `).join('') + `</div>`;
      }
    }

    // Patterns list
    const patsContainer = document.getElementById('list-proc-ex-patterns');
    const patsBadge = document.getElementById('badge-proc-ex-patterns-count');
    if (patsBadge) patsBadge.textContent = String(currentExclusions.patterns?.length || 0);
    if (patsContainer) {
      if (!currentExclusions.patterns || currentExclusions.patterns.length === 0) {
        patsContainer.innerHTML = `<div class="text-muted small text-center py-2">Нет исключенных шаблонов</div>`;
      } else {
        patsContainer.innerHTML = `<div class="d-flex flex-wrap gap-1">` + currentExclusions.patterns.map(pat => `
          <span class="badge bg-dark border border-secondary text-warning d-inline-flex align-items-center gap-1 font-monospace" style="font-size: 0.75rem;">
            ${escapeHtml(pat)}
            <button type="button" class="btn-close btn-close-white" style="font-size: 0.5rem;" onclick="window._procRemoveExclusionItem('patterns', '${escapeHtml(pat)}')" title="Удалить"></button>
          </span>
        `).join('') + `</div>`;
      }
    }

    // Processes list
    const procsContainer = document.getElementById('list-proc-ex-processes');
    const procsBadge = document.getElementById('badge-proc-ex-processes-count');
    if (procsBadge) procsBadge.textContent = String(currentExclusions.processes?.length || 0);
    if (procsContainer) {
      if (!currentExclusions.processes || currentExclusions.processes.length === 0) {
        procsContainer.innerHTML = `<div class="text-muted small text-center py-2">Нет исключенных программ</div>`;
      } else {
        procsContainer.innerHTML = `<div class="d-flex flex-wrap gap-1">` + currentExclusions.processes.map(proc => `
          <span class="badge bg-dark border border-secondary text-danger d-inline-flex align-items-center gap-1 font-monospace" style="font-size: 0.75rem;">
            <i class="bi bi-cpu me-0.5"></i>${escapeHtml(proc)}
            <button type="button" class="btn-close btn-close-white" style="font-size: 0.5rem;" onclick="window._procRemoveExclusionItem('processes', '${escapeHtml(proc)}')" title="Удалить"></button>
          </span>
        `).join('') + `</div>`;
      }
    }
  }

  async function fetchExclusionsData() {
    try {
      const res = await fetch('/api/sysadmin/file-audit/exclusions');
      if (res.ok) {
        currentExclusions = await res.json();
        renderExclusionsLists();
      }
    } catch (e) {
      console.warn('[ProcessesLoadInspectorTab] Failed to fetch exclusions:', e);
    }
  }

  async function addExclusionItem(category, value) {
    if (!value || !value.trim()) return;
    const cleanVal = value.trim();
    try {
      const res = await fetch('/api/sysadmin/file-audit/exclusions/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ category, value: cleanVal })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        currentExclusions = data.exclusions || currentExclusions;
        renderExclusionsLists();
        showExclusionsAlert(`Правило добавлено: <code>${escapeHtml(cleanVal)}</code>`, 'success');
        const inputVal = document.getElementById('input-proc-exclusion-value');
        if (inputVal) inputVal.value = '';
      } else {
        showExclusionsAlert(data.message || 'Правило уже существует или невалидно', 'warning');
      }
    } catch (e) {
      showExclusionsAlert(`Ошибка добавления: ${e.message}`, 'danger');
    }
  }

  window._procRemoveExclusionItem = async function(category, value) {
    if (!value) return;
    try {
      const res = await fetch('/api/sysadmin/file-audit/exclusions/remove', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ category, value })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        currentExclusions = data.exclusions || currentExclusions;
        renderExclusionsLists();
        showExclusionsAlert(`Правило удалено: <code>${escapeHtml(value)}</code>`, 'info');
      } else {
        showExclusionsAlert(data.message || 'Не удалось удалить правило', 'warning');
      }
    } catch (e) {
      showExclusionsAlert(`Ошибка удаления: ${e.message}`, 'danger');
    }
  };

  async function toggleExclusionsActive(enabled) {
    try {
      const res = await fetch('/api/sysadmin/file-audit/exclusions/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        currentExclusions = data.exclusions || currentExclusions;
        renderExclusionsLists();
        showExclusionsAlert(`Фильтрация исключений ${data.enabled ? 'включена' : 'отключена'}`, 'info');
      }
    } catch (e) {
      showExclusionsAlert(`Ошибка переключения: ${e.message}`, 'danger');
    }
  }

  async function applyExclusionPreset(preset) {
    if (preset === 'logs') {
      await addExclusionItem('paths', 'AppData\\Roaming\\AI-Breadboard\\apps\\windows\\telemetry\\logs');
      await addExclusionItem('extensions', '.log');
      await addExclusionItem('extensions', '.csv');
      await addExclusionItem('patterns', '*system_inspector_polls.csv*');
    } else if (preset === 'search') {
      await addExclusionItem('processes', 'SearchIndexer.exe');
      await addExclusionItem('patterns', '*Windows.db*');
      await addExclusionItem('patterns', '*Windows.db-wal*');
      await addExclusionItem('patterns', '*Windows.db-shm*');
    } else if (preset === 'temp') {
      await addExclusionItem('paths', 'AppData\\Local\\Temp');
      await addExclusionItem('extensions', '.tmp');
      await addExclusionItem('patterns', '~$*');
    } else if (preset === 'dev') {
      await addExclusionItem('paths', '.git');
      await addExclusionItem('paths', 'node_modules');
      await addExclusionItem('paths', '__pycache__');
      await addExclusionItem('paths', '.pytest_cache');
    }
  }

  async function openWatchFoldersModal(initialTab = 'folders') {
    const modalEl = document.getElementById('modal-proc-watch-folders');
    if (!modalEl) {
      console.warn('[ProcessesLoadInspectorTab] modal-proc-watch-folders element not found');
      return;
    }

    try {
      const res = await fetch('/api/sysadmin/file-audit/watch-dirs');
      if (res.ok) {
        const data = await res.json();
        stagedWatchDirs = data.watch_dirs && data.watch_dirs.length ? [...data.watch_dirs] : [currentWatchDir || 'C:\\'];
      } else {
        stagedWatchDirs = currentWatchDirs.length ? [...currentWatchDirs] : [currentWatchDir || 'C:\\'];
      }
    } catch {
      stagedWatchDirs = currentWatchDirs.length ? [...currentWatchDirs] : [currentWatchDir || 'C:\\'];
    }

    renderModalActiveDirsList();
    const tabFoldersBadge = document.getElementById('modal-proc-dirs-tab-count');
    if (tabFoldersBadge) tabFoldersBadge.textContent = String(stagedWatchDirs.length);

    await loadSystemDrives();
    await fetchExclusionsData();

    if (initialTab === 'exclusions') {
      const tabExBtn = document.getElementById('tab-btn-proc-exclusions');
      if (tabExBtn && window.bootstrap?.Tab) {
        window.bootstrap.Tab.getOrCreateInstance(tabExBtn).show();
      } else if (tabExBtn) {
        tabExBtn.click();
      }
    } else {
      const tabFoldersBtn = document.getElementById('tab-btn-proc-folders');
      if (tabFoldersBtn && window.bootstrap?.Tab) {
        window.bootstrap.Tab.getOrCreateInstance(tabFoldersBtn).show();
      } else if (tabFoldersBtn) {
        tabFoldersBtn.click();
      }
    }

    const startPath = stagedWatchDirs[0] || currentBrowserPath || 'C:\\';
    loadFolderBrowser(startPath);

    if (window.bootstrap?.Modal) {
      window.bootstrap.Modal.getOrCreateInstance(modalEl).show();
    } else {
      modalEl.classList.add('show');
      modalEl.style.display = 'block';
    }
  }

  function showLiveWatcherHelpModal() {
    const dirsStr = currentWatchDirs.length ? currentWatchDirs.join('\n- ') : (currentWatchDir || 'Рабочая папка');
    if (window.AITableModal) {
      window.AITableModal.show({
        icon: 'ℹ️',
        title: 'Справка: Изменения файлов в реальном времени',
        subtitle: 'Низкоуровневый мониторинг файловой системы Windows через WinAPI ReadDirectoryChangesW',
        tableType: 'help',
        badges: [
          { text: 'WinAPI ReadDirectoryChangesW', class: 'badge bg-info text-dark' },
          { text: 'Multi-Directory', class: 'badge bg-primary' },
          { text: 'Real-Time Streaming', class: 'badge bg-success' },
          { text: 'Рекурсивно (bWatchSubtree = True)', class: 'badge bg-warning text-dark' }
        ],
        metadata: [
          { label: 'Технология', value: 'WinAPI ReadDirectoryChangesW (kernel32.dll)' },
          { label: 'Активные папки', value: dirsStr, fullWidth: true },
          { label: 'Автологгер', value: 'file_watcher_telemetry_polls.csv' }
        ],
        rawTitle: 'Архитектурная справка',
        rawContent: `Компонент для мгновенного перехвата операций файловой системы в режиме реального времени на базе WinAPI ReadDirectoryChangesW.\n\nТекущие отслеживаемые каталоги:\n${dirsStr}`
      });
    } else {
      alert('Мониторинг файловой системы в реальном времени (ReadDirectoryChangesW).\nОтслеживаемые папки:\n- ' + dirsStr);
    }
  }

  // =============================================================================
  // 5. Table Resizers
  // =============================================================================

  function initTableResizers() {
    // Process table resizer
    const procResizer = document.getElementById('sys-proc-table-resizer');
    const procContainer = document.getElementById('sys-proc-table-container');
    if (procResizer && procContainer) {
      let startY = 0, startHeight = 0;
      const onMouseMove = (e) => {
        const delta = e.clientY - startY;
        const newH = Math.max(140, Math.min(850, startHeight + delta));
        procContainer.style.height = `${newH}px`;
      };
      const onMouseUp = () => {
        procResizer.classList.remove('resizing');
        document.removeEventListener('mousemove', onMouseMove);
        document.removeEventListener('mouseup', onMouseUp);
      };
      procResizer.onmousedown = (e) => {
        e.preventDefault();
        startY = e.clientY;
        startHeight = parseInt(window.getComputedStyle(procContainer).height, 10) || 380;
        procResizer.classList.add('resizing');
        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
      };
      procResizer.ondblclick = () => { procContainer.style.height = '380px'; };
    }

    // Network table resizer
    const netResizer = document.getElementById('proc-net-table-resizer');
    const netContainer = document.getElementById('proc-net-table-container');
    if (netResizer && netContainer) {
      let startY = 0, startHeight = 0;
      const onMouseMove = (e) => {
        const delta = e.clientY - startY;
        const newH = Math.max(140, Math.min(850, startHeight + delta));
        netContainer.style.height = `${newH}px`;
      };
      const onMouseUp = () => {
        netResizer.classList.remove('resizing');
        document.removeEventListener('mousemove', onMouseMove);
        document.removeEventListener('mouseup', onMouseUp);
      };
      netResizer.onmousedown = (e) => {
        e.preventDefault();
        startY = e.clientY;
        startHeight = parseInt(window.getComputedStyle(netContainer).height, 10) || 360;
        netResizer.classList.add('resizing');
        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
      };
      netResizer.ondblclick = () => { netContainer.style.height = '360px'; };
    }

    // Watcher table resizer
    const watchResizer = document.getElementById('proc-watcher-table-resizer');
    const watchContainer = document.getElementById('proc-watcher-table-container');
    if (watchResizer && watchContainer) {
      let startY = 0, startHeight = 0;
      const onMouseMove = (e) => {
        const delta = e.clientY - startY;
        const newH = Math.max(120, Math.min(850, startHeight + delta));
        watchContainer.style.height = `${newH}px`;
      };
      const onMouseUp = () => {
        watchResizer.classList.remove('resizing');
        document.removeEventListener('mousemove', onMouseMove);
        document.removeEventListener('mouseup', onMouseUp);
      };
      watchResizer.onmousedown = (e) => {
        e.preventDefault();
        startY = e.clientY;
        startHeight = parseInt(window.getComputedStyle(watchContainer).height, 10) || 340;
        watchResizer.classList.add('resizing');
        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
      };
      watchResizer.ondblclick = () => { watchContainer.style.height = '340px'; };
    }
  }

  // =============================================================================
  // 6. Bind Events
  // =============================================================================

  function bindEvents() {
    // Process stream events
    const btnPauseProc = document.getElementById('btn-sys-pause-proc');
    if (btnPauseProc) {
      btnPauseProc.onclick = () => {
        isProcPaused = !isProcPaused;
        btnPauseProc.textContent = isProcPaused ? 'Возобновить' : 'Пауза';
        btnPauseProc.className = isProcPaused
          ? 'btn btn-xs btn-warning rounded-pill px-2.5 py-0.5'
          : 'btn btn-xs btn-outline-secondary rounded-pill px-2.5 py-0.5';
      };
    }

    const btnRefreshProc = document.getElementById('btn-sys-refresh-proc');
    if (btnRefreshProc) {
      btnRefreshProc.onclick = () => fetchTopProcesses();
    }

    const searchProc = document.getElementById('sys-proc-search');
    if (searchProc) {
      searchProc.oninput = () => renderProcessTable();
    }

    // Network filter buttons
    document.querySelectorAll('.proc-net-filter-btn').forEach(btn => {
      btn.onclick = () => {
        document.querySelectorAll('.proc-net-filter-btn').forEach(b => {
          b.classList.remove('active', 'btn-outline-primary');
          b.classList.add('btn-outline-secondary');
        });
        btn.classList.add('active', 'btn-outline-primary');
        btn.classList.remove('btn-outline-secondary');
        currentNetFilter = btn.getAttribute('data-filter') || 'all';
        renderNetworkActivityTable();
      };
    });

    // Network search
    const netSearch = document.getElementById('proc-net-search');
    if (netSearch) {
      netSearch.oninput = () => renderNetworkActivityTable();
    }

    // Network pause
    const btnPauseNet = document.getElementById('btn-proc-pause-net');
    if (btnPauseNet) {
      btnPauseNet.onclick = () => {
        isNetPaused = !isNetPaused;
        btnPauseNet.textContent = isNetPaused ? 'Возобновить' : 'Пауза';
        btnPauseNet.className = isNetPaused
          ? 'btn btn-xs btn-warning rounded-pill px-2.5 py-0.5'
          : 'btn btn-xs btn-outline-secondary rounded-pill px-2.5 py-0.5';
        if (!isNetPaused) renderNetworkActivityTable();
      };
    }

    // Network refresh
    const btnRefreshNet = document.getElementById('btn-proc-refresh-net');
    if (btnRefreshNet) {
      btnRefreshNet.onclick = () => fetchNetworkActivity();
    }

    // File watcher buttons
    const btnWatchEx = document.getElementById('btn-proc-watch-exclusions');
    if (btnWatchEx) btnWatchEx.onclick = () => openWatchFoldersModal('exclusions');

    const btnChangeDir = document.getElementById('btn-proc-change-watch-dir');
    if (btnChangeDir) btnChangeDir.onclick = () => openWatchFoldersModal('folders');

    const badgeDir = document.getElementById('proc-watch-dir-badge');
    if (badgeDir) badgeDir.onclick = () => openWatchFoldersModal('folders');

    const btnLiveHelp = document.getElementById('btn-proc-live-help');
    if (btnLiveHelp) btnLiveHelp.onclick = () => showLiveWatcherHelpModal();

    // Modal navigation & controls
    const btnUp = document.getElementById('btn-modal-proc-folder-up');
    if (btnUp) {
      btnUp.onclick = () => {
        const parts = currentBrowserPath.replace(/\\+$/, '').split('\\');
        if (parts.length > 1) {
          parts.pop();
          let parentPath = parts.join('\\');
          if (parts.length === 1 && !parentPath.endsWith('\\')) parentPath += '\\';
          loadFolderBrowser(parentPath);
        }
      };
    }

    const btnGo = document.getElementById('btn-modal-proc-folder-go');
    const inputPath = document.getElementById('modal-proc-folder-path-input');
    if (btnGo && inputPath) {
      btnGo.onclick = () => {
        if (inputPath.value?.trim()) loadFolderBrowser(inputPath.value.trim());
      };
      inputPath.onkeydown = (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          btnGo.click();
        }
      };
    }

    const btnAddCurrent = document.getElementById('btn-modal-proc-folder-add-current');
    if (btnAddCurrent) {
      btnAddCurrent.onclick = () => {
        const val = inputPath ? inputPath.value.trim() : currentBrowserPath;
        if (val) addDirToStaged(val);
      };
    }

    // Presets
    document.querySelectorAll('.proc-preset-btn').forEach(btn => {
      btn.onclick = () => {
        const preset = btn.getAttribute('data-preset');
        let target = '';
        if (preset === 'project') target = 'C:\\Users\\onela\\AppData\\Local\\AI-Breadboard';
        else if (preset === 'downloads') target = 'C:\\Users\\onela\\Downloads';
        else if (preset === 'desktop') target = 'C:\\Users\\onela\\Desktop';
        else if (preset === 'temp') target = 'C:\\Users\\onela\\AppData\\Local\\Temp';
        if (target) {
          addDirToStaged(target);
          loadFolderBrowser(target);
        }
      };
    });

    // Exclusions switch & add
    const switchExActive = document.getElementById('switch-proc-exclusions-active');
    if (switchExActive) {
      switchExActive.onchange = (e) => toggleExclusionsActive(e.target.checked);
    }

    const btnAddEx = document.getElementById('btn-proc-add-exclusion');
    const selectExCat = document.getElementById('select-proc-exclusion-category');
    const inputExVal = document.getElementById('input-proc-exclusion-value');
    if (btnAddEx && selectExCat && inputExVal) {
      btnAddEx.onclick = () => addExclusionItem(selectExCat.value, inputExVal.value);
      inputExVal.onkeydown = (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          btnAddEx.click();
        }
      };
    }

    // Exclusions presets
    document.querySelectorAll('.proc-ex-preset-btn').forEach(btn => {
      btn.onclick = () => {
        const preset = btn.getAttribute('data-preset');
        if (preset) applyExclusionPreset(preset);
      };
    });

    // Modal apply button
    const btnApply = document.getElementById('btn-modal-proc-dirs-apply');
    const modalEl = document.getElementById('modal-proc-watch-folders');
    if (btnApply && modalEl) {
      btnApply.onclick = async () => {
        if (stagedWatchDirs.length === 0) {
          showWatchDirsAlert('Выберите хотя бы одну папку для мониторинга', 'warning');
          return;
        }

        btnApply.disabled = true;
        btnApply.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Применение...';

        try {
          const res = await fetch('/api/sysadmin/file-audit/watch-dirs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ paths: stagedWatchDirs })
          });
          const resData = await res.json();
          if (res.ok && resData.success) {
            if (window.bootstrap?.Modal) {
              const modal = window.bootstrap.Modal.getInstance(modalEl);
              if (modal) modal.hide();
            } else {
              modalEl.classList.remove('show');
              modalEl.style.display = 'none';
            }
            await fetchLiveFileEvents();
          } else {
            showWatchDirsAlert(`Ошибка: ${resData.detail || 'Не удалось применить список папок'}`, 'danger');
          }
        } catch (err) {
          showWatchDirsAlert(`Сетевая ошибка: ${err.message}`, 'danger');
        } finally {
          btnApply.disabled = false;
          btnApply.innerHTML = '<i class="bi bi-check2-circle me-1"></i> Применить и запустить';
        }
      };
    }

    initTableResizers();
  }

  // =============================================================================
  // 7. Poller & Tab Lifecycle
  // =============================================================================

  function setupPoller(seconds) {
    _currentUiRefreshSeconds = seconds;
    const pollHandler = async () => {
      await fetchTopProcesses();
      await fetchNetworkActivity();
      await fetchLiveFileEvents();
    };

    if (window.registerTabPoller) {
      window.registerTabPoller('tab-processes-load-inspector', pollHandler, seconds * 1000, { immediate: false });
    } else {
      if (window._procLoadInspectorInterval) {
        clearInterval(window._procLoadInspectorInterval);
        window._procLoadInspectorInterval = null;
      }
      window._procLoadInspectorInterval = setInterval(() => {
        if (window.isTabActive ? window.isTabActive('tab-processes-load-inspector') : true) {
          pollHandler();
        }
      }, seconds * 1000);
    }
  }

  async function initProcessesLoadInspectorTab() {
    console.log('[ProcessesLoadInspectorTab] Initializing...');
    bindEvents();
    await fetchTopProcesses();
    await fetchNetworkActivity();
    await fetchLiveFileEvents();
    setupPoller(_currentUiRefreshSeconds || 2);
  }

  function activateProcessesLoadInspectorTab() {
    if (window.isTabActive && !window.isTabActive('tab-processes-load-inspector')) return;
    console.log('[ProcessesLoadInspectorTab] Tab activated, refreshing metrics...');
    fetchTopProcesses();
    fetchNetworkActivity();
    fetchLiveFileEvents();
  }

  function deactivateProcessesLoadInspectorTab() {
    console.log('[ProcessesLoadInspectorTab] Tab deactivated');
  }

  window.initProcessesLoadInspectorTab = initProcessesLoadInspectorTab;
  window.activateProcessesLoadInspectorTab = activateProcessesLoadInspectorTab;
  window.deactivateProcessesLoadInspectorTab = deactivateProcessesLoadInspectorTab;

  if (document.getElementById('tab-processes-load-inspector')) {
    initProcessesLoadInspectorTab();
  }
})();
