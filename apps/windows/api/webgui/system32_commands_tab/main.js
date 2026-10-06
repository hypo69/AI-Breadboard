/**
 * =============================================================================
 * Process Name: Windows Web Interface - System32 Commands Tab Main Script
 * =============================================================================
 * Description:
 *   Клиентский контроллер вкладки tab-system32-commands: отображение каталога
 *   штатных средств Windows, слоев Control Plane, AITelemetry Tiers, инвентаря
 *   и интеллектуального пульта подбора и запуска команд по свободному тексту.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/webgui/system32_commands_tab/main.js?v=20261006_v1" type="module"></script>
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: windows/api/webgui/system32_commands_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-06 15:20:00
 * =============================================================================
 */

(function () {
  'use strict';

  let toolsList = [];
  let currentTierFilter = 'all';
  let searchQuery = '';
  let activeSelectedTool = null;
  let isExecuting = false;

  const tierColors = {
    OBSERVE: { bg: 'bg-success-subtle', text: 'text-success', border: 'border-success-subtle', badge: 'bg-success' },
    DIAGNOSE: { bg: 'bg-warning-subtle', text: 'text-warning', border: 'border-warning-subtle', badge: 'bg-warning text-dark' },
    CONTROL: { bg: 'bg-info-subtle', text: 'text-info', border: 'border-info-subtle', badge: 'bg-info text-dark' },
    ADMIN: { bg: 'bg-danger-subtle', text: 'text-danger', border: 'border-danger-subtle', badge: 'bg-danger' },
    DESTRUCTIVE: { bg: 'bg-dark-subtle', text: 'text-light', border: 'border-dark', badge: 'bg-dark text-danger fw-bold' },
    RECOVERY: { bg: 'bg-primary-subtle', text: 'text-primary', border: 'border-primary-subtle', badge: 'bg-primary' },
  };

  const planeIcons = {
    CLI: '💻',
    POWERSHELL: '⚡',
    WMI_CIM: '🧩',
    COM: '🔌',
    WIN32_API: '⚙️',
    NATIVE_NT_API: '🔬',
    ETW: '⏱️',
    EVENT_LOG: '📜',
    REGISTRY: '🗝️',
    GUI_MMC_CPL: '🖥️',
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

  // Load summary metrics and full catalog from backend
  async function loadCatalog() {
    const container = document.getElementById('system32-cards-container');
    if (!container) return;

    try {
      const [catRes, sumRes] = await Promise.all([
        fetch('/api/v1/system32/catalog'),
        fetch('/api/v1/system32/summary')
      ]);

      if (!catRes.ok) throw new Error(`HTTP ${catRes.status}`);
      const catData = await catRes.json();
      toolsList = catData.tools || [];

      if (sumRes.ok) {
        const sumData = await sumRes.json();
        updateSummaryMetrics(sumData);
      }

      renderToolsGrid();
    } catch (err) {
      console.error('[System32CommandsTab] Error loading catalog:', err);
      if (container) {
        container.innerHTML = `
          <div class="col-12 text-center py-4 text-danger">
            <i class="bi bi-exclamation-triangle fs-3 mb-2"></i>
            <div>Не удалось загрузить каталог System32: ${escapeHtml(err.message)}</div>
            <button class="btn btn-outline-primary btn-sm mt-2" onclick="location.reload()">Повторить</button>
          </div>
        `;
      }
    }
  }

  function updateSummaryMetrics(sum) {
    const elTotal = document.getElementById('stat-total-tools');
    const elCats = document.getElementById('stat-total-categories');
    const elObs = document.getElementById('stat-observe-tools');
    const elEtw = document.getElementById('stat-etw-tools');
    const elUsn = document.getElementById('stat-usn-tools');
    const elGui = document.getElementById('stat-gui-tools');

    if (elTotal) elTotal.innerText = sum.total_tools || toolsList.length;
    if (elCats) elCats.innerText = sum.categories_count || '66';
    if (elObs) elObs.innerText = sum.by_telemetry_tier?.OBSERVE || sum.read_tools_count || '0';
    if (elEtw) elEtw.innerText = sum.etw_tools_count || '0';
    if (elUsn) elUsn.innerText = sum.usn_journal_tools_count || '1';
    if (elGui) elGui.innerText = (sum.gui_tools_count || 0) + (sum.msc_consoles_count || 0);
  }

  function getFilteredTools() {
    let list = [...toolsList];
    if (currentTierFilter !== 'all') {
      list = list.filter(t => t.telemetry_tier === currentTierFilter);
    }
    if (searchQuery) {
      const q = searchQuery.toLowerCase().trim();
      list = list.filter(t =>
        t.executable.toLowerCase().includes(q) ||
        t.purpose.toLowerCase().includes(q) ||
        t.category_code.toLowerCase().includes(q) ||
        (t.tags && t.tags.some(tag => tag.toLowerCase().includes(q)))
      );
    }
    return list;
  }

  function renderToolsGrid() {
    const container = document.getElementById('system32-cards-container');
    if (!container) return;

    const filtered = getFilteredTools();

    if (filtered.length === 0) {
      container.innerHTML = `
        <div class="col-12 text-center py-5 text-muted">
          <i class="bi bi-search fs-2 mb-2"></i>
          <div>Инструменты не найдены по заданному фильтру</div>
        </div>
      `;
      return;
    }

    container.innerHTML = filtered.map((tool, idx) => {
      const tierStyle = tierColors[tool.telemetry_tier] || { badge: 'bg-secondary' };
      const planeIcon = planeIcons[tool.primary_control_plane] || '💻';
      const firstTemplate = tool.command_templates && tool.command_templates.length > 0 ? tool.command_templates[0] : tool.executable;

      return `
        <div class="col-12 col-md-6 col-lg-4 col-xl-3">
          <div class="card h-100 border-secondary-subtle shadow-sm hover-shadow transition">
            <div class="card-header bg-transparent border-secondary-subtle py-2 px-3 d-flex align-items-center justify-content-between">
              <div class="d-flex align-items-center gap-1.5 overflow-hidden text-truncate">
                <span class="fs-5">${planeIcon}</span>
                <span class="fw-bold font-monospace text-truncate text-primary" title="${escapeHtml(tool.executable)}">${escapeHtml(tool.executable)}</span>
              </div>
              <span class="badge ${tierStyle.badge} small" style="font-size: 0.68rem;">${escapeHtml(tool.telemetry_tier)}</span>
            </div>
            <div class="card-body p-2 d-flex flex-column justify-content-between">
              <div>
                <div class="text-muted small mb-1 text-truncate" style="font-size: 0.72rem;" title="${escapeHtml(tool.category_code)}">
                  📂 ${escapeHtml(tool.category_code)}
                </div>
                <p class="card-text small text-body mb-2" style="font-size: 0.78rem; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;" title="${escapeHtml(tool.purpose)}">
                  ${escapeHtml(tool.purpose)}
                </p>
              </div>
              <div class="pt-2 border-top border-secondary-subtle d-flex align-items-center justify-content-between gap-1">
                <button class="btn btn-outline-info btn-sm py-0.5 px-2 btn-open-tool-details" data-idx="${idx}" style="font-size: 0.75rem;" title="Посмотреть эквиваленты и руководство">
                  📖 Инструкция
                </button>
                <button class="btn btn-outline-primary btn-sm py-0.5 px-2 btn-paste-cmd" data-cmd="${escapeHtml(firstTemplate)}" style="font-size: 0.75rem;" title="Вставить шаблон в пульт">
                  ⚡ В пульт
                </button>
              </div>
            </div>
          </div>
        </div>
      `;
    }).join('');

    // Attach click events
    container.querySelectorAll('.btn-open-tool-details').forEach(btn => {
      btn.onclick = () => {
        const idx = parseInt(btn.getAttribute('data-idx'), 10);
        if (!isNaN(idx) && filtered[idx]) {
          showToolDetailsModal(filtered[idx]);
        }
      };
    });

    container.querySelectorAll('.btn-paste-cmd').forEach(btn => {
      btn.onclick = () => {
        const cmd = btn.getAttribute('data-cmd');
        const input = document.getElementById('system32-cmd-input');
        if (input && cmd) {
          input.value = cmd;
          input.focus();
        }
      };
    });
  }

  function showToolDetailsModal(tool) {
    activeSelectedTool = tool;
    const modalTitle = document.getElementById('modal-tool-title');
    const modalIcon = document.getElementById('modal-tool-icon');
    const modalBody = document.getElementById('modal-tool-body');

    if (modalTitle) modalTitle.innerText = `${tool.executable} (${tool.category_code})`;
    if (modalIcon) modalIcon.innerText = planeIcons[tool.primary_control_plane] || '🛠️';

    let subcommandsHtml = '';
    if (tool.subcommands_info && Object.keys(tool.subcommands_info).length > 0) {
      subcommandsHtml = `
        <h6 class="fw-bold mt-3 mb-2">⚡ Подкоманды и контексты:</h6>
        <div class="list-group list-group-flush border rounded small">
          ${Object.entries(tool.subcommands_info).map(([sub, desc]) => `
            <div class="list-group-item py-1.5 px-2 d-flex justify-content-between align-items-center">
              <code class="text-primary font-monospace">${escapeHtml(sub)}</code>
              <span class="text-muted">${escapeHtml(desc)}</span>
            </div>
          `).join('')}
        </div>
      `;
    }

    let templatesHtml = '';
    if (tool.command_templates && tool.command_templates.length > 0) {
      templatesHtml = `
        <h6 class="fw-bold mt-3 mb-2">💻 Шаблоны команд:</h6>
        <div class="d-flex flex-column gap-1">
          ${tool.command_templates.map(tmpl => `
            <div class="d-flex align-items-center justify-content-between p-2 bg-body-secondary rounded font-monospace small">
              <code class="text-warning">${escapeHtml(tmpl)}</code>
              <button class="btn btn-sm btn-outline-secondary py-0 px-1.5 btn-copy-inline" data-clip="${escapeHtml(tmpl)}" title="Копировать">
                <i class="bi bi-clipboard"></i>
              </button>
            </div>
          `).join('')}
        </div>
      `;
    }

    if (modalBody) {
      modalBody.innerHTML = `
        <div class="mb-3">
          <div class="text-muted small mb-1">Назначение:</div>
          <div class="p-2 bg-body-tertiary rounded small fw-medium">${escapeHtml(tool.purpose)}</div>
        </div>

        <div class="row g-2 mb-3">
          <div class="col-6 col-md-3">
            <div class="p-2 bg-body-tertiary rounded text-center small">
              <span class="text-muted d-block" style="font-size: 0.7rem;">Tier:</span>
              <span class="badge ${tierColors[tool.telemetry_tier]?.badge || 'bg-secondary'}">${escapeHtml(tool.telemetry_tier)}</span>
            </div>
          </div>
          <div class="col-6 col-md-3">
            <div class="p-2 bg-body-tertiary rounded text-center small">
              <span class="text-muted d-block" style="font-size: 0.7rem;">Опасность:</span>
              <span class="fw-bold ${tool.danger_level === 'CRITICAL' ? 'text-danger' : 'text-body'}">${escapeHtml(tool.danger_level)}</span>
            </div>
          </div>
          <div class="col-6 col-md-3">
            <div class="p-2 bg-body-tertiary rounded text-center small">
              <span class="text-muted d-block" style="font-size: 0.7rem;">Привилегии:</span>
              <span class="fw-semibold">${escapeHtml(tool.required_privileges)}</span>
            </div>
          </div>
          <div class="col-6 col-md-3">
            <div class="p-2 bg-body-tertiary rounded text-center small">
              <span class="text-muted d-block" style="font-size: 0.7rem;">Control Plane:</span>
              <span class="badge bg-secondary">${escapeHtml(tool.primary_control_plane)}</span>
            </div>
          </div>
        </div>

        <h6 class="fw-bold mb-2">🎛️ Эквиваленты в Control Plane:</h6>
        <div class="table-responsive">
          <table class="table table-sm table-bordered small mb-0">
            <tbody>
              <tr>
                <th style="width: 25%;">PowerShell</th>
                <td><code>${escapeHtml(tool.powershell_equivalent || '—')}</code></td>
              </tr>
              <tr>
                <th>Win32 API</th>
                <td><code>${escapeHtml(tool.native_api_equivalent || '—')}</code></td>
              </tr>
              <tr>
                <th>WMI / CIM</th>
                <td><code>${escapeHtml(tool.wmi_cim_equivalent || '—')}</code></td>
              </tr>
              <tr>
                <th>COM</th>
                <td><code>${escapeHtml(tool.com_equivalent || '—')}</code></td>
              </tr>
              ${tool.etw_pipeline_enabled ? '<tr><th>ETW Pipeline</th><td><span class="badge bg-success">Интегрирован в AITelemetry</span></td></tr>' : ''}
              ${tool.usn_journal_enabled ? '<tr><th>USN Journal</th><td><span class="badge bg-info">Поддержка прямого чтения NTFS USN</span></td></tr>' : ''}
            </tbody>
          </table>
        </div>

        ${subcommandsHtml}
        ${templatesHtml}
      `;

      // Copy buttons in modal
      modalBody.querySelectorAll('.btn-copy-inline').forEach(btn => {
        btn.onclick = () => {
          const txt = btn.getAttribute('data-clip');
          if (txt) navigator.clipboard.writeText(txt);
        };
      });
    }

    const modalEl = document.getElementById('toolDetailsModal');
    if (modalEl && typeof bootstrap !== 'undefined' && bootstrap.Modal) {
      const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
      modal.show();
    }
  }

  // Load and display host inventory
  async function loadHostInventory() {
    const body = document.getElementById('modal-inventory-body');
    if (!body) return;

    try {
      const res = await fetch('/api/v1/system32/inventory');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      body.innerHTML = `
        <div class="d-flex align-items-center justify-content-between mb-3 p-2 bg-body-tertiary rounded small">
          <div>📁 Каталог: <code>${escapeHtml(data.system32_path)}</code></div>
          <div>✅ Найдено: <strong>${data.total_installed}</strong> / <strong>${data.total_registered}</strong></div>
        </div>
        <div class="table-responsive" style="max-height: 400px; overflow-y: auto;">
          <table class="table table-sm table-hover table-striped small">
            <thead>
              <tr>
                <th>Инструмент</th>
                <th>Категория</th>
                <th>Статус</th>
                <th>Путь / Источник</th>
              </tr>
            </thead>
            <tbody>
              ${data.installed.map(item => `
                <tr>
                  <td class="font-monospace fw-bold text-success">${escapeHtml(item.executable)}</td>
                  <td class="text-muted">${escapeHtml(item.category_code || item.category)}</td>
                  <td><span class="badge bg-success-subtle text-success border border-success-subtle">Доступен</span></td>
                  <td class="font-monospace text-muted" style="font-size: 0.72rem;">${escapeHtml(item.path)}</td>
                </tr>
              `).join('')}
              ${data.missing.map(item => `
                <tr class="table-warning">
                  <td class="font-monospace text-muted">${escapeHtml(item.executable)}</td>
                  <td class="text-muted">${escapeHtml(item.category_code || item.category)}</td>
                  <td><span class="badge bg-secondary-subtle text-secondary">Не найден</span></td>
                  <td class="text-muted" style="font-size: 0.72rem;">${escapeHtml(item.source)}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `;
    } catch (err) {
      body.innerHTML = `<div class="text-danger p-3 text-center">Ошибка инвентаризации: ${escapeHtml(err.message)}</div>`;
    }
  }

  // Setup Bottom AI Command Input Bar & Execution
  function setupAiCommandRunner() {
    const form = document.getElementById('system32-ai-cmd-form');
    const input = document.getElementById('system32-cmd-input');
    const sendBtn = document.getElementById('btn-system32-cmd-send');
    const statusInd = document.getElementById('ai-cmd-status-indicator');
    const resultBox = document.getElementById('ai-command-result-box');
    const dryRunCheck = document.getElementById('check-cmd-dry-run');
    const confirmAdminCheck = document.getElementById('check-cmd-confirm-admin');

    const resToolName = document.getElementById('res-tool-name');
    const resTierBadge = document.getElementById('res-tier-badge');
    const resDangerBadge = document.getElementById('res-danger-badge');
    const resDuration = document.getElementById('res-duration-badge');
    const resCmdLine = document.getElementById('res-cmd-line');
    const resExplanation = document.getElementById('res-explanation');
    const resPsEquiv = document.getElementById('res-ps-equiv');
    const resWin32Equiv = document.getElementById('res-win32-equiv');
    const resOutput = document.getElementById('res-output-pre');
    const btnCopyOutput = document.getElementById('btn-copy-command-output');
    const btnCloseBox = document.getElementById('btn-close-result-box');

    if (btnCloseBox && resultBox) {
      btnCloseBox.onclick = () => { resultBox.style.display = 'none'; };
    }

    if (btnCopyOutput && resOutput) {
      btnCopyOutput.onclick = () => {
        navigator.clipboard.writeText(resOutput.innerText);
        btnCopyOutput.innerHTML = '<i class="bi bi-check2 me-1"></i>Скопировано';
        setTimeout(() => {
          btnCopyOutput.innerHTML = '<i class="bi bi-clipboard me-1"></i>Копировать';
        }, 1800);
      };
    }

    // Modal paste command button
    const btnModalPaste = document.getElementById('btn-modal-paste-command');
    if (btnModalPaste && input) {
      btnModalPaste.onclick = () => {
        if (activeSelectedTool) {
          const tmpl = activeSelectedTool.command_templates?.[0] || activeSelectedTool.executable;
          input.value = tmpl;
          input.focus();
          const modalEl = document.getElementById('toolDetailsModal');
          if (modalEl && typeof bootstrap !== 'undefined' && bootstrap.Modal) {
            bootstrap.Modal.getInstance(modalEl)?.hide();
          }
        }
      };
    }

    // Quick command pills
    document.querySelectorAll('.quick-cmd-pill').forEach(btn => {
      btn.onclick = () => {
        if (isExecuting) return;
        const prompt = btn.getAttribute('data-prompt');
        if (prompt && input) {
          input.value = prompt;
          executePrompt(prompt);
        }
      };
    });

    if (form && input) {
      form.onsubmit = (e) => {
        e.preventDefault();
        const prompt = input.value.trim();
        if (prompt) executePrompt(prompt);
      };
    }

    async function executePrompt(promptText) {
      if (isExecuting) return;
      isExecuting = true;

      input.disabled = true;
      if (sendBtn) sendBtn.disabled = true;
      if (statusInd) statusInd.innerText = '🧠 Подбор инструмента и формирование команды...';

      if (resultBox) {
        resultBox.style.display = '';
        resultBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
      if (resToolName) resToolName.innerText = 'Анализ намерения...';
      if (resCmdLine) resCmdLine.innerText = '...';
      if (resExplanation) resExplanation.innerText = 'Подбор штатной утилиты System32...';
      if (resOutput) {
        resOutput.className = 'p-2 bg-black rounded text-info small mb-0 font-monospace';
        resOutput.innerText = 'Выполнение системной команды... Пожалуйста, подождите.';
      }

      const isDryRun = dryRunCheck ? dryRunCheck.checked : false;
      const confirmAdmin = confirmAdminCheck ? confirmAdminCheck.checked : true;

      try {
        const response = await fetch('/api/v1/system32/interpret-and-run', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            prompt: promptText,
            execute: !isDryRun,
            confirmed_by_user: !confirmAdmin,
          }),
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();

        if (resToolName) resToolName.innerText = data.matched_executable;
        if (resTierBadge) {
          resTierBadge.className = `badge ${tierColors[data.telemetry_tier]?.badge || 'bg-secondary'} ms-2`;
          resTierBadge.innerText = data.telemetry_tier;
        }
        if (resDangerBadge) {
          if (data.danger_level === 'HIGH' || data.danger_level === 'CRITICAL') {
            resDangerBadge.style.display = '';
            resDangerBadge.innerText = data.danger_level;
          } else {
            resDangerBadge.style.display = 'none';
          }
        }
        if (resDuration) resDuration.innerText = `${data.execution_time_ms} ms`;
        if (resCmdLine) resCmdLine.innerText = data.command_line;
        if (resExplanation) resExplanation.innerText = data.explanation;
        if (resPsEquiv) resPsEquiv.innerHTML = data.powershell_equivalent ? `⚡ PowerShell: <code>${escapeHtml(data.powershell_equivalent)}</code>` : '';
        if (resWin32Equiv) resWin32Equiv.innerHTML = data.win32_api_equivalent ? `⚙️ Win32 API: <code>${escapeHtml(data.win32_api_equivalent)}</code>` : '';

        if (resOutput) {
          if (data.status === 'success') {
            resOutput.className = 'p-2 bg-black rounded text-success small mb-0 font-monospace';
          } else if (data.status === 'warn' || data.status === 'requires_confirmation') {
            resOutput.className = 'p-2 bg-black rounded text-warning small mb-0 font-monospace';
          } else {
            resOutput.className = 'p-2 bg-black rounded text-danger small mb-0 font-monospace';
          }
          resOutput.innerText = data.execution_output || 'Команда выполнена успешно.';
        }

        if (statusInd) statusInd.innerText = `Готово: ${data.matched_executable} (${data.status})`;
      } catch (err) {
        console.error('[System32CommandsTab] Execution error:', err);
        if (resOutput) {
          resOutput.className = 'p-2 bg-black rounded text-danger small mb-0 font-monospace';
          resOutput.innerText = `Сбой запроса: ${err.message}`;
        }
        if (statusInd) statusInd.innerText = 'Ошибка выполнения';
      } finally {
        isExecuting = false;
        input.disabled = false;
        if (sendBtn) sendBtn.disabled = false;
        input.focus();
      }
    }
  }

  // Setup toolbar filters & search
  function setupFilters() {
    const tierGroup = document.getElementById('tier-filters');
    if (tierGroup) {
      tierGroup.querySelectorAll('button').forEach(btn => {
        btn.onclick = () => {
          tierGroup.querySelectorAll('button').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          currentTierFilter = btn.getAttribute('data-tier') || 'all';
          renderToolsGrid();
        };
      });
    }

    const searchInput = document.getElementById('tool-search-input');
    const clearBtn = document.getElementById('btn-clear-search');
    if (searchInput) {
      searchInput.oninput = () => {
        searchQuery = searchInput.value;
        renderToolsGrid();
      };
    }
    if (clearBtn && searchInput) {
      clearBtn.onclick = () => {
        searchInput.value = '';
        searchQuery = '';
        renderToolsGrid();
      };
    }

    const refreshBtn = document.getElementById('btn-refresh-system32-catalog');
    if (refreshBtn) {
      refreshBtn.onclick = () => { loadCatalog(); };
    }

    const invBtn = document.getElementById('btn-open-inventory-modal');
    if (invBtn) {
      invBtn.onclick = () => { loadHostInventory(); };
    }
  }

  // Module initialization
  function init() {
    setupFilters();
    setupAiCommandRunner();
    loadCatalog();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
