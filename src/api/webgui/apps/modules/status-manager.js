/**
 * apps/modules/status-manager.js — Управление состоянием приложений и бейджем модели
 */

export async function fetchAppsStatus() {
  const isTcRoute = window.location.pathname.startsWith('/tc');
  const query = isTcRoute ? '?profile=tc' : '';
  
  // 1. Пытаемся получить полный статус приложений и AI-конфига
  let statusData = null;
  const urls = [
    `/api/apps/status${query}`,
    `/api/admin/apps/status${query}`,
    `/apps/status${query}`
  ];

  for (const url of urls) {
    try {
      const resp = await fetch(url);
      if (resp.ok) {
        statusData = await resp.json();
        if (statusData && (statusData.apps || statusData.ai)) {
          break;
        }
      }
    } catch {}
  }

  if (statusData && statusData.apps) {
    window.appsStatusMap = statusData.apps;
  }

  // 2. Если в ответе нет секции ai, явно запрашиваем активную модель через /api/chat/active-model
  if (!statusData?.ai) {
    try {
      const modelResp = await fetch(`/api/chat/active-model${query}`);
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
      console.warn('[AppsHub] Could not fetch active model from /api/chat/active-model:', err);
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

  // 1. Приоритет: запрос актуальной активной модели с сервера (учитывает профиль и настройки пользователя)
  try {
    const isTcRoute = window.location.pathname.startsWith('/tc');
    const query = isTcRoute ? '?profile=tc' : '';
    const resp = await fetch(`/api/chat/active-model${query}`);
    if (resp.ok) {
      const data = await resp.json();
      if (data && data.model) {
        prov = data.provider || '';
        mod = data.model;
        cfgFile = data.config_file || cfgFile;
      }
    }
  } catch (err) {
    console.warn('[AppsHub] Failed to fetch active model from /api/chat/active-model:', err);
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
      mod = ai.gemini_model_id || ai.model || 'gemini-2.5-flash';
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

