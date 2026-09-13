// Skills Tab Logic for AI Breadboard Admin Interface
// Supports 3 Creation Modes (Step-by-Step Wizard, AI Assistant, Presets Library) and Live Sandbox Testing

class SkillsTabManager {
  constructor() {
    this.skills = [];
    this.filteredSkills = [];
    this.currentSkill = null;
    this.viewMode = 'cards'; // 'cards' | 'table'
    this.searchQuery = '';
    this.activeFilter = 'all'; // 'all' | 'scripts' | 'references' | 'packaged'
    this.isInitialized = false;

    // Wizard state
    this.currentWizardStep = 1;
    this.createMode = 'wizard'; // 'wizard' | 'ai' | 'presets'
    this.aiGeneratedData = null;

    // Presets catalog
    this.presets = [
      {
        id: 'tool-automation',
        title: '🛠️ CLI & Python Tool',
        category: 'tools',
        badge: 'Automation',
        description: 'Исполняемый навык с Python-скриптом автоматизации в папке scripts/. Подходит для утилит, конвертеров и системных задач.',
        name: 'custom-cli-tool',
        descRu: 'Автоматизированная CLI утилита для выполнения задач через скрипты.',
        descEn: 'Automated CLI utility providing executable scripts for system routines.',
        purpose: 'Execute specialized automation commands via internal scripts.',
        triggers: 'Triggered when the user requests executing a custom tool or batch script task.',
        protocol: '1. Validate arguments and environment.\n2. Execute python script in `scripts/main.py`.\n3. Return formatted stdout/stderr status.',
        rules: '- Ensure non-zero exit codes are logged and reported.\n- Maintain English logging.',
        hasScript: true,
        scriptCode: `# -*- coding: utf-8 -*-\n"""CLI tool automation script."""\nimport sys\n\ndef main():\n    print("Executing automated tool task...")\n    return 0\n\nif __name__ == "__main__":\n    sys.exit(main())\n`,
        hasRef: false,
      },
      {
        id: 'api-connector',
        title: '🌐 REST API Connector',
        category: 'api',
        badge: 'Integration',
        description: 'Интеграция с внешним REST/JSON API. Шаблон с проверкой авторизации, обработкой таймаутов и структурированием ответов.',
        name: 'rest-api-connector',
        descRu: 'Интеграция с внешним сервисом через REST API.',
        descEn: 'Connector skill for external REST API services and endpoints.',
        purpose: 'Query external HTTP REST API endpoints and process JSON payloads.',
        triggers: 'Triggered when user asks to fetch data from or post payloads to remote APIs.',
        protocol: '1. Parse endpoint parameters and auth tokens.\n2. Send HTTP request with exponential retry.\n3. Parse JSON response and summarize.',
        rules: '- Protect sensitive secrets and auth tokens.\n- Handle rate limits and connection timeouts gracefully.',
        hasScript: true,
        scriptCode: `# -*- coding: utf-8 -*-\n"""REST API client script."""\nimport os, urllib.request, json\n\ndef query_api(url: str):\n    req = urllib.request.Request(url, headers={"User-Agent": "AI-Breadboard/1.0"})\n    with urllib.request.urlopen(req, timeout=10) as resp:\n        return json.loads(resp.read().decode("utf-8"))\n`,
        hasRef: true,
        refContent: `# REST API Protocol Guidelines\n\n- Standard timeout: 10s\n- Required headers: User-Agent, Accept\n`,
      },
      {
        id: 'data-parser',
        title: '📊 Data Analyzer & Parser',
        category: 'data',
        badge: 'Analytics',
        description: 'Обработка и анализ структурированных данных (CSV, JSON, XML, таблицы, логи). Извлечение инсайтов и форматирование результатов.',
        name: 'data-analyzer',
        descRu: 'Анализ структурированных данных, логов и таблиц с выводом статистики.',
        descEn: 'Analyze structured data, logs, CSV/JSON datasets, and generate statistics.',
        purpose: 'Parse input data files, compute aggregated metrics, and present visual summaries.',
        triggers: 'Triggered when datasets, spreadsheets or data files need parsing and reporting.',
        protocol: '1. Identify input format (CSV/JSON/Log).\n2. Parse schema and clean invalid rows.\n3. Compute totals, distributions, and outliers.\n4. Output Markdown summary tables.',
        rules: '- Avoid memory leaks on large files.\n- Strictly English docstrings.',
        hasScript: true,
        scriptCode: `# -*- coding: utf-8 -*-\n"""Data parsing helper."""\nimport csv, json\n\ndef parse_records(filepath: str):\n    # Add parser logic here\n    pass\n`,
        hasRef: false,
      },
      {
        id: 'ai-persona',
        title: '🎭 AI Expert & Persona',
        category: 'persona',
        badge: 'Agent Role',
        description: 'Специализированная роль и экспертные инструкции (Архитектор, Аналитик безопасности, Code Reviewer, Консультант).',
        name: 'domain-expert',
        descRu: 'Экспертная роль и правила поведения для специализированных консультаций.',
        descEn: 'Specialized domain expert persona with strict evaluation guidelines.',
        purpose: 'Act as a senior domain expert offering high-level technical feedback.',
        triggers: 'Triggered whenever specialized architectural or domain advice is requested.',
        protocol: '1. Analyze problem from the perspective of domain best practices.\n2. Provide structured pros/cons analysis.\n3. Recommend action plan with trade-offs.',
        rules: '- Be concise, objective, and reference industry standards.',
        hasScript: false,
        hasRef: true,
        refContent: `# Domain Expertise Standards\n\nKey methodologies, architecture patterns, and decision trees.\n`,
      },
      {
        id: 'monitoring-notifier',
        title: '🔔 Monitor & Notifier',
        category: 'monitoring',
        badge: 'Observability',
        description: 'Периодическая проверка сервисов, мониторинг системных параметров, выявление сбоев и отправка нотификаций.',
        name: 'health-monitor',
        descRu: 'Мониторинг доступности сервисов и формирование алертов при сбоях.',
        descEn: 'Health monitoring and alerting skill for infrastructure and services.',
        purpose: 'Continuously verify target service endpoints and notify on anomalies.',
        triggers: 'Triggered by scheduled cron jobs or on-demand health check requests.',
        protocol: '1. Ping healthcheck endpoints.\n2. Measure latency and status codes.\n3. If failure detected, format diagnostic alert.',
        rules: '- Fail-fast on network unreachability.\n- Include timestamps and severity level.',
        hasScript: true,
        scriptCode: `# -*- coding: utf-8 -*-\n"""Health check monitor."""\nimport time\n\ndef check_service(host: str, port: int):\n    # Health probe\n    return True\n`,
        hasRef: false,
      },
      {
        id: 'doc-generator',
        title: '📄 Report & Doc Generator',
        category: 'docgen',
        badge: 'Documentation',
        description: 'Автоматическая генерация документации, отчетов в Markdown/HTML и сводок по проекту на основе входных данных.',
        name: 'report-generator',
        descRu: 'Генератор красивых отчетов, проектной документации и сводок.',
        descEn: 'Automated documentation and structured report generation skill.',
        purpose: 'Generate comprehensive Markdown reports, change logs, and release notes.',
        triggers: 'Triggered when documentation, release summaries or audit reports are requested.',
        protocol: '1. Collect source items and metadata.\n2. Apply template sections and headings.\n3. Format tables and GitHub alerts.\n4. Save output file.',
        rules: '- Follow documentation style standards.\n- Ensure all links and tables are valid.',
        hasScript: false,
        hasRef: true,
        refContent: `# Document Generation Templates\n\nTemplate blocks, header standards, and formatting guidelines.\n`,
      }
    ];
  }

  async init() {
    if (this.isInitialized) {
      await this.refresh();
      return;
    }
    this.bindEvents();
    this.renderPresets();
    this.isInitialized = true;
    await this.refresh();
  }

  bindEvents() {
    const searchInput = document.getElementById('skills-search-input');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        this.searchQuery = e.target.value.trim().toLowerCase();
        this.applyFilters();
      });
    }

    const wizardNameInput = document.getElementById('wizard-skill-name');
    if (wizardNameInput) {
      wizardNameInput.addEventListener('input', (e) => {
        const val = e.target.value;
        const normalized = val.toLowerCase().replace(/[^a-z0-9_-]/g, '-');
        if (val !== normalized) {
          e.target.value = normalized;
        }
        this.syncWizardPreview();
      });
    }

    // Step 2 field listeners for live markdown generator
    ['wizard-inst-purpose', 'wizard-inst-triggers', 'wizard-inst-protocol', 'wizard-inst-rules'].forEach(id => {
      const el = document.getElementById(id);
      if (el) {
        el.addEventListener('input', () => this.syncInstructionsFromFields());
      }
    });

    ['wizard-skill-desc-ru', 'wizard-skill-desc-en', 'wizard-skill-dir'].forEach(id => {
      const el = document.getElementById(id);
      if (el) {
        el.addEventListener('input', () => this.syncWizardPreview());
        el.addEventListener('change', () => this.syncWizardPreview());
      }
    });
  }

  async apiFetch(endpoint, options = {}) {
    let url = endpoint;
    let res = await fetch(url, options);
    if (!res.ok && url.startsWith('/api/skills')) {
      const fallbackUrl = url.replace('/api/skills', '/api/admin/skills');
      const fallbackRes = await fetch(fallbackUrl, options);
      if (fallbackRes.ok) {
        return fallbackRes;
      }
    }
    return res;
  }

  async refresh() {
    this.showLoading(true);
    try {
      const response = await this.apiFetch('/api/skills');
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      this.skills = data.skills || [];
      this.updateStats();
      this.applyFilters();
    } catch (err) {
      console.error('[SkillsTab] Load error:', err);
      const cardsContainer = document.getElementById('skills-cards-container');
      if (cardsContainer) {
        cardsContainer.innerHTML = `
          <div class="col-12">
            <div class="alert alert-danger d-flex align-items-center justify-content-between p-3 shadow-sm">
              <div><i class="bi bi-exclamation-triangle-fill me-2"></i><strong>Ошибка загрузки навыков:</strong> ${err.message}</div>
              <button class="btn btn-sm btn-outline-light" onclick="window.skillsTab?.refresh()">Повторить</button>
            </div>
          </div>
        `;
      }
    } finally {
      this.showLoading(false);
    }
  }

  updateStats() {
    const total = this.skills.length;
    const withScripts = this.skills.filter(s => s.has_scripts).length;
    const withRefs = this.skills.filter(s => s.has_references).length;
    const packaged = this.skills.filter(s => s.has_dist).length;

    const setVal = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.textContent = val;
    };

    setVal('skills-total-badge', total);
    setVal('stat-total-skills', total);
    setVal('stat-scripts-skills', withScripts);
    setVal('stat-refs-skills', withRefs);
    setVal('stat-packaged-skills', packaged);
  }

  applyFilters() {
    const filterSelect = document.getElementById('skills-filter-select');
    this.activeFilter = filterSelect ? filterSelect.value : 'all';

    this.filteredSkills = this.skills.filter(skill => {
      if (this.searchQuery) {
        const nameMatch = (skill.name || '').toLowerCase().includes(this.searchQuery);
        const descMatch = (skill.description || '').toLowerCase().includes(this.searchQuery);
        const i18nMatch = Object.values(skill.descriptions_i18n || {}).some(d => (d || '').toLowerCase().includes(this.searchQuery));
        if (!nameMatch && !descMatch && !i18nMatch) return false;
      }

      if (this.activeFilter === 'scripts' && !skill.has_scripts) return false;
      if (this.activeFilter === 'references' && !skill.has_references) return false;
      if (this.activeFilter === 'packaged' && !skill.has_dist) return false;

      return true;
    });

    this.render();
  }

  clearSearch() {
    const searchInput = document.getElementById('skills-search-input');
    if (searchInput) searchInput.value = '';
    this.searchQuery = '';
    this.applyFilters();
  }

  setViewMode(mode) {
    this.viewMode = mode;
    const btnCards = document.getElementById('btn-view-cards');
    const btnTable = document.getElementById('btn-view-table');

    if (mode === 'cards') {
      btnCards?.classList.add('active');
      btnTable?.classList.remove('active');
    } else {
      btnCards?.classList.remove('active');
      btnTable?.classList.add('active');
    }
    this.render();
  }

  render() {
    const cardsContainer = document.getElementById('skills-cards-container');
    const tableCard = document.getElementById('skills-table-card');
    const emptyNotice = document.getElementById('skills-empty');

    if (!cardsContainer || !tableCard) return;

    if (this.filteredSkills.length === 0) {
      cardsContainer.innerHTML = '';
      tableCard.classList.add('d-none');
      emptyNotice?.classList.remove('d-none');
      return;
    }

    emptyNotice?.classList.add('d-none');

    if (this.viewMode === 'cards') {
      tableCard.classList.add('d-none');
      cardsContainer.classList.remove('d-none');
      cardsContainer.innerHTML = this.filteredSkills.map(s => this.renderCard(s)).join('');
    } else {
      cardsContainer.classList.add('d-none');
      tableCard.classList.remove('d-none');
      const tableBody = document.getElementById('skills-table-body');
      if (tableBody) {
        tableBody.innerHTML = this.filteredSkills.map(s => this.renderTableRow(s)).join('');
      }
    }
  }

  renderCard(skill) {
    const escapeHtml = str => String(str || '').replace(/[&<>'"]/g, tag => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
    }[tag] || tag));

    const badges = [];
    if (skill.has_scripts) badges.push('<span class="badge bg-info-subtle text-info border border-info-subtle small me-1"><i class="bi bi-file-earmark-code"></i> scripts</span>');
    if (skill.has_references) badges.push('<span class="badge bg-warning-subtle text-warning border border-warning-subtle small me-1"><i class="bi bi-journal-text"></i> references</span>');
    if (skill.has_assets) badges.push('<span class="badge bg-secondary border border-secondary small me-1"><i class="bi bi-images"></i> assets</span>');
    if (skill.has_dist) badges.push('<span class="badge bg-success-subtle text-success border border-success-subtle small me-1"><i class="bi bi-box-seam"></i> .skill</span>');

    const descRu = skill.descriptions_i18n?.ru || '';
    const descDisplay = descRu ? `${descRu}` : (skill.description || 'Описание отсутствует');

    return `
      <div class="col-12 col-md-6 col-lg-4">
        <div class="card bg-dark border-secondary text-white h-100 shadow-sm skill-card">
          <div class="card-header border-secondary d-flex justify-content-between align-items-center bg-black bg-opacity-25 py-2">
            <span class="badge bg-primary font-monospace fs-6 text-truncate" style="max-width: 70%;" title="${escapeHtml(skill.name)}">
              ⚡ ${escapeHtml(skill.name)}
            </span>
            <span class="text-muted small" title="Количество файлов">
              <i class="bi bi-files"></i> ${skill.files_count || 1}
            </span>
          </div>
          <div class="card-body py-2">
            <p class="card-text text-light small mb-2 text-truncate-3" style="min-height: 40px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;" title="${escapeHtml(descDisplay)}">
              ${escapeHtml(descDisplay)}
            </p>
            <div class="mb-2 text-truncate">
              <small class="text-secondary font-monospace"><i class="bi bi-folder"></i> ${escapeHtml(skill.relative_path)}</small>
            </div>
            <div class="d-flex flex-wrap gap-1">
              ${badges.join('')}
            </div>
          </div>
          <div class="card-footer border-secondary bg-black bg-opacity-25 py-2 d-flex justify-content-between align-items-center">
            <button type="button" class="btn btn-sm btn-outline-primary d-flex align-items-center gap-1" onclick="window.skillsTab?.openSkillDetails('${escapeHtml(skill.name)}')">
              <i class="bi bi-sliders"></i> Детали
            </button>
            <div class="btn-group btn-group-sm">
              <button type="button" class="btn btn-outline-warning" title="Тестировать в Sandbox" onclick="window.skillsTab?.openSkillSandbox('${escapeHtml(skill.name)}')">
                <i class="bi bi-play-circle"></i>
              </button>
              <button type="button" class="btn btn-outline-info" title="Собрать .skill архив" onclick="window.skillsTab?.packageSkill('${escapeHtml(skill.name)}')">
                <i class="bi bi-box-seam"></i>
              </button>
              <button type="button" class="btn btn-outline-danger" title="Удалить навык" onclick="window.skillsTab?.deleteSkill('${escapeHtml(skill.name)}')">
                <i class="bi bi-trash"></i>
              </button>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  renderTableRow(skill) {
    const escapeHtml = str => String(str || '').replace(/[&<>'"]/g, tag => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
    }[tag] || tag));

    const badges = [];
    if (skill.has_scripts) badges.push('<span class="badge bg-info-subtle text-info border border-info-subtle small me-1">scripts</span>');
    if (skill.has_references) badges.push('<span class="badge bg-warning-subtle text-warning border border-warning-subtle small me-1">refs</span>');
    if (skill.has_dist) badges.push('<span class="badge bg-success-subtle text-success border border-success-subtle small me-1">.skill</span>');

    const descRu = skill.descriptions_i18n?.ru || '';
    const descDisplay = descRu ? `${descRu}` : (skill.description || '—');

    return `
      <tr>
        <td>
          <span class="badge bg-primary font-monospace fs-6">⚡ ${escapeHtml(skill.name)}</span>
        </td>
        <td>
          <div class="small text-light text-truncate" style="max-width: 350px;" title="${escapeHtml(descDisplay)}">
            ${escapeHtml(descDisplay)}
          </div>
        </td>
        <td>
          <code class="small text-secondary">${escapeHtml(skill.relative_path)}</code>
        </td>
        <td>
          ${badges.length ? badges.join('') : '<span class="text-muted small">—</span>'}
        </td>
        <td style="text-align: right;">
          <div class="btn-group btn-group-sm">
            <button type="button" class="btn btn-outline-primary" title="Открыть детали" onclick="window.skillsTab?.openSkillDetails('${escapeHtml(skill.name)}')">
              <i class="bi bi-sliders"></i>
            </button>
            <button type="button" class="btn btn-outline-warning" title="Тестировать в Sandbox" onclick="window.skillsTab?.openSkillSandbox('${escapeHtml(skill.name)}')">
              <i class="bi bi-play-circle"></i>
            </button>
            <button type="button" class="btn btn-outline-info" title="Собрать архив" onclick="window.skillsTab?.packageSkill('${escapeHtml(skill.name)}')">
              <i class="bi bi-box-seam"></i>
            </button>
            <button type="button" class="btn btn-outline-danger" title="Удалить" onclick="window.skillsTab?.deleteSkill('${escapeHtml(skill.name)}')">
              <i class="bi bi-trash"></i>
            </button>
          </div>
        </td>
      </tr>
    `;
  }

  // =========================================================================
  // CREATION WIZARD LOGIC (3 Modes: Wizard, AI, Presets)
  // =========================================================================

  switchCreateMode(mode) {
    this.createMode = mode;
  }

  goToStep(step) {
    if (step < 1 || step > 4) return;
    this.currentWizardStep = step;

    for (let i = 1; i <= 4; i++) {
      const stepEl = document.getElementById(`wizard-step-${i}`);
      const badgeEl = document.getElementById(`step-badge-${i}`);
      const labelEl = document.getElementById(`step-label-${i}`);

      if (stepEl) {
        if (i === step) stepEl.classList.remove('d-none');
        else stepEl.classList.add('d-none');
      }

      if (badgeEl && labelEl) {
        if (i === step) {
          badgeEl.className = 'badge rounded-circle p-2 bg-primary step-indicator';
          labelEl.className = 'small fw-semibold text-white';
        } else if (i < step) {
          badgeEl.className = 'badge rounded-circle p-2 bg-success step-indicator';
          labelEl.className = 'small text-success';
        } else {
          badgeEl.className = 'badge rounded-circle p-2 bg-secondary step-indicator';
          labelEl.className = 'small text-muted';
        }
      }
    }

    const prevBtn = document.getElementById('btn-wizard-prev');
    const nextBtn = document.getElementById('btn-wizard-next');
    const submitBtn = document.getElementById('btn-wizard-submit');

    if (prevBtn) prevBtn.disabled = (step === 1);
    if (nextBtn) {
      if (step === 4) nextBtn.classList.add('d-none');
      else nextBtn.classList.remove('d-none');
    }
    if (submitBtn) {
      if (step === 4) submitBtn.classList.remove('d-none');
      else submitBtn.classList.add('d-none');
    }

    if (step === 4) {
      this.syncWizardPreview();
    }
  }

  wizardNextStep() {
    if (this.currentWizardStep === 1) {
      const name = document.getElementById('wizard-skill-name')?.value.trim();
      if (!name) {
        this.showCreateAlert('Укажите имя навыка (kebab-case)', 'danger');
        return;
      }
      this.clearCreateAlert();
    }
    this.goToStep(this.currentWizardStep + 1);
  }

  wizardPrevStep() {
    this.goToStep(this.currentWizardStep - 1);
  }

  generateSlugFromName() {
    const descRu = document.getElementById('wizard-skill-desc-ru')?.value.trim();
    const descEn = document.getElementById('wizard-skill-desc-en')?.value.trim();
    const source = descEn || descRu || 'custom-skill';
    
    // Transliterate or simple slugify
    let slug = source.toLowerCase()
      .replace(/[а-яё]/g, char => {
        const tr = {'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'yo','ж':'zh','з':'z','и':'i','й':'y','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f','х':'h','ц':'ts','ч':'ch','ш':'sh','щ':'sch','ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya'};
        return tr[char] || char;
      })
      .replace(/[^a-z0-9_-]/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-|-$/g, '')
      .slice(0, 32);

    if (slug) {
      const nameInput = document.getElementById('wizard-skill-name');
      if (nameInput) nameInput.value = slug;
      this.syncWizardPreview();
    }
  }

  onCategoryChanged() {
    const cat = document.getElementById('wizard-skill-category')?.value;
    const descRuInput = document.getElementById('wizard-skill-desc-ru');
    const descEnInput = document.getElementById('wizard-skill-desc-en');
    
    if (cat && (!descRuInput?.value || !descEnInput?.value)) {
      const preset = this.presets.find(p => p.category === cat);
      if (preset) {
        if (!descRuInput.value) descRuInput.value = preset.descRu;
        if (!descEnInput.value) descEnInput.value = preset.descEn;
      }
    }
    this.syncWizardPreview();
  }

  fillStandardInstructions() {
    const name = document.getElementById('wizard-skill-name')?.value.trim() || 'custom-skill';
    const descRu = document.getElementById('wizard-skill-desc-ru')?.value.trim() || 'Выполнение специализированных задач';
    const descEn = document.getElementById('wizard-skill-desc-en')?.value.trim() || 'Specialized agent task execution';

    document.getElementById('wizard-inst-purpose').value = descEn;
    document.getElementById('wizard-inst-triggers').value = `Activate when the user asks to perform tasks matching: ${descRu}.`;
    document.getElementById('wizard-inst-protocol').value = `1. Validate input query and preconditions.\n2. Execute core logic and inspect helper scripts in scripts/.\n3. Return structured markdown response.`;
    document.getElementById('wizard-inst-rules').value = `- Ensure English logging via src.logger.logger.\n- Gracefully catch and report all execution errors.`;

    this.syncInstructionsFromFields();
  }

  syncInstructionsFromFields() {
    const name = document.getElementById('wizard-skill-name')?.value.trim() || 'custom-skill';
    const title = name.replace('-', ' ').replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
    const purpose = document.getElementById('wizard-inst-purpose')?.value.trim() || 'Provide specialized agent capability.';
    const triggers = document.getElementById('wizard-inst-triggers')?.value.trim() || 'Activate upon relevant user requests.';
    const protocol = document.getElementById('wizard-inst-protocol')?.value.trim() || '1. Parse input.\n2. Execute action.\n3. Output result.';
    const rules = document.getElementById('wizard-inst-rules')?.value.trim() || '- Maintain fail-fast validation.\n- Report status clearly.';

    const md = `# ${title}

## 🎯 Purpose
${purpose}

## 🚀 When to Use & Triggers
${triggers}

## 📋 Execution Protocol
${protocol}

## ⚙️ Rules & Constraints
${rules}
`;
    const instEl = document.getElementById('wizard-skill-instructions');
    if (instEl) instEl.value = md;
    this.syncWizardPreview();
  }

  toggleScriptEditor() {
    const chk = document.getElementById('wizard-enable-script');
    const container = document.getElementById('wizard-script-container');
    const scriptCode = document.getElementById('wizard-script-code');

    if (chk?.checked) {
      container?.classList.remove('d-none');
      if (!scriptCode.value.trim()) {
        const name = document.getElementById('wizard-skill-name')?.value.trim() || 'custom-skill';
        scriptCode.value = `# -*- coding: utf-8 -*-\n"""Executable tool helper for ${name}."""\n\nimport sys\n\ndef main():\n    print("Running helper script...")\n    return 0\n\nif __name__ == "__main__":\n    sys.exit(main())\n`;
      }
    } else {
      container?.classList.add('d-none');
    }
    this.syncWizardPreview();
  }

  toggleRefEditor() {
    const chk = document.getElementById('wizard-enable-ref');
    const container = document.getElementById('wizard-ref-container');
    const refContent = document.getElementById('wizard-ref-content');

    if (chk?.checked) {
      container?.classList.remove('d-none');
      if (!refContent.value.trim()) {
        const name = document.getElementById('wizard-skill-name')?.value.trim() || 'custom-skill';
        refContent.value = `# ${name.replace('-', ' ').toUpperCase()} Specification\n\nDetailed operational rules and reference data.\n`;
      }
    } else {
      container?.classList.add('d-none');
    }
    this.syncWizardPreview();
  }

  syncWizardPreview() {
    const name = document.getElementById('wizard-skill-name')?.value.trim() || 'custom-skill';
    const dir = document.getElementById('wizard-skill-dir')?.value || '.agents/skills';
    const descEn = document.getElementById('wizard-skill-desc-en')?.value.trim() || `Agent skill for ${name}.`;
    const descRu = document.getElementById('wizard-skill-desc-ru')?.value.trim() || descEn;
    const instructions = document.getElementById('wizard-skill-instructions')?.value.trim() || `# ${name}\n\n## 🎯 Purpose\n${descEn}\n`;

    const hasScript = document.getElementById('wizard-enable-script')?.checked;
    const hasRef = document.getElementById('wizard-enable-ref')?.checked;

    // Badges in step 4
    const nameEl = document.getElementById('preview-skill-name');
    const pathEl = document.getElementById('preview-skill-path');
    const badgeScript = document.getElementById('preview-badge-script');
    const badgeRef = document.getElementById('preview-badge-ref');
    const previewFull = document.getElementById('preview-skillmd-full');

    if (nameEl) nameEl.textContent = name;
    if (pathEl) pathEl.textContent = `${dir}/${name}`;
    if (badgeScript) {
      if (hasScript) badgeScript.classList.remove('d-none');
      else badgeScript.classList.add('d-none');
    }
    if (badgeRef) {
      if (hasRef) badgeRef.classList.remove('d-none');
      else badgeRef.classList.add('d-none');
    }

    const fullSkillMd = `---
name: ${name}
description: ${descEn}
description_i18n:
  en: ${descEn}
  ru: ${descRu}
---

${instructions}`;

    if (previewFull) previewFull.textContent = fullSkillMd;

    // Sync README default
    const readmeEl = document.getElementById('wizard-skill-readme');
    if (readmeEl && !readmeEl.value.trim()) {
      readmeEl.value = `# ${name.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())}\n\n## Overview\n${descEn}\n\n## Location\n\`${dir}/${name}/\`\n`;
    }
  }

  async createSkillFromWizard() {
    const name = document.getElementById('wizard-skill-name')?.value.trim().toLowerCase();
    if (!name) {
      this.goToStep(1);
      this.showCreateAlert('Укажите имя навыка', 'danger');
      return;
    }

    const spinner = document.getElementById('wizard-submit-spinner');
    spinner?.classList.remove('d-none');

    const descEn = document.getElementById('wizard-skill-desc-en')?.value.trim() || `Agent skill for ${name}.`;
    const descRu = document.getElementById('wizard-skill-desc-ru')?.value.trim() || descEn;
    const targetDir = document.getElementById('wizard-skill-dir')?.value || '.agents/skills';
    const category = document.getElementById('wizard-skill-category')?.value || 'general';
    const instructions = document.getElementById('wizard-skill-instructions')?.value.trim() || '';
    const readme = document.getElementById('wizard-skill-readme')?.value.trim() || '';

    const scripts = {};
    if (document.getElementById('wizard-enable-script')?.checked) {
      scripts['main.py'] = document.getElementById('wizard-script-code')?.value || '';
    }

    const references = {};
    if (document.getElementById('wizard-enable-ref')?.checked) {
      references['guide.md'] = document.getElementById('wizard-ref-content')?.value || '';
    }

    try {
      const res = await this.apiFetch('/api/skills', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name,
          description: descEn,
          description_ru: descRu,
          category,
          target_dir: targetDir,
          instructions,
          readme,
          scripts,
          references
        })
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || res.statusText);
      }

      // Close modal
      const modalEl = document.getElementById('createSkillModal');
      const modal = bootstrap.Modal.getInstance(modalEl);
      modal?.hide();

      await this.refresh();
      await this.openSkillDetails(name);
    } catch (err) {
      console.error('[SkillsTab] Create error:', err);
      this.showCreateAlert(`Ошибка создания навыка: ${err.message}`, 'danger');
    } finally {
      spinner?.classList.add('d-none');
    }
  }

  // =========================================================================
  // AI GENERATOR MODE
  // =========================================================================

  async generateSkillWithAi() {
    const prompt = document.getElementById('ai-skill-prompt')?.value.trim();
    if (!prompt) {
      this.showCreateAlert('Введите описание задачи для генерации навыка', 'warning');
      return;
    }

    const spinner = document.getElementById('ai-gen-spinner');
    const resBox = document.getElementById('ai-result-box');
    const resSlug = document.getElementById('ai-res-slug');
    const resPreview = document.getElementById('ai-res-preview');

    spinner?.classList.remove('d-none');
    this.clearCreateAlert();

    try {
      const category = document.getElementById('ai-skill-category')?.value || 'general';
      const targetDir = document.getElementById('ai-skill-dir')?.value || '.agents/skills';

      const res = await this.apiFetch('/api/skills/generate-ai', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, category, target_dir: targetDir })
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || res.statusText);
      }

      const data = await res.json();
      this.aiGeneratedData = data.generated;

      if (resSlug) resSlug.textContent = `⚡ ${this.aiGeneratedData.name}`;
      if (resPreview) resPreview.textContent = this.aiGeneratedData.instructions;
      resBox?.classList.remove('d-none');
    } catch (err) {
      console.error('[SkillsTab] AI generate error:', err);
      this.showCreateAlert(`Ошибка генерации навыка: ${err.message}`, 'danger');
    } finally {
      spinner?.classList.add('d-none');
    }
  }

  applyAiResultToWizard() {
    if (!this.aiGeneratedData) return;
    const g = this.aiGeneratedData;

    document.getElementById('wizard-skill-name').value = g.name || '';
    document.getElementById('wizard-skill-desc-en').value = g.description || '';
    document.getElementById('wizard-skill-desc-ru').value = g.description_ru || '';
    document.getElementById('wizard-skill-category').value = g.category || 'general';
    document.getElementById('wizard-skill-dir').value = g.target_dir || '.agents/skills';
    document.getElementById('wizard-skill-instructions').value = g.instructions || '';
    document.getElementById('wizard-skill-readme').value = g.readme || '';

    if (g.scripts && g.scripts['main.py']) {
      document.getElementById('wizard-enable-script').checked = true;
      document.getElementById('wizard-script-container').classList.remove('d-none');
      document.getElementById('wizard-script-code').value = g.scripts['main.py'];
    }

    if (g.references && g.references['guide.md']) {
      document.getElementById('wizard-enable-ref').checked = true;
      document.getElementById('wizard-ref-container').classList.remove('d-none');
      document.getElementById('wizard-ref-content').value = g.references['guide.md'];
    }

    // Switch to wizard tab
    const wizardTabBtn = document.getElementById('mode-wizard-tab');
    if (wizardTabBtn) {
      const tab = new bootstrap.Tab(wizardTabBtn);
      tab.show();
    }
    this.goToStep(1);
    this.syncWizardPreview();
  }

  async saveAiSkillDirectly() {
    if (!this.aiGeneratedData) return;
    const g = this.aiGeneratedData;

    try {
      const res = await this.apiFetch('/api/skills', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: g.name,
          description: g.description,
          description_ru: g.description_ru,
          category: g.category,
          target_dir: g.target_dir,
          instructions: g.instructions,
          readme: g.readme,
          scripts: g.scripts || {},
          references: g.references || {}
        })
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || res.statusText);
      }

      const modalEl = document.getElementById('createSkillModal');
      const modal = bootstrap.Modal.getInstance(modalEl);
      modal?.hide();

      await this.refresh();
      await this.openSkillDetails(g.name);
    } catch (err) {
      console.error('[SkillsTab] AI Direct Save error:', err);
      this.showCreateAlert(`Ошибка сохранения: ${err.message}`, 'danger');
    }
  }

  // =========================================================================
  // PRESETS LIBRARY
  // =========================================================================

  renderPresets() {
    const container = document.getElementById('presets-cards-container');
    if (!container) return;

    container.innerHTML = this.presets.map(p => `
      <div class="col-12 col-md-6 col-lg-4">
        <div class="card bg-dark border-secondary text-white h-100 shadow-sm">
          <div class="card-header border-secondary d-flex justify-content-between align-items-center bg-black bg-opacity-25 py-2">
            <span class="fw-bold small text-white">${p.title}</span>
            <span class="badge bg-primary-subtle text-primary border border-primary-subtle small">${p.badge}</span>
          </div>
          <div class="card-body py-2">
            <p class="card-text text-muted small mb-2" style="min-height: 48px;">
              ${p.description}
            </p>
            <div class="small font-monospace text-secondary mb-2">
              <code>⚡ ${p.name}</code>
            </div>
          </div>
          <div class="card-footer border-secondary bg-black bg-opacity-25 py-2">
            <button type="button" class="btn btn-outline-primary btn-sm w-100 d-flex align-items-center justify-content-center gap-1" onclick="window.skillsTab?.applyPreset('${p.id}')">
              <i class="bi bi-box-arrow-in-right"></i> Использовать шаблон
            </button>
          </div>
        </div>
      </div>
    `).join('');
  }

  applyPreset(presetId) {
    const preset = this.presets.find(p => p.id === presetId);
    if (!preset) return;

    document.getElementById('wizard-skill-name').value = preset.name;
    document.getElementById('wizard-skill-desc-en').value = preset.descEn;
    document.getElementById('wizard-skill-desc-ru').value = preset.descRu;
    document.getElementById('wizard-skill-category').value = preset.category;
    document.getElementById('wizard-skill-dir').value = '.agents/skills';

    document.getElementById('wizard-inst-purpose').value = preset.purpose;
    document.getElementById('wizard-inst-triggers').value = preset.triggers;
    document.getElementById('wizard-inst-protocol').value = preset.protocol;
    document.getElementById('wizard-inst-rules').value = preset.rules;
    this.syncInstructionsFromFields();

    // Scripts
    const scriptChk = document.getElementById('wizard-enable-script');
    if (scriptChk) {
      scriptChk.checked = preset.hasScript;
      if (preset.hasScript) {
        document.getElementById('wizard-script-container')?.classList.remove('d-none');
        document.getElementById('wizard-script-code').value = preset.scriptCode || '';
      } else {
        document.getElementById('wizard-script-container')?.classList.add('d-none');
      }
    }

    // References
    const refChk = document.getElementById('wizard-enable-ref');
    if (refChk) {
      refChk.checked = preset.hasRef;
      if (preset.hasRef) {
        document.getElementById('wizard-ref-container')?.classList.remove('d-none');
        document.getElementById('wizard-ref-content').value = preset.refContent || '';
      } else {
        document.getElementById('wizard-ref-container')?.classList.add('d-none');
      }
    }

    // Switch to wizard tab
    const wizardTabBtn = document.getElementById('mode-wizard-tab');
    if (wizardTabBtn) {
      const tab = new bootstrap.Tab(wizardTabBtn);
      tab.show();
    }
    this.goToStep(1);
    this.syncWizardPreview();
  }

  showCreateAlert(msg, type = 'danger') {
    const alertEl = document.getElementById('create-skill-alert');
    if (alertEl) {
      alertEl.className = `alert alert-${type} py-2 mt-3 mb-0`;
      alertEl.textContent = msg;
      alertEl.classList.remove('d-none');
    }
  }

  clearCreateAlert() {
    const alertEl = document.getElementById('create-skill-alert');
    if (alertEl) alertEl.classList.add('d-none');
  }

  // =========================================================================
  // SKILL DETAILS & SANDBOX TESTER
  // =========================================================================

  async openSkillDetails(name, defaultTab = 'detail-tab-skillmd') {
    try {
      const res = await this.apiFetch(`/api/skills/${encodeURIComponent(name)}`);
      if (!res.ok) throw new Error(`Failed to load skill details: ${res.statusText}`);
      const data = await res.json();
      this.currentSkill = data.skill;

      // Populate modal fields
      document.getElementById('detail-skill-title').textContent = this.currentSkill.name;
      document.getElementById('detail-skill-path').textContent = this.currentSkill.relative_path;
      document.getElementById('detail-skill-desc-input').value = this.currentSkill.description || '';
      document.getElementById('detail-skill-desc-ru-input').value = this.currentSkill.descriptions_i18n?.ru || '';
      document.getElementById('detail-skill-instructions').value = this.currentSkill.instructions || '';
      document.getElementById('detail-skill-readme').value = this.currentSkill.readme_raw || '';

      // Populate files list
      const filesContainer = document.getElementById('detail-files-list');
      if (filesContainer) {
        if (this.currentSkill.files && this.currentSkill.files.length > 0) {
          filesContainer.innerHTML = this.currentSkill.files.map(f => `
            <div class="list-group-item bg-transparent text-light border-secondary d-flex justify-content-between align-items-center py-1 small">
              <span><i class="bi bi-file-earmark text-secondary"></i> ${f.rel_path}</span>
              <span class="badge bg-secondary font-monospace">${this.formatBytes(f.size)}</span>
            </div>
          `).join('');
        } else {
          filesContainer.innerHTML = '<div class="text-muted small py-2">Файлы отсутствуют</div>';
        }
      }

      // Populate JSON contract
      const contractEl = document.getElementById('detail-json-contract');
      if (contractEl) {
        const contractObj = {
          name: this.currentSkill.name,
          description: this.currentSkill.description,
          descriptions_i18n: this.currentSkill.descriptions_i18n,
          metadata: this.currentSkill.metadata,
          manifest: this.currentSkill.manifest,
        };
        contractEl.textContent = JSON.stringify(contractObj, null, 2);
      }

      // Reset sandbox box
      const sandboxOutput = document.getElementById('sandbox-output-box');
      if (sandboxOutput) {
        sandboxOutput.textContent = `Готов к тестированию навыка '${this.currentSkill.name}'. Введите тестовый запрос и нажмите «Запустить».`;
      }

      // Hide alerts
      const alertEl = document.getElementById('detail-skill-alert');
      if (alertEl) alertEl.classList.add('d-none');

      // Show modal
      const modalEl = document.getElementById('skillDetailsModal');
      const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
      modal.show();

      // Switch to requested tab
      const targetTabBtn = document.getElementById(defaultTab);
      if (targetTabBtn) {
        const tab = new bootstrap.Tab(targetTabBtn);
        tab.show();
      }
    } catch (err) {
      console.error('[SkillsTab] Details error:', err);
      alert(`Ошибка открытия деталей навыка: ${err.message}`);
    }
  }

  async openSkillSandbox(name) {
    await this.openSkillDetails(name, 'detail-tab-sandbox');
  }

  async runSandboxTest() {
    if (!this.currentSkill) return;
    const promptInput = document.getElementById('sandbox-test-prompt');
    const outputBox = document.getElementById('sandbox-output-box');
    const spinner = document.getElementById('sandbox-spinner');

    const prompt = promptInput?.value.trim() || `Test execute skill ${this.currentSkill.name}`;
    spinner?.classList.remove('d-none');
    if (outputBox) outputBox.textContent = `⏳ Отправка запроса к модели для навыка '${this.currentSkill.name}'...\n`;

    try {
      const res = await this.apiFetch(`/api/skills/${encodeURIComponent(this.currentSkill.name)}/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt })
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || res.statusText);
      }

      const data = await res.json();
      if (outputBox) {
        outputBox.textContent = `[Model: ${data.model_used}]\n\n${data.response}`;
      }
    } catch (err) {
      console.error('[SkillsTab] Sandbox test error:', err);
      if (outputBox) outputBox.textContent = `❌ Ошибка тестирования: ${err.message}`;
    } finally {
      spinner?.classList.add('d-none');
    }
  }

  async saveCurrentSkill() {
    if (!this.currentSkill) return;
    const spinner = document.getElementById('save-skill-spinner');
    const alertEl = document.getElementById('detail-skill-alert');

    spinner?.classList.remove('d-none');
    try {
      const description = document.getElementById('detail-skill-desc-input').value.trim();
      const description_ru = document.getElementById('detail-skill-desc-ru-input').value.trim();
      const instructions = document.getElementById('detail-skill-instructions').value;
      const readme = document.getElementById('detail-skill-readme').value;

      const res = await this.apiFetch(`/api/skills/${encodeURIComponent(this.currentSkill.name)}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description, description_ru, instructions, readme })
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || res.statusText);
      }

      if (alertEl) {
        alertEl.className = 'alert alert-success py-2 mt-3 mb-0';
        alertEl.textContent = '✅ Изменения успешно сохранены';
        alertEl.classList.remove('d-none');
      }

      await this.refresh();
    } catch (err) {
      console.error('[SkillsTab] Save error:', err);
      if (alertEl) {
        alertEl.className = 'alert alert-danger py-2 mt-3 mb-0';
        alertEl.textContent = `Ошибка сохранения: ${err.message}`;
        alertEl.classList.remove('d-none');
      }
    } finally {
      spinner?.classList.add('d-none');
    }
  }

  async packageSkill(name) {
    try {
      const res = await this.apiFetch(`/api/skills/${encodeURIComponent(name)}/package`, {
        method: 'POST'
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || res.statusText);
      }
      const data = await res.json();
      alert(`✅ Навык '${name}' успешно упакован в архив:\n${data.archive?.path} (${this.formatBytes(data.archive?.size)})`);
      await this.refresh();
    } catch (err) {
      console.error('[SkillsTab] Package error:', err);
      alert(`Ошибка сборки архива: ${err.message}`);
    }
  }

  async packageCurrentSkill() {
    if (!this.currentSkill) return;
    await this.packageSkill(this.currentSkill.name);
    await this.openSkillDetails(this.currentSkill.name);
  }

  async deleteSkill(name) {
    if (!confirm(`Вы действительно хотите удалить навык '${name}' и все его файлы? Это действие необратимо.`)) {
      return;
    }

    try {
      const res = await this.apiFetch(`/api/skills/${encodeURIComponent(name)}`, {
        method: 'DELETE'
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || res.statusText);
      }

      const modalEl = document.getElementById('skillDetailsModal');
      const modal = bootstrap.Modal.getInstance(modalEl);
      modal?.hide();

      await this.refresh();
    } catch (err) {
      console.error('[SkillsTab] Delete error:', err);
      alert(`Ошибка удаления навыка: ${err.message}`);
    }
  }

  async deleteCurrentSkill() {
    if (!this.currentSkill) return;
    await this.deleteSkill(this.currentSkill.name);
  }

  showLoading(show) {
    const loadingEl = document.getElementById('skills-loading');
    if (loadingEl) {
      if (show) loadingEl.classList.remove('d-none');
      else loadingEl.classList.add('d-none');
    }
  }

  formatBytes(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }
}

// Global initialization hook
window.SkillsTabManager = SkillsTabManager;
if (!window.skillsTab) {
  window.skillsTab = new SkillsTabManager();
}
window.initSkillsTab = function() {
  if (window.skillsTab) {
    window.skillsTab.init();
  }
};

// Auto-init on script load if container is present
if (document.getElementById('skills-tab-root')) {
  window.skillsTab.init();
}


