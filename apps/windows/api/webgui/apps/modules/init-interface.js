/**
 * =============================================================================
 * Process Name: Windows Modules - Init-Interface Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля init-interface.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/webgui/apps/modules/init-interface.js?v=20261006_v10" type="module"></script>
 *
 *   JavaScript Import:
 *     import { setupGlobalApi, setupThemeAndLang } from '/windows/api/webgui/apps/modules/init-interface.js';
 *
 * File: init-interface.js
 * Project: ai-breadboard
 * Package: windows/api/webgui/apps/modules
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-06 22:15:00
 * =============================================================================
 */

/**
 * apps/modules/init-interface.js — Инициализация тем, языка и глобального окружения /apps
 */

import { initI18n, switchLang, switchLocale, applyTranslations, normalizeLocaleTag, getCurrentLocale, getCurrentLang } from '../../js/i18n.js';
import { initTheme, setTheme, getThemeMode, getResolvedTheme, themeEngine, ThemeEngine } from '../../js/theme.js';

export function setupGlobalApi() {
  window.switchLang = switchLang;
  window.switchLocale = switchLocale;
  window.normalizeLocaleTag = normalizeLocaleTag;
  window.getCurrentLocale = getCurrentLocale;
  window.getCurrentLang = getCurrentLang;
  window.applyTranslations = applyTranslations;
  window.setTheme = setTheme;
  window.getThemeMode = getThemeMode;
  window.getResolvedTheme = getResolvedTheme;
  window.themeEngine = themeEngine;
  window.ThemeEngine = ThemeEngine;

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

  // Инициализация i18n с автоматической проверкой URL параметров (?region=ru-ru и т.д.)
  await initI18n();

  const langSel = document.getElementById('apps-lang-selector');
  if (langSel) {
    const curLocale = getCurrentLocale();
    const curLang = getCurrentLang();
    const matchLocale = Array.from(langSel.options).find(opt => opt.value.toLowerCase() === curLocale.toLowerCase());
    const matchLang = Array.from(langSel.options).find(opt => opt.value.toLowerCase() === curLang.toLowerCase());
    if (matchLocale) langSel.value = matchLocale.value;
    else if (matchLang) langSel.value = matchLang.value;

    langSel.addEventListener('change', (e) => {
      switchLocale(e.target.value);
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
