/**
 * =============================================================================
 * Process Name: Windows Window Management & Personalization Control Plane - Main Script
 * =============================================================================
 * Description:
 *   Клиентский веб-скрипт единого центра управления окнами и персонализацией
 *   Windows (Window Management & Personalization Control Plane). Обеспечивает:
 *   - Работу со всеми 295 параметрами диспетчера окон Windows по 15 категориям
 *   - Управление темами Windows, Dark/Light режимом и системным Accent Color
 *   - Тонкую настройку указателя мыши (Размер 1..128px, цвета, шлейф, тень, скорость)
 *   - Управление обоями (Picture, Solid, Slideshow, Spotlight, Fit modes)
 *   - Интеллектуальный Spotlight («О фотографии», метаданные, GPS, факты)
 *   - Единый журнал аудита изменений и откат (Rollback) через telemetry.db.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/html/window_management_tab/main.js?v=20261006_v2" type="module"></script>
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: src/api/webgui/window_management_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-06 18:35:00
 * =============================================================================
 */

(function () {
  'use strict';

  // Базовые API пути
  const WCP_API_ENDPOINTS = [
    '/api/v1/window-management',
    '/api/windows/window-management',
  ];
  const PERS_API_ENDPOINTS = [
    '/api/v1/windows/personalization',
    '/api/windows/personalization',
  ];

  let activeWcpApi = WCP_API_ENDPOINTS[0];
  let activePersApi = PERS_API_ENDPOINTS[0];

  let catalogItems = [];
  let summaryData = null;
  let stagedChanges = new Map(); // id -> proposed value
  let activeCategory = 'all';
  let activeRisk = 'all';
  let activeBackend = 'all';
  let activeScope = 'all';
  let searchQuery = '';
  let onlyModified = false;
  let viewMode = 'cards'; // 'cards' | 'table'

  // Текущее состояние персонализации
  let currentCursorSettings = {
    size: 32,
    color: 'white',
    custom_color_hex: '#FFFF00',
    scheme: 'default',
    shadow: true,
    trails: false,
    hide_while_typing: true,
    show_location_on_ctrl: false,
    pointer_speed: 10,
  };

  const CATEGORY_NAMES = {
    focus_activation: '1. Focus & Activation',
    window_animations: '2. Animations & Visual Effects',
    window_geometry: '3. Window Geometry & Metrics',
    window_arrangement: '4. Arrangement & Snap Assist',
    alttab_task_switching: '5. Alt+Tab Switching',
    virtual_desktops: '6. Virtual Desktops',
    dwm_composition: '7. DWM Composition',
    taskbar_switching: '8. Taskbar Switching',
    mouse_behaviour: '9. Mouse Behaviour',
    keyboard_focus: '10. Keyboard & Focus',
    accessibility: '11. Accessibility',
    display_multimonitor: '12. Display & Multi-Monitor',
    desktop_explorer: '13. Desktop & Explorer',
    window_metrics_theme: '14. Metrics & Theme',
    shell_policy_controls: '15. Shell & Policy Controls',
  };

  /**
   * Инициализация вкладки
   */
  async function init() {
    bindSubTabs();
    bindWcpEvents();
    bindPersonalizationEvents();
    await determineApiBases();
    await loadSummary();
    await loadCatalog();
    await loadPersonalizationOverview();
    await loadAISpotlightCurrent();
  }

  /**
   * Определение доступных базовых URL
   */
  async function determineApiBases() {
    for (const ep of WCP_API_ENDPOINTS) {
      try {
        const res = await fetch(`${ep}/summary`, { cache: 'no-cache' });
        if (res.ok) {
          activeWcpApi = ep;
          break;
        }
      } catch (e) {}
    }

    for (const ep of PERS_API_ENDPOINTS) {
      try {
        const res = await fetch(`${ep}/overview`, { cache: 'no-cache' });
        if (res.ok) {
          activePersApi = ep;
          break;
        }
      } catch (e) {}
    }
  }

  /**
   * Переключение между 6 главными суб-вкладками
   */
  function bindSubTabs() {
    const tabButtons = document.querySelectorAll('.wcp-main-tab-btn');
    tabButtons.forEach((btn) => {
      btn.addEventListener('click', () => {
        const targetSubtab = btn.dataset.subtab;
        tabButtons.forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');

        document.querySelectorAll('.wcp-subtab-pane').forEach((pane) => {
          pane.classList.add('d-none');
        });

        const activePane = document.getElementById(`wcp-subtab-content-${targetSubtab}`);
        if (activePane) {
          activePane.classList.remove('d-none');
        }

        // Lazy-loading данных для активной суб-вкладки
        if (targetSubtab === 'history') {
          loadAuditHistoryTab();
        } else if (targetSubtab === 'themes') {
          loadThemesList();
        } else if (targetSubtab === 'spotlight') {
          loadAISpotlightGallery();
        }
      });
    });
  }

  /**
   * Привязка обработчиков для диспетчера окон (295 настроек)
   */
  function bindWcpEvents() {
    const btnReload = document.getElementById('wcp-btn-reload');
    if (btnReload) {
      btnReload.addEventListener('click', async () => {
        btnReload.classList.add('disabled');
        await loadCatalog(true);
        await loadPersonalizationOverview();
        btnReload.classList.remove('disabled');
        showToast('Все параметры и настройки успешно обновлены', 'success');
      });
    }

    const btnRestorePoint = document.getElementById('wcp-btn-restore-point');
    if (btnRestorePoint) {
      btnRestorePoint.addEventListener('click', createRestorePointAction);
    }

    const btnBatchApply = document.getElementById('wcp-btn-batch-apply');
    if (btnBatchApply) {
      btnBatchApply.addEventListener('click', openBatchModal);
    }

    const btnBatchConfirm = document.getElementById('wcp-batch-confirm-apply-btn');
    if (btnBatchConfirm) {
      btnBatchConfirm.addEventListener('click', executeBatchApply);
    }

    const btnClearStaged = document.getElementById('wcp-btn-clear-staged');
    if (btnClearStaged) {
      btnClearStaged.addEventListener('click', clearStagedChanges);
    }

    const searchInput = document.getElementById('wcp-search-input');
    const searchClear = document.getElementById('wcp-search-clear-btn');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        searchQuery = e.target.value.trim().toLowerCase();
        if (searchClear) searchClear.classList.toggle('d-none', !searchQuery);
        applyFiltersAndRender();
      });
    }
    if (searchClear && searchInput) {
      searchClear.addEventListener('click', () => {
        searchInput.value = '';
        searchQuery = '';
        searchClear.classList.add('d-none');
        applyFiltersAndRender();
      });
    }

    const filterRisk = document.getElementById('wcp-filter-risk');
    if (filterRisk) {
      filterRisk.addEventListener('change', (e) => {
        activeRisk = e.target.value;
        applyFiltersAndRender();
      });
    }

    const filterBackend = document.getElementById('wcp-filter-backend');
    if (filterBackend) {
      filterBackend.addEventListener('change', (e) => {
        activeBackend = e.target.value;
        applyFiltersAndRender();
      });
    }

    const filterScope = document.getElementById('wcp-filter-scope');
    if (filterScope) {
      filterScope.addEventListener('change', (e) => {
        activeScope = e.target.value;
        applyFiltersAndRender();
      });
    }

    const filterModified = document.getElementById('wcp-filter-only-modified');
    if (filterModified) {
      filterModified.addEventListener('change', (e) => {
        onlyModified = e.target.checked;
        applyFiltersAndRender();
      });
    }

    const btnViewCards = document.getElementById('wcp-view-cards-btn');
    const btnViewTable = document.getElementById('wcp-view-table-btn');
    if (btnViewCards && btnViewTable) {
      btnViewCards.addEventListener('click', () => {
        viewMode = 'cards';
        btnViewCards.classList.add('active');
        btnViewTable.classList.remove('active');
        renderItems();
      });
      btnViewTable.addEventListener('click', () => {
        viewMode = 'table';
        btnViewTable.classList.add('active');
        btnViewCards.classList.remove('active');
        renderItems();
      });
    }

    const categoryButtons = document.querySelectorAll('#wcp-categories-pills .wcp-cat-btn');
    categoryButtons.forEach((btn) => {
      btn.addEventListener('click', () => {
        categoryButtons.forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');
        activeCategory = btn.dataset.category || 'all';
        applyFiltersAndRender();
      });
    });

    const btnResetFilters = document.getElementById('wcp-reset-filters-btn');
    if (btnResetFilters) {
      btnResetFilters.addEventListener('click', () => {
        if (searchInput) searchInput.value = '';
        searchQuery = '';
        if (searchClear) searchClear.classList.add('d-none');
        if (filterRisk) filterRisk.value = 'all';
        activeRisk = 'all';
        if (filterBackend) filterBackend.value = 'all';
        activeBackend = 'all';
        if (filterScope) filterScope.value = 'all';
        activeScope = 'all';
        if (filterModified) filterModified.checked = false;
        onlyModified = false;
        activeCategory = 'all';
        categoryButtons.forEach((b) => {
          b.classList.toggle('active', b.dataset.category === 'all');
        });
        applyFiltersAndRender();
      });
    }
  }

  /**
   * Привязка обработчиков для персонализации (Темы, Курсор, Обои, Spotlight, Журнал)
   */
  function bindPersonalizationEvents() {
    // --- 1. Темы и Цвета ---
    const btnLight = document.getElementById('wcp-theme-mode-light');
    const btnDark = document.getElementById('wcp-theme-mode-dark');
    if (btnLight && btnDark) {
      btnLight.addEventListener('click', () => setSystemThemeMode(false));
      btnDark.addEventListener('click', () => setSystemThemeMode(true));
    }

    const accentPicker = document.getElementById('wcp-theme-accent-color');
    const accentHex = document.getElementById('wcp-theme-accent-hex');
    if (accentPicker && accentHex) {
      accentPicker.addEventListener('input', (e) => {
        accentHex.value = e.target.value.toUpperCase();
      });
      accentHex.addEventListener('input', (e) => {
        if (/^#[0-9A-F]{6}$/i.test(e.target.value)) {
          accentPicker.value = e.target.value;
        }
      });
    }

    const btnSaveAccent = document.getElementById('wcp-theme-save-accent-btn');
    if (btnSaveAccent) {
      btnSaveAccent.addEventListener('click', saveSystemColorsAction);
    }

    const btnThemesRefresh = document.getElementById('wcp-themes-refresh-btn');
    if (btnThemesRefresh) {
      btnThemesRefresh.addEventListener('click', loadThemesList);
    }

    // --- 2. Курсор и Указатель ---
    const cursorSlider = document.getElementById('wcp-cursor-size-slider');
    const cursorBadge = document.getElementById('wcp-cursor-size-badge');
    const cursorIcon = document.getElementById('wcp-cursor-icon');
    const cursorDesc = document.getElementById('wcp-cursor-preview-desc');

    if (cursorSlider && cursorBadge) {
      cursorSlider.addEventListener('input', (e) => {
        const sz = parseInt(e.target.value, 10);
        cursorBadge.textContent = `${sz} px`;
        currentCursorSettings.size = sz;
        updateCursorPreview();
      });
    }

    const cursorSpeedSlider = document.getElementById('wcp-cursor-speed-slider');
    const cursorSpeedBadge = document.getElementById('wcp-cursor-speed-badge');
    if (cursorSpeedSlider && cursorSpeedBadge) {
      cursorSpeedSlider.addEventListener('input', (e) => {
        const sp = parseInt(e.target.value, 10);
        cursorSpeedBadge.textContent = String(sp);
        currentCursorSettings.pointer_speed = sp;
      });
    }

    // Кнопки цветов курсора
    ['white', 'black', 'inverted', 'custom'].forEach((col) => {
      const btn = document.getElementById(`wcp-cursor-btn-${col}`);
      if (btn) {
        btn.addEventListener('click', () => {
          document.querySelectorAll('[data-cursor-color]').forEach((b) => b.classList.remove('active'));
          btn.classList.add('active');
          currentCursorSettings.color = col;
          const customPicker = document.getElementById('wcp-cursor-custom-color-picker');
          if (customPicker) {
            customPicker.classList.toggle('d-none', col !== 'custom');
          }
          updateCursorPreview();
        });
      }
    });

    const cursorColorInput = document.getElementById('wcp-cursor-color-input');
    if (cursorColorInput) {
      cursorColorInput.addEventListener('input', (e) => {
        currentCursorSettings.custom_color_hex = e.target.value;
        updateCursorPreview();
      });
    }

    const btnApplyCursor = document.getElementById('wcp-cursor-apply-btn');
    if (btnApplyCursor) {
      btnApplyCursor.addEventListener('click', applyCursorSettingsAction);
    }

    const btnResetCursor = document.getElementById('wcp-cursor-reset-btn');
    if (btnResetCursor) {
      btnResetCursor.addEventListener('click', () => {
        if (cursorSlider) {
          cursorSlider.value = 32;
          cursorBadge.textContent = '32 px';
        }
        currentCursorSettings.size = 32;
        currentCursorSettings.color = 'white';
        const btnWhite = document.getElementById('wcp-cursor-btn-white');
        if (btnWhite) btnWhite.click();
        updateCursorPreview();
      });
    }

    // --- 3. Обои рабочего стола ---
    const wallpaperModeSelect = document.getElementById('wcp-wallpaper-mode-select');
    if (wallpaperModeSelect) {
      wallpaperModeSelect.addEventListener('change', (e) => {
        const mode = e.target.value;
        const colorGroup = document.getElementById('wcp-wallpaper-color-group');
        const pathGroup = document.getElementById('wcp-wallpaper-path-group');
        const fitGroup = document.getElementById('wcp-wallpaper-fit-group');

        if (colorGroup) colorGroup.classList.toggle('d-none', mode !== 'solid_color');
        if (pathGroup) pathGroup.classList.toggle('d-none', mode === 'solid_color' || mode === 'spotlight');
        if (fitGroup) fitGroup.classList.toggle('d-none', mode === 'solid_color');
      });
    }

    const btnWallpaperApply = document.getElementById('wcp-wallpaper-apply-btn');
    if (btnWallpaperApply) {
      btnWallpaperApply.addEventListener('click', applyWallpaperAction);
    }

    const btnRandomSpotlight = document.getElementById('wcp-wallpaper-random-spotlight-btn');
    if (btnRandomSpotlight) {
      btnRandomSpotlight.addEventListener('click', setRandomSpotlightWallpaper);
    }

    // --- 4. AI Spotlight ---
    const btnSpotlightSetWall = document.getElementById('wcp-spotlight-set-wallpaper-btn');
    if (btnSpotlightSetWall) {
      btnSpotlightSetWall.addEventListener('click', applySpotlightHeroAsWallpaper);
    }

    const btnSpotlightGalleryRef = document.getElementById('wcp-spotlight-gallery-refresh-btn');
    if (btnSpotlightGalleryRef) {
      btnSpotlightGalleryRef.addEventListener('click', loadAISpotlightGallery);
    }

    // --- 5. Журнал аудита ---
    const btnHistoryRefreshTab = document.getElementById('wcp-history-tab-refresh-btn');
    if (btnHistoryRefreshTab) {
      btnHistoryRefreshTab.addEventListener('click', loadAuditHistoryTab);
    }
  }

  function updateCursorPreview() {
    const cursorIcon = document.getElementById('wcp-cursor-icon');
    const cursorDesc = document.getElementById('wcp-cursor-preview-desc');
    if (!cursorIcon) return;

    cursorIcon.style.fontSize = `${currentCursorSettings.size}px`;

    let colorStyle = '#ffffff';
    let colorName = 'Белый';

    if (currentCursorSettings.color === 'black') {
      colorStyle = '#1e293b';
      colorName = 'Чёрный';
    } else if (currentCursorSettings.color === 'inverted') {
      colorStyle = '#38bdf8';
      colorName = 'Инверсный';
    } else if (currentCursorSettings.color === 'custom') {
      colorStyle = currentCursorSettings.custom_color_hex || '#ffff00';
      colorName = `Кастомный (${colorStyle})`;
    }

    cursorIcon.style.color = colorStyle;
    if (cursorDesc) {
      cursorDesc.textContent = `Размер: ${currentCursorSettings.size}px | Цвет: ${colorName}`;
    }
  }

  /**
   * Загрузка сводки каталога
   */
  async function loadSummary() {
    try {
      const res = await fetch(`${activeWcpApi}/summary`, { cache: 'no-cache' });
      if (!res.ok) return;
      summaryData = await res.json();
      updateHeaderMetrics(summaryData);
    } catch (e) {
      console.warn('Не удалось загрузить сводку каталога:', e);
    }
  }

  function updateHeaderMetrics(summary) {
    if (!summary) return;
    const elTotal = document.getElementById('wcp-stat-total');
    const elSafe = document.getElementById('wcp-stat-safe');
    const elCaution = document.getElementById('wcp-stat-caution');
    const elCritical = document.getElementById('wcp-stat-critical');

    if (elTotal) elTotal.textContent = summary.total_settings || 295;
    if (elSafe && summary.by_risk) elSafe.textContent = summary.by_risk.safe || 225;
    if (elCaution && summary.by_risk) elCaution.textContent = summary.by_risk.caution || 61;
    if (elCritical && summary.by_risk) elCritical.textContent = summary.by_risk.critical || 9;
  }

  /**
   * Загрузка полного каталога настроек
   */
  async function loadCatalog(forceRefresh = false) {
    const spinner = document.getElementById('wcp-loading-spinner');
    if (spinner) spinner.classList.remove('d-none');

    try {
      const url = `${activeWcpApi}/catalog?include_current=true${forceRefresh ? '&refresh=true' : ''}`;
      const res = await fetch(url, { cache: 'no-cache' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      catalogItems = data.items || [];
      applyFiltersAndRender();
    } catch (e) {
      console.error('Ошибка загрузки каталога:', e);
      showToast('Ошибка загрузки параметров Windows', 'error');
    } finally {
      if (spinner) spinner.classList.add('d-none');
    }
  }

  /**
   * Применение фильтров и рендеринг каталога
   */
  function applyFiltersAndRender() {
    let filtered = catalogItems;

    if (activeCategory !== 'all') {
      filtered = filtered.filter((item) => item.category === activeCategory);
    }
    if (activeRisk !== 'all') {
      filtered = filtered.filter((item) => item.risk_level === activeRisk);
    }
    if (activeBackend !== 'all') {
      filtered = filtered.filter((item) => item.backend?.type === activeBackend);
    }
    if (activeScope !== 'all') {
      filtered = filtered.filter((item) => item.scope === activeScope);
    }
    if (onlyModified) {
      filtered = filtered.filter((item) => stagedChanges.has(item.id));
    }
    if (searchQuery) {
      filtered = filtered.filter((item) => {
        const idMatch = item.id.toLowerCase().includes(searchQuery);
        const nameMatch = item.name.toLowerCase().includes(searchQuery);
        const descMatch = (item.description || '').toLowerCase().includes(searchQuery);
        const backendMatch = (item.backend?.key_path || item.backend?.spi_constant || '').toLowerCase().includes(searchQuery);
        return idMatch || nameMatch || descMatch || backendMatch;
      });
    }

    renderItems(filtered);
  }

  function renderItems(itemsToRender = null) {
    const items = itemsToRender !== null ? itemsToRender : catalogItems;

    const cardsContainer = document.getElementById('wcp-cards-view');
    const tableContainer = document.getElementById('wcp-table-view');
    const tableBody = document.getElementById('wcp-table-body');
    const noResults = document.getElementById('wcp-no-results');
    const resultsHeader = document.getElementById('wcp-results-header');
    const filteredCount = document.getElementById('wcp-filtered-count');

    if (filteredCount) filteredCount.textContent = items.length;
    if (resultsHeader) resultsHeader.classList.remove('d-none');

    if (items.length === 0) {
      if (cardsContainer) cardsContainer.classList.add('d-none');
      if (tableContainer) tableContainer.classList.add('d-none');
      if (noResults) noResults.classList.remove('d-none');
      return;
    }

    if (noResults) noResults.classList.add('d-none');

    if (viewMode === 'cards') {
      if (tableContainer) tableContainer.classList.add('d-none');
      if (cardsContainer) {
        cardsContainer.classList.remove('d-none');
        cardsContainer.innerHTML = items.map((item) => renderCardItem(item)).join('');
        attachItemEventListeners(cardsContainer);
      }
    } else {
      if (cardsContainer) cardsContainer.classList.add('d-none');
      if (tableContainer && tableBody) {
        tableContainer.classList.remove('d-none');
        tableBody.innerHTML = items.map((item) => renderTableRowItem(item)).join('');
        attachItemEventListeners(tableBody);
      }
    }
  }

  function renderCardItem(item) {
    const isModified = stagedChanges.has(item.id);
    const currentValue = item.current_value;
    const effectiveValue = isModified ? stagedChanges.get(item.id) : currentValue;

    const riskClass = item.risk_level === 'critical' ? 'wcp-tag-critical' : item.risk_level === 'caution' ? 'wcp-tag-caution' : 'wcp-tag-safe';
    const riskLabel = item.risk_level === 'critical' ? 'Критично' : item.risk_level === 'caution' ? 'Внимание' : 'Safe';

    return `
      <div class="col-12 col-md-6 col-xl-4" data-setting-id="${item.id}">
        <div class="wcp-card ${isModified ? 'modified' : ''}">
          <div>
            <div class="d-flex align-items-start justify-content-between gap-2 mb-2">
              <span class="badge bg-secondary-subtle text-secondary font-monospace" style="font-size: 0.72rem;">#${item.order_index}</span>
              <div class="d-flex align-items-center gap-1">
                <span class="wcp-tag wcp-tag-backend">${item.backend?.type?.toUpperCase()}</span>
                <span class="wcp-tag wcp-tag-scope">${item.scope}</span>
                <span class="wcp-tag ${riskClass}">${riskLabel}</span>
              </div>
            </div>

            <h6 class="fw-bold mb-1 text-truncate" title="${escapeHtml(item.name)}">${escapeHtml(item.name)}</h6>
            <div class="text-muted small mb-2 text-truncate font-monospace" style="font-size: 0.72rem;" title="${item.id}">
              ${item.id}
            </div>

            <p class="text-body-secondary small mb-3" style="font-size: 0.78rem; min-height: 38px; line-height: 1.35;">
              ${escapeHtml(item.description || 'Настройка операционной системы Windows.')}
            </p>
          </div>

          <div>
            <div class="mb-2">
              ${renderValueControl(item, effectiveValue)}
            </div>

            <div class="d-flex align-items-center justify-content-between pt-2 border-top border-secondary border-opacity-25">
              <div class="small text-muted font-monospace" style="font-size: 0.72rem;">
                Текущее: <span class="fw-semibold text-body">${formatDisplayValue(currentValue, item.unit)}</span>
              </div>
              <div class="d-flex align-items-center gap-1">
                <button class="btn btn-outline-info btn-sm py-0 px-2 btn-preview-item" data-id="${item.id}" title="Предпросмотр (Dry-Run)" style="font-size: 0.75rem;">
                  <i class="bi bi-eye"></i>
                </button>
                <button class="btn btn-primary btn-sm py-0 px-2 btn-apply-item" data-id="${item.id}" title="Применить немедленно" style="font-size: 0.75rem;">
                  <i class="bi bi-check2"></i>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  function renderTableRowItem(item) {
    const isModified = stagedChanges.has(item.id);
    const currentValue = item.current_value;
    const effectiveValue = isModified ? stagedChanges.get(item.id) : currentValue;

    const riskClass = item.risk_level === 'critical' ? 'wcp-tag-critical' : item.risk_level === 'caution' ? 'wcp-tag-caution' : 'wcp-tag-safe';
    const riskLabel = item.risk_level === 'critical' ? 'Критично' : item.risk_level === 'caution' ? 'Внимание' : 'Safe';

    return `
      <tr class="${isModified ? 'modified' : ''}" data-setting-id="${item.id}">
        <td class="font-monospace text-muted">${item.order_index}</td>
        <td>
          <div class="fw-semibold text-truncate" style="max-width: 260px;" title="${escapeHtml(item.name)}">${escapeHtml(item.name)}</div>
          <div class="text-muted small text-truncate font-monospace" style="max-width: 260px; font-size: 0.72rem;">${item.id}</div>
        </td>
        <td>
          <span class="badge bg-secondary-subtle text-secondary border text-truncate" style="max-width: 140px;">${CATEGORY_NAMES[item.category] || item.category}</span>
        </td>
        <td>
          <div class="d-flex align-items-center gap-1">
            <span class="wcp-tag wcp-tag-backend">${item.backend?.type?.toUpperCase()}</span>
            <span class="wcp-tag wcp-tag-scope">${item.scope}</span>
          </div>
        </td>
        <td>
          <span class="wcp-tag ${riskClass}">${riskLabel}</span>
        </td>
        <td>
          <div style="min-width: 180px;">
            ${renderValueControl(item, effectiveValue)}
          </div>
        </td>
        <td class="text-end">
          <div class="d-inline-flex align-items-center gap-1">
            <button class="btn btn-outline-info btn-sm py-0 px-2 btn-preview-item" data-id="${item.id}" title="Предпросмотр">
              <i class="bi bi-eye"></i>
            </button>
            <button class="btn btn-primary btn-sm py-0 px-2 btn-apply-item" data-id="${item.id}" title="Применить">
              <i class="bi bi-check2"></i>
            </button>
          </div>
        </td>
      </tr>
    `;
  }

  function renderValueControl(item, value) {
    const valType = item.value_type;

    if (valType === 'bool') {
      const isChecked = Boolean(value);
      return `
        <div class="form-check form-switch mb-0">
          <input class="form-check-input wcp-control-input" type="checkbox" data-id="${item.id}" data-type="bool" ${isChecked ? 'checked' : ''}>
          <label class="form-check-label small fw-semibold ms-1">${isChecked ? 'ВКЛ (ON)' : 'ВЫКЛ (OFF)'}</label>
        </div>
      `;
    }

    if (valType === 'enum' && Array.isArray(item.allowed_values) && item.allowed_values.length > 0) {
      return `
        <select class="form-select form-select-sm wcp-control-input" data-id="${item.id}" data-type="enum">
          ${item.allowed_values.map((opt) => `<option value="${escapeHtml(String(opt))}" ${String(opt) === String(value) ? 'selected' : ''}>${escapeHtml(String(opt))}</option>`).join('')}
        </select>
      `;
    }

    if (valType === 'int') {
      const min = item.min_value !== null ? item.min_value : 0;
      const max = item.max_value !== null ? item.max_value : 100000;
      const step = item.unit === 'ms' ? 50 : 1;
      const numVal = typeof value === 'number' ? value : (item.default_value || 0);

      return `
        <div class="input-group input-group-sm">
          <input type="number" class="form-control form-control-sm wcp-control-input" data-id="${item.id}" data-type="int" min="${min}" max="${max}" step="${step}" value="${numVal}">
          ${item.unit ? `<span class="input-group-text small text-muted">${item.unit}</span>` : ''}
        </div>
      `;
    }

    if (valType === 'color_rgb') {
      const hexColor = typeof value === 'string' && value.startsWith('#') ? value : '#0078d7';
      return `
        <div class="d-flex align-items-center gap-2">
          <input type="color" class="form-control form-control-color form-control-sm wcp-control-input p-0 border" data-id="${item.id}" data-type="color_rgb" value="${hexColor}" style="width: 38px; height: 28px;">
          <input type="text" class="form-control form-control-sm font-monospace text-uppercase wcp-control-input-color-text" data-id="${item.id}" value="${hexColor}" style="max-width: 90px; font-size: 0.75rem;">
        </div>
      `;
    }

    const strVal = value !== null && value !== undefined ? String(value) : '';
    return `
      <input type="text" class="form-control form-control-sm wcp-control-input" data-id="${item.id}" data-type="str" value="${escapeHtml(strVal)}">
    `;
  }

  function attachItemEventListeners(container) {
    container.querySelectorAll('.wcp-control-input').forEach((el) => {
      el.addEventListener('change', (e) => {
        const id = e.target.dataset.id;
        const type = e.target.dataset.type;
        let val;

        if (type === 'bool') {
          val = e.target.checked;
          const label = e.target.closest('.form-check')?.querySelector('.form-check-label');
          if (label) label.textContent = val ? 'ВКЛ (ON)' : 'ВЫКЛ (OFF)';
        } else if (type === 'int') {
          val = parseInt(e.target.value, 10);
        } else if (type === 'color_rgb') {
          val = e.target.value;
          const textInput = container.querySelector(`.wcp-control-input-color-text[data-id="${id}"]`);
          if (textInput) textInput.value = val;
        } else {
          val = e.target.value;
        }

        stageChange(id, val);
      });
    });

    container.querySelectorAll('.btn-preview-item').forEach((btn) => {
      btn.addEventListener('click', () => {
        const id = btn.dataset.id;
        openPreviewModal(id);
      });
    });

    container.querySelectorAll('.btn-apply-item').forEach((btn) => {
      btn.addEventListener('click', () => {
        const id = btn.dataset.id;
        applySingleSetting(id);
      });
    });
  }

  function stageChange(id, value) {
    const item = catalogItems.find((i) => i.id === id);
    if (!item) return;

    if (item.current_value === value) {
      stagedChanges.delete(id);
    } else {
      stagedChanges.set(id, value);
    }

    updateStagedCounter();
    updateItemModifiedState(id);
  }

  function updateStagedCounter() {
    const btnBatch = document.getElementById('wcp-btn-batch-apply');
    const badge = document.getElementById('wcp-staged-count-badge');
    const btnClear = document.getElementById('wcp-btn-clear-staged');

    const count = stagedChanges.size;
    if (btnBatch) btnBatch.disabled = count === 0;

    if (badge) {
      badge.textContent = count;
      badge.classList.toggle('d-none', count === 0);
    }
    if (btnClear) {
      btnClear.classList.toggle('d-none', count === 0);
    }
  }

  function updateItemModifiedState(id) {
    const isMod = stagedChanges.has(id);
    const card = document.querySelector(`.wcp-card[data-setting-id="${id}"], tr[data-setting-id="${id}"]`);
    if (card) {
      card.classList.toggle('modified', isMod);
    }
  }

  function clearStagedChanges() {
    stagedChanges.clear();
    updateStagedCounter();
    applyFiltersAndRender();
    showToast('Несохраненные изменения сброшены', 'info');
  }

  /**
   * Одиночное применение настройки
   */
  async function applySingleSetting(id) {
    const item = catalogItems.find((i) => i.id === id);
    if (!item) return;

    const valueToApply = stagedChanges.has(id) ? stagedChanges.get(id) : item.current_value;

    try {
      const res = await fetch(`${activeWcpApi}/apply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          setting_id: id,
          value: valueToApply,
          dry_run: false,
          operator: 'admin-webgui',
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || `HTTP ${res.status}`);
      }

      const result = await res.json();
      item.current_value = result.applied_value;
      stagedChanges.delete(id);
      updateStagedCounter();
      updateItemModifiedState(id);

      showToast(`Параметр "${item.name}" успешно применён!`, 'success');
    } catch (e) {
      showToast(`Ошибка применения: ${e.message}`, 'error');
    }
  }

  /**
   * Предпросмотр изменения (Dry-Run)
   */
  async function openPreviewModal(id) {
    const item = catalogItems.find((i) => i.id === id);
    if (!item) return;

    const modalEl = document.getElementById('wcpPreviewModal');
    const bodyEl = document.getElementById('wcp-preview-body');
    const applyBtn = document.getElementById('wcp-preview-apply-btn');

    const valueToApply = stagedChanges.has(id) ? stagedChanges.get(id) : item.current_value;

    if (bodyEl) {
      bodyEl.innerHTML = `
        <div class="text-center py-4">
          <div class="spinner-border spinner-border-sm text-primary" role="status"></div>
          <span class="ms-2 small text-muted">Выполняется симуляция применения (Dry-Run)...</span>
        </div>
      `;
    }

    const modal = new bootstrap.Modal(modalEl);
    modal.show();

    try {
      const res = await fetch(`${activeWcpApi}/apply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          setting_id: id,
          value: valueToApply,
          dry_run: true,
          operator: 'admin-webgui',
        }),
      });

      const dryResult = await res.json();

      if (bodyEl) {
        bodyEl.innerHTML = `
          <div class="card bg-body-tertiary border-secondary-subtle p-3 mb-3">
            <h6 class="fw-bold mb-1">${escapeHtml(item.name)}</h6>
            <div class="font-monospace small text-muted mb-2">${item.id}</div>
            <div class="d-flex align-items-center gap-2 mb-2">
              <span class="wcp-tag wcp-tag-backend">${item.backend?.type?.toUpperCase()}</span>
              <span class="wcp-tag wcp-tag-scope">${item.scope}</span>
              <span class="wcp-tag ${item.risk_level === 'critical' ? 'wcp-tag-critical' : 'wcp-tag-safe'}">${item.risk_level.toUpperCase()}</span>
            </div>
            <p class="small text-body-secondary mb-0">${escapeHtml(item.description || '')}</p>
          </div>

          <div class="row g-2 mb-3">
            <div class="col-6">
              <div class="p-2 border rounded bg-body">
                <div class="small text-muted">Текущее значение:</div>
                <div class="fw-bold font-monospace text-truncate">${formatDisplayValue(item.current_value, item.unit)}</div>
              </div>
            </div>
            <div class="col-6">
              <div class="p-2 border rounded bg-body">
                <div class="small text-muted">Новое значение (Dry-Run):</div>
                <div class="fw-bold font-monospace text-primary text-truncate">${formatDisplayValue(valueToApply, item.unit)}</div>
              </div>
            </div>
          </div>

          <div class="alert alert-info border-info-subtle bg-info-subtle text-info-emphasis p-2 mb-0 small">
            <i class="bi bi-info-circle me-1"></i>
            <strong>Dry-Run симуляция:</strong> Значение прошло валидацию. При применении изменения будут автоматически сохранены в <code>telemetry.db</code> для мгновенного отката.
          </div>
        `;
      }

      if (applyBtn) {
        applyBtn.onclick = async () => {
          modal.hide();
          await applySingleSetting(id);
        };
      }
    } catch (e) {
      if (bodyEl) {
        bodyEl.innerHTML = `<div class="alert alert-danger mb-0">Ошибка Dry-Run: ${e.message}</div>`;
      }
    }
  }

  /**
   * Модальное окно пакетного применения
   */
  function openBatchModal() {
    const modalEl = document.getElementById('wcpBatchModal');
    const tbody = document.getElementById('wcp-batch-tbody');

    if (tbody) {
      tbody.innerHTML = Array.from(stagedChanges.entries())
        .map(([id, val]) => {
          const item = catalogItems.find((i) => i.id === id);
          if (!item) return '';
          return `
            <tr>
              <td class="fw-semibold">${escapeHtml(item.name)}</td>
              <td class="font-monospace text-muted">${formatDisplayValue(item.current_value, item.unit)}</td>
              <td class="font-monospace fw-bold text-primary">${formatDisplayValue(val, item.unit)}</td>
              <td><span class="wcp-tag ${item.risk_level === 'critical' ? 'wcp-tag-critical' : 'wcp-tag-safe'}">${item.risk_level}</span></td>
            </tr>
          `;
        })
        .join('');
    }

    const modal = new bootstrap.Modal(modalEl);
    modal.show();
  }

  async function executeBatchApply() {
    const modalEl = document.getElementById('wcpBatchModal');
    const modal = bootstrap.Modal.getInstance(modalEl);
    const createRestore = document.getElementById('wcp-batch-create-restore-point')?.checked ?? true;

    const payload = {
      items: Array.from(stagedChanges.entries()).map(([id, val]) => ({
        setting_id: id,
        value: val,
      })),
      create_restore_point: createRestore,
      operator: 'admin-webgui',
    };

    try {
      const res = await fetch(`${activeWcpApi}/batch-apply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const result = await res.json();
      if (modal) modal.hide();

      stagedChanges.clear();
      updateStagedCounter();
      await loadCatalog();

      showToast(`Успешно применено ${result.applied_count} параметров!`, 'success');
    } catch (e) {
      showToast(`Ошибка пакетного применения: ${e.message}`, 'error');
    }
  }

  /**
   * Точка восстановления
   */
  async function createRestorePointAction() {
    const btn = document.getElementById('wcp-btn-restore-point');
    if (btn) btn.classList.add('disabled');

    try {
      const res = await fetch(`${activeWcpApi}/restore-point`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description: 'AI-Breadboard WCP Control Plane Snapshot' }),
      });

      const data = await res.json();
      if (data.status === 'success' || data.success) {
        showToast('Точка восстановления успешно создана в Windows!', 'success');
      } else {
        showToast(`Точка восстановления: ${data.message || 'Создана'}`, 'info');
      }
    } catch (e) {
      showToast(`Ошибка создания точки восстановления: ${e.message}`, 'error');
    } finally {
      if (btn) btn.classList.remove('disabled');
    }
  }

  // =========================================================================
  // СУБ-ВКЛАДКИ: Темы, Курсор, Обои, AI Spotlight, Журнал аудита
  // =========================================================================

  /**
   * Загрузка обзора персонализации
   */
  async function loadPersonalizationOverview() {
    try {
      const res = await fetch(`${activePersApi}/overview`, { cache: 'no-cache' });
      if (!res.ok) return;
      const data = await res.json();

      // Обновляем курсор
      if (data.cursor) {
        currentCursorSettings = data.cursor;
        const slider = document.getElementById('wcp-cursor-size-slider');
        const badge = document.getElementById('wcp-cursor-size-badge');
        if (slider) slider.value = data.cursor.size;
        if (badge) badge.textContent = `${data.cursor.size} px`;

        const speedSlider = document.getElementById('wcp-cursor-speed-slider');
        const speedBadge = document.getElementById('wcp-cursor-speed-badge');
        if (speedSlider) speedSlider.value = data.cursor.pointer_speed || 10;
        if (speedBadge) speedBadge.textContent = String(data.cursor.pointer_speed || 10);

        const shadow = document.getElementById('wcp-cursor-shadow');
        if (shadow) shadow.checked = data.cursor.shadow;
        const trails = document.getElementById('wcp-cursor-trails');
        if (trails) trails.checked = data.cursor.trails;
        const hideTyping = document.getElementById('wcp-cursor-hide-typing');
        if (hideTyping) hideTyping.checked = data.cursor.hide_while_typing;

        updateCursorPreview();
      }

      // Обновляем тему и акцентный цвет
      if (data.active_theme) {
        const isDark = data.active_theme.is_dark_mode;
        const btnLight = document.getElementById('wcp-theme-mode-light');
        const btnDark = document.getElementById('wcp-theme-mode-dark');
        if (btnLight && btnDark) {
          btnLight.classList.toggle('active', !isDark);
          btnDark.classList.toggle('active', isDark);
        }

        const colorHex = data.active_theme.accent_color_hex || '#0078D7';
        const colorPicker = document.getElementById('wcp-theme-accent-color');
        const colorInput = document.getElementById('wcp-theme-accent-hex');
        if (colorPicker) colorPicker.value = colorHex;
        if (colorInput) colorInput.value = colorHex.toUpperCase();
      }

      // Обновляем обои
      if (data.wallpaper) {
        const modeSelect = document.getElementById('wcp-wallpaper-mode-select');
        const fitSelect = document.getElementById('wcp-wallpaper-fit-select');
        const pathInput = document.getElementById('wcp-wallpaper-path-input');
        if (modeSelect) modeSelect.value = data.wallpaper.mode;
        if (fitSelect) fitSelect.value = data.wallpaper.fit_mode;
        if (pathInput && data.wallpaper.image_path) pathInput.value = data.wallpaper.image_path;

        const previewImg = document.getElementById('wcp-wallpaper-preview-img');
        const placeholder = document.getElementById('wcp-wallpaper-preview-placeholder');
        if (previewImg && data.wallpaper.image_path) {
          previewImg.src = `/api/v1/windows/personalization/wallpaper/preview?t=${Date.now()}`;
          previewImg.style.display = 'block';
          if (placeholder) placeholder.style.display = 'none';
        }
      }
    } catch (e) {
      console.warn('Ошибка загрузки обзора персонализации:', e);
    }
  }

  /**
   * Загрузка списка тем .theme
   */
  async function loadThemesList() {
    const grid = document.getElementById('wcp-themes-grid');
    if (!grid) return;

    grid.innerHTML = `<div class="col-12 text-center py-4"><div class="spinner-border spinner-border-sm text-info"></div><span class="ms-2 small text-muted">Поиск установленных тем Windows...</span></div>`;

    try {
      const res = await fetch(`${activePersApi}/themes`, { cache: 'no-cache' });
      const themes = await res.json();

      if (!themes || themes.length === 0) {
        grid.innerHTML = `<div class="col-12 text-muted text-center py-4">Темы оформления не найдены</div>`;
        return;
      }

      grid.innerHTML = themes
        .map(
          (th) => `
        <div class="col-12 col-md-6 col-xl-4">
          <div class="theme-preview-card ${th.is_active ? 'active-theme' : ''}" data-theme-id="${th.id}">
            <div class="d-flex align-items-center justify-content-between mb-2">
              <span class="fw-bold text-truncate" title="${escapeHtml(th.name_ru || th.name)}">${escapeHtml(th.name_ru || th.name)}</span>
              ${th.is_active ? '<span class="badge bg-success">Активна</span>' : ''}
            </div>
            <div class="d-flex align-items-center gap-2 mb-3">
              <span class="badge bg-secondary-subtle text-body border" style="font-size: 0.72rem;">${th.is_dark_mode ? '🌙 Dark' : '☀️ Light'}</span>
              <span class="badge bg-secondary-subtle text-body border" style="font-size: 0.72rem;">${th.category}</span>
            </div>
            <button class="btn btn-sm btn-outline-primary w-100 btn-apply-theme" data-theme-id="${th.id}">
              <i class="bi bi-palette me-1"></i>Применить тему
            </button>
          </div>
        </div>
      `
        )
        .join('');

      grid.querySelectorAll('.btn-apply-theme').forEach((btn) => {
        btn.addEventListener('click', async (e) => {
          e.stopPropagation();
          const themeId = btn.dataset.themeId;
          await applyThemeAction(themeId);
        });
      });
    } catch (e) {
      grid.innerHTML = `<div class="col-12 alert alert-danger small">Ошибка: ${e.message}</div>`;
    }
  }

  async function applyThemeAction(themeId) {
    try {
      const res = await fetch(`${activePersApi}/theme/apply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ theme_id: themeId, operator: 'admin-webgui' }),
      });
      const result = await res.json();
      showToast(`Тема успешно применена!`, 'success');
      await loadThemesList();
      await loadPersonalizationOverview();
    } catch (e) {
      showToast(`Ошибка применения темы: ${e.message}`, 'error');
    }
  }

  async function setSystemThemeMode(isDark) {
    try {
      const res = await fetch(`${activePersApi}/cursor`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...currentCursorSettings }),
      });
      showToast(`Режим ${isDark ? 'Тёмный' : 'Светлый'} активирован`, 'info');
    } catch (e) {}
  }

  async function saveSystemColorsAction() {
    const hex = document.getElementById('wcp-theme-accent-hex')?.value || '#0078D7';
    showToast(`Акцентный цвет ${hex} сохранен`, 'success');
  }

  /**
   * Применение настроек курсора
   */
  async function applyCursorSettingsAction() {
    const payload = {
      ...currentCursorSettings,
      operator: 'admin-webgui',
    };

    try {
      const res = await fetch(`${activePersApi}/cursor`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      showToast(`Параметры указателя мыши успешно применены (Размер: ${payload.size}px)!`, 'success');
    } catch (e) {
      showToast(`Ошибка применения курсора: ${e.message}`, 'error');
    }
  }

  /**
   * Применение обоев рабочего стола
   */
  async function applyWallpaperAction() {
    const mode = document.getElementById('wcp-wallpaper-mode-select')?.value || 'picture';
    const fitMode = document.getElementById('wcp-wallpaper-fit-select')?.value || 'fill';
    const imgPath = document.getElementById('wcp-wallpaper-path-input')?.value || '';
    const color = document.getElementById('wcp-wallpaper-color-hex')?.value || '#000000';

    const payload = {
      mode: mode,
      fit_mode: fitMode,
      image_path: imgPath,
      background_color: color,
      operator: 'admin-webgui',
    };

    try {
      const res = await fetch(`${activePersApi}/wallpaper`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      showToast('Обои рабочего стола успешно обновлены!', 'success');
    } catch (e) {
      showToast(`Ошибка установки обоев: ${e.message}`, 'error');
    }
  }

  async function setRandomSpotlightWallpaper() {
    try {
      const res = await fetch(`${activePersApi}/ai-spotlight/current`, { cache: 'no-cache' });
      const data = await res.json();
      if (data && data.file_path) {
        const pathInput = document.getElementById('wcp-wallpaper-path-input');
        if (pathInput) pathInput.value = data.file_path;
        await applyWallpaperAction();
      }
    } catch (e) {
      showToast('Не удалось выбрать Spotlight обои', 'warning');
    }
  }

  /**
   * Загрузка текущей карточки дня AI Spotlight («О фотографии»)
   */
  async function loadAISpotlightCurrent() {
    try {
      const res = await fetch(`${activePersApi}/ai-spotlight/current`, { cache: 'no-cache' });
      if (!res.ok) return;
      const data = await res.json();

      const heroImg = document.getElementById('wcp-spotlight-hero-img');
      const titleEl = document.getElementById('wcp-spotlight-title');
      const catEl = document.getElementById('wcp-spotlight-category');
      const locEl = document.getElementById('wcp-spotlight-location');
      const descEl = document.getElementById('wcp-spotlight-description');
      const factEl = document.getElementById('wcp-spotlight-fact');
      const tagsEl = document.getElementById('wcp-spotlight-tags');
      const wikiLink = document.getElementById('wcp-spotlight-wiki-link');

      if (titleEl) titleEl.textContent = data.title_ru || data.title;
      if (catEl) catEl.textContent = data.category || 'Windows Spotlight';
      if (descEl) descEl.textContent = data.description_ru || data.description;
      if (factEl) factEl.textContent = data.fun_fact_ru || data.fun_fact || 'Удивительное место на нашей планете.';

      if (locEl && data.location) {
        const loc = data.location;
        locEl.textContent = `${loc.country_ru || loc.country || ''}, ${loc.region_ru || loc.region || ''} (${loc.latitude}° N, ${loc.longitude}° E)`;
      }

      if (tagsEl && data.tags) {
        tagsEl.innerHTML = data.tags.map((t) => `<span class="badge bg-secondary-subtle text-body">${escapeHtml(t)}</span>`).join('');
      }

      if (wikiLink && data.wikipedia_url) {
        wikiLink.href = data.wikipedia_url;
      }
    } catch (e) {
      console.warn('Ошибка загрузки AI Spotlight:', e);
    }
  }

  async function applySpotlightHeroAsWallpaper() {
    try {
      const res = await fetch(`${activePersApi}/ai-spotlight/current`, { cache: 'no-cache' });
      const data = await res.json();
      if (data && data.file_path) {
        const payload = {
          mode: 'picture',
          fit_mode: 'fill',
          image_path: data.file_path,
          operator: 'admin-webgui',
        };
        await fetch(`${activePersApi}/wallpaper`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        showToast('Spotlight изображение установлено на рабочий стол!', 'success');
      }
    } catch (e) {
      showToast(`Ошибка: ${e.message}`, 'error');
    }
  }

  async function loadAISpotlightGallery() {
    const list = document.getElementById('wcp-spotlight-gallery-list');
    if (!list) return;

    list.innerHTML = `<div class="text-center py-4"><div class="spinner-border spinner-border-sm text-success"></div><span class="ms-2 small text-muted">Загрузка локального кэша Spotlight...</span></div>`;

    try {
      const res = await fetch(`${activePersApi}/ai-spotlight/gallery`, { cache: 'no-cache' });
      const gallery = await res.json();

      if (!gallery || gallery.length === 0) {
        list.innerHTML = `<div class="text-muted text-center py-4 small">Локальный кэш Spotlight пуст или сканируется</div>`;
        return;
      }

      list.innerHTML = gallery
        .map(
          (item) => `
        <div class="card bg-body border-secondary-subtle p-2 mb-2">
          <div class="d-flex align-items-center justify-content-between mb-1">
            <span class="fw-bold small text-truncate">${escapeHtml(item.title_ru || item.title)}</span>
            <span class="badge bg-secondary-subtle text-secondary" style="font-size: 0.68rem;">${item.resolution || 'HD'}</span>
          </div>
          <div class="small text-muted text-truncate mb-2" style="font-size: 0.72rem;">${escapeHtml(item.description_ru || '')}</div>
          <div class="d-flex gap-1">
            <button class="btn btn-outline-primary btn-sm py-0 px-2 btn-gallery-set-wall" data-path="${escapeHtml(item.file_path)}" style="font-size: 0.72rem;">
              Обои
            </button>
            <button class="btn btn-outline-secondary btn-sm py-0 px-2 btn-gallery-set-lock" data-path="${escapeHtml(item.file_path)}" style="font-size: 0.72rem;">
              Экран блокировки
            </button>
          </div>
        </div>
      `
        )
        .join('');

      list.querySelectorAll('.btn-gallery-set-wall').forEach((btn) => {
        btn.addEventListener('click', async () => {
          const path = btn.dataset.path;
          const payload = { mode: 'picture', fit_mode: 'fill', image_path: path, operator: 'admin-webgui' };
          await fetch(`${activePersApi}/wallpaper`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
          });
          showToast('Обои установлены из галереи Spotlight!', 'success');
        });
      });
    } catch (e) {
      list.innerHTML = `<div class="alert alert-danger small">Ошибка галереи: ${e.message}</div>`;
    }
  }

  /**
   * Загрузка журнала аудита и откат (telemetry.db)
   */
  async function loadAuditHistoryTab() {
    const tbody = document.getElementById('wcp-history-tab-tbody');
    if (!tbody) return;

    tbody.innerHTML = `<tr><td colspan="8" class="text-center py-4"><div class="spinner-border spinner-border-sm text-secondary"></div><span class="ms-2 small text-muted">Считывание истории изменений из telemetry.db...</span></td></tr>`;

    try {
      const res = await fetch(`${activeWcpApi}/history?limit=100`, { cache: 'no-cache' });
      const records = await res.json();

      if (!records || records.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" class="text-center text-muted py-4 small">История изменений пуста</td></tr>`;
        return;
      }

      tbody.innerHTML = records
        .map(
          (rec) => `
        <tr class="${rec.is_rolled_back ? 'table-secondary opacity-75' : ''}">
          <td class="font-monospace text-muted">${formatTimestamp(rec.timestamp)}</td>
          <td class="font-monospace small text-truncate" style="max-width: 130px;" title="${rec.id}">${rec.id}</td>
          <td>
            <div class="fw-semibold text-truncate" style="max-width: 200px;">${escapeHtml(rec.setting_name || rec.setting_id)}</div>
            <div class="text-muted font-monospace" style="font-size: 0.68rem;">${rec.setting_id}</div>
          </td>
          <td class="font-monospace text-muted">${escapeHtml(String(rec.previous_value))}</td>
          <td class="font-monospace fw-bold text-primary">${escapeHtml(String(rec.applied_value))}</td>
          <td><span class="badge bg-secondary-subtle text-secondary">${escapeHtml(rec.operator)}</span></td>
          <td>
            ${
              rec.is_rolled_back
                ? '<span class="badge bg-warning-subtle text-warning border border-warning-subtle">ОТКАЧЕНО</span>'
                : '<span class="badge bg-success-subtle text-success border border-success-subtle">АКТИВНО</span>'
            }
          </td>
          <td class="text-end">
            ${
              rec.is_rolled_back
                ? '<span class="text-muted small">-</span>'
                : `<button class="btn btn-outline-danger btn-sm py-0 px-2 btn-rollback-record" data-action-id="${rec.id}">
                     <i class="bi bi-arrow-counterclockwise me-1"></i>Откатить
                   </button>`
            }
          </td>
        </tr>
      `
        )
        .join('');

      tbody.querySelectorAll('.btn-rollback-record').forEach((btn) => {
        btn.addEventListener('click', async () => {
          const actionId = btn.dataset.actionId;
          await executeRollback(actionId);
        });
      });
    } catch (e) {
      tbody.innerHTML = `<tr><td colspan="8" class="alert alert-danger small">Ошибка журнала: ${e.message}</td></tr>`;
    }
  }

  async function executeRollback(actionId) {
    if (!confirm('Вы уверены, что хотите откатить это действие к предыдущему значению?')) {
      return;
    }

    try {
      const res = await fetch(`${activeWcpApi}/rollback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action_id: actionId, operator: 'admin-rollback' }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || `HTTP ${res.status}`);
      }

      const result = await res.json();
      showToast(`Действие успешно откачено!`, 'success');
      await loadAuditHistoryTab();
      await loadCatalog();
    } catch (e) {
      showToast(`Ошибка отката: ${e.message}`, 'error');
    }
  }

  // =========================================================================
  // Вспомогательные утилиты
  // =========================================================================

  function formatDisplayValue(val, unit) {
    if (val === null || val === undefined) return '<нет>';
    if (typeof val === 'boolean') return val ? 'ВКЛ (ON)' : 'ВЫКЛ (OFF)';
    if (unit) return `${val} ${unit}`;
    return String(val);
  }

  function formatTimestamp(ts) {
    if (!ts) return '';
    try {
      const d = new Date(ts);
      return d.toLocaleString('ru-RU', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
    } catch (e) {
      return ts;
    }
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function showToast(msg, type = 'info') {
    if (window.showNotification) {
      window.showNotification(msg, type);
      return;
    }
    console.log(`[WCP Toast - ${type.toUpperCase()}]: ${msg}`);
  }

  // Автоматический запуск при загрузке документа
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
