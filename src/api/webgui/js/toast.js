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
  'use strict';

  // Конфигурация по умолчанию
  const DEFAULT_DURATION = 4500;
  const CONTAINER_ID = 'floating-toast-container';

  /**
   * Инициализирует контейнер для всплывающих окон.
   * @returns {HTMLElement} Элемент контейнера.
   */
  function getOrCreateContainer() {
    let container = document.getElementById(CONTAINER_ID);
    if (!container) {
      container = document.createElement('div');
      container.id = CONTAINER_ID;
      container.className = 'floating-toast-container';
      container.setAttribute('aria-live', 'polite');
      container.setAttribute('aria-atomic', 'true');
      document.body.appendChild(container);
    }
    return container;
  }

  /**
   * Определяет иконку и заголовок по типу уведомления.
   * @param {string} type - Тип ('success', 'danger', 'error', 'warning', 'info').
   * @returns {{iconClass: string, headerText: string, bootstrapType: string}}
   */
  function getMetaForType(type) {
    const t = (type || 'info').toLowerCase();
    switch (t) {
      case 'success':
      case 'ok':
        return {
          iconClass: 'bi bi-check-circle-fill text-success',
          headerText: 'Успешно',
          bootstrapType: 'success'
        };
      case 'danger':
      case 'error':
      case 'err':
        return {
          iconClass: 'bi bi-exclamation-octagon-fill text-danger',
          headerText: 'Ошибка',
          bootstrapType: 'danger'
        };
      case 'warning':
      case 'warn':
        return {
          iconClass: 'bi bi-exclamation-triangle-fill text-warning',
          headerText: 'Внимание',
          bootstrapType: 'warning'
        };
      case 'info':
      default:
        return {
          iconClass: 'bi bi-info-circle-fill text-info',
          headerText: 'Уведомление',
          bootstrapType: 'info'
        };
    }
  }

  /**
   * Автоматически определяет тип уведомления по содержимому сообщения.
   * @param {string} text - Текст сообщения.
   * @returns {string} Определенный тип ('success', 'danger', 'warning', 'info').
   */
  function detectTypeFromText(text) {
    if (!text || typeof text !== 'string') return 'info';
    const lower = text.toLowerCase();
    if (text.includes('✅') || lower.includes('успешно') || lower.includes('success') || lower.includes('готов')) {
      return 'success';
    }
    if (text.includes('❌') || lower.includes('ошибка') || lower.includes('error') || lower.includes('failed') || lower.includes('не удалось')) {
      return 'danger';
    }
    if (text.includes('⚠️') || lower.includes('внимание') || lower.includes('warning') || lower.includes('заполните') || lower.includes('пожалуйста, выберите') || lower.includes('пожалуйста выберите') || lower.includes('укажите')) {
      return 'warning';
    }
    return 'info';
  }

  /**
   * Отображает всплывающее окно (Toast).
   * @param {string} message - Текст сообщения или HTML.
   * @param {string} [type='info'] - Тип сообщения ('success', 'danger', 'error', 'warning', 'info').
   * @param {Object} [options={}] - Дополнительные параметры (duration, title, isHtml, autoClose).
   * @returns {HTMLElement} DOM-элемент тоста.
   */
  function showToast(message, type, options = {}) {
    if (message === undefined || message === null) return null;

    // Если тип не указан, пытаемся определить его автоматически по тексту
    const resolvedType = type || detectTypeFromText(String(message));
    const meta = getMetaForType(resolvedType);
    const duration = options.duration !== undefined ? options.duration : DEFAULT_DURATION;
    const title = options.title || meta.headerText;

    const container = getOrCreateContainer();

    const toastEl = document.createElement('div');
    toastEl.className = `floating-toast floating-toast-${meta.bootstrapType}`;
    toastEl.setAttribute('role', 'alert');

    // Форматирование текста (сохранение переводов строк)
    const formattedMessage = options.isHtml
      ? message
      : String(message)
          .replace(/&/g, '&amp;')
          .replace(/</g, '&lt;')
          .replace(/>/g, '&gt;')
          .replace(/\n/g, '<br>');

    toastEl.innerHTML = `
      <div class="floating-toast-header">
        <i class="${meta.iconClass} floating-toast-icon"></i>
        <strong class="floating-toast-title">${title}</strong>
        <button type="button" class="floating-toast-close" aria-label="Закрыть">&times;</button>
      </div>
      <div class="floating-toast-body">${formattedMessage}</div>
      ${duration > 0 ? `<div class="floating-toast-progress"><div class="floating-toast-progress-bar bg-${meta.bootstrapType}"></div></div>` : ''}
    `;

    container.appendChild(toastEl);

    // Анимация появления
    requestAnimationFrame(() => {
      toastEl.classList.add('show');
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
      toastEl.addEventListener('transitionend', () => {
        if (toastEl.parentElement) {
          toastEl.parentElement.removeChild(toastEl);
        }
      }, { once: true });
    };

    // Слушатели событий
    const closeBtn = toastEl.querySelector('.floating-toast-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        closeToast();
      });
    }

    if (duration > 0) {
      toastEl.addEventListener('mouseenter', pauseTimer);
      toastEl.addEventListener('mouseleave', () => {
        if (remainingTime > 0) startTimer();
      });
      startTimer();
    }

    return toastEl;
  }

  /**
   * Отображает уведомление с заголовком и текстом.
   * @param {string} title - Заголовок.
   * @param {string} message - Текст сообщения.
   * @param {string} [type='info'] - Тип.
   * @param {number} [duration=4500] - Длительность показа.
   */
  function showNotification(title, message, type = 'info', duration = DEFAULT_DURATION) {
    return showToast(message, type, { title, duration });
  }

  // Экспорт в глобальную область видимости
  window.showToast = showToast;
  window.showNotification = showNotification;
  window._showToast = showToast; // Для совместимости с уже имеющимися вкладками

  // Перехват стандартного window.alert()
  // Сохраняем ссылку на оригинальный alert на случай необходимости
  window._originalAlert = window.alert;

  window.alert = function (message) {
    // Выводим неблокирующее всплывающее окно
    showToast(message);
    // Также дублируем в консоль для отладки
    if (window.console && console.debug) {
      console.debug('[Toast Alert]:', message);
    }
  };

  // Инициализация контейнера при загрузке документа
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', getOrCreateContainer);
  } else {
    getOrCreateContainer();
  }
})();
