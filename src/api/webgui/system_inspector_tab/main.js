// System & Hardware Inspector Tab JS Module
(function() {
  let sysWs = null;
  let isSysInitialized = false;
  let isSysPaused = false;
  let isNetPaused = false;
  let currentNetFilter = 'internet';
  let _currentUiRefreshSeconds = 5;
  let cachedProcStats = null;

  async function fetchProcessesFromDb() {
    if (isSysPaused) return;
    try {
      const res = await fetch('/api/v1/system/processes?limit=35&source=db');
      if (res.ok) {
        const procs = await res.json();
        if (!latestTelemetrySnapshot) {
          latestTelemetrySnapshot = { top_processes: [] };
        }
        latestTelemetrySnapshot.top_processes = procs;
        renderProcessTable();

        const timeBadge = document.getElementById('sys-proc-updated-time');
        if (timeBadge) {
          const now = new Date();
          timeBadge.textContent = now.toLocaleTimeString();
        }
      }
    } catch (e) {
      console.warn(i18n.t('auto__systeminspectortab_sqlite__114b5a'), e);
    }
  }

  async function fetchLhmSensors() {
    const container = document.getElementById('sys-lhm-sensors-container');
    const badgeStatus = document.getElementById('sys-lhm-status-badge');
    const badgeCount = document.getElementById('sys-lhm-sensors-count');
    const btnLaunch = document.getElementById('btn-sys-launch-lhmi18n.t('auto__if_container_return_try_1_lhm_let_lhmstatus_null_try_const_sres_await_fetch__5fd2e6')/api/v1/lhm/status');
        if (sRes.ok) lhmStatus = await sRes.json();
      } catch {}

      isLhmRunning = lhmStatus && lhmStatus.is_running;

      if (btnLaunch) {
        if (!isLhmRunning && lhmStatus && lhmStatus.is_binary_available) {
          btnLaunch.classList.remove('d-none');
        } else {
          btnLaunch.classList.add('d-none');
        }
      }

      let sensorsList = [];

      if (isLhmRunning) {
        if (badgeStatus) {
          badgeStatus.textContent = '● LHM Active';
          badgeStatus.className = 'badge bg-success';
        }
        showLhmFallbackNotice(false);
        const mRes = await fetch('/api/v1/lhm/metricsi18n.t('auto__if_mres_ok_const_mdata_await_mres_json_sensorslist_mdata_sensors_else_fallback_sqlite_if_badgestatus_badgestatus_textcontent__6ac53a')● БД SQLite';
          badgeStatus.className = 'badge bg-primary';
        }
        try {
          const dbRes = await fetch('/api/v1/system/sensors?source=dbi18n.t('auto__if_dbres_ok_const_dbdata_await_dbres_json_if_array_isarray_dbdata_dbdata_length_0_sensorslist_dbdata_map_s_id_s_id_s_sensor_id_s_sensor_name_hardware_name_s_hardware_name__2f9160')System Hardware',
                hardware_type: s.hardware_type || 'system',
                sensor_category: s.sensor_category || 'General',
                sensor_name: s.sensor_name || 'Sensor',
                value_raw: s.value_raw || `${s.value_numeric ?? 0} ${s.unit || ''}`.trim(),
                value_numeric: s.value_numeric ?? 0,
                unit: s.unit || 'i18n.t('auto__showlhmfallbacknotice_false_catch_live_fallback_live_fallback_if_sensorslist_length_0_if_badgestatus_badgestatus_textcontent__ba206b')WMI/GPU (live)';
            badgeStatus.className = 'badge bg-secondaryi18n.t('auto__live_showlhmfallbacknotice_true_try_const_liveres_await_fetch__ca1d8f')/api/v1/system/sensors?source=live');
            if (liveRes.ok) {
              const raw = await liveRes.json();
              sensorsList = (raw || []).map(s => ({
                id: s.sensor_id || s.id || s.name,
                hardware_name: s.hardware_name || (s.category ? s.category.toUpperCase() : 'System Hardware'),
                hardware_type: s.hardware_type || 'system',
                sensor_category: s.sensor_category || s.category || 'Temperatures',
                sensor_name: s.sensor_name || s.name,
                value_raw: s.value_raw || (s.unit ? `${s.value} ${s.unit}` : `${s.value}`),
                value_numeric: s.value_numeric ?? (typeof s.value === 'number' ? s.value : parseFloat(s.value)),
                unit: s.unit || '',
              }));
            }
          } catch (liveErr) {
            console.warn(i18n.t('auto__systeminspectortab_live_fallback__df0a7a'), liveErr);
          }
        }
      }

      cachedSensors = sensorsList;
      if (badgeCount) {
        badgeCount.textContent = `${sensorsList.length} шт.`;
      }

      renderSensors();
    } catch (e) {
      console.warn('[SystemInspectorTab] Failed to fetch LHM sensors:', e);
      if (container) {
        container.innerHTML = `<div class="text-center py-4 text-muted small">Датчики опрашиваются... (${e.message})</div>`;
      }
    }
  }

  /** Показывает или скрывает предупреждение о live-fallback при пустой БД сенсоров. */
  function showLhmFallbackNotice(visible) {
    const notice = document.getElementById('sys-lhm-fallback-notice');
    if (!notice) return;
    if (visible) {
      notice.classList.remove('d-none');
    } else {
      notice.classList.add('d-nonei18n.t('auto__if_container_return_try_1_lhm_let_lhmstatus_null_try_const_sres_await_fetch__b3d7d7')/api/v1/lhm/status');
        if (sRes.ok) lhmStatus = await sRes.json();
      } catch {}

      isLhmRunning = lhmStatus && lhmStatus.is_running;

      if (btnLaunch) {
        if (!isLhmRunning && lhmStatus && lhmStatus.is_binary_available) {
          btnLaunch.classList.remove('d-none');
        } else {
          btnLaunch.classList.add('d-none');
        }
      }

      let sensorsList = [];

      if (isLhmRunning) {
        if (badgeStatus) {
          badgeStatus.textContent = '● LHM Active';
          badgeStatus.className = 'badge bg-success';
        }
        const mRes = await fetch('/api/v1/lhm/metricsi18n.t('auto__if_mres_ok_const_mdata_await_mres_json_sensorslist_mdata_sensors_else_fallback_sqlite_if_badgestatus_badgestatus_textcontent__6ac53a')● БД SQLite';
          badgeStatus.className = 'badge bg-primary';
        }
        try {
          const dbRes = await fetch('/api/v1/system/sensors?source=dbi18n.t('auto__if_dbres_ok_const_dbdata_await_dbres_json_if_array_isarray_dbdata_dbdata_length_0_sensorslist_dbdata_map_s_id_s_id_s_sensor_id_s_sensor_name_hardware_name_s_hardware_name__2f9160')System Hardware',
                hardware_type: s.hardware_type || 'system',
                sensor_category: s.sensor_category || 'General',
                sensor_name: s.sensor_name || 'Sensor',
                value_raw: s.value_raw || `${s.value_numeric ?? 0} ${s.unit || ''}`.trim(),
                value_numeric: s.value_numeric ?? 0,
                unit: s.unit || 'i18n.t('auto__catch_live_fallback_live_fallback_if_sensorslist_length_0_if_badgestatus_badgestatus_textcontent__1a00a6')WMI/GPU (live)';
            badgeStatus.className = 'badge bg-secondary';
          }
          try {
            const liveRes = await fetch('/api/v1/system/sensors?source=live');
            if (liveRes.ok) {
              const raw = await liveRes.json();
              sensorsList = (raw || []).map(s => ({
                id: s.sensor_id || s.id || s.name,
                hardware_name: s.hardware_name || (s.category ? s.category.toUpperCase() : 'System Hardware'),
                hardware_type: s.hardware_type || 'system',
                sensor_category: s.sensor_category || s.category || 'Temperatures',
                sensor_name: s.sensor_name || s.name,
                value_raw: s.value_raw || (s.unit ? `${s.value} ${s.unit}` : `${s.value}`),
                value_numeric: s.value_numeric ?? (typeof s.value === 'number' ? s.value : parseFloat(s.value)),
                unit: s.unit || '',
              }));
            }
          } catch (liveErr) {
            console.warn(i18n.t('auto__systeminspectortab_live_fallback__df0a7a'), liveErr);
          }
        }
      }

      cachedSensors = sensorsList;
      if (badgeCount) {
        badgeCount.textContent = `${sensorsList.length} шт.`;
      }

      renderSensors();
    } catch (e) {
      console.warn('[SystemInspectorTab] Failed to fetch LHM sensors:', e);
      if (container) {
        container.innerHTML = `<div class="text-center py-4 text-muted small">Датчики опрашиваются... (${e.message})</div>`;
      }
    }
  }

  function renderSensors() {
    const container = document.getElementById('sys-lhm-sensors-container');
    if (!container) return;

    const searchInput = document.getElementById('sys-lhm-search');
    const filterText = (searchInput ? searchInput.value : '').trim().toLowerCase();

    if (!Array.isArray(cachedSensors) || cachedSensors.length === 0) {
      container.innerHTML = `
        <div class="text-center py-4 text-muted smalli18n.t('auto__div_librehardwaremonitor_div_div_class__341524')mt-2 text-muted" style="font-size: 0.72rem;">Убедитесь, что LHM запущен с правами администратора и включен Web Server (:8085)</div>
        </div>
      `;
      return;
    }

    const filtered = cachedSensors.filter(s => {
      // Category filter
      if (currentSensorCategory !== 'all') {
        const catLower = (s.sensor_category || '').toLowerCase();
        const typeLower = (s.hardware_type || '').toLowerCase();
        if (currentSensorCategory === 'temperature' && !catLower.includes('temp')) return false;
        if (currentSensorCategory === 'load' && !catLower.includes('load')) return false;
        if (currentSensorCategory === 'fan' && !catLower.includes('fan') && !catLower.includes('control')) return false;
        if (currentSensorCategory === 'voltage' && !catLower.includes('volt') && !catLower.includes('power')) return false;
        if (currentSensorCategory === 'clock' && !catLower.includes('clock')) return false;
      }

      // Text search
      if (filterText) {
        const hName = (s.hardware_name || '').toLowerCase();
        const sName = (s.sensor_name || '').toLowerCase();
        const sCat = (s.sensor_category || '').toLowerCase();
        const valStr = String(s.value_raw || '').toLowerCase();
        return hName.includes(filterText) || sName.includes(filterText) || sCat.includes(filterText) || valStr.includes(filterText);
      }
      return true;
    });

    if (filtered.length === 0) {
      container.innerHTML = `<div class="text-center py-4 text-muted small">По выбранному фильтру сенсоров не найдено</div>`;
      return;
    }

    // Group sensors by Hardware Name or Category
    const groups = {};
    filtered.forEach(s => {
      const grpKey = s.hardware_name || s.sensor_category || i18n.t('auto___2cf041');
      if (!groups[grpKey]) groups[grpKey] = [];
      groups[grpKey].push(s);
    });

    container.innerHTML = Object.entries(groups).map(([grpName, items]) => {
      const itemsHtml = items.map(s => {
        const cat = (s.sensor_category || '').toLowerCase();
        const num = s.value_numeric;
        const valRaw = s.value_raw || `${num || 0} ${s.unit || ''}`;

        let valClass = 'text-white';
        let badgeHtml = '';

        if (cat.includes('temp')) {
          if (num > 75) valClass = 'text-danger fw-bold';
          else if (num > 60) valClass = 'text-warning fw-bold';
          else valClass = 'text-info';
          badgeHtml = `<span class="badge ${num > 75 ? 'bg-danger' : num > 60 ? 'bg-warning text-dark' : 'bg-info text-dark'}" style="font-size: 0.65rem;">t°</span>`;
        } else if (cat.includes('load')) {
          const pct = Math.min(100, Math.max(0, num || 0));
          badgeHtml = `
            <div class="progress" style="width: 45px; height: 4px; background: rgba(255,255,255,0.1);">
              <div class="progress-bar ${pct > 80 ? 'bg-danger' : pct > 50 ? 'bg-warning' : 'bg-primary'}" style="width: ${pct}%"></div>
            </div>
          `;
        } else if (cat.includes('fan')) {
          valClass = 'text-success';
        } else if (cat.includes('clock')) {
          valClass = 'text-primary';
        }

        return `
          <div class="sys-sensor-row">
            <span class="sys-sensor-name" title="${escapeHtml(s.sensor_name)} (${escapeHtml(s.sensor_category)})">
              ${escapeHtml(s.sensor_name)}
            </span>
            <div class="d-flex align-items-center gap-1.5 ms-auto">
              ${badgeHtml}
              <span class="sys-sensor-value ${valClass}">${escapeHtml(valRaw)}</span>
            </div>
          </div>
        `;
      }).join('');

      return `
        <div class="sys-sensor-group">
          <div class="sys-sensor-group-title">
            <span><i class="bi bi-cpu me-1 text-info"></i> ${escapeHtml(grpName)}</span>
            <span class="badge bg-dark border border-secondary text-muted" style="font-size: 0.65rem;">${items.length}</span>
          </div>
          <div>
            ${itemsHtml}
          </div>
        </div>
      `;
    }).join('');
  }

  let lastAnalysisReportText = '';

  async function analyzeSensorsAndReport() {
    const modalEl = document.getElementById('sysSensorAnalysisModal');
    let modal = null;
    if (modalEl && window.bootstrap && window.bootstrap.Modal) {
      modal = window.bootstrap.Modal.getOrCreateInstance(modalEl);
      modal.show();
    }

    // Set Loading state in modal
    const titleEl = document.getElementById('modal-sensor-status-title');
    const subEl = document.getElementById('modal-sensor-status-sub');
    const aiCompEl = document.getElementById('modal-sensor-ai-comparison');
    const devListEl = document.getElementById('modal-sensor-devices-list');
    const devCountEl = document.getElementById('modal-sensor-devices-count');
    const modelBadge = document.getElementById('modal-sensor-model-badge');

    if (titleEl) titleEl.textContent = i18n.t('auto__ai__4adf76');
    if (subEl) subEl.textContent = i18n.t('auto__csv__0d764f');
    if (aiCompEl) {
      aiCompEl.innerHTML = '<div class="d-flex align-items-center gap-2 py-3"><div class="spinner-border spinner-border-sm text-primary" role="status"></div><span>Запрос к модели AI и сравнительный анализ номинальных параметров железа...</span></div>';
    }
    if (devListEl) {
      devListEl.innerHTML = '<span class="badge bg-dark border border-secondary text-muted"><span class="spinner-border spinner-border-sm me-1" style="width:0.6rem;height:0.6rem;"></span>Определение устройств...</span>';
    }

    let report = null;
    try {
      let res = await fetch('/api/v1/system/lhm-audit', { method: 'POST' });
      if (!res.ok) {
        res = await fetch('/api/v1/lhm/audit', { method: 'POST' });
      }
      if (res.ok) {
        report = await res.json();
      }
    } catch (err) {
      console.warn('[SystemInspectorTab] LHM Audit API error:', err);
    }

    // Extract metrics from report or fallback to cachedSensors
    const sensorsList = (report && report.aggregated_sensors) ? report.aggregated_sensors : (cachedSensors || []);
    const devices = (report && report.devices) ? report.devices : [];
    let healthScore = report ? (report.health_score || 100) : 100;
    const recommendations = [];

    let maxCpuTemp = null;
    let maxGpuTemp = null;
    let maxMbTemp = null;
    let maxStorageTemp = null;
    let fanSpeeds = [];
    let voltages = [];
    let cpuLoads = [];
    let gpuLoads = [];

    sensorsList.forEach(s => {
      const cat = ((s.category || s.sensor_category) || '').toLowerCase();
      const hw = ((s.hardware || s.hardware_name) || '').toLowerCase();
      const sName = (s.sensor_name || '').toLowerCase();
      const num = s.avg !== undefined ? s.avg : s.value_numeric;

      if (num === null || num === undefined || isNaN(num)) return;

      if (cat.includes('temp')) {
        if (hw.includes('cpu') || sName.includes('cpu') || sName.includes('core')) {
          if (maxCpuTemp === null || num > maxCpuTemp) maxCpuTemp = num;
        } else if (hw.includes('gpu') || hw.includes('nvidia') || sName.includes('gpu')) {
          if (maxGpuTemp === null || num > maxGpuTemp) maxGpuTemp = num;
        } else if (hw.includes('storage') || hw.includes('nvme') || hw.includes('ssd') || hw.includes('hdd') || sName.includes('drive')) {
          if (maxStorageTemp === null || num > maxStorageTemp) maxStorageTemp = num;
        } else {
          if (maxMbTemp === null || num > maxMbTemp) maxMbTemp = num;
        }
      } else if (cat.includes('fan')) {
        fanSpeeds.push({ name: s.sensor_name, value: num, unit: s.unit || 'RPM' });
      } else if (cat.includes('volt')) {
        voltages.push({ name: s.sensor_name, value: num, unit: s.unit || 'V' });
      } else if (cat.includes('load')) {
        if (hw.includes('cpu') || sName.includes('cpu')) cpuLoads.push(num);
        else if (hw.includes('gpu') || sName.includes('gpu')) gpuLoads.push(num);
      }
    });

    const overallMaxTemp = Math.max(
      maxCpuTemp || 0,
      maxGpuTemp || 0,
      maxMbTemp || 0,
      maxStorageTemp || 0
    );

    // Update Model Badge
    if (modelBadge && report) {
      modelBadge.textContent = report.ai_model_used || 'Heuristic Enginei18n.t('auto__render_devices_list_if_devcountel_devcountel_textcontent_devices_length_if_devlistel_if_devices_length_0_devlistel_innerhtml_devices_map_d_let_icon__4299a3')bi-hdd-network';
          const low = d.toLowerCase();
          if (low.includes('core') || low.includes('cpu') || low.includes('intel') || low.includes('amd')) icon = 'bi-cpu';
          else if (low.includes('geforce') || low.includes('gpu') || low.includes('nvidia') || low.includes('radeon')) icon = 'bi-gpu-card';
          else if (low.includes('ssd') || low.includes('hd') || low.includes('wdc') || low.includes('toshiba') || low.includes('st3500')) icon = 'bi-device-hdd';
          else if (low.includes('memory') || low.includes('ram')) icon = 'bi-memory';
          else if (low.includes('ethernet') || low.includes('wi-fi') || low.includes('network')) icon = 'bi-wifi';

          return `<span class="badge bg-dark border border-secondary text-info px-2 py-1 d-inline-flex align-items-center gap-1"><i class="bi ${icon}"></i> ${escapeHtml(d)}</span>`;
        }).join('');
      } else {
        devListEl.innerHTML = '<span class="text-muted small">Устройства считываются из текущей телеметрии</span>';
      }
    }

    // Render AI Comparison Report
    if (aiCompEl) {
      if (report && report.comparison_report) {
        aiCompEl.textContent = report.comparison_report;
      } else {
        aiCompEl.textContent = i18n.t('auto_ai__f28d1c');
      }
    }

    // Analyze CPU
    const elCpuBadge = document.getElementById('modal-cpu-temp-badge');
    const elCpuText = document.getElementById('modal-cpu-analysis-text');
    if (maxCpuTemp !== null) {
      if (elCpuBadge) {
        elCpuBadge.textContent = `${Math.round(maxCpuTemp)} °C`;
        elCpuBadge.className = `badge ${maxCpuTemp > 82 ? 'bg-danger' : maxCpuTemp > 70 ? 'bg-warning text-dark' : 'bg-successi18n.t('auto__if_maxcputemp_82_if_elcputext_elcputext_textcontent_math_round_maxcputemp_c_recommendations_push_type__b1a7a3')danger',
          icon: 'bi-exclamation-triangle-fill',
          title: i18n.t('auto___51cfdb'),
          text: `Пиковая/средняя температура CPU достигает ${Math.round(maxCpuTemp)}°C. Проверьте плотность прижима кулера, термопасту и запыленность радиатора.`
        });
      } else if (maxCpuTemp > 70) {
        if (elCpuText) elCpuText.textContent = `Повышенная температура (${Math.round(maxCpuTemp)}°C) под нагрузкой.`;
        recommendations.push({
          type: 'warning',
          icon: 'bi-thermometer-high',
          title: i18n.t('auto__cpu_b9a733'),
          text: `Температура CPU ${Math.round(maxCpuTemp)}°C выше оптимального порога. Рекомендуется настроить кривую оборотов вентилятора.`
        });
      } else {
        if (elCpuText) elCpuText.textContent = `Штатный температурный режим (${Math.round(maxCpuTemp)}°C). Троттлинг отсутствует.`;
        recommendations.push({
          type: 'success',
          icon: 'bi-check-circle-fill',
          title: i18n.t('auto___803b47'),
          text: `Температура процессора ${Math.round(maxCpuTemp)}°C находится в безопасной зоне номинальных характеристик.`
        });
      }
    } else {
      if (elCpuBadge) elCpuBadge.textContent = 'N/A';
      if (elCpuText) elCpuText.textContent = i18n.t('auto__cpu__6eab63');
    }

    // Analyze GPU
    const elGpuBadge = document.getElementById('modal-gpu-temp-badge');
    const elGpuText = document.getElementById('modal-gpu-analysis-text');
    if (maxGpuTemp !== null) {
      if (elGpuBadge) {
        elGpuBadge.textContent = `${Math.round(maxGpuTemp)} °C`;
        elGpuBadge.className = `badge ${maxGpuTemp > 80 ? 'bg-danger' : maxGpuTemp > 72 ? 'bg-warning text-dark' : 'bg-successi18n.t('auto__if_maxgputemp_80_if_elgputext_elgputext_textcontent_gpu_math_round_maxgputemp_c_recommendations_push_type__fde995')danger',
          icon: 'bi-gpu-card',
          title: i18n.t('auto___cd5b94'),
          text: `Графический чип нагревается до ${Math.round(maxGpuTemp)}°C. Проверьте циркуляцию воздуха в корпусе ПК.`
        });
      } else {
        if (elGpuText) elGpuText.textContent = `Температура GPU ${Math.round(maxGpuTemp)}°C в норме.`;
        recommendations.push({
          type: 'success',
          icon: 'bi-check-circle-fill',
          title: i18n.t('auto___33faf5'),
          text: `Температурные показатели GPU (${Math.round(maxGpuTemp)}°C) соответствуют номиналу.`
        });
      }
    } else {
      if (elGpuBadge) elGpuBadge.textContent = 'N/A';
      if (elGpuText) elGpuText.textContent = i18n.t('auto__gpu__ab99e3');
    }

    // Analyze Cooling
    const elFanBadge = document.getElementById('modal-fan-status-badge');
    const elFanText = document.getElementById('modal-fan-analysis-texti18n.t('auto__if_fanspeeds_length_0_const_activefans_fanspeeds_filter_f_f_value_0_if_elfanbadge_elfanbadge_textcontent_activefans_length_elfanbadge_classname__134b7b')badge bg-successi18n.t('auto__if_elfantext_elfantext_textcontent_fanspeeds_length_else_if_elfanbadge_elfanbadge_textcontent__8a1f7c')Пассив / WMI';
      if (elFanText) elFanText.textContent = i18n.t('auto__bios__6d249e');
    }

    // Additional recommendations from backend report
    if (report && Array.isArray(report.recommendations)) {
      report.recommendations.forEach(r => {
        if (!recommendations.some(ex => ex.text.includes(r))) {
          recommendations.push({
            type: 'info',
            icon: 'bi-info-circle',
            title: i18n.t('auto___b4aa1a'),
            text: r
          });
        }
      });
    }

    // Update Header & Badge
    const badgeHealth = document.getElementById('modal-sensor-health-badge');
    if (badgeHealth) {
      badgeHealth.textContent = `Health: ${healthScore}/100`;
      badgeHealth.className = `badge ms-1 ${healthScore >= 85 ? 'bg-success' : healthScore >= 65 ? 'bg-warning text-dark' : 'bg-danger'}`;
    }

    const countStat = document.getElementById('modal-sensor-count-stati18n.t('auto__if_countstat_const_totalsmpls_report_report_total_samples_sensorslist_length_countstat_textcontent_sensorslist_length_totalsmpls_const_maxtempstat_document_getelementbyid__79963f')modal-sensor-max-temp');
    if (maxTempStat) maxTempStat.textContent = overallMaxTemp > 0 ? `${Math.round(overallMaxTemp)} °C` : 'N/A';

    const statusTitle = document.getElementById('modal-sensor-status-title');
    const statusSub = document.getElementById('modal-sensor-status-sub');
    const statusIcon = document.getElementById('modal-sensor-status-icon');

    if (healthScore >= 85) {
      if (statusIcon) statusIcon.textContent = '✅';
      if (statusTitle) statusTitle.textContent = i18n.t('auto___addd1a');
      if (statusSub) statusSub.textContent = `Усредненные показатели соответствуют спецификациям реального железа (макс. ${Math.round(overallMaxTemp)}°C).`;
    } else if (healthScore >= 65) {
      if (statusIcon) statusIcon.textContent = '⚠️';
      if (statusTitle) statusTitle.textContent = i18n.t('auto___7c9b75');
      if (statusSub) statusSub.textContent = `Пиковая температура ${Math.round(overallMaxTemp)}°C. Ознакомьтесь с AI-заключением и рекомендациями.`;
    } else {
      if (statusIcon) statusIcon.textContent = '🚨';
      if (statusTitle) statusTitle.textContent = i18n.t('auto___f7118b');
      if (statusSub) statusSub.textContent = `Зафиксирован опасный нагрев или высокая перегрузка компонентов.`;
    }

    // Render Recommendations List
    const recList = document.getElementById('modal-sensor-recommendations-list');
    if (recList) {
      recList.innerHTML = recommendations.map(r => `
        <div class="p-2.5 rounded border d-flex align-items-start gap-2.5" style="background: var(--surface-2); border-color: var(--border-color) !important;">
          <div class="mt-0.5">
            <span class="badge ${r.type === 'danger' ? 'bg-danger' : r.type === 'warning' ? 'bg-warning text-dark' : r.type === 'info' ? 'bg-info text-dark' : 'bg-success'} rounded-circle p-1.5 d-flex align-items-center justify-content-center" style="width: 24px; height: 24px;">
              <i class="bi ${r.icon}" style="font-size: 0.75rem;"></i>
            </span>
          </div>
          <div class="flex-grow-1">
            <div class="fw-bold text-white mb-0.5" style="font-size: 0.82rem;">${escapeHtml(r.title)}</div>
            <div class="text-muted" style="font-size: 0.76rem; line-height: 1.4;">${escapeHtml(r.text)}</div>
          </div>
        </div>
      `).join('i18n.t('auto__prepare_clipboard_text_lastanalysisreporttext_ai_breadboard_ai_n_new_date_tolocalestring__efe91f')ru-RUi18n.t('auto__n_healthscore_100_n_ai_report_report_ai_model_used__ed0863')Heuristici18n.t('auto__n_devices_length_devices_join__c4d383'), i18n.t('auto__n_sensorslist_length_n_overallmaxtemp_0_math_round_overallmaxtemp__5a3cf6') °C' : 'N/Ai18n.t('auto__n_n_ai_n_report_report_comparison_report_report_comparison_report__fc1133')Параметры в норме.i18n.t('auto__n_n_n_recommendations_map_r_i_i_1_r_title_r_text_join__b71b38')\n') +
      `\n======================================================`;
  }

  function updateCoreMetrics(snap) {
    if (!snap) return;

    // CPU
    if (snap.cpu) {
      const cpuVal = document.getElementById('sys-metric-cpu-val');
      const cpuFill = document.getElementById('sys-metric-cpu-fill');
      const cpuSub = document.getElementById('sys-metric-cpu-sub');

      const pct = Number(snap.cpu.total_percent || 0);
      if (cpuVal) cpuVal.innerText = `${pct.toFixed(1)}%`;
      if (cpuFill) cpuFill.style.width = `${Math.min(100, pct)}%`;
      if (cpuSub) cpuSub.innerText = `${snap.cpu.physical_cores || '--i18n.t('auto__snap_cpu_logical_cores__27129a')--i18n.t('auto__ram_if_snap_memory_const_ramval_document_getelementbyid__fb9bfc')sys-metric-ram-val');
      const ramFill = document.getElementById('sys-metric-ram-fill');
      const ramSub = document.getElementById('sys-metric-ram-subi18n.t('auto__const_usedgb_number_snap_memory_used_gb_0_const_totalgb_number_snap_memory_total_gb_0_const_pct_number_snap_memory_percent_0_if_ramval_ramval_innertext_usedgb_tofixed_1_totalgb_tofixed_1_gb_if_ramfill_ramfill_style_width_pct_if_ramsub_ramsub_innertext_pct_number_snap_memory_available_gb_0_tofixed_1_gb_gpu_if_array_isarray_snap_gpus_snap_gpus_length_0_const_g_snap_gpus_0_const_gpuval_document_getelementbyid__e84949')sys-metric-gpu-val');
      const gpuSub = document.getElementById('sys-metric-gpu-sub');

      if (gpuVal) gpuVal.innerText = g.name || 'GPU';
      if (gpuSub) gpuSub.innerText = `VRAM: ${Number(g.memory_total_gb || 0).toFixed(1)} GB | CUDA: ${g.has_cuda ? i18n.t('auto___8d2fab') : i18n.t('auto___f82a82')}`;
    }

    // Disk I/O
    if (snap.disk_io) {
      const diskVal = document.getElementById('sys-metric-disk-val');
      const diskSub = document.getElementById('sys-metric-disk-subi18n.t('auto__const_totalmb_snap_disk_io_read_bytes_per_sec_snap_disk_io_write_bytes_per_sec_1024_1024_tofixed_2_const_rkb_snap_disk_io_read_bytes_per_sec_1024_tofixed_0_const_wkb_snap_disk_io_write_bytes_per_sec_1024_tofixed_0_if_diskval_diskval_innertext_totalmb_mb_s_if_disksub_disksub_innertext_rkb_kb_s_wkb_kb_s_battery_power_const_powercont_document_getelementbyid__062600')sys-power-info-container');
    const powerBadge = document.getElementById('sys-power-status-badge');
    if (powerCont && snap.battery) {
      if (snap.battery.has_battery && snap.battery.percent !== null) {
        if (powerBadge) {
          powerBadge.textContent = `${snap.battery.percent}% ${snap.battery.power_plugged ? i18n.t('auto___7e9ecd') : i18n.t('auto___03aeda')}`;
          powerBadge.className = snap.battery.power_plugged ? 'badge bg-success-subtle text-success border border-success' : 'badge bg-warning-subtle text-warning border border-warningi18n.t('auto__const_minsleft_snap_battery_secs_left_math_round_snap_battery_secs_left_60_null_powercont_innerhtml_div_snap_battery_power_plugged__deba64')Подключено к сети' : i18n.t('auto___1d7f6d')}</div>
          <div>${minsLeft ? `Осталось ~${minsLeft} мин.` : i18n.t('auto___13615d') + (snap.battery.power_profile || 'Balanced')}</div>
        `;
      } else {
        if (powerBadge) {
          powerBadge.textContent = 'AC Mains';
          powerBadge.className = 'badge bg-secondary';
        }
        powerCont.innerHTML = `
          <div>Питание: Стационарная электросеть 220V</div>
          <div class="text-muted">Профиль: ${escapeHtml(snap.battery.power_profile || 'High Performance')}</div>
        `;
      }
    }
  }

  function updateHardwareQuick(snap) {
    if (!snap) return;

    // Physical Disks SMART Health
    const diskCont = document.getElementById('sys-physical-disks-container');
    const diskBadge = document.getElementById('sys-disk-health-badge');
    if (diskCont && Array.isArray(snap.physical_disks) && snap.physical_disks.length > 0) {
      const allHealthy = snap.physical_disks.every(d => d.health_status === 'Healthy');
      if (diskBadge) {
        diskBadge.textContent = allHealthy ? 'SMART OK' : i18n.t('auto___5f5f86');
        diskBadge.className = allHealthy ? 'badge bg-success-subtle text-success border border-success' : 'badge bg-warning-subtle text-warning border border-warning';
      }
      diskCont.innerHTML = snap.physical_disks.map(d => `
        <div class="d-flex justify-content-between align-items-center py-0.5 border-bottom border-dark-subtle" style="border-bottom-style: dashed !important;">
          <span class="text-truncate me-2" style="max-width: 160px;" title="${escapeHtml(d.model)}">${escapeHtml(d.model)}</span>
          <span class="badge bg-secondary font-monospace" style="font-size: 0.65rem;">${d.size_gb} GB ${escapeHtml(d.media_type || '')}</span>
        </div>
      `).join('');
    }

    // RAM SPD Modules
    const ramSticksCont = document.getElementById('sys-ram-sticks-container');
    const ramSticksBadge = document.getElementById('sys-ram-sticks-badge');
    if (ramSticksCont && Array.isArray(snap.ram_sticks) && snap.ram_sticks.length > 0) {
      if (ramSticksBadge) {
        ramSticksBadge.textContent = `${snap.ram_sticks.length} модулей`;
      }
      ramSticksCont.innerHTML = snap.ram_sticks.slice(0, 2).map(m => `
        <div class="d-flex justify-content-between align-items-center py-0.5">
          <span>${escapeHtml(m.bank_label)}: ${escapeHtml(m.manufacturer)}</span>
          <span class="font-monospace text-primary">${m.capacity_gb} GB @ ${m.speed_mhz} MT/s</span>
        </div>
      `).join('');
    } else if (ramSticksCont && snap.memory) {
      ramSticksCont.innerHTML = `<div>RAM: ${snap.memory.total_gb || '--i18n.t('auto__gb_div_reliability_open_ports_const_alertscont_document_getelementbyid__42d5a8')sys-alerts-ports-container');
    const alertsBadge = document.getElementById('sys-alerts-badge');
    if (alertsCont) {
      const portCount = Array.isArray(snap.listening_ports) ? snap.listening_ports.length : 0;
      const isReboot = snap.alerts && snap.alerts.reboot_pending;
      if (alertsBadge) {
        alertsBadge.textContent = isReboot ? i18n.t('auto___a40813') : i18n.t('auto___331370');
        alertsBadge.className = isReboot ? 'badge bg-warning text-dark' : 'badge bg-info-subtle text-info border border-info';
      }
      alertsCont.innerHTML = `
        <div>Сетевые сокеты: <span class="fw-bold text-whitei18n.t('auto__portcount_listen_span_div_div_class__2003e4')text-truncate" title="${escapeHtml(snap.alerts?.latest_alert || '')}">${escapeHtml(snap.alerts?.latest_alert || i18n.t('auto___f4824e'))}</div>
      `;
    }
  }

  async function fetchCoreMetrics() {
    try {
      const res = await fetch('/api/v1/system/metrics/core');
      if (res.ok) {
        const data = await res.json();
        if (!latestTelemetrySnapshot) latestTelemetrySnapshot = {};
        Object.assign(latestTelemetrySnapshot, data);
        updateCoreMetrics(data);
      }
    } catch (e) {
      console.warn(i18n.t('auto__systeminspectortab__b7563c'), e);
    }
  }

  async function fetchHardwareQuick() {
    try {
      const res = await fetch('/api/v1/system/hardware/quick');
      if (res.ok) {
        const data = await res.json();
        if (!latestTelemetrySnapshot) latestTelemetrySnapshot = {};
        Object.assign(latestTelemetrySnapshot, data);
        updateHardwareQuick(data);
      }
    } catch (e) {
      console.warn(i18n.t('auto__systeminspectortab__59c2b7'), e);
    }
  }

  function updateTelemetryDashboard(snap) {
    if (!snap) return;
    updateCoreMetrics(snap);
    updateHardwareQuick(snap);
    renderProcessTable();
    if (snap.network_activity) {
      renderNetworkActivityTable(snap.network_activity);
    }
  }

  function renderProcessTable() {
    if (!latestTelemetrySnapshot || isSysPaused) return;
    const filterInput = document.getElementById('sys-proc-search');
    const filter = (filterInput?.value || '').toLowerCase().trim();
    const tbody = document.getElementById('sys-proc-tbody');
    if (!tbody) return;

    const processes = latestTelemetrySnapshot.top_processes || [];
    const filtered = processes.filter(p => {
      if (!filter) return true;
      return (
        String(p.pid).includes(filter) ||
        (p.name || '').toLowerCase().includes(filter) ||
        (p.username && p.username.toLowerCase().includes(filter))
      );
    });

    if (filtered.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" class="text-center py-3 text-muted">Процессы не найдены</td></tr>';
      return;
    }

    tbody.innerHTML = filtered.map((p, idx) => {
      let cpuClass = '';
      if (p.cpu_percent > 40) cpuClass = 'badge-cpu-high';
      else if (p.cpu_percent > 15) cpuClass = 'badge-cpu-med';

      return `
        <tr class="sys-proc-row" data-idx="${idx}" style="cursor: pointer;" title=i18n.t('auto__ai__923281')>
          <td style="color: #38bdf8;">${p.pid}</td>
          <td style="font-weight: 600; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${escapeHtml(p.name || '')}">${escapeHtml(p.name || '')}</td>
          <td style="color: #94a3b8;">${escapeHtml(p.status || 'running')}</td>
          <td style="text-align: right;" class="${cpuClass}">${Number(p.cpu_percent || 0).toFixed(1)}%</td>
          <td style="text-align: right; color: #4ade80;">${Number(p.memory_mb || 0).toFixed(1)} MB</td>
          <td style="text-align: right; color: #a855f7;">${p.num_threads || 1}</td>
          <td style="color: #94a3b8;">${escapeHtml(p.username || 'SYSTEM')}</td>
        </tr>
      `;
    }).join('');

    tbody.querySelectorAll('.sys-proc-row').forEach(row => {
      row.onclick = () => {
        const idx = parseInt(row.getAttribute('data-idx'), 10);
        const p = filtered[idx];
        if (!p) return;

        if (window.AITableModal) {
          window.AITableModal.show({
            icon: '⚙️',
            title: p.name,
            subtitle: `PID: ${p.pid} | ${p.username || 'SYSTEM'}`,
            tableType: 'process',
            badges: [
              { text: `PID ${p.pid}`, class: 'badge bg-info text-dark' },
              { text: p.status || 'running', class: 'badge bg-success' }
            ],
            metadata: [
              { label: i18n.t('auto___79ec71'), value: p.name },
              { label: 'Process ID (PID)', value: String(p.pid) },
              { label: i18n.t('auto___c42702'), value: p.username || 'SYSTEM' },
              { label: i18n.t('auto___f7f293'), value: p.status || i18n.t('auto___eff79c') },
              { label: i18n.t('auto__cpu_15e14e'), value: `${Number(p.cpu_percent || 0).toFixed(1)}%` },
              { label: i18n.t('auto___5b8b72'), value: `${Number(p.memory_mb || 0).toFixed(1)} MB` },
              { label: i18n.t('auto___1a2061'), value: String(p.num_threads || 1) },
              { label: i18n.t('auto___a232b1'), value: p.exe || p.executable_path || i18n.t('auto__windows_0b21b3'), isCode: true, fullWidth: true }
            ],
            rawTitle: i18n.t('auto___d50554'),
            rawContent: Array.isArray(p.cmdline) ? p.cmdline.join(' ') : (p.cmdline || p.exe || ''),
            requestData: {
              pid: p.pid,
              cpu_percent: p.cpu_percent,
              memory_mb: p.memory_mb,
              username: p.username,
              status: p.status
            }
          });
        }
      };
    });
  }

  async function fetchNetworkActivity() {
    try {
      const res = await fetch('/api/v1/system/network-activity?limit=100');
      if (res.ok) {
        const data = await res.json();
        renderNetworkActivityTable(data);
      }
    } catch (e) {
      console.warn('[SystemInspectorTab] Failed to fetch network activity:', e);
    }
  }

  function renderNetworkActivityTable(activities) {
    if (activities) {
      cachedNetworkActivities = activities;
    }
    if (isNetPaused) return;

    const tbody = document.getElementById('sys-net-tbody');
    if (!tbody) return;

    const searchInput = document.getElementById('sys-net-search');
    const filterText = (searchInput?.value || '').toLowerCase().trim();
    const countBadge = document.getElementById('sys-netact-count-badge');
    const connsBadge = document.getElementById('sys-netact-conns-badge');

    const rawList = Array.isArray(cachedNetworkActivities) ? cachedNetworkActivities : [];

    // Filter by category and search query
    let filtered = rawList.filter(item => {
      if (currentNetFilter === 'internet' && !item.is_internet) return false;
      if (currentNetFilter === 'listen' && item.status !== 'LISTEN') return false;

      if (filterText) {
        return (
          String(item.pid).includes(filterText) ||
          (item.name || '').toLowerCase().includes(filterText) ||
          (item.user || '').toLowerCase().includes(filterText) ||
          (item.remote_address || '').toLowerCase().includes(filterText) ||
          (item.local_address || '').toLowerCase().includes(filterText) ||
          (item.service_type || '').toLowerCase().includes(filterText) ||
          (item.sent_summary || '').toLowerCase().includes(filterText) ||
          (item.recv_summary || 'i18n.t('auto__tolowercase_includes_filtertext_return_true_const_uniqueprocs_new_set_filtered_map_i_i_pid_size_if_countbadge_countbadge_textcontent_uniqueprocs_if_connsbadge_connsbadge_textcontent_filtered_length_if_filtered_length_0_tbody_innerhtml__955048')<tr><td colspan="6" class="text-center py-4 text-muted small">Нет активных сетевых соединений по выбранному фильтру</td></tr>';
      return;
    }

    tbody.innerHTML = filtered.map((item, idx) => {
      const isListen = item.status === 'LISTEN';
      const statusBadgeClass = isListen
        ? 'badge bg-secondary-subtle text-light border border-secondary'
        : item.status === 'ESTABLISHED'
        ? 'badge bg-success-subtle text-success border border-success'
        : 'badge bg-warning-subtle text-warning border border-warning';

      const protoBadge = item.protocol === 'UDP'
        ? '<span class="badge bg-primary text-white" style="font-size: 0.65rem;">UDP</span>'
        : '<span class="badge bg-dark border border-secondary text-info" style="font-size: 0.65rem;">TCP</span>';

      const isExtBadge = item.is_internet
        ? '<span class="badge bg-primary-subtle text-primary border border-primary px-1" style="font-size: 0.62rem;" title=i18n.t('auto___092aaf')>WAN</span>'
        : '<span class="badge bg-secondary px-1" style="font-size: 0.62rem;" title=i18n.t('auto__loopback_14dd1c')>LAN</span>';

      const formatNetKb = (kb) => {
        if (!kb || kb <= 0) return '0 KB';
        if (kb >= 1024 * 1024) return (kb / (1024 * 1024)).toFixed(2) + ' GB';
        if (kb >= 1024) return (kb / 1024).toFixed(1) + ' MB';
        return kb.toFixed(1) + ' KB';
      };

      const formatNetRate = (rate) => {
        if (!rate || rate <= 0.05) return '';
        if (rate >= 1024) return (rate / 1024).toFixed(1) + ' MB/s';
        return rate.toFixed(1) + ' KB/s';
      };

      const deltaSentStr = (item.delta_sent_kb && item.delta_sent_kb > 0)
        ? `▲ +${formatNetKb(item.delta_sent_kb)}${item.sent_rate_kbs > 0.05 ? ' (' + formatNetRate(item.sent_rate_kbs) + ')' : ''}`
        : '▲ 0 KB';
      const deltaRecvStr = (item.delta_recv_kb && item.delta_recv_kb > 0)
        ? `▼ +${formatNetKb(item.delta_recv_kb)}${item.recv_rate_kbs > 0.05 ? ' (' + formatNetRate(item.recv_rate_kbs) + ')' : ''}`
        : '▼ 0 KB';

      const totalSentStr = formatNetKb(item.sent_kb || 0);
      const totalRecvStr = formatNetKb(item.recv_kb || 0);

      return `
        <tr class="sys-net-row" data-idx="${idx}" style="cursor: pointer;" title=i18n.t('auto___bb922f')>
          <td>
            <div class="fw-bold text-white text-truncate" style="max-width: 165px;" title="${escapeHtml(item.name)}">${escapeHtml(item.name)}</div>
            <div class="small text-muted" style="font-size: 0.70rem;">PID: <span style="color: #38bdf8;">${item.pid}</span> ${item.user ? '• ' + escapeHtml(item.user) : ''}</div>
          </td>
          <td>
            <div class="d-flex align-items-center gap-1">
              ${isExtBadge}
              <span class="font-monospace text-light fw-semibold text-truncate" style="max-width: 195px;" title="${escapeHtml(item.remote_address)}">
                ${escapeHtml(item.remote_address !== '-' ? item.remote_address : item.local_address)}
              </span>
            </div>
            <div class="small text-muted font-monospace" style="font-size: 0.68rem;">Local: ${escapeHtml(item.local_address)}</div>
          </td>
          <td>
            <div class="d-flex align-items-center gap-1 mb-0.5">
              ${protoBadge}
              <span class="fw-semibold text-truncate" style="max-width: 210px; font-size: 0.74rem; color: #a855f7;" title="${escapeHtml(item.service_type)}">${escapeHtml(item.service_type)}</span>
            </div>
          </td>
          <td style="text-align: center;">
            <span class="${statusBadgeClass}" style="font-size: 0.68rem;">${escapeHtml(item.status)}</span>
          </td>
          <td>
            <div class="d-flex align-items-center justify-content-start gap-2 mb-1">
              <span class="badge bg-warning-subtle text-warning border border-warning px-1.5 py-0.5" style="font-size: 0.68rem;" title=i18n.t('auto___0c1b19')>
                ${deltaSentStr}
              </span>
              <span class="text-muted font-monospace" style="font-size: 0.68rem;" title=i18n.t('auto___6ebfa4')>
                Σ ${totalSentStr}
              </span>
            </div>
            <div class="d-flex align-items-start gap-1">
              <i class="bi bi-arrow-up-right text-warning mt-0.5" style="font-size: 0.70rem;"></i>
              <div class="text-truncate" style="max-width: 250px; font-size: 0.72rem; color: #fde047;" title="${escapeHtml(item.sent_summary)}">
                ${escapeHtml(item.sent_summary)}
              </div>
            </div>
          </td>
          <td>
            <div class="d-flex align-items-center justify-content-start gap-2 mb-1">
              <span class="badge bg-success-subtle text-success border border-success px-1.5 py-0.5" style="font-size: 0.68rem;" title=i18n.t('auto___d49345')>
                ${deltaRecvStr}
              </span>
              <span class="text-muted font-monospace" style="font-size: 0.68rem;" title=i18n.t('auto___dbb2d6')>
                Σ ${totalRecvStr}
              </span>
            </div>
            <div class="d-flex align-items-start gap-1">
              <i class="bi bi-arrow-down-left text-success mt-0.5" style="font-size: 0.70rem;"></i>
              <div class="text-truncate" style="max-width: 250px; font-size: 0.72rem; color: #86efac;" title="${escapeHtml(item.recv_summary)}">
                ${escapeHtml(item.recv_summary)}
              </div>
            </div>
          </td>
        </tr>
      `;
    }).join('');

    tbody.querySelectorAll('.sys-net-row').forEach(row => {
      row.onclick = () => {
        const idx = parseInt(row.getAttribute('data-idx'), 10);
        const item = filtered[idx];
        if (!item) return;

        const formatNetKb = (kb) => {
          if (!kb || kb <= 0) return '0 KB';
          if (kb >= 1024 * 1024) return (kb / (1024 * 1024)).toFixed(2) + ' GB';
          if (kb >= 1024) return (kb / 1024).toFixed(1) + ' MB';
          return kb.toFixed(1) + ' KB';
        };

        const formatNetRate = (rate) => {
          if (!rate || rate <= 0.05) return '';
          if (rate >= 1024) return (rate / 1024).toFixed(1) + ' MB/s';
          return rate.toFixed(1) + ' KB/s';
        };

        if (window.AITableModal) {
          window.AITableModal.show({
            icon: '🌐',
            title: `${item.name} (${item.service_type})`,
            subtitle: `PID: ${item.pid} | ${item.remote_address}`,
            tableType: 'network',
            badges: [
              { text: `PID ${item.pid}`, class: 'badge bg-info text-dark' },
              { text: item.protocol, class: 'badge bg-primary' },
              { text: item.status, class: 'badge bg-success' },
              { text: item.is_internet ? i18n.t('auto__wan__6918e6') : i18n.t('auto__lan__b1581a'), class: item.is_internet ? 'badge bg-warning text-dark' : 'badge bg-secondary' }
            ],
            metadata: [
              { label: i18n.t('auto___87d72c'), value: item.name },
              { label: 'Process ID (PID)', value: String(item.pid) },
              { label: i18n.t('auto___e36524'), value: item.user || 'SYSTEM' },
              { label: i18n.t('auto__remote__1ddfe5'), value: item.remote_address },
              { label: i18n.t('auto__local__9b2247'), value: item.local_address },
              { label: i18n.t('auto___6582e4'), value: `${item.protocol} • ${item.service_type}` },
              { label: i18n.t('auto___6a4666'), value: item.status },
              { label: i18n.t('auto___79710a'), value: `${formatNetKb(item.delta_recv_kb || 0)} ${item.recv_rate_kbs > 0.05 ? '(' + formatNetRate(item.recv_rate_kbs) + ')' : ''}` },
              { label: i18n.t('auto___d2f9e3'), value: formatNetKb(item.recv_kb || 0) },
              { label: i18n.t('auto___dc8000'), value: `${formatNetKb(item.delta_sent_kb || 0)} ${item.sent_rate_kbs > 0.05 ? '(' + formatNetRate(item.sent_rate_kbs) + ')' : ''}` },
              { label: i18n.t('auto___3f01d4'), value: formatNetKb(item.sent_kb || 0) },
              { label: i18n.t('auto___1fef33'), value: item.sent_summary, fullWidth: true },
              { label: i18n.t('auto___4262a1'), value: item.recv_summary, fullWidth: true }
            ],
            rawTitle: i18n.t('auto___561dba'),
            rawContent: JSON.stringify(item, null, 2),
            requestData: item
          });
        }
      };
    });
  }

  async function runAiDiagnostics() {
    const summaryEl = document.getElementById('sys-ai-summary-text');
    const badgeEl = document.getElementById('sys-ai-health-badge');
    const anomaliesEl = document.getElementById('sys-ai-anomalies-container');
    const engineTagEl = document.getElementById('sys-ai-model-tag');

    if (summaryEl) summaryEl.innerText = i18n.t('auto__ai__729be3');

    try {
      const res = await fetch('/api/v1/system/diagnose', { method: 'POST' });
      if (!res.ok) throw new Error('AI Diagnosis error');
      const report = await res.json();

      if (badgeEl) {
        badgeEl.innerText = `Health: ${report.health_score || 100}/100`;
        badgeEl.className = `badge ${report.health_score >= 80 ? 'bg-success' : report.health_score >= 60 ? 'bg-warning' : 'bg-danger'}`;
      }

      if (engineTagEl) {
        engineTagEl.innerText = report.ai_model_used || 'Heuristic Engine';
      }

      if (anomaliesEl) {
        if (Array.isArray(report.anomalies) && report.anomalies.length > 0) {
          anomaliesEl.innerHTML = report.anomalies.map(a => `<span class="anomaly-tag">⚠️ [${a.subsystem}] ${escapeHtml(a.title)}</span>`).join('');
        } else {
          anomaliesEl.innerHTML = '<span style="color: #4ade80; font-size: 0.75rem;"><i class="bi bi-check-circle me-1"></i> Аномалий в работе оборудования не обнаружено</span>i18n.t('auto__if_summaryel_const_recs_array_isarray_report_recommendations_report_recommendations_length_0_n_report_recommendations_join__537a08'), ')}`
          : '';
        summaryEl.innerText = `${report.summary || i18n.t('auto___bba1b2')}${recs}`;
      }
    } catch (e) {
      console.error('[SystemInspectorTab] AI Diagnose error:', e);
      if (summaryEl) summaryEl.innerText = i18n.t('auto__ai__6b4476') + e.message;
    }
  }

  let sysWsReconnectTimer = null;

  function connectSystemWebSocket() {
    if (sysWsReconnectTimer) {
      clearTimeout(sysWsReconnectTimer);
      sysWsReconnectTimer = null;
    }
    if (sysWs) {
      try {
        sysWs.onclose = null;
        sysWs.onerror = null;
        sysWs.close();
      } catch {}
      sysWs = null;
    }

    if (window.isTabActive && !window.isTabActive('tab-system-inspector')) {
      const statusBadge = document.getElementById('sys-conn-status');
      if (statusBadge) {
        statusBadge.className = 'badge rounded-pill bg-secondary text-light px-3 py-2';
        statusBadge.innerText = i18n.t('auto___28ad51');
      }
      return;
    }

    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${proto}//${window.location.host}/api/v1/system/stream`;

    try {
      sysWs = new WebSocket(wsUrl);
      const statusBadge = document.getElementById('sys-conn-status');

      sysWs.onopen = () => {
        console.info(i18n.t('auto__systeminspectortab_websocket__fbf1b5'));
        if (statusBadge) {
          statusBadge.className = 'badge rounded-pill bg-success-subtle text-success border border-success px-3 py-2';
          statusBadge.innerText = i18n.t('auto___ff0ae1');
        }
      };

      sysWs.onmessage = (evt) => {
        try {
          const snap = JSON.parse(evt.data);
          latestTelemetrySnapshot = snap;
          updateTelemetryDashboard(snap);
        } catch (e) {
          console.error(i18n.t('auto__systeminspectortab__4852f6'), e);
        }
      };

      const scheduleReconnect = (reason) => {
        if (sysWsReconnectTimer) return;
        if (window.isTabActive && !window.isTabActive('tab-system-inspectori18n.t('auto__return_console_warn_systeminspectortab_websocket_reason_3_if_statusbadge_statusbadge_classname__f6c30c')badge rounded-pill bg-warning-subtle text-warning border border-warning px-3 py-2';
          statusBadge.innerText = i18n.t('auto___24ff60');
        }
        sysWsReconnectTimer = setTimeout(() => {
          sysWsReconnectTimer = null;
          if (!window.isTabActive || window.isTabActive('tab-system-inspectori18n.t('auto__connectsystemwebsocket_3000_sysws_onclose_evt_schedulereconnect_evt_code_sysws_onerror_err_console_warn__98fb7d')[SystemInspectorTab] Ошибка соединения WebSocket:', err);
        scheduleReconnect(i18n.t('auto___0c3bf9'));
      };
    } catch (err) {
      console.error(i18n.t('auto__systeminspectortab_websocket__ea6383'), err);
      sysWsReconnectTimer = setTimeout(() => {
        sysWsReconnectTimer = null;
        if (!window.isTabActive || window.isTabActive('tab-system-inspector')) {
          connectSystemWebSocket();
        }
      }, 5000);
    }
  }

  function disconnectSystemWebSocket() {
    if (sysWsReconnectTimer) {
      clearTimeout(sysWsReconnectTimer);
      sysWsReconnectTimer = null;
    }
    if (sysWs) {
      try {
        sysWs.onclose = null;
        sysWs.onerror = null;
        sysWs.close();
      } catch {}
      sysWs = null;
    }
    const statusBadge = document.getElementById('sys-conn-status');
    if (statusBadge) {
      statusBadge.className = 'badge rounded-pill bg-secondary text-light px-3 py-2';
      statusBadge.innerText = i18n.t('auto___28ad51');
    }
  }

  function bindSensorTabEvents() {
    const btnPause = document.getElementById('btn-sys-pause-proc');
    if (btnPause) {
      btnPause.onclick = () => {
        isSysPaused = !isSysPaused;
        btnPause.innerText = isSysPaused ? i18n.t('auto___fa6a34') : i18n.t('auto___03498e');
        btnPause.className = isSysPaused ? 'btn btn-sm btn-warning rounded-pill px-3' : 'btn btn-sm btn-outline-secondary rounded-pill px-3';
      };
    }

    const btnRefreshSensors = document.getElementById('btn-sys-refresh-sensors');
    if (btnRefreshSensors) {
      btnRefreshSensors.onclick = () => fetchLhmSensors();
    }

    const btnRefreshLhm = document.getElementById('btn-sys-refresh-lhm');
    if (btnRefreshLhm) {
      btnRefreshLhm.onclick = () => fetchLhmSensors();
    }

    const btnLaunchLhm = document.getElementById('btn-sys-launch-lhm');
    if (btnLaunchLhm) {
      btnLaunchLhm.onclick = async () => {
        btnLaunchLhm.disabled = true;
        btnLaunchLhm.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Запуск...';
        try {
          const res = await fetch('/api/v1/lhm/launch', { method: 'POST' });
          if (res.ok) {
            setTimeout(fetchLhmSensors, 2500);
          }
        } catch (e) {
          console.error('[SystemInspectorTab] Failed to launch LHM:', e);
        } finally {
          btnLaunchLhm.disabled = false;
        }
      };
    }

    const searchSensors = document.getElementById('sys-lhm-search');
    if (searchSensors) {
      searchSensors.oninput = () => renderSensors();
    }

    // Category pills
    document.querySelectorAll('.sys-lhm-cat-btn').forEach(btn => {
      btn.onclick = () => {
        document.querySelectorAll('.sys-lhm-cat-btn').forEach(b => {
          b.classList.remove('active', 'btn-outline-primary');
          b.classList.add('btn-outline-secondary');
        });
        btn.classList.remove('btn-outline-secondary');
        btn.classList.add('active', 'btn-outline-primary');
        currentSensorCategory = btn.getAttribute('data-cat') || 'all';
        renderSensors();
      };
    });

    // Analyze Button (Sensors)
    const btnAnalyze = document.getElementById('btn-sys-sensor-analyze');
    if (btnAnalyze) {
      btnAnalyze.onclick = () => analyzeSensorsAndReport();
    }

    // Modal Re-analyze Button
    const btnReAnalyze = document.getElementById('btn-re-analyze-sensors');
    if (btnReAnalyze) {
      btnReAnalyze.onclick = async () => {
        btnReAnalyze.disabled = true;
        const icon = btnReAnalyze.querySelector('i');
        if (icon) icon.classList.add('spin-animation');
        await fetchLhmSensors();
        await analyzeSensorsAndReport();
        if (icon) icon.classList.remove('spin-animation');
        btnReAnalyze.disabled = false;
      };
    }

    // Modal Copy Report Button
    const btnCopyReport = document.getElementById('btn-copy-sensor-report');
    if (btnCopyReport) {
      btnCopyReport.onclick = async () => {
        if (!lastAnalysisReportText) return;
        try {
          await navigator.clipboard.writeText(lastAnalysisReportText);
          const origHtml = btnCopyReport.innerHTML;
          btnCopyReport.innerHTML = '<i class="bi bi-check2 text-success me-1"></i> Скопировано!';
          setTimeout(() => {
            btnCopyReport.innerHTML = origHtml;
          }, 2000);
        } catch (e) {
          console.warn('[SystemInspectorTab] Clipboard copy failed:', e);
        }
      };
    }
  }

  async function openProcStatsModal() {
    const modalEl = document.getElementById('sysProcStatsModal');
    if (modalEl && window.bootstrap && window.bootstrap.Modal) {
      const modal = window.bootstrap.Modal.getOrCreateInstance(modalEl);
      modal.show();
    }
    await fetchProcStats();
  }

  async function fetchProcStats(filterName = '') {
    const tbodyRollups = document.getElementById('tbody-proc-rollups');
    const tbodyOutliers = document.getElementById('tbody-proc-outliers');
    const tbodyDaily = document.getElementById('tbody-proc-daily');
    const badgeCount = document.getElementById('modal-proc-stats-count-badge');
    const badgeOutliers = document.getElementById('proc-outliers-count');

    try {
      const url = `/api/v1/system/processes/stats?limit=60${filterName ? '&name=' + encodeURIComponent(filterName) : ''}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('HTTP i18n.t('auto__res_status_const_data_await_res_json_cachedprocstats_data_const_rollups_data_rollups_2min_const_outliers_data_outliers_const_daily_data_daily_stats_if_badgecount_badgecount_textcontent_rollups_length_daily_length_if_badgeoutliers_badgeoutliers_textcontent_string_outliers_length_1_2_if_tbodyrollups_if_rollups_length_0_tbodyrollups_innerhtml__962df4')<tr><td colspan="10" class="text-center py-3 text-muted">Обобщённых записей (&gt; 2 мин) пока нет. Данные собираются каждые 5 сек.</td></tr>';
        } else {
          tbodyRollups.innerHTML = rollups.map(r => {
            const timeRange = `${(r.period_start || '').slice(11, 19)} - ${(r.period_end || '').slice(11, 19)}`;
            const cpuClass = r.avg_cpu_percent > 30 ? 'text-danger fw-bold' : (r.avg_cpu_percent > 10 ? 'text-warning' : 'text-info');
            return `
              <tr>
                <td style="color: #94a3b8;">${timeRange}</td>
                <td style="font-weight: 600; color: #38bdf8;">${escapeHtml(r.name || '')}</td>
                <td>${r.pid || '-'}</td>
                <td style="color: #94a3b8;">${escapeHtml(r.username || '')}</td>
                <td class="text-end text-white">${r.sample_count}</td>
                <td class="text-end ${cpuClass}">${Number(r.avg_cpu_percent).toFixed(1)}%</td>
                <td class="text-end text-danger">${Number(r.max_cpu_percent).toFixed(1)}%</td>
                <td class="text-end text-success">${Number(r.avg_memory_mb).toFixed(1)} MB</td>
                <td class="text-end text-success">${Number(r.max_memory_mb).toFixed(1)} MB</td>
                <td class="text-end">${r.outliers_count > 0 ? `<span class="badge bg-warning text-dark">${r.outliers_count}</span>` : '0'}</td>
              </tr>
            `;
          }).join('i18n.t('auto__2_if_tbodyoutliers_if_outliers_length_0_tbodyoutliers_innerhtml__083b44')<tr><td colspan="8" class="text-center py-3 text-muted">Аномальных выбросов нагрузки не зафиксировано.</td></tr>';
        } else {
          tbodyOutliers.innerHTML = outliers.map(o => {
            return `
              <tr>
                <td style="color: #f59e0b;">${(o.timestamp || '').replace('T', ' ').slice(0, 19)}</td>
                <td style="font-weight: 600; color: #38bdf8;">${escapeHtml(o.name || '')}</td>
                <td>${o.pid}</td>
                <td class="text-end text-danger fw-bold">${Number(o.cpu_percent).toFixed(1)}%</td>
                <td class="text-end text-success">${Number(o.memory_mb).toFixed(1)} MB</td>
                <td>${o.num_threads || 1}</td>
                <td style="color: #94a3b8;">${escapeHtml(o.username || '')}</td>
                <td class="text-warning">${escapeHtml(o.details || i18n.t('auto__cpu_51f3d5'))}</td>
              </tr>
            `;
          }).join('i18n.t('auto__3_if_tbodydaily_if_daily_length_0_tbodydaily_innerhtml__65630e')<tr><td colspan="9" class="text-center py-3 text-muted">Данных старше 1 дня пока нет. Обобщение формируется автоматически.</td></tr>';
        } else {
          tbodyDaily.innerHTML = daily.map(d => {
            return `
              <tr>
                <td class="text-info">${d.date}</td>
                <td style="font-weight: 600; color: #38bdf8;">${escapeHtml(d.name || '')}</td>
                <td class="text-end text-white">${d.sample_count}</td>
                <td class="text-end text-warning">${Number(d.avg_cpu_percent).toFixed(1)}%</td>
                <td class="text-end text-danger">${Number(d.max_cpu_percent).toFixed(1)}%</td>
                <td class="text-end text-success">${Number(d.avg_memory_mb).toFixed(1)} MB</td>
                <td class="text-end text-success">${Number(d.max_memory_mb).toFixed(1)} MB</td>
                <td class="text-end">${d.outliers_count > 0 ? `<span class="badge bg-warning text-dark">${d.outliers_count}</span>` : '0'}</td>
                <td style="color: #94a3b8;">${(d.last_seen || '').slice(11, 19)}</td>
              </tr>
            `;
          }).join('');
        }
      }

    } catch (err) {
      console.warn(i18n.t('auto__systeminspectortab__876d35'), err);
      if (tbodyRollups) tbodyRollups.innerHTML = `<tr><td colspan="10" class="text-center py-3 text-danger">Ошибка: ${escapeHtml(err.message)}</td></tr>`;
    }
  }

  async function triggerProcRollupNow() {
    const btn = document.getElementById('btn-trigger-proc-rollup');
    const statusText = document.getElementById('modal-proc-rollup-status');
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Обобщение...';
    }
    try {
      const res = await fetch('/api/v1/system/processes/rollup?cutoff_seconds=120&outlier_cpu_threshold=30.0', { method: 'POSTi18n.t('auto__if_res_ok_const_data_await_res_json_if_statustext_statustext_textcontent_2_data_rollup_2min_rollups_created_0_data_rollup_2min_outliers_saved_0_await_fetchprocstats_catch_e_console_error__568741')[SystemInspectorTab] Ошибка выполнения роллапа:', e);
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-lightning-charge me-1"></i>Обобщить сейчас';
      }
    }
  }

  function bindTabEvents() {
    bindSensorTabEvents();

    const btnProcStats = document.getElementById('btn-sys-proc-stats');
    if (btnProcStats) {
      btnProcStats.onclick = () => openProcStatsModal();
    }

    const btnRefreshStats = document.getElementById('btn-refresh-proc-stats');
    if (btnRefreshStats) {
      btnRefreshStats.onclick = () => {
        const q = (document.getElementById('modal-proc-stats-filter')?.value || '').trim();
        fetchProcStats(q);
      };
    }

    const btnRollupTrigger = document.getElementById('btn-trigger-proc-rollup');
    if (btnRollupTrigger) {
      btnRollupTrigger.onclick = () => triggerProcRollupNow();
    }

    const inputStatsFilter = document.getElementById('modal-proc-stats-filter');
    if (inputStatsFilter) {
      inputStatsFilter.oninput = (e) => fetchProcStats(e.target.value.trim());
    }

    const searchProc = document.getElementById('sys-proc-search');
    if (searchProc) {
      searchProc.oninput = () => renderProcessTable();
    }

    const btnAudit = document.getElementById('btn-sys-run-audit');
    if (btnAudit) {
      btnAudit.onclick = () => runAiDiagnostics();
    }

    const btnConfig = document.getElementById('btn-sys-config');
    if (btnConfig) {
      btnConfig.onclick = () => {
        if (window.appConfigEditor) {
          window.appConfigEditor.open('system_inspector', i18n.t('auto___33a2f8'));
        } else {
          console.info('[SystemInspectorTab] Config editor not available');
        }
      };
    }

    // Interval editor modal buttons
    const btnIntervalsTop = document.getElementById('btn-sys-intervals');
    if (btnIntervalsTop) {
      btnIntervalsTop.onclick = () => openSysIntervalsModal();
    }

    const btnIntervalsLhm = document.getElementById('btn-sys-intervals-lhm');
    if (btnIntervalsLhm) {
      btnIntervalsLhm.onclick = () => openSysIntervalsModal();
    }

    const btnRefreshIntervals = document.getElementById('btn-modal-intervals-refresh');
    if (btnRefreshIntervals) {
      btnRefreshIntervals.onclick = () => loadSysIntervalsConfig(true);
    }

    const btnSaveIntervals = document.getElementById('btn-modal-intervals-save');
    if (btnSaveIntervals) {
      btnSaveIntervals.onclick = () => saveSysIntervalsConfig();
    }

    const selUiRefresh = document.getElementById('modal-ui-refresh-select');
    if (selUiRefresh) {
      selUiRefresh.onchange = (e) => {
        const sec = parseInt(e.target.value, 10) || 5;
        setupSysSensorInterval(sec);
        const badge = document.getElementById('modal-ui-refresh-badgei18n.t('auto__if_badge_badge_textcontent_sec_controls_const_changewatchdirbtn_document_getelementbyid__a139bc')btn-sys-change-watch-dir');
    if (changeWatchDirBtn) {
      changeWatchDirBtn.onclick = () => openWatchFoldersModal('folders');
    }
    const exclusionsBtn = document.getElementById('btn-sys-watch-exclusions');
    if (exclusionsBtn) {
      exclusionsBtn.onclick = () => openWatchFoldersModal('exclusions');
    }
    const watchDirBadge = document.getElementById('sys-watch-dir-badge');
    if (watchDirBadge) {
      watchDirBadge.onclick = () => openWatchFoldersModal('folders');
    }
    const liveHelpBtn = document.getElementById('btn-sys-live-help');
    if (liveHelpBtn) {
      liveHelpBtn.onclick = showLiveWatcherHelpModal;
    }

    // Network Activity Table controls
    const searchNet = document.getElementById('sys-net-search');
    if (searchNet) {
      searchNet.oninput = () => renderNetworkActivityTable();
    }

    const btnPauseNet = document.getElementById('btn-sys-pause-net');
    if (btnPauseNet) {
      btnPauseNet.onclick = () => {
        isNetPaused = !isNetPaused;
        btnPauseNet.innerText = isNetPaused ? i18n.t('auto___fa6a34') : i18n.t('auto___03498e');
        btnPauseNet.className = isNetPaused ? 'btn btn-xs btn-warning rounded-pill px-2.5 py-0.5' : 'btn btn-xs btn-outline-secondary rounded-pill px-2.5 py-0.5';
        if (!isNetPaused) renderNetworkActivityTable();
      };
    }

    const btnRefreshNet = document.getElementById('btn-sys-refresh-net');
    if (btnRefreshNet) {
      btnRefreshNet.onclick = () => fetchNetworkActivity();
    }

    document.querySelectorAll('.sys-net-filter-btn').forEach(btn => {
      btn.onclick = () => {
        document.querySelectorAll('.sys-net-filter-btn').forEach(b => {
          b.classList.remove('active', 'btn-outline-primary');
          b.classList.add('btn-outline-secondary');
        });
        btn.classList.remove('btn-outline-secondary');
        btn.classList.add('active', 'btn-outline-primary');
        currentNetFilter = btn.getAttribute('data-filter') || 'interneti18n.t('auto__rendernetworkactivitytable_initnettableresizer_initwatchertableresizer_function_initnettableresizer_const_resizer_document_getelementbyid__cdb184')sys-net-table-resizer');
    const tableContainer = document.getElementById('sys-net-table-container');
    if (!resizer || !tableContainer) return;

    if (resizer._resizerInitialized) return;
    resizer._resizerInitialized = true;

    try {
      const savedHeight = localStorage.getItem('sys_inspector_net_height');
      if (savedHeight) {
        const parsed = parseInt(savedHeight, 10);
        if (!isNaN(parsed) && parsed >= 140 && parsed <= 1200) {
          tableContainer.style.height = `${parsed}px`;
        }
      }
    } catch {}

    let startY = 0;
    let startHeight = 0;
    let isDragging = false;

    function onMouseMove(e) {
      if (!isDragging) return;
      const clientY = e.clientY ?? (e.touches && e.touches[0] ? e.touches[0].clientY : null);
      if (clientY === null) return;

      const deltaY = clientY - startY;
      let newHeight = startHeight + deltaY;
      if (newHeight < 140) newHeight = 140;
      if (newHeight > 1200) newHeight = 1200;

      tableContainer.style.height = `${newHeight}px`;
    }

    function onMouseUp() {
      if (!isDragging) return;
      isDragging = false;
      resizer.classList.remove('resizing');
      document.body.style.cursor = '';
      document.body.style.userSelect = '';

      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      window.removeEventListener('touchmove', onMouseMove);
      window.removeEventListener('touchend', onMouseUp);

      const currentH = parseInt(tableContainer.style.height, 10);
      if (!isNaN(currentH)) {
        try {
          localStorage.setItem('sys_inspector_net_height', String(currentH));
        } catch {}
      }
    }

    function onMouseDown(e) {
      isDragging = true;
      startY = e.clientY ?? (e.touches && e.touches[0] ? e.touches[0].clientY : 0);
      startHeight = tableContainer.getBoundingClientRect().height;
      resizer.classList.add('resizing');
      document.body.style.cursor = 'ns-resize';
      document.body.style.userSelect = 'none';

      window.addEventListener('mousemove', onMouseMove, { passive: false });
      window.addEventListener('mouseup', onMouseUp);
      window.addEventListener('touchmove', onMouseMove, { passive: false });
      window.addEventListener('touchend', onMouseUp);
      e.preventDefault();
    }

    resizer.addEventListener('mousedown', onMouseDown);
    resizer.addEventListener('touchstart', onMouseDown, { passive: false });

    resizer.addEventListener('dblclick', () => {
      tableContainer.style.height = '300px';
      try {
        localStorage.removeItem('sys_inspector_net_height');
      } catch {}
    });
  }

  function initWatcherTableResizer() {
    const resizer = document.getElementById('sys-watcher-table-resizer');
    const tableContainer = document.getElementById('sys-watcher-table-containeri18n.t('auto__if_resizer_tablecontainer_return_if_resizer_resizerinitialized_return_resizer_resizerinitialized_true_try_const_savedheight_localstorage_getitem__27a83b')sys_inspector_watcher_height');
      if (savedHeight) {
        const parsed = parseInt(savedHeight, 10);
        if (!isNaN(parsed) && parsed >= 120 && parsed <= 1200) {
          tableContainer.style.height = `${parsed}px`;
        }
      }
    } catch {}

    let startY = 0;
    let startHeight = 0;
    let isDragging = false;

    function onMouseMove(e) {
      if (!isDragging) return;
      const clientY = e.clientY ?? (e.touches && e.touches[0] ? e.touches[0].clientY : null);
      if (clientY === null) return;

      const deltaY = clientY - startY;
      let newHeight = startHeight + deltaY;
      if (newHeight < 120) newHeight = 120;
      if (newHeight > 1200) newHeight = 1200;

      tableContainer.style.height = `${newHeight}px`;
    }

    function onMouseUp() {
      if (!isDragging) return;
      isDragging = false;
      resizer.classList.remove('resizing');
      document.body.style.cursor = '';
      document.body.style.userSelect = '';

      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      window.removeEventListener('touchmove', onMouseMove);
      window.removeEventListener('touchend', onMouseUp);

      const currentH = parseInt(tableContainer.style.height, 10);
      if (!isNaN(currentH)) {
        try {
          localStorage.setItem('sys_inspector_watcher_height', String(currentH));
        } catch {}
      }
    }

    function onMouseDown(e) {
      isDragging = true;
      startY = e.clientY ?? (e.touches && e.touches[0] ? e.touches[0].clientY : 0);
      startHeight = tableContainer.getBoundingClientRect().height;
      resizer.classList.add('resizing');
      document.body.style.cursor = 'ns-resize';
      document.body.style.userSelect = 'none';

      window.addEventListener('mousemove', onMouseMove, { passive: false });
      window.addEventListener('mouseup', onMouseUp);
      window.addEventListener('touchmove', onMouseMove, { passive: false });
      window.addEventListener('touchend', onMouseUp);
      e.preventDefault();
    }

    resizer.addEventListener('mousedown', onMouseDown);
    resizer.addEventListener('touchstarti18n.t('auto__onmousedown_passive_false_resizer_addeventlistener__c2649d')dblclick', () => {
      tableContainer.style.height = '280px';
      try {
        localStorage.removeItem('sys_inspector_watcher_height');
      } catch {}
    });
  }

  // =============================================================================
  // Telemetry & Polling Intervals Editor Controller (config.json)
  // =============================================================================

  const INTERVAL_PRESETS = [
    { value: '1 second', label: i18n.t('auto_1__6a38c5') },
    { value: '2 seconds', label: i18n.t('auto_2__e3c7e5') },
    { value: '3 seconds', label: i18n.t('auto_3__542798') },
    { value: '5 seconds', label: i18n.t('auto_5__a0e595') },
    { value: '10 seconds', label: i18n.t('auto_10__bc63e4') },
    { value: '30 seconds', label: i18n.t('auto_30__252c1a') },
    { value: '1 minute', label: i18n.t('auto_1__f5125b') },
    { value: '5 minutes', label: i18n.t('auto_5__26b591') },
    { value: '10 minutes', label: i18n.t('auto_10__a140da') },
    { value: '30 minutes', label: i18n.t('auto_30__214427') },
    { value: '1 hour', label: i18n.t('auto_1__e5f168') },
    { value: '6 hours', label: i18n.t('auto_6__915bfe') },
    { value: '24 hours', label: i18n.t('auto_24__e14e41') },
  ];

  const CORE_RESOURCE_LOGGERS = [
    'librehardwaremonitor',
    'system_inspector',
    'hardware_monitor'
  ];

  const LOGGER_META = {
    librehardwaremonitor: {
      icon: '🌡️',
      title: 'LibreHardwareMonitor',
      desc: i18n.t('auto__cpu_gpu__e3c871'),
    },
    system_inspector: {
      icon: '📊',
      title: 'System Inspector',
      desc: i18n.t('auto__cpu_ram__624f00'),
    },
    hardware_monitor: {
      icon: '💻',
      title: 'Hardware Monitor',
      desc: i18n.t('auto__wmi_gpu_smi_nvidia_amd_intel__df24c1'),
    },
    windows_sysadmin: {
      icon: '🛠️',
      title: 'Windows SysAdmin',
      desc: i18n.t('auto__windows__e8148c'),
    },
    windows_defender: {
      icon: '🛡️',
      title: 'Windows Defender',
      desc: i18n.t('auto___2b7b9c'),
    },
    windows_startup_auditor: {
      icon: '🚀',
      title: 'StartUp Auditor',
      desc: i18n.t('auto__run_runonce__f31145'),
    },
    windows_backup_manager: {
      icon: '📦',
      title: 'Backup Manager',
      desc: i18n.t('auto__sqlite__70e86e'),
    },
    website_monitor: {
      icon: '🌐',
      title: 'Website Monitor',
      desc: i18n.t('auto__http_https_af2474'),
    },
    gcloud_monitor: {
      icon: '☁️',
      title: 'GCloud Monitor',
      desc: i18n.t('auto__google_cloud_45eb1d'),
    },
    cloudflared_monitor: {
      icon: '🚇',
      title: 'Cloudflare Tunnel',
      desc: i18n.t('auto__cloudflared__23e001'),
    },
    user_assistant: {
      icon: '🤖',
      title: 'User Assistant',
      desc: i18n.t('auto___8a88f9'),
    },
    trading_terminal: {
      icon: '📈',
      title: 'Trading Terminal',
      desc: i18n.t('auto___aaec96'),
    },
    registry_viewer: {
      icon: '📑',
      title: 'Registry Viewer',
      desc: i18n.t('auto__windows_367a25'),
    },
    software_audit: {
      icon: '🔍',
      title: 'Software Audit',
      desc: i18n.t('auto__userassist_prefetch__95f74f'),
    },
    helpdesk: {
      icon: '🎫',
      title: 'Helpdesk',
      desc: i18n.t('auto___2f5688'),
    },
  };

  let _sysIntervalsConfigData = null;

  function showAlertInModal(msg, type = 'success') {
    const alertEl = document.getElementById('modal-intervals-alert');
    if (!alertEl) return;
    alertEl.className = `alert alert-${type} py-2 px-3 small mb-3`;
    alertEl.innerHTML = msg;
    alertEl.classList.remove('d-none');
    if (type === 'success') {
      setTimeout(() => {
        alertEl.classList.add('d-none');
      }, 4000);
    }
  }

  async function loadSysIntervalsConfig(notify = false) {
    const btnRefresh = document.getElementById('btn-modal-intervals-refresh');
    const icon = btnRefresh ? btnRefresh.querySelector('i') : null;
    if (icon) icon.classList.add('spin-animation');

    try {
      let res = await fetch('/api/autolog/config');
      if (!res.ok) {
        res = await fetch('/sysautologging/config');
      }
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      _sysIntervalsConfigData = await res.json();
      renderSysIntervalsForm(_sysIntervalsConfigData);

      if (notify) {
        showAlertInModal('<i class="bi bi-check2 me-1"></i> Конфигурация успешно загружена из файла', 'success');
      }
    } catch (e) {
      console.warn('[SystemInspectorTab] Failed to load intervals config:', e);
      showAlertInModal(`<i class="bi bi-exclamation-triangle me-1"></i> Ошибка загрузки конфигурации: ${escapeHtml(e.message)}`, 'danger');
    } finally {
      if (icon) icon.classList.remove('spin-animation');
    }
  }

  function buildIntervalSelectHtml(loggerName, currentInterval) {
    const val = currentInterval || '1 minute';
    const isCustom = !INTERVAL_PRESETS.some(p => p.value === val);

    let html = `<select class="form-select form-select-sm bg-dark text-white border-secondary sys-int-select" data-logger="${loggerName}" style="min-width: 120px;">`;
    INTERVAL_PRESETS.forEach(p => {
      const sel = p.value === val ? 'selected' : '';
      html += `<option value="${p.value}" ${sel}>${p.label} (${p.value})</option>`;
    });
    if (isCustom) {
      html += `<option value="${escapeHtml(val)}" selected>${escapeHtml(val)} (пользовательский)</option>`;
    }
    html += `</select>`;
    return html;
  }

  function renderSysIntervalsForm(data) {
    if (!data) return;

    // 1. Config file badge
    const cfgBadge = document.getElementById('modal-intervals-cfg-file');
    if (cfgBadge && data.config_file) {
      cfgBadge.textContent = data.config_file;
    }

    // 2. Engine status & global switch
    const engineStatusBadge = document.getElementById('modal-intervals-engine-status');
    if (engineStatusBadge) {
      if (data.is_running) {
        engineStatusBadge.textContent = 'AutoLog Active';
        engineStatusBadge.className = 'badge bg-success';
      } else {
        engineStatusBadge.textContent = 'AutoLog Paused';
        engineStatusBadge.className = 'badge bg-secondary';
      }
    }

    const globalEnable = document.getElementById('modal-intervals-global-enable');
    if (globalEnable) {
      globalEnable.checked = data.enable_autolog !== false;
    }

    // 3. Default fallback interval select
    const defSelect = document.getElementById('modal-intervals-default-select');
    if (defSelect && data.default_interval) {
      defSelect.value = data.default_interval;
    }

    // 4. Populate Core resource loggers & Other loggers
    const coreContainer = document.getElementById('modal-core-loggers-container');
    const otherContainer = document.getElementById('modal-other-loggers-container');
    const otherCountEl = document.getElementById('modal-other-loggers-count');

    if (!coreContainer || !otherContainer) return;

    const loggers = data.loggers || {};
    let coreHtml = '';
    let otherHtml = '';
    let otherCount = 0;

    // Process core loggers
    CORE_RESOURCE_LOGGERS.forEach(name => {
      const cfg = loggers[name] || { interval: '5 seconds', enabled: true };
      const meta = LOGGER_META[name] || { icon: '⚙️', title: name, desc: i18n.t('auto___b91dfc') };
      const isEnabled = cfg.enabled !== false;
      const intervalVal = cfg.interval || '5 seconds';

      coreHtml += `
        <div class="p-2 rounded d-flex align-items-center justify-content-between flex-wrap gap-2" style="background: var(--bg-color); border: 1px solid var(--border-color);">
          <div class="d-flex align-items-center gap-2" style="max-width: 58%;">
            <span class="fs-5">${meta.icon}</span>
            <div>
              <div class="fw-bold small" style="color: var(--text-color);">${meta.title}</div>
              <div class="small text-muted" style="font-size: 0.72rem; line-height: 1.2;">${meta.desc}</div>
            </div>
          </div>
          <div class="d-flex align-items-center gap-2 ms-auto">
            <div class="form-check form-switch m-0" title=i18n.t('auto___6f8316')>
              <input class="form-check-input sys-int-enable" type="checkbox" data-logger="${name}" ${isEnabled ? 'checked' : ''}>
            </div>
            ${buildIntervalSelectHtml(name, intervalVal)}
            <button class="btn btn-xs btn-outline-secondary rounded px-1.5 py-0.5 sys-int-custom-btn" data-logger="${name}" title=i18n.t('auto___87400a')>
              <i class="bi bi-pencil"></i>
            </button>
          </div>
        </div>
      `;
    });

    // Process remaining loggers
    const allLoggerNames = Object.keys(loggers).length > 0
      ? Object.keys(loggers)
      : Object.keys(LOGGER_META);

    allLoggerNames.forEach(name => {
      if (CORE_RESOURCE_LOGGERS.includes(name)) return;
      otherCount++;
      const cfg = loggers[name] || { interval: data.default_interval || '1 minute', enabled: true };
      const meta = LOGGER_META[name] || { icon: '🔹', title: name, desc: i18n.t('auto___e3b145') };
      const isEnabled = cfg.enabled !== false;
      const intervalVal = cfg.interval || '1 minute';

      otherHtml += `
        <div class="p-2 rounded d-flex align-items-center justify-content-between flex-wrap gap-2" style="background: var(--bg-color); border: 1px solid var(--border-color);">
          <div class="d-flex align-items-center gap-2" style="max-width: 58%;">
            <span class="fs-6">${meta.icon}</span>
            <div>
              <div class="fw-bold small" style="color: var(--text-color); font-size: 0.78rem;">${meta.title}</div>
              <div class="small text-muted" style="font-size: 0.7rem; line-height: 1.2;">${meta.desc}</div>
            </div>
          </div>
          <div class="d-flex align-items-center gap-2 ms-auto">
            <div class="form-check form-switch m-0" title=i18n.t('auto___a132ad')>
              <input class="form-check-input sys-int-enable" type="checkbox" data-logger="${name}" ${isEnabled ? 'checked' : ''}>
            </div>
            ${buildIntervalSelectHtml(name, intervalVal)}
            <button class="btn btn-xs btn-outline-secondary rounded px-1.5 py-0.5 sys-int-custom-btn" data-logger="${name}" title=i18n.t('auto___87400a')>
              <i class="bi bi-pencil"></i>
            </button>
          </div>
        </div>
      `;
    });

    coreContainer.innerHTML = coreHtml;
    otherContainer.innerHTML = otherHtml;
    if (otherCountEl) otherCountEl.textContent = String(otherCount);

    // Bind custom interval prompt buttons
    document.querySelectorAll('.sys-int-custom-btn').forEach(btn => {
      btn.onclick = () => {
        const lName = btn.getAttribute('data-logger');
        const sel = document.querySelector(`.sys-int-select[data-logger="${lName}"]`);
        const currentVal = sel ? sel.value : '1 minute';
        const custom = prompt(`Введите интервал опроса для ${lName} (например: "2 seconds", "15 seconds", "10 minutes", "1 hour"):`, currentVal);
        if (custom && custom.trim()) {
          const trimmed = custom.trim();
          let opt = sel.querySelector(`option[value="${trimmed}"]`);
          if (!opt) {
            opt = document.createElement('optioni18n.t('auto__opt_value_trimmed_opt_textcontent_trimmed_sel_appendchild_opt_sel_value_trimmed_async_function_savesysintervalsconfig_const_btnsave_document_getelementbyid__63dfbe')btn-modal-intervals-save');
    if (btnSave) {
      btnSave.disabled = true;
      btnSave.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status"></span> Сохранение...';
    }

    try {
      const globalEnable = document.getElementById('modal-intervals-global-enable');
      const defSelect = document.getElementById('modal-intervals-default-select');

      const payload = {
        enable_autolog: globalEnable ? globalEnable.checked : true,
        default_interval: defSelect ? defSelect.value : '1 minute',
        loggers: {}
      };

      // Collect values from all interval selects & switches
      document.querySelectorAll('.sys-int-select').forEach(sel => {
        const lName = sel.getAttribute('data-logger');
        if (!lName) return;
        const sw = document.querySelector(`.sys-int-enable[data-logger="${lName}"]`);
        payload.loggers[lName] = {
          interval: sel.value,
          enabled: sw ? sw.checked : true
        };
      });

      let saveRes = await fetch('/api/autolog/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!saveRes.ok) {
        saveRes = await fetch('/sysautologging/config', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
      }

      if (!saveRes.ok) {
        const errJson = await saveRes.json().catch(() => ({}));
        throw new Error(errJson.detail || `HTTP ${saveRes.status}`);
      }

      const result = await saveRes.json();
      showAlertInModal(
        `<i class="bi bi-check-circle-fill text-success me-1"></i> ${result.message || i18n.t('auto__config_json__83018a')}`,
        'success'
      );

      // Refresh engine badge
      const engineStatusBadge = document.getElementById('modal-intervals-engine-status');
      if (engineStatusBadge) {
        if (result.is_running) {
          engineStatusBadge.textContent = 'AutoLog Active';
          engineStatusBadge.className = 'badge bg-success';
        } else {
          engineStatusBadge.textContent = 'AutoLog Paused';
          engineStatusBadge.className = 'badge bg-secondary';
        }
      }
    } catch (e) {
      console.error('[SystemInspectorTab] Save intervals config error:', e);
      showAlertInModal(`<i class="bi bi-exclamation-triangle-fill text-danger me-1"></i> Не удалось сохранить интервалы: ${escapeHtml(e.message)}`, 'danger');
    } finally {
      if (btnSave) {
        btnSave.disabled = false;
        btnSave.innerHTML = '<i class="bi bi-check2-circle me-1"></i> Сохранить в config.json';
      }
    }
  }

  let currentWatchDirs = [];
  let currentWatchDir = '';
  let stagedWatchDirs = [];
  let currentBrowserPath = 'C:\\';
  let cachedDrives = [];

  async function fetchLiveFileEvents() {
    try {
      const [resEvents, resTelem] = await Promise.all([
        fetch('/api/sysadmin/file-audit/live-events?limit=30'),
        fetch('/api/sysadmin/file-audit/telemetry').catch(() => null)
      ]);

      if (resTelem && resTelem.ok) {
        const telem = await resTelem.json();
        const elRate = document.getElementById('sys-watcher-rate');
        const elCr = document.getElementById('sys-watcher-cr');
        const elMod = document.getElementById('sys-watcher-mod');
        const elDel = document.getElementById('sys-watcher-del');
        const elDrive = document.getElementById('sys-watcher-drive');
        const elDriveModel = document.getElementById('sys-watcher-drive-model');
        const elDriveTemp = document.getElementById('sys-watcher-temp');
        const elDiskR = document.getElementById('sys-watcher-r-kbs');
        const elDiskW = document.getElementById('sys-watcher-w-kbs');
        const elSecMatches = document.getElementById('sys-watcher-sec-matches');
        const elStatus = document.getElementById('sys-watcher-sensor-status');

        if (elRate) elRate.textContent = (telem.events_rate_per_sec || 0).toFixed(1);
        if (elCr) elCr.textContent = (telem.created_rate_per_sec || 0).toFixed(1);
        if (elMod) elMod.textContent = (telem.modified_rate_per_sec || 0).toFixed(1);
        if (elDel) elDel.textContent = (telem.deleted_rate_per_sec || 0).toFixed(1);
        
        if (elDrive) {
          const drivesStr = (telem.drive_letters && telem.drive_letters.length)
            ? telem.drive_letters.join(', ')
            : (telem.drive_letter || 'C:');
          elDrive.textContent = drivesStr;
        }
        if (elDriveModel) elDriveModel.textContent = telem.drive_model || 'Storage';
        if (elDriveTemp) elDriveTemp.textContent = telem.drive_temperature_c !== null && telem.drive_temperature_c !== undefined ? `${telem.drive_temperature_c} °C` : '-- °C';
        if (elDiskR) elDiskR.textContent = Math.round(telem.disk_read_kbs || 0);
        if (elDiskW) elDiskW.textContent = Math.round(telem.disk_write_kbs || 0);
        if (elSecMatches) elSecMatches.textContent = telem.security_audit_matched_count || 0;

        if (elStatus) {
          if (telem.burst_deletions_alert) {
            elStatus.className = 'badge bg-danger-subtle text-danger border border-danger px-2 py-1';
            elStatus.textContent = i18n.t('auto___c5297b');
          } else if (telem.high_activity_alert) {
            elStatus.className = 'badge bg-warning-subtle text-warning border border-warning px-2 py-1';
            elStatus.textContent = i18n.t('auto__i_o_964b64');
          } else {
            elStatus.className = 'badge bg-success-subtle text-success border border-success px-2 py-1';
            elStatus.textContent = i18n.t('auto___f81d71');
          }
        }
      }

      if (!resEvents || !resEvents.ok) return;
      const data = await resEvents.json();
      const events = data.events || [];

      if (data.filtered_count !== undefined) {
        const filteredEl = document.getElementById('sys-watcher-filtered-count');
        if (filteredEl) filteredEl.textContent = data.filtered_count;
      }
      
      currentWatchDirs = data.watch_dirs || (data.watch_dir ? [data.watch_dir] : []);
      currentWatchDir = currentWatchDirs[0] || data.watch_dir || '';
      
      const dirPathEl = document.getElementById('sys-watch-dir-path');
      const badge = document.getElementById('sys-watch-dir-badge');
      if (dirPathEl) {
        if (currentWatchDirs.length === 0) {
          dirPathEl.innerText = i18n.t('auto___235db6');
        } else if (currentWatchDirs.length === 1) {
          const singleName = currentWatchDirs[0].split('\\').pop() || currentWatchDirs[0];
          dirPathEl.innerText = singleName;
        } else {
          const firstNames = currentWatchDirs.slice(0, 2).map(p => p.split('\\').pop() || p).join(', i18n.t('auto__dirpathel_innertext_currentwatchdirs_length_firstnames_currentwatchdirs_length_2__aee1f8')...' : 'i18n.t('auto__if_badge_badge_title_currentwatchdirs_length_n_currentwatchdirs_join__2ec896')\ni18n.t('auto__n_n_const_tbody_document_getelementbyid__3071c6')sys-watcher-tbody');
      if (tbody) {
        if (events.length === 0) {
          const labelDirs = currentWatchDirs.length > 0 ? currentWatchDirs.join(', ') : i18n.t('auto___890c8b');
          tbody.innerHTML = `<tr><td colspan="4" class="text-center text-muted p-2">Ожидание изменений в папках <code>${labelDirs}</code>...</td></tr>`;
          return;
        }
        tbody.innerHTML = events.map((e, idx) => {
          const rootDirHint = e.watch_dir ? (e.watch_dir.split('\\').pop() || e.watch_dir) : '';
          const procDisplay = e.process_name
            ? `<span class="badge bg-dark border border-secondary text-info font-monospace text-truncate d-inline-block" style="max-width: 165px; font-size: 0.72rem;" title="Программа: ${escapeHtml(e.process_name)}${e.process_id ? ` (PID: ${e.process_id})` : ''}"><i class="bi bi-cpu me-1"></i>${escapeHtml(e.process_name)}${e.process_id ? ` [${e.process_id}]` : ''}</span>`
            : `<span class="text-muted" style="font-size: 0.72rem;">—</span>`;
          return `
            <tr class="sys-live-row" data-idx="${idx}" style="cursor: pointer;" title=i18n.t('auto__ai__638c45')>
              <td class="font-monospace text-muted small">${e.timestamp?.slice(11, 19) || ''}</td>
              <td>
                <span class="badge ${e.is_deletion ? 'bg-danger' : (e.action === 'Created' ? 'bg-success' : 'bg-secondary')}">${e.action}</span>
                ${rootDirHint && currentWatchDirs.length > 1 ? `<span class="badge bg-dark border border-secondary text-muted ms-1" style="font-size: 0.65rem;" title=i18n.t('auto__escapehtml_e_watch_dir__aed9c9')>${rootDirHint}</span>` : ''}
              </td>
              <td>${procDisplay}</td>
              <td class="font-monospace small text-light" style="word-break: break-all;" title="${escapeHtml(e.path)}">${escapeHtml(e.path)}</td>
            </tr>
          `;
        }).join('');

        tbody.querySelectorAll('.sys-live-row').forEach(row => {
          row.onclick = () => {
            const idx = parseInt(row.getAttribute('data-idx'), 10);
            const e = events[idx];
            if (!e) return;

            if (window.AITableModal) {
              window.AITableModal.show({
                icon: '⚡i18n.t('auto__title_e_action_subtitle_e_path_e_timestamp_tabletype__4d5178')file_event',
                badges: [
                  { text: e.action, class: e.is_deletion ? 'badge bg-danger' : (e.action === 'Created' ? 'badge bg-success' : 'badge bg-info text-darki18n.t('auto__text_e_process_name_e_process_name__6d7996')WinAPI ReadDirectoryChangesW', class: 'badge bg-dark border border-secondary text-info' },
                  { text: 'WinAPI', class: 'badge bg-secondary' }
                ],
                metadata: [
                  { label: i18n.t('auto___4fe9c0'), value: e.action },
                  { label: i18n.t('auto___f6ae8c'), value: e.path },
                  { label: i18n.t('auto___87d72c'), value: e.process_name ? `${e.process_name}${e.process_id ? ` (PID: ${e.process_id})` : ''}` : i18n.t('auto___24f084') },
                  { label: i18n.t('auto___e9fe45'), value: e.timestamp },
                  { label: i18n.t('auto___73c61c'), value: e.is_deletion ? i18n.t('auto___f835de') : i18n.t('auto___f82a82') },
                  { label: i18n.t('auto___a4ab77'), value: e.watch_dir || currentWatchDir },
                  { label: i18n.t('auto___36dec8'), value: currentWatchDirs.join('; ') }
                ],
                rawTitle: i18n.t('auto__winapi_process_info_8c57dd'),
                rawContent: JSON.stringify(e, null, 2),
                requestData: e
              });
            }
          };
        });
      }
    } catch (e) {
      console.error('[SystemInspectorTab] Failed to fetch live file events:', e);
    }
  }

  // =============================================================================
  // Multi-Directory Watcher Manager & Folder Explorer Modal Logic
  // =============================================================================

  function showWatchDirsAlert(msg, type = 'success') {
    const alertEl = document.getElementById('modal-watch-dirs-alert');
    if (!alertEl) return;
    alertEl.className = `alert alert-${type} py-2 px-3 small mb-3`;
    alertEl.innerHTML = msg;
    alertEl.classList.remove('d-none');
    if (type === 'success') {
      setTimeout(() => {
        alertEl.classList.add('d-none');
      }, 3500);
    }
  }

  function renderModalActiveDirsList() {
    const container = document.getElementById('modal-watch-dirs-active-list');
    const countBadge = document.getElementById('modal-watch-dirs-count');
    const hintEl = document.getElementById('modal-watch-dirs-footer-hint');

    if (!container) return;

    if (countBadge) countBadge.textContent = String(stagedWatchDirs.length);
    if (hintEl) hintEl.textContent = `Выбрано папок для мониторинга: ${stagedWatchDirs.length}`;

    if (stagedWatchDirs.length === 0) {
      container.innerHTML = `
        <div class="text-center text-muted small py-3">
          <i class="bi bi-folder-x me-1"></i> Список пуст. Выберите папки в проводнике ниже или воспользуйтесь быстрыми пресетами.
        </div>
      `;
      return;
    }

    container.innerHTML = stagedWatchDirs.map((dirPath, idx) => {
      const folderName = dirPath.split('\\').pop() || dirPath;
      const driveLetter = (dirPath.slice(0, 2)).toUpperCase();
      return `
        <div class="p-1.5 px-2 rounded d-flex align-items-center justify-content-between gap-2" style="background: var(--bg-color); border: 1px solid var(--border-color);">
          <div class="d-flex align-items-center gap-2 text-truncate" style="max-width: 82%;">
            <i class="bi bi-folder-check text-warning fs-6"></i>
            <span class="badge bg-secondary font-monospace" style="font-size: 0.68rem;">${driveLetter}</span>
            <div class="text-truncate">
              <span class="fw-bold small text-light">${escapeHtml(folderName)}</span>
              <span class="small text-muted font-monospace d-block text-truncate" style="font-size: 0.72rem;" title="${escapeHtml(dirPath)}">${escapeHtml(dirPath)}</span>
            </div>
          </div>
          <button class="btn btn-xs btn-outline-danger rounded-pill px-2 py-0.5" onclick="window._removeStagedWatchDir(${idx})" title=i18n.t('auto___b31e8b')>
            <i class="bi bi-trash3"></i>
          </button>
        </div>
      `;
    }).join('i18n.t('auto__window_removestagedwatchdir_function_index_if_index_0_index_stagedwatchdirs_length_const_removed_stagedwatchdirs_splice_index_1_0_rendermodalactivedirslist_showwatchdirsalert_code_escapehtml_removed_code__ad56fb')infoi18n.t('auto__function_adddirtostaged_pathtoadd_if_pathtoadd_pathtoadd_trim_return_const_cleanpath_pathtoadd_trim_if_stagedwatchdirs_includes_cleanpath_showwatchdirsalert_code_escapehtml_cleanpath_code__9b1e45')warningi18n.t('auto__return_stagedwatchdirs_push_cleanpath_rendermodalactivedirslist_showwatchdirsalert_code_escapehtml_cleanpath_code__abd723')success');
  }

  async function loadSystemDrives() {
    const drivesBar = document.getElementById('modal-watch-drives-bar');
    if (!drivesBar) return;

    try {
      const res = await fetch('/api/sysadmin/filesystem/drives');
      if (res.ok) {
        const data = await res.json();
        cachedDrives = data.drives || [];
      }
    } catch (e) {
      console.warn('[SystemInspectorTab] Failed to fetch system drives:', e);
      cachedDrives = [{ mountpoint: 'C:\\', free_gb: 0 }];
    }

    if (cachedDrives.length === 0) {
      cachedDrives = [{ mountpoint: 'C:\\', free_gb: 0 }];
    }

    drivesBar.innerHTML = cachedDrives.map(d => {
      const label = d.mountpoint || 'C:\\';
      const freeTxt = d.free_gb ? `${d.free_gb} GB free` : '';
      return `
        <button class="btn btn-xs btn-outline-light rounded-pill px-2 py-0.5 sys-drive-btn font-monospace" data-drive="${escapeHtml(label)}" title="${escapeHtml(label)} ${freeTxt}">
          <i class="bi bi-hdd me-1"></i>${escapeHtml(label)}
        </button>
      `;
    }).join('');

    drivesBar.querySelectorAll('.sys-drive-btn').forEach(btn => {
      btn.onclick = () => {
        const drv = btn.getAttribute('data-drive');
        if (drv) loadFolderBrowser(drv);
      };
    });
  }

  function renderBreadcrumbs(currentPath) {
    const bcContainer = document.getElementById('modal-folder-breadcrumbs');
    if (!bcContainer) return;

    const parts = currentPath.replace(/\\+$/, '').split('\\');
    let builtPath = '';
    const crumbsHtml = parts.map((part, idx) => {
      if (idx === 0) {
        builtPath = part + '\\';
      } else {
        builtPath = builtPath + (builtPath.endsWith('\\') ? '' : '\\') + part;
      }
      const clickPath = builtPath;
      const isLast = idx === parts.length - 1;
      return `
        <span class="d-inline-flex align-items-center">
          ${idx > 0 ? '<span class="text-muted mx-1">/</span>' : ''}
          <a href="#" class="sys-breadcrumb-link text-decoration-none ${isLast ? 'fw-bold text-info' : 'text-light'}" data-path="${escapeHtml(clickPath)}">
            ${escapeHtml(part || i18n.t('auto___16ff06'))}
          </a>
        </span>
      `;
    }).join('');

    bcContainer.innerHTML = crumbsHtml;

    bcContainer.querySelectorAll('.sys-breadcrumb-link').forEach(link => {
      link.onclick = (e) => {
        e.preventDefault();
        const p = link.getAttribute('data-path');
        if (p) loadFolderBrowser(p);
      };
    });
  }

  async function loadFolderBrowser(targetPath) {
    const inputPath = document.getElementById('modal-folder-path-input');
    const browserList = document.getElementById('modal-folder-browser-list');
    if (!targetPath) targetPath = 'C:\\';
    currentBrowserPath = targetPath;

    if (inputPath) inputPath.value = targetPath;
    renderBreadcrumbs(targetPath);

    if (!browserList) return;
    browserList.innerHTML = `<div class="text-center text-muted small py-3"><span class="spinner-border spinner-border-sm me-1i18n.t('auto__span_div_try_const_res_await_fetch_api_sysadmin_filesystem_browse_path_encodeuricomponent_targetpath_if_res_ok_const_errjson_await_res_json_catch_throw_new_error_errjson_detail_http_res_status_const_data_await_res_json_const_dirs_data_directories_if_dirs_length_0_browserlist_innerhtml_div_class__ebc8be')text-center text-muted small py-3i18n.t('auto__div_return_browserlist_innerhtml_dirs_map_d_const_isalreadyselected_stagedwatchdirs_includes_d_path_return_div_class__f915e8')p-1 px-2 rounded d-flex align-items-center justify-content-between gap-2 sys-folder-browser-item" style="background: var(--surface-1); border: 1px solid var(--border-color); cursor: pointer;">
            <div class="d-flex align-items-center gap-2 text-truncate flex-grow-1 sys-nav-to-folder" data-path="${escapeHtml(d.path)}" title=i18n.t('auto___3976d8')>
              <i class="bi ${d.has_subdirs ? 'bi-folder2 text-warning' : 'bi-folder text-warning'}"></i>
              <span class="small text-light text-truncate">${escapeHtml(d.name)}</span>
              <span class="small text-muted font-monospace ms-auto me-2" style="font-size: 0.68rem;">${d.modified || ''}</span>
            </div>
            <button class="btn btn-xs ${isAlreadySelected ? 'btn-success' : 'btn-outline-info'} rounded-pill px-2 py-0.5 sys-add-folder-btn" data-path="${escapeHtml(d.path)}" title=i18n.t('auto___9dab5a')>
              <i class="bi ${isAlreadySelected ? 'bi-check2' : 'bi-plus-lg'} me-1"></i>${isAlreadySelected ? i18n.t('auto___741829') : i18n.t('auto___a0b8fc')}
            </button>
          </div>
        `;
      }).join('');

      // Bind folder navigation
      browserList.querySelectorAll('.sys-nav-to-folder').forEach(el => {
        el.onclick = () => {
          const p = el.getAttribute('data-path');
          if (p) loadFolderBrowser(p);
        };
      });

      // Bind Add buttons
      browserList.querySelectorAll('.sys-add-folder-btn').forEach(btn => {
        btn.onclick = (e) => {
          e.stopPropagation();
          const p = btn.getAttribute('data-path');
          if (p) {
            addDirToStaged(p);
            btn.className = 'btn btn-xs btn-success rounded-pill px-2 py-0.5 sys-add-folder-btn';
            btn.innerHTML = '<i class="bi bi-check2 me-1"></i>Выбрана';
          }
        };
      });

    } catch (e) {
      console.warn('[SystemInspectorTab] Failed to browse folder:', e);
      browserList.innerHTML = `<div class="text-danger small py-2 px-2"><i class="bi bi-exclamation-triangle me-1"></i> Ошибка доступа: ${escapeHtml(e.message)}</div>`;
    }
  }

  let currentExclusions = {
    enabled: true,
    paths: [],
    extensions: [],
    patterns: [],
    processes: [],
    filtered_count: 0
  };

  function showExclusionsAlert(msg, type = 'success') {
    const alertEl = document.getElementById('modal-exclusions-alert');
    if (!alertEl) return;
    alertEl.className = `alert alert-${type} py-2 px-3 small mb-3`;
    alertEl.innerHTML = msg;
    alertEl.classList.remove('d-none');
    if (type === 'success' || type === 'info') {
      setTimeout(() => {
        alertEl.classList.add('d-none');
      }, 3500);
    }
  }

  function renderExclusionsLists() {
    const totalCount = (currentExclusions.paths?.length || 0) +
      (currentExclusions.extensions?.length || 0) +
      (currentExclusions.patterns?.length || 0) +
      (currentExclusions.processes?.length || 0);

    const tabBadge = document.getElementById('modal-watch-exclusions-tab-count');
    const headerBadge = document.getElementById('sys-exclusions-count-badge');
    if (tabBadge) tabBadge.textContent = String(totalCount);
    if (headerBadge) headerBadge.textContent = String(totalCount);

    const switchEl = document.getElementById('switch-exclusions-active');
    const statusBadge = document.getElementById('badge-exclusions-status');
    if (switchEl) switchEl.checked = Boolean(currentExclusions.enabled);
    if (statusBadge) {
      if (currentExclusions.enabled) {
        statusBadge.className = 'badge bg-success';
        statusBadge.textContent = i18n.t('auto___593689');
      } else {
        statusBadge.className = 'badge bg-secondary';
        statusBadge.textContent = i18n.t('auto___919af8');
      }
    }

    const filteredTotalEl = document.getElementById('modal-exclusions-filtered-total');
    if (filteredTotalEl) filteredTotalEl.textContent = String(currentExclusions.filtered_count || 0);

    // 1. Paths list
    const pathsContainer = document.getElementById('list-ex-paths');
    const pathsBadge = document.getElementById('badge-ex-paths-count');
    if (pathsBadge) pathsBadge.textContent = String(currentExclusions.paths?.length || 0);
    if (pathsContainer) {
      if (!currentExclusions.paths || currentExclusions.paths.length === 0) {
        pathsContainer.innerHTML = `<div class="text-muted small text-center py-2i18n.t('auto__div_else_pathscontainer_innerhtml_currentexclusions_paths_map_p_idx_div_class__7b2386')d-flex align-items-center justify-content-between gap-1.5 p-1 px-2 rounded mb-1" style="background: var(--bg-color); border: 1px solid var(--border-color);">
            <span class="small font-monospace text-light text-truncate" style="font-size: 0.72rem;" title="${escapeHtml(p)}">${escapeHtml(p)}</span>
            <button class="btn btn-xs btn-outline-danger py-0 px-1 rounded-pill" onclick="window._removeExclusionItem('paths', '${escapeHtml(p.replace(/\\/g, '\\\\'))}')" title=i18n.t('auto___86ea33')>✕</button>
          </div>
        `).join('');
      }
    }

    // 2. Extensions list
    const extsContainer = document.getElementById('list-ex-extensions');
    const extsBadge = document.getElementById('badge-ex-extensions-count');
    if (extsBadge) extsBadge.textContent = String(currentExclusions.extensions?.length || 0);
    if (extsContainer) {
      if (!currentExclusions.extensions || currentExclusions.extensions.length === 0) {
        extsContainer.innerHTML = `<div class="text-muted small text-center py-2i18n.t('auto__div_else_extscontainer_innerhtml_div_class__c33de1')d-flex flex-wrap gap-1">` + currentExclusions.extensions.map(e => `
          <span class="badge bg-dark border border-secondary text-info d-inline-flex align-items-center gap-1 font-monospace" style="font-size: 0.75rem;">
            ${escapeHtml(e)}
            <button type="button" class="btn-close btn-close-white" style="font-size: 0.5rem;" onclick="window._removeExclusionItem('extensions', '${escapeHtml(e)}')" title=i18n.t('auto___86ea33')></button>
          </span>
        `).join('') + `</div>`;
      }
    }

    // 3. Patterns list
    const patsContainer = document.getElementById('list-ex-patterns');
    const patsBadge = document.getElementById('badge-ex-patterns-count');
    if (patsBadge) patsBadge.textContent = String(currentExclusions.patterns?.length || 0);
    if (patsContainer) {
      if (!currentExclusions.patterns || currentExclusions.patterns.length === 0) {
        patsContainer.innerHTML = `<div class="text-muted small text-center py-2i18n.t('auto__div_else_patscontainer_innerhtml_div_class__7fb86a')d-flex flex-wrap gap-1">` + currentExclusions.patterns.map(pat => `
          <span class="badge bg-dark border border-secondary text-warning d-inline-flex align-items-center gap-1 font-monospace" style="font-size: 0.75rem;">
            ${escapeHtml(pat)}
            <button type="button" class="btn-close btn-close-white" style="font-size: 0.5rem;" onclick="window._removeExclusionItem('patterns', '${escapeHtml(pat)}')" title=i18n.t('auto___86ea33')></button>
          </span>
        `).join('') + `</div>`;
      }
    }

    // 4. Processes list
    const procsContainer = document.getElementById('list-ex-processes');
    const procsBadge = document.getElementById('badge-ex-processes-count');
    if (procsBadge) procsBadge.textContent = String(currentExclusions.processes?.length || 0);
    if (procsContainer) {
      if (!currentExclusions.processes || currentExclusions.processes.length === 0) {
        procsContainer.innerHTML = `<div class="text-muted small text-center py-2i18n.t('auto__div_else_procscontainer_innerhtml_div_class__8fcfb2')d-flex flex-wrap gap-1">` + currentExclusions.processes.map(proc => `
          <span class="badge bg-dark border border-secondary text-danger d-inline-flex align-items-center gap-1 font-monospace" style="font-size: 0.75rem;">
            <i class="bi bi-cpu me-0.5"></i>${escapeHtml(proc)}
            <button type="button" class="btn-close btn-close-white" style="font-size: 0.5rem;" onclick="window._removeExclusionItem('processes', '${escapeHtml(proc)}')" title=i18n.t('auto___86ea33')></button>
          </span>
        `).join('') + `</div>`;
      }
    }
  }

  async function fetchExclusionsData() {
    try {
      const res = await fetch('/api/sysadmin/file-audit/exclusions');
      if (res.ok) {
        currentExclusions = await res.json();
        renderExclusionsLists();
      }
    } catch (e) {
      console.warn('[SystemInspectorTab] Failed to fetch exclusions:', e);
    }
  }

  async function addExclusionItem(category, value) {
    if (!value || !value.trim()) return;
    const cleanVal = value.trim();
    try {
      const res = await fetch('/api/sysadmin/file-audit/exclusions/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/jsoni18n.t('auto__body_json_stringify_category_value_cleanval_const_data_await_res_json_if_res_ok_data_success_currentexclusions_data_exclusions_currentexclusions_renderexclusionslists_showexclusionsalert_code_escapehtml_cleanval_code__77510c')success');
        const inputVal = document.getElementById('input-exclusion-value');
        if (inputVal) inputVal.value = '';
      } else {
        showExclusionsAlert(data.message || i18n.t('auto___6eb64a'), 'warningi18n.t('auto__catch_e_showexclusionsalert_e_message__10c413')danger');
    }
  }

  window._removeExclusionItem = async function(category, value) {
    if (!value) return;
    try {
      const res = await fetch('/api/sysadmin/file-audit/exclusions/remove', {
        method: 'POST',
        headers: { 'Content-Type': 'application/jsoni18n.t('auto__body_json_stringify_category_value_const_data_await_res_json_if_res_ok_data_success_currentexclusions_data_exclusions_currentexclusions_renderexclusionslists_showexclusionsalert_code_escapehtml_value_code__d88c8a')info');
      } else {
        showExclusionsAlert(data.message || i18n.t('auto___6c75fb'), 'warningi18n.t('auto__catch_e_showexclusionsalert_e_message__20d84e')danger');
    }
  };

  async function toggleExclusionsActive(enabled) {
    try {
      const res = await fetch('/api/sysadmin/file-audit/exclusions/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/jsoni18n.t('auto__body_json_stringify_enabled_const_data_await_res_json_if_res_ok_data_success_currentexclusions_data_exclusions_currentexclusions_renderexclusionslists_showexclusionsalert_data_enabled__246a4d')включена' : i18n.t('auto___91e464')}`, 'infoi18n.t('auto__catch_e_showexclusionsalert_e_message__032e3b')danger');
    }
  }

  async function applyExclusionPreset(preset) {
    if (preset === 'logs') {
      await addExclusionItem('paths', 'AppData\\Roaming\\AI-Breadboard\\apps\\windows\\telemetry\\logs');
      await addExclusionItem('extensions', '.log');
      await addExclusionItem('extensions', '.csv');
      await addExclusionItem('patterns', '*librehardwaremonitor_polls.csv*');
    } else if (preset === 'search') {
      await addExclusionItem('processes', 'SearchIndexer.exe');
      await addExclusionItem('patterns', '*Windows.db*');
      await addExclusionItem('patterns', '*Windows.db-wal*');
      await addExclusionItem('patterns', '*Windows.db-shm*');
    } else if (preset === 'temp') {
      await addExclusionItem('paths', 'AppData\\Local\\Temp');
      await addExclusionItem('extensions', '.tmp');
      await addExclusionItem('patterns', '~$*');
    } else if (preset === 'dev') {
      await addExclusionItem('paths', '.git');
      await addExclusionItem('paths', 'node_modules');
      await addExclusionItem('paths', '__pycache__');
      await addExclusionItem('paths', '.pytest_cache');
    }
  }

  async function openWatchFoldersModal(initialTab = 'folders') {
    const modalEl = document.getElementById('modal-sys-watch-folders');
    if (!modalEl) {
      console.warn('[SystemInspectorTab] modal-sys-watch-folders element not found');
      return;
    }

    try {
      const res = await fetch('/api/sysadmin/file-audit/watch-dirs');
      if (res.ok) {
        const data = await res.json();
        stagedWatchDirs = data.watch_dirs && data.watch_dirs.length ? [...data.watch_dirs] : [currentWatchDir || 'C:\\'];
      } else {
        stagedWatchDirs = currentWatchDirs.length ? [...currentWatchDirs] : [currentWatchDir || 'C:\\'];
      }
    } catch {
      stagedWatchDirs = currentWatchDirs.length ? [...currentWatchDirs] : [currentWatchDir || 'C:\\'];
    }

    renderModalActiveDirsList();
    const tabFoldersBadge = document.getElementById('modal-watch-dirs-tab-count');
    if (tabFoldersBadge) tabFoldersBadge.textContent = String(stagedWatchDirs.length);

    await loadSystemDrives();
    await fetchExclusionsData();

    // Tab activation
    if (initialTab === 'exclusions') {
      const tabExBtn = document.getElementById('tab-btn-watch-exclusions');
      if (tabExBtn && window.bootstrap && window.bootstrap.Tab) {
        const tab = window.bootstrap.Tab.getOrCreateInstance(tabExBtn);
        tab.show();
      } else if (tabExBtn) {
        tabExBtn.click();
      }
    } else {
      const tabFoldersBtn = document.getElementById('tab-btn-watch-folders');
      if (tabFoldersBtn && window.bootstrap && window.bootstrap.Tab) {
        const tab = window.bootstrap.Tab.getOrCreateInstance(tabFoldersBtn);
        tab.show();
      } else if (tabFoldersBtn) {
        tabFoldersBtn.click();
      }
    }

    const startPath = stagedWatchDirs[0] || currentBrowserPath || 'C:\\';
    loadFolderBrowser(startPath);

    // Bind navigation buttons
    const btnUp = document.getElementById('btn-modal-folder-up');
    if (btnUp) {
      btnUp.onclick = () => {
        const parts = currentBrowserPath.replace(/\\+$/, '').split('\\');
        if (parts.length > 1) {
          parts.pop();
          let parentPath = parts.join('\\');
          if (parts.length === 1 && !parentPath.endsWith('\\')) parentPath += '\\';
          loadFolderBrowser(parentPath);
        }
      };
    }

    const btnGo = document.getElementById('btn-modal-folder-go');
    const inputPath = document.getElementById('modal-folder-path-input');
    if (btnGo && inputPath) {
      btnGo.onclick = () => {
        if (inputPath.value && inputPath.value.trim()) {
          loadFolderBrowser(inputPath.value.trim());
        }
      };
      inputPath.onkeydown = (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          btnGo.click();
        }
      };
    }

    const btnAddCurrent = document.getElementById('btn-modal-folder-add-current');
    if (btnAddCurrent) {
      btnAddCurrent.onclick = () => {
        const val = inputPath ? inputPath.value.trim() : currentBrowserPath;
        if (val) addDirToStaged(val);
      };
    }

    // Presets buttons (folders)
    document.querySelectorAll('.sys-preset-btn').forEach(btn => {
      btn.onclick = () => {
        const preset = btn.getAttribute('data-preset');
        let target = '';
        if (preset === 'project') target = 'C:\\Users\\onela\\AppData\\Local\\AI-Breadboard';
        else if (preset === 'downloads') target = 'C:\\Users\\onela\\Downloads';
        else if (preset === 'desktop') target = 'C:\\Users\\onela\\Desktop';
        else if (preset === 'temp') target = 'C:\\Users\\onela\\AppData\\Local\\Temp';

        if (target) {
          addDirToStaged(target);
          loadFolderBrowser(target);
        }
      };
    });

    // Exclusions switch and add buttons binding
    const switchExActive = document.getElementById('switch-exclusions-active');
    if (switchExActive) {
      switchExActive.onchange = (e) => {
        toggleExclusionsActive(e.target.checked);
      };
    }

    const btnAddEx = document.getElementById('btn-add-exclusion');
    const selectExCat = document.getElementById('select-exclusion-category');
    const inputExVal = document.getElementById('input-exclusion-value');
    if (btnAddEx && selectExCat && inputExVal) {
      btnAddEx.onclick = () => {
        addExclusionItem(selectExCat.value, inputExVal.value);
      };
      inputExVal.onkeydown = (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          btnAddEx.click();
        }
      };
    }

    // Exclusions preset buttons
    document.querySelectorAll('.sys-ex-preset-btn').forEach(btn => {
      btn.onclick = () => {
        const preset = btn.getAttribute('data-preset');
        if (preset) applyExclusionPreset(preset);
      };
    });

    // Apply button
    const btnApply = document.getElementById('btn-modal-watch-dirs-apply');
    if (btnApply) {
      btnApply.onclick = async () => {
        if (stagedWatchDirs.length === 0) {
          showWatchDirsAlert(i18n.t('auto___59aa83'), 'warning');
          return;
        }

        btnApply.disabled = true;
        btnApply.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Применение...';

        try {
          const res = await fetch('/api/sysadmin/file-audit/watch-dirs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ paths: stagedWatchDirs })
          });
          const resData = await res.json();
          if (res.ok && resData.success) {
            if (window.bootstrap && window.bootstrap.Modal) {
              const modal = window.bootstrap.Modal.getInstance(modalEl);
              if (modal) modal.hide();
            } else {
              modalEl.classList.remove('show');
              modalEl.style.display = 'nonei18n.t('auto__await_fetchlivefileevents_else_showwatchdirsalert_resdata_detail__16d204')Не удалось применить список папок'}`, 'dangeri18n.t('auto__catch_err_showwatchdirsalert_err_message__fc83ed')danger');
        } finally {
          btnApply.disabled = false;
          btnApply.innerHTML = '<i class="bi bi-check2-circle me-1"></i> Применить и запустить';
        }
      };
    }

    if (window.bootstrap && window.bootstrap.Modal) {
      const modal = window.bootstrap.Modal.getOrCreateInstance(modalEl);
      modal.show();
    } else {
      modalEl.classList.add('show');
      modalEl.style.display = 'block';
    }
  }

  function showLiveWatcherHelpModal() {
    const dirsStr = currentWatchDirs.length ? currentWatchDirs.join('\n- ') : (currentWatchDir || i18n.t('auto___72e5f4'));
    if (window.AITableModal) {
      window.AITableModal.show({
        icon: 'ℹ️',
        title: i18n.t('auto__multi_directory__b3bfdb'),
        subtitle: i18n.t('auto__windows_winapi_readdirectorychangesw_a40215'),
        tableType: 'help',
        badges: [
          { text: 'WinAPI ReadDirectoryChangesW', class: 'badge bg-info text-dark' },
          { text: 'Multi-Directory', class: 'badge bg-primary' },
          { text: 'Real-Time Streaming', class: 'badge bg-success' },
          { text: i18n.t('auto__bwatchsubtree_true__711b17'), class: 'badge bg-warning text-dark' }
        ],
        metadata: [
          { label: i18n.t('auto___a4f422'), value: i18n.t('auto_winapi_readdirectorychangesw_windows_kernel32_dll__6baf20') },
          { label: i18n.t('auto___f23fe5'), value: i18n.t('auto___336209') },
          { label: i18n.t('auto___178611'), value: currentWatchDirs.join('; ') || i18n.t('auto___39020a') },
          { label: i18n.t('auto___1e65eb'), value: i18n.t('auto_apps_windows_sysadmin_config_json_watch_directories__b6a336') }
        ],
        rawTitle: i18n.t('auto___7b02e3'),
        rawContent: `# ПанельИзменения файлов в реальном времени

### 1. Что это такое?
Компонент для мгновенного перехвата операций файловой системы в режиме реального времени на базе WinAPI ReadDirectoryChangesW с поддержкой одновременного наблюдения за произвольным количеством папок.

### 2. Типы отслеживаемых действий:
- Created: Создание нового файла или папки (FILE_ACTION_ADDED).
- Modified: Модификация содержимого, атрибутов или размера файла (FILE_ACTION_MODIFIED).
- Deleted: Удаление файла или папки с диска (FILE_ACTION_REMOVED).
- Renamed: Переименование объекта (старое и новое имя).

### 3. Как выбрать или добавить папки?
1. Нажмите кнопку «Папка» в заголовке панели.
2. Откроется модальное окно с проводником файловой системы.
3. Выберите логический диск (C:, D:, E:), перейдите в нужную папку или вставьте путь вручную.
4. Нажмите «+ Добавить папку» или кнопку «Следить» напротив любой подпапки.
5. Нажмите «Применить и запустить». Список сохранится в config.json и мониторинг стартует автоматически!`,
        requestData: {
          current_watch_dirs: currentWatchDirs,
          engine: 'ReadDirectoryChangesW (Multi-Directory)'
        }
      });
    } else {
      alert(i18n.t('auto__multi_directory_n_n__69cda7') + dirsStr);
    }
  }

  function setupSysSensorInterval(seconds) {
    _currentUiRefreshSeconds = seconds || 5;
    const pollHandler = async () => {
      // Поэтапный независимый опрос подсистем
      fetchCoreMetrics();
      fetchProcessesFromDb();
      fetchLhmSensors();
      fetchLiveFileEvents();
      fetchNetworkActivity();
    };
    if (window.registerTabPoller) {
      window.registerTabPoller('tab-system-inspector', pollHandler, _currentUiRefreshSeconds * 1000, { immediate: false });
    } else {
      if (window._sysSensorInterval) {
        clearInterval(window._sysSensorInterval);
        window._sysSensorInterval = null;
      }
      window._sysSensorInterval = setInterval(() => {
        if (window.isTabActive ? window.isTabActive('tab-system-inspector') : true) {
          pollHandler();
        }
      }, _currentUiRefreshSeconds * 1000);
    }
    console.log(`[SystemInspectorTab] UI sensor refresh interval set to ${_currentUiRefreshSeconds}s (SQLite processes & telemetry)`);
  }

  function openSysIntervalsModal() {
    const modalEl = document.getElementById('sysIntervalsModal');
    if (!modalEl) {
      console.warn('[SystemInspectorTab] sysIntervalsModal element not found');
      return;
    }

    // Set UI select to current seconds
    const selUi = document.getElementById('modal-ui-refresh-select');
    if (selUi) {
      selUi.value = String(_currentUiRefreshSeconds);
    }
    const uiBadge = document.getElementById('modal-ui-refresh-badgei18n.t('auto__if_uibadge_uibadge_textcontent_currentuirefreshseconds_loadsysintervalsconfig_false_if_window_bootstrap_window_bootstrap_modal_const_modal_window_bootstrap_modal_getorcreateinstance_modalel_modal_show_else_modalel_classlist_add__37cc52')show');
      modalEl.style.display = 'block';
    }
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  async function initSystemInspectorTab() {
    console.log('[SystemInspectorTab] Initializing (progressive telemetry & SQLite processes)...i18n.t('auto__bindtabevents_1_fetchcoremetrics_2_sqlite_fetchprocessesfromdb_3_smart_ram_fetchhardwarequick_4_lhm_fetchlhmsensors_5_fetchnetworkactivity_fetchlivefileevents_6_websocket_connectsystemwebsocket_7_5_if_window_syssensorinterval_setupsyssensorinterval_currentuirefreshseconds_5_function_activatesysteminspectortab_if_window_istabactive_window_istabactive__19cd5f')tab-system-inspector')) return;
    console.log('[SystemInspectorTab] Tab activated, resuming telemetry stream...');
    fetchCoreMetrics();
    fetchProcessesFromDb();
    fetchHardwareQuick();
    fetchLhmSensors();
    connectSystemWebSocket();
  }

  function deactivateSystemInspectorTab() {
    console.log('[SystemInspectorTab] Tab deactivated, pausing telemetry stream...');
    disconnectSystemWebSocket();
  }

  window.initSystemInspectorTab = initSystemInspectorTab;
  window.activateSystemInspectorTab = activateSystemInspectorTab;
  window.deactivateSystemInspectorTab = deactivateSystemInspectorTab;
  window.openSysIntervalsModal = openSysIntervalsModal;
  window.openProcStatsModal = openProcStatsModal;
  window.fetchProcessesFromDb = fetchProcessesFromDb;
})();

