/**
 * =============================================================================
 * Process Name: AI-Breadboard UI - Status-Manager Script
 * =============================================================================
 * Description:
 *   Клиентский веб-скрипт модуля status-manager.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/src/api/webgui/apps/modules/status-manager.js?v=20261001_v1" type="module"></script>
 *
 * File: status-manager.js
 * Project: ai-breadboard
 * Package: src/api/webgui/apps/modules
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-04 01:12:00
 * =============================================================================
 */

/**
 * apps/modules/status-manager.js — Управление состоянием приложений и бейджем модели
 */

export async function fetchAppsStatus() {
  const isTcRoute = window.location.pathname.startsWith('/tc');
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

  // 2. Если в ответе нет секции ai, явно запрашиваем активную модель через /api/v1/chat/active-model
  if (!statusData?.ai) {
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
  const modelBadgeText = document.getElementById('apps-model-text');
  const modelBadge = document.getElementById('apps-model-badge');
  if (!modelBadgeText) return;

  let prov = '';
  let mod = '';
  let cfgFile = statusData?.config_file || '';

  // 1. Приоритет: запрос актуальной активной модели с сервера (/api/v1/chat/active-model)
  try {
    const isTcRoute = window.location.pathname.startsWith('/tc');
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

  // 2. Резервный парсинг конфигурации statusData.ai, если эндпоинт не вернул модель
  if (!mod && statusData?.ai) {
    const ai = statusData.ai;
    if (ai.provider) {
      const p = String(ai.provider).toLowerCase();
      prov = String(ai.provider).toUpperCase();
      mod = ai.model || (ai[p] && typeof ai[p] === 'object' ? ai[p].model : null) || (ai.providers && ai.providers[p] ? ai.providers[p].model : null) || ai[`${p}_model_id`] || '';
    } else if (ai.providers && typeof ai.providers === 'object') {
      for (const [pk, pv] of Object.entries(ai.providers)) {
        if (pv && pv.enabled) {
          prov = pk.toUpperCase();
          mod = pv.model || '';
          break;
        }
      }
    } else if (ai.use_gemini) {
      prov = 'GEMINI';
      mod = ai.gemini_model_id || ai.model || 'gemini-flash-latest';
    } else if (ai.use_agy) {
      prov = 'AGY';
      mod = ai.agy_model_id || ai.model || 'gemini-3.6-flash';
    } else if (ai.use_ollama) {
      prov = 'OLLAMA';
      mod = ai.ollama_model_id || ai.model || 'llama3.1';
    } else if (ai.use_foundry) {
      prov = 'FOUNDRY';
      mod = ai.foundry_model_id || ai.model || 'local';
    } else if (ai.model) {
      mod = ai.model;
      prov = 'AI';
    }
  }

  // 3. Очистка и форматирование отображаемой строки
  if (mod && mod.startsWith(`${prov.toLowerCase()}:`)) {
    mod = mod.substring(prov.length + 1);
  }

  if (prov && mod && mod !== 'default') {
    modelBadgeText.textContent = `${prov}: ${mod}`;
    if (modelBadge) {
      const fileLabel = cfgFile ? `, Профиль: ${cfgFile}` : '';
      modelBadge.title = `Используемая модель: ${mod} (Провайдер: ${prov}${fileLabel})`;
    }
  } else if (mod && mod !== 'default') {
    modelBadgeText.textContent = `${mod}`;
    if (modelBadge) {
      modelBadge.title = `Используемая модель: ${mod}`;
    }
  } else if (prov) {
    modelBadgeText.textContent = `${prov}`;
    if (modelBadge) {
      modelBadge.title = `Используемый провайдер: ${prov}`;
    }
  } else {
    modelBadgeText.textContent = 'AI: Не определена';
  }
}
