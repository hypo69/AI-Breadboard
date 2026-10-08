/**
 * =============================================================================
 * Process Name: Windows Disk Speed Tab - Main Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом бенчмарка дисковой подсистемы (DiskSpd).
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/webgui/disk_speed_tab/main.js?v=20261004_v1" type="module"></script>
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: windows/api/webgui/disk_speed_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-08 02:00:00
 * =============================================================================
 */

const registerTabPoller = window.registerTabPoller || function() {};
const isTabActive = window.isTabActive || function() { return true; };

let mbChartInstance = null;
let currentTaskId = null;
let pollTimer = null;
let cachedTargets = [];
let lastResult = null;

async function initDiskSpeedTab() {
  if (isInitialized) return;
  isInitialized = true;
  initChart();
  setupEventListeners();
  if (window.isTabActive ? window.isTabActive('tab-disk-speed') : false) {
    await checkEngineStatus();
    await loadTargets();
    await loadHistory();
  }
}

async function activateDiskSpeedTab() {
  await checkEngineStatus();
  await loadTargets();
  await loadHistory();
}

window.activateDiskSpeedTab = activateDiskSpeedTab;

/**
 * Проверка статуса утилиты DiskSpd.
 */
async function checkEngineStatus() {
  try {
    const res = await fetch('/api/v1/storage/benchmark/engine');
    if (!res.ok) return;
    const data = await res.json();
    const badge = document.getElementById('bench-engine-badge');
    if (badge) {
      if (data.available) {
        badge.className = 'badge bg-success-subtle text-success border border-success-subtle px-2 py-1';
        badge.innerHTML = '<i class="bi bi-check-circle-fill"></i> DiskSpd Ready';
      } else {
        badge.className = 'badge bg-warning-subtle text-warning border border-warning-subtle px-2 py-1';
        badge.innerHTML = '<i class="bi bi-exclamation-triangle"></i> DiskSpd не установлен';
      }
    }
  } catch (err) {
    console.debug('[DiskSpeed] Ошибка проверки движка:', err);
  }
}

/**
 * Загрузка списка доступных дисков и разделов.
 */
async function loadTargets() {
  try {
    const res = await fetch('/api/v1/storage/benchmark/targets');
    if (!res.ok) return;
    cachedTargets = await res.json();

    const select = document.getElementById('bench-drive-select');
    if (!select) return;

    select.innerHTML = '';
    cachedTargets.forEach(t => {
      const opt = document.createElement('option');
      opt.value = t.drive_letter;
      const tag = t.is_system ? ' [Системный]' : '';
      opt.textContent = `${t.drive_letter} (${t.label || t.drive_letter})${tag} — ${t.free_gb} ГБ свободно`;
      select.appendChild(opt);
    });

    updateDriveDetails();
  } catch (err) {
    console.error('[DiskSpeed] Ошибка загрузки списка накопителей:', err);
  }
}

/**
 * Обновление информации о выбранном диске и пути безопасного файла.
 */
function updateDriveDetails() {
  const select = document.getElementById('bench-drive-select');
  if (!select) return;
  const drive = select.value;
  const target = cachedTargets.find(t => t.drive_letter === drive);

  const fsEl = document.getElementById('bench-drive-fs');
  const freeEl = document.getElementById('bench-drive-free');
  const pathEl = document.getElementById('bench-safe-filepath');
  const summaryDisk = document.getElementById('bench-summary-disk');

  if (target) {
    if (fsEl) fsEl.textContent = `ФС: ${target.fs_type}`;
    if (freeEl) freeEl.textContent = `Свободно: ${target.free_gb} ГБ`;
    if (pathEl) pathEl.textContent = `${target.recommended_dir}\\diskspd-test.dat`;
    if (summaryDisk) summaryDisk.textContent = `${target.drive_letter} (${target.fs_type})`;
  }
}

/**
 * Настройка событий элементов управления.
 */
function setupEventListeners() {
  const driveSelect = document.getElementById('bench-drive-select');
  if (driveSelect) {
    driveSelect.addEventListener('change', updateDriveDetails);
  }

  const refreshBtn = document.getElementById('bench-refresh-targets-btn');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', async () => {
      await loadTargets();
      if (window.toast) window.toast.info('Обновлено', 'Список накопителей обновлен');
    });
  }

  const runAllBtn = document.getElementById('bench-run-all-btn');
  if (runAllBtn) {
    runAllBtn.addEventListener('click', () => {
      startBenchmark(['seq1m_q8t1', 'seq1m_q1t1', 'rnd4k_q32t16', 'rnd4k_q1t1']);
    });
  }

  const cancelBtn = document.getElementById('bench-cancel-btn');
  if (cancelBtn) {
    cancelBtn.addEventListener('click', cancelBenchmark);
  }

  // Одиночные кнопки профилей
  const pMap = {
    'bench-run-seq1m-q8': ['seq1m_q8t1'],
    'bench-run-seq1m-q1': ['seq1m_q1t1'],
    'bench-run-rnd4k-q32': ['rnd4k_q32t16'],
    'bench-run-rnd4k-q1': ['rnd4k_q1t1'],
  };

  Object.entries(pMap).forEach(([btnId, profiles]) => {
    const btn = document.getElementById(btnId);
    if (btn) {
      btn.addEventListener('click', () => startBenchmark(profiles));
    }
  });

  const copyMdBtn = document.getElementById('bench-copy-md-btn');
  if (copyMdBtn) {
    copyMdBtn.addEventListener('click', copyResultsAsMarkdown);
  }
}

/**
 * Запуск тестирования производительности.
 * @param {Array<string>} profiles - Список профилей для выполнения.
 */
async function startBenchmark(profiles) {
  const driveSelect = document.getElementById('bench-drive-select');
  const sizeSelect = document.getElementById('bench-size-select');
  const durSelect = document.getElementById('bench-duration-select');
  const typeRadio = document.querySelector('input[name="bench-type-radio"]:checked');

  const payload = {
    target_drive: driveSelect ? driveSelect.value : 'C:',
    file_size_mb: sizeSelect ? parseInt(sizeSelect.value, 10) : 256,
    duration_sec: durSelect ? parseInt(durSelect.value, 10) : 3,
    test_type: typeRadio ? typeRadio.value : 'both',
    profiles: profiles,
    disable_cache: true,
    delete_test_file: true,
  };

  setUiRunning(true);

  const summarySize = document.getElementById('bench-summary-size');
  if (summarySize) summarySize.textContent = `${payload.file_size_mb} MB`;

  try {
    const res = await fetch('/api/v1/storage/benchmark/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Не удалось запустить бенчмарк');
    }

    const task = await res.json();
    currentTaskId = task.task_id;
    pollBenchmarkTask();
  } catch (err) {
    setUiRunning(false);
    if (window.toast) {
      window.toast.error('Ошибка старта', err.message);
    } else {
      alert(`Ошибка: ${err.message}`);
    }
  }
}

function pollBenchmarkTask() {
  if (pollTimer) clearInterval(pollTimer);

  pollTimer = setInterval(async () => {
    if (!currentTaskId) {
      clearInterval(pollTimer);
      return;
    }
    if (window.isTabActive && !window.isTabActive('tab-disk-speed')) return;

    try {
      const res = await fetch(`/api/v1/storage/benchmark/status/${currentTaskId}`);
      if (!res.ok) return;

      const task = await res.json();
      updateProgress(task.progress_percent, task.destination);

      if (task.status === 'completed') {
        clearInterval(pollTimer);
        setUiRunning(false);
        if (window.toast) window.toast.success('Тест завершен', 'Результаты бенчмарка готовы');
        await loadLatestHistoryResult();
        await loadHistory();
      } else if (task.status === 'failed') {
        clearInterval(pollTimer);
        setUiRunning(false);
        if (window.toast) window.toast.error('Ошибка теста', task.error_message || 'Тестирование завершилось с ошибкой');
      } else if (task.status === 'cancelled') {
        clearInterval(pollTimer);
        setUiRunning(false);
        if (window.toast) window.toast.warning('Отменено', 'Тест был отменен');
      }
    } catch (e) {
      console.debug('[DiskSpeed] Ошибка опроса задачи:', e);
    }
  }, 1000);
}

/**
 * Отмена запущенного бенчмарка.
 */
async function cancelBenchmark() {
  if (!currentTaskId) return;
  try {
    await fetch(`/api/v1/storage/benchmark/cancel/${currentTaskId}`, { method: 'POST' });
    if (window.toast) window.toast.info('Отмена', 'Запрос на остановку отправлен...');
  } catch (err) {
    console.error('[DiskSpeed] Ошибка отмены:', err);
  }
}

/**
 * Управление состоянием элементов UI во время теста.
 * @param {boolean} isRunning - Флаг активности теста.
 */
function setUiRunning(isRunning) {
  const runAllBtn = document.getElementById('bench-run-all-btn');
  const cancelBtn = document.getElementById('bench-cancel-btn');
  const progressWrapper = document.getElementById('bench-progress-wrapper');
  const statusBadge = document.getElementById('bench-status-badge');

  if (runAllBtn) runAllBtn.disabled = isRunning;
  if (cancelBtn) {
    if (isRunning) {
      cancelBtn.classList.remove('d-none');
    } else {
      cancelBtn.classList.add('d-none');
    }
  }

  if (progressWrapper) {
    if (isRunning) {
      progressWrapper.classList.remove('d-none');
    } else {
      progressWrapper.classList.add('d-none');
    }
  }

  if (statusBadge) {
    if (isRunning) {
      statusBadge.className = 'badge bg-warning text-dark font-monospace';
      statusBadge.textContent = 'Идет тестирование...';
    } else {
      statusBadge.className = 'badge bg-secondary font-monospace';
      statusBadge.textContent = 'Готов к тесту';
    }
  }
}

/**
 * Обновление полосы прогресса.
 * @param {number} pct - Процент выполнения.
 * @param {string} msg - Сообщение фазы.
 */
function updateProgress(pct, msg) {
  const bar = document.getElementById('bench-progress-bar');
  const pctEl = document.getElementById('bench-progress-pct');
  const msgEl = document.getElementById('bench-progress-msg');

  const val = Math.max(0, Math.min(100, pct || 0));
  if (bar) bar.style.width = `${val}%`;
  if (pctEl) pctEl.textContent = `${val}%`;
  if (msgEl && msg) msgEl.textContent = msg;
}

/**
 * Загрузка последнего результата и заполнение таблицы CDM.
 */
async function loadLatestHistoryResult() {
  try {
    const res = await fetch('/api/v1/storage/benchmark/history?limit=1');
    if (!res.ok) return;
    const items = await res.json();
    if (!items || items.length === 0) return;

    const latest = items[0];
    lastResult = latest;

    const summaryTime = document.getElementById('bench-summary-time');
    if (summaryTime) summaryTime.textContent = latest.created_at;

    // SEQ1M Q8T1
    updateRowValues('seq1m_q8t1', latest.seq1m_read_mb_s, latest.seq1m_write_mb_s, '-- / --', '-- µs');
    // RND4K Q32T16
    updateRowValues('rnd4k_q32t16', latest.rnd4k_read_mb_s, latest.rnd4k_write_mb_s, `${Math.round(latest.rnd4k_read_iops)} / ${Math.round(latest.rnd4k_write_iops)}`, '-- µs');

    updateChartData([
      { label: 'SEQ1M Q8T1', read: latest.seq1m_read_mb_s, write: latest.seq1m_write_mb_s },
      { label: 'RND4K Q32T16', read: latest.rnd4k_read_mb_s, write: latest.rnd4k_write_mb_s },
    ]);
  } catch (err) {
    console.debug('[DiskSpeed] Ошибка загрузки свежих результатов:', err);
  }
}

/**
 * Обновление строки таблицы CDM.
 */
function updateRowValues(rowKey, readMb, writeMb, iops, lat) {
  const rEl = document.getElementById(`val-${rowKey}-read`);
  const wEl = document.getElementById(`val-${rowKey}-write`);
  const iopsEl = document.getElementById(`val-${rowKey}-iops`);
  const latEl = document.getElementById(`val-${rowKey}-lat`);

  if (rEl) rEl.textContent = (readMb || 0).toFixed(2);
  if (wEl) wEl.textContent = (writeMb || 0).toFixed(2);
  if (iopsEl) iopsEl.textContent = iops;
  if (latEl) latEl.textContent = lat;
}

/**
 * Инициализация графика Chart.js.
 */
function initChart() {
  const ctx = document.getElementById('bench-mb-chart');
  if (!ctx || typeof Chart === 'undefined') return;

  if (mbChartInstance) {
    mbChartInstance.destroy();
  }

  mbChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['SEQ1M Q8T1', 'SEQ1M Q1T1', 'RND4K Q32T16', 'RND4K Q1T1'],
      datasets: [
        {
          label: 'Read (MB/s)',
          data: [0, 0, 0, 0],
          backgroundColor: 'rgba(13, 202, 240, 0.75)',
          borderColor: '#0dcaf0',
          borderWidth: 1,
        },
        {
          label: 'Write (MB/s)',
          data: [0, 0, 0, 0],
          backgroundColor: 'rgba(255, 193, 7, 0.75)',
          borderColor: '#ffc107',
          borderWidth: 1,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: '#334155' },
          ticks: { color: '#94a3b8' },
        },
        x: {
          grid: { display: false },
          ticks: { color: '#94a3b8' },
        },
      },
      plugins: {
        legend: { labels: { color: '#f8fafc' } },
      },
    },
  });
}

/**
 * Обновление данных графика.
 */
function updateChartData(points) {
  if (!mbChartInstance) return;
  const labels = points.map(p => p.label);
  const reads = points.map(p => p.read || 0);
  const writes = points.map(p => p.write || 0);

  mbChartInstance.data.labels = labels;
  mbChartInstance.data.datasets[0].data = reads;
  mbChartInstance.data.datasets[1].data = writes;
  mbChartInstance.update();
}

/**
 * Загрузка истории тестирования.
 */
async function loadHistory() {
  try {
    const res = await fetch('/api/v1/storage/benchmark/history?limit=20');
    if (!res.ok) return;
    const list = await res.json();

    const countBadge = document.getElementById('bench-history-count');
    if (countBadge) countBadge.textContent = `${list.length} записей`;

    const tbody = document.getElementById('bench-history-tbody');
    if (!tbody) return;

    if (!list || list.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-3">История пуста</td></tr>';
      return;
    }

    tbody.innerHTML = '';
    list.forEach(item => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td class="text-white">${item.created_at}</td>
        <td><span class="badge bg-secondary">${item.target}</span></td>
        <td class="text-info fw-bold">${item.seq1m_read_mb_s.toFixed(0)} <span class="text-muted">/</span> <span class="text-warning">${item.seq1m_write_mb_s.toFixed(0)} MB/s</span></td>
        <td class="text-success">${Math.round(item.rnd4k_read_iops)} <span class="text-muted">/</span> ${Math.round(item.rnd4k_write_iops)}</td>
        <td class="text-end">
          <button class="btn btn-outline-danger btn-sm py-0 px-1 bench-delete-btn" data-id="${item.id}" title="Удалить">
            <i class="bi bi-trash"></i>
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });

    tbody.querySelectorAll('.bench-delete-btn').forEach(btn => {
      btn.addEventListener('click', async e => {
        e.stopPropagation();
        const id = btn.getAttribute('data-id');
        if (confirm('Удалить эту запись из истории?')) {
          await deleteHistoryItem(id);
        }
      });
    });
  } catch (err) {
    console.debug('[DiskSpeed] Ошибка загрузки истории:', err);
  }
}

/**
 * Удаление записи из истории.
 */
async function deleteHistoryItem(id) {
  try {
    await fetch(`/api/v1/storage/benchmark/history/${id}`, { method: 'DELETE' });
    await loadHistory();
    if (window.toast) window.toast.info('Удалено', 'Запись удалена из базы данных');
  } catch (err) {
    console.error('[DiskSpeed] Ошибка удаления:', err);
  }
}

/**
 * Копирование результатов в формате Markdown таблицы.
 */
function copyResultsAsMarkdown() {
  const s8r = document.getElementById('val-seq1m_q8t1-read')?.textContent || '0';
  const s8w = document.getElementById('val-seq1m_q8t1-write')?.textContent || '0';
  const s1r = document.getElementById('val-seq1m_q1t1-read')?.textContent || '0';
  const s1w = document.getElementById('val-seq1m_q1t1-write')?.textContent || '0';
  const r32r = document.getElementById('val-rnd4k_q32t16-read')?.textContent || '0';
  const r32w = document.getElementById('val-rnd4k_q32t16-write')?.textContent || '0';
  const r1r = document.getElementById('val-rnd4k_q1t1-read')?.textContent || '0';
  const r1w = document.getElementById('val-rnd4k_q1t1-write')?.textContent || '0';

  const disk = document.getElementById('bench-drive-select')?.value || 'C:';

  const md = [
    `### AI-Breadboard DiskSpd Benchmark (${disk})`,
    '',
    '| Профиль | Read (MB/s) | Write (MB/s) |',
    '| :--- | :---: | :---: |',
    `| **SEQ1M Q8T1** | ${s8r} MB/s | ${s8w} MB/s |`,
    `| **SEQ1M Q1T1** | ${s1r} MB/s | ${s1w} MB/s |`,
    `| **RND4K Q32T16** | ${r32r} MB/s | ${r32w} MB/s |`,
    `| **RND4K Q1T1** | ${r1r} MB/s | ${r1w} MB/s |`,
    '',
    `*Дата замера: ${new Date().toLocaleString('ru-RU')}*`,
  ].join('\n');

  navigator.clipboard.writeText(md).then(() => {
    if (window.toast) window.toast.success('Скопировано', 'Таблица скопирована в буфер обмена');
  });
}

// Регистрация поллера при активной вкладке tab-disk-speed
registerTabPoller('tab-disk-speed', checkEngineStatus, 15000, { immediate: false });

// Автоматический запуск при загрузке
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initDiskSpeedTab);
} else {
  initDiskSpeedTab();
}

export { initDiskSpeedTab };
