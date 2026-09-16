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

      // Close other dropdowns
      dropdowns.forEach((other) => {
        if (other !== dropdown) {
          other.classList.remove('show');
          const menu = other.nextElementSibling;
          if (menu) menu.classList.remove('show');
        }
      });

      // Toggle current dropdown
      dropdown.classList.toggle('show');
      const menu = dropdown.nextElementSibling;
      if (menu) {
        menu.classList.toggle('show');
      }
    });

    // Handle dropdown items clicks
    const menu = dropdown.nextElementSibling;
    if (menu) {
      const items = menu.querySelectorAll('.dropdown-item');
      items.forEach((item) => {
        item.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();

          const targetId = item.getAttribute('data-tab') || 
                          item.getAttribute('data-bs-target')?.replace('#', '');
          
          if (targetId) {
            window.switchTab(targetId);
            
            // Close dropdown
            dropdown.classList.remove('show');
            menu.classList.remove('show');
          }
        });
      });
    }
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
