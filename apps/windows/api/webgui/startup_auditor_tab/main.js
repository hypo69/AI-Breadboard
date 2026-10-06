/**
 * =============================================================================
 * Process Name: Windows Startup Auditor Tab - Main Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля main (Startup Auditor).
 *   Обеспечивает загрузку, фильтрацию, переключение состояния, AI-диагностику,
 *   асинхронное обновление снимков телеметрии и аудит дифференциальных изменений.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/webgui/startup_auditor_tab/main.js?v=20261006_v15" type="module"></script>
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: windows/api/webgui/startup_auditor_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-06 14:05:00
 * =============================================================================
 */

// Windows Startup Auditor Frontend Logic
(function () {
  let allEntries = [];
  let currentSummary = null;

  async function initStartupAuditorTab() {
    console.log('[StartupAuditor] Initializing tab...');
    bindEvents();
    await loadAuditData();
    checkRecentChangesBadge().catch(() => {});
  }

  function bindEvents() {
    const btnRefreshTelemetry = document.getElementById('sa-btn-refresh-telemetry');
    if (btnRefreshTelemetry) {
      btnRefreshTelemetry.onclick = () => refreshStartupTelemetry();
    }

    const btnRefreshLegacy = document.getElementById('sa-btn-refresh');
    if (btnRefreshLegacy) {
      btnRefreshLegacy.onclick = () => refreshStartupTelemetry();
    }

    const btnViewChanges = document.getElementById('sa-btn-view-changes');
    if (btnViewChanges) {
      btnViewChanges.onclick = () => showChangesModal();
    }

    const btnRefreshChangesModal = document.getElementById('sa-btn-refresh-changes-modal');
    if (btnRefreshChangesModal) {
      btnRefreshChangesModal.onclick = () => loadChangesData();
    }

    const searchInput = document.getElementById('sa-search-input');
    if (searchInput) {
      searchInput.oninput = () => renderFilteredTable();
    }

    const filterRisk = document.getElementById('sa-filter-risk');
    if (filterRisk) {
      filterRisk.onchange = () => renderFilteredTable();
    }

    const filterLocation = document.getElementById('sa-filter-location');
    if (filterLocation) {
      filterLocation.onchange = () => renderFilteredTable();
    }

    const filterState = document.getElementById('sa-filter-state');
    if (filterState) {
      filterState.onchange = () => renderFilteredTable();
    }

    const btnExportJson = document.getElementById('sa-btn-export-json');
    if (btnExportJson) {
      btnExportJson.onclick = () => {
        window.open('/api/v1/startup-auditor/export?format=json', '_blank');
      };
    }

    const btnExportCsv = document.getElementById('sa-btn-export-csv');
    if (btnExportCsv) {
      btnExportCsv.onclick = () => {
        window.open('/api/v1/startup-auditor/export?format=csv', '_blank');
      };
    }
  }

  /**
   * Асинхронно перезапускает сбор данных автозапуска через API телеметрии,
   * регистрирует снимок в SQLite и сохраняет дифференциальные изменения.
   */
  async function refreshStartupTelemetry() {
    const btn = document.getElementById('sa-btn-refresh-telemetry');
    const spinner = document.getElementById('sa-refresh-spinner');
    const statusText = document.getElementById('sa-telemetry-last-snap');

    if (btn) btn.disabled = true;
    if (spinner) spinner.classList.add('spinner-border', 'spinner-border-sm');

    try {
      if (statusText) statusText.textContent = 'Телеметрия: сбор снимка...';

      const res = await window.api.fetch('/api/v1/startup-auditor/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      if (res && res.report) {
        allEntries = res.report.entries || [];
        currentSummary = res.report.summary || {};
        renderSummaryCards(res.report);
        renderFilteredTable();
      }

      const count = res.changes_count || (res.changes ? res.changes.length : 0);
      const timeStr = new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit', second: '2-digit' });

      if (statusText) {
        statusText.textContent = count > 0 
          ? `Телеметрия: снимок ${timeStr} (изменений: ${count})`
          : `Телеметрия: снимок ${timeStr} (без изменений)`;
      }

      const badge = document.getElementById('sa-changes-badge');
      if (badge) {
        if (count > 0) {
          badge.textContent = count;
          badge.classList.remove('d-none');
        }
      }

      if (count > 0) {
        window.showToast?.(`Снимок сохранен! Зафиксировано изменений: ${count}`, 'warning');
      } else {
        window.showToast?.('Снимок телеметрии успешно зафиксирован (изменений нет)', 'success');
      }
    } catch (err) {
      console.error('[StartupAuditor] Error refreshing telemetry snapshot:', err);
      if (statusText) statusText.textContent = 'Телеметрия: ошибка сбора';
      window.showToast?.(`Ошибка обновления телеметрии: ${err.message}`, 'danger');
    } finally {
      if (btn) btn.disabled = false;
      if (spinner) spinner.classList.remove('spinner-border', 'spinner-border-sm');
    }
  }

  async function checkRecentChangesBadge() {
    try {
      const data = await window.api.fetch('/api/v1/startup-auditor/changes?limit=10');
      const badge = document.getElementById('sa-changes-badge');
      if (badge && data && data.changes && data.changes.length > 0) {
        badge.textContent = data.changes.length;
        badge.classList.remove('d-none');
      }
    } catch {
      // Игнорируем фоновые ошибки бейджа
    }
  }

  async function showChangesModal() {
    const modalEl = document.getElementById('sa-changes-modal');
    if (!modalEl) return;

    if (window.bootstrap && window.bootstrap.Modal) {
      const bsModal = window.bootstrap.Modal.getOrCreateInstance(modalEl);
      bsModal.show();
    }
    await loadChangesData();
  }

  async function loadChangesData() {
    const tbody = document.getElementById('sa-changes-table-body');
    const countEl = document.getElementById('sa-changes-modal-count');

    if (tbody) {
      tbody.innerHTML = `
        <tr>
          <td colspan="5" class="text-center py-4 text-muted">
            <div class="spinner-border spinner-border-sm text-warning me-2" role="status"></div>
            Загрузка истории изменений автозапуска из телеметрии...
          </td>
        </tr>
      `;
    }

    try {
      const data = await window.api.fetch('/api/v1/startup-auditor/changes?limit=100');
      const changes = data.changes || [];

      if (countEl) {
        countEl.textContent = `${changes.length} записей`;
      }

      if (changes.length === 0) {
        if (tbody) {
          tbody.innerHTML = `
            <tr>
              <td colspan="5" class="text-center py-4 text-muted">
                <i class="bi bi-shield-check text-success fs-4 d-block mb-1"></i>
                Изменений в конфигурации автозапуска между снимками телеметрии не зафиксировано.
              </td>
            </tr>
          `;
        }
        return;
      }

      if (tbody) {
        tbody.innerHTML = changes.map(ch => {
          const changeBadge = getChangeTypeBadge(ch.change_type);
          const timeFormatted = ch.created_at ? ch.created_at.replace('T', ' ').substring(0, 19) : '-';
          
          let detailsHtml = '';
          if (ch.change_type === 'added') {
            detailsHtml = `<span class="font-monospace small text-success text-truncate d-block" style="max-width: 420px;" title="${escapeHtml(ch.new_value)}">+ ${escapeHtml(ch.new_value || ch.item_name)}</span>`;
          } else if (ch.change_type === 'removed') {
            detailsHtml = `<span class="font-monospace small text-danger text-truncate d-block" style="max-width: 420px;" title="${escapeHtml(ch.old_value)}">- ${escapeHtml(ch.old_value || ch.item_name)}</span>`;
          } else if (ch.change_type === 'state_changed') {
            detailsHtml = `<div class="small">Состояние: <strong class="text-danger">${escapeHtml(ch.old_value)}</strong> <i class="bi bi-arrow-right"></i> <strong class="text-success">${escapeHtml(ch.new_value)}</strong></div>`;
          } else if (ch.change_type === 'risk_changed') {
            detailsHtml = `<div class="small">Уровень риска: <strong>${escapeHtml(ch.old_value)}</strong> <i class="bi bi-arrow-right"></i> <strong class="text-warning">${escapeHtml(ch.new_value)}</strong></div>`;
          } else {
            detailsHtml = `
              <div class="small font-monospace text-muted text-truncate" style="max-width: 420px;" title="Было: ${escapeHtml(ch.old_value)}">Было: ${escapeHtml(ch.old_value || '-')}</div>
              <div class="small font-monospace text-primary text-truncate" style="max-width: 420px;" title="Стало: ${escapeHtml(ch.new_value)}">Стало: ${escapeHtml(ch.new_value || '-')}</div>
            `;
          }

          return `
            <tr>
              <td class="font-monospace small text-muted">${timeFormatted}</td>
              <td class="text-center">${changeBadge}</td>
              <td>
                <div class="fw-semibold text-truncate" style="max-width: 190px;" title="${escapeHtml(ch.item_name)}">${escapeHtml(ch.item_name)}</div>
              </td>
              <td><span class="sa-badge sa-badge-loc">${escapeHtml(ch.location_type || 'registry_run')}</span></td>
              <td>${detailsHtml}</td>
            </tr>
          `;
        }).join('');
      }
    } catch (err) {
      console.error('[StartupAuditor] Error loading changes history:', err);
      if (tbody) {
        tbody.innerHTML = `
          <tr>
            <td colspan="5" class="text-center py-4 text-danger">
              Ошибка загрузки истории изменений: ${escapeHtml(err.message)}
            </td>
          </tr>
        `;
      }
    }
  }

  function getChangeTypeBadge(changeType) {
    switch (changeType) {
      case 'added':
        return '<span class="sa-badge sa-badge-enabled"><i class="bi bi-plus-circle"></i> Добавлен</span>';
      case 'removed':
        return '<span class="sa-badge sa-badge-disabled"><i class="bi bi-dash-circle"></i> Удален</span>';
      case 'state_changed':
        return '<span class="sa-badge sa-risk-warning"><i class="bi bi-toggle2-on"></i> Статус</span>';
      case 'path_changed':
        return '<span class="sa-badge sa-risk-suspicious"><i class="bi bi-pencil"></i> Путь</span>';
      case 'risk_changed':
        return '<span class="sa-badge sa-risk-critical"><i class="bi bi-shield-exclamation"></i> Риск</span>';
      default:
        return `<span class="sa-badge sa-badge-cat">${escapeHtml(changeType)}</span>`;
    }
  }

  async function loadAuditData() {
    const tbody = document.getElementById('sa-table-body');
    if (tbody) {
      tbody.innerHTML = `
        <tr>
          <td colspan="8" class="text-center py-4 text-muted">
            <div class="spinner-border spinner-border-sm text-primary me-2" role="status"></div>
            Выполняется сканирование точек автозапуска Windows...
          </td>
        </tr>
      `;
    }

    try {
      const report = await window.api.fetch('/api/v1/startup-auditor/audit');
      allEntries = report.entries || [];
      currentSummary = report.summary || {};

      renderSummaryCards(report);
      renderFilteredTable();
    } catch (err) {
      console.error('[StartupAuditor] Error loading audit report:', err);
      if (tbody) {
        tbody.innerHTML = `
          <tr>
            <td colspan="8" class="text-center py-4 text-danger">
              Ошибка загрузки данных аудита: ${err.message}
            </td>
          </tr>
        `;
      }
    }
  }

  function renderSummaryCards(report) {
    const summary = report.summary || {};
    
    // Health Score
    const scoreEl = document.getElementById('sa-health-score');
    if (scoreEl) {
      scoreEl.textContent = summary.health_score ?? '--';
      scoreEl.className = 'sa-card-value ' + (
        summary.health_score >= 80 ? 'text-success' : (summary.health_score >= 60 ? 'text-warning' : 'text-danger')
      );
    }

    // Counters
    const activeEl = document.getElementById('sa-active-count');
    if (activeEl) activeEl.textContent = summary.active_entries ?? '--';

    const totalEl = document.getElementById('sa-total-count');
    if (totalEl) totalEl.textContent = summary.total_entries ?? '--';

    const disabledEl = document.getElementById('sa-disabled-count');
    if (disabledEl) disabledEl.textContent = summary.disabled_entries ?? '0';

    const brokenEl = document.getElementById('sa-broken-count');
    if (brokenEl) brokenEl.textContent = summary.broken_entries ?? '0';

    const threatsEl = document.getElementById('sa-threats-count');
    if (threatsEl) threatsEl.textContent = (summary.critical_count || 0) + (summary.suspicious_count || 0);

    // Recommendations
    const recDesc = document.getElementById('sa-rec-desc');
    if (recDesc) {
      if (report.recommendations && report.recommendations.length > 0) {
        recDesc.innerHTML = report.recommendations.map(r => `<div>${r}</div>`).join('');
      } else {
        recDesc.textContent = 'Конфигурация автозапуска оптимальна, критических замечаний нет.';
      }
    }
  }

  function renderFilteredTable() {
    const tbody = document.getElementById('sa-table-body');
    const tableCount = document.getElementById('sa-table-count');
    if (!tbody) return;

    const query = (document.getElementById('sa-search-input')?.value || '').toLowerCase().trim();
    const riskFilter = (document.getElementById('sa-filter-risk')?.value || '').toLowerCase();
    const locFilter = (document.getElementById('sa-filter-location')?.value || '').toLowerCase();
    const stateFilter = (document.getElementById('sa-filter-state')?.value || '').toLowerCase();

    const filtered = allEntries.filter(e => {
      if (query) {
        const fullText = `${e.name || ''} ${e.command || ''} ${e.executable_path || ''} ${e.publisher || ''} ${e.category || ''}`.toLowerCase();
        if (!fullText.includes(query)) return false;
      }
      if (riskFilter && (e.risk_level || '').toLowerCase() !== riskFilter) {
        return false;
      }
      if (locFilter && (e.location_type || '').toLowerCase() !== locFilter) {
        return false;
      }
      if (stateFilter === 'enabled' && !e.is_enabled) return false;
      if (stateFilter === 'disabled' && e.is_enabled) return false;

      return true;
    });

    if (tableCount) {
      tableCount.textContent = `Показано: ${filtered.length} из ${allEntries.length}`;
    }

    if (filtered.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="8" class="text-center py-5 text-muted">
            <div class="fs-4 mb-2">🔍</div>
            <div>Элементы автозапуска по заданным критериям не найдены</div>
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = filtered.map(e => {
      const isEnabled = e.is_enabled;
      const statusBadge = isEnabled
        ? '<span class="sa-badge sa-badge-enabled"><i class="bi bi-check-circle-fill"></i> ВКЛ</span>'
        : '<span class="sa-badge sa-badge-disabled"><i class="bi bi-dash-circle"></i> ОТКЛ</span>';

      const riskBadge = getRiskBadge(e.risk_level);
      const isBroken = !e.file_exists && e.executable_path;
      
      const pathDisplay = isBroken
        ? `<div class="d-flex align-items-center gap-1 text-danger small font-monospace">
             <i class="bi bi-x-octagon-fill text-danger flex-shrink-0"></i>
             <span class="text-truncate fw-semibold" style="max-width: 480px;" title="${e.executable_path || e.command}">[Файл не найден] ${e.executable_path || e.command}</span>
           </div>`
        : `<div class="font-monospace small text-truncate" style="max-width: 480px; color: var(--text-color);" title="${e.command || e.executable_path}">
             ${e.executable_path || e.command}
           </div>`;

      const argsDisplay = e.arguments ? `
        <div class="d-flex align-items-center gap-1 font-monospace text-truncate mt-1 text-muted" style="max-width: 480px; font-size: 0.73rem;" title="${e.arguments}">
          <span class="badge bg-secondary-subtle text-secondary-emphasis border border-secondary" style="font-size: 0.68rem; padding: 1px 4px;">ARG</span>
          <span class="text-truncate">${e.arguments}</span>
        </div>` : '';

      const toggleIcon = isEnabled
        ? '<i class="bi bi-toggle2-on text-success" style="font-size: 1.4rem;"></i>'
        : '<i class="bi bi-toggle2-off text-muted" style="font-size: 1.4rem;"></i>';
      const toggleTitle = isEnabled ? 'Отключить элемент автозапуска' : 'Включить элемент автозапуска';

      let impactBadge = '';
      if (!isEnabled) {
        impactBadge = '<span class="sa-badge sa-badge-disabled">Отключено</span>';
      } else if (e.boot_impact === 'Высокое') {
        impactBadge = '<span class="sa-badge sa-risk-critical">Высокое</span>';
      } else if (e.boot_impact === 'Среднее') {
        impactBadge = '<span class="sa-badge sa-risk-warning">Среднее</span>';
      } else {
        impactBadge = '<span class="sa-badge sa-badge-cat">Низкое</span>';
      }

      return `
        <tr class="sa-row-item" data-id="${e.id}" style="cursor: pointer;" title="Нажмите для подробного AI-аудита">
          <td class="text-center">${statusBadge}</td>
          <td>
            <div class="fw-semibold text-truncate" style="max-width: 230px; color: var(--text-color);" title="${e.name}">${e.name}</div>
            <div class="small text-truncate text-muted" style="max-width: 230px; font-size: 0.73rem;" title="${e.publisher || 'Неизвестен'}">${e.publisher || 'Неизвестный издатель'}</div>
          </td>
          <td><span class="sa-badge sa-badge-loc">${e.location_type}</span></td>
          <td><span class="sa-badge sa-badge-cat">${e.category || 'Неизвестно'}</span></td>
          <td class="text-center">${riskBadge}</td>
          <td>
            ${pathDisplay}
            ${argsDisplay}
          </td>
          <td class="text-center">${impactBadge}</td>
          <td class="text-center">
            <button class="sa-toggle-btn" data-id="${e.id}" data-enabled="${isEnabled}" title="${toggleTitle}">
              ${toggleIcon}
            </button>
          </td>
        </tr>
      `;
    }).join('');

    // Attach row click listeners for modal details
    tbody.querySelectorAll('.sa-row-item').forEach(row => {
      row.onclick = (evt) => {
        // Prevent modal open when clicking directly on the toggle button
        if (evt.target.closest('.sa-toggle-btn')) {
          return;
        }
        const entryId = row.getAttribute('data-id');
        const entry = allEntries.find(item => item.id === entryId);
        if (entry) {
          showEntryModal(entry);
        }
      };
    });

    // Attach toggle listeners
    tbody.querySelectorAll('.sa-toggle-btn').forEach(btn => {
      btn.onclick = async (evt) => {
        evt.stopPropagation();
        const entryId = btn.getAttribute('data-id');
        const currentState = btn.getAttribute('data-enabled') === 'true';
        const newState = !currentState;
        try {
          btn.disabled = true;
          btn.style.opacity = '0.5';
          const res = await window.api.fetch('/api/v1/startup-auditor/toggle', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ entry_id: entryId, enable: newState })
          });
          if (res.success) {
            window.showToast?.(`Автозагрузка ${newState ? 'включена' : 'отключена'}`, 'success');
            await loadAuditData();
          } else {
            window.showToast?.(`Ошибка переключения: ${res.message}`, 'danger') || alert(`Ошибка переключения: ${res.message}`);
          }
        } catch (err) {
          window.showToast?.(`Ошибка: ${err.message}`, 'danger') || alert(`Ошибка: ${err.message}`);
        } finally {
          btn.disabled = false;
          btn.style.opacity = '1';
        }
      };
    });
  }

  function showEntryModal(entry) {
    if (!entry) return;

    const modalEl = document.getElementById('sa-entry-detail-modal');
    if (!modalEl) return;

    // Header info
    const titleEl = document.getElementById('sa-modal-title');
    if (titleEl) titleEl.textContent = entry.name || 'Детали программы';

    const statusBadgeEl = document.getElementById('sa-modal-status-badge');
    if (statusBadgeEl) {
      statusBadgeEl.innerHTML = entry.is_enabled
        ? '<span class="sa-badge sa-badge-enabled"><i class="bi bi-check-circle-fill"></i> ВКЛ</span>'
        : '<span class="sa-badge sa-badge-disabled"><i class="bi bi-dash-circle"></i> ОТКЛ</span>';
    }

    const riskBadgeEl = document.getElementById('sa-modal-risk-badge');
    if (riskBadgeEl) {
      riskBadgeEl.innerHTML = getRiskBadge(entry.risk_level);
    }

    // Metadata Fields
    const setTxt = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.textContent = val ?? '-';
    };
    const setHtml = (id, html) => {
      const el = document.getElementById(id);
      if (el) el.innerHTML = html;
    };

    setTxt('sa-modal-name', entry.name);
    setTxt('sa-modal-publisher', entry.publisher || 'Неизвестный разработчик');
    setTxt('sa-modal-location-type', entry.location_type || 'registry_run');
    setTxt('sa-modal-category', entry.category || 'Неизвестно');
    setTxt('sa-modal-boot-impact', entry.boot_impact || 'Низкое');
    setTxt('sa-modal-location-path', entry.location_path || 'Не указан');
    
    setHtml('sa-modal-is-signed', entry.is_signed
      ? '<span class="text-success"><i class="bi bi-patch-check me-1"></i>Подписан (Valid)</span>'
      : '<span class="text-muted"><i class="bi bi-patch-question me-1"></i>Без подписи / Неизвестно</span>'
    );

    setHtml('sa-modal-file-exists', entry.file_exists
      ? '<span class="text-success"><i class="bi bi-file-earmark-check me-1"></i>Файл существует</span>'
      : '<span class="text-danger fw-bold"><i class="bi bi-file-earmark-x me-1"></i>Файл не найден (битая ссылка)</span>'
    );

    setTxt('sa-modal-file-size', entry.file_size_kb > 0 ? `${entry.file_size_kb.toFixed(1)} KB` : '-');
    setTxt('sa-modal-executable-path', entry.executable_path || entry.command || 'Путь не указан');
    setTxt('sa-modal-command', entry.command || '-');

    // Reset AI Diagnostic section
    const aiExplanation = document.getElementById('sa-modal-ai-explanation');
    if (aiExplanation) {
      aiExplanation.innerHTML = `Нажмите «Анализ контекста», чтобы получить экспертное объяснение назначения программы от языковой модели, оценку рисков и рекомендации по оптимизации.`;
    }

    // AI Diagnose button
    const diagnoseBtn = document.getElementById('btn-sa-modal-diagnose');
    if (diagnoseBtn) {
      diagnoseBtn.onclick = async () => {
        aiExplanation.innerHTML = `
          <div class="d-flex align-items-center gap-2 py-2 text-primary">
            <div class="spinner-border spinner-border-sm" role="status"></div>
            <span>Генерация AI-диагностики и анализа рисков для программы «${escapeHtml(entry.name)}»...</span>
          </div>
        `;
        const activeModel = window.activeModelName
          || window.userSettings?.model
          || document.getElementById('model-select')?.value
          || document.getElementById('header-model-select')?.value
          || '';
        try {
          const res = await window.api.fetch('/api/v1/startup-auditor/explain', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              entry_id: entry.id,
              name: entry.name,
              publisher: entry.publisher,
              executable_path: entry.executable_path,
              command: entry.command,
              arguments: entry.arguments,
              location_type: entry.location_type,
              location_path: entry.location_path,
              risk_level: entry.risk_level,
              is_enabled: entry.is_enabled,
              file_exists: entry.file_exists,
              is_signed: entry.is_signed,
              boot_impact: entry.boot_impact,
              model: activeModel || undefined
            })
          });

          aiExplanation.innerHTML = `
            <div class="mb-2"><strong class="text-primary"><i class="bi bi-card-text me-1"></i>Назначение:</strong> ${escapeHtml(res.summary)}</div>
            <div class="mb-2"><strong class="text-muted"><i class="bi bi-building me-1"></i>Разработчик / Категория:</strong> ${escapeHtml(res.developer || entry.publisher || 'Неизвестен')} (${escapeHtml(res.category || 'Приложение')})</div>
            <div class="mb-2"><strong class="text-warning"><i class="bi bi-shield-lock me-1"></i>Оценка безопасности:</strong> ${escapeHtml(res.security_verdict)}</div>
            <div class="mb-2"><strong class="text-info"><i class="bi bi-speedometer2 me-1"></i>Влияние на запуск:</strong> ${escapeHtml(res.boot_impact_analysis)}</div>
            <div class="p-2 mb-2 rounded alert alert-warning">
              <strong class="text-warning"><i class="bi bi-lightbulb me-1"></i>Рекомендация:</strong> ${escapeHtml(res.startup_recommendation)}
            </div>
            ${res.action_steps && res.action_steps.length > 0 ? `
              <h6 class="small text-uppercase text-muted fw-bold mb-1">Рекомендуемые действия:</h6>
              <ul class="mb-0 ps-3">
                ${res.action_steps.map(s => `<li>${escapeHtml(s)}</li>`).join('')}
              </ul>
            ` : ''}
          `;
        } catch (err) {
          aiExplanation.innerHTML = `<div class="text-danger py-2"><i class="bi bi-exclamation-octagon me-1"></i>Ошибка получения AI-анализа: ${escapeHtml(err.message)}</div>`;
        }
      };
    }

    // Modal Footer Toggle Button
    const modalToggleBtn = document.getElementById('btn-sa-modal-toggle');
    if (modalToggleBtn) {
      modalToggleBtn.innerHTML = entry.is_enabled
        ? '<i class="bi bi-toggle2-off me-1 text-warning"></i>Отключить автозапуск'
        : '<i class="bi bi-toggle2-on me-1 text-success"></i>Включить автозапуск';
      modalToggleBtn.onclick = async () => {
        const newState = !entry.is_enabled;
        try {
          modalToggleBtn.disabled = true;
          const res = await window.api.fetch('/api/v1/startup-auditor/toggle', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ entry_id: entry.id, enable: newState })
          });
          if (res.success) {
            entry.is_enabled = newState;
            showEntryModal(entry);
            window.showToast?.(`Автозагрузка ${newState ? 'включена' : 'отключена'}`, 'success');
            await loadAuditData();
          } else {
            window.showToast?.(`Ошибка переключения: ${res.message}`, 'danger') || alert(`Ошибка переключения: ${res.message}`);
          }
        } catch (err) {
          window.showToast?.(`Ошибка: ${err.message}`, 'danger') || alert(`Ошибка: ${err.message}`);
        } finally {
          modalToggleBtn.disabled = false;
        }
      };
    }

    // Modal Footer Copy Button
    const modalCopyBtn = document.getElementById('btn-sa-modal-copy');
    if (modalCopyBtn) {
      modalCopyBtn.onclick = () => {
        const textToCopy = entry.executable_path || entry.command || '';
        navigator.clipboard.writeText(textToCopy).then(() => {
          const orig = modalCopyBtn.innerHTML;
          modalCopyBtn.innerHTML = '<i class="bi bi-check2 me-1 text-success"></i>Скопировано!';
          setTimeout(() => { modalCopyBtn.innerHTML = orig; }, 1800);
        });
      };
    }

    // Show modal via Bootstrap
    if (window.bootstrap && window.bootstrap.Modal) {
      const bsModal = window.bootstrap.Modal.getOrCreateInstance(modalEl);
      bsModal.show();
    }
  }

  function getRiskBadge(level) {
    switch ((level || '').toLowerCase()) {
      case 'critical':
        return '<span class="sa-badge sa-risk-critical"><i class="bi bi-shield-x"></i> CRITICAL</span>';
      case 'suspicious':
        return '<span class="sa-badge sa-risk-suspicious"><i class="bi bi-exclamation-octagon"></i> SUSPICIOUS</span>';
      case 'warning':
        return '<span class="sa-badge sa-risk-warning"><i class="bi bi-exclamation-triangle"></i> WARNING</span>';
      case 'notice':
        return '<span class="sa-badge sa-risk-notice"><i class="bi bi-info-circle"></i> NOTICE</span>';
      default:
        return '<span class="sa-badge sa-risk-clean"><i class="bi bi-shield-check"></i> CLEAN</span>';
    }
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // Expose globally for Apps Hub
  window.initStartupAuditorTab = initStartupAuditorTab;
})();
