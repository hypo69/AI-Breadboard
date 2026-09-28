/**
 * TabRegistry – единый источник правды (SSOT) для всех вкладок WebGUI.
 * Экспортирует методы getAll(), getById(id), getFiltered(appsStatusMap, role).
 */
export const TAB_DEFINITIONS = [];

export class TabRegistry {
  static getAll() { return TAB_DEFINITIONS; }
  static getById(tabId) {
    const clean = tabId.replace(/^tab-/, '');
    return TAB_DEFINITIONS.find(t => t.id === clean || t.appId === clean);
  }
  static getFiltered(appsStatusMap = null, targetRole = 'admin') {
    return TAB_DEFINITIONS.filter(tab => {
      if (!tab.roles?.includes(targetRole)) return false;
      if (tab.appId && appsStatusMap && appsStatusMap[tab.appId]) {
        return appsStatusMap[tab.appId].enabled !== false;
      }
      return true;
    });
  }
}
