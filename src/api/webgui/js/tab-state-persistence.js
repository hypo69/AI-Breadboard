/**
 * Tab State Persistence - Сохранение состояния вкладок в localStorage
 * 
 * Сохраняет:
 * - Активную вкладку
 * - Историю переходов
 * - Фильтры и поиск на каждой вкладке
 * 
 * Usage:
 *   const persistence = new TabStatePersistence('admin');
 *   persistence.saveActiveTab('tab-chat');
 *   persistence.getLastActiveTab();  // 'tab-chat'
 */

class TabStatePersistence {
  constructor(namespace = 'admin') {
    this.namespace = namespace;
    this.storagePrefix = `${namespace}:tab-state`;
    this.maxHistorySize = 10;
  }

  /**
   * Сохранить активную вкладку
   */
  saveActiveTab(tabId) {
    if (!tabId) return;
    
    const cleanTabId = tabId.startsWith('#') ? tabId.slice(1) : tabId;
    const timestamp = Date.now();
    
    // Сохраняем текущую активную вкладку
    localStorage.setItem(`${this.storagePrefix}:active`, cleanTabId);
    localStorage.setItem(`${this.storagePrefix}:active-timestamp`, timestamp.toString());
    
    // Добавляем в историю
    this._addToHistory(cleanTabId, timestamp);
    
    console.log(`[TabStatePersistence] Saved active tab: ${cleanTabId}`);
  }

  /**
   * Получить последнюю активную вкладку
   */
  getLastActiveTab(fallback = null) {
    const lastTab = localStorage.getItem(`${this.storagePrefix}:active`);
    return lastTab || fallback;
  }

  /**
   * Получить последнюю активную вкладку с временем
   */
  getLastActiveTabWithTimestamp() {
    const tabId = localStorage.getItem(`${this.storagePrefix}:active`);
    const timestamp = localStorage.getItem(`${this.storagePrefix}:active-timestamp`);
    
    if (!tabId) return null;
    
    return {
      tabId,
      timestamp: timestamp ? parseInt(timestamp) : null,
      age: timestamp ? Date.now() - parseInt(timestamp) : null
    };
  }

  /**
   * Добавить вкладку в историю
   */
  _addToHistory(tabId, timestamp) {
    const historyKey = `${this.storagePrefix}:history`;
    let history = [];
    
    try {
      const stored = localStorage.getItem(historyKey);
      if (stored) {
        history = JSON.parse(stored);
      }
    } catch (e) {
      console.warn('[TabStatePersistence] Failed to parse history:', e);
      history = [];
    }

    // Добавляем новую запись в начало
    history.unshift({ tabId, timestamp });

    // Удаляем дубли
    const seen = new Set();
    history = history.filter(item => {
      if (seen.has(item.tabId)) return false;
      seen.add(item.tabId);
      return true;
    });

    // Ограничиваем размер истории
    if (history.length > this.maxHistorySize) {
      history = history.slice(0, this.maxHistorySize);
    }

    // Сохраняем обновленную историю
    localStorage.setItem(historyKey, JSON.stringify(history));
  }

  /**
   * Получить историю переходов между вкладками
   */
  getHistory() {
    const historyKey = `${this.storagePrefix}:history`;
    try {
      const stored = localStorage.getItem(historyKey);
      return stored ? JSON.parse(stored) : [];
    } catch (e) {
      console.warn('[TabStatePersistence] Failed to parse history:', e);
      return [];
    }
  }

  /**
   * Очистить историю
   */
  clearHistory() {
    localStorage.removeItem(`${this.storagePrefix}:history`);
    console.log('[TabStatePersistence] History cleared');
  }

  /**
   * Сохранить состояние вкладки (фильтры, поиск и т.д.)
   */
  saveTabState(tabId, state) {
    if (!tabId || !state) return;
    
    const cleanTabId = tabId.startsWith('#') ? tabId.slice(1) : tabId;
    const stateKey = `${this.storagePrefix}:state:${cleanTabId}`;
    
    try {
      localStorage.setItem(stateKey, JSON.stringify(state));
      console.log(`[TabStatePersistence] Saved state for tab: ${cleanTabId}`);
    } catch (e) {
      console.warn(`[TabStatePersistence] Failed to save state for ${cleanTabId}:`, e);
    }
  }

  /**
   * Получить состояние вкладки
   */
  getTabState(tabId) {
    if (!tabId) return null;
    
    const cleanTabId = tabId.startsWith('#') ? tabId.slice(1) : tabId;
    const stateKey = `${this.storagePrefix}:state:${cleanTabId}`;
    
    try {
      const stored = localStorage.getItem(stateKey);
      return stored ? JSON.parse(stored) : null;
    } catch (e) {
      console.warn(`[TabStatePersistence] Failed to parse state for ${cleanTabId}:`, e);
      return null;
    }
  }

  /**
   * Удалить состояние вкладки
   */
  deleteTabState(tabId) {
    if (!tabId) return;
    
    const cleanTabId = tabId.startsWith('#') ? tabId.slice(1) : tabId;
    const stateKey = `${this.storagePrefix}:state:${cleanTabId}`;
    
    localStorage.removeItem(stateKey);
    console.log(`[TabStatePersistence] Deleted state for tab: ${cleanTabId}`);
  }

  /**
   * Очистить все сохраненное состояние
   */
  clear() {
    const keys = Object.keys(localStorage).filter(key => 
      key.startsWith(this.storagePrefix)
    );
    
    keys.forEach(key => localStorage.removeItem(key));
    console.log(`[TabStatePersistence] Cleared ${keys.length} entries`);
  }

  /**
   * Получить полную информацию о сохраненном состоянии
   */
  getStorageInfo() {
    const keys = Object.keys(localStorage).filter(key => 
      key.startsWith(this.storagePrefix)
    );
    
    const info = {
      namespace: this.namespace,
      totalEntries: keys.length,
      entries: {}
    };

    keys.forEach(key => {
      const shortKey = key.replace(`${this.storagePrefix}:`, '');
      const value = localStorage.getItem(key);
      
      try {
        info.entries[shortKey] = {
          size: value.length,
          parsed: JSON.parse(value)
        };
      } catch {
        info.entries[shortKey] = {
          size: value.length,
          raw: value
        };
      }
    });

    return info;
  }

  /**
   * Экспортировать состояние в JSON
   */
  exportState() {
    return JSON.stringify(this.getStorageInfo(), null, 2);
  }

  /**
   * Импортировать состояние из JSON
   */
  importState(jsonString) {
    try {
      const data = JSON.parse(jsonString);
      // Реализация импорта если нужна
      console.log('[TabStatePersistence] Import not implemented yet');
    } catch (e) {
      console.error('[TabStatePersistence] Failed to import state:', e);
    }
  }
}

/**
 * Глобальный экземпляр для админки
 */
window.tabStatePersistence = new TabStatePersistence('admin');

// Экспортируем
window.TabStatePersistence = TabStatePersistence;

export default TabStatePersistence;
