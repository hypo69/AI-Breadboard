/**
 * Users Tab Debounce Patch
 * 
 * Применяет улучшенный дебаунс к поиску пользователей,
 * используя RequestManager для снижения нагрузки на сервер
 */

import { createUserSearchDebounce } from '../js/debounce-integration.js';

// Ждем загрузки основного скрипта
if (window.initUsersTab) {
  const originalInitUsersTab = window.initUsersTab;

  window.initUsersTab = async function() {
    // Вызываем оригинальную функцию
    await originalInitUsersTab.apply(this, arguments);

    console.log('[UsersDebouncePatch] Patching users tab search...');

    // После инициализации, патчим поиск
    setTimeout(() => {
      const searchInput = document.getElementById('users-search-input');
      
      if (searchInput && window.globalRequestManager) {
        // Сохраняем оригинальный обработчик
        const listeners = searchInput._eventListeners?.input || [];
        
        // Удаляем старые обработчики
        searchInput.replaceWith(searchInput.cloneNode(true));
        const newSearchInput = document.getElementById('users-search-input');

        // Добавляем новый дебаунсированный обработчик
        newSearchInput.addEventListener('input', (e) => {
          const val = e.target.value;
          const searchClear = document.getElementById('users-search-clear');
          
          if (searchClear) {
            searchClear.classList.toggle('d-none', !val);
          }

          // Используем улучшенный дебаунс
          window.globalRequestManager.debounce(
            'user-search-optimized',
            async () => {
              // Обновляем state поиска (симуляция)
              if (window.updateUserSearch) {
                window.updateUserSearch(val.trim());
              }
            },
            500
          ).catch(e => console.error('Search debounce error:', e));
        });

        // Обновляем кнопку очистки
        const searchClear = document.getElementById('users-search-clear');
        if (searchClear) {
          searchClear.onclick = () => {
            newSearchInput.value = '';
            searchClear.classList.add('d-none');
            if (window.updateUserSearch) {
              window.updateUserSearch('');
            }
          };
        }

        console.log('[UsersDebouncePatch] Users tab search patched with RequestManager debounce');
      }
    }, 500);
  };
}

// Альтернативный подход: Если users tab уже загружена, патчим сразу
if (document.getElementById('users-search-input')) {
  console.log('[UsersDebouncePatch] Users tab already loaded, applying patch immediately...');
  
  const searchInput = document.getElementById('users-search-input');
  const searchClear = document.getElementById('users-search-clear');

  // Создаем новый дебаунсированный обработчик
  const debouncedSearch = createUserSearchDebounce(async (query) => {
    console.log(`[UsersDebouncePatch] Executing debounced search for: ${query}`);
    // Обновляем UI через существующую функцию если она есть
    if (window.updateUserSearch) {
      await window.updateUserSearch(query);
    }
  });

  // Заменяем обработчик
  searchInput.replaceWith(searchInput.cloneNode(true));
  const newSearchInput = document.getElementById('users-search-input');

  newSearchInput.addEventListener('input', (e) => {
    const val = e.target.value;
    
    if (searchClear) {
      searchClear.classList.toggle('d-none', !val);
    }

    debouncedSearch(val.trim());
  });

  if (searchClear) {
    searchClear.addEventListener('click', () => {
      newSearchInput.value = '';
      searchClear.classList.add('d-none');
      debouncedSearch('');
    });
  }

  console.log('[UsersDebouncePatch] Search debouncing initialized');
}

export {};
