// Windows Startup Auditor Frontend Logic
(function () {
  let allEntries = [];
  let currentSummary = null;

  async function initStartupAuditorTab() {
    console.log('[StartupAuditor] Initializing tab...');
    bindEvents();
    await loadAuditData();
  }

  function bindEvents() {
    const btnRefresh = document.getElementById('sa-btn-refresh');
    if (btnRefresh) {
      btnRefresh.onclick = () => loadAuditData();
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
          <td colspan="8" class="text-center py-5" style="color: #94a3b8;">
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
        : `<div class="font-monospace small text-truncate" style="max-width: 480px; color: #cbd5e1;" title="${e.command || e.executable_path}">
             ${e.executable_path || e.command}
           </div>`;

      const argsDisplay = e.arguments ? `
        <div class="d-flex align-items-center gap-1 font-monospace text-truncate mt-1" style="max-width: 480px; font-size: 0.73rem; color: #94a3b8;" title="${e.arguments}">
          <span class="badge bg-secondary-subtle text-secondary-emphasis border border-secondary" style="font-size: 0.68rem; padding: 1px 4px;">ARG</span>
          <span class="text-truncate">${e.arguments}</span>
        </div>` : '';

      const toggleIcon = isEnabled
        ? '<i class="bi bi-toggle2-on text-success" style="font-size: 1.4rem;"></i>'
        : '<i class="bi bi-toggle2-off" style="font-size: 1.4rem; color: #64748b;"></i>';
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
            <div class="fw-semibold text-truncate" style="max-width: 230px; color: #f8fafc;" title="${e.name}">${e.name}</div>
            <div class="small text-truncate" style="max-width: 230px; color: #94a3b8; font-size: 0.73rem;" title="${e.publisher || 'Неизвестен'}">${e.publisher || 'Неизвестный издатель'}</div>
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
      : '<span class="text-secondary"><i class="bi bi-patch-question me-1"></i>Без подписи / Неизвестно</span>'
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
          <div class="d-flex align-items-center gap-2 py-2 text-info">
            <div class="spinner-border spinner-border-sm" role="status"></div>
            <span>Генерация AI-диагностики и анализа рисков для программы «${escapeHtml(entry.name)}»...</span>
          </div>
        `;
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
              boot_impact: entry.boot_impact
            })
          });

          aiExplanation.innerHTML = `
            <div class="mb-2"><strong class="text-info"><i class="bi bi-card-text me-1"></i>Назначение:</strong> ${escapeHtml(res.summary)}</div>
            <div class="mb-2"><strong class="text-secondary"><i class="bi bi-building me-1"></i>Разработчик / Категория:</strong> ${escapeHtml(res.developer || entry.publisher || 'Неизвестен')} (${escapeHtml(res.category || 'Приложение')})</div>
            <div class="mb-2"><strong class="text-warning"><i class="bi bi-shield-lock me-1"></i>Оценка безопасности:</strong> ${escapeHtml(res.security_verdict)}</div>
            <div class="mb-2"><strong class="text-info"><i class="bi bi-speedometer2 me-1"></i>Влияние на запуск:</strong> ${escapeHtml(res.boot_impact_analysis)}</div>
            <div class="p-2 mb-2 rounded bg-dark-subtle border border-warning-subtle">
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
