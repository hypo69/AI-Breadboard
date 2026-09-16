// Wikipedia Research & Multi-Model Benchmark Laboratory WebGUI JS
(function () {
  'use strict';

  console.log('[WikiLab] Initializing Wikipedia Research Tab JS...');

  async function checkHealth() {
    try {
      const res = await fetch('/api/v1/wikipedia-research/health');
      if (res.ok) {
        const data = await res.json();
        alert(`Wikipedia Research API статус: ${data.status.toUpperCase()} (приложение: ${data.app})`);
      } else {
        alert(`Ошибка API: HTTP ${res.status}`);
      }
    } catch (e) {
      alert(`Не удалось связаться с API: ${e.message}`);
    }
  }

  function getSelectedLanguages() {
    const checkboxes = document.querySelectorAll('.wiki-lang-check:checked');
    const langs = [];
    checkboxes.forEach((cb) => langs.push(cb.value));
    return langs.length > 0 ? langs : ['en', 'ru'];
  }

  function getSelectedModels() {
    const checkboxes = document.querySelectorAll('.wiki-model-check:checked');
    const models = [];
    checkboxes.forEach((cb) => models.push(cb.value));
    return models.length > 0 ? models : ['gemini', 'foundry'];
  }

  function formatSentimentBadge(val) {
    if (val === undefined || val === null) return '<span class="text-muted">n/a</span>';
    const num = parseFloat(val);
    if (num > 0.05) {
      return `<span class="wiki-badge-pos">+${num.toFixed(2)}</span>`;
    } else if (num < -0.05) {
      return `<span class="wiki-badge-neg">${num.toFixed(2)}</span>`;
    }
    return `<span class="wiki-badge-neu">${num.toFixed(2)}</span>`;
  }

  function setLoading(loading, text = 'Выполняется сбор и анализ...') {
    const spinner = document.getElementById('wiki-loading-spinner');
    const loadingText = document.getElementById('wiki-loading-text');
    const resultsSec = document.getElementById('wiki-results-section');
    if (spinner) {
      if (loading) {
        spinner.classList.remove('d-none');
        if (loadingText) loadingText.textContent = text;
        if (resultsSec) resultsSec.classList.add('d-none');
      } else {
        spinner.classList.add('d-none');
        if (resultsSec) resultsSec.classList.remove('d-none');
      }
    }
  }

  function renderInsights(insights) {
    const container = document.getElementById('wiki-insights-container');
    if (!container) return;
    if (!insights || insights.length === 0) {
      container.innerHTML = '<div class="text-muted small">Нет выявленных значимых расхождений.</div>';
      return;
    }
    let html = '<ul class="list-unstyled mb-0 d-flex flex-column gap-2">';
    insights.forEach((ins) => {
      html += `<li class="d-flex align-items-start gap-2 text-light"><i class="bi bi-check-circle-fill text-info mt-1"></i> <span>${ins}</span></li>`;
    });
    html += '</ul>';
    container.innerHTML = html;
  }

  async function runExperimentA() {
    const topicInput = document.getElementById('wiki-topic-input');
    const topic = topicInput ? topicInput.value.trim() : 'Israel–Gaza war';
    const languages = getSelectedLanguages();
    const model = document.getElementById('wiki-primary-model')?.value || 'gemini';

    setLoading(true, `Эксперимент A: сбор статей по теме "${topic}" и анализ моделью ${model}...`);

    try {
      const response = await fetch('/api/v1/wikipedia-research/experiment/languages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic, languages, model }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${await response.text()}`);
      }

      const report = await response.json();
      renderExperimentAResults(report);
    } catch (err) {
      alert(`Ошибка выполнения Эксперимента A: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  function renderExperimentAResults(report) {
    const titleEl = document.getElementById('wiki-results-title');
    if (titleEl) {
      titleEl.innerHTML = `<i class="bi bi-translate"></i> Experiment A: Кросс-языковое сравнение темы «${report.topic}» (Модель: ${report.model_used})`;
    }

    renderInsights(report.cross_language_insights);

    const tableContainer = document.getElementById('wiki-results-table-container');
    if (!tableContainer) return;

    let html = `
      <table class="wiki-table">
        <thead>
          <tr>
            <th>Язык</th>
            <th>Статья</th>
            <th>Тональность</th>
            <th>Субъективность</th>
            <th>Критика</th>
            <th>Похвала</th>
            <th>Неопределенность</th>
            <th>Спорные тезисы</th>
            <th>Фрейминг</th>
            <th>Слов</th>
          </tr>
        </thead>
        <tbody>
    `;

    (report.metrics_summary_table || []).forEach((row) => {
      html += `
        <tr>
          <td><strong class="text-info">${row.lang.toUpperCase()}</strong></td>
          <td><a href="${row.url}" target="_blank" class="text-light text-decoration-underline">${row.title}</a></td>
          <td>${formatSentimentBadge(row.sentiment)}</td>
          <td><span class="text-warning">${row.subjectivity.toFixed(2)}</span></td>
          <td><span class="text-danger">${row.criticism.toFixed(2)}</span></td>
          <td><span class="text-success">${row.praise.toFixed(2)}</span></td>
          <td><span class="text-primary">${row.uncertainty.toFixed(2)}</span></td>
          <td class="text-center"><span class="badge bg-secondary">${row.claims_count}</span></td>
          <td><span class="badge bg-dark border border-secondary text-info">${row.framing}</span></td>
          <td class="text-muted small">${row.word_count.toLocaleString()}</td>
        </tr>
      `;
    });

    html += `</tbody></table>`;
    tableContainer.innerHTML = html;
  }

  async function runExperimentB() {
    const topicInput = document.getElementById('wiki-topic-input');
    const topic = topicInput ? topicInput.value.trim() : 'Israel–Gaza war';
    const languages = getSelectedLanguages();
    const models = getSelectedModels();

    setLoading(true, `Эксперимент B: сопоставление интерпретаций моделями [${models.join(', ')}]...`);

    try {
      const response = await fetch('/api/v1/wikipedia-research/experiment/models', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic, languages, models }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${await response.text()}`);
      }

      const report = await response.json();
      renderExperimentBResults(report);
    } catch (err) {
      alert(`Ошибка выполнения Эксперимента B: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  function renderExperimentBResults(report) {
    const titleEl = document.getElementById('wiki-results-title');
    if (titleEl) {
      titleEl.innerHTML = `<i class="bi bi-cpu"></i> Experiment B: Мульти-модельный бенчмарк интерпретации «${report.topic}»`;
    }

    renderInsights(report.model_alignment_insights);

    const tableContainer = document.getElementById('wiki-results-table-container');
    if (!tableContainer) return;

    let html = `
      <table class="wiki-table">
        <thead>
          <tr>
            <th>Языковой раздел</th>
    `;

    report.models.forEach((mod) => {
      html += `<th>Модель: ${mod}</th>`;
    });

    html += `
          </tr>
        </thead>
        <tbody>
    `;

    report.languages.forEach((lang) => {
      html += `<tr><td><strong class="text-warning">${lang.toUpperCase()}</strong></td>`;
      report.models.forEach((mod) => {
        const sentiment = report.sentiment_grid?.[lang]?.[mod];
        const res = report.matrix?.[lang]?.[mod];
        const framing = res?.metrics?.framing_tone || 'n/a';
        html += `
          <td>
            <div class="d-flex flex-column gap-1">
              <div>${formatSentimentBadge(sentiment)}</div>
              <small class="text-muted" style="font-size: 0.75rem;">(${framing})</small>
            </div>
          </td>
        `;
      });
      html += `</tr>`;
    });

    html += `</tbody></table>`;
    tableContainer.innerHTML = html;
  }

  function bindEvents() {
    const btnHealth = document.getElementById('btn-wiki-health');
    if (btnHealth) btnHealth.onclick = checkHealth;

    const btnExpA = document.getElementById('btn-run-exp-a');
    if (btnExpA) btnExpA.onclick = runExperimentA;

    const btnExpB = document.getElementById('btn-run-exp-b');
    if (btnExpB) btnExpB.onclick = runExperimentB;
  }

  window.initWikipediaResearchTab = function () {
    console.log('[WikiLab] initWikipediaResearchTab triggered');
    bindEvents();
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bindEvents);
  } else {
    bindEvents();
  }
})();
