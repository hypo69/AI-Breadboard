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

  if (statusData?.ai) {
    const ai = statusData.ai;
    if (ai.provider) {
      prov = ai.provider.toUpperCase();
      mod = ai.model || ai[`${ai.provider.toLowerCase()}_model_id`] || 'default';
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

  // Если модель всё ещё не определена, делаем прямой запрос к /api/chat/active-model
  if (!mod || !prov) {
    try {
      const isTcRoute = window.location.pathname.startsWith('/tc');
      const query = isTcRoute ? '?profile=tc' : '';
      const resp = await fetch(`/api/chat/active-model${query}`);
      if (resp.ok) {
        const data = await resp.json();
        if (data && data.model) {
          prov = data.provider || 'AI';
          mod = data.model;
          cfgFile = data.config_file || cfgFile;
        }
      }
    } catch {}
  }

  if (prov && mod) {
    modelBadgeText.textContent = `${prov}: ${mod}`;
    if (modelBadge) {
      const fileLabel = cfgFile ? `, Профиль: ${cfgFile}` : '';
      modelBadge.title = `Используемая модель: ${mod} (Провайдер: ${prov}${fileLabel})`;
    }
  } else {
    modelBadgeText.textContent = 'AI: Не определена';
  }
}

