/**
 * Apps Sync Module - Синхронизация видимости приложений
 */

export async function syncApplicationsVisibility() {
  console.log('[AppSync] Syncing application visibility...');

  let appsMap = {};
  
  try {
    let appsData = null;
    try {
      appsData = await window.api.fetch('/api/apps/status');
    } catch {
      appsData = await window.api.fetch('/api/admin/apps/status');
    }
    
    if (appsData && appsData.apps) {
      appsMap = appsData.apps;
      window.appsStatusMap = appsData.apps;
      syncAppsTabsVisibility(appsData.apps);
    }
  } catch (error) {
    console.warn('[AppSync] Failed to sync apps visibility:', error);
  }

  return appsMap;
}

export function syncAppsTabsVisibility(appsMap) {
  if (!appsMap || typeof appsMap !== 'object') return;

  const dropdown = document.getElementById('appsTabsDropdown');
  if (!dropdown) return;

  const dropdownMenu = dropdown.nextElementSibling || 
                      dropdown.closest('.dropdown')?.querySelector('.dropdown-menu');
  if (!dropdownMenu) return;

  const appButtons = dropdownMenu.querySelectorAll('button[data-tab]');
  let visibleCount = 0;

  appButtons.forEach((btn) => {
    const dataTab = btn.getAttribute('data-tab') || 
                   btn.getAttribute('data-bs-target')?.replace('#', '');
    const cleanId = dataTab ? dataTab.replace(/^tab-/, '') : '';
    const appInfo = Object.values(appsMap).find(
      a => a.tab === dataTab || a.id === cleanId || a.folder === cleanId
    );
    const isEnabled = appInfo ? appInfo.enabled : true;

    if (isEnabled) {
      btn.style.display = '';
      btn.classList.remove('d-none');
      visibleCount++;
    } else {
      btn.style.display = 'none';
      btn.classList.add('d-none');
      
      const pane = document.getElementById(dataTab);
      if (pane) {
        pane.style.display = 'none';
        pane.classList.remove('show', 'active');
      }
      
      if (btn.classList.contains('active')) {
        btn.classList.remove('active');
        if (typeof window.switchTab === 'function') {
          window.switchTab('tab-chat');
        }
      }
    }
  });

  // Hide/show apps dropdown if all apps are disabled
  const dropdownWrapper = dropdown.closest('li.nav-item');
  if (dropdownWrapper) {
    const prevDivider = dropdownWrapper.previousElementSibling;
    
    if (visibleCount === 0) {
      dropdownWrapper.style.display = 'none';
      if (prevDivider) prevDivider.style.display = 'none';
    } else {
      dropdownWrapper.style.display = '';
      if (prevDivider) prevDivider.style.display = '';
    }
  }

  console.log(`[AppSync] Synced apps visibility: ${visibleCount} visible`);
}

export function getAppsMap() {
  return window.appsStatusMap || {};
}

export { syncAppsTabsVisibility };
