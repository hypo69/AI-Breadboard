/**
 * =============================================================================
 * Process Name: Windows About System Tab - Main Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля main.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/webgui/about_system_tab/main.js?v=20261001_v1" type="module"></script>
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: windows/api/webgui/about_system_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-06 18:34:00
 * =============================================================================
 */

// =============================================================================
// Process Name: About System Tab Web Controller
// =============================================================================
// Description:
//   Client-side JavaScript controller for the About System tab.
//   Provides real-time host telemetry, system identity & locale parameters,
//   AIDA64-like hardware tree, live top processes, disk volumes and security status.
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
// Updated: 2026-10-04 00:22:00
// =============================================================================

(function () {
  let hardwareData = [];
  let currentProcesses = [];
  let currentDisks = [];
  let isLiveActive = true;
  let liveIntervalId = null;
  let wearAutoRefreshTimer = null;
  let isUpdating = false;
  let isAiRunning = false;
  let activeHistoryMetric = 'all';
  
  // Кеш-стратегия и TTL
  const CACHE_STRATEGY = {
    HARDWARE_SPEC: { ttl: 30 * 60 * 1000, strategy: 'cache-first' },      // 30 мин, редко меняется
    SYSTEM_SUMMARY: { ttl: 5 * 1000, strategy: 'stale-while-revalidate' }, // 5 сек
    CONTROL_STATUS: { ttl: 60 * 1000, strategy: 'stale-while-revalidate' }, // 1 мин
    BACKUP_STATUS: { ttl: 5 * 60 * 1000, strategy: 'cache-first' },         // 5 мин
    STORAGE_BATTERY: { ttl: 10 * 1000, strategy: 'stale-while-revalidate' }, // 10 сек
    PANEL_KPI: { ttl: 5 * 1000, strategy: 'stale-while-revalidate' }         // 5 сек
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

  function setStatusText(id, isPositive, activeText = 'Active', inactiveText = 'Disabled') {
    const el = document.getElementById(id);
    if (!el) return;
    const active = Boolean(isPositive);
    el.textContent = active ? activeText : inactiveText;
    el.className = active ? 'text-success fw-bold' : 'text-danger fw-bold';
  }

  function setFormattedStatusHtml(id, text) {
    const el = document.getElementById(id);
    if (!el) return;
    if (!text) { el.innerHTML = '--'; return; }
    el.innerHTML = String(text)
      .replace(/\b(OFF|Disabled|Выключено|Отключен|Отключено|Inactive)\b/gi, '<strong class="text-danger fw-bold">$1</strong>')
      .replace(/\b(ON|Active|Enabled|Включен|Включено)\b/gi, '<strong class="text-success fw-bold">$1</strong>');
  }

  function setHtml(id, html) {
    const el = document.getElementById(id);
    if (el) el.innerHTML = html;
  }

  async function initAboutSystemTab() {
    console.log('[AboutSystemTab] Initializing tab controller...');
    bindEvents();
    bindAIEvents();
    bindHistoryEvents();
    bindRegionalEvents();
    updateLocalClock();
    updatePowerDisplay();
    
    // Проверка доступности кеша
    await updateCacheStatus();

    // Инициализация индивидуальных опросников и выпадающих списков частоты для всех панелей
    initPanelPollers();

    // Запуск таймера часов и статуса кеша
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
        await updateCacheStatus();
      }, 5000, { pollerId: 'tab-about-system_clock', immediate: true });
    } else {
      if (liveIntervalId) clearInterval(liveIntervalId);
      liveIntervalId = setInterval(async () => {
        updateLocalClock();
        await updateCacheStatus();
      }, 5000);
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
          window.setTabPollerEnabled('tab-about-system_clock', isLiveActive);
          Object.keys(panelPollingRegistry).forEach(pollId => {
            window.setTabPollerEnabled(`tab-about-system_${pollId}`, isLiveActive);
          });
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

    const procSearch = document.getElementById('about-proc-search');
    if (procSearch) {
      procSearch.oninput = () => {
        renderProcessesTable(currentProcesses);
      };
    }

    const btnWearRefresh = document.getElementById('btn-diag-wear-refresh');
    if (btnWearRefresh) {
      btnWearRefresh.onclick = () => fetchStorageBatteryWear(true);
    }

    const wearAutoSwitch = document.getElementById('diag-wear-auto-refresh');
    if (wearAutoSwitch) {
      wearAutoSwitch.onchange = (e) => {
        if (e.target.checked) {
          wearAutoRefreshTimer = setInterval(() => fetchStorageBatteryWear(true), 10000);
        } else if (wearAutoRefreshTimer) {
          clearInterval(wearAutoRefreshTimer);
          wearAutoRefreshTimer = null;
        }
      };
    }

    // Inline Edit: Hostname
    const btnHostEdit = document.getElementById('btn-host-inline-edit');
    const viewBox = document.getElementById('about-host-view-box');
    const editBox = document.getElementById('about-host-edit-box');
    const inputHost = document.getElementById('about-host-inline-input');
    const btnHostSave = document.getElementById('btn-host-inline-save');
    const btnHostCancel = document.getElementById('btn-host-inline-cancel');
    const reminderAlert = document.getElementById('about-host-reminder-alert');
    const reminderText = document.getElementById('about-host-reminder-text');

    function openHostEdit() {
      if (!viewBox || !editBox || !inputHost) return;
      const hostEl = document.getElementById('about-kpi-os-host');
      let currentHost = hostEl ? hostEl.textContent.replace(/^Host:\s*/i, '').trim() : '';
      if (!currentHost || currentHost === '--') currentHost = window.location.hostname || 'DELL-VOSTRO';
      inputHost.value = currentHost;
      viewBox.classList.add('d-none');
      viewBox.classList.remove('d-flex');
      editBox.classList.remove('d-none');
      editBox.classList.add('d-flex');
      inputHost.focus();
      inputHost.select();
    }

    function closeHostEdit() {
      if (!viewBox || !editBox) return;
      editBox.classList.add('d-none');
      editBox.classList.remove('d-flex');
      viewBox.classList.remove('d-none');
      viewBox.classList.add('d-flex');
    }

    if (btnHostEdit) {
      btnHostEdit.onclick = (e) => {
        e.preventDefault();
        openHostEdit();
      };
    }

    if (btnHostCancel) {
      btnHostCancel.onclick = (e) => {
        e.preventDefault();
        closeHostEdit();
      };
    }

    if (inputHost) {
      inputHost.onkeydown = (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          if (btnHostSave) btnHostSave.click();
        } else if (e.key === 'Escape') {
          e.preventDefault();
          closeHostEdit();
        }
      };
    }

    if (btnHostSave && inputHost) {
      btnHostSave.onclick = async (e) => {
        e.preventDefault();
        const newName = inputHost.value.trim();

        if (!newName) {
          if (window.showToast) window.showToast('Пожалуйста, введите новое имя компьютера', 'warning');
          return;
        }

        const validNamePattern = /^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,13}[a-zA-Z0-9])?$/;
        if (!validNamePattern.test(newName) || newName.length > 15) {
          if (window.showToast) window.showToast('Имя должно содержать от 1 до 15 символов (A-Z, 0-9, дефис) без пробелов', 'warning');
          return;
        }

        btnHostSave.disabled = true;
        inputHost.disabled = true;
        btnHostSave.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" style="width: 10px; height: 10px;"></span>';

        try {
          const res = await fetch('/api/v1/system/rename-computer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ new_name: newName, restart: false }),
          });
          const result = await res.json();
          if (res.ok && result.status === 'ok') {
            setText('about-kpi-os-host', `Host: ${newName}`);
            setText('about-ident-hostname', newName);
            closeHostEdit();

            // Показываем напоминание о перезагрузке
            if (reminderAlert) {
              reminderAlert.classList.remove('d-none');
              if (reminderText) {
                reminderText.textContent = `Имя компьютера изменено на «${newName}». Изменение сработает только после перезагрузки системы!`;
              }
            }
            if (window.showToast) {
              window.showToast(`✅ Имя изменено на «${newName}». Напоминание: требуется перезагрузка для применения!`, 'warning');
            }
          } else {
            const errMsg = result.message || result.detail || 'Не удалось изменить имя компьютера.';
            if (window.showToast) window.showToast(`Ошибка: ${errMsg}`, 'danger');
            else alert(errMsg);
          }
        } catch (err) {
          const errMsg = `Сетевая ошибка: ${err.message}`;
          if (window.showToast) window.showToast(errMsg, 'danger');
          else alert(errMsg);
        } finally {
          btnHostSave.disabled = false;
          inputHost.disabled = false;
          btnHostSave.innerHTML = '<i class="bi bi-check-lg"></i>';
        }
      };
    }

    // Inline Edit: Workgroup
    const btnWgEdit = document.getElementById('btn-workgroup-inline-edit');
    const wgViewBox = document.getElementById('about-workgroup-view-box');
    const wgEditBox = document.getElementById('about-workgroup-edit-box');
    const inputWg = document.getElementById('about-workgroup-inline-input');
    const btnWgSave = document.getElementById('btn-workgroup-inline-save');
    const btnWgCancel = document.getElementById('btn-workgroup-inline-cancel');

    function openWgEdit() {
      if (!wgViewBox || !wgEditBox || !inputWg) return;
      const wgEl = document.getElementById('about-kpi-os-workgroup');
      let currentWg = wgEl ? wgEl.textContent.replace(/^Workgroup:\s*/i, '').trim() : '';
      if (!currentWg || currentWg === '--') currentWg = 'WORKGROUP';
      inputWg.value = currentWg;
      wgViewBox.classList.add('d-none');
      wgViewBox.classList.remove('d-flex');
      wgEditBox.classList.remove('d-none');
      wgEditBox.classList.add('d-flex');
      inputWg.focus();
      inputWg.select();
    }

    function closeWgEdit() {
      if (!wgViewBox || !wgEditBox) return;
      wgEditBox.classList.add('d-none');
      wgEditBox.classList.remove('d-flex');
      wgViewBox.classList.remove('d-none');
      wgViewBox.classList.add('d-flex');
    }

    if (btnWgEdit) {
      btnWgEdit.onclick = (e) => {
        e.preventDefault();
        openWgEdit();
      };
    }

    if (btnWgCancel) {
      btnWgCancel.onclick = (e) => {
        e.preventDefault();
        closeWgEdit();
      };
    }

    if (inputWg) {
      inputWg.onkeydown = (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          if (btnWgSave) btnWgSave.click();
        } else if (e.key === 'Escape') {
          e.preventDefault();
          closeWgEdit();
        }
      };
    }

    if (btnWgSave && inputWg) {
      btnWgSave.onclick = async (e) => {
        e.preventDefault();
        const newWg = inputWg.value.trim().toUpperCase();

        if (!newWg) {
          if (window.showToast) window.showToast('Пожалуйста, введите имя рабочей группы', 'warning');
          return;
        }

        const validWgPattern = /^[a-zA-Z0-9_\-]{1,15}$/;
        if (!validWgPattern.test(newWg)) {
          if (window.showToast) window.showToast('Имя группы должно содержать от 1 до 15 символов (A-Z, 0-9, -, _)', 'warning');
          return;
        }

        btnWgSave.disabled = true;
        inputWg.disabled = true;
        btnWgSave.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" style="width: 10px; height: 10px;"></span>';

        try {
          const res = await fetch('/api/v1/system/change-workgroup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ new_workgroup: newWg, restart: false }),
          });
          const result = await res.json();
          if (res.ok && result.status === 'ok') {
            setText('about-kpi-os-workgroup', `Workgroup: ${newWg}`);
            closeWgEdit();

            // Показываем напоминание о перезагрузке
            if (reminderAlert) {
              reminderAlert.classList.remove('d-none');
              if (reminderText) {
                reminderText.textContent = `Рабочая группа изменена на «${newWg}». Изменение сработает только после перезагрузки системы!`;
              }
            }
            if (window.showToast) {
              window.showToast(`✅ Рабочая группа изменена на «${newWg}». Напоминание: требуется перезагрузка для применения!`, 'warning');
            }
          } else {
            const errMsg = result.message || result.detail || 'Не удалось изменить рабочую группу.';
            if (window.showToast) window.showToast(`Ошибка: ${errMsg}`, 'danger');
            else alert(errMsg);
          }
        } catch (err) {
          const errMsg = `Сетевая ошибка: ${err.message}`;
          if (window.showToast) window.showToast(errMsg, 'danger');
          else alert(errMsg);
        } finally {
          btnWgSave.disabled = false;
          inputWg.disabled = false;
          btnWgSave.innerHTML = '<i class="bi bi-check-lg"></i>';
        }
      };
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
          apiFetch('/api/v1/windows-backup/health').then(data => {
            if (window.browserCache) {
              window.browserCache.set(CACHE_STORE, 'backup_status', data, { 
                ttl: CACHE_STRATEGY.BACKUP_STATUS.ttl, 
                tags: [CACHE_TAG] 
              });
            }
            return fetchBackupStatus();
          }),
          apiFetch('/api/v1/system/diagnostics/storage-battery').then(data => {
            if (window.browserCache) {
              window.browserCache.set(CACHE_STORE, 'storage_battery_wear', data, {
                ttl: CACHE_STRATEGY.STORAGE_BATTERY.ttl,
                tags: [CACHE_TAG]
              });
            }
            return fetchStorageBatteryWear(true);
          }),
          fetchKpiPanels(true)
        ]);
      } else {
        await Promise.allSettled([
          fetchSystemSummary(),
          fetchSystemControlStatus(),
          fetchHardwareSpec(),
          fetchBackupStatus(),
          fetchStorageBatteryWear(),
          fetchKpiPanels(false)
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

  /**
   * Обновление панели "Питание и Энергия" в таблице спецификации оборудования и ОС.
   * @param {Object} [batteryWear] - Объект телеметрии батареи/питания
   * @param {string} [powerProfileName] - Название активной схемы электропитания
   */
  function updatePowerDisplay(batteryWear = null, powerProfileName = '') {
    const badgeEl = document.getElementById('about-spec-power-badge');
    const sourceEl = document.getElementById('about-spec-power-source');
    const profileEl = document.getElementById('about-spec-power-profile');
    const legacyEl = document.getElementById('about-spec-power');

    let badgeText = 'AC Mains';
    let badgeClass = 'bg-secondary';
    let sourceText = 'Питание: Стационарная электросеть 220V';
    let profileText = powerProfileName ? `Профиль: ${powerProfileName}` : 'Профиль: AC Mains / Desktop';

    if (batteryWear) {
      if (batteryWear.has_battery) {
        badgeText = batteryWear.is_charging ? 'AC Adapter' : 'Battery';
        badgeClass = batteryWear.is_charging ? 'bg-success' : (batteryWear.percent < 20 ? 'bg-danger' : 'bg-warning text-dark');
        sourceText = `Батарея: ${batteryWear.percent}% (${batteryWear.is_charging ? 'Заряжается' : 'Работа от батареи'})`;
      } else {
        badgeText = batteryWear.power_source ? (batteryWear.power_source.includes('AC') ? 'AC Mains' : batteryWear.power_source) : 'AC Mains';
        badgeClass = 'bg-secondary';
        sourceText = 'Питание: Стационарная электросеть 220V';
      }
    }

    if (badgeEl) {
      badgeEl.textContent = badgeText;
      badgeEl.className = `badge ${badgeClass} font-monospace`;
    }
    if (sourceEl) {
      sourceEl.textContent = sourceText;
    }
    if (profileEl) {
      if (powerProfileName) {
        profileEl.textContent = `Профиль: ${powerProfileName}`;
      } else if (!profileEl.textContent || profileEl.textContent.trim() === '' || profileEl.textContent === 'Профиль: --') {
        profileEl.textContent = profileText;
      }
    }
    if (legacyEl) {
      legacyEl.textContent = `${sourceText} | ${profileText}`;
    }
  }

  async function fetchStorageBatteryWear(forceNetwork = false) {
    try {
      const config = CACHE_STRATEGY.STORAGE_BATTERY;
      const data = await cachedFetch(
        '/api/v1/system/diagnostics/storage-battery',
        'storage_battery_wear',
        { ttl: config.ttl, strategy: config.strategy, forceNetwork }
      );
      if (!data) return;

      // Disks Wear & SMART
      const disksTbody = document.getElementById('diag-wear-disks-tbody');
      if (disksTbody && data.disks_wear) {
        setText('diag-wear-disks-count', `${data.disks_wear.length} дисков`);
        if (data.disks_wear.length === 0) {
          disksTbody.innerHTML = '<tr><td colspan="9" class="text-center py-4 text-muted">Физических накопителей не обнаружено</td></tr>';
        } else {
          const formatBytesLocal = (bytes) => {
            if (bytes == null || bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
          };

          const formatPohLocal = (hours) => {
            if (hours == null || hours <= 0) return null;
            const days = Math.floor(hours / 24);
            const years = (hours / (24 * 365.25)).toFixed(1);
            if (days >= 365) return `${hours.toLocaleString()} ч (≈ ${years} г)`;
            if (days >= 1) return `${hours.toLocaleString()} ч (${days} д)`;
            return `${hours.toLocaleString()} ч`;
          };

          disksTbody.innerHTML = data.disks_wear.map(d => {
            const diskName = d.name || d.model || d.device_id || 'Физический диск';
            const devId = d.device_id ? `<span class="badge bg-secondary-subtle text-light border border-secondary me-1.5">${escapeHtml(d.device_id)}</span>` : '';
            const isSsd = (d.media_type && d.media_type.toUpperCase().includes('SSD')) || (d.bus_type && d.bus_type.toUpperCase().includes('NVME'));
            const diskIcon = isSsd ? 'bi-device-ssd text-info' : 'bi-hdd text-primary';
            const typeBus = [d.media_type, d.bus_type].filter(Boolean).join(' / ') || 'Storage';
            const partsBadge = d.partitions && d.partitions !== '—'
              ? `<span class="badge bg-primary-subtle text-info border border-info-subtle font-monospace">${escapeHtml(d.partitions)}</span>`
              : '<span class="text-muted">—</span>';
            const freeGbStr = d.free_gb != null ? `${d.free_gb} GB` : '<span class="text-muted">—</span>';
            const healthPct = d.health_pct != null ? d.health_pct : 100;
            const healthColor = healthPct >= 80 ? 'success' : (healthPct >= 50 ? 'warning' : 'danger');

            // Наработка и дата первого включения
            const pohFormatted = formatPohLocal(d.power_on_hours);
            const pohHtml = pohFormatted
              ? `<div class="font-monospace text-info">${pohFormatted}</div><div class="small text-muted font-monospace mt-0.5">Старт: ${escapeHtml(d.first_power_on || '—')}</div>`
              : '<span class="text-muted font-monospace small">—</span>';

            // Объемы ввода/вывода (запись и чтение)
            const ioHtml = `
              <div class="font-monospace text-light" style="white-space: nowrap;" title="Записано за сессию">
                <i class="bi bi-arrow-up-circle text-warning me-1"></i>Записано: ${formatBytesLocal(d.bytes_written)}
              </div>
              <div class="small font-monospace text-info mt-0.5" style="white-space: nowrap;" title="Прочитано за сессию">
                <i class="bi bi-arrow-down-circle text-info me-1"></i>Прочитано: ${formatBytesLocal(d.bytes_read)}
              </div>
            `;

            return `
            <tr>
              <td class="fw-bold text-white">
                <div class="d-flex align-items-center">
                  <i class="bi ${diskIcon} me-2 fs-6"></i>
                  <div>
                    <div class="text-truncate" style="max-width: 250px;" title="${escapeHtml(diskName)}">${escapeHtml(diskName)}</div>
                    <div class="small text-muted font-monospace mt-0.5">${devId}${d.serial_number && d.serial_number !== 'N/A' ? `<span class="text-secondary">S/N: ${escapeHtml(d.serial_number)}</span>` : ''}</div>
                  </div>
                </div>
              </td>
              <td class="text-muted font-monospace"><span class="badge bg-dark border border-secondary text-light">${escapeHtml(typeBus)}</span></td>
              <td>${partsBadge}</td>
              <td style="text-align: right;" class="text-light font-monospace">${d.total_gb} GB</td>
              <td style="text-align: right;" class="text-success font-monospace">${freeGbStr}</td>
              <td>${pohHtml}</td>
              <td style="text-align: right;">${ioHtml}</td>
              <td>
                <div class="d-flex align-items-center gap-1.5">
                  <div class="about-sys-progress-track flex-grow-1" style="height: 6px; min-width: 55px;">
                    <div class="about-sys-progress-bar bg-${healthColor}" style="width: ${healthPct}%;"></div>
                  </div>
                  <span class="small font-monospace text-${healthColor} ms-1">${healthPct}%</span>
                </div>
              </td>
              <td><span class="badge bg-${healthColor}-subtle text-${healthColor} border border-${healthColor}">${escapeHtml(d.status || 'OK')}</span></td>
            </tr>
          `;}).join('');
        }
      }

      // Battery Degradation
      const batContainer = document.getElementById('diag-battery-details-container');
      const batSourceBadge = document.getElementById('diag-battery-source-badge');
      if (batContainer && data.battery_wear) {
        const b = data.battery_wear;
        updatePowerDisplay(b);
        if (batSourceBadge) {
          batSourceBadge.textContent = b.power_source || 'AC Mains';
        }
        if (!b.has_battery) {
          batContainer.innerHTML = `
            <div class="text-center py-4 text-muted small">
              <i class="bi bi-plug-fill fs-4 text-info d-block mb-1"></i>
              Стационарный компьютер — питание напрямую от электросети
            </div>
          `;
        } else {
          batContainer.innerHTML = `
            <table class="about-sys-spec-table">
              <tbody>
                <tr>
                  <td class="about-sys-spec-key"><i class="bi bi-battery-charging me-1.5 text-warning"></i>Уровень заряда</td>
                  <td class="about-sys-spec-val fw-bold text-white">${b.percent}% (${b.is_charging ? 'Заряжается' : 'Разряд'})</td>
                </tr>
                <tr>
                  <td class="about-sys-spec-key"><i class="bi bi-shield-shaded me-1.5 text-info"></i>Заводская емкость</td>
                  <td class="about-sys-spec-val font-monospace">${b.design_capacity_mwh ? b.design_capacity_mwh + ' mWh' : '--'}</td>
                </tr>
                <tr>
                  <td class="about-sys-spec-key"><i class="bi bi-battery-full me-1.5 text-success"></i>Текущая емкость</td>
                  <td class="about-sys-spec-val font-monospace">${b.full_charge_capacity_mwh ? b.full_charge_capacity_mwh + ' mWh' : '--'}</td>
                </tr>
                <tr>
                  <td class="about-sys-spec-key"><i class="bi bi-heart-pulse me-1.5 text-danger"></i>Деградация (Износ)</td>
                  <td class="about-sys-spec-val ${b.wear_level_pct > 20 ? 'text-danger fw-bold' : 'text-success'}">
                    ${b.wear_level_pct}% износа
                  </td>
                </tr>
              </tbody>
            </table>
          `;
        }
      }
    } catch (err) {
      console.warn('[AboutSystemTab] fetchStorageBatteryWear error:', err);
    }
  }

  /**
   * Гранулярные функции получения данных для каждой карточки KPI
   */
  async function fetchKpiOs(forceNetwork = false) {
    try {
      const config = CACHE_STRATEGY.PANEL_KPI || { ttl: 5000, strategy: 'stale-while-revalidate' };
      const opts = { ttl: config.ttl, strategy: config.strategy, forceNetwork };
      const data = await cachedFetch('/api/v1/dashboard/os', 'dash_os', opts);
      if (data) {
        if (data.display_title) setText('about-kpi-os-title', data.display_title);
        if (data.display_host) setText('about-kpi-os-host', data.display_host);
        if (data.workgroup) setText('about-kpi-os-workgroup', `Workgroup: ${data.workgroup}`);
        else if (data.display_workgroup) setText('about-kpi-os-workgroup', data.display_workgroup);
        if (data.uptime_human) setText('about-spec-uptime', `Uptime: ${data.uptime_human}`);
        if (data.os_build) setText('about-spec-os', data.os_build);
        if (data.os_install_date) {
          setText('about-ident-install-date', data.os_install_date);
        }
      }
    } catch (e) {
      console.warn('[AboutSystemTab] fetchKpiOs error:', e);
    }
  }

  async function fetchKpiSecurity(forceNetwork = false) {
    try {
      const config = CACHE_STRATEGY.PANEL_KPI || { ttl: 5000, strategy: 'stale-while-revalidate' };
      const opts = { ttl: config.ttl, strategy: config.strategy, forceNetwork };
      const data = await cachedFetch('/api/v1/dashboard/security', 'dash_sec', opts);
      if (data) {
        if (data.display_title) {
          const el = document.getElementById('about-kpi-sec-title');
          if (el) {
            el.textContent = data.display_title;
            el.className = `about-sys-value ${data.status === 'Active & Protected' ? 'text-success' : 'text-danger fw-bold'} text-truncate mt-1`;
          }
        }
        if (data.display_subtitle) setFormattedStatusHtml('about-kpi-sec-sub', data.display_subtitle);
      }
    } catch (e) {
      console.warn('[AboutSystemTab] fetchKpiSecurity error:', e);
    }
  }

  async function fetchKpiCheckpoints(forceNetwork = false) {
    try {
      const config = CACHE_STRATEGY.PANEL_KPI || { ttl: 5000, strategy: 'stale-while-revalidate' };
      const opts = { ttl: config.ttl, strategy: config.strategy, forceNetwork };
      const data = await cachedFetch('/api/v1/dashboard/checkpoints', 'dash_chk', opts);
      if (data) {
        if (data.display_title) setText('about-kpi-prot-title', data.display_title);
        if (data.display_subtitle) setFormattedStatusHtml('about-kpi-prot-sub', data.display_subtitle);
      }
    } catch (e) {
      console.warn('[AboutSystemTab] fetchKpiCheckpoints error:', e);
    }
  }

  async function fetchKpiStorage(forceNetwork = false) {
    try {
      const config = CACHE_STRATEGY.PANEL_KPI || { ttl: 5000, strategy: 'stale-while-revalidate' };
      const opts = { ttl: config.ttl, strategy: config.strategy, forceNetwork };
      const data = await cachedFetch('/api/v1/dashboard/storage', 'dash_stor', opts);
      if (data) {
        if (data.display_title) setText('about-kpi-stor-title', data.display_title);
        if (data.display_subtitle) setText('about-kpi-stor-clean', data.display_subtitle);
      }
    } catch (e) {
      console.warn('[AboutSystemTab] fetchKpiStorage error:', e);
    }
  }

  async function fetchHardwareSpecs(forceNetwork = false) {
    await fetchHardwareSpec(forceNetwork);
  }

  async function fetchUserEnvSecurity(forceNetwork = false) {
    await Promise.allSettled([
      fetchSystemSummary(forceNetwork ? false : true),
      fetchSystemControlStatus(forceNetwork),
      fetchBackupStatus(forceNetwork)
    ]);
  }

  async function fetchDisksVolumes(forceNetwork = false) {
    await fetchSystemSummary(forceNetwork ? false : true);
  }

  async function fetchWearPanel(forceNetwork = false) {
    await fetchStorageBatteryWear(forceNetwork);
  }

  async function fetchBatteryPanel(forceNetwork = false) {
    await fetchStorageBatteryWear(forceNetwork);
  }

  async function fetchHwTreePanel(forceNetwork = false) {
    await fetchHardwareSpec(forceNetwork);
  }

  /**
   * Загрузка всех 4 сводных KPI-карточек
   */
  async function fetchKpiPanels(forceNetwork = false) {
    await Promise.allSettled([
      fetchKpiOs(forceNetwork),
      fetchKpiSecurity(forceNetwork),
      fetchKpiCheckpoints(forceNetwork),
      fetchKpiStorage(forceNetwork)
    ]);
  }

  /**
   * Реестр панелей и частоты их опроса
   */
  const panelPollingRegistry = {
    'about_kpi_os': { fn: fetchKpiOs, defaultFreq: 'manual' },
    'about_kpi_sec': { fn: fetchKpiSecurity, defaultFreq: 'manual' },
    'about_kpi_prot': { fn: fetchKpiCheckpoints, defaultFreq: 'manual' },
    'about_kpi_stor': { fn: fetchKpiStorage, defaultFreq: 'manual' },
    'about_hw_specs': { fn: fetchHardwareSpecs, defaultFreq: 'start' },
    'about_user_env': { fn: fetchUserEnvSecurity, defaultFreq: 'manual' },
    'about_disks': { fn: fetchDisksVolumes, defaultFreq: 'manual' },
    'about_wear': { fn: fetchWearPanel, defaultFreq: 'manual' },
    'about_battery': { fn: fetchBatteryPanel, defaultFreq: 'manual' },
    'about_hw_tree': { fn: fetchHwTreePanel, defaultFreq: 'start' }
  };

  const panelTimers = new Map();

  function getPanelFrequency(pollId) {
    try {
      const saved = localStorage.getItem(`poll_freq_${pollId}`);
      if (saved !== null && saved !== undefined && saved !== '') return saved;
    } catch (_) {}
    return panelPollingRegistry[pollId]?.defaultFreq || 'start';
  }

  function setPanelFrequency(pollId, freq) {
    try {
      localStorage.setItem(`poll_freq_${pollId}`, freq);
    } catch (_) {}
    applyPanelPoller(pollId, freq, false);
  }

  function stopPanelPoller(pollId) {
    const pollerId = `tab-about-system_${pollId}`;
    if (window.unregisterTabPoller) {
      window.unregisterTabPoller(pollerId);
    }
    if (panelTimers.has(pollId)) {
      clearInterval(panelTimers.get(pollId));
      panelTimers.delete(pollId);
    }
  }

  function applyPanelPoller(pollId, freq, runInitial = false) {
    stopPanelPoller(pollId);
    const config = panelPollingRegistry[pollId];
    if (!config) return;

    if (freq === 'start') {
      if (runInitial) {
        config.fn();
      }
      return;
    }

    if (freq === 'manual') {
      if (runInitial) {
        config.fn();
      }
      return;
    }

    const intervalSec = parseInt(freq, 10);
    if (isNaN(intervalSec) || intervalSec <= 0) return;

    const intervalMs = intervalSec * 1000;
    const pollerId = `tab-about-system_${pollId}`;

    if (window.registerTabPoller) {
      window.registerTabPoller('tab-about-system', async () => {
        if (isLiveActive && !isUpdating) {
          await config.fn();
        }
      }, intervalMs, { pollerId, immediate: runInitial });
    } else {
      if (runInitial) config.fn();
      const timer = setInterval(async () => {
        if (isLiveActive && !isUpdating) {
          await config.fn();
        }
      }, intervalMs);
      panelTimers.set(pollId, timer);
    }
  }

  function initPanelPollers() {
    document.querySelectorAll('.poll-freq-select').forEach(select => {
      const pollId = select.dataset.pollId;
      if (!pollId) return;

      const currentFreq = getPanelFrequency(pollId);
      select.value = currentFreq;

      select.onchange = (e) => {
        const newFreq = e.target.value;
        setPanelFrequency(pollId, newFreq);
        if (newFreq !== 'manual' && newFreq !== 'start') {
          panelPollingRegistry[pollId]?.fn(true);
        }
        if (window.showToast) {
          const label = select.options[select.selectedIndex]?.text || newFreq;
          window.showToast(`Частота опроса обновлена: ${label}`, 'info');
        }
      };

      applyPanelPoller(pollId, currentFreq, true);
    });
  }

  async function pollLiveTelemetry() {
    isUpdating = true;
    try {
      await fetchSystemSummary(true);
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
      const instLang = snap.os_install_language || snap.install_language || '';
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
      const localesText = instLang
        ? `Локали: User: ${userLoc} | Sys: ${sysLoc} | Оригинал: ${instLang}`
        : `Локали: User: ${userLoc} | Sys: ${sysLoc}`;
      setText('about-ident-locales', localesText);
      setText('about-ident-timezone', tz);
      setText('about-ident-codepage', `Кодировка: ${cp}`);
      setText('about-ident-inputs', inputs);
      const installDate = snap.os_install_date || 'Не определена';
      setText('about-ident-install-date', installDate);

      // Top KPI Card 1: Operating System
      setText('about-kpi-os-title', `${snap.os_name || 'Windows 11'} (${snap.cpu?.architecture || 'AMD64'})`);
      setText('about-kpi-os-host', `Host: ${host}`);
      const wg = snap.workgroup || 'WORKGROUP';
      setText('about-kpi-os-workgroup', `Workgroup: ${wg}`);

  /**
   * Форматирование коммерческого названия процессора (например, Intel Core i5-10400)
   * @param {string} rawModel - Название модели (из реестра или API)
   * @returns {string} Чистое коммерческое наименование
   */
  function formatCpuCommercial(rawModel) {
    if (!rawModel) return 'Intel Core i5-10400';
    
    // Если передана сырая строка CPUID
    if (rawModel.includes('Family 6 Model 165') || rawModel.includes('Intel64 Family 6 Model 165')) {
      return 'Intel Core i5-10400';
    }

    // Очистка от знаков (R), (TM), слова CPU, частоты @ ... GHz, лишних суффиксов
    let clean = rawModel
      .replace(/\(R\)/gi, '')
      .replace(/\(TM\)/gi, '')
      .replace(/\bCPU\b/gi, '')
      .replace(/@.*$/i, '')
      .replace(/\b\d+-Core Processor\b/gi, '')
      .replace(/\s+/g, ' ')
      .trim();

    return clean || 'Intel Core i5-10400';
  }

      // 2. Telemetry Live & Spec Table
      if (snap.cpu) {
        // Specification Table CPU
        setText('about-spec-cpu', formatCpuCommercial(snap.cpu.model));
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

      // 5.3 Power & Energy Block
      if (snap.battery) {
        updatePowerDisplay(snap.battery, snap.power_profile || snap.battery.power_profile);
      } else {
        updatePowerDisplay(null, snap.power_profile);
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
      const kpiSecTitle = document.getElementById('about-kpi-sec-title');
      if (kpiSecTitle) {
        kpiSecTitle.textContent = defActive ? 'Active & Protected' : 'Attention Required';
        kpiSecTitle.className = `about-sys-value ${defActive ? 'text-success' : 'text-danger fw-bold'} text-truncate mt-1`;
      }
      const fwOk = sec.firewall_overall_enabled !== false;
      const uacOk = sec.uac_enabled !== false;
      setFormattedStatusHtml('about-kpi-sec-sub', `Firewall: ${fwOk ? 'ON' : 'OFF'} | UAC: ${uacOk ? 'ON' : 'OFF'}`);

      // KPI 3: System Protection
      const countPoints = rest.restore_points_count || 0;
      setText('about-kpi-prot-title', `${countPoints} Checkpoints`);
      const protActive = Boolean(rest.system_protection_enabled);
      setFormattedStatusHtml('about-kpi-prot-sub', `Protection: ${protActive ? 'Active' : 'Disabled'}`);

      // KPI 4: Cleanable estimate & Total Disk Size
      const cleanMb = disk.cleanup_estimate?.total_cleanable_mb || 150;
      const cDrive = currentDisks.find(d => (d.device || '').toUpperCase().startsWith('C')) || currentDisks[0];
      const totalGbTxt = cDrive ? ` | Всего: ${Number(cDrive.total_gb || 0).toFixed(1)} GB` : '';
      setText('about-kpi-stor-clean', `Cleanable: ~${cleanMb} MB${totalGbTxt}`);

      // Security table rows
      setStatusText('about-sec-defender', defActive, 'Enabled', 'Disabled');
      setStatusText('about-sec-realtime', sec.realtime_protection_enabled !== false && sec.realtime_protection_enabled !== 0 && sec.realtime_protection_enabled !== 'Disabled', 'Enabled', 'Disabled');
      
      const fwDom = sec.firewall_profiles?.Domain ?? sec.firewall_domain_enabled;
      const fwPriv = sec.firewall_profiles?.Private ?? sec.firewall_private_enabled;
      const fwPub = sec.firewall_profiles?.Public ?? sec.firewall_public_enabled;

      setStatusText('about-sec-fw-domain', fwDom === true || fwDom === 'Active' || fwDom === 1 || fwDom === 'ON', 'Active', 'Disabled');
      setStatusText('about-sec-fw-private', fwPriv === true || fwPriv === 'Active' || fwPriv === 1 || fwPriv === 'ON', 'Active', 'Disabled');
      setStatusText('about-sec-fw-public', fwPub === true || fwPub === 'Active' || fwPub === 1 || fwPub === 'ON', 'Active', 'Disabled');
      setStatusText('about-sec-uac', uacOk, 'Enabled', 'Disabled');

      // Power Scheme & Updates
      if (pwr.active_plan_name) {
        updatePowerDisplay(null, pwr.active_plan_name);
      }
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


  async function fetchHardwareSpec(forceNetwork = false) {
    const container = document.getElementById('about-sys-tree-container');
    const badgeCount = document.getElementById('about-sys-node-count');
    if (!container) return;

    try {
      const config = CACHE_STRATEGY.HARDWARE_SPEC;
      const nodes = await cachedFetch(
        '/api/v1/system/hardware',
        'hardware_spec',
        { ttl: config.ttl, strategy: config.strategy, forceNetwork }
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
      container.innerHTML = `
        <div class="text-center py-4 text-danger small">
          <div><i class="bi bi-exclamation-circle me-1"></i> Ошибка загрузки оборудования: ${escapeHtml(e.message)}</div>
          <button class="btn btn-sm btn-outline-primary mt-2" type="button" onclick="window.fetchHardwareSpec ? window.fetchHardwareSpec(true) : null">
            <i class="bi bi-arrow-clockwise me-1"></i> Повторить попытку
          </button>
        </div>
      `;
    }
  }
  window.fetchHardwareSpec = fetchHardwareSpec;

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

      const devStr = String(d.device || d.mountpoint || '');
      const volStr = String(d.volume_name || '');
      const isGoogleDrive = d.is_virtual || d.drive_type === 'Google Drive' || volStr.toLowerCase().includes('google') || volStr.includes('@') || devStr.startsWith('G:') || devStr.startsWith('J:');

      let driveIcon = 'bi-hdd-fill text-primary';
      let driveBadge = '';
      let driveSubtitle = '';
      let fsBadge = `<span class="badge" style="background: var(--surface-2, rgba(255,255,255,0.06)); color: var(--text-color, #f8fafc); border: 1px solid var(--border-subtle, rgba(255,255,255,0.1)); font-family: var(--font-mono); font-size: 0.72rem; font-weight: 500;">${escapeHtml(d.fstype || 'NTFS')}</span>`;
      let smartBadge = `<span class="about-sys-badge-ok">OK</span>`;

      if (isGoogleDrive) {
        driveIcon = 'bi-cloud-fill text-warning';
        driveBadge = `<span class="badge bg-warning-subtle text-warning border border-warning-subtle ms-1 font-monospace" style="font-size: 0.68rem;">Google Drive</span>`;
        let emailDesc = 'Google Drive for Desktop';
        if (volStr.includes('@')) {
          emailDesc = volStr.replace(' - Google Drive', '').replace(' - Goog...', '');
        } else if (devStr.startsWith('G:')) {
          emailDesc = 'one.last.bit@gmail.com';
        } else if (devStr.startsWith('J:')) {
          emailDesc = 'e.cat.co.il@gmail.com';
        }
        driveSubtitle = `<div class="small text-muted font-monospace mt-0.5">${escapeHtml(emailDesc)}</div>`;
        fsBadge = `<span class="badge" style="background: var(--surface-2, rgba(255,255,255,0.06)); color: var(--accent-color, #38bdf8); border: 1px solid var(--border-subtle, rgba(255,255,255,0.1)); font-family: var(--font-mono); font-size: 0.72rem; font-weight: 500;">Virtual ${escapeHtml(d.fstype || 'FAT32')}</span>`;
        smartBadge = `<span class="badge font-monospace" title="Виртуальный диск Google Drive — аппаратный контроллер S.M.A.R.T. отсутствует" style="background: var(--surface-2); color: var(--text-muted); border: 1px solid var(--border-subtle); font-size: 0.68rem;">N/A (Облако)</span>`;
      } else if (d.volume_name) {
        driveSubtitle = `<div class="small text-muted font-monospace mt-0.5">${escapeHtml(d.volume_name)}</div>`;
      }

      return `
        <tr>
          <td>
            <div class="d-flex align-items-center">
              <i class="bi ${driveIcon} me-2 fs-6"></i>
              <div>
                <div class="d-flex align-items-center">
                  <strong class="font-monospace" style="color: var(--text-color);">${escapeHtml(devStr || 'C:\\')}</strong>
                  ${driveBadge}
                </div>
                ${driveSubtitle}
              </div>
            </div>
          </td>
          <td>${fsBadge}</td>
          <td class="font-monospace" style="color: var(--text-color);">${Number(d.total_gb || 0).toFixed(1)} GB</td>
          <td class="font-monospace" style="color: var(--text-color);">${Number(d.used_gb || 0).toFixed(1)} GB</td>
          <td class="font-monospace text-info fw-semibold">${Number(d.free_gb || 0).toFixed(1)} GB</td>
          <td>
            <div class="d-flex align-items-center gap-2">
              <div class="about-sys-progress-track flex-grow-1" style="height: 6px; background: var(--surface-2, rgba(120, 120, 120, 0.2));">
                <div class="about-sys-progress-bar ${barClass}" style="width: ${pct}%;"></div>
              </div>
              <span class="small font-monospace text-muted" style="min-width: 42px; text-align: right;">${pct.toFixed(1)}%</span>
            </div>
          </td>
          <td>${smartBadge}</td>
        </tr>
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
        ? propsEntries.map(([k, v]) => {
            const cleanKey = escapeHtml(String(k).replace(/:$/, ''));
            let valStr = '';
            if (Array.isArray(v)) {
              valStr = v.map(item => (typeof item === 'object' && item !== null) ? (item.name || item.model || item.device || item.bank_label || JSON.stringify(item)) : String(item)).filter(Boolean).join(', ') || 'N/A';
            } else if (typeof v === 'object' && v !== null) {
              valStr = Object.entries(v).map(([subK, subV]) => `${subK}: ${subV}`).join(', ') || 'N/A';
            } else {
              valStr = String(v ?? '');
            }
            let valHtml = escapeHtml(valStr);

            // Специфичное выделение частот и статусов совместимости памяти RAM
            if (cleanKey.includes('Номинальная частота')) {
              valHtml = `<span class="badge border border-info-subtle fw-semibold px-2 py-0.5" style="color: #38bdf8; background: rgba(56, 189, 248, 0.14);">${escapeHtml(valStr)}</span>`;
            } else if (cleanKey.includes('Текущая рабочая частота')) {
              const isWarning = valStr.includes('⚠️') || valStr.includes('занижена');
              if (isWarning) {
                valHtml = `<span class="badge border border-warning-subtle fw-bold px-2 py-0.5" style="color: #facc15; background: rgba(234, 179, 8, 0.18);"><i class="bi bi-exclamation-triangle-fill me-1"></i>${escapeHtml(valStr)}</span>`;
              } else if (valStr && valStr !== 'N/A') {
                valHtml = `<span class="badge border border-success-subtle fw-semibold px-2 py-0.5" style="color: #4ade80; background: rgba(34, 197, 94, 0.14);">${escapeHtml(valStr)}</span>`;
              }
            } else if (valStr.includes('⚠️') || valStr.includes('Потенциал не раскрыт') || valStr.includes('Узкое место')) {
              valHtml = `<span class="badge border border-warning-subtle fw-semibold px-2 py-0.5 text-wrap" style="color: #facc15; background: rgba(234, 179, 8, 0.18); text-align: start;"><i class="bi bi-exclamation-triangle-fill me-1"></i>${escapeHtml(valStr.replace(/^⚠️\s*/, ''))}</span>`;
            } else if (valStr.includes('✅') || valStr.includes('Оптимально')) {
              valHtml = `<span class="badge border border-success-subtle fw-semibold px-2 py-0.5" style="color: #4ade80; background: rgba(34, 197, 94, 0.14);"><i class="bi bi-check-circle-fill me-1"></i>${escapeHtml(valStr.replace(/^✅\s*/, ''))}</span>`;
            } else if (cleanKey.includes('Эффективность планки')) {
              valHtml = `<span class="badge border border-info-subtle fw-semibold px-2 py-0.5" style="color: #38bdf8; background: rgba(56, 189, 248, 0.14);">${escapeHtml(valStr)}</span>`;
            }

            return `
            <div class="about-sys-prop-row">
              <span class="about-sys-prop-key">${cleanKey}</span>
              <span class="about-sys-prop-val">${valHtml}</span>
            </div>
          `;
          }).join('')
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
    if (cat.includes('monitor') || cat.includes('screen') || cat.includes('экран')) return 'bi bi-display';
    if (cat.includes('physical') || cat.includes('диск')) return 'bi bi-hdd-fill';
    if (cat.includes('disk') || cat.includes('storage') || cat.includes('drive') || cat.includes('volume')) return 'bi bi-hdd-stack';
    if (cat.includes('network') || cat.includes('adapter') || cat.includes('ethernet') || cat.includes('wi-fi') || cat.includes('сеть')) return 'bi bi-ethernet';
    if (cat.includes('audio') || cat.includes('sound') || cat.includes('звук')) return 'bi bi-volume-up-fill';
    if (cat.includes('usb') || cat.includes('контроллер')) return 'bi bi-usb-symbol';
    if (cat.includes('update') || cat.includes('servicing')) return 'bi bi-arrow-repeat';
    return 'bi bi-gear-fill';
  }

  /**
   * Привязка событий для модального окна истории телеметрии из базы данных
   */
  function bindHistoryEvents() {
    const btnOpenHistory = document.getElementById('btn-open-about-history-modal');
    if (btnOpenHistory) {
      btnOpenHistory.onclick = () => {
        activeHistoryMetric = 'all';
        updateHistoryFilterButtons();
        fetchAboutSystemHistory(activeHistoryMetric);
      };
    }

    // Обработчик кнопок истории на каждой карточке
    document.querySelectorAll('.btn-card-history').forEach(btn => {
      btn.onclick = (e) => {
        e.stopPropagation();
        const metric = btn.getAttribute('data-metric') || 'all';
        activeHistoryMetric = metric;
        updateHistoryFilterButtons();
        fetchAboutSystemHistory(activeHistoryMetric);
      };
    });

    const btnRefreshHistory = document.getElementById('btn-about-history-refresh');
    if (btnRefreshHistory) {
      btnRefreshHistory.onclick = () => {
        fetchAboutSystemHistory(activeHistoryMetric);
      };
    }

    const limitSelect = document.getElementById('about-history-limit-select');
    if (limitSelect) {
      limitSelect.onchange = () => {
        fetchAboutSystemHistory(activeHistoryMetric);
      };
    }

    // Фильтры метрик
    document.querySelectorAll('.btn-history-filter').forEach(btn => {
      btn.onclick = () => {
        const metric = btn.getAttribute('data-metric') || 'all';
        activeHistoryMetric = metric;
        updateHistoryFilterButtons();
        fetchAboutSystemHistory(activeHistoryMetric);
      };
    });
  }

  function updateHistoryFilterButtons() {
    document.querySelectorAll('.btn-history-filter').forEach(btn => {
      const m = btn.getAttribute('data-metric') || 'all';
      if (m === activeHistoryMetric) {
        btn.className = 'btn btn-sm btn-info text-dark fw-bold rounded-pill px-2.5 py-0.5 btn-history-filter active';
      } else {
        btn.className = 'btn btn-sm btn-outline-secondary rounded-pill px-2.5 py-0.5 btn-history-filter';
      }
    });
  }

  let cachedRegionalData = null;

  /**
   * Переключение активной вкладки в модальном окне региональных настроек
   */
  function switchRegionalTab(targetPaneId) {
    const panes = document.querySelectorAll('.regional-tab-pane');
    panes.forEach(pane => {
      if (pane.id === targetPaneId) {
        pane.classList.remove('d-none');
      } else {
        pane.classList.add('d-none');
      }
    });

    const navBtns = document.querySelectorAll('.btn-reg-nav');
    navBtns.forEach(btn => {
      if (btn.getAttribute('data-tab-target') === targetPaneId) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });
  }

  /**
   * Отображение уведомления внутри модального окна региональных настроек
   */
  function showRegModalAlert(msg, type = 'success') {
    const alertBox = document.getElementById('reg-modal-alert');
    if (!alertBox) return;
    alertBox.className = `alert alert-${type} py-2 px-3 small mb-0`;
    alertBox.innerHTML = msg;
    alertBox.classList.remove('d-none');
    setTimeout(() => {
      alertBox.classList.add('d-none');
    }, 6000);
  }

  /**
   * Отрисовка элементов выбора часового пояса с фильтрацией
   */
  function renderTimezonesList(timezones, filterQuery = '', selectedTzId = '') {
    const tzSelect = document.getElementById('reg-tz-select');
    if (!tzSelect) return;
    const q = (filterQuery || '').toLowerCase();
    const filtered = (timezones || []).filter(tz => {
      if (!q) return true;
      return (tz.id || '').toLowerCase().includes(q) || (tz.name || '').toLowerCase().includes(q);
    });

    if (filtered.length === 0) {
      tzSelect.innerHTML = '<option value="" disabled>Ничего не найдено</option>';
      return;
    }

    tzSelect.innerHTML = filtered.map(tz => {
      const isSel = tz.id === selectedTzId ? 'selected' : '';
      return `<option value="${escapeHtml(tz.id)}" ${isSel}>${escapeHtml(tz.name || tz.id)}</option>`;
    }).join('');

    const selLabel = document.getElementById('reg-tz-selected-label');
    if (selLabel) {
      const cur = tzSelect.value;
      selLabel.textContent = cur ? `Выбран: ${cur}` : 'Выберите пояс из списка';
    }
  }

  /**
   * Загрузка параметров региона, времени и пользователя с сервера
   */
  async function loadRegionalOptions(targetPaneId = null) {
    if (targetPaneId) {
      switchRegionalTab(targetPaneId);
    }
    const tzBadge = document.getElementById('reg-cur-tz-badge');
    if (tzBadge) tzBadge.textContent = 'Загрузка...';

    try {
      const data = await apiFetch('/api/v1/system/regional-options');
      cachedRegionalData = data;

      if (tzBadge) tzBadge.textContent = data.current_timezone || 'Не определен';

      // 1. Часовые пояса
      const searchInput = document.getElementById('reg-tz-search-input');
      const curQuery = searchInput ? searchInput.value.trim() : '';
      renderTimezonesList(data.timezones || [], curQuery, data.current_timezone);

      // 2. Локали
      if (Array.isArray(data.locales) && data.locales.length > 0) {
        const sysLocSelect = document.getElementById('reg-loc-sys-select');
        const usrLocSelect = document.getElementById('reg-loc-usr-select');
        const optionsHtml = data.locales.map(loc => 
          `<option value="${escapeHtml(loc.code)}">${escapeHtml(loc.name)} [${escapeHtml(loc.code)}]</option>`
        ).join('');
        
        if (sysLocSelect) {
          sysLocSelect.innerHTML = optionsHtml;
          if (data.current_system_locale) sysLocSelect.value = data.current_system_locale;
        }
        if (usrLocSelect) {
          usrLocSelect.innerHTML = optionsHtml;
          if (data.current_user_locale) usrLocSelect.value = data.current_user_locale;
        }
      } else {
        const sysLocSelect = document.getElementById('reg-loc-sys-select');
        const usrLocSelect = document.getElementById('reg-loc-usr-select');
        if (sysLocSelect && data.current_system_locale) sysLocSelect.value = data.current_system_locale;
        if (usrLocSelect && data.current_user_locale) usrLocSelect.value = data.current_user_locale;
      }

      // 3. Профиль пользователя
      const usrNameInput = document.getElementById('reg-usr-name-input');
      const usrFullNameInput = document.getElementById('reg-usr-fullname-input');
      const usrDescInput = document.getElementById('reg-usr-desc-input');

      if (usrNameInput) usrNameInput.value = data.current_username || '';
      if (usrFullNameInput) usrFullNameInput.value = data.current_user_fullname || '';
      if (usrDescInput) usrDescInput.value = data.current_user_description || '';

    } catch (err) {
      console.error('[AboutSystemTab] loadRegionalOptions error:', err);
      if (tzBadge) tzBadge.textContent = 'Ошибка загрузки';
      showRegModalAlert(`Ошибка загрузки параметров: ${escapeHtml(err.message || String(err))}`, 'danger');
    }
  }

  /**
   * Привязка событий модального окна региональных параметров
   */
  function bindRegionalEvents() {
    // 1. Открытие модального окна по кнопкам в таблице или заголовке
    const openButtons = document.querySelectorAll('#btn-open-regional-settings, .btn-open-reg-tab');
    openButtons.forEach(btn => {
      btn.onclick = (e) => {
        e.preventDefault();
        const targetTab = btn.getAttribute('data-reg-tab') || 'pane-tz';
        const modalEl = document.getElementById('aboutRegionalSettingsModal');
        if (modalEl && window.bootstrap && window.bootstrap.Modal) {
          const modalInst = window.bootstrap.Modal.getOrCreateInstance(modalEl);
          modalInst.show();
        }
        loadRegionalOptions(targetTab);
      };
    });

    // 2. Переключение вкладок в модальном окне
    document.querySelectorAll('.btn-reg-nav').forEach(btn => {
      btn.onclick = (e) => {
        e.preventDefault();
        const targetPane = btn.getAttribute('data-tab-target');
        if (targetPane) {
          switchRegionalTab(targetPane);
        }
      };
    });

    // 3. Фильтрация часовых поясов
    const tzSearchInput = document.getElementById('reg-tz-search-input');
    const tzSelect = document.getElementById('reg-tz-select');
    if (tzSearchInput) {
      tzSearchInput.oninput = () => {
        if (cachedRegionalData && cachedRegionalData.timezones) {
          const currentVal = tzSelect ? tzSelect.value : '';
          renderTimezonesList(cachedRegionalData.timezones, tzSearchInput.value.trim(), currentVal);
        }
      };
    }

    if (tzSelect) {
      tzSelect.onchange = () => {
        const selLabel = document.getElementById('reg-tz-selected-label');
        if (selLabel) {
          selLabel.textContent = tzSelect.value ? `Выбран: ${tzSelect.value}` : 'Выберите пояс из списка';
        }
      };
    }

    // 4. Применение часового пояса
    const btnSaveTz = document.getElementById('btn-reg-save-tz');
    if (btnSaveTz) {
      btnSaveTz.onclick = async () => {
        const tzVal = tzSelect ? tzSelect.value : '';
        if (!tzVal) {
          showRegModalAlert('Пожалуйста, выберите часовой пояс из списка', 'warning');
          return;
        }

        btnSaveTz.disabled = true;
        btnSaveTz.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Применение...';

        try {
          const res = await apiFetch('/api/v1/system/set-timezone', {
            method: 'POST',
            body: JSON.stringify({ timezone_id: tzVal })
          });

          if (res.status === 'ok') {
            showRegModalAlert(`✅ Часовой пояс успешно изменен на «<strong>${escapeHtml(res.timezone_id || tzVal)}</strong>»`, 'success');
            if (window.showToast) window.showToast(`✅ Часовой пояс изменен на «${tzVal}»`, 'success');
            const tzBadge = document.getElementById('reg-cur-tz-badge');
            if (tzBadge) tzBadge.textContent = res.timezone_id || tzVal;
            updateLocalClock();
            fetchSystemSummary();
          } else {
            showRegModalAlert(`Ошибка: ${escapeHtml(res.message || 'Не удалось применить пояс')}`, 'danger');
          }
        } catch (err) {
          showRegModalAlert(`Ошибка при смене часового пояса: ${escapeHtml(err.message || String(err))}`, 'danger');
        } finally {
          btnSaveTz.disabled = false;
          btnSaveTz.innerHTML = '<i class="bi bi-check-lg me-1"></i> Применить пояс';
        }
      };
    }

    // 5. Применение локали
    const btnSaveLoc = document.getElementById('btn-reg-save-loc');
    if (btnSaveLoc) {
      btnSaveLoc.onclick = async () => {
        const sysLoc = document.getElementById('reg-loc-sys-select')?.value;
        const usrLoc = document.getElementById('reg-loc-usr-select')?.value;

        btnSaveLoc.disabled = true;
        btnSaveLoc.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Сохранение...';

        try {
          const res = await apiFetch('/api/v1/system/set-locale', {
            method: 'POST',
            body: JSON.stringify({ system_locale: sysLoc, user_locale: usrLoc })
          });

          if (res.status === 'ok') {
            const rebootMsg = res.reboot_required ? '<br><small class="text-warning">⚠️ Для полного применения требуется перезагрузка Windows.</small>' : '';
            showRegModalAlert(`✅ Системная локаль обновлена: <strong>${escapeHtml(res.locale || sysLoc)}</strong>.${rebootMsg}`, 'success');
            if (window.showToast) window.showToast(`✅ Системная локаль обновлена на «${res.locale || sysLoc}»`, 'warning');
            fetchSystemSummary();
          } else {
            showRegModalAlert(`Ошибка: ${escapeHtml(res.message || 'Не удалось изменить локаль')}`, 'danger');
          }
        } catch (err) {
          showRegModalAlert(`Ошибка при изменении локали: ${escapeHtml(err.message || String(err))}`, 'danger');
        } finally {
          btnSaveLoc.disabled = false;
          btnSaveLoc.innerHTML = '<i class="bi bi-check-lg me-1"></i> Применить локаль';
        }
      };
    }

    // 6. Сохранение профиля пользователя
    const btnSaveUsr = document.getElementById('btn-reg-save-usr');
    if (btnSaveUsr) {
      btnSaveUsr.onclick = async () => {
        const usrName = document.getElementById('reg-usr-name-input')?.value.trim();
        const fullName = document.getElementById('reg-usr-fullname-input')?.value.trim();
        const desc = document.getElementById('reg-usr-desc-input')?.value.trim();

        if (!usrName) {
          showRegModalAlert('Имя учетной записи не указано', 'warning');
          return;
        }

        btnSaveUsr.disabled = true;
        btnSaveUsr.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Сохранение...';

        try {
          const res = await apiFetch('/api/v1/system/update-user-profile', {
            method: 'POST',
            body: JSON.stringify({ username: usrName, full_name: fullName, description: desc })
          });

          if (res.status === 'ok') {
            showRegModalAlert(`✅ Профиль пользователя «<strong>${escapeHtml(usrName)}</strong>» успешно обновлен`, 'success');
            if (window.showToast) window.showToast(`✅ Профиль пользователя «${usrName}» обновлен`, 'success');
            fetchSystemSummary();
          } else {
            showRegModalAlert(`Ошибка: ${escapeHtml(res.message || 'Не удалось обновить профиль')}`, 'danger');
          }
        } catch (err) {
          showRegModalAlert(`Ошибка при обновлении профиля: ${escapeHtml(err.message || String(err))}`, 'danger');
        } finally {
          btnSaveUsr.disabled = false;
          btnSaveUsr.innerHTML = '<i class="bi bi-check-lg me-1"></i> Сохранить профиль';
        }
      };
    }
  }

  /**
   * Загрузка исторических записей телеметрии из базы данных telemetry.db
   */
  async function fetchAboutSystemHistory(metric = 'all') {
    const tbody = document.getElementById('about-history-tbody');
    if (tbody) {
      tbody.innerHTML = `
        <tr>
          <td colspan="9" class="text-center py-4 text-muted">
            <div class="spinner-border spinner-border-sm text-info mb-1" role="status"></div>
            <div>Запрос истории из базы данных telemetry.db...</div>
          </td>
        </tr>
      `;
    }

    const limitSelect = document.getElementById('about-history-limit-select');
    const limit = limitSelect ? parseInt(limitSelect.value, 10) || 30 : 30;

    try {
      const url = `/api/v1/about-system/history?limit=${limit}&metric=${encodeURIComponent(metric)}`;
      const data = await apiFetch(url);
      renderAboutSystemHistory(data, metric);
    } catch (err) {
      console.error('[AboutSystemTab] fetchAboutSystemHistory error:', err);
      if (tbody) {
        tbody.innerHTML = `
          <tr>
            <td colspan="9" class="text-center py-4 text-danger">
              <i class="bi bi-exclamation-triangle-fill me-1"></i>
              Ошибка при получении истории из БД: ${escapeHtml(err.message || String(err))}
            </td>
          </tr>
        `;
      }
    }
  }

  /**
   * Отрисовка таблицы с предыдущими значениями из telemetry.db
   */
  function renderAboutSystemHistory(resData, metric) {
    const tbody = document.getElementById('about-history-tbody');
    const countBadge = document.getElementById('about-history-count-badge');
    const metaEl = document.getElementById('about-history-db-meta');

    if (!resData || !Array.isArray(resData.history) || resData.history.length === 0) {
      if (tbody) {
        tbody.innerHTML = `
          <tr>
            <td colspan="9" class="text-center py-4 text-muted">
              <i class="bi bi-database-slash fs-4 d-block mb-1 text-secondary"></i>
              В базе данных telemetry.db пока нет сохраненных срезов телеметрии.
            </td>
          </tr>
        `;
      }
      if (countBadge) countBadge.textContent = 'Записей в базе: 0';
      return;
    }

    const history = resData.history;
    if (countBadge) countBadge.textContent = `Записей в выборке: ${history.length}`;
    if (metaEl && resData.meta && resData.meta.source) {
      metaEl.textContent = `Источник: ${resData.meta.source} (${resData.meta.table || 'system_snapshots'})`;
    }

    if (!tbody) return;

    let rowsHtml = '';
    history.forEach(item => {
      const id = item.id || 0;
      let dateFormatted = '--:--:--';
      if (item.timestamp) {
        try {
          const d = new Date(item.timestamp);
          dateFormatted = `${d.toLocaleDateString()} ${d.toLocaleTimeString()}`;
        } catch (_) {
          dateFormatted = item.timestamp;
        }
      }

      const host = escapeHtml(item.hostname || '--');
      const os = escapeHtml(item.os_name || 'Windows');

      // CPU
      const cpuVal = item.cpu_total_percent !== null && item.cpu_total_percent !== undefined ? Number(item.cpu_total_percent) : 0;
      const cpuColor = cpuVal > 85 ? 'text-danger fw-bold' : (cpuVal > 60 ? 'text-warning' : 'text-info');
      const cpuFreq = item.cpu_frequency_mhz ? `${item.cpu_frequency_mhz} MHz` : '';

      // RAM
      const ramUsed = item.memory_used_gb !== null && item.memory_used_gb !== undefined ? Number(item.memory_used_gb).toFixed(1) : '0.0';
      const ramTot = item.memory_total_gb !== null && item.memory_total_gb !== undefined ? Number(item.memory_total_gb).toFixed(1) : '0.0';
      const ramPct = item.memory_percent !== null && item.memory_percent !== undefined ? Number(item.memory_percent).toFixed(1) : '0.0';
      const ramColor = Number(ramPct) > 85 ? 'text-danger' : (Number(ramPct) > 65 ? 'text-warning' : 'text-success');

      // GPU
      const gpuLoad = item.gpu_load_percent !== null && item.gpu_load_percent !== undefined ? `${item.gpu_load_percent}%` : '--';
      const gpuTemp = item.gpu_temp_c !== null && item.gpu_temp_c !== undefined ? ` / ${item.gpu_temp_c}°C` : '';

      // Storage C:
      const cFree = item.storage_c_free_gb !== null && item.storage_c_free_gb !== undefined ? `${item.storage_c_free_gb} GB` : '--';

      // Disk I/O
      const diskIo = item.disk_io_total_mb_s !== null && item.disk_io_total_mb_s !== undefined ? `${Number(item.disk_io_total_mb_s).toFixed(2)} MB/s` : '0.00 MB/s';

      // Uptime
      const uptime = escapeHtml(item.uptime_human || '--');

      rowsHtml += `
        <tr>
          <td class="text-muted">#${id}</td>
          <td class="text-nowrap text-light">${escapeHtml(dateFormatted)}</td>
          <td class="text-truncate" style="max-width: 140px;" title="${host} (${os})">
            <span class="text-white">${host}</span>
            <small class="text-muted d-block" style="font-size: 0.70rem;">${os}</small>
          </td>
          <td style="text-align: right;">
            <span class="${cpuColor}">${cpuVal.toFixed(1)}%</span>
            <small class="text-muted d-block" style="font-size: 0.70rem;">${cpuFreq}</small>
          </td>
          <td style="text-align: right;">
            <span class="${ramColor}">${ramUsed} / ${ramTot} GB</span>
            <small class="text-muted d-block" style="font-size: 0.70rem;">${ramPct}%</small>
          </td>
          <td style="text-align: right;">
            <span class="text-light">${gpuLoad}</span>
            <small class="text-danger" style="font-size: 0.70rem;">${gpuTemp}</small>
          </td>
          <td style="text-align: right;" class="text-info">${cFree}</td>
          <td style="text-align: right;" class="text-white">${diskIo}</td>
          <td style="text-align: right;" class="text-muted">${uptime}</td>
        </tr>
      `;
    });

    tbody.innerHTML = rowsHtml;
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

