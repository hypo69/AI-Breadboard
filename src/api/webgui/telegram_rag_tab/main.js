// ── TELEGRAM CHANNEL & GROUP RAG TAB MAIN.JS ─────────────────────────────────

let tgramSubscribedChannels = [];
let tgramAvailableChannels = [];

// Initialize Telegram RAG Tab
window.initTelegramRagTab = async function() {
  console.log('[TelegramRAG] Initializing Telegram RAG Tab...');
  await loadTelegramChannels();
};

// Notification helper
function showTgramNotification(message, type = 'info') {
  if (typeof window.showNotification === 'function') {
    window.showNotification(message, type);
    return;
  }
  console.log(`[TelegramRAG Notification ${type}]: ${message}`);
}

// Load channels from backend API
async function loadTelegramChannels() {
  const container = document.getElementById('tgram-channels-list-container');
  const statsBadge = document.getElementById('tgram-stats-badge');
  const countEl = document.getElementById('tgram-channels-count');
  const activeCountBadge = document.getElementById('tgram-active-count-badge');
  const filterSelect = document.getElementById('tgram-filter-channel');

  try {
    const res = await fetch('/api/telegram_rag/channels');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    tgramSubscribedChannels = data.user_subscriptions || [];
    tgramAvailableChannels = data.available_channels || [];

    // Calculate total messages
    const totalMsgs = tgramAvailableChannels.reduce((sum, c) => sum + (c.messages_count || 0), 0);

    if (statsBadge) {
      statsBadge.textContent = `${tgramSubscribedChannels.length} подписок • ${totalMsgs} сообщений`;
    }
    if (countEl) countEl.textContent = tgramSubscribedChannels.length;
    if (activeCountBadge) activeCountBadge.textContent = `${tgramAvailableChannels.length} в пуле`;

    // Render channels list
    renderTelegramChannelsList(tgramSubscribedChannels, tgramAvailableChannels);

    // Update filter dropdown
    if (filterSelect) {
      const currentVal = filterSelect.value || 'all';
      let optsHtml = '<option value="all">🌐 Все подключенные каналы (Общий пул)</option>';
      tgramSubscribedChannels.forEach(ch => {
        const isSel = ch === currentVal ? 'selected' : '';
        const found = tgramAvailableChannels.find(a => a.channel === ch);
        const countText = found ? ` (${found.messages_count} сообщ.)` : '';
        optsHtml += `<option value="${ch}" ${isSel}>@${ch}${countText}</option>`;
      });
      filterSelect.innerHTML = optsHtml;
    }
  } catch (err) {
    console.error('Error loading Telegram channels:', err);
    if (container) {
      container.innerHTML = `<div class="alert alert-danger m-2 small">Ошибка загрузки каналов: ${err.message}</div>`;
    }
  }
}

// Render Channels List
function renderTelegramChannelsList(userSubs, availablePool) {
  const container = document.getElementById('tgram-channels-list-container');
  if (!container) return;

  if (userSubs.length === 0) {
    container.innerHTML = `
      <div class="text-center text-muted p-4 small">
        <i class="bi bi-chat-left-dots fs-3 d-block mb-2 text-secondary"></i>
        Нет подключенных каналов.<br>Добавьте канал выше для индексации.
      </div>
    `;
    return;
  }

  let html = '<div class="list-group list-group-flush">';
  userSubs.forEach(channelName => {
    const info = availablePool.find(p => p.channel === channelName) || {
      channel: channelName,
      messages_count: 0,
      is_indexed: false,
    };

    const statusBadge = info.is_indexed
      ? `<span class="badge bg-success-subtle text-success border border-success-subtle">${info.messages_count} сообщ.</span>`
      : `<span class="badge bg-warning-subtle text-warning border">Не индексирован</span>`;

    html += `
      <div class="list-group-item p-2 rounded mb-1 border-0 bg-body-tertiary shadow-sm">
        <div class="d-flex justify-content-between align-items-center mb-1">
          <div class="d-flex align-items-center gap-2 text-truncate">
            <span class="fs-5 text-primary">💬</span>
            <a href="https://t.me/${channelName}" target="_blank" rel="noopener noreferrer" class="fw-bold text-decoration-none text-truncate" title="Открыть в Telegram">
              @${channelName}
              <i class="bi bi-box-arrow-up-right ms-1 text-muted" style="font-size: 0.75rem;"></i>
            </a>
          </div>
          <div>${statusBadge}</div>
        </div>
        <div class="d-flex justify-content-between align-items-center mt-2 pt-1 border-top border-secondary-subtle">
          <button class="btn btn-sm btn-outline-secondary py-0 px-2 small" onclick="filterByChannel('${channelName}')" title="Искать только в этом канале">
            <i class="bi bi-search"></i> Искать здесь
          </button>
          <div class="btn-group btn-group-sm">
            <button class="btn btn-outline-primary py-0 px-2" onclick="handleReindexTelegramChannel('${channelName}')" title="Переиндексировать канал">
              <i class="bi bi-arrow-clockwise"></i>
            </button>
            <button class="btn btn-outline-danger py-0 px-2" onclick="handleUnsubscribeTelegramChannel('${channelName}')" title="Отключить канал">
              <i class="bi bi-trash"></i>
            </button>
          </div>
        </div>
      </div>
    `;
  });
  html += '</div>';
  container.innerHTML = html;
}

// Quick filter helper from channel list
function filterByChannel(channelName) {
  const filterSelect = document.getElementById('tgram-filter-channel');
  if (filterSelect) {
    filterSelect.value = channelName;
  }
  const searchInput = document.getElementById('tgram-search-input');
  if (searchInput) {
    searchInput.focus();
  }
}

// Add / Subscribe Channel Handler
async function handleAddTelegramChannel() {
  const input = document.getElementById('tgram-channel-input');
  const maxMsgsSelect = document.getElementById('tgram-max-msgs-select');
  const btn = document.getElementById('btn-tgram-subscribe');

  if (!input || !input.value.trim()) return;
  const channel = input.value.trim();
  const maxMessages = parseInt(maxMsgsSelect?.value || '500', 10);

  try {
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status"></span> Индексация...';
    }

    showTgramNotification(`Подключение канала @${channel}...`, 'info');
    const resp = await fetch('/api/telegram_rag/subscribe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ channel, max_messages: maxMessages }),
    });

    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();

    showTgramNotification(data.message || `Канал @${channel} успешно подключен`, 'success');
    input.value = '';
    await loadTelegramChannels();
  } catch (err) {
    console.error('Error adding Telegram channel:', err);
    showTgramNotification(`Ошибка: ${err.message}`, 'danger');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<i class="bi bi-cloud-arrow-down-fill me-1"></i> Подключить и индексировать';
    }
  }
}

// Unsubscribe Channel Handler
async function handleUnsubscribeTelegramChannel(channel) {
  if (!confirm(`Вы действительно хотите отключить канал @${channel}?`)) return;

  try {
    const resp = await fetch('/api/telegram_rag/unsubscribe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ channel }),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();
    showTgramNotification(data.message || `Канал @${channel} отключен`, 'info');
    await loadTelegramChannels();
  } catch (err) {
    console.error('Error unsubscribing channel:', err);
    showTgramNotification(`Ошибка: ${err.message}`, 'danger');
  }
}

// Reindex Channel Handler
async function handleReindexTelegramChannel(channel) {
  const maxMsgs = parseInt(document.getElementById('tgram-max-msgs-select')?.value || '500', 10);
  try {
    showTgramNotification(`Обновление индекса @${channel}...`, 'info');
    const resp = await fetch('/api/telegram_rag/reindex', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ channel, max_messages: maxMsgs }),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();
    showTgramNotification(data.message || `Индекс @${channel} успешно обновлен`, 'success');
    await loadTelegramChannels();
  } catch (err) {
    console.error('Error reindexing channel:', err);
    showTgramNotification(`Ошибка переиндексации: ${err.message}`, 'danger');
  }
}

// Highlight keywords in text
function highlightKeywords(text, query) {
  if (!text || !query) return text || '';
  const words = query.split(/\s+/).filter(w => w.length > 2);
  if (words.length === 0) return text;

  let escaped = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  words.forEach(w => {
    const regex = new RegExp(`(${w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    escaped = escaped.replace(regex, '<mark class="bg-warning-subtle text-body px-1 rounded">$1</mark>');
  });
  return escaped;
}

// Execute Telegram RAG Search
async function executeTelegramSearch() {
  const searchInput = document.getElementById('tgram-search-input');
  const filterSelect = document.getElementById('tgram-filter-channel');
  const modeSelect = document.getElementById('tgram-search-mode');
  const topkSelect = document.getElementById('tgram-topk-select');
  const resultsContainer = document.getElementById('tgram-results-container');
  const searchBtn = document.getElementById('btn-tgram-do-search');

  if (!searchInput || !searchInput.value.trim()) return;
  const query = searchInput.value.trim();
  const channel = filterSelect ? filterSelect.value : 'all';
  const searchMode = modeSelect ? modeSelect.value : 'unified';
  const topK = parseInt(topkSelect?.value || '5', 10);

  if (resultsContainer) {
    resultsContainer.innerHTML = `
      <div class="text-center text-muted p-5">
        <div class="spinner-border text-primary mb-3" role="status"></div>
        <h6>Поиск в базе знаний Telegram...</h6>
        <div class="small text-muted">Запрос: «${query}»</div>
      </div>
    `;
  }

  if (searchBtn) searchBtn.disabled = true;

  try {
    const startTime = performance.now();
    const resp = await fetch('/api/telegram_rag/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query,
        channel: channel === 'all' ? null : channel,
        search_mode: searchMode,
        top_k: topK,
      }),
    });

    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();
    const duration = Math.round(performance.now() - startTime);

    renderTelegramSearchResults(data.results || [], query, duration);
  } catch (err) {
    console.error('Error executing Telegram search:', err);
    if (resultsContainer) {
      resultsContainer.innerHTML = `
        <div class="alert alert-danger shadow-sm">
          <h6><i class="bi bi-exclamation-triangle-fill me-2"></i> Ошибка поиска</h6>
          <p class="mb-0 small">${err.message}</p>
        </div>
      `;
    }
  } finally {
    if (searchBtn) searchBtn.disabled = false;
  }
}

// Render Search Results Cards
function renderTelegramSearchResults(results, query, durationMs) {
  const container = document.getElementById('tgram-results-container');
  if (!container) return;

  if (results.length === 0) {
    container.innerHTML = `
      <div class="text-center text-muted p-5">
        <span class="fs-1 mb-2">🤷‍♂️</span>
        <h6 class="fw-bold">Ничего не найдено</h6>
        <p class="small text-muted mb-0">По запросу «${query}» в индексах Telegram сообщений не обнаружено. Попробуйте изменить формулировку или подключить дополнительные каналы.</p>
      </div>
    `;
    return;
  }

  let html = `
    <div class="d-flex justify-content-between align-items-center mb-3 pb-2 border-bottom">
      <div class="small text-muted">
        Найдено результатов: <strong class="text-primary">${results.length}</strong> (${durationMs} мс)
      </div>
      <span class="badge bg-secondary-subtle text-body border">RAG Ranker</span>
    </div>
    <div class="d-flex flex-column gap-3">
  `;

  results.forEach((r, idx) => {
    const channelName = r.channel || 'unknown';
    const author = r.author || 'Telegram';
    const dateStr = r.date || '';
    const msgUrl = r.url || `https://t.me/${channelName}/${r.id || ''}`;
    const highlightedSnippet = highlightKeywords(r.snippet || r.text || '', query);
    const scoreBadge = r.score !== undefined
      ? `<span class="badge bg-info-subtle text-info border">Релевантность: ${Math.round(r.score * 100)}%</span>`
      : '';

    html += `
      <div class="card border shadow-sm rounded-3">
        <div class="card-header bg-body-tertiary d-flex justify-content-between align-items-center py-2">
          <div class="d-flex align-items-center gap-2">
            <span class="badge bg-primary text-white">#${idx + 1}</span>
            <a href="https://t.me/${channelName}" target="_blank" rel="noopener noreferrer" class="fw-bold text-decoration-none text-primary">
              @${channelName}
            </a>
            <span class="text-muted small">• ${author}</span>
            ${dateStr ? `<span class="text-muted small">• ${dateStr}</span>` : ''}
          </div>
          <div>${scoreBadge}</div>
        </div>
        <div class="card-body p-3">
          <p class="mb-0 small text-body font-monospace" style="white-space: pre-wrap; word-break: break-word;">
            ${highlightedSnippet}
          </p>
        </div>
        <div class="card-footer bg-body-secondary py-2 d-flex justify-content-between align-items-center flex-wrap gap-2">
          <a href="${msgUrl}" target="_blank" rel="noopener noreferrer" class="btn btn-sm btn-outline-primary d-inline-flex align-items-center gap-1">
            <i class="bi bi-box-arrow-up-right"></i>
            <span>Открыть в Telegram</span>
          </a>
          <div class="btn-group btn-group-sm">
            <button class="btn btn-outline-secondary" onclick="copyTelegramLink('${msgUrl}')" title="Скопировать ссылку на сообщение">
              <i class="bi bi-clipboard"></i> Ссылка
            </button>
            <button class="btn btn-outline-success" onclick="sendTelegramResultToChat('${msgUrl}', '${encodeURIComponent(r.snippet || '')}')" title="Вставить цитату в чат">
              <i class="bi bi-chat-quote-fill"></i> В чат
            </button>
          </div>
        </div>
      </div>
    `;
  });

  html += '</div>';
  container.innerHTML = html;
}

// Copy link to clipboard
function copyTelegramLink(url) {
  navigator.clipboard.writeText(url).then(() => {
    showTgramNotification('Ссылка скопирована в буфер обмена', 'success');
  }).catch(() => {
    prompt('Скопируйте ссылку вручную:', url);
  });
}

// Insert result snippet into main chat
function sendTelegramResultToChat(url, encodedSnippet) {
  const snippet = decodeURIComponent(encodedSnippet);
  const textToInsert = `[Сообщение Telegram](${url}):\n> ${snippet.replace(/\n/g, '\n> ')}`;

  if (typeof window.switchTab === 'function') {
    window.switchTab('tab-chat');
  }

  const msgInput = document.getElementById('message-input');
  if (msgInput) {
    msgInput.value = (msgInput.value ? msgInput.value + '\n\n' : '') + textToInsert;
    msgInput.focus();
    showTgramNotification('Цитата вставлена в поле ввода чата', 'success');
  }
}

// Make globally accessible
window.loadTelegramChannels = loadTelegramChannels;
window.handleAddTelegramChannel = handleAddTelegramChannel;
window.handleUnsubscribeTelegramChannel = handleUnsubscribeTelegramChannel;
window.handleReindexTelegramChannel = handleReindexTelegramChannel;
window.executeTelegramSearch = executeTelegramSearch;
window.filterByChannel = filterByChannel;
window.copyTelegramLink = copyTelegramLink;
window.sendTelegramResultToChat = sendTelegramResultToChat;
