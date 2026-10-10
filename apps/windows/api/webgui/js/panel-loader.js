/**
 * =============================================================================
 * Process Name: Windows WebGUI - Universal Panel Loader
 * =============================================================================
 * Description:
 *   Клиентский модуль автоматической загрузки данных для панелей интерфейса.
 *   Каждая панель с div id="panel-{panel_id}" или data-panel-id="{panel_id}"
 *   при инициализации/активации страницы и вкладок вызывает эндпоинт:
 *   GET /api/v1/panel/{panel_id} -> выполнение SQL-запроса в SQLite (telemetry.db).
 *
 * Usage Examples:
 *   HTML:
 *     <div id="panel-cpu-load" class="ui-panel" data-panel-id="panel-cpu-load">...</div>
 *     <script src="/html/js/panel-loader.js?v=20261010_v2"></script>
 *
 *   JavaScript:
 *     import { loadPanelData, initPanels } from '/html/js/panel-loader.js';
 *     await loadPanelData('panel-cpu-load');
 *
 * File: panel-loader.js
 * Project: ai-breadboard
 * Package: windows/api/webgui/js
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-10 10:37:00
 * =============================================================================
 */

const panelRenderers = new Map();
const panelDataCache = new Map();
const pendingRequests = new Map();

/**
 * Загружает данные для панели через GET /api/v1/panel/{panel_id}.
 * @param {string} panelId - Идентификатор панели
 * @param {Object} [options] - Дополнительные параметры запроса (limit, force)
 * @returns {Promise<Object>} Данные ответа SQL-запроса
 */
export async function loadPanelData(panelId, options = {}) {
  if (!panelId) return null;
  const cleanId = panelId.trim();

  // Если уже выполняется запрос для этого panelId, возвращаем существующий промис
  if (pendingRequests.has(cleanId) && !options.force) {
    return pendingRequests.get(cleanId);
  }

  const limit = options.limit || 60;
  const url = `/api/v1/panel/${encodeURIComponent(cleanId)}?limit=${limit}&t=${Date.now()}`;

  const el = document.getElementById(cleanId) || document.querySelector(`[data-panel-id="${cleanId}"]`);
  if (el) {
    el.setAttribute('data-panel-status', 'loading');
  }

  const fetchPromise = (async () => {
    try {
      const res = await fetch(url);
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
      const result = await res.json();
      panelDataCache.set(cleanId, result);

      if (el) {
        el.setAttribute('data-panel-status', 'loaded');
        if (result.sql) {
          el.setAttribute('data-panel-sql', result.sql);
        }
        el._panelData = result;
      }

      // Вызов зарегистрированного рендерера
      const renderer = panelRenderers.get(cleanId);
      if (typeof renderer === 'function') {
        try {
          renderer(result, el);
        } catch (rErr) {
          console.warn(`[PanelLoader] Ошибка рендера панели ${cleanId}:`, rErr);
        }
      }

      // Диспетчеризация кастомных событий
      const eventDetail = { panelId: cleanId, result, data: result.data || [], sql: result.sql };
      document.dispatchEvent(new CustomEvent('panel:data', { detail: eventDetail }));
      document.dispatchEvent(new CustomEvent(`panel:${cleanId}:loaded`, { detail: eventDetail }));

      return result;
    } catch (err) {
      console.warn(`[PanelLoader] Ошибка загрузки данных панели ${cleanId}:`, err);
      if (el) {
        el.setAttribute('data-panel-status', 'error');
      }
      return { status: 'error', panel_id: cleanId, error: err.message, data: [] };
    } finally {
      pendingRequests.delete(cleanId);
    }
  })();

  pendingRequests.set(cleanId, fetchPromise);
  return fetchPromise;
}

/**
 * Регистрирует пользовательскую функцию отрисовки для панели.
 * @param {string} panelId 
 * @param {Function} renderFn 
 */
export function registerPanelRenderer(panelId, renderFn) {
  if (panelId && typeof renderFn === 'function') {
    panelRenderers.set(panelId, renderFn);
  }
}

/**
 * Инициализирует и опрашивает все панели внутри контейнера.
 * @param {HTMLElement|Document} [container=document] 
 */
export function initPanels(container = document) {
  if (!container || typeof container.querySelectorAll !== 'function') return;
  const elements = container.querySelectorAll('[id^="panel-"], [data-panel-id]');
  const processedIds = new Set();

  elements.forEach((el) => {
    const panelId = el.getAttribute('data-panel-id') || el.id;
    if (panelId && !processedIds.has(panelId)) {
      processedIds.add(panelId);
      loadPanelData(panelId);
    }
  });
}

// Экспорт в глобальный контекст window
if (typeof window !== 'undefined') {
  window.loadPanelData = loadPanelData;
  window.registerPanelRenderer = registerPanelRenderer;
  window.initPanels = initPanels;

  // Автоматический опрос панелей при активации вкладки
  document.addEventListener('tab:activated', (e) => {
    const tabId = e.detail?.tabId;
    if (tabId) {
      const tabPane = document.getElementById(tabId);
      if (tabPane) {
        initPanels(tabPane);
      }
    }
  });

  // Первичная инициализация при готовности DOM
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => initPanels(document));
  } else {
    setTimeout(() => initPanels(document), 100);
  }
}
