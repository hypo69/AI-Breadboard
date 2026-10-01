/**
 * =============================================================================
 * Process Name: Windows Web - App Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля app.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/telemetry_research/web/app.js?v=20261001_v1" type="module"></script>
 *
 * File: app.js
 * Project: ai-breadboard
 * Package: windows/telemetry_research/web
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-01 13:04:40
 * =============================================================================
 */

/**
 * Клиентский контроллер Web GUI Исследования и Мониторинга Телеметрии Windows.
 * Поддерживает живой мониторинг telemetry.db, глубокий анализ и AI-ассистента с визуализацией.
 */

let currentReport = null;
let researchCharts = {};
let liveCharts = {};
let aiDynamicChart = null;
let currentPage = 1;
const pageSize = 20;
let totalPages = 1;
let searchQuery = "";
let liveRefreshTimer = null;

document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  bindEvents();
  initAiChat();
  loadSources();
  initLiveCharts();
  loadCurrentState();
  setupAutoRefresh();
  runResearch();
});

/**
 * Инициализация переключения вкладок.
 */
function initTabs() {
  const tabBtns = document.querySelectorAll(".tab-btn");
  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      tabBtns.forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach((c) => c.classList.remove("active"));

      btn.classList.add("active");
      const targetId = btn.getAttribute("data-tab");
      const targetContent = document.getElementById(targetId);
      if (targetContent) {
        targetContent.classList.add("active");
      }

      if (targetId === "tab-current") {
        loadCurrentState();
      } else if (targetId === "tab-records") {
        loadRecords();
      }
    });
  });
}

/**
 * Привязка событий элементов управления.
 */
function bindEvents() {
  const btnRun = document.getElementById("btn-run");
  if (btnRun) {
    btnRun.onclick = () => runResearch();
  }

  const selectSource = document.getElementById("select-source");
  if (selectSource) {
    selectSource.onchange = () => {
      runResearch();
      loadCurrentState();
    };
  }

  const btnDashboard = document.getElementById("btn-dashboard");
  if (btnDashboard) {
    btnDashboard.onclick = () => openHtmlDashboard();
  }

  const btnJson = document.getElementById("btn-json");
  if (btnJson) {
    btnJson.onclick = () => downloadJsonReport();
  }

  const btnRefreshCurrent = document.getElementById("btn-refresh-current");
  if (btnRefreshCurrent) {
    btnRefreshCurrent.onclick = () => loadCurrentState();
  }

  const rangeSelect = document.getElementById("current-range-select");
  if (rangeSelect) {
    rangeSelect.onchange = () => loadCurrentState();
  }

  const autoRefreshToggle = document.getElementById("auto-refresh-toggle");
  if (autoRefreshToggle) {
    autoRefreshToggle.onchange = () => setupAutoRefresh();
  }

  const searchInput = document.getElementById("input-search");
  if (searchInput) {
    searchInput.onkeydown = (e) => {
      if (e.key === "Enter") {
        searchQuery = searchInput.value.trim();
        currentPage = 1;
        loadRecords();
      }
    };
  }

  const prevBtn = document.getElementById("btn-prev-page");
  if (prevBtn) {
    prevBtn.onclick = () => {
      if (currentPage > 1) {
        currentPage--;
        loadRecords();
      }
    };
  }

  const nextBtn = document.getElementById("btn-next-page");
  if (nextBtn) {
    nextBtn.onclick = () => {
      if (currentPage < totalPages) {
        currentPage++;
        loadRecords();
      }
    };
  }
}

/**
 * Инициализация обработчиков AI-чата и панели ввода.
 */
function initAiChat() {
  const form = document.getElementById("ai-query-form");
  const input = document.getElementById("ai-query-input");
  const btnClear = document.getElementById("btn-ai-clear");
  const btnClose = document.getElementById("btn-ai-close");
  const responseCard = document.getElementById("ai-response-card");

  if (input) {
    input.addEventListener("input", () => {
      if (btnClear) {
        btnClear.style.display = input.value.length > 0 ? "block" : "none";
      }
    });

    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        submitAiQuery(input.value.trim());
      }
    });
  }

  if (btnClear && input) {
    btnClear.addEventListener("click", () => {
      input.value = "";
      btnClear.style.display = "none";
      input.focus();
    });
  }

  if (form && input) {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      submitAiQuery(input.value.trim());
    });
  }

  if (btnClose && responseCard) {
    btnClose.addEventListener("click", () => {
      responseCard.style.display = "none";
    });
  }

  // Привязка быстрых чипов
  const chips = document.querySelectorAll(".prompt-chip");
  chips.forEach((chip) => {
    chip.addEventListener("click", () => {
      const q = chip.getAttribute("data-query");
      if (q) {
        if (input) input.value = q;
        submitAiQuery(q);
      }
    });
  });
}

/**
 * Отправка запроса к AI-ассистенту телеметрии.
 */
async function submitAiQuery(queryText) {
  if (!queryText) return;

  const input = document.getElementById("ai-query-input");
  const btnSend = document.getElementById("btn-ai-send");
  const btnText = document.getElementById("btn-ai-send-text");
  const spinner = document.getElementById("btn-ai-spinner");
  const responseCard = document.getElementById("ai-response-card");
  const selectSource = document.getElementById("select-source");
  const sourcePath = selectSource ? selectSource.value : null;

  // Установка состояния загрузки
  if (btnSend) btnSend.disabled = true;
  if (btnText) btnText.style.display = "none";
  if (spinner) spinner.style.display = "inline-block";

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: queryText,
        source_path: sourcePath || null,
      }),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    renderAiResponse(queryText, data);
  } catch (err) {
    console.error("Ошибка при выполнении AI запроса:", err);
    if (responseCard) {
      responseCard.style.display = "block";
      const replyBody = document.getElementById("ai-reply-body");
      if (replyBody) {
        replyBody.innerHTML = `<div style="color: var(--accent-red); padding: 10px;">⚠️ Ошибка соединения с сервером AI-ассистента: ${err.message}</div>`;
      }
    }
  } finally {
    if (btnSend) btnSend.disabled = false;
    if (btnText) btnText.style.display = "inline";
    if (spinner) spinner.style.display = "none";
  }
}

/**
 * Рендеринг ответа AI-ассистента, графиков Chart.js и выполненных SQL.
 */
function renderAiResponse(queryText, data) {
  const responseCard = document.getElementById("ai-response-card");
  const titleEl = document.getElementById("ai-response-title");
  const chartWrapper = document.getElementById("ai-chart-wrapper");
  const chartTitle = document.getElementById("ai-chart-title");
  const metricsRow = document.getElementById("ai-metrics-row");
  const replyBody = document.getElementById("ai-reply-body");
  const sqlDetails = document.getElementById("ai-sql-details");
  const sqlCode = document.getElementById("ai-sql-code");
  const followupRow = document.getElementById("ai-followup-row");
  const followupChips = document.getElementById("ai-followup-chips");

  if (!responseCard) return;
  responseCard.style.display = "block";

  if (titleEl) {
    titleEl.textContent = queryText.length > 60 ? queryText.substring(0, 60) + "..." : queryText;
  }

  // 1. Форматирование текста ответа
  if (replyBody) {
    replyBody.innerHTML = formatMarkdownToHtml(data.reply || "");
  }

  // 2. Рендеринг динамического графика Chart.js
  if (data.chart && data.chart.datasets && data.chart.datasets.length > 0) {
    chartWrapper.style.display = "block";
    if (chartTitle) chartTitle.textContent = data.chart.title || "📈 Визуализация данных";

    renderDynamicAiChart(data.chart);
  } else {
    chartWrapper.style.display = "none";
    if (aiDynamicChart) {
      aiDynamicChart.destroy();
      aiDynamicChart = null;
    }
  }

  // 3. Метрики KPI
  if (data.metrics_summary && Object.keys(data.metrics_summary).length > 0) {
    metricsRow.style.display = "flex";
    metricsRow.innerHTML = "";
    Object.entries(data.metrics_summary).forEach(([k, v]) => {
      const pill = document.createElement("div");
      pill.className = "ai-metric-pill";
      const cleanKey = k.replace(/_/g, " ");
      pill.innerHTML = `<span>${cleanKey}:</span> <strong>${v}</strong>`;
      metricsRow.appendChild(pill);
    });
  } else {
    metricsRow.style.display = "none";
  }

  // 4. SQL-запросы
  if (data.sql_queries && data.sql_queries.length > 0 && data.sql_queries[0]) {
    sqlDetails.style.display = "block";
    if (sqlCode) {
      sqlCode.textContent = data.sql_queries.join("\n\n");
    }
  } else {
    sqlDetails.style.display = "none";
  }

  // 5. Быстрые уточняющие вопросы
  if (data.quick_followups && data.quick_followups.length > 0) {
    followupRow.style.display = "flex";
    if (followupChips) {
      followupChips.innerHTML = "";
      data.quick_followups.forEach((fText) => {
        const btn = document.createElement("button");
        btn.className = "prompt-chip";
        btn.textContent = fText;
        btn.onclick = () => {
          const input = document.getElementById("ai-query-input");
          if (input) input.value = fText;
          submitAiQuery(fText);
        };
        followupChips.appendChild(btn);
      });
    }
  } else {
    followupRow.style.display = "none";
  }

  // Прокрутка к ответу
  responseCard.scrollIntoView({ behavior: "smooth", block: "start" });
}

/**
 * Динамический рендеринг любого типа графика через Chart.js.
 */
function renderDynamicAiChart(chartConfig) {
  const canvas = document.getElementById("chart-ai-dynamic");
  if (!canvas) return;

  if (aiDynamicChart) {
    aiDynamicChart.destroy();
    aiDynamicChart = null;
  }

  const ctx = canvas.getContext("2d");
  const chartType = chartConfig.type || "line";

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 500 },
    plugins: {
      legend: {
        position: chartType === "doughnut" || chartType === "pie" ? "right" : "top",
        labels: { color: "#94a3b8", font: { size: 12 } },
      },
      tooltip: {
        backgroundColor: "#131b2e",
        titleColor: "#38bdf8",
        bodyColor: "#f1f5f9",
        borderColor: "#23304d",
        borderWidth: 1,
      },
    },
  };

  if (chartType === "line" || chartType === "bar") {
    options.scales = {
      x: {
        grid: { color: "rgba(35, 48, 77, 0.4)" },
        ticks: { color: "#94a3b8", maxRotation: 0, autoSkip: true, maxTicksLimit: 10 },
      },
      y: {
        grid: { color: "rgba(35, 48, 77, 0.4)" },
        ticks: { color: "#94a3b8" },
      },
    };
  }

  aiDynamicChart = new Chart(ctx, {
    type: chartType,
    data: {
      labels: chartConfig.labels,
      datasets: chartConfig.datasets,
    },
    options: options,
  });
}

/**
 * Простой и надежный Markdown парсер для форматирования ответов AI.
 */
function formatMarkdownToHtml(md) {
  if (!md) return "";
  let html = md
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  // Заголовки
  html = html.replace(/^### (.*$)/gim, "<h3>$1</h3>");
  html = html.replace(/^#### (.*$)/gim, "<h4>$1</h4>");
  html = html.replace(/^## (.*$)/gim, "<h2>$1</h2>");
  html = html.replace(/^# (.*$)/gim, "<h1>$1</h1>");

  // Жирный шрифт и курсив
  html = html.replace(/\*\*(.*?)\*\*/gim, "<strong>$1</strong>");
  html = html.replace(/\*(.*?)\*/gim, "<em>$1</em>");
  html = html.replace(/`([^`]+)`/gim, "<code>$1</code>");

  // Таблицы Markdown
  const tableRegex = /(?:\|[^\n]+\|\r?\n)((?:\|[^\n]+\|\r?\n)+)/g;
  html = html.replace(tableRegex, (match) => {
    const lines = match.trim().split("\n");
    if (lines.length < 2) return match;

    let tableHtml = "<table>";
    let isHeader = true;

    for (let line of lines) {
      if (line.includes("---")) {
        isHeader = false;
        continue;
      }
      const cells = line
        .split("|")
        .slice(1, -1)
        .map((c) => c.trim());

      tableHtml += "<tr>";
      for (let cell of cells) {
        const tag = isHeader ? "th" : "td";
        tableHtml += `<${tag}>${cell}</${tag}>`;
      }
      tableHtml += "</tr>";
      isHeader = false;
    }
    tableHtml += "</table>";
    return tableHtml;
  });

  // Списки
  html = html.replace(/^\- (.*$)/gim, "<li>$1</li>");
  html = html.replace(/(<li>.*<\/li>)/gim, "<ul>$1</ul>");
  html = html.replace(/<\/ul>\s*<ul>/gim, "");

  // Абзацы и переводы строк
  html = html.replace(/\n\n+/g, "<br/><br/>");

  return html;
}

/**
 * Настройка периодического автообновления живого мониторинга.
 */
function setupAutoRefresh() {
  if (liveRefreshTimer) {
    clearInterval(liveRefreshTimer);
    liveRefreshTimer = null;
  }
  const toggle = document.getElementById("auto-refresh-toggle");
  if (toggle && toggle.checked) {
    liveRefreshTimer = setInterval(() => {
      const currentTab = document.getElementById("tab-current");
      if (currentTab && currentTab.classList.contains("active")) {
        loadCurrentState(true);
      }
    }, 3000);
  }
}

/**
 * Загрузка списка доступных файлов и БД телеметрии.
 */
async function loadSources() {
  const select = document.getElementById("select-source");
  if (!select) return;

  try {
    const res = await fetch("/api/sources");
    if (!res.ok) return;
    const files = await res.json();
    select.innerHTML = '<option value="">Все доступные источники (telemetry.db + логи)</option>';
    files.forEach((f) => {
      const opt = document.createElement("option");
      opt.value = f.path;
      const sizeMb = (f.size_bytes / (1024 * 1024)).toFixed(1);
      opt.textContent = `${f.name} (${sizeMb} MB)`;
      select.appendChild(opt);
    });
  } catch (err) {
    console.warn("Ошибка загрузки источников:", err);
  }
}

/**
 * Инициализация пустых экземпляров графиков Chart.js для текущего состояния.
 */
function initLiveCharts() {
  const commonOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 300 },
    interaction: { intersect: false, mode: "index" },
    plugins: {
      legend: { labels: { color: "#94a3b8", font: { size: 11 } } },
      tooltip: { backgroundColor: "#131b2e", titleColor: "#38bdf8", bodyColor: "#f1f5f9", borderColor: "#23304d", borderWidth: 1 }
    },
    scales: {
      x: { grid: { color: "rgba(35, 48, 77, 0.4)" }, ticks: { color: "#94a3b8", font: { size: 10 }, maxRotation: 0, autoSkip: true, maxTicksLimit: 8 } },
      y: { grid: { color: "rgba(35, 48, 77, 0.4)" }, ticks: { color: "#94a3b8", font: { size: 10 } } }
    }
  };

  const createChart = (id, datasets, extraY = {}) => {
    const ctx = document.getElementById(id);
    if (!ctx) return null;
    const opts = JSON.parse(JSON.stringify(commonOptions));
    if (Object.keys(extraY).length > 0) {
      opts.scales = { ...opts.scales, ...extraY };
    }
    return new Chart(ctx.getContext("2d"), {
      type: "line",
      data: { labels: [], datasets: datasets },
      options: opts
    });
  };

  liveCharts.cpu = createChart("chart-live-cpu", [
    { label: "CPU Load (%)", data: [], borderColor: "#38bdf8", backgroundColor: "rgba(56, 189, 248, 0.15)", borderWidth: 2, fill: true, tension: 0.3, yAxisID: "y" },
    { label: "Частота (GHz)", data: [], borderColor: "#f59e0b", backgroundColor: "transparent", borderWidth: 2, borderDash: [4, 4], tension: 0.2, yAxisID: "y1" }
  ], {
    y: { min: 0, max: 100, ticks: { color: "#38bdf8" } },
    y1: { position: "right", grid: { drawOnChartArea: false }, ticks: { color: "#f59e0b" } }
  });

  liveCharts.ram = createChart("chart-live-ram", [
    { label: "RAM (%)", data: [], borderColor: "#10b981", backgroundColor: "rgba(16, 185, 129, 0.15)", borderWidth: 2, fill: true, tension: 0.3, yAxisID: "y" },
    { label: "Занято (GB)", data: [], borderColor: "#a855f7", backgroundColor: "transparent", borderWidth: 2, tension: 0.2, yAxisID: "y1" }
  ], {
    y: { min: 0, max: 100, ticks: { color: "#10b981" } },
    y1: { position: "right", grid: { drawOnChartArea: false }, ticks: { color: "#a855f7" } }
  });

  liveCharts.gpu = createChart("chart-live-gpu", [
    { label: "GPU Load (%)", data: [], borderColor: "#a855f7", backgroundColor: "rgba(168, 85, 247, 0.15)", borderWidth: 2, fill: true, tension: 0.3, yAxisID: "y" },
    { label: "GPU Temp (°C)", data: [], borderColor: "#ef4444", backgroundColor: "transparent", borderWidth: 2, tension: 0.2, yAxisID: "y1" }
  ], {
    y: { min: 0, max: 100, ticks: { color: "#a855f7" } },
    y1: { position: "right", grid: { drawOnChartArea: false }, ticks: { color: "#ef4444" } }
  });

  liveCharts.disk = createChart("chart-live-disk", [
    { label: "Чтение (MB/s)", data: [], borderColor: "#06b6d4", backgroundColor: "rgba(6, 182, 212, 0.15)", borderWidth: 2, fill: true, tension: 0.3 },
    { label: "Запись (MB/s)", data: [], borderColor: "#ec4899", backgroundColor: "rgba(236, 72, 153, 0.15)", borderWidth: 2, fill: true, tension: 0.3 }
  ]);

  liveCharts.net = createChart("chart-live-net", [
    { label: "Входящий (KB/s)", data: [], borderColor: "#6366f1", backgroundColor: "rgba(99, 102, 241, 0.15)", borderWidth: 2, fill: true, tension: 0.3 },
    { label: "Исходящий (KB/s)", data: [], borderColor: "#14b8a6", backgroundColor: "rgba(20, 184, 166, 0.15)", borderWidth: 2, fill: true, tension: 0.3 }
  ]);
}

/**
 * Загрузка актуального среза состояния и построение графиков из telemetry.db.
 */
async function loadCurrentState(silent = false) {
  const rangeSelect = document.getElementById("current-range-select");
  const limit = rangeSelect ? rangeSelect.value : 100;
  const selectSource = document.getElementById("select-source");
  const dbPath = selectSource && selectSource.value && selectSource.value.endsWith(".db") ? selectSource.value : "";

  try {
    const url = `/api/current-state?limit=${limit}${dbPath ? `&db_path=${encodeURIComponent(dbPath)}` : ""}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    if (data.status !== "ok") {
      document.getElementById("live-db-status").textContent = "⚠️ База данных не обнаружена";
      document.getElementById("live-db-sub").textContent = data.message || "Нет данных";
      return;
    }

    renderCurrentStatusBar(data);
    renderCurrentKPI(data.latest_snapshot);
    updateLiveCharts(data.time_series);
    renderLiveSensors(data.sensors);
    renderLiveProcesses(data.top_processes);
    renderLiveActivity(data.recent_events);
  } catch (err) {
    if (!silent) {
      console.error("Ошибка загрузки текущего состояния:", err);
    }
  }
}

/**
 * Отображение статуса базы данных telemetry.db.
 */
function renderCurrentStatusBar(data) {
  const statusEl = document.getElementById("live-db-status");
  const subEl = document.getElementById("live-db-sub");
  if (statusEl) {
    statusEl.innerHTML = `🟢 <strong>${data.db_name || "telemetry.db"}</strong> (${data.db_size_mb || 0} MB)`;
  }
  if (subEl) {
    const latestTs = data.latest_snapshot && data.latest_snapshot.timestamp ? data.latest_snapshot.timestamp.replace("T", " ").substring(0, 19) : "н/д";
    subEl.textContent = `Всего записей: ${data.total_snapshots.toLocaleString()} • Отображено точек: ${data.returned_points} • Время последнего замера: ${latestTs}`;
  }
}

/**
 * Обновление мгновенных карточек текущего состояния.
 */
function renderCurrentKPI(snap) {
  if (!snap) return;

  const cpuVal = document.getElementById("curr-cpu-val");
  const cpuFreq = document.getElementById("curr-cpu-freq");
  const cpuMeter = document.getElementById("curr-cpu-meter");
  if (cpuVal) {
    const cpuPct = Number(snap.cpu_total_percent || 0).toFixed(1);
    cpuVal.textContent = `${cpuPct}%`;
    if (cpuMeter) cpuMeter.style.width = `${Math.min(100, cpuPct)}%`;
  }
  if (cpuFreq) {
    const mhz = Number(snap.cpu_frequency_mhz || 0);
    cpuFreq.textContent = mhz > 0 ? `Частота: ${(mhz / 1000).toFixed(2)} GHz` : "Частота: --";
  }

  const ramVal = document.getElementById("curr-ram-val");
  const ramGb = document.getElementById("curr-ram-gb");
  const ramMeter = document.getElementById("curr-ram-meter");
  if (ramVal) {
    const ramPct = Number(snap.memory_percent || 0).toFixed(1);
    ramVal.textContent = `${ramPct}%`;
    if (ramMeter) ramMeter.style.width = `${Math.min(100, ramPct)}%`;
  }
  if (ramGb) {
    const used = Number(snap.memory_used_gb || 0).toFixed(1);
    const total = Number(snap.memory_total_gb || 0).toFixed(1);
    ramGb.textContent = `${used} / ${total} GB (Swap: ${snap.swap_percent || 0}%)`;
  }

  const gpuVal = document.getElementById("curr-gpu-val");
  const gpuTemp = document.getElementById("curr-gpu-temp");
  const gpuMeter = document.getElementById("curr-gpu-meter");
  if (gpuVal) {
    const gpuPct = Number(snap.gpu_load_percent || 0).toFixed(1);
    gpuVal.textContent = `${gpuPct}%`;
    if (gpuMeter) gpuMeter.style.width = `${Math.min(100, gpuPct)}%`;
  }
  if (gpuTemp) {
    const t = snap.gpu_temp_c;
    gpuTemp.textContent = t ? `Температура: ${Number(t).toFixed(1)}°C` : "Температура: --";
  }

  const diskVal = document.getElementById("curr-disk-val");
  if (diskVal) {
    const rb = ((snap.disk_read_bytes_sec || 0) / (1024 * 1024)).toFixed(1);
    const wb = ((snap.disk_write_bytes_sec || 0) / (1024 * 1024)).toFixed(1);
    diskVal.textContent = `R: ${rb} / W: ${wb} MB/s`;
  }

  const netVal = document.getElementById("curr-net-val");
  const uptimeVal = document.getElementById("curr-uptime-val");
  if (netVal) {
    const nr = ((snap.network_recv_bytes_sec || 0) / 1024).toFixed(1);
    const ns = ((snap.network_sent_bytes_sec || 0) / 1024).toFixed(1);
    netVal.textContent = `↓ ${nr} / ↑ ${ns} KB/s`;
  }
  if (uptimeVal) {
    const upSec = Number(snap.uptime_seconds || 0);
    const hours = Math.floor(upSec / 3600);
    const mins = Math.floor((upSec % 3600) / 60);
    uptimeVal.textContent = upSec > 0 ? `Аптайм: ${hours}ч ${mins}м` : "Аптайм: --";
  }
}

/**
 * Плавное обновление временных рядов Chart.js.
 */
function updateLiveCharts(ts) {
  if (!ts || !ts.labels) return;
  const labels = ts.labels;

  if (liveCharts.cpu) {
    liveCharts.cpu.data.labels = labels;
    liveCharts.cpu.data.datasets[0].data = ts.cpu_load || [];
    liveCharts.cpu.data.datasets[1].data = ts.cpu_freq_ghz || [];
    liveCharts.cpu.update("none");
  }

  if (liveCharts.ram) {
    liveCharts.ram.data.labels = labels;
    liveCharts.ram.data.datasets[0].data = ts.ram_percent || [];
    liveCharts.ram.data.datasets[1].data = ts.ram_used_gb || [];
    liveCharts.ram.update("none");
  }

  if (liveCharts.gpu) {
    liveCharts.gpu.data.labels = labels;
    liveCharts.gpu.data.datasets[0].data = ts.gpu_load || [];
    liveCharts.gpu.data.datasets[1].data = ts.gpu_temp || [];
    liveCharts.gpu.update("none");
  }

  if (liveCharts.disk) {
    liveCharts.disk.data.labels = labels;
    liveCharts.disk.data.datasets[0].data = ts.disk_read_mb || [];
    liveCharts.disk.data.datasets[1].data = ts.disk_write_mb || [];
    liveCharts.disk.update("none");
  }

  if (liveCharts.net) {
    liveCharts.net.data.labels = labels;
    liveCharts.net.data.datasets[0].data = ts.net_recv_kb || [];
    liveCharts.net.data.datasets[1].data = ts.net_sent_kb || [];
    liveCharts.net.update("none");
  }
}

/**
 * Отображение плиток датчиков и сенсоров.
 */
function renderLiveSensors(sensors) {
  const container = document.getElementById("live-sensors-container");
  if (!container) return;
  if (!sensors || sensors.length === 0) {
    container.innerHTML = '<div style="color: var(--text-secondary); grid-column: span 2;">Сенсоры LHM не зафиксированы в БД</div>';
    return;
  }
  container.innerHTML = "";
  sensors.slice(0, 16).forEach((s) => {
    const tile = document.createElement("div");
    tile.style.background = "rgba(11, 15, 25, 0.6)";
    tile.style.border = "1px solid var(--border-color)";
    tile.style.borderRadius = "8px";
    tile.style.padding = "8px 10px";
    tile.style.display = "flex";
    tile.style.justifyContent = "space-between";
    tile.style.alignItems = "center";

    const name = `${s.hardware_name ? s.hardware_name + " - " : ""}${s.sensor_name}`;
    const val = `${s.value} ${s.unit || ""}`;
    tile.innerHTML = `
      <div style="color: var(--text-secondary); font-size: 11px; max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${name}">${name}</div>
      <div style="font-weight: 700; color: var(--accent-blue);">${val}</div>
    `;
    container.appendChild(tile);
  });
}

/**
 * Отображение таблицы топ активных процессов.
 */
function renderLiveProcesses(processes) {
  const tbody = document.getElementById("live-processes-body");
  if (!tbody) return;
  if (!processes || processes.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--text-secondary);">Нет записей о процессах в выборке</td></tr>';
    return;
  }
  tbody.innerHTML = "";
  processes.forEach((p) => {
    const tr = document.createElement("tr");
    const cpuPct = Number(p.cpu_percent || 0).toFixed(1);
    const memMb = Number(p.memory_mb || 0).toFixed(1);
    tr.innerHTML = `
      <td><code>${p.pid}</code></td>
      <td><strong>${p.name}</strong></td>
      <td style="color: ${cpuPct > 20 ? 'var(--accent-amber)' : 'inherit'}; font-weight: ${cpuPct > 20 ? '700' : 'normal'};">${cpuPct}%</td>
      <td>${memMb} MB</td>
      <td>${p.num_threads || 1}</td>
    `;
    tbody.appendChild(tr);
  });
}

/**
 * Отображение ленты системных событий.
 */
function renderLiveActivity(events) {
  const list = document.getElementById("live-activity-list");
  if (!list) return;
  if (!events || events.length === 0) {
    list.innerHTML = '<li style="color: var(--text-secondary); text-align: center; padding: 10px;">События не зафиксированы</li>';
    return;
  }
  list.innerHTML = "";
  events.forEach((ev) => {
    const li = document.createElement("li");
    li.className = "activity-feed-item";
    const ts = (ev.timestamp || "").replace("T", " ").substring(11, 19);
    const tagClass = ev.source === "device" ? "activity-tag-device" : "activity-tag-system";
    const desc = ev.friendly_name || ev.name || ev.path || ev.event_type || "Событие";
    li.innerHTML = `
      <div class="activity-feed-left">
        <span style="font-weight: 600;">${desc}</span>
        <span style="color: var(--text-secondary); font-size: 11px;">${ev.category || ev.provider || ev.event_type || ""}</span>
      </div>
      <div style="text-align: right;">
        <span class="activity-tag ${tagClass}">${ev.event_type || "EVT"}</span>
        <div style="font-size: 10px; color: var(--text-secondary); margin-top: 4px;">${ts}</div>
      </div>
    `;
    list.appendChild(li);
  });
}

/**
 * Запуск глубокого исследования телеметрии.
 */
async function runResearch() {
  const btnRun = document.getElementById("btn-run");
  const selectSource = document.getElementById("select-source");
  const sourcePath = selectSource ? selectSource.value : null;

  if (btnRun) {
    btnRun.disabled = true;
    btnRun.innerHTML = "⏳ Анализ...";
  }

  try {
    const res = await fetch("/api/run-research", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source_path: sourcePath || null }),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const report = await res.json();
    currentReport = report;

    renderKPI(report);
    renderResearchCharts(report.base_report.charts);
    renderHypotheses(report.hypotheses);
    renderCorrelations(report.correlations);
    renderAnomalies(report.base_report.anomalies, report.base_report.summary_conclusions);
  } catch (err) {
    console.error("Ошибка при исследовании телеметрии:", err);
  } finally {
    if (btnRun) {
      btnRun.disabled = false;
      btnRun.innerHTML = "🔬 Анализ";
    }
  }
}

/**
 * Рендеринг сводных KPI карточек исследования.
 */
function renderKPI(report) {
  const base = report.base_report;
  const healthEl = document.getElementById("kpi-health");
  const recordsEl = document.getElementById("kpi-records");
  const cpuEl = document.getElementById("kpi-cpu-val");
  const ramEl = document.getElementById("kpi-ram-val");
  const anomaliesEl = document.getElementById("kpi-anomalies");
  const devicesEl = document.getElementById("kpi-devices");

  if (healthEl) {
    healthEl.textContent = `${base.health_score}%`;
    healthEl.style.color = base.health_score >= 80 ? "var(--accent-green)" : base.health_score >= 50 ? "var(--accent-amber)" : "var(--accent-red)";
  }

  if (recordsEl) {
    recordsEl.textContent = base.records_analyzed.toLocaleString();
  }

  if (cpuEl) {
    const stats = base.statistics || {};
    const cpuStat = stats.cpu_load || stats.cpu_total_percent;
    if (cpuStat && cpuStat.count > 0) {
      cpuEl.textContent = `CPU: ${cpuStat.avg_val}% (Max: ${cpuStat.max_val}%)`;
    } else {
      cpuEl.textContent = "CPU: --%";
    }
  }

  if (ramEl) {
    const stats = base.statistics || {};
    const ramStat = stats.ram_used_percent || stats.memory_percent;
    if (ramStat && ramStat.count > 0) {
      ramEl.textContent = `RAM: ${ramStat.avg_val}% (Max: ${ramStat.max_val}%)`;
    } else {
      ramEl.textContent = "RAM: --%";
    }
  }

  if (anomaliesEl) {
    const count = (base.anomalies ? base.anomalies.length : 0) + (base.device_summary ? base.device_summary.error_count : 0);
    anomaliesEl.textContent = count;
    anomaliesEl.style.color = count === 0 ? "var(--accent-green)" : count > 5 ? "var(--accent-red)" : "var(--accent-amber)";
  }

  if (devicesEl) {
    const dev = base.device_summary;
    if (dev && dev.error_count > 0) {
      devicesEl.textContent = `Сбоев оборудования: ${dev.error_count}`;
      devicesEl.style.color = "var(--accent-red)";
    } else {
      devicesEl.textContent = "Оборудование в норме";
      devicesEl.style.color = "var(--text-secondary)";
    }
  }
}

/**
 * Рендеринг графиков вкладки Исследования.
 */
function renderResearchCharts(charts) {
  const container = document.getElementById("charts-container");
  if (!container) return;

  Object.values(researchCharts).forEach((chart) => chart.destroy());
  researchCharts = {};
  container.innerHTML = "";

  if (!charts || charts.length === 0) {
    container.innerHTML = '<div class="kpi-card" style="grid-column: 1 / -1; text-align: center; padding: 40px;">Нет данных для построения графиков исследования</div>';
    return;
  }

  charts.forEach((cfg, idx) => {
    const card = document.createElement("div");
    card.className = "chart-card";

    const header = document.createElement("div");
    header.className = "chart-header";
    header.innerHTML = `<h3 class="chart-title">${cfg.title}</h3>`;

    const wrapper = document.createElement("div");
    wrapper.className = "chart-canvas-wrapper";

    const canvas = document.createElement("canvas");
    canvas.id = `research-chart-${idx}`;

    wrapper.appendChild(canvas);
    card.appendChild(header);
    card.appendChild(wrapper);
    container.appendChild(card);

    const ctx = canvas.getContext("2d");
    const chartDatasets = cfg.datasets.map((ds) => ({
      label: ds.label,
      data: ds.data,
      borderColor: ds.borderColor || "#38bdf8",
      backgroundColor: ds.backgroundColor || "rgba(56, 189, 248, 0.1)",
      borderWidth: 2,
      fill: true,
      tension: 0.3,
    }));

    researchCharts[canvas.id] = new Chart(ctx, {
      type: cfg.chart_type === "bar" ? "bar" : "line",
      data: { labels: cfg.labels, datasets: chartDatasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { grid: { color: "rgba(35, 48, 77, 0.4)" }, ticks: { color: "#94a3b8", maxRotation: 0, autoSkip: true, maxTicksLimit: 8 } },
          y: { grid: { color: "rgba(35, 48, 77, 0.4)" }, ticks: { color: "#94a3b8" } },
        },
      },
    });
  });
}

/**
 * Рендеринг гипотез.
 */
function renderHypotheses(hypotheses) {
  const container = document.getElementById("hypotheses-container");
  if (!container) return;
  container.innerHTML = "";

  if (!hypotheses || hypotheses.length === 0) {
    container.innerHTML = '<div class="kpi-card" style="grid-column: 1 / -1; text-align: center; padding: 40px;">Гипотезы не проверялись</div>';
    return;
  }

  hypotheses.forEach((h) => {
    const card = document.createElement("div");
    card.className = "hypothesis-card";
    const statusClass = h.confirmed ? "status-confirmed" : "status-rejected";
    const statusText = h.confirmed ? "Подтверждена" : "Отвергнута";

    card.innerHTML = `
      <div class="hyp-header">
        <h4 style="font-size: 15px; font-weight: 600;">${h.name}</h4>
        <span class="hyp-status ${statusClass}">${statusText}</span>
      </div>
      <p style="font-size: 13px; color: var(--text-secondary); margin-bottom: 8px;">${h.description}</p>
      <div style="font-size: 12px; color: var(--text-primary); margin-bottom: 8px;">
        <strong>Обоснование:</strong> ${h.evidence}
      </div>
      <div style="font-size: 11px; color: var(--accent-blue); background: var(--bg-main); padding: 6px 10px; border-radius: 6px;">
        💡 <strong>Рекомендация:</strong> ${h.recommendation}
      </div>
    `;
    container.appendChild(card);
  });
}

/**
 * Рендеринг корреляций Пирсона.
 */
function renderCorrelations(correlations) {
  const container = document.getElementById("correlations-container");
  if (!container) return;
  container.innerHTML = "";

  if (!correlations || correlations.length === 0) {
    container.innerHTML = '<p style="color: var(--text-secondary);">Недостаточно данных для матрицы корреляций</p>';
    return;
  }

  correlations.forEach((c) => {
    const item = document.createElement("div");
    item.className = "corr-item";
    const coeff = Number(c.pearson_coeff).toFixed(2);
    const isStrong = Math.abs(c.pearson_coeff) >= 0.7;
    const coeffClass = isStrong ? "corr-strong" : "corr-med";

    item.innerHTML = `
      <div>
        <strong>${c.metric_a}</strong> ↔ <strong>${c.metric_b}</strong>
        <div style="font-size: 12px; color: var(--text-secondary); margin-top: 2px;">${c.interpretation}</div>
      </div>
      <div class="corr-coeff ${coeffClass}">${coeff}</div>
    `;
    container.appendChild(item);
  });
}

/**
 * Рендеринг аномалий и выводов.
 */
function renderAnomalies(anomalies, conclusions) {
  const list = document.getElementById("conclusions-list");
  if (list) {
    list.innerHTML = "";
    if (conclusions && conclusions.length > 0) {
      conclusions.forEach((c) => {
        const li = document.createElement("li");
        li.style.marginBottom = "6px";
        li.textContent = c;
        list.appendChild(li);
      });
    } else {
      list.innerHTML = "<li>Аномалий не выявлено.</li>";
    }
  }

  const tbody = document.getElementById("anomalies-table-body");
  if (tbody) {
    tbody.innerHTML = "";
    if (anomalies && anomalies.length > 0) {
      anomalies.forEach((a) => {
        const tr = document.createElement("tr");
        const isCrit = a.severity === "critical";
        const tagColor = isCrit ? "var(--accent-red)" : "var(--accent-amber)";
        tr.innerHTML = `
          <td><span style="color: ${tagColor}; font-weight: 700; text-transform: uppercase;">${a.severity}</span></td>
          <td>${a.timestamp || "--"}</td>
          <td><strong>${a.metric}</strong></td>
          <td>${a.value}</td>
          <td>${a.description}</td>
        `;
        tbody.appendChild(tr);
      });
    } else {
      tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--accent-green);">Критических аномалий в исследуемой выборке не обнаружено</td></tr>';
    }
  }
}

/**
 * Загрузка сырых записей телеметрии с пагинацией.
 */
async function loadRecords() {
  const tbody = document.getElementById("records-table-body");
  const selectSource = document.getElementById("select-source");
  const sourcePath = selectSource ? selectSource.value : null;

  if (tbody) {
    tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: var(--text-secondary);">Загрузка записей...</td></tr>';
  }

  try {
    const params = new URLSearchParams({
      page: currentPage,
      page_size: pageSize,
    });
    if (sourcePath) params.append("source_path", sourcePath);
    if (searchQuery) params.append("query", searchQuery);

    const res = await fetch(`/api/records?${params.toString()}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    totalPages = Math.ceil(data.total / pageSize) || 1;
    const pageLabel = document.getElementById("page-label");
    if (pageLabel) {
      pageLabel.textContent = `Страница ${data.page} из ${totalPages} (Всего: ${data.total})`;
    }

    if (tbody) {
      tbody.innerHTML = "";
      if (data.items.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: var(--text-secondary);">Записи не найдены</td></tr>';
        return;
      }

      data.items.forEach((item) => {
        const tr = document.createElement("tr");
        const ts = item.timestamp || item.created_at || "--";
        const source = item.source_file || "sqlite";
        const type = item.event_type || (item.cpu_total_percent !== undefined ? "system_snapshot" : item.sensor_name ? "sensor_poll" : "custom");

        const displayObj = { ...item };
        delete displayObj.source_file;
        delete displayObj.timestamp;

        tr.innerHTML = `
          <td><code>${ts}</code></td>
          <td><span style="color: var(--accent-blue);">${source}</span></td>
          <td><span style="font-weight: 600;">${type}</span></td>
          <td><pre style="max-height: 80px; overflow-y: auto; font-size: 11px; background: rgba(0,0,0,0.2); padding: 4px; border-radius: 4px;">${JSON.stringify(displayObj, null, 2)}</pre></td>
        `;
        tbody.appendChild(tr);
      });
    }
  } catch (err) {
    if (tbody) {
      tbody.innerHTML = `<tr><td colspan="4" style="color: var(--accent-red); text-align: center;">Ошибка загрузки записей: ${err.message}</td></tr>`;
    }
  }
}

/**
 * Открытие автономного HTML отчета в новой вкладке.
 */
function openHtmlDashboard() {
  const selectSource = document.getElementById("select-source");
  const sourcePath = selectSource ? selectSource.value : "";
  const url = `/api/dashboard${sourcePath ? `?source_path=${encodeURIComponent(sourcePath)}` : ""}`;
  window.open(url, "_blank");
}

/**
 * Скачивание JSON-отчета исследования.
 */
function downloadJsonReport() {
  if (!currentReport) {
    alert("Сначала выполните анализ для генерации отчета");
    return;
  }
  const blob = new Blob([JSON.stringify(currentReport, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `telemetry_research_${Date.now()}.json`;
  a.click();
  URL.revokeObjectURL(url);
}
