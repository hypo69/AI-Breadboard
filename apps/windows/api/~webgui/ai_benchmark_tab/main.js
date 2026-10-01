/**
 * =============================================================================
 * Process Name: Windows Ai Benchmark Tab - Main Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля main.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/~webgui/ai_benchmark_tab/main.js?v=20261001_v1" type="module"></script>
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: windows/api/~webgui/ai_benchmark_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-01 13:04:40
 * =============================================================================
 */

/**
 * ai_benchmark_tab/main.js — Контроллер вкладки AI Inference Benchmark
 */

export async function initAiBenchmarkTab() {
  const runBtn = document.getElementById('bm-run-btn');
  const refreshBtn = document.getElementById('bm-refresh-history-btn');
  const providerSelect = document.getElementById('bm-provider-select');
  const modelInput = document.getElementById('bm-model-input');
  const tokensInput = document.getElementById('bm-tokens-input');
  const tempInput = document.getElementById('bm-temp-input');
  const promptInput = document.getElementById('bm-prompt-input');
  const statusBadge = document.getElementById('bm-status-badgei18n.t('auto__if_providerselect_providerselect_addeventlistener__df8f21')change', () => {
      const p = providerSelect.value;
      if (p === 'gemini') modelInput.value = 'gemini-2.5-flash';
      else if (p === 'ollama') modelInput.value = 'llama3.2:latest';
      else if (p === 'foundry') modelInput.value = 'phi-3.5-mini';
      else if (p === 'onnx') modelInput.value = 'directml-phi3i18n.t('auto__if_runbtn_runbtn_addeventlistener__c4d4ca')click', async () => {
      runBtn.disabled = true;
      runBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Тестирование...';
      if (statusBadge) {
        statusBadge.className = 'badge bg-warning-subtle text-warning border border-warning-subtle';
        statusBadge.textContent = i18n.t('auto___f7abff');
      }

      try {
        const payload = {
          provider: providerSelect ? providerSelect.value : 'gemini',
          model_name: modelInput ? modelInput.value : 'gemini-2.5-flash',
          prompt: promptInput ? promptInput.value : i18n.t('auto___387814'),
          max_tokens: tokensInput ? parseInt(tokensInput.value, 10) || 150 : 150,
          temperature: tempInput ? parseFloat(tempInput.value) || 0.7 : 0.7,
        };

        const res = await fetch('/api/windows/benchmark/ai', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });

        const data = await res.json();
        if (res.ok && data.success) {
          updateCards(data);
          if (statusBadge) {
            statusBadge.className = 'badge bg-success-subtle text-success border border-success-subtle';
            statusBadge.textContent = i18n.t('auto___b718ea');
          }
          if (window.toast) {
            window.toast.success(i18n.t('auto___983c1c'), `Скорость: ${data.tokens_per_second} t/s | TTFT: ${data.ttft_ms} ms`);
          }
        } else {
          if (statusBadge) {
            statusBadge.className = 'badge bg-danger-subtle text-danger border border-danger-subtle';
            statusBadge.textContent = i18n.t('auto___72aecd');
          }
          if (window.toast) {
            window.toast.error(i18n.t('auto___f29ff0'), data.error_message || i18n.t('auto___f6377e'));
          }
        }
      } catch (err) {
        if (statusBadge) {
          statusBadge.className = 'badge bg-danger-subtle text-danger border border-danger-subtle';
          statusBadge.textContent = i18n.t('auto___c00aca');
        }
        if (window.toast) {
          window.toast.error(i18n.t('auto___089486'), err.message);
        }
      } finally {
        runBtn.disabled = false;
        runBtn.innerHTML = '<i class="bi bi-play-fill fs-6"></i> Запустить тестi18n.t('auto__await_loadhistory_if_refreshbtn_refreshbtn_addeventlistener__909824')clicki18n.t('auto__loadhistory_await_loadhistory_function_updatecards_data_const_ttftel_document_getelementbyid__9cba8e')bm-card-ttft');
  const tpsEl = document.getElementById('bm-card-tps');
  const totalEl = document.getElementById('bm-card-total');
  const tokensEl = document.getElementById('bm-card-tokens');

  if (ttftEl) ttftEl.textContent = `${data.ttft_ms} ms`;
  if (tpsEl) tpsEl.textContent = `${data.tokens_per_second} t/s`;
  if (totalEl) totalEl.textContent = `${data.total_time_ms} ms`;
  if (tokensEl) tokensEl.textContent = `${data.prompt_tokens} / ${data.completion_tokens}`;
}

async function loadHistory() {
  const tbody = document.getElementById('bm-history-tbody');
  if (!tbody) return;

  try {
    const res = await fetch('/api/windows/benchmark/ai/history');
    const items = await res.json();

    if (!Array.isArray(items) || items.length === 0) {
      tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted py-3i18n.t('auto___9f84ae')Запустить тест".</td></tr>';
      return;
    }

    tbody.innerHTML = items.slice().reverse().map(item => {
      const timeStr = item.timestamp ? new Date(item.timestamp * 1000).toLocaleTimeString() : '—';
      const statusBadge = item.success
        ? '<span class="badge bg-success-subtle text-success">OK</span>'
        : `<span class="badge bg-danger-subtle text-danger" title="${item.error_message || ''}i18n.t('auto__span_return_tr_td_span_class__613956')text-muted small">${timeStr}</span></td>
          <td><span class="badge bg-secondary-subtle text-info">${item.provider}</span></td>
          <td class="fw-semibold text-white">${item.model_name}</td>
          <td><span class="text-info">${item.ttft_ms} ms</span></td>
          <td><span class="text-success fw-bold">${item.tokens_per_second} t/s</span></td>
          <td>${item.total_time_ms} ms</td>
          <td><span class="text-muted small">${item.prompt_tokens} in / ${item.completion_tokens} out</span></td>
          <td>${statusBadge}</td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-danger text-center py-2">Ошибка загрузки истории: ${err.message}</td></tr>`;
  }
}

// Автозапуск при инициализации вкладки
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initAiBenchmarkTab);
} else {
  initAiBenchmarkTab();
}
