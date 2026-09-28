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
      const engBadge = document.getElementById('def-engine-ver-badgei18n.t('auto__if_engbadge_engbadge_textcontent_status_engine_version__bd9264')N/A'}`;
      const sigsBadge = document.getElementById('def-sigs-ver-badgei18n.t('auto__if_sigsbadge_sigsbadge_textcontent_status_antivirus_signature_version__4c1d67')N/A'}`;

      // Stat Cards
      const rtVal = document.getElementById('def-realtime-val');
      if (rtVal) {
        rtVal.textContent = status.real_time_protection_enabled ? i18n.t('auto___593689') : i18n.t('auto___919af8');
        rtVal.className = `def-card-value ${status.real_time_protection_enabled ? 'text-success' : 'text-danger'}`;
      }

      const cloudVal = document.getElementById('def-cloud-val');
      if (cloudVal) {
        cloudVal.textContent = status.cloud_protection_enabled ? i18n.t('auto___f12754') : i18n.t('auto___919af8');
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
          { name: 'Real-time Protection', enabled: status.real_time_protection_enabled, desc: i18n.t('auto___756338') },
          { name: 'Cloud Protection (MAPS)i18n.t('auto__enabled_status_cloud_protection_enabled_desc_microsoft_status_cloud_block_level_name__c76066')Behavior Monitoring', enabled: status.behavior_monitor_enabled, desc: i18n.t('auto___286e6a') },
          { name: 'IOAV Protection', enabled: status.ioav_protection_enabled, desc: i18n.t('auto___81d54e') },
          { name: 'AMSI Script Scanning', enabled: status.script_scanning_enabled, desc: i18n.t('auto__powershell_vbscript_javascript__530ecd') },
          { name: 'Tamper Protection', enabled: status.tamper_protection_enabled, desc: i18n.t('auto___2d1444') },
          { name: 'PUA Protection', enabled: status.pua_protection_enabled, desc: i18n.t('auto___35d0c6') },
          { name: 'Controlled Folder Access', enabled: status.controlled_folder_access_enabled, desc: i18n.t('auto__ransomware_56de3b') },
          { name: 'Network Protection', enabled: status.network_protection_enabled, desc: i18n.t('auto__ip_78dc54') },
        ];

        shieldsTbody.innerHTML = shields.map(s => `
          <tr>
            <td class="fw-semibold text-light">${s.name}</td>
            <td class="text-center">
              <span class="badge ${s.enabled ? 'def-badge-active' : 'def-badge-disabled'}">
                ${s.enabled ? i18n.t('auto___b9e023') : i18n.t('auto___90f449')}
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
                ${svc.running ? i18n.t('auto___d1ccf9') : i18n.t('auto___bf1365')}
              </span>
            </td>
            <td class="text-end text-secondary">${svc.pid || '-'}</td>
            <td class="text-end font-monospace">${svc.running ? svc.memory_mb + ' MB' : '-'}</td>
          </tr>
        `).join('');
      }

    } catch (err) {
      console.error('[DefenderTab] Error loading status:i18n.t('auto__err_showalert_defender_err_message_true_async_function_loadasrrules_try_const_rules_await_fetchjson__6e36c3')/api/v1/defender/asr');
      const tbody = document.getElementById('def-asr-tbody');
      const badge = document.getElementById('def-asr-count-badgei18n.t('auto__if_badge_badge_textcontent_rules_length_if_tbody_tbody_innerhtml_rules_map_r_let_statebadge__4364d0')<span class="badge bg-secondary">Не задано</span>';
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
      const tbody = document.getElementById('def-exclusions-tbodyi18n.t('auto__if_countval_countval_textcontent_rep_total_exclusions_if_countsub_countsub_textcontent_rep_suspicious_count_if_summarybadge_summarybadge_textcontent_rep_total_exclusions_rep_suspicious_count_if_recbox_recbox_textcontent_rep_summary_recommendation_const_allitems_rep_path_exclusions_rep_extension_exclusions_rep_process_exclusions_if_tbody_if_allitems_length_0_tbody_innerhtml__a9ca03')<tr><td colspan="4" class="text-center text-muted py-3">Исключения отсутствуют. Защита работает без пропусков.</td></tr>';
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
      const tbody = document.getElementById('def-threats-tbodyi18n.t('auto__if_countbadge_countbadge_textcontent_threats_length_if_countval_countval_textcontent_threats_length_const_quarantined_threats_filter_t_t_status_tolowercase_includes__87b411')quarantinei18n.t('auto__length_if_countsub_countsub_textcontent_quarantined_if_tbody_if_threats_length_0_tbody_innerhtml__33adba')<tr><td colspan="6" class="text-center text-muted py-3">Активных и архивных угроз не зафиксировано.</td></tr>';
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
      const tbody = document.getElementById('def-procs-tbodyi18n.t('auto__if_badge_badge_textcontent_chains_length_if_tbody_if_chains_length_0_tbody_innerhtml__a9a2a6')<tr><td colspan="5" class="text-center text-muted py-3">Подозрительных связей процессов и fileless индикаторов не обнаружено.</td></tr>';
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
      const tbody = document.getElementById('def-events-tbodyi18n.t('auto__if_badge_badge_textcontent_events_length_if_tbody_if_events_length_0_tbody_innerhtml__2086ac')<tr><td colspan="5" class="text-center text-muted py-3">Событий в журнале Defender Operational не обнаружено.</td></tr>';
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
          showAlert(i18n.t('auto__defender__caeced'));
          const res = await fetchJSON('/api/v1/defender/scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ scan_type: 'quicki18n.t('auto__showalert_res_message_await_loaddefenderstatus_catch_err_showalert_err_message_true_const_btnfull_document_getelementbyid__13022e')btn-def-full-scan');
    if (btnFull) {
      btnFull.onclick = async () => {
        try {
          showAlert(i18n.t('auto__defender__c6f3f8'));
          const res = await fetchJSON('/api/v1/defender/scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ scan_type: 'fulli18n.t('auto__showalert_res_message_catch_err_showalert_err_message_true_const_btnupdate_document_getelementbyid__14d775')btn-def-update-sigs');
    if (btnUpdate) {
      btnUpdate.onclick = async () => {
        try {
          showAlert(i18n.t('auto__defender__c56ee9'));
          const res = await fetchJSON('/api/v1/defender/update-signatures', { method: 'POSTi18n.t('auto__showalert_res_message_await_loaddefenderstatus_catch_err_showalert_err_message_true_const_btnrefresh_document_getelementbyid__6be809')btn-def-refresh');
    if (btnRefresh) {
      btnRefresh.onclick = async () => {
        showAlert(i18n.t('auto__defender__4caf38'));
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
