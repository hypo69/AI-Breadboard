/**
 * tab-core.js — Единая система управления вкладками, их жизненным циклом и поллингом.
 * Архитектура: UI_ARCHITECTURE.md
 * 
 * Правило: Только открытая АКТИВНАЯ вкладка выполняет периодические опросы API.
 * При неактивности вкладки или скрытии страницы (visibilitychange) все таймеры засыпают.
 * 
 * Приоритет переключения: кнопки навигации имеют самый высокий приоритет.
 * Если что-то запущено внутри вкладки, переключение происходит немедленно без ожидания.
 */

const OFFCANVAS_IDS = ['leftSideNavOffcanvas', 'appsSideNavOffcanvas'];

let currentActiveTabId = null;
const registeredPollers = new Map();
const processingFlags = new Map(); // хранит флаг isProcessing для каждой вкладки

/**
 * Приводит идентификатор вкладки к стандартному виду 'tab-xxx'.
 * @param {string} tabId 
 * @returns {string}
 */
export function normalizeTabId(tabId) {
  if (!tabId) return '';
  return tabId.startsWith('tab-') ? tabId : `tab-${tabId}`;
}

/**
 * Проверяет, активна ли сейчас вкладка (видна пользователю и вкладка браузера в фокусе).
 * @param {string} tabId 
 * @returns {boolean}
 */
export function isTabActive(tabId) {
  const normId = normalizeTabId(tabId);
  if (typeof document !== 'undefined' && document.hidden) {
    return false;
  }
  if (currentActiveTabId) {
    return currentActiveTabId === normId;
  }
  const pane = document.getElementById(normId);
  return pane ? pane.classList.contains('active') : false;
}

/**
 * Останавливает таймер конкретного опросника.
 * @param {Object} poller 
 */
function stopPoller(poller) {
  if (poller.timerId) {
    clearInterval(poller.timerId);
    poller.timerId = null;
  }
}

/**
 * Запускает таймер опросника, если вкладка активна и опрос разрешён.
 * @param {Object} poller 
 * @param {boolean} immediate - Выполнить ли опрос немедленно перед установкой таймера
 */
function startPoller(poller, immediate = false) {
  stopPoller(poller);
  if (!poller.enabled || !isTabActive(poller.tabId)) return;

  const runTick = async () => {
    if (!poller.enabled || !isTabActive(poller.tabId) || poller.inFlight) return;
    poller.inFlight = true;
    try {
      await poller.pollFn();
    } catch (err) {
      console.warn(`[TabPoller] Ошибка выполнения pollFn для [${poller.id}]:`, err);
    } finally {
      poller.inFlight = false;
    }
  };

  if (immediate) {
    runTick();
  }

  poller.timerId = setInterval(runTick, poller.intervalMs);
}

/**
 * Регистрирует или обновляет периодический опросник (poller) для вкладки.
 * Опросник будет срабатывать ТОЛЬКО тогда, когда вкладка АКТИВНА
 * и документ находится в фокусе (не свёрнут / не скрыт).
 * 
 * @param {string} tabId - ID вкладки (например 'tab-about-system' или 'about-system')
 * @param {Function} pollFn - Функция опроса API
 * @param {number} intervalMs - Интервал опроса в миллисекундах (мин. 1000мс)
 * @param {Object} [options] - Опции: { pollerId, immediate = true, enabled = true }
 * @returns {string} pollerId
 */
export function registerTabPoller(tabId, pollFn, intervalMs = 3000, options = {}) {
  const normTabId = normalizeTabId(tabId);
  const pollerId = options.pollerId || `${normTabId}_default`;

  unregisterTabPoller(pollerId);

  const poller = {
    id: pollerId,
    tabId: normTabId,
    pollFn,
    intervalMs: Math.max(1000, intervalMs),
    enabled: options.enabled !== false,
    timerId: null,
    inFlight: false,
  };

  registeredPollers.set(pollerId, poller);

  if (isTabActive(normTabId) && poller.enabled) {
    startPoller(poller, options.immediate !== false);
  }

  return pollerId;
}

/**
 * Удаляет зарегистрированный опросник по его ID.
 * @param {string} pollerId 
 */
export function unregisterTabPoller(pollerId) {
  if (registeredPollers.has(pollerId)) {
    const poller = registeredPollers.get(pollerId);
    stopPoller(poller);
    registeredPollers.delete(pollerId);
  }
}

/**
 * Удаляет все зарегистрированные опросники для вкладки.
 * @param {string} tabId 
 */
export function unregisterAllTabPollers(tabId) {
  const normTabId = normalizeTabId(tabId);
  for (const [id, poller] of registeredPollers.entries()) {
    if (poller.tabId === normTabId) {
      stopPoller(poller);
      registeredPollers.delete(id);
    }
  }
}

/**
 * Включает или выключает опросник вкладки (например, переключатель Live-режима).
 * @param {string} pollerId 
 * @param {boolean} enabled 
 */
export function setTabPollerEnabled(pollerId, enabled) {
  const poller = registeredPollers.get(pollerId);
  if (!poller) return;
  poller.enabled = !!enabled;
  if (poller.enabled && isTabActive(poller.tabId)) {
    startPoller(poller, true);
  } else {
    stopPoller(poller);
  }
}

/**
 * Переключает активную вкладку и управляет жизненным циклом (активация/деактивация/поллеры).
 * Приоритет: кнопки навигации имеют самый высокий приоритет.
 * Если что-то запущено внутри вкладки, переключение происходит немедленно без ожидания.
 * @param {string} tabId 
 */
export function switchTab(tabId) {
  if (!tabId) return;
  const id = normalizeTabId(tabId);
  const prevTabId = currentActiveTabId;

  // Проверяем флаг isProcessing для предыдущей вкладки
  // Если что-то запущено, прерываем без ожидания завершения
  let prevProcessing = false;
  if (prevTabId && prevTabId !== id && processingFlags.has(prevTabId)) {
    prevProcessing = processingFlags.get(prevTabId);
  }

  // 1. Деактивация предыдущей активной вкладки (асинхронно, без ожидания если processing)
  if (prevTabId && prevTabId !== id) {
    for (const poller of registeredPollers.values()) {
      if (poller.tabId === prevTabId) {
        stopPoller(poller);
      }
    }
    
    const prevName = prevTabId.replace(/^tab-/, '').replace(/-([a-z])/g, (_, c) => c.toUpperCase());
    const deactivateFn = window[`deactivate${prevName[0].toUpperCase() + prevName.slice(1)}Tab`];
    
    // Если есть флаг processing, вызываем без ожидания
    if (prevProcessing && typeof deactivateFn === 'function') {
      // Вызываем деактивацию асинхронно, не блокируя переключение
      Promise.resolve().then(() => deactivateFn().catch(() => {})).catch(() => {});
    } else if (typeof deactivateFn === 'function') {
      deactivateFn();
    }
    
    document.dispatchEvent(new CustomEvent('tab:deactivated', { detail: { tabId: prevTabId, name: prevName } }));
  }

  currentActiveTabId = id;

  // 2. Активная кнопка меню
  document.querySelectorAll('[data-tab]').forEach(btn =>
    btn.classList.toggle('active', btn.dataset.tab === id)
  );

  // 3. Видимая панель
  document.querySelectorAll('#mainTabContent .tab-pane').forEach(pane => {
    pane.classList.toggle('show', pane.id === id);
    pane.classList.toggle('active', pane.id === id);
  });

  // 4. Бейдж заголовка
  const badge = document.getElementById('active-tab-title-badge');
  const activeBtn = document.querySelector(`[data-tab="${id}"]`);
  if (badge && activeBtn) badge.innerHTML = activeBtn.innerHTML;

  // 5. Закрыть offcanvas меню
  OFFCANVAS_IDS.forEach(ocId => {
    const el = document.getElementById(ocId);
    if (el) bootstrap.Offcanvas.getInstance(el)?.hide();
  });

  // 6. Обновить хэш URL
  history.replaceState(null, null, `#${id}`);

  // 7. Запуск опросников новой активной вкладки
  for (const poller of registeredPollers.values()) {
    if (poller.tabId === id && poller.enabled) {
      startPoller(poller, true);
    }
  }

  // 8. Lifecycle hooks
  const name = id.replace(/^tab-/, '').replace(/-([a-z])/g, (_, c) => c.toUpperCase());
  
  // Инициализация новой вкладки
  const initFn = window[`init${name[0].toUpperCase() + name.slice(1)}Tab`];
  if (typeof initFn === 'function') {
    initFn();
  }
  
  const activateFn = window[`activate${name[0].toUpperCase() + name.slice(1)}Tab`];
  if (typeof activateFn === 'function') {
    activateFn();
  }
  
  document.dispatchEvent(new CustomEvent('tab:activated', { detail: { tabId: id, name } }));
}

/**
 * Загружает разметку и скрипт вкладки по требованию (Lazy Load).
 * @param {string} tabName 
 * @param {string} htmlUrl 
 * @param {string} jsUrl 
 */
export async function loadTab(tabName, htmlUrl, jsUrl) {
  const container = document.getElementById(`tab-${tabName}`);
  if (!container) return;
  try {
    const r = await fetch(htmlUrl);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    container.innerHTML = await r.text();
    await new Promise(resolve => {
      const s = document.createElement('script');
      s.src = jsUrl;
      s.onload = s.onerror = resolve;
      document.body.appendChild(s);
    });
    const name = tabName.replace(/-([a-z])/g, (_, c) => c.toUpperCase());
    window[`init${name[0].toUpperCase() + name.slice(1)}Tab`]?.();
  } catch (e) {
    container.innerHTML = `<div class="alert alert-danger">Ошибка загрузки ${tabName}: ${e.message}</div>`;
  }
}

/**
 * Устанавливает единый слушатель кликов по элементам с data-tab.
 */
export function setupTabClicks() {
  document.addEventListener('click', e => {
    const btn = e.target.closest('button[data-tab], a[data-tab]');
    if (btn && btn.dataset.tab) {
      if (typeof window.switchTab === 'function') {
        window.switchTab(btn.dataset.tab);
      } else {
        switchTab(btn.dataset.tab);
      }
    }
  });
}

// Слушатель изменения видимости вкладки браузера
if (typeof document !== 'undefined') {
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      // Страница скрыта: останавливаем все активные опросники
      for (const poller of registeredPollers.values()) {
        stopPoller(poller);
      }
    } else {
      // Страница снова видна: возобновляем опросники ТОЛЬКО для активной вкладки
      if (currentActiveTabId) {
        for (const poller of registeredPollers.values()) {
          if (poller.tabId === currentActiveTabId && poller.enabled) {
            startPoller(poller, true);
          }
        }
      }
    }
  });
}

/**
 * Устанавливает флаг processing для вкладки (используется при длительных операциях).
 * Позволяет переключать вкладки без ожидания завершения операции.
 * @param {string} tabId - ID вкладки
 * @param {boolean} isProcessing - флаг состояния
 */
export function setTabProcessing(tabId, isProcessing) {
  const normId = normalizeTabId(tabId);
  processingFlags.set(normId, !!isProcessing);
}

/**
 * Сбрасывает флаг processing для вкладки.
 * @param {string} tabId - ID вкладки
 */
export function resetTabProcessing(tabId) {
  const normId = normalizeTabId(tabId);
  processingFlags.delete(normId);
}

/**
 * Экспорт в глобальный контекст window для совместимости с инлайн-скриптами и вкладками
 */
if (typeof window !== 'undefined') {
  window.switchTab = switchTab;
  window.switchToTab = switchTab;
  window.loadTab = loadTab;
  window.setupTabClicks = setupTabClicks;
  window.normalizeTabId = normalizeTabId;
  window.isTabActive = isTabActive;
  window.registerTabPoller = registerTabPoller;
  window.unregisterTabPoller = unregisterTabPoller;
  window.unregisterAllTabPollers = unregisterAllTabPollers;
  window.setTabPollerEnabled = setTabPollerEnabled;
  window.setTabProcessing = setTabProcessing;
  window.resetTabProcessing = resetTabProcessing;
}
