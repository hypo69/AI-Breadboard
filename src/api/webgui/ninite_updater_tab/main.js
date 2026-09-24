/**
 * ninite_updater_tab/main.js — логика управления установкой и автообновлением Ninite
 */

(function () {
  'use strict';

  let selectedFile = null;

  /**
   * Настройка обработчиков событий
   */
  function setupEventListeners() {
    const dropzone = document.getElementById('ninite-dropzone');
    const fileInput = document.getElementById('ninite-file-input');
    const form = document.getElementById('ninite-upload-form');
    const refreshBtn = document.getElementById('btn-ninite-refresh');
    const runNowBtn = document.getElementById('btn-ninite-run-now');
    const scheduleOnlyBtn = document.getElementById('btn-ninite-update-schedule-only');

    if (fileInput) {
      fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
          handleFileSelect(e.target.files[0]);
        }
      });
    }

    if (dropzone) {
      dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
      });

      dropzone.addEventListener('dragleave', () => {
        dropzone.classList.remove('dragover');
      });

      dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
          handleFileSelect(e.dataTransfer.files[0]);
        }
      });
    }

    if (form) {
      form.addEventListener('submit', handleFormSubmit);
    }

    if (refreshBtn) {
      refreshBtn.addEventListener('click', () => loadStatus());
    }

    if (runNowBtn) {
      runNowBtn.addEventListener('click', handleRunNow);
    }

    if (scheduleOnlyBtn) {
      scheduleOnlyBtn.addEventListener('click', handleScheduleOnly);
    }

    const recoveryBtn = document.getElementById('btn-ninite-recovery-launch');
    if (recoveryBtn) {
      recoveryBtn.addEventListener('click', handleLaunchRecovery);
    }
  }

  /**
   * Запуск R-Studio для восстановления удаленных файлов
   */
  async function handleLaunchRecovery() {
    const btn = document.getElementById('btn-ninite-recovery-launch');
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>Запуск R-Studio...`;
    }

    try {
      const res = await fetch('/api/recovery/launch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || `HTTP ${res.status}`);
      }

      showAlert(`<strong>Успех:</strong> ${data.message || 'Программа восстановления файлов R-Studio запущена!'}`, 'success');
      if (window.toast) {
        window.toast.success('R-Studio запущена', data.message || 'Окно программы открывается...');
      }
    } catch (err) {
      showAlert(`<strong>Ошибка запуска:</strong> ${err.message}`, 'danger');
      if (window.toast) {
        window.toast.error('Ошибка запуска R-Studio', err.message);
      }
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = `<i class="bi bi-folder-symlink-fill"></i> Восстановить удаленные файлы`;
      }
    }
  }

  /**
   * Обработка выбора файла
   */
  function handleFileSelect(file) {
    selectedFile = file;
    const label = document.getElementById('ninite-file-label');
    if (label) {
      const sizeMb = (file.size / (1024 * 1024)).toFixed(2);
      label.innerHTML = `✅ Выбран файл: <strong class="text-info">${file.name}</strong> (${sizeMb} MB)`;
    }
  }

  /**
   * Загрузка текущего статуса файла и задачи в Task Scheduler
   */
  async function loadStatus() {
    const statusBadge = document.getElementById('ninite-status-badge');
    const fileStatus = document.getElementById('ninite-file-status');
    const fileDetails = document.getElementById('ninite-file-details');
    const taskStatus = document.getElementById('ninite-task-status');
    const taskDetails = document.getElementById('ninite-task-details');
    const taskNext = document.getElementById('ninite-task-next');
    const logViewer = document.getElementById('ninite-log-viewer');
    const logTimestamp = document.getElementById('ninite-log-timestamp');

    try {
      const res = await fetch(`/api/ninite/status?t=${Date.now()}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      if (data.file) {
        if (data.file.installed) {
          const sizeMb = (data.file.size_bytes / (1024 * 1024)).toFixed(2);
          fileStatus.innerHTML = `<span class="text-success">● Установлен</span>`;
          fileDetails.textContent = `Размер: ${sizeMb} MB | Изменён: ${data.file.modified_time}`;
        } else {
          fileStatus.innerHTML = `<span class="text-warning">● Не установлен</span>`;
          fileDetails.textContent = `Файл ninite.exe отсутствует в Program Files`;
        }
      }

      if (data.task) {
        if (data.task.exists) {
          taskStatus.innerHTML = `<span class="text-success">● Активна (${data.task.state})</span>`;
          taskDetails.textContent = `Задача: ${data.task.task_name} | Посл. запуск: ${data.task.last_run_time || 'нет'}`;
          taskNext.textContent = data.task.next_run_time || 'По расписанию';
        } else {
          taskStatus.innerHTML = `<span class="text-secondary">● Не запланирована</span>`;
          taskDetails.textContent = `Задача NiniteAutoUpdate отсутствует в Task Scheduler`;
          taskNext.textContent = '--';
        }
      }

      if (statusBadge) {
        if (data.file?.installed && data.task?.exists) {
          statusBadge.className = 'badge rounded-pill bg-success-subtle text-success border border-success px-2.5 py-1.5';
          statusBadge.textContent = '● Автообновление активно';
        } else if (data.file?.installed) {
          statusBadge.className = 'badge rounded-pill bg-warning-subtle text-warning border border-warning px-2.5 py-1.5';
          statusBadge.textContent = '● Файл готов, расписание не задано';
        } else {
          statusBadge.className = 'badge rounded-pill bg-secondary-subtle text-light border border-secondary px-2.5 py-1.5';
          statusBadge.textContent = '● Ожидание установки';
        }
      }

      if (logViewer && data.log) {
        logViewer.textContent = data.log;
        if (logTimestamp) {
          logTimestamp.textContent = `Обновлено: ${new Date().toLocaleTimeString()}`;
        }
      }
    } catch (err) {
      console.error('Ошибка загрузки статуса Ninite:', err);
      if (statusBadge) {
        statusBadge.className = 'badge rounded-pill bg-danger-subtle text-danger border border-danger px-2.5 py-1.5';
        statusBadge.textContent = '● Ошибка связи с сервером';
      }
    }
  }

  /**
   * Отправка формы (загрузка файла + настройка Task Scheduler)
   */
  async function handleFormSubmit(e) {
    e.preventDefault();

    if (!selectedFile) {
      showAlert('Пожалуйста, выберите файл инсталлятора Ninite для загрузки.', 'warning');
      return;
    }

    const interval = document.getElementById('ninite-interval')?.value || '2';
    const timeStr = document.getElementById('ninite-time')?.value || '20:00';
    const submitBtn = document.getElementById('btn-ninite-submit');

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('interval_weeks', interval);
    formData.append('time_str', timeStr);

    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>Копирование в Program Files и регистрация задачи...`;
    }

    try {
      const res = await fetch('/api/ninite/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || `HTTP ${res.status}`);
      }

      showAlert(`Успешно! ${data.message}`, 'success');
      await loadStatus();
    } catch (err) {
      showAlert(`Ошибка: ${err.message}`, 'danger');
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = `<i class="bi bi-check-circle-fill me-1"></i> Установить в Program Files и активировать Task Scheduler`;
      }
    }
  }

  /**
   * Обновление только расписания без перезагрузки файла
   */
  async function handleScheduleOnly() {
    const interval = parseInt(document.getElementById('ninite-interval')?.value || '2', 10);
    const timeStr = document.getElementById('ninite-time')?.value || '20:00';
    const day = document.getElementById('ninite-day')?.value || 'Sunday';

    try {
      const res = await fetch('/api/ninite/schedule', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          interval_weeks: interval,
          time_str: timeStr,
          days_of_week: day,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || `HTTP ${res.status}`);
      }

      showAlert(`Расписание обновлено: каждые ${interval} нед. в ${timeStr}`, 'success');
      await loadStatus();
    } catch (err) {
      showAlert(`Ошибка обновления расписания: ${err.message}`, 'danger');
    }
  }

  /**
   * Ручной запуск обновления сейчас
   */
  async function handleRunNow() {
    const btn = document.getElementById('btn-ninite-run-now');
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>Запуск обновления...`;
    }

    try {
      const res = await fetch('/api/ninite/run-now', { method: 'POST' });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || `HTTP ${res.status}`);
      }

      showAlert(`Обновление запущено: ${data.message}`, 'info');
      setTimeout(loadStatus, 3000);
    } catch (err) {
      showAlert(`Ошибка запуска: ${err.message}`, 'danger');
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = `<i class="bi bi-play-circle-fill me-1"></i> Запустить обновление прямо сейчас`;
      }
    }
  }

  /**
   * Отображение информационного сообщения
   */
  function showAlert(message, type = 'info') {
    const box = document.getElementById('ninite-alert-box');
    if (!box) return;

    box.className = `alert alert-${type} alert-dismissible fade show small`;
    box.innerHTML = `
      <div>${message}</div>
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Закрыть"></button>
    `;
    box.style.display = 'block';
  }

  /**
   * Инициализация вкладки Ninite Updater
   */
  function initNiniteUpdaterTab() {
    setupEventListeners();
    loadStatus();
  }

  // Экспорт для жизненного цикла tab-core.js и глобального контекста
  window.initNiniteUpdaterTab = initNiniteUpdaterTab;
  window.initNiniteupdaterTab = initNiniteUpdaterTab;
  window.initNinite_updaterTab = initNiniteUpdaterTab;

  // Автоматический запуск при автономной загрузке
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initNiniteUpdaterTab);
  } else {
    initNiniteUpdaterTab();
  }
})();
