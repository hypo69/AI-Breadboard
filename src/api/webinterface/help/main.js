// ── HELP.JS ───────────────────────────────────────────────────────────────────
// Interactive User Guides & Knowledge Base Navigation

function loadHelpSection(target) {
  const contentEl = document.getElementById('help-content');
  const titleEl = document.getElementById('help-title');
  if (!contentEl) return;

  const content = (window.HELP_CONTENT && window.HELP_CONTENT[target]) || '<div class="alert alert-warning">Информация по данному разделу не найдена.</div>';
  contentEl.innerHTML = content;

  // Update title
  const navItem = document.querySelector(`#help-nav a[data-target="${target}"]`);
  if (navItem && titleEl) {
    const textEl = navItem.querySelector('span.fw-semibold') || navItem.querySelector('strong') || navItem;
    titleEl.textContent = textEl.textContent.trim();
  }

  // Update active state in nav
  document.querySelectorAll('#help-nav a').forEach(a => {
    a.classList.remove('active', 'bg-primary', 'text-white');
    if (a.dataset.target === target) {
      a.classList.add('active');
    }
  });

  // Attach copy listeners to code snippet copy buttons
  contentEl.querySelectorAll('.btn-copy-snippet').forEach(btn => {
    btn.onclick = (e) => {
      e.preventDefault();
      const codeTargetId = btn.dataset.copyTarget;
      const targetEl = codeTargetId ? document.getElementById(codeTargetId) : btn.closest('.code-box')?.querySelector('code, pre');
      const textToCopy = targetEl ? targetEl.innerText : btn.dataset.copyText || '';
      if (textToCopy) {
        navigator.clipboard.writeText(textToCopy.trim()).then(() => {
          const origHtml = btn.innerHTML;
          btn.innerHTML = '<i class="bi bi-check2 text-success"></i> Скопировано!';
          btn.classList.add('btn-success', 'text-white');
          btn.classList.remove('btn-outline-secondary', 'btn-outline-primary');
          setTimeout(() => {
            btn.innerHTML = origHtml;
            btn.classList.remove('btn-success', 'text-white');
            btn.classList.add('btn-outline-secondary');
          }, 2000);
        });
      }
    };
  });

  // Attach tab switch triggers
  contentEl.querySelectorAll('[data-jump-tab]').forEach(btn => {
    btn.onclick = (e) => {
      e.preventDefault();
      const targetTab = btn.dataset.jumpTab;
      if (typeof window.switchToTab === 'function') {
        window.switchToTab(targetTab);
      } else {
        const tabBtn = document.querySelector(`[data-tab="${targetTab}"]`) || document.querySelector(`[data-bs-target="#${targetTab}"]`);
        if (tabBtn) tabBtn.click();
      }
    };
  });

  contentEl.scrollTop = 0;
}

// Navigation click handler
function setupHelpNavigation() {
  const navList = document.querySelectorAll('#help-nav a');
  navList.forEach(a => {
    a.onclick = (e) => {
      e.preventDefault();
      const target = a.dataset.target;
      if (target) loadHelpSection(target);
    };
  });
}

// Live search filter across topics
function setupHelpSearch() {
  const searchInput = document.getElementById('help-search-input');
  const clearBtn = document.getElementById('help-search-clear');
  const topicCount = document.getElementById('help-topic-count');
  if (!searchInput) return;

  const performFilter = () => {
    const query = (searchInput.value || '').trim().toLowerCase();
    const navItems = document.querySelectorAll('#help-nav a');
    let visibleCount = 0;
    let firstVisibleTarget = '';

    if (clearBtn) {
      clearBtn.style.display = query.length > 0 ? 'inline-block' : 'none';
    }

    navItems.forEach(item => {
      const target = item.dataset.target || '';
      const title = item.innerText.toLowerCase();
      const fullText = (window.HELP_CONTENT && window.HELP_CONTENT[target]) ? window.HELP_CONTENT[target].toLowerCase() : '';

      if (!query || title.includes(query) || fullText.includes(query)) {
        item.style.setProperty('display', 'flex', 'important');
        visibleCount++;
        if (!firstVisibleTarget) firstVisibleTarget = target;
      } else {
        item.style.setProperty('display', 'none', 'important');
      }
    });

    if (topicCount) {
      topicCount.textContent = visibleCount;
    }
  };

  searchInput.oninput = performFilter;
  searchInput.onkeydown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const firstVisible = document.querySelector('#help-nav a[style*="display: flex"], #help-nav a:not([style*="display: none"])');
      if (firstVisible && firstVisible.dataset.target) {
        loadHelpSection(firstVisible.dataset.target);
      }
    }
  };

  if (clearBtn) {
    clearBtn.onclick = () => {
      searchInput.value = '';
      performFilter();
      searchInput.focus();
    };
  }
}

function initHelpTab() {
  setupHelpNavigation();
  setupHelpSearch();
  loadHelpSection('overview');
}

window.initHelpTab = initHelpTab;
window.loadHelpSection = loadHelpSection;

// Initialize when container is present
if (document.getElementById('help-nav')) {
  initHelpTab();
}