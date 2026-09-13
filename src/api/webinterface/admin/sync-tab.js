/**
 * Google Drive Sync Management Tab
 * Управление синхронизацией Google Drive через админ-панель
 */

class SyncTab {
  constructor() {
    this.initialized = false;
    this.messageTimeout = null;
  }

  /**
   * Инициализация вкладки
   */
  async init() {
    if (this.initialized) return;

    console.log('[SyncTab] Initializing...');
    
    // Загрузка HTML
    await this.loadHTML();
    
    // Установка обработчиков
    this.attachEventListeners();
    
    // Загрузка данных
    await this.updateStatus();
    await this.updateStats();
    
    // Установка автообновления
    setInterval(() => this.updateStatus(), 5000);
    setInterval(() => this.updateStats(), 30000);
    
    this.initialized = true;
    console.log('[SyncTab] Initialized');
  }

  /**
   * Загрузить HTML компонента
   */
  async loadHTML() {
    const container = document.getElementById('tab-sync');
    if (!container) {
      console.warn('[SyncTab] Container not found');
      return;
    }

    const html = `
      <div class="sync-panel">
        <!-- Заголовок -->
        <div class="mb-4">
          <h4 class="d-flex align-items-center gap-2">
            <i class="bi bi-cloud-upload-fill text-primary"></i>
            <span>Google Drive Synchronization</span>
          </h4>
          <p class="text-muted mb-0">Manage data synchronization and storage migration</p>
        </div>

        <!-- Статус -->
        <div class="card border-secondary-subtle mb-3">
          <div class="card-header bg-body-tertiary border-secondary-subtle">
            <h6 class="mb-0">📊 Synchronization Status</h6>
          </div>
          <div class="card-body">
            <div class="row g-3">
              <div class="col-md-3">
                <div class="ps-3 border-start border-primary-subtle">
                  <small class="text-muted">Scheduler</small>
                  <div>
                    <span id="scheduler-status" class="badge bg-danger">Inactive</span>
                  </div>
                </div>
              </div>
              <div class="col-md-3">
                <div class="ps-3 border-start border-primary-subtle">
                  <small class="text-muted">Last Sync</small>
                  <div id="last-sync-time" class="small">Never</div>
                </div>
              </div>
              <div class="col-md-3">
                <div class="ps-3 border-start border-primary-subtle">
                  <small class="text-muted">Interval</small>
                  <div id="sync-interval" class="small">6 hours</div>
                </div>
              </div>
              <div class="col-md-3">
                <div class="ps-3 border-start border-primary-subtle">
                  <small class="text-muted">Drive Folder</small>
                  <div>
                    <a id="drive-url" href="#" target="_blank" class="small text-decoration-none">
                      Open
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Статистика -->
        <div class="card border-secondary-subtle mb-3">
          <div class="card-header bg-body-tertiary border-secondary-subtle">
            <h6 class="mb-0">💾 Storage Statistics</h6>
          </div>
          <div class="card-body">
            <div class="row g-3">
              <div class="col-md-3 text-center">
                <div class="fs-5 fw-bold text-info" id="total-size">-</div>
                <small class="text-muted">Total Size</small>
              </div>
              <div class="col-md-3 text-center">
                <div class="fs-5 fw-bold text-success" id="files-count">-</div>
                <small class="text-muted">Files</small>
              </div>
              <div class="col-md-3 text-center">
                <div class="fs-5 fw-bold text-warning" id="folders-count">-</div>
                <small class="text-muted">Folders</small>
              </div>
              <div class="col-md-3 text-center">
                <div class="fs-5 fw-bold text-danger" id="sync-errors">0</div>
                <small class="text-muted">Errors</small>
              </div>
            </div>
          </div>
        </div>

        <!-- Управление -->
        <div class="card border-secondary-subtle mb-3">
          <div class="card-header bg-body-tertiary border-secondary-subtle">
            <h6 class="mb-0">🎮 Synchronization Controls</h6>
          </div>
          <div class="card-body">
            <div class="mb-3">
              <label class="form-label">Sync Interval (hours)</label>
              <div class="input-group mb-2">
                <input type="number" id="sync-interval-input" min="1" max="24" value="6" class="form-control">
                <button class="btn btn-outline-secondary" onclick="window.syncTab.updateInterval()">
                  Update
                </button>
              </div>
            </div>

            <div class="d-flex gap-2 flex-wrap">
              <button id="start-scheduler-btn" class="btn btn-success btn-sm" onclick="window.syncTab.startScheduler()">
                <i class="bi bi-play-fill"></i> Start Scheduler
              </button>
              <button id="stop-scheduler-btn" class="btn btn-danger btn-sm" disabled onclick="window.syncTab.stopScheduler()">
                <i class="bi bi-stop-fill"></i> Stop Scheduler
              </button>
              <button class="btn btn-primary btn-sm" onclick="window.syncTab.showSyncOptions()">
                <i class="bi bi-arrow-repeat"></i> Sync Now
              </button>
              <button class="btn btn-info btn-sm" onclick="window.syncTab.testConnection()">
                <i class="bi bi-link-45deg"></i> Test Connection
              </button>
            </div>
          </div>
        </div>

        <!-- Опции синхронизации -->
        <div id="sync-options-modal" class="modal fade" tabindex="-1">
          <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content bg-dark text-white border-secondary">
              <div class="modal-header border-secondary">
                <h5 class="modal-title">Select Data to Sync</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
              </div>
              <div class="modal-body">
                <div class="form-check mb-2">
                  <input class="form-check-input" type="radio" name="sync-type" value="all" id="sync-all" checked>
                  <label class="form-check-label" for="sync-all">
                    <strong>All Data</strong> - Everything (data, logs, secrets, configs)
                  </label>
                </div>
                <div class="form-check mb-2">
                  <input class="form-check-input" type="radio" name="sync-type" value="data" id="sync-data">
                  <label class="form-check-label" for="sync-data">
                    <strong>Data Only</strong> - Databases and RAG indices
                  </label>
                </div>
                <div class="form-check mb-2">
                  <input class="form-check-input" type="radio" name="sync-type" value="logs" id="sync-logs">
                  <label class="form-check-label" for="sync-logs">
                    <strong>Logs Only</strong> - Application logs
                  </label>
                </div>
                <div class="form-check mb-2">
                  <input class="form-check-input" type="radio" name="sync-type" value="secrets" id="sync-secrets">
                  <label class="form-check-label" for="sync-secrets">
                    <strong>Secrets Only</strong> - Configuration and keys
                  </label>
                </div>
              </div>
              <div class="modal-footer border-secondary">
                <button type="button" class="btn btn-secondary btn-sm" data-bs-dismiss="modal">
                  Cancel
                </button>
                <button type="button" class="btn btn-primary btn-sm" onclick="window.syncTab.performSync()">
                  Sync Selected
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Сообщения -->
        <div id="sync-messages" class="mb-3"></div>

        <!-- Лог активности -->
        <div class="card border-secondary-subtle">
          <div class="card-header bg-body-tertiary border-secondary-subtle">
            <h6 class="mb-0">📋 Recent Activity</h6>
          </div>
          <div class="card-body" style="max-height: 300px; overflow-y: auto;">
            <div id="activity-log">
              <p class="text-muted mb-0">No recent activity</p>
            </div>
          </div>
        </div>
      </div>
    `;

    container.innerHTML = html;
  }

  /**
   * Присоединить обработчики событий
   */
  attachEventListeners() {
    // Обработка модального окна
    const modal = new bootstrap.Modal(document.getElementById('sync-options-modal'), {
      backdrop: 'static'
    });

    window.syncTab = this; // Для доступа из HTML
  }

  /**
   * Обновить статус синхронизации
   */
  async updateStatus() {
    try {
      const response = await fetch('/api/admin/sync/status');
      if (!response.ok) throw new Error('Failed to fetch status');
      
      const data = await response.json();

      // Обновить статус
      const badge = document.getElementById('scheduler-status');
      badge.textContent = data.is_running ? 'Running' : 'Inactive';
      badge.className = data.is_running 
        ? 'badge bg-success' 
        : 'badge bg-danger';

      // Обновить кнопки
      document.getElementById('start-scheduler-btn').disabled = data.is_running;
      document.getElementById('stop-scheduler-btn').disabled = !data.is_running;

      // Обновить время
      document.getElementById('last-sync-time').textContent = data.last_sync_time || 'Never';
      document.getElementById('sync-interval').textContent = `${data.sync_interval_hours} hours`;

      // Обновить Google Drive папку
      try {
        const driveResponse = await fetch('/api/admin/sync/drive-info');
        if (driveResponse.ok) {
          const driveData = await driveResponse.json();
          const link = document.getElementById('drive-url');
          link.href = driveData.folder_url;
        }
      } catch (e) {
        console.warn('[SyncTab] Failed to fetch drive info');
      }
    } catch (error) {
      console.error('[SyncTab] Error updating status:', error);
    }
  }

  /**
   * Обновить статистику
   */
  async updateStats() {
    try {
      const response = await fetch('/api/admin/sync/stats');
      if (!response.ok) throw new Error('Failed to fetch stats');
      
      const data = await response.json();

      document.getElementById('total-size').textContent = 
        `${data.total_size_mb.toFixed(1)} MB`;
      document.getElementById('files-count').textContent = data.files_count;
      document.getElementById('folders-count').textContent = data.folders_count;
      document.getElementById('sync-errors').textContent = data.sync_errors;
    } catch (error) {
      console.error('[SyncTab] Error updating stats:', error);
    }
  }

  /**
   * Запустить планировщик
   */
  async startScheduler() {
    try {
      const interval = parseInt(document.getElementById('sync-interval-input').value);
      const response = await fetch('/api/admin/sync/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sync_interval_hours: interval })
      });
      
      const data = await response.json();
      this.showMessage(data.message || 'Scheduler started', 'success');
      await this.updateStatus();
    } catch (error) {
      this.showMessage('Error: ' + error.message, 'danger');
    }
  }

  /**
   * Остановить планировщик
   */
  async stopScheduler() {
    try {
      const response = await fetch('/api/admin/sync/stop', {
        method: 'POST'
      });
      
      const data = await response.json();
      this.showMessage(data.message || 'Scheduler stopped', 'success');
      await this.updateStatus();
    } catch (error) {
      this.showMessage('Error: ' + error.message, 'danger');
    }
  }

  /**
   * Проверить подключение
   */
  async testConnection() {
    try {
      const response = await fetch('/api/admin/sync/test-connection', {
        method: 'POST'
      });
      
      const data = await response.json();
      const type = data.connected ? 'success' : 'warning';
      this.showMessage(data.message || 'Connection test completed', type);
    } catch (error) {
      this.showMessage('Error: ' + error.message, 'danger');
    }
  }

  /**
   * Показать опции синхронизации
   */
  showSyncOptions() {
    const modal = bootstrap.Modal.getInstance(document.getElementById('sync-options-modal')) ||
      new bootstrap.Modal(document.getElementById('sync-options-modal'));
    modal.show();
  }

  /**
   * Выполнить синхронизацию
   */
  async performSync() {
    const syncType = document.querySelector('input[name="sync-type"]:checked')?.value || 'all';
    
    try {
      const response = await fetch('/api/admin/sync/sync-now', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sync_type: syncType })
      });
      
      const data = await response.json();
      this.showMessage(data.message || 'Sync started', 'success');
      this.addActivityLog(`Started ${syncType} synchronization`);
      
      // Скрыть модаль
      const modal = bootstrap.Modal.getInstance(document.getElementById('sync-options-modal'));
      if (modal) modal.hide();
    } catch (error) {
      this.showMessage('Error: ' + error.message, 'danger');
    }
  }

  /**
   * Обновить интервал
   */
  async updateInterval() {
    const interval = parseInt(document.getElementById('sync-interval-input').value);
    
    try {
      const response = await fetch('/api/admin/sync/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sync_interval_hours: interval })
      });
      
      this.showMessage(`Interval updated to ${interval} hours`, 'success');
      await this.updateStatus();
    } catch (error) {
      this.showMessage('Error: ' + error.message, 'danger');
    }
  }

  /**
   * Показать сообщение
   */
  showMessage(text, type = 'info') {
    const container = document.getElementById('sync-messages');
    if (!container) return;

    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
      ${text}
      <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    container.appendChild(alert);
    
    clearTimeout(this.messageTimeout);
    this.messageTimeout = setTimeout(() => {
      alert.remove();
    }, 5000);
  }

  /**
   * Добавить в лог активности
   */
  addActivityLog(text) {
    const log = document.getElementById('activity-log');
    if (!log) return;

    const item = document.createElement('div');
    item.className = 'small mb-2 pb-2 border-bottom';
    
    const now = new Date().toLocaleTimeString();
    item.innerHTML = `<span class="text-muted">${now}</span> - ${text}`;
    
    if (log.textContent.includes('No recent activity')) {
      log.innerHTML = '';
    }
    
    log.insertBefore(item, log.firstChild);
  }
}

// Инициализация при загрузке документа
document.addEventListener('DOMContentLoaded', async () => {
  window.syncTab = new SyncTab();
  
  // Инициализировать когда вкладка станет видимой
  const tab = document.getElementById('tab-sync');
  if (tab) {
    // Проверить если вкладка уже активна
    const tabPane = tab.closest('.tab-pane');
    if (tabPane && tabPane.classList.contains('active')) {
      await window.syncTab.init();
    } else if (tabPane) {
      // Инициализировать при активации вкладки
      tabPane.addEventListener('shown.bs.tab', () => {
        window.syncTab.init();
      });
    }
  }
});
