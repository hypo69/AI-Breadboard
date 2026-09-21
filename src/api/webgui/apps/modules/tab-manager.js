/**
 * apps/modules/tab-manager.js — Управление вкладками и жизненным циклом приложений /apps
 */

export function onTabSwitched(targetId) {
  const cleanId = targetId.startsWith('#') ? targetId.slice(1) : targetId;
  const tabName = cleanId.replace(/^tab-/, '');
  const camelName = tabName.replace(/-([a-z])/g, (_, c) => c.toUpperCase());
  const initFuncName = 'init' + camelName.charAt(0).toUpperCase() + camelName.slice(1) + 'Tab';

  console.log(`[AppsHub] Switching to tab: ${cleanId}`);

  if (typeof window[initFuncName] === 'function') {
    window[initFuncName]();
  }

  if (cleanId === 'tab-chat') {
    const msgInput = document.getElementById('message-input');
    if (msgInput) msgInput.focus();
  }
}

export function switchTab(targetId) {
  if (!targetId) return;
  const cleanId = targetId.startsWith('#') ? targetId.slice(1) : targetId;
  const tabId = cleanId.startsWith('tab-') ? cleanId : `tab-${cleanId}`;

  const statusEntry = Object.values(window.appsStatusMap || {}).find(a => a.tab === tabId || a.id === cleanId);
  if (statusEntry && statusEntry.enabled === false) {
    console.warn(`[AppsHub] Tab ${tabId} is disabled in configuration, skipping switch.`);
    return;
  }

  document.querySelectorAll('#appsNavTabs .list-group-item, #appsNavTabs .nav-link').forEach((item) => {
    const itemTarget = item.getAttribute('data-tab') || item.getAttribute('data-bs-target')?.replace('#', '');
    if (itemTarget === tabId || itemTarget === cleanId) {
      item.classList.add('active');
    } else {
      item.classList.remove('active');
    }
  });

  const mainTabContent = document.getElementById('mainTabContent');
  if (mainTabContent) {
    Array.from(mainTabContent.children).forEach((pane) => {
      if (pane.classList.contains('tab-pane')) {
        pane.classList.remove('show', 'active');
      }
    });
  }
  const targetPane = document.getElementById(tabId) || document.getElementById(cleanId);
  if (targetPane) {
    targetPane.classList.add('show', 'active');
  }

  // Закрываем offcanvas, если переключение вызвано из выпадающей панели
  const offcanvasEl = document.getElementById('appsSideNavOffcanvas');
  if (offcanvasEl && typeof bootstrap !== 'undefined' && bootstrap.Offcanvas) {
    const bsOffcanvas = bootstrap.Offcanvas.getInstance(offcanvasEl);
    if (bsOffcanvas) {
      bsOffcanvas.hide();
    }
  }

  // Обновляем бейдж текущего активного раздела
  const activeBadge = document.getElementById('active-tab-title-badge');
  if (activeBadge) {
    const activeBtn = document.querySelector(`#appsNavTabs [data-tab="${tabId}"], #appsNavTabs [data-bs-target="#${tabId}"]`);
    if (activeBtn) {
      activeBadge.innerHTML = activeBtn.innerHTML;
    }
  }

  if (history.replaceState) {
    history.replaceState(null, null, `#${tabId}`);
  }

  onTabSwitched(tabId);
}

export function setupNavTabs() {
  const navTabs = document.getElementById('appsNavTabs');
  if (!navTabs) return;

  navTabs.querySelectorAll('.list-group-item, .nav-link').forEach((btn) => {
    btn.onclick = (e) => {
      e.preventDefault();
      const targetId = btn.getAttribute('data-tab') || btn.getAttribute('data-bs-target')?.replace('#', '');
      if (targetId) {
        switchTab(targetId);
      }
    };
  });
}

export async function loadTabContent(tabName, url, jsOverrideSrc) {
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const html = await response.text();
    const container = document.getElementById(`tab-${tabName}`);
    if (!container) return;
    container.innerHTML = html;

    const cacheBuster = Date.now();
    const scriptSrc = jsOverrideSrc || `/html/${tabName}_tab/main.js?v=${cacheBuster}`;

    await new Promise((resolve) => {
      const script = document.createElement('script');
      script.src = scriptSrc;
      script.onload = () => {
        console.log(`[AppsHub] Loaded JS for ${tabName}`);
        resolve();
      };
      script.onerror = (err) => {
        console.warn(`[AppsHub] Note: No JS loaded for ${tabName} from ${scriptSrc}`);
        resolve();
      };
      document.body.appendChild(script);
    });

    const camelName = tabName.replace(/-([a-z])/g, (_, c) => c.toUpperCase());
    const initFuncName = 'init' + camelName.charAt(0).toUpperCase() + camelName.slice(1) + 'Tab';
    if (typeof window[initFuncName] === 'function') {
      console.log(`[AppsHub] Calling ${initFuncName} for ${tabName}`);
      try {
        await window[initFuncName]();
      } catch (err) {
        console.error(`[AppsHub] Error executing ${initFuncName}:`, err);
      }
    }
  } catch (e) {
    console.error(`[AppsHub] Error loading tab ${tabName}:`, e);
    const container = document.getElementById(`tab-${tabName}`);
    if (container) {
      container.innerHTML = `<div class="alert alert-danger">Ошибка загрузки ${tabName}: ${e.message}</div>`;
    }
  }
}
