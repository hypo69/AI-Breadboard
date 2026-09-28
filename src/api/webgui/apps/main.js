/**
 * apps/main.js — оркестратор страницы /tc (tc.ps1)
 * Архитектура: UI_ARCHITECTURE.md
 */

import { setupGlobalApi, setupThemeAndLang } from './modules/init-interface.js';
import { fetchAppsStatus, updateModelDropdown } from './modules/status-manager.js';
import { APP_TAB_DEFS } from './modules/tabs-config.js';
import { applyTranslations } from '../js/i18n.js';
import { switchTab, loadTab, setupTabClicks } from '../js/tab-core.jsi18n.t('auto__window_switchtab_switchtab_window_switchtotab_switchtab_tabid_tabs_config_const_tab_paths_object_fromentries_app_tab_defs_map_d_d_tabid_html_d_html_js_d_js_lazy_const_loadedtabs_new_set_async_function_lazyload_tabid_const_normid_tabid_startswith__c88127')tab-') ? tabId : `tab-${tabId}`;
  if (loadedTabs.has(normId)) return;
  const paths = TAB_PATHS[normId];
  if (!paths) return;
  loadedTabs.add(normId);
  const v = Date.now();
  const name = normId.replace(/^tab-/, '');
  await loadTab(name, `${paths.html}?v=${v}`, `${paths.js}?v=${v}`);
  applyTranslations();
}

const _switchTab = switchTab;
export async function switchAppTab(tabId) {
  if (!tabId) return;
  const normId = tabId.startsWith('tab-i18n.t('auto__tabid_tab_tabid_await_lazyload_normid_switchtab_normid_window_switchtab_switchapptab_window_switchtotab_switchapptab_dom_bi_svg_param_string_iconstr_param_string_defaulticon_returns_htmlelement_export_function_createiconelement_iconstr_defaulticon__90a1c8')📄') {
  const icon = (iconStr || defaultIcon).trim();
  if (/^bi-[a-z0-9-]+$/.test(icon) || icon.startsWith('bi-') || icon.startsWith('bi ')) {
    const i = document.createElement('i');
    const iconClass = icon.startsWith('bi ') ? icon : `bi ${icon}`;
    i.className = iconClass;
    return i;
  }
  if (icon.startsWith('<svg') || icon.startsWith('<i ')) {
    const span = document.createElement('span');
    span.innerHTML = icon;
    return span;
  }
  const span = document.createElement('spani18n.t('auto__span_textcontent_icon_return_span_r_studio_param_object_item_param_htmlelement_iconel_async_function_executelaunchitem_item_iconel_null_const_origcontent_iconel_iconel_innerhtml__4bf198')';
  if (iconEl) iconEl.innerHTML = '⏳';
  try {
    const res = await fetch('/api/recovery/launch', { method: 'POST' });
    const data = await res.json();
    if (res.ok && data.success) {
      if (window.toast) {
        window.toast.success(i18n.t('auto_r_studio__de553b'), data.message || i18n.t('auto___4f0b2d'));
      }
    } else {
      if (window.toast) {
        window.toast.error(i18n.t('auto___ee6366'), data.detail || i18n.t('auto___f2a964'));
      }
    }
  } catch (err) {
    if (window.toast) {
      window.toast.error(i18n.t('auto___6105a2'), err.message);
    }
  } finally {
    if (iconEl) iconEl.innerHTML = origContent;
  }
}

function getMenuTarget() {
  const p = location.pathname.toLowerCase();
  if (p.startsWith('/su') || location.search.includes('target=su')) {
    return 'su';
  }
  return 'tci18n.t('auto__async_function_buildmenu_appsmap_customcfg_null_let_cfg_customcfg_const_target_getmenutarget_if_cfg_try_const_r_await_fetch_api_menu_config_target_target_t_date_now_if_r_ok_cfg_await_r_json_catch_e_console_warn_api_menu_config_target_target_e_if_cfg_try_const_staticfile_target__ff7f92')su' ? 'su_menu_config.json' : 'tc_menu_config.json';
      const r = await fetch(`/html/config_menues/${staticFile}?t=${Date.now()}`);
      if (r.ok) {
        cfg = await r.json();
      }
    } catch (e) {
      console.error(i18n.t('auto___a46a03'), e);
    }
  }

  if (!cfg || !cfg.menu) return null;

  const enabled = item => appsMap[item.id]?.enabled !== false;
  const sorted = arr => [...arr]
    .filter(x => x.visible !== false && enabled(x))
    .sort((a, b) => (a.order || 0) - (b.order || 0));

  // Верхнее меню
  const topEl = document.querySelector('.main-nav-container .d-flex.gap-1.flex-wrap');
  if (topEl) {
    topEl.innerHTML = '';
    sorted(cfg.menu.topButtons || []).forEach(item => {
      const btn = document.createElement('button');
      btn.className = 'btn btn-sm btn-outline-primary d-flex align-items-center gap-1.5 py-1 px-2 rounded';
      btn.type = 'button';
      btn.title = item.label;

      const iconEl = createIconElement(item.icon, 'bi-app');
      const labelSpan = document.createElement('span');
      labelSpan.className = 'd-none d-sm-inline';
      labelSpan.textContent = item.label;
      if (item.i18n) labelSpan.dataset.i18n = item.i18n;

      btn.append(iconEl, labelSpan);

      if (item.id === 'file_recovery' || item.action === 'launch') {
        btn.dataset.action = 'launchi18n.t('auto__btn_onclick_async_e_e_preventdefault_e_stoppropagation_await_executelaunchitem_item_iconel_else_btn_dataset_tab_item_tab_topel_appendchild_btn_const_navel_document_getelementbyid__0e57a6')appsNavTabs');
  if (navEl) {
    navEl.innerHTML = '';
    sorted(cfg.menu.sidebarItems || []).forEach(item => {
      const btn = document.createElement('button');
      btn.className = 'list-group-item list-group-item-action d-flex align-items-center gap-2 py-2 px-3';
      btn.type = 'button';

      const iconEl = createIconElement(item.icon, '📄');
      iconEl.classList.add('fs-6');
      const label = document.createElement('span');
      label.className = 'fw-medium';
      label.textContent = item.label;
      if (item.i18n) label.dataset.i18n = item.i18n;

      btn.append(iconEl, label);

      if (item.id === 'file_recovery' || item.action === 'launch') {
        btn.dataset.action = 'launch';
        btn.title = i18n.t('auto__r_studio__d641cc');
        btn.onclick = async (e) => {
          e.preventDefault();
          e.stopPropagation();
          await executeLaunchItem(item, iconEl);
        };
      } else {
        btn.dataset.tab = item.tab;
      }

      navEl.appendChild(btn);
    });
  }

  // Обновление активного состояния кнопок вкладок
  const activePane = document.querySelector('#mainTabContent .tab-pane.active') || document.querySelector('.tab-pane.active');
  const activeTabId = activePane ? activePane.id : null;
  if (activeTabId) {
    document.querySelectorAll('[data-tab]').forEach(btn => {
      btn.classList.toggle('activei18n.t('auto__btn_dataset_tab_activetabid_applytranslations_return_cfg_export_async_function_loadrequiredtabs_tabs_for_const_tab_of_tabs_await_lazyload_tab_function_initmenueditor_cfg_appsmap_const_editorbtn_document_getelementbyid__b8895b')menu-editor-btn');
  const modal = document.getElementById('menuEditorModal');
  const list = document.getElementById('allMenuEditor');
  const saveBtn = document.getElementById('saveMenuConfig');
  if (!editorBtn || !modal || !list || !cfg) return;

  let currentItems = [];
  let draggedIdx = null;

  function collectInitialItems() {
    const knownIds = new Set();
    const items = [];

    (cfg.menu.topButtons || []).forEach(x => {
      knownIds.add(x.id);
      items.push({ ...x, position: x.visible === false ? 'hidden' : 'top' });
    });

    (cfg.menu.sidebarItems || []).forEach(x => {
      if (!knownIds.has(x.id)) {
        knownIds.add(x.id);
        items.push({ ...x, position: x.visible === false ? 'hidden' : 'bottomi18n.t('auto__app_tab_defs_hidden_app_tab_defs_foreach_def_if_knownids_has_def_id_items_push_id_def_id_label_def_label_def_id_replace_g__4bcb79') ').replace(/\b\w/g, c => c.toUpperCase()),
          icon: def.icon || 'bi-app',
          tab: def.tabId || `tab-${def.tab}`,
          order: items.length + 1,
          visible: false,
          position: 'hidden'
        });
        knownIds.add(def.id);
      }
    });

    return items;
  }

  function renderList() {
    list.innerHTML = '';
    const total = currentItems.length;

    currentItems.forEach((item, idx) => {
      const safeId = (item.id || `item_${idx}`).replace(/[^a-zA-Z0-9_-]/g, '');
      const div = document.createElement('div');
      div.className = 'menu-editor-item d-flex align-items-center gap-2 p-2 mb-2 rounded border border-secondary-subtlei18n.t('auto__div_dataset_id_item_id_div_dataset_index_idx_div_draggable_true_1_drag_handle_const_draghandle_document_createelement__b0b9cc')div');
      dragHandle.className = 'drag-handle-container text-muted px-1';
      dragHandle.title = i18n.t('auto___350d14');
      dragHandle.innerHTML = '<i class="bi bi-grip-vertical fs-5"></i>i18n.t('auto__2_const_orderbadge_document_createelement__6357e6')span');
      orderBadge.className = 'badge bg-secondary-subtle text-light border px-2 py-1';
      orderBadge.textContent = `#${idx + 1}`;
      orderBadge.style.minWidth = '38px';
      orderBadge.style.textAlign = 'centeri18n.t('auto__3_const_iconcontainer_document_createelement__3c7154')div');
      iconContainer.className = 'item-icon d-flex align-items-center justify-content-center px-1 text-center';
      iconContainer.style.minWidth = '30px';
      const iconEl = createIconElement(item.icon, '📄i18n.t('auto__iconcontainer_appendchild_iconel_4_const_info_document_createelement__7effef')div');
      info.className = 'item-info flex-grow-1 min-w-0 px-1';
      const labelDiv = document.createElement('div');
      labelDiv.className = 'fw-semibold text-truncate small';
      labelDiv.textContent = item.label;
      const tabDiv = document.createElement('div');
      tabDiv.className = 'text-muted text-truncate font-monospace';
      tabDiv.style.fontSize = '0.75remi18n.t('auto__tabdiv_textcontent_item_tab_info_append_labeldiv_tabdiv_4_const_orderctrl_document_createelement__8df1ca')div');
      orderCtrl.className = 'd-flex align-items-center gap-1 me-2';
      orderCtrl.style.width = '160px';
      orderCtrl.style.flexShrink = '0';

      const btnUp = document.createElement('button');
      btnUp.type = 'button';
      btnUp.className = 'btn btn-sm btn-outline-secondary p-0 px-1';
      btnUp.title = i18n.t('auto___0d3983');
      btnUp.disabled = idx === 0;
      btnUp.innerHTML = '<i class="bi bi-chevron-up"></i>';
      btnUp.addEventListener('click', () => {
        if (idx > 0) {
          const [moved] = currentItems.splice(idx, 1);
          currentItems.splice(idx - 1, 0, moved);
          renderList();
        }
      });

      const slider = document.createElement('input');
      slider.type = 'range';
      slider.className = 'form-range order-slider flex-grow-1 m-0';
      slider.min = '1i18n.t('auto__slider_max_string_total_slider_value_string_idx_1_slider_title_idx_1_total_slider_addeventlistener__daa3fc')input', (e) => {
        const targetIdx = parseInt(e.target.value, 10) - 1;
        if (targetIdx !== idx && targetIdx >= 0 && targetIdx < total) {
          const [moved] = currentItems.splice(idx, 1);
          currentItems.splice(targetIdx, 0, moved);
          renderList();
        }
      });

      const btnDown = document.createElement('button');
      btnDown.type = 'button';
      btnDown.className = 'btn btn-sm btn-outline-secondary p-0 px-1';
      btnDown.title = i18n.t('auto___750140');
      btnDown.disabled = idx === total - 1;
      btnDown.innerHTML = '<i class="bi bi-chevron-down"></i>';
      btnDown.addEventListener('clicki18n.t('auto__if_idx_total_1_const_moved_currentitems_splice_idx_1_currentitems_splice_idx_1_0_moved_renderlist_orderctrl_append_btnup_slider_btndown_5_const_group_document_createelement__65ee40')div');
      group.className = 'btn-group btn-group-sm flex-shrink-0';
      group.setAttribute('role', 'group');

      [['top', i18n.t('auto___aa6b22'), 'btn-outline-primary'], ['bottom', i18n.t('auto___4af253'), 'btn-outline-secondary'], ['hidden', i18n.t('auto___107291'), 'btn-outline-danger']]
        .forEach(([val, text, cls]) => {
          const inp = document.createElement('input');
          inp.type = 'radio'; inp.className = 'btn-check';
          inp.name = `pos-${safeId}`; inp.id = `pos-${val}-${safeId}`; inp.value = val;
          inp.checked = item.position === val;
          inp.addEventListener('change', () => {
            item.position = val;
            item.visible = val !== 'hidden';
          });
          const lbl = document.createElement('label');
          lbl.className = `btn ${cls}`; lbl.setAttribute('fori18n.t('auto__inp_id_lbl_textcontent_text_group_append_inp_lbl_6_drag_drop_div_addeventlistener__c7dd07')dragstart', (e) => {
        draggedIdx = idx;
        div.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', String(idx));
      });

      div.addEventListener('dragend', () => {
        div.classList.remove('dragging');
        document.querySelectorAll('.menu-editor-item').forEach(el => el.classList.remove('drag-over'));
      });

      div.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        div.classList.add('drag-over');
      });

      div.addEventListener('dragleave', () => {
        div.classList.remove('drag-over');
      });

      div.addEventListener('drop', (e) => {
        e.preventDefault();
        div.classList.remove('drag-over');
        if (draggedIdx !== null && draggedIdx !== idx) {
          const [moved] = currentItems.splice(draggedIdx, 1);
          currentItems.splice(idx, 0, moved);
          draggedIdx = null;
          renderList();
        }
      });

      div.append(dragHandle, orderBadge, info, orderCtrl, group);
      list.appendChild(div);
    });

    return currentItems;
  }

  editorBtn.addEventListener('click', () => {
    currentItems = collectInitialItems();
    renderList();
    new bootstrap.Modal(modal).show();
  });

  saveBtn.addEventListener('click', async () => {
    cfg.menu.topButtons = currentItems
      .filter(x => x.position === 'top')
      .map(({ position, ...x }, idx) => ({ ...x, visible: true, order: idx + 1 }));

    cfg.menu.sidebarItems = currentItems
      .filter(x => x.position !== 'top')
      .map(({ position, ...x }, idx) => ({ ...x, visible: position === 'bottom', order: idx + 1 }));

    try {
      const target = getMenuTarget();
      const r = await fetch(`/api/menu/config?target=${target}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/jsoni18n.t('auto__body_json_stringify_cfg_if_r_ok_throw_new_error_r_statustext_http_r_status_await_buildmenu_appsmap_cfg_const_modalinstance_bootstrap_modal_getinstance_modal_if_modalinstance_modalinstance_hide_const_currenttabel_document_queryselector__9e9ed1').tab-pane.active');
      const activeTabId = currentTabEl ? currentTabEl.id : '';
      const isStillInMenu = document.querySelector(`[data-tab="${activeTabId}"]`);
      if (!isStillInMenu) {
        const firstVisible = document.querySelector('[data-tab]');
        if (firstVisible?.dataset.tab) {
          await switchAppTab(firstVisible.dataset.tab);
        }
      }
    } catch (e) {
      window.showToast?.(i18n.t('auto___c2d2a7') + e.message, 'danger') || alert(i18n.t('auto___c2d2a7') + e.message);
    }
  });
}

// ── INIT ─────────────────────────────────────────────────────────────────────

async function init() {
  setupGlobalApi();
  await setupThemeAndLang();

  if (location.pathname.startsWith('/tc'))
    document.title = 'AI Breadboard — Test Computer (/tc)i18n.t('auto__setuptabclicks_const_statusdata_await_fetchappsstatus_window_appsstatusmap_statusdata_apps_await_updatemodeldropdown_const_appsmap_statusdata_apps_const_cfg_await_buildmenu_appsmap_catch_null_initmenueditor_cfg_appsmap_applytranslations_hash_defaulttab_const_hash_location_hash_replace__218760')#', '');
  const defaultTab = cfg?.settings?.defaultTab;
  const first = document.querySelector('#appsNavTabs [data-tab]') || document.querySelector('[data-tab]');
  const initialTab = hash || (defaultTab && document.querySelector(`[data-tab="${defaultTab}"]`) ? defaultTab : first?.dataset.tab || 'tab-chat');
  await switchAppTab(initialTab);
}

document.readyState === 'loading'
  ? document.addEventListener('DOMContentLoaded', init)
  : init();
