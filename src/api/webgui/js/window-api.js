/**
 * window-api.js — инициализация window.api для всех вкладок и панелей управления
 * Этот файл загружается ДО всех вкладок, чтобы window.api был доступен сразу
 */

window.api = window.api || {};

// Универсальный fetch для API и Auth
if (!window.api.fetch) {
  window.api.fetch = async function(url, opts = {}) {
    const response = await fetch(url, opts);
    if (!response.ok) {
      let msg = response.statusText;
      try {
        const data = await response.json();
        if (data && data.detail) {
          if (typeof data.detail === 'string') {
            msg = data.detail;
          } else if (Array.isArray(data.detail)) {
            msg = data.detail.map(d => d.msg || JSON.stringify(d)).join(', ');
          } else {
            msg = JSON.stringify(data.detail);
          }
        } else if (data && data.message) {
          msg = data.message;
        }
      } catch {}
      throw new Error(`${response.status} ${msg}`);
    }
    return response.json();
  };
}

// User management API
window.api.users = window.api.users || {
  async list(params = {}) {
    const q = new URLSearchParams(params).toString();
    return window.api.fetch(`/api/admin/users${q ? '?' + q : ''}`);
  },
  async get(userId) {
    return window.api.fetch(`/api/admin/users/${userId}`);
  },
  async create(data) {
    return window.api.fetch('/api/admin/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
  },
  async update(userId, data) {
    return window.api.fetch(`/api/admin/users/${userId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
  },
  async setPassword(userId, password) {
    return window.api.fetch(`/api/admin/users/${userId}/password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password })
    });
  },
  async toggleActive(userId) {
    return window.api.fetch(`/api/admin/users/${userId}/toggle-active`, {
      method: 'POST'
    });
  },
  async toggleRole(userId) {
    return window.api.fetch(`/api/admin/users/${userId}/toggle-role`, {
      method: 'POST'
    });
  },
  async delete(userId) {
    return window.api.fetch(`/api/admin/users/${userId}`, {
      method: 'DELETE'
    });
  }
};

// Skills management API
window.api.skills = window.api.skills || {
  async list(params = {}) {
    const q = new URLSearchParams(params).toString();
    return window.api.fetch(`/api/admin/skills${q ? '?' + q : ''}`);
  },
  async get(name) {
    return window.api.fetch(`/api/admin/skills/${encodeURIComponent(name)}`);
  },
  async create(data) {
    return window.api.fetch('/api/admin/skills', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
  },
  async update(name, data) {
    return window.api.fetch(`/api/admin/skills/${encodeURIComponent(name)}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
  },
  async delete(name) {
    return window.api.fetch(`/api/admin/skills/${encodeURIComponent(name)}`, {
      method: 'DELETE'
    });
  },
  async package(name) {
    return window.api.fetch(`/api/admin/skills/${encodeURIComponent(name)}/package`, {
      method: 'POST'
    });
  }
};

// MCP Servers management API
window.api.mcp = window.api.mcp || {
  async list() {
    return window.api.fetch('/api/admin/mcp/servers');
  },
  async get(id) {
    return window.api.fetch(`/api/admin/mcp/servers/${encodeURIComponent(id)}`);
  },
  async create(data) {
    return window.api.fetch('/api/admin/mcp/servers', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
  },
  async update(id, data) {
    return window.api.fetch(`/api/admin/mcp/servers/${encodeURIComponent(id)}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
  },
  async delete(id) {
    return window.api.fetch(`/api/admin/mcp/servers/${encodeURIComponent(id)}`, {
      method: 'DELETE'
    });
  },
  async toggle(id) {
    return window.api.fetch(`/api/admin/mcp/servers/${encodeURIComponent(id)}/toggle`, {
      method: 'POST'
    });
  },
  async test(id) {
    return window.api.fetch(`/api/admin/mcp/servers/${encodeURIComponent(id)}/test`, {
      method: 'POST'
    });
  },
  async testAdhoc(data) {
    return window.api.fetch('/api/admin/mcp/test', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
  },
  async getTools() {
    return window.api.fetch('/api/admin/mcp/tools');
  }
};

// Google Workspace Accounts API wrapper
window.api.googleAccounts = window.api.googleAccounts || {
  async list() {
    return await window.api.fetch('/api/admin/google-accounts');
  },
  async upload(formData) {
    const r = await fetch('/api/admin/google-accounts/upload', {
      method: 'POST',
      body: formData
    });
    if (!r.ok) {
      let msg = r.statusText;
      try { msg = (await r.json()).detail || msg; } catch {}
      throw new Error(`${r.status} ${msg}`);
    }
    return await r.json();
  },
  async create(params) {
    return await window.api.fetch('/api/admin/google-accounts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    });
  },
  async setDefault(name) {
    return await window.api.fetch(`/api/admin/google-accounts/${encodeURIComponent(name)}/default`, {
      method: 'POST'
    });
  },
  async resetStatus(name) {
    return await window.api.fetch(`/api/admin/google-accounts/${encodeURIComponent(name)}/reset-status`, {
      method: 'POST'
    });
  },
  async test(name) {
    return await window.api.fetch(`/api/admin/google-accounts/${encodeURIComponent(name)}/test`, {
      method: 'POST'
    });
  },
  async delete(name) {
    return await window.api.fetch(`/api/admin/google-accounts/${encodeURIComponent(name)}`, {
      method: 'DELETE'
    });
  }
};
