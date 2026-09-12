// Background Service Worker for AI-Breadboard Chrome Extension (Manifest V3)

let _cachedConfig = null;

/**
 * Load runtime extension configuration from bundled config.json.
 */
async function getAppConfig() {
  if (_cachedConfig) return _cachedConfig;
  try {
    const configUrl = chrome.runtime.getURL('config.json');
    const res = await fetch(configUrl);
    if (res.ok) {
      _cachedConfig = await res.json();
      return _cachedConfig;
    }
  } catch (err) {
    console.error('Failed to load extension config.json:', err);
  }
  _cachedConfig = {
    serverUrl: '',
    subfolder: 'web_pages',
    autoSendChat: true,
    language: 'default',
    chatWindow: { type: 'popup', width: 520, height: 780 }
  };
  return _cachedConfig;
}

/**
 * Helper to get extension user settings (merged with config.json defaults).
 */
async function getSettings() {
  const config = await getAppConfig();
  return new Promise((resolve) => {
    chrome.storage.sync.get(
      {
        serverUrl: config.serverUrl || '',
        language: config.language || 'default',
        customPrompt: '',
        subfolder: config.subfolder || 'web_pages',
        autoSendChat: config.autoSendChat !== false
      },
      (items) => resolve(items)
    );
  });
}

/**
 * Resolve summary prompt based on settings and language.
 */
function resolveSummaryPrompt(settings) {
  if (settings.customPrompt && settings.customPrompt.trim().length > 0) {
    return settings.customPrompt.trim();
  }

  let lang = settings.language;
  if (!lang || lang === 'default') {
    const uiLang = chrome.i18n.getUILanguage() || 'ru';
    lang = uiLang.toLowerCase();
  }

  if (lang.startsWith('ru')) {
    return 'Дай краткое содержание';
  } else if (lang.startsWith('he')) {
    return 'תן סיכום תמציתי של דף זה:';
  } else {
    return 'Provide a concise summary of this page:';
  }
}

/**
 * Sanitize filename for safe storage.
 */
function sanitizeFilename(title) {
  const clean = (title || 'webpage')
    .replace(/[\\/:*?"<>|]+/g, '_')
    .replace(/\s+/g, '_')
    .slice(0, 50);
  return clean || 'webpage';
}

/**
 * Setup context menus on installation.
 */
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.removeAll(() => {
    chrome.contextMenus.create({
      id: 'ai_breadboard_save_page',
      title: chrome.i18n.getMessage('menuSavePage') || 'Сохранить страницу',
      contexts: ['page', 'selection', 'link']
    });

    chrome.contextMenus.create({
      id: 'ai_breadboard_analyze_in_chat',
      title: chrome.i18n.getMessage('menuAnalyzeInChat') || 'Проанализировать страницу в чате',
      contexts: ['page', 'selection', 'link']
    });
  });
});

/**
 * Extract page data from a tab.
 */
async function extractDataFromTab(tabId) {
  try {
    const response = await chrome.tabs.sendMessage(tabId, { action: 'extract_page_data' });
    if (response && response.status === 'ok') {
      return response.data;
    }
  } catch (err) {
    // Content script might not be injected yet, inject dynamically
    try {
      await chrome.scripting.executeScript({
        target: { tabId },
        files: ['content.js']
      });
      const response = await chrome.tabs.sendMessage(tabId, { action: 'extract_page_data' });
      if (response && response.status === 'ok') {
        return response.data;
      }
    } catch (injectErr) {
      console.error('Failed to inject or communicate with content script:', injectErr);
    }
  }

  // Fallback if content script could not run
  const tab = await chrome.tabs.get(tabId);
  return {
    title: tab.title || 'Page',
    url: tab.url || '',
    selection: '',
    description: '',
    author: '',
    textContent: `URL: ${tab.url}`,
    timestamp: new Date().toISOString()
  };
}

/**
 * Handle context menu item clicks.
 */
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (!tab || !tab.id) return;

  const settings = await getSettings();
  const pageData = await extractDataFromTab(tab.id);

  // If selection context was used, override selection
  if (info.selectionText) {
    pageData.selection = info.selectionText;
  }

  if (info.menuItemId === 'ai_breadboard_save_page') {
    await handleSavePage(pageData, settings);
  } else if (info.menuItemId === 'ai_breadboard_analyze_in_chat') {
    await handleAnalyzeInChat(pageData, settings);
  }
});

/**
 * Save page to user workspace.
 */
async function handleSavePage(pageData, settings) {
  const config = await getAppConfig();
  const serverUrl = (settings.serverUrl || config.serverUrl || '').replace(/\/+$/, '');
  if (!serverUrl) {
    notify('error', 'URL сервера не настроен в конфигурации.');
    return;
  }

  const dateStr = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
  const safeTitle = sanitizeFilename(pageData.title);
  const filename = `web_${safeTitle}_${dateStr}.md`;

  const mdContent = [
    `# ${pageData.title}`,
    ``,
    `- **URL:** ${pageData.url}`,
    `- **Date:** ${pageData.timestamp}`,
    pageData.author ? `- **Author:** ${pageData.author}` : null,
    pageData.description ? `- **Description:** ${pageData.description}` : null,
    ``,
    `---`,
    ``,
    pageData.selection ? `### Selected Snippet\n\n${pageData.selection}\n\n### Full Content\n` : '',
    pageData.textContent || ''
  ].filter(line => line !== null).join('\n');

  const subfolder = settings.subfolder || config.subfolder || 'web_pages';
  const formData = new FormData();
  const blob = new Blob([mdContent], { type: 'text/markdown;charset=utf-8' });
  formData.append('file', blob, filename);
  formData.append('subfolder', subfolder);

  const uploadUrl = `${serverUrl}/api/user/files/upload`;

  try {
    const res = await fetch(uploadUrl, {
      method: 'POST',
      body: formData,
      credentials: 'include'
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `HTTP ${res.status}`);
    }

    notify(
      'success',
      chrome.i18n.getMessage('pageSavedSuccess') || 'Страница успешно сохранена в рабочее пространство!'
    );
  } catch (err) {
    console.error('Error saving page:', err);
    notify(
      'error',
      (chrome.i18n.getMessage('pageSaveError') || 'Ошибка сохранения страницы') + `: ${err.message}`
    );
  }
}

/**
 * Open chat in a popup window and execute analysis prompt.
 */
async function handleAnalyzeInChat(pageData, settings) {
  const config = await getAppConfig();
  const serverUrl = (settings.serverUrl || config.serverUrl || '').replace(/\/+$/, '');
  if (!serverUrl) {
    notify('error', 'URL сервера не настроен в конфигурации.');
    return;
  }

  const prompt = resolveSummaryPrompt(settings);
  const contentToAnalyze = pageData.selection 
    ? `> ${pageData.selection}\n\n${pageData.textContent}` 
    : pageData.textContent;

  const fullPromptMessage = `${prompt}\n\n**Источник:** [${pageData.title}](${pageData.url})\n\n${contentToAnalyze}`;
  const chatTargetUrl = `${serverUrl}/`;

  const executePayload = {
    action: 'breadboard_external_chat_prompt',
    prompt: fullPromptMessage,
    autoSend: settings.autoSendChat !== false
  };

  const winWidth = (config.chatWindow && config.chatWindow.width) || 520;
  const winHeight = (config.chatWindow && config.chatWindow.height) || 780;

  // Create standalone popup window for the chat interface
  const popupWindow = await chrome.windows.create({
    url: chatTargetUrl,
    type: 'popup',
    width: winWidth,
    height: winHeight,
    focused: true
  });

  const targetTab = popupWindow.tabs && popupWindow.tabs[0];
  const targetTabId = targetTab ? targetTab.id : null;

  if (targetTabId) {
    const onTabUpdated = (tabId, changeInfo) => {
      if (tabId === targetTabId && changeInfo.status === 'complete') {
        chrome.tabs.onUpdated.removeListener(onTabUpdated);
        setTimeout(async () => {
          try {
            await chrome.tabs.sendMessage(targetTabId, executePayload);
          } catch (e) {
            try {
              await chrome.scripting.executeScript({
                target: { tabId: targetTabId },
                func: (payload) => {
                  window.sessionStorage.setItem('pending_breadboard_chat', JSON.stringify(payload));
                  if (window.handleExternalChatPrompt) {
                    window.handleExternalChatPrompt(payload);
                  }
                },
                args: [executePayload]
              });
            } catch (err) {
              console.error('Failed to inject chat prompt to popup window:', err);
            }
          }
        }, 400);
      }
    };
    chrome.tabs.onUpdated.addListener(onTabUpdated);
  }
}

/**
 * Show desktop notification.
 */
function notify(type, message) {
  chrome.notifications.create({
    type: 'basic',
    iconUrl: 'icons/icon128.png',
    title: 'AI-Breadboard',
    message: message,
    priority: 1
  });
}

// Listen to messages from popup or options
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'save_current_tab') {
    (async () => {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tab) {
        const settings = await getSettings();
        const data = await extractDataFromTab(tab.id);
        await handleSavePage(data, settings);
        sendResponse({ status: 'ok' });
      } else {
        sendResponse({ status: 'error', error: 'No active tab' });
      }
    })();
    return true;
  } else if (request.action === 'analyze_current_tab') {
    (async () => {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tab) {
        const settings = await getSettings();
        const data = await extractDataFromTab(tab.id);
        await handleAnalyzeInChat(data, settings);
        sendResponse({ status: 'ok' });
      } else {
        sendResponse({ status: 'error', error: 'No active tab' });
      }
    })();
    return true;
  }
});
