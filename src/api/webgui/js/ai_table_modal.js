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
                <h5 class="modal-title fw-bold text-info mb-0" id="uai-modal-titlei18n.t('auto__h5_div_id__bbefd7')uai-modal-badges" class="d-flex align-items-center gap-1"></div>
              </div>
              <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body py-3 px-3">
              <!-- Metadata Grid -->
              <div class="row g-2 mb-3 small" id="uai-modal-metadata-grid"></div>

              <!-- Raw / Code Content Section -->
              <div class="card bg-black border-secondary p-3 mb-3" id="uai-modal-raw-container" style="display: none;">
                <div class="d-flex justify-content-between align-items-center mb-1">
                  <h6 class="small text-uppercase text-muted fw-bold mb-0" id="uai-modal-raw-titlei18n.t('auto__h6_div_div_class__bc70ed')small font-monospace text-light" id="uai-modal-raw-content" style="white-space: pre-wrap; word-break: break-all;"></div>
              </div>

              <!-- AI Contextual Diagnostic Card -->
              <div class="card border-info bg-dark p-3" id="uai-modal-ai-section">
                <div class="d-flex justify-content-between align-items-center mb-2 flex-wrap gap-2">
                  <div class="d-flex align-items-center gap-2">
                    <h6 class="fw-bold text-info mb-0"><i class="bi bi-robot me-1"></i> AI Contextual Explanation</h6>
                    <span class="badge bg-info-subtle text-info border border-info-subtle small px-2 py-0.5" id="uai-modal-web-status" title=i18n.t('auto___441b4d')>
                      <i class="bi bi-globe me-1"></i>Web Grounding
                    </span>
                  </div>
                  <div class="d-flex align-items-center gap-1.5">
                    <button class="btn btn-sm btn-outline-secondary py-0 px-2 rounded-pill" id="btn-uai-modal-edit-prompt" title=i18n.t('auto___ebcb79')>
                      <i class="bi bi-gear-fill me-1i18n.t('auto__i_button_button_class__2d84f7')btn btn-sm btn-outline-info py-0 px-2 rounded-pill" id="btn-uai-modal-refresh" title=i18n.t('auto__ai__52c90a')>
                      <i class="bi bi-arrow-clockwise"></i>
                    </button>
                  </div>
                </div>
                <div class="small" id="uai-modal-ai-explanation">
                  <div class="d-flex align-items-center gap-2 py-2 text-info">
                    <div class="spinner-border spinner-border-sm" role="statusi18n.t('auto__div_span_ai_span_div_div_div_div_div_class__c64efb')modal-footer border-secondary py-2 px-3 d-flex justify-content-between">
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
      title: i18n.t('auto___4f7c08'),
      subtitle: '',
      icon: '🔍',
      badges: [],
      metadata: [],
      rawTitle: i18n.t('auto___b6d2b4'),
      rawContent: '',
      tableType: 'generic',
      requestData: {},
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

    // Reset AI Diagnostic section
    const aiExplanation = document.getElementById('uai-modal-ai-explanationi18n.t('auto__if_aiexplanation_aiexplanation_innerhtml_wire_up_prompt_editor_button_const_editpromptbtn_document_getelementbyid__1525f8')btn-uai-modal-edit-prompt');
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

        aiExplanation.innerHTML = `
          <div class="mb-2"><strong class="text-info"><i class="bi bi-card-text me-1i18n.t('auto__i_strong_escapehtml_data_summary_div_div_class__07b7ca')mb-2"><strong class="text-secondary"><i class="bi bi-building me-1"></i>Разработчик / Категория:</strong> ${escapeHtml(data.developer || i18n.t('auto___1fada4'))} (${escapeHtml(data.category || i18n.t('auto___8879f4'))})</div>
          <div class="mb-2"><strong class="text-warning"><i class="bi bi-shield-lock me-1i18n.t('auto__i_strong_escapehtml_data_security_verdict_div_div_class__0b8cf0')mb-2"><strong class="text-info"><i class="bi bi-speedometer2 me-1i18n.t('auto__i_strong_escapehtml_data_performance_impact_div_div_class__cb18ac')p-2 mb-2 rounded bg-dark-subtle border border-warning-subtle">
            <strong class="text-warning"><i class="bi bi-lightbulb me-1i18n.t('auto__i_strong_escapehtml_data_recommendation_div_data_action_steps_data_action_steps_length_0_h6_class__f38d65')small text-uppercase text-muted fw-bold mb-1i18n.t('auto__h6_ul_class__9e4d57')mb-0 ps-3">
              ${data.action_steps.map(s => `<li>${escapeHtml(s)}</li>`).join('')}
            </ul>
          ` : ''}
        `;
      } catch (err) {
        aiExplanation.innerHTML = `<div class="text-danger py-2"><i class="bi bi-exclamation-octagon me-1"></i>Ошибка получения AI-анализа: ${escapeHtml(err.message)}</div>`;
      }
    }

    // Wire up refresh button
    const refreshBtn = document.getElementById('btn-uai-modal-refresh');
    if (refreshBtn) {
      refreshBtn.onclick = () => executeDiagnostics();
    }

    // Auto-run AI diagnostic on show
    executeDiagnostics();

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
                <h5 class="modal-title fw-bold text-warning mb-0i18n.t('auto__h5_div_button_type__8456c2')button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body py-3 px-3">
              <div class="row g-2 mb-3">
                <div class="col-sm-6">
                  <label class="form-label small text-secondary fw-bold mb-1i18n.t('auto__label_select_class__125b0a')form-select form-select-sm bg-dark text-light border-secondary" id="uai-prompt-type-select">
                    <option value="softwarei18n.t('auto__software_option_option_value__cab84b')processi18n.t('auto__process_windows_option_option_value__d09cc1')servicei18n.t('auto__service_windows_option_option_value__e876d7')taski18n.t('auto__task_option_option_value__0f4ac1')networki18n.t('auto__network_option_option_value__640b0c')registryi18n.t('auto__registry_windows_option_option_value__748201')useri18n.t('auto__user_option_option_value__1b4037')websitei18n.t('auto__website_option_option_value__8a78b8')rag_doci18n.t('auto__rag_doc_rag_option_option_value__646bc7')diski18n.t('auto__disk_option_option_value__c1466f')startupi18n.t('auto__startup_option_option_value__70f31a')generici18n.t('auto__generic_option_select_div_div_class__b8c2ff')col-sm-6">
                  <label class="form-label small text-secondary fw-bold mb-1i18n.t('auto__label_input_type__c86976')text" class="form-control form-control-sm bg-dark text-light border-secondary" id="uai-prompt-name-input" placeholder=i18n.t('auto___fa788b')>
                </div>
              </div>

              <div class="mb-3">
                <label class="form-label small text-secondary fw-bold mb-1i18n.t('auto__system_instruction_label_textarea_class__0675d5')form-control form-control-sm bg-dark text-light border-secondary font-monospace" id="uai-prompt-system-input" rows="2" placeholder=i18n.t('auto___f8fea7')></textarea>
              </div>

              <div class="mb-2">
                <div class="d-flex justify-content-between align-items-center mb-1">
                  <label class="form-label small text-secondary fw-bold mb-0i18n.t('auto__prompt_template_label_div_class__d61df1')d-flex gap-1" id="uai-prompt-variables-bar">
                    <button type="button" class="btn btn-xs btn-outline-info py-0 px-1 font-monospace" style="font-size: 0.75rem;" onclick="window.AITableModal.insertVariable('{title}')">{title}</button>
                    <button type="button" class="btn btn-xs btn-outline-info py-0 px-1 font-monospace" style="font-size: 0.75rem;" onclick="window.AITableModal.insertVariable('{subtitle}')">{subtitle}</button>
                    <button type="button" class="btn btn-xs btn-outline-info py-0 px-1 font-monospace" style="font-size: 0.75rem;" onclick="window.AITableModal.insertVariable('{metadata}')">{metadata}</button>
                    <button type="button" class="btn btn-xs btn-outline-info py-0 px-1 font-monospace" style="font-size: 0.75rem;" onclick="window.AITableModal.insertVariable('{raw_data}')">{raw_data}</button>
                  </div>
                </div>
                <textarea class="form-control form-control-sm bg-dark text-light border-secondary font-monospace" id="uai-prompt-template-input" rows="8" placeholder=i18n.t('auto___e32441')></textarea>
                <div class="form-text small text-secondary" style="font-size: 0.75rem;i18n.t('auto__code_title_code_code_subtitle_code_code_metadata_code_code_raw_data_code_div_div_div_id__2fd75d')uai-prompt-status-msg" class="small mt-2" style="display: none;"></div>
            </div>
            <div class="modal-footer border-secondary py-2 px-3 d-flex justify-content-between">
              <button type="button" class="btn btn-sm btn-outline-danger" id="btn-uai-prompt-reset">
                <i class="bi bi-arrow-counterclockwise me-1i18n.t('auto__i_button_div_class__b54560')d-flex gap-2">
                <button type="button" class="btn btn-sm btn-secondary" data-bs-dismiss="modali18n.t('auto__button_button_type__9e4235')button" class="btn btn-sm btn-primary" id="btn-uai-prompt-save">
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
        console.error(i18n.t('auto___7249c9'), e);
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
        const currentType = typeSelect ? typeSelect.value : 'generici18n.t('auto__if_confirm_currenttype_return_try_const_fetchfn_window_api_window_api_fetch_window_api_fetch_fetch_const_res_await_fetchfn_api_v1_diagnostics_prompts_encodeuricomponent_currenttype_reset_method__b5420f')POST'
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
