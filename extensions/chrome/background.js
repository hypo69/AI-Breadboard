// Background Service Worker for AI-Breadboard Chrome Extension (Manifest V3)

const DEFAULT_SERVER_URL = 'http://localhost:8000';
const DEFAULT_SUBFOLDER = 'web_pages';

/**
 * Helper to get extension settings.
 */
async function getSettings() {
  return new Promise((resolve) => {
    chrome.storage.sync.get(
      {
        serverUrl: DEFAULT_SERVER_URL,
        language: 'default',
        customPrompt: '',
        subfolder: DEFAULT_SUBFOLDER,
        autoSendChat: true
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

  // Fallback if content script could not run (e.g. chrome:// internal pages)
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

  const formData = new FormData();
  const blob = new Blob([mdContent], { type: 'text/markdown;charset=utf-8' });
  formData.append('file', blob, filename);
  formData.append('subfolder', settings.subfolder || DEFAULT_SUBFOLDER);

  const serverUrl = (settings.serverUrl || DEFAULT_SERVER_URL).replace(/\/+$/, '');
  const uploadUrl = `${serverUrl}/api/user/files/upload`;

  try {
    const res = await fetch(uploadUrl, {
      method: 'POST',
      body: formData
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
 * Send page to AI-Breadboard chat.
 */
async function handleAnalyzeInChat(pageData, settings) {
  const prompt = resolveSummaryPrompt(settings);
  const contentToAnalyze = pageData.selection 
    ? `> ${pageData.selection}\n\n${pageData.textContent}` 
    : pageData.textContent;

  const fullPromptMessage = `${prompt}\n\n**Источник:** [${pageData.title}](${pageData.url})\n\n${contentToAnalyze}`;

  const serverUrl = (settings.serverUrl || DEFAULT_SERVER_URL).replace(/\/+$/, '');
  const chatTargetUrl = `${serverUrl}/`;

  // Find existing tab or open a new one
  const tabs = await chrome.tabs.query({ url: `${serverUrl}/*` });
  let targetTab = null;

  if (tabs.length > 0) {
    targetTab = tabs[0];
    await chrome.tabs.update(targetTab.id, { active: true });
    if (targetTab.windowId) {
      await chrome.windows.update(targetTab.windowId, { focused: true });
    }
  } else {
    targetTab = await chrome.tabs.create({ url: chatTargetUrl, active: true });
  }

  // Send message to the tab to execute chat analysis
  const executePayload = {
    action: 'breadboard_external_chat_prompt',
    prompt: fullPromptMessage,
    autoSend: settings.autoSendChat !== false
  };

  // Give the web page a brief moment to initialize if newly opened
  setTimeout(async () => {
    try {
      await chrome.tabs.sendMessage(targetTab.id, executePayload);
    } catch (e) {
      // If message fails, inject directly via scripting
      try {
        await chrome.scripting.executeScript({
          target: { tabId: targetTab.id },
          func: (payload) => {
            window.sessionStorage.setItem('pending_breadboard_chat', JSON.stringify(payload));
            if (window.handleExternalChatPrompt) {
              window.handleExternalChatPrompt(payload);
            }
          },
          args: [executePayload]
        });
      } catch (scriptErr) {
        console.error('Failed to dispatch chat prompt to tab:', scriptErr);
      }
    }
  }, tabs.length > 0 ? 300 : 1500);
}

/**
 * Show chrome notification.
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
