/**
 * AI Breadboard Helpdesk Management Client
 */

const CONFIG = {
  apiBase: window.location.origin,
  wsProtocol: window.location.protocol === 'https:' ? 'wss:' : 'ws:',
};

let tickets = [];
let activeTicketId = null;
let activeTicket = null;
let currentFilter = 'all';
let ws = null;
let clientId = 'op_' + Math.random().toString(36).substring(2, 9);

// Elements
const ticketListContainer = document.getElementById('ticketListContainer');
const searchTicketInput = document.getElementById('searchTicketInput');
const noTicketSelected = document.getElementById('noTicketSelected');
const activeTicketView = document.getElementById('activeTicketView');
const messagesStream = document.getElementById('messagesStream');
const replyTextInput = document.getElementById('replyTextInput');
const btnSendReply = document.getElementById('btnSendReply');
const switchInternalNote = document.getElementById('switchInternalNote');
const btnRefreshTickets = document.getElementById('btnRefreshTickets');
const hdTypingIndicator = document.getElementById('hdTypingIndicator');

window.addEventListener('DOMContentLoaded', async () => {
  initWebSocket();
  await loadTickets();
  await updateStats();
  setupEventListeners();
  setInterval(updateStats, 15000);
});

function initWebSocket() {
  const wsUrl = `${CONFIG.wsProtocol}//${window.location.host}/api/helpdesk/ws/${clientId}?role=operator`;
  ws = new WebSocket(wsUrl);

  ws.onopen = () => console.log('Helpdesk WebSocket connected as operator');
  ws.onmessage = (event) => {
    try {
      const packet = JSON.parse(event.data);
      handleIncomingPacket(packet);
    } catch (e) {
      console.error('Error parsing WS message:', e);
    }
  };
  ws.onclose = () => {
    console.warn('Helpdesk WebSocket closed. Reconnecting in 3s...');
    setTimeout(initWebSocket, 3000);
  };
}

function handleIncomingPacket(packet) {
  const { type, ticket, message, ticket_id, status } = packet;

  if (type === 'new_ticket_alert') {
    // New ticket created
    playNotificationSound();
    loadTickets();
    updateStats();
  } else if (type === 'new_ticket_message') {
    if (activeTicketId === ticket_id) {
      appendMessageToStream(message);
      scrollToBottom();
    }
    loadTickets();
  } else if (type === 'ticket_updated') {
    if (activeTicketId === ticket.id) {
      activeTicket = ticket;
      updateHeaderUI(ticket);
    }
    loadTickets();
    updateStats();
  }
}

function playNotificationSound() {
  try {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.frequency.setValueAtTime(587.33, audioCtx.currentTime); // D5
    osc.frequency.setValueAtTime(880.00, audioCtx.currentTime + 0.1); // A5
    gain.gain.setValueAtTime(0.2, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.3);
    osc.start();
    osc.stop(audioCtx.currentTime + 0.3);
  } catch (e) {}
}

async function loadTickets() {
  try {
    let url = `${CONFIG.apiBase}/api/helpdesk/tickets?status=${encodeURIComponent(currentFilter)}`;
    const query = searchTicketInput.value.trim();
    if (query) {
      url += `&search=${encodeURIComponent(query)}`;
    }
    const res = await fetch(url, { credentials: 'include' });
    const data = await res.json();
    if (data.status === 'success') {
      tickets = data.tickets;
      renderTicketsList();
    }
  } catch (e) {
    console.error('Failed to load tickets:', e);
  }
}

async function updateStats() {
  try {
    const res = await fetch(`${CONFIG.apiBase}/api/helpdesk/stats`, { credentials: 'include' });
    const data = await res.json();
    if (data.status === 'success') {
      const s = data.stats;
      document.getElementById('statOpen').innerText = `Open: ${s.open_tickets}`;
      document.getElementById('statInProgress').innerText = `Active: ${s.in_progress_tickets}`;
      document.getElementById('statResolved').innerText = `Resolved: ${s.resolved_tickets}`;
    }
  } catch (e) {}
}

function renderTicketsList() {
  ticketListContainer.innerHTML = '';
  if (tickets.length === 0) {
    ticketListContainer.innerHTML = '<div class="text-center text-muted p-4">No tickets matching filter.</div>';
    return;
  }

  tickets.forEach((t) => {
    const card = document.createElement('div');
    card.className = `ticket-card ${activeTicketId === t.id ? 'active' : ''}`;
    card.onclick = () => selectTicket(t.id);

    const priorityBadgeClass = `badge-priority-${t.priority}`;
    const statusBadge = getStatusBadge(t.status);
    const lastSnippet = t.last_message ? escapeHtml(t.last_message.content) : 'No messages';
    const timeAgo = formatTimeAgo(t.updated_at);

    card.innerHTML = `
      <div class="d-flex align-items-center justify-content-between mb-1">
        <span class="badge bg-secondary">#${t.ticket_number}</span>
        <div class="d-flex align-items-center gap-1">
          <span class="badge ${priorityBadgeClass}">${t.priority.toUpperCase()}</span>
          ${statusBadge}
        </div>
      </div>
      <div class="fw-semibold text-truncate text-light mb-1">${escapeHtml(t.subject)}</div>
      <div class="small text-muted text-truncate mb-1">${lastSnippet}</div>
      <div class="d-flex align-items-center justify-content-between text-muted" style="font-size: 0.75rem;">
        <span>👤 ${escapeHtml(t.user_name)}</span>
        <span>${timeAgo}</span>
      </div>
    `;
    ticketListContainer.appendChild(card);
  });
}

function getStatusBadge(status) {
  switch (status) {
    case 'open':
      return '<span class="badge bg-danger">OPEN</span>';
    case 'in_progress':
      return '<span class="badge bg-warning text-dark">IN PROGRESS</span>';
    case 'resolved':
      return '<span class="badge bg-success">RESOLVED</span>';
    case 'closed':
      return '<span class="badge bg-secondary">CLOSED</span>';
    default:
      return `<span class="badge bg-info">${status}</span>`;
  }
}

async function selectTicket(ticketId) {
  activeTicketId = ticketId;
  renderTicketsList();

  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ action: 'subscribe_ticket', ticket_id: ticketId }));
  }

  try {
    const res = await fetch(`${CONFIG.apiBase}/api/helpdesk/tickets/${ticketId}`, { credentials: 'include' });
    const data = await res.json();
    if (data.status === 'success') {
      activeTicket = data.ticket;
      noTicketSelected.classList.add('d-none');
      activeTicketView.classList.remove('d-none');
      activeTicketView.classList.add('d-flex');

      updateHeaderUI(activeTicket);
      renderMessages(data.messages);
      scrollToBottom();
    }
  } catch (e) {
    console.error('Failed to load ticket details:', e);
  }
}

function updateHeaderUI(t) {
  document.getElementById('ticketNumberBadge').innerText = `#${t.ticket_number}`;
  document.getElementById('ticketSubject').innerText = t.subject;
  document.getElementById('ticketUserMeta').innerText = `From: ${t.user_name} (${t.user_email || 'No email'}) • ${formatTimeAgo(t.created_at)}`;
  document.getElementById('currentPriorityLabel').innerText = t.priority.toUpperCase();
}

function renderMessages(messages) {
  messagesStream.innerHTML = '';
  messages.forEach((msg) => appendMessageToStream(msg));
}

function appendMessageToStream(msg) {
  const el = document.createElement('div');
  let typeClass = 'bubble-user';
  if (msg.is_internal_note) {
    typeClass = 'bubble-note';
  } else if (msg.sender_type === 'operator') {
    typeClass = 'bubble-operator';
  }

  const renderedContent = window.marked ? marked.parse(msg.content) : escapeHtml(msg.content);
  const timeStr = new Date(msg.created_at).toLocaleTimeString();

  el.className = `chat-bubble ${typeClass}`;
  el.innerHTML = `
    <div class="d-flex align-items-center justify-content-between gap-2 mb-1" style="font-size: 0.75rem; opacity: 0.85;">
      <strong>${escapeHtml(msg.sender_name)} ${msg.is_internal_note ? '(Internal Note)' : ''}</strong>
      <span>${timeStr}</span>
    </div>
    <div class="message-content">${renderedContent}</div>
  `;
  messagesStream.appendChild(el);
}

function scrollToBottom() {
  messagesStream.scrollTop = messagesStream.scrollHeight;
}

async function sendReply() {
  const content = replyTextInput.value.trim();
  if (!content || !activeTicketId) return;

  const isNote = switchInternalNote.checked;
  btnSendReply.disabled = true;

  try {
    const res = await fetch(`${CONFIG.apiBase}/api/helpdesk/tickets/${activeTicketId}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        content: content,
        is_internal_note: isNote,
        sender_type: 'operator'
      })
    });

    if (res.ok) {
      replyTextInput.value = '';
    }
  } catch (e) {
    console.error('Failed to send reply:', e);
  } finally {
    btnSendReply.disabled = false;
  }
}

async function updateTicketStatus(status) {
  if (!activeTicketId) return;
  try {
    await fetch(`${CONFIG.apiBase}/api/helpdesk/tickets/${activeTicketId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ status: status })
    });
  } catch (e) {
    console.error('Failed to update status:', e);
  }
}

async function updateTicketPriority(priority) {
  if (!activeTicketId) return;
  try {
    await fetch(`${CONFIG.apiBase}/api/helpdesk/tickets/${activeTicketId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ priority: priority })
    });
  } catch (e) {
    console.error('Failed to update priority:', e);
  }
}

function setupEventListeners() {
  btnSendReply.onclick = sendReply;
  replyTextInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      sendReply();
    }
  });

  btnRefreshTickets.onclick = () => {
    loadTickets();
    updateStats();
  };

  searchTicketInput.addEventListener('input', () => {
    loadTickets();
  });

  document.querySelectorAll('#statusFilterGroup button').forEach((btn) => {
    btn.onclick = () => {
      document.querySelectorAll('#statusFilterGroup button').forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      currentFilter = btn.dataset.filter;
      loadTickets();
    };
  });

  document.querySelectorAll('.status-opt').forEach((btn) => {
    btn.onclick = () => updateTicketStatus(btn.dataset.status);
  });

  document.querySelectorAll('.priority-opt').forEach((item) => {
    item.onclick = (e) => {
      e.preventDefault();
      updateTicketPriority(item.dataset.priority);
    };
  });
}

function escapeHtml(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.innerText = str;
  return div.innerHTML;
}

function formatTimeAgo(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  const now = new Date();
  const diffSec = Math.floor((now - d) / 1000);
  if (diffSec < 60) return 'just now';
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHours = Math.floor(diffMin / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  return d.toLocaleDateString();
}
