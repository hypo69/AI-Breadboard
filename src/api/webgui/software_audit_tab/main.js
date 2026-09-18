// Software Audit Tab JavaScript Module
(function() {
  let allApps = [];
  let auditReport = null;
  let isInitialized = false;

  function formatRelativeTime(dateStr) {
    if (!dateStr) return '<span class="text-muted">Нет данных</span>';
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return '<span class="text-muted">-</span>';
    const now = new Date();
    const diffMs = now - d;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHrs = Math.floor(diffMin / 60);
    const diffDays = Math.floor(diffHrs / 24);

    if (diffDays > 90) {
      return `<span class="text-warning" title="${d.toLocaleString()}">${diffDays} дн назад</span>`;
    } else if (diffDays > 0) {
      return `<span class="text-success" title="${d.toLocaleString()}">${diffDays} дн назад</span>`;
    } else if (diffHrs > 0) {
      return `<span class="text-info" title="${d.toLocaleString()}">${diffHrs} ч назад</span>`;
    } else if (diffMin > 0) {
      return `<span class="text-info" title="${d.toLocaleString()}">${diffMin} мин назад</span>`;
    } else {
      return `<span class="text-info">Только что</span>`;
    }
  }

  function formatDuration(sec) {
    if (!sec || sec <= 0) return '<span class="text-muted">-</span>';
    const hrs = Math.floor(sec / 3600);
    const mins = Math.floor((sec % 3600) / 60);
    if (hrs > 0) return `${hrs}ч ${mins}м`;
    if (mins > 0) return `${mins} мин`;
    return `${sec} сек`;
  }

  async function loadSoftwareAudit() {
    const tbody = document.getElementById('sw-audit-tbody');
    const badge = document.getElementById('sw-audit-status-badge');
    if (badge) badge.innerText = '● Сканирование реестра...';

    try {
      // 1. Пытаемся получить сводный аналитический отчет
      let reportRes = await fetch('/api/windows/software/audit');
      if (!reportRes.ok) {
        reportRes = await fetch('/api/v1/windows-admin/software/audit');
      }
      if (reportRes.ok) {
        auditReport = await reportRes.json();
      }

      // 2. Получаем полный список установленных приложений
      let appsRes = await fetch('/api/windows/software?limit=500');
      if (!appsRes.ok) {
        // Fallback на router_windows_admin
        appsRes = await fetch('/api/v1/windows-admin/software?limit=500');
      }

      if (appsRes.ok) {
        allApps = await appsRes.json();
      } else {
        throw new Error(`HTTP ${appsRes.status}`);
      }

      // Обновляем метрики
      updateMetrics();
      // Заполняем выпадающий список категорий
      populateCategories();
      // Рендерим таблицу
      renderTable();

      if (badge) {
        badge.className = 'badge rounded-pill bg-success-subtle text-success border border-success px-3 py-2';
        badge.innerText = `● Аудит: Завершено (${allApps.length} программ)`;
      }

      const timeEl = document.getElementById('sw-last-scanned-time');
      if (timeEl) {
        timeEl.innerText = `Обновлено: ${new Date().toLocaleTimeString()}`;
      }
    } catch (err) {
      console.error('[SoftwareAuditTab] Failed to load software audit:', err);
      if (tbody) {
        tbody.innerHTML = `<tr><td colspan="8" class="text-center text-danger p-4">Ошибка сбора сведений об установленном ПО: ${err.message}</td></tr>`;
      }
      if (badge) {
        badge.className = 'badge rounded-pill bg-danger-subtle text-danger border border-danger px-3 py-2';
        badge.innerText = '● Ошибка аудита';
      }
    }
  }

  function updateMetrics() {
    const totalEl = document.getElementById('sw-metric-total');
    const activeEl = document.getElementById('sw-metric-active');
    const dormantEl = document.getElementById('sw-metric-dormant');
    const catEl = document.getElementById('sw-metric-categories');

    if (auditReport) {
      if (totalEl) totalEl.innerText = auditReport.total_apps || allApps.length;
      if (activeEl) activeEl.innerText = auditReport.active_apps_count || 0;
      if (dormantEl) dormantEl.innerText = auditReport.never_launched_or_dormant_count || 0;
      if (catEl) catEl.innerText = Object.keys(auditReport.categories_breakdown || {}).length;
    } else {
      const activeCount = allApps.filter(a => a.execution_info && a.execution_info.last_run_time).length;
      if (totalEl) totalEl.innerText = allApps.length;
      if (activeEl) activeEl.innerText = activeCount;
      if (dormantEl) dormantEl.innerText = allApps.length - activeCount;
      const cats = new Set(allApps.map(a => a.category).filter(Boolean));
      if (catEl) catEl.innerText = cats.size;
    }
  }

  function populateCategories() {
    const sel = document.getElementById('sw-category-filter');
    if (!sel) return;

    const currentVal = sel.value;
    const cats = Array.from(new Set(allApps.map(a => a.category).filter(Boolean))).sort();

    sel.innerHTML = '<option value="">Все категории</option>' + cats.map(c =>
      `<option value="${c}" ${c === currentVal ? 'selected' : ''}>${c}</option>`
    ).join('');
  }

  function getFilteredApps() {
    const search = (document.getElementById('sw-search-input')?.value || '').toLowerCase().trim();
    const category = document.getElementById('sw-category-filter')?.value || '';
    const status = document.getElementById('sw-status-filter')?.value || 'all';

    const dormantThresholdMs = 90 * 24 * 3600 * 1000;
    const now = Date.now();

    return allApps.filter(app => {
      // Поиск по ключевым полям
      if (search) {
        const text = `${app.display_name || ''} ${app.name || ''} ${app.publisher || ''} ${app.purpose_description || ''}`.toLowerCase();
        if (!text.includes(search)) return false;
      }

      // Фильтр по категории
      if (category && app.category !== category) {
        return false;
      }

      // Фильтр по статусу использования
      const lastRun = app.execution_info?.last_run_time ? new Date(app.execution_info.last_run_time).getTime() : null;
      if (status === 'active') {
        if (!lastRun || (now - lastRun > dormantThresholdMs)) return false;
      } else if (status === 'dormant') {
        if (lastRun && (now - lastRun <= dormantThresholdMs)) return false;
      }

      return true;
    });
  }

  function renderTable() {
    const tbody = document.getElementById('sw-audit-tbody');
    const badge = document.getElementById('sw-filtered-count-badge');
    if (!tbody) return;

    const filtered = getFilteredApps();
    if (badge) {
      badge.innerText = `${filtered.length} / ${allApps.length}`;
    }

    if (filtered.length === 0) {
      tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted p-4">Программы по заданным критериям не найдены</td></tr>';
      return;
    }

    tbody.innerHTML = filtered.map((app, idx) => {
      const exec = app.execution_info;
      const lastRunFormatted = exec ? formatRelativeTime(exec.last_run_time) : '<span class="text-muted">Никогда</span>';
      const runCount = exec && exec.run_count ? `<span class="badge bg-secondary">${exec.run_count}</span>` : '<span class="text-muted">0</span>';
      const focusTime = exec ? formatDuration(exec.focus_time_seconds) : '<span class="text-muted">-</span>';
      const sizeStr = app.size_mb > 0 ? `${app.size_mb} MB` : '<span class="text-muted">-</span>';
      const archBadge = app.architecture === 'x64' ? '<span class="badge bg-primary-subtle text-primary" style="font-size: 0.65rem;">x64</span>' : '<span class="badge bg-secondary-subtle text-secondary" style="font-size: 0.65rem;">x86</span>';

      return `
        <tr class="sw-row-item" data-idx="${idx}" style="cursor: pointer;" title="Нажмите для AI-диагностики и подробных сведений">
          <td>
            <div class="fw-bold text-white text-truncate" style="max-width: 260px;" title="${app.display_name || app.name}">
              ${app.display_name || app.name}
            </div>
            <div class="small text-muted text-truncate" style="max-width: 260px; font-size: 0.72rem;" title="${app.purpose_description || ''}">
              ${app.purpose_description || 'Прикладное ПО'}
            </div>
          </td>
          <td>
            <span class="sw-badge-category">${app.category || 'Прочее'}</span>
          </td>
          <td>
            <div class="text-truncate text-light" style="max-width: 180px;" title="${app.publisher || 'Неизвестен'}">${app.publisher || '<span class="text-muted">-</span>'}</div>
            <div class="small text-muted" style="font-size: 0.72rem;">${app.version || '-'}</div>
          </td>
          <td>${lastRunFormatted}</td>
          <td>${runCount}</td>
          <td class="small text-light">${focusTime}</td>
          <td class="small">
            <div>${sizeStr}</div>
            <div>${archBadge}</div>
          </td>
          <td style="text-align: right;">
            <button class="btn btn-sm btn-outline-info p-1 px-2 btn-sw-detail" data-idx="${idx}" title="Подробности">
              <i class="bi bi-info-circle"></i>
            </button>
          </td>
        </tr>
      `;
    }).join('');

    // Привязка кликабельности всей строки
    tbody.querySelectorAll('.sw-row-item').forEach(row => {
      row.onclick = (evt) => {
        const idx = parseInt(row.getAttribute('data-idx'), 10);
        showAppDetails(filtered[idx]);
      };
    });

    // Привязка обработчиков кнопки деталей
    tbody.querySelectorAll('.btn-sw-detail').forEach(btn => {
      btn.onclick = (evt) => {
        evt.stopPropagation();
        const idx = parseInt(btn.getAttribute('data-idx'), 10);
        showAppDetails(filtered[idx]);
      };
    });
  }

  function showAppDetails(app) {
    if (!app) return;
    const exec = app.execution_info;

    if (window.AITableModal) {
      window.AITableModal.show({
        icon: '📦',
        title: app.display_name || app.name,
        subtitle: app.publisher || 'Неизвестный разработчик',
        tableType: 'software',
        badges: [
          { text: app.category || 'ПО', class: 'badge bg-info' },
          { text: app.architecture || 'x64', class: 'badge bg-secondary' }
        ],
        metadata: [
          { label: 'Продукт', value: app.display_name || app.name },
          { label: 'Издатель', value: app.publisher || 'Не указан' },
          { label: 'Версия', value: app.version || 'Не указана' },
          { label: 'Категория', value: app.category || 'Прочее' },
          { label: 'Размер на диске', value: app.size_mb > 0 ? `${app.size_mb} MB` : 'Не указан' },
          { label: 'Дата установки', value: app.install_date || 'Неизвестно' },
          { label: 'Запусков (UserAssist)', value: exec?.run_count ? `${exec.run_count} раз` : '0' },
          { label: 'Время в фокусе', value: exec ? formatDuration(exec.focus_time_seconds) : '-' },
          { label: 'Последний запуск', value: exec?.last_run_time ? new Date(exec.last_run_time).toLocaleString() : 'Нет данных', fullWidth: true },
          { label: 'Путь установки', value: app.install_location || 'Не указан', isCode: true, fullWidth: true }
        ],
        rawTitle: 'Команда удаления / Путь',
        rawContent: app.uninstall_string || app.install_location || '',
        requestData: {
          install_location: app.install_location,
          uninstall_string: app.uninstall_string,
          version: app.version,
          size_mb: app.size_mb,
          run_count: exec?.run_count
        }
      });
      return;
    }
  }

  function exportJson() {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(allApps, null, 2));
    const dlAnchor = document.createElement('a');
    dlAnchor.setAttribute("href", dataStr);
    dlAnchor.setAttribute("download", `software_audit_${new Date().toISOString().slice(0, 10)}.json`);
    document.body.appendChild(dlAnchor);
    dlAnchor.click();
    dlAnchor.remove();
  }

  window.initSoftwareAuditTab = async function() {
    console.log('[SoftwareAuditTab] Initializing Software Audit tab...');
    
    // Привязываем контролы поиска и фильтрации
    const searchInput = document.getElementById('sw-search-input');
    const catSelect = document.getElementById('sw-category-filter');
    const statusSelect = document.getElementById('sw-status-filter');
    const refreshBtn = document.getElementById('btn-sw-audit-refresh');
    const exportBtn = document.getElementById('btn-sw-audit-export');

    if (searchInput) searchInput.oninput = renderTable;
    if (catSelect) catSelect.onchange = renderTable;
    if (statusSelect) statusSelect.onchange = renderTable;
    if (refreshBtn) refreshBtn.onclick = loadSoftwareAudit;
    if (exportBtn) exportBtn.onclick = exportJson;

    await loadSoftwareAudit();
    isInitialized = true;
  };
})();
