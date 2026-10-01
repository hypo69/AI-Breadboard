/**
 * =============================================================================
 * Process Name: AI-Breadboard UI - Main Script
 * =============================================================================
 * Description:
 *   Клиентский веб-скрипт модуля main.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/src/api/webgui/sources/main.js?v=20261001_v1" type="module"></script>
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: src/api/webgui/sources
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-01 13:13:56
 * =============================================================================
 */

/**
 * sources_tab/main.js
 * Логика вкладки редактирования источников.
 */

let currentSourcesObj = {};

async function loadSourcesRaw() {
    const editor = document.getElementById('sources-json-editor');
    const tbody = document.getElementById('sources-list-body');
    
    if (editor) {
        editor.disabled = true;
        editor.value = i18n.t('auto___a90ed3');
    }
    if (tbody) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-muted">Загрузка источников...</td></tr>';
    }

    try {
        const response = await window.api.fetch('/api/admin/sources/raw');
        const rawContent = response.content || '{}';
        
        if (editor) editor.value = rawContent;
        
        try {
            currentSourcesObj = JSON.parse(rawContent);
            renderSourcesTable();
        } catch (e) {
            console.error(i18n.t('auto__json__3ea759'), e);
            if (tbody) {
                tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-danger">Ошибка формата JSON. Таблица недоступна.</td></tr>';
            }
        }
        
    } catch (err) {
        console.error(i18n.t('auto___3e0a7f'), err);
        if (editor) editor.value = i18n.t('auto__n_d7b40b') + err.message;
        if (tbody) tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-danger">Ошибка загрузки: ${err.message}</td></tr>`;
    } finally {
        if (editor) editor.disabled = false;
    }
}

async function saveSourcesRaw(content) {
    const editor = document.getElementById('sources-json-editori18n.t('auto__try_json_parse_content_catch_e_if_typeof_shownotification__c50f5c')function') {
            showNotification(i18n.t('auto__json__636c61') + e.message, 'danger');
        } else {
            alert(i18n.t('auto__json__636c61') + e.message);
        }
        return false;
    }

    try {
        if (editor) editor.disabled = true;
        const response = await window.api.fetch('/api/admin/sources/raw', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: content })
        });
        
        if (response.status === 'ok') {
            if (typeof showNotification === 'function') {
                showNotification(i18n.t('auto___17582e'), 'success');
            }
            return true;
        }
    } catch (err) {
        console.error(i18n.t('auto___0f089d'), err);
        if (typeof showNotification === 'function') {
            showNotification(i18n.t('auto___bbbabd') + err.message, 'danger');
        }
        return false;
    } finally {
        if (editor) editor.disabled = false;
    }
}

function renderSourcesTable() {
    const tbody = document.getElementById('sources-list-body');
    const filterSelect = document.getElementById('sources-category-filter');
    if (!tbody) return;

    const filterVal = filterSelect ? filterSelect.value : 'all';
    tbody.innerHTML = '';
    
    let hasItems = false;
    
    for (const [category, items] of Object.entries(currentSourcesObj)) {
        if (!Array.isArray(items)) continue; // Пропускаем метаданные самого файла (например, "metadata": {...})
        
        // Маппинг категорий
        let catForFilter = 'other';
        if (category === 'metadata_apis') catForFilter = 'metadata';
        else if (category === 'streaming_search') catForFilter = 'streaming_search';
        else if (category.includes('streaming') || category === 'direct_sites') catForFilter = 'streaming';
        else if (category === 'iframe_players') catForFilter = 'embed_player';
        else if (category === 'torrent_trackers') catForFilter = 'torrent';
        else if (category === 'video_search') catForFilter = 'search';
        
        if (filterVal !== 'all' && catForFilter !== filterVal) continue;
        
        items.forEach((item, index) => {
            hasItems = true;
            const tr = document.createElement('tr');
            
            const isEnabled = item.enabled !== false; // по умолчанию true
            
            tr.innerHTML = `
                <td>
                    <div class="form-check form-switch">
                        <input class="form-check-input toggle-source-btn" type="checkbox" role="switch" 
                            data-category="${category}" data-index="${index}" ${isEnabled ? 'checked' : ''}>
                    </div>
                </td>
                <td class="fw-bold">${item.name || item.id || i18n.t('auto___32b74a')}</td>
                <td><a href="${item.url || '#'}" target="_blank" class="small text-truncate d-inline-block" style="max-width: 150px;">${item.url || '-'}</a></td>
                <td><span class="badge bg-secondary">${category}</span></td>
                <td class="small text-muted">${item.description || '-'}</td>
                <td class="text-end">
                    <button class="btn btn-sm btn-outline-danger delete-source-btn" data-category="${category}" data-index="${index}" title=i18n.t('auto___86ea33')>
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    }
    
    if (!hasItems) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-muted">Нет источников для отображения</td></tr>i18n.t('auto__document_queryselectorall__521712').toggle-source-btn').forEach(btn => {
        btn.addEventListener('change', handleToggleSource);
    });
    
    document.querySelectorAll('.delete-source-btn').forEach(btn => {
        btn.addEventListener('click', handleDeleteSource);
    });
}

async function handleToggleSource(e) {
    const category = e.target.getAttribute('data-category');
    const index = parseInt(e.target.getAttribute('data-indexi18n.t('auto__if_currentsourcesobj_category_currentsourcesobj_category_index_currentsourcesobj_category_index_enabled_e_target_checked_const_newjson_json_stringify_currentsourcesobj_null_2_const_editor_document_getelementbyid__5a75cc')sources-json-editor');
        if (editor) editor.value = newJson;
        
        await saveSourcesRaw(newJson);
    }
}

async function handleDeleteSource(e) {
    const btn = e.target.closest('button');
    const category = btn.getAttribute('data-category');
    const index = parseInt(btn.getAttribute('data-index'));
    
    if (confirm(i18n.t('auto___102afb'))) {
        if (currentSourcesObj[category] && currentSourcesObj[category][index]) {
            currentSourcesObj[category].splice(index, 1);
            
            const newJson = JSON.stringify(currentSourcesObj, null, 2);
            const editor = document.getElementById('sources-json-editor');
            if (editor) editor.value = newJson;
            
            const success = await saveSourcesRaw(newJson);
            if (success) renderSourcesTable();
        }
    }
}

async function handleAddSource() {
    const id = document.getElementById('new-source-id')?.value.trim();
    const name = document.getElementById('new-source-name')?.value.trim();
    const url = document.getElementById('new-source-url')?.value.trim();
    const filterCat = document.getElementById('new-source-category')?.value;
    const desc = document.getElementById('new-source-description')?.value.trim();
    
    if (!id || !name || !url) {
        window.showToast?.(i18n.t('auto__id_url_9e1f64'), 'warning') || alert(i18n.t('auto__id_url_9e1f64'));
        return;
    }
    
    // Определяем в какую секцию JSON положить новый элемент
    let targetCategory = 'other';
    if (filterCat === 'metadata') targetCategory = 'metadata_apis';
    else if (filterCat === 'streaming_search') targetCategory = 'streaming_search';
    else if (filterCat === 'streaming') targetCategory = 'direct_sites';
    else if (filterCat === 'embed_player') targetCategory = 'iframe_players';
    else if (filterCat === 'torrent') targetCategory = 'torrent_trackers';
    else if (filterCat === 'search') targetCategory = 'video_search';
    
    if (!currentSourcesObj[targetCategory]) {
        currentSourcesObj[targetCategory] = [];
    }
    
    const newItem = {
        id: id,
        name: name,
        url: url,
        description: desc,
        enabled: true
    };
    
    currentSourcesObj[targetCategory].push(newItem);
    
    const newJson = JSON.stringify(currentSourcesObj, null, 2);
    const editor = document.getElementById('sources-json-editori18n.t('auto__if_editor_editor_value_newjson_const_success_await_savesourcesraw_newjson_if_success_rendersourcestable_document_getelementbyid__3f13fe')form-add-sourcei18n.t('auto__reset_window_initsourcestab_function_console_log__14f270')Инициализация вкладки Источники...');
    
    const btnRefresh = document.getElementById('btn-refresh-sources-json');
    const btnSave = document.getElementById('btn-save-sources-json');
    const btnSaveAll = document.getElementById('btn-save-all-sources');
    const btnAdd = document.getElementById('btn-add-source');
    const filterSelect = document.getElementById('sources-category-filter');
    const editor = document.getElementById('sources-json-editori18n.t('auto__if_btnrefresh_btnrefresh_onclick_loadsourcesraw_if_btnsave_btnsave_onclick_if_editor_savesourcesraw_editor_value_then_json_try_currentsourcesobj_json_parse_editor_value_rendersourcestable_catch_e_if_btnsaveall_btnsaveall_onclick_btnsave_onclick_if_btnadd_btnadd_onclick_handleaddsource_if_filterselect_filterselect_addeventlistener__0d8404')changei18n.t('auto__rendersourcestable_json_if_editor_editor_addeventlistener__231a71')blur', () => {
            try {
                currentSourcesObj = JSON.parse(editor.value);
                renderSourcesTable();
            } catch(e){}
        });
    }

    // Загружаем данные при открытии
    loadSourcesRaw();
};
