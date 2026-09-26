/**
 * ═══════════════════════════════════════════════════════════════════════════
 * STATUS HIGHLIGHTER — AI Breadboard WebGUI
 * Глобальный менеджер программного выделения статусов (Зелёный = Включен/Активен, Красный = Выключен/Неактивен)
 * ═══════════════════════════════════════════════════════════════════════════
 */

(function (window, document) {
  'use strict';

  // Множества ключевых слов для положительных (зелёных) и отрицательных (красных) состояний
  const POSITIVE_KEYWORDS = new Set([
    'active', 'enabled', 'on', 'running', 'online', 'connected', 'true', '1', 'ok', 'success',
    'включен', 'включена', 'включено', 'активен', 'активна', 'активно',
    'работает', 'запущен', 'запущена', 'онлайн', 'подключен', 'подключено', 'успех', 'успешно', 'в норме'
  ]);

  const NEGATIVE_KEYWORDS = new Set([
    'inactive', 'disabled', 'off', 'stopped', 'offline', 'disconnected', 'false', '0', 'error', 'failed', 'failure',
    'выключен', 'выключена', 'выключено', 'неактивен', 'неактивна', 'неактивно',
    'остановлен', 'остановлена', 'офлайн', 'отключен', 'отключено', 'ошибка', 'сбой', 'не запущен'
  ]);

  /**
   * Класс системы программной подсветки статусов
   */
  class StatusHighlighterEngine {
    constructor() {
      this.observer = null;
      this.initObserver();
    }

    /**
     * Проверяет, является ли значение положительным состоянием ("включен", "активен")
     * @param {*} value Проверяемое значение или строка
     * @returns {boolean} True, если состояние положительное
     */
    isPositive(value) {
      if (typeof value === 'boolean') return value === true;
      if (typeof value === 'number') return value > 0;
      if (!value) return false;

      const normalized = String(value).trim().toLowerCase();
      if (POSITIVE_KEYWORDS.has(normalized)) return true;

      // Проверка подстрок
      for (const kw of POSITIVE_KEYWORDS) {
        if (normalized.includes(kw)) return true;
      }
      return false;
    }

    /**
     * Проверяет, является ли значение отрицательным состоянием ("выключен", "остановлен")
     * @param {*} value Проверяемое значение или строка
     * @returns {boolean} True, если состояние отрицательное
     */
    isNegative(value) {
      if (typeof value === 'boolean') return value === false;
      if (typeof value === 'number') return value === 0;
      if (!value) return false;

      const normalized = String(value).trim().toLowerCase();
      if (NEGATIVE_KEYWORDS.has(normalized)) return true;

      // Проверка подстрок
      for (const kw of NEGATIVE_KEYWORDS) {
        if (normalized.includes(kw)) return true;
      }
      return false;
    }

    /**
     * Возвращает название цветовой темы статуса ('success', 'danger', 'neutral')
     * @param {*} value Состояние
     * @returns {string} Тема статуса
     */
    getStatusTheme(value) {
      if (this.isPositive(value)) return 'success';
      if (this.isNegative(value)) return 'danger';
      return 'neutral';
    }

    /**
     * Генерирует HTML-строку для бейджа статуса
     * @param {*} value Значение состояния
     * @param {string} [customText] Кастомный текст бейджа
     * @param {string} [extraClasses] Дополнительные CSS классы
     * @returns {string} HTML бейджа
     */
    getBadgeHtml(value, customText = '', extraClasses = '') {
      const isPos = this.isPositive(value);
      const isNeg = this.isNegative(value);

      let themeClass = 'bg-secondary-subtle text-secondary border';
      if (isPos) {
        themeClass = 'bg-success-subtle text-success border border-success-subtle';
      } else if (isNeg) {
        themeClass = 'bg-danger-subtle text-danger border border-danger-subtle';
      }

      const displayText = customText || String(value);
      return `<span class="badge ${themeClass} ${extraClasses}">${displayText}</span>`;
    }

    /**
     * Программно обновляет стили элемента в зависимости от его статуса
     * @param {HTMLElement} element Элемент для подсветки
     */
    applyElementStatus(element) {
      if (!element || !(element instanceof HTMLElement)) return;

      const statusVal = element.getAttribute('data-status') ||
                        element.getAttribute('data-state') ||
                        element.getAttribute('data-auto-status') ||
                        element.textContent;

      if (!statusVal) return;

      const isPos = this.isPositive(statusVal);
      const isNeg = this.isNegative(statusVal);

      if (isPos) {
        element.classList.remove('is-status-negative', 'status-inactive', 'status-disabled', 'bg-danger', 'text-danger', 'bg-danger-subtle', 'bg-secondary-subtle', 'text-secondary');
        element.classList.add('is-status-positive', 'status-active');
      } else if (isNeg) {
        element.classList.remove('is-status-positive', 'status-active', 'status-enabled', 'bg-success', 'text-success', 'bg-success-subtle', 'bg-secondary-subtle', 'text-secondary');
        element.classList.add('is-status-negative', 'status-inactive');
      }
    }

    /**
     * Сканирует DOM-дерево и применяет подсвечивание ко всем элементам статуса
     * @param {HTMLElement|Document} [root] Корневой элемент для поиска
     */
    scanDOM(root = document) {
      const selectors = '[data-status], [data-state], [data-auto-status], .badge-status, .status-badge';
      const elements = root.querySelectorAll(selectors);
      elements.forEach(el => this.applyElementStatus(el));
    }

    /**
     * Инициализирует MutationObserver для автоматической подсветки создаваемых/изменяемых элементов
     */
    initObserver() {
      if (typeof MutationObserver === 'undefined') return;

      this.observer = new MutationObserver((mutations) => {
        for (const mutation of mutations) {
          if (mutation.type === 'childList') {
            mutation.addedNodes.forEach(node => {
              if (node.nodeType === Node.ELEMENT_NODE) {
                this.applyElementStatus(node);
                if (node.querySelectorAll) {
                  this.scanDOM(node);
                }
              }
            });
          } else if (mutation.type === 'attributes') {
            const attr = mutation.attributeName;
            if (attr === 'data-status' || attr === 'data-state' || attr === 'data-auto-status') {
              this.applyElementStatus(mutation.target);
            }
          }
        }
      });

      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => this.startObserving());
      } else {
        this.startObserving();
      }
    }

    /**
     * Запускает наблюдение MutationObserver за документом
     */
    startObserving() {
      if (!this.observer || !document.body) return;
      this.scanDOM(document.body);
      this.observer.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['data-status', 'data-state', 'data-auto-status']
      });
    }
  }

  // Экспорт синглтона в глобальную область видимости
  window.StatusHighlighter = new StatusHighlighterEngine();

})(window, document);
