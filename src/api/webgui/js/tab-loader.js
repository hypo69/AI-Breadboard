/**
 * LazyTabLoader - Система ленивой загрузки вкладок
 * 
 * Управляет загрузкой вкладок по требованию, кешировани в памяти
 * и минимизирует первоначальную нагрузку на интерфейс.
 * 
 * Usage:
 *   const loader = new LazyTabLoader();
 *   loader.registerTab('chat', '/html/chat/index.html', '/html/chat/main.js');
 *   await loader.loadTab('chat');  // Загружает вкладку
 *   loader.isLoaded('chat');       // true
 */

class LazyTabLoader {
  constructor() {
    this.tabs = new Map(); // Реестр вкладок
    this.loaded = new Set(); // Какие вкладки уже загружены
    this.loading = new Map(); // Текущие загрузки (для дедупликации)
    this.cache = new Map(); // Кеш содержимого вкладок в памяти
  }

  /**
   * Регистрирует вкладку для последующей загрузки
   */
  registerTab(tabName, htmlUrl, jsUrl = null) {
    if (!this.tabs.has(tabName)) {
      this.tabs.set(tabName, { htmlUrl, jsUrl, initialized: false });
    }
  }

  /**
   * Загружает вкладку по требованию
   */
  async loadTab(tabName) {
    if (!this.tabs.has(tabName)) {
      console.warn(`[LazyTabLoader] Tab '${tabName}' not registered`);
      return false;
    }

    // Если уже загружается - дождаться
    if (this.loading.has(tabName)) {
      return this.loading.get(tabName);
    }

    // Если уже загружена - вернуть
    if (this.loaded.has(tabName)) {
      return true;
    }

    // Начать загрузку
    const loadPromise = this._performLoad(tabName);
    this.loading.set(tabName, loadPromise);

    try {
      const result = await loadPromise;
      this.loaded.add(tabName);
      return result;
    } finally {
      this.loading.delete(tabName);
    }
  }

  /**
   * Предварительная загрузка вкладки в фоне (не блокирует)
   */
  preloadTab(tabName) {
    if (!this.loaded.has(tabName) && !this.loading.has(tabName)) {
      this.loadTab(tabName).catch(e => {
        console.error(`[LazyTabLoader] Failed to preload ${tabName}:`, e);
      });
    }
  }

  /**
   * Проверяет загружена ли вкладка
   */
  isLoaded(tabName) {
    return this.loaded.has(tabName);
  }

  /**
   * Загружает вкладку и выполняет инициализацию
   */
  async _performLoad(tabName) {
    const tab = this.tabs.get(tabName);
    if (!tab) return false;

    try {
      // Показываем loader на вкладке
      this._showLoading(tabName);

      // Загружаем HTML
      const response = await fetch(tab.htmlUrl);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const html = await response.text();

      // Вставляем HTML в контейнер вкладки
      const container = document.getElementById(`tab-${tabName}`);
      if (!container) {
        throw new Error(`Container tab-${tabName} not found`);
      }

      container.innerHTML = html;
      this.cache.set(tabName, html);

      // Загружаем и выполняем JS
      if (tab.jsUrl) {
        await this._loadAndExecuteScript(tabName, tab.jsUrl);
      }

      // Скрываем loader
      this._hideLoading(tabName);

      // Вызываем init функцию если существует
      const initFuncName = this._getInitFunctionName(tabName);
      if (typeof window[initFuncName] === 'function') {
        console.log(`[LazyTabLoader] Calling ${initFuncName} for ${tabName}`);
        try {
          await window[initFuncName]();
        } catch (err) {
          console.error(`[LazyTabLoader] Error executing ${initFuncName}:`, err);
        }
      }

      console.log(`[LazyTabLoader] Successfully loaded tab: ${tabName}`);
      return true;
    } catch (e) {
      console.error(`[LazyTabLoader] Error loading tab ${tabName}:`, e);
      this._showError(tabName, e.message);
      return false;
    }
  }

  /**
   * Загружает и выполняет скрипт вкладки
   */
  _loadAndExecuteScript(tabName, jsUrl) {
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = jsUrl;
      script.type = 'module'; // Используем модули для современного подхода
      
      script.onload = () => {
        console.log(`[LazyTabLoader] Loaded JS for ${tabName}`);
        resolve();
      };
      
      script.onerror = (err) => {
        console.warn(`[LazyTabLoader] Note: No JS loaded for ${tabName} from ${jsUrl}`);
        resolve(); // Не падаем если нет JS
      };
      
      document.body.appendChild(script);
    });
  }

  /**
   * Вычисляет имя функции инициализации из имени вкладки
   */
  _getInitFunctionName(tabName) {
    const camelName = tabName.replace(/-([a-z])/g, (_, c) => c.toUpperCase());
    return 'init' + camelName.charAt(0).toUpperCase() + camelName.slice(1) + 'Tab';
  }

  /**
   * Показывает индикатор загрузки на вкладке
   */
  _showLoading(tabName) {
    const container = document.getElementById(`tab-${tabName}`);
    if (container) {
      container.innerHTML = `
        <div class="d-flex justify-content-center align-items-center" style="height: 300px;">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Загрузка...</span>
          </div>
        </div>
      `;
    }
  }

  /**
   * Скрывает индикатор загрузки
   */
  _hideLoading(tabName) {
    // После вставки содержимого loader уже заменен
  }

  /**
   * Показывает ошибку загрузки
   */
  _showError(tabName, errorMessage) {
    const container = document.getElementById(`tab-${tabName}`);
    if (container) {
      container.innerHTML = `
        <div class="alert alert-danger m-3" role="alert">
          <strong>Ошибка загрузки:</strong> ${errorMessage}
          <br><small class="text-muted">Вкладка: ${tabName}</small>
        </div>
      `;
    }
  }

  /**
   * Очищает кеш и загруженные вкладки
   */
  clear() {
    this.loaded.clear();
    this.cache.clear();
    this.loading.clear();
  }

  /**
   * Выгружает конкретную вкладку из памяти
   */
  unload(tabName) {
    this.loaded.delete(tabName);
    this.cache.delete(tabName);
    const container = document.getElementById(`tab-${tabName}`);
    if (container) {
      container.innerHTML = '';
    }
  }

  /**
   * Вспомогательный метод: загрузить несколько вкладок параллельно
   */
  async loadMultiple(tabNames) {
    return Promise.all(tabNames.map(name => this.loadTab(name)));
  }

  /**
   * Вспомогательный метод: предзагрузить несколько вкладок в фоне
   */
  preloadMultiple(tabNames) {
    tabNames.forEach(name => this.preloadTab(name));
  }
}

// Экспортируем глобально
window.LazyTabLoader = LazyTabLoader;

export default LazyTabLoader;
