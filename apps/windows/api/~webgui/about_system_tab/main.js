/**
 * =============================================================================
 * Process Name: Windows About System Tab - Main Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля main.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/~webgui/about_system_tab/main.js?v=20261001_v1" type="module"></script>
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: windows/api/~webgui/about_system_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-01 13:04:40
 * =============================================================================
 */

// =============================================================================
// Process Name: About System Tab Web Controller
// =============================================================================
// Description:
//   Client-side JavaScript controller for the About System tab.
//   Provides real-time host telemetry, system identity & locale parameters,
//   AIDA64-like hardware tree, WMI sensors, live top processes,
//   disk volumes and security status.
//
//   Data source: telemetry.db only (via /api/windows/dashboard/*)
//   Removed LibreHardwareMonitor (LHM) dependency
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
  let activeSensorFilter = 'alli18n.t('auto__let_isliveactive_true_let_liveintervalid_null_let_wearautorefreshtimer_null_let_isupdating_false_let_isairunning_false_ttl_const_cache_strategy_hardware_spec_ttl_30_60_1000_strategy__b1907a')cache-firsti18n.t('auto__30_system_summary_ttl_5_1000_strategy__778b42')stale-while-revalidatei18n.t('auto__5_sensors_ttl_3_1000_strategy__8158d8')network-firsti18n.t('auto__3_control_status_ttl_60_1000_strategy__33f2e3')stale-while-revalidatei18n.t('auto__1_backup_status_ttl_5_60_1000_strategy__583e13')cache-firsti18n.t('auto__5_storage_battery_ttl_10_1000_strategy__426999')stale-while-revalidatei18n.t('auto__10_const_cache_store__748fc1')api_cache';
  const CACHE_TAG = 'about-system-tabi18n.t('auto__cache_first_network_first_stale_while_revalidate_async_function_cachedfetch_url_cachekey_options_const_ttl_60000_strategy__020612')stale-while-revalidatei18n.t('auto__forcenetwork_false_options_const_cache_window_browsercache_if_cache_fallback_return_await_apifetch_url_cache_first_if_strategy__4cb9e2')cache-firsti18n.t('auto__forcenetwork_const_cached_await_cache_get_cache_store_cachekey_if_cached_console_log_cache_hit_cache_first_cachekey_return_cached_stale_while_revalidate_if_strategy__b88e61')stale-while-revalidatei18n.t('auto__forcenetwork_const_cached_await_cache_get_cache_store_cachekey_if_cached_console_log_cache_hit_stale_while_revalidate_cachekey_updating_in_background_apifetch_url_then_fresh_cache_set_cache_store_cachekey_fresh_ttl_tags_cache_tag_catch_err_console_warn_cache_background_update_failed_for_cachekey_err_return_cached_network_first_try_const_fresh_await_apifetch_url_await_cache_set_cache_store_cachekey_fresh_ttl_tags_cache_tag_console_log_cache_miss_stored_cachekey_return_fresh_catch_err_const_cached_await_cache_get_cache_store_cachekey_if_cached_console_warn_cache_network_failed_returning_stale_cache_cachekey_return_cached_throw_err_async_function_cleartabcache_const_cache_window_browsercache_if_cache_await_cache_invalidatebytag_cache_store_cache_tag_console_log__1be9a3')[Cache] Tab cache cleared');
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
    console.log('[AboutSystemTab] Initializing tab controller...i18n.t('auto__bindevents_bindaievents_updatelocalclock_await_updatecachestatus_prefetch_const_prefetchpromises_fetchsystemsummary_catch_err_console_warn__995727')[AboutSystemTab] Quick summary error:', err)),
      fetchHardwareSpec().catch(err => console.warn('[AboutSystemTab] Hardware spec error:i18n.t('auto__err_await_promise_allsettled_prefetchpromises_fetchhardwaresensors_catch_err_console_warn__a2af8e')[AboutSystemTab] Sensors error:', err));
    fetchBackupStatus().catch(err => console.warn('[AboutSystemTab] Backup status error:', err));
    fetchSystemControlStatus().catch(err => console.warn('[AboutSystemTab] Control status error:', err));
    fetchStorageBatteryWear().catch(err => console.warn('[AboutSystemTab] Storage & Battery wear error:i18n.t('auto__err_ai_rescan_start_live_telemetry_ticker_startlivestream_window_initaboutsystemtab_initaboutsystemtab_async_function_updatecachestatus_const_badge_document_getelementbyid__ffa413')about-sys-cache-badge');
    if (!badge) return;
    
    const cache = window.browserCache;
    if (!cache) {
      badge.textContent = '💾 Cache: Unavailable';
      badge.className = 'badge rounded-pill bg-warning-subtle text-warning border border-warning px-2.5 py-1';
      badge.title = i18n.t('auto__api_d395a1');
      return;
    }
    
    const ready = await cache.ready();
    if (ready) {
      const stats = await cache.getDetailedStats();
      const hitRate = stats.metrics.hits + stats.metrics.misses > 0 
        ? Math.round((stats.metrics.hits / (stats.metrics.hits + stats.metrics.misses)) * 100)
        : 0;
      
      badge.textContent = `💾 Cache: ${hitRate}% hit`;
      badge.className = 'badge rounded-pill bg-success-subtle text-success border border-success px-2.5 py-1i18n.t('auto__badge_title_n_stats_metrics_hits_n_stats_metrics_misses_n_stats_memorycachesize_else_badge_textcontent__23e62d')💾 Cache: Error';
      badge.className = 'badge rounded-pill bg-danger-subtle text-danger border border-danger px-2.5 py-1';
      badge.title = i18n.t('auto___4fed3d');
    }
  }

  function updateLocalClock() {
    const clockEl = document.getElementById('about-ident-time-badgei18n.t('auto__if_clockel_const_now_new_date_clockel_textcontent_now_tolocaletimestring_function_startlivestream_if_window_registertabpoller_window_registertabpoller__1a3e0b')tab-about-system', async () => {
        updateLocalClock();
        if (isLiveActive && !isUpdating) {
          await pollLiveTelemetry();
          if (activeSubtab !== 'subtab-overviewi18n.t('auto__await_refreshactivesubtab_3_await_updatecachestatus_3000_immediate_true_else_if_liveintervalid_clearinterval_liveintervalid_liveintervalid_setinterval_async_updatelocalclock_if_isliveactive_isupdating_await_polllivetelemetry_if_activesubtab__ad7dca')subtab-overview') {
            await refreshActiveSubtab();
          }
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
        if (icon) icon.classList.add('spin-animationi18n.t('auto__await_cleartabcache_await_refreshalldata_true_if_icon_icon_classlist_remove__c6f4d7')spin-animation');
        btnClearCache.disabled = false;
        
        if (window.showToast) {
          window.showToast(i18n.t('auto___0d819b'), 'success');
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
          if (txt) txt.textContent = i18n.t('auto___03498e');
          if (liveBadge) {
            liveBadge.className = 'badge rounded-pill bg-info-subtle text-info border border-info px-2.5 py-1';
            liveBadge.textContent = '● Live Host Telemetry';
          }
        } else {
          if (icon) icon.className = 'bi bi-play-fill me-1';
          if (txt) txt.textContent = i18n.t('auto___fa6a34');
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
        adjustHardwareTreeHeight();
      };
    }

    const btnCollapseAll = document.getElementById('btn-about-sys-collapse-all');
    if (btnCollapseAll) {
      btnCollapseAll.onclick = () => {
        document.querySelectorAll('.about-sys-tree-body').forEach(b => b.classList.add('d-none'));
        document.querySelectorAll('.about-sys-chevron').forEach(c => c.textContent = '▼');
        adjustHardwareTreeHeight();
      };
    }

    window.addEventListener('resize', () => adjustHardwareTreeHeight());

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

    const btnWearRefresh = document.getElementById('btn-diag-wear-refresh');
    if (btnWearRefresh) {
      btnWearRefresh.onclick = () => fetchStorageBatteryWear(true);
    }

    const wearAutoSwitch = document.getElementById('diag-wear-auto-refreshi18n.t('auto__if_wearautoswitch_wearautoswitch_onchange_e_if_e_target_checked_wearautorefreshtimer_setinterval_fetchstoragebatterywear_true_10000_else_if_wearautorefreshtimer_clearinterval_wearautorefreshtimer_wearautorefreshtimer_null_async_function_refreshalldata_forcenetwork_false_isupdating_true_try_if_forcenetwork_await_promise_allsettled_apifetch__640ad9')/api/v1/system/summary?process_limit=25').then(data => {
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
          }),
          apiFetch('/api/v1/system/diagnostics/storage-battery').then(data => {
            if (window.browserCache) {
              window.browserCache.set(CACHE_STORE, 'storage_battery_wear', data, {
                ttl: CACHE_STRATEGY.STORAGE_BATTERY.ttl,
                tags: [CACHE_TAG]
              });
            }
            return fetchStorageBatteryWear(true);
          })
        ]);
      } else {
        await Promise.allSettled([
          fetchSystemSummary(),
          fetchSystemControlStatus(),
          fetchHardwareSpec(),
          fetchHardwareSensors(),
          fetchBackupStatus(),
          fetchStorageBatteryWear()
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

      let lastTimeStr = i18n.t('auto___096309');
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
        const target = storage.target_path || i18n.t('auto___ca0407');
        const freeGb = typeof storage.free_space_gb === 'numberi18n.t('auto__storage_free_space_gb_tofixed_1_storage_free_space_gb_storagestr_target_freegb_gb_else_if_cfg_cfg_target_drive_letter_cfg_target_url_storagestr_cfg_target_drive_letter_cfg_target_url_else_storagestr__8298dd')Хранилище не найдено';
      }

      const backupSummary = `${lastTimeStr} | ${storageStr}`;
      const backupEl = document.getElementById('about-ident-backupi18n.t('auto__if_backupel_backupel_textcontent_backupsummary_backupel_title_lasttimestr_n_storagestr_n_file_history_data_file_history_service_status__a3f8e0')—'}\nHealth Score: ${data.health_score ?? '--'}/100`;
      }
    } catch (e) {
      console.warn('[AboutSystemTab] fetchBackupStatus warning:', e);
      setText('about-ident-backup', i18n.t('auto___1411ab'));
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
        setText('diag-wear-disks-counti18n.t('auto__data_disks_wear_length_if_data_disks_wear_length_0_diskstbody_innerhtml__438bf3')<tr><td colspan="9" class="text-center py-4 text-muted">Физических накопителей не обнаружено</td></tr>';
        } else {
          const formatBytesLocal = (bytes) => {
            if (bytes == null || bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PBi18n.t('auto__const_i_math_floor_math_log_bytes_math_log_k_return_parsefloat_bytes_math_pow_k_i_tofixed_1_sizes_i_const_formatpohlocal_hours_if_hours_null_hours_0_return_null_const_days_math_floor_hours_24_const_years_hours_24_365_25_tofixed_1_if_days_365_return_hours_tolocalestring_years_if_days_1_return_hours_tolocalestring_days_return_hours_tolocalestring_diskstbody_innerhtml_data_disks_wear_map_d_const_diskname_d_name_d_model_d_device_id__be61dc')Физический диск';
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
              : '<span class="text-muted font-monospace small">Сессия ОС</span>';

            // Объемы ввода/вывода (запись и чтение)
            const ioHtml = `
              <div class="font-monospace text-light" title=i18n.t('auto___2b456e')>
                <i class="bi bi-arrow-up-circle text-warning me-1"></i>${formatBytesLocal(d.bytes_written)}
              </div>
              <div class="small font-monospace text-info mt-0.5" title=i18n.t('auto___650fa5')>
                <i class="bi bi-arrow-down-circle text-info me-1"></i>${formatBytesLocal(d.bytes_read)}
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
        if (batSourceBadge) {
          batSourceBadge.textContent = b.power_source || 'AC Mains';
        }
        if (!b.has_battery) {
          batContainer.innerHTML = `
            <div class="text-center py-4 text-muted small">
              <i class="bi bi-plug-fill fs-4 text-info d-block mb-1i18n.t('auto__i_div_else_batcontainer_innerhtml_table_class__23689a')about-sys-spec-table">
              <tbody>
                <tr>
                  <td class="about-sys-spec-key"><i class="bi bi-battery-charging me-1.5 text-warningi18n.t('auto__i_td_td_class__15f163')about-sys-spec-val fw-bold text-white">${b.percent}% (${b.is_charging ? i18n.t('auto___a03862') : i18n.t('auto___777161')})</td>
                </tr>
                <tr>
                  <td class="about-sys-spec-key"><i class="bi bi-shield-shaded me-1.5 text-infoi18n.t('auto__i_td_td_class__b49187')about-sys-spec-val font-monospace">${b.design_capacity_mwh ? b.design_capacity_mwh + ' mWh' : '--'}</td>
                </tr>
                <tr>
                  <td class="about-sys-spec-key"><i class="bi bi-battery-full me-1.5 text-successi18n.t('auto__i_td_td_class__2138b6')about-sys-spec-val font-monospace">${b.full_charge_capacity_mwh ? b.full_charge_capacity_mwh + ' mWh' : '--'}</td>
                </tr>
                <tr>
                  <td class="about-sys-spec-key"><i class="bi bi-heart-pulse me-1.5 text-dangeri18n.t('auto__i_td_td_class__6dd619')about-sys-spec-val ${b.wear_level_pct > 20 ? 'text-danger fw-bold' : 'text-success'}">
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
      const lang = snap.system_language || i18n.t('auto__ru_ru__d30645');
      const userLoc = snap.user_locale || 'ru-RU';
      const sysLoc = snap.system_locale || 'ru-RU';
      const tz = snap.timezone || 'UTC+03:00';
      const cp = snap.codepage || 'UTF-8 (ACP: 65001)';
      const inputs = Array.isArray(snap.input_languages) && snap.input_languages.length > 0
        ? snap.input_languages.join(', ')
        : i18n.t('auto__ru_english_us_il__169750');
      const osBuild = snap.os_build ? `${snap.os_name || 'Windows 11'} (Build ${snap.os_build})` : (snap.os_name || 'Windows 11');

      setText('about-ident-hostname', host);
      setText('about-ident-domain', `Workgroup / Host: ${host}`);
      setText('about-ident-username', user);
      setText('about-ident-language', lang);
      setText('about-ident-localesi18n.t('auto__user_userloc_sys_sysloc_settext__671e3a')about-ident-timezone', tz);
      setText('about-ident-codepagei18n.t('auto__cp_settext__ddd79f')about-ident-inputs', inputs);
      setText('about-ident-os-build', osBuild);
      setText('about-ident-install-date', snap.os_install_date || i18n.t('auto___657510'));

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
        setText('about-telemetry-cpu-coresi18n.t('auto__cores_threads_specification_table_cpu_settext__54c885')about-spec-cpu', `${snap.cpu.model || 'Intel Processor'} (${threads} logical cores)`);
      }

      if (snap.memory) {
        const total = Number(snap.memory.total_gb || 0).toFixed(1);
        const used = Number(snap.memory.used_gb || 0).toFixed(1);
        const avail = Number(snap.memory.available_gb || 0).toFixed(1);
        const pct = snap.memory.percent || 0;

        setText('about-telemetry-ram-val', `${used} / ${total} GB`);
        setText('about-telemetry-ram-subi18n.t('auto__pct_avail_gb_const_rambar_document_getelementbyid__836395')about-telemetry-ram-bar');
        if (ramBar) {
          ramBar.style.width = `${Math.min(100, Math.max(0, pct))}%`;
          ramBar.className = pct > 85 ? 'about-sys-progress-bar bg-danger' : (pct > 65 ? 'about-sys-progress-bar bg-warning' : 'about-sys-progress-bar bg-info');
        }

        // Specification Table RAM (Hardware installed capacity)
        setText('about-spec-rami18n.t('auto__total_gb_ram_avail_gb_if_array_isarray_snap_gpus_snap_gpus_length_0_const_gpu_snap_gpus_0_settext__d6dc56')about-telemetry-gpu-name', gpu.name || 'GPU');
        const vramTxt = gpu.memory_total_gb ? `VRAM: ${Number(gpu.memory_total_gb).toFixed(1)} GB` : 'VRAM: N/Ai18n.t('auto__const_loadtxt_gpu_load_percent_null_gpu_load_percent_undefined_gpu_load_percent__0e1d4b')';
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
        setText('about-telemetry-disk-ratesi18n.t('auto__rkbs_wkbs_specification_table_general_settext__84aedd')about-spec-host', host);
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
          const prim = m.is_primary ? i18n.t('auto___8ce815') : '';
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
        const offTxt = snap.office.status || (snap.office.installed ? `${snap.office.product_name || 'MS Office'} (${snap.office.version || ''})` : i18n.t('auto___11382e'));
        setText('about-ident-ms-office', offTxt);
      } else {
        setText('about-ident-ms-office', i18n.t('auto___11382e'));
      }

      // 5.2 OneDrive Storage Block
      if (snap.onedrive) {
        const odTxt = snap.onedrive.status || (snap.onedrive.installed ? `${snap.onedrive.free_gb || 0} GB своб.` : i18n.t('auto___1411ab'));
        setText('about-ident-onedrive', odTxt);
      } else {
        setText('about-ident-onedrive', i18n.t('auto___1411ab'));
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
      setText('about-ident-privilege', isElevated ? i18n.t('auto__full_access__cb9a53') : i18n.t('auto___e17d95'));

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
      const cDrive = currentDisks.find(d => (d.device || '').toUpperCase().startsWith('Ci18n.t('auto__currentdisks_0_const_totalgbtxt_cdrive_number_cdrive_total_gb_0_tofixed_1_gb__ebb7d0')';
      setText('about-kpi-stor-clean', `Cleanable: ~${cleanMb} MB${totalGbTxt}`);

      // Security table rows
      const setSecStatus = (id, active, activeText = 'Enabled', inactiveText = 'Disabled') => {
        const el = document.getElementById(id);
        if (!el) return;
        const stateText = active ? activeText : inactiveText;
        el.setAttribute('data-status', stateText);
        el.className = active ? 'text-success fw-bold' : 'text-danger fw-bold';
        el.textContent = stateText;
      };
      setSecStatus('about-sec-defender', defActive);
      setSecStatus('about-sec-realtime', sec.realtime_protection_enabled !== false);
      setSecStatus('about-sec-fw-domain', sec.firewall_profiles?.Domain, 'Active', 'Disabled');
      setSecStatus('about-sec-fw-private', sec.firewall_profiles?.Private, 'Active', 'Disabled');
      setSecStatus('about-sec-fw-public', sec.firewall_profiles?.Public, 'Active', 'Disabled');
      setSecStatus('about-sec-uac', uacOk);

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
        if (badge) badge.textContent = `${sensors.length} сенсоров.`;
      }
    } catch (e) {
      console.warn('[AboutSystemTab] Sensors error:', e);
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
          txtStages.textContent = isHidden ? i18n.t('auto___62d981') : i18n.t('auto___6bff8b');
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
          if (s) s.textContent = i18n.t('auto___f266fa');
          setTimeout(() => { if (s) s.textContent = i18n.t('auto___4a05d8'); }, 1800);
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
          if (s) s.textContent = i18n.t('auto___f266fa');
          setTimeout(() => { if (s) s.textContent = i18n.t('auto___4a05d8'); }, 1800);
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
          if (s) s.textContent = i18n.t('auto___f266fa');
          setTimeout(() => { if (s) s.textContent = i18n.t('auto___4a05d8'); }, 1800);
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
          if (s) s.textContent = i18n.t('auto___f266fa');
          setTimeout(() => { if (s) s.textContent = i18n.t('auto__json_74cfdc'); }, 1800);
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
            <span>${escapeHtml(st.message || st.title || i18n.t('auto___13d403'))}</span>
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
                ${escapeHtml(g.summary || g.description || i18n.t('auto___8c6ae0'))}
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
    }).join('i18n.t('auto__async_function_runaidiagnostics_ismanualrescan_false_if_isairunning_return_isairunning_true_processing_if_window_settabprocessing_window_settabprocessing__eb708e')tab-about-system', true);
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
    if (txtRescan) txtRescan.textContent = i18n.t('auto___f1d9e1');

    if (errorSec) errorSec.classList.add('d-none');
    if (actionsBox) actionsBox.classList.add('d-none');
    if (progressBar) progressBar.style.width = '5%';

    if (liveStatusText) liveStatusText.textContent = i18n.t('auto__wmi_psutil_smart__b1f6a1');

    // Reset chips to active polling state
    [chipWmi, chipRam, chipDisks, chipNet].forEach(c => {
      if (c) c.className = 'badge bg-secondary bg-opacity-40 text-light border border-secondary';
    });

    if (badgeHealth) {
      badgeHealth.textContent = i18n.t('auto_health__01af48');
      badgeHealth.className = 'badge bg-warning-subtle text-warning border border-warning font-monospace';
    }
    if (badgeHealthBtn) {
      badgeHealthBtn.textContent = i18n.t('auto_health__d24baf');
      badgeHealthBtn.className = 'badge bg-warning-subtle text-warning border border-warning font-monospace ms-1';
    }

    const stagesLog = [
      {
        stage: 'init',
        title: i18n.t('auto___497c64'),
        message: i18n.t('auto___76f41d'),
        details: i18n.t('auto__wmi_systemsnapshot_d7d326'),
      }
    ];
    renderAIDiagnosticStages(stagesLog, false);

    try {
      // 1. Получение списка подготовленных 4 групп телеметрии
      const groups = await apiFetch('/api/v1/system/diagnose/groups');
      if (!Array.isArray(groups) || groups.length === 0) {
        throw new Error(i18n.t('auto___ac81c8'));
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
        if (tickTemp) tickTemp.textContent = maxT !== null ? `${maxT}°C` : i18n.t('auto___e168bd');
      }

      const memGroup = groups.find(g => g.group_id === 'memory_processes');
      if (memGroup && memGroup.payload) {
        const ram = memGroup.payload.ram || {};
        if (tickRam) tickRam.textContent = `${ram.used_gb ?? 0} / ${ram.total_gb ?? 0} GB (${ram.used_percent ?? 0}%)`;
        const procs = memGroup.payload.top_active_processes || [];
        if (tickTopProc) tickTopProc.textContent = procs.length > 0 ? `${procs[0].name} (${procs[0].cpu_percent ?? 0}%)` : i18n.t('auto___e592fc');
      }

      const diskGroup = groups.find(g => g.group_id === 'storage_smart');
      if (diskGroup && diskGroup.payload) {
        const parts = diskGroup.payload.storage_partitions || [];
        if (tickDisks) tickDisks.textContent = parts.map(p => `${p.mountpoint || p.device || 'Voli18n.t('auto__p_free_gb_0_gb_join__5e8069'), ') || 'OKi18n.t('auto__4_const_cardsstate_groups_map_g_const_keymetrics_if_g_group_id__c69a71')compute_thermals') {
          const cpu = g.payload?.cpu || {};
          keyMetrics['cpu_load'] = `${cpu.load_percent ?? 0}%`;
          keyMetrics['cpu_model'] = cpu.model || 'CPU';
          const temps = g.payload?.sensors?.temperatures_celsius || {};
          const maxT = Object.values(temps).length > 0 ? Math.max(...Object.values(temps)) : null;
          keyMetrics['max_temp'] = maxT !== null ? `${maxT}°C` : i18n.t('auto___e168bd');
        } else if (g.group_id === 'memory_processes') {
          const ram = g.payload?.ram || {};
          keyMetrics['ram_used'] = `${ram.used_gb ?? 0} / ${ram.total_gb ?? 0} GB (${ram.used_percent ?? 0}%)`;
          const procs = g.payload?.top_active_processes || [];
          keyMetrics['top_process'] = procs.length > 0 ? `${procs[0].name} (${procs[0].cpu_percent ?? 0}%)` : i18n.t('auto___f82a82');
        } else if (g.group_id === 'storage_smart') {
          const parts = g.payload?.storage_partitions || [];
          const maxUsed = parts.length > 0 ? Math.max(...parts.map(p => p.used_percent || 0)) : 0;
          keyMetrics['max_volume_fill'] = `${maxUsed}%`;
          keyMetrics['volumes_count'] = parts.length;
        } else if (g.group_id === 'system_network') {
          const updates = g.payload?.system_updates || {};
          keyMetrics['reboot_pending'] = updates.reboot_pending ? i18n.t('auto___8d2fab') : i18n.t('auto___f82a82');
          keyMetrics['update_status'] = updates.status || 'Up to date';
        }

        return {
          group_id: g.group_id,
          title: g.title,
          icon: g.icon,
          status: 'pending'
        };
      });
      // compute_thermals - WMI sensors
      if (group.group_id === 'compute_thermals') {
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

        // Обновляем статус карточки на i18n.t('auto___0267f3')
        cardsState[i].status = 'analyzingi18n.t('auto__cardsstate_i_summary_stepnum_totalsteps_renderaidomaincards_cardsstate_stageslog_push_stage__39cc75')group_runi18n.t('auto__title_stepnum_totalsteps_message_stepnum_totalsteps_group_title_details_group_description_renderaidiagnosticstages_stageslog_false_ai_const_res_await_apifetch__a5150a')/api/v1/system/diagnose/group', {
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
          cardsState[i].summary = i18n.t('auto___7ed47e');
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
          if (chipNet) chipNet.className = 'badge bg-success-subtle text-success border border-successi18n.t('auto__renderaidomaincards_cardsstate_stageslog_push_stage__fe9121')group_donei18n.t('auto__title_stepnum_message_stepnum_totalsteps_group_title_cardsstate_i_status_touppercase_details_cardsstate_i_summary_substring_0_120_cardsstate_i_summary_length_120__2bfb93')...' : ''),
        });
        renderAIDiagnosticStages(stagesLog, false);
      }

      if (liveStatusText) {
        liveStatusText.textContent = i18n.t('auto___4cf5dc');
      }

      // 3. Финальный синтез итогового вердикта
      if (progressBar) progressBar.style.width = '95%';
      stagesLog.push({
        stage: 'synthesis',
        title: i18n.t('auto___042bba'),
        message: i18n.t('auto__health_score__06fd4e'),
        details: i18n.t('auto__4__abf473'),
      });
      renderAIDiagnosticStages(stagesLog, false);

      const synthesis = await apiFetch('/api/v1/system/diagnose/synthesize', {
        method: 'POST',
        body: JSON.stringify({ groups: completedGroups }),
      });

      if (progressBar) progressBar.style.width = '100%i18n.t('auto__health_badge_const_score_number_synthesis_health_score_100_const_healthclass_score_80__b81c42')bg-success-subtle text-success border border-success' :
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
        summaryEl.textContent = synthesis.executive_summary || i18n.t('auto___634507');
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
        title: i18n.t('auto___8f77fd'),
        message: `✅ Поэтапная AI-диагностика успешно завершена (Health: ${score}/100)`,
        details: i18n.t('auto__4__321da6'),
      });
      renderAIDiagnosticStages(stagesLog, true);

    } catch (e) {
      console.error('[AboutSystemTab] Grouped AI Diagnosis error:', e);
      if (summaryEl) summaryEl.textContent = i18n.t('auto__ai__130e03') + e.message;
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
        title: i18n.t('auto___72aecd'),
        message: `❌ Ошибка выполнения: ${e.message}`,
        details: i18n.t('auto__api__0e2a8c'),
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
        'hardware_speci18n.t('auto__ttl_config_ttl_strategy_config_strategy_hardwaredata_array_isarray_nodes_nodes_if_badgecount_badgecount_textcontent_hardwaredata_length_const_searchinput_document_getelementbyid__aa7e2f')about-sys-search');
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

      const devStr = String(d.device || d.mountpoint || '');
      const volStr = String(d.volume_name || '');
      const isGoogleDrive = d.is_virtual || d.drive_type === 'Google Drive' || volStr.toLowerCase().includes('google') || volStr.includes('@') || devStr.startsWith('G:') || devStr.startsWith('J:');

      let driveIcon = 'bi-hdd-fill text-primary';
      let driveBadge = '';
      let driveSubtitle = '';
      let fsBadge = `<span class="badge bg-secondary-subtle text-secondary border border-secondary">${escapeHtml(d.fstype || 'NTFS')}</span>`;
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
        fsBadge = `<span class="badge bg-dark border border-secondary text-info">Virtual ${escapeHtml(d.fstype || 'FAT32')}</span>`;
        smartBadge = `<span class="badge bg-secondary-subtle text-muted border border-secondary font-monospace" title=i18n.t('auto__google_drive_s_m_a_r_t__e99524') style="font-size: 0.68rem;i18n.t('auto__n_a_span_else_if_d_volume_name_drivesubtitle_div_class__e45cb4')small text-secondary font-monospace mt-0.5">${escapeHtml(d.volume_name)}</div>`;
      }

      return `
        <tr>
          <td>
            <div class="d-flex align-items-center">
              <i class="bi ${driveIcon} me-1.5 fs-6"></i>
              <div>
                <div class="d-flex align-items-center">
                  <strong>${escapeHtml(devStr || 'C:\\')}</strong>
                  ${driveBadge}
                </div>
                ${driveSubtitle}
              </div>
            </div>
          </td>
          <td>${fsBadge}</td>
          <td class="font-monospace">${Number(d.total_gb || 0).toFixed(1)} GB</td>
          <td class="text-light font-monospace">${Number(d.used_gb || 0).toFixed(1)} GB</td>
          <td class="text-info fw-semibold font-monospace">${Number(d.free_gb || 0).toFixed(1)} GB</td>
          <td>
            <div class="d-flex align-items-center gap-2">
              <div class="about-sys-progress-track flex-grow-1" style="height: 6px;">
                <div class="about-sys-progress-bar ${barClass}" style="width: ${pct}%;"></div>
              </div>
              <span class="small font-monospace" style="min-width: 42px; text-align: right;">${pct.toFixed(1)}%</span>
            </div>
          </td>
          <td>${smartBadge}</td>
        </tr>
      `;
    }).join('');
  }

  function renderSensorsList(sensors) {
    const container = document.getElementById('about-sensors-container');
    if (!container) return;

    if (!Array.isArray(sensors) || sensors.length === 0) {
      container.innerHTML = '<div class="text-center py-4 text-muted small">Нет доступных сенсоров (WMI)</div>';
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
    }).join('i18n.t('auto__function_adjusthardwaretreeheight_const_container_document_getelementbyid__a0b378')about-sys-tree-container');
    if (!container) return;

    const visibleNodes = container.querySelectorAll('.about-sys-tree-node');
    if (visibleNodes.length === 0) {
      container.style.maxHeight = '300px';
      return;
    }

    let totalEstimatedHeight = 32;
    visibleNodes.forEach(node => {
      totalEstimatedHeight += 38;
      const body = node.querySelector('.about-sys-tree-body');
      if (body && !body.classList.contains('d-none')) {
        const rows = body.querySelectorAll('.about-sys-prop-row');
        const gridRowsCount = Math.ceil(rows.length / 2);
        totalEstimatedHeight += gridRowsCount * 28 + 16;
      }
    });

    const vhLimit = Math.floor(window.innerHeight * 0.85);
    const dynamicMaxHeight = Math.max(500, Math.min(totalEstimatedHeight + 20, Math.max(900, vhLimit)));
    container.style.maxHeight = `${dynamicMaxHeight}px`;
  }

  function renderHardwareTree(nodes, filter) {
    const container = document.getElementById('about-sys-tree-container');
    if (!container) return;

    if (!Array.isArray(nodes) || nodes.length === 0) {
      container.innerHTML = '<div class="text-center py-4 text-muted small">Оборудование не обнаружено или опрашивается...</div>';
      adjustHardwareTreeHeight();
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
      adjustHardwareTreeHeight();
      return;
    }

    container.innerHTML = filtered.map((node, idx) => {
      const propsEntries = Object.entries(node.properties || {});
      const propsHtml = propsEntries.length > 0
        ? propsEntries.map(([k, v]) => {
            const cleanKey = escapeHtml(String(k).replace(/:$/, ''));
            return `
              <div class="about-sys-prop-row">
                <span class="about-sys-prop-key">${cleanKey}</span>
                <span class="about-sys-prop-val">${escapeHtml(String(v))}</span>
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

    adjustHardwareTreeHeight();
  }

  window.toggleNode = function(idx) {
    const body = document.getElementById(`about-node-body-${idx}`);
    const chevron = document.getElementById(`about-chevron-${idx}`);
    if (body) {
      body.classList.toggle('d-none');
      if (chevron) {
        chevron.textContent = body.classList.contains('d-none') ? '▼' : '▲';
      }
      adjustHardwareTreeHeight();
    }
  };

  function getNodeIcon(category) {
    const cat = (category || '').toLowerCase();
    if (cat.includes('processor') || cat.includes('cpu')) return 'bi bi-cpu';
    if (cat.includes('module') || cat.includes(i18n.t('auto___bf3547'))) return 'bi bi-memory';
    if (cat.includes('memory') || cat.includes('ram')) return 'bi bi-sd-card';
    if (cat.includes('system') || cat.includes('os')) return 'bi bi-laptop';
    if (cat.includes('motherboard') || cat.includes('mainboard')) return 'bi bi-motherboard';
    if (cat.includes('display') || cat.includes('gpu') || cat.includes('video') || cat.includes('graphics')) return 'bi bi-gpu-card';
    if (cat.includes('monitor') || cat.includes('screen') || cat.includes(i18n.t('auto___4e8cde'))) return 'bi bi-display';
    if (cat.includes('physical') || cat.includes(i18n.t('auto___094e84'))) return 'bi bi-hdd-fill';
    if (cat.includes('disk') || cat.includes('storage') || cat.includes('drive') || cat.includes('volume')) return 'bi bi-hdd-stack';
    if (cat.includes('network') || cat.includes('adapter') || cat.includes('ethernet') || cat.includes('wi-fi') || cat.includes(i18n.t('auto___2f481e'))) return 'bi bi-ethernet';
    if (cat.includes('audio') || cat.includes('sound') || cat.includes(i18n.t('auto___2300cb'))) return 'bi bi-volume-up-fill';
    if (cat.includes('usb') || cat.includes(i18n.t('auto___7c692f'))) return 'bi bi-usb-symbol';
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

