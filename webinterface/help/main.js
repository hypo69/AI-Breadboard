// ── HELP.JS ───────────────────────────────────────────────────────────────────

// HELP content stored in window.HELP_CONTENT (defined in main.js)
// This file handles navigation and tab switching

function loadHelpSection(target) {
  const contentEl = document.getElementById('help-content');
  const titleEl = document.getElementById('help-title');
  
  const content = window.HELP_CONTENT[target] || '<p>Информация не найдена</p>';
  contentEl.innerHTML = content;
  
  // Update title
  const navItem = document.querySelector(`#help-nav a[data-target="${target}"]`);
  if (navItem) {
    titleEl.textContent = navItem.querySelector('strong').textContent;
  }
  
  // Update active state in nav
  document.querySelectorAll('#help-nav a').forEach(a => {
    a.classList.remove('active', 'bg-primary', 'text-white');
    if (a.dataset.target === target) {
      a.classList.add('active', 'bg-primary', 'text-white');
    }
  });
  
  console.log(`HELP section loaded: ${target}`);
}

// Navigation click handler
document.querySelectorAll('#help-nav a').forEach(a => {
  a.addEventListener('click', (e) => {
    e.preventDefault();
    const target = a.dataset.target;
    loadHelpSection(target);
  });
});

// Initialize with overview when tab is loaded
// Note: HELP content is initialized in main.js before loading tabs