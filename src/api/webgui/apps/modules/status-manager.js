/**
 * apps/modules/status-manager.js — Управление состоянием приложений и бейджем/дропдауном модели
 */

/**
 * Получение текущей активной модели из настроек пользователя и активного профиля
 * @returns {Promise<{provider: string, model: string, display: string, configFile: string}>}
 */
export async function fetchActiveModelInfo() {
  const isTcRoute = window.location.pathname.startsWith('/tc');
  const query = isTcRoute ? '?profile=tc' : '';

  let provider = '';
  let model = '';
  let configFile = '';

  // 1. Проверяем настройки пользователя
  try {
    const sResp = await fetch('/auth/settings');
    if (sResp.ok) {
      const sData = await sResp.json();
      if (sData && sData.model) {
        let raw = sData.model.trim();
        if (raw.includes(':')) {
          const parts = raw.split(':');
          provider = parts[0].toUpperCase();
          model = parts.slice(1).join(':');
        } else if (raw.startsWith('agy-')) {
          provider = 'AGY';
          model = raw;
        } else if (raw.toLowerCase().includes('gemini')) {
          provider = 'GEMINI';
          model = raw;
        } else {
          provider = 'AI';
          model = raw;
        }
      }
    }
  } catch (err) {
    console.warn('[AppsHub] Could not fetch user settings:', err);
  }

  // 2. Если модель не получена из профиля, запрашиваем эндпоинт активной модели
  if (!model) {
    try {
      const resp = await fetch(`/api/chat/active-model${query}`);
      if (resp.ok) {
        const data = await resp.json();
        if (data && data.model) {
          provider = data.provider || provider || 'AI';
          model = data.model;
          configFile = data.config_file || '';
        }
      }
    } catch (err) {
      console.warn('[AppsHub] Could not fetch active model from /api/chat/active-model:', err);
    }
  }

  // Очищаем префикс провайдера из имени модели, если он продублирован
  if (provider && model && model.toLowerCase().startsWith(`${provider.toLowerCase()}:`)) {
    model = model.substring(provider.length + 1);
  }

  const display = (provider && model && model !== 'default')
    ? `${provider}: ${model}`
    : (model && model !== 'default')
      ? model
      : (provider ? provider : 'AI: Не определена');

  return { provider, model, display, configFile };
}

/**
 * Получение списка доступных моделей из /api/chat/models
 * @returns {Promise<Array<{provider: string, model: string, fullId: string, label: string}>>}
 */
export async function fetchAvailableModels() {
  try {
    const resp = await fetch('/api/chat/models');
    if (!resp.ok) return [];

    const data = await resp.json();
    const grouped = data.models || {};
    const result = [];

    for (const [prov, mList] of Object.entries(grouped)) {
      if (!Array.isArray(mList)) continue;
      const provUpper = prov.toUpperCase();

      for (const m of mList) {
        let cleanName = m;
        if (cleanName.startsWith(`${prov}:`)) cleanName = cleanName.substring(prov.length + 1);
        else if (cleanName.startsWith('gemini_cli:')) cleanName = cleanName.substring(11);
        else if (cleanName.startsWith('agy-')) cleanName = cleanName.substring(4);
        else if (cleanName.startsWith('foundry:')) cleanName = cleanName.substring(8);
        else if (cleanName.startsWith('ollama:')) cleanName = cleanName.substring(7);
        else if (cleanName.startsWith('onnx:')) cleanName = cleanName.substring(5);

        result.push({
          provider: provUpper,
          model: cleanName,
          fullId: m.includes(':') || m.startsWith('agy-') ? m : `${prov}:${m}`,
          label: `${provUpper}: ${cleanName}`
        });
      }
    }

    return result;
  } catch (err) {
    console.warn('[AppsHub] Could not fetch available models from /api/chat/models:', err);
    return [];
  }
}

/**
 * Обновляет выпадающий список и текст кнопки активной модели
 */
export async function updateModelDropdown() {
  const dropdownBtn = document.getElementById('apps-model-dropdown-btn');
  const dropdownMenu = document.getElementById('apps-model-dropdown-menu');
  const modelText = document.getElementById('apps-model-text');

  if (!dropdownBtn && !modelText) return;

  // 1. Получаем и отображаем текущую активную модель
  const activeInfo = await fetchActiveModelInfo();
  if (modelText) {
    modelText.textContent = activeInfo.display;
  }
  if (dropdownBtn) {
    const fileLabel = activeInfo.configFile ? `, Профиль: ${activeInfo.configFile}` : '';
    dropdownBtn.title = `Используемая модель: ${activeInfo.model || 'не определена'} (Провайдер: ${activeInfo.provider || 'AI'}${fileLabel})`;
  }

  if (!dropdownMenu) return;

  // 2. Загружаем доступные модели для меню
  try {
    const models = await fetchAvailableModels();

    if (models.length === 0) {
      dropdownMenu.innerHTML = '<li><span class="dropdown-item-text text-muted small px-2">Нет доступных моделей</span></li>';
      return;
    }

    dropdownMenu.innerHTML = '';

    // Группируем по провайдерам
    let currentProvider = '';
    models.forEach(({ provider, model, fullId, label }) => {
      if (provider !== currentProvider) {
        if (currentProvider !== '') {
          const divider = document.createElement('li');
          divider.innerHTML = '<hr class="dropdown-divider border-secondary my-1">';
          dropdownMenu.appendChild(divider);
        }
        currentProvider = provider;
        const header = document.createElement('li');
        header.innerHTML = `<h6 class="dropdown-header text-info py-0 px-2 small">${provider}</h6>`;
        dropdownMenu.appendChild(header);
      }

      const li = document.createElement('li');
      const a = document.createElement('a');
      a.className = 'dropdown-item text-white small px-2 py-1';
      a.href = '#';

      const isActive = activeInfo.model === model || activeInfo.display.includes(model);
      a.innerHTML = isActive
        ? `<i class="bi bi-check2 text-success me-1"></i><strong>${model}</strong>`
        : `<span class="ms-3">${model}</span>`;

      a.addEventListener('click', async (e) => {
        e.preventDefault();
        e.stopPropagation();

        try {
          // Сохраняем выбранную модель в настройках пользователя
          const saveResp = await fetch('/auth/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model: fullId })
          });

          if (saveResp.ok) {
            window.activeModelName = fullId;
            if (typeof window.updateChatBadges === 'function') {
              window.updateChatBadges(fullId);
            }
            if (modelText) {
              modelText.textContent = `${provider}: ${model}`;
            }
            if (window.toast && typeof window.toast.success === 'function') {
              window.toast.success('Модель обновлена', `Активная модель: ${provider}: ${model}`);
            }
            // Перерисовываем список для обновления галочки
            await updateModelDropdown();
          }
        } catch (saveErr) {
          console.error('[AppsHub] Error saving selected model:', saveErr);
        }
      });

      li.appendChild(a);
      dropdownMenu.appendChild(li);
    });
  } catch (err) {
    console.error('[AppsHub] Failed to build model dropdown:', err);
    dropdownMenu.innerHTML = '<li><span class="dropdown-item-text text-muted small px-2">Ошибка загрузки моделей</span></li>';
  }
}

/**
 * Получение статуса приложений и AI-конфига
 */
export async function fetchAppsStatus() {
  const isTcRoute = window.location.pathname.startsWith('/tc');
  const query = isTcRoute ? '?profile=tc' : '';

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

  return statusData;
}

/**
 * Алиас для совместимости с бейджами
 */
export async function updateModelBadge(statusData) {
  return updateModelDropdown();
}
