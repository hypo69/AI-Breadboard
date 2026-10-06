/**
 * =============================================================================
 * Process Name: Windows Web Interface - Focus Settings Tab Script
 * =============================================================================
 * Description:
 *   Клиентский контроллер вкладки управления сессиями фокусировки (Focus Sessions),
 *   режимом «Не беспокоить» (Do Not Disturb), подавлением бейджей и мигания панели задач.
 *
 * Usage Examples:
 *   JavaScript:
 *     initFocusSettingsTab();
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: windows/api/webgui/focus_settings_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-06 19:35:00
 * =============================================================================
 */

let durationMinutes = 30;
let isFocusActive = false;
let timerInterval = null;
let remainingSeconds = 0;

export async function initFocusSettingsTab() {
  console.log('[FocusSettingsTab] Инициализация вкладки Focus Settings...');
  bindEventListeners();
  await loadFocusState();
}

/**
 * Подключение обработчиков событий элементов управления интерфейса.
 */
function bindEventListeners() {
  // Кнопки регулировки длительности сессии
  const btnMinus = document.getElementById('btn-duration-minus');
  const btnPlus = document.getElementById('btn-duration-plus');
  if (btnMinus) {
    btnMinus.onclick = () => changeDuration(-5);
  }
  if (btnPlus) {
    btnPlus.onclick = () => changeDuration(5);
  }

  // Кнопка старта / остановки сессии
  const btnToggle = document.getElementById('btn-toggle-focus');
  if (btnToggle) {
    btnToggle.onclick = toggleFocusSession;
  }

  // Сохранение настроек
  const btnSave = document.getElementById('btn-save-focus-settings');
  if (btnSave) {
    btnSave.onclick = saveFocusSettings;
  }

  // Запуск нативных окон Windows
  const btnWinSettings = document.getElementById('btn-open-win-settings');
  if (btnWinSettings) {
    btnWinSettings.onclick = openWindowsSettings;
  }

  const btnClockApp = document.getElementById('btn-open-clock-app');
  if (btnClockApp) {
    btnClockApp.onclick = openClockApp;
  }

  // Переход к смежной вкладке управления панелью задач
  const btnTaskbar = document.getElementById('btn-goto-taskbar-tab');
  if (btnTaskbar) {
    btnTaskbar.onclick = () => {
      if (typeof window.switchTab === 'function') {
        window.switchTab('tab-taskbar-controller');
      }
    };
  }
}

/**
 * Изменение длительности сессии с шагом в 5 минут (диапазон 5..240 мин).
 * @param {number} delta Шаг изменения в минутах.
 */
function changeDuration(delta) {
  if (isFocusActive) return;
  durationMinutes = Math.max(5, Math.min(240, durationMinutes + delta));
  updateDurationLabel();
}

/**
 * Обновление текстовой метки длительности.
 */
function updateDurationLabel() {
  const lbl = document.getElementById('lbl-duration');
  if (lbl) {
    lbl.textContent = `${durationMinutes} mins`;
  }
}

/**
 * Загрузка актуального состояния из REST API.
 */
async function loadFocusState() {
  try {
    const res = await fetch('/api/windows/focus/state');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderState(data);
  } catch (err) {
    console.warn('[FocusSettingsTab] Ошибка загрузки состояния focus:', err);
  }
}

/**
 * Отрисовка полученного состояния в интерфейсе.
 * @param {object} state Объект FocusSessionStateDTO.
 */
function renderState(state) {
  isFocusActive = Boolean(state.is_active);
  durationMinutes = state.session_duration_minutes || durationMinutes;
  remainingSeconds = state.remaining_seconds || 0;

  updateDurationLabel();

  // Обновление чекбоксов
  const s = state.settings || {};
  setCheckbox('chk-clock-timer', s.show_timer_in_clock_app ?? true);
  setCheckbox('chk-hide-badges', s.hide_badges_on_taskbar ?? true);
  setCheckbox('chk-hide-flashing', s.hide_flashing_on_taskbar ?? true);
  setCheckbox('chk-turn-on-dnd', s.turn_on_do_not_disturb ?? true);

  // Обновление бейджа и кнопок
  const badge = document.getElementById('focus-status-badge');
  const btnToggle = document.getElementById('btn-toggle-focus');
  const btnIcon = document.getElementById('btn-focus-icon');
  const btnText = document.getElementById('btn-focus-text');
  const hint = document.getElementById('focus-session-hint');
  const countdownBox = document.getElementById('focus-countdown-box');

  if (isFocusActive) {
    if (badge) {
      badge.className = 'badge bg-success small fs-6';
      badge.textContent = 'Сессия активна';
    }
    if (btnToggle) {
      btnToggle.className = 'btn btn-danger px-4 py-2 d-flex align-items-center gap-2 shadow-sm';
    }
    if (btnIcon) btnIcon.className = 'bi bi-stop-fill';
    if (btnText) btnText.textContent = 'Stop focus session';
    if (hint) hint.textContent = 'Сессия фокусировки активна. Отвлекающие факторы заблокированы.';
    if (countdownBox) countdownBox.classList.remove('d-none');

    startLocalCountdown();
  } else {
    if (badge) {
      badge.className = 'badge bg-secondary-subtle text-secondary border border-secondary-subtle small fs-6';
      badge.textContent = 'Не активна';
    }
    if (btnToggle) {
      btnToggle.className = 'btn btn-primary px-4 py-2 d-flex align-items-center gap-2 shadow-sm';
    }
    if (btnIcon) btnIcon.className = 'bi bi-play-fill';
    if (btnText) btnText.textContent = 'Start focus session';
    if (hint) hint.textContent = 'Готов к запуску сессии без отвлечений';
    if (countdownBox) countdownBox.classList.add('d-none');

    stopLocalCountdown();
  }
}

/**
 * Локальный таймер обратного отсчета для плавного отображения секунд.
 */
function startLocalCountdown() {
  stopLocalCountdown();
  updateCountdownDisplay();
  timerInterval = setInterval(() => {
    if (remainingSeconds > 0) {
      remainingSeconds -= 1;
      updateCountdownDisplay();
    } else {
      stopLocalCountdown();
      loadFocusState();
    }
  }, 1000);
}

function stopLocalCountdown() {
  if (timerInterval) {
    clearInterval(timerInterval);
    timerInterval = null;
  }
}

function updateCountdownDisplay() {
  const timerText = document.getElementById('focus-timer-text');
  if (timerText) {
    const mins = Math.floor(remainingSeconds / 60);
    const secs = remainingSeconds % 60;
    timerText.textContent = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  }
}

/**
 * Переключение состояния сессии фокусировки (Старт / Стоп).
 */
async function toggleFocusSession() {
  const btnToggle = document.getElementById('btn-toggle-focus');
  if (btnToggle) btnToggle.disabled = true;

  try {
    // Сохраняем текущие выбранные чекбоксы перед стартом
    await saveFocusSettings();

    const endpoint = isFocusActive ? '/api/windows/focus/session/stop' : `/api/windows/focus/session/start?duration_minutes=${durationMinutes}`;
    const res = await fetch(endpoint, { method: 'POST' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderState(data);
  } catch (err) {
    console.error('[FocusSettingsTab] Ошибка переключения сессии:', err);
    alert(`Ошибка управления сессией фокусировки: ${err.message}`);
  } finally {
    if (btnToggle) btnToggle.disabled = false;
  }
}

/**
 * Сохранение конфигурации в постоянные настройки.
 */
async function saveFocusSettings() {
  const settings = {
    session_duration_minutes: durationMinutes,
    show_timer_in_clock_app: getCheckbox('chk-clock-timer'),
    hide_badges_on_taskbar: getCheckbox('chk-hide-badges'),
    hide_flashing_on_taskbar: getCheckbox('chk-hide-flashing'),
    turn_on_do_not_disturb: getCheckbox('chk-turn-on-dnd')
  };

  try {
    const res = await fetch('/api/windows/focus/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings)
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const syncLabel = document.getElementById('focus-last-synced');
    if (syncLabel) {
      syncLabel.textContent = `Сохранено в ${new Date().toLocaleTimeString()}`;
    }
  } catch (err) {
    console.warn('[FocusSettingsTab] Ошибка сохранения настроек:', err);
  }
}

/**
 * Вызов нативных параметров Windows.
 */
async function openWindowsSettings() {
  try {
    await fetch('/api/windows/focus/open-settings', { method: 'POST' });
  } catch (err) {
    console.warn('[FocusSettingsTab] Ошибка вызова параметров Windows:', err);
  }
}

/**
 * Вызов нативного приложения Windows Clock.
 */
async function openClockApp() {
  try {
    await fetch('/api/windows/focus/open-clock', { method: 'POST' });
  } catch (err) {
    console.warn('[FocusSettingsTab] Ошибка вызова Windows Clock:', err);
  }
}

function getCheckbox(id) {
  const el = document.getElementById(id);
  return el ? Boolean(el.checked) : false;
}

function setCheckbox(id, value) {
  const el = document.getElementById(id);
  if (el) el.checked = Boolean(value);
}

// Экспорт для глобального использования
window.initFocusSettingsTab = initFocusSettingsTab;

// Автоинициализация при загрузке содержимого вкладки
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initFocusSettingsTab);
} else {
  initFocusSettingsTab();
}
