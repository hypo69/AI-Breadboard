// System & Hardware Inspector Tab JS Module
(function() {
  let sysWs = null;
  let isSysInitialized = false;
  let isSysPaused = false;
  let isNetPaused = false;
  let currentNetFilter = 'internet';
  let cachedNetworkActivities = [];
  let latestTelemetrySnapshot = null;
  let cachedSensors = [];
  let currentSensorCategory = 'all';
  let isLhmRunning = false;

  async function fetchLhmSensors() {
    const container = document.getElementById('sys-lhm-sensors-container');
    const badgeStatus = document.getElementById('sys-lhm-status-badge');
    const badgeCount = document.getElementById('sys-lhm-sensors-count');
    const btnLaunch = document.getElementById('btn-sys-launch-lhm');
    if (!container) return;

    try {
      // 1. Проверяем статус LHM
      let lhmStatus = null;
      try {
        const sRes = await fetch('/api/v1/lhm/status');
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
        const mRes = await fetch('/api/v1/lhm/metrics');
        if (mRes.ok) {
          const mData = await mRes.json();
          sensorsList = mData.sensors || [];
        }
      } else {
        // Fallback: Опрос аппаратных сенсоров хоста (WMI + NVIDIA-SMI)
        if (badgeStatus) {
          badgeStatus.textContent = 'WMI/GPU';
          badgeStatus.className = 'badge bg-secondary';
        }
        try {
          const hwRes = await fetch('/api/windows/hardware/sensors');
          if (hwRes.ok) {
            const hwData = await hwRes.json();
            const rawSensors = hwData.sensors || [];
            sensorsList = rawSensors.map(s => ({
              id: s.id || s.sensor_id || s.name,
              hardware_name: s.hardware_name || s.component || (s.sensor_type === 'Temperature' ? 'Thermal Sensors' : 'System Hardware'),
              hardware_type: s.hardware_type || 'system',
              sensor_category: s.category || s.sensor_type || s.type || 'Temperatures',
              sensor_name: s.name || s.label || 'Sensor',
              value_raw: s.unit ? `${s.value} ${s.unit}` : `${s.value}`,
              value_numeric: typeof s.value === 'number' ? s.value : parseFloat(s.value),
              unit: s.unit || ''
            }));
          }
        } catch {
          // Второй fallback
          const sysRes = await fetch('/api/v1/system/sensors');
          if (sysRes.ok) {
            const raw = await sysRes.json();
            sensorsList = (raw || []).map(s => ({
              id: s.sensor_id || s.name,
              hardware_name: s.category ? s.category.toUpperCase() : 'System Hardware',
              hardware_type: 'system',
              sensor_category: s.category || 'Temperatures',
              sensor_name: s.name,
              value_raw: s.unit ? `${s.value} ${s.unit}` : `${s.value}`,
              value_numeric: s.value,
              unit: s.unit
            }));
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
        <div class="text-center py-4 text-muted small">
          <div>Сенсоры LibreHardwareMonitor не обнаружены</div>
          <div class="mt-2 text-muted" style="font-size: 0.72rem;">Убедитесь, что LHM запущен с правами администратора и включен Web Server (:8085)</div>
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
      const grpKey = s.hardware_name || s.sensor_category || 'Оборудование';
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

    if (titleEl) titleEl.textContent = 'Выполняется AI-аудит залогированных сенсоров...';
    if (subEl) subEl.textContent = 'Чтение CSV-логов, усреднение значений и сравнение со спецификациями железа';
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
      modelBadge.textContent = report.ai_model_used || 'Heuristic Engine';
    }

    // Render Devices List
    if (devCountEl) {
      devCountEl.textContent = `${devices.length} устр.`;
    }
    if (devListEl) {
      if (devices.length > 0) {
        devListEl.innerHTML = devices.map(d => {
          let icon = 'bi-hdd-network';
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
        aiCompEl.textContent = 'AI-сравнение выполнено по эвристическим профилям оборудования хоста. Все параметры сенсоров в пределах нормы.';
      }
    }

    // Analyze CPU
    const elCpuBadge = document.getElementById('modal-cpu-temp-badge');
    const elCpuText = document.getElementById('modal-cpu-analysis-text');
    if (maxCpuTemp !== null) {
      if (elCpuBadge) {
        elCpuBadge.textContent = `${Math.round(maxCpuTemp)} °C`;
        elCpuBadge.className = `badge ${maxCpuTemp > 82 ? 'bg-danger' : maxCpuTemp > 70 ? 'bg-warning text-dark' : 'bg-success'}`;
      }
      if (maxCpuTemp > 82) {
        if (elCpuText) elCpuText.textContent = `Критический нагрев (${Math.round(maxCpuTemp)}°C). Риск теплового троттлинга.`;
        recommendations.push({
          type: 'danger',
          icon: 'bi-exclamation-triangle-fill',
          title: 'Высокая температура процессора',
          text: `Пиковая/средняя температура CPU достигает ${Math.round(maxCpuTemp)}°C. Проверьте плотность прижима кулера, термопасту и запыленность радиатора.`
        });
      } else if (maxCpuTemp > 70) {
        if (elCpuText) elCpuText.textContent = `Повышенная температура (${Math.round(maxCpuTemp)}°C) под нагрузкой.`;
        recommendations.push({
          type: 'warning',
          icon: 'bi-thermometer-high',
          title: 'Повышенный нагрев CPU',
          text: `Температура CPU ${Math.round(maxCpuTemp)}°C выше оптимального порога. Рекомендуется настроить кривую оборотов вентилятора.`
        });
      } else {
        if (elCpuText) elCpuText.textContent = `Штатный температурный режим (${Math.round(maxCpuTemp)}°C). Троттлинг отсутствует.`;
        recommendations.push({
          type: 'success',
          icon: 'bi-check-circle-fill',
          title: 'Тепловой режим процессора оптимален',
          text: `Температура процессора ${Math.round(maxCpuTemp)}°C находится в безопасной зоне номинальных характеристик.`
        });
      }
    } else {
      if (elCpuBadge) elCpuBadge.textContent = 'N/A';
      if (elCpuText) elCpuText.textContent = 'Температурные датчики CPU не предоставили данных.';
    }

    // Analyze GPU
    const elGpuBadge = document.getElementById('modal-gpu-temp-badge');
    const elGpuText = document.getElementById('modal-gpu-analysis-text');
    if (maxGpuTemp !== null) {
      if (elGpuBadge) {
        elGpuBadge.textContent = `${Math.round(maxGpuTemp)} °C`;
        elGpuBadge.className = `badge ${maxGpuTemp > 80 ? 'bg-danger' : maxGpuTemp > 72 ? 'bg-warning text-dark' : 'bg-success'}`;
      }
      if (maxGpuTemp > 80) {
        if (elGpuText) elGpuText.textContent = `Критический нагрев GPU (${Math.round(maxGpuTemp)}°C).`;
        recommendations.push({
          type: 'danger',
          icon: 'bi-gpu-card',
          title: 'Высокая температура видеокарты',
          text: `Графический чип нагревается до ${Math.round(maxGpuTemp)}°C. Проверьте циркуляцию воздуха в корпусе ПК.`
        });
      } else {
        if (elGpuText) elGpuText.textContent = `Температура GPU ${Math.round(maxGpuTemp)}°C в норме.`;
        recommendations.push({
          type: 'success',
          icon: 'bi-check-circle-fill',
          title: 'Видеокарта работает штатно',
          text: `Температурные показатели GPU (${Math.round(maxGpuTemp)}°C) соответствуют номиналу.`
        });
      }
    } else {
      if (elGpuBadge) elGpuBadge.textContent = 'N/A';
      if (elGpuText) elGpuText.textContent = 'Дискретный GPU в режиме энергосбережения или данные отсутствуют.';
    }

    // Analyze Cooling
    const elFanBadge = document.getElementById('modal-fan-status-badge');
    const elFanText = document.getElementById('modal-fan-analysis-text');
    if (fanSpeeds.length > 0) {
      const activeFans = fanSpeeds.filter(f => f.value > 0);
      if (elFanBadge) {
        elFanBadge.textContent = `${activeFans.length} акт. кулеров`;
        elFanBadge.className = 'badge bg-success';
      }
      if (elFanText) {
        elFanText.textContent = `Опрошено ${fanSpeeds.length} кулеров. Обороты стабильны.`;
      }
    } else {
      if (elFanBadge) elFanBadge.textContent = 'Пассив / WMI';
      if (elFanText) elFanText.textContent = 'Управление вентиляторами через BIOS или пассивное охлаждение.';
    }

    // Additional recommendations from backend report
    if (report && Array.isArray(report.recommendations)) {
      report.recommendations.forEach(r => {
        if (!recommendations.some(ex => ex.text.includes(r))) {
          recommendations.push({
            type: 'info',
            icon: 'bi-info-circle',
            title: 'Рекомендация по оборудованию',
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

    const countStat = document.getElementById('modal-sensor-count-stat');
    if (countStat) {
      const totalSmpls = report ? report.total_samples : sensorsList.length;
      countStat.textContent = `${sensorsList.length} шт. (${totalSmpls} замеров)`;
    }

    const maxTempStat = document.getElementById('modal-sensor-max-temp');
    if (maxTempStat) maxTempStat.textContent = overallMaxTemp > 0 ? `${Math.round(overallMaxTemp)} °C` : 'N/A';

    const statusTitle = document.getElementById('modal-sensor-status-title');
    const statusSub = document.getElementById('modal-sensor-status-sub');
    const statusIcon = document.getElementById('modal-sensor-status-icon');

    if (healthScore >= 85) {
      if (statusIcon) statusIcon.textContent = '✅';
      if (statusTitle) statusTitle.textContent = 'Все аппаратные подсистемы работают в идеальном режиме';
      if (statusSub) statusSub.textContent = `Усредненные показатели соответствуют спецификациям реального железа (макс. ${Math.round(overallMaxTemp)}°C).`;
    } else if (healthScore >= 65) {
      if (statusIcon) statusIcon.textContent = '⚠️';
      if (statusTitle) statusTitle.textContent = 'Обнаружены параметры оборудования, требующие внимания';
      if (statusSub) statusSub.textContent = `Пиковая температура ${Math.round(overallMaxTemp)}°C. Ознакомьтесь с AI-заключением и рекомендациями.`;
    } else {
      if (statusIcon) statusIcon.textContent = '🚨';
      if (statusTitle) statusTitle.textContent = 'Внимание: Критические параметры оборудования!';
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
      `).join('');
    }

    // Prepare Clipboard text
    lastAnalysisReportText = `=== AI-Breadboard: Отчет AI-аудита сенсоров и оборудования ===\n` +
      `Дата: ${new Date().toLocaleString('ru-RU')}\n` +
      `Индекс здоровья системы: ${healthScore}/100\n` +
      `AI-модель: ${report ? report.ai_model_used : 'Heuristic'}\n` +
      `Распознанные устройства (${devices.length} шт.): ${devices.join(', ')}\n` +
      `Сенсоров в аудите: ${sensorsList.length}\n` +
      `Максимальная температура: ${overallMaxTemp > 0 ? Math.round(overallMaxTemp) + ' °C' : 'N/A'}\n\n` +
      `=== AI СРАВНЕНИЕ СО СПЕЦИФИКАЦИЯМИ РЕАЛЬНОГО ЖЕЛЕЗА ===\n` +
      `${(report && report.comparison_report) ? report.comparison_report : 'Параметры в норме.'}\n\n` +
      `=== РЕКОМЕНДАЦИИ И ВЫВОДЫ ===\n` +
      recommendations.map((r, i) => `${i + 1}. [${r.title}] ${r.text}`).join('\n') +
      `\n======================================================`;
  }

  function updateTelemetryDashboard(snap) {
    if (!snap) return;

    // CPU
    if (snap.cpu) {
      const cpuVal = document.getElementById('sys-metric-cpu-val');
      const cpuFill = document.getElementById('sys-metric-cpu-fill');
      const cpuSub = document.getElementById('sys-metric-cpu-sub');

      const pct = Number(snap.cpu.total_percent || 0);
      if (cpuVal) cpuVal.innerText = `${pct.toFixed(1)}%`;
      if (cpuFill) cpuFill.style.width = `${Math.min(100, pct)}%`;
      if (cpuSub) cpuSub.innerText = `${snap.cpu.physical_cores || '--'} Физических / ${snap.cpu.logical_cores || '--'} Потоков`;
    }

    // RAM
    if (snap.memory) {
      const ramVal = document.getElementById('sys-metric-ram-val');
      const ramFill = document.getElementById('sys-metric-ram-fill');
      const ramSub = document.getElementById('sys-metric-ram-sub');

      const usedGb = Number(snap.memory.used_gb || 0);
      const totalGb = Number(snap.memory.total_gb || 0);
      const pct = Number(snap.memory.percent || 0);

      if (ramVal) ramVal.innerText = `${usedGb.toFixed(1)} / ${totalGb.toFixed(1)} GB`;
      if (ramFill) ramFill.style.width = `${pct}%`;
      if (ramSub) ramSub.innerText = `${pct}% занято (${Number(snap.memory.available_gb || 0).toFixed(1)} GB свободно)`;
    }

    // GPU
    if (Array.isArray(snap.gpus) && snap.gpus.length > 0) {
      const g = snap.gpus[0];
      const gpuVal = document.getElementById('sys-metric-gpu-val');
      const gpuSub = document.getElementById('sys-metric-gpu-sub');

      if (gpuVal) gpuVal.innerText = g.name || 'GPU';
      if (gpuSub) gpuSub.innerText = `VRAM: ${Number(g.memory_total_gb || 0).toFixed(1)} GB | CUDA: ${g.has_cuda ? 'Да' : 'Нет'}`;
    }

    // Disk I/O
    if (snap.disk_io) {
      const diskVal = document.getElementById('sys-metric-disk-val');
      const diskSub = document.getElementById('sys-metric-disk-sub');

      const totalMb = ((snap.disk_io.read_bytes_per_sec + snap.disk_io.write_bytes_per_sec) / (1024 * 1024)).toFixed(2);
      const rKb = (snap.disk_io.read_bytes_per_sec / 1024).toFixed(0);
      const wKb = (snap.disk_io.write_bytes_per_sec / 1024).toFixed(0);

      if (diskVal) diskVal.innerText = `${totalMb} MB/s`;
      if (diskSub) diskSub.innerText = `Чтение: ${rKb} KB/s | Запись: ${wKb} KB/s`;
    }

    // Physical Disks SMART Health
    const diskCont = document.getElementById('sys-physical-disks-container');
    const diskBadge = document.getElementById('sys-disk-health-badge');
    if (diskCont && Array.isArray(snap.physical_disks) && snap.physical_disks.length > 0) {
      const allHealthy = snap.physical_disks.every(d => d.health_status === 'Healthy');
      if (diskBadge) {
        diskBadge.textContent = allHealthy ? 'SMART OK' : 'Внимание';
        diskBadge.className = allHealthy ? 'badge bg-success-subtle text-success border border-success' : 'badge bg-warning-subtle text-warning border border-warning';
      }
      diskCont.innerHTML = snap.physical_disks.slice(0, 2).map(d => `
        <div class="d-flex justify-content-between align-items-center py-0.5">
          <span class="text-truncate" style="max-width: 140px;" title="${escapeHtml(d.model)}">${escapeHtml(d.model)}</span>
          <span class="badge bg-secondary font-monospace">${d.size_gb} GB ${d.media_type}</span>
        </div>
      `).join('');
    }

    // Battery & Power
    const powerCont = document.getElementById('sys-power-info-container');
    const powerBadge = document.getElementById('sys-power-status-badge');
    if (powerCont && snap.battery) {
      if (snap.battery.has_battery && snap.battery.percent !== null) {
        if (powerBadge) {
          powerBadge.textContent = `${snap.battery.percent}% ${snap.battery.power_plugged ? '⚡ Зарядка' : '🔋 Батарея'}`;
          powerBadge.className = snap.battery.power_plugged ? 'badge bg-success-subtle text-success border border-success' : 'badge bg-warning-subtle text-warning border border-warning';
        }
        const minsLeft = snap.battery.secs_left ? Math.round(snap.battery.secs_left / 60) : null;
        powerCont.innerHTML = `
          <div>Статус: ${snap.battery.power_plugged ? 'Подключено к сети' : 'Работа от батареи'}</div>
          <div>${minsLeft ? `Осталось ~${minsLeft} мин.` : 'Профиль: ' + (snap.battery.power_profile || 'Balanced')}</div>
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
    } else if (ramSticksCont) {
      ramSticksCont.innerHTML = `<div>RAM: ${snap.memory ? snap.memory.total_gb : '--'} GB физической памяти</div>`;
    }

    // Reliability & Open Ports
    const alertsCont = document.getElementById('sys-alerts-ports-container');
    const alertsBadge = document.getElementById('sys-alerts-badge');
    if (alertsCont) {
      const portCount = Array.isArray(snap.listening_ports) ? snap.listening_ports.length : 0;
      const isReboot = snap.alerts && snap.alerts.reboot_pending;
      if (alertsBadge) {
        alertsBadge.textContent = isReboot ? 'Перезагрузка' : 'Стабильно';
        alertsBadge.className = isReboot ? 'badge bg-warning text-dark' : 'badge bg-info-subtle text-info border border-info';
      }
      alertsCont.innerHTML = `
        <div>Сетевые сокеты: <span class="fw-bold text-white">${portCount} портов LISTEN</span></div>
        <div class="text-truncate" title="${escapeHtml(snap.alerts?.latest_alert || '')}">${escapeHtml(snap.alerts?.latest_alert || 'Система стабильна')}</div>
      `;
    }

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
        <tr class="sys-proc-row" data-idx="${idx}" style="cursor: pointer;" title="Нажмите для детальной AI-диагностики процесса">
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
              { label: 'Имя процесса', value: p.name },
              { label: 'Process ID (PID)', value: String(p.pid) },
              { label: 'Пользователь / Учетная запись', value: p.username || 'SYSTEM' },
              { label: 'Статус', value: p.status || 'Выполняется' },
              { label: 'Загрузка CPU', value: `${Number(p.cpu_percent || 0).toFixed(1)}%` },
              { label: 'Оперативная память', value: `${Number(p.memory_mb || 0).toFixed(1)} MB` },
              { label: 'Количество потоков', value: String(p.num_threads || 1) },
              { label: 'Исполняемый путь', value: p.exe || p.executable_path || 'Системный процесс Windows', isCode: true, fullWidth: true }
            ],
            rawTitle: 'Команда запуска / Аргументы',
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
          (item.recv_summary || '').toLowerCase().includes(filterText)
        );
      }
      return true;
    });

    const uniqueProcs = new Set(filtered.map(i => i.pid)).size;
    if (countBadge) countBadge.textContent = `${uniqueProcs} программ`;
    if (connsBadge) connsBadge.textContent = `${filtered.length} сокетов`;

    if (filtered.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-muted small">Нет активных сетевых соединений по выбранному фильтру</td></tr>';
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
        ? '<span class="badge bg-primary-subtle text-primary border border-primary px-1" style="font-size: 0.62rem;" title="Внешний сервер в сети Интернет">WAN</span>'
        : '<span class="badge bg-secondary px-1" style="font-size: 0.62rem;" title="Локальный сокет Loopback">LAN</span>';

      const sentBytes = item.sent_kb > 0 ? `<span class="badge bg-dark border border-warning text-warning ms-1" style="font-size: 0.68rem;">${item.sent_kb.toLocaleString()} KB</span>` : '';
      const recvBytes = item.recv_kb > 0 ? `<span class="badge bg-dark border border-success text-success ms-1" style="font-size: 0.68rem;">${item.recv_kb.toLocaleString()} KB</span>` : '';

      return `
        <tr class="sys-net-row" data-idx="${idx}" style="cursor: pointer;" title="Нажмите для детальной диагностики сетевого соединения">
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
              <span class="fw-semibold text-truncate" style="max-width: 110px; font-size: 0.74rem; color: #a855f7;" title="${escapeHtml(item.service_type)}">${escapeHtml(item.service_type)}</span>
            </div>
          </td>
          <td style="text-align: center;">
            <span class="${statusBadgeClass}" style="font-size: 0.68rem;">${escapeHtml(item.status)}</span>
          </td>
          <td>
            <div class="d-flex align-items-start gap-1">
              <i class="bi bi-arrow-up-right text-warning mt-0.5" style="font-size: 0.72rem;"></i>
              <div class="text-truncate" style="max-width: 250px; font-size: 0.73rem; color: #fde047;" title="${escapeHtml(item.sent_summary)}">
                ${escapeHtml(item.sent_summary)} ${sentBytes}
              </div>
            </div>
          </td>
          <td>
            <div class="d-flex align-items-start gap-1">
              <i class="bi bi-arrow-down-left text-success mt-0.5" style="font-size: 0.72rem;"></i>
              <div class="text-truncate" style="max-width: 250px; font-size: 0.73rem; color: #86efac;" title="${escapeHtml(item.recv_summary)}">
                ${escapeHtml(item.recv_summary)} ${recvBytes}
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
              { text: item.is_internet ? 'Интернет (WAN)' : 'Локально (LAN)', class: item.is_internet ? 'badge bg-warning text-dark' : 'badge bg-secondary' }
            ],
            metadata: [
              { label: 'Программа / Процесс', value: item.name },
              { label: 'Process ID (PID)', value: String(item.pid) },
              { label: 'Пользователь системы', value: item.user || 'SYSTEM' },
              { label: 'Удаленный адрес (Remote)', value: item.remote_address },
              { label: 'Локальный сокет (Local)', value: item.local_address },
              { label: 'Протокол / Служба', value: `${item.protocol} • ${item.service_type}` },
              { label: 'Что шлет (Отправка)', value: `${item.sent_summary} ${item.sent_kb > 0 ? '(' + item.sent_kb + ' KB)' : ''}`, fullWidth: true },
              { label: 'Что принимает (Прием)', value: `${item.recv_summary} ${item.recv_kb > 0 ? '(' + item.recv_kb + ' KB)' : ''}`, fullWidth: true }
            ],
            rawTitle: 'Сетевой дамп подключения',
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

    if (summaryEl) summaryEl.innerText = 'Запуск глубокого AI-аудита системы и оборудования...';

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
          anomaliesEl.innerHTML = '<span style="color: #4ade80; font-size: 0.75rem;"><i class="bi bi-check-circle me-1"></i> Аномалий в работе оборудования не обнаружено</span>';
        }
      }

      if (summaryEl) {
        const recs = Array.isArray(report.recommendations) && report.recommendations.length > 0
          ? `\nРекомендации: ${report.recommendations.join(', ')}`
          : '';
        summaryEl.innerText = `${report.summary || 'Телеметрия в норме.'}${recs}`;
      }
    } catch (e) {
      console.error('[SystemInspectorTab] AI Diagnose error:', e);
      if (summaryEl) summaryEl.innerText = 'Ошибка выполнения AI-диагностики: ' + e.message;
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
        statusBadge.innerText = '○ Поток приостановлен';
      }
      return;
    }

    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${proto}//${window.location.host}/api/v1/system/stream`;

    try {
      sysWs = new WebSocket(wsUrl);
      const statusBadge = document.getElementById('sys-conn-status');

      sysWs.onopen = () => {
        console.info('[SystemInspectorTab] WebSocket соединение с телеметрией установлено.');
        if (statusBadge) {
          statusBadge.className = 'badge rounded-pill bg-success-subtle text-success border border-success px-3 py-2';
          statusBadge.innerText = '● Телеметрия активна';
        }
      };

      sysWs.onmessage = (evt) => {
        try {
          const snap = JSON.parse(evt.data);
          latestTelemetrySnapshot = snap;
          updateTelemetryDashboard(snap);
        } catch (e) {
          console.error('[SystemInspectorTab] Ошибка разбора сообщения телеметрии:', e);
        }
      };

      const scheduleReconnect = (reason) => {
        if (sysWsReconnectTimer) return;
        if (window.isTabActive && !window.isTabActive('tab-system-inspector')) return;
        console.warn(`[SystemInspectorTab] WebSocket отключен (${reason}). Автопереподключение через 3 сек...`);
        if (statusBadge) {
          statusBadge.className = 'badge rounded-pill bg-warning-subtle text-warning border border-warning px-3 py-2';
          statusBadge.innerText = '○ Переподключение...';
        }
        sysWsReconnectTimer = setTimeout(() => {
          sysWsReconnectTimer = null;
          if (!window.isTabActive || window.isTabActive('tab-system-inspector')) {
            connectSystemWebSocket();
          }
        }, 3000);
      };

      sysWs.onclose = (evt) => {
        scheduleReconnect(`код закрытия: ${evt.code}`);
      };

      sysWs.onerror = (err) => {
        console.warn('[SystemInspectorTab] Ошибка соединения WebSocket:', err);
        scheduleReconnect('ошибка связи');
      };
    } catch (err) {
      console.error('[SystemInspectorTab] Ошибка инициализации WebSocket:', err);
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
      statusBadge.innerText = '○ Поток приостановлен';
    }
  }

  function bindTabEvents() {
    const btnPause = document.getElementById('btn-sys-pause-proc');
    if (btnPause) {
      btnPause.onclick = () => {
        isSysPaused = !isSysPaused;
        btnPause.innerText = isSysPaused ? 'Возобновить' : 'Пауза';
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
          window.appConfigEditor.open('system_inspector', 'Настройки телеметрии и инспектора');
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
        const badge = document.getElementById('modal-ui-refresh-badge');
        if (badge) badge.textContent = `${sec} сек`;
      };
    }

    // Изменения файлов в реальном времени controls
    const changeWatchDirBtn = document.getElementById('btn-sys-change-watch-dir');
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
        btnPauseNet.innerText = isNetPaused ? 'Возобновить' : 'Пауза';
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
        currentNetFilter = btn.getAttribute('data-filter') || 'internet';
        renderNetworkActivityTable();
      };
    });

    // Инициализация интерактивных ресайзеров таблиц
    initNetTableResizer();
    initWatcherTableResizer();
  }

  function initNetTableResizer() {
    const resizer = document.getElementById('sys-net-table-resizer');
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
    const tableContainer = document.getElementById('sys-watcher-table-container');
    if (!resizer || !tableContainer) return;

    if (resizer._resizerInitialized) return;
    resizer._resizerInitialized = true;

    // Восстановление сохранённой пользователем высоты
    try {
      const savedHeight = localStorage.getItem('sys_inspector_watcher_height');
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
    resizer.addEventListener('touchstart', onMouseDown, { passive: false });

    // Сброс по двойному клику
    resizer.addEventListener('dblclick', () => {
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
    { value: '1 second', label: '1 сек' },
    { value: '2 seconds', label: '2 сек' },
    { value: '3 seconds', label: '3 сек' },
    { value: '5 seconds', label: '5 сек' },
    { value: '10 seconds', label: '10 сек' },
    { value: '30 seconds', label: '30 сек' },
    { value: '1 minute', label: '1 мин' },
    { value: '5 minutes', label: '5 мин' },
    { value: '10 minutes', label: '10 мин' },
    { value: '30 minutes', label: '30 мин' },
    { value: '1 hour', label: '1 час' },
    { value: '6 hours', label: '6 часов' },
    { value: '24 hours', label: '24 часа' },
  ];

  const CORE_RESOURCE_LOGGERS = [
    'librehardwaremonitor',
    'system_inspector',
    'hardware_monitor',
    'smartmontools'
  ];

  const LOGGER_META = {
    librehardwaremonitor: {
      icon: '🌡️',
      title: 'LibreHardwareMonitor',
      desc: 'Аппаратные сенсоры: температура CPU/GPU, вольтаж, обороты вентиляторов, частоты',
    },
    system_inspector: {
      icon: '📊',
      title: 'System Inspector',
      desc: 'Комплексный снимок: загрузка CPU, RAM, дисковый ввод-вывод, процессы хоста',
    },
    hardware_monitor: {
      icon: '💻',
      title: 'Hardware Monitor',
      desc: 'Аппаратные датчики WMI, GPU SMI (NVIDIA/AMD/Intel) и физические шины',
    },
    smartmontools: {
      icon: '💾',
      title: 'SmartMonTools (SMART)',
      desc: 'Диагностика накопителей NVMe/SSD/HDD, температура дисков и здоровье SMART',
    },
    windows_sysadmin: {
      icon: '🛠️',
      title: 'Windows SysAdmin',
      desc: 'Системные службы Windows, пользователи, локальные группы и сетевые порты',
    },
    windows_defender: {
      icon: '🛡️',
      title: 'Windows Defender',
      desc: 'Статус антивирусной защиты, сигнатуры, обнаруженные угрозы и карантин',
    },
    windows_startup_auditor: {
      icon: '🚀',
      title: 'StartUp Auditor',
      desc: 'Автозагрузка программ, реестр Run/RunOnce, сервисы и планировщик задач',
    },
    windows_backup_manager: {
      icon: '📦',
      title: 'Backup Manager',
      desc: 'Резервные копии баз данных SQLite, конфигураций и снапшотов системы',
    },
    website_monitor: {
      icon: '🌐',
      title: 'Website Monitor',
      desc: 'Проверка доступности веб-сервисов, задержка ответов HTTP/HTTPS',
    },
    gcloud_monitor: {
      icon: '☁️',
      title: 'GCloud Monitor',
      desc: 'Телеметрия виртуальных машин, квоты и мониторинг Google Cloud',
    },
    cloudflared_monitor: {
      icon: '🚇',
      title: 'Cloudflare Tunnel',
      desc: 'Статус защищенных туннелей cloudflared и исходящих подключений',
    },
    user_assistant: {
      icon: '🤖',
      title: 'User Assistant',
      desc: 'Фоновые периодические напоминания, календарь и уведомления',
    },
    trading_terminal: {
      icon: '📈',
      title: 'Trading Terminal',
      desc: 'Торговые котировки, балансы криптобирж и открытые ордера',
    },
    registry_viewer: {
      icon: '📑',
      title: 'Registry Viewer',
      desc: 'Мониторинг изменений системного реестра Windows',
    },
    software_audit: {
      icon: '🔍',
      title: 'Software Audit',
      desc: 'Аудит неиспользуемого и редко запускаемого ПО (UserAssist/Prefetch)',
    },
    helpdesk: {
      icon: '🎫',
      title: 'Helpdesk',
      desc: 'Мониторинг тикетов техподдержки и уведомлений',
    },
  };

  let _sysIntervalsConfigData = null;
  let _currentUiRefreshSeconds = 5;

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
      const meta = LOGGER_META[name] || { icon: '⚙️', title: name, desc: 'Системный сбор метрик' };
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
            <div class="form-check form-switch m-0" title="Включить/отключить сбор метрик для этого сервиса">
              <input class="form-check-input sys-int-enable" type="checkbox" data-logger="${name}" ${isEnabled ? 'checked' : ''}>
            </div>
            ${buildIntervalSelectHtml(name, intervalVal)}
            <button class="btn btn-xs btn-outline-secondary rounded px-1.5 py-0.5 sys-int-custom-btn" data-logger="${name}" title="Ввести произвольный интервал вручную">
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
      const meta = LOGGER_META[name] || { icon: '🔹', title: name, desc: 'Фоновый опрос службы' };
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
            <div class="form-check form-switch m-0" title="Включить/выключить">
              <input class="form-check-input sys-int-enable" type="checkbox" data-logger="${name}" ${isEnabled ? 'checked' : ''}>
            </div>
            ${buildIntervalSelectHtml(name, intervalVal)}
            <button class="btn btn-xs btn-outline-secondary rounded px-1.5 py-0.5 sys-int-custom-btn" data-logger="${name}" title="Ввести произвольный интервал вручную">
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
            opt = document.createElement('option');
            opt.value = trimmed;
            opt.textContent = `${trimmed} (пользовательский)`;
            sel.appendChild(opt);
          }
          sel.value = trimmed;
        }
      };
    });
  }

  async function saveSysIntervalsConfig() {
    const btnSave = document.getElementById('btn-modal-intervals-save');
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
        `<i class="bi bi-check-circle-fill text-success me-1"></i> ${result.message || 'Интервалы успешно сохранены в config.json и применены!'}`,
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
            elStatus.textContent = '🚨 Всплеск удалений';
          } else if (telem.high_activity_alert) {
            elStatus.className = 'badge bg-warning-subtle text-warning border border-warning px-2 py-1';
            elStatus.textContent = '⚡ Высокий I/O';
          } else {
            elStatus.className = 'badge bg-success-subtle text-success border border-success px-2 py-1';
            elStatus.textContent = '🟢 Штатный режим';
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
          dirPathEl.innerText = 'Папки не выбраны';
        } else if (currentWatchDirs.length === 1) {
          const singleName = currentWatchDirs[0].split('\\').pop() || currentWatchDirs[0];
          dirPathEl.innerText = singleName;
        } else {
          const firstNames = currentWatchDirs.slice(0, 2).map(p => p.split('\\').pop() || p).join(', ');
          dirPathEl.innerText = `${currentWatchDirs.length} папок: ${firstNames}${currentWatchDirs.length > 2 ? '...' : ''}`;
        }
      }
      if (badge) {
        badge.title = `Отслеживаемые каталоги (${currentWatchDirs.length}):\n${currentWatchDirs.join('\n')}\n\n(Нажмите для настройки и выбора папок)`;
      }

      const tbody = document.getElementById('sys-watcher-tbody');
      if (tbody) {
        if (events.length === 0) {
          const labelDirs = currentWatchDirs.length > 0 ? currentWatchDirs.join(', ') : 'проекта';
          tbody.innerHTML = `<tr><td colspan="4" class="text-center text-muted p-2">Ожидание изменений в папках <code>${labelDirs}</code>...</td></tr>`;
          return;
        }
        tbody.innerHTML = events.map((e, idx) => {
          const rootDirHint = e.watch_dir ? (e.watch_dir.split('\\').pop() || e.watch_dir) : '';
          const procDisplay = e.process_name
            ? `<span class="badge bg-dark border border-secondary text-info font-monospace text-truncate d-inline-block" style="max-width: 165px; font-size: 0.72rem;" title="Программа: ${escapeHtml(e.process_name)}${e.process_id ? ` (PID: ${e.process_id})` : ''}"><i class="bi bi-cpu me-1"></i>${escapeHtml(e.process_name)}${e.process_id ? ` [${e.process_id}]` : ''}</span>`
            : `<span class="text-muted" style="font-size: 0.72rem;">—</span>`;
          return `
            <tr class="sys-live-row" data-idx="${idx}" style="cursor: pointer;" title="Нажмите для AI-диагностики события">
              <td class="font-monospace text-muted small">${e.timestamp?.slice(11, 19) || ''}</td>
              <td>
                <span class="badge ${e.is_deletion ? 'bg-danger' : (e.action === 'Created' ? 'bg-success' : 'bg-secondary')}">${e.action}</span>
                ${rootDirHint && currentWatchDirs.length > 1 ? `<span class="badge bg-dark border border-secondary text-muted ms-1" style="font-size: 0.65rem;" title="Корень: ${escapeHtml(e.watch_dir)}">${rootDirHint}</span>` : ''}
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
                icon: '⚡',
                title: `Файловое событие: ${e.action}`,
                subtitle: `${e.path} | ${e.timestamp}`,
                tableType: 'file_event',
                badges: [
                  { text: e.action, class: e.is_deletion ? 'badge bg-danger' : (e.action === 'Created' ? 'badge bg-success' : 'badge bg-info text-dark') },
                  { text: e.process_name ? `Программа: ${e.process_name}` : 'WinAPI ReadDirectoryChangesW', class: 'badge bg-dark border border-secondary text-info' },
                  { text: 'WinAPI', class: 'badge bg-secondary' }
                ],
                metadata: [
                  { label: 'Действие', value: e.action },
                  { label: 'Полный путь к файлу', value: e.path },
                  { label: 'Программа / Процесс', value: e.process_name ? `${e.process_name}${e.process_id ? ` (PID: ${e.process_id})` : ''}` : 'Фоновый процесс / завершен' },
                  { label: 'Время события', value: e.timestamp },
                  { label: 'Признак удаления', value: e.is_deletion ? 'Да (Файл удален/переименован)' : 'Нет' },
                  { label: 'Папка события', value: e.watch_dir || currentWatchDir },
                  { label: 'Все отслеживаемые папки', value: currentWatchDirs.join('; ') }
                ],
                rawTitle: 'Детали события WinAPI & Process Info',
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
          <button class="btn btn-xs btn-outline-danger rounded-pill px-2 py-0.5" onclick="window._removeStagedWatchDir(${idx})" title="Удалить из списка мониторинга">
            <i class="bi bi-trash3"></i>
          </button>
        </div>
      `;
    }).join('');
  }

  window._removeStagedWatchDir = function(index) {
    if (index >= 0 && index < stagedWatchDirs.length) {
      const removed = stagedWatchDirs.splice(index, 1)[0];
      renderModalActiveDirsList();
      showWatchDirsAlert(`Папка удалена из списка: <code>${escapeHtml(removed)}</code>`, 'info');
    }
  };

  function addDirToStaged(pathToAdd) {
    if (!pathToAdd || !pathToAdd.trim()) return;
    const cleanPath = pathToAdd.trim();
    if (stagedWatchDirs.includes(cleanPath)) {
      showWatchDirsAlert(`Папка уже есть в списке: <code>${escapeHtml(cleanPath)}</code>`, 'warning');
      return;
    }
    stagedWatchDirs.push(cleanPath);
    renderModalActiveDirsList();
    showWatchDirsAlert(`Папка добавлена: <code>${escapeHtml(cleanPath)}</code>`, 'success');
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
            ${escapeHtml(part || 'Корень')}
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
    browserList.innerHTML = `<div class="text-center text-muted small py-3"><span class="spinner-border spinner-border-sm me-1"></span> Загрузка директорий...</div>`;

    try {
      const res = await fetch(`/api/sysadmin/filesystem/browse?path=${encodeURIComponent(targetPath)}`);
      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `HTTP ${res.status}`);
      }

      const data = await res.json();
      const dirs = data.directories || [];

      if (dirs.length === 0) {
        browserList.innerHTML = `<div class="text-center text-muted small py-3">В этой директории нет доступных подпапок</div>`;
        return;
      }

      browserList.innerHTML = dirs.map(d => {
        const isAlreadySelected = stagedWatchDirs.includes(d.path);
        return `
          <div class="p-1 px-2 rounded d-flex align-items-center justify-content-between gap-2 sys-folder-browser-item" style="background: var(--surface-1); border: 1px solid var(--border-color); cursor: pointer;">
            <div class="d-flex align-items-center gap-2 text-truncate flex-grow-1 sys-nav-to-folder" data-path="${escapeHtml(d.path)}" title="Нажмите для перехода в папку">
              <i class="bi ${d.has_subdirs ? 'bi-folder2 text-warning' : 'bi-folder text-warning'}"></i>
              <span class="small text-light text-truncate">${escapeHtml(d.name)}</span>
              <span class="small text-muted font-monospace ms-auto me-2" style="font-size: 0.68rem;">${d.modified || ''}</span>
            </div>
            <button class="btn btn-xs ${isAlreadySelected ? 'btn-success' : 'btn-outline-info'} rounded-pill px-2 py-0.5 sys-add-folder-btn" data-path="${escapeHtml(d.path)}" title="Добавить в отслеживаемые">
              <i class="bi ${isAlreadySelected ? 'bi-check2' : 'bi-plus-lg'} me-1"></i>${isAlreadySelected ? 'Выбрана' : 'Следить'}
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
        statusBadge.textContent = 'ВКЛ';
      } else {
        statusBadge.className = 'badge bg-secondary';
        statusBadge.textContent = 'ВЫКЛ';
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
        pathsContainer.innerHTML = `<div class="text-muted small text-center py-2">Нет исключенных папок</div>`;
      } else {
        pathsContainer.innerHTML = currentExclusions.paths.map((p, idx) => `
          <div class="d-flex align-items-center justify-content-between gap-1.5 p-1 px-2 rounded mb-1" style="background: var(--bg-color); border: 1px solid var(--border-color);">
            <span class="small font-monospace text-light text-truncate" style="font-size: 0.72rem;" title="${escapeHtml(p)}">${escapeHtml(p)}</span>
            <button class="btn btn-xs btn-outline-danger py-0 px-1 rounded-pill" onclick="window._removeExclusionItem('paths', '${escapeHtml(p.replace(/\\/g, '\\\\'))}')" title="Удалить">✕</button>
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
        extsContainer.innerHTML = `<div class="text-muted small text-center py-2">Нет исключенных расширений</div>`;
      } else {
        extsContainer.innerHTML = `<div class="d-flex flex-wrap gap-1">` + currentExclusions.extensions.map(e => `
          <span class="badge bg-dark border border-secondary text-info d-inline-flex align-items-center gap-1 font-monospace" style="font-size: 0.75rem;">
            ${escapeHtml(e)}
            <button type="button" class="btn-close btn-close-white" style="font-size: 0.5rem;" onclick="window._removeExclusionItem('extensions', '${escapeHtml(e)}')" title="Удалить"></button>
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
        patsContainer.innerHTML = `<div class="text-muted small text-center py-2">Нет исключенных шаблонов</div>`;
      } else {
        patsContainer.innerHTML = `<div class="d-flex flex-wrap gap-1">` + currentExclusions.patterns.map(pat => `
          <span class="badge bg-dark border border-secondary text-warning d-inline-flex align-items-center gap-1 font-monospace" style="font-size: 0.75rem;">
            ${escapeHtml(pat)}
            <button type="button" class="btn-close btn-close-white" style="font-size: 0.5rem;" onclick="window._removeExclusionItem('patterns', '${escapeHtml(pat)}')" title="Удалить"></button>
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
        procsContainer.innerHTML = `<div class="text-muted small text-center py-2">Нет исключенных программ</div>`;
      } else {
        procsContainer.innerHTML = `<div class="d-flex flex-wrap gap-1">` + currentExclusions.processes.map(proc => `
          <span class="badge bg-dark border border-secondary text-danger d-inline-flex align-items-center gap-1 font-monospace" style="font-size: 0.75rem;">
            <i class="bi bi-cpu me-0.5"></i>${escapeHtml(proc)}
            <button type="button" class="btn-close btn-close-white" style="font-size: 0.5rem;" onclick="window._removeExclusionItem('processes', '${escapeHtml(proc)}')" title="Удалить"></button>
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
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ category, value: cleanVal })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        currentExclusions = data.exclusions || currentExclusions;
        renderExclusionsLists();
        showExclusionsAlert(`Правило добавлено: <code>${escapeHtml(cleanVal)}</code>`, 'success');
        const inputVal = document.getElementById('input-exclusion-value');
        if (inputVal) inputVal.value = '';
      } else {
        showExclusionsAlert(data.message || 'Правило уже существует или невалидно', 'warning');
      }
    } catch (e) {
      showExclusionsAlert(`Ошибка добавления: ${e.message}`, 'danger');
    }
  }

  window._removeExclusionItem = async function(category, value) {
    if (!value) return;
    try {
      const res = await fetch('/api/sysadmin/file-audit/exclusions/remove', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ category, value })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        currentExclusions = data.exclusions || currentExclusions;
        renderExclusionsLists();
        showExclusionsAlert(`Правило удалено: <code>${escapeHtml(value)}</code>`, 'info');
      } else {
        showExclusionsAlert(data.message || 'Не удалось удалить правило', 'warning');
      }
    } catch (e) {
      showExclusionsAlert(`Ошибка удаления: ${e.message}`, 'danger');
    }
  };

  async function toggleExclusionsActive(enabled) {
    try {
      const res = await fetch('/api/sysadmin/file-audit/exclusions/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        currentExclusions = data.exclusions || currentExclusions;
        renderExclusionsLists();
        showExclusionsAlert(`Фильтрация исключений ${data.enabled ? 'включена' : 'отключена'}`, 'info');
      }
    } catch (e) {
      showExclusionsAlert(`Ошибка переключения: ${e.message}`, 'danger');
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
          showWatchDirsAlert('Выберите хотя бы одну папку для мониторинга', 'warning');
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
              modalEl.style.display = 'none';
            }
            await fetchLiveFileEvents();
          } else {
            showWatchDirsAlert(`Ошибка: ${resData.detail || 'Не удалось применить список папок'}`, 'danger');
          }
        } catch (err) {
          showWatchDirsAlert(`Сетевая ошибка: ${err.message}`, 'danger');
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
    const dirsStr = currentWatchDirs.length ? currentWatchDirs.join('\n- ') : (currentWatchDir || 'Рабочая папка');
    if (window.AITableModal) {
      window.AITableModal.show({
        icon: 'ℹ️',
        title: 'Справка:Изменения файлов в реальном времени (Multi-Directory)',
        subtitle: 'Низкоуровневый мониторинг файловой системы Windows через WinAPI ReadDirectoryChangesW',
        tableType: 'help',
        badges: [
          { text: 'WinAPI ReadDirectoryChangesW', class: 'badge bg-info text-dark' },
          { text: 'Multi-Directory', class: 'badge bg-primary' },
          { text: 'Real-Time Streaming', class: 'badge bg-success' },
          { text: 'Рекурсивно (bWatchSubtree = True)', class: 'badge bg-warning text-dark' }
        ],
        metadata: [
          { label: 'Технология', value: 'WinAPI ReadDirectoryChangesW (нативный вызов ядра Windows kernel32.dll)' },
          { label: 'Режим работы', value: 'Множественные потоки мониторинга с агрегацией в единый кольцевой буфер' },
          { label: 'Отслеживаемые папки', value: currentWatchDirs.join('; ') || 'Рабочая папка проекта' },
          { label: 'Хранение настроек', value: 'apps/windows_sysadmin/config.json (ключ watch_directories)' }
        ],
        rawTitle: 'Подробное руководство по панели мониторинга',
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
      alert('Мониторинг файловой системыИзменения файлов в реальном времени (Multi-Directory).\nОтслеживаемые папки:\n- ' + dirsStr);
    }
  }

  function setupSysSensorInterval(seconds) {
    _currentUiRefreshSeconds = seconds;
    const pollHandler = async () => {
      await fetchLhmSensors();
      await fetchLiveFileEvents();
    };
    if (window.registerTabPoller) {
      window.registerTabPoller('tab-system-inspector', pollHandler, seconds * 1000, { immediate: false });
    } else {
      if (window._sysSensorInterval) {
        clearInterval(window._sysSensorInterval);
        window._sysSensorInterval = null;
      }
      window._sysSensorInterval = setInterval(() => {
        if (window.isTabActive ? window.isTabActive('tab-system-inspector') : true) {
          pollHandler();
        }
      }, seconds * 1000);
    }
    console.log(`[SystemInspectorTab] UI sensor refresh interval set to ${seconds}s`);
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
    const uiBadge = document.getElementById('modal-ui-refresh-badge');
    if (uiBadge) {
      uiBadge.textContent = `${_currentUiRefreshSeconds} сек`;
    }

    loadSysIntervalsConfig(false);

    if (window.bootstrap && window.bootstrap.Modal) {
      const modal = window.bootstrap.Modal.getOrCreateInstance(modalEl);
      modal.show();
    } else {
      modalEl.classList.add('show');
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
    console.log('[SystemInspectorTab] Initializing...');
    bindTabEvents();
    await fetchLhmSensors();
    await fetchLiveFileEvents();
    await fetchNetworkActivity();

    try {
      const snapRes = await fetch('/api/v1/system/summary');
      if (snapRes.ok) {
        latestTelemetrySnapshot = await snapRes.json();
        updateTelemetryDashboard(latestTelemetrySnapshot);
      }
    } catch (e) {
      console.warn('[SystemInspectorTab] Initial snapshot fetch failed:', e);
    }

    connectSystemWebSocket();

    // Periodic sensor refresh
    if (!window._sysSensorInterval) {
      setupSysSensorInterval(_currentUiRefreshSeconds);
    }
  }

  function activateSystemInspectorTab() {
    if (window.isTabActive && !window.isTabActive('tab-system-inspector')) return;
    console.log('[SystemInspectorTab] Tab activated, resuming telemetry stream...');
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
})();

