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
  const statusBadge = document.getElementById('bm-status-badge');

  // Автозаполнение модели при смене провайдера
  if (providerSelect) {
    providerSelect.addEventListener('change', () => {
      const p = providerSelect.value;
      if (p === 'gemini') modelInput.value = 'gemini-2.5-flash';
      else if (p === 'ollama') modelInput.value = 'llama3.2:latest';
      else if (p === 'foundry') modelInput.value = 'phi-3.5-mini';
      else if (p === 'onnx') modelInput.value = 'directml-phi3';
    });
  }

  // Запуск бенчмарка
  if (runBtn) {
    runBtn.addEventListener('click', async () => {
      runBtn.disabled = true;
      runBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Тестирование...';
      if (statusBadge) {
        statusBadge.className = 'badge bg-warning-subtle text-warning border border-warning-subtle';
        statusBadge.textContent = 'Выполняется замер...';
      }

      try {
        const payload = {
          provider: providerSelect ? providerSelect.value : 'gemini',
          model_name: modelInput ? modelInput.value : 'gemini-2.5-flash',
          prompt: promptInput ? promptInput.value : 'Тестовый запрос',
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
            statusBadge.textContent = 'Успешно завершен';
          }
          if (window.toast) {
            window.toast.success('Бенчмарк завершен', `Скорость: ${data.tokens_per_second} t/s | TTFT: ${data.ttft_ms} ms`);
          }
        } else {
          if (statusBadge) {
            statusBadge.className = 'badge bg-danger-subtle text-danger border border-danger-subtle';
            statusBadge.textContent = 'Ошибка';
          }
          if (window.toast) {
            window.toast.error('Ошибка бенчмарка', data.error_message || 'Не удалось выполнить замер');
          }
        }
      } catch (err) {
        if (statusBadge) {
          statusBadge.className = 'badge bg-danger-subtle text-danger border border-danger-subtle';
          statusBadge.textContent = 'Ошибка сети';
        }
        if (window.toast) {
          window.toast.error('Сбой запроса', err.message);
        }
      } finally {
        runBtn.disabled = false;
        runBtn.innerHTML = '<i class="bi bi-play-fill fs-6"></i> Запустить тест';
        await loadHistory();
      }
    });
  }

  // Обновление истории
  if (refreshBtn) {
    refreshBtn.addEventListener('click', loadHistory);
  }

  // Загрузка начальной истории
  await loadHistory();
}

function updateCards(data) {
  const ttftEl = document.getElementById('bm-card-ttft');
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
      tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted py-3">История бенчмарков пуста. Нажмите "Запустить тест".</td></tr>';
      return;
    }

    tbody.innerHTML = items.slice().reverse().map(item => {
      const timeStr = item.timestamp ? new Date(item.timestamp * 1000).toLocaleTimeString() : '—';
      const statusBadge = item.success
        ? '<span class="badge bg-success-subtle text-success">OK</span>'
        : `<span class="badge bg-danger-subtle text-danger" title="${item.error_message || ''}">Ошибка</span>`;

      return `
        <tr>
          <td><span class="text-muted small">${timeStr}</span></td>
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
