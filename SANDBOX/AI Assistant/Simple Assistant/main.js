/**
 * =============================================================================
 * Process Name: Simple Assistant Chat Controller
 * =============================================================================
 * Description:
 *   Coordinates the browser chat state, history serialization, and SSE response handling.
 *   Keeps model and developer controls outside the focused user interface.
 *
 * File: main.js
 * Project: ai-breadboard
 * Module: Simple Assistant
 * Author: hypo69
 * Copyright: (C) 2026 hypo69
 * =============================================================================
 */

const elements = {
  form: document.querySelector('#chat-form'),
  input: document.querySelector('#message-input'),
  sendButton: document.querySelector('#send-button'),
  clearButton: document.querySelector('#clear-button'),
  conversation: document.querySelector('#conversation'),
  welcome: document.querySelector('#welcome-message'),
  state: document.querySelector('#connection-state'),
  stateLabel: document.querySelector('#state-label'),
  hint: document.querySelector('#hint-text')
};

const state = { history: [], controller: null, isStreaming: false };

function decodeLabel(label) {
  const decoder = document.createElement('textarea');
  decoder.innerHTML = label;
  return decoder.value;
}

function setStatus(label, mode = '') {
  elements.state.className = `connection-state ${mode}`.trim();
  elements.stateLabel.textContent = decodeLabel(label);
}

function scrollConversation() {
  elements.conversation.scrollTop = elements.conversation.scrollHeight;
}

function addMessage(role, text) {
  elements.welcome.hidden = true;
  const message = document.createElement('article');
  message.className = `message ${role}`;
  const label = document.createElement('span');
  label.className = 'message-label';
  label.textContent = role === 'user' ? 'You' : 'AI';
  const bubble = document.createElement('div');
  bubble.className = 'message-bubble';
  bubble.textContent = text;
  message.append(role === 'user' ? bubble : label, role === 'user' ? label : bubble);
  elements.conversation.append(message);
  scrollConversation();
  return bubble;
}

function addStatus(text) {
  const status = document.createElement('div');
  status.className = 'status-line';
  status.textContent = text;
  elements.conversation.append(status);
  scrollConversation();
  return status;
}

function setStreamingMode(isStreaming) {
  state.isStreaming = isStreaming;
  elements.sendButton.classList.toggle('stop', isStreaming);
  elements.sendButton.querySelector('span').textContent = isStreaming ? '×' : '↑';
  elements.sendButton.setAttribute('aria-label', isStreaming ? 'Stop' : 'Send');
  elements.sendButton.title = isStreaming ? 'Stop' : 'Send';
  elements.input.disabled = isStreaming;
  elements.clearButton.disabled = isStreaming;
}

async function readStream(response, assistantBubble, statusNode) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let answer = '';

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';
    for (const line of lines) {
      const data = parseEvent(line);
      if (!data) continue;
      if (data.error) throw new Error(data.error);
      if (data.status) statusNode.textContent = data.status;
      if (data.text) {
        answer += data.text;
        assistantBubble.textContent = answer;
        scrollConversation();
      }
    }
  }
  return answer;
}

function parseEvent(line) {
  const trimmed = line.trim();
  if (!trimmed.startsWith('data: ')) return {};
  try {
    return JSON.parse(trimmed.slice(6));
  } catch {
    return {};
  }
}

async function sendMessage(message) {
  state.controller = new AbortController();
  setStreamingMode(true);
  setStatus('&#1044;&#1091;&#1084;&#1072;&#1102;...', 'busy');
  addMessage('user', message);
  const assistantBubble = addMessage('assistant', '');
  const statusNode = addStatus('&#1055;&#1086;&#1076;&#1075;&#1086;&#1090;&#1082;&#1072; &#1086;&#1090;&#1074;&#1077;&#1090;&#1072;...');

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify({ message, history: state.history, generation_config: {} }),
      signal: state.controller.signal
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const answer = await readStream(response, assistantBubble, statusNode);
    state.history.push({ role: 'user', parts: [message] }, { role: 'model', parts: [answer] });
    statusNode.remove();
    setStatus('&#1043;&#1086;&#1090;&#1086;&#1074;');
  } catch (error) {
    statusNode.textContent = error.name === 'AbortError' ? 'Stopped' : `Error: ${error.message}`;
    setStatus('Error', 'error');
  } finally {
    state.controller = null;
    setStreamingMode(false);
    elements.input.focus();
  }
}

elements.form.addEventListener('submit', (event) => {
  event.preventDefault();
  if (state.isStreaming) {
    state.controller?.abort();
    return;
  }
  const message = elements.input.value.trim();
  if (!message) return;
  elements.input.value = '';
  elements.input.style.height = 'auto';
  sendMessage(message);
});

elements.input.addEventListener('input', () => {
  elements.input.style.height = 'auto';
  elements.input.style.height = `${Math.min(elements.input.scrollHeight, 150)}px`;
});

elements.input.addEventListener('keydown', (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    elements.form.requestSubmit();
  }
});

elements.clearButton.addEventListener('click', () => {
  if (state.isStreaming) return;
  state.history = [];
  elements.conversation.replaceChildren(elements.welcome);
  elements.welcome.hidden = false;
  setStatus('&#1043;&#1086;&#1090;&#1086;&#1074;');
});

setStatus('&#1043;&#1086;&#1090;&#1086;&#1074;');
