/**
 * =============================================================================
 * Process Name: Maintenance & Recovery Web Controller
 * =============================================================================
 * Description:
 *   Клиентский контроллер вкладки «Обслуживание и восстановление». Управляет
 *   очисткой временных файлов, проверкой системных файлов (SFC/DISM) и
 *   точками восстановления Windows.
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: src.api.webinterface.maintenance_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * =============================================================================
 */

(function () {
  'use strict';

  let isInitialized = false;

  function formatRestorePointType(rawType) {
    if (!rawType) return 'System Checkpoint';
    const s = String(rawType).toUpperCase();
    if (s.includes('APPLICATION_INSTALL') || s === '0') return 'App Install';
    if (s.includes('APPLICATION_UNINSTALL') || s === '1') return 'App Uninstall';
    if (s.includes('DEVICE_DRIVER') || s === '10') return 'Driver Install';
    if (s.includes('MODIFY_SETTINGS') || s === '12') return 'Settings Change';
    if (s.includes('CANCELLED') || s === '13') return 'Cancelled Op';
    if (s.includes('WINDOWS_UPDATE') || s === '17') return 'Windows Update';
    return s.replace(/_/g, ' ');
  }

  function formatRestoreTime(rawTime) {
    if (!rawTime) return '-';
    const s = String(rawTime).trim();
    if (s.length >= 14 && /^\d{14}/.test(s)) {
      return `${s.slice(0, 4)}-${s.slice(4, 6)}-${s.slice(6, 8)} ${s.slice(8, 10)}:${s.slice(10, 12)}:${s.slice(12, 14)}`;
    }
    return s;
  }

  async function fetchMaintenanceStatus() {
    try {
      const res = await fetch('/api/system-control/status');
      if (!res.ok) return;
      const data = await res.json();
      const disk = data.disk || {};

      const cleanEstimateTxt = document.getElementById('mtn-clean-estimate-txt');
      if (cleanEstimateTxt) {
        const cleanMb = disk.cleanup_estimate?.total_cleanable_mb || 0;
        cleanEstimateTxt.innerText = `Очищаемый объём: ~${cleanMb} MB`;
      }

      await fetchRestorePoints();
    } catch (e) {
      console.error('[MaintenanceTab] Failed to fetch maintenance status:', e);
    }
  }

  async function fetchRestorePoints() {
    try {
      const res = await fetch('/api/system-control/restore-points');
      if (!res.ok) return;
      const data = await res.json();
      const points = data.restore_points || [];

      const tbody = document.getElementById('mtn-restore-tbody');
      if (!tbody) return;

      if (points.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted p-3">Точки восстановления не найдены. Нажмите "Создать точку восстановления".</td></tr>';
        return;
      }

      tbody.innerHTML = points.map((p, idx) => {
        const typeBadge = formatRestorePointType(p.restore_point_type);
        const timeFormatted = formatRestoreTime(p.creation_time);
        return `
          <tr class="mtn-restore-row" data-idx="${idx}" style="cursor: pointer;" title="Нажмите для детальной информации">
            <td class="font-monospace text-info fw-bold">#${p.sequence_number}</td>
            <td class="fw-semibold text-white">${p.description}</td>
            <td><span class="badge bg-secondary text-light px-2 py-1 font-monospace" style="font-size: 0.75rem;">${typeBadge}</span></td>
            <td class="small text-light font-monospace">${timeFormatted}</td>
          </tr>
        `;
      }).join('');

      tbody.querySelectorAll('.mtn-restore-row').forEach(row => {
        row.onclick = () => {
          const idx = parseInt(row.getAttribute('data-idx'), 10);
          const p = points[idx];
          if (!p) return;
          if (window.AITableModal) {
            window.AITableModal.show({
              icon: '🔄',
              title: `Точка восстановления #${p.sequence_number}`,
              subtitle: p.description,
              tableType: 'generic',
              badges: [
                { text: p.restore_point_type || 'System Checkpoint', class: 'badge bg-info text-dark' }
              ],
              metadata: [
                { label: 'Номер', value: String(p.sequence_number) },
                { label: 'Описание', value: p.description },
                { label: 'Тип', value: p.restore_point_type },
                { label: 'Дата создания', value: p.creation_time }
              ],
              rawTitle: 'Метаданные точки восстановления',
              rawContent: JSON.stringify(p, null, 2)
            });
          }
        };
      });
    } catch (e) {
      console.error('[MaintenanceTab] Failed to fetch restore points:', e);
    }
  }

  async function loadRestorePolicyModal() {
    try {
      const res = await fetch('/api/system-control/restore-points/config');
      if (!res.ok) return;
      const data = await res.json();

      const storageSel = document.getElementById('mtn-policy-storage-size');
      const triggerSel = document.getElementById('mtn-policy-trigger');
      const timeInput = document.getElementById('mtn-policy-time');
      const timeWrapper = document.getElementById('mtn-policy-time-wrapper');
      const freqChk = document.getElementById('mtn-policy-freq-limit');
      const maxPtsSel = document.getElementById('mtn-policy-max-points');
      const autoPruneChk = document.getElementById('mtn-policy-auto-prune');
      const storageBar = document.getElementById('mtn-policy-storage-bar');
      const storageLabel = document.getElementById('mtn-policy-storage-label');

      if (storageSel && data.max_storage_size) storageSel.value = data.max_storage_size;
      if (triggerSel && data.schedule_trigger) {
        triggerSel.value = data.schedule_trigger;
        if (timeWrapper) timeWrapper.style.display = (data.schedule_trigger === 'daily' || data.schedule_trigger === 'weekly') ? 'block' : 'none';
      }
      if (timeInput && data.schedule_time) timeInput.value = data.schedule_time;
      if (freqChk) freqChk.checked = data.frequency_limit_minutes === 0;
      if (maxPtsSel && data.max_points) maxPtsSel.value = String(data.max_points);
      if (autoPruneChk && data.auto_prune !== undefined) autoPruneChk.checked = Boolean(data.auto_prune);

      const st = data.storage_info || {};
      if (storageBar && storageLabel) {
        const pct = st.usage_percent || 0;
        const usedGb = (st.used_bytes ? (st.used_bytes / (1024 ** 3)).toFixed(2) : '0.00');
        const maxGb = (st.max_bytes ? (st.max_bytes / (1024 ** 3)).toFixed(2) : '0.00');
        storageBar.style.width = `${Math.min(pct, 100)}%`;
        storageBar.className = pct > 85 ? 'progress-bar bg-danger' : (pct > 60 ? 'progress-bar bg-warning' : 'progress-bar bg-info');
        storageLabel.innerHTML = `<span>Занято: ${usedGb} GB (${pct}%)</span><span>Лимит: ${maxGb} GB</span>`;
      }

      if (triggerSel) {
        triggerSel.onchange = () => {
          if (timeWrapper) timeWrapper.style.display = (triggerSel.value === 'daily' || triggerSel.value === 'weekly') ? 'block' : 'none';
        };
      }

      const modalEl = document.getElementById('modal-mtn-restore-config');
      if (modalEl && window.bootstrap?.Modal) {
        const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
        modal.show();
      }
    } catch (e) {
      console.error('[MaintenanceTab] Failed to load restore policy config:', e);
    }
  }

  async function saveRestorePolicy() {
    const saveBtn = document.getElementById('btn-mtn-save-restore-policy');
    const storageSel = document.getElementById('mtn-policy-storage-size');
    const triggerSel = document.getElementById('mtn-policy-trigger');
    const timeInput = document.getElementById('mtn-policy-time');
    const freqChk = document.getElementById('mtn-policy-freq-limit');
    const maxPtsSel = document.getElementById('mtn-policy-max-points');
    const autoPruneChk = document.getElementById('mtn-policy-auto-prune');

    const payload = {
      max_storage_size: storageSel ? storageSel.value : '10%',
      schedule_trigger: triggerSel ? triggerSel.value : 'daily',
      schedule_time: timeInput ? timeInput.value : '03:00',
      frequency_limit_minutes: freqChk && freqChk.checked ? 0 : 1440,
      max_points: maxPtsSel ? parseInt(maxPtsSel.value, 10) : 5,
      auto_prune: autoPruneChk ? autoPruneChk.checked : true,
    };

    if (saveBtn) {
      saveBtn.disabled = true;
      saveBtn.innerText = 'Сохранение...';
    }

    try {
      const res = await fetch('/api/system-control/restore-points/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const d = await res.json();
      window.showToast?.(d.message || 'Политика успешно сохранена', d.success ? 'success' : 'danger') || alert(d.message || 'Политика сохранена');
      const modalEl = document.getElementById('modal-mtn-restore-config');
      if (modalEl && window.bootstrap?.Modal) {
        const modal = bootstrap.Modal.getInstance(modalEl);
        modal?.hide();
      }
      await fetchRestorePoints();
    } catch (e) {
      console.error('[MaintenanceTab] Failed to save restore policy:', e);
      alert('Ошибка сохранения политики: ' + e);
    } finally {
      if (saveBtn) {
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<i class="bi bi-check-lg me-1"></i> Сохранить и применить';
      }
    }
  }

  async function pruneRestorePointsNow() {
    const maxPtsSel = document.getElementById('mtn-policy-max-points');
    const keep = maxPtsSel ? parseInt(maxPtsSel.value, 10) : 5;
    if (!confirm(`Выполнить ротацию точек восстановления и оставить только ${keep} последних?`)) {
      return;
    }
    try {
      const res = await fetch('/api/system-control/restore-points/prune', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ keep_count: keep })
      });
      const d = await res.json();
      window.showToast?.(d.message || 'Ротация выполнена', 'info') || alert(d.message || 'Ротация выполнена');
      await fetchRestorePoints();
    } catch (e) {
      console.error('[MaintenanceTab] Failed to prune restore points:', e);
    }
  }

  function initMaintenanceTab() {
    console.log('[MaintenanceTab] Initializing Maintenance & Recovery tab...');
    fetchMaintenanceStatus();

    if (!isInitialized) {
      const refreshBtn = document.getElementById('btn-mtn-refresh');
      const cleanBtn = document.getElementById('btn-mtn-action-clean');
      const sfcBtn = document.getElementById('btn-mtn-action-sfc');
      const dismBtn = document.getElementById('btn-mtn-action-dism');
      const createRestoreBtn = document.getElementById('btn-mtn-create-restore');
      const configRestoreBtn = document.getElementById('btn-mtn-config-restore');
      const savePolicyBtn = document.getElementById('btn-mtn-save-restore-policy');
      const pruneNowBtn = document.getElementById('btn-mtn-policy-prune-now');

      if (refreshBtn) refreshBtn.onclick = () => fetchMaintenanceStatus();

      if (cleanBtn) {
        cleanBtn.onclick = async () => {
          if (confirm('Выполнить безопасную очистку временных директорий и кэша обновлений?')) {
            cleanBtn.disabled = true;
            await fetch('/api/system-control/maintenance/cleanup', { method: 'POST' });
            cleanBtn.disabled = false;
            fetchMaintenanceStatus();
          }
        };
      }

      if (sfcBtn) {
        sfcBtn.onclick = async () => {
          sfcBtn.disabled = true;
          sfcBtn.innerText = 'Сканирование...';
          const res = await fetch('/api/system-control/maintenance/sfc', { method: 'POST' });
          const d = await res.json();
          window.showToast?.(d.message || 'Проверка SFC завершена', d.status === 'error' ? 'danger' : 'success') || alert(d.message || 'Проверка SFC завершена');
          sfcBtn.disabled = false;
          sfcBtn.innerHTML = '<i class="bi bi-search me-1"></i> Запустить проверку SFC';
        };
      }

      if (dismBtn) {
        dismBtn.onclick = async () => {
          dismBtn.disabled = true;
          dismBtn.innerText = 'Проверка...';
          const res = await fetch('/api/system-control/maintenance/dism', { method: 'POST' });
          const d = await res.json();
          window.showToast?.(d.message || 'Проверка DISM завершена', d.status === 'error' ? 'danger' : 'success') || alert(d.message || 'Проверка DISM завершена');
          dismBtn.disabled = false;
          dismBtn.innerHTML = '<i class="bi bi-activity me-1"></i> Проверить хранилище DISM';
        };
      }

      if (createRestoreBtn) {
        createRestoreBtn.onclick = async () => {
          const desc = prompt('Введите описание точки восстановления:', 'Точка восстановления системы');
          if (desc) {
            createRestoreBtn.disabled = true;
            const res = await fetch('/api/system-control/restore-points', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ description: desc })
            });
            const d = await res.json();
            window.showToast?.(d.message || 'Точка восстановления создана.', d.status === 'error' ? 'danger' : 'success') || alert(d.message || 'Точка восстановления создана.');
            createRestoreBtn.disabled = false;
            fetchRestorePoints();
          }
        };
      }

      if (configRestoreBtn) configRestoreBtn.onclick = loadRestorePolicyModal;
      if (savePolicyBtn) savePolicyBtn.onclick = saveRestorePolicy;
      if (pruneNowBtn) pruneNowBtn.onclick = pruneRestorePointsNow;

      isInitialized = true;
    }
  }

  window.initMaintenanceTab = initMaintenanceTab;
})();
