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
        editor.value = 'Загрузка...';
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
            console.error('Ошибка парсинга JSON для таблицы:', e);
            if (tbody) {
                tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-danger">Ошибка формата JSON. Таблица недоступна.</td></tr>';
            }
        }
        
    } catch (err) {
        console.error('Ошибка загрузки источников:', err);
        if (editor) editor.value = 'Ошибка загрузки:\n' + err.message;
        if (tbody) tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-danger">Ошибка загрузки: ${err.message}</td></tr>`;
    } finally {
        if (editor) editor.disabled = false;
    }
}

async function saveSourcesRaw(content) {
    const editor = document.getElementById('sources-json-editor');
    
    // Проверка синтаксиса на клиенте перед отправкой
    try {
        JSON.parse(content);
    } catch (e) {
        if (typeof showNotification === 'function') {
            showNotification('Синтаксическая ошибка JSON: ' + e.message, 'danger');
        } else {
            alert('Синтаксическая ошибка JSON: ' + e.message);
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
                showNotification('Источники успешно сохранены!', 'success');
            }
            return true;
        }
    } catch (err) {
        console.error('Ошибка сохранения источников:', err);
        if (typeof showNotification === 'function') {
            showNotification('Ошибка сохранения: ' + err.message, 'danger');
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
                <td class="fw-bold">${item.name || item.id || 'Без названия'}</td>
                <td><a href="${item.url || '#'}" target="_blank" class="small text-truncate d-inline-block" style="max-width: 150px;">${item.url || '-'}</a></td>
                <td><span class="badge bg-secondary">${category}</span></td>
                <td class="small text-muted">${item.description || '-'}</td>
                <td class="text-end">
                    <button class="btn btn-sm btn-outline-danger delete-source-btn" data-category="${category}" data-index="${index}" title="Удалить">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    }
    
    if (!hasItems) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-muted">Нет источников для отображения</td></tr>';
    }
    
    // Привязываем обработчики к сгенерированным кнопкам
    document.querySelectorAll('.toggle-source-btn').forEach(btn => {
        btn.addEventListener('change', handleToggleSource);
    });
    
    document.querySelectorAll('.delete-source-btn').forEach(btn => {
        btn.addEventListener('click', handleDeleteSource);
    });
}

async function handleToggleSource(e) {
    const category = e.target.getAttribute('data-category');
    const index = parseInt(e.target.getAttribute('data-index'));
    
    if (currentSourcesObj[category] && currentSourcesObj[category][index]) {
        currentSourcesObj[category][index].enabled = e.target.checked;
        const newJson = JSON.stringify(currentSourcesObj, null, 2);
        
        // Обновляем текстовое поле и сервер
        const editor = document.getElementById('sources-json-editor');
        if (editor) editor.value = newJson;
        
        await saveSourcesRaw(newJson);
    }
}

async function handleDeleteSource(e) {
    const btn = e.target.closest('button');
    const category = btn.getAttribute('data-category');
    const index = parseInt(btn.getAttribute('data-index'));
    
    if (confirm('Вы уверены, что хотите удалить этот источник?')) {
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
        alert('Заполните обязательные поля: ID, Название и URL');
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
    const editor = document.getElementById('sources-json-editor');
    if (editor) editor.value = newJson;
    
    const success = await saveSourcesRaw(newJson);
    if (success) {
        renderSourcesTable();
        // Очищаем форму
        document.getElementById('form-add-source').reset();
    }
}

// Инициализация вкладки
window.initSourcesTab = function() {
    console.log('Инициализация вкладки Источники...');
    
    const btnRefresh = document.getElementById('btn-refresh-sources-json');
    const btnSave = document.getElementById('btn-save-sources-json');
    const btnSaveAll = document.getElementById('btn-save-all-sources');
    const btnAdd = document.getElementById('btn-add-source');
    const filterSelect = document.getElementById('sources-category-filter');
    const editor = document.getElementById('sources-json-editor');
    
    if (btnRefresh) btnRefresh.onclick = loadSourcesRaw;
    
    if (btnSave) {
        btnSave.onclick = () => {
            if (editor) saveSourcesRaw(editor.value).then(() => {
                // Обновляем таблицу после ручного изменения JSON
                try {
                    currentSourcesObj = JSON.parse(editor.value);
                    renderSourcesTable();
                } catch(e){}
            });
        };
    }
    
    if (btnSaveAll) {
        btnSaveAll.onclick = btnSave.onclick;
    }
    
    if (btnAdd) {
        btnAdd.onclick = handleAddSource;
    }
    
    if (filterSelect) {
        filterSelect.addEventListener('change', renderSourcesTable);
    }
    
    // Также обновляем таблицу при потере фокуса редактором, если JSON валидный
    if (editor) {
        editor.addEventListener('blur', () => {
            try {
                currentSourcesObj = JSON.parse(editor.value);
                renderSourcesTable();
            } catch(e){}
        });
    }

    // Загружаем данные при открытии
    loadSourcesRaw();
};
