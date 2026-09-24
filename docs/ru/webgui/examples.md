# Примеры использования API Cache System

> Практические примеры интеграции кеширования в разные типы вкладок

## 📚 Содержание

1. [Простая вкладка со статикой](#простая-вкладка-со-статикой)
2. [Live Telemetry вкладка](#live-telemetry-вкладка)
3. [Чат с историей](#чат-с-историей)
4. [Dashboard с метриками](#dashboard-с-метриками)
5. [Настройки с сохранением](#настройки-с-сохранением)

---

## 1. Простая вкладка со статикой

**Сценарий:** Вкладка с редко меняющимися данными (модели, конфигурация)

```javascript
// models_tab/main.js
(function() {
  let models = [];
  
  async function initModelsTab() {
    await loadModels();
    bindEvents();
  }
  
  async function loadModels() {
    try {
      // Автоматически: cache-first, TTL 1 час
      models = await cachedApiFetch('/api/v1/models');
      renderModels(models);
    } catch (err) {
      console.error('Failed to load models:', err);
      showError('Не удалось загрузить модели');
    }
  }
  
  function bindEvents() {
    // Кнопка обновления
    document.getElementById('btn-refresh-models').onclick = async () => {
      // Принудительное обновление из сети
      models = await cachedApiFetch('/api/v1/models', {}, { 
        forceNetwork: true 
      });
      renderModels(models);
    };
  }
  
  function renderModels(models) {
    const container = document.getElementById('models-list');
    container.innerHTML = models.map(m => `
      <div class="model-card">
        <h5>${m.name}</h5>
        <p>${m.description}</p>
      </div>
    `).join('');
  }
  
  window.initModelsTab = initModelsTab;
})();
```

---

## 2. Live Telemetry вкладка

**Сценарий:** Реалтайм мониторинг системных метрик

```javascript
// system_monitor_tab/main.js
(function() {
  let isActive = true;
  let pollerId = null;
  
  async function initSystemMonitorTab() {
    await loadInitialData();
    startLiveUpdates();
  }
  
  async function loadInitialData() {
    // Prefetch: загружаем критичные данные сразу
    await Promise.all([
      loadSystemSummary(),
      loadSensors()
    ]);
  }
  
  async function loadSystemSummary() {
    // Stale-while-revalidate: показываем кеш, обновляем в фоне
    const summary = await cachedApiFetch('/api/v1/system/summary');
    renderSummary(summary);
  }
  
  async function loadSensors() {
    // Network-first: всегда свежие данные
    const sensors = await cachedApiFetch('/api/v1/system/sensors');
    renderSensors(sensors);
  }
  
  function startLiveUpdates() {
    if (window.registerTabPoller) {
      pollerId = window.registerTabPoller('tab-system-monitor', async () => {
        if (isActive) {
          await loadSensors(); // Обновляем только динамические данные
        }
      }, 3000); // Каждые 3 секунды
    }
  }
  
  function deactivateSystemMonitorTab() {
    isActive = false;
    if (pollerId) {
      window.unregisterTabPoller(pollerId);
    }
  }
  
  window.initSystemMonitorTab = initSystemMonitorTab;
  window.deactivateSystemMonitorTab = deactivateSystemMonitorTab;
})();
```

---

## 3. Чат с историей

**Сценарий:** Чат с сохранением истории в кеш

```javascript
// chat_tab/main.js
(function() {
  let messages = [];
  const CACHE_TAG = 'chat-history';
  
  async function initChatTab() {
    await loadChatHistory();
    bindChatEvents();
  }
  
  async function loadChatHistory() {
    try {
      // Загружаем историю из кеша (stale-while-revalidate)
      const history = await cachedApiFetch('/api/chat/history', {}, {
        tag: CACHE_TAG
      });
      
      messages = history.messages || [];
      renderMessages(messages);
    } catch (err) {
      console.error('Failed to load chat history:', err);
    }
  }
  
  async function sendMessage(text) {
    // Добавляем сообщение в UI оптимистично
    const tempMsg = { id: Date.now(), text, sender: 'user', pending: true };
    messages.push(tempMsg);
    renderMessages(messages);
    
    try {
      // Отправляем на сервер (не кешируем POST-запросы)
      const response = await cachedApiFetch('/api/chat/send', {
        method: 'POST',
        body: JSON.stringify({ text })
      }, {
        ttl: 0 // Не кешируем мутации
      });
      
      // Обновляем сообщение
      const idx = messages.findIndex(m => m.id === tempMsg.id);
      if (idx >= 0) {
        messages[idx] = response.userMessage;
        messages.push(response.aiMessage);
      }
      
      // Инвалидируем кеш истории
      await invalidateCacheByTag(CACHE_TAG);
      
      renderMessages(messages);
    } catch (err) {
      // Откат оптимистичного обновления
      messages = messages.filter(m => m.id !== tempMsg.id);
      renderMessages(messages);
      showError('Не удалось отправить сообщение');
    }
  }
  
  function bindChatEvents() {
    document.getElementById('btn-send').onclick = () => {
      const input = document.getElementById('chat-input');
      const text = input.value.trim();
      if (text) {
        sendMessage(text);
        input.value = '';
      }
    };
  }
  
  window.initChatTab = initChatTab;
})();
```

---

## 4. Dashboard с метриками

**Сценарий:** Дашборд с разными типами данных и частотами обновления

```javascript
// dashboard_tab/main.js
(function() {
  const REFRESH_INTERVALS = {
    static: 30 * 60 * 1000,  // 30 минут
    dynamic: 5 * 1000,        // 5 секунд
    realtime: 1 * 1000        // 1 секунда
  };
  
  async function initDashboardTab() {
    // Параллельная загрузка разных типов данных
    await Promise.allSettled([
      loadStaticWidgets(),    // Cache-first
      loadDynamicWidgets(),   // Stale-while-revalidate
      loadRealtimeWidgets()   // Network-first
    ]);
    
    startAutoRefresh();
  }
  
  async function loadStaticWidgets() {
    // Конфигурация, справочники (редко меняются)
    const [config, users] = await Promise.all([
      cachedApiFetch('/api/dashboard/config', {}, {
        strategy: 'cache-first',
        ttl: REFRESH_INTERVALS.static
      }),
      cachedApiFetch('/api/dashboard/users', {}, {
        strategy: 'cache-first',
        ttl: REFRESH_INTERVALS.static
      })
    ]);
    
    renderConfigWidget(config);
    renderUsersWidget(users);
  }
  
  async function loadDynamicWidgets() {
    // Статистика, метрики (обновляются периодически)
    const [stats, alerts] = await Promise.all([
      cachedApiFetch('/api/dashboard/stats', {}, {
        strategy: 'stale-while-revalidate',
        ttl: REFRESH_INTERVALS.dynamic
      }),
      cachedApiFetch('/api/dashboard/alerts', {}, {
        strategy: 'stale-while-revalidate',
        ttl: REFRESH_INTERVALS.dynamic
      })
    ]);
    
    renderStatsWidget(stats);
    renderAlertsWidget(alerts);
  }
  
  async function loadRealtimeWidgets() {
    // Live данные (всегда свежие)
    const [metrics, events] = await Promise.all([
      cachedApiFetch('/api/dashboard/metrics', {}, {
        strategy: 'network-first',
        ttl: REFRESH_INTERVALS.realtime
      }),
      cachedApiFetch('/api/dashboard/events', {}, {
        strategy: 'network-first',
        ttl: REFRESH_INTERVALS.realtime
      })
    ]);
    
    renderMetricsWidget(metrics);
    renderEventsWidget(events);
  }
  
  function startAutoRefresh() {
    // Динамические виджеты обновляем каждые 5 секунд
    setInterval(() => loadDynamicWidgets(), REFRESH_INTERVALS.dynamic);
    
    // Realtime виджеты обновляем каждую секунду
    setInterval(() => loadRealtimeWidgets(), REFRESH_INTERVALS.realtime);
  }
  
  window.initDashboardTab = initDashboardTab;
})();
```

---

## 5. Настройки с сохранением

**Сценарий:** Вкладка настроек с кешированием и оптимистичным обновлением

```javascript
// settings_tab/main.js
(function() {
  let settings = {};
  const CACHE_TAG = 'user-settings';
  
  async function initSettingsTab() {
    await loadSettings();
    bindSettingsEvents();
  }
  
  async function loadSettings() {
    try {
      // Загружаем настройки (cache-first)
      settings = await cachedApiFetch('/api/settings', {}, {
        strategy: 'cache-first',
        ttl: 60 * 60 * 1000, // 1 час
        tag: CACHE_TAG
      });
      
      renderSettings(settings);
    } catch (err) {
      console.error('Failed to load settings:', err);
    }
  }
  
  async function saveSetting(key, value) {
    // Оптимистичное обновление UI
    const oldValue = settings[key];
    settings[key] = value;
    renderSettings(settings);
    
    try {
      // Сохраняем на сервер
      const updated = await cachedApiFetch('/api/settings', {
        method: 'POST',
        body: JSON.stringify({ [key]: value })
      }, {
        ttl: 0 // Не кешируем POST
      });
      
      // Обновляем локальные настройки
      settings = updated;
      
      // Инвалидируем кеш настроек
      await invalidateCacheByTag(CACHE_TAG);
      
      showSuccess('Настройка сохранена');
    } catch (err) {
      // Откат при ошибке
      settings[key] = oldValue;
      renderSettings(settings);
      showError('Не удалось сохранить настройку');
    }
  }
  
  function bindSettingsEvents() {
    // Переключатели
    document.querySelectorAll('.setting-toggle').forEach(toggle => {
      toggle.onchange = (e) => {
        const key = e.target.dataset.setting;
        saveSetting(key, e.target.checked);
      };
    });
    
    // Кнопка сброса кеша
    document.getElementById('btn-clear-cache').onclick = async () => {
      await clearAllApiCache();
      await loadSettings();
      showSuccess('Кеш очищен');
    };
  }
  
  window.initSettingsTab = initSettingsTab;
})();
```

---

## 🎯 Общие паттерны

### Паттерн 1: Prefetching

```javascript
async function initTab() {
  // Загружаем критичные данные параллельно
  await Promise.allSettled([
    loadCriticalData1(),
    loadCriticalData2()
  ]);
  
  // Фоновая загрузка менее критичных данных
  loadSecondaryData();
}
```

### Паттерн 2: Оптимистичное обновление

```javascript
async function updateData(id, newValue) {
  // 1. Обновляем UI сразу
  updateUI(id, newValue);
  
  try {
    // 2. Отправляем на сервер
    await cachedApiFetch('/api/update', { 
      method: 'POST', 
      body: JSON.stringify({ id, value: newValue }) 
    });
    
    // 3. Инвалидируем кеш
    await invalidateCacheByTag('data-tag');
  } catch (err) {
    // 4. Откат при ошибке
    rollbackUI(id);
    showError('Не удалось сохранить');
  }
}
```

### Паттерн 3: Background Sync

```javascript
async function loadWithBackgroundSync() {
  // Показываем кеш
  const cached = await cachedApiFetch('/api/data', {}, {
    strategy: 'stale-while-revalidate'
  });
  
  // Данные обновляются в фоне автоматически
  // При следующем запросе будут свежие
}
```

---

## 🔍 Debug и тестирование

### Запуск тестов

```javascript
// В консоли браузера
await testApiCache();
```

### Включение debug-логов

```javascript
// В консоли браузера
localStorage.setItem('DEBUG_API_CACHE', 'true');
location.reload();
```

### Проверка hit rate

```javascript
const stats = await getApiCacheStats();
console.log(`Hit rate: ${stats.apiCache.hitRate}%`);
```

---

## 📚 Дополнительно

- **[Полная документация API Cache](api-cache.md)**
- **[Быстрый старт](README.md)**

---

**© 2026 AI-Breadboard Team**
