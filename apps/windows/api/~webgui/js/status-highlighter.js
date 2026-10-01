/**
 * =============================================================================
 * Process Name: Windows Js - Status-Highlighter Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля status-highlighter.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/~webgui/js/status-highlighter.js?v=20261001_v1" type="module"></script>
 *
 * File: status-highlighter.js
 * Project: ai-breadboard
 * Package: windows/api/~webgui/js
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-01 13:04:40
 * =============================================================================
 */

/**
 * ═══════════════════════════════════════════════════════════════════════════
 * STATUS HIGHLIGHTER — AI Breadboard WebGUI
 * Глобальный менеджер программного выделения статусов (Зелёный = Включен/Активен, Красный = Выключен/Неактивен)
 * ═══════════════════════════════════════════════════════════════════════════
 */

(function (window, document) {
  'use stricti18n.t('auto__const_positive_keywords_new_set__d0d9d2')active', 'enabled', 'on', 'running', 'online', 'connected', 'true', '1', 'ok', 'success',
    i18n.t('auto___bb3fc3'), i18n.t('auto___b9147a'), i18n.t('auto___547612'), i18n.t('auto___84ce68'), i18n.t('auto___be2f93'), i18n.t('auto___2ae44e'),
    i18n.t('auto___e23dc6'), i18n.t('auto___db1a92'), i18n.t('auto___7a9758'), i18n.t('auto___f56d3f'), i18n.t('auto___448409'), i18n.t('auto___aa37b8'), i18n.t('auto___7f274e'), i18n.t('auto___62e346'), i18n.t('auto___e5498a')
  ]);

  const NEGATIVE_KEYWORDS = new Set([
    'inactive', 'disabled', 'off', 'stopped', 'offline', 'disconnected', 'false', '0', 'error', 'failed', 'failure',
    i18n.t('auto___0b48cc'), i18n.t('auto___3bafb2'), i18n.t('auto___bedfed'), i18n.t('auto___8007e2'), i18n.t('auto___3b5ab2'), i18n.t('auto___5e1a20'),
    i18n.t('auto___037aac'), i18n.t('auto___982686'), i18n.t('auto___a07960'), i18n.t('auto___9f961e'), i18n.t('auto___696924'), i18n.t('auto___c394f7'), i18n.t('auto___79ce37'), i18n.t('auto___287eee')
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
     * Проверяет, является ли значение положительным состоянием (i18n.t('auto___bb3fc3'), i18n.t('auto___84ce68'))
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
     * Проверяет, является ли значение отрицательным состоянием (i18n.t('auto___0b48cc'), i18n.t('auto___037aac'))
     * @param {*} value Проверяемое значение или строка
     * @returns {boolean} True, если состояние отрицательное
     */
    isNegative(value) {
      if (typeof value === 'boolean') return value === false;
      if (typeof value === 'numberi18n.t('auto__return_value_0_if_value_return_false_const_normalized_string_value_trim_tolowercase_if_negative_keywords_has_normalized_return_true_for_const_kw_of_negative_keywords_if_normalized_includes_kw_return_true_return_false__d5d39f')success', 'danger', 'neutrali18n.t('auto__param_value_returns_string_getstatustheme_value_if_this_ispositive_value_return_3bfd60')success';
      if (this.isNegative(value)) return 'danger';
      return 'neutrali18n.t('auto__html_param_value_param_string_customtext_param_string_extraclasses_css_returns_string_html_getbadgehtml_value_customtext__d57324')', extraClasses = '') {
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
        element.classList.add('is-status-negative', 'status-inactivei18n.t('auto__dom_param_htmlelement_document_root_scandom_root_document_const_selectors__5e4ee6')[data-status], [data-state], [data-auto-status], .badge-status, .status-badgei18n.t('auto__const_elements_root_queryselectorall_selectors_elements_foreach_el_this_applyelementstatus_el_mutationobserver_initobserver_if_typeof_mutationobserver__9a1b91')undefined') return;

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
        document.addEventListener('DOMContentLoadedi18n.t('auto__this_startobserving_else_this_startobserving_mutationobserver_startobserving_if_this_observer_document_body_return_this_scandom_document_body_this_observer_observe_document_body_childlist_true_subtree_true_attributes_true_attributefilter__9f67e0')data-status', 'data-state', 'data-auto-status']
      });
    }
  }

  // Экспорт синглтона в глобальную область видимости
  window.StatusHighlighter = new StatusHighlighterEngine();

})(window, document);
