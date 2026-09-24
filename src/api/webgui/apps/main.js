/**
 * apps/main.js — оркестратор страницы /tc (tc.ps1)
 * Архитектура: UI_ARCHITECTURE.md
 */

import { setupGlobalApi, setupThemeAndLang } from './modules/init-interface.js';
import { fetchAppsStatus, updateModelBadge } from './modules/status-manager.js';
import { APP_TAB_DEFS } from './modules/tabs-config.js';
import { applyTranslations } from '../js/i18n.js';
import { switchTab, loadTab, setupTabClicks } from '../js/tab-core.js';

// Глобальный экспорт
window.switchTab = switchTab;
window.switchToTab = switchTab;

// Карта: tabId → пути (из tabs-config, не генерируем)
const TAB_PATHS = Object.fromEntries(
  APP_TAB_DEFS.map(d => [d.tabId, { html: d.html, js: d.js }])
);

// Lazy-загрузка: вкладка грузится только при первом открытии
const loadedTabs = new Set();

async function lazyLoad(tabId) {
  const normId = tabId.startsWith('tab-') ? tabId : `tab-${tabId}`;
  if (loadedTabs.has(normId)) return;
  const paths = TAB_PATHS[normId];
  if (!paths) return;
  loadedTabs.add(normId);
  const v = Date.now();
  const name = normId.replace(/^tab-/, '');
  await loadTab(name, `${paths.html}?v=${v}`, `${paths.js}?v=${v}`);
  applyTranslations();
}

const _switchTab = switchTab;
export async function switchAppTab(tabId) {
  if (!tabId) return;
  const normId = tabId.startsWith('tab-') ? tabId : `tab-${tabId}`;
  await lazyLoad(normId);
  _switchTab(normId);
}
window.switchTab = switchAppTab;
window.switchToTab = switchAppTab;

// ── МЕНЮ ─────────────────────────────────────────────────────────────────────

/**
 * Создает DOM-элемент иконки для кнопок и редактора (поддерживает bi-* и эмодзи)
 * @param {string} iconStr
 * @param {string} defaultIcon
 * @returns {HTMLElement}
 */
function createIconElement(iconStr, defaultIcon = '📄') {
  const icon = iconStr || defaultIcon;
  if (/^bi-[a-z0-9-]+$/.test(icon) || icon.startsWith('bi-')) {
    const i = document.createElement('i');
    i.className = `bi ${icon}`;
    return i;
  }
  const span = document.createElement('span');
  span.textContent = icon;
  return span;
}

/**
 * Обработчик прямого запуска программ (например R-Studio)
 * @param {Object} item
 * @param {HTMLElement} [iconEl]
 */
async function executeLaunchItem(item, iconEl = null) {
  const origContent = iconEl ? iconEl.innerHTML : '';
  if (iconEl) iconEl.innerHTML = '⏳';
  try {
    const res = await fetch('/api/recovery/launch', { method: 'POST' });
    const data = await res.json();
    if (res.ok && data.success) {
      if (window.toast) {
        window.toast.success('R-Studio запущена', data.message || 'Программа восстановления файлов запущена');
      }
    } else {
      if (window.toast) {
        window.toast.error('Ошибка запуска', data.detail || 'Не удалось запустить программу');
      }
    }
  } catch (err) {
    if (window.toast) {
      window.toast.error('Ошибка связи', err.message);
    }
  } finally {
    if (iconEl) iconEl.innerHTML = origContent;
  }
}

function getMenuTarget() {
  const p = location.pathname.toLowerCase();
  if (p.startsWith('/su') || location.search.includes('target=su')) {
    return 'su';
  }
  return 'tc';
}

async function buildMenu(appsMap = {}, customCfg = null) {
  let cfg = customCfg;
  const target = getMenuTarget();
  if (!cfg) {
    try {
      const r = await fetch(`/api/menu/config?target=${target}&t=${Date.now()}`);
      if (r.ok) {
        cfg = await r.json();
      }
    } catch (e) {
      console.warn(`Не удалось загрузить /api/menu/config?target=${target}, пробуем статический файл`, e);
    }
  }

  if (!cfg) {
    try {
      const staticFile = target === 'su' ? 'su_menu_config.json' : 'tc_menu_config.json';
      const r = await fetch(`/html/config_menues/${staticFile}?t=${Date.now()}`);
      if (r.ok) {
        cfg = await r.json();
      }
    } catch (e) {
      console.error('Ошибка загрузки статического файла конфигурации меню', e);
    }
  }

  if (!cfg || !cfg.menu) return null;

  const enabled = item => appsMap[item.id]?.enabled !== false;
  const sorted = arr => [...arr]
    .filter(x => x.visible !== false && enabled(x))
    .sort((a, b) => (a.order || 0) - (b.order || 0));

  // Верхнее меню
  const topEl = document.querySelector('.main-nav-container .d-flex.gap-1.flex-wrap');
  if (topEl) {
    topEl.innerHTML = '';
    sorted(cfg.menu.topButtons || []).forEach(item => {
      const btn = document.createElement('button');
      btn.className = 'btn btn-sm btn-outline-primary d-flex align-items-center gap-1.5 py-1 px-2 rounded';
      btn.type = 'button';
      btn.title = item.label;

      const iconEl = createIconElement(item.icon, 'bi-app');
      const labelSpan = document.createElement('span');
      labelSpan.className = 'd-none d-sm-inline';
      labelSpan.textContent = item.label;
      if (item.i18n) labelSpan.dataset.i18n = item.i18n;

      btn.append(iconEl, labelSpan);

      if (item.id === 'file_recovery' || item.action === 'launch') {
        btn.dataset.action = 'launch';
        btn.onclick = async (e) => {
          e.preventDefault();
          e.stopPropagation();
          await executeLaunchItem(item, iconEl);
        };
      } else {
        btn.dataset.tab = item.tab;
      }

      topEl.appendChild(btn);
    });
  }

  // Боковое меню
  const navEl = document.getElementById('appsNavTabs');
  if (navEl) {
    navEl.innerHTML = '';
    sorted(cfg.menu.sidebarItems || []).forEach(item => {
      const btn = document.createElement('button');
      btn.className = 'list-group-item list-group-item-action d-flex align-items-center gap-2 py-2 px-3';
      btn.type = 'button';

      const iconEl = createIconElement(item.icon, '📄');
      iconEl.classList.add('fs-6');
      const label = document.createElement('span');
      label.className = 'fw-medium';
      label.textContent = item.label;
      if (item.i18n) label.dataset.i18n = item.i18n;

      btn.append(iconEl, label);

      if (item.id === 'file_recovery' || item.action === 'launch') {
        btn.dataset.action = 'launch';
        btn.title = 'Запуск программы восстановления файлов (R-Studio)';
        btn.onclick = async (e) => {
          e.preventDefault();
          e.stopPropagation();
          await executeLaunchItem(item, iconEl);
        };
      } else {
        btn.dataset.tab = item.tab;
      }

      navEl.appendChild(btn);
    });
  }

  // Обновление активного состояния кнопок вкладок
  const activePane = document.querySelector('#mainTabContent .tab-pane.active') || document.querySelector('.tab-pane.active');
  const activeTabId = activePane ? activePane.id : null;
  if (activeTabId) {
    document.querySelectorAll('[data-tab]').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.tab === activeTabId);
    });
  }

  applyTranslations();
  return cfg;
}

export async function loadRequiredTabs(tabs = []) {
  for (const tab of tabs) {
    await lazyLoad(tab);
  }
}

// ── РЕДАКТОР МЕНЮ ─────────────────────────────────────────────────────────────

function initMenuEditor(cfg, appsMap = {}) {
  const editorBtn = document.getElementById('menu-editor-btn');
  const modal = document.getElementById('menuEditorModal');
  const list = document.getElementById('allMenuEditor');
  const saveBtn = document.getElementById('saveMenuConfig');
  if (!editorBtn || !modal || !list || !cfg) return;

  let currentItems = [];
  let draggedIdx = null;

  function collectInitialItems() {
    return [
      ...(cfg.menu.topButtons || []).map(x => ({ ...x, position: x.visible === false ? 'hidden' : 'top' })),
      ...(cfg.menu.sidebarItems || []).map(x => ({ ...x, position: x.visible === false ? 'hidden' : 'bottom' })),
    ];
  }

  function renderList() {
    list.innerHTML = '';
    const total = currentItems.length;

    currentItems.forEach((item, idx) => {
      const safeId = (item.id || `item_${idx}`).replace(/[^a-zA-Z0-9_-]/g, '');
      const div = document.createElement('div');
      div.className = 'menu-editor-item d-flex align-items-center gap-2 p-2 mb-2 rounded border border-secondary-subtle';
      div.dataset.id = item.id;
      div.dataset.index = idx;
      div.draggable = true;

      // 1. Ручка перетаскивания (Drag Handle)
      const dragHandle = document.createElement('div');
      dragHandle.className = 'drag-handle-container text-muted px-1';
      dragHandle.title = 'Перетащите для изменения порядка';
      dragHandle.innerHTML = '<i class="bi bi-grip-vertical fs-5"></i>';

      // 2. Порядковый номер
      const orderBadge = document.createElement('span');
      orderBadge.className = 'badge bg-secondary-subtle text-light border px-2 py-1';
      orderBadge.textContent = `#${idx + 1}`;
      orderBadge.style.minWidth = '38px';
      orderBadge.style.textAlign = 'center';

      // 3. Иконка элемента
      const iconContainer = document.createElement('div');
      iconContainer.className = 'item-icon d-flex align-items-center justify-content-center px-1 text-center';
      iconContainer.style.minWidth = '30px';
      const iconEl = createIconElement(item.icon, '📄');
      iconContainer.appendChild(iconEl);

      // 4. Информация об элементе (название и вкладка)
      const info = document.createElement('div');
      info.className = 'item-info flex-grow-1 min-w-0 px-1';
      const labelDiv = document.createElement('div');
      labelDiv.className = 'fw-semibold text-truncate small';
      labelDiv.textContent = item.label;
      const tabDiv = document.createElement('div');
      tabDiv.className = 'text-muted text-truncate font-monospace';
      tabDiv.style.fontSize = '0.75rem';
      tabDiv.textContent = item.tab;
      info.append(labelDiv, tabDiv);

      // 4. Слайдер-перетаскиватель порядка и кнопки перемещения
      const orderCtrl = document.createElement('div');
      orderCtrl.className = 'd-flex align-items-center gap-1 me-2';
      orderCtrl.style.width = '160px';
      orderCtrl.style.flexShrink = '0';

      const btnUp = document.createElement('button');
      btnUp.type = 'button';
      btnUp.className = 'btn btn-sm btn-outline-secondary p-0 px-1';
      btnUp.title = 'Переместить выше';
      btnUp.disabled = idx === 0;
      btnUp.innerHTML = '<i class="bi bi-chevron-up"></i>';
      btnUp.addEventListener('click', () => {
        if (idx > 0) {
          const [moved] = currentItems.splice(idx, 1);
          currentItems.splice(idx - 1, 0, moved);
          renderList();
        }
      });

      const slider = document.createElement('input');
      slider.type = 'range';
      slider.className = 'form-range order-slider flex-grow-1 m-0';
      slider.min = '1';
      slider.max = String(total);
      slider.value = String(idx + 1);
      slider.title = `Слайдер порядка: ${idx + 1} из ${total}`;

      slider.addEventListener('input', (e) => {
        const targetIdx = parseInt(e.target.value, 10) - 1;
        if (targetIdx !== idx && targetIdx >= 0 && targetIdx < total) {
          const [moved] = currentItems.splice(idx, 1);
          currentItems.splice(targetIdx, 0, moved);
          renderList();
        }
      });

      const btnDown = document.createElement('button');
      btnDown.type = 'button';
      btnDown.className = 'btn btn-sm btn-outline-secondary p-0 px-1';
      btnDown.title = 'Переместить ниже';
      btnDown.disabled = idx === total - 1;
      btnDown.innerHTML = '<i class="bi bi-chevron-down"></i>';
      btnDown.addEventListener('click', () => {
        if (idx < total - 1) {
          const [moved] = currentItems.splice(idx, 1);
          currentItems.splice(idx + 1, 0, moved);
          renderList();
        }
      });

      orderCtrl.append(btnUp, slider, btnDown);

      // 5. Переключатели позиции (Сверху / Слева / Скрыть)
      const group = document.createElement('div');
      group.className = 'btn-group btn-group-sm flex-shrink-0';
      group.setAttribute('role', 'group');

      [['top', 'Сверху', 'btn-outline-primary'], ['bottom', 'Слева', 'btn-outline-secondary'], ['hidden', 'Скрыть', 'btn-outline-danger']]
        .forEach(([val, text, cls]) => {
          const inp = document.createElement('input');
          inp.type = 'radio'; inp.className = 'btn-check';
          inp.name = `pos-${safeId}`; inp.id = `pos-${val}-${safeId}`; inp.value = val;
          inp.checked = item.position === val;
          inp.addEventListener('change', () => {
            item.position = val;
            item.visible = val !== 'hidden';
          });
          const lbl = document.createElement('label');
          lbl.className = `btn ${cls}`; lbl.setAttribute('for', inp.id); lbl.textContent = text;
          group.append(inp, lbl);
        });

      // 6. Drag & Drop события
      div.addEventListener('dragstart', (e) => {
        draggedIdx = idx;
        div.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', String(idx));
      });

      div.addEventListener('dragend', () => {
        div.classList.remove('dragging');
        document.querySelectorAll('.menu-editor-item').forEach(el => el.classList.remove('drag-over'));
      });

      div.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        div.classList.add('drag-over');
      });

      div.addEventListener('dragleave', () => {
        div.classList.remove('drag-over');
      });

      div.addEventListener('drop', (e) => {
        e.preventDefault();
        div.classList.remove('drag-over');
        if (draggedIdx !== null && draggedIdx !== idx) {
          const [moved] = currentItems.splice(draggedIdx, 1);
          currentItems.splice(idx, 0, moved);
          draggedIdx = null;
          renderList();
        }
      });

      div.append(dragHandle, orderBadge, info, orderCtrl, group);
      list.appendChild(div);
    });

    return currentItems;
  }

  editorBtn.addEventListener('click', () => {
    currentItems = collectInitialItems();
    renderList();
    new bootstrap.Modal(modal).show();
  });

  saveBtn.addEventListener('click', async () => {
    cfg.menu.topButtons = currentItems
      .filter(x => x.position === 'top')
      .map(({ position, ...x }, idx) => ({ ...x, visible: true, order: idx + 1 }));

    cfg.menu.sidebarItems = currentItems
      .filter(x => x.position !== 'top')
      .map(({ position, ...x }, idx) => ({ ...x, visible: position === 'bottom', order: idx + 1 }));

    try {
      const target = getMenuTarget();
      const r = await fetch(`/api/menu/config?target=${target}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(cfg)
      });

      if (!r.ok) {
        throw new Error(r.statusText || `HTTP ${r.status}`);
      }

      // Немедленно переопределяем меню и структуру вкладок в интерфейсе
      await buildMenu(appsMap, cfg);

      const modalInstance = bootstrap.Modal.getInstance(modal);
      if (modalInstance) {
        modalInstance.hide();
      }

      // Проверяем, активна ли ещё текущая вкладка, если нет — переключаемся на первую доступную
      const currentTabEl = document.querySelector('.tab-pane.active');
      const activeTabId = currentTabEl ? currentTabEl.id : '';
      const isStillInMenu = document.querySelector(`[data-tab="${activeTabId}"]`);
      if (!isStillInMenu) {
        const firstVisible = document.querySelector('[data-tab]');
        if (firstVisible?.dataset.tab) {
          await switchAppTab(firstVisible.dataset.tab);
        }
      }
    } catch (e) {
      window.showToast?.('Ошибка при сохранении меню: ' + e.message, 'danger') || alert('Ошибка при сохранении меню: ' + e.message);
    }
  });
}

// ── INIT ─────────────────────────────────────────────────────────────────────

async function init() {
  setupGlobalApi();
  await setupThemeAndLang();

  if (location.pathname.startsWith('/tc'))
    document.title = 'AI Breadboard — Test Computer (/tc)';

  // Единый обработчик кликов
  setupTabClicks();

  // Статус + бейдж модели
  const statusData = await fetchAppsStatus();
  await updateModelBadge(statusData);
  const appsMap = statusData?.apps || {};

  // Меню из конфига
  const cfg = await buildMenu(appsMap).catch(() => null);
  initMenuEditor(cfg, appsMap);

  applyTranslations();

  // Активировать вкладку по hash, defaultTab из конфига или первую доступную
  const hash = location.hash.replace('#', '');
  const defaultTab = cfg?.settings?.defaultTab;
  const first = document.querySelector('#appsNavTabs [data-tab]') || document.querySelector('[data-tab]');
  const initialTab = hash || (defaultTab && document.querySelector(`[data-tab="${defaultTab}"]`) ? defaultTab : first?.dataset.tab || 'tab-chat');
  await switchAppTab(initialTab);
}

document.readyState === 'loading'
  ? document.addEventListener('DOMContentLoaded', init)
  : init();
