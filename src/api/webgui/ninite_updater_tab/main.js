/**
 * ninite_updater_tab/main.js — логика управления установкой и автообновлением Ninite
 */

(function () {
  'use stricti18n.t('auto__let_selectedfile_null_function_setupeventlisteners_const_dropzone_document_getelementbyid__04d3ad')ninite-dropzone');
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
      recoveryBtn.addEventListener('clicki18n.t('auto__handlelaunchrecovery_r_studio_async_function_handlelaunchrecovery_const_btn_document_getelementbyid__5057cc')btn-ninite-recovery-launch');
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>Запуск R-Studio...`;
    }

    try {
      const res = await fetch('/api/recovery/launch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/jsoni18n.t('auto__const_data_await_res_json_if_res_ok_throw_new_error_data_detail_http_res_status_showalert_strong_strong_data_message__95a524')Программа восстановления файлов R-Studio запущена!'}`, 'success');
      if (window.toast) {
        window.toast.success(i18n.t('auto_r_studio__de553b'), data.message || i18n.t('auto___380b94'));
      }
    } catch (err) {
      showAlert(`<strong>Ошибка запуска:</strong> ${err.message}`, 'danger');
      if (window.toast) {
        window.toast.error(i18n.t('auto__r_studio_666415'), err.message);
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
          fileStatus.innerHTML = `<span class="text-successi18n.t('auto__span_filedetails_textcontent_sizemb_mb_data_file_modified_time_else_filestatus_innerhtml_span_class__a0f680')text-warningi18n.t('auto__span_filedetails_textcontent_ninite_exe_program_files_if_data_task_if_data_task_exists_taskstatus_innerhtml_span_class__28e734')text-success">● Активна (${data.task.state})</span>`;
          taskDetails.textContent = `Задача: ${data.task.task_name} | Посл. запуск: ${data.task.last_run_time || i18n.t('auto___ced07f')}`;
          taskNext.textContent = data.task.next_run_time || i18n.t('auto___58506a');
        } else {
          taskStatus.innerHTML = `<span class="text-secondary">● Не запланирована</span>`;
          taskDetails.textContent = `Задача NiniteAutoUpdate отсутствует в Task Scheduler`;
          taskNext.textContent = '--';
        }
      }

      if (statusBadge) {
        if (data.file?.installed && data.task?.exists) {
          statusBadge.className = 'badge rounded-pill bg-success-subtle text-success border border-success px-2.5 py-1.5';
          statusBadge.textContent = i18n.t('auto___b147e5');
        } else if (data.file?.installed) {
          statusBadge.className = 'badge rounded-pill bg-warning-subtle text-warning border border-warning px-2.5 py-1.5';
          statusBadge.textContent = i18n.t('auto___22eddb');
        } else {
          statusBadge.className = 'badge rounded-pill bg-secondary-subtle text-light border border-secondary px-2.5 py-1.5';
          statusBadge.textContent = i18n.t('auto___b055a1');
        }
      }

      if (logViewer && data.log) {
        logViewer.textContent = data.log;
        if (logTimestamp) {
          logTimestamp.textContent = `Обновлено: ${new Date().toLocaleTimeString()}`;
        }
      }
    } catch (err) {
      console.error(i18n.t('auto__ninite__fd478f'), err);
      if (statusBadge) {
        statusBadge.className = 'badge rounded-pill bg-danger-subtle text-danger border border-danger px-2.5 py-1.5';
        statusBadge.textContent = i18n.t('auto___d58857');
      }
    }
  }

  /**
   * Отправка формы (загрузка файла + настройка Task Scheduler)
   */
  async function handleFormSubmit(e) {
    e.preventDefault();

    if (!selectedFile) {
      showAlert(i18n.t('auto__ninite__559d79'), 'warning');
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
        method: 'POSTi18n.t('auto__body_formdata_const_data_await_res_json_if_res_ok_throw_new_error_data_detail_http_res_status_showalert_data_message__c1f861')successi18n.t('auto__await_loadstatus_catch_err_showalert_err_message__a9b143')danger');
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
        headers: { 'Content-Type': 'application/jsoni18n.t('auto__body_json_stringify_interval_weeks_interval_time_str_timestr_days_of_week_day_const_data_await_res_json_if_res_ok_throw_new_error_data_detail_http_res_status_showalert_interval_timestr__9900ae')successi18n.t('auto__await_loadstatus_catch_err_showalert_err_message__0e1b43')dangeri18n.t('auto__async_function_handlerunnow_const_btn_document_getelementbyid__a5c30c')btn-ninite-run-now');
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>Запуск обновления...`;
    }

    try {
      const res = await fetch('/api/ninite/run-now', { method: 'POSTi18n.t('auto__const_data_await_res_json_if_res_ok_throw_new_error_data_detail_http_res_status_showalert_data_message__8d7fd7')infoi18n.t('auto__settimeout_loadstatus_3000_catch_err_showalert_err_message__fa737b')danger');
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
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label=i18n.t('auto___4ae50d')></button>
    `;
    box.style.display = 'blocki18n.t('auto__ninite_updater_function_initniniteupdatertab_setupeventlisteners_loadstatus_tab_core_js_window_initniniteupdatertab_initniniteupdatertab_window_initniniteupdatertab_initniniteupdatertab_window_initninite_updatertab_initniniteupdatertab_if_document_readystate__5fcf9c')loading') {
    document.addEventListener('DOMContentLoaded', initNiniteUpdaterTab);
  } else {
    initNiniteUpdaterTab();
  }
})();
