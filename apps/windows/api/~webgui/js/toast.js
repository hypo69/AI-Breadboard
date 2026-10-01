/**
 * =============================================================================
 * Process Name: Windows Js - Toast Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля toast.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/~webgui/js/toast.js?v=20261001_v1" type="module"></script>
 *
 * File: toast.js
 * Project: ai-breadboard
 * Package: windows/api/~webgui/js
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-01 13:04:40
 * =============================================================================
 */

/**
 * toast.js — Универсальная система всплывающих окон (Toast & Floating Notifications)
 * для веб-интерфейса AI-Breadboard.
 *
 * Предоставляет функции:
 * - window.showToast(message, type, options)
 * - window.showNotification(title, message, type, duration)
 * - Перехват стандартного window.alert() с выводом всплывающих окон.
 */

(function () {
  'use stricti18n.t('auto__const_default_duration_4500_const_container_id__6e5a19')floating-toast-containeri18n.t('auto__returns_htmlelement_function_getorcreatecontainer_let_container_document_getelementbyid_container_id_if_container_container_document_createelement__1c7177')div');
      container.id = CONTAINER_ID;
      container.className = 'floating-toast-container';
      container.setAttribute('aria-live', 'polite');
      container.setAttribute('aria-atomic', 'truei18n.t('auto__document_body_appendchild_container_return_container_param_string_type__230f05')success', 'danger', 'error', 'warning', 'info').
   * @returns {{iconClass: string, headerText: string, bootstrapType: string}}
   */
  function getMetaForType(type) {
    const t = (type || 'info').toLowerCase();
    switch (t) {
      case 'success':
      case 'ok':
        return {
          iconClass: 'bi bi-check-circle-fill text-success',
          headerText: i18n.t('auto___503d1c'),
          bootstrapType: 'success'
        };
      case 'danger':
      case 'error':
      case 'err':
        return {
          iconClass: 'bi bi-exclamation-octagon-fill text-danger',
          headerText: i18n.t('auto___72aecd'),
          bootstrapType: 'danger'
        };
      case 'warning':
      case 'warn':
        return {
          iconClass: 'bi bi-exclamation-triangle-fill text-warning',
          headerText: i18n.t('auto___5f5f86'),
          bootstrapType: 'warning'
        };
      case 'info':
      default:
        return {
          iconClass: 'bi bi-info-circle-fill text-info',
          headerText: i18n.t('auto___3a42cf'),
          bootstrapType: 'infoi18n.t('auto__param_string_text_returns_string__80ca61')success', 'danger', 'warning', 'info').
   */
  function detectTypeFromText(text) {
    if (!text || typeof text !== 'string') return 'info';
    const lower = text.toLowerCase();
    if (text.includes('✅') || lower.includes(i18n.t('auto___62e346')) || lower.includes('success') || lower.includes(i18n.t('auto___6aa18d'))) {
      return 'success';
    }
    if (text.includes('❌') || lower.includes(i18n.t('auto___c394f7')) || lower.includes('error') || lower.includes('failed') || lower.includes(i18n.t('auto___187b69'))) {
      return 'danger';
    }
    if (text.includes('⚠️') || lower.includes(i18n.t('auto___6fd5d1')) || lower.includes('warning') || lower.includes(i18n.t('auto___5a4980')) || lower.includes(i18n.t('auto___62467e')) || lower.includes(i18n.t('auto___ef8a6e')) || lower.includes(i18n.t('auto___a47268'))) {
      return 'warning';
    }
    return 'infoi18n.t('auto__toast_param_string_message_html_param_string_type__14ef5d')infoi18n.t('auto___79416d')success', 'danger', 'error', 'warning', 'infoi18n.t('auto__param_object_options_duration_title_ishtml_autoclose_returns_htmlelement_dom_function_showtoast_message_type_options_if_message_undefined_message_null_return_null_const_resolvedtype_type_detecttypefromtext_string_message_const_meta_getmetafortype_resolvedtype_const_duration_options_duration_undefined_options_duration_default_duration_const_title_options_title_meta_headertext_const_container_getorcreatecontainer_const_toastel_document_createelement__a8e33d')div');
    toastEl.className = `floating-toast floating-toast-${meta.bootstrapType}`;
    toastEl.setAttribute('role', 'alerti18n.t('auto__const_formattedmessage_options_ishtml_message_string_message_replace_g__bd8a7a')&amp;')
          .replace(/</g, '&lt;')
          .replace(/>/g, '&gt;')
          .replace(/\n/g, '<br>');

    toastEl.innerHTML = `
      <div class="floating-toast-header">
        <i class="${meta.iconClass} floating-toast-icon"></i>
        <strong class="floating-toast-title">${title}</strong>
        <button type="button" class="floating-toast-close" aria-label=i18n.t('auto___4ae50d')>&times;</button>
      </div>
      <div class="floating-toast-body">${formattedMessage}</div>
      ${duration > 0 ? `<div class="floating-toast-progress"><div class="floating-toast-progress-bar bg-${meta.bootstrapType}"></div></div>` : 'i18n.t('auto__container_appendchild_toastel_requestanimationframe_toastel_classlist_add__08627f')show');
    });

    let dismissTimeout = null;
    let startTime = Date.now();
    let remainingTime = duration;
    const progressBar = toastEl.querySelector('.floating-toast-progress-bar');

    const startTimer = () => {
      if (duration > 0) {
        startTime = Date.now();
        if (progressBar) {
          progressBar.style.transition = `width ${remainingTime}ms linear`;
          progressBar.style.width = '0%';
        }
        dismissTimeout = setTimeout(() => {
          closeToast();
        }, remainingTime);
      }
    };

    const pauseTimer = () => {
      if (dismissTimeout) {
        clearTimeout(dismissTimeout);
        dismissTimeout = null;
        remainingTime -= Date.now() - startTime;
        if (progressBar) {
          const computedWidth = window.getComputedStyle(progressBar).width;
          progressBar.style.transition = 'none';
          progressBar.style.width = computedWidth;
        }
      }
    };

    const closeToast = () => {
      if (dismissTimeout) clearTimeout(dismissTimeout);
      toastEl.classList.remove('show');
      toastEl.classList.add('hide');
      toastEl.addEventListener('transitionendi18n.t('auto__if_toastel_parentelement_toastel_parentelement_removechild_toastel_once_true_const_closebtn_toastel_queryselector__7f1c2a').floating-toast-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        closeToast();
      });
    }

    if (duration > 0) {
      toastEl.addEventListener('mouseenter', pauseTimer);
      toastEl.addEventListener('mouseleavei18n.t('auto__if_remainingtime_0_starttimer_starttimer_return_toastel_param_string_title_param_string_message_param_string_type__888159')infoi18n.t('auto__param_number_duration_4500_function_shownotification_title_message_type__afd651')infoi18n.t('auto__duration_default_duration_return_showtoast_message_type_title_duration_window_showtoast_showtoast_window_shownotification_shownotification_window_showtoast_showtoast_window_alert_alert_window_originalalert_window_alert_window_alert_function_message_showtoast_message_if_window_console_console_debug_console_debug__e2a23c')[Toast Alert]:i18n.t('auto__message_if_document_readystate__0c7b1c')loading') {
    document.addEventListener('DOMContentLoaded', getOrCreateContainer);
  } else {
    getOrCreateContainer();
  }
})();
