/**
 * =============================================================================
 * Process Name: Windows Js - Theme Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля theme и интеграции с ThemeEngine.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/webgui/js/theme.js?v=20261004_v17" type="module"></script>
 *
 *   JavaScript Import:
 *     import { getThemeMode, getResolvedTheme, setTheme, themeEngine } from '/windows/api/webgui/js/theme.js';
 *
 * File: theme.js
 * Project: ai-breadboard
 * Package: windows/api/webgui/js
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-04 12:12:00
 * =============================================================================
 */

import { themeEngine, ThemeEngine, THEME_STORAGE_KEY, DEFAULT_THEME_MODE, BUILTIN_THEMES } from './theme-engine.js';

/**
 * Получает сохранённый режим темы пользователя.
 * @returns {string}
 */
export function getThemeMode() {
  return themeEngine.getSavedMode();
}

/**
 * Разрешает эффективную тему оформления ('light' | 'dark' | 'brick' | 'terminal').
 * @param {string} [mode]
 * @returns {string}
 */
export function getResolvedTheme(mode = getThemeMode()) {
  return themeEngine.resolveTheme(mode);
}

/**
 * Устанавливает тему оформления и применяет её ко всем элементам интерфейса.
 * @param {string} mode
 */
export function setTheme(mode) {
  themeEngine.applyTheme(mode);
}

/**
 * Инициализирует менеджер тем и слушатели событий при загрузке страницы.
 */
export function initTheme() {
  themeEngine.init();
}

// Экспорт синглтона и констант
export { themeEngine, ThemeEngine, THEME_STORAGE_KEY, DEFAULT_THEME_MODE, BUILTIN_THEMES };

// Экспорт в глобальный объект window
if (typeof window !== 'undefined') {
  window.setTheme = setTheme;
  window.getThemeMode = getThemeMode;
  window.getResolvedTheme = getResolvedTheme;
  window.initTheme = initTheme;
  window.themeEngine = themeEngine;
  window.ThemeEngine = ThemeEngine;
}
