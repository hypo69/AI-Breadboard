// Content script for AI-Breadboard Chrome Extension
// Extracts clean page content, metadata, and user selection.

function extractPageData() {
  const title = document.title || document.querySelector('h1')?.innerText || 'Untitled Page';
  const url = window.location.href;
  const selection = window.getSelection() ? window.getSelection().toString().trim() : '';

  // Get metadata
  const metaDesc = document.querySelector('meta[name="description"]')?.content || 
                   document.querySelector('meta[property="og:description"]')?.content || '';
  const author = document.querySelector('meta[name="author"]')?.content || '';

  // Get readable main content
  let mainElement = document.querySelector('article') || 
                    document.querySelector('main') || 
                    document.querySelector('[role="main"]') || 
                    document.body;

  let textContent = '';
  if (mainElement) {
    // Clone to avoid modifying DOM
    const clone = mainElement.cloneNode(true);
    // Remove unwanted script, style, nav, footer, ads elements
    const unwanted = clone.querySelectorAll('script, style, nav, footer, noscript, iframe, svg, form, [aria-hidden="true"]');
    unwanted.forEach(el => el.remove());
    textContent = clone.innerText ? clone.innerText.trim() : '';
  }

  // Fallback to body text if empty
  if (!textContent && document.body) {
    textContent = document.body.innerText.trim();
  }

  // Truncate if excessively long (e.g. limit to first 50,000 characters for optimal AI chat latency)
  if (textContent.length > 50000) {
    textContent = textContent.slice(0, 50000) + '\n\n[... Контент сокращен для оптимизации ...]';
  }

  return {
    title,
    url,
    selection,
    description: metaDesc,
    author,
    textContent,
    timestamp: new Date().toISOString()
  };
}

// Listen for messages from background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'extract_page_data') {
    try {
      const data = extractPageData();
      sendResponse({ status: 'ok', data });
    } catch (err) {
      sendResponse({ status: 'error', error: String(err) });
    }
  }
  return true;
});
