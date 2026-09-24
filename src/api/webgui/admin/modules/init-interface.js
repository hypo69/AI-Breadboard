/**
 * Interface Initialization Module - Инициализация компонентов интерфейса
 */

import { initI18n, switchLang, applyTranslations } from '../../js/i18n.js';
import { initTheme, setTheme, getThemeMode, getResolvedTheme } from '../../js/theme.js';
import { initUserSettings, refreshUserProfile } from '../../js/userSettings.js';

export async function initializeInterface() {
  console.log('[AdminInterface] Initializing core components...');

  try {
    // Initialize theme
    initTheme();

    // Initialize i18n
    await initI18n();

    // Initialize user settings
    await initUserSettings();

    // Apply translations
    applyTranslations();

    // Обновляем бейджи активной модели и поиска
    if (typeof window.updateChatBadges === 'function') {
      window.updateChatBadges();
    }

    console.log('[AdminInterface] Core components initialized');
  } catch (error) {
    console.error('[AdminInterface] Initialization error:', error);
    throw error;
  }
}

export function setupGlobalFunctions() {
  // Make functions available globally
  window.switchLang = switchLang;
  window.applyTranslations = applyTranslations;
  window.setTheme = setTheme;
  window.getThemeMode = getThemeMode;
  window.getResolvedTheme = getResolvedTheme;
  window.initUserSettings = initUserSettings;
  window.refreshUserProfile = refreshUserProfile;
  
  // Help and modals
  window.showHelpModal = window.showHelpModal || (() => {});
  window.showChatLogicModal = window.showChatLogicModal || (() => {});
  window.showNotification = window.showNotification || (() => {});

  // API Fallback
  window.api = window.api || {};
  if (!window.api.fetch) {
    window.api.fetch = async function(url, options = {}) {
      const response = await fetch(url, options);
      if (!response.ok) {
        let msg = response.statusText;
        try {
          const data = await response.json();
          if (data && data.detail) {
            if (typeof data.detail === 'string') msg = data.detail;
            else if (Array.isArray(data.detail)) msg = data.detail.map(d => d.msg || JSON.stringify(d)).join(', ');
            else msg = JSON.stringify(data.detail);
          } else if (data && data.message) {
            msg = data.message;
          }
        } catch {}
        throw new Error(`${response.status} ${msg}`);
      }
      return response.json();
    };
  }

  console.log('[AdminInterface] Global functions registered');
}

export function setupLanguageSelector() {
  const langSelectors = document.querySelectorAll('.lang-selector');
  const savedLang = localStorage.getItem('language') || 'ru';

  langSelectors.forEach((selector) => {
    selector.value = savedLang;
    selector.addEventListener('change', (e) => {
      switchLang(e.target.value);
    });
  });

  console.log('[AdminInterface] Language selector setup');
}

export function setupThemeSelector() {
  const themeSelectors = document.querySelectorAll('.theme-selector');
  const savedTheme = getThemeMode();

  themeSelectors.forEach((selector) => {
    selector.value = savedTheme;
    selector.addEventListener('change', (e) => {
      setTheme(e.target.value);
    });
  });

  console.log('[AdminInterface] Theme selector setup');
}

export { initI18n, switchLang, applyTranslations };
export { initTheme, setTheme, getThemeMode, getResolvedTheme };
export { initUserSettings, refreshUserProfile };
