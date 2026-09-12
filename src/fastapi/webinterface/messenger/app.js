/**
 * AI Breadboard Messenger & WebRTC Conference Client
 */

const CONFIG = {
  apiBase: window.location.origin,
  wsProtocol: window.location.protocol === 'https:' ? 'wss:' : 'ws:',
  iceServers: [{ urls: 'stun:stun.l.google.com:19302' }, { urls: 'stun:stun1.l.google.com:19302' }],
};

let currentUser = null;
let activeRoomId = null;
let activeRoomData = null;
let ws = null;
let rooms = [];
let mediaRecorder = null;
let recordedAudioChunks = [];
let isRecordingVoice = false;

// WebRTC Call State
let peerConnection = null;
let localStream = null;
let remoteStream = null;
let isInCall = false;

// DOM Elements
const chatListEl = document.getElementById('chatList');
const messagesContainerEl = document.getElementById('messagesContainer');
const messageInputEl = document.getElementById('messageInput');
const btnSendMessageEl = document.getElementById('btnSendMessage');
const btnRecordVoiceEl = document.getElementById('btnRecordVoice');
const btnAttachFileEl = document.getElementById('btnAttachFile');
const fileAttachmentInputEl = document.getElementById('fileAttachmentInput');
const typingIndicatorEl = document.getElementById('typingIndicator');
const chatHeaderEl = document.getElementById('chatHeader');
const chatInputBarEl = document.getElementById('chatInputBar');
const activeChatTitleEl = document.getElementById('activeChatTitle');
const activeChatSubtitleEl = document.getElementById('activeChatSubtitle');
const newChatModalEl = document.getElementById('newChatModal');
const videoCallOverlayEl = document.getElementById('videoCallOverlay');

// Initialize
window.addEventListener('DOMContentLoaded', async () => {
  await initUserProfile();
  initWebSocket();
  await loadRooms();
  setupEventListeners();
  registerServiceWorker();
});

async function initUserProfile() {
  try {
    const res = await fetch(`${CONFIG.apiBase}/api/messenger/users/me`, { credentials: 'include' });
    const data = await res.json();
    if (data.status === 'success') {
      currentUser = data.user;
      document.getElementById('myName').innerText = currentUser.display_name || currentUser.username;
      document.getElementById('myAvatarText').innerText = (currentUser.display_name || 'U')[0].toUpperCase();
    }
  } catch (e) {
    console.error('Failed to load user profile:', e);
  }
}

function initWebSocket() {
  if (!currentUser) return;
  const wsUrl = `${CONFIG.wsProtocol}//${window.location.host}/api/messenger/ws/${currentUser.id}`;
  ws = new WebSocket(wsUrl);

  ws.onopen = () => console.log('Messenger WebSocket Connected');
  ws.onmessage = (event) => handleIncomingWsPacket(JSON.parse(event.data));
  ws.onclose = () => {
    console.warn('WebSocket closed. Reconnecting in 3s...');
    setTimeout(initWebSocket, 3000);
  };
}

function handleIncomingWsPacket(packet) {
  const { type, message, room_id, user_id, bot_name, is_online } = packet;

  if (type === 'new_message') {
    if (activeRoomId === message.room_id) {
      appendMessageToChat(message);
      scrollToBottom();
      // Send read receipt
      if (ws && ws.readyState === WebSocket.OPEN && message.sender_id !== currentUser.id) {
        ws.send(JSON.stringify({ type: 'message_read', room_id: activeRoomId, message_id: message.id }));
      }
    }
    updateRoomLastMessage(message);
  } else if (type === 'typing_start') {
    if (activeRoomId === room_id && user_id !== currentUser.id) {
      typingIndicatorEl.style.display = 'block';
      typingIndicatorEl.innerText = `${bot_name || 'Someone'} is typing...`;
    }
  } else if (type === 'typing_stop') {
    if (activeRoomId === room_id) {
      typingIndicatorEl.style.display = 'none';
    }
  } else if (type === 'presence_update') {
    updateUserPresenceUI(user_id, is_online);
  } else if (type.startsWith('webrtc_')) {
    handleWebRTCSignalPacket(packet);
  }
}

async function loadRooms() {
  try {
    const res = await fetch(`${CONFIG.apiBase}/api/messenger/rooms`, { credentials: 'include' });
    const data = await res.json();
    if (data.status === 'success') {
      rooms = data.rooms;
      renderRoomsList();
    }
  } catch (e) {
    console.error('Error loading rooms:', e);
  }
}

function renderRoomsList() {
  chatListEl.innerHTML = '';
  rooms.forEach((r) => {
    const item = document.createElement('div');
    item.className = `chat-item ${activeRoomId === r.id ? 'active' : ''}`;
    item.onclick = () => selectRoom(r);

    const initial = (r.title || '#')[0].toUpperCase();
    const lastContent = r.last_message ? (r.last_message.content || '[Attachment]') : 'No messages yet';
    const unreadHtml = r.unread_count > 0 ? `<span class="unread-badge">${r.unread_count}</span>` : '';
    const onlineHtml = r.is_online ? '<div class="status-dot online"></div>' : '';

    item.innerHTML = `
      <div class="avatar">
        <span>${initial}</span>
        ${onlineHtml}
      </div>
      <div class="chat-info">
        <div class="chat-title-row">
          <span class="chat-title">${escapeHtml(r.title)}</span>
          <span class="chat-time">${r.last_message ? formatTime(r.last_message.created_at) : ''}</span>
        </div>
        <div class="chat-snippet-row">
          <span class="chat-snippet">${escapeHtml(lastContent)}</span>
          ${unreadHtml}
        </div>
      </div>
    `;
    chatListEl.appendChild(item);
  });
}

async function selectRoom(room) {
  activeRoomId = room.id;
  activeRoomData = room;
  renderRoomsList();

  chatHeaderEl.style.display = 'flex';
  chatInputBarEl.style.display = 'flex';
  document.getElementById('emptyPlaceholder').style.display = 'none';

  activeChatTitleEl.innerText = room.title;
  activeChatSubtitleEl.innerText = room.room_type === 'direct' ? (room.is_online ? 'Online' : 'Offline') : `${room.members_count} members`;
  document.getElementById('activeChatAvatarText').innerText = (room.title || '#')[0].toUpperCase();

  await loadRoomMessages(room.id);
}

async function loadRoomMessages(roomId) {
  messagesContainerEl.innerHTML = '';
  try {
    const res = await fetch(`${CONFIG.apiBase}/api/messenger/rooms/${roomId}/messages`, { credentials: 'include' });
    const data = await res.json();
    if (data.status === 'success') {
      data.messages.forEach(appendMessageToChat);
      scrollToBottom();
    }
  } catch (e) {
    console.error('Error loading messages:', e);
  }
}

function appendMessageToChat(msg) {
  const isOut = msg.sender_id === currentUser.id;
  const bubble = document.createElement('div');
  bubble.className = `message-bubble ${isOut ? 'outgoing' : 'incoming'}`;

  let senderHeader = '';
  if (!isOut && activeRoomData && activeRoomData.room_type !== 'direct') {
    senderHeader = `<div class="message-sender">${escapeHtml(msg.sender_name || 'Member')}</div>`;
  }

  let attachmentsHtml = '';
  if (msg.attachments && msg.attachments.length > 0) {
    msg.attachments.forEach((att) => {
      if (att.file_type === 'audio') {
        attachmentsHtml += `<audio class="audio-player-custom" controls src="${att.file_path}"></audio>`;
      } else if (att.file_type === 'image') {
        attachmentsHtml += `<img src="${att.file_path}" style="max-width:100%; border-radius:10px; margin-top:6px;" />`;
      } else {
        attachmentsHtml += `<div style="margin-top:6px;"><a href="${att.file_path}" download style="color:#60a5fa;">📎 ${escapeHtml(att.file_name)}</a></div>`;
      }
    });
  }

  bubble.innerHTML = `
    ${senderHeader}
    <div>${escapeHtml(msg.content || '')}</div>
    ${attachmentsHtml}
    <div class="message-meta">
      <span>${formatTime(msg.created_at)}</span>
      ${isOut ? '<span>✓✓</span>' : ''}
    </div>
  `;
  messagesContainerEl.appendChild(bubble);
}

function updateRoomLastMessage(msg) {
  const r = rooms.find((x) => x.id === msg.room_id);
  if (r) {
    r.last_message = msg;
    renderRoomsList();
  }
}

function updateUserPresenceUI(userId, isOnline) {
  rooms.forEach((r) => {
    if (r.room_type === 'direct') {
      r.is_online = isOnline;
    }
  });
  renderRoomsList();
}

// Send Message
async function sendMessage() {
  const content = messageInputEl.value.trim();
  if (!content || !activeRoomId) return;

  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({
      type: 'send_message',
      room_id: activeRoomId,
      content: content,
      message_type: 'text'
    }));
  } else {
    // REST Fallback
    await fetch(`${CONFIG.apiBase}/api/messenger/rooms/${activeRoomId}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ content: content, message_type: 'text' }),
    });
  }

  messageInputEl.value = '';
}

// Voice Note Recording
async function toggleVoiceRecording() {
  if (isRecordingVoice) {
    mediaRecorder.stop();
    isRecordingVoice = false;
    btnRecordVoiceEl.style.background = 'var(--bg-secondary)';
  } else {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder = new MediaRecorder(stream);
      recordedAudioChunks = [];

      mediaRecorder.ondataavailable = (e) => recordedAudioChunks.push(e.data);
      mediaRecorder.onstop = async () => {
        const blob = new Blob(recordedAudioChunks, { type: 'audio/webm' });
        const formData = new FormData();
        formData.append('file', blob, `voice_${Date.now()}.webm`);
        formData.append('duration_sec', '3.0');

        const res = await fetch(`${CONFIG.apiBase}/api/messenger/upload`, {
          method: 'POST',
          credentials: 'include',
          body: formData,
        });
        const data = await res.json();
        if (data.status === 'success') {
          ws.send(JSON.stringify({
            type: 'send_message',
            room_id: activeRoomId,
            content: '',
            message_type: 'audio',
            attachment_ids: [data.attachment_id],
          }));
        }
      };

      mediaRecorder.start();
      isRecordingVoice = true;
      btnRecordVoiceEl.style.background = 'var(--danger-color)';
    } catch (e) {
      alert('Microphone access required for voice notes.');
    }
  }
}

// WebRTC Conference / Call Handler
async function startWebRTCCall(callType = 'video') {
  if (!activeRoomId) return;
  videoCallOverlayEl.style.display = 'flex';
  isInCall = true;

  try {
    localStream = await navigator.mediaDevices.getUserMedia({
      video: callType === 'video',
      audio: true,
    });
    document.getElementById('localVideo').srcObject = localStream;

    initPeerConnection();
    localStream.getTracks().forEach((track) => peerConnection.addTrack(track, localStream));

    const offer = await peerConnection.createOffer();
    await peerConnection.setLocalDescription(offer);

    ws.send(JSON.stringify({
      type: 'webrtc_offer',
      data: {
        action: 'offer',
        room_id: activeRoomId,
        sdp: offer.sdp,
        call_type: callType,
      },
    }));
  } catch (e) {
    console.error('Call initialization failed:', e);
  }
}

function initPeerConnection() {
  peerConnection = new RTCPeerConnection({ iceServers: CONFIG.iceServers });

  peerConnection.onicecandidate = (event) => {
    if (event.candidate && ws) {
      ws.send(JSON.stringify({
        type: 'webrtc_ice_candidate',
        data: {
          action: 'ice_candidate',
          room_id: activeRoomId,
          candidate: event.candidate,
        },
      }));
    }
  };

  peerConnection.ontrack = (event) => {
    remoteStream = event.streams[0];
    const remoteVid = document.getElementById('remoteVideo');
    remoteVid.srcObject = remoteStream;
    document.getElementById('remoteVideoTile').style.display = 'flex';
  };
}

async function handleWebRTCSignalPacket(packet) {
  const { type, sdp, candidate, sender_id, room_id } = packet;

  if (type === 'webrtc_offer') {
    videoCallOverlayEl.style.display = 'flex';
    isInCall = true;
    initPeerConnection();

    localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
    document.getElementById('localVideo').srcObject = localStream;
    localStream.getTracks().forEach((track) => peerConnection.addTrack(track, localStream));

    await peerConnection.setRemoteDescription(new RTCSessionDescription({ type: 'offer', sdp }));
    const answer = await peerConnection.createAnswer();
    await peerConnection.setLocalDescription(answer);

    ws.send(JSON.stringify({
      type: 'webrtc_answer',
      data: {
        action: 'answer',
        room_id: room_id,
        target_id: sender_id,
        sdp: answer.sdp,
      },
    }));
  } else if (type === 'webrtc_answer') {
    if (peerConnection) {
      await peerConnection.setRemoteDescription(new RTCSessionDescription({ type: 'answer', sdp }));
    }
  } else if (type === 'webrtc_ice_candidate') {
    if (peerConnection && candidate) {
      await peerConnection.addIceCandidate(new RTCIceCandidate(candidate));
    }
  }
}

function endCall() {
  if (localStream) localStream.getTracks().forEach((t) => t.stop());
  if (peerConnection) peerConnection.close();
  peerConnection = null;
  videoCallOverlayEl.style.display = 'none';
  isInCall = false;

  if (ws && activeRoomId) {
    ws.send(JSON.stringify({
      type: 'webrtc_leave_call',
      data: { action: 'leave_call', room_id: activeRoomId },
    }));
  }
}

// Event Listeners
function setupEventListeners() {
  btnSendMessageEl.onclick = sendMessage;
  messageInputEl.onkeydown = (e) => {
    if (e.key === 'Enter') sendMessage();
  };
  btnRecordVoiceEl.onclick = toggleVoiceRecording;
  btnAttachFileEl.onclick = () => fileAttachmentInputEl.click();

  fileAttachmentInputEl.onchange = async () => {
    const file = fileAttachmentInputEl.files[0];
    if (!file || !activeRoomId) return;
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${CONFIG.apiBase}/api/messenger/upload`, {
      method: 'POST',
      credentials: 'include',
      body: formData,
    });
    const data = await res.json();
    if (data.status === 'success') {
      ws.send(JSON.stringify({
        type: 'send_message',
        room_id: activeRoomId,
        content: '',
        message_type: data.file_type,
        attachment_ids: [data.attachment_id],
      }));
    }
  };

  document.getElementById('btnStartVideoCall').onclick = () => startWebRTCCall('video');
  document.getElementById('btnStartAudioCall').onclick = () => startWebRTCCall('audio');
  document.getElementById('btnEndCall').onclick = endCall;

  // New Chat Modal
  document.getElementById('btnNewChat').onclick = () => { newChatModalEl.style.display = 'flex'; };
  document.getElementById('modalBtnCancel').onclick = () => { newChatModalEl.style.display = 'none'; };
  document.getElementById('modalRoomType').onchange = (e) => {
    document.getElementById('modalTitleGroup').style.display = e.target.value !== 'direct' ? 'block' : 'none';
  };

  document.getElementById('modalBtnCreate').onclick = async () => {
    const roomType = document.getElementById('modalRoomType').value;
    const title = document.getElementById('modalRoomTitle').value;
    const res = await fetch(`${CONFIG.apiBase}/api/messenger/rooms`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ room_type: roomType, title: title }),
    });
    const data = await res.json();
    if (data.status === 'success') {
      newChatModalEl.style.display = 'none';
      await loadRooms();
    }
  };
}

function formatTime(isoStr) {
  if (!isoStr) return '';
  const d = new Date(isoStr);
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function scrollToBottom() {
  messagesContainerEl.scrollTop = messagesContainerEl.scrollHeight;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.innerText = text;
  return div.innerHTML;
}

function registerServiceWorker() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('sw.js').catch(console.error);
  }
}
