/**
 * cache-ui.js - Контроллер пользовательского интерфейса управления браузерным кешем
 * 
 * Отвечает за:
 * - Отображение модального окна управления кешем
 * - Получение и визуализацию статистики хранилищ и квот браузера
 * - Обработку действий очистки, экспорта, импорта и запроса персистентности
 */

import { browserCache, STORES } from './browser-cache.js';

// Человекопонятные названия хранилищ
const STORE_LABELS = {
  [STORES.API_CACHE]: { title: 'Кеш ответов API', icon: 'bi-hdd-network', desc: 'Кешированные ответы сервера и справочники' },
  [STORES.RAG_EMBEDDINGS]: { title: 'RAG и Векторы', icon: 'bi-database-fill-gear', desc: 'Эмбеддинги, векторные чанки и поисковый индекс' },
  [STORES.CHAT_HISTORY]: { title: 'История чатов', icon: 'bi-chat-dots-fill', desc: 'Диалоги, сообщения ассистентов и контекст' },
  [STORES.MEDIA_BLOBS]: { title: 'Медиа и Аудио TTS', icon: 'bi-file-earmark-music-fill', desc: 'Сгенерированные аудиодорожки, картинки и бинарные файлы' },
  [STORES.MODELS_REGISTRY]: { title: 'Реестр моделей', icon: 'bi-robot', desc: 'Метаданные локальных и облачных моделей' },
  [STORES.KEY_VALUE]: { title: 'Пользовательские данные', icon: 'bi-key-fill', desc: 'Локальные параметры и временные значения' }
};

/**
 * Инициализация интерфейса управления кешем
 */
export function initCacheUI() {
  const openButtons = document.querySelectorAll('#btn-open-cache-manager, .btn-open-cache-manager, #user-menu-btn-cache');
  const modalEl = document.getElementById('cacheManagerModal');

  if (!modalEl) {
    console.warn('[CacheUI] Элемент #cacheManagerModal не найден в DOM.');
    return;
  }

  // Привязка кнопок открытия
  openButtons.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      openCacheModal();
    });
  });

  // Обновление статистики при открытии модального окна
  modalEl.addEventListener('show.bs.modal', () => {
    refreshCacheModalStats();
  });

  // Привязка действий кнопок
  const btnCleanupExpired = document.getElementById('cache-btn-cleanup-expired');
  if (btnCleanupExpired) {
    btnCleanupExpired.addEventListener('click', async () => {
      btnCleanupExpired.disabled = true;
      const count = await browserCache.cleanupExpired();
      window.showToast?.(`Очищено просроченных записей: ${count}`, 'info') || alert(`Очищено просроченных записей: ${count}`);
      btnCleanupExpired.disabled = false;
      await refreshCacheModalStats();
    });
  }

  const btnClearAll = document.getElementById('cache-btn-clear-all');
  if (btnClearAll) {
    btnClearAll.addEventListener('click', async () => {
      if (confirm('Вы действительно хотите полностью очистить весь браузерный кеш?')) {
        btnClearAll.disabled = true;
        await browserCache.clearAll();
        window.showToast?.('Все хранилища браузерного кеша успешно очищены.', 'success') || alert('Все хранилища браузерного кеша успешно очищены.');
        btnClearAll.disabled = false;
        await refreshCacheModalStats();
      }
    });
  }

  const btnRequestPersist = document.getElementById('cache-btn-request-persist');
  if (btnRequestPersist) {
    btnRequestPersist.addEventListener('click', async () => {
      const granted = await browserCache.requestPersistence();
      const msg = granted ? 'Постоянное хранилище успешно включено браузером.' : 'Браузер отклонил запрос персистентности.';
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
      window.showToast?.('Экспорт кеша успешно сохранён', 'success');
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
        window.showToast?.('Данные кеша успешно импортированы.', 'success') || alert('Данные кеша успешно импортированы.');
        await refreshCacheModalStats();
      } catch (err) {
        window.showToast?.('Ошибка при чтении файла импорта: ' + err.message, 'danger') || alert('Ошибка при чтении файла импорта: ' + err.message);
      } finally {
        fileInput.value = '';
      }
    });
  }
}

/**
 * Открыть модальное окно управления кешем
 */
export function openCacheModal() {
  const modalEl = document.getElementById('cacheManagerModal');
  if (modalEl && typeof bootstrap !== 'undefined' && bootstrap.Modal) {
    const bsModal = bootstrap.Modal.getOrCreateInstance(modalEl);
    bsModal.show();
  }
}

/**
 * Обновить и отрендерить статистику в модальном окне
 */
export async function refreshCacheModalStats() {
  const statsContainer = document.getElementById('cache-stores-list');
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
      usageProgress.className = `progress-bar ${percent > 80 ? 'bg-danger' : (percent > 50 ? 'bg-warning' : 'bg-primary')}`;
    }

    // 2. Статус персистентности
    if (persistBadge) {
      if (stats.storageEstimate.isPersisted) {
        persistBadge.className = 'badge bg-success-subtle text-success border border-success-subtle';
        persistBadge.innerHTML = '<i class="bi bi-shield-check me-1"></i>Постоянное хранилище активно';
      } else {
        persistBadge.className = 'badge bg-warning-subtle text-warning-emphasis border border-warning-subtle';
        persistBadge.innerHTML = '<i class="bi bi-shield-exclamation me-1"></i>Временное хранилище';
      }
    }

    // 3. Таблица хранилищ
    let html = '<div class="list-group list-group-flush border rounded overflow-hidden">';
    for (const [storeName, storeInfo] of Object.entries(stats.stores)) {
      const meta = STORE_LABELS[storeName] || { title: storeName, icon: 'bi-folder', desc: 'Хранилище данных' };
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
              <span class="badge bg-secondary-subtle text-secondary border px-2 py-1">${storeInfo.count} зап.</span>
              <div class="small fw-semibold text-muted mt-0.5">${storeInfo.sizeKB} КБ</div>
            </div>
            <button class="btn btn-outline-danger btn-sm px-2 py-1 rounded" 
                    title="Очистить это хранилище" 
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
    console.error('[CacheUI] Ошибка обновления статистики:', err);
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
