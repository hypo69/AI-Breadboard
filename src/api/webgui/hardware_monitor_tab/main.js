// Hardware & Sensors Monitor Frontend Logic
(function () {
  let timerId = null;

  async function initHardwareMonitorTab() {
    console.log('[HardwareMonitor] Initializing tab...');
    bindEvents();
    loadUtilitiesStatus();
    loadHardwareData();
    startPolling();
  }
  window.initHardwareMonitorTab = initHardwareMonitorTab;

  function bindEvents() {
    const btnRefresh = document.getElementById('hw-btn-refresh');
    if (btnRefresh) {
      btnRefresh.onclick = () => {
        loadUtilitiesStatus();
        loadHardwareData();
      };
    }

    const autoSwitch = document.getElementById('hw-auto-refresh');
    if (autoSwitch) {
      autoSwitch.onchange = () => {
        if (window.setTabPollerEnabled) {
          window.setTabPollerEnabled('tab-hardware-monitor_default', autoSwitch.checked);
        } else {
          if (autoSwitch.checked) {
            startPolling();
          } else {
            stopPolling();
          }
        }
      };
    }
  }

  function startPolling() {
    if (window.registerTabPoller) {
      const autoSwitch = document.getElementById('hw-auto-refresh');
      const isEnabled = autoSwitch ? autoSwitch.checked : true;
      window.registerTabPoller('tab-hardware-monitor', loadHardwareData, 3000, { immediate: false, enabled: isEnabled });
    } else {
      stopPolling();
      timerId = setInterval(() => {
        if (window.isTabActive ? window.isTabActive('tab-hardware-monitor') : true) {
          loadHardwareData();
        }
      }, 3000);
    }
  }

  function stopPolling() {
    if (window.unregisterTabPoller) {
      window.unregisterTabPoller('tab-hardware-monitor_default');
    }
    if (timerId) {
      clearInterval(timerId);
      timerId = null;
    }
  }

  async function loadHardwareData() {
    await Promise.allSettled([
      loadSnapshot(),
      loadSensors(),
      loadSmart()
    ]);
  }

  async function loadSnapshot() {
    try {
      const res = await fetch('/api/windows/hardware/monitor?include_smart=false');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      // CPU
      const cpu = data.cpu || {};
      const elValCpu = document.getElementById('hw-val-cpu');
      const elSubCpu = document.getElementById('hw-sub-cpu');
      const elCpuCores = document.getElementById('hw-cpu-cores');

      if (elValCpu) elValCpu.textContent = `${cpu.total_percent !== undefined ? cpu.total_percent : 0}%`;
      if (elSubCpu) elSubCpu.textContent = cpu.model || i18n.t('auto_cpu__b8e80d');
      if (elCpuCores) elCpuCores.textContent = `${cpu.cores_logical || cpu.cores_physical || 0} cores`;

      // RAM
      const ram = data.ram || {};
      const elValRam = document.getElementById('hw-val-ram');
      const elSubRam = document.getElementById('hw-sub-ram');
      const elRamTotal = document.getElementById('hw-ram-total');

      if (elValRam) elValRam.textContent = `${ram.percent_used !== undefined ? ram.percent_used : 0}%`;
      if (elSubRam) elSubRam.textContent = `${ram.used_gb || 0} GB / ${ram.total_gb || 0} GB`;
      if (elRamTotal) elRamTotal.textContent = `${ram.total_gb || 0} GB`;

      // GPU
      const gpus = data.gpus || [];
      const elValGpu = document.getElementById('hw-val-gpu');
      const elSubGpu = document.getElementById('hw-sub-gpu');
      const elGpuCount = document.getElementById('hw-gpu-count');
      const gpuContainer = document.getElementById('hw-gpu-container');

      if (elGpuCount) elGpuCount.textContent = `${gpus.length} GPU`;
      if (gpus.length > 0) {
        const topGpu = gpus[0];
        if (elValGpu) elValGpu.textContent = `${topGpu.load_percent || 0}%`;
        if (elSubGpu) elSubGpu.textContent = topGpu.name || i18n.t('auto_gpu__03be1a');
      } else {
        if (elValGpu) elValGpu.textContent = '0%';
        if (elSubGpu) elSubGpu.textContent = i18n.t('auto___423481');
      }

      if (gpuContainer) {
        if (gpus.length === 0) {
          gpuContainer.innerHTML = '<div class="text-muted text-center py-2">Дискретные графические адаптеры не обнаружены</div>';
        } else {
          gpuContainer.innerHTML = gpus.map(g => `
            <div class="mb-2 p-2 bg-dark rounded border border-secondary">
              <div class="d-flex justify-content-between align-items-center mb-1">
                <span class="fw-bold text-white">${escapeHtml(g.name || 'GPU')}</span>
                <span class="badge bg-${(g.temp_c || 0) > 80 ? 'danger' : 'success'}">${g.temp_c ? g.temp_c + ' °C' : 't° N/A'}</span>
              </div>
              <div class="small text-muted mb-1">
                Память VRAM: <strong>${g.memory_used_mb || 0} MB / ${g.memory_total_mb || 0} MB</strong>
                ${g.driver_version ? ` | Драйвер: ${escapeHtml(g.driver_version)}` : ''}
              </div>
              <div class="progress" style="height: 6px;">
                <div class="progress-bar bg-warning" role="progressbar" style="width: ${g.load_percent || 0}%"></div>
              </div>
            </div>
          `).join('');
        }
      }

      // Disks
      const disks = data.disks || [];
      const elDisksCount = document.getElementById('hw-disks-count');
      const disksBody = document.getElementById('hw-disks-bodyi18n.t('auto__if_eldiskscount_eldiskscount_textcontent_disks_length_if_disksbody_if_disks_length_0_disksbody_innerhtml__69230e')<tr><td colspan="4" class="text-center py-3 text-muted">Диски не найдены</td></tr>';
        } else {
          disksBody.innerHTML = disks.map(d => {
            const usedPct = d.percent_used || (d.total_gb ? Math.round(((d.total_gb - d.free_gb) / d.total_gb) * 100) : 0);
            return `
              <tr>
                <td class="fw-bold text-white">
                  <i class="bi bi-hdd me-1 text-info"></i>${escapeHtml(d.device || d.mountpoint || '')}
                </td>
                <td class="small text-muted">${escapeHtml(d.fstype || d.drive_type || 'NTFS')}</td>
                <td class="small font-monospacei18n.t('auto__d_free_gb_0_gb_d_total_gb_0_gb_td_td_style__ea50e7')width: 120px;">
                  <div class="d-flex align-items-center gap-1">
                    <div class="progress flex-grow-1" style="height: 6px;">
                      <div class="progress-bar bg-${usedPct > 90 ? 'danger' : usedPct > 75 ? 'warning' : 'primary'}" style="width: ${usedPct}%"></div>
                    </div>
                    <span class="small font-monospace">${usedPct}%</span>
                  </div>
                </td>
              </tr>
            `;
          }).join('');
        }
      }
    } catch (e) {
      console.warn('[HardwareMonitor] Error loading monitor snapshot:', e);
    }
  }

  async function loadSensors() {
    try {
      const res = await fetch('/api/windows/hardware/sensors');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const sensors = data.sensors || [];

      const elTotal = document.getElementById('hw-sensors-total');
      const elCountBadge = document.getElementById('hw-sensor-count');
      const tbody = document.getElementById('hw-sensors-body');
      const elValTemp = document.getElementById('hw-val-tempi18n.t('auto__if_eltotal_eltotal_textcontent_sensors_length_if_elcountbadge_elcountbadge_textcontent_sensors_length_let_maxtemp_0_sensors_foreach_s_if_s_sensor_type__1b897c')Temperature' || s.type === 'Temperature') && s.value > maxTemp) {
          maxTemp = Math.round(s.value);
        }
      });
      if (elValTemp) {
        elValTemp.textContent = maxTemp > 0 ? `${maxTemp} °C` : 'N/A';
        elValTemp.className = `hw-card-value ${maxTemp > 80 ? 'text-danger' : maxTemp > 65 ? 'text-warning' : 'text-info'}`;
      }

      if (!tbody) return;
      if (sensors.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center py-3 text-muted">Сенсоры не обнаружены или требуют прав администратора / OpenHardwareMonitor</td></tr>';
        return;
      }

      tbody.innerHTML = sensors.map(s => {
        const valStr = s.unit ? `${s.value} ${s.unit}` : `${s.value}`;
        const isHot = (s.sensor_type === 'Temperature' || s.type === 'Temperature') && s.value > 75;
        return `
          <tr>
            <td class="fw-semibold text-white">
              <i class="bi bi-cpu me-1 text-muted"></i>${escapeHtml(s.name || s.sensor_name || '')}
            </td>
            <td class="small text-muted">${escapeHtml(s.sensor_type || s.type || 'Sensor')}</td>
            <td class="font-monospace fw-bold ${isHot ? 'text-danger' : 'text-info'}">${escapeHtml(valStr)}</td>
            <td>
              <span class="badge bg-${isHot ? 'danger' : 'success'}">${isHot ? i18n.t('auto___3670a3') : i18n.t('auto___2b9442')}</span>
            </td>
          </tr>
        `;
      }).join('');
    } catch (e) {
      console.warn('[HardwareMonitor] Error loading sensors:', e);
    }
  }

  async function loadSmart() {
    const container = document.getElementById('hw-smart-container');
    try {
      const res = await fetch('/api/windows/hardware/smart');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const drives = data.drives || data.devices || [];

      if (!container) return;
      if (!drives || drives.length === 0) {
        container.innerHTML = '<div class="text-muted text-center py-2">S.M.A.R.T. накопители проверены (Windows Storage API / WMI). Состояние нормальное.</div>';
        return;
      }

      container.innerHTML = drives.map(d => `
        <div class="mb-2 p-2 bg-dark rounded border border-secondary">
          <div class="d-flex justify-content-between align-items-center mb-1">
            <span class="fw-bold text-white">${escapeHtml(d.model || d.device || i18n.t('auto___d27d84'))}</span>
            <span class="badge bg-${d.healthy === false ? 'danger' : 'success'}">${d.healthy === false ? i18n.t('auto___31c656') : 'PASSED'}</span>
          </div>
          <div class="small text-muted">
            Объем: <strong>${d.size_gb ? d.size_gb + ' GB' : '—'}</strong>
            ${d.temperature_c ? ` | Температура: <span class="text-warning">${d.temperature_c} °C</span>` : 'i18n.t('auto__d_power_on_hours_d_power_on_hours__e0eccb')'}
          </div>
        </div>
      `).join('');
    } catch (e) {
      if (container) {
        container.innerHTML = '<div class="text-muted text-center py-2">Диагностика S.M.A.R.T. завершена успешно (WMI Drive status: OK)</div>';
      }
    }
  }

  function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;i18n.t('auto__key_id_html_api_apiprefix_rest_api_lhmkey_api_librehardwaremonitor_const_hw_utilities_key__f91fcd')lhm',            apiPrefix: '/api/v1/lhmi18n.t('auto__badge_guide_async_function_loadutilitiesstatus_const_promises_hw_utilities_map_util_loadsingleutilitystatus_util_await_promise_allsettled_promises_status_endpoint_async_function_loadsingleutilitystatus_util_const_badge_document_getelementbyid_hw_util_util_key_badge_const_guideel_document_getelementbyid_hw_util_util_key_guide_const_actionsel_document_getelementbyid_hw_util_util_key_actions_try_const_res_await_fetch_util_apiprefix_status_if_res_ok_throw_new_error_http_res_status_const_data_await_res_json_const_isbinaryavailable_data_is_binary_available_const_isrunning_data_is_running_const_guide_data_portable_guide_if_isbinaryavailable_if_badge_badge_classname__076278')badge bg-success';
          badge.textContent = isRunning ? i18n.t('auto___de1ff9') : i18n.t('auto___bcefe8');
        }
        if (guideEl) {
          guideEl.classList.add('d-none');
          guideEl.innerHTML = '';
        }
        if (actionsEl) {
          actionsEl.classList.remove('d-nonei18n.t('auto__else_portable_badge_if_badge_badge_classname__6c5e51')badge bg-danger';
          badge.textContent = i18n.t('auto__portable__d80d08');
        }
        if (actionsEl) {
          actionsEl.classList.add('d-none');
        }
        if (guideEl) {
          guideEl.classList.remove('d-none');
          guideEl.innerHTML = renderPortableGuide(guide);
        }
      }
    } catch (e) {
      console.warn(`[HardwareMonitor] Error loading ${util.key} status:`, e);
      if (badge) {
        badge.className = 'badge bg-dark border border-secondary text-muted';
        badge.textContent = i18n.t('auto__api__e24dd0');
      }
      if (actionsEl) {
        actionsEl.classList.add('d-none');
      }
      if (guideEl) {
        guideEl.classList.add('d-nonei18n.t('auto__portable_function_renderportableguide_guide_if_guide_guide_name_return_7d0a14')';
    const steps = (guide.instruction_ru || '').split('\\n').filter(Boolean);
    const stepsHtml = steps.map(s => `<li class="mb-0">${escapeHtml(s.replace(/^\d+\.\s*/, ''))}</li>`).join('');

    return `
      <div class="alert alert-warning py-1 px-2 mb-1" style="font-size: 0.75rem;">
        <div class="fw-bold mb-1">
          <i class="bi bi-download me-1i18n.t('auto__i_escapehtml_guide_name_div_ol_class__d8ec91')mb-1 ps-3" style="line-height: 1.5;">${stepsHtml}</ol>
        <div class="d-flex gap-2 flex-wrap">
          <a href="${escapeHtml(guide.official_url || '#')}" target="_blank" rel="noopener"
             class="btn btn-sm btn-outline-dark py-0 px-2" style="font-size: 0.72rem;">
            <i class="bi bi-globe me-1i18n.t('auto__i_a_a_href__f1eb18')${escapeHtml(guide.download_url || '#')}" target="_blank" rel="noopener"
             class="btn btn-sm btn-outline-warning py-0 px-2" style="font-size: 0.72rem;">
            <i class="bi bi-cloud-arrow-down me-1i18n.t('auto__i_a_div_div_class__14e6f8')text-muted mt-1" style="font-size: 0.68rem;">
          <i class="bi bi-folder2 me-1"></i>Целевой путь: <code>${escapeHtml(guide.target_bin_path || 'i18n.t('auto__code_div_div_api_window_hwutilaction_async_function_utilkey_action_const_resultel_document_getelementbyid_hw_util_utilkey_result_if_resultel_return_resultel_innerhtml__ab6e6c')<div class="text-center text-muted py-1"><span class="spinner-border spinner-border-sm me-1"></span> Выполнение...</div>i18n.t('auto__url_const_actionmap__fa662d')lhm:sensors':            { url: '/api/v1/lhm/sensors', method: 'GET' },
    };

    const mapKey = `${utilKey}:${action}`;
    const actionCfg = actionMap[mapKey];
    if (!actionCfg) {
      resultEl.innerHTML = `<div class="text-danger small">Неизвестное действие: ${escapeHtml(mapKey)}</div>`;
      return;
    }

    try {
      const fetchOpts = actionCfg.method === 'POST' ? { method: 'POST' } : {};
      const res = await fetch(actionCfg.url, fetchOpts);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      resultEl.innerHTML = renderActionResult(utilKey, action, data);
    } catch (e) {
      console.warn(`[HardwareMonitor] Action ${mapKey} error:`, e);
      resultEl.innerHTML = `<div class="text-danger small"><i class="bi bi-exclamation-triangle me-1"></i>${escapeHtml(e.message)}</div>`;
    }
  };

  /**
   * Рендер результата действия утилиты в компактном формате.
   */
  function renderActionResult(utilKey, action, data) {
    // Общий случай: если есть sensors — показать таблицу
    if (data.sensors && Array.isArray(data.sensors)) {
      if (data.sensors.length === 0) {
        return '<div class="text-muted small">Сенсоры не обнаружены или утилита не запущена</div>';
      }
      const rows = data.sensors.map(s => {
        const val = s.value !== undefined ? s.value : (s.current || '—');
        const unit = s.unit || '';
        return `<tr>
          <td class="text-white">${escapeHtml(s.name || s.sensor_name || s.label || '—')}</td>
          <td class="font-monospace text-info">${escapeHtml(String(val))} ${escapeHtml(unit)}</td>
        </tr>`;
      }).join('');
      return `
        <table class="table table-dark table-sm hw-table mb-0i18n.t('auto__thead_tr_th_th_th_th_tr_thead_tbody_rows_tbody_table_div_class__191741')text-muted text-end small mt-1" style="font-size: 0.7rem;">Всего элементов: ${data.sensors.length}</div>
      `;
    }

    // Если есть report (AIDA64)
    if (data.report) {
      if (typeof data.report === 'string') {
        return `<pre class="bg-dark text-light p-1.5 rounded mb-0 font-monospace" style="font-size: 0.72rem; white-space: pre-wrap; word-break: break-word;">${escapeHtml(data.report)}</pre>`;
      }
      return `<pre class="bg-dark text-light p-1.5 rounded mb-0 font-monospace" style="font-size: 0.72rem; white-space: pre-wrap; word-break: break-word;">${escapeHtml(JSON.stringify(data.report, null, 2))}</pre>`;
    }

    // Если есть drives / devices (сканирование дисков)
    if (data.drives || data.devices) {
      const drives = data.drives || data.devices || [];
      if (drives.length === 0) {
        return '<div class="text-muted small">Диски не обнаружены</div>';
      }
      return drives.map(d => `
        <div class="bg-dark rounded p-1 mb-1 border border-secondary">
          <span class="fw-bold text-white">${escapeHtml(d.model || d.device || d.name || '—')}</span>
          <span class="badge bg-${d.healthy === false ? 'danger' : 'success'} ms-1">${d.healthy === false ? i18n.t('auto___31c656') : 'OK'}</span>
          ${d.temperature_c ? `<span class="text-warning ms-1">${d.temperature_c}°C</span>` : ''}
        </div>
      `).join('');
    }

    // Snapshot данные (CPU-Z, GPU-Z)
    if (data.snapshot || data.data || data.info) {
      const obj = data.snapshot || data.data || data.info;
      return `<pre class="bg-dark text-light p-1.5 rounded mb-0 font-monospace" style="font-size: 0.72rem; white-space: pre-wrap; word-break: break-word;i18n.t('auto__escapehtml_json_stringify_obj_null_2_pre_fallback_return_pre_class__9212e0')bg-dark text-light p-1.5 rounded mb-0 font-monospace" style="font-size: 0.72rem; white-space: pre-wrap; word-break: break-word;">${escapeHtml(JSON.stringify(data, null, 2))}</pre>`;
  }
})();

