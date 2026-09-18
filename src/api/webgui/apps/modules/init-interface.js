/**
 * apps/modules/init-interface.js — Инициализация тем, языка и глобального окружения /apps
 */

import { initI18n, switchLang, applyTranslations } from '../../js/i18n.js';
import { initTheme, setTheme, getThemeMode, getResolvedTheme } from '../../js/theme.js';

export function setupGlobalApi() {
  window.switchLang = switchLang;
  window.applyTranslations = applyTranslations;
  window.setTheme = setTheme;
  window.getThemeMode = getThemeMode;
  window.getResolvedTheme = getResolvedTheme;

  window.api = window.api || {
    async fetch(url, options = {}) {
      const response = await fetch(url, options);
      if (!response.ok) {
        let msg = response.statusText;
        try {
          const data = await response.json();
          if (data && data.detail) {
            if (typeof data.detail === 'string') {
              msg = data.detail;
            } else if (Array.isArray(data.detail)) {
              msg = data.detail.map(d => d.msg || JSON.stringify(d)).join(', ');
            } else {
              msg = JSON.stringify(data.detail);
            }
          }
        } catch {}
        throw new Error(`${response.status} ${msg}`);
      }
      return response.json();
    }
  };

  window.appsStatusMap = window.appsStatusMap || {};
}

export async function setupThemeAndLang() {
  initTheme();

  const savedLang = localStorage.getItem('app_language') || 'ru';
  await initI18n(savedLang);

  const langSel = document.getElementById('apps-lang-selector');
  if (langSel) {
    langSel.value = savedLang;
    langSel.addEventListener('change', (e) => {
      switchLang(e.target.value);
    });
  }

  const themeSel = document.getElementById('apps-theme-selector');
  if (themeSel) {
    themeSel.value = getThemeMode();
    themeSel.addEventListener('change', (e) => {
      setTheme(e.target.value);
    });
  }
}
