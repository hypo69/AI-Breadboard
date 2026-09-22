// Windows Users Tab Module
// =============================================================================

export async function initWindowsUsersTab() {
  console.log('[WindowsUsersTab] Initializing...');
  
  try {
    // Load Windows users
    const usersContainer = document.getElementById('windows-users-list');
    const groupsContainer = document.getElementById('windows-groups-list');
    
    if (usersContainer) {
      usersContainer.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';
    }
    
    if (groupsContainer) {
      groupsContainer.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';
    }
    
    // Fetch Windows users
    try {
      const response = await fetch('/api/windows-users');
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'ok' && data.users) {
          if (usersContainer) {
            usersContainer.innerHTML = `
              <div class="table-responsive">
                <table class="table table-dark table-sm table-bordered">
                  <thead>
                    <tr>
                      <th>Имя</th>
                      <th>Enabled</th>
                      <th>Описание</th>
                      <th>SID</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${data.users.map(u => `
                      <tr>
                        <td><strong>${escapeHtml(u.Name || '')}</strong></td>
                        <td>${u.Enabled ? '<span class="badge bg-success">Да</span>' : '<span class="badge bg-danger">Нет</span>'}</td>
                        <td>${escapeHtml(u.Description || '')}</td>
                        <td class="text-muted small">${escapeHtml(u.SID || '')}</td>
                      </tr>
                    `).join('')}
                  </tbody>
                </table>
              </div>
            `;
          }
        }
      }
    } catch (err) {
      console.error('[WindowsUsersTab] Error loading users:', err);
      if (usersContainer) {
        usersContainer.innerHTML = `<div class="alert alert-danger">Ошибка загрузки: ${escapeHtml(err.message)}</div>`;
      }
    }
    
    // Fetch Windows groups
    try {
      const response = await fetch('/api/windows-users/groups');
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'ok' && data.groups) {
          if (groupsContainer) {
            groupsContainer.innerHTML = `
              <div class="table-responsive">
                <table class="table table-dark table-sm table-bordered">
                  <thead>
                    <tr>
                      <th>Группа</th>
                      <th>SID</th>
                      <th>Описание</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${data.groups.map(g => `
                      <tr>
                        <td><strong>${escapeHtml(g.Name || '')}</strong></td>
                        <td class="text-muted small">${escapeHtml(g.SID || '')}</td>
                        <td>${escapeHtml(g.Description || '')}</td>
                      </tr>
                    `).join('')}
                  </tbody>
                </table>
              </div>
            `;
          }
        }
      }
    } catch (err) {
      console.error('[WindowsUsersTab] Error loading groups:', err);
      if (groupsContainer) {
        groupsContainer.innerHTML = `<div class="alert alert-danger">Ошибка загрузки групп: ${escapeHtml(err.message)}</div>`;
      }
    }
    
  } catch (err) {
    console.error('[WindowsUsersTab] Initialization error:', err);
  }
}

function escapeHtml(text) {
  if (!text) return '';
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}