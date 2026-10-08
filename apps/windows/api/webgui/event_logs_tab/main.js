/**
 * =============================================================================
 * Process Name: Windows Event Logs Tab - Main Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля Windows Event Logs
 *   с интеграцией аналитического пайплайна Log Intelligence (EDA -> Gate -> RAG).
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/webgui/event_logs_tab/main.js?v=20261006_v1" type="module"></script>
 *
 *   JavaScript Import:
 *     import { initEventLogsTab } from '/windows/api/webgui/event_logs_tab/main.js';
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: windows/api/webgui/event_logs_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-08 02:00:00
 * =============================================================================
 */

const registerTabPoller = window.registerTabPoller || function() {};
const isTabActive = window.isTabActive || (() => true);

let isInitialized = false;
let eventsList = [];

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

export async function fetchEventLogsSummary() {
  if (!isTabActive('tab-event-logs')) return;
  const channelSelect = document.getElementById('el-channel-select');
  const channel = channelSelect ? channelSelect.value : 'System';

  try {
    const res = await fetch(`/api/event-logs/events?channel=${encodeURIComponent(channel)}&limit=100&hours=24`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const entries = await res.json();
    renderEventLogs(entries);
    // Also fetch intelligence profile in background to update Health Score & Redundancy
    fetchIntelligenceProfile(channel, false);
  } catch (err) {
    console.warn('[EventLogs] Ошибка получения событий:', err);
  }
}

async function fetchIntelligenceProfile(channel, showBanner = true) {
  try {
    const res = await fetch(`/api/event-logs/intelligence/profile?channel=${encodeURIComponent(channel)}&hours=24&limit=100`);
    if (!res.ok) return;
    const data = await res.json();

    const healthEl = document.getElementById('el-health-score');
    const redEl = document.getElementById('el-redundancy-pct');

    if (data.profile) {
      if (healthEl) {
        const score = Math.round(data.profile.health_score ?? 100);
        healthEl.textContent = `${score}/100`;
        healthEl.className = `fs-4 fw-bold mt-1 font-monospace ${score >= 80 ? 'text-success' : (score >= 50 ? 'text-warning' : 'text-danger')}`;
      }
      if (redEl) {
        const rPct = (data.profile.redundancy_ratio_pct ?? 0).toFixed(1);
        redEl.textContent = `${rPct}%`;
      }
    }

    if (showBanner && data.decision) {
      renderIntelligenceBanner(data);
    }
  } catch (err) {
    console.debug('[EventLogs] Фоновый сбор аналитики:', err);
  }
}

function renderIntelligenceBanner(data) {
  const banner = document.getElementById('el-intel-banner');
  const title = document.getElementById('el-intel-title');
  const strat = document.getElementById('el-strategy-badge');
  const rationale = document.getElementById('el-intel-rationale');
  const rec = document.getElementById('el-intel-recommendation');
  const chunks = document.getElementById('el-chunks-badge');

  if (!banner) return;

  if (title) title.textContent = `Log Intelligence: Канал ${data.channel || 'System'}`;
  if (strat) strat.textContent = (data.decision.strategy || 'SNAPSHOT').toUpperCase();
  if (rationale) rationale.textContent = data.decision.rationale || '';
  if (rec) rec.innerHTML = `<i class="bi bi-lightbulb me-1"></i><strong>Рекомендация:</strong> ${escapeHtml(data.decision.recommended_llm_action || 'Система в штатном режиме.')}`;
  if (chunks) chunks.textContent = `${data.decision.chunks_generated || 0} RAG chunks`;

  banner.classList.remove('d-none');
}

export async function runFullAudit() {
  const channelSelect = document.getElementById('el-channel-select');
  const channel = channelSelect ? channelSelect.value : 'System';

  try {
    const res = await fetch(`/api/event-logs/intelligence/audit?channel=${encodeURIComponent(channel)}&hours=24&limit=200`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderIntelligenceBanner({
      channel: data.channel,
      decision: {
        strategy: data.strategy,
        rationale: data.strategy_rationale,
        recommended_llm_action: data.recommended_llm_action,
        chunks_generated: data.top_clusters ? data.top_clusters.length : 0,
      }
    });
  } catch (err) {
    console.warn('[EventLogs] Ошибка аудита:', err);
  }
}

export async function runRAGSearch() {
  const input = document.getElementById('el-rag-query-input');
  const channelSelect = document.getElementById('el-channel-select');
  const resultsCard = document.getElementById('el-rag-results-card');
  const resultsBody = document.getElementById('el-rag-results-body');

  if (!input || !resultsCard || !resultsBody) return;
  const query = input.value.trim();
  if (!query) return;

  resultsBody.innerHTML = `<div class="text-center py-3 text-muted"><div class="spinner-border spinner-border-sm text-info me-2"></div>Поиск в Adaptive Log RAG...</div>`;
  resultsCard.classList.remove('d-none');

  try {
    const channel = channelSelect ? channelSelect.value : '';
    const res = await fetch(`/api/event-logs/intelligence/search?query=${encodeURIComponent(query)}&top_k=5&channel=${encodeURIComponent(channel)}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const results = await res.json();

    if (!results || results.length === 0) {
      resultsBody.innerHTML = `<div class="text-center py-3 text-muted">По запросу "<em>${escapeHtml(query)}</em>" совпадений не найдено.</div>`;
      return;
    }

    resultsBody.innerHTML = results.map(r => `
      <div class="p-2 mb-2 rounded bg-black border border-secondary">
        <div class="d-flex justify-content-between align-items-center mb-1">
          <strong class="text-info">${escapeHtml(r.title || 'Документ RAG')}</strong>
          <span class="badge bg-secondary font-monospace">Relevance: ${Math.round((r.relevance_score || 0) * 100)}%</span>
        </div>
        <div class="small text-light font-monospace" style="word-break: break-word;">${escapeHtml(r.content || '')}</div>
        <div class="small text-muted mt-1 font-monospace"><i class="bi bi-tag me-1"></i>Стратегия: ${escapeHtml(r.strategy || 'Adaptive')} • ${escapeHtml(r.created_at || '')}</div>
      </div>
    `).join('');
  } catch (err) {
    resultsBody.innerHTML = `<div class="text-danger small p-2">Ошибка поиска: ${escapeHtml(err.message)}</div>`;
  }
}

function renderEventLogs(entries) {
  eventsList = entries || [];

  const critEl = document.getElementById('el-critical-count');
  const errEl = document.getElementById('el-error-count');

  let crits = 0;
  let errs = 0;

  eventsList.forEach(e => {
    const l = (e.level || '').toLowerCase();
    if (l.includes('crit')) crits++;
    else if (l.includes('err')) errs++;
  });

  if (critEl) critEl.textContent = crits;
  if (errEl) errEl.textContent = errs;

  applyEventFilters();
}

function applyEventFilters() {
  const tbody = document.getElementById('el-tbody');
  const searchInput = document.getElementById('el-search-input');
  const badge = document.getElementById('el-table-badge');

  if (!tbody) return;

  const query = (searchInput ? searchInput.value : '').toLowerCase().trim();

  const filtered = eventsList.filter(e => {
    if (!query) return true;
    const msgMatch = (e.message || '').toLowerCase().includes(query);
    const provMatch = (e.provider_name || e.provider || '').toLowerCase().includes(query);
    const idMatch = String(e.event_id || e.id || '').includes(query);
    return msgMatch || provMatch || idMatch;
  });

  if (badge) badge.textContent = `${filtered.length} из ${eventsList.length} событий`;

  if (filtered.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-4">События не найдены</td></tr>';
    return;
  }

  tbody.innerHTML = filtered.slice(0, 150).map(e => {
    const level = (e.level || 'Information').toLowerCase();
    let badgeClass = 'bg-secondary';
    if (level.includes('crit')) badgeClass = 'bg-danger text-white';
    else if (level.includes('err')) badgeClass = 'bg-danger text-white';
    else if (level.includes('warn')) badgeClass = 'bg-warning text-dark';
    else if (level.includes('info')) badgeClass = 'bg-info text-dark';

    return `
      <tr>
        <td><span class="badge ${badgeClass}">${escapeHtml(e.level || 'Info')}</span></td>
        <td class="text-muted small font-monospace">${escapeHtml(e.time_created || e.timestamp || '-')}</td>
        <td class="fw-semibold text-light small">${escapeHtml(e.provider_name || e.provider || 'Windows')}</td>
        <td class="font-monospace text-warning small">${escapeHtml(String(e.event_id || e.id || '-'))}</td>
        <td class="text-light small" style="max-width: 500px; word-break: break-word;">${escapeHtml(e.message || '-')}</td>
      </tr>
    `;
  }).join('');
}

export function initEventLogsTab() {
  if (isInitialized) return;
  isInitialized = true;

  const refreshBtn = document.getElementById('el-refresh-btn');
  if (refreshBtn) refreshBtn.addEventListener('click', fetchEventLogsSummary);

  const channelSelect = document.getElementById('el-channel-select');
  if (channelSelect) channelSelect.addEventListener('change', fetchEventLogsSummary);

  const searchInput = document.getElementById('el-search-input');
  if (searchInput) searchInput.addEventListener('input', applyEventFilters);

  const analyzeBtn = document.getElementById('el-intel-analyze-btn');
  if (analyzeBtn) analyzeBtn.addEventListener('click', () => {
    const chan = channelSelect ? channelSelect.value : 'System';
    fetchIntelligenceProfile(chan, true);
  });

  const auditBtn = document.getElementById('el-intel-audit-btn');
  if (auditBtn) auditBtn.addEventListener('click', runFullAudit);

  const ragBtn = document.getElementById('el-rag-search-btn');
  if (ragBtn) ragBtn.addEventListener('click', runRAGSearch);

  const ragInput = document.getElementById('el-rag-query-input');
  if (ragInput) ragInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') runRAGSearch();
  });

  const bannerCloseBtn = document.getElementById('el-intel-close-btn');
  if (bannerCloseBtn) bannerCloseBtn.addEventListener('click', () => {
    const banner = document.getElementById('el-intel-banner');
    if (banner) banner.classList.add('d-none');
  });

  const ragCloseBtn = document.getElementById('el-rag-close-btn');
  if (ragCloseBtn) ragCloseBtn.addEventListener('click', () => {
    const card = document.getElementById('el-rag-results-card');
    if (card) card.classList.add('d-none');
  });

  registerTabPoller('tab-event-logs', fetchEventLogsSummary, 15000, { immediate: true });
  if (isTabActive('tab-event-logs')) {
    fetchEventLogsSummary();
  }
}

export function activateEventLogsTab() {
  fetchEventLogsSummary();
}

window.initEventLogsTab = initEventLogsTab;
window.activateEventLogsTab = activateEventLogsTab;

// Автоинициализация: загрузчик вкладок только подключает скрипт
if (document.getElementById('el-tbody') && isTabActive('tab-event-logs')) {
  initEventLogsTab();
}
