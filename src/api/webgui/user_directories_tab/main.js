/**
 * user_directories_tab/main.js — Модуль управления пользовательскими директориями и хранилищем
 * AI Breadboard
 */

let state = {
  users: [],
  selectedUserId: null,
  selectedUserName: '',
  currentSubfolder: '',
  searchQuery: '',
  extFilter: '',
  files: [],
  previewFile: null,
  orphanedDirs: [],
};

/**
 * Инициализация вкладки пользовательских директорий
 */
export async function initUserDirectoriesTab() {
  const root = document.getElementById('user-directories-tab-root');
  if (!root) return;

  setupEventListeners();
  await refreshData();
}

/**
 * Настройка обработчиков событий элементов управления
 */
function setupEventListeners() {
  // Кнопка обновления
  const refreshBtn = document.getElementById('btn-refresh-user-dirs');
  if (refreshBtn) {
    refreshBtn.onclick = () => refreshData();
  }

  // Поиск с дебаунсом
  const searchInput = document.getElementById('user-dirs-search-input');
  const searchClear = document.getElementById('user-dirs-search-clear');
  if (searchInput) {
    let timeout = null;
    searchInput.oninput = () => {
      clearTimeout(timeout);
      state.searchQuery = searchInput.value.trim();
      if (searchClear) {
        searchClear.classList.toggle('d-none', !state.searchQuery);
      }
      timeout = setTimeout(() => {
        applyFilters();
      }, 300);
    };
  }

  if (searchClear && searchInput) {
    searchClear.onclick = () => {
      searchInput.value = '';
      state.searchQuery = '';
      searchClear.classList.add('d-none');
      applyFilters();
    };
  }

  // Фильтр по расширениям
  const extSelect = document.getElementById('user-dirs-ext-filter');
  if (extSelect) {
    extSelect.onchange = () => {
      state.extFilter = extSelect.value;
      if (state.selectedUserId) {
        loadUserFiles(state.selectedUserId);
      }
    };
  }

  // Фильтры подпапок
  const subfolderGroup = document.getElementById('subfolder-filter-group');
  if (subfolderGroup) {
    subfolderGroup.addEventListener('click', (e) => {
      const btn = e.target.closest('button[data-subfolder]');
      if (!btn) return;
      subfolderGroup.querySelectorAll('button').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.currentSubfolder = btn.dataset.subfolder || '';
      if (state.selectedUserId) {
        loadUserFiles(state.selectedUserId);
      }
    });
  }

  // Кнопки модального окна осиротевших каталогов
  const openOrphanedBtn = document.getElementById('btn-open-orphaned-dirs-modal');
  if (openOrphanedBtn) {
    openOrphanedBtn.onclick = () => openOrphanedModal();
  }

  const refreshOrphanedBtn = document.getElementById('btn-modal-refresh-orphaned');
  if (refreshOrphanedBtn) {
    refreshOrphanedBtn.onclick = () => loadOrphanedDirs();
  }

  const cleanAllOrphanedBtn = document.getElementById('btn-modal-clean-all-orphaned');
  if (cleanAllOrphanedBtn) {
    cleanAllOrphanedBtn.onclick = () => cleanOrphanedDirs();
  }

  // Кнопка удаления файла из предпросмотра
  const previewDeleteBtn = document.getElementById('btn-preview-delete-file');
  if (previewDeleteBtn) {
    previewDeleteBtn.onclick = () => {
      if (state.previewFile && state.selectedUserId) {
        deleteFile(state.selectedUserId, state.previewFile.relative_path);
      }
    };
  }
}

/**
 * Полное обновление данных: сводка и список пользователей
 */
async function refreshData() {
  await Promise.all([
    loadSummary(),
    loadUsersList(),
    loadOrphanedBadge(),
  ]);
}

/**
 * Загрузка сводной статистики хранилища
 */
async function loadSummary() {
  try {
    const res = await fetch('/api/admin/user-directories/summary');
    if (!res.ok) return;
    const data = await res.json();
    if (data.status === 'ok' && data.summary) {
      const s = data.summary;
      const elUsers = document.getElementById('metric-total-users');
      const elStorage = document.getElementById('metric-total-storage');
      const elFiles = document.getElementById('metric-total-files');
      const elOrphaned = document.getElementById('metric-orphaned-size');

      if (elUsers) elUsers.textContent = s.total_users || 0;
      if (elStorage) elStorage.textContent = s.total_storage_formatted || '0 B';
      if (elFiles) elFiles.textContent = s.total_files_count || 0;
      if (elOrphaned) elOrphaned.textContent = s.orphaned_formatted || '0 B';
    }
  } catch (err) {
    console.warn('Ошибка загрузки сводки хранилища:', err);
  }
}

/**
 * Загрузка бейджа осиротевших каталогов
 */
async function loadOrphanedBadge() {
  try {
    const res = await fetch('/api/admin/user-directories/orphaned');
    if (!res.ok) return;
    const data = await res.json();
    if (data.status === 'ok') {
      const badge = document.getElementById('badge-orphaned-count');
      if (badge) badge.textContent = data.total || 0;
    }
  } catch (err) {
    console.warn('Ошибка проверки осиротевших каталогов:', err);
  }
}

/**
 * Загрузка списка пользователей с метриками хранилища
 */
async function loadUsersList() {
  const usersListEl = document.getElementById('user-dirs-users-list');
  const countBadge = document.getElementById('users-badge-count');
  const statusLabel = document.getElementById('user-dirs-status-label');

  try {
    if (statusLabel) statusLabel.textContent = 'Обновление списка пользователей...';
    const res = await fetch('/api/admin/user-directories/users');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    state.users = data.users || [];
    if (countBadge) countBadge.textContent = state.users.length;
    if (statusLabel) statusLabel.textContent = `Загружено пользователей: ${state.users.length}`;

    renderUsersList();

    // Если уже был выбран пользователь — перезагрузим его файлы, иначе выберем первого
    if (state.selectedUserId && state.users.some(u => u.id === state.selectedUserId)) {
      selectUser(state.selectedUserId);
    } else if (state.users.length > 0) {
      selectUser(state.users[0].id);
    }
  } catch (err) {
    console.error('Ошибка загрузки пользователей:', err);
    if (usersListEl) {
      usersListEl.innerHTML = `
        <div class="text-center py-4 text-danger small">
          <i class="bi bi-exclamation-triangle fs-4 d-block mb-1"></i>
          Не удалось загрузить список пользователей: ${err.message}
        </div>
      `;
    }
  }
}

/**
 * Рендеринг списка пользователей в левой колонке
 */
function renderUsersList() {
  const usersListEl = document.getElementById('user-dirs-users-list');
  if (!usersListEl) return;

  const query = state.searchQuery.toLowerCase();
  const filteredUsers = state.users.filter(u => {
    if (!query) return true;
    return (
      (u.name && u.name.toLowerCase().includes(query)) ||
      (u.email && u.email.toLowerCase().includes(query)) ||
      String(u.id).includes(query)
    );
  });

  if (filteredUsers.length === 0) {
    usersListEl.innerHTML = `
      <div class="text-center py-4 text-muted small">
        Пользователи не найдены
      </div>
    `;
    return;
  }

  usersListEl.innerHTML = filteredUsers.map(u => {
    const isSelected = u.id === state.selectedUserId;
    const activeClass = isSelected ? 'active border-primary' : '';
    const roleBadge = u.is_admin
      ? '<span class="badge bg-warning text-dark me-1">admin</span>'
      : '<span class="badge bg-secondary me-1">user</span>';

    const diskWarning = u.quota_percent > 85 ? 'bg-danger' : u.quota_percent > 60 ? 'bg-warning' : 'bg-primary';

    return `
      <a href="javascript:void(0)" 
         class="list-group-item list-group-item-action p-2.5 user-select-item ${activeClass}" 
         data-user-id="${u.id}">
        <div class="d-flex w-100 justify-content-between align-items-center mb-1">
          <div class="d-flex align-items-center gap-1.5 text-truncate">
            <span class="badge bg-dark border text-info" style="font-size: 0.72rem;">#${u.id}</span>
            <strong class="text-truncate small ${isSelected ? 'text-white' : ''}">${escapeHtml(u.name)}</strong>
          </div>
          <div>${roleBadge}</div>
        </div>
        <div class="text-truncate small text-muted mb-1.5" style="font-size: 0.76rem;">
          ${escapeHtml(u.email || '-')}
        </div>
        <div class="d-flex justify-content-between align-items-center small mb-1" style="font-size: 0.74rem;">
          <span class="text-muted"><i class="bi bi-files me-1"></i>${u.files_count} файлов</span>
          <span class="fw-semibold text-info">${u.size_formatted}</span>
        </div>
        <div class="progress" style="height: 4px;" title="Использовано квоты: ${u.quota_percent}%">
          <div class="progress-bar ${diskWarning}" role="progressbar" style="width: ${u.quota_percent}%;"></div>
        </div>
      </a>
    `;
  }).join('');

  // Обработчики клика по элементам пользователей
  usersListEl.querySelectorAll('.user-select-item').forEach(item => {
    item.onclick = () => {
      const uid = parseInt(item.dataset.userId, 10);
      selectUser(uid);
    };
  });
}

/**
 * Выбор пользователя и загрузка его файлового проводника
 */
function selectUser(userId) {
  state.selectedUserId = userId;
  const user = state.users.find(u => u.id === userId);
  state.selectedUserName = user ? user.name : `Пользователь #${userId}`;

  // Обновление подсветки в списке слева
  const usersListEl = document.getElementById('user-dirs-users-list');
  if (usersListEl) {
    usersListEl.querySelectorAll('.user-select-item').forEach(item => {
      const uid = parseInt(item.dataset.userId, 10);
      item.classList.toggle('active', uid === userId);
      item.classList.toggle('border-primary', uid === userId);
    });
  }

  // Обновление заголовка проводника
  const titleEl = document.getElementById('explorer-user-title');
  const pathBadge = document.getElementById('explorer-user-path-badge');
  if (titleEl) {
    titleEl.innerHTML = `<i class="bi bi-folder-fill text-warning me-1"></i> Хранилище: <strong>${escapeHtml(state.selectedUserName)}</strong> (#${userId})`;
  }
  if (pathBadge && user) {
    pathBadge.classList.remove('d-none');
    pathBadge.textContent = `data/users/${userId}/`;
  }

  loadUserFiles(userId);
}

/**
 * Загрузка файлов выбранного пользователя
 */
async function loadUserFiles(userId) {
  const tbody = document.getElementById('user-files-table-body');
  const footerStats = document.getElementById('explorer-footer-stats');
  const footerQuota = document.getElementById('explorer-footer-quota');

  if (tbody) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" class="text-center py-4 text-muted">
          <div class="spinner-border spinner-border-sm text-primary me-2"></div>
          Загрузка файлов пользователя...
        </td>
      </tr>
    `;
  }

  try {
    let url = `/api/admin/user-directories/users/${userId}/tree?`;
    const params = new URLSearchParams();
    if (state.currentSubfolder) params.append('subfolder', state.currentSubfolder);
    if (state.searchQuery) params.append('q', state.searchQuery);
    if (state.extFilter) params.append('extension', state.extFilter);

    const res = await fetch(url + params.toString());
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    state.files = data.items || [];

    if (footerStats) {
      footerStats.innerHTML = `Файлов: <strong>${data.total_items || 0}</strong> | Общий размер: <strong>${data.total_size_formatted || '0 B'}</strong>`;
    }

    const user = state.users.find(u => u.id === userId);
    if (footerQuota && user) {
      footerQuota.innerHTML = `Квота: <strong>${user.size_formatted} / ${user.quota_formatted}</strong> (${user.quota_percent}%)`;
    }

    renderUserFilesTable();
  } catch (err) {
    console.error('Ошибка загрузки файлов:', err);
    if (tbody) {
      tbody.innerHTML = `
        <tr>
          <td colspan="6" class="text-center py-4 text-danger small">
            Ошибка загрузки файлов: ${err.message}
          </td>
        </tr>
      `;
    }
  }
}

/**
 * Рендеринг таблицы файлов пользователя
 */
function renderUserFilesTable() {
  const tbody = document.getElementById('user-files-table-body');
  if (!tbody) return;

  if (state.files.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" class="text-center py-5 text-muted small">
          <i class="bi bi-inbox fs-3 d-block mb-1 text-secondary"></i>
          В выбранном разделе нет файлов
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = state.files.map(f => {
    const isDir = f.is_dir;
    const icon = isDir
      ? '<i class="bi bi-folder-fill text-warning fs-6"></i>'
      : getFileIcon(f.extension);

    const subfolderBadge = f.subfolder === 'root'
      ? '<span class="badge bg-secondary-subtle text-secondary border">root</span>'
      : `<span class="badge bg-info-subtle text-info border border-info-subtle">${escapeHtml(f.subfolder)}</span>`;

    return `
      <tr>
        <td class="text-center">${icon}</td>
        <td>
          <div class="fw-semibold text-truncate text-white" style="max-width: 260px;" title="${escapeHtml(f.relative_path)}">
            ${escapeHtml(f.name)}
          </div>
          <div class="text-muted small font-monospace" style="font-size: 0.72rem;">
            ${escapeHtml(f.relative_path)}
          </div>
        </td>
        <td class="text-center">${subfolderBadge}</td>
        <td class="text-center font-monospace small">${f.size_formatted}</td>
        <td class="small text-muted font-monospace" style="font-size: 0.76rem;">${f.modified_formatted}</td>
        <td class="text-center">
          <div class="btn-group btn-group-sm" role="group">
            ${!isDir ? `
              <button class="btn btn-xs btn-outline-info btn-preview-file" 
                      data-path="${escapeHtml(f.relative_path)}" 
                      title="Предпросмотр файла">
                <i class="bi bi-eye"></i>
              </button>
              <a href="/api/admin/user-directories/users/${state.selectedUserId}/file/download?path=${encodeURIComponent(f.relative_path)}" 
                 class="btn btn-xs btn-outline-success" 
                 title="Скачать файл" 
                 download>
                <i class="bi bi-download"></i>
              </a>
            ` : ''}
            <button class="btn btn-xs btn-outline-danger btn-delete-file" 
                    data-path="${escapeHtml(f.relative_path)}" 
                    data-is-dir="${isDir}"
                    title="Удалить">
              <i class="bi bi-trash3"></i>
            </button>
          </div>
        </td>
      </tr>
    `;
  }).join('');

  // Навешивание событий предпросмотра
  tbody.querySelectorAll('.btn-preview-file').forEach(btn => {
    btn.onclick = () => {
      const path = btn.dataset.path;
      openFilePreview(state.selectedUserId, path);
    };
  });

  // Навешивание событий удаления
  tbody.querySelectorAll('.btn-delete-file').forEach(btn => {
    btn.onclick = () => {
      const path = btn.dataset.path;
      const isDir = btn.dataset.isDir === 'true';
      const promptText = isDir
        ? `Вы уверены, что хотите удалить директорию "${path}" со всем содержимым?`
        : `Вы уверены, что хотите удалить файл "${path}"?`;
      if (confirm(promptText)) {
        deleteFile(state.selectedUserId, path);
      }
    };
  });
}

/**
 * Иконка по расширению файла
 */
function getFileIcon(ext) {
  const e = (ext || '').toLowerCase();
  switch (e) {
    case 'pdf':
      return '<i class="bi bi-file-earmark-pdf-fill text-danger fs-6"></i>';
    case 'txt':
    case 'md':
    case 'log':
      return '<i class="bi bi-file-earmark-text-fill text-info fs-6"></i>';
    case 'json':
    case 'xml':
    case 'yaml':
    case 'yml':
      return '<i class="bi bi-file-earmark-code-fill text-warning fs-6"></i>';
    case 'csv':
    case 'tsv':
    case 'xlsx':
      return '<i class="bi bi-file-earmark-spreadsheet-fill text-success fs-6"></i>';
    case 'png':
    case 'jpg':
    case 'jpeg':
    case 'webp':
    case 'gif':
    case 'svg':
      return '<i class="bi bi-file-earmark-image-fill text-primary fs-6"></i>';
    case 'mp3':
    case 'wav':
    case 'ogg':
      return '<i class="bi bi-file-earmark-music-fill text-purple fs-6"></i>';
    case 'py':
    case 'js':
    case 'sh':
    case 'ps1':
      return '<i class="bi bi-filetype-py text-warning fs-6"></i>';
    default:
      return '<i class="bi bi-file-earmark-fill text-secondary fs-6"></i>';
  }
}

/**
 * Открытие модального окна предпросмотра файла
 */
async function openFilePreview(userId, path) {
  const modalEl = document.getElementById('modal-file-preview');
  if (!modalEl) return;

  const titleEl = document.getElementById('modal-file-preview-title');
  const pathEl = document.getElementById('preview-file-path');
  const sizeEl = document.getElementById('preview-file-size');
  const typeEl = document.getElementById('preview-file-type');
  const contentWrapper = document.getElementById('preview-content-wrapper');
  const downloadLink = document.getElementById('btn-preview-download-file');

  if (titleEl) titleEl.textContent = `Предпросмотр: ${path.split('/').pop()}`;
  if (pathEl) pathEl.textContent = `data/users/${userId}/${path}`;
  if (sizeEl) sizeEl.textContent = '...';
  if (typeEl) typeEl.textContent = '...';
  if (contentWrapper) {
    contentWrapper.innerHTML = `
      <div class="text-center py-4 text-muted">
        <div class="spinner-border spinner-border-sm text-primary me-2"></div> Загрузка содержимого...
      </div>
    `;
  }
  if (downloadLink) {
    downloadLink.href = `/api/admin/user-directories/users/${userId}/file/download?path=${encodeURIComponent(path)}`;
  }

  const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
  modal.show();

  try {
    const res = await fetch(`/api/admin/user-directories/users/${userId}/file/preview?path=${encodeURIComponent(path)}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    state.previewFile = data;

    if (sizeEl) sizeEl.textContent = data.size_formatted;
    if (typeEl) typeEl.textContent = data.mime_type || data.extension;

    if (contentWrapper) {
      if (data.is_image) {
        contentWrapper.innerHTML = `
          <div class="text-center p-2">
            <img src="${data.content}" class="img-fluid rounded border border-secondary shadow" style="max-height: 400px; object-fit: contain;">
          </div>
        `;
      } else {
        contentWrapper.textContent = data.content || '(Файл пуст)';
      }
    }
  } catch (err) {
    console.error('Ошибка предпросмотра файла:', err);
    if (contentWrapper) {
      contentWrapper.innerHTML = `<div class="text-danger p-3">Ошибка загрузки содержимого: ${err.message}</div>`;
    }
  }
}

/**
 * Удаление файла или папки
 */
async function deleteFile(userId, path) {
  try {
    const res = await fetch(`/api/admin/user-directories/users/${userId}/file?path=${encodeURIComponent(path)}`, {
      method: 'DELETE',
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `HTTP ${res.status}`);
    }

    showAlert(`Файл "${path}" успешно удален`, 'success');

    // Закрываем модальное окно предпросмотра, если оно открыто
    const previewModalEl = document.getElementById('modal-file-preview');
    if (previewModalEl) {
      const modal = bootstrap.Modal.getInstance(previewModalEl);
      if (modal) modal.hide();
    }

    // Перезагружаем файлы и сводку
    await loadUserFiles(userId);
    await loadSummary();
    await loadUsersList();
  } catch (err) {
    console.error('Ошибка удаления файла:', err);
    showAlert(`Ошибка удаления файла: ${err.message}`, 'danger');
  }
}

/**
 * Открытие модального окна управления осиротевшими директориями
 */
async function openOrphanedModal() {
  const modalEl = document.getElementById('modal-orphaned-user-dirs');
  if (!modalEl) return;
  const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
  modal.show();
  await loadOrphanedDirs();
}

/**
 * Загрузка списка осиротевших директорий
 */
async function loadOrphanedDirs() {
  const tbody = document.getElementById('modal-orphaned-dirs-tbody');
  const countEl = document.getElementById('modal-orphaned-count');
  const sizeEl = document.getElementById('modal-orphaned-size');
  const filesEl = document.getElementById('modal-orphaned-files');

  if (tbody) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" class="text-center py-4 text-muted">
          <div class="spinner-border spinner-border-sm text-warning me-2"></div> Сканирование...
        </td>
      </tr>
    `;
  }

  try {
    const res = await fetch('/api/admin/user-directories/orphaned');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    state.orphanedDirs = data.orphaned_dirs || [];

    if (countEl) countEl.textContent = data.total || 0;
    if (sizeEl) sizeEl.textContent = data.total_size_formatted || '0 B';
    if (filesEl) filesEl.textContent = data.total_files || 0;

    const badge = document.getElementById('badge-orphaned-count');
    if (badge) badge.textContent = data.total || 0;

    renderOrphanedDirsTable();
  } catch (err) {
    console.error('Ошибка загрузки осиротевших директорий:', err);
    if (tbody) {
      tbody.innerHTML = `
        <tr>
          <td colspan="6" class="text-center py-3 text-danger small">
            Ошибка сканирования: ${err.message}
          </td>
        </tr>
      `;
    }
  }
}

/**
 * Рендеринг таблицы осиротевших каталогов
 */
function renderOrphanedDirsTable() {
  const tbody = document.getElementById('modal-orphaned-dirs-tbody');
  if (!tbody) return;

  if (state.orphanedDirs.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" class="text-center py-4 text-success small">
          <i class="bi bi-check-circle fs-4 d-block mb-1"></i>
          Осиротевших каталогов не обнаружено. Все директории привязаны к активным пользователям!
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = state.orphanedDirs.map(d => `
    <tr>
      <td>
        <div class="fw-bold font-monospace text-warning small">${escapeHtml(d.dir_name)}</div>
        <div class="text-muted small" style="font-size: 0.72rem;">${escapeHtml(d.full_path)}</div>
      </td>
      <td><span class="badge bg-secondary-subtle text-secondary border">${escapeHtml(d.reason)}</span></td>
      <td class="text-center font-monospace">${d.files_count}</td>
      <td class="text-center font-monospace small">${d.size_formatted}</td>
      <td class="small text-muted font-monospace" style="font-size: 0.76rem;">${d.modified_formatted}</td>
      <td class="text-center">
        <button class="btn btn-xs btn-outline-danger btn-clean-single-orphaned" 
                data-dir="${escapeHtml(d.dir_name)}" 
                title="Удалить этот каталог">
          <i class="bi bi-trash3"></i>
        </button>
      </td>
    </tr>
  `).join('');

  tbody.querySelectorAll('.btn-clean-single-orphaned').forEach(btn => {
    btn.onclick = () => {
      const dirName = btn.dataset.dir;
      if (confirm(`Удалить осиротевший каталог "${dirName}"?`)) {
        cleanOrphanedDirs([dirName]);
      }
    };
  });
}

/**
 * Очистка осиротевших каталогов (конкретных или всех)
 */
async function cleanOrphanedDirs(dirsList = null) {
  if (!dirsList && !confirm('Вы уверены, что хотите удалить ВСЕ осиротевшие каталоги пользователей? Это действие необратимо.')) {
    return;
  }

  try {
    const payload = dirsList ? { dirs: dirsList } : {};
    const res = await fetch('/api/admin/user-directories/orphaned/clean', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    showAlert(`Удалено каталогов: ${data.deleted_count}, освобождено места: ${data.freed_formatted}`, 'success');

    await loadOrphanedDirs();
    await loadSummary();
  } catch (err) {
    console.error('Ошибка очистки осиротевших каталогов:', err);
    showAlert(`Ошибка очистки каталогов: ${err.message}`, 'danger');
  }
}

/**
 * Применение клиентских фильтров поиска
 */
function applyFilters() {
  renderUsersList();
  if (state.selectedUserId) {
    loadUserFiles(state.selectedUserId);
  }
}

/**
 * Вывод сообщения alert
 */
function showAlert(message, type = 'info') {
  const alertBox = document.getElementById('user-dirs-alert-box');
  const alertMsg = document.getElementById('user-dirs-alert-message');
  if (!alertBox || !alertMsg) return;

  alertBox.className = `alert alert-${type} alert-dismissible fade show mb-3 shadow-sm`;
  alertMsg.textContent = message;
  alertBox.classList.remove('d-none');

  setTimeout(() => {
    alertBox.classList.add('d-none');
  }, 6000);
}

/**
 * Экранирование HTML
 */
function escapeHtml(text) {
  if (!text) return '';
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;',
  };
  return String(text).replace(/[&<>"']/g, m => map[m]);
}

// Экспорт по умолчанию
export default initUserDirectoriesTab;
