# Menu Systems Guide (Creation & Usage)

**Project:** `AI-Breadboard`  
**File:** [`docs/en/menus_guide.md`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/docs/en/menus_guide.md)  
**Status:** ✅ Up to date  
**Version:** 3.0  

This document provides complete instructions for creating, configuring, and interacting with all menu systems in AI-Breadboard.

For the full detailed specification, please refer to [`.ai/instructions/knowledge/MENU_CREATION_AND_USAGE_GUIDE.md`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/.ai/instructions/knowledge/MENU_CREATION_AND_USAGE_GUIDE.md).

---

## 🎯 Quick Reference by Environment

### 1. Web Administration Navigation (`/admin`)
- **File:** [`src/api/webinterface/admin/index.html`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/src/api/webinterface/admin/index.html) & [`main.js`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/src/api/webinterface/admin/main.js)
- **Menu Groups:**
  - Dialog & Audio (`#dialogTabsDropdown`)
  - AI & Knowledge (`#aiTabsDropdown`)
  - Plugins & Search (`#pluginsTabsDropdown`)
  - Applications (`#appsTabsDropdown`)
  - Administration (`#adminTabsDropdown`)
- **Adding Micro-Apps:** Follow the 6-step integration protocol from `CODE_RULES.md § 4.5`. Add item to `#appsTabsDropdown` with `data-tab="tab-<app-name>"` and wire dynamic loading into `admin/main.js`.

### 2. Web User Workspace Navigation (`/user`)
- **File:** [`src/api/webinterface/user/index.html`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/src/api/webinterface/user/index.html)
- **Components:** Model selector dropdown, prompt presets, voice input switch, CosmicPlayer media menu, chat history drawer.

### 3. Windows System Tray Context Menu
- **File:** [`launchers/ShowHide-InTray.ps1`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/launchers/ShowHide-InTray.ps1)
- **Items:** Open Web UI, Show/Hide Console, Restart Server, Service Status, Exit.
- **Technology:** `.NET System.Windows.Forms.ContextMenuStrip` + `NotifyIcon`.

### 4. CLI Command Menu Dispatcher
- **File:** [`manage_tools.py`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/manage_tools.py)
- **Usage:** `py manage_tools.py <group> <command> [args]` (Groups: `skills`, `rag`, `db`, `docs`, `models`, `app`).

### 5. Terminal Workspace Layout Selector
- **File:** [`launchers/Run-Terminals.ps1`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/launchers/Run-Terminals.ps1)
- **Usage:** `.\launchers\Run-Terminals.ps1 -Preset [breadboard|trading|network|custom] -Layout [grid|split|tabs|windows]`

### 6. Chrome Browser Extension Menus
- **Files:** [`extensions/chrome/manifest.json`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/extensions/chrome/manifest.json), [`background.js`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/extensions/chrome/background.js)
- **Items:** Action toolbar popup and selection context menu (`chrome.contextMenus`).

### 7. WordPress Companion Plugin Menus
- **Files:** [`wp/wp-content/plugins/ai-responder/admin/class-admin-settings.php`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/wp/wp-content/plugins/ai-responder/admin/class-admin-settings.php)
- **Hook:** `admin_menu` -> `add_menu_page()` and `add_submenu_page()`.
