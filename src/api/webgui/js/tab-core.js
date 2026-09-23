/**
 * tab-core.js — единая логика вкладок для всех страниц.
 * Документация: UI_ARCHITECTURE.md
 */

const OFFCANVAS_IDS = ['leftSideNavOffcanvas', 'appsSideNavOffcanvas'];

export function switchTab(tabId) {
  if (!tabId) return;
  const id = tabId.startsWith('tab-') ? tabId : `tab-${tabId}`;

  // Активная кнопка меню
  document.querySelectorAll('[data-tab]').forEach(btn =>
    btn.classList.toggle('active', btn.dataset.tab === id)
  );

  // Видимая панель
  document.querySelectorAll('#mainTabContent .tab-pane').forEach(pane => {
    pane.classList.toggle('show', pane.id === id);
    pane.classList.toggle('active', pane.id === id);
  });

  // Бейдж
  const badge = document.getElementById('active-tab-title-badge');
  const activeBtn = document.querySelector(`[data-tab="${id}"]`);
  if (badge && activeBtn) badge.innerHTML = activeBtn.innerHTML;

  // Закрыть offcanvas
  OFFCANVAS_IDS.forEach(ocId => {
    const el = document.getElementById(ocId);
    if (el) bootstrap.Offcanvas.getInstance(el)?.hide();
  });

  // URL hash
  history.replaceState(null, null, `#${id}`);

  // Lifecycle hook
  const name = id.replace(/^tab-/, '').replace(/-([a-z])/g, (_, c) => c.toUpperCase());
  window[`init${name[0].toUpperCase() + name.slice(1)}Tab`]?.();
}

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

export function setupTabClicks() {
  document.addEventListener('click', e => {
    const btn = e.target.closest('button[data-tab], a[data-tab]');
    if (btn) switchTab(btn.dataset.tab);
  });
}
