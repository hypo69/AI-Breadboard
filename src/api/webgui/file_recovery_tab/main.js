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
      if (badge) badge.textContent = 'Обновление...';
      const res = await fetch(`/api/recovery/status?t=${Date.now()}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const data = await res.json();
      const tool = data.tool || {};

      if (tool.exists) {
        if (badge) {
          badge.className = 'badge rounded-pill bg-success-subtle border border-success text-success px-2.5 py-1.5';
          badge.textContent = 'Готов к запуску';
        }
        if (fileStatus) {
          fileStatus.className = 'recovery-stat-val text-success text-truncate';
          fileStatus.textContent = 'Файл найден';
        }
        if (filePath) filePath.textContent = tool.path || tool.relative_path || '';
        if (fileSize) fileSize.textContent = formatBytes(tool.size_bytes);
        if (fileDate) fileDate.textContent = `Изменён: ${tool.modified_time || '--'}`;
      } else {
        if (badge) {
          badge.className = 'badge rounded-pill bg-warning-subtle border border-warning text-warning px-2.5 py-1.5';
          badge.textContent = 'Исполняемый файл не найден';
        }
        if (fileStatus) {
          fileStatus.className = 'recovery-stat-val text-warning text-truncate';
          fileStatus.textContent = 'Не найден в bin';
        }
        if (filePath) filePath.textContent = tool.relative_path || '';
        if (fileSize) fileSize.textContent = '0 B';
        if (fileDate) fileDate.textContent = '--';
      }
    } catch (err) {
      console.error('Ошибка загрузки статуса утилиты восстановления:', err);
      if (badge) {
        badge.className = 'badge rounded-pill bg-danger-subtle border border-danger text-danger px-2.5 py-1.5';
        badge.textContent = 'Ошибка связи';
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
        headers: { 'Content-Type': 'application/json' },
      });

      const data = await res.json();

      if (res.ok && data.success) {
        showAlert(`<strong>Успех:</strong> ${data.message || 'Программа R-Studio успешно запущена!'}`, 'success');
        if (window.toast) {
          window.toast.success('R-Studio запущена', data.message || 'Окно программы открывается...');
        }
      } else {
        const err = data.detail || 'Не удалось запустить R-Studio';
        showAlert(`<strong>Ошибка:</strong> ${err}`, 'danger');
        if (window.toast) {
          window.toast.error('Ошибка запуска', err);
        }
      }
    } catch (err) {
      console.error('Ошибка вызова API запуска:', err);
      showAlert(`<strong>Сетевая ошибка:</strong> ${err.message}`, 'danger');
      if (window.toast) {
        window.toast.error('Сетевая ошибка', err.message);
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

    const launchBtn = document.getElementById('btn-recovery-launch');
    if (launchBtn) {
      launchBtn.onclick = () => launchRecoveryTool();
    }
  }

  function initFileRecoveryTab() {
    initListeners();
    loadRecoveryStatus();
  }

  // Экспорт для жизненного цикла tab-core.js
  window.initFile_recoveryTab = initFileRecoveryTab;
  window.initFilerecoveryTab = initFileRecoveryTab;
  window.initFileRecoveryTab = initFileRecoveryTab;
  window.initRecoveryTab = initFileRecoveryTab;

  // Автозапуск при самостоятельной загрузке
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initFileRecoveryTab);
  } else {
    initFileRecoveryTab();
  }
})();
