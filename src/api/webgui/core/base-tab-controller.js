/**
 * BaseTabController – базовый класс для всех контроллеров вкладок WebGUI.
 * Предоставляет жизненный цикл и вспомогательные методы (mount, unmount, событие, поллеры, API).
 */
import { registerTabPoller, unregisterAllTabPollers } from './tab-core.js';
import { cachedApiFetch } from './api-cache.js';

export class BaseTabController {
  constructor(tabId) {
    this.tabId = tabId.startsWith('tab-') ? tabId : `tab-${tabId}`;
    this.container = null;
    this.eventCleanups = [];
    this.isMounted = false;
  }

  async mount(container) {
    this.container = container;
    this.isMounted = true;
    this.bindEvents();
    await this.onInit();
  }

  unmount() {
    this.eventCleanups.forEach(c => c());
    this.eventCleanups = [];
    unregisterAllTabPollers(this.tabId);
    this.isMounted = false;
  }

  onActivate() {}
  onDeactivate() {}
  async onInit() {}
  bindEvents() {}

  addEventListener(el, ev, handler) {
    if (!el) return;
    el.addEventListener(ev, handler);
    this.eventCleanups.push(() => el.removeEventListener(ev, handler));
  }

  registerPoller(pollFn, intervalMs = 3000, options = {}) {
    return registerTabPoller(this.tabId, pollFn, intervalMs, options);
  }

  async fetch(url, opts = {}, cacheOpts = {}) {
    return cachedApiFetch(url, opts, cacheOpts);
  }
}
