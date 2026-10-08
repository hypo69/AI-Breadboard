/**
 * =============================================================================
 * Process Name: Windows Js - Model-Tester Script
 * =============================================================================
 * Description:
 *   Клиентский модуль быстрой проверки доступности активной AI-модели.
 *   Позволяет отправлять одиночные проверочные запросы к модели без сохранения
 *   истории диалога и сессий, отображая сырой ответ или ошибку как есть.
 *
 * Usage Examples:
 *   JavaScript Import:
 *     import { initModelTester, sendModelPing } from '/windows/api/webgui/js/model-tester.js';
 *
 * File: model-tester.js
 * Project: ai-breadboard
 * Package: windows/api/webgui/js
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-08 04:22:00
 * =============================================================================
 */

/**
 * Отправляет проверочный запрос к AI-модели и выводит полученный ответ или ошибку.
 *
 * @param {string} [customMessage] - Опциональный текст запроса. Если не задан, берется из input.
 * @returns {Promise<void>}
 */
export async function sendModelPing(customMessage = null) {
  const inputEl = document.getElementById('model-ping-input');
  const btnEl = document.getElementById('btn-model-ping-send');
  const btnTextEl = document.getElementById('model-ping-btn-text');
  const btnIconEl = document.getElementById('model-ping-btn-icon');
  const responseContainerEl = document.getElementById('model-ping-response-container');
  const responseEl = document.getElementById('model-ping-response');

  if (!inputEl || !responseEl) return;

  const rawMessage = customMessage !== null ? customMessage : inputEl.value;
  const message = (rawMessage || '').trim() || 'Проверка доступности модели';

  // Перевод элементов интерфейса в состояние загрузки
  if (btnEl) btnEl.disabled = true;
  if (inputEl) inputEl.disabled = true;
  if (btnIconEl) btnIconEl.className = 'spinner-border spinner-border-sm';
  if (btnTextEl) btnTextEl.textContent = 'Отправка...';

  if (responseContainerEl) responseContainerEl.style.display = 'block';
  responseEl.className = 'small p-2 rounded bg-body-tertiary border text-break font-monospace text-muted';
  responseEl.textContent = 'Отправка запроса к модели, ожидание ответа...';

  const isTcRoute = window.location.pathname.startsWith('/tc');
  const query = isTcRoute ? '?profile=tc' : '';

  try {
    const resp = await fetch(`/api/v1/chat/test-model${query}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: message,
      }),
    });

    if (resp.ok) {
      const data = await resp.json().catch(() => null);
      if (data && data.status === 'success' && data.response !== undefined) {
        responseEl.textContent = data.response;
        responseEl.className = 'small p-2 rounded bg-success-subtle text-success-emphasis border border-success-subtle text-break font-monospace';
      } else if (data && data.status === 'error') {
        const errMsg = data.message || data.detail || JSON.stringify(data, null, 2);
        responseEl.textContent = errMsg;
        responseEl.className = 'small p-2 rounded bg-danger-subtle text-danger-emphasis border border-danger-subtle text-break font-monospace';
      } else if (data) {
        responseEl.textContent = data.response || data.message || data.detail || JSON.stringify(data, null, 2);
        responseEl.className = 'small p-2 rounded bg-body-tertiary border text-break font-monospace';
      } else {
        responseEl.textContent = 'Пустой ответ от сервера';
        responseEl.className = 'small p-2 rounded bg-warning-subtle text-warning-emphasis border text-break font-monospace';
      }
    } else {
      let errBody = '';
      try {
        const errData = await resp.json();
        errBody = errData.detail || errData.message || errData.response || JSON.stringify(errData, null, 2);
      } catch {
        errBody = await resp.text();
      }
      responseEl.textContent = errBody || `HTTP ${resp.status} ${resp.statusText}`;
      responseEl.className = 'small p-2 rounded bg-danger-subtle text-danger-emphasis border border-danger-subtle text-break font-monospace';
    }
  } catch (err) {
    responseEl.textContent = err.message || String(err);
    responseEl.className = 'small p-2 rounded bg-danger-subtle text-danger-emphasis border border-danger-subtle text-break font-monospace';
  } finally {
    if (btnEl) btnEl.disabled = false;
    if (inputEl) inputEl.disabled = false;
    if (btnIconEl) btnIconEl.className = 'bi bi-send-fill';
    if (btnTextEl) btnTextEl.textContent = 'Отправить';
  }
}

/**
 * Инициализирует интерактивные обработчики для выпадающей панели проверки доступности модели.
 */
export function initModelTester() {
  const sendBtn = document.getElementById('btn-model-ping-send');
  const inputEl = document.getElementById('model-ping-input');
  const dropdownEl = document.getElementById('model-ping-dropdown-wrapper');

  if (sendBtn) {
    sendBtn.onclick = (e) => {
      e.preventDefault();
      sendModelPing();
    };
  }

  if (inputEl) {
    inputEl.onkeydown = (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendModelPing();
      }
    };
  }

  if (dropdownEl) {
    dropdownEl.addEventListener('shown.bs.dropdown', () => {
      if (inputEl) {
        inputEl.focus();
        inputEl.select();
      }
    });
  }
}
