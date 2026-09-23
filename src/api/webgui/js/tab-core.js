/**
 * tab-core.js — единая логика переключения вкладок для всех интерфейсов.
 * Используется в js/main.js (/) и apps/main.js (/tc).
 *
 * Контракт:
 *   - Кнопки меню: <button data-tab="tab-xxx">
 *   - Панели:      <div id="tab-xxx" class="tab-pane fade">
 *   - Offcanvas:   id="leftSideNavOffcanvas" или id="appsSideNavOffcanvas"
 *   - Бейдж:       id="active-tab-title-badge"
 */

/**
 * @param {string} tabId  — "tab-xxx" или "xxx"
 * @param {object} opts
 * @param {string} [opts.navSelector]      — селектор контейнера кнопок меню
 * @param {string} [opts.offcanvasId]      — id offcanvas для закрытия
 * @param {Function} [opts.onSwitch]       — колбэк после переключения
 */
export function switchTab(tabId, opts = {}) {
  if (!tabId) return;
  const id = tabId.startsWith('tab-') ? tabId : `tab-${tabId}`;

  // 1. Активный пункт меню — ищем по всем кнопкам с data-tab на странице
  const navSel = opts.navSelector || '[data-tab]';
  document.querySelectorAll(navSel).forEach(btn => {
    if (!btn.dataset.tab) return;
    btn.classList.toggle('active', btn.dataset.tab === id);
  });

  // 2. Видимая панель
  document.querySelectorAll('#mainTabContent .tab-pane').forEach(pane => {
    pane.classList.toggle('show', pane.id === id);
    pane.classList.toggle('active', pane.id === id);
  });

  // 3. Бейдж активного раздела
  const activeBtn = document.querySelector(`[data-tab="${id}"]`);
  const badge = document.getElementById('active-tab-title-badge');
  if (activeBtn && badge) badge.innerHTML = activeBtn.innerHTML;

  // 4. Закрыть offcanvas
  const ocId = opts.offcanvasId || 'leftSideNavOffcanvas';
  const ocEl = document.getElementById(ocId) || document.getElementById('appsSideNavOffcanvas');
  if (ocEl) bootstrap.Offcanvas.getInstance(ocEl)?.hide();

  // 5. URL hash
  history.replaceState(null, null, `#${id}`);

  // 6. Вызов init-функции вкладки если есть
  const name = id.replace(/^tab-/, '').replace(/-([a-z])/g, (_, c) => c.toUpperCase());
  window[`init${name[0].toUpperCase() + name.slice(1)}Tab`]?.();

  opts.onSwitch?.(id);
}

/**
 * Загрузить HTML+JS вкладки в контейнер tab-{tabName}.
 * @param {string} tabName  — имя без "tab-" префикса
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
 * Повесить единый обработчик кликов на document.
 * Все кнопки и ссылки с data-tab на странице будут переключать вкладки.
 * @param {object} opts — те же опции что у switchTab
 */
export function setupTabClicks(opts = {}) {
  document.addEventListener('click', e => {
    const btn = e.target.closest('button[data-tab], a[data-tab]');
    if (btn) switchTab(btn.dataset.tab, opts);
  });
}
