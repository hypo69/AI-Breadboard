import { setupGlobalApi, setupThemeAndLang } from './modules/init-interface.js';
import { fetchAppsStatus, updateModelBadge } from './modules/status-manager.js';
import { APP_TAB_DEFS } from './modules/tabs-config.js';
import { applyTranslations } from '../js/i18n.js';

// Карта: tabId → { html, js } — берём из tabs-config, не генерируем пути вручную
const TAB_PATHS = Object.fromEntries(
  APP_TAB_DEFS.map(d => [d.tabId, { html: d.html, js: d.js }])
);

// ── SWITCH TAB ───────────────────────────────────────────────────────────────

export function switchTab(tabId) {
  if (!tabId) return;
  const id = tabId.startsWith('tab-') ? tabId : `tab-${tabId}`;

  document.querySelectorAll('#appsNavTabs [data-tab]').forEach(btn =>
    btn.classList.toggle('active', btn.dataset.tab === id)
  );

  document.querySelectorAll('#mainTabContent .tab-pane').forEach(pane => {
    pane.classList.toggle('show', pane.id === id);
    pane.classList.toggle('active', pane.id === id);
  });

  const activeBtn = document.querySelector(`#appsNavTabs [data-tab="${id}"]`);
  const badge = document.getElementById('active-tab-title-badge');
  if (activeBtn && badge) badge.innerHTML = activeBtn.innerHTML;

  const oc = bootstrap.Offcanvas.getInstance(document.getElementById('appsSideNavOffcanvas'));
  oc?.hide();

  history.replaceState(null, null, `#${id}`);

  // Вызов init-функции вкладки
  const name = id.replace(/^tab-/, '').replace(/-([a-z])/g, (_, c) => c.toUpperCase());
  window[`init${name[0].toUpperCase() + name.slice(1)}Tab`]?.();
}

window.switchTab = switchTab;
window.switchToTab = switchTab;

// Единственный обработчик кликов для ВСЕХ кнопок с data-tab на странице
document.addEventListener('click', e => {
  const btn = e.target.closest('button[data-tab], a[data-tab]');
  if (btn) switchTab(btn.dataset.tab);
});

// ── MENU BUILDER ─────────────────────────────────────────────────────────────

async function buildMenu(appsMap) {
  const res = await fetch('/html/config/tc_menu_config.json');
  if (!res.ok) return null;
  const cfg = await res.json();
  if (!cfg.menu) return null;

  const isEnabled = item => {
    const app = appsMap[item.id];
    return !app || app.enabled !== false;
  };
  const sorted = arr => [...arr]
    .filter(x => x.visible !== false && isEnabled(x))
    .sort((a, b) => (a.order || 0) - (b.order || 0));

  // Верхнее меню
  const topContainer = document.querySelector('.main-nav-container .d-flex.gap-1.flex-wrap');
  if (topContainer) {
    topContainer.innerHTML = '';
    sorted(cfg.menu.topButtons || []).forEach(item => {
      const safeIcon = /^bi-[a-z0-9-]+$/.test(item.icon) ? item.icon : 'bi-app';
      const btn = document.createElement('button');
      btn.className = 'btn btn-sm btn-outline-primary d-flex align-items-center gap-1 py-1 px-2 rounded';
      btn.type = 'button';
      btn.dataset.tab = item.tab;
      btn.title = item.label;
      btn.innerHTML = `<i class="bi ${safeIcon}"></i><span class="d-none d-sm-inline">${item.label}</span>`;
      topContainer.appendChild(btn);
    });
  }

  // Боковое меню
  const navTabs = document.getElementById('appsNavTabs');
  if (navTabs) {
    navTabs.innerHTML = '';
    sorted(cfg.menu.sidebarItems || []).forEach(item => {
      const btn = document.createElement('button');
      btn.className = 'list-group-item list-group-item-action d-flex align-items-center gap-2 py-2 px-3';
      btn.type = 'button';
      btn.dataset.tab = item.tab;
      if (item.i18n) btn.dataset.i18n = item.i18n;
      const iconSpan = document.createElement('span');
      iconSpan.className = 'fs-6';
      iconSpan.textContent = item.icon;
      const labelSpan = document.createElement('span');
      labelSpan.className = 'fw-medium';
      labelSpan.textContent = item.label;
      btn.append(iconSpan, labelSpan);
      navTabs.appendChild(btn);
    });
  }

  return cfg;
}

// ── MENU EDITOR ──────────────────────────────────────────────────────────────

function initMenuEditor(cfg) {
  const editorBtn = document.getElementById('menu-editor-btn');
  const modal = document.getElementById('menuEditorModal');
  const list = document.getElementById('allMenuEditor');
  const saveBtn = document.getElementById('saveMenuConfig');
  if (!editorBtn || !modal || !list || !cfg) return;

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

    [['top', 'Сверху', 'btn-outline-primary'], ['bottom', 'Слева', 'btn-outline-secondary'], ['hidden', 'Скрыть', 'btn-outline-danger']].forEach(([val, text, cls]) => {
      const inp = document.createElement('input');
      inp.type = 'radio'; inp.className = 'btn-check';
      inp.name = `pos-${safeId}`; inp.id = `pos-${val}-${safeId}`; inp.value = val;
      inp.checked = item.position === val;
      inp.addEventListener('change', () => { item.position = val; item.visible = val !== 'hidden'; });
      const lbl = document.createElement('label');
      lbl.className = `btn ${cls}`; lbl.setAttribute('for', inp.id); lbl.textContent = text;
      group.append(inp, lbl);
    });

    div.append(info, group);
    list.appendChild(div);
  });

  editorBtn.addEventListener('click', () => new bootstrap.Modal(modal).show());
  saveBtn.addEventListener('click', async () => {
    cfg.menu.topButtons = items.filter(x => x.position === 'top').map(({ position, ...x }) => x);
    cfg.menu.sidebarItems = items.filter(x => x.position !== 'top').map(({ position, ...x }) => x);
    try {
      const r = await fetch('/api/menu/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(cfg)
      });
      r.ok ? (alert('Сохранено!'), location.reload()) : alert('Ошибка: ' + r.statusText);
    } catch (e) { alert('Ошибка: ' + e.message); }
  });
}

// ── TAB LOADER ───────────────────────────────────────────────────────────────

async function loadTab(tabId, v) {
  const paths = TAB_PATHS[tabId];
  if (!paths) return; // вкладка не в реестре — пропускаем без ошибки
  const container = document.getElementById(tabId);
  if (!container) return;
  try {
    const html = await fetch(`${paths.html}?v=${v}`).then(r => {
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return r.text();
    });
    container.innerHTML = html;
    await new Promise(resolve => {
      const s = document.createElement('script');
      s.src = `${paths.js}?v=${v}`;
      s.onload = s.onerror = resolve;
      document.body.appendChild(s);
    });
    const name = tabId.replace(/^tab-/, '').replace(/-([a-z])/g, (_, c) => c.toUpperCase());
    window[`init${name[0].toUpperCase() + name.slice(1)}Tab`]?.();
  } catch (e) {
    container.innerHTML = `<div class="alert alert-danger">Ошибка загрузки ${tabId}: ${e.message}</div>`;
  }
}

// ── INIT ─────────────────────────────────────────────────────────────────────

async function init() {
  setupGlobalApi();
  await setupThemeAndLang();

  if (window.location.pathname.startsWith('/tc'))
    document.title = 'AI Breadboard — Test Computer (/tc)';

  const statusData = await fetchAppsStatus();
  await updateModelBadge(statusData);
  const appsMap = statusData?.apps || {};

  const cfg = await buildMenu(appsMap).catch(() => null);
  initMenuEditor(cfg);

  // Загружаем все вкладки из бокового меню (пути берём из TAB_PATHS)
  const v = Date.now();
  await Promise.all(
    Array.from(document.querySelectorAll('#appsNavTabs [data-tab]'))
      .map(btn => loadTab(btn.dataset.tab, v))
  );

  applyTranslations();

  const hash = location.hash.replace('#', '');
  const first = document.querySelector('#appsNavTabs [data-tab]');
  switchTab(hash || first?.dataset.tab || '');
}

document.readyState === 'loading'
  ? document.addEventListener('DOMContentLoaded', init)
  : init();
