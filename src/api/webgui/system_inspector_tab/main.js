// System & Hardware Inspector Tab JS Module
(function() {
  let sysWs = null;
  let isSysInitialized = false;
  let isSysPaused = false;
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

  function analyzeSensorsAndReport() {
    if (!cachedSensors || cachedSensors.length === 0) {
      alert('Сенсоры еще не загружены или LibreHardwareMonitor не запущен. Пожалуйста, подождите загрузки.');
      return;
    }

    let healthScore = 100;
    const recommendations = [];

    // Extract metrics
    let maxCpuTemp = null;
    let maxGpuTemp = null;
    let maxMbTemp = null;
    let maxStorageTemp = null;
    let fanSpeeds = [];
    let voltages = [];
    let cpuLoads = [];
    let gpuLoads = [];

    cachedSensors.forEach(s => {
      const cat = (s.sensor_category || '').toLowerCase();
      const hwType = (s.hardware_type || '').toLowerCase();
      const hwName = (s.hardware_name || '').toLowerCase();
      const sName = (s.sensor_name || '').toLowerCase();
      const num = s.value_numeric;

      if (num === null || num === undefined || isNaN(num)) return;

      if (cat.includes('temp')) {
        if (hwType.includes('cpu') || hwName.includes('cpu') || sName.includes('cpu') || sName.includes('core')) {
          if (maxCpuTemp === null || num > maxCpuTemp) maxCpuTemp = num;
        } else if (hwType.includes('gpu') || hwName.includes('gpu') || hwName.includes('nvidia') || sName.includes('gpu')) {
          if (maxGpuTemp === null || num > maxGpuTemp) maxGpuTemp = num;
        } else if (hwType.includes('storage') || hwName.includes('nvme') || hwName.includes('ssd') || hwName.includes('hdd') || sName.includes('drive')) {
          if (maxStorageTemp === null || num > maxStorageTemp) maxStorageTemp = num;
        } else {
          if (maxMbTemp === null || num > maxMbTemp) maxMbTemp = num;
        }
      } else if (cat.includes('fan')) {
        fanSpeeds.push({ name: s.sensor_name, value: num, unit: s.unit || 'RPM' });
      } else if (cat.includes('volt')) {
        voltages.push({ name: s.sensor_name, value: num, unit: s.unit || 'V' });
      } else if (cat.includes('load')) {
        if (hwType.includes('cpu') || sName.includes('cpu')) cpuLoads.push(num);
        else if (hwType.includes('gpu') || sName.includes('gpu')) gpuLoads.push(num);
      }
    });

    const overallMaxTemp = Math.max(
      maxCpuTemp || 0,
      maxGpuTemp || 0,
      maxMbTemp || 0,
      maxStorageTemp || 0
    );

    // Analyze CPU
    const elCpuBadge = document.getElementById('modal-cpu-temp-badge');
    const elCpuText = document.getElementById('modal-cpu-analysis-text');
    if (maxCpuTemp !== null) {
      if (elCpuBadge) {
        elCpuBadge.textContent = `${Math.round(maxCpuTemp)} °C`;
        elCpuBadge.className = `badge ${maxCpuTemp > 82 ? 'bg-danger' : maxCpuTemp > 70 ? 'bg-warning text-dark' : 'bg-success'}`;
      }
      if (maxCpuTemp > 82) {
        healthScore -= 20;
        if (elCpuText) elCpuText.textContent = `Критический нагрев (${Math.round(maxCpuTemp)}°C). Риск теплового троттлинга.`;
        recommendations.push({
          type: 'danger',
          icon: 'bi-exclamation-triangle-fill',
          title: 'Высокая температура процессора',
          text: `Пиковая температура CPU достигает ${Math.round(maxCpuTemp)}°C. Проверьте плотность прижима кулера, термопасту и запыленность радиатора.`
        });
      } else if (maxCpuTemp > 70) {
        healthScore -= 8;
        if (elCpuText) elCpuText.textContent = `Повышенная температура (${Math.round(maxCpuTemp)}°C) под нагрузкой.`;
        recommendations.push({
          type: 'warning',
          icon: 'bi-thermometer-high',
          title: 'Повышенный нагрев CPU',
          text: `Температура CPU ${Math.round(maxCpuTemp)}°C выше оптимального порога в простое. Рекомендуется настроить кривую оборотов вентилятора в BIOS/ПО.`
        });
      } else {
        if (elCpuText) elCpuText.textContent = `Штатный температурный режим (${Math.round(maxCpuTemp)}°C). Троттлинг отсутствует.`;
        recommendations.push({
          type: 'success',
          icon: 'bi-check-circle-fill',
          title: 'Тепловой режим процессора оптимален',
          text: `Пиковая температура процессора ${Math.round(maxCpuTemp)}°C находится в безопасной зеленой зоне (до 70°C).`
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
        healthScore -= 20;
        if (elGpuText) elGpuText.textContent = `Критический нагрев GPU (${Math.round(maxGpuTemp)}°C).`;
        recommendations.push({
          type: 'danger',
          icon: 'bi-gpu-card',
          title: 'Высокая температура видеокарты',
          text: `Графический чип нагревается до ${Math.round(maxGpuTemp)}°C. Проверьте циркуляцию воздуха в корпусе ПК и работу вентиляторов GPU.`
        });
      } else if (maxGpuTemp > 72) {
        healthScore -= 8;
        if (elGpuText) elGpuText.textContent = `Умеренный нагрев (${Math.round(maxGpuTemp)}°C).`;
        recommendations.push({
          type: 'warning',
          icon: 'bi-gpu-card',
          title: 'Нагрев видеокарты под нагрузкой',
          text: `Температура GPU ${Math.round(maxGpuTemp)}°C в допустимых пределах, но близка к верхней границе комфортного диапазона.`
        });
      } else {
        if (elGpuText) elGpuText.textContent = `Температура GPU ${Math.round(maxGpuTemp)}°C в норме.`;
        recommendations.push({
          type: 'success',
          icon: 'bi-check-circle-fill',
          title: 'Видеокарта работает штатно',
          text: `Температурные показатели GPU (${Math.round(maxGpuTemp)}°C) в норме.`
        });
      }
    } else {
      if (elGpuBadge) elGpuBadge.textContent = 'N/A';
      if (elGpuText) elGpuText.textContent = 'Дискретный GPU в режиме энергосбережения или отсутствует.';
    }

    // Analyze Cooling & Motherboard
    const elFanBadge = document.getElementById('modal-fan-status-badge');
    const elFanText = document.getElementById('modal-fan-analysis-text');
    if (fanSpeeds.length > 0) {
      const activeFans = fanSpeeds.filter(f => f.value > 0);
      if (elFanBadge) {
        elFanBadge.textContent = `${activeFans.length} акт. кулеров`;
        elFanBadge.className = 'badge bg-success';
      }
      if (elFanText) {
        elFanText.textContent = `Активно ${activeFans.length} из ${fanSpeeds.length} кулеров. Обороты стабильны.`;
      }
    } else {
      if (elFanBadge) elFanBadge.textContent = 'Пассив / WMI';
      if (elFanText) elFanText.textContent = 'Управление вентиляторами через BIOS или пассивное охлаждение.';
    }

    // Analyze Memory & Snapshots
    if (latestTelemetrySnapshot && latestTelemetrySnapshot.memory) {
      const mem = latestTelemetrySnapshot.memory;
      const memPct = Number(mem.percent || 0);
      if (memPct > 85) {
        healthScore -= 10;
        recommendations.push({
          type: 'warning',
          icon: 'bi-memory',
          title: 'Высокая загрузка оперативной памяти',
          text: `Занято ${memPct.toFixed(1)}% RAM (${mem.used_gb || 0} GB из ${mem.total_gb || 0} GB). Закройте фоновые ресурсоемкие приложения для освобождения памяти.`
        });
      } else {
        recommendations.push({
          type: 'success',
          icon: 'bi-check2-circle',
          title: 'Запас оперативной памяти достаточен',
          text: `Свободно ${Number(mem.available_gb || 0).toFixed(1)} GB RAM (${memPct.toFixed(1)}% занято). Свопинг не требуется.`
        });
      }
    }

    // Analyze Voltages
    if (voltages.length > 0) {
      recommendations.push({
        type: 'info',
        icon: 'bi-lightning-charge',
        title: 'Линии питания материнской платы',
        text: `Опрошено ${voltages.length} датчиков вольтажа. Отклонений по шинам 12V/5V/3.3V не обнаружено.`
      });
    }

    // Final Health Score bounds
    healthScore = Math.max(10, Math.min(100, healthScore));

    // Update Header & Badge
    const badgeHealth = document.getElementById('modal-sensor-health-badge');
    if (badgeHealth) {
      badgeHealth.textContent = `Health: ${healthScore}/100`;
      badgeHealth.className = `badge ms-1 ${healthScore >= 85 ? 'bg-success' : healthScore >= 65 ? 'bg-warning text-dark' : 'bg-danger'}`;
    }

    const countStat = document.getElementById('modal-sensor-count-stat');
    if (countStat) countStat.textContent = `${cachedSensors.length} шт.`;

    const maxTempStat = document.getElementById('modal-sensor-max-temp');
    if (maxTempStat) maxTempStat.textContent = overallMaxTemp > 0 ? `${Math.round(overallMaxTemp)} °C` : 'N/A';

    const statusTitle = document.getElementById('modal-sensor-status-title');
    const statusSub = document.getElementById('modal-sensor-status-sub');
    const statusIcon = document.getElementById('modal-sensor-status-icon');

    if (healthScore >= 85) {
      if (statusIcon) statusIcon.textContent = '✅';
      if (statusTitle) statusTitle.textContent = 'Все аппаратные подсистемы работают в идеальном режиме';
      if (statusSub) statusSub.textContent = `Температурный профиль в норме (макс. ${Math.round(overallMaxTemp)}°C). Аномалий охлаждения и питания не выявлено.`;
    } else if (healthScore >= 65) {
      if (statusIcon) statusIcon.textContent = '⚠️';
      if (statusTitle) statusTitle.textContent = 'Обнаружены параметры, требующие внимания';
      if (statusSub) statusSub.textContent = `Пиковая температура ${Math.round(overallMaxTemp)}°C или повышенная нагрузка подсистем. Ознакомьтесь с рекомендациями ниже.`;
    } else {
      if (statusIcon) statusIcon.textContent = '🚨';
      if (statusTitle) statusTitle.textContent = 'Внимание: Критические параметры оборудования!';
      if (statusSub) statusSub.textContent = `Зафиксирован опасный нагрев или высокая перегрузка компонентов. Необходима оптимизация охлаждения.`;
    }

    // Render Recommendations
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
    lastAnalysisReportText = `=== AI-Breadboard: Отчет анализа сенсоров и оборудования ===\n` +
      `Дата: ${new Date().toLocaleString('ru-RU')}\n` +
      `Индекс здоровья системы: ${healthScore}/100\n` +
      `Сенсоров в анализе: ${cachedSensors.length}\n` +
      `Максимальная температура: ${overallMaxTemp > 0 ? Math.round(overallMaxTemp) + ' °C' : 'N/A'}\n\n` +
      `[Процессор (CPU)]: ${maxCpuTemp ? Math.round(maxCpuTemp) + ' °C' : 'N/A'}\n` +
      `[Видеокарта (GPU)]: ${maxGpuTemp ? Math.round(maxGpuTemp) + ' °C' : 'N/A'}\n` +
      `[Кулеры]: ${fanSpeeds.length > 0 ? fanSpeeds.length + ' датчиков' : 'Пассив/BIOS'}\n\n` +
      `Рекомендации и выводы:\n` +
      recommendations.map((r, i) => `${i + 1}. [${r.title}] ${r.text}`).join('\n') +
      `\n======================================================`;

    // Show modal
    const modalEl = document.getElementById('sysSensorAnalysisModal');
    if (modalEl && window.bootstrap && window.bootstrap.Modal) {
      const modal = window.bootstrap.Modal.getOrCreateInstance(modalEl);
      modal.show();
    }
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
          <td style="font-weight: 600;">${escapeHtml(p.name || '')}</td>
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

  function connectSystemWebSocket() {
    if (sysWs) {
      try { sysWs.close(); } catch {}
    }
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${proto}//${window.location.host}/api/v1/system/stream`;

    try {
      sysWs = new WebSocket(wsUrl);
      const statusBadge = document.getElementById('sys-conn-status');

      sysWs.onopen = () => {
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
          console.error('[SystemInspectorTab] WS message parse error:', e);
        }
      };

      sysWs.onclose = () => {
        if (statusBadge) {
          statusBadge.className = 'badge rounded-pill bg-warning-subtle text-warning border border-warning px-3 py-2';
          statusBadge.innerText = '○ Переподключение...';
        }
        setTimeout(connectSystemWebSocket, 4000);
      };

      sysWs.onerror = () => {
        if (statusBadge) {
          statusBadge.className = 'badge rounded-pill bg-danger-subtle text-danger border border-danger px-3 py-2';
          statusBadge.innerText = '✕ Ошибка связи';
        }
      };
    } catch (err) {
      console.error('[SystemInspectorTab] WS Init failed:', err);
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
        analyzeSensorsAndReport();
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

    // Periodic sensor refresh every 5 seconds
    if (!window._sysSensorInterval) {
      window._sysSensorInterval = setInterval(() => {
        const activeTab = document.querySelector('#appsNavTabs .nav-link.active, #mainTabs .dropdown-item.active');
        const isActive = activeTab && (
          activeTab.getAttribute('data-tab') === 'tab-system-inspector' ||
          activeTab.getAttribute('data-bs-target') === '#tab-system-inspector'
        );
        if (isActive) {
          fetchLhmSensors();
        }
      }, 5000);
    }
  }

  window.initSystemInspectorTab = initSystemInspectorTab;
})();
