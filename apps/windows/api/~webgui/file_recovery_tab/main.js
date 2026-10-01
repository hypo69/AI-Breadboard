/**
 * =============================================================================
 * Process Name: Windows File Recovery Tab - Main Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля main.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/~webgui/file_recovery_tab/main.js?v=20261001_v1" type="module"></script>
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: windows/api/~webgui/file_recovery_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-01 13:04:40
 * =============================================================================
 */

/**
 * file_recovery_tab/main.js — логика вкладки «Восстановить удаленные файлы» (R-Studio Technician Portable)
 */

(function () {
  'use strict';

  function formatBytes(bytes) {
    if (!bytes || bytes <= 0) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return (bytes / Math.pow(1024, i)).toFixed(2) + ' ' + units[i];
  }

  function showAlert(msg, type = 'info') {
    const box = document.getElementById('recovery-alert-box');
    if (!box) return;
    box.className = `alert alert-${type} alert-dismissible fade show small py-2 px-3`;
    box.innerHTML = `
      <div class="d-flex align-items-center justify-content-between">
        <div>${msg}</div>
        <button type="button" class="btn-close py-2" data-bs-dismiss="alert" aria-label="Close"></button>
      </div>
    `;
    box.style.display = 'block';
  }

  async function loadRecoveryStatus() {
    const badge = document.getElementById('recovery-status-badge');
    const fileStatus = document.getElementById('recovery-file-status');
    const filePath = document.getElementById('recovery-file-path');
    const fileSize = document.getElementById('recovery-file-size');
    const fileDate = document.getElementById('recovery-file-date');

    try {
      if (badge) badge.textContent = i18n.t('auto___3eeb40');
      const res = await fetch(`/api/recovery/status?t=${Date.now()}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const data = await res.json();
      const tool = data.tool || {};

      if (tool.exists) {
        if (badge) {
          badge.className = 'badge rounded-pill bg-success-subtle border border-success text-success px-2.5 py-1.5';
          badge.textContent = i18n.t('auto___610706');
        }
        if (fileStatus) {
          fileStatus.className = 'recovery-stat-val text-success text-truncate';
          fileStatus.textContent = i18n.t('auto___01cc45');
        }
        if (filePath) filePath.textContent = tool.path || tool.relative_path || 'i18n.t('auto__if_filesize_filesize_textcontent_formatbytes_tool_size_bytes_if_filedate_filedate_textcontent_tool_modified_time__866f3f')--'}`;
      } else {
        if (badge) {
          badge.className = 'badge rounded-pill bg-warning-subtle border border-warning text-warning px-2.5 py-1.5';
          badge.textContent = i18n.t('auto___301538');
        }
        if (fileStatus) {
          fileStatus.className = 'recovery-stat-val text-warning text-truncate';
          fileStatus.textContent = i18n.t('auto__bin_eb95e4');
        }
        if (filePath) filePath.textContent = tool.relative_path || '';
        if (fileSize) fileSize.textContent = '0 B';
        if (fileDate) fileDate.textContent = '--';
      }
    } catch (err) {
      console.error(i18n.t('auto___b6e10b'), err);
      if (badge) {
        badge.className = 'badge rounded-pill bg-danger-subtle border border-danger text-danger px-2.5 py-1.5';
        badge.textContent = i18n.t('auto___6105a2');
      }
    }
  }

  async function launchRecoveryTool() {
    const btn = document.getElementById('btn-recovery-launch');
    if (!btn) return;

    const originalContent = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Запуск R-Studio...`;

    try {
      const res = await fetch('/api/recovery/launch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/jsoni18n.t('auto__const_data_await_res_json_if_res_ok_data_success_showalert_strong_strong_data_message__7aa3a2')Программа R-Studio успешно запущена!'}`, 'success');
        if (window.toast) {
          window.toast.success(i18n.t('auto_r_studio__de553b'), data.message || i18n.t('auto___380b94'));
        }
      } else {
        const err = data.detail || i18n.t('auto__r_studio_89e5b2');
        showAlert(`<strong>Ошибка:</strong> ${err}`, 'danger');
        if (window.toast) {
          window.toast.error(i18n.t('auto___ee6366'), err);
        }
      }
    } catch (err) {
      console.error(i18n.t('auto__api__b901f6'), err);
      showAlert(`<strong>Сетевая ошибка:</strong> ${err.message}`, 'danger');
      if (window.toast) {
        window.toast.error(i18n.t('auto___af5916'), err.message);
      }
    } finally {
      btn.disabled = false;
      btn.innerHTML = originalContent;
    }
  }

  function initListeners() {
    const refreshBtn = document.getElementById('btn-recovery-refresh');
    if (refreshBtn) {
      refreshBtn.onclick = () => loadRecoveryStatus();
    }

    const launchBtn = document.getElementById('btn-recovery-launchi18n.t('auto__if_launchbtn_launchbtn_onclick_launchrecoverytool_function_initfilerecoverytab_initlisteners_loadrecoverystatus_tab_core_js_window_initfile_recoverytab_initfilerecoverytab_window_initfilerecoverytab_initfilerecoverytab_window_initfilerecoverytab_initfilerecoverytab_window_initrecoverytab_initfilerecoverytab_if_document_readystate__5c8142')loading') {
    document.addEventListener('DOMContentLoaded', initFileRecoveryTab);
  } else {
    initFileRecoveryTab();
  }
})();
