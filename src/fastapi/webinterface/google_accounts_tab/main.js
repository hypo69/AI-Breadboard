// Google Workspace Accounts Tab JavaScript Logic

function escapeHtml(text) {
  if (!text) return '';
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function showGAccountsNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.className = `alert alert-${type} position-fixed top-0 end-0 m-3 shadow-lg`;
  notification.style.zIndex = '9999';
  notification.style.maxWidth = '400px';
  notification.innerHTML = message;
  document.body.appendChild(notification);
  
  setTimeout(() => {
    notification.remove();
  }, 4000);
}

async function refreshTabGoogleAccountsList() {
  const container = document.getElementById('tab-gaccounts-list-body');
  if (!container) return;

  try {
    container.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-muted"><span class="spinner-border spinner-border-sm me-2 text-primary"></span>Загрузка аккаунтов...</td></tr>';
    const data = await window.api.googleAccounts.list();
    const accounts = data.accounts || [];

    // Update stats
    const totalEl = document.getElementById('gstat-total-accounts');
    const activeEl = document.getElementById('gstat-active-accounts');
    const oauthEl = document.getElementById('gstat-oauth-accounts');
    const saEl = document.getElementById('gstat-sa-accounts');
    const countBadge = document.getElementById('tab-gaccounts-count-badge');

    if (totalEl) totalEl.textContent = accounts.length;
    if (activeEl) activeEl.textContent = accounts.filter(a => a.status === 'active').length;
    if (oauthEl) oauthEl.textContent = accounts.filter(a => a.type === 'oauth2').length;
    if (saEl) saEl.textContent = accounts.filter(a => a.type === 'service_account').length;
    if (countBadge) countBadge.textContent = `${accounts.length} акк.`;

    if (accounts.length === 0) {
      container.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-muted">Список аккаунтов пуст. Загрузите credentials.json или service_account.json.</td></tr>';
      return;
    }

    container.innerHTML = '';
    accounts.forEach(acc => {
      const row = document.createElement('tr');

      // 1. Account Name + Default Badge + Email
      const tdName = document.createElement('td');
      tdName.innerHTML = `
        <div class="d-flex align-items-center gap-2">
          <strong class="text-white">${escapeHtml(acc.name)}</strong>
          ${acc.is_default ? '<span class="badge bg-warning text-dark"><i class="bi bi-star-fill"></i> Default</span>' : ''}
        </div>
        ${acc.email ? `<div class="small text-muted font-monospace">${escapeHtml(acc.email)}</div>` : ''}
      `;
      row.appendChild(tdName);

      // 2. Type
      const tdType = document.createElement('td');
      tdType.className = 'text-center';
      const isOAuth = acc.type === 'oauth2';
      tdType.innerHTML = isOAuth
        ? '<span class="badge bg-primary-subtle text-primary border border-primary-subtle"><i class="bi bi-person me-1"></i>OAuth 2.0</span>'
        : '<span class="badge bg-info-subtle text-info border border-info-subtle"><i class="bi bi-cpu me-1"></i>Service Account</span>';
      row.appendChild(tdType);

      // 3. Status / Quota
      const tdStatus = document.createElement('td');
      tdStatus.className = 'text-center';
      const isActive = acc.status === 'active';
      if (isActive) {
        tdStatus.innerHTML = '<span class="badge bg-success">Активен</span>';
      } else if (acc.status === 'exhausted') {
        tdStatus.innerHTML = '<span class="badge bg-danger" title="Исчерпан суточный лимит квоты">Лимит</span>';
      } else {
        tdStatus.innerHTML = `<span class="badge bg-secondary">${escapeHtml(acc.status)}</span>`;
      }
      row.appendChild(tdStatus);

      // 4. Token / Credentials Status
      const tdToken = document.createElement('td');
      tdToken.className = 'text-center';
      if (acc.has_token || acc.type === 'service_account') {
        tdToken.innerHTML = '<span class="badge bg-success-subtle text-success border border-success-subtle"><i class="bi bi-shield-check me-1"></i>Готов</span>';
      } else {
        tdToken.innerHTML = '<span class="badge bg-warning-subtle text-warning border border-warning-subtle"><i class="bi bi-key me-1"></i>Нужен токен</span>';
      }
      row.appendChild(tdToken);

      // 5. Actions
      const tdActions = document.createElement('td');
      tdActions.className = 'text-center';

      // Set Default button
      if (!acc.is_default) {
        const btnDefault = document.createElement('button');
        btnDefault.className = 'btn btn-xs btn-outline-warning btn-sm me-1';
        btnDefault.title = 'Сделать аккаунтом по умолчанию';
        btnDefault.innerHTML = '<i class="bi bi-star"></i>';
        btnDefault.onclick = () => setTabGoogleAccountDefault(acc.name);
        tdActions.appendChild(btnDefault);
      }

      // Reset status button
      if (acc.status === 'exhausted') {
        const btnReset = document.createElement('button');
        btnReset.className = 'btn btn-xs btn-outline-info btn-sm me-1';
        btnReset.title = 'Сбросить статус исчерпания';
        btnReset.innerHTML = '<i class="bi bi-arrow-repeat"></i>';
        btnReset.onclick = () => resetTabGoogleAccountStatus(acc.name);
        tdActions.appendChild(btnReset);
      }

      // Test button
      const btnTest = document.createElement('button');
      btnTest.className = 'btn btn-xs btn-outline-info btn-sm me-1';
      btnTest.title = 'Проверить доступ и авторизацию';
      btnTest.innerHTML = '<i class="bi bi-play-circle"></i> Тест';
      btnTest.onclick = () => testTabGoogleAccount(acc.name);
      tdActions.appendChild(btnTest);

      // Delete button
      const btnDelete = document.createElement('button');
      btnDelete.className = 'btn btn-xs btn-outline-danger btn-sm';
      btnDelete.title = 'Удалить аккаунт из пула';
      btnDelete.innerHTML = '<i class="bi bi-trash"></i>';
      btnDelete.onclick = () => deleteTabGoogleAccount(acc.name);
      tdActions.appendChild(btnDelete);

      row.appendChild(tdActions);
      container.appendChild(row);
    });

  } catch (err) {
    console.error('Ошибка загрузки аккаунтов Google Workspace:', err);
    container.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-danger">Ошибка: ${escapeHtml(err.message)}</td></tr>`;
  }
}

async function handleAddTabGoogleAccount() {
  const nameInput = document.getElementById('tab-new-gacc-name');
  const typeSelect = document.getElementById('tab-new-gacc-type');
  const emailInput = document.getElementById('tab-new-gacc-email');
  const fileInput = document.getElementById('tab-new-gacc-file');
  const jsonTextarea = document.getElementById('tab-new-gacc-json');
  const defaultCheckbox = document.getElementById('tab-new-gacc-default');
  const addBtn = document.getElementById('tab-btn-add-gacc');

  if (!nameInput || !addBtn) return;

  const accountName = nameInput.value.trim();
  const accountType = typeSelect ? typeSelect.value : 'oauth2';
  const email = emailInput ? emailInput.value.trim() : '';
  const setAsDefault = defaultCheckbox ? defaultCheckbox.checked : false;

  if (!accountName) {
    showGAccountsNotification('Введите имя аккаунта (например: work, personal)', 'warning');
    nameInput.focus();
    return;
  }

  const file = fileInput && fileInput.files && fileInput.files[0];
  const jsonContent = jsonTextarea ? jsonTextarea.value.trim() : '';

  if (!file && !jsonContent) {
    showGAccountsNotification('Загрузите файл credentials.json / service_account.json или вставьте JSON', 'warning');
    return;
  }

  addBtn.disabled = true;
  const originalText = addBtn.innerHTML;
  addBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Сохранение...';

  try {
    if (file) {
      const formData = new FormData();
      formData.append('account_name', accountName);
      formData.append('account_type', accountType);
      if (email) formData.append('email', email);
      formData.append('set_as_default', setAsDefault ? 'true' : 'false');
      formData.append('file', file);

      await window.api.googleAccounts.upload(formData);
    } else {
      let parsedJson = null;
      try {
        parsedJson = JSON.parse(jsonContent);
      } catch (e) {
        throw new Error('Некорректный JSON в поле учетных данных');
      }

      await window.api.googleAccounts.create({
        account_name: accountName,
        account_type: accountType,
        email: email || undefined,
        credentials_dict: parsedJson,
        set_as_default: setAsDefault
      });
    }

    showGAccountsNotification(`Аккаунт Google "${accountName}" успешно сохранен в пул`, 'success');
    nameInput.value = '';
    if (emailInput) emailInput.value = '';
    if (fileInput) fileInput.value = '';
    if (jsonTextarea) jsonTextarea.value = '';
    if (defaultCheckbox) defaultCheckbox.checked = false;

    await refreshTabGoogleAccountsList();
  } catch (err) {
    console.error('Ошибка сохранения аккаунта Google:', err);
    showGAccountsNotification('Ошибка сохранения: ' + err.message, 'danger');
  } finally {
    addBtn.disabled = false;
    addBtn.innerHTML = originalText;
  }
}

async function setTabGoogleAccountDefault(name) {
  try {
    await window.api.googleAccounts.setDefault(name);
    showGAccountsNotification(`Аккаунт "${name}" назначен по умолчанию`, 'success');
    await refreshTabGoogleAccountsList();
  } catch (err) {
    console.error('Ошибка установки аккаунта по умолчанию:', err);
    showGAccountsNotification('Ошибка: ' + err.message, 'danger');
  }
}

async function resetTabGoogleAccountStatus(name) {
  try {
    await window.api.googleAccounts.resetStatus(name);
    showGAccountsNotification(`Статус аккаунта "${name}" сброшен в активный`, 'success');
    await refreshTabGoogleAccountsList();
  } catch (err) {
    console.error('Ошибка сброса статуса аккаунта:', err);
    showGAccountsNotification('Ошибка сброса: ' + err.message, 'danger');
  }
}

async function testTabGoogleAccount(name) {
  const testCard = document.getElementById('tab-gaccount-test-card');
  const testBody = document.getElementById('tab-gaccount-test-body');

  if (testCard && testBody) {
    testCard.style.display = 'block';
    testBody.innerHTML = `<span class="spinner-border spinner-border-sm me-2 text-info"></span>Проверка аутентификации для аккаунта <strong>${escapeHtml(name)}</strong>...`;
  }

  try {
    const res = await window.api.googleAccounts.test(name);
    if (testBody) {
      const isSuccess = res.status === 'success';
      const isWarning = res.status === 'warning';
      const badgeClass = isSuccess ? 'bg-success' : isWarning ? 'bg-warning text-dark' : 'bg-danger';
      
      testBody.innerHTML = `
        <div class="mb-2 d-flex align-items-center gap-2">
          <span class="badge ${badgeClass}">${res.status.toUpperCase()}</span>
          <strong class="text-white">${escapeHtml(name)}</strong>
        </div>
        <div class="mb-1 text-light">${escapeHtml(res.message || '')}</div>
        ${res.scopes && res.scopes.length > 0 ? `<div class="text-muted mt-2"><strong>Доступные Scopes:</strong><br>${res.scopes.map(s => '• ' + escapeHtml(s)).join('<br>')}</div>` : ''}
      `;
    }
  } catch (err) {
    if (testBody) {
      testBody.innerHTML = `<span class="text-danger"><i class="bi bi-x-circle me-1"></i>Ошибка проверки: ${escapeHtml(err.message)}</span>`;
    }
  }
}

async function deleteTabGoogleAccount(name) {
  if (!confirm(`Вы уверены, что хотите удалить аккаунт "${name}" из пула Google Workspace?`)) return;
  try {
    await window.api.googleAccounts.delete(name);
    showGAccountsNotification(`Аккаунт "${name}" успешно удален`, 'success');
    await refreshTabGoogleAccountsList();
  } catch (err) {
    console.error('Ошибка удаления аккаунта Google:', err);
    showGAccountsNotification('Ошибка удаления: ' + err.message, 'danger');
  }
}

async function initGoogleAccountsTab() {
  const refreshBtn = document.getElementById('tab-btn-refresh-gaccounts');
  const addBtn = document.getElementById('tab-btn-add-gacc');

  if (refreshBtn) {
    refreshBtn.onclick = async () => {
      refreshBtn.disabled = true;
      const orig = refreshBtn.innerHTML;
      refreshBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Обновление...';
      try {
        await refreshTabGoogleAccountsList();
        showGAccountsNotification('Список Google аккаунтов обновлен', 'success');
      } finally {
        refreshBtn.disabled = false;
        refreshBtn.innerHTML = orig;
      }
    };
  }

  if (addBtn) {
    addBtn.onclick = handleAddTabGoogleAccount;
  }

  await refreshTabGoogleAccountsList();
}

window.initGoogleAccountsTab = initGoogleAccountsTab;
window.refreshTabGoogleAccountsList = refreshTabGoogleAccountsList;
