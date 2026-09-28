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
  let configFile = 'i18n.t('auto__1_try_const_sresp_await_fetch__674719')/auth/settings');
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
    console.warn('[AppsHub] Could not fetch user settings:i18n.t('auto__err_2_if_model_try_const_resp_await_fetch_api_chat_active_model_query_if_resp_ok_const_data_await_resp_json_if_data_data_model_provider_data_provider_provider__896c6b')AI';
          model = data.model;
          configFile = data.config_file || '';
        }
      }
    } catch (err) {
      console.warn('[AppsHub] Could not fetch active model from /api/chat/active-model:i18n.t('auto__err_if_provider_model_model_tolowercase_startswith_provider_tolowercase_model_model_substring_provider_length_1_const_display_provider_model_model__a075bf')default')
    ? `${provider}: ${model}`
    : (model && model !== 'default')
      ? model
      : (provider ? provider : i18n.t('auto_ai__d14452'));

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
    console.warn('[AppsHub] Could not fetch available models from /api/chat/models:i18n.t('auto__err_return_export_async_function_updatemodeldropdown_const_dropdownbtn_document_getelementbyid__f3ead0')apps-model-dropdown-btn');
  const dropdownMenu = document.getElementById('apps-model-dropdown-menu');
  const modelText = document.getElementById('apps-model-texti18n.t('auto__if_dropdownbtn_modeltext_return_1_const_activeinfo_await_fetchactivemodelinfo_if_modeltext_modeltext_textcontent_activeinfo_display_if_dropdownbtn_const_filelabel_activeinfo_configfile_activeinfo_configfile__809e49')i18n.t('auto__dropdownbtn_title_activeinfo_model__b9b8f5')не определенаi18n.t('auto__activeinfo_provider__91bc0b')AIi18n.t('auto__filelabel_if_dropdownmenu_return_2_try_const_models_await_fetchavailablemodels_if_models_length_0_dropdownmenu_innerhtml__af3ab3')<li><span class="dropdown-item-text text-muted small px-2">Нет доступных моделей</span></li>';
      return;
    }

    dropdownMenu.innerHTML = 'i18n.t('auto__let_currentprovider__ed5a2c')';
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

      a.addEventListener('clicki18n.t('auto__async_e_e_preventdefault_e_stoppropagation_try_const_saveresp_await_fetch__e5f3c5')/auth/settings', {
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
              window.toast.success(i18n.t('auto___28266d'), `Активная модель: ${provider}: ${model}`);
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
    dropdownMenu.innerHTML = '<li><span class="dropdown-item-text text-muted small px-2">Ошибка загрузки моделей</span></li>i18n.t('auto__ai_export_async_function_fetchappsstatus_const_istcroute_window_location_pathname_startswith__1a4fdd')/tc');
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
