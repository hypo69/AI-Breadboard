/**
 * =============================================================================
 * Process Name: Windows Apps - Main Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля main.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/webgui/apps/main.js?v=20261001_v1" type="module"></script>
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: windows/api/webgui/apps
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-08 04:24:00
 * =============================================================================
 */

/**
 * apps/main.js — оркестратор страницы /tc (tc.ps1)
 * Архитектура: UI_ARCHITECTURE.md
 */

import { setupGlobalApi, setupThemeAndLang } from './modules/init-interface.js';
import { fetchAppsStatus, updateModelBadge } from './modules/status-manager.js';
import { initModelTester, sendModelPing } from './modules/model-tester.js';
import { APP_TAB_DEFS } from './modules/tabs-config.js';
import { applyTranslations } from '../js/i18n.js';
import { switchTab, loadTab, setupTabClicks } from '../js/tab-core.js';

// Глобальный экспорт
window.switchTab = switchTab;
window.switchToTab = switchTab;
window.sendModelPing = sendModelPing;
window.initModelTester = initModelTester;

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
  const v = Date.now();
  const name = normId.replace(/^tab-/, '');
  const cleanHtml = paths.html ? (paths.html.includes('?') ? paths.html.split('?')[0] : paths.html) : '';
  const cleanJs = paths.js ? (paths.js.includes('?') ? paths.js.split('?')[0] : paths.js) : '';
  try {
    await loadTab(name, `${cleanHtml}?v=${v}`, cleanJs ? `${cleanJs}?v=${v}` : '');
    loadedTabs.add(normId);
    applyTranslations();
  } catch (err) {
    console.error(`[apps/main.js] Ошибка загрузки вкладки ${normId}:`, err);
    loadedTabs.delete(normId);
    if (window.toast) {
      window.toast.error('Ошибка загрузки', `Не удалось загрузить раздел ${name}: ${err.message}`);
    }
  }
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
      const r = await fetch(`/api/v1/menu/config?target=${target}&t=${Date.now()}`);
      if (r.ok) {
        cfg = await r.json();
      }
    } catch (e) {
      console.warn(`Не удалось загрузить /api/v1/menu/config?target=${target}, пробуем статический файл`, e);
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
  const activePane = document.querySelector('#mainTabContent > .tab-pane.active') || document.querySelector('.tab-pane.active');
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
  let draggedGlobalIdx = null;

  function collectInitialItems() {
    return [
      ...(cfg.menu.topButtons || []).map(x => ({ ...x, position: x.position || (x.visible === false ? 'hidden' : 'top') })),
      ...(cfg.menu.sidebarItems || []).map(x => ({ ...x, position: x.position || (x.visible === false ? 'hidden' : 'bottom') })),
    ];
  }

  function renderList() {
    list.innerHTML = '';

    const GROUPS = [
      {
        key: 'top',
        title: 'Сверху (Верхняя панель)',
        icon: 'bi-layout-text-window-reverse',
        badgeCls: 'bg-primary text-white',
        borderCls: 'border-primary-subtle'
      },
      {
        key: 'bottom',
        title: 'Сбоку (Боковое меню)',
        icon: 'bi-layout-sidebar-inset',
        badgeCls: 'bg-info text-dark',
        borderCls: 'border-info-subtle'
      },
      {
        key: 'hidden',
        title: 'Скрыто (Не отображаются)',
        icon: 'bi-eye-slash',
        badgeCls: 'bg-secondary text-white',
        borderCls: 'border-secondary-subtle'
      }
    ];

    GROUPS.forEach(grp => {
      const groupItems = currentItems.filter(x => x.position === grp.key);
      const grpTotal = groupItems.length;

      const section = document.createElement('div');
      section.className = `menu-group-section mb-3 p-2 rounded border ${grp.borderCls}`;
      section.style.background = 'var(--surface-1, rgba(255,255,255,0.03))';

      // Заголовок группы
      const header = document.createElement('div');
      header.className = 'd-flex align-items-center justify-content-between mb-2 px-1 pb-1 border-bottom border-secondary-subtle';
      header.innerHTML = `
        <span class="fw-bold d-flex align-items-center gap-2 small">
          <i class="bi ${grp.icon}"></i> ${grp.title}
        </span>
        <span class="badge ${grp.badgeCls} rounded-pill px-2 py-1">${grpTotal}</span>
      `;
      section.appendChild(header);

      const itemsContainer = document.createElement('div');
      itemsContainer.className = 'menu-group-items d-flex flex-column gap-2';
      itemsContainer.dataset.group = grp.key;

      if (grpTotal === 0) {
        const empty = document.createElement('div');
        empty.className = 'text-muted small text-center py-2 fst-italic';
        empty.textContent = 'Нет элементов в этой группе';
        itemsContainer.appendChild(empty);
      } else {
        groupItems.forEach((item, grpIdx) => {
          const globalIdx = currentItems.indexOf(item);
          const safeId = (item.id || `item_${globalIdx}`).replace(/[^a-zA-Z0-9_-]/g, '');

          const div = document.createElement('div');
          div.className = 'menu-editor-item d-flex align-items-center gap-2 p-2 rounded border border-secondary-subtle';
          div.dataset.id = item.id || `item_${globalIdx}`;
          div.dataset.globalIndex = globalIdx;
          div.dataset.groupIndex = grpIdx;
          div.draggable = true;

          // 1. Ручка перетаскивания (Drag Handle)
          const dragHandle = document.createElement('div');
          dragHandle.className = 'drag-handle-container text-muted px-1';
          dragHandle.title = 'Перетащите для изменения порядка';
          dragHandle.style.cursor = 'grab';
          dragHandle.innerHTML = '<i class="bi bi-grip-vertical fs-5"></i>';

          // 2. Порядковый номер в группе
          const orderBadge = document.createElement('span');
          orderBadge.className = 'badge bg-secondary-subtle text-light border px-2 py-1';
          orderBadge.textContent = `#${grpIdx + 1}`;
          orderBadge.style.minWidth = '38px';
          orderBadge.style.textAlign = 'center';

          // 3. Иконка элемента
          const iconContainer = document.createElement('div');
          iconContainer.className = 'item-icon d-flex align-items-center justify-content-center px-1 text-center';
          iconContainer.style.minWidth = '28px';
          const iconEl = createIconElement(item.icon, '📄');
          iconContainer.appendChild(iconEl);

          // 4. Информация об элементе
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

          // 5. Управление порядком внутри группы
          const orderCtrl = document.createElement('div');
          orderCtrl.className = 'd-flex align-items-center gap-1 me-2';
          orderCtrl.style.width = '160px';
          orderCtrl.style.flexShrink = '0';

          const btnUp = document.createElement('button');
          btnUp.type = 'button';
          btnUp.className = 'btn btn-sm btn-outline-secondary p-0 px-1';
          btnUp.title = 'Переместить выше в группе';
          btnUp.disabled = grpIdx === 0;
          btnUp.innerHTML = '<i class="bi bi-chevron-up"></i>';
          btnUp.addEventListener('click', () => {
            if (grpIdx > 0) {
              const prevItem = groupItems[grpIdx - 1];
              const curIdx = currentItems.indexOf(item);
              const targetIdx = currentItems.indexOf(prevItem);
              currentItems.splice(curIdx, 1);
              currentItems.splice(targetIdx, 0, item);
              renderList();
            }
          });

          const slider = document.createElement('input');
          slider.type = 'range';
          slider.className = 'form-range order-slider flex-grow-1 m-0';
          slider.min = '1';
          slider.max = String(grpTotal);
          slider.value = String(grpIdx + 1);
          slider.title = `Позиция в группе: ${grpIdx + 1} из ${grpTotal}`;

          slider.addEventListener('input', (e) => {
            const targetGrpIdx = parseInt(e.target.value, 10) - 1;
            if (targetGrpIdx !== grpIdx && targetGrpIdx >= 0 && targetGrpIdx < grpTotal) {
              const targetItem = groupItems[targetGrpIdx];
              const curIdx = currentItems.indexOf(item);
              const targetIdx = currentItems.indexOf(targetItem);
              currentItems.splice(curIdx, 1);
              currentItems.splice(targetIdx, 0, item);
              renderList();
            }
          });

          const btnDown = document.createElement('button');
          btnDown.type = 'button';
          btnDown.className = 'btn btn-sm btn-outline-secondary p-0 px-1';
          btnDown.title = 'Переместить ниже в группе';
          btnDown.disabled = grpIdx === grpTotal - 1;
          btnDown.innerHTML = '<i class="bi bi-chevron-down"></i>';
          btnDown.addEventListener('click', () => {
            if (grpIdx < grpTotal - 1) {
              const nextItem = groupItems[grpIdx + 1];
              const curIdx = currentItems.indexOf(item);
              const targetIdx = currentItems.indexOf(nextItem);
              currentItems.splice(curIdx, 1);
              currentItems.splice(targetIdx, 0, item);
              renderList();
            }
          });

          orderCtrl.append(btnUp, slider, btnDown);

          // 6. Переключатели позиции (Сверху / Сбоку / Скрыть)
          const group = document.createElement('div');
          group.className = 'btn-group btn-group-sm flex-shrink-0';
          group.setAttribute('role', 'group');

          const radioName = `pos_grp_${globalIdx}_${safeId}`;
          [
            ['top', 'Сверху', 'btn-outline-primary'],
            ['bottom', 'Сбоку', 'btn-outline-info'],
            ['hidden', 'Скрыть', 'btn-outline-danger']
          ].forEach(([val, text, cls]) => {
            const inp = document.createElement('input');
            inp.type = 'radio';
            inp.className = 'btn-check';
            inp.autocomplete = 'off';
            inp.name = radioName;
            inp.id = `pos_${val}_${globalIdx}_${safeId}`;
            inp.value = val;
            inp.checked = (item.position === val);
            inp.addEventListener('change', () => {
              if (inp.checked && item.position !== val) {
                item.position = val;
                item.visible = (val !== 'hidden');
                // Перемещаем элемент в конец новой группы в currentItems
                const curIdx = currentItems.indexOf(item);
                currentItems.splice(curIdx, 1);
                const lastOfGroup = currentItems.filter(x => x.position === val).pop();
                if (lastOfGroup) {
                  const lastIdx = currentItems.indexOf(lastOfGroup);
                  currentItems.splice(lastIdx + 1, 0, item);
                } else {
                  currentItems.push(item);
                }
                renderList();
              }
            });

            const lbl = document.createElement('label');
            lbl.className = `btn ${cls}`;
            lbl.setAttribute('for', inp.id);
            lbl.textContent = text;
            group.append(inp, lbl);
          });

          // Drag & Drop события
          div.addEventListener('dragstart', (e) => {
            draggedGlobalIdx = globalIdx;
            div.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('text/plain', String(globalIdx));
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
            const fromGlobalIdx = parseInt(e.dataTransfer.getData('text/plain'), 10);
            if (!isNaN(fromGlobalIdx) && fromGlobalIdx !== globalIdx) {
              const [moved] = currentItems.splice(fromGlobalIdx, 1);
              moved.position = grp.key;
              moved.visible = (grp.key !== 'hidden');
              currentItems.splice(globalIdx, 0, moved);
              renderList();
            }
          });

          div.append(dragHandle, orderBadge, iconContainer, info, orderCtrl, group);
          itemsContainer.appendChild(div);
        });
      }

      section.appendChild(itemsContainer);
      list.appendChild(section);
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
      const r = await fetch(`/api/v1/menu/config?target=${target}`, {
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
      const currentTabEl = document.querySelector('#mainTabContent > .tab-pane.active') || document.querySelector('.tab-pane.active');
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

  // Инициализация быстрой проверки доступности модели
  initModelTester();

  // Меню из конфига
  const cfg = await buildMenu(appsMap).catch(() => null);
  initMenuEditor(cfg, appsMap);

  applyTranslations();

  // Активировать вкладку по hash, defaultTab из конфига или первую доступную
  const hash = location.hash.replace('#', '');
  const defaultTab = cfg?.settings?.defaultTab;
  const first = document.querySelector('#appsNavTabs [data-tab]') || document.querySelector('[data-tab]');
  const initialTab = hash || (defaultTab && document.querySelector(`[data-tab="${defaultTab}"]`) ? defaultTab : first?.dataset.tab || 'tab-about-system');
  await switchAppTab(initialTab);
}

document.readyState === 'loading'
  ? document.addEventListener('DOMContentLoaded', init)
  : init();
