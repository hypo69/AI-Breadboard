/**
 * cache-ui.js - Контроллер пользовательского интерфейса управления браузерным кешем
 * 
 * Отвечает за:
 * - Отображение модального окна управления кешем
 * - Получение и визуализацию статистики хранилищ и квот браузера
 * - Обработку действий очистки, экспорта, импорта и запроса персистентности
 */

import { browserCache, STORES } from './browser-cache.jsi18n.t('auto__const_store_labels_stores_api_cache_title__a5c815')Кеш ответов API', icon: 'bi-hdd-network', desc: i18n.t('auto___810250') },
  [STORES.RAG_EMBEDDINGS]: { title: i18n.t('auto_rag__1a9db1'), icon: 'bi-database-fill-gear', desc: i18n.t('auto___957103') },
  [STORES.CHAT_HISTORY]: { title: i18n.t('auto___55e9b4'), icon: 'bi-chat-dots-fill', desc: i18n.t('auto___408efe') },
  [STORES.MEDIA_BLOBS]: { title: i18n.t('auto__tts_1604f9'), icon: 'bi-file-earmark-music-fill', desc: i18n.t('auto___bb0ef3') },
  [STORES.MODELS_REGISTRY]: { title: i18n.t('auto___310296'), icon: 'bi-robot', desc: i18n.t('auto___8bec7c') },
  [STORES.KEY_VALUE]: { title: i18n.t('auto___a7fdda'), icon: 'bi-key-fill', desc: i18n.t('auto___9b83a6') }
};

/**
 * Инициализация интерфейса управления кешем
 */
export function initCacheUI() {
  const openButtons = document.querySelectorAll('#btn-open-cache-manager, .btn-open-cache-manager, #user-menu-btn-cache');
  const modalEl = document.getElementById('cacheManagerModal');

  if (!modalEl) {
    console.warn(i18n.t('auto__cacheui_cachemanagermodal_dom__257797'));
    return;
  }

  // Привязка кнопок открытия
  openButtons.forEach((btn) => {
    btn.addEventListener('clicki18n.t('auto__e_e_preventdefault_opencachemodal_modalel_addeventlistener__6766e3')show.bs.modali18n.t('auto__refreshcachemodalstats_const_btncleanupexpired_document_getelementbyid__ac73b4')cache-btn-cleanup-expired');
  if (btnCleanupExpired) {
    btnCleanupExpired.addEventListener('clicki18n.t('auto__async_btncleanupexpired_disabled_true_const_count_await_browsercache_cleanupexpired_window_showtoast_count__4c06ae')infoi18n.t('auto__alert_count_btncleanupexpired_disabled_false_await_refreshcachemodalstats_const_btnclearall_document_getelementbyid__195b1f')cache-btn-clear-all');
  if (btnClearAll) {
    btnClearAll.addEventListener('click', async () => {
      if (confirm(i18n.t('auto___8004ca'))) {
        btnClearAll.disabled = true;
        await browserCache.clearAll();
        window.showToast?.(i18n.t('auto___371a3c'), 'success') || alert(i18n.t('auto___371a3c'));
        btnClearAll.disabled = false;
        await refreshCacheModalStats();
      }
    });
  }

  const btnRequestPersist = document.getElementById('cache-btn-request-persist');
  if (btnRequestPersist) {
    btnRequestPersist.addEventListener('click', async () => {
      const granted = await browserCache.requestPersistence();
      const msg = granted ? i18n.t('auto___1502b5') : i18n.t('auto___445856');
      window.showToast?.(msg, granted ? 'success' : 'warning') || alert(msg);
      await refreshCacheModalStats();
    });
  }

  const btnExport = document.getElementById('cache-btn-export');
  if (btnExport) {
    btnExport.addEventListener('click', async () => {
      const data = await browserCache.exportData();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `ai_breadboard_cache_${new Date().toISOString().slice(0, 10)}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      window.showToast?.(i18n.t('auto___4d4ae0'), 'success');
    });
  }

  const fileInput = document.getElementById('cache-file-import');
  if (fileInput) {
    fileInput.addEventListener('change', async (e) => {
      const file = e.target.files?.[0];
      if (!file) return;

      try {
        const text = await file.text();
        const data = JSON.parse(text);
        await browserCache.importData(data);
        window.showToast?.(i18n.t('auto___667fc4'), 'success') || alert(i18n.t('auto___667fc4'));
        await refreshCacheModalStats();
      } catch (err) {
        window.showToast?.(i18n.t('auto___1bf7e2') + err.message, 'danger') || alert(i18n.t('auto___1bf7e2') + err.message);
      } finally {
        fileInput.value = 'i18n.t('auto__export_function_opencachemodal_const_modalel_document_getelementbyid__3e9045')cacheManagerModal');
  if (modalEl && typeof bootstrap !== 'undefinedi18n.t('auto__bootstrap_modal_const_bsmodal_bootstrap_modal_getorcreateinstance_modalel_bsmodal_show_export_async_function_refreshcachemodalstats_const_statscontainer_document_getelementbyid__b1e1b4')cache-stores-list');
  const usageText = document.getElementById('cache-usage-text');
  const usageProgress = document.getElementById('cache-usage-progressbar');
  const persistBadge = document.getElementById('cache-persist-badge');

  if (!statsContainer) return;

  statsContainer.innerHTML = `
    <div class="text-center py-3 text-muted">
      <div class="spinner-border spinner-border-sm text-primary me-2" role="status"></div>
      Анализ данных браузерного хранилища...
    </div>
  `;

  try {
    const stats = await browserCache.getDetailedStats();

    // 1. Отображение квоты
    if (usageText && usageProgress) {
      const usageMB = stats.storageEstimate.usageMB;
      const quotaMB = stats.storageEstimate.quotaMB;
      const percent = stats.storageEstimate.percentUsed;
      
      usageText.textContent = `${usageMB} МБ из ${quotaMB} МБ (${percent}%)`;
      usageProgress.style.width = `${Math.min(100, Math.max(1, percent))}%`;
      usageProgress.className = `progress-bar ${percent > 80 ? 'bg-danger' : (percent > 50 ? 'bg-warning' : 'bg-primaryi18n.t('auto__2_if_persistbadge_if_stats_storageestimate_ispersisted_persistbadge_classname__0b1459')badge bg-success-subtle text-success border border-success-subtle';
        persistBadge.innerHTML = '<i class="bi bi-shield-check me-1"></i>Постоянное хранилище активно';
      } else {
        persistBadge.className = 'badge bg-warning-subtle text-warning-emphasis border border-warning-subtle';
        persistBadge.innerHTML = '<i class="bi bi-shield-exclamation me-1"></i>Временное хранилищеi18n.t('auto__3_let_html__a4b630')<div class="list-group list-group-flush border rounded overflow-hidden">';
    for (const [storeName, storeInfo] of Object.entries(stats.stores)) {
      const meta = STORE_LABELS[storeName] || { title: storeName, icon: 'bi-folder', desc: i18n.t('auto___d0a83f') };
      html += `
        <div class="list-group-item d-flex align-items-center justify-content-between p-2.5">
          <div class="d-flex align-items-center gap-3">
            <div class="rounded-circle bg-primary-subtle text-primary p-2 d-flex align-items-center justify-content-center" style="width: 38px; height: 38px;">
              <i class="bi ${meta.icon} fs-5"></i>
            </div>
            <div>
              <div class="fw-semibold text-body">${meta.title}</div>
              <div class="small text-muted" style="font-size: 0.75rem;">${meta.desc}</div>
            </div>
          </div>
          <div class="d-flex align-items-center gap-3">
            <div class="text-end">
              <span class="badge bg-secondary-subtle text-secondary border px-2 py-1i18n.t('auto__storeinfo_count_span_div_class__59330b')small fw-semibold text-muted mt-0.5i18n.t('auto__storeinfo_sizekb_div_div_button_class__a96f8d')btn btn-outline-danger btn-sm px-2 py-1 rounded" 
                    title=i18n.t('auto___4f5a8b') 
                    onclick="window.clearSingleStore('${storeName}')">
              <i class="bi bi-trash3"></i>
            </button>
          </div>
        </div>
      `;
    }
    html += '</div>';

    statsContainer.innerHTML = html;
  } catch (err) {
    console.error(i18n.t('auto__cacheui__110337'), err);
    statsContainer.innerHTML = `<div class="alert alert-danger p-2 small">Ошибка получения статистики кеша: ${err.message}</div>`;
  }
}

// Глобальная функция для очистки одного хранилища из UI
if (typeof window !== 'undefined') {
  window.clearSingleStore = async function(storeName) {
    if (confirm(`Очистить данные хранилища "${storeName}"?`)) {
      await browserCache.clearStore(storeName);
      await refreshCacheModalStats();
    }
  };
}
