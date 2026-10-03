/**
 * =============================================================================
 * Process Name: Windows Modules - Apps-Sync Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля apps-sync.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/webgui/admin/modules/apps-sync.js?v=20261001_v1" type="module"></script>
 *
 *   JavaScript Import:
 *     import { syncAppsTabsVisibility, getAppsMap } from '/windows/api/webgui/admin/modules/apps-sync.js';
 *
 * File: apps-sync.js
 * Project: ai-breadboard
 * Package: windows/api/webgui/admin/modules
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-04 01:12:00
 * =============================================================================
 */

/**
 * Apps Sync Module - Синхронизация видимости приложений
 */

export async function syncApplicationsVisibility() {
  console.log('[AppSync] Syncing application visibility...');

  let appsMap = {};
  
  try {
    const appsData = await (window.api ? window.api.fetch('/api/v1/apps/status') : fetch('/api/v1/apps/status').then(r => r.json()));
    
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

