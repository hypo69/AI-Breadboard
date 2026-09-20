/**
 * Tab Manager Module - Управление вкладками и навигацией
 */

export function setupTabManagement() {
  setupDropdownTabs();
  setupTabEvents();
}

function setupDropdownTabs() {
  const mainTabs = document.getElementById('mainTabs');
  if (!mainTabs) return;

  const dropdowns = mainTabs.querySelectorAll('.dropdown-toggle');

  dropdowns.forEach((dropdown) => {
    dropdown.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();

      const parentDropdown = dropdown.closest('.dropdown');
      const menu = dropdown.nextElementSibling || parentDropdown?.querySelector('.dropdown-menu');
      const isAlreadyOpen = menu?.classList.contains('show');

      // Close other dropdowns
      document.querySelectorAll('#mainTabs .dropdown-menu.show').forEach((otherMenu) => {
        otherMenu.classList.remove('show');
        otherMenu.closest('.dropdown')?.querySelector('.dropdown-toggle')?.classList.remove('show');
      });

      // Toggle current dropdown
      if (!isAlreadyOpen && menu) {
        dropdown.classList.add('show');
        menu.classList.add('show');
      }
    });
  });

  // Handle all clickable navigation items inside mainTabs (tabs and dropdown items)
  mainTabs.querySelectorAll('.dropdown-item, .list-group-item, [data-tab], [data-bs-target], [data-plugin]').forEach((item) => {
    item.addEventListener('click', (e) => {
      const pluginName = item.getAttribute('data-plugin');
      const targetId = item.getAttribute('data-tab') || 
                      item.getAttribute('data-bs-target')?.replace('#', '');

      // Close parent dropdown menu
      const menu = item.closest('.dropdown-menu');
      if (menu) {
        menu.classList.remove('show');
        menu.closest('.dropdown')?.querySelector('.dropdown-toggle')?.classList.remove('show');
      }

      if (pluginName && typeof window.openPluginFromDropdown === 'function') {
        e.preventDefault();
        e.stopPropagation();
        window.openPluginFromDropdown(pluginName);
      } else if (targetId) {
        e.preventDefault();
        e.stopPropagation();
        if (typeof window.switchTab === 'function') {
          window.switchTab(targetId);
        }
      }
    });
  });

  // Close dropdowns on outside click
  document.addEventListener('click', (e) => {
    if (!mainTabs.contains(e.target)) {
      dropdowns.forEach((dropdown) => {
        dropdown.classList.remove('show');
        const menu = dropdown.nextElementSibling;
        if (menu) menu.classList.remove('show');
      });
    }
  });
}

function setupTabEvents() {
  // Tab content click handlers
  const tabPane = document.getElementById('mainTabsContent');
  if (tabPane) {
    tabPane.addEventListener('click', (e) => {
      const target = e.target.closest('[data-tab]');
      if (target) {
        const tabId = target.getAttribute('data-tab');
        if (tabId) {
          window.switchTab(tabId);
        }
      }
    });
  }
}

export function onTabSwitched(targetId) {
  const cleanId = targetId.startsWith('#') ? targetId.slice(1) : targetId;
  
  if (cleanId === 'tab-chat') {
    if (typeof window.initChatTab === 'function') {
      window.initChatTab();
    }
  }
}

export { setupDropdownTabs, setupTabEvents };
