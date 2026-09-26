// Microsoft Defender Security Center Frontend Controller
(function() {
  'use strict';

  let defenderData = null;

  function showAlert(msg, isError = false) {
    const box = document.getElementById('def-alert-box');
    if (!box) return;
    box.className = `alert py-2 px-3 mb-2 small ${isError ? 'alert-danger' : 'alert-info'}`;
    box.textContent = msg;
    box.classList.remove('d-none');
    setTimeout(() => {
      box.classList.add('d-none');
    }, 8000);
  }

  async function fetchJSON(url, options = {}) {
    if (window.api && typeof window.api.fetch === 'function') {
      return await window.api.fetch(url, options);
    }
    const res = await fetch(url, options);
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    return await res.json();
  }

  async function loadDefenderStatus() {
    try {
      const status = await fetchJSON('/api/v1/defender/status');
      defenderData = status;

      // Badges in header
      const engBadge = document.getElementById('def-engine-ver-badge');
      if (engBadge) engBadge.textContent = `Движок: ${status.engine_version || 'N/A'}`;
      const sigsBadge = document.getElementById('def-sigs-ver-badge');
      if (sigsBadge) sigsBadge.textContent = `Базы: ${status.antivirus_signature_version || 'N/A'}`;

      // Stat Cards
      const rtVal = document.getElementById('def-realtime-val');
      if (rtVal) {
        rtVal.textContent = status.real_time_protection_enabled ? 'ВКЛ' : 'ВЫКЛ';
        rtVal.className = `def-card-value ${status.real_time_protection_enabled ? 'text-success' : 'text-danger'}`;
      }

      const cloudVal = document.getElementById('def-cloud-val');
      if (cloudVal) {
        cloudVal.textContent = status.cloud_protection_enabled ? 'АКТИВНА' : 'ВЫКЛ';
        cloudVal.className = `def-card-value ${status.cloud_protection_enabled ? 'text-success' : 'text-warning'}`;
      }

      const puaCfaVal = document.getElementById('def-pua-cfa-val');
      if (puaCfaVal) {
        const puaText = status.pua_protection_enabled ? 'PUA: ✓' : 'PUA: ✗';
        const cfaText = status.controlled_folder_access_enabled ? 'CFA: ✓' : 'CFA: ✗';
        puaCfaVal.textContent = `${puaText} | ${cfaText}`;
        puaCfaVal.className = 'def-card-value small text-info';
      }

      // Shields Table
      const shieldsTbody = document.getElementById('def-shields-tbody');
      if (shieldsTbody) {
        const shields = [
          { name: 'Real-time Protection', enabled: status.real_time_protection_enabled, desc: 'Постоянный перехват и проверка файлов при создании и обращении' },
          { name: 'Cloud Protection (MAPS)', enabled: status.cloud_protection_enabled, desc: `Мгновенная блокировка новых угроз через облачный ИИ Microsoft (${status.cloud_block_level})` },
          { name: 'Behavior Monitoring', enabled: status.behavior_monitor_enabled, desc: 'Анализ поведения запущенных процессов и цепочек активности' },
          { name: 'IOAV Protection', enabled: status.ioav_protection_enabled, desc: 'Проверка файлов, загружаемых из браузера, почты и мессенджеров' },
          { name: 'AMSI Script Scanning', enabled: status.script_scanning_enabled, desc: 'Инспекция скриптов PowerShell, VBScript, JavaScript до их выполнения' },
          { name: 'Tamper Protection', enabled: status.tamper_protection_enabled, desc: 'Защита настроек антивируса от отключения вредоносным ПО' },
          { name: 'PUA Protection', enabled: status.pua_protection_enabled, desc: 'Блокировка нежелательного ПО, рекламных инсталляторов и майнеров' },
          { name: 'Controlled Folder Access', enabled: status.controlled_folder_access_enabled, desc: 'Защита папок Документы/Рабочий стол от шифрования Ransomware' },
          { name: 'Network Protection', enabled: status.network_protection_enabled, desc: 'Блокировка сетевых соединений с вредоносными доменами и IP' },
        ];

        shieldsTbody.innerHTML = shields.map(s => `
          <tr>
            <td class="fw-semibold text-light">${s.name}</td>
            <td class="text-center">
              <span class="badge ${s.enabled ? 'def-badge-active' : 'def-badge-disabled'}">
                ${s.enabled ? 'ВКЛЮЧЕНО' : 'ОТКЛЮЧЕНО'}
              </span>
            </td>
            <td class="def-desc-text">${s.desc}</td>
          </tr>
        `).join('');
      }

      // Services Table
      const servicesTbody = document.getElementById('def-services-tbody');
      if (servicesTbody && status.services) {
        servicesTbody.innerHTML = status.services.map(svc => `
          <tr>
            <td>
              <div class="fw-semibold text-light">${svc.name}</div>
              <div class="def-desc-text" style="font-size: 0.72rem;">${svc.display_name}</div>
            </td>
            <td class="text-center">
              <span class="badge ${svc.running ? 'bg-success' : 'bg-secondary'}">
                ${svc.running ? 'АКТИВЕН' : 'СТОП'}
              </span>
            </td>
            <td class="text-end text-secondary">${svc.pid || '-'}</td>
            <td class="text-end font-monospace">${svc.running ? svc.memory_mb + ' MB' : '-'}</td>
          </tr>
        `).join('');
      }

    } catch (err) {
      console.error('[DefenderTab] Error loading status:', err);
      showAlert(`Ошибка загрузки статуса Defender: ${err.message}`, true);
    }
  }

  async function loadASRRules() {
    try {
      const rules = await fetchJSON('/api/v1/defender/asr');
      const tbody = document.getElementById('def-asr-tbody');
      const badge = document.getElementById('def-asr-count-badge');
      if (badge) badge.textContent = `Всего: ${rules.length}`;

      if (tbody) {
        tbody.innerHTML = rules.map(r => {
          let stateBadge = '<span class="badge bg-secondary">Не задано</span>';
          if (r.state === 'enabled') stateBadge = '<span class="badge def-badge-active">Блокировка (Block)</span>';
          else if (r.state === 'audit') stateBadge = '<span class="badge def-badge-audit">Аудит (Audit)</span>';
          else if (r.state === 'warn') stateBadge = '<span class="badge def-badge-warn">Предупреждение</span>';
          else if (r.state === 'disabled') stateBadge = '<span class="badge def-badge-disabled">Отключено</span>';

          return `
            <tr>
              <td>
                <div class="fw-semibold text-light">${r.name}</div>
                <div class="def-desc-text" style="font-size: 0.72rem;">${r.description}</div>
              </td>
              <td><span class="badge bg-dark border border-secondary">${r.category}</span></td>
              <td class="text-center">${stateBadge}</td>
              <td class="def-desc-text small">${r.recommendation || '-'}</td>
              <td class="text-secondary font-monospace" style="font-size: 0.68rem;">${r.guid}</td>
            </tr>
          `;
        }).join('');
      }
    } catch (err) {
      console.error('[DefenderTab] Error loading ASR rules:', err);
    }
  }

  async function loadCFA() {
    try {
      const cfa = await fetchJSON('/api/v1/defender/cfa');
      const foldersList = document.getElementById('def-cfa-folders-list');
      const appsList = document.getElementById('def-cfa-apps-list');

      if (foldersList) {
        if (cfa.protected_folders && cfa.protected_folders.length > 0) {
          foldersList.innerHTML = `
            <ul class="list-group list-group-flush bg-transparent">
              ${cfa.protected_folders.map(f => `
                <li class="list-group-item bg-transparent text-light border-secondary py-1 px-0 font-monospace small">
                  📁 ${f}
                </li>
              `).join('')}
            </ul>
          `;
        } else {
          foldersList.innerHTML = '<div class="text-muted small">Нет настроенных защищенных папок.</div>';
        }
      }

      if (appsList) {
        if (cfa.allowed_applications && cfa.allowed_applications.length > 0) {
          appsList.innerHTML = `
            <ul class="list-group list-group-flush bg-transparent">
              ${cfa.allowed_applications.map(a => `
                <li class="list-group-item bg-transparent text-light border-secondary py-1 px-0 font-monospace small">
                  🛡️ ${a}
                </li>
              `).join('')}
            </ul>
          `;
        } else {
          appsList.innerHTML = '<div class="text-muted small">Список доверенных приложений пуст.</div>';
        }
      }
    } catch (err) {
      console.error('[DefenderTab] Error loading CFA:', err);
    }
  }

  async function loadExclusions() {
    try {
      const rep = await fetchJSON('/api/v1/defender/exclusions');
      
      const countVal = document.getElementById('def-exclusions-val');
      const countSub = document.getElementById('def-exclusions-sub');
      const summaryBadge = document.getElementById('def-exc-summary-badge');
      const recBox = document.getElementById('def-exc-recommendation-box');
      const tbody = document.getElementById('def-exclusions-tbody');

      if (countVal) countVal.textContent = rep.total_exclusions;
      if (countSub) countSub.textContent = `${rep.suspicious_count} подозрительных`;
      if (summaryBadge) summaryBadge.textContent = `${rep.total_exclusions} исключений (${rep.suspicious_count} риск)`;
      if (recBox) recBox.textContent = rep.summary_recommendation;

      const allItems = [...rep.path_exclusions, ...rep.extension_exclusions, ...rep.process_exclusions];

      if (tbody) {
        if (allItems.length === 0) {
          tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted py-3">Исключения отсутствуют. Защита работает без пропусков.</td></tr>';
        } else {
          tbody.innerHTML = allItems.map(itm => {
            let riskBadge = '<span class="badge bg-success">Безопасно</span>';
            if (itm.risk_level === 'critical') riskBadge = '<span class="badge def-badge-critical">КРИТИЧЕСКИЙ</span>';
            else if (itm.risk_level === 'high') riskBadge = '<span class="badge def-badge-disabled">ВЫСОКИЙ</span>';
            else if (itm.risk_level === 'medium') riskBadge = '<span class="badge def-badge-warn">СРЕДНИЙ</span>';

            return `
              <tr>
                <td><span class="badge bg-dark border border-secondary">${itm.type.toUpperCase()}</span></td>
                <td class="font-monospace text-light">${itm.value}</td>
                <td class="text-center">${riskBadge}</td>
                <td class="text-secondary small">${itm.risk_reason}</td>
              </tr>
            `;
          }).join('');
        }
      }
    } catch (err) {
      console.error('[DefenderTab] Error loading exclusions:', err);
    }
  }

  async function loadThreats() {
    try {
      const threats = await fetchJSON('/api/v1/defender/threats?limit=50');
      const countBadge = document.getElementById('def-threats-count-badge');
      const countVal = document.getElementById('def-threats-val');
      const countSub = document.getElementById('def-threats-sub');
      const tbody = document.getElementById('def-threats-tbody');

      if (countBadge) countBadge.textContent = `${threats.length} записей`;
      if (countVal) countVal.textContent = threats.length;
      
      const quarantined = threats.filter(t => t.status.toLowerCase().includes('quarantine')).length;
      if (countSub) countSub.textContent = `Карантин: ${quarantined}`;

      if (tbody) {
        if (threats.length === 0) {
          tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-3">Активных и архивных угроз не зафиксировано.</td></tr>';
        } else {
          tbody.innerHTML = threats.map(t => `
            <tr>
              <td class="fw-semibold text-danger">${t.threat_name}</td>
              <td><span class="badge bg-dark border border-secondary">${t.category}</span></td>
              <td class="text-center"><span class="badge bg-warning text-dark">${t.severity.toUpperCase()}</span></td>
              <td><span class="badge bg-success">${t.status}</span></td>
              <td class="text-secondary small">${t.last_detection_time || t.initial_detection_time || '-'}</td>
              <td class="text-secondary font-monospace small">${(t.resources || []).join(', ')}</td>
            </tr>
          `).join('');
        }
      }
    } catch (err) {
      console.error('[DefenderTab] Error loading threats:', err);
    }
  }

  async function loadProcesses() {
    try {
      const chains = await fetchJSON('/api/v1/defender/process-tree');
      const badge = document.getElementById('def-procs-count-badge');
      const tbody = document.getElementById('def-procs-tbody');

      if (badge) badge.textContent = `${chains.length} аномалий`;

      if (tbody) {
        if (chains.length === 0) {
          tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-3">Подозрительных связей процессов и fileless индикаторов не обнаружено.</td></tr>';
        } else {
          tbody.innerHTML = chains.map(c => `
            <tr>
              <td class="font-monospace text-warning">${c.parent_process} (PID: ${c.parent_pid || '-'})</td>
              <td class="font-monospace text-danger fw-semibold">${c.child_process}</td>
              <td class="text-center text-secondary">${c.child_pid || '-'}</td>
              <td class="text-center"><span class="badge def-badge-critical">${c.severity.toUpperCase()}</span></td>
              <td class="text-secondary small">
                <div>${c.reason}</div>
                ${c.command_line ? `<div class="font-monospace text-muted mt-1" style="font-size: 0.68rem;">cmd: ${c.command_line}</div>` : ''}
              </td>
            </tr>
          `).join('');
        }
      }
    } catch (err) {
      console.error('[DefenderTab] Error loading process chains:', err);
    }
  }

  async function loadEvents() {
    try {
      const events = await fetchJSON('/api/v1/defender/events?limit=50');
      const badge = document.getElementById('def-events-count-badge');
      const tbody = document.getElementById('def-events-tbody');

      if (badge) badge.textContent = `${events.length} событий`;

      if (tbody) {
        if (events.length === 0) {
          tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-3">Событий в журнале Defender Operational не обнаружено.</td></tr>';
        } else {
          tbody.innerHTML = events.map(e => `
            <tr>
              <td class="font-monospace fw-semibold text-info">${e.event_id}</td>
              <td class="text-secondary small font-monospace">${e.timestamp}</td>
              <td><span class="badge ${e.level.toLowerCase().includes('err') || e.level.toLowerCase().includes('crit') ? 'bg-danger' : (e.level.toLowerCase().includes('warn') ? 'bg-warning text-dark' : 'bg-secondary')}">${e.level}</span></td>
              <td><span class="badge bg-dark border border-secondary">${e.category}</span></td>
              <td class="text-light small">${e.message}</td>
            </tr>
          `).join('');
        }
      }
    } catch (err) {
      console.error('[DefenderTab] Error loading events:', err);
    }
  }

  async function loadDiagnostics() {
    try {
      const rep = await fetchJSON('/api/v1/defender/diagnostics');
      
      const scoreVal = document.getElementById('def-score-val');
      const scoreSub = document.getElementById('def-score-sub');
      const diagScoreDisplay = document.getElementById('def-diag-score-display');
      const diagSummaryDisplay = document.getElementById('def-diag-summary-display');
      const recsContainer = document.getElementById('def-diag-recs-container');
      const critsContainer = document.getElementById('def-diag-criticals-container');

      const scoreColor = rep.security_score >= 80 ? 'text-success' : (rep.security_score >= 50 ? 'text-warning' : 'text-danger');

      if (scoreVal) {
        scoreVal.textContent = `${rep.security_score}/100`;
        scoreVal.className = `def-card-value ${scoreColor}`;
      }
      if (scoreSub) scoreSub.textContent = rep.status_summary;

      if (diagScoreDisplay) {
        diagScoreDisplay.textContent = `${rep.security_score}/100`;
        diagScoreDisplay.className = `display-4 fw-bold ${scoreColor}`;
      }
      if (diagSummaryDisplay) diagSummaryDisplay.textContent = rep.status_summary;

      if (recsContainer) {
        if (rep.recommendations && rep.recommendations.length > 0) {
          recsContainer.innerHTML = `
            <ol class="ps-3 mb-0">
              ${rep.recommendations.map(r => `<li class="py-1 text-light">${r}</li>`).join('')}
            </ol>
          `;
        } else {
          recsContainer.innerHTML = '<div class="text-success">Все рекомендации соблюдены. Защита оптимальна.</div>';
        }
      }

      if (critsContainer) {
        if (rep.critical_findings && rep.critical_findings.length > 0) {
          critsContainer.innerHTML = `
            <ul class="ps-3 mb-0 text-danger">
              ${rep.critical_findings.map(c => `<li class="py-1">${c}</li>`).join('')}
            </ul>
          `;
        } else {
          critsContainer.innerHTML = '<div class="text-muted">Критических уязвимостей не зафиксировано.</div>';
        }
      }

    } catch (err) {
      console.error('[DefenderTab] Error loading diagnostics:', err);
    }
  }

  function setupActions() {
    const btnQuick = document.getElementById('btn-def-quick-scan');
    if (btnQuick) {
      btnQuick.onclick = async () => {
        try {
          showAlert('Запуск быстрого сканирования Defender...');
          const res = await fetchJSON('/api/v1/defender/scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ scan_type: 'quick' }),
          });
          showAlert(`Быстрое сканирование: ${res.message}`);
          await loadDefenderStatus();
        } catch (err) {
          showAlert(`Ошибка запуска сканирования: ${err.message}`, true);
        }
      };
    }

    const btnFull = document.getElementById('btn-def-full-scan');
    if (btnFull) {
      btnFull.onclick = async () => {
        try {
          showAlert('Запуск полного сканирования системы (фоновый процесс Defender)...');
          const res = await fetchJSON('/api/v1/defender/scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ scan_type: 'full' }),
          });
          showAlert(`Полное сканирование: ${res.message}`);
        } catch (err) {
          showAlert(`Ошибка полного сканирования: ${err.message}`, true);
        }
      };
    }

    const btnUpdate = document.getElementById('btn-def-update-sigs');
    if (btnUpdate) {
      btnUpdate.onclick = async () => {
        try {
          showAlert('Обновление баз сигнатур Defender...');
          const res = await fetchJSON('/api/v1/defender/update-signatures', { method: 'POST' });
          showAlert(`Обновление сигнатур: ${res.message}`);
          await loadDefenderStatus();
        } catch (err) {
          showAlert(`Ошибка обновления баз: ${err.message}`, true);
        }
      };
    }

    const btnRefresh = document.getElementById('btn-def-refresh');
    if (btnRefresh) {
      btnRefresh.onclick = async () => {
        showAlert('Обновление данных Defender...');
        await refreshAll();
      };
    }

    const btnAiDiag = document.getElementById('btn-def-ai-diag');
    if (btnAiDiag) {
      btnAiDiag.onclick = () => {
        const diagTabBtn = document.getElementById('def-tab-diag-btn');
        if (diagTabBtn) {
          const tab = new bootstrap.Tab(diagTabBtn);
          tab.show();
        }
      };
    }
  }

  async function refreshAll() {
    await Promise.all([
      loadDefenderStatus(),
      loadASRRules(),
      loadCFA(),
      loadExclusions(),
      loadThreats(),
      loadProcesses(),
      loadEvents(),
      loadDiagnostics(),
    ]);
  }

  window.initDefenderTab = async function() {
    console.log('[DefenderTab] Initializing Defender Security Center Tab...');
    setupActions();
    await refreshAll();
  };

  // Auto initialize if container exists
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      if (document.getElementById('def-shields-tbody')) {
        window.initDefenderTab();
      }
    });
  } else {
    if (document.getElementById('def-shields-tbody')) {
      window.initDefenderTab();
    }
  }

})();
