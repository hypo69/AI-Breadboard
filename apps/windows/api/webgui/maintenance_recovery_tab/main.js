/**
 * =============================================================================
 * Process Name: Windows Maintenance & Recovery - Main Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт обслуживания и восстановления Windows (Maintenance & Recovery).
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/html/maintenance_recovery_tab/main.js?v=20261006_v1" type="module"></script>
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: windows/api/webgui/maintenance_recovery_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-06 05:55:00
 * =============================================================================
 */

(function () {
  'use strict';

  let isInitialized = false;

  /**
   * Экранирование HTML-символов для защиты от XSS.
   *
   * @param {string} str - Исходная строка.
   * @returns {string} Экранированная строка.
   */
  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  /**
   * Форматирование типа точки восстановления.
   *
   * @param {string|number} rawType - Сырой тип.
   * @returns {string} Читаемый тип.
   */
  function formatRestorePointType(rawType) {
    if (!rawType) return 'Системный снимок';
    const s = String(rawType).toUpperCase();
    if (s.includes('APPLICATION_INSTALL') || s === '0') return 'Установка ПО';
    if (s.includes('APPLICATION_UNINSTALL') || s === '1') return 'Удаление ПО';
    if (s.includes('DEVICE_DRIVER') || s === '10') return 'Драйвер устройства';
    if (s.includes('MODIFY_SETTINGS') || s === '12') return 'Изменение настроек';
    if (s.includes('CANCELLED') || s === '13') return 'Отмена операции';
    if (s.includes('WINDOWS_UPDATE') || s === '17') return 'Windows Update';
    return s.replace(/_/g, ' ');
  }

  /**
   * Форматирование времени точки восстановления.
   *
   * @param {string} rawTime - Сырое время (YYYYMMDDHHmmss).
   * @returns {string} Форматированное время.
   */
  function formatRestoreTime(rawTime) {
    if (!rawTime) return '-';
    const s = String(rawTime).trim();
    if (s.length >= 14 && /^\d{14}/.test(s)) {
      return `${s.slice(0, 4)}-${s.slice(4, 6)}-${s.slice(6, 8)} ${s.slice(8, 10)}:${s.slice(10, 12)}:${s.slice(12, 14)}`;
    }
    return s;
  }

  /**
   * Получение статуса обслуживания и прав доступа.
   */
  async function fetchMaintStatus() {
    try {
      const res = await fetch('/api/system-control/status');
      if (!res.ok) return;
      const data = await res.json();

      const elevBadge = document.getElementById('maint-elevation-badge');
      if (elevBadge) {
        if (data.is_elevated) {
          elevBadge.className = 'badge rounded-pill bg-success-subtle text-success border border-success px-3 py-2';
          elevBadge.innerHTML = '🛡️ Режим: Администратор (Полный доступ)';
        } else {
          elevBadge.className = 'badge rounded-pill bg-warning-subtle text-warning border border-warning px-3 py-2';
          elevBadge.innerHTML = '👁️ Режим: Обычный пользователь (Ограничено)';
        }
      }

      const cleanEstimateTxt = document.getElementById('maint-clean-estimate-txt');
      if (cleanEstimateTxt) {
        const cleanMb = data.disk?.cleanup_estimate?.total_cleanable_mb || 0;
        cleanEstimateTxt.innerText = `Доступно к очистке: ~${cleanMb} MB`;
      }
    } catch (e) {
      console.warn('[MaintenanceRecovery] Ошибка получения статуса:', e);
    }
  }

  /**
   * Загрузка списка точек восстановления Windows.
   */
  async function fetchRestorePoints() {
    try {
      const res = await fetch('/api/system-control/restore-points');
      if (!res.ok) return;
      const data = await res.json();
      const points = data.restore_points || [];

      const tbody = document.getElementById('maint-restore-tbody');
      if (tbody) {
        if (points.length === 0) {
          tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted p-3">Точки восстановления не найдены. Нажмите «Создать точку восстановления» для фиксации состояния.</td></tr>';
          return;
        }
        tbody.innerHTML = points.map((p, idx) => {
          const typeBadge = formatRestorePointType(p.restore_point_type);
          const timeFormatted = formatRestoreTime(p.creation_time);
          return `
          <tr class="maint-restore-row" data-idx="${idx}" style="cursor: pointer;" title="Нажмите для анализа точки восстановления">
            <td class="font-monospace text-info fw-bold">#${p.sequence_number}</td>
            <td class="fw-semibold text-white">${escapeHtml(p.description)}</td>
            <td><span class="badge bg-secondary text-light px-2 py-1 font-monospace" style="font-size: 0.75rem;">${escapeHtml(typeBadge)}</span></td>
            <td class="small text-light font-monospace">${escapeHtml(timeFormatted)}</td>
          </tr>
        `;
        }).join('');

        tbody.querySelectorAll('.maint-restore-row').forEach(row => {
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
      }
    } catch (e) {
      console.error('[MaintenanceRecovery] Ошибка загрузки точек восстановления:', e);
    }
  }

  /**
   * Открытие модального окна настройки политик теневого хранилища (VSS).
   */
  async function openRestoreConfigModal() {
    try {
      const res = await fetch('/api/system-control/restore-points/config');
      if (res.ok) {
        const cfg = await res.json();
        const sizeSelect = document.getElementById('maint-policy-storage-size');
        if (sizeSelect && cfg.max_storage_size) sizeSelect.value = cfg.max_storage_size;

        const trigSelect = document.getElementById('maint-policy-trigger');
        if (trigSelect && cfg.schedule_trigger) trigSelect.value = cfg.schedule_trigger;

        const timeInput = document.getElementById('maint-policy-time');
        if (timeInput && cfg.schedule_time) timeInput.value = cfg.schedule_time;

        const ptsSelect = document.getElementById('maint-policy-max-points');
        if (ptsSelect && cfg.max_points) ptsSelect.value = String(cfg.max_points);

        const pruneSwitch = document.getElementById('maint-policy-auto-prune');
        if (pruneSwitch && typeof cfg.auto_prune === 'boolean') pruneSwitch.checked = cfg.auto_prune;

        const freqSwitch = document.getElementById('maint-policy-freq-limit');
        if (freqSwitch && typeof cfg.frequency_limit_minutes === 'number') freqSwitch.checked = cfg.frequency_limit_minutes === 0;

        const shadow = cfg.shadow_storage || {};
        const usedGb = shadow.allocated_space_gb || 0;
        const maxGb = shadow.max_space_gb || 1;
        const pct = shadow.percent_used || (maxGb > 0 ? Math.min(100, Math.round((usedGb / maxGb) * 100)) : 0);

        const bar = document.getElementById('maint-policy-storage-bar');
        if (bar) {
          bar.style.width = `${pct}%`;
          bar.className = `progress-bar ${pct > 80 ? 'bg-danger' : pct > 50 ? 'bg-warning' : 'bg-info'}`;
        }
        const lbl = document.getElementById('maint-policy-storage-label');
        if (lbl) {
          lbl.innerHTML = `<span>Занято: ${usedGb} GB (${pct}%)</span><span>Лимит: ${maxGb} GB</span>`;
        }
      }
    } catch (e) {
      console.warn('[MaintenanceRecovery] Ошибка получения конфигурации VSS:', e);
    }

    const modalEl = document.getElementById('modal-maint-restore-config');
    if (modalEl && window.bootstrap?.Modal) {
      const bsModal = bootstrap.Modal.getOrCreateInstance(modalEl);
      bsModal.show();
    }
  }

  /**
   * Сохранение политик теневого хранилища и точек восстановления.
   */
  async function saveRestoreConfig() {
    const saveBtn = document.getElementById('btn-maint-save-restore-policy');
    const origText = saveBtn ? saveBtn.innerHTML : '';
    if (saveBtn) {
      saveBtn.disabled = true;
      saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Сохранение...';
    }

    try {
      const sizeSelect = document.getElementById('maint-policy-storage-size');
      const trigSelect = document.getElementById('maint-policy-trigger');
      const timeInput = document.getElementById('maint-policy-time');
      const ptsSelect = document.getElementById('maint-policy-max-points');
      const pruneSwitch = document.getElementById('maint-policy-auto-prune');
      const freqSwitch = document.getElementById('maint-policy-freq-limit');

      const payload = {
        max_storage_size: sizeSelect ? sizeSelect.value : '10%',
        schedule_trigger: trigSelect ? trigSelect.value : 'daily',
        schedule_time: timeInput ? timeInput.value : '03:00',
        max_points: ptsSelect ? parseInt(ptsSelect.value, 10) : 5,
        auto_prune: pruneSwitch ? pruneSwitch.checked : true,
        frequency_limit_minutes: freqSwitch && freqSwitch.checked ? 0 : 1440
      };

      const res = await fetch('/api/system-control/restore-points/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      if (!res.ok || (data.success === false)) {
        throw new Error(data.message || 'Ошибка сохранения политики');
      }

      if (window.toast) {
        window.toast.success('Политики VSS', 'Политики и лимиты дискового пространства успешно обновлены.');
      }

      const modalEl = document.getElementById('modal-maint-restore-config');
      if (modalEl && window.bootstrap?.Modal) {
        bootstrap.Modal.getInstance(modalEl)?.hide();
      }

      fetchRestorePoints();
      fetchMaintStatus();
    } catch (e) {
      console.error('[MaintenanceRecovery] Ошибка сохранения политики:', e);
      if (window.toast) window.toast.error('Политики VSS', e.message);
    } finally {
      if (saveBtn) {
        saveBtn.disabled = false;
        saveBtn.innerHTML = origText;
      }
    }
  }

  /**
   * Принудительная очистка избыточных точек восстановления.
   */
  async function pruneRestorePoints() {
    const ptsSelect = document.getElementById('maint-policy-max-points');
    const keepCount = ptsSelect ? parseInt(ptsSelect.value, 10) : 5;

    if (!confirm(`Вы действительно хотите удалить старые точки восстановления, оставив ${keepCount} последних?`)) {
      return;
    }

    try {
      const res = await fetch('/api/system-control/restore-points/prune', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ keep_count: keepCount })
      });
      const data = await res.json();
      if (window.toast) window.toast.success('Ротация VSS', data.message || `Оставлено ${keepCount} последних точек.`);
      fetchRestorePoints();
    } catch (e) {
      if (window.toast) window.toast.error('Ротация VSS', e.message);
    }
  }

  /**
   * Инициализация вкладки Maintenance & Recovery.
   */
  function initMaintenanceRecoveryTab() {
    fetchMaintStatus();
    fetchRestorePoints();

    if (window.registerTabPoller) {
      window.registerTabPoller('tab-maintenance-recovery_status', fetchMaintStatus, 5000);
    }

    if (isInitialized) return;
    isInitialized = true;

    const refreshBtn = document.getElementById('btn-maint-refresh');
    if (refreshBtn) {
      refreshBtn.onclick = () => {
        fetchMaintStatus();
        fetchRestorePoints();
      };
    }

    // Быстрая очистка кэшей
    const cleanBtn = document.getElementById('btn-maint-action-clean');
    if (cleanBtn) {
      cleanBtn.onclick = async () => {
        const orig = cleanBtn.innerHTML;
        cleanBtn.disabled = true;
        cleanBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Очистка...';
        try {
          let res = await fetch('/api/system-control/actions/cleanup', { method: 'POST' });
          if (!res.ok) {
            res = await fetch('/api/system-control/maintenance/cleanup', { method: 'POST' });
          }
          const data = await res.json();
          if (window.toast) window.toast.success('Очистка диска', data.message || 'Временные файлы успешно удалены.');
          fetchMaintStatus();
        } catch (e) {
          if (window.toast) window.toast.error('Очистка диска', e.message);
        } finally {
          cleanBtn.disabled = false;
          cleanBtn.innerHTML = orig;
        }
      };
    }

    // Запуск проверки SFC
    const sfcBtn = document.getElementById('btn-maint-action-sfc');
    if (sfcBtn) {
      sfcBtn.onclick = async () => {
        const orig = sfcBtn.innerHTML;
        sfcBtn.disabled = true;
        sfcBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Сканирование...';
        try {
          const res = await fetch('/api/system-control/maintenance/sfc', { method: 'POST' });
          const data = await res.json();
          if (window.toast) window.toast.info('Проверка SFC', data.message || 'Сканирование целостности файлов завершено.');
        } catch (e) {
          if (window.toast) window.toast.error('Проверка SFC', e.message);
        } finally {
          sfcBtn.disabled = false;
          sfcBtn.innerHTML = orig;
        }
      };
    }

    // Запуск проверки DISM
    const dismBtn = document.getElementById('btn-maint-action-dism');
    if (dismBtn) {
      dismBtn.onclick = async () => {
        const orig = dismBtn.innerHTML;
        dismBtn.disabled = true;
        dismBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Проверка DISM...';
        try {
          const res = await fetch('/api/system-control/maintenance/dism', { method: 'POST' });
          const data = await res.json();
          if (window.toast) window.toast.info('Проверка DISM', data.message || 'Диагностика Component Store завершена.');
        } catch (e) {
          if (window.toast) window.toast.error('Проверка DISM', e.message);
        } finally {
          dismBtn.disabled = false;
          dismBtn.innerHTML = orig;
        }
      };
    }

    // Создание точки восстановления
    const createRestoreBtn = document.getElementById('btn-maint-create-restore');
    if (createRestoreBtn) {
      createRestoreBtn.onclick = async () => {
        const desc = prompt('Введите описание для новой точки восстановления:', 'Ручной снимок системы перед изменениями');
        if (!desc) return;
        const orig = createRestoreBtn.innerHTML;
        createRestoreBtn.disabled = true;
        createRestoreBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Создание...';
        try {
          const res = await fetch('/api/system-control/restore-points', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ description: desc, restore_point_type: 'MODIFY_SETTINGS' })
          });
          const data = await res.json();
          if (!res.ok) throw new Error(data.detail || data.message || 'Ошибка создания точки');
          if (window.toast) window.toast.success('Точка восстановления', 'Точка восстановления успешно создана.');
          fetchRestorePoints();
        } catch (e) {
          if (window.toast) window.toast.error('Точка восстановления', e.message);
        } finally {
          createRestoreBtn.disabled = false;
          createRestoreBtn.innerHTML = orig;
        }
      };
    }

    // Открытие модального окна политик
    const cfgRestoreBtn = document.getElementById('btn-maint-config-restore');
    if (cfgRestoreBtn) {
      cfgRestoreBtn.onclick = () => {
        openRestoreConfigModal();
      };
    }

    // Сохранение политик
    const savePolicyBtn = document.getElementById('btn-maint-save-restore-policy');
    if (savePolicyBtn) {
      savePolicyBtn.onclick = () => {
        saveRestoreConfig();
      };
    }

    // Очистить избыточные точки
    const pruneBtn = document.getElementById('btn-maint-policy-prune-now');
    if (pruneBtn) {
      pruneBtn.onclick = () => {
        pruneRestorePoints();
      };
    }
  }

  window.initMaintenanceRecoveryTab = initMaintenanceRecoveryTab;
})();
