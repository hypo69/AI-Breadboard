// Helpdesk Tab — Admin Control Panel Logic
'use strict';

(function() {
  let hdTickets = [];
  let hdActiveTicketId = null;
  let hdActiveTicket = null;
  let hdCurrentFilter = 'all';
  let hdWs = null;
  let hdClientId = 'admin_tab_' + Math.random().toString(36).substring(2, 9);
  let hdStatsInterval = null;

  async function initHelpdeskTab() {
    console.log('[HelpdeskTab] Initializing Helpdesk multi-tool tab...');
    setupEventListeners();
    initWebSocket();
    await loadTickets();
    await updateStats();

    if (window.registerTabPoller) {
      window.registerTabPoller('tab-helpdesk', updateStats, 15000, { immediate: false });
    } else if (!hdStatsInterval) {
      hdStatsInterval = setInterval(updateStats, 15000);
    }
  }

  function initWebSocket() {
    if (hdWs && hdWs.readyState === WebSocket.OPEN) return;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/helpdesk/ws/${hdClientId}?role=operator`;
    
    try {
      hdWs = new WebSocket(wsUrl);
      hdWs.onopen = () => console.log('[HelpdeskTab] WS Connected as Admin Operator');
      hdWs.onmessage = (event) => {
        try {
          const packet = JSON.parse(event.data);
          handleIncomingPacket(packet);
        } catch (e) {
          console.error('[HelpdeskTab] WS Parse error:', e);
        }
      };
      hdWs.onclose = () => {
        console.warn('[HelpdeskTab] WS Disconnected, reconnecting in 5s...');
        setTimeout(initWebSocket, 5000);
      };
    } catch (e) {
      console.warn('[HelpdeskTab] WS Init failed:', e);
    }
  }

  function handleIncomingPacket(packet) {
    const { type, ticket, message, ticket_id } = packet;

    if (type === 'new_ticket_alert') {
      if (typeof showNotification === 'function') {
        showNotification(`🛟 Новое обращение #${ticket?.ticket_number}: ${ticket?.subject}`, 'warning');
      }
      loadTickets();
      updateStats();
    } else if (type === 'new_ticket_message') {
      if (hdActiveTicketId === ticket_id) {
        appendMessage(message);
        scrollMessagesToBottom();
      }
      loadTickets();
    } else if (type === 'ticket_updated') {
      if (hdActiveTicketId === ticket?.id) {
        hdActiveTicket = ticket;
        renderActiveTicketHeader(ticket);
      }
      loadTickets();
      updateStats();
    }
  }

  async function loadTickets() {
    const listContainer = document.getElementById('hd-tab-ticket-list');
    if (!listContainer) return;

    try {
      let url = `/api/helpdesk/tickets?status=${encodeURIComponent(hdCurrentFilter)}`;
      const searchInput = document.getElementById('hd-tab-search-input');
      const query = searchInput?.value?.trim();
      if (query) {
        url += `&search=${encodeURIComponent(query)}`;
      }

      const res = await fetch(url, { credentials: 'include' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      hdTickets = data.tickets || [];
      renderTicketList(hdTickets);
    } catch (err) {
      console.error('[HelpdeskTab] Error loading tickets:', err);
      listContainer.innerHTML = `<div class="p-3 text-danger small">Ошибка загрузки тикетов: ${err.message}</div>`;
    }
  }

  async function updateStats() {
    try {
      const res = await fetch('/api/helpdesk/stats', { credentials: 'include' });
      if (!res.ok) return;
      const data = await res.json();
      const stats = data.stats || {};

      const elOpen = document.getElementById('hd-metric-open');
      const elProg = document.getElementById('hd-metric-progress');
      const elRes = document.getElementById('hd-metric-resolved');
      const elTot = document.getElementById('hd-metric-total');

      if (elOpen) elOpen.textContent = stats.open || 0;
      if (elProg) elProg.textContent = stats.in_progress || 0;
      if (elRes) elRes.textContent = stats.resolved || 0;
      if (elTot) elTot.textContent = stats.total || 0;
    } catch (e) {
      console.debug('[HelpdeskTab] Stats update skipped:', e);
    }
  }

  function renderTicketList(ticketsList) {
    const listContainer = document.getElementById('hd-tab-ticket-list');
    if (!listContainer) return;

    if (!ticketsList || ticketsList.length === 0) {
      listContainer.innerHTML = '<div class="text-center text-muted p-4 small">Нет обращений по выбранному фильтру</div>';
      return;
    }

    listContainer.innerHTML = ticketsList.map(t => {
      const isActive = t.id === hdActiveTicketId;
      const statusBadge = getStatusBadge(t.status);
      const priorityBadge = getPriorityBadge(t.priority);
      const timeStr = formatTimeAgo(t.created_at);

      return `
        <div class="card p-2 border-secondary-subtle ${isActive ? 'bg-primary-subtle border-primary' : 'bg-body'} hover-shadow"
             style="cursor: pointer; transition: all 0.15s ease;"
             onclick="window.selectHelpdeskTicket('${t.id}')">
          <div class="d-flex justify-content-between align-items-center mb-1">
            <span class="badge bg-secondary-subtle text-body fw-bold">#${t.ticket_number}</span>
            <div class="d-flex gap-1">
              ${priorityBadge}
              ${statusBadge}
            </div>
          </div>
          <h6 class="fw-bold mb-1 text-truncate" style="font-size: 0.9rem;">${escapeHtml(t.subject)}</h6>
          <div class="d-flex justify-content-between align-items-center small text-muted" style="font-size: 0.75rem;">
            <span class="text-truncate" style="max-width: 140px;"><i class="bi bi-person me-1"></i>${escapeHtml(t.user_name || t.user_email || 'Пользователь')}</span>
            <span>${timeStr}</span>
          </div>
        </div>
      `;
    }).join('');
  }

  async function selectTicket(ticketId) {
    hdActiveTicketId = ticketId;
    renderTicketList(hdTickets); // re-render for active highlight

    const emptyState = document.getElementById('hd-tab-empty-state');
    const activeView = document.getElementById('hd-tab-active-view');
    if (emptyState) emptyState.classList.add('d-none');
    if (activeView) {
      activeView.classList.remove('d-none');
      activeView.classList.add('d-flex');
    }

    try {
      const res = await fetch(`/api/helpdesk/tickets/${ticketId}`, { credentials: 'include' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      hdActiveTicket = data.ticket;
      renderActiveTicketHeader(data.ticket);
      renderMessagesStream(data.messages || []);
      scrollMessagesToBottom();
    } catch (err) {
      console.error('[HelpdeskTab] Error loading ticket details:', err);
      if (typeof showNotification === 'function') showNotification('Ошибка загрузки тикета: ' + err.message, 'danger');
    }
  }

  function renderActiveTicketHeader(ticket) {
    if (!ticket) return;
    const numEl = document.getElementById('hd-active-number');
    const subEl = document.getElementById('hd-active-subject');
    const metaEl = document.getElementById('hd-active-meta');
    const prioLabel = document.getElementById('hd-active-priority-label');

    if (numEl) numEl.textContent = `#${ticket.ticket_number}`;
    if (subEl) subEl.textContent = ticket.subject;
    if (metaEl) {
      const author = ticket.user_name || ticket.user_email || 'User';
      metaEl.textContent = `Автор: ${author} (${ticket.category || 'technical'}) • ${formatTimeAgo(ticket.created_at)}`;
    }
    if (prioLabel) {
      const pLabels = { low: '🟢 Низкий', normal: '🔵 Обычный', high: '🟠 Высокий', urgent: '🔴 Срочный' };
      prioLabel.textContent = pLabels[ticket.priority] || ticket.priority;
    }
  }

  function renderMessagesStream(messages) {
    const stream = document.getElementById('hd-tab-messages-stream');
    if (!stream) return;

    if (!messages || messages.length === 0) {
      stream.innerHTML = '<div class="text-center text-muted p-4 small">В данном тикете пока нет сообщений</div>';
      return;
    }

    stream.innerHTML = messages.map(m => createMessageHtml(m)).join('');
  }

  function createMessageHtml(m) {
    const isStaff = m.sender_role === 'operator' || m.sender_role === 'admin';
    const isNote = Boolean(m.is_internal_note);
    const timeStr = new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    let cardBg = isStaff ? 'bg-primary-subtle border-primary-subtle' : 'bg-body-tertiary border-secondary-subtle';
    let align = isStaff ? 'align-self-end' : 'align-self-start';

    if (isNote) {
      cardBg = 'bg-warning-subtle border-warning';
    }

    let parsedText = escapeHtml(m.message);
    if (window.marked && typeof window.marked.parse === 'function') {
      try {
        parsedText = window.marked.parse(m.message);
      } catch (e) {}
    }

    return `
      <div class="d-flex flex-column ${align}" style="max-width: 80%;">
        <div class="card p-2 ${cardBg} shadow-sm">
          <div class="d-flex justify-content-between align-items-center mb-1 gap-2 small">
            <strong>${isNote ? '🔒 Заметка оператора (' + escapeHtml(m.sender_name) + ')' : escapeHtml(m.sender_name || (isStaff ? 'Оператор' : 'Пользователь'))}</strong>
            <span class="text-muted" style="font-size: 0.75rem;">${timeStr}</span>
          </div>
          <div class="message-content text-break" style="font-size: 0.88rem;">${parsedText}</div>
        </div>
      </div>
    `;
  }

  function appendMessage(m) {
    const stream = document.getElementById('hd-tab-messages-stream');
    if (!stream) return;
    const msgDiv = document.createElement('div');
    msgDiv.innerHTML = createMessageHtml(m);
    stream.appendChild(msgDiv.firstElementChild);
  }

  function scrollMessagesToBottom() {
    const stream = document.getElementById('hd-tab-messages-stream');
    if (stream) {
      setTimeout(() => {
        stream.scrollTop = stream.scrollHeight;
      }, 50);
    }
  }

  async function sendReply() {
    if (!hdActiveTicketId) return;
    const replyInput = document.getElementById('hd-reply-input');
    const isInternalNote = document.getElementById('hd-switch-internal-note')?.checked || false;
    const text = replyInput?.value?.trim();

    if (!text) return;

    try {
      const res = await fetch(`/api/helpdesk/tickets/${hdActiveTicketId}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          message: text,
          is_internal_note: isInternalNote
        })
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      replyInput.value = '';
      const data = await res.json();
      if (data.message) {
        appendMessage(data.message);
        scrollMessagesToBottom();
      }
      loadTickets();
    } catch (err) {
      console.error('[HelpdeskTab] Error sending message:', err);
      if (typeof showNotification === 'function') showNotification('Ошибка отправки: ' + err.message, 'danger');
    }
  }

  async function updateTicketStatus(status) {
    if (!hdActiveTicketId) return;
    try {
      const res = await fetch(`/api/helpdesk/tickets/${hdActiveTicketId}/status`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ status })
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      if (typeof showNotification === 'function') showNotification(`Статус изменен на: ${status}`, 'success');
      loadTickets();
      updateStats();
      selectTicket(hdActiveTicketId);
    } catch (err) {
      console.error('[HelpdeskTab] Status update failed:', err);
    }
  }

  async function updateTicketPriority(priority) {
    if (!hdActiveTicketId) return;
    try {
      const res = await fetch(`/api/helpdesk/tickets/${hdActiveTicketId}/priority`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ priority })
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      if (typeof showNotification === 'function') showNotification(`Приоритет изменен на: ${priority}`, 'success');
      loadTickets();
      selectTicket(hdActiveTicketId);
    } catch (err) {
      console.error('[HelpdeskTab] Priority update failed:', err);
    }
  }

  async function generateAiDraft() {
    if (!hdActiveTicket) return;
    const replyInput = document.getElementById('hd-reply-input');
    if (!replyInput) return;

    replyInput.value = '🤖 Генерация черновика ответа ИИ...';
    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          prompt: `Сформулируй вежливый, профессиональный и конкретный ответ технической поддержки Helpdesk на следующее обращение пользователя.
Тема: "${hdActiveTicket.subject}"
Описание: "${hdActiveTicket.description || ''}"
Категория: "${hdActiveTicket.category}"
Ответ должен быть кратким и готовым к отправке клиенту.`,
          use_rag: false
        })
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const answer = data.response || data.text || '';
      replyInput.value = answer.trim();
    } catch (e) {
      replyInput.value = `Здравствуйте! Мы изучили ваше обращение по теме "${hdActiveTicket.subject}". Специалисты уже занимаются решением.`;
    }
  }

  function setupEventListeners() {
    // Search input debounce
    const searchInput = document.getElementById('hd-tab-search-input');
    let searchTimer = null;
    if (searchInput) {
      searchInput.oninput = () => {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(loadTickets, 300);
      };
    }

    // Filter buttons
    const filterBtns = document.querySelectorAll('#hd-tab-status-filters button');
    filterBtns.forEach(btn => {
      btn.onclick = () => {
        filterBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        hdCurrentFilter = btn.getAttribute('data-filter') || 'all';
        loadTickets();
      };
    });

    // Send reply button & shortcut
    const btnSend = document.getElementById('hd-btn-send-reply');
    if (btnSend) btnSend.onclick = sendReply;

    const replyInput = document.getElementById('hd-reply-input');
    if (replyInput) {
      replyInput.onkeydown = (e) => {
        if (e.ctrlKey && e.key === 'Enter') {
          e.preventDefault();
          sendReply();
        }
      };
    }

    // Internal note switcher toggle label
    const switchNote = document.getElementById('hd-switch-internal-note');
    const modeBadge = document.getElementById('hd-composer-mode-badge');
    if (switchNote && modeBadge) {
      switchNote.onchange = () => {
        if (switchNote.checked) {
          modeBadge.textContent = '🔒 Режим: Внутренняя скрытая заметка';
          modeBadge.className = 'badge bg-warning text-dark';
        } else {
          modeBadge.textContent = 'Режим: Публичный ответ';
          modeBadge.className = 'badge bg-secondary-subtle text-body';
        }
      };
    }

    // Status action buttons
    document.querySelectorAll('.hd-status-opt').forEach(btn => {
      btn.onclick = () => {
        const st = btn.getAttribute('data-status');
        if (st) updateTicketStatus(st);
      };
    });

    // Priority dropdown items
    document.querySelectorAll('.hd-priority-opt').forEach(opt => {
      opt.onclick = (e) => {
        e.preventDefault();
        const prio = opt.getAttribute('data-priority');
        if (prio) updateTicketPriority(prio);
      };
    });

    // Quick canned responses
    document.querySelectorAll('.hd-quick-template').forEach(tplBtn => {
      tplBtn.onclick = () => {
        const tpl = tplBtn.getAttribute('data-tpl');
        if (tpl && replyInput) {
          replyInput.value = tpl;
          replyInput.focus();
        }
      };
    });

    // AI Assist Draft Button
    const aiAssistBtn = document.getElementById('hd-btn-ai-assist');
    if (aiAssistBtn) aiAssistBtn.onclick = generateAiDraft;

    // Submit new ticket in modal
    const btnSubmitNew = document.getElementById('hd-btn-submit-new-ticket');
    if (btnSubmitNew) {
      btnSubmitNew.onclick = async () => {
        const subject = document.getElementById('hd-new-ticket-subject')?.value?.trim();
        const category = document.getElementById('hd-new-ticket-category')?.value || 'technical';
        const priority = document.getElementById('hd-new-ticket-priority')?.value || 'normal';
        const message = document.getElementById('hd-new-ticket-message')?.value?.trim();

        if (!subject || !message) {
          window.showToast?.('Пожалуйста, заполните тему и текст обращения.', 'warning') || alert('Пожалуйста, заполните тему и текст обращения.');
          return;
        }

        try {
          btnSubmitNew.disabled = true;
          const res = await fetch('/api/helpdesk/tickets', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ subject, category, priority, message })
          });

          if (!res.ok) throw new Error(`HTTP ${res.status}`);
          const data = await res.json();
          if (data.status === 'success') {
            window.showToast?.(`Тикет #${data.ticket.ticket_number} успешно создан!`, 'success');
            const modalEl = document.getElementById('hdCreateTicketModal');
            const modal = bootstrap.Modal.getInstance(modalEl);
            modal?.hide();

            document.getElementById('hd-new-ticket-subject').value = '';
            document.getElementById('hd-new-ticket-message').value = '';

            await loadTickets();
            await updateStats();
            if (data.ticket?.id) {
              selectTicket(data.ticket.id);
            }
          }
        } catch (err) {
          console.error('[HelpdeskTab] Create ticket failed:', err);
          window.showToast?.('Ошибка создания тикета: ' + err.message, 'danger') || alert('Ошибка создания тикета: ' + err.message);
        } finally {
          btnSubmitNew.disabled = false;
        }
      };
    }
  }

  function getStatusBadge(status) {
    switch (status) {
      case 'open': return '<span class="badge bg-danger-subtle text-danger">Новый</span>';
      case 'in_progress': return '<span class="badge bg-warning-subtle text-warning">В работе</span>';
      case 'resolved': return '<span class="badge bg-success-subtle text-success">Решено</span>';
      case 'closed': return '<span class="badge bg-secondary-subtle text-body">Закрыт</span>';
      default: return `<span class="badge bg-secondary">${status}</span>`;
    }
  }

  function getPriorityBadge(priority) {
    switch (priority) {
      case 'urgent': return '<span class="badge bg-danger">🔴 Срочно</span>';
      case 'high': return '<span class="badge bg-warning text-dark">🟠 Высокий</span>';
      case 'low': return '<span class="badge bg-secondary-subtle text-muted">🟢 Низкий</span>';
      default: return '<span class="badge bg-info-subtle text-info">🔵 Обычный</span>';
    }
  }

  function formatTimeAgo(isoStr) {
    if (!isoStr) return '';
    try {
      const diffMs = Date.now() - new Date(isoStr).getTime();
      const diffMin = Math.floor(diffMs / 60000);
      if (diffMin < 1) return 'только что';
      if (diffMin < 60) return `${diffMin} мин назад`;
      const diffHours = Math.floor(diffMin / 60);
      if (diffHours < 24) return `${diffHours} ч назад`;
      return `${Math.floor(diffHours / 24)} дн назад`;
    } catch (e) {
      return '';
    }
  }

  function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // Global window functions for event hooks
  window.initHelpdeskTab = initHelpdeskTab;
  window.refreshHelpdeskTab = () => { loadTickets(); updateStats(); };
  window.selectHelpdeskTicket = selectTicket;
  window.openCreateTicketModal = () => {
    const modalEl = document.getElementById('hdCreateTicketModal');
    if (modalEl) {
      const modal = new bootstrap.Modal(modalEl);
      modal.show();
    }
  };
})();
