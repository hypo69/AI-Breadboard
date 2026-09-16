/**
 * Admin Interface Main - Оркестратор
 * 
 * Главный модуль для инициализации административного интерфейса.
 * Все реальная реализация находится в модулях, этот файл только оркестрирует.
 * 
 * Модули:
 * - auth-handler.js: Аутентификация и проверка пароля
 * - tab-manager.js: Управление вкладками и навигацией
 * - ui-handler.js: Модали, уведомления, помощь
 * - init-interface.js: Инициализация компонентов
 * - apps-sync.js: Синхронизация приложений
 */

// ============================================================================
// ИМПОРТ МОДУЛЕЙ
// ============================================================================

import { setupAuthHandlers, verifyPassword } from './modules/auth-handler.js';
import { setupTabManagement, onTabSwitched } from './modules/tab-manager.js';
import { setupUIHandlers, showHelpModal, showNotification, showChatLogicModal } from './modules/ui-handler.js';
import { 
  initializeInterface, 
  setupGlobalFunctions, 
  setupLanguageSelector, 
  setupThemeSelector 
} from './modules/init-interface.js';
import { syncApplicationsVisibility } from './modules/apps-sync.js';

// ============================================================================
// ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ
// ============================================================================

let tabLoader = null;
let apiFetcher = null;

// ============================================================================
// ГЛАВНАЯ ФУНКЦИЯ ИНИЦИАЛИЗАЦИИ
// ============================================================================

async function initAdminInterface() {
  console.log('🚀 [AdminInterface] Starting initialization...');
  
  try {
    // 1. Инициализируем компоненты интерфейса
    console.log('[AdminInterface] Step 1: Initializing core components...');
    await initializeInterface();
    setupGlobalFunctions();
    setupLanguageSelector();
    setupThemeSelector();
    
    // 2. Регистрируем глобальные функции для UI
    console.log('[AdminInterface] Step 2: Setting up UI handlers...');
    registerGlobalFunctions();
    setupUIHandlers();
    setupAuthHandlers();
    
    // 3. Инициализируем управление вкладками
    console.log('[AdminInterface] Step 3: Setting up tab management...');
    setupTabManagement();
    
    // 4. Синхронизируем видимость приложений
    console.log('[AdminInterface] Step 4: Syncing applications visibility...');
    await syncApplicationsVisibility();
    
    // 5. Инициализируем оптимизации (ленивая загрузка, кеширование и т.д.)
    console.log('[AdminInterface] Step 5: Initializing optimizations...');
    await initializeOptimizations();
    
    // 6. Инициализируем API клиент
    console.log('[AdminInterface] Step 6: Setting up API client...');
    setupAPIClient();
    
    console.log('✅ [AdminInterface] Initialization complete!');
    
  } catch (error) {
    console.error('❌ [AdminInterface] Initialization error:', error);
    showNotification('Ошибка инициализации интерфейса: ' + error.message, 'danger');
  }
}

// ============================================================================
// РЕГИСТРАЦИЯ ГЛОБАЛЬНЫХ ФУНКЦИЙ
// ============================================================================

function registerGlobalFunctions() {
  window.switchTab = switchTab;
  window.onTabSwitched = onTabSwitched;
  window.showHelpModal = showHelpModal;
  window.showNotification = showNotification;
  window.showChatLogicModal = showChatLogicModal;
  window.verifyPassword = verifyPassword;
}

// ============================================================================
// УПРАВЛЕНИЕ ВКЛАДКАМИ
// ============================================================================

/**
 * Переключить на вкладку
 */
async function switchTab(targetId) {
  if (!targetId) return;

  const cleanId = targetId.startsWith('#') ? targetId.slice(1) : targetId;
  const tabName = cleanId.replace(/^tab-/, '');

  console.log(`[AdminInterface] Switching to tab: ${tabName}`);

  // Используем LazyTabLoader если доступен
  if (tabLoader && typeof tabLoader.isLoaded === 'function') {
    if (!tabLoader.isLoaded(tabName)) {
      console.log(`[AdminInterface] Loading tab: ${tabName}`);
      await tabLoader.loadTab(tabName);
    }
  }

  // Обновляем визуальное состояние
  updateTabUI(cleanId);

  // Вызываем callback
  if (typeof window.onTabSwitched === 'function') {
    window.onTabSwitched(cleanId);
  }

  console.log(`[AdminInterface] Tab switched: ${tabName}`);
}

/**
 * Обновить визуальное состояние UI
 */
function updateTabUI(cleanId) {
  // Скрываем все вкладки
  document.querySelectorAll('[role="tabpanel"]').forEach(tab => {
    tab.classList.remove('active', 'show');
    tab.setAttribute('aria-hidden', 'true');
  });

  // Показываем целевую вкладку
  const targetTab = document.getElementById(cleanId);
  if (targetTab) {
    targetTab.classList.add('active', 'show');
    targetTab.setAttribute('aria-hidden', 'false');
  }

  // Обновляем состояние кнопок
  document.querySelectorAll('[role="tab"]').forEach(tab => {
    tab.classList.remove('active');
    tab.setAttribute('aria-selected', 'false');
  });

  const targetButton = document.querySelector(`[aria-controls="${cleanId}"]`) ||
                      document.querySelector(`[data-bs-target="#${cleanId}"]`);
  if (targetButton) {
    targetButton.classList.add('active');
    targetButton.setAttribute('aria-selected', 'true');
  }
}

// ============================================================================
// ИНИЦИАЛИЗАЦИЯ ОПТИМИЗАЦИЙ
// ============================================================================

async function initializeOptimizations() {
  // Оптимизации автоматически инициализируются в lazy-init-patch.js
  // Здесь просто сохраняем ссылки для последующего использования
  
  if (window.optimizationModule) {
    tabLoader = window.optimizationModule.tabLoader;
    apiFetcher = window.optimizationModule.apiFetcher;
    console.log('[AdminInterface] Optimizations initialized');
  } else {
    console.warn('[AdminInterface] Optimization module not found');
  }
}

// ============================================================================
// ИНИЦИАЛИЗАЦИЯ API КЛИЕНТА
// ============================================================================

function setupAPIClient() {
  if (!window.api) {
    console.warn('[AdminInterface] API client not found, skipping setup');
    return;
  }

  // API клиент уже подключен в main.js (исходный), здесь могут быть
  // дополнительные настройки
  console.log('[AdminInterface] API client ready');
}

// ============================================================================
// ОБРАБОТКА СОБЫТИЯ LOAD
// ============================================================================

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initAdminInterface);
} else {
  initAdminInterface();
}

console.log('📦 [AdminInterface] Module loaded and ready');

// ============================================================================
// ЭКСПОРТЫ (для модульного использования)
// ============================================================================

export {
  initAdminInterface,
  switchTab,
  setupAuthHandlers,
  setupTabManagement,
  setupUIHandlers,
  syncApplicationsVisibility,
  initializeInterface,
  setupGlobalFunctions
};
