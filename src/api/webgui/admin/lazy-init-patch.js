/**
 * Lazy Init Patch - Патч для переключения на ленивую загрузку вкладок
 * 
 * Этот скрипт перехватывает инициализацию main.js и использует
 * LazyTabLoader вместо стандартной загрузки всех вкладок сразу
 */

import { 
  initLazyTabLoading, 
  enhanceTabSwitching, 
  restoreLastTab 
} from './optimization-init.js';
import { autoPatchTab } from '../js/tab-debounce-auto-patch.js';
import TabStatePersistence from '../js/tab-state-persistence.js';
import TabSwitchOptimizer from '../js/tab-switch-optimizer.js';

console.log('[LazyInitPatch] Patching admin interface initialization...');

// Инициализируем persistence для админки
const tabPersistence = new TabStatePersistence('admin');
window.tabPersistence = tabPersistence;

// Ждем когда main.js загрузится и инициализирует базовые элементы
window.addEventListener('load', async () => {
  console.log('[LazyInitPatch] Window load event, initializing lazy loading...');

  // Ждем немного чтобы main.js выполнил свои скрипты
  await new Promise(resolve => setTimeout(resolve, 100));

  // Если есть оригинальная функция switchTab, оборачиваем ее
  if (window.switchTab && typeof window.switchTab === 'function') {
    const originalSwitchTab = window.switchTab;
    
    // Применяем оптимизацию переключения
    const switchOptimizer = new TabSwitchOptimizer();
    switchOptimizer.enableDOMCaching();
    
    // Оборачиваем в enhanced версию с lazy loading
    let enhancedSwitchTab = enhanceTabSwitching(originalSwitchTab);
    
    // Оборачиваем в optimizer версию для отслеживания производительности
    const optimizedSwitchTab = switchOptimizer.optimizeSwitching(enhancedSwitchTab);
    
    window.switchTab = async function(targetId) {
      // Вызываем оптимизированную функцию
      await optimizedSwitchTab.call(this, targetId);
      
      // Сохраняем активную вкладку
      if (targetId) {
        const cleanId = targetId.startsWith('#') ? targetId.slice(1) : targetId;
        tabPersistence.saveActiveTab(cleanId);
      }
    };
    
    console.log('[LazyInitPatch] Enhanced switchTab with on-demand lazy loading and persistence');
  }

  // Инициализируем ленивую загрузку с определением всех вкладок
  const allTabDefinitions = [
    // Основные вкладки (Диалог и аудио)
    { tabName: 'chat', htmlUrl: `/html/chat/index.html`, jsUrl: `/html/chat/main.js` },
    { tabName: 'voice', htmlUrl: `/html/voice_tab/index.html`, jsUrl: `/html/voice_tab/main.js` },
    { tabName: 'tts', htmlUrl: `/html/tts_tab/index.html`, jsUrl: `/html/tts_tab/main.js` },
    
    // ИИ и Знания
    { tabName: 'rag', htmlUrl: `/html/rag_tab/index.html`, jsUrl: `/html/rag_tab/main.js` },
    { tabName: 'models', htmlUrl: `/html/models_tab/index.html`, jsUrl: `/html/models_tab/main.js` },
    { tabName: 'agents', htmlUrl: `/html/agents_tab/index.html`, jsUrl: `/html/agents_tab/main.js` },
    { tabName: 'skills', htmlUrl: `/html/skills_tab/index.html`, jsUrl: `/html/skills_tab/main.js` },
    { tabName: 'mcp', htmlUrl: `/html/mcp_tab/index.html`, jsUrl: `/html/mcp_tab/main.js` },
    { tabName: 'observability', htmlUrl: `/html/system_inspector_tab/index.html`, jsUrl: `/html/system_inspector_tab/main.js` },
    { tabName: 'telegram-rag', htmlUrl: `/html/telegram_rag_tab/index.html`, jsUrl: `/html/telegram_rag_tab/main.js` },
    { tabName: 'sources', htmlUrl: `/html/sources_tab/index.html`, jsUrl: `/html/sources_tab/main.js` },
    { tabName: 'search', htmlUrl: `/html/search_tab/index.html`, jsUrl: `/html/search_tab/main.js` },
    
    // Система и Администратор
    { tabName: 'admin', htmlUrl: `/html/admin_tab/index.html`, jsUrl: `/html/admin_tab/main.js` },
    { tabName: 'users', htmlUrl: `/html/users_tab/index.html`, jsUrl: `/html/users_tab/main.js` },
    { tabName: 'plugins', htmlUrl: `/html/plugins_tab/index.html`, jsUrl: `/html/plugins_tab/main.js` },
    { tabName: 'google-accounts', htmlUrl: `/html/google_accounts_tab/index.html`, jsUrl: `/html/google_accounts_tab/main.js` },
    { tabName: 'instructions', htmlUrl: `/html/instructions_tab/index.html`, jsUrl: `/html/instructions_tab/main.js` },
    { tabName: 'news', htmlUrl: `/html/news_tab/index.html`, jsUrl: `/html/news_tab/main.js` },
    { tabName: 'logs', htmlUrl: `/html/logs/index.html`, jsUrl: `/html/logs/main.js` },
    { tabName: 'help', htmlUrl: `/html/help/index.html`, jsUrl: `/html/help/main.js` },
    
    // Микроприложения (с привязкой к ID приложения в конфиге профиля)
    { tabName: 'trading', appId: 'trading_terminal', htmlUrl: `/html/trading_tab/index.html`, jsUrl: `/html/trading_tab/main.js` },
    { tabName: 'network', appId: 'network_terminal', htmlUrl: `/html/network_tab/index.html`, jsUrl: `/html/network_tab/main.js` },
    { tabName: 'system-inspector', appId: 'system_inspector', htmlUrl: `/html/system_inspector_tab/index.html`, jsUrl: `/html/system_inspector_tab/main.js` },
    { tabName: 'about-system', appId: 'about_system', htmlUrl: `/html/about_system_tab/index.html?v=20260924_v7`, jsUrl: `/html/about_system_tab/main.js?v=20260924_v7` },
    { tabName: 'windows-admin', appId: 'windows_sysadmin', htmlUrl: `/html/windows_admin_tab/index.html`, jsUrl: `/html/windows_admin_tab/main.js` },
    { tabName: 'cloudflared', appId: 'cloudflared_monitor', htmlUrl: `/html/cloudflared_tab/index.html`, jsUrl: `/html/cloudflared_tab/main.js` },
    { tabName: 'user-assistant', appId: 'user_assistant', htmlUrl: `/html/user_assistant_tab/index.html`, jsUrl: `/html/user_assistant_tab/main.js` },
    { tabName: 'gcloud', appId: 'gcloud_monitor', htmlUrl: `/html/gcloud_tab/index.html`, jsUrl: `/html/gcloud_tab/main.js` },
    { tabName: 'website-monitor', appId: 'website_monitor', htmlUrl: `/html/website_monitor_tab/index.html`, jsUrl: `/html/website_monitor_tab/main.js` },
    { tabName: 'system-control', appId: 'system_control_center', htmlUrl: `/html/system_control_tab/index.html?v=20260924_v1`, jsUrl: `/html/system_control_tab/main.js?v=20260924_v1` },
    { tabName: 'system-logs', appId: 'system_log_viewer', htmlUrl: `/html/system_logs_tab/index.html`, jsUrl: `/html/system_logs_tab/main.js` },
    { tabName: 'software-audit', appId: 'software_audit', htmlUrl: `/html/software_audit_tab/index.html`, jsUrl: `/html/software_audit_tab/main.js` },
    { tabName: 'registry-viewer', appId: 'registry_viewer', htmlUrl: `/html/registry_viewer_tab/index.html`, jsUrl: `/html/registry_viewer_tab/main.js` },
    { tabName: 'startup-auditor', appId: 'windows_startup_auditor', htmlUrl: `/html/startup_auditor_tab/index.html`, jsUrl: `/html/startup_auditor_tab/main.js` },
    { tabName: 'windows-backup', appId: 'windows_backup_manager', htmlUrl: `/html/windows_backup_tab/index.html?v=20260924_v2`, jsUrl: `/html/windows_backup_tab/main.js?v=20260924_v2` },
    { tabName: 'wikipedia-research', appId: 'wikipedia_research', htmlUrl: `/html/wikipedia_research_tab/index.html`, jsUrl: `/html/wikipedia_research_tab/main.js` },
    { tabName: 'process-leaks', appId: 'process_leaks', htmlUrl: `/html/process_leaks_tab/index.html?v=20260924_v1`, jsUrl: `/html/process_leaks_tab/main.js?v=20260924_v1` },
    { tabName: 'forensics', appId: 'forensics', htmlUrl: `/html/forensics_tab/index.html?v=20260924_v1`, jsUrl: `/html/forensics_tab/main.js?v=20260924_v1` },
    { tabName: 'throttling', appId: 'throttling', htmlUrl: `/html/throttling_tab/index.html?v=20260924_v1`, jsUrl: `/html/throttling_tab/main.js?v=20260924_v1` },
    { tabName: 'storage-wear', appId: 'storage_wear', htmlUrl: `/html/storage_wear_tab/index.html?v=20260924_v1`, jsUrl: `/html/storage_wear_tab/main.js?v=20260924_v1` },
    { tabName: 'peripherals', appId: 'peripherals', htmlUrl: `/html/peripherals_tab/index.html?v=20260924_v1`, jsUrl: `/html/peripherals_tab/main.js?v=20260924_v1` },
  ];

  try {
    // Получаем статус приложений для активного сценария (Run-Dashboard, Run-TC, su)
    let appsStatus = window.appsStatusMap || null;
    if (!appsStatus) {
      try {
        const res = await (window.api ? window.api.fetch('/api/apps/status') : fetch('/api/apps/status').then(r => r.json()));
        appsStatus = res?.apps || null;
      } catch (err) {
        console.warn('[LazyInitPatch] Could not fetch apps status for profile filtering:', err);
      }
    }

    // Фильтруем вкладки: загружаем ТОЛЬКО те, которые разрешены в активном профиле конфига
    const activeTabDefinitions = allTabDefinitions.filter(tab => {
      if (tab.appId && appsStatus) {
        const appInfo = appsStatus[tab.appId] || Object.values(appsStatus).find(a => a.id === tab.appId || a.tab === `tab-${tab.tabName}`);
        if (appInfo && appInfo.enabled === false) {
          return false; // Отключено в активном сценарии/профиле
        }
      }
      return true;
    });

    // Инициализируем систему ленивой загрузки только для разрешенных в профиле вкладок
    await initLazyTabLoading(activeTabDefinitions);
    
    console.log(`[LazyInitPatch] Lazy loading initialized: ${activeTabDefinitions.length} tabs registered on-demand.`);

    // Восстанавливаем и загружаем ТОЛЬКО одну активную вкладку
    const restored = await restoreLastTab('tab-about-system');
    console.log(`[LazyInitPatch] Initial active tab loaded: ${restored}`);

  } catch (error) {
    console.error('[LazyInitPatch] Error during initialization:', error);
  }
});

console.log('[LazyInitPatch] Patch loaded successfully');

export {};
