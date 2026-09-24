/**
 * AI-Breadboard Helpdesk Widget
 * Встраиваемый чат поддержки для любых сайтов
 * 
 * Версия: 1.0.0
 * Лицензия: MIT
 */

(function(window, document) {
  'use strict';

  // Конфигурация по умолчанию
  var defaultConfig = {
    url: 'http://localhost:8080',
    theme: 'dark',
    position: 'right',
    buttonColor: '#3498db',
    welcomeMessage: 'Привет! Чем можем помочь?',
    autoOpen: false,
    showBadge: true,
    onlineText: 'Online',
    offlineText: 'Offline',
    buttonSize: '56px',
    widgetWidth: '380px',
    widgetHeight: '500px',
    zIndex: 999999,
    mobile: {
      enabled: true,
      widgetWidth: '100%',
      position: 'bottom'
    }
  };

  // Глобальный объект Helpdesk
  window.Helpdesk = {
    config: {},
    state: { isOpen: false, isOnline: false, user: null, messages: [] },
    elements: {},
    
    init: function(config) {
      this.config = this.mergeConfig(config);
      this.loadStyles();
      this.createButton();
      this.createWidget();
      this.loadScript(this.config.url + '/api/status.php', this.onStatusLoaded.bind(this));
      if (this.config.autoOpen) this.open();
      return this;
    },
    
    mergeConfig: function(config) {
      var merged = JSON.parse(JSON.stringify(defaultConfig));
      if (config) for (var key in config) if (config.hasOwnProperty(key)) merged[key] = config[key];
      return merged;
    },
    
    loadStyles: function() {
      var css = this.getStyles(this.config.theme);
      var styleEl = document.createElement('style');
      styleEl.textContent = css;
      document.head.appendChild(styleEl);
    },
    
    getStyles: function(theme) {
      var colors = theme === 'dark' ? {
        primary: '#3498db', secondary: '#2c3e50', background: '#1a1a1a',
        text: '#ecf0f1', textSecondary: '#bdc3c7', border: '#34495e', button: '#3498db'
      } : {
        primary: '#3498db', secondary: '#2c3e50', background: '#ffffff',
        text: '#2c3e50', textSecondary: '#7f8c8d', border: '#ecf0f1', button: '#3498db'
      };
      
      return `
        .helpdesk-widget-container {
          position: fixed; z-index: ${this.config.zIndex};
          ${this.config.position}: ${this.config.buttonSize}; bottom: ${this.config.buttonSize};
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        .helpdesk-button {
          width: ${this.config.buttonSize}; height: ${this.config.buttonSize};
          border-radius: 50%; background-color: ${colors.button}; border: none;
          cursor: pointer; box-shadow: 0 4px 12px rgba(0,0,0,0.3);
          transition: all 0.3s ease; display: flex; align-items: center; justify-content: center; position: relative;
        }
        .helpdesk-button:hover { transform: scale(1.1); box-shadow: 0 6px 16px rgba(0,0,0,0.4); }
        .helpdesk-button svg { width: 24px; height: 24px; fill: white; }
        .helpdesk-badge {
          position: absolute; top: 0; right: 0; width: 20px; height: 20px;
          border-radius: 50%; background-color: #e74c3c; color: white;
          font-size: 12px; font-weight: bold; display: flex; align-items: center; justify-content: center;
        }
        .helpdesk-widget {
          position: fixed; ${this.config.position}: ${this.config.position === 'right' ? '0' : '50%'};
          bottom: ${this.config.buttonSize}; width: ${this.config.widgetWidth}; height: ${this.config.widgetHeight};
          background-color: ${colors.background}; border-radius: 12px;
          box-shadow: 0 8px 32px rgba(0,0,0,0.3); overflow: hidden;
          transition: all 0.3s ease; transform: translateX(${this.config.position === 'right' ? '120%' : '-120%'});
        }
        .helpdesk-widget.active { transform: translateX(${this.config.position === 'right' ? '0' : '50%'}); }
        .helpdesk-header { background-color: ${colors.secondary}; color: white; padding: 16px; display: flex; align-items: center; justify-content: space-between; }
        .helpdesk-header-title { font-size: 16px; font-weight: 600; }
        .helpdesk-header-status { font-size: 12px; display: flex; align-items: center; gap: 6px; }
        .helpdesk-status-dot { width: 8px; height: 8px; border-radius: 50%; background-color: #27ae60; }
        .helpdesk-status-dot.offline { background-color: #95a5a6; }
        .helpdesk-close-btn { background: none; border: none; color: white; cursor: pointer; font-size: 20px; line-height: 1; }
        .helpdesk-messages { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 12px; }
        .helpdesk-message { max-width: 80%; padding: 12px 16px; border-radius: 12px; font-size: 14px; line-height: 1.5; }
        .helpdesk-message.user { align-self: flex-end; background-color: ${colors.primary}; color: white; border-bottom-right-radius: 4px; }
        .helpdesk-message.operator { align-self: flex-start; background-color: ${colors.border}; color: ${colors.text}; border-bottom-left-radius: 4px; }
        .helpdesk-message.system { align-self: center; background-color: transparent; color: ${colors.textSecondary}; font-size: 12px; font-style: italic; }
        .helpdesk-message-time { display: block; font-size: 10px; margin-top: 4px; opacity: 0.7; }
        .helpdesk-input-area { padding: 16px; border-top: 1px solid ${colors.border}; display: flex; gap: 10px; background-color: ${colors.background}; }
        .helpdesk-input { flex: 1; padding: 10px 14px; border: 1px solid ${colors.border}; border-radius: 20px; background-color: ${colors.background}; color: ${colors.text}; font-size: 14px; outline: none; }
        .helpdesk-input:focus { border-color: ${colors.primary}; }
        .helpdesk-send-btn { width: 40px; height: 40px; border-radius: 50%; background-color: ${colors.primary}; border: none; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: background-color 0.3s ease; }
        .helpdesk-send-btn:hover { background-color: ${colors.primary}; }
        .helpdesk-send-btn svg { width: 18px; height: 18px; fill: white; }
        .helpdesk-ticket-form { display: none; padding: 16px; }
        .helpdesk-ticket-form.active { display: block; }
        .helpdesk-form-group { margin-bottom: 12px; }
        .helpdesk-form-label { display: block; margin-bottom: 4px; font-size: 12px; color: ${colors.textSecondary}; }
        .helpdesk-form-input, .helpdesk-form-textarea { width: 100%; padding: 10px 14px; border: 1px solid ${colors.border}; border-radius: 8px; background-color: ${colors.background}; color: ${colors.text}; font-size: 14px; outline: none; }
        .helpdesk-form-textarea { min-height: 80px; resize: vertical; }
        .helpdesk-form-btn { width: 100%; padding: 12px; background-color: ${colors.primary}; color: white; border: none; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; transition: background-color 0.3s ease; }
        .helpdesk-form-btn:hover { background-color: ${colors.primary}; }
        .helpdesk-toggle-form { display: none; padding: 16px; text-align: center; }
        .helpdesk-toggle-form.active { display: block; }
        .helpdesk-toggle-btn { background: none; border: none; color: ${colors.primary}; cursor: pointer; font-size: 14px; text-decoration: underline; }
        @media (max-width: 480px) {
          .helpdesk-widget-container { ${this.config.mobile.position}: 0; bottom: 0; }
          .helpdesk-widget { width: ${this.config.mobile.widgetWidth}; height: 100vh; border-radius: 0; }
          .helpdesk-button { width: ${this.config.buttonSize}; height: ${this.config.buttonSize}; }
        }
      `;
    },
    
    createButton: function() {
      var container = document.createElement('div');
      container.className = 'helpdesk-widget-container';
      var button = document.createElement('button');
      button.className = 'helpdesk-button';
      button.innerHTML = '<svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-2 12H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z"/></svg>';
      if (this.config.showBadge) {
        var badge = document.createElement('div');
        badge.className = 'helpdesk-badge'; badge.textContent = '0';
        button.appendChild(badge); this.elements.badge = badge;
      }
      button.onclick = this.toggle.bind(this);
      container.appendChild(button); this.elements.button = button;
      document.body.appendChild(container);
    },
    
    createWidget: function() {
      var widget = document.createElement('div');
      widget.className = 'helpdesk-widget';
      widget.innerHTML = '<div class="helpdesk-header"><div class="helpdesk-header-title"><span>🤖 AI Helpdesk</span><span class="helpdesk-header-status"><span class="helpdesk-status-dot" id="hd-status-dot"></span><span id="hd-status-text">' + this.config.offlineText + '</span></span></div><button class="helpdesk-close-btn" onclick="Helpdesk.close()">&times;</button></div><div class="helpdesk-messages" id="hd-messages"><div class="helpdesk-message system">' + this.config.welcomeMessage + '<span class="helpdesk-message-time">Сейчас</span></div></div><div class="helpdesk-toggle-form" id="hd-toggle-form"><button class="helpdesk-toggle-btn" onclick="Helpdesk.showTicketForm()">Создать тикет</button></div><div class="helpdesk-ticket-form" id="hd-ticket-form"><div class="helpdesk-form-group"><label class="helpdesk-form-label">Тема</label><input type="text" class="helpdesk-form-input" id="hd-ticket-subject" placeholder="Кратко опишите проблему"></div><div class="helpdesk-form-group"><label class="helpdesk-form-label">Сообщение</label><textarea class="helpdesk-form-textarea" id="hd-ticket-message" placeholder="Подробно опишите вашу проблему"></textarea></div><button class="helpdesk-form-btn" onclick="Helpdesk.submitTicket()">Отправить</button><button class="helpdesk-form-btn" style="background-color: #95a5a6; margin-top: 8px;" onclick="Helpdesk.hideTicketForm()">Отмена</button></div><div class="helpdesk-input-area" id="hd-input-area"><input type="text" class="helpdesk-input" id="hd-input" placeholder="Напишите сообщение..." onkeypress="if(event.key === \'Enter\') Helpdesk.sendMessage()"><button class="helpdesk-send-btn" onclick="Helpdesk.sendMessage()"><svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg></button></div>';
      document.body.appendChild(widget);
      this.elements.widget = widget;
      this.elements.messages = widget.querySelector('#hd-messages');
      this.elements.input = widget.querySelector('#hd-input');
      this.elements.statusDot = widget.querySelector('#hd-status-dot');
      this.elements.statusText = widget.querySelector('#hd-status-text');
      this.elements.toggleForm = widget.querySelector('#hd-toggle-form');
      this.elements.ticketForm = widget.querySelector('#hd-ticket-form');
      this.elements.inputArea = widget.querySelector('#hd-input-area');
    },
    
    open: function() { this.state.isOpen = true; this.elements.widget.classList.add('active'); this.elements.button.classList.add('active'); this.hideTicketForm(); },
    close: function() { this.state.isOpen = false; this.elements.widget.classList.remove('active'); this.elements.button.classList.remove('active'); },
    toggle: function() { this.state.isOpen ? this.close() : this.open(); },
    
    setStatus: function(online) {
      this.state.isOnline = online;
      if (online) { this.elements.statusDot.classList.remove('offline'); this.elements.statusText.textContent = this.config.onlineText; }
      else { this.elements.statusDot.classList.add('offline'); this.elements.statusText.textContent = this.config.offlineText; }
    },
    
    addMessage: function(text, type) {
      var message = document.createElement('div');
      message.className = 'helpdesk-message ' + type;
      var time = new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
      message.innerHTML = this.escapeHtml(text) + '<span class="helpdesk-message-time">' + time + '</span>';
      this.elements.messages.appendChild(message);
      this.elements.messages.scrollTop = this.elements.messages.scrollHeight;
      this.state.messages.push({ text: text, type: type, time: time });
    },
    
    sendMessage: function() {
      var text = this.elements.input.value.trim();
      if (!text) return;
      this.addMessage(text, 'user');
      this.elements.input.value = '';
      this.loadScript(this.config.url + '/api/messages.php?ticket_id=' + this.getTicketId(), function(response) { console.log('Message sent:', response); }, 'POST', JSON.stringify({ content: text }));
    },
    
    showTicketForm: function() { this.elements.toggleForm.classList.remove('active'); this.elements.ticketForm.classList.add('active'); this.elements.inputArea.style.display = 'none'; },
    hideTicketForm: function() { this.elements.ticketForm.classList.remove('active'); this.elements.toggleForm.classList.add('active'); this.elements.inputArea.style.display = 'flex'; },
    
    submitTicket: function() {
      var subject = document.getElementById('hd-ticket-subject').value.trim();
      var message = document.getElementById('hd-ticket-message').value.trim();
      if (!subject || !message) {
        if (window.showToast) window.showToast('Пожалуйста, заполните все поля', 'warning');
        else alert('Пожалуйста, заполните все поля');
        return;
      }
      this.loadScript(this.config.url + '/api/tickets.php', function(response) {
        if (response.status === 'success') {
          if (window.showToast) window.showToast('Тикет создан! Мы свяжемся с вами в ближайшее время.', 'success');
          else alert('Тикет создан! Мы свяжемся с вами в ближайшее время.');
          this.hideTicketForm(); this.elements.inputArea.style.display = 'flex';
          document.getElementById('hd-ticket-subject').value = ''; document.getElementById('hd-ticket-message').value = '';
        } else {
          var errMsg = 'Ошибка при создании тикета: ' + (response.message || 'Неизвестная ошибка');
          if (window.showToast) window.showToast(errMsg, 'danger');
          else alert(errMsg);
        }
      }.bind(this), 'POST', JSON.stringify({ subject: subject, message: message, category: 'general', priority: 'normal' }));
    },
    
    loadScript: function(url, callback, method, data) {
      var xhr = new XMLHttpRequest(); method = method || 'GET';
      xhr.open(method, url, true); xhr.setRequestHeader('Content-Type', 'application/json');
      xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) try { callback(JSON.parse(xhr.responseText)); } catch(e) { console.error('Helpdesk: Error parsing response', e); callback({ error: xhr.responseText }); }
      };
      if (method === 'POST' && data) xhr.send(data); else xhr.send();
    },
    
    getTicketId: function() { return 'temp_' + Date.now(); },
    escapeHtml: function(text) { var div = document.createElement('div'); div.textContent = text; return div.innerHTML; },
    setUser: function(user) { this.state.user = user; console.log('Helpdesk: User set', user); },
    onStatusLoaded: function(response) { if (response.status === 'success') this.setStatus(response.online); }
  };
  
  if (window.HelpdeskConfig) window.Helpdesk.init(window.HelpdeskConfig);
})(window, document);
