// =============================================================================
// Process Name: About System Tab Web Controller
// =============================================================================
// Description:
//   Client-side JavaScript controller for the About System tab.
//   Provides real-time host telemetry, system identity & locale parameters,
//   AIDA64-like hardware tree, LibreHardwareMonitor sensors, live top processes,
//   disk volumes and security status.
//
//   КЕШИРОВАНИЕ (IndexedDB + Memory):
//   - Stale-While-Revalidate для всех данных
//   - Cache-First для hardware spec (меняется редко)
//   - Network-First для live telemetry (всегда свежие)
//   - Prefetching при активации вкладки
//
// File: main.js
// Package: src.api.webgui.about_system_tab
// Author: hypo69
// Copyright: © 2026 hypo69
// =============================================================================

(function () {
  let hardwareData = [];
  let currentSensors = [];
  let currentProcesses = [];
  let currentDisks = [];
  let activeSensorFilter = 'all';
  let isLiveActive = true;
  let liveIntervalId = null;
  let isUpdating = false;
  let isAiRunning = false;
  
  // Кеш-стратегия и TTL
  const CACHE_STRATEGY = {
    HARDWARE_SPEC: { ttl: 30 * 60 * 1000, strategy: 'cache-first' },      // 30 мин, редко меняется
    SYSTEM_SUMMARY: { ttl: 5 * 1000, strategy: 'stale-while-revalidate' }, // 5 сек
    SENSORS: { ttl: 3 * 1000, strategy: 'network-first' },                 // 3 сек, всегда свежие
    CONTROL_STATUS: { ttl: 60 * 1000, strategy: 'stale-while-revalidate' }, // 1 мин
    BACKUP_STATUS: { ttl: 5 * 60 * 1000, strategy: 'cache-first' }         // 5 мин
  };
  
  const CACHE_STORE = 'api_cache';
  const CACHE_TAG = 'about-system-tab';
  
  /**
   * Универсальная функция для работы с кешем
   * Поддерживает стратегии: cache-first, network-first, stale-while-revalidate
   */
  async function cachedFetch(url, cacheKey, options = {}) {
    const { ttl = 60000, strategy = 'stale-while-revalidate', forceNetwork = false } = options;
    const cache = window.browserCache;
    
    if (!cache) {
      // Fallback: кеш недоступен, прямой запрос
      return await apiFetch(url);
    }
    
    // Cache-First: сначала кеш, потом сеть (для редко меняющихся данных)
    if (strategy === 'cache-first' && !forceNetwork) {
      const cached = await cache.get(CACHE_STORE, cacheKey);
      if (cached) {
        console.log(`[Cache] HIT (cache-first): ${cacheKey}`);
        return cached;
      }
    }
    
    // Stale-While-Revalidate: показываем кеш, обновляем в фоне
    if (strategy === 'stale-while-revalidate' && !forceNetwork) {
      const cached = await cache.get(CACHE_STORE, cacheKey);
      if (cached) {
        console.log(`[Cache] HIT (stale-while-revalidate): ${cacheKey}, updating in background...`);
        // Запускаем обновление в фоне
        apiFetch(url)
          .then(fresh => cache.set(CACHE_STORE, cacheKey, fresh, { ttl, tags: [CACHE_TAG] }))
          .catch(err => console.warn(`[Cache] Background update failed for ${cacheKey}:`, err));
        return cached;
      }
    }
    
    // Network-First или первый запрос: сначала сеть, потом кеш
    try {
      const fresh = await apiFetch(url);
      // Сохраняем в кеш
      await cache.set(CACHE_STORE, cacheKey, fresh, { ttl, tags: [CACHE_TAG] });
      console.log(`[Cache] MISS → stored: ${cacheKey}`);
      return fresh;
    } catch (err) {
      // Если сеть недоступна, пытаемся вернуть устаревший кеш
      const cached = await cache.get(CACHE_STORE, cacheKey);
      if (cached) {
        console.warn(`[Cache] Network failed, returning stale cache: ${cacheKey}`);
        return cached;
      }
      throw err;
    }
  }
  
  /**
   * Очистка кеша вкладки (при необходимости)
   */
  async function clearTabCache() {
    const cache = window.browserCache;
    if (cache) {
      await cache.invalidateByTag(CACHE_STORE, CACHE_TAG);
      console.log('[Cache] Tab cache cleared');
    }
  }

  async function apiFetch(url, options = {}) {
    const opts = { ...options };
    if (opts.body && typeof opts.body === 'string') {
      opts.headers = {
        'Content-Type': 'application/json',
        ...(opts.headers || {})
      };
    }
    if (window.api && typeof window.api.fetch === 'function') {
      return await window.api.fetch(url, opts);
    }
    const res = await fetch(url, opts);
    if (!res.ok) {
      let errMsg = `HTTP ${res.status}`;
      try {
        const errJson = await res.json();
        if (errJson && errJson.detail) {
          errMsg += ` (${typeof errJson.detail === 'object' ? JSON.stringify(errJson.detail) : errJson.detail})`;
        }
      } catch (_) {}
      throw new Error(errMsg);
    }
    return await res.json();
  }

  function setText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text !== null && text !== undefined ? String(text) : '--';
  }

  function setHtml(id, html) {
    const el = document.getElementById(id);
    if (el) el.innerHTML = html;
  }

  async function initAboutSystemTab() {
    console.log('[AboutSystemTab] Initializing tab controller...');
    bindEvents();
    bindAIEvents();
    updateLocalClock();
    
    // Проверка доступности кеша
    await updateCacheStatus();

    // Prefetch: предзагрузка критичных данных для мгновенного отображения
    const prefetchPromises = [
      fetchSystemSummary().catch(err => console.warn('[AboutSystemTab] Quick summary error:', err)),
      fetchHardwareSpec().catch(err => console.warn('[AboutSystemTab] Hardware spec error:', err))
    ];
    
    // Ждем критичные данные перед отображением
    await Promise.allSettled(prefetchPromises);
    
    // Фоновая загрузка менее критичных данных
    fetchHardwareSensors().catch(err => console.warn('[AboutSystemTab] Sensors error:', err));
    fetchBackupStatus().catch(err => console.warn('[AboutSystemTab] Backup status error:', err));
    fetchSystemControlStatus().catch(err => console.warn('[AboutSystemTab] Control status error:', err));

    // AI-диагностика запускается только пользователем по кнопке Rescan / Запуск
    // Start live telemetry ticker
    startLiveStream();
  }
  window.initAboutSystemTab = initAboutSystemTab;
  
  /**
   * Обновление статуса кеша в интерфейсе
   */
  async function updateCacheStatus() {
    const badge = document.getElementById('about-sys-cache-badge');
    if (!badge) return;
    
    const cache = window.browserCache;
    if (!cache) {
      badge.textContent = '💾 Cache: Unavailable';
      badge.className = 'badge rounded-pill bg-warning-subtle text-warning border border-warning px-2.5 py-1';
      badge.title = 'Кеш недоступен, используется прямой запрос к API';
      return;
    }
    
    const ready = await cache.ready();
    if (ready) {
      const stats = await cache.getDetailedStats();
      const hitRate = stats.metrics.hits + stats.metrics.misses > 0 
        ? Math.round((stats.metrics.hits / (stats.metrics.hits + stats.metrics.misses)) * 100)
        : 0;
      
      badge.textContent = `💾 Cache: ${hitRate}% hit`;
      badge.className = 'badge rounded-pill bg-success-subtle text-success border border-success px-2.5 py-1';
      badge.title = `Кеш активен\nПопаданий: ${stats.metrics.hits}\nПромахов: ${stats.metrics.misses}\nВ памяти: ${stats.memoryCacheSize} записей`;
    } else {
      badge.textContent = '💾 Cache: Error';
      badge.className = 'badge rounded-pill bg-danger-subtle text-danger border border-danger px-2.5 py-1';
      badge.title = 'Ошибка инициализации кеша';
    }
  }

  function updateLocalClock() {
    const clockEl = document.getElementById('about-ident-time-badge');
    if (clockEl) {
      const now = new Date();
      clockEl.textContent = `Локальное время: ${now.toLocaleTimeString()}`;
    }
  }

  function startLiveStream() {
    if (window.registerTabPoller) {
      window.registerTabPoller('tab-about-system', async () => {
        updateLocalClock();
        if (isLiveActive && !isUpdating) {
          await pollLiveTelemetry();
        }
        // Обновляем статус кеша каждые 3 секунды
        await updateCacheStatus();
      }, 3000, { immediate: true });
    } else {
      if (liveIntervalId) clearInterval(liveIntervalId);
      liveIntervalId = setInterval(async () => {
        updateLocalClock();
        if (isLiveActive && !isUpdating) {
          await pollLiveTelemetry();
        }
        await updateCacheStatus();
      }, 3000);
    }
  }

  function bindEvents() {
    const btnRefresh = document.getElementById('btn-about-sys-refresh');
    if (btnRefresh) {
      btnRefresh.onclick = async () => {
        btnRefresh.disabled = true;
        const icon = btnRefresh.querySelector('i');
        if (icon) icon.classList.add('spin-animation');
        await refreshAllData();
        if (icon) icon.classList.remove('spin-animation');
        btnRefresh.disabled = false;
      };
    }
    
    const btnClearCache = document.getElementById('btn-about-sys-clear-cache');
    if (btnClearCache) {
      btnClearCache.onclick = async () => {
        btnClearCache.disabled = true;
        const icon = btnClearCache.querySelector('i');
        if (icon) icon.classList.add('spin-animation');
        
        // Очищаем кеш вкладки
        await clearTabCache();
        
        // Принудительно обновляем все данные из сети
        await refreshAllData(true);
        
        if (icon) icon.classList.remove('spin-animation');
        btnClearCache.disabled = false;
        
        if (window.showToast) {
          window.showToast('Кеш вкладки очищен, данные обновлены', 'success');
        }
      };
    }

    const btnLiveToggle = document.getElementById('btn-about-sys-live-toggle');
    if (btnLiveToggle) {
      btnLiveToggle.onclick = () => {
        isLiveActive = !isLiveActive;
        if (window.setTabPollerEnabled) {
          window.setTabPollerEnabled('tab-about-system_default', isLiveActive);
        }
        const icon = document.getElementById('icon-about-sys-live');
        const txt = document.getElementById('txt-about-sys-live');
        const liveBadge = document.getElementById('about-sys-live-badge');
        if (isLiveActive) {
          if (icon) icon.className = 'bi bi-pause-fill me-1';
          if (txt) txt.textContent = 'Пауза';
          if (liveBadge) {
            liveBadge.className = 'badge rounded-pill bg-info-subtle text-info border border-info px-2.5 py-1';
            liveBadge.textContent = '● Live Host Telemetry';
          }
        } else {
          if (icon) icon.className = 'bi bi-play-fill me-1';
          if (txt) txt.textContent = 'Возобновить';
          if (liveBadge) {
            liveBadge.className = 'badge rounded-pill bg-warning-subtle text-warning border border-warning px-2.5 py-1';
            liveBadge.textContent = '⏸ Stream Paused';
          }
        }
      };
    }

    const btnExpandAll = document.getElementById('btn-about-sys-expand-all');
    if (btnExpandAll) {
      btnExpandAll.onclick = () => {
        document.querySelectorAll('.about-sys-tree-body').forEach(b => b.classList.remove('d-none'));
        document.querySelectorAll('.about-sys-chevron').forEach(c => c.textContent = '▲');
      };
    }

    const btnCollapseAll = document.getElementById('btn-about-sys-collapse-all');
    if (btnCollapseAll) {
      btnCollapseAll.onclick = () => {
        document.querySelectorAll('.about-sys-tree-body').forEach(b => b.classList.add('d-none'));
        document.querySelectorAll('.about-sys-chevron').forEach(c => c.textContent = '▼');
      };
    }

    const treeSearch = document.getElementById('about-sys-search');
    if (treeSearch) {
      treeSearch.oninput = () => {
        renderHardwareTree(hardwareData, treeSearch.value.trim().toLowerCase());
      };
    }

    const sensorSearch = document.getElementById('about-sensor-search');
    if (sensorSearch) {
      sensorSearch.oninput = () => {
        renderSensorsList(currentSensors);
      };
    }

    const procSearch = document.getElementById('about-proc-search');
    if (procSearch) {
      procSearch.oninput = () => {
        renderProcessesTable(currentProcesses);
      };
    }

    // Sensor category filter buttons
    const filterGroup = document.getElementById('about-sensor-filter-group');
    if (filterGroup) {
      filterGroup.querySelectorAll('button').forEach(btn => {
        btn.onclick = () => {
          filterGroup.querySelectorAll('button').forEach(b => {
            b.classList.remove('active', 'btn-outline-info');
            b.classList.add('btn-outline-secondary');
          });
          btn.classList.add('active', 'btn-outline-info');
          btn.classList.remove('btn-outline-secondary');
          activeSensorFilter = btn.getAttribute('data-sensor-cat') || 'all';
          renderSensorsList(currentSensors);
        };
      });
    }
  }

  async function refreshAllData(forceNetwork = false) {
    isUpdating = true;
    try {
      if (forceNetwork) {
        // Принудительная загрузка из сети (игнорируем кеш)
        await Promise.allSettled([
          apiFetch('/api/v1/system/summary?process_limit=25').then(data => {
            if (window.browserCache) {
              window.browserCache.set(CACHE_STORE, 'system_summary', data, { 
                ttl: CACHE_STRATEGY.SYSTEM_SUMMARY.ttl, 
                tags: [CACHE_TAG] 
              });
            }
            return fetchSystemSummary();
          }),
          apiFetch('/api/system-control/status').then(data => {
            if (window.browserCache) {
              window.browserCache.set(CACHE_STORE, 'system_control_status', data, { 
                ttl: CACHE_STRATEGY.CONTROL_STATUS.ttl, 
                tags: [CACHE_TAG] 
              });
            }
            return fetchSystemControlStatus();
          }),
          apiFetch('/api/v1/system/hardware').then(data => {
            if (window.browserCache) {
              window.browserCache.set(CACHE_STORE, 'hardware_spec', data, { 
                ttl: CACHE_STRATEGY.HARDWARE_SPEC.ttl, 
                tags: [CACHE_TAG] 
              });
            }
            return fetchHardwareSpec();
          }),
          apiFetch('/api/v1/system/sensors').then(data => {
            if (window.browserCache) {
              window.browserCache.set(CACHE_STORE, 'hardware_sensors', data, { 
                ttl: CACHE_STRATEGY.SENSORS.ttl, 
                tags: [CACHE_TAG] 
              });
            }
            return fetchHardwareSensors();
          }),
          apiFetch('/api/v1/windows-backup/health').then(data => {
            if (window.browserCache) {
              window.browserCache.set(CACHE_STORE, 'backup_status', data, { 
                ttl: CACHE_STRATEGY.BACKUP_STATUS.ttl, 
                tags: [CACHE_TAG] 
              });
            }
            return fetchBackupStatus();
          })
        ]);
      } else {
        await Promise.allSettled([
          fetchSystemSummary(),
          fetchSystemControlStatus(),
          fetchHardwareSpec(),
          fetchHardwareSensors(),
          fetchBackupStatus()
        ]);
      }
    } finally {
      isUpdating = false;
    }
  }

  async function fetchBackupStatus() {
    try {
      const config = CACHE_STRATEGY.BACKUP_STATUS;
      const data = await cachedFetch(
        '/api/v1/windows-backup/health',
        'backup_status',
        { ttl: config.ttl, strategy: config.strategy }
      );
      if (!data) return;

      const cfg = data.file_history?.config;
      const storage = data.storage_audit;

      let lastTimeStr = 'Нет записей';
      if (cfg && cfg.last_backup_time) {
        try {
          const d = new Date(cfg.last_backup_time);
          if (!isNaN(d.getTime())) {
            lastTimeStr = d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
          }
        } catch (_) {}
      } else if (storage && storage.sample_versions && storage.sample_versions.length > 0) {
        const latestSample = storage.sample_versions[0];
        if (latestSample && latestSample.version_timestamp) {
          try {
            const d = new Date(latestSample.version_timestamp);
            if (!isNaN(d.getTime())) {
              lastTimeStr = d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            }
          } catch (_) {}
        }
      }

      let storageStr = '';
      if (storage && storage.target_exists && storage.free_space_gb !== null && storage.free_space_gb !== undefined) {
        const target = storage.target_path || 'Диск';
        const freeGb = typeof storage.free_space_gb === 'number' ? storage.free_space_gb.toFixed(1) : storage.free_space_gb;
        storageStr = `${target} (${freeGb} GB своб.)`;
      } else if (cfg && (cfg.target_drive_letter || cfg.target_url)) {
        storageStr = cfg.target_drive_letter || cfg.target_url;
      } else {
        storageStr = 'Хранилище не найдено';
      }

      const backupSummary = `${lastTimeStr} | ${storageStr}`;
      const backupEl = document.getElementById('about-ident-backup');
      if (backupEl) {
        backupEl.textContent = backupSummary;
        backupEl.title = `Последний бэкап: ${lastTimeStr}\nХранилище: ${storageStr}\nСлужба File History: ${data.file_history?.service_status || '—'}\nHealth Score: ${data.health_score ?? '--'}/100`;
      }
    } catch (e) {
      console.warn('[AboutSystemTab] fetchBackupStatus warning:', e);
      setText('about-ident-backup', 'Не настроено');
    }
  }

  async function pollLiveTelemetry() {
    isUpdating = true;
    try {
      await Promise.allSettled([
        fetchSystemSummary(true),
        fetchHardwareSensors(true)
      ]);
    } finally {
      isUpdating = false;
    }
  }

  async function fetchSystemSummary(isLightPoll = false) {
    try {
      const config = CACHE_STRATEGY.SYSTEM_SUMMARY;
      const snap = await cachedFetch(
        '/api/v1/system/summary?process_limit=25',
        'system_summary',
        { ttl: config.ttl, strategy: isLightPoll ? 'stale-while-revalidate' : 'network-first' }
      );
      if (!snap) return;

      // 1. Identity & Locale Block
      const host = snap.hostname || 'DELL-VOSTRO';
      const user = snap.username || 'onela';
      const lang = snap.system_language || 'Русский (Россия) [ru-RU]';
      const userLoc = snap.user_locale || 'ru-RU';
      const sysLoc = snap.system_locale || 'ru-RU';
      const tz = snap.timezone || 'UTC+03:00';
      const cp = snap.codepage || 'UTF-8 (ACP: 65001)';
      const inputs = Array.isArray(snap.input_languages) && snap.input_languages.length > 0
        ? snap.input_languages.join(', ')
        : 'Русский (RU), English (US), עברית (IL)';
      const osBuild = snap.os_build ? `${snap.os_name || 'Windows 11'} (Build ${snap.os_build})` : (snap.os_name || 'Windows 11');

      setText('about-ident-hostname', host);
      setText('about-ident-domain', `Workgroup / Host: ${host}`);
      setText('about-ident-username', user);
      setText('about-ident-language', lang);
      setText('about-ident-locales', `Локали: User: ${userLoc} | Sys: ${sysLoc}`);
      setText('about-ident-timezone', tz);
      setText('about-ident-codepage', `Кодировка: ${cp}`);
      setText('about-ident-inputs', inputs);
      setText('about-ident-os-build', osBuild);
      setText('about-ident-install-date', snap.os_install_date || 'Не определена');

      // Top KPI Card 1: Operating System
      setText('about-kpi-os-title', `${snap.os_name || 'Windows 11'} (${snap.cpu?.architecture || 'AMD64'})`);
      setText('about-kpi-os-host', `Host: ${host}`);

      // 2. Telemetry Live Bar
      if (snap.cpu) {
        const cpuPct = snap.cpu.total_percent || 0;
        setText('about-telemetry-cpu-val', `${cpuPct.toFixed(1)}%`);
        const cpuBar = document.getElementById('about-telemetry-cpu-bar');
        if (cpuBar) {
          cpuBar.style.width = `${Math.min(100, Math.max(0, cpuPct))}%`;
          cpuBar.className = cpuPct > 85 ? 'about-sys-progress-bar bg-danger' : (cpuPct > 60 ? 'about-sys-progress-bar bg-warning' : 'about-sys-progress-bar bg-info');
        }
        const freqTxt = snap.cpu.frequency_mhz ? `${snap.cpu.frequency_mhz} MHz` : '';
        setText('about-telemetry-cpu-freq', freqTxt);
        const cores = snap.cpu.physical_cores || 6;
        const threads = snap.cpu.logical_cores || 12;
        setText('about-telemetry-cpu-cores', `${cores} физ. / ${threads} Потоков`);

        // Specification Table CPU
        setText('about-spec-cpu', `${snap.cpu.model || 'Intel Processor'} (${threads} logical cores)`);
      }

      if (snap.memory) {
        const total = Number(snap.memory.total_gb || 0).toFixed(1);
        const used = Number(snap.memory.used_gb || 0).toFixed(1);
        const avail = Number(snap.memory.available_gb || 0).toFixed(1);
        const pct = snap.memory.percent || 0;

        setText('about-telemetry-ram-val', `${used} / ${total} GB`);
        setText('about-telemetry-ram-sub', `${pct}% занято (${avail} GB свободно)`);
        const ramBar = document.getElementById('about-telemetry-ram-bar');
        if (ramBar) {
          ramBar.style.width = `${Math.min(100, Math.max(0, pct))}%`;
          ramBar.className = pct > 85 ? 'about-sys-progress-bar bg-danger' : (pct > 65 ? 'about-sys-progress-bar bg-warning' : 'about-sys-progress-bar bg-info');
        }

        // Specification Table RAM (Hardware installed capacity)
        setText('about-spec-ram', `${total} GB RAM (${avail} GB свободно)`);
      }

      if (Array.isArray(snap.gpus) && snap.gpus.length > 0) {
        const gpu = snap.gpus[0];
        setText('about-telemetry-gpu-name', gpu.name || 'GPU');
        const vramTxt = gpu.memory_total_gb ? `VRAM: ${Number(gpu.memory_total_gb).toFixed(1)} GB` : 'VRAM: N/A';
        const loadTxt = gpu.load_percent !== null && gpu.load_percent !== undefined ? ` | Нагрузка: ${gpu.load_percent}%` : '';
        setText('about-telemetry-gpu-vram', `${vramTxt}${loadTxt}`);

        const badgeGpu = document.getElementById('about-telemetry-gpu-badge');
        if (badgeGpu) {
          const caps = [];
          if (gpu.has_cuda) caps.push('CUDA');
          if (gpu.has_directml) caps.push('DirectML');
          badgeGpu.textContent = caps.length > 0 ? caps.join(' + ') : 'Active GPU';
        }
      }

      if (snap.disk_io) {
        const rKbs = Math.round((snap.disk_io.read_bytes_per_sec || 0) / 1024);
        const wKbs = Math.round((snap.disk_io.write_bytes_per_sec || 0) / 1024);
        const totalMb = (((snap.disk_io.read_bytes_per_sec || 0) + (snap.disk_io.write_bytes_per_sec || 0)) / (1024 * 1024)).toFixed(2);
        setText('about-telemetry-disk-val', `${totalMb} MB/s`);
        setText('about-telemetry-disk-rates', `Чтение: ${rKbs} КБ/с | Запись: ${wKbs} КБ/с`);
      }

      // Specification Table general
      setText('about-spec-host', host);
      setText('about-spec-os', osBuild);
      if (snap.uptime_seconds) {
        const sec = snap.uptime_seconds;
        const h = Math.floor(sec / 3600);
        const m = Math.floor((sec % 3600) / 60);
        setText('about-spec-uptime', `Uptime: ${h}h ${m}m`);
      }

      // 3. Disks Table
      if (Array.isArray(snap.disks) && snap.disks.length > 0) {
        currentDisks = snap.disks;
        renderDisksTable(snap.disks);

        // Update Top KPI Storage C:
        const cDrive = snap.disks.find(d => (d.device || '').toUpperCase().startsWith('C')) || snap.disks[0];
        if (cDrive) {
          const freeGb = Number(cDrive.free_gb || 0).toFixed(1);
          const totalGb = Number(cDrive.total_gb || 0).toFixed(1);
          setText('about-kpi-stor-title', `${freeGb} GB Free / ${totalGb} GB`);
        }
      }

      // 4. Monitors & Displays Block
      if (Array.isArray(snap.monitors) && snap.monitors.length > 0) {
        const monShorts = snap.monitors.map(m => {
          const prim = m.is_primary ? ' [Основной]' : '';
          return `${m.name || 'Monitor'} (${m.width}x${m.height}@${m.frequency_hz}Hz${prim})`;
        });
        setText('about-ident-monitors', monShorts.join(', '));
        setText('about-spec-monitors', monShorts.join(', '));
      }

      // 5. Windows Updates Block
      if (snap.updates) {
        const kbCount = snap.updates.installed_kb_count ? ` (${snap.updates.installed_kb_count} KBs)` : '';
        const updTxt = `${snap.updates.status || 'Up to date'}${kbCount}`;
        setText('about-ident-updates', updTxt);
        setText('about-spec-update', updTxt);
      }

      // 5.1 MS Office Block
      if (snap.office) {
        const offTxt = snap.office.status || (snap.office.installed ? `${snap.office.product_name || 'MS Office'} (${snap.office.version || ''})` : 'Не установлен');
        setText('about-ident-ms-office', offTxt);
      } else {
        setText('about-ident-ms-office', 'Не установлен');
      }

      // 5.2 OneDrive Storage Block
      if (snap.onedrive) {
        const odTxt = snap.onedrive.status || (snap.onedrive.installed ? `${snap.onedrive.free_gb || 0} GB своб.` : 'Не настроено');
        setText('about-ident-onedrive', odTxt);
      } else {
        setText('about-ident-onedrive', 'Не настроено');
      }

      // 6. Processes Table
      if (Array.isArray(snap.top_processes)) {
        currentProcesses = snap.top_processes;
        renderProcessesTable(snap.top_processes);
      }

    } catch (e) {
      console.warn('[AboutSystemTab] fetchSystemSummary warning:', e);
    }
  }

  async function fetchSystemControlStatus() {
    try {
      const config = CACHE_STRATEGY.CONTROL_STATUS;
      const res = await cachedFetch(
        '/api/system-control/status',
        'system_control_status',
        { ttl: config.ttl, strategy: config.strategy }
      );
      if (!res) return;

      const isElevated = res.is_elevated;
      const privBadge = document.getElementById('about-sys-privilege-badge');
      if (privBadge) {
        if (isElevated) {
          privBadge.className = 'badge rounded-pill bg-success-subtle text-success border border-success px-2.5 py-1';
          privBadge.textContent = '🛡️ Administrator Access';
        } else {
          privBadge.className = 'badge rounded-pill bg-secondary-subtle text-secondary border border-secondary px-2.5 py-1';
          privBadge.textContent = '👁️ Standard User Mode';
        }
      }
      setText('about-ident-privilege', isElevated ? 'Права: Администратор (Full Access)' : 'Права: Стандартный пользователь');

      // Security Details
      const sec = res.security || {};
      const rest = res.restore || {};
      const disk = res.disk || {};
      const pwr = res.power || {};
      const upd = res.update || {};

      // KPI 2: Security & Defender
      const defActive = sec.defender_enabled !== false;
      setText('about-kpi-sec-title', defActive ? 'Active & Protected' : 'Attention Required');
      const fwOk = sec.firewall_overall_enabled !== false;
      const uacOk = sec.uac_enabled !== false;
      setText('about-kpi-sec-sub', `Firewall: ${fwOk ? 'ON' : 'OFF'} | UAC: ${uacOk ? 'ON' : 'OFF'}`);

      // KPI 3: System Protection
      const countPoints = rest.restore_points_count || 0;
      setText('about-kpi-prot-title', `${countPoints} Checkpoints`);
      setText('about-kpi-prot-sub', `Protection: ${rest.system_protection_enabled ? 'Active' : 'Disabled'}`);

      // KPI 4: Cleanable estimate & Total Disk Size
      const cleanMb = disk.cleanup_estimate?.total_cleanable_mb || 150;
      const cDrive = currentDisks.find(d => (d.device || '').toUpperCase().startsWith('C')) || currentDisks[0];
      const totalGbTxt = cDrive ? ` | Всего: ${Number(cDrive.total_gb || 0).toFixed(1)} GB` : '';
      setText('about-kpi-stor-clean', `Cleanable: ~${cleanMb} MB${totalGbTxt}`);

      // Security table rows
      setText('about-sec-defender', defActive ? 'Enabled' : 'Disabled');
      setText('about-sec-realtime', sec.realtime_protection_enabled !== false ? 'Enabled' : 'Disabled');
      setText('about-sec-fw-domain', sec.firewall_profiles?.Domain ? 'Active' : 'Disabled');
      setText('about-sec-fw-private', sec.firewall_profiles?.Private ? 'Active' : 'Disabled');
      setText('about-sec-fw-public', sec.firewall_profiles?.Public ? 'Active' : 'Disabled');
      setText('about-sec-uac', uacOk ? 'Enabled' : 'Disabled');

      // Power Scheme & Updates
      if (pwr.active_plan_name) setText('about-spec-power', pwr.active_plan_name);
      if (upd.status) {
        const kbCount = upd.recent_hotfixes_count ? ` (${upd.recent_hotfixes_count} KBs installed)` : '';
        const updTxt = `${upd.status}${kbCount}`;
        setText('about-spec-update', updTxt);
        setText('about-ident-updates', updTxt);
      }

    } catch (e) {
      console.warn('[AboutSystemTab] fetchSystemControlStatus warning:', e);
    }
  }

  async function fetchHardwareSensors(isPoll = false) {
    try {
      const config = CACHE_STRATEGY.SENSORS;
      const sensors = await cachedFetch(
        '/api/v1/system/sensors',
        'hardware_sensors',
        { ttl: config.ttl, strategy: config.strategy }
      );
      if (Array.isArray(sensors)) {
        currentSensors = sensors;
        const badge = document.getElementById('about-sensors-count-badge');
        if (badge) badge.textContent = `LHM Active (${sensors.length} шт.)`;
        renderSensorsList(sensors);
      }
    } catch (e) {
      console.warn('[AboutSystemTab] fetchHardwareSensors warning:', e);
    }
  }

  function bindAIEvents() {
    const btnRescan = document.getElementById('btn-about-ai-rescan');
    if (btnRescan) {
      btnRescan.onclick = () => runAIDiagnostics(true);
    }

    const btnToggleStages = document.getElementById('btn-about-ai-toggle-stages');
    const stagesBox = document.getElementById('about-ai-stages-container');
    const icStages = document.getElementById('ic-about-ai-toggle-stages');
    const txtStages = document.getElementById('txt-about-ai-toggle-stages');
    if (btnToggleStages && stagesBox) {
      btnToggleStages.onclick = () => {
        const isHidden = stagesBox.classList.toggle('d-none');
        if (icStages) {
          icStages.className = isHidden ? 'bi bi-chevron-down ms-0.5' : 'bi bi-chevron-up ms-0.5';
        }
        if (txtStages) {
          txtStages.textContent = isHidden ? 'Показать этапы' : 'Свернуть этапы';
        }
      };
    }

    const btnToggleInstruction = document.getElementById('btn-about-ai-toggle-instruction');
    const instructionCollapse = document.getElementById('about-ai-instruction-collapse');
    const icInstruction = document.getElementById('ic-about-ai-instruction');
    if (btnToggleInstruction && instructionCollapse) {
      btnToggleInstruction.onclick = () => {
        const isShown = !instructionCollapse.classList.toggle('d-none');
        if (icInstruction) {
          icInstruction.className = isShown ? 'bi bi-chevron-up text-muted ms-1' : 'bi bi-chevron-down text-muted ms-1';
        }
      };
    }

    const btnCopyInstruction = document.getElementById('btn-about-ai-copy-instruction');
    if (btnCopyInstruction) {
      btnCopyInstruction.onclick = () => {
        const text = document.getElementById('about-ai-instruction-text')?.textContent || '';
        navigator.clipboard.writeText(text).then(() => {
          const s = document.getElementById('txt-about-ai-copy-instruction');
          if (s) s.textContent = 'Скопировано!';
          setTimeout(() => { if (s) s.textContent = 'Копировать'; }, 1800);
        });
      };
    }

    const btnTogglePrompt = document.getElementById('btn-about-ai-toggle-prompt');
    const promptCollapse = document.getElementById('about-ai-prompt-collapse');
    const icPrompt = document.getElementById('ic-about-ai-prompt');
    if (btnTogglePrompt && promptCollapse) {
      btnTogglePrompt.onclick = () => {
        const isShown = !promptCollapse.classList.toggle('d-none');
        if (icPrompt) {
          icPrompt.className = isShown ? 'bi bi-chevron-up text-muted ms-1' : 'bi bi-chevron-down text-muted ms-1';
        }
      };
    }

    const btnCopyPrompt = document.getElementById('btn-about-ai-copy-prompt');
    if (btnCopyPrompt) {
      btnCopyPrompt.onclick = () => {
        const text = document.getElementById('about-ai-prompt-text')?.textContent || '';
        navigator.clipboard.writeText(text).then(() => {
          const s = document.getElementById('txt-about-ai-copy-prompt');
          if (s) s.textContent = 'Скопировано!';
          setTimeout(() => { if (s) s.textContent = 'Копировать'; }, 1800);
        });
      };
    }

    const btnToggleRaw = document.getElementById('btn-about-ai-toggle-raw');
    const rawCollapse = document.getElementById('about-ai-raw-collapse');
    const icRaw = document.getElementById('ic-about-ai-raw');
    if (btnToggleRaw && rawCollapse) {
      btnToggleRaw.onclick = () => {
        const isShown = !rawCollapse.classList.toggle('d-none');
        if (icRaw) {
          icRaw.className = isShown ? 'bi bi-chevron-up text-muted ms-1' : 'bi bi-chevron-down text-muted ms-1';
        }
      };
    }

    const btnCopyRaw = document.getElementById('btn-about-ai-copy-raw');
    if (btnCopyRaw) {
      btnCopyRaw.onclick = () => {
        const text = document.getElementById('about-ai-raw-text')?.textContent || '';
        navigator.clipboard.writeText(text).then(() => {
          const s = document.getElementById('txt-about-ai-copy-raw');
          if (s) s.textContent = 'Скопировано!';
          setTimeout(() => { if (s) s.textContent = 'Копировать'; }, 1800);
        });
      };
    }

    const btnToggleSnapshot = document.getElementById('btn-about-ai-toggle-snapshot');
    const snapshotCollapse = document.getElementById('about-ai-snapshot-collapse');
    const icSnapshot = document.getElementById('ic-about-ai-snapshot');
    if (btnToggleSnapshot && snapshotCollapse) {
      btnToggleSnapshot.onclick = () => {
        const isShown = !snapshotCollapse.classList.toggle('d-none');
        if (icSnapshot) {
          icSnapshot.className = isShown ? 'bi bi-chevron-up text-muted ms-1' : 'bi bi-chevron-down text-muted ms-1';
        }
      };
    }

    const btnCopySnapshot = document.getElementById('btn-about-ai-copy-snapshot');
    if (btnCopySnapshot) {
      btnCopySnapshot.onclick = () => {
        const text = document.getElementById('about-ai-snapshot-text')?.textContent || '';
        navigator.clipboard.writeText(text).then(() => {
          const s = document.getElementById('txt-about-ai-copy-snapshot');
          if (s) s.textContent = 'Скопировано!';
          setTimeout(() => { if (s) s.textContent = 'Копировать JSON'; }, 1800);
        });
      };
    }
  }

  function renderAIDiagnosticStages(stages, isCompleted = true) {
    const container = document.getElementById('about-ai-stages-container');
    if (!container) return;
    if (!Array.isArray(stages) || stages.length === 0) {
      container.innerHTML = '<div class="small text-muted text-center py-2">Этапы пошагового аудита не запущены</div>';
      return;
    }

    container.innerHTML = stages.map((st, idx) => {
      const isLatest = idx === stages.length - 1 && !isCompleted;
      const icon = isLatest
        ? '<div class="spinner-grow spinner-grow-sm text-info" style="width: 0.6rem; height: 0.6rem;" role="status"></div>'
        : (st.stage === 'error' || st.stage === 'warning')
        ? '<span class="text-warning small fw-bold" style="font-size: 0.72rem;">⚠️</span>'
        : '<span class="text-success small fw-bold" style="font-size: 0.72rem;">✔</span>';
      const textClass = isLatest ? 'text-light fw-semibold' : 'text-muted';
      return `
        <div class="about-ai-stage-row ${textClass}">
          <div class="d-flex align-items-center gap-2">
            <span>${icon}</span>
            <span>${escapeHtml(st.message || st.title || 'Выполнение этапа...')}</span>
          </div>
          ${st.details ? `<div class="text-secondary ps-3 font-monospace" style="font-size: 0.68rem; word-break: break-all;">↳ ${escapeHtml(st.details)}</div>` : ''}
        </div>
      `;
    }).join('');
  }

  function renderAIDomainCards(groupsResults) {
    const container = document.getElementById('about-ai-groups-container');
    if (!container) return;

    container.innerHTML = groupsResults.map(g => {
      const isPending = g.status === 'pending';
      const isAnalyzing = g.status === 'analyzing';
      const isCrit = g.status === 'critical';
      const isWarn = g.status === 'warning';

      const statusBadge = isPending
        ? '<span class="badge bg-secondary bg-opacity-25 text-muted border border-secondary border-opacity-25"><i class="bi bi-hourglass me-1"></i>Ожидание</span>'
        : isAnalyzing
        ? '<span class="badge bg-info bg-opacity-20 text-info border border-info border-opacity-50"><span class="spinner-border spinner-border-sm me-1" style="width:0.6rem;height:0.6rem;"></span>Анализ LLM...</span>'
        : isCrit
        ? '<span class="badge bg-danger text-white"><i class="bi bi-exclamation-octagon-fill me-1"></i>Критично</span>'
        : isWarn
        ? '<span class="badge bg-warning text-dark"><i class="bi bi-exclamation-triangle-fill me-1"></i>Внимание</span>'
        : '<span class="badge bg-success-subtle text-success border border-success"><i class="bi bi-check-circle-fill me-1"></i>В норме</span>';

      const cardBorder = isCrit
        ? 'border-danger border-opacity-75 shadow-sm'
        : isWarn
        ? 'border-warning border-opacity-50 shadow-sm'
        : isAnalyzing
        ? 'border-info border-opacity-60 shadow-sm'
        : 'border-secondary border-opacity-30';

      const metricsList = g.key_metrics && Object.keys(g.key_metrics).length > 0
        ? `<div class="mt-2 pt-1.5 border-top border-secondary border-opacity-20 d-flex flex-wrap gap-1.5 font-monospace" style="font-size: 0.70rem;">
            ${Object.entries(g.key_metrics).map(([k, v]) => `<span class="badge bg-dark bg-opacity-75 border border-secondary text-light px-2 py-1"><strong class="text-info">${escapeHtml(k)}:</strong> <span class="text-white">${escapeHtml(String(v))}</span></span>`).join('')}
           </div>`
        : '';

      return `
        <div class="col-12 col-md-6">
          <div class="p-2.5 rounded bg-black bg-opacity-40 border ${cardBorder} h-100 d-flex flex-column justify-content-between transition-all" id="domain-card-${g.group_id}">
            <div>
              <div class="d-flex align-items-center justify-content-between mb-1.5">
                <div class="d-flex align-items-center gap-1.5">
                  <i class="bi ${escapeHtml(g.icon || 'bi-cpu')} text-info fs-6"></i>
                  <strong class="text-light" style="font-size: 0.82rem;">${escapeHtml(g.title)}</strong>
                </div>
                ${statusBadge}
              </div>
              <div class="small text-light mt-1" style="font-size: 0.73rem; line-height: 1.45; white-space: pre-line;">
                ${escapeHtml(g.summary || g.description || 'Ожидание запуска группы...')}
              </div>
            </div>
            ${metricsList}
          </div>
        </div>
      `;
    }).join('');
  }

  function renderAIAnomalies(anomalies) {
    const container = document.getElementById('about-ai-anomalies-container');
    if (!container) return;
    if (!Array.isArray(anomalies) || anomalies.length === 0) {
      container.innerHTML = '<span class="badge bg-success-subtle text-success border border-success px-2.5 py-1" style="font-size: 0.72rem;"><i class="bi bi-check-circle me-1"></i> Аномалий в подсистемах оборудования не обнаружено</span>';
      return;
    }

    container.innerHTML = anomalies.map(a => {
      const isCrit = a.severity === 'critical';
      return `<span class="anomaly-pill ${isCrit ? 'critical' : 'warning'}">⚠️ [${escapeHtml(a.subsystem || 'SYS')}] ${escapeHtml(a.title || '')}: ${escapeHtml(a.description || '')}</span>`;
    }).join('');
  }

  async function runAIDiagnostics(isManualRescan = false) {
    if (isAiRunning) return;
    isAiRunning = true;
    
    // Устанавливаем флаг processing для немедленного переключения вкладок
    if (window.setTabProcessing) {
      window.setTabProcessing('tab-about-system', true);
    }

    const btnRescan = document.getElementById('btn-about-ai-rescan');
    const txtRescan = document.getElementById('txt-about-ai-rescan');
    const icRescan = document.getElementById('ic-about-ai-rescan');
    const badgeHealth = document.getElementById('about-ai-health-badge');
    const badgeHealthBtn = document.getElementById('about-ai-health-badge-btn');
    const engineTag = document.getElementById('about-ai-engine-name');
    const summaryEl = document.getElementById('about-ai-summary-text');
    const errorSec = document.getElementById('about-ai-error-section');
    const errorText = document.getElementById('about-ai-error-text');
    const progressBar = document.getElementById('about-ai-step-progress');
    const synthesisStatus = document.getElementById('about-ai-synthesis-status');
    const actionsBox = document.getElementById('about-ai-actions-box');
    const actionsList = document.getElementById('about-ai-actions-list');

    const liveStatusText = document.getElementById('about-ai-live-status-text');
    const chipLhm = document.getElementById('chip-sensor-lhm');
    const chipWmi = document.getElementById('chip-sensor-wmi');
    const chipRam = document.getElementById('chip-sensor-ram');
    const chipDisks = document.getElementById('chip-sensor-disks');
    const chipNet = document.getElementById('chip-sensor-net');
    const snapshotText = document.getElementById('about-ai-snapshot-text');
    const tickCpu = document.getElementById('live-tick-cpu');
    const tickTemp = document.getElementById('live-tick-temp');
    const tickRam = document.getElementById('live-tick-ram');
    const tickDisks = document.getElementById('live-tick-disks');
    const tickTopProc = document.getElementById('live-tick-top-proc');

    if (btnRescan) btnRescan.disabled = true;
    if (icRescan) icRescan.className = 'spinner-border spinner-border-sm text-dark';
    if (txtRescan) txtRescan.textContent = 'Диагностика...';

    if (errorSec) errorSec.classList.add('d-none');
    if (actionsBox) actionsBox.classList.add('d-none');
    if (progressBar) progressBar.style.width = '5%';

    if (liveStatusText) liveStatusText.textContent = 'Опрос аппаратных датчиков хоста (LibreHardwareMonitor, WMI, psutil, SMART)...';

    // Reset chips to active polling state
    [chipLhm, chipWmi, chipRam, chipDisks, chipNet].forEach(c => {
      if (c) c.className = 'badge bg-secondary bg-opacity-40 text-light border border-secondary';
    });

    if (badgeHealth) {
      badgeHealth.textContent = 'Health: Поэтапный опрос...';
      badgeHealth.className = 'badge bg-warning-subtle text-warning border border-warning font-monospace';
    }
    if (badgeHealthBtn) {
      badgeHealthBtn.textContent = 'Health: Опрос...';
      badgeHealthBtn.className = 'badge bg-warning-subtle text-warning border border-warning font-monospace ms-1';
    }

    const stagesLog = [
      {
        stage: 'init',
        title: 'Сбор телеметрии',
        message: '🔌 Получение среза телеметрии и сенсоров хоста...',
        details: 'Опрос LibreHardwareMonitor, WMI счетчиков и SystemSnapshot',
      }
    ];
    renderAIDiagnosticStages(stagesLog, false);

    try {
      // 1. Получение списка подготовленных 4 групп телеметрии
      const groups = await apiFetch('/api/v1/system/diagnose/groups');
      if (!Array.isArray(groups) || groups.length === 0) {
        throw new Error('Не удалось получить список диагностических групп');
      }

      if (snapshotText) {
        snapshotText.textContent = JSON.stringify(groups, null, 2);
      }

      // Обновление живой информационной плашки собранных метрик
      const compGroup = groups.find(g => g.group_id === 'compute_thermals');
      if (compGroup && compGroup.payload) {
        const cpu = compGroup.payload.cpu || {};
        if (tickCpu) tickCpu.textContent = `${cpu.model || 'CPU'} (${cpu.load_percent ?? 0}%)`;
        const temps = compGroup.payload.sensors?.temperatures_celsius || {};
        const tempVals = Object.values(temps);
        const maxT = tempVals.length > 0 ? Math.max(...tempVals) : null;
        if (tickTemp) tickTemp.textContent = maxT !== null ? `${maxT}°C` : 'В норме';
      }

      const memGroup = groups.find(g => g.group_id === 'memory_processes');
      if (memGroup && memGroup.payload) {
        const ram = memGroup.payload.ram || {};
        if (tickRam) tickRam.textContent = `${ram.used_gb ?? 0} / ${ram.total_gb ?? 0} GB (${ram.used_percent ?? 0}%)`;
        const procs = memGroup.payload.top_active_processes || [];
        if (tickTopProc) tickTopProc.textContent = procs.length > 0 ? `${procs[0].name} (${procs[0].cpu_percent ?? 0}%)` : 'Нет активных';
      }

      const diskGroup = groups.find(g => g.group_id === 'storage_smart');
      if (diskGroup && diskGroup.payload) {
        const parts = diskGroup.payload.storage_partitions || [];
        if (tickDisks) tickDisks.textContent = parts.map(p => `${p.mountpoint || p.device || 'Vol'}: ${p.free_gb ?? 0} GB св.`).join(', ') || 'OK';
      }

      // Отрисовка начальных 4 карточек в режиме ожидания с уже доступными собранными метриками
      const cardsState = groups.map(g => {
        const keyMetrics = {};
        if (g.group_id === 'compute_thermals') {
          const cpu = g.payload?.cpu || {};
          keyMetrics['cpu_load'] = `${cpu.load_percent ?? 0}%`;
          keyMetrics['cpu_model'] = cpu.model || 'CPU';
          const temps = g.payload?.sensors?.temperatures_celsius || {};
          const maxT = Object.values(temps).length > 0 ? Math.max(...Object.values(temps)) : null;
          keyMetrics['max_temp'] = maxT !== null ? `${maxT}°C` : 'В норме';
        } else if (g.group_id === 'memory_processes') {
          const ram = g.payload?.ram || {};
          keyMetrics['ram_used'] = `${ram.used_gb ?? 0} / ${ram.total_gb ?? 0} GB (${ram.used_percent ?? 0}%)`;
          const procs = g.payload?.top_active_processes || [];
          keyMetrics['top_process'] = procs.length > 0 ? `${procs[0].name} (${procs[0].cpu_percent ?? 0}%)` : 'Нет';
        } else if (g.group_id === 'storage_smart') {
          const parts = g.payload?.storage_partitions || [];
          const maxUsed = parts.length > 0 ? Math.max(...parts.map(p => p.used_percent || 0)) : 0;
          keyMetrics['max_volume_fill'] = `${maxUsed}%`;
          keyMetrics['volumes_count'] = parts.length;
        } else if (g.group_id === 'system_network') {
          const updates = g.payload?.system_updates || {};
          keyMetrics['reboot_pending'] = updates.reboot_pending ? 'Да' : 'Нет';
          keyMetrics['update_status'] = updates.status || 'Up to date';
        }

        return {
          group_id: g.group_id,
          title: g.title,
          icon: g.icon,
          status: 'pending',
          summary: g.description,
          key_metrics: keyMetrics,
          payload: g.payload,
        };
      });
      renderAIDomainCards(cardsState);

      const completedGroups = [];

      // 2. Последовательный вызов каждой группы (цепочка Запрос -> Ответ -> Отображение)
      for (let i = 0; i < groups.length; i++) {
        const group = groups[i];
        const stepNum = i + 1;
        const totalSteps = groups.length;
        const pct = Math.round((stepNum / totalSteps) * 85);
        if (progressBar) progressBar.style.width = `${pct}%`;

        // Подсветка активного чипа собираемого домена
        if (group.group_id === 'compute_thermals') {
          if (chipLhm) chipLhm.className = 'badge bg-info text-dark border border-info fw-bold';
          if (chipWmi) chipWmi.className = 'badge bg-info text-dark border border-info fw-bold';
        } else if (group.group_id === 'memory_processes') {
          if (chipRam) chipRam.className = 'badge bg-info text-dark border border-info fw-bold';
        } else if (group.group_id === 'storage_smart') {
          if (chipDisks) chipDisks.className = 'badge bg-info text-dark border border-info fw-bold';
        } else if (group.group_id === 'system_network') {
          if (chipNet) chipNet.className = 'badge bg-info text-dark border border-info fw-bold';
        }

        if (liveStatusText) {
          liveStatusText.textContent = `🧠 Анализ [${stepNum}/${totalSteps}]: ${group.title} (оценка сенсоров и метрик)...`;
        }

        // Обновляем статус карточки на "Анализ"
        cardsState[i].status = 'analyzing';
        cardsState[i].summary = `🧠 Модель выполняет целевой анализ телеметрии группы ${stepNum}/${totalSteps}...`;
        renderAIDomainCards(cardsState);

        stagesLog.push({
          stage: 'group_run',
          title: `Группа ${stepNum}/${totalSteps}`,
          message: `🧠 [${stepNum}/${totalSteps}] Запрос модели: ${group.title}...`,
          details: group.description,
        });
        renderAIDiagnosticStages(stagesLog, false);

        // Запрос к AI модели по данной группе
        const res = await apiFetch('/api/v1/system/diagnose/group', {
          method: 'POST',
          body: JSON.stringify({
            group_id: group.group_id,
            title: group.title,
            payload: group.payload,
          }),
        });

        if (res) {
          cardsState[i] = res;
          completedGroups.push(res);
        } else {
          cardsState[i].status = 'warning';
          cardsState[i].summary = 'Ответ не получен, используются базовые метрики.';
          completedGroups.push(cardsState[i]);
        }

        // Отмечаем чип как завершенный (зеленый)
        if (group.group_id === 'compute_thermals') {
          if (chipLhm) chipLhm.className = 'badge bg-success-subtle text-success border border-success';
          if (chipWmi) chipWmi.className = 'badge bg-success-subtle text-success border border-success';
        } else if (group.group_id === 'memory_processes') {
          if (chipRam) chipRam.className = 'badge bg-success-subtle text-success border border-success';
        } else if (group.group_id === 'storage_smart') {
          if (chipDisks) chipDisks.className = 'badge bg-success-subtle text-success border border-success';
        } else if (group.group_id === 'system_network') {
          if (chipNet) chipNet.className = 'badge bg-success-subtle text-success border border-success';
        }

        // Немедленно обновляем красивую карточку на экране!
        renderAIDomainCards(cardsState);

        stagesLog.push({
          stage: 'group_done',
          title: `Группа ${stepNum} завершена`,
          message: `✅ [${stepNum}/${totalSteps}] ${group.title}: ${cardsState[i].status.toUpperCase()}`,
          details: cardsState[i].summary.substring(0, 120) + (cardsState[i].summary.length > 120 ? '...' : ''),
        });
        renderAIDiagnosticStages(stagesLog, false);
      }

      if (liveStatusText) {
        liveStatusText.textContent = '🏆 Поэтапный опрос и анализ всех доменов завершен.';
      }

      // 3. Финальный синтез итогового вердикта
      if (progressBar) progressBar.style.width = '95%';
      stagesLog.push({
        stage: 'synthesis',
        title: 'Финальный синтез',
        message: '🏆 Формирование итогового заключения и расчет Health Score...',
        details: 'Агрегация заключений всех 4 доменов',
      });
      renderAIDiagnosticStages(stagesLog, false);

      const synthesis = await apiFetch('/api/v1/system/diagnose/synthesize', {
        method: 'POST',
        body: JSON.stringify({ groups: completedGroups }),
      });

      if (progressBar) progressBar.style.width = '100%';

      // Обновление итогового Health Badge
      const score = Number(synthesis.health_score || 100);
      const healthClass = score >= 80 ? 'bg-success-subtle text-success border border-success' :
        score >= 60 ? 'bg-warning-subtle text-warning border border-warning' :
        'bg-danger-subtle text-danger border border-danger';

      if (badgeHealth) {
        badgeHealth.textContent = `Health: ${score}/100`;
        badgeHealth.className = `badge font-monospace ${healthClass}`;
      }
      if (badgeHealthBtn) {
        badgeHealthBtn.textContent = `Health: ${score}/100`;
        badgeHealthBtn.className = `badge font-monospace ms-1 ${healthClass}`;
      }

      if (engineTag) {
        engineTag.innerHTML = `<i class="bi bi-cpu me-1"></i>${escapeHtml(synthesis.ai_model_used || 'Heuristic Engine')}`;
      }

      if (synthesisStatus) {
        synthesisStatus.textContent = `${synthesis.status_label} (${score}/100)`;
        synthesisStatus.className = `badge font-monospace ${
          score >= 80 ? 'bg-success text-white' :
          score >= 60 ? 'bg-warning text-dark' :
          'bg-danger text-white'
        }`;
      }

      if (summaryEl) {
        summaryEl.textContent = synthesis.executive_summary || 'Анализ завершён.';
      }

      // Отрисовка приоритетных действий
      if (Array.isArray(synthesis.critical_actions) && synthesis.critical_actions.length > 0) {
        if (actionsBox && actionsList) {
          actionsBox.classList.remove('d-none');
          actionsList.innerHTML = synthesis.critical_actions.map(act => `<li class="mb-1"><i class="bi bi-arrow-right-short text-warning me-1"></i>${escapeHtml(act)}</li>`).join('');
        }
      }

      stagesLog.push({
        stage: 'done',
        title: 'Аудит завершен',
        message: `✅ Поэтапная AI-диагностика успешно завершена (Health: ${score}/100)`,
        details: 'Все 4 функциональные группы оценены моделью',
      });
      renderAIDiagnosticStages(stagesLog, true);

    } catch (e) {
      console.error('[AboutSystemTab] Grouped AI Diagnosis error:', e);
      if (summaryEl) summaryEl.textContent = 'Ошибка выполнения поэтапной AI-диагностики: ' + e.message;
      if (badgeHealth) {
        badgeHealth.textContent = 'Health: Error';
        badgeHealth.className = 'badge bg-danger-subtle text-danger border border-danger font-monospace';
      }
      if (badgeHealthBtn) {
        badgeHealthBtn.textContent = 'Health: Error';
        badgeHealthBtn.className = 'badge bg-danger-subtle text-danger border border-danger font-monospace ms-1';
      }
      if (errorSec) {
        errorSec.classList.remove('d-none');
        if (errorText) errorText.textContent = e.message;
      }
      stagesLog.push({
        stage: 'error',
        title: 'Ошибка',
        message: `❌ Ошибка выполнения: ${e.message}`,
        details: 'Проверьте доступность API-сервера',
      });
      renderAIDiagnosticStages(stagesLog, true);
    } finally {
      isAiRunning = false;
      
      // Сбрасываем флаг processing после завершения
      if (window.resetTabProcessing) {
        window.resetTabProcessing('tab-about-system');
      }
      
      if (btnRescan) btnRescan.disabled = false;
      if (icRescan) icRescan.className = 'bi bi-lightning-charge-fill';
      if (txtRescan) txtRescan.textContent = 'Rescan';
    }
  }


  async function fetchHardwareSpec() {
    const container = document.getElementById('about-sys-tree-container');
    const badgeCount = document.getElementById('about-sys-node-count');
    if (!container) return;

    try {
      const config = CACHE_STRATEGY.HARDWARE_SPEC;
      const nodes = await cachedFetch(
        '/api/v1/system/hardware',
        'hardware_spec',
        { ttl: config.ttl, strategy: config.strategy }
      );
      hardwareData = Array.isArray(nodes) ? nodes : [];

      if (badgeCount) {
        badgeCount.textContent = `${hardwareData.length} категорий`;
      }

      const searchInput = document.getElementById('about-sys-search');
      const filter = searchInput ? searchInput.value.trim().toLowerCase() : '';
      renderHardwareTree(hardwareData, filter);
    } catch (e) {
      console.error('[AboutSystemTab] Failed to fetch hardware spec:', e);
      container.innerHTML = `<div class="text-center py-4 text-danger small">Ошибка загрузки оборудования: ${escapeHtml(e.message)}</div>`;
    }
  }

  function renderDisksTable(disks) {
    const tbody = document.getElementById('about-sys-disks-tbody');
    const countBadge = document.getElementById('about-disks-count');
    if (!tbody) return;

    if (!Array.isArray(disks) || disks.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" class="text-center py-3 text-muted">Дисковые разделы не обнаружены</td></tr>';
      return;
    }

    if (countBadge) countBadge.textContent = `${disks.length} Drives`;

    tbody.innerHTML = disks.map(d => {
      const pct = Math.min(100, Math.max(0, d.percent || 0));
      let barClass = 'bg-info';
      if (pct > 88) barClass = 'bg-danger';
      else if (pct > 70) barClass = 'bg-warning';

      return `
        <tr>
          <td><i class="bi bi-hdd me-1 text-primary"></i><strong>${escapeHtml(d.device || d.mountpoint || 'C:\\')}</strong></td>
          <td><span class="badge bg-secondary-subtle text-secondary border border-secondary">${escapeHtml(d.fstype || 'NTFS')}</span></td>
          <td>${Number(d.total_gb || 0).toFixed(1)} GB</td>
          <td class="text-light">${Number(d.used_gb || 0).toFixed(1)} GB</td>
          <td class="text-info fw-semibold">${Number(d.free_gb || 0).toFixed(1)} GB</td>
          <td>
            <div class="d-flex align-items-center gap-2">
              <div class="about-sys-progress-track flex-grow-1" style="height: 6px;">
                <div class="about-sys-progress-bar ${barClass}" style="width: ${pct}%;"></div>
              </div>
              <span class="small" style="min-width: 42px; text-align: right;">${pct.toFixed(1)}%</span>
            </div>
          </td>
          <td><span class="about-sys-badge-ok">OK</span></td>
        </tr>
      `;
    }).join('');
  }

  function renderSensorsList(sensors) {
    const container = document.getElementById('about-sensors-container');
    if (!container) return;

    if (!Array.isArray(sensors) || sensors.length === 0) {
      container.innerHTML = '<div class="text-center py-4 text-muted small">Нет доступных сенсоров LHM</div>';
      return;
    }

    const searchInput = document.getElementById('about-sensor-search');
    const query = searchInput ? searchInput.value.trim().toLowerCase() : '';

    const filtered = sensors.filter(s => {
      if (activeSensorFilter !== 'all') {
        const cat = (s.category || '').toLowerCase();
        if (activeSensorFilter === 'temperature' && !cat.includes('temp')) return false;
        if (activeSensorFilter === 'voltage' && !cat.includes('volt')) return false;
        if (activeSensorFilter === 'clock' && !cat.includes('clock') && !cat.includes('freq')) return false;
        if (activeSensorFilter === 'power' && !cat.includes('power') && !cat.includes('load')) return false;
      }
      if (query) {
        return (s.name || '').toLowerCase().includes(query) || (s.category || '').toLowerCase().includes(query);
      }
      return true;
    });

    if (filtered.length === 0) {
      container.innerHTML = '<div class="text-center py-3 text-muted small">Сенсоры по заданному фильтру не найдены</div>';
      return;
    }

    container.innerHTML = filtered.map(s => {
      let icon = 'bi bi-thermometer-half text-danger';
      let valColor = 'text-info';
      const cat = (s.category || '').toLowerCase();

      if (cat.includes('volt')) {
        icon = 'bi bi-lightning-charge text-warning';
        valColor = 'text-warning';
      } else if (cat.includes('clock') || cat.includes('freq')) {
        icon = 'bi bi-speedometer text-info';
        valColor = 'text-info';
      } else if (cat.includes('power')) {
        icon = 'bi bi-plug text-success';
        valColor = 'text-success';
      } else if (cat.includes('load')) {
        icon = 'bi bi-percent text-primary';
        valColor = 'text-light';
      }

      return `
        <div class="d-flex align-items-center justify-content-between py-1 px-2 border-bottom border-secondary-subtle">
          <div class="d-flex align-items-center gap-2 text-truncate" style="max-width: 68%;">
            <i class="${icon}" style="font-size: 0.85rem;"></i>
            <span class="small text-truncate" title="${escapeHtml(s.name)}">${escapeHtml(s.name)}</span>
          </div>
          <div class="sensor-badge-val ${valColor}">${s.value} ${escapeHtml(s.unit || '')}</div>
        </div>
      `;
    }).join('');
  }

  function renderProcessesTable(procs) {
    const tbody = document.getElementById('about-sys-procs-tbody');
    if (!tbody) return;

    if (!Array.isArray(procs) || procs.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4 text-muted">Процессы не найдены</td></tr>';
      return;
    }

    const searchInput = document.getElementById('about-proc-search');
    const query = searchInput ? searchInput.value.trim().toLowerCase() : '';

    const filtered = procs.filter(p => {
      if (!query) return true;
      return String(p.pid).includes(query) ||
             (p.name || '').toLowerCase().includes(query) ||
             (p.username || '').toLowerCase().includes(query);
    });

    if (filtered.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4 text-muted">Процессы по запросу не найдены</td></tr>';
      return;
    }

    tbody.innerHTML = filtered.slice(0, 30).map(p => {
      const cpuVal = Number(p.cpu_percent || 0).toFixed(1);
      const memVal = Number(p.memory_mb || 0).toFixed(1);
      const isHigh = p.cpu_percent > 10;

      return `
        <tr>
          <td class="text-muted">${p.pid}</td>
          <td class="text-white fw-semibold text-truncate" style="max-width: 160px;" title="${escapeHtml(p.name)}">
            ${escapeHtml(p.name)}
          </td>
          <td><span class="badge bg-dark border border-secondary text-secondary" style="font-size: 0.68rem;">${escapeHtml(p.status || 'running')}</span></td>
          <td class="${isHigh ? 'text-danger fw-bold' : 'text-info'}">${cpuVal}%</td>
          <td class="text-light">${memVal} MB</td>
          <td class="text-secondary">${p.num_threads || 1}</td>
          <td class="text-muted small text-truncate" style="max-width: 140px;" title="${escapeHtml(p.username || '')}">
            ${escapeHtml(p.username || '-')}
          </td>
        </tr>
      `;
    }).join('');
  }

  function renderHardwareTree(nodes, filter) {
    const container = document.getElementById('about-sys-tree-container');
    if (!container) return;

    if (!Array.isArray(nodes) || nodes.length === 0) {
      container.innerHTML = '<div class="text-center py-4 text-muted small">Оборудование не обнаружено или опрашивается...</div>';
      return;
    }

    const filtered = nodes.filter(node => {
      if (!filter) return true;
      const catMatch = (node.category || '').toLowerCase().includes(filter);
      const nameMatch = (node.name || '').toLowerCase().includes(filter);
      const propsMatch = Object.entries(node.properties || {}).some(
        ([k, v]) => k.toLowerCase().includes(filter) || String(v).toLowerCase().includes(filter)
      );
      return catMatch || nameMatch || propsMatch;
    });

    if (filtered.length === 0) {
      container.innerHTML = `<div class="text-center py-4 text-muted small">По запросу «${escapeHtml(filter)}» компонентов не найдено</div>`;
      return;
    }

    container.innerHTML = filtered.map((node, idx) => {
      const propsEntries = Object.entries(node.properties || {});
      const propsHtml = propsEntries.length > 0
        ? propsEntries.map(([k, v]) => `
            <div class="about-sys-prop-row">
              <span class="about-sys-prop-key">${escapeHtml(k)}</span>
              <span class="about-sys-prop-val">${escapeHtml(String(v))}</span>
            </div>
          `).join('')
        : '<div class="text-muted small py-1">Свойства не указаны</div>';

      const iconClass = getNodeIcon(node.category);

      return `
        <div class="about-sys-tree-node">
          <div class="about-sys-tree-title" onclick="toggleNode(${idx})">
            <span class="d-flex align-items-center gap-2">
              <i class="${iconClass} text-info"></i>
              <strong>${escapeHtml(node.category)}:</strong>
              <span class="text-white">${escapeHtml(node.name || '')}</span>
            </span>
            <span class="about-sys-chevron" id="about-chevron-${idx}" style="font-size: 0.72rem; color: #38bdf8;">▼</span>
          </div>
          <div class="about-sys-tree-body" id="about-node-body-${idx}">
            ${propsHtml}
          </div>
        </div>
      `;
    }).join('');
  }

  window.toggleNode = function(idx) {
    const body = document.getElementById(`about-node-body-${idx}`);
    const chevron = document.getElementById(`about-chevron-${idx}`);
    if (body) {
      body.classList.toggle('d-none');
      if (chevron) {
        chevron.textContent = body.classList.contains('d-none') ? '▼' : '▲';
      }
    }
  };

  function getNodeIcon(category) {
    const cat = (category || '').toLowerCase();
    if (cat.includes('processor') || cat.includes('cpu')) return 'bi bi-cpu';
    if (cat.includes('module') || cat.includes('планка')) return 'bi bi-memory';
    if (cat.includes('memory') || cat.includes('ram')) return 'bi bi-sd-card';
    if (cat.includes('system') || cat.includes('os')) return 'bi bi-laptop';
    if (cat.includes('motherboard') || cat.includes('mainboard')) return 'bi bi-motherboard';
    if (cat.includes('display') || cat.includes('gpu') || cat.includes('video') || cat.includes('graphics')) return 'bi bi-gpu-card';
    if (cat.includes('physical') || cat.includes('диск')) return 'bi bi-hdd-fill';
    if (cat.includes('disk') || cat.includes('storage') || cat.includes('drive') || cat.includes('volume')) return 'bi bi-hdd-stack';
    if (cat.includes('network') || cat.includes('adapter') || cat.includes('ethernet')) return 'bi bi-ethernet';
    if (cat.includes('update') || cat.includes('servicing')) return 'bi bi-arrow-repeat';
    return 'bi bi-gear-fill';
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

  // Self-trigger if container is already in DOM
  if (document.getElementById('about-sys-wrapper') || document.getElementById('tab-about-system')) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => initAboutSystemTab());
    } else {
      setTimeout(() => initAboutSystemTab(), 10);
    }
  }
})();

