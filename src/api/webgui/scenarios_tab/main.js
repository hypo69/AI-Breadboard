// Scenarios and Test Computer Automated Diagnostics Module (/tc)
(function () {
  'use strict';

  let scenariosList = [];
  let currentFilter = 'all';
  let isRunning = false;

  // Icons and badges helper
  const categoryIcons = {
    quick: '⚡',
    logs: '📜',
    diagnostics: '🖥️',
    security: '🛡️',
    network: '🌐',
    ai: '🤖',
  };

  const statusIcons = {
    ok: '✅',
    warn: '⚠️',
    error: '❌',
    skipped: '⏭️',
  };

  // Helper for safe HTML escaping
  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // Simple Markdown to HTML formatter for mini-chat
  function formatMarkdown(text) {
    if (!text) return '';
    let html = escapeHtml(text);
    // Bold
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Italic
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
    // Inline code
    html = html.replace(/`(.*?)`/g, '<code class="text-info bg-black bg-opacity-50 px-1 rounded">$1</code>');
    // Blockquote
    html = html.replace(/^&gt;\s+(.*$)/gim, '<div class="border-start border-primary border-3 ps-2 my-1 text-info bg-primary bg-opacity-10 py-1 rounded-end">$1</div>');
    // Headers
    html = html.replace(/^###\s+(.*$)/gim, '<h6 class="fw-bold text-info mt-2 mb-1">$1</h6>');
    html = html.replace(/^##\s+(.*$)/gim, '<h5 class="fw-bold text-white mt-2 mb-1">$1</h5>');
    // Line breaks
    html = html.replace(/\n/g, '<br>');
    return html;
  }

  // Load scenarios from API
  async function loadScenarios() {
    const container = document.getElementById('scenarios-cards-container');
    if (!container) return;

    try {
      const res = await fetch('/api/v1/scenarios');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      scenariosList = await res.json();
      renderScenariosGrid();
    } catch (err) {
      console.warn('[ScenariosTab] Error fetching /api/v1/scenarios, using local fallback:', err);
      scenariosList = [
        {
          id: 'quick_check',
          title: 'Быстрая проверка (Smoke Test)',
          description: 'Экспресс-проверка целостности окружения, доступности ядра FastAPI, AI-провайдеров, свободного места и ключевых логов. Рекомендуется после установки.',
          category: 'quick',
          icon: '⚡',
          recommended: true,
          estimated_duration_sec: 2,
        },
        {
          id: 'log_audit',
          title: 'Запустить аудит логов',
          description: 'Комплексный анализ файлов логов (info.log, errors.log, app.log) и журналов событий Windows. Поиск критических ошибок и аномалий.',
          category: 'logs',
          icon: '📜',
          recommended: false,
          estimated_duration_sec: 3,
        },
        {
          id: 'system_inspector',
          title: 'Диагностика системы и оборудования',
          description: 'Срез телеметрии: загрузка ядер процессора, температура, оперативная память, свободное место на дисках и фоновые процессы.',
          category: 'diagnostics',
          icon: '🖥️',
          recommended: false,
          estimated_duration_sec: 3,
        },
        {
          id: 'windows_admin',
          title: 'Аудит автозапуска и служб Windows',
          description: 'Проверка записей реестра Run/RunOnce, папки автозагрузки, системных служб Windows и прав текущего процесса.',
          category: 'security',
          icon: '🛡️',
          recommended: false,
          estimated_duration_sec: 4,
        },
        {
          id: 'network_test',
          title: 'Проверка сетевой доступности и портов',
          description: 'Тестирование локального шлюза, разрешения DNS, открытых серверных портов (8000) и доступности внешних AI-сервисов.',
          category: 'network',
          icon: '🌐',
          recommended: false,
          estimated_duration_sec: 4,
        },
        {
          id: 'ai_providers_check',
          title: 'Проверка статуса AI-провайдеров',
          description: 'Опрос сконфигурированных AI-моделей (Google Gemini, AGY, Ollama, Foundry) и замер времени отклика инференса.',
          category: 'ai',
          icon: '🤖',
          recommended: false,
          estimated_duration_sec: 5,
        },
      ];
      renderScenariosGrid();
    }
  }

  // Render cards grid based on active filter
  function renderScenariosGrid() {
    const container = document.getElementById('scenarios-cards-container');
    if (!container) return;

    const filtered = scenariosList.filter(sc => {
      if (currentFilter === 'all') return true;
      return sc.category === currentFilter;
    });

    const badgeEl = document.getElementById('scenarios-count-badge');
    if (badgeEl) {
      badgeEl.innerText = `Доступно: ${filtered.length}`;
    }
    const headerBadgeEl = document.getElementById('scenarios-count-badge-header');
    if (headerBadgeEl) {
      headerBadgeEl.innerText = `${scenariosList.length}`;
    }

    if (filtered.length === 0) {
      container.innerHTML = '<div class="col-12 text-center py-4 text-muted small">В этой категории нет сценариев.</div>';
      return;
    }

    container.innerHTML = filtered.map(sc => {
      const isRecommended = Boolean(sc.recommended);
      const borderClass = isRecommended ? 'border-success border-opacity-50 shadow-sm' : 'border-secondary-subtle';
      const bgHeader = isRecommended ? 'bg-success bg-opacity-10' : 'bg-transparent';
      const btnClass = isRecommended ? 'btn-success' : 'btn-outline-primary';

      return `
        <div class="col-12">
          <div class="card bg-dark bg-opacity-75 ${borderClass} transition-all hover-shadow">
            <div class="card-header ${bgHeader} border-secondary-subtle py-2 px-3 d-flex align-items-center justify-content-between">
              <div class="d-flex align-items-center gap-2">
                <span class="fs-5">${sc.icon || categoryIcons[sc.category] || '🎬'}</span>
                <strong class="text-white small">${escapeHtml(sc.title)}</strong>
              </div>
              <div>
                ${isRecommended ? '<span class="badge bg-success small">Рекомендуется</span>' : `<span class="badge bg-secondary small">${sc.estimated_duration_sec || 3} сек</span>`}
              </div>
            </div>
            <div class="card-body p-3 d-flex flex-column justify-content-between">
              <p class="text-muted small mb-2" style="font-size: 0.8rem; line-height: 1.35;">
                ${escapeHtml(sc.description)}
              </p>
              <div class="d-flex align-items-center justify-content-between gap-2 mt-auto pt-2 border-top border-secondary-subtle">
                <span class="text-secondary small" style="font-size: 0.72rem;">
                  ID: <code>${escapeHtml(sc.id)}</code>
                </span>
                <button class="btn ${btnClass} btn-sm py-1 px-3 d-flex align-items-center gap-1 btn-run-scenario-item" data-scenario-id="${escapeHtml(sc.id)}" ${isRunning ? 'disabled' : ''}>
                  <i class="bi bi-play-fill"></i>
                  <span>Запустить</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      `;
    }).join('');

    // Attach listeners to individual run buttons
    container.querySelectorAll('.btn-run-scenario-item').forEach(btn => {
      btn.onclick = () => {
        const scId = btn.getAttribute('data-scenario-id');
        if (scId) runScenario(scId);
      };
    });
  }

  // Execute scenario via API
  async function runScenario(scenarioId) {
    if (isRunning) return;
    isRunning = true;

    // Automatically open the scenarios drawer if closed
    const offcanvasEl = document.getElementById('scenariosOffcanvas');
    if (offcanvasEl && typeof bootstrap !== 'undefined' && bootstrap.Offcanvas) {
      try {
        const offcanvasInstance = bootstrap.Offcanvas.getOrCreateInstance(offcanvasEl);
        offcanvasInstance.show();
      } catch (e) {
        console.warn('[ScenariosTab] Offcanvas show error:', e);
      }
    }

    const resultPanel = document.getElementById('scenario-result-panel');
    const titleEl = document.getElementById('result-scenario-title');
    const metaEl = document.getElementById('result-scenario-meta');
    const iconEl = document.getElementById('result-status-icon');
    const durationBadge = document.getElementById('result-duration-badge');
    const summaryBanner = document.getElementById('result-summary-banner');
    const summaryText = document.getElementById('result-summary-text');
    const stepsContainer = document.getElementById('scenario-steps-container');
    const progressBar = document.getElementById('scenario-progress-bar');

    if (resultPanel) {
      resultPanel.style.display = '';
      resultPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    if (titleEl) titleEl.innerText = `Выполнение сценария [${scenarioId}]...`;
    if (metaEl) metaEl.innerText = 'Опрос системных подсистем и выполнение тестов...';
    if (iconEl) iconEl.innerText = '⏳';
    if (durationBadge) durationBadge.innerText = 'Выполняется...';
    if (summaryBanner) summaryBanner.className = 'alert alert-info py-2 px-3 mb-3 small d-flex align-items-start gap-2';
    if (summaryText) summaryText.innerText = 'Идет тестирование компонентов... Пожалуйста, подождите.';
    if (stepsContainer) stepsContainer.innerHTML = '<div class="text-center py-3 text-muted small"><div class="spinner-border spinner-border-sm text-primary mb-2"></div><div>Тестирование запущено...</div></div>';
    if (progressBar) {
      progressBar.style.width = '100%';
      progressBar.className = 'progress-bar progress-bar-striped progress-bar-animated bg-primary';
    }

    renderScenariosGrid();

    const tStart = performance.now();
    try {
      const response = await fetch('/api/v1/scenarios/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario_id: scenarioId }),
      });

      if (!response.ok) {
        throw new Error(`Ошибка сервера: HTTP ${response.status}`);
      }

      const res = await response.json();
      displayScenarioResults(res);
    } catch (err) {
      console.error('[ScenariosTab] Error running scenario:', err);
      const totalDur = Math.round(performance.now() - tStart);
      displayScenarioResults({
        scenario_id: scenarioId,
        title: scenarioId,
        status: 'error',
        duration_ms: totalDur,
        total_steps: 1,
        passed_steps: 0,
        warn_steps: 0,
        failed_steps: 1,
        steps: [
          {
            name: 'Выполнение запроса сценария',
            status: 'error',
            duration_ms: totalDur,
            details: `Ошибка: ${err.message}`,
            recommendation: 'Проверьте соединение с бэкенд сервером FastAPI.',
          },
        ],
        summary: `Сбой при выполнении сценария: ${err.message}`,
      });
    } finally {
      isRunning = false;
      renderScenariosGrid();
    }
  }

  // Display structured results in panel
  function displayScenarioResults(res) {
    const titleEl = document.getElementById('result-scenario-title');
    const metaEl = document.getElementById('result-scenario-meta');
    const iconEl = document.getElementById('result-status-icon');
    const durationBadge = document.getElementById('result-duration-badge');
    const summaryBanner = document.getElementById('result-summary-banner');
    const summaryText = document.getElementById('result-summary-text');
    const stepsContainer = document.getElementById('scenario-steps-container');
    const progressBar = document.getElementById('scenario-progress-bar');

    if (titleEl) titleEl.innerText = res.title || res.scenario_id;
    if (metaEl) metaEl.innerText = `Шагов: ${res.total_steps || 0} (Пройдено: ${res.passed_steps || 0}, Замечаний: ${res.warn_steps || 0}, Ошибок: ${res.failed_steps || 0})`;
    if (durationBadge) durationBadge.innerText = `${res.duration_ms || 0} ms`;

    // Overall status styling
    if (res.status === 'ok') {
      if (iconEl) iconEl.innerText = '✅';
      if (summaryBanner) summaryBanner.className = 'alert alert-success py-2 px-3 mb-3 small d-flex align-items-start gap-2';
      if (progressBar) progressBar.className = 'progress-bar bg-success';
    } else if (res.status === 'warn') {
      if (iconEl) iconEl.innerText = '⚠️';
      if (summaryBanner) summaryBanner.className = 'alert alert-warning py-2 px-3 mb-3 small d-flex align-items-start gap-2';
      if (progressBar) progressBar.className = 'progress-bar bg-warning';
    } else {
      if (iconEl) iconEl.innerText = '❌';
      if (summaryBanner) summaryBanner.className = 'alert alert-danger py-2 px-3 mb-3 small d-flex align-items-start gap-2';
      if (progressBar) progressBar.className = 'progress-bar bg-danger';
    }

    if (summaryText) summaryText.innerText = res.summary || 'Прогон завершен.';

    // Steps rendering
    if (stepsContainer && Array.isArray(res.steps)) {
      stepsContainer.innerHTML = res.steps.map((step, idx) => {
        const icon = statusIcons[step.status] || '🔹';
        const badgeBg = step.status === 'ok' ? 'bg-success' : (step.status === 'warn' ? 'bg-warning text-dark' : 'bg-danger');

        const hasData = step.data && Object.keys(step.data).length > 0;
        const dataId = `step-data-${idx}`;

        return `
          <div class="card bg-black bg-opacity-30 border border-secondary-subtle p-2 rounded">
            <div class="d-flex align-items-center justify-content-between gap-2 flex-wrap">
              <div class="d-flex align-items-center gap-2">
                <span>${icon}</span>
                <strong class="text-light small">${escapeHtml(step.name)}</strong>
              </div>
              <div class="d-flex align-items-center gap-2">
                <span class="badge ${badgeBg} small" style="font-size: 0.68rem;">${step.status.toUpperCase()}</span>
                <span class="text-secondary small" style="font-size: 0.7rem;">${step.duration_ms || 0} ms</span>
              </div>
            </div>
            <div class="text-muted small mt-1 ps-4" style="font-size: 0.78rem;">
              ${escapeHtml(step.details)}
            </div>
            ${step.recommendation ? `
              <div class="mt-1 ps-4 small text-warning" style="font-size: 0.75rem;">
                💡 <strong>Рекомендация:</strong> ${escapeHtml(step.recommendation)}
              </div>
            ` : ''}
            ${hasData ? `
              <div class="ps-4 mt-1">
                <button class="btn btn-link btn-sm p-0 text-info text-decoration-none small" style="font-size: 0.72rem;" onclick="const el=document.getElementById('${dataId}'); if(el) el.classList.toggle('d-none')">
                  🔍 Показать детали JSON
                </button>
                <div id="${dataId}" class="d-none mt-1 p-2 bg-dark rounded border border-secondary font-monospace text-light small overflow-auto" style="max-height: 140px; font-size: 0.7rem;">
                  <pre class="m-0">${escapeHtml(JSON.stringify(step.data, null, 2))}</pre>
                </div>
              </div>
            ` : ''}
          </div>
        `;
      }).join('');
    }
  }

  let isChatSubmitting = false;
  let isEventsSetup = false;

  // Extract [CHAT] and [VOICE] blocks from response and clean embedded action blocks
  function parseChatAndVoice(rawText) {
    if (!rawText) return { chatText: '', voiceText: '' };
    let text = rawText;
    let voiceText = '';

    if (text.includes('[CHAT]') || text.includes('[VOICE]')) {
      const voiceMatch = text.match(/\[VOICE\]([\s\S]*?)(?:\[\/VOICE\]|(?=\[CHAT\])|$)/i);
      if (voiceMatch) {
        voiceText = voiceMatch[1].trim();
      }
      const chatMatch = text.match(/\[CHAT\]([\s\S]*?)(?:\[\/CHAT\]|(?=\[VOICE\])|$)/i);
      if (chatMatch) {
        text = chatMatch[1].trim();
      } else {
        text = text.replace(/\[VOICE\][\s\S]*?(?:\[\/VOICE\]|(?=\[CHAT\])|$)/gi, '').trim();
      }
    }

    // Clean action blocks from chat display text
    text = text.replace(/```(?:action|json:action)[\s\S]*?```/gi, '').trim();
    text = text.replace(/\[ACTION:[\s\S]*?\]/gi, '').trim();

    // Clean remaining tags
    text = text.replace(/\[\/?CHAT\]/gi, '').replace(/\[\/?VOICE\]/gi, '').trim();
    return { chatText: text, voiceText: voiceText || text };
  }

  // Dynamic pool of questions & quick buttons loaded from external file
  let sampleQuestionsPool = [];
  let quickButtonsPool = [];

  // Asynchronously load questions and quick buttons from external file / API
  async function loadQuestionsFromConfig() {
    try {
      const res = await fetch('/api/v1/scenarios/questions');
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data.prompts) && data.prompts.length > 0) {
          sampleQuestionsPool = data.prompts;
        }
        if (Array.isArray(data.quick_buttons) && data.quick_buttons.length > 0) {
          quickButtonsPool = data.quick_buttons;
          renderQuickButtons();
        }
      }
    } catch (err) {
      console.warn('[ScenariosTab] Falling back to direct JSON load for questions:', err);
      try {
        const fallbackRes = await fetch('/html/scenarios_tab/questions.json');
        if (fallbackRes.ok) {
          const fbData = await fallbackRes.json();
          if (Array.isArray(fbData.prompts)) sampleQuestionsPool = fbData.prompts;
          if (Array.isArray(fbData.quick_buttons)) {
            quickButtonsPool = fbData.quick_buttons;
            renderQuickButtons();
          }
        }
      } catch {}
    }
    renderDynamicGreetingPrompts();
  }

  function renderQuickButtons() {
    const container = document.getElementById('chat-quick-prompts');
    if (!container || !quickButtonsPool.length) return;

    container.innerHTML = quickButtonsPool.map(btn => `
      <button class="btn btn-outline-secondary btn-sm py-0 px-2 quick-prompt-btn" style="font-size: 0.75rem;" data-prompt="${escapeHtml(btn.text)}">
        ${escapeHtml(btn.icon || '⚡')} ${escapeHtml(btn.text)}
      </button>
    `).join('');

    // Re-bind click handlers
    container.querySelectorAll('.quick-prompt-btn').forEach(btn => {
      btn.onclick = () => {
        if (isChatSubmitting) return;
        const text = btn.dataset.prompt || btn.innerText.replace(/^[^a-zA-Zа-яА-ЯёЁ]+/, '').trim();
        const chatInput = document.getElementById('scenario-chat-input');
        if (chatInput) {
          chatInput.value = text;
          submitChat();
        }
      };
    });
  }

  function renderDynamicGreetingPrompts() {
    const greetingContainer = document.getElementById('chat-greeting-prompts');
    if (!greetingContainer) return;
    if (!sampleQuestionsPool.length) return;

    // Pick 3 random distinct questions from external config
    const shuffled = [...sampleQuestionsPool].sort(() => 0.5 - Math.random());
    const selected = shuffled.slice(0, 3);

    greetingContainer.innerHTML = selected.map(q => `
      <div>• <a href="#" class="chat-prompt-link text-info text-decoration-none border-bottom border-info border-opacity-50" data-prompt="${escapeHtml(q)}">«${escapeHtml(q)}»</a></div>
    `).join('');
  }

  function getGreetingHtml() {
    const shuffled = sampleQuestionsPool.length ? [...sampleQuestionsPool].sort(() => 0.5 - Math.random()) : [];
    const selected = shuffled.slice(0, 3);
    const promptsHtml = selected.length ? selected.map(q => `
      <div>• <a href="#" class="chat-prompt-link text-info text-decoration-none border-bottom border-info border-opacity-50" data-prompt="${escapeHtml(q)}">«${escapeHtml(q)}»</a></div>
    `).join('') : `
      <div>• <a href="#" class="chat-prompt-link text-info text-decoration-none border-bottom border-info border-opacity-50" data-prompt="Какие мыши были подключены к этому компьютеру?">«Какие мыши были подключены к этому компьютеру?»</a></div>
      <div>• <a href="#" class="chat-prompt-link text-info text-decoration-none border-bottom border-info border-opacity-50" data-prompt="Покажи список сетевых портов и активных соединений">«Покажи список сетевых портов и активных соединений»</a></div>
      <div>• <a href="#" class="chat-prompt-link text-info text-decoration-none border-bottom border-info border-opacity-50" data-prompt="Проверь автозапуск и службы Windows">«Проверь автозапуск и службы Windows»</a></div>
    `;

    return `
      <div class="d-flex gap-2 mb-3">
        <div class="fs-5">🤖</div>
        <div class="bg-secondary bg-opacity-25 p-2 rounded border border-secondary-subtle small text-light flex-grow-1">
          Привет! Я интеллектуальный ассистент Test Computer. Вы можете задать мне любой вопрос о конфигурации хоста, например:
          <br><br>
          <div id="chat-greeting-prompts" class="d-flex flex-column gap-1">
            ${promptsHtml}
          </div>
          <br>
          Если для вопроса нет готового сценария, я опрошу оборудование через PowerShell/WMI, сформирую для вас ответ и **автоматически сохраню новый навык** в каталог <code>.skills/</code>.
        </div>
      </div>
    `;
  }

  // Handle Mini-Chat interaction
  function setupMiniChat() {
    const chatForm = document.getElementById('scenario-chat-form');
    const chatInput = document.getElementById('scenario-chat-input');
    const chatHistory = document.getElementById('scenario-chat-history');
    const sendBtn = document.getElementById('btn-scenario-chat-send');
    const statusInd = document.getElementById('chat-status-indicator');
    const ragCheck = document.getElementById('check-scenario-rag');

    if (!chatForm || !chatInput || !chatHistory) return;

    // Fetch and render questions dynamically from external configuration
    loadQuestionsFromConfig();

    if (ragCheck) {
      const savedRagState = localStorage.getItem('tc_scenario_use_rag');
      if (savedRagState !== null) {
        ragCheck.checked = savedRagState === 'true';
      }
      ragCheck.addEventListener('change', (e) => {
        localStorage.setItem('tc_scenario_use_rag', e.target.checked);
      });
    }

    let currentConversationId = `scenario-chat-${Date.now()}`;

    // New Session button handler
    const btnNewChat = document.getElementById('btn-scenario-new-chat');
    if (btnNewChat) {
      btnNewChat.onclick = async () => {
        try {
          await fetch('/api/v1/scenarios/chat/clear', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ conversation_id: currentConversationId, message: 'clear' }),
          });
        } catch (e) {
          console.warn('[ScenariosTab] Clear session error:', e);
        }
        currentConversationId = `scenario-chat-${Date.now()}`;
        chatHistory.innerHTML = getGreetingHtml();
        if (statusInd) statusInd.innerText = 'Новая сессия начата';
        chatInput.focus();
      };
    }

    // Quick prompt buttons & clickable prompt links
    document.querySelectorAll('.quick-prompt-btn').forEach(btn => {
      btn.onclick = () => {
        if (isChatSubmitting) return;
        const text = btn.innerText.replace(/^[^a-zA-Zа-яА-ЯёЁ]+/, '').trim();
        chatInput.value = text;
        submitChat();
      };
    });

    // Delegated click handler for inline prompt links in chat history
    chatHistory.onclick = (e) => {
      const link = e.target.closest('.chat-prompt-link');
      if (link) {
        e.preventDefault();
        e.stopPropagation();
        if (isChatSubmitting) return;
        const promptText = link.dataset.prompt || link.innerText.replace(/^[«"']|[»"']$/g, '').trim();
        if (promptText) {
          chatInput.value = promptText;
          submitChat();
        }
      }
    };

    async function submitChat() {
      const message = chatInput.value.trim();
      if (!message || isChatSubmitting) return;

      isChatSubmitting = true;
      chatInput.value = '';
      chatInput.disabled = true;
      if (sendBtn) sendBtn.disabled = true;
      if (statusInd) statusInd.innerText = '🔌 Инициализация системного зонда...';

      // Append User message
      const userMsgHtml = `
        <div class="d-flex justify-content-end mb-2">
          <div class="bg-primary text-white p-2 rounded small shadow-sm" style="max-width: 85%;">
            ${escapeHtml(message)}
          </div>
        </div>
      `;
      chatHistory.insertAdjacentHTML('beforeend', userMsgHtml);
      chatHistory.scrollTop = chatHistory.scrollHeight;

      // Handle client-side slash commands (/skills list, /skills, /help)
      const cleanCmd = message.trim().toLowerCase();
      if (cleanCmd === '/skills' || cleanCmd === '/skills list' || cleanCmd.startsWith('/skills search')) {
        try {
          const searchParam = cleanCmd.startsWith('/skills search') ? cleanCmd.replace('/skills search', '').trim() : '';
          const url = searchParam ? `/api/admin/skills?q=${encodeURIComponent(searchParam)}` : '/api/admin/skills';
          const res = await fetch(url);
          if (!res.ok) throw new Error(`HTTP ${res.status}`);
          const data = await res.json();
          const skills = data.skills || [];

          let replyMd = `### 📚 Каталог зарегистрированных навыков (.skills)\n\n`;
          if (skills.length === 0) {
            replyMd += `*Навыки не найдены.*`;
          } else {
            replyMd += `Всего доступно навыков: **${skills.length}**\n\n`;
            skills.forEach((s, idx) => {
              const pathStr = s.root_relative || s.path || `.skills/${s.name}/SKILL.md`;
              const desc = s.description_ru || s.description || 'Без описания';
              replyMd += `${idx + 1}. 🧩 **${escapeHtml(s.name)}** — *${escapeHtml(desc)}* (\`${escapeHtml(pathStr)}\`)\n`;
            });
          }

          const assistantMsgHtml = `
            <div class="d-flex gap-2 mb-3">
              <div class="fs-5">🤖</div>
              <div class="bg-secondary bg-opacity-25 p-2.5 rounded border border-secondary-subtle small text-light flex-grow-1 shadow-sm">
                <div>${formatMarkdown(replyMd)}</div>
              </div>
            </div>
          `;
          chatHistory.insertAdjacentHTML('beforeend', assistantMsgHtml);
          chatHistory.scrollTop = chatHistory.scrollHeight;
          if (statusInd) statusInd.innerText = 'Список навыков выведен';
        } catch (err) {
          const errorMsgHtml = `
            <div class="d-flex gap-2 mb-3">
              <div class="fs-5">⚠️</div>
              <div class="bg-danger bg-opacity-25 p-2 rounded border border-danger small text-danger flex-grow-1">
                Ошибка получения списка навыков: ${escapeHtml(err.message)}
              </div>
            </div>
          `;
          chatHistory.insertAdjacentHTML('beforeend', errorMsgHtml);
          chatHistory.scrollTop = chatHistory.scrollHeight;
          if (statusInd) statusInd.innerText = 'Ошибка запроса';
        } finally {
          isChatSubmitting = false;
          chatInput.disabled = false;
          if (sendBtn) sendBtn.disabled = false;
          chatInput.focus();
        }
        return;
      }

      // Append Streaming Assistant placeholder with multi-step live tracker
      const msgId = `msg-${Date.now()}-${Math.random().toString(36).substr(2, 6)}`;
      const stagesLog = [];

      const renderStagesHtml = (stages, isFinal = false) => {
        if (!stages || stages.length === 0) return '';
        const currentCount = stages.length;
        const isComplete = isFinal;
        const headerIcon = isComplete
          ? '<i class="bi bi-check-circle-fill text-success"></i>'
          : '<div class="spinner-border spinner-border-sm text-info" role="status" style="width:0.75rem;height:0.75rem;"></div>';
        const headerText = isComplete
          ? `Диагностика хоста завершена (${currentCount} шагов)`
          : `Диагностический конвейер хоста (${currentCount} шагов)...`;
        const headerClass = isComplete ? 'text-success' : 'text-info';
        const collapseClass = isComplete ? 'd-none' : '';
        const chevronIcon = isComplete ? 'bi-chevron-down' : 'bi-chevron-up';
        const lastTitle = stages[stages.length - 1]?.title || 'Зонд';

        return `
          <div class="mb-2 p-2 bg-black bg-opacity-40 border border-secondary border-opacity-30 rounded shadow-sm" id="${msgId}-stages-wrapper">
            <div class="d-flex align-items-center justify-content-between flex-wrap gap-1" onclick="const b=document.getElementById('${msgId}-stages-content'); const c=document.getElementById('${msgId}-stages-chevron'); if(b){b.classList.toggle('d-none'); if(c){c.classList.toggle('bi-chevron-down'); c.classList.toggle('bi-chevron-up');}}" style="cursor:pointer;" title="Нажмите, чтобы развернуть/свернуть детали этапов">
              <span class="${headerClass} small fw-semibold d-flex align-items-center gap-1.5" style="font-size:0.75rem;">
                ${headerIcon}
                <span>${escapeHtml(headerText)}</span>
              </span>
              <div class="d-flex align-items-center gap-1">
                <span class="badge bg-dark text-secondary border border-secondary-subtle font-monospace" style="font-size:0.63rem;">${escapeHtml(lastTitle)}</span>
                <i class="bi ${chevronIcon} text-muted" id="${msgId}-stages-chevron" style="font-size:0.65rem;"></i>
              </div>
            </div>
            <div class="mt-1.5 pt-1.5 border-top border-secondary border-opacity-25 d-flex flex-column gap-1.5 ${collapseClass}" id="${msgId}-stages-content">
              ${stages.map((st, sIdx) => {
                const isLatest = sIdx === stages.length - 1 && !isComplete;
                const icon = isLatest
                  ? '<div class="spinner-grow spinner-grow-sm text-info" style="width: 0.55rem; height: 0.55rem;" role="status"></div>'
                  : '<span class="text-success small" style="font-size:0.7rem;">✔</span>';
                const textClass = isLatest ? 'text-light fw-medium' : 'text-muted';
                return `
                  <div class="small ${textClass} d-flex flex-column ps-0.5" style="font-size: 0.74rem; line-height: 1.35;">
                    <div class="d-flex align-items-center gap-1.5">
                      <span>${icon}</span>
                      <span>${escapeHtml(st.message || '')}</span>
                    </div>
                    ${st.details ? `<div class="text-secondary ps-3 font-monospace" style="font-size: 0.68rem; word-break: break-all;">↳ ${escapeHtml(st.details)}</div>` : ''}
                    ${st.generated_prompt ? `
                      <div class="mt-1 ps-3">
                        <button class="btn btn-sm btn-outline-warning py-0 px-2 d-inline-flex align-items-center gap-1 font-monospace" type="button" onclick="event.stopPropagation(); const p=document.getElementById('${msgId}-stage-prompt-${sIdx}'); const ic=document.getElementById('${msgId}-stage-prompt-ic-${sIdx}'); if(p){p.classList.toggle('d-none'); if(ic){ic.classList.toggle('bi-chevron-down'); ic.classList.toggle('bi-chevron-up');}}" style="font-size: 0.68rem;">
                          <i class="bi bi-cpu-fill"></i>
                          <span>Показать отправленный промпт</span>
                          <i class="bi bi-chevron-down text-warning" id="${msgId}-stage-prompt-ic-${sIdx}" style="font-size:0.6rem;"></i>
                        </button>
                        <div id="${msgId}-stage-prompt-${sIdx}" class="d-none mt-1.5 p-2 bg-black bg-opacity-70 border border-warning border-opacity-40 rounded text-start" onclick="event.stopPropagation();">
                          <div class="d-flex justify-content-between align-items-center text-warning mb-1" style="font-size: 0.68rem;">
                            <span><i class="bi bi-terminal me-1"></i>Точный текст промпта, отправленный модели:</span>
                            <button class="btn btn-dark btn-sm py-0 px-1.5 text-secondary border border-secondary-subtle" type="button" onclick="navigator.clipboard.writeText(this.closest('#${msgId}-stage-prompt-${sIdx}').querySelector('pre')?.innerText || ''); this.innerText='Скопировано!'; setTimeout(()=>this.innerText='Копировать', 1500);" style="font-size: 0.65rem;">Копировать</button>
                          </div>
                          <pre class="m-0 p-1.5 bg-dark bg-opacity-75 text-light border border-secondary border-opacity-30 rounded font-monospace" style="font-size: 0.70rem; line-height: 1.35; max-height: 220px; overflow-y: auto; white-space: pre-wrap; word-break: break-word;">${escapeHtml(st.generated_prompt)}</pre>
                        </div>
                      </div>
                    ` : ''}
                  </div>
                `;
              }).join('')}
            </div>
          </div>
        `;
      };

      const initialStage = {
        stage: 'init',
        title: 'Инициализация',
        message: '🔌 Подключение к локальной подсистеме Windows API и сервисам хоста...',
        details: 'Подготовка системных интерфейсов WMI/PnP, коллекторов и контекста сессии',
      };
      stagesLog.push(initialStage);

      const loadingHtml = `
        <div class="d-flex gap-2 mb-3" id="${msgId}-container">
          <div class="fs-5">🤖</div>
          <div class="bg-secondary bg-opacity-25 p-2.5 rounded border border-secondary-subtle small text-light flex-grow-1 shadow-sm" id="${msgId}-body">
            ${renderStagesHtml(stagesLog, false)}
          </div>
        </div>
      `;
      chatHistory.insertAdjacentHTML('beforeend', loadingHtml);
      chatHistory.scrollTop = chatHistory.scrollHeight;

      try {
        const useRag = ragCheck ? ragCheck.checked : true;

        const res = await fetch('/api/v1/scenarios/chat/stream', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: message,
            conversation_id: currentConversationId,
            auto_create_skill: false,
            keep_context: true,
            use_rag: useRag,
          }),
        });

        if (!res.ok) {
          throw new Error(`Ошибка ответа сервера: HTTP ${res.status}`);
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';
        let finalData = null;
        let streamedReplyText = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });

          const lines = buffer.split('\n\n');
          buffer = lines.pop(); // Оставляем неполный хвост в буфере

          for (const line of lines) {
            const cleanLine = line.trim();
            if (!cleanLine.startsWith('data:')) continue;
            try {
              const evt = JSON.parse(cleanLine.substring(5).trim());
              if (evt.type === 'stage') {
                const lastSt = stagesLog[stagesLog.length - 1];
                if (!lastSt || lastSt.stage !== evt.stage || lastSt.message !== evt.message) {
                  stagesLog.push(evt);
                }
                if (statusInd) statusInd.innerText = evt.message || 'Обработка...';

                const bodyElem = document.getElementById(`${msgId}-body`);
                if (bodyElem) {
                  const { chatText } = parseChatAndVoice(streamedReplyText);
                  bodyElem.innerHTML = `
                    ${renderStagesHtml(stagesLog, false)}
                    ${streamedReplyText ? `<div class="chat-streaming-content mt-1.5">${formatMarkdown(chatText)}<span class="streaming-cursor">▌</span></div>` : ''}
                  `;
                  chatHistory.scrollTop = chatHistory.scrollHeight;
                }
              } else if (evt.type === 'chunk') {
                streamedReplyText += (evt.content || '');
                const bodyElem = document.getElementById(`${msgId}-body`);
                if (bodyElem) {
                  const { chatText } = parseChatAndVoice(streamedReplyText);
                  bodyElem.innerHTML = `
                    ${renderStagesHtml(stagesLog, false)}
                    <div class="chat-streaming-content mt-1.5">${formatMarkdown(chatText)}<span class="streaming-cursor">▌</span></div>
                  `;
                  chatHistory.scrollTop = chatHistory.scrollHeight;
                }
              } else if (evt.type === 'done') {
                finalData = evt;
              } else if (evt.type === 'error') {
                throw new Error(evt.error || 'Ошибка в потоке');
              }
            } catch (pErr) {
              console.warn('[ScenariosTab] SSE parse warning:', pErr);
            }
          }
        }

        if (!finalData) {
          throw new Error('Не удалось получить завершающий ответ от сервера.');
        }

        const fullReply = finalData.reply || streamedReplyText || 'Ответ получен.';
        const { chatText, voiceText } = parseChatAndVoice(fullReply);
        const formattedReply = formatMarkdown(chatText || 'Ответ получен.');

        let remediationHtml = '';
        if (Array.isArray(finalData.remediation_actions) && finalData.remediation_actions.length > 0) {
          const actionsList = finalData.remediation_actions;
          remediationHtml = `
            <div class="mt-2.5 p-2.5 bg-black bg-opacity-30 border border-warning border-opacity-50 rounded" id="remediation-container-${msgId}">
              <div class="d-flex align-items-center justify-content-between mb-2">
                <span class="fw-semibold text-warning small d-flex align-items-center gap-1">
                  <i class="bi bi-shield-check text-warning"></i> <span>Предложенные действия и исправления:</span>
                </span>
                <span class="badge bg-warning text-dark small" style="font-size: 0.68rem;">SafeOps (${actionsList.length})</span>
              </div>
              <div class="d-flex flex-column gap-1.5" id="remediation-buttons-${msgId}">
                ${actionsList.map((act, aIdx) => {
                  const isCaution = (act.risk || '').toLowerCase() === 'caution' || (act.risk || '').toLowerCase() === 'critical';
                  const badgeRisk = isCaution ? '<span class="badge bg-danger-subtle text-danger border border-danger-subtle ms-1" style="font-size:0.65rem;">Требует подтверждения</span>' : '<span class="badge bg-info-subtle text-info border border-info-subtle ms-1" style="font-size:0.65rem;">Безопасно</span>';
                  return `
                    <div class="d-flex align-items-center justify-content-between p-2 bg-dark bg-opacity-75 rounded border border-secondary border-opacity-25 gap-2 flex-wrap" id="act-row-${msgId}-${aIdx}">
                      <div class="small text-light d-flex flex-column" style="font-size: 0.78rem;">
                        <div><strong>${escapeHtml(act.title || act.action_id)}</strong>${badgeRisk}</div>
                        ${act.description ? `<span class="text-muted mt-0.5" style="font-size: 0.72rem;">${escapeHtml(act.description)}</span>` : ''}
                        ${act.execution_command ? `<code class="text-warning-emphasis bg-black bg-opacity-50 px-1 py-0.5 rounded mt-1 font-monospace" style="font-size: 0.68rem; word-break: break-all;">${escapeHtml(act.execution_command)}</code>` : ''}
                      </div>
                      <button class="btn btn-warning btn-sm py-1 px-3 d-flex align-items-center gap-1.5 shadow-sm fw-semibold btn-exec-action"
                        id="btn-act-${msgId}-${aIdx}"
                        data-msg-id="${msgId}"
                        data-action-id="${escapeHtml(act.action_id)}"
                        data-action-type="${escapeHtml(act.action_type)}"
                        data-title="${escapeHtml(act.title)}"
                        data-description="${escapeHtml(act.description)}"
                        data-target="${escapeHtml(act.target)}"
                        data-risk="${escapeHtml(act.risk)}"
                        data-command="${escapeHtml(act.execution_command)}"
                        style="font-size: 0.78rem;">
                        <i class="bi bi-play-circle-fill"></i>
                        <span>Подтвердить</span>
                      </button>
                    </div>
                  `;
                }).join('')}
              </div>
            </div>
          `;
        }

        let skillActionHtml = '';
        if (finalData.created_skill) {
          const isNew = finalData.created_skill.is_new !== false;
          const badgeTitle = isNew ? '✨ <strong>Автоматически создан навык:</strong>' : '📁 <strong>Использован существующий навык:</strong>';
          const badgeClass = isNew ? 'bg-success bg-opacity-10 border-success border-opacity-50 text-success' : 'bg-info bg-opacity-10 border-info border-opacity-50 text-info';
          skillActionHtml = `
            <div class="mt-2 p-2 ${badgeClass} border rounded small" id="skill-action-container-${msgId}">
              ${badgeTitle} <code>${escapeHtml(finalData.created_skill.path)}</code>
              <div class="text-muted small mt-1">${escapeHtml(finalData.created_skill.description_ru)}</div>
            </div>
          `;
        } else if (finalData.tool_plan) {
          skillActionHtml = `
            <div class="mt-2 pt-2 border-top border-secondary border-opacity-25 d-flex align-items-center gap-2 flex-wrap" id="skill-action-container-${msgId}">
              <button class="btn btn-outline-success btn-sm d-flex align-items-center gap-1.5 py-1 px-2.5 shadow-sm" id="btn-save-skill-${msgId}" type="button">
                <i class="bi bi-bookmark-check-fill text-success"></i>
                <span>Ответ правильный, запомнить как навык</span>
              </button>
              <button class="btn btn-outline-secondary btn-sm d-flex align-items-center gap-1.5 py-1 px-2 shadow-sm" id="btn-edit-skill-${msgId}" type="button">
                <i class="bi bi-pencil-square"></i>
                <span>Скорректировать</span>
              </button>
            </div>
            <div id="skill-edit-form-${msgId}" class="mt-2 p-2.5 bg-dark bg-opacity-50 border border-secondary-subtle rounded small d-none">
              <div class="fw-semibold text-warning mb-2"><i class="bi bi-sliders me-1"></i>Корректировка навыка перед сохранением</div>
              <div class="mb-2">
                <label class="form-label text-muted mb-1" style="font-size:0.75rem;">Заголовок навыка:</label>
                <input type="text" class="form-control form-control-sm bg-dark text-light border-secondary" id="edit-title-${msgId}" value="${escapeHtml(finalData.tool_plan.tool_title || '')}">
              </div>
              <div class="mb-2">
                <label class="form-label text-muted mb-1" style="font-size:0.75rem;">Описание (русский язык):</label>
                <textarea class="form-control form-control-sm bg-dark text-light border-secondary" id="edit-desc-${msgId}" rows="2">${escapeHtml(finalData.tool_plan.description_ru || '')}</textarea>
              </div>
              <div class="mb-2">
                <label class="form-label text-muted mb-1" style="font-size:0.75rem;">Команда проверки / скрипт:</label>
                <input type="text" class="form-control form-control-sm bg-dark text-light border-secondary font-monospace" id="edit-cmd-${msgId}" value="${escapeHtml(finalData.command_executed || finalData.tool_plan.probe_script || '')}">
              </div>
              <div class="d-flex gap-2 justify-content-end mt-2">
                <button class="btn btn-secondary btn-sm py-1 px-2" id="btn-cancel-edit-${msgId}" type="button">Отмена</button>
                <button class="btn btn-success btn-sm py-1 px-2.5" id="btn-save-edited-${msgId}" type="button">
                  <i class="bi bi-check-circle-fill me-1"></i>Сохранить скорректированный навык
                </button>
              </div>
            </div>
          `;
        }

        let metaInfoHtml = '';
        const agentsList = finalData.agents_used || [];
        const knowledgeList = finalData.knowledge_used || [];

        if (agentsList.length > 0 || knowledgeList.length > 0) {
          const totalCount = agentsList.length + knowledgeList.length;
          const metaCollapseId = `meta-details-${msgId}`;
          metaInfoHtml = `
            <div class="mt-2.5 pt-2 border-top border-secondary border-opacity-25" id="meta-container-${msgId}">
              <div class="d-flex align-items-center justify-content-between flex-wrap gap-1">
                <button class="btn btn-sm btn-link p-0 text-info text-decoration-none d-flex align-items-center gap-1.5" type="button" onclick="const el=document.getElementById('${metaCollapseId}'); const ic=document.getElementById('meta-icon-${msgId}'); if(el){el.classList.toggle('d-none'); if(ic) { ic.classList.toggle('bi-chevron-down'); ic.classList.toggle('bi-chevron-up'); }}" style="font-size: 0.75rem;">
                  <i class="bi bi-diagram-3-fill text-info"></i>
                  <span><strong>Задействованные знания и агенты</strong> (${totalCount})</span>
                  <i class="bi bi-chevron-down text-muted" id="meta-icon-${msgId}" style="font-size: 0.7rem;"></i>
                </button>
                <div class="d-flex gap-1 flex-wrap">
                  ${agentsList.map(a => `<span class="badge bg-primary bg-opacity-25 text-primary border border-primary border-opacity-25" style="font-size: 0.65rem;" title="${escapeHtml(a.role || '')}">${escapeHtml(a.icon || '🤖')} ${escapeHtml(a.name)}</span>`).slice(0, 2).join('')}
                </div>
              </div>

              <div id="${metaCollapseId}" class="d-none mt-2 p-2 bg-black bg-opacity-40 border border-secondary border-opacity-50 rounded small">
                ${agentsList.length > 0 ? `
                  <div class="mb-2">
                    <div class="text-warning fw-semibold mb-1" style="font-size: 0.73rem;">
                      <i class="bi bi-robot me-1"></i>Задействованные агенты и модули:
                    </div>
                    <div class="d-flex flex-column gap-1 ps-1">
                      ${agentsList.map(ag => `
                        <div class="d-flex align-items-start gap-1.5 text-light" style="font-size: 0.73rem;">
                          <span>${escapeHtml(ag.icon || '🤖')}</span>
                          <div>
                            <strong>${escapeHtml(ag.name)}</strong>
                            <span class="text-muted ms-1">— ${escapeHtml(ag.role || 'Системный агент')}</span>
                          </div>
                        </div>
                      `).join('')}
                    </div>
                  </div>
                ` : ''}

                ${knowledgeList.length > 0 ? `
                  <div>
                    <div class="text-info fw-semibold mb-1" style="font-size: 0.73rem;">
                      <i class="bi bi-book-half me-1"></i>Использованные источники знаний и артефакты:
                    </div>
                    <div class="d-flex flex-column gap-1 ps-1">
                      ${knowledgeList.map(kn => `
                        <div class="d-flex align-items-start gap-1.5 text-light" style="font-size: 0.73rem;">
                          <span class="badge bg-info bg-opacity-25 text-info border border-info border-opacity-25" style="font-size: 0.65rem;">${escapeHtml(kn.badge || 'База')}</span>
                          <div>
                            <strong>${escapeHtml(kn.title)}</strong>
                            <span class="text-muted ms-1">— ${escapeHtml(kn.description || '')}</span>
                          </div>
                        </div>
                      `).join('')}
                    </div>
                  </div>
                ` : ''}
              </div>
            </div>
          `;
        }

        let promptInfoHtml = '';
        const generatedPromptText = finalData.generated_prompt || (stagesLog.find(s => s.stage === 'synthesizing' && s.generated_prompt)?.generated_prompt);
        if (generatedPromptText) {
          const promptCollapseId = `prompt-details-${msgId}`;
          const promptCodeId = `prompt-code-${msgId}`;
          promptInfoHtml = `
            <div class="mt-2.5 pt-2 border-top border-secondary border-opacity-25" id="prompt-container-${msgId}">
              <div class="d-flex align-items-center justify-content-between flex-wrap gap-1">
                <button class="btn btn-sm btn-link p-0 text-warning text-decoration-none d-flex align-items-center gap-1.5" type="button" onclick="const el=document.getElementById('${promptCollapseId}'); const ic=document.getElementById('prompt-icon-${msgId}'); if(el){el.classList.toggle('d-none'); if(ic) { ic.classList.toggle('bi-chevron-down'); ic.classList.toggle('bi-chevron-up'); }}" style="font-size: 0.75rem;">
                  <i class="bi bi-cpu-fill text-warning"></i>
                  <span><strong>Сформированный промпт модели</strong></span>
                  <i class="bi bi-chevron-down text-muted" id="prompt-icon-${msgId}" style="font-size: 0.7rem;"></i>
                </button>
                <div class="d-flex align-items-center gap-1">
                  <button class="btn btn-dark btn-sm py-0 px-2 text-secondary border border-secondary-subtle d-flex align-items-center gap-1" type="button" onclick="navigator.clipboard.writeText(document.getElementById('${promptCodeId}')?.innerText || ''); const s=this.querySelector('span'); if(s){s.innerText='Скопировано!'; setTimeout(()=>s.innerText='Копировать', 1800);}" style="font-size: 0.68rem;" title="Скопировать отправленный промпт">
                    <i class="bi bi-clipboard"></i>
                    <span>Копировать</span>
                  </button>
                </div>
              </div>

              <div id="${promptCollapseId}" class="d-none mt-2 p-2.5 bg-black bg-opacity-60 border border-warning border-opacity-40 rounded">
                <div class="d-flex align-items-center justify-content-between text-warning small mb-1.5" style="font-size: 0.72rem;">
                  <span><i class="bi bi-terminal me-1"></i>Точный текст запроса, отправленный языковой модели:</span>
                  <span class="badge bg-warning bg-opacity-10 text-warning border border-warning border-opacity-25 font-monospace" style="font-size: 0.65rem;">${generatedPromptText.length} симв.</span>
                </div>
                <pre class="m-0 p-2 bg-dark bg-opacity-75 text-light border border-secondary border-opacity-30 rounded font-monospace small" id="${promptCodeId}" style="font-size: 0.72rem; line-height: 1.4; max-height: 280px; overflow-y: auto; white-space: pre-wrap; word-break: break-word;">${escapeHtml(generatedPromptText)}</pre>
              </div>
            </div>
          `;
        }

        const trainingActionHtml = `
          <div class="mt-2.5 pt-2 border-top border-secondary border-opacity-25 d-flex align-items-center justify-content-between flex-wrap gap-2" id="training-save-container-${msgId}">
            <button class="btn btn-outline-info btn-sm d-flex align-items-center gap-1.5 py-1 px-2.5 shadow-sm btn-save-training-qa" id="btn-save-training-${msgId}" type="button" title="Сохранить пару вопрос-ответ в базу данных Test Computer для RAG и последующего обучения (тюнинга) модели">
              <i class="bi bi-mortarboard-fill text-info"></i>
              <span>Сохранить ответ для обучения модели</span>
            </button>
            <span class="text-muted" style="font-size: 0.68rem;"><i class="bi bi-database me-1"></i>data/tc/approved_responses</span>
          </div>
        `;

        const bodyElem = document.getElementById(`${msgId}-body`);
        if (bodyElem) {
          bodyElem.innerHTML = `
            ${renderStagesHtml(stagesLog, true)}
            <div>${formattedReply}</div>
            ${remediationHtml}
            ${skillActionHtml}
            ${trainingActionHtml}
            ${metaInfoHtml}
            ${promptInfoHtml}
          `;
        }
        chatHistory.scrollTop = chatHistory.scrollHeight;

        // Wire up save response for training & RAG button
        const btnSaveTraining = document.getElementById(`btn-save-training-${msgId}`);
        if (btnSaveTraining) {
          btnSaveTraining.onclick = async () => {
            btnSaveTraining.disabled = true;
            btnSaveTraining.innerHTML = `<div class="spinner-border spinner-border-sm text-info me-1" role="status"></div><span>Сохранение...</span>`;
            try {
              const res = await fetch('/api/v1/scenarios/save-approved-response', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  user_id: 'tc_admin',
                  query: message,
                  chat_text: chatText,
                  voice_text: voiceText || '',
                  system_context: {
                    command_executed: finalData.command_executed || '',
                    tool_plan: finalData.tool_plan || null,
                    platform: 'Windows'
                  },
                  tags: ['tc', 'diagnostics', 'training']
                }),
              });
              if (!res.ok) throw new Error(`HTTP ${res.status}`);
              const resData = await res.json();
              const container = document.getElementById(`training-save-container-${msgId}`);
              if (container) {
                container.innerHTML = `
                  <div class="p-1.5 px-2.5 bg-success bg-opacity-10 border border-success border-opacity-50 text-success rounded small d-flex align-items-center gap-1.5 w-100 shadow-sm">
                    <i class="bi bi-check-circle-fill text-success"></i>
                    <span><strong>Успешно:</strong> ответ сохранён для обучения модели и RAG (<code>data/tc/approved_responses</code>)</span>
                  </div>
                `;
              }
              if (statusInd) statusInd.innerText = 'Ответ сохранён в базу для обучения модели!';
            } catch (saveErr) {
              console.error('[ScenariosTab] Error saving training QA:', saveErr);
              btnSaveTraining.disabled = false;
              btnSaveTraining.innerHTML = `<i class="bi bi-exclamation-triangle-fill text-danger me-1"></i><span>Ошибка сохранения. Повторить</span>`;
            }
          };
        }


        // Wire up manual save & inline edit logic
        if (!finalData.created_skill && finalData.tool_plan) {
          const saveBtn = document.getElementById(`btn-save-skill-${msgId}`);
          const editBtn = document.getElementById(`btn-edit-skill-${msgId}`);
          const editForm = document.getElementById(`skill-edit-form-${msgId}`);
          const cancelEditBtn = document.getElementById(`btn-cancel-edit-${msgId}`);
          const saveEditedBtn = document.getElementById(`btn-save-edited-${msgId}`);

          const executeSave = async (payload) => {
            const container = document.getElementById(`skill-action-container-${msgId}`);
            if (saveBtn) saveBtn.disabled = true;
            if (saveEditedBtn) saveEditedBtn.disabled = true;
            if (saveBtn) saveBtn.innerHTML = `<div class="spinner-border spinner-border-sm text-success me-1" role="status"></div><span>Сохранение...</span>`;

            try {
              const saveRes = await fetch('/api/v1/scenarios/save-skill', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
              });
              if (!saveRes.ok) throw new Error(`HTTP ${saveRes.status}`);
              const savedData = await saveRes.json();
              if (container) {
                container.innerHTML = `
                  <div class="p-2 bg-success bg-opacity-10 border border-success border-opacity-50 text-success rounded small w-100">
                    ✨ <strong>Навык успешно сохранён:</strong> <code>${escapeHtml(savedData.path)}</code>
                    <div class="text-muted small mt-1">${escapeHtml(savedData.description_ru)}</div>
                  </div>
                `;
              }
              if (editForm) editForm.classList.add('d-none');
              if (statusInd) statusInd.innerText = `Навык '${savedData.name}' сохранён!`;
            } catch (saveErr) {
              console.error('[ScenariosTab] Error saving skill:', saveErr);
              if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.innerHTML = `<i class="bi bi-exclamation-triangle-fill text-danger me-1"></i><span>Ошибка. Повторить</span>`;
              }
              if (saveEditedBtn) saveEditedBtn.disabled = false;
            }
          };

          if (saveBtn) {
            saveBtn.addEventListener('click', () => {
              executeSave({
                tool_name: finalData.tool_plan.tool_name,
                tool_title: finalData.tool_plan.tool_title,
                description_ru: finalData.tool_plan.description_ru,
                probe_type: finalData.tool_plan.probe_type || 'powershell',
                collector_name: finalData.tool_plan.collector_name,
                probe_script: finalData.tool_plan.probe_script,
                instructions: finalData.tool_plan.instructions,
                command_executed: finalData.command_executed,
              });
            });
          }

          if (editBtn && editForm) {
            editBtn.addEventListener('click', () => {
              editForm.classList.toggle('d-none');
            });
          }

          if (cancelEditBtn && editForm) {
            cancelEditBtn.addEventListener('click', () => {
              editForm.classList.add('d-none');
            });
          }

          if (saveEditedBtn) {
            saveEditedBtn.addEventListener('click', () => {
              const editedTitle = document.getElementById(`edit-title-${msgId}`)?.value || finalData.tool_plan.tool_title;
              const editedDesc = document.getElementById(`edit-desc-${msgId}`)?.value || finalData.tool_plan.description_ru;
              const editedCmd = document.getElementById(`edit-cmd-${msgId}`)?.value || finalData.command_executed;

              executeSave({
                tool_name: finalData.tool_plan.tool_name,
                tool_title: editedTitle,
                description_ru: editedDesc,
                probe_type: finalData.tool_plan.probe_type || 'powershell',
                collector_name: finalData.tool_plan.collector_name,
                probe_script: editedCmd,
                instructions: finalData.tool_plan.instructions,
                command_executed: editedCmd,
              });
            });
          }
        }

        // Wire up remediation action execution buttons
        if (Array.isArray(finalData.remediation_actions) && finalData.remediation_actions.length > 0) {
          const remContainer = document.getElementById(`remediation-container-${msgId}`);
          if (remContainer) {
            remContainer.querySelectorAll('.btn-exec-action').forEach(btn => {
              btn.addEventListener('click', async () => {
                const actionId = btn.dataset.actionId;
                const actionType = btn.dataset.actionType;
                const title = btn.dataset.title;
                const description = btn.dataset.description;
                const target = btn.dataset.target;
                const risk = btn.dataset.risk;
                const command = btn.dataset.command;

                // Confirm if risk is caution or critical
                const isRisky = (risk || '').toLowerCase() === 'caution' || (risk || '').toLowerCase() === 'critical';
                if (isRisky) {
                  const ok = confirm(`Подтвердите применение исправления:\n\n«${title}»\n\nКоманда: ${command || target}`);
                  if (!ok) return;
                }

                btn.disabled = true;
                btn.innerHTML = `<div class="spinner-border spinner-border-sm text-warning" role="status"></div><span>Применение...</span>`;
                if (statusInd) statusInd.innerText = `Применение '${title}'...`;

                try {
                  const execRes = await fetch('/api/v1/scenarios/execute-fix', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                      action_id: actionId,
                      action_type: actionType,
                      title: title,
                      description: description,
                      target: target,
                      risk: risk,
                      execution_command: command,
                      confirmed_by_user: true,
                    }),
                  });

                  if (!execRes.ok) throw new Error(`HTTP ${execRes.status}`);
                  const resData = await execRes.json();
                  if (resData.success) {
                    btn.className = 'btn btn-success btn-sm py-1 px-3 d-flex align-items-center gap-1.5 shadow-sm';
                    btn.innerHTML = `<i class="bi bi-check-circle-fill"></i><span>Подтверждено и выполнено</span>`;
                    if (statusInd) statusInd.innerText = `Действие '${title}' успешно выполнено!`;
                  } else {
                    btn.disabled = false;
                    btn.className = 'btn btn-danger btn-sm py-0.5 px-2.5 d-flex align-items-center gap-1 shadow-sm';
                    btn.innerHTML = `<i class="bi bi-exclamation-triangle-fill"></i><span>Ошибка</span>`;
                    btn.title = resData.error_message || resData.message;
                    if (statusInd) statusInd.innerText = `Ошибка: ${resData.error_message || resData.message}`;
                  }
                } catch (exErr) {
                  console.error('[ScenariosTab] Error executing fix:', exErr);
                  btn.disabled = false;
                  btn.className = 'btn btn-outline-danger btn-sm py-0.5 px-2.5 d-flex align-items-center gap-1 shadow-sm';
                  btn.innerHTML = `<i class="bi bi-arrow-repeat"></i><span>Повторить</span>`;
                  if (statusInd) statusInd.innerText = `Сбой: ${exErr.message}`;
                }
              });
            });
          }
        }

        if (statusInd) statusInd.innerText = 'Ответ сформирован';
      } catch (err) {
        console.error('[ScenariosTab] Chat error:', err);
        const bodyElem = document.getElementById(`${msgId}-body`);
        if (bodyElem) {
          bodyElem.innerHTML = `
            <div class="text-danger">
              <i class="bi bi-exclamation-triangle-fill me-1"></i>Ошибка: ${escapeHtml(err.message)}
            </div>
          `;
        }
        chatHistory.scrollTop = chatHistory.scrollHeight;
        if (statusInd) statusInd.innerText = 'Ошибка запроса';
      } finally {
        isChatSubmitting = false;
        chatInput.disabled = false;
        if (sendBtn) sendBtn.disabled = false;
        chatInput.focus();
      }
    }

    chatForm.onsubmit = (e) => {
      e.preventDefault();
      submitChat();
    };
  }

  // Setup UI event handlers
  function setupEvents() {
    if (isEventsSetup) return;
    isEventsSetup = true;

    // Quick Check Button
    const btnQuick = document.getElementById('btn-run-quick-check');
    if (btnQuick) {
      btnQuick.onclick = () => runScenario('quick_check');
    }

    // Run All Button
    const btnAll = document.getElementById('btn-run-all-scenarios');
    if (btnAll) {
      btnAll.onclick = () => runScenario('all');
    }

    // Refresh List Button
    const btnRefresh = document.getElementById('btn-scenario-refresh-list');
    if (btnRefresh) {
      btnRefresh.onclick = () => loadScenarios();
    }

    // Close Results Button
    const btnCloseRes = document.getElementById('btn-close-result-panel');
    if (btnCloseRes) {
      btnCloseRes.onclick = () => {
        const panel = document.getElementById('scenario-result-panel');
        if (panel) panel.style.display = 'none';
      };
    }

    // Category Filter Buttons
    const filterContainer = document.getElementById('scenario-category-filters');
    if (filterContainer) {
      filterContainer.querySelectorAll('button').forEach(btn => {
        btn.onclick = () => {
          filterContainer.querySelectorAll('button').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          currentFilter = btn.getAttribute('data-filter') || 'all';
          renderScenariosGrid();
        };
      });
    }

    setupMiniChat();
  }

  // Public initialization entrypoint
  window.initScenariosTab = async function () {
    console.log('[ScenariosTab] Initializing Scenarios & Test Computer Tab...');
    setupEvents();
    loadQuestionsFromConfig();
    await loadScenarios();
    console.log('[ScenariosTab] Scenarios tab ready.');
  };
  window.initChatTab = window.initScenariosTab;

  // Auto-init if container exists
  if (document.getElementById('scenarios-cards-container') || document.getElementById('scenario-chat-history')) {
    window.initScenariosTab();
  }
})();
