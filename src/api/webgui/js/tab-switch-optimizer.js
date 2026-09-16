/**
 * Tab Switch Optimizer - Оптимизация переключения между вкладками
 * 
 * Реализует:
 * - DOM кеширование (сохранение содержимого вкладки вместо удаления)
 * - Мгновенная визуальная обратная связь (показ активной вкладки до загрузки)
 * - Предварительная загрузка соседних вкладок
 * - Трекинг времени переключения
 * 
 * Usage:
 *   const optimizer = new TabSwitchOptimizer();
 *   optimizer.enableDOMCaching();
 *   optimizer.optimizeSwitching();
 */

class TabSwitchOptimizer {
  constructor() {
    this.domCache = new Map(); // Кеш DOM содержимого вкладок
    this.switchStats = {
      totalSwitches: 0,
      avgSwitchTime: 0,
      lastSwitchTime: null,
      switchTimes: []
    };
    this.isOptimized = false;
  }

  /**
   * Включить DOM кеширование
   * Вместо удаления содержимого вкладки, сохраняем его в памяти
   */
  enableDOMCaching() {
    console.log('[TabSwitchOptimizer] Enabling DOM caching...');

    // Перехватываем стандартное управление табами
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'childList' || mutation.type === 'attributes') {
          // Вызываем автосохранение изменений
          this._cacheVisibleTabs();
        }
      });
    });

    // Наблюдаем за контейнером с табами
    const tabContainer = document.getElementById('mainTabsContent') || 
                         document.querySelector('[role="tablist"]')?.parentElement;
    
    if (tabContainer) {
      observer.observe(tabContainer, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['class', 'style', 'aria-hidden']
      });
    }

    this.isOptimized = true;
    console.log('[TabSwitchOptimizer] DOM caching enabled');
  }

  /**
   * Кешировать видимые вкладки
   */
  _cacheVisibleTabs() {
    const tabs = document.querySelectorAll('[role="tabpanel"]:not([aria-hidden="true"])');
    tabs.forEach(tab => {
      if (tab.id) {
        // Сохраняем клон вкладки
        this.domCache.set(tab.id, tab.cloneNode(true));
      }
    });
  }

  /**
   * Получить кешированное содержимое вкладки
   */
  getCachedTabContent(tabId) {
    return this.domCache.get(tabId);
  }

  /**
   * Очистить кеш DOM
   */
  clearDOMCache(tabId = null) {
    if (tabId) {
      this.domCache.delete(tabId);
    } else {
      this.domCache.clear();
    }
  }

  /**
   * Оптимизировать функцию переключения вкладок
   * Добавляет мгновенную визуальную обратную связь и трекинг времени
   */
  optimizeSwitching(originalSwitchFn) {
    return async (targetTabId) => {
      const startTime = performance.now();
      
      if (!targetTabId) return;

      // Мгновенно показываем активную вкладку визуально (без загрузки)
      this._showTabImmediately(targetTabId);

      // Выполняем оригинальное переключение
      if (typeof originalSwitchFn === 'function') {
        await originalSwitchFn(targetTabId);
      }

      // Записываем время переключения
      const switchTime = performance.now() - startTime;
      this._recordSwitchTime(switchTime, targetTabId);

      console.log(`[TabSwitchOptimizer] Tab switched in ${switchTime.toFixed(2)}ms`);
    };
  }

  /**
   * Мгновенно показать вкладку визуально (до загрузки содержимого)
   */
  _showTabImmediately(targetTabId) {
    const cleanTabId = targetTabId.startsWith('#') ? targetTabId.slice(1) : targetTabId;
    
    // Скрываем все остальные вкладки
    document.querySelectorAll('[role="tabpanel"]').forEach(tab => {
      tab.style.display = 'none';
      tab.classList.remove('active', 'show');
      tab.setAttribute('aria-hidden', 'true');
    });

    // Показываем целевую вкладку
    const targetTab = document.getElementById(cleanTabId);
    if (targetTab) {
      targetTab.style.display = 'block';
      targetTab.classList.add('active', 'show');
      targetTab.setAttribute('aria-hidden', 'false');
    }

    // Обновляем визуальное состояние кнопок вкладок
    document.querySelectorAll('[role="tab"]').forEach(tab => {
      tab.classList.remove('active');
      tab.setAttribute('aria-selected', 'false');
    });

    const targetButton = document.querySelector(`[aria-controls="${cleanTabId}"]`) || 
                        document.querySelector(`[data-bs-target="#${cleanTabId}"]`);
    if (targetButton) {
      targetButton.classList.add('active');
      targetButton.setAttribute('aria-selected', 'true');
    }
  }

  /**
   * Записать время переключения и вычислить среднее
   */
  _recordSwitchTime(time, tabId) {
    this.switchStats.totalSwitches++;
    this.switchStats.lastSwitchTime = time;
    this.switchStats.switchTimes.push({ time, tabId, timestamp: Date.now() });

    // Ограничиваем историю последних 100 переключениями
    if (this.switchStats.switchTimes.length > 100) {
      this.switchStats.switchTimes = this.switchStats.switchTimes.slice(-100);
    }

    // Вычисляем среднее время
    const sum = this.switchStats.switchTimes.reduce((acc, s) => acc + s.time, 0);
    this.switchStats.avgSwitchTime = sum / this.switchStats.switchTimes.length;
  }

  /**
   * Предварительная загрузка соседних вкладок
   */
  preloadAdjacentTabs(currentTabId) {
    const allTabs = Array.from(document.querySelectorAll('[role="tab"]'));
    const currentIndex = allTabs.findIndex(tab => 
      tab.getAttribute('aria-controls') === currentTabId || 
      tab.getAttribute('data-bs-target') === `#${currentTabId}`
    );

    if (currentIndex >= 0) {
      // Предзагружаем соседние вкладки
      const adjacentIndices = [currentIndex - 1, currentIndex + 1];
      adjacentIndices.forEach(idx => {
        if (idx >= 0 && idx < allTabs.length) {
          const tab = allTabs[idx];
          const tabId = tab.getAttribute('aria-controls') || 
                       tab.getAttribute('data-bs-target')?.replace('#', '');
          
          if (tabId && window.optimizationModule?.tabLoader) {
            console.log(`[TabSwitchOptimizer] Preloading adjacent tab: ${tabId}`);
            window.optimizationModule.tabLoader.preloadTab(tabId);
          }
        }
      });
    }
  }

  /**
   * Получить статистику переключения
   */
  getStats() {
    return {
      ...this.switchStats,
      avgSwitchTimeFormatted: `${this.switchStats.avgSwitchTime.toFixed(2)}ms`,
      lastSwitchTimeFormatted: this.switchStats.lastSwitchTime ? 
        `${this.switchStats.lastSwitchTime.toFixed(2)}ms` : 'N/A',
      cachedTabs: this.domCache.size,
      isOptimized: this.isOptimized
    };
  }

  /**
   * Вывести статистику в консоль
   */
  printStats() {
    const stats = this.getStats();
    console.group('📊 Tab Switch Performance Stats');
    console.log('Total Switches:', stats.totalSwitches);
    console.log('Average Switch Time:', stats.avgSwitchTimeFormatted);
    console.log('Last Switch Time:', stats.lastSwitchTimeFormatted);
    console.log('Cached Tabs:', stats.cachedTabs);
    console.log('Performance Target: <100ms (currently', 
      (stats.avgSwitchTime < 100 ? '✓ GOOD' : '✗ SLOW'), ')');
    console.groupEnd();
  }

  /**
   * Очистить статистику
   */
  resetStats() {
    this.switchStats = {
      totalSwitches: 0,
      avgSwitchTime: 0,
      lastSwitchTime: null,
      switchTimes: []
    };
  }
}

// Глобальный экземпляр
window.tabSwitchOptimizer = new TabSwitchOptimizer();

// Экспортируем
window.TabSwitchOptimizer = TabSwitchOptimizer;

export default TabSwitchOptimizer;
