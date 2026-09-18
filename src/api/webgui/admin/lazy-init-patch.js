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
        
        // Предзагружаем соседние вкладки
        switchOptimizer.preloadAdjacentTabs(cleanId);
      }
    };
    
    console.log('[LazyInitPatch] Enhanced switchTab with lazy loading, persistence, and performance optimization');
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
    
    // Микроприложения
    { tabName: 'trading', htmlUrl: `/html/trading_tab/index.html`, jsUrl: `/html/trading_tab/main.js` },
    { tabName: 'network', htmlUrl: `/html/network_tab/index.html`, jsUrl: `/html/network_tab/main.js` },
    { tabName: 'system-inspector', htmlUrl: `/html/system_inspector_tab/index.html`, jsUrl: `/html/system_inspector_tab/main.js` },
    { tabName: 'about-system', htmlUrl: `/html/about_system_tab/index.html`, jsUrl: `/html/about_system_tab/main.js` },
    { tabName: 'windows-admin', htmlUrl: `/html/windows_admin_tab/index.html`, jsUrl: `/html/windows_admin_tab/main.js` },
    { tabName: 'cloudflared', htmlUrl: `/html/cloudflared_tab/index.html`, jsUrl: `/html/cloudflared_tab/main.js` },
    { tabName: 'user-assistant', htmlUrl: `/html/user_assistant_tab/index.html`, jsUrl: `/html/user_assistant_tab/main.js` },
    { tabName: 'gcloud', htmlUrl: `/html/gcloud_tab/index.html`, jsUrl: `/html/gcloud_tab/main.js` },
    { tabName: 'website-monitor', htmlUrl: `/html/website_monitor_tab/index.html`, jsUrl: `/html/website_monitor_tab/main.js` },
    { tabName: 'system-control', htmlUrl: `/html/system_control_tab/index.html`, jsUrl: `/html/system_control_tab/main.js` },
    { tabName: 'system-logs', htmlUrl: `/html/system_logs_tab/index.html`, jsUrl: `/html/system_logs_tab/main.js` },
    { tabName: 'software-audit', htmlUrl: `/html/software_audit_tab/index.html`, jsUrl: `/html/software_audit_tab/main.js` },
    { tabName: 'registry-viewer', htmlUrl: `/html/registry_viewer_tab/index.html`, jsUrl: `/html/registry_viewer_tab/main.js` },
    { tabName: 'wikipedia-research', htmlUrl: `/html/wikipedia_research_tab/index.html`, jsUrl: `/html/wikipedia_research_tab/main.js` },
  ];

  try {
    // Инициализируем систему ленивой загрузки
    const { priorityTabs, restTabs } = await initLazyTabLoading(allTabDefinitions);
    
    console.log(`[LazyInitPatch] Lazy loading initialized`);
    console.log(`  Priority tabs loaded: ${priorityTabs.join(', ')}`);
    console.log(`  Remaining tabs will load in background: ${restTabs.length} tabs`);

    // Восстанавливаем последнюю открытую вкладку
    const restored = await restoreLastTab('tab-about-system');
    console.log(`[LazyInitPatch] Last tab restored: ${restored}`);

  } catch (error) {
    console.error('[LazyInitPatch] Error during initialization:', error);
  }
});

console.log('[LazyInitPatch] Patch loaded successfully');

export {};
