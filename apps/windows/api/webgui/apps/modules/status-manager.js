/**
 * =============================================================================
 * Process Name: Windows Modules - Status-Manager Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля status-manager.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/webgui/apps/modules/status-manager.js?v=20261001_v1" type="module"></script>
 *
 * File: status-manager.js
 * Project: ai-breadboard
 * Package: windows/api/webgui/apps/modules
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-08 09:01:00
 * =============================================================================
 */

/**
 * apps/modules/status-manager.js — Управление состоянием приложений и бейджем модели
 */

export async function fetchAppsStatus() {
  const isTcRoute = window.location.pathname.startsWith('/tc') || window.location.pathname.startsWith('/apps');
  const query = isTcRoute ? '?profile=tc' : '';
  
  // 1. Получаем статус приложений и AI-конфига по стандарту /api/v1/apps/status
  let statusData = null;
  try {
    const resp = await fetch(`/api/v1/apps/status${query}`);
    if (resp.ok) {
      statusData = await resp.json();
    }
  } catch (err) {
    console.warn('[AppsHub] Failed to fetch /api/v1/apps/status:', err);
  }

  if (statusData && statusData.apps) {
    window.appsStatusMap = statusData.apps;
  }

  // 2. Если в ответе нет секции ai / ai_providers_and_models_configuration, явно запрашиваем активную модель через /api/v1/chat/active-model
  if (!statusData?.ai && !statusData?.ai_providers_and_models_configuration) {
    try {
      const modelResp = await fetch(`/api/v1/chat/active-model${query}`);
      if (modelResp.ok) {
        const modelData = await modelResp.json();
        if (modelData && modelData.model) {
          statusData = statusData || {};
          statusData.ai = {
            provider: modelData.provider,
            model: modelData.model
          };
          statusData.config_file = modelData.config_file;
        }
      }
    } catch (err) {
      console.warn('[AppsHub] Could not fetch active model from /api/v1/chat/active-model:', err);
    }
  }

  return statusData;
}

export async function updateModelBadge(statusData) {
  const modelBadgeContainer = document.getElementById('apps-model-badge') || document.getElementById('chat-model-badge');
  const modelBadgeText = document.getElementById('apps-model-text') || document.getElementById('chat-model-badge') || modelBadgeContainer;
  if (!modelBadgeContainer && !modelBadgeText) return;

  let prov = '';
  let mod = '';
  let cfgFile = statusData?.config_file || '';

  // 1. Приоритет: прямой запрос актуальной активной модели с сервера (/api/v1/chat/active-model)
  try {
    const isTcRoute = window.location.pathname.startsWith('/tc') || window.location.pathname.startsWith('/apps');
    const query = isTcRoute ? '?profile=tc' : '';
    const resp = await fetch(`/api/v1/chat/active-model${query}`);
    if (resp.ok) {
      const data = await resp.json();
      if (data && data.model) {
        prov = data.provider || '';
        mod = data.model;
        cfgFile = data.config_file || cfgFile;
      }
    }
  } catch (err) {
    console.warn('[AppsHub] Failed to fetch active model from /api/v1/chat/active-model:', err);
  }

  // 2. Резервный парсинг конфигурации statusData
  if (!mod && statusData) {
    const ai = statusData.ai_providers_and_models_configuration || statusData.ai;
    if (ai) {
      if (ai.default_provider) {
        prov = String(ai.default_provider).toUpperCase();
      }
      if (ai.default_model) {
        mod = ai.default_model;
      }
      if (!mod && ai.provider) {
        const p = String(ai.provider).toLowerCase();
        prov = String(ai.provider).toUpperCase();
        mod = ai.model || (ai[p] && typeof ai[p] === 'object' ? ai[p].model : null) || (ai.providers && ai.providers[p] ? ai.providers[p].model : null) || ai[`${p}_model_id`] || '';
      } else if (!mod && ai.providers && typeof ai.providers === 'object') {
        for (const [pk, pv] of Object.entries(ai.providers)) {
          if (pv && pv.enabled) {
            prov = pk.toUpperCase();
            mod = pv.model || '';
            break;
          }
        }
      } else if (!mod && ai.model) {
        mod = ai.model;
        prov = prov || 'AI';
      }
    }
  }

  // 3. Очистка и форматирование отображаемой строки
  if (mod && prov && mod.startsWith(`${prov.toLowerCase()}:`)) {
    mod = mod.substring(prov.length + 1);
  }

  const displayText = (prov && mod && mod !== 'default')
    ? `${prov}: ${mod}`
    : (mod && mod !== 'default' ? `${mod}` : (prov ? `${prov}` : 'AI: Не определена'));

  const titleText = (mod && mod !== 'default')
    ? `Используемая модель: ${mod} (Провайдер: ${prov || 'AI'}, Профиль: ${cfgFile || 'config.json'}) — нажмите для перехода к настройкам моделей`
    : `AI-модель не настроена — нажмите для перехода к настройкам моделей`;

  if (modelBadgeText) {
    modelBadgeText.textContent = displayText;
  }
  if (modelBadgeContainer) {
    modelBadgeContainer.title = titleText;
    modelBadgeContainer.style.display = 'inline-flex';
    if (!modelBadgeContainer._hasClick) {
      modelBadgeContainer._hasClick = true;
      modelBadgeContainer.style.cursor = 'pointer';
      modelBadgeContainer.addEventListener('click', () => {
        if (typeof window.switchTab === 'function') {
          window.switchTab('tab-models');
        }
      });
    }
  }
}

