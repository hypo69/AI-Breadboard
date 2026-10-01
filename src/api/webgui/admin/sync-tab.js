/**
 * =============================================================================
 * Process Name: AI-Breadboard UI - Sync-Tab Script
 * =============================================================================
 * Description:
 *   Клиентский веб-скрипт модуля sync-tab.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/src/api/webgui/admin/sync-tab.js?v=20261001_v1" type="module"></script>
 *
 * File: sync-tab.js
 * Project: ai-breadboard
 * Package: src/api/webgui/admin
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-01 13:13:56
 * =============================================================================
 */

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

    console.log('[SyncTab] Initializing...i18n.t('auto__html_await_this_loadhtml_this_attacheventlisteners_await_this_updatestatus_await_this_updatestats_if_window_registertabpoller_window_registertabpoller__1dafe3')tab-sync', () => this.updateStatus(), 5000, { pollerId: 'sync_status', immediate: false });
      window.registerTabPoller('tab-sync', () => this.updateStats(), 30000, { pollerId: 'sync_stats', immediate: false });
    } else {
      setInterval(() => this.updateStatus(), 5000);
      setInterval(() => this.updateStats(), 30000);
    }
    
    this.initialized = true;
    console.log('[SyncTab] Initializedi18n.t('auto__html_async_loadhtml_const_container_document_getelementbyid__11af5b')tab-sync');
    if (!container) {
      console.warn('[SyncTab] Container not found');
      return;
    }

    const html = `
      <div class="sync-paneli18n.t('auto__div_class__2f72cf')mb-4">
          <h4 class="d-flex align-items-center gap-2">
            <i class="bi bi-cloud-upload-fill text-primary"></i>
            <span>Google Drive Synchronization</span>
          </h4>
          <p class="text-muted mb-0i18n.t('auto__manage_data_synchronization_and_storage_migration_p_div_div_class__126a77')card border-secondary-subtle mb-3">
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
                    <a id="drive-url" href="#" target="_blank" class="small text-decoration-nonei18n.t('auto__open_a_div_div_div_div_div_div_div_class__0ec078')card border-secondary-subtle mb-3">
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
                <small class="text-mutedi18n.t('auto__errors_small_div_div_div_div_div_class__01984d')card border-secondary-subtle mb-3">
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
                <i class="bi bi-link-45degi18n.t('auto__i_test_connection_button_div_div_div_div_id__d81349')sync-options-modal" class="modal fade" tabindex="-1">
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
                <button type="button" class="btn btn-primary btn-sm" onclick="window.syncTab.performSync()i18n.t('auto__sync_selected_button_div_div_div_div_div_id__e4de77')sync-messages" class="mb-3i18n.t('auto__div_div_class__f1492d')card border-secondary-subtle">
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
      backdrop: 'statici18n.t('auto__window_synctab_this_html_async_updatestatus_try_const_response_await_fetch__a93059')/api/admin/sync/status');
      if (!response.ok) throw new Error('Failed to fetch statusi18n.t('auto__const_data_await_response_json_const_badge_document_getelementbyid__8dc09f')scheduler-status');
      badge.textContent = data.is_running ? 'Running' : 'Inactive';
      badge.className = data.is_running 
        ? 'badge bg-success' 
        : 'badge bg-dangeri18n.t('auto__document_getelementbyid__d54e5f')start-scheduler-btn').disabled = data.is_running;
      document.getElementById('stop-scheduler-btni18n.t('auto__disabled_data_is_running_document_getelementbyid__8950ff')last-sync-time').textContent = data.last_sync_time || 'Never';
      document.getElementById('sync-intervali18n.t('auto__textcontent_data_sync_interval_hours_hours_google_drive_try_const_driveresponse_await_fetch__1c1b68')/api/admin/sync/drive-info');
        if (driveResponse.ok) {
          const driveData = await driveResponse.json();
          const link = document.getElementById('drive-url');
          link.href = driveData.folder_url;
        }
      } catch (e) {
        console.warn('[SyncTab] Failed to fetch drive info');
      }
    } catch (error) {
      console.error('[SyncTab] Error updating status:i18n.t('auto__error_async_updatestats_try_const_response_await_fetch__9a4df7')/api/admin/sync/stats');
      if (!response.ok) throw new Error('Failed to fetch stats');
      
      const data = await response.json();

      document.getElementById('total-size').textContent = 
        `${data.total_size_mb.toFixed(1)} MB`;
      document.getElementById('files-count').textContent = data.files_count;
      document.getElementById('folders-count').textContent = data.folders_count;
      document.getElementById('sync-errors').textContent = data.sync_errors;
    } catch (error) {
      console.error('[SyncTab] Error updating stats:i18n.t('auto__error_async_startscheduler_try_const_interval_parseint_document_getelementbyid__01a7ed')sync-interval-input').value);
      const response = await fetch('/api/admin/sync/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sync_interval_hours: interval })
      });
      
      const data = await response.json();
      this.showMessage(data.message || 'Scheduler started', 'success');
      await this.updateStatus();
    } catch (error) {
      this.showMessage('Error: ' + error.message, 'dangeri18n.t('auto__async_stopscheduler_try_const_response_await_fetch__f1ec20')/api/admin/sync/stop', {
        method: 'POST'
      });
      
      const data = await response.json();
      this.showMessage(data.message || 'Scheduler stopped', 'success');
      await this.updateStatus();
    } catch (error) {
      this.showMessage('Error: ' + error.message, 'dangeri18n.t('auto__async_testconnection_try_const_response_await_fetch__503578')/api/admin/sync/test-connection', {
        method: 'POST'
      });
      
      const data = await response.json();
      const type = data.connected ? 'success' : 'warning';
      this.showMessage(data.message || 'Connection test completed', type);
    } catch (error) {
      this.showMessage('Error: ' + error.message, 'dangeri18n.t('auto__showsyncoptions_const_modal_bootstrap_modal_getinstance_document_getelementbyid__05706e')sync-options-modal')) ||
      new bootstrap.Modal(document.getElementById('sync-options-modali18n.t('auto__modal_show_async_performsync_const_synctype_document_queryselector__a40b11')input[name="sync-type"]:checked')?.value || 'all';
    
    try {
      const response = await fetch('/api/admin/sync/sync-now', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sync_type: syncType })
      });
      
      const data = await response.json();
      this.showMessage(data.message || 'Sync started', 'successi18n.t('auto__this_addactivitylog_started_synctype_synchronization_const_modal_bootstrap_modal_getinstance_document_getelementbyid__0332c5')sync-options-modal'));
      if (modal) modal.hide();
    } catch (error) {
      this.showMessage('Error: ' + error.message, 'dangeri18n.t('auto__async_updateinterval_const_interval_parseint_document_getelementbyid__92bf2f')sync-interval-input').value);
    
    try {
      const response = await fetch('/api/admin/sync/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sync_interval_hours: interval })
      });
      
      this.showMessage(`Interval updated to ${interval} hours`, 'success');
      await this.updateStatus();
    } catch (error) {
      this.showMessage('Error: ' + error.message, 'dangeri18n.t('auto__showmessage_text_type__f4dbdf')info') {
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
      log.innerHTML = 'i18n.t('auto__log_insertbefore_item_log_firstchild_document_addeventlistener__a7f3c0')DOMContentLoadedi18n.t('auto__async_window_synctab_new_synctab_const_tab_document_getelementbyid__db0d04')tab-synci18n.t('auto__if_tab_const_tabpane_tab_closest__3de99f').tab-pane');
    if (tabPane && tabPane.classList.contains('activei18n.t('auto__await_window_synctab_init_else_if_tabpane_tabpane_addeventlistener__a1f76c')shown.bs.tab', () => {
        window.syncTab.init();
      });
    }
  }
});
