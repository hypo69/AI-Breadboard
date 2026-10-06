/**
 * =============================================================================
 * Process Name: Windows Post-Install Wizard - Main Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт мастера первичной настройки Windows (Post-Install Wizard).
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/html/post_install_wizard_tab/main.js?v=20261006_v1" type="module"></script>
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: windows/api/webgui/post_install_wizard_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-06 05:55:00
 * =============================================================================
 */

(function () {
  'use strict';

  let isInitialized = false;
  let activeProfileSteps = [];

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
   * Проверка прав администратора и обновление бейджа.
   */
  async function fetchElevationStatus() {
    try {
      const res = await fetch('/api/system-control/status');
      if (!res.ok) return;
      const data = await res.json();
      const elevBadge = document.getElementById('piw-elevation-badge');
      if (elevBadge) {
        if (data.is_elevated) {
          elevBadge.className = 'badge rounded-pill bg-success-subtle text-success border border-success px-3 py-2';
          elevBadge.innerHTML = '🛡️ Режим: Администратор (Полный доступ)';
        } else {
          elevBadge.className = 'badge rounded-pill bg-warning-subtle text-warning border border-warning px-3 py-2';
          elevBadge.innerHTML = '👁️ Режим: Обычный пользователь (Ограничено)';
        }
      }
    } catch (e) {
      console.warn('[PostInstallWizard] Ошибка проверки прав:', e);
    }
  }

  /**
   * Загрузка профилей и шагов мастера.
   */
  async function loadWizardProfiles() {
    try {
      const res = await fetch('/api/system-control/profiles');
      if (!res.ok) return;
      const data = await res.json();
      const profiles = data.profiles || [];
      const currentProf = profiles[0];
      if (currentProf && currentProf.steps) {
        activeProfileSteps = currentProf.steps;
        renderWizardSteps(currentProf.steps);
      }
    } catch (e) {
      console.error('[PostInstallWizard] Ошибка загрузки профилей:', e);
    }
  }

  /**
   * Отрисовка элементов шагов мастера.
   *
   * @param {Array} steps - Список шагов.
   */
  function renderWizardSteps(steps) {
    const container = document.getElementById('piw-wizard-steps-container');
    if (!container) return;

    if (!steps || steps.length === 0) {
      container.innerHTML = '<div class="text-center text-muted p-3">Нет доступных шагов для выбранного профиля.</div>';
      return;
    }

    container.innerHTML = steps.map(step => {
      const badgeClass = step.status === 'SUCCESS' ? 'bg-success' : step.status === 'RUNNING' ? 'bg-info' : step.status === 'FAILED' ? 'bg-danger' : 'bg-secondary';
      return `
      <div class="piw-step-item d-flex justify-content-between align-items-center flex-wrap gap-2" id="piw-step-${step.id}">
        <div class="d-flex align-items-start gap-3">
          <input class="form-check-input mt-1 piw-step-checkbox" type="checkbox" value="${step.id}" ${step.enabled ? 'checked' : ''} style="cursor: pointer;">
          <div>
            <div class="fw-bold text-white d-flex align-items-center gap-2">
              <span>${escapeHtml(step.title)}</span>
              ${step.requires_elevation ? '<span class="badge bg-warning-subtle text-warning border border-warning px-1.5 py-0.5" style="font-size: 0.65rem;">Admin</span>' : ''}
            </div>
            <div class="small text-muted">${escapeHtml(step.description)}</div>
          </div>
        </div>
        <div class="d-flex align-items-center gap-2">
          <span class="badge ${badgeClass} font-monospace px-2 py-1" id="piw-step-status-${step.id}" style="font-size: 0.72rem;">${step.status || 'READY'}</span>
          <button class="btn btn-sm btn-outline-info rounded-pill px-3 piw-btn-step-run" data-step-id="${step.id}">
            <i class="bi bi-play-circle me-1"></i> Выполнить
          </button>
        </div>
      </div>
    `;
    }).join('');

    // Привязка обработчиков одиночного запуска шагов
    container.querySelectorAll('.piw-btn-step-run').forEach(btn => {
      btn.onclick = async () => {
        const stepId = btn.getAttribute('data-step-id');
        await executeWizardSteps([stepId]);
      };
    });
  }

  /**
   * Выполнение списка шагов мастера.
   *
   * @param {Array<string>} stepIds - Идентификаторы шагов.
   */
  async function executeWizardSteps(stepIds) {
    if (!stepIds || stepIds.length === 0) {
      if (window.toast) window.toast.warning('Мастер настройки', 'Выберите хотя бы один шаг для выполнения.');
      return;
    }

    const summaryEl = document.getElementById('piw-status-summary');
    if (summaryEl) summaryEl.innerText = `Выполняется ${stepIds.length} шагов...`;

    stepIds.forEach(sid => {
      const badge = document.getElementById(`piw-step-status-${sid}`);
      if (badge) {
        badge.className = 'badge bg-info font-monospace px-2 py-1';
        badge.innerText = 'RUNNING';
      }
    });

    try {
      const profileSelect = document.getElementById('piw-profile-select');
      const profileId = profileSelect ? profileSelect.value : 'post_install';

      const res = await fetch('/api/system-control/profiles/apply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profile_id: profileId, step_ids: stepIds }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      stepIds.forEach(sid => {
        const badge = document.getElementById(`piw-step-status-${sid}`);
        if (badge) {
          badge.className = 'badge bg-success font-monospace px-2 py-1';
          badge.innerText = 'SUCCESS';
        }
      });

      if (summaryEl) summaryEl.innerText = 'Профиль успешно применен.';
      if (window.toast) window.toast.success('Мастер настройки', data.message || 'Шаги успешно применены.');
    } catch (e) {
      console.error('[PostInstallWizard] Ошибка выполнения шагов:', e);
      stepIds.forEach(sid => {
        const badge = document.getElementById(`piw-step-status-${sid}`);
        if (badge) {
          badge.className = 'badge bg-danger font-monospace px-2 py-1';
          badge.innerText = 'FAILED';
        }
      });
      if (summaryEl) summaryEl.innerText = `Ошибка применения: ${e.message}`;
      if (window.toast) window.toast.error('Мастер настройки', `Ошибка: ${e.message}`);
    }
  }

  /**
   * Инициализация вкладки Post-Install Wizard.
   */
  function initPostInstallWizardTab() {
    fetchElevationStatus();
    loadWizardProfiles();

    if (isInitialized) return;
    isInitialized = true;

    const refreshBtn = document.getElementById('btn-piw-refresh');
    if (refreshBtn) {
      refreshBtn.onclick = () => {
        fetchElevationStatus();
        loadWizardProfiles();
      };
    }

    const applyProfileBtn = document.getElementById('btn-piw-apply-profile');
    if (applyProfileBtn) {
      applyProfileBtn.onclick = async () => {
        const checkedBoxes = document.querySelectorAll('.piw-step-checkbox:checked');
        const stepIds = Array.from(checkedBoxes).map(cb => cb.value);
        await executeWizardSteps(stepIds);
      };
    }

    const selectAllBtn = document.getElementById('btn-piw-select-all');
    if (selectAllBtn) {
      selectAllBtn.onclick = () => {
        document.querySelectorAll('.piw-step-checkbox').forEach(cb => { cb.checked = true; });
      };
    }

    const deselectAllBtn = document.getElementById('btn-piw-deselect-all');
    if (deselectAllBtn) {
      deselectAllBtn.onclick = () => {
        document.querySelectorAll('.piw-step-checkbox').forEach(cb => { cb.checked = false; });
      };
    }
  }

  window.initPostInstallWizardTab = initPostInstallWizardTab;
})();
