/**
 * =============================================================================
 * Process Name: Windows Js - Ai Table Modal Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля ai_table_modal.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/webgui/js/ai_table_modal.js?v=20261008_v4" type="module"></script>
 *
 * File: ai_table_modal.js
 * Project: ai-breadboard
 * Package: windows/api/webgui/js
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-08 09:50:00
 * =============================================================================
 */

// Universal AI Table Modal Module for AI-Breadboard
// Enables interactive row inspection and AI contextual explanation across all data tables.

(function () {
  const MODAL_ID = 'universal-ai-table-modal';

  function ensureModalElement() {
    let modalEl = document.getElementById(MODAL_ID);
    if (!modalEl) {
      modalEl = document.createElement('div');
      modalEl.id = MODAL_ID;
      modalEl.className = 'modal fade';
      modalEl.tabIndex = -1;
      modalEl.setAttribute('aria-hidden', 'true');
      modalEl.innerHTML = `
        <div class="modal-dialog modal-lg modal-dialog-centered modal-dialog-scrollable">
          <div class="modal-content bg-dark text-light border-secondary shadow-lg">
            <div class="modal-header border-secondary py-2 px-3">
              <div class="d-flex align-items-center gap-2 flex-wrap">
                <span class="fs-5 text-info" id="uai-modal-icon">🔍</span>
                <h5 class="modal-title fw-bold text-info mb-0" id="uai-modal-title">Детали записи</h5>
                <div id="uai-modal-badges" class="d-flex align-items-center gap-1"></div>
              </div>
              <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body py-3 px-3">
              <!-- Metadata Grid -->
              <div class="row g-2 mb-3 small" id="uai-modal-metadata-grid"></div>

              <!-- Raw / Code Content Section -->
              <div class="card bg-black border-secondary p-3 mb-3" id="uai-modal-raw-container" style="display: none;">
                <div class="d-flex justify-content-between align-items-center mb-1">
                  <h6 class="small text-uppercase text-muted fw-bold mb-0" id="uai-modal-raw-title">Контекст / Данные</h6>
                </div>
                <div class="small font-monospace text-light" id="uai-modal-raw-content" style="white-space: pre-wrap; word-break: break-all;"></div>
              </div>

              <!-- AI Contextual Diagnostic Card -->
              <div class="card border-info bg-dark p-3" id="uai-modal-ai-section">
                <div class="d-flex justify-content-between align-items-center mb-2 flex-wrap gap-2">
                  <div class="d-flex align-items-center gap-2">
                    <h6 class="fw-bold text-info mb-0"><i class="bi bi-robot me-1"></i> AI Contextual Explanation</h6>
                    <span class="badge bg-info-subtle text-info border border-info-subtle small px-2 py-0.5" id="uai-modal-web-status" title="Сведения обогащаются поиском в интернете">
                      <i class="bi bi-globe me-1"></i>Web Grounding
                    </span>
                  </div>
                  <div class="d-flex align-items-center gap-1.5">
                    <button class="btn btn-sm btn-outline-secondary py-0 px-2 rounded-pill" id="btn-uai-modal-edit-prompt" title="Настроить промпт для этого типа таблицы">
                      <i class="bi bi-gear-fill me-1"></i>Промпт
                    </button>
                    <button class="btn btn-sm btn-outline-info py-0 px-2 rounded-pill" id="btn-uai-modal-refresh" title="Обновить AI-анализ" style="display: none;">
                      <i class="bi bi-arrow-clockwise me-1"></i>Обновить
                    </button>
                  </div>
                </div>
                <div class="small" id="uai-modal-ai-explanation"></div>
              </div>
            </div>
            <div class="modal-footer border-secondary py-2 px-3 d-flex justify-content-between">
              <div id="uai-modal-custom-actions" class="d-flex gap-1.5 flex-wrap"></div>
              <button type="button" class="btn btn-sm btn-secondary" data-bs-dismiss="modal">Закрыть</button>
            </div>
          </div>
        </div>
      `;
      document.body.appendChild(modalEl);
    }
    return modalEl;
  }

  function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  /**
   * Universal method to show item inspection modal with AI explanation.
   * @param {Object} options Configuration object
   */
  function show(options) {
    const opts = Object.assign({
      title: 'Детали записи',
      subtitle: '',
      icon: '🔍',
      badges: [],
      metadata: [],
      rawTitle: 'Данные / Путь',
      rawContent: '',
      tableType: 'generic',
      requestData: {},
      autoRun: false,
      actions: []
    }, options);

    const modalEl = ensureModalElement();

    // Icon & Title
    const iconEl = document.getElementById('uai-modal-icon');
    if (iconEl) iconEl.textContent = opts.icon;

    const titleEl = document.getElementById('uai-modal-title');
    if (titleEl) titleEl.textContent = opts.title;

    // Badges
    const badgesContainer = document.getElementById('uai-modal-badges');
    if (badgesContainer) {
      badgesContainer.innerHTML = (opts.badges || []).map(b => {
        const cls = b.class || 'badge bg-secondary';
        return `<span class="${cls}">${escapeHtml(b.text)}</span>`;
      }).join('');
    }

    // Metadata Grid
    const metaContainer = document.getElementById('uai-modal-metadata-grid');
    if (metaContainer) {
      metaContainer.innerHTML = (opts.metadata || []).map(m => {
        const colSize = m.fullWidth ? 'col-sm-12' : 'col-sm-6';
        let valHtml = '';
        if (m.html) {
          valHtml = m.html;
        } else if (m.isCode) {
          valHtml = `<span class="font-monospace text-info small" style="word-break: break-all;">${escapeHtml(m.value || '-')}</span>`;
        } else {
          valHtml = `<span class="text-light">${escapeHtml(m.value || '-')}</span>`;
        }
        return `
          <div class="${colSize}">
            <strong class="text-secondary">${escapeHtml(m.label)}:</strong> ${valHtml}
          </div>
        `;
      }).join('');
    }

    // Raw Content Block
    const rawContainer = document.getElementById('uai-modal-raw-container');
    const rawTitleEl = document.getElementById('uai-modal-raw-title');
    const rawContentEl = document.getElementById('uai-modal-raw-content');
    if (rawContainer && rawTitleEl && rawContentEl) {
      if (opts.rawContent && opts.rawContent.trim()) {
        rawTitleEl.textContent = opts.rawTitle;
        rawContentEl.textContent = opts.rawContent;
        rawContainer.style.display = 'block';
      } else {
        rawContainer.style.display = 'none';
      }
    }

    const refreshBtn = document.getElementById('btn-uai-modal-refresh');
    if (refreshBtn) {
      refreshBtn.style.display = 'none';
      refreshBtn.onclick = () => executeDiagnostics();
    }

    // Reset AI Diagnostic section with on-demand trigger button
    const aiExplanation = document.getElementById('uai-modal-ai-explanation');
    function renderPromptCallout() {
      if (!aiExplanation) return;
      aiExplanation.innerHTML = `
        <div class="d-flex align-items-center justify-content-between flex-wrap gap-2 py-2">
          <div class="text-secondary small">
            <i class="bi bi-info-circle me-1"></i>Нажмите кнопку для отправки запроса к модели ИИ и получения экспертного анализа, оценки рисков и рекомендаций.
          </div>
          <button type="button" class="btn btn-sm btn-primary d-inline-flex align-items-center gap-1.5" id="btn-uai-modal-run-ai">
            <i class="bi bi-robot"></i> Запросить AI-анализ
          </button>
        </div>
      `;
      const runBtn = document.getElementById('btn-uai-modal-run-ai');
      if (runBtn) {
        runBtn.onclick = () => executeDiagnostics();
      }
    }

    renderPromptCallout();

    // Wire up Prompt Editor button
    const editPromptBtn = document.getElementById('btn-uai-modal-edit-prompt');
    if (editPromptBtn) {
      editPromptBtn.onclick = () => openPromptEditor(opts.tableType);
    }

    // Function to execute AI diagnostic request with Web Grounding
    async function executeDiagnostics() {
      const aiExplanation = document.getElementById('uai-modal-ai-explanation');
      if (!aiExplanation) return;

      aiExplanation.innerHTML = `
        <div class="d-flex align-items-center gap-2 py-2 text-info">
          <div class="spinner-border spinner-border-sm" role="status"></div>
          <span>Выполняется экспертный AI-анализ для «${escapeHtml(opts.title)}» с проверкой в интернете...</span>
        </div>
      `;

      const metaDict = {};
      (opts.metadata || []).forEach(m => {
        if (m.label && (m.value !== undefined && m.value !== null)) {
          metaDict[m.label] = m.value;
        }
      });

      try {
        const fetchFn = (window.api && window.api.fetch) ? window.api.fetch : fetch;
        const res = await fetchFn('/api/v1/diagnostics/explain', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            table_type: opts.tableType,
            title: opts.title,
            subtitle: opts.subtitle,
            metadata: Object.assign({}, metaDict, opts.requestData || {}),
            raw_data: opts.rawContent || '',
            web_search: true
          })
        });
        const data = (res && typeof res.json === 'function') ? await res.json() : res;

        const isVerified = Boolean(data.is_verified || data.source === 'wikillm');
        const wikillmBadge = isVerified
          ? `<div class="badge bg-success-subtle text-success border border-success p-1 px-2 mb-2 d-inline-flex align-items-center gap-1.5"><i class="bi bi-shield-check"></i> Верифицировано в базе знаний WikiLLM (L1 Exact Cache)</div>`
          : '';

        const approvalBlock = !isVerified ? `
          <div class="p-2 mt-2 rounded bg-dark border border-secondary d-flex align-items-center justify-content-between flex-wrap gap-2" id="uai-approval-container">
            <div class="small text-secondary">
              <i class="bi bi-patch-question me-1 text-warning"></i>Ответ сгенерирован моделью ИИ. Одобрить результат для базы знаний?
            </div>
            <button type="button" class="btn btn-sm btn-outline-success d-inline-flex align-items-center gap-1.5" id="btn-uai-approve-wikillm">
              <i class="bi bi-hand-thumbs-up"></i> Одобрить и сохранить в WikiLLM
            </button>
          </div>
        ` : '';

        aiExplanation.innerHTML = `
          ${wikillmBadge}
          <div class="mb-2"><strong class="text-info"><i class="bi bi-card-text me-1"></i>Назначение:</strong> ${escapeHtml(data.summary)}</div>
          <div class="mb-2"><strong class="text-secondary"><i class="bi bi-building me-1"></i>Разработчик / Категория:</strong> ${escapeHtml(data.developer || 'Неизвестен')} (${escapeHtml(data.category || 'Компонент')})</div>
          <div class="mb-2"><strong class="text-warning"><i class="bi bi-shield-lock me-1"></i>Оценка безопасности:</strong> ${escapeHtml(data.security_verdict)}</div>
          <div class="mb-2"><strong class="text-info"><i class="bi bi-speedometer2 me-1"></i>Влияние на ресурсы:</strong> ${escapeHtml(data.performance_impact)}</div>
          <div class="p-2 mb-2 rounded bg-dark-subtle border border-warning-subtle">
            <strong class="text-warning"><i class="bi bi-lightbulb me-1"></i>Рекомендация:</strong> ${escapeHtml(data.recommendation)}
          </div>
          ${data.action_steps && data.action_steps.length > 0 ? `
            <h6 class="small text-uppercase text-muted fw-bold mb-1">Рекомендуемые действия:</h6>
            <ul class="mb-0 ps-3">
              ${data.action_steps.map(s => `<li>${escapeHtml(s)}</li>`).join('')}
            </ul>
          ` : ''}
          ${approvalBlock}
        `;

        const approveBtn = document.getElementById('btn-uai-approve-wikillm');
        if (approveBtn) {
          approveBtn.onclick = () => approveInWikiLLM(data, opts);
        }

        if (refreshBtn) {
          refreshBtn.style.display = 'inline-flex';
        }
      } catch (err) {
        aiExplanation.innerHTML = `
          <div class="text-danger py-2 d-flex align-items-center justify-content-between flex-wrap gap-2">
            <div><i class="bi bi-exclamation-octagon me-1"></i>Ошибка получения AI-анализа: ${escapeHtml(err.message)}</div>
            <button type="button" class="btn btn-sm btn-outline-danger" id="btn-uai-modal-retry">
              <i class="bi bi-arrow-clockwise me-1"></i>Повторить
            </button>
          </div>
        `;
        const retryBtn = document.getElementById('btn-uai-modal-retry');
        if (retryBtn) {
          retryBtn.onclick = () => executeDiagnostics();
        }
      }
    }

    async function approveInWikiLLM(aiData, options) {
      const approveBtn = document.getElementById('btn-uai-approve-wikillm');
      const container = document.getElementById('uai-approval-container');
      if (approveBtn) approveBtn.disabled = true;

      try {
        const fetchFn = (window.api && window.api.fetch) ? window.api.fetch : fetch;
        const payload = {
          canonical_key: aiData.canonical_key || undefined,
          table_type: options.tableType || 'generic',
          title: options.title || '',
          subtitle: options.subtitle || '',
          summary: aiData.summary || '',
          category: aiData.category || 'system',
          security_verdict: aiData.security_verdict || '',
          performance_impact: aiData.performance_impact || '',
          recommendation: aiData.recommendation || '',
          action_steps: aiData.action_steps || [],
          possible_causes: [],
          tags: [options.tableType || 'generic', 'user_approved'],
          model_name: 'gemini'
        };

        let res = await fetchFn('/api/windows/wikillm/approve', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        // Fallback если роутер смонтирован по /api/v1/diagnostics/approve
        if (res && res.status === 404) {
          res = await fetchFn('/api/v1/diagnostics/approve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          });
        }

        if (res && res.ok === false) {
          throw new Error(`${res.status} ${res.statusText}`);
        }

        const respData = (res && typeof res.json === 'function') ? await res.json() : res;
        if (respData && respData.success) {
          if (container) {
            container.className = 'p-2 mt-2 rounded bg-success bg-opacity-10 border border-success d-flex align-items-center justify-content-between flex-wrap gap-2';
            container.innerHTML = `
              <div class="small text-success fw-bold">
                <i class="bi bi-check-circle-fill me-1"></i>Знание верифицировано и сохранено в WikiLLM (${escapeHtml(respData.canonical_key)})
              </div>
              <span class="badge bg-success text-dark">L1 Exact Cache O(1)</span>
            `;
          }
          if (window.showToast) {
            window.showToast(`Знание «${options.title}» зафиксировано в WikiLLM`, 'success');
          }
        } else {
          throw new Error(respData?.detail || 'Не удалось сохранить знание');
        }
      } catch (err) {
        if (approveBtn) approveBtn.disabled = false;
        alert(`Ошибка сохранения в WikiLLM: ${err.message}`);
      }
    }

    // Only run AI diagnostic automatically if explicitly requested in options
    if (opts.autoRun === true) {
      executeDiagnostics();
    }

    // Custom Footer Actions
    const actionsContainer = document.getElementById('uai-modal-custom-actions');
    if (actionsContainer) {
      actionsContainer.innerHTML = '';
      (opts.actions || []).forEach(act => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = `btn btn-sm ${act.class || 'btn-outline-secondary'}`;
        btn.innerHTML = `${act.icon ? `<i class="bi ${act.icon} me-1"></i>` : ''}${escapeHtml(act.label)}`;
        btn.onclick = () => act.onClick && act.onClick(opts);
        actionsContainer.appendChild(btn);
      });
    }

    // Open Modal
    if (window.bootstrap && window.bootstrap.Modal) {
      const bsModal = window.bootstrap.Modal.getOrCreateInstance(modalEl);
      bsModal.show();
    }
  }

  const PROMPT_MODAL_ID = 'universal-ai-prompt-editor-modal';

  function ensurePromptModalElement() {
    let promptEl = document.getElementById(PROMPT_MODAL_ID);
    if (!promptEl) {
      promptEl = document.createElement('div');
      promptEl.id = PROMPT_MODAL_ID;
      promptEl.className = 'modal fade';
      promptEl.tabIndex = -1;
      promptEl.setAttribute('aria-hidden', 'true');
      promptEl.innerHTML = `
        <div class="modal-dialog modal-lg modal-dialog-centered modal-dialog-scrollable">
          <div class="modal-content bg-dark text-light border-secondary shadow-lg">
            <div class="modal-header border-secondary py-2 px-3">
              <div class="d-flex align-items-center gap-2">
                <span class="fs-5 text-warning">⚙️</span>
                <h5 class="modal-title fw-bold text-warning mb-0">Редактор промпта диагностики</h5>
              </div>
              <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body py-3 px-3">
              <div class="row g-2 mb-3">
                <div class="col-sm-6">
                  <label class="form-label small text-secondary fw-bold mb-1">Тип таблицы / сущности</label>
                  <select class="form-select form-select-sm bg-dark text-light border-secondary" id="uai-prompt-type-select">
                    <option value="software">software (Установленное ПО)</option>
                    <option value="process">process (Процессы Windows)</option>
                    <option value="service">service (Службы Windows)</option>
                    <option value="task">task (Задачи планировщика)</option>
                    <option value="network">network (Сетевой мониторинг)</option>
                    <option value="registry">registry (Реестр Windows)</option>
                    <option value="user">user (Пользователи и группы)</option>
                    <option value="website">website (Мониторинг сайтов)</option>
                    <option value="rag_doc">rag_doc (RAG База знаний)</option>
                    <option value="disk">disk (Диски и тома)</option>
                    <option value="startup">startup (Автозагрузка)</option>
                    <option value="generic">generic (Общий шаблон)</option>
                  </select>
                </div>
                <div class="col-sm-6">
                  <label class="form-label small text-secondary fw-bold mb-1">Название шаблона</label>
                  <input type="text" class="form-control form-control-sm bg-dark text-light border-secondary" id="uai-prompt-name-input" placeholder="Название шаблона">
                </div>
              </div>

              <div class="mb-3">
                <label class="form-label small text-secondary fw-bold mb-1">Системная инструкция (System Instruction)</label>
                <textarea class="form-control form-control-sm bg-dark text-light border-secondary font-monospace" id="uai-prompt-system-input" rows="2" placeholder="Роль и поведение модели..."></textarea>
              </div>

              <div class="mb-2">
                <div class="d-flex justify-content-between align-items-center mb-1">
                  <label class="form-label small text-secondary fw-bold mb-0">Шаблон текста промпта (Prompt Template)</label>
                  <div class="d-flex gap-1" id="uai-prompt-variables-bar">
                    <button type="button" class="btn btn-xs btn-outline-info py-0 px-1 font-monospace" style="font-size: 0.75rem;" onclick="window.AITableModal.insertVariable('{title}')">{title}</button>
                    <button type="button" class="btn btn-xs btn-outline-info py-0 px-1 font-monospace" style="font-size: 0.75rem;" onclick="window.AITableModal.insertVariable('{subtitle}')">{subtitle}</button>
                    <button type="button" class="btn btn-xs btn-outline-info py-0 px-1 font-monospace" style="font-size: 0.75rem;" onclick="window.AITableModal.insertVariable('{metadata}')">{metadata}</button>
                    <button type="button" class="btn btn-xs btn-outline-info py-0 px-1 font-monospace" style="font-size: 0.75rem;" onclick="window.AITableModal.insertVariable('{raw_data}')">{raw_data}</button>
                  </div>
                </div>
                <textarea class="form-control form-control-sm bg-dark text-light border-secondary font-monospace" id="uai-prompt-template-input" rows="8" placeholder="Текст промпта с плейсхолдерами..."></textarea>
                <div class="form-text small text-secondary" style="font-size: 0.75rem;">
                  Используйте переменные <code>{title}</code>, <code>{subtitle}</code>, <code>{metadata}</code>, <code>{raw_data}</code> для автоматической подстановки контекста строки таблицы.
                </div>
              </div>

              <div id="uai-prompt-status-msg" class="small mt-2" style="display: none;"></div>
            </div>
            <div class="modal-footer border-secondary py-2 px-3 d-flex justify-content-between">
              <button type="button" class="btn btn-sm btn-outline-danger" id="btn-uai-prompt-reset">
                <i class="bi bi-arrow-counterclockwise me-1"></i>Сбросить по умолчанию
              </button>
              <div class="d-flex gap-2">
                <button type="button" class="btn btn-sm btn-secondary" data-bs-dismiss="modal">Закрыть</button>
                <button type="button" class="btn btn-sm btn-primary" id="btn-uai-prompt-save">
                  <i class="bi bi-check2 me-1"></i>Сохранить промпт
                </button>
              </div>
            </div>
          </div>
        </div>
      `;
      document.body.appendChild(promptEl);
    }
    return promptEl;
  }

  async function openPromptEditor(tableType) {
    const promptModalEl = ensurePromptModalElement();
    const typeSelect = document.getElementById('uai-prompt-type-select');
    const nameInput = document.getElementById('uai-prompt-name-input');
    const systemInput = document.getElementById('uai-prompt-system-input');
    const templateInput = document.getElementById('uai-prompt-template-input');
    const statusMsg = document.getElementById('uai-prompt-status-msg');
    const saveBtn = document.getElementById('btn-uai-prompt-save');
    const resetBtn = document.getElementById('btn-uai-prompt-reset');

    if (typeSelect && tableType) {
      typeSelect.value = tableType;
    }

    async function loadTemplate(tType) {
      if (statusMsg) statusMsg.style.display = 'none';
      try {
        const fetchFn = (window.api && window.api.fetch) ? window.api.fetch : fetch;
        const res = await fetchFn(`/api/v1/diagnostics/prompts/${encodeURIComponent(tType)}`);
        const data = (res && typeof res.json === 'function') ? await res.json() : res;
        if (data) {
          if (nameInput) nameInput.value = data.name || '';
          if (systemInput) systemInput.value = data.system_instruction || '';
          if (templateInput) templateInput.value = data.prompt_template || '';
        }
      } catch (e) {
        console.error('Ошибка загрузки шаблона промпта:', e);
      }
    }

    if (typeSelect) {
      typeSelect.onchange = () => loadTemplate(typeSelect.value);
    }

    if (saveBtn) {
      saveBtn.onclick = async () => {
        const currentType = typeSelect ? typeSelect.value : 'generic';
        try {
          const fetchFn = (window.api && window.api.fetch) ? window.api.fetch : fetch;
          await fetchFn(`/api/v1/diagnostics/prompts/${encodeURIComponent(currentType)}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              table_type: currentType,
              name: nameInput ? nameInput.value : '',
              system_instruction: systemInput ? systemInput.value : '',
              prompt_template: templateInput ? templateInput.value : ''
            })
          });
          if (statusMsg) {
            statusMsg.className = 'small mt-2 text-success';
            statusMsg.innerHTML = '<i class="bi bi-check-circle me-1"></i>Шаблон промпта успешно сохранен!';
            statusMsg.style.display = 'block';
            setTimeout(() => { if (statusMsg) statusMsg.style.display = 'none'; }, 3000);
          }
        } catch (err) {
          if (statusMsg) {
            statusMsg.className = 'small mt-2 text-danger';
            statusMsg.innerHTML = `<i class="bi bi-exclamation-triangle me-1"></i>Ошибка сохранения: ${escapeHtml(err.message)}`;
            statusMsg.style.display = 'block';
          }
        }
      };
    }

    if (resetBtn) {
      resetBtn.onclick = async () => {
        const currentType = typeSelect ? typeSelect.value : 'generic';
        if (!confirm(`Сбросить промпт для «${currentType}» к системному значению по умолчанию?`)) return;
        try {
          const fetchFn = (window.api && window.api.fetch) ? window.api.fetch : fetch;
          const res = await fetchFn(`/api/v1/diagnostics/prompts/${encodeURIComponent(currentType)}/reset`, {
            method: 'POST'
          });
          const data = (res && typeof res.json === 'function') ? await res.json() : res;
          if (data) {
            if (nameInput) nameInput.value = data.name || '';
            if (systemInput) systemInput.value = data.system_instruction || '';
            if (templateInput) templateInput.value = data.prompt_template || '';
          }
          if (statusMsg) {
            statusMsg.className = 'small mt-2 text-info';
            statusMsg.innerHTML = '<i class="bi bi-arrow-counterclockwise me-1"></i>Шаблон промпта сброшен к системному по умолчанию.';
            statusMsg.style.display = 'block';
            setTimeout(() => { if (statusMsg) statusMsg.style.display = 'none'; }, 3000);
          }
        } catch (err) {
          if (statusMsg) {
            statusMsg.className = 'small mt-2 text-danger';
            statusMsg.innerHTML = `<i class="bi bi-exclamation-triangle me-1"></i>Ошибка сброса: ${escapeHtml(err.message)}`;
            statusMsg.style.display = 'block';
          }
        }
      };
    }

    await loadTemplate(typeSelect ? typeSelect.value : (tableType || 'generic'));

    if (window.bootstrap && window.bootstrap.Modal) {
      const bsPromptModal = window.bootstrap.Modal.getOrCreateInstance(promptModalEl);
      bsPromptModal.show();
    }
  }

  function insertVariable(varText) {
    const templateInput = document.getElementById('uai-prompt-template-input');
    if (!templateInput) return;
    const start = templateInput.selectionStart || 0;
    const end = templateInput.selectionEnd || 0;
    const val = templateInput.value;
    templateInput.value = val.substring(0, start) + varText + val.substring(end);
    templateInput.focus();
    templateInput.selectionStart = templateInput.selectionEnd = start + varText.length;
  }

  // Global Export
  window.AITableModal = {
    show: show,
    openPromptEditor: openPromptEditor,
    insertVariable: insertVariable,
    escapeHtml: escapeHtml
  };
})();
