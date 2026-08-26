/**
 * theme.js — Theme management module (Light / Dark / System)
 * 
 * Supports 3 modes:
 *  - 'light': Forces light theme
 *  - 'dark': Forces dark theme
 *  - 'system': Automatically follows OS / browser color scheme preferences
 * 
 * Persists selected mode to localStorage under key 'theme'.
 */

const STORAGE_KEY = 'theme';
const DEFAULT_MODE = 'system';

let mediaQueryListenerAttached = false;

/**
 * Get the user's stored theme preference or default to 'system'.
 * @returns {'light' | 'dark' | 'system'}
 */
export function getThemeMode() {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved === 'light' || saved === 'dark' || saved === 'system') {
    return saved;
  }
  return DEFAULT_MODE;
}

/**
 * Resolve the effective theme ('light' or 'dark') based on the mode.
 * @param {'light' | 'dark' | 'system'} mode
 * @returns {'light' | 'dark'}
 */
export function getResolvedTheme(mode = getThemeMode()) {
  if (mode === 'system') {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
      ? 'dark'
      : 'light';
  }
  return mode;
}

/**
 * Set the theme mode, update DOM attributes, UI icons, checkmarks, and persist.
 * @param {'light' | 'dark' | 'system'} mode
 */
export function setTheme(mode) {
  if (mode !== 'light' && mode !== 'dark' && mode !== 'system') {
    mode = DEFAULT_MODE;
  }

  localStorage.setItem(STORAGE_KEY, mode);
  applyThemeToDOM(mode);
}

/**
 * Apply the given theme mode to documentElement and sync UI controls.
 * @param {'light' | 'dark' | 'system'} mode
 */
function applyThemeToDOM(mode) {
  const resolved = getResolvedTheme(mode);

  // Set data-theme, data-bs-theme (Bootstrap 5.3+), and data-theme-mode
  document.documentElement.setAttribute('data-theme', resolved);
  document.documentElement.setAttribute('data-bs-theme', resolved);
  document.documentElement.setAttribute('data-theme-mode', mode);

  // Update theme button icon and title
  updateThemeIcon(mode, resolved);

  // Update dropdown checkmarks & active states
  updateThemeDropdownUI(mode);

  // Sync any theme select elements (e.g., in user settings)
  document.querySelectorAll('.theme-selector, #settings-theme').forEach((sel) => {
    if (sel.value !== mode) {
      sel.value = mode;
    }
  });

  // Dispatch custom event for tabs/components that need to react
  window.dispatchEvent(new CustomEvent('themechanged', {
    detail: { mode, resolved }
  }));
}

/**
 * Update the theme toggle / dropdown icon.
 * @param {'light' | 'dark' | 'system'} mode
 * @param {'light' | 'dark'} resolved
 */
function updateThemeIcon(mode, resolved) {
  const iconEl = document.getElementById('theme-icon');
  const toggleBtn = document.getElementById('theme-toggle');

  let iconClass = 'bi-circle-half text-info';
  let titleText = 'Системная тема';

  if (mode === 'light') {
    iconClass = 'bi-sun-fill text-warning';
    titleText = 'Светлая тема';
  } else if (mode === 'dark') {
    iconClass = 'bi-moon-stars-fill text-primary';
    titleText = 'Темная тема';
  } else {
    // system mode
    iconClass = 'bi-circle-half text-info';
    titleText = `Системная тема (${resolved === 'dark' ? 'тёмная' : 'светлая'})`;
  }

  if (iconEl) {
    iconEl.className = `bi ${iconClass}`;
  }

  const dropdownBtn = document.getElementById('theme-dropdown');
  if (dropdownBtn) {
    dropdownBtn.setAttribute('title', titleText);
  }

  // Legacy / fallback toggle button
  if (toggleBtn) {
    toggleBtn.innerHTML = `<i class="bi ${iconClass}"></i>`;
    toggleBtn.setAttribute('title', titleText);
  }
}

/**
 * Update checkmarks and active classes in the theme dropdown menu.
 * @param {'light' | 'dark' | 'system'} activeMode
 */
function updateThemeDropdownUI(activeMode) {
  // Update checkmarks
  document.querySelectorAll('.theme-check-icon').forEach((icon) => {
    const target = icon.getAttribute('data-theme-check');
    if (target === activeMode) {
      icon.classList.remove('d-none');
    } else {
      icon.classList.add('d-none');
    }
  });

  // Update active state on dropdown items
  document.querySelectorAll('[data-theme-value]').forEach((item) => {
    const val = item.getAttribute('data-theme-value');
    if (val === activeMode) {
      item.classList.add('active');
    } else {
      item.classList.remove('active');
    }
  });
}

/**
 * Initialize theme listeners and apply the current theme on page load.
 */
export function initTheme() {
  const currentMode = getThemeMode();
  applyThemeToDOM(currentMode);

  // Attach OS color-scheme change listener once
  if (!mediaQueryListenerAttached && window.matchMedia) {
    try {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      const handler = () => {
        if (getThemeMode() === 'system') {
          applyThemeToDOM('system');
        }
      };
      if (mediaQuery.addEventListener) {
        mediaQuery.addEventListener('change', handler);
      } else if (mediaQuery.addListener) {
        mediaQuery.addListener(handler);
      }
      mediaQueryListenerAttached = true;
    } catch (e) {
      console.warn('[theme] Failed to attach media query listener:', e);
    }
  }

  // Bind click listeners for theme dropdown items
  document.querySelectorAll('[data-theme-value]').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const selected = btn.getAttribute('data-theme-value');
      if (selected) {
        setTheme(selected);
      }
    });
  });

  // Bind legacy / simple toggle button if present without dropdown
  const themeToggle = document.getElementById('theme-toggle');
  if (themeToggle && !themeToggle.hasAttribute('data-bs-toggle')) {
    themeToggle.addEventListener('click', () => {
      const mode = getThemeMode();
      // Cycle: system -> light -> dark -> system
      const cycleMap = { system: 'light', light: 'dark', dark: 'system' };
      const nextMode = cycleMap[mode] || 'system';
      setTheme(nextMode);
    });
  }

  // Bind theme selector dropdowns if present
  document.querySelectorAll('.theme-selector, #settings-theme').forEach((sel) => {
    sel.value = currentMode;
    sel.addEventListener('change', (e) => {
      setTheme(e.target.value);
    });
  });
}

// Make available globally on window
window.setTheme = setTheme;
window.getThemeMode = getThemeMode;
window.getResolvedTheme = getResolvedTheme;
window.initTheme = initTheme;
