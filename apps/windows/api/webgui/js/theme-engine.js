/**
 * =============================================================================
 * Process Name: Windows Web Styles - Theme Engine
 * =============================================================================
 * Description:
 *   Шаблонизатор и менеджер тем оформления для веб-интерфейса AI Breadboard.
 *   Поддерживает светлые темы (Light, Brick), тёмные темы (Dark Contrast, Terminal),
 *   системный режим, динамическую регистрацию и шаблонизацию UI-селекторов.
 *
 * Usage Examples:
 *   import { themeEngine } from './theme-engine.js';
 *   themeEngine.applyTheme('brick');
 *   themeEngine.registerTheme({ id: 'custom', name: 'Custom Theme', category: 'dark' });
 *
 * File: theme-engine.js
 * Project: ai-breadboard
 * Package: apps.windows.api.webgui.js
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-06 21:10:15
 * =============================================================================
 */

/**
 * Ключ хранения выбранного режима темы в LocalStorage
 */
export const THEME_STORAGE_KEY = 'theme';

/**
 * Режим по умолчанию
 */
export const DEFAULT_THEME_MODE = 'system';

/**
 * Определение стандартных встроенных тем
 */
export const BUILTIN_THEMES = [
  {
    id: 'system',
    name: 'Системная',
    nameEn: 'System',
    category: 'system',
    icon: 'bi-circle-half',
    iconColor: 'text-info',
    description: 'Автоматический выбор темы на основе настроек операционной системы',
    baseType: 'system',
  },
  {
    id: 'light',
    name: 'Светлая (NightView)',
    nameEn: 'Light (NightView)',
    category: 'light',
    icon: 'bi-sun-fill',
    iconColor: 'text-warning',
    description: 'Мягкая светлая тема в стиле NightView без слепящей белизны для комфортного чтения ночью',
    baseType: 'light',
    tokens: { '--about-card-bg': 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)' },
  },
  {
    id: 'brick',
    name: 'Кирпичная (Терракота)',
    nameEn: 'Brick (Terracotta)',
    category: 'light',
    icon: 'bi-bricks',
    iconColor: 'text-danger',
    description: 'Теплая светлая тема в стиле клинкерного кирпича и обожженной глины',
    baseType: 'light',
    tokens: { '--about-card-bg': 'linear-gradient(135deg, #f5e8d4 0%, #e2c8b8 100%)' },
  },
  {
    id: 'dark',
    name: '🌙 Midnight Console',
    nameEn: 'Dark (High-Contrast)',
    category: 'dark',
    icon: 'bi-moon-stars-fill',
    iconColor: 'text-primary',
    description: 'Глубокая контрастная тёмная тема для удобной работы в ночное время',
    baseType: 'dark',
  },
  {
    id: 'terminal',
    name: 'Терминал (Matrix / CRT)',
    nameEn: 'Terminal (Matrix / CRT)',
    category: 'dark',
    icon: 'bi-terminal-fill',
    iconColor: 'text-success',
    description: 'Тёмная тема в ретро-стиле зеленого фосфорного терминала с моноширинными акцентами',
    baseType: 'dark',
  },
];

/**
 * Класс шаблонизатора и оркестратора тем оформления
 */
export class ThemeEngine {
  constructor() {
    /** @type {Map<string, Object>} */
    this.registry = new Map();
    this.mediaQueryListenerAttached = false;
    this._dynamicStyleEl = null;

    // Регистрация встроенных тем
    for (const theme of BUILTIN_THEMES) {
      this.registry.set(theme.id, { ...theme });
    }
  }

  /**
   * Регистрирует новую тему в реестре шаблонизатора.
   * @param {Object} themeDef - Определение темы
   * @param {string} themeDef.id - Уникальный идентификатор темы
   * @param {string} themeDef.name - Отображаемое имя темы (русский)
   * @param {string} [themeDef.nameEn] - Отображаемое имя темы (английский)
   * @param {'light'|'dark'|'system'} themeDef.category - Категория темы
   * @param {string} [themeDef.icon] - Иконка Bootstrap Icons (например, 'bi-palette')
   * @param {string} [themeDef.iconColor] - CSS класс цвета иконки (например, 'text-warning')
   * @param {string} [themeDef.description] - Описание темы
   * @param {'light'|'dark'} [themeDef.baseType] - Базовый тип темы (светлая/тёмная)
   * @param {Object<string, string>} [themeDef.tokens] - Словарь CSS-переменных
   */
  registerTheme(themeDef) {
    if (!themeDef || !themeDef.id) {
      console.warn('[ThemeEngine] Некорректное определение темы:', themeDef);
      return;
    }

    const baseType = themeDef.baseType || (themeDef.category === 'dark' ? 'dark' : 'light');
    this.registry.set(themeDef.id, {
      id: themeDef.id,
      name: themeDef.name || themeDef.id,
      nameEn: themeDef.nameEn || themeDef.name || themeDef.id,
      category: themeDef.category || 'dark',
      icon: themeDef.icon || 'bi-palette',
      iconColor: themeDef.iconColor || 'text-info',
      description: themeDef.description || '',
      baseType,
      tokens: themeDef.tokens || null,
    });

    if (themeDef.tokens) {
      this._applyDynamicTokens();
    }
  }

  /**
   * Возвращает определение темы по идентификатору.
   * @param {string} themeId
   * @returns {Object|null}
   */
  getTheme(themeId) {
    return this.registry.get(themeId) || null;
  }

  /**
   * Возвращает список всех зарегистрированных тем.
   * @returns {Array<Object>}
   */
  getAllThemes() {
    return Array.from(this.registry.values());
  }

  /**
   * Возвращает темы, отфильтрованные по категории ('light' | 'dark' | 'system').
   * @param {'light'|'dark'|'system'} category
   * @returns {Array<Object>}
   */
  getThemesByCategory(category) {
    return this.getAllThemes().filter((t) => t.category === category);
  }

  /**
   * Получает сохранённый режим темы из LocalStorage.
   * @returns {string}
   */
  getSavedMode() {
    const saved = localStorage.getItem(THEME_STORAGE_KEY);
    if (saved && this.registry.has(saved)) {
      return saved;
    }
    return DEFAULT_THEME_MODE;
  }

  /**
   * Разрешает эффективный идентификатор темы ('light', 'dark', 'brick', 'terminal' и т.д.)
   * @param {string} [mode]
   * @returns {string}
   */
  resolveTheme(mode = this.getSavedMode()) {
    if (mode === 'system') {
      const prefersDark =
        typeof window !== 'undefined' &&
        window.matchMedia &&
        window.matchMedia('(prefers-color-scheme: dark)').matches;
      return prefersDark ? 'dark' : 'light';
    }

    if (this.registry.has(mode)) {
      return mode;
    }
    return 'dark';
  }

  /**
   * Определяет базовый режим Bootstrap ('light' | 'dark') для текущей темы.
   * @param {string} resolvedThemeId
   * @returns {'light'|'dark'}
   */
  getBsTheme(resolvedThemeId) {
    const theme = this.getTheme(resolvedThemeId);
    if (theme) {
      return theme.baseType || (theme.category === 'dark' ? 'dark' : 'light');
    }
    return resolvedThemeId === 'light' || resolvedThemeId === 'brick' ? 'light' : 'dark';
  }

  /**
   * Применяет тему к DOM, обновляет атрибуты и UI-элементы.
   * @param {string} mode
   */
  applyTheme(mode) {
    if (!mode || !this.registry.has(mode)) {
      mode = DEFAULT_THEME_MODE;
    }

    localStorage.setItem(THEME_STORAGE_KEY, mode);

    const resolved = this.resolveTheme(mode);
    const bsTheme = this.getBsTheme(resolved);

    if (typeof document !== 'undefined') {
      // 1. Установка атрибутов на <html>
      document.documentElement.setAttribute('data-theme', resolved);
      document.documentElement.setAttribute('data-bs-theme', bsTheme);
      document.documentElement.setAttribute('data-theme-mode', mode);

      // 2. Обновление иконок и кнопок
      this._updateThemeUI(mode, resolved);

      // 3. Синхронизация селекторов выбора тем
      this.syncSelectInputs(mode);
    }

    // 4. Оповещение слушателей через CustomEvent
    if (typeof window !== 'undefined') {
      window.dispatchEvent(
        new CustomEvent('themechanged', {
          detail: {
            mode,
            resolved,
            bsTheme,
            themeMeta: this.getTheme(resolved),
          },
        })
      );
    }
  }

  /**
   * Генерирует HTML-разметку опций для тега <select> с группировкой по категориям.
   * @param {string} [currentMode]
   * @returns {string}
   */
  renderOptionsHTML(currentMode = this.getSavedMode()) {
    const lightThemes = this.getThemesByCategory('light');
    const darkThemes = this.getThemesByCategory('dark');
    const systemThemes = this.getThemesByCategory('system');

    let html = '';

    if (systemThemes.length > 0) {
      for (const t of systemThemes) {
        const isSelected = t.id === currentMode ? ' selected' : '';
        html += `<option value="${t.id}"${isSelected}>🌓 ${t.name}</option>\n`;
      }
    }

    if (lightThemes.length > 0) {
      html += '<optgroup label="☀️ Светлые темы">\n';
      for (const t of lightThemes) {
        const isSelected = t.id === currentMode ? ' selected' : '';
        const iconSymbol = t.id === 'brick' ? '🧱' : '☀️';
        html += `  <option value="${t.id}"${isSelected}>${iconSymbol} ${t.name}</option>\n`;
      }
      html += '</optgroup>\n';
    }

    if (darkThemes.length > 0) {
      html += '<optgroup label="🌙 Тёмные темы">\n';
      for (const t of darkThemes) {
        const isSelected = t.id === currentMode ? ' selected' : '';
        const iconSymbol = t.id === 'terminal' ? '📟' : '🌙';
        html += `  <option value="${t.id}"${isSelected}>${iconSymbol} ${t.name}</option>\n`;
      }
      html += '</optgroup>\n';
    }

    return html;
  }

  /**
   * Синхронизирует все элементы <select> выбора темы на странице.
   * @param {string} [mode]
   */
  syncSelectInputs(mode = this.getSavedMode()) {
    if (typeof document === 'undefined') return;

    const selectors = document.querySelectorAll(
      '.theme-selector, #apps-theme-selector, #settings-theme, #modal-theme-selector'
    );

    selectors.forEach((selectEl) => {
      // Если у селектора еще нет сгенерированных опций с optgroup, наполняем его
      if (!selectEl.querySelector('optgroup')) {
        selectEl.innerHTML = this.renderOptionsHTML(mode);
      } else if (selectEl.value !== mode) {
        selectEl.value = mode;
      }
    });
  }

  /**
   * Инициализирует менеджер тем, регистрирует обработчики событий и применяет начальную тему.
   */
  init() {
    const currentMode = this.getSavedMode();
    this.applyTheme(currentMode);

    // Подписка на изменение системной темы
    if (!this.mediaQueryListenerAttached && typeof window !== 'undefined' && window.matchMedia) {
      try {
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        const handler = () => {
          if (this.getSavedMode() === 'system') {
            this.applyTheme('system');
          }
        };
        if (mediaQuery.addEventListener) {
          mediaQuery.addEventListener('change', handler);
        } else if (mediaQuery.addListener) {
          mediaQuery.addListener(handler);
        }
        this.mediaQueryListenerAttached = true;
      } catch (e) {
        console.warn('[ThemeEngine] Не удалось подписаться на prefers-color-scheme:', e);
      }
    }

    if (typeof document === 'undefined') return;

    // Наполнение всех селекторов опциями
    this.syncSelectInputs(currentMode);

    // Привязка слушателей изменений к селекторам тем
    document.querySelectorAll(
      '.theme-selector, #apps-theme-selector, #settings-theme, #modal-theme-selector'
    ).forEach((sel) => {
      sel.addEventListener('change', (e) => {
        this.applyTheme(e.target.value);
      });
    });

    // Привязка кликов по кнопкам data-theme-value
    document.querySelectorAll('[data-theme-value]').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const selected = btn.getAttribute('data-theme-value');
        if (selected) {
          this.applyTheme(selected);
        }
      });
    });

    // Привязка кнопки быстрого циклического переключения тем (legacy / toggle button)
    const toggleBtn = document.getElementById('theme-toggle');
    if (toggleBtn && !toggleBtn.hasAttribute('data-bs-toggle')) {
      toggleBtn.addEventListener('click', () => {
        const mode = this.getSavedMode();
        // Цикл переключения: system -> light -> brick -> dark -> terminal -> system
        const cycle = ['system', 'light', 'brick', 'dark', 'terminal'];
        const currentIndex = cycle.indexOf(mode);
        const nextMode = cycle[(currentIndex + 1) % cycle.length];
        this.applyTheme(nextMode);
      });
    }
  }

  /**
   * Обновляет UI-иконки, подсказки и активные состояния в выпадающих меню.
   * @private
   */
  _updateThemeUI(mode, resolved) {
    const activeTheme = this.getTheme(resolved) || this.getTheme('dark');
    const modeTheme = this.getTheme(mode);

    const iconEl = document.getElementById('theme-icon');
    const toggleBtn = document.getElementById('theme-toggle');
    const dropdownBtn = document.getElementById('theme-dropdown');

    const iconClass = modeTheme ? modeTheme.icon : 'bi-circle-half';
    const iconColor = modeTheme ? modeTheme.iconColor : 'text-info';
    const titleText =
      mode === 'system'
        ? `Системная тема (${activeTheme ? activeTheme.name : resolved})`
        : modeTheme
        ? modeTheme.name
        : resolved;

    if (iconEl) {
      iconEl.className = `bi ${iconClass} ${iconColor}`;
    }

    if (dropdownBtn) {
      dropdownBtn.setAttribute('title', titleText);
    }

    if (toggleBtn) {
      toggleBtn.innerHTML = `<i class="bi ${iconClass} ${iconColor}"></i>`;
      toggleBtn.setAttribute('title', titleText);
    }

    // Обновление галочек в выпадающих меню
    document.querySelectorAll('.theme-check-icon').forEach((icon) => {
      const target = icon.getAttribute('data-theme-check');
      if (target === mode) {
        icon.classList.remove('d-none');
      } else {
        icon.classList.add('d-none');
      }
    });

    // Обновление active класса
    document.querySelectorAll('[data-theme-value]').forEach((item) => {
      const val = item.getAttribute('data-theme-value');
      if (val === mode) {
        item.classList.add('active');
      } else {
        item.classList.remove('active');
      }
    });
  }

  /**
   * Инжектирует динамические стили для зарегистрированных кастомных тем с токенами.
   * @private
   */
  _applyDynamicTokens() {
    if (typeof document === 'undefined') return;

    let css = '';
    for (const [id, def] of this.registry.entries()) {
      if (def.tokens && typeof def.tokens === 'object') {
        css += `[data-theme="${id}"] {\n`;
        for (const [prop, val] of Object.entries(def.tokens)) {
          css += `  ${prop}: ${val};\n`;
        }
        css += '}\n';
      }
    }

    if (!this._dynamicStyleEl) {
      this._dynamicStyleEl = document.createElement('style');
      this._dynamicStyleEl.id = 'theme-engine-dynamic-styles';
      document.head.appendChild(this._dynamicStyleEl);
    }
    this._dynamicStyleEl.textContent = css;
  }
}

/**
 * Синглтон экземпляр движка тем
 */
export const themeEngine = new ThemeEngine();

// Глобальный экспорт на window
if (typeof window !== 'undefined') {
  window.ThemeEngine = ThemeEngine;
  window.themeEngine = themeEngine;
}
