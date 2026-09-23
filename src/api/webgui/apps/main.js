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

const loadedTabs = new Set();

/**
 * Загружает необходимые вкладки HTML/JS
 */
async function loadRequiredTabs() {
  const v = Date.now();
  await Promise.all(
    Array.from(document.querySelectorAll('[data-tab]')).map(btn => {
      const tabId = btn.dataset.tab;
      if (!tabId || loadedTabs.has(tabId)) return Promise.resolve();
      loadedTabs.add(tabId);
      const paths = TAB_PATHS[tabId];
      if (!paths) return Promise.resolve();
      const name = tabId.replace(/^tab-/, '');
      return loadTab(name, `${paths.html}?v=${v}`, `${paths.js}?v=${v}`);
    })
  );
}

// ── МЕНЮ ─────────────────────────────────────────────────────────────────────

async function buildMenu(appsMap = {}, customCfg = null) {
  let cfg = customCfg;
  if (!cfg) {
    try {
      const r = await fetch(`/api/menu/config?t=${Date.now()}`);
      if (r.ok) {
        cfg = await r.json();
      }
    } catch (e) {
      console.warn('Не удалось загрузить /api/menu/config, пробуем статический файл', e);
    }
  }

  if (!cfg) {
    try {
      const r = await fetch(`/html/config/tc_menu_config.json?t=${Date.now()}`);
      if (r.ok) {
        cfg = await r.json();
      }
    } catch (e) {
      console.error('Ошибка загрузки tc_menu_config.json', e);
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
      const safeIcon = /^bi-[a-z0-9-]+$/.test(item.icon) ? item.icon : 'bi-app';
      const btn = document.createElement('button');
      btn.className = 'btn btn-sm btn-outline-primary d-flex align-items-center gap-1 py-1 px-2 rounded';
      btn.type = 'button';
      btn.dataset.tab = item.tab;
      btn.title = item.label;
      btn.innerHTML = `<i class="bi ${safeIcon}"></i><span class="d-none d-sm-inline">${item.label}</span>`;
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
      btn.dataset.tab = item.tab;
      if (item.i18n) btn.dataset.i18n = item.i18n;
      const icon = document.createElement('span');
      icon.className = 'fs-6';
      icon.textContent = item.icon || '📄';
      const label = document.createElement('span');
      label.className = 'fw-medium';
      label.textContent = item.label;
      btn.append(icon, label);
      navEl.appendChild(btn);
    });
  }

  applyTranslations();
  return cfg;
}

// ── РЕДАКТОР МЕНЮ ─────────────────────────────────────────────────────────────

function initMenuEditor(cfg, appsMap = {}) {
  const editorBtn = document.getElementById('menu-editor-btn');
  const modal = document.getElementById('menuEditorModal');
  const list = document.getElementById('allMenuEditor');
  const saveBtn = document.getElementById('saveMenuConfig');
  if (!editorBtn || !modal || !list || !cfg) return;

  function renderEditorItems() {
    const items = [
      ...(cfg.menu.topButtons || []).map(x => ({ ...x, position: 'top' })),
      ...(cfg.menu.sidebarItems || []).map(x => ({ ...x, position: x.visible === false ? 'hidden' : 'bottom' })),
    ];

    list.innerHTML = '';
    items.forEach(item => {
      const safeId = item.id.replace(/[^a-zA-Z0-9_-]/g, '');
      const div = document.createElement('div');
      div.className = 'd-flex align-items-center gap-3 p-2 border-bottom';
      div.dataset.id = item.id;

      const info = document.createElement('div');
      info.className = 'flex-grow-1 small';
      info.textContent = `${item.label} (${item.tab})`;

      const group = document.createElement('div');
      group.className = 'btn-group btn-group-sm';
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

      div.append(info, group);
      list.appendChild(div);
    });

    return items;
  }

  let currentItems = renderEditorItems();

  editorBtn.addEventListener('click', () => {
    currentItems = renderEditorItems();
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
      const r = await fetch('/api/menu/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(cfg)
      });

      if (!r.ok) {
        throw new Error(r.statusText || `HTTP ${r.status}`);
      }

      // Немедленно переопределяем меню и структуру вкладок в интерфейсе
      await buildMenu(appsMap, cfg);
      await loadRequiredTabs();

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
          switchTab(firstVisible.dataset.tab);
        }
      }
    } catch (e) {
      alert('Ошибка при сохранении меню: ' + e.message);
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

  // Загрузить все вкладки (из верхнего и бокового меню)
  await loadRequiredTabs();

  applyTranslations();

  // Активировать вкладку по hash или первую
  const hash = location.hash.replace('#', '');
  const first = document.querySelector('#appsNavTabs [data-tab]') || document.querySelector('[data-tab]');
  switchTab(hash || first?.dataset.tab || '');
}

document.readyState === 'loading'
  ? document.addEventListener('DOMContentLoaded', init)
  : init();
