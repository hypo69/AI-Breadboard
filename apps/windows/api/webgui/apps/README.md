# Веб-интерфейс центра приложений (`/apps` и `/tc`)

## 📋 Обзор
Центр приложений (`/apps`, а также профиль Test Computer `/tc`) предоставляет модульный веб-интерфейс для запуска, мониторинга и тестирования микроприложений и системных утилит платформы AI Breadboard.

## 🏗️ Модульная архитектура фронтенда
Интерфейс построен по принципу тонкого оркестратора без монолитного кода:
- **`main.js`**: Тонкий оркестратор инициализации интерфейса и загрузки активных вкладок.
- **`modules/status-manager.js`**: Асинхронное получение статуса приложений через `/api/apps/status` и активной модели ИИ через `/api/chat/active-model`.
- **`modules/tab-manager.js`**: Управление переключением, навигацией и ленивой загрузкой контента вкладок.
- **`modules/tabs-config.js`**: Декларативный реестр вкладок (`APP_TAB_DEFS`) и правил исключения (`TC_EXCLUDES`).
- **`modules/init-interface.js`**: Инициализация темы, локализации (i18n) и безопасной обертки API.

## 💡 Особенности и возможности
1. **Динамический бейдж модели ИИ (`#apps-model-badge`):**
   - Получает имя активной модели и провайдера динамически из FastAPI бэкенда (`/api/chat/active-model` и `/api/apps/status`).
   - Исключает хардкод: отображает реальные данные активного профиля (`config_tc.json` или `config.json`).
2. **Переключатель режимов:**
   - Быстрый переход между **Test Computer (`/tc`)** и **Админ-панелью (`/admin`)**.
3. **Автоматический выбор протокола:**
   - При запуске `tc.ps1` или `run.ps1 -TestComputer` считывается протокол из `config_tc.json` (`http`, без SSL).
   - При основном запуске `run.ps1` используется протокол из `config.json` (`https` с сертификатами SSL).
4. **Интернационализация и темы:**
   - Поддержка языков (RU, EN, HE) и переключение светлой/тёмной темы.
5. **Делегирование событий меню (исправлено):**
   - Кнопки верхнего меню и бокового меню используют делегирование событий через родительский контейнер.
   - Это обеспечивает корректную работу кнопок, созданных динамически из `tc_menu_config.json`.

## ⚠️ Известные особенности архитектуры

### Динамическая генерация меню и делегирование событий

**Проблема (исправлена в сентябре 2026):** Кнопки верхнего меню `/tc` не открывали приложения.

**Причина:** Меню генерируется в два этапа:
1. `index.html` рендерит статические кнопки-заглушки.
2. `initMenuFromConfig()` (инлайн-скрипт в `index.html`) асинхронно загружает `tc_menu_config.json` и **перезаписывает** контейнер через `innerHTML = ''` + `appendChild`, создавая новые кнопки.

Старый код в `setupTopMenuButtons()`, `setupSidebarButtons()` и `setupNavTabs()` привязывал обработчики `click` напрямую к кнопкам, существовавшим в DOM **до** динамической генерации. Новые кнопки обработчиков не получали.

**Решение:** Все три функции переведены на **делегирование событий** — обработчик вешается на неизменяемый родительский контейнер и перехватывает клики по любым дочерним кнопкам через `e.target.closest()`:

```javascript
// ✅ Делегирование — работает для динамически созданных кнопок
function setupTopMenuButtons() {
  const topMenuContainer = document.querySelector('.main-nav-container .d-flex.gap-1.flex-wrap');
  if (topMenuContainer) {
    topMenuContainer.addEventListener('click', (e) => {
      const btn = e.target.closest('button[data-tab]');
      if (btn) switchTab(btn.getAttribute('data-tab'));
    });
  }
}

// ❌ Прямая привязка — не работает для динамических кнопок (старый код)
function setupTopMenuButtons() {
  document.querySelectorAll('.main-nav-container button[data-tab]').forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.getAttribute('data-tab')));
  });
}
```

**Затронутые файлы:**
- `apps/main.js` — `setupTopMenuButtons()`, `setupSidebarButtons()`
- `apps/modules/tab-manager.js` — `setupNavTabs()`

**Тесты:** `tests/test_tc_menu_event_delegation.py` — 19 тестов, 6 категорий.

## 🗂️ Файлы

- `index.html` — Разметка интерфейса, инлайн-скрипты инициализации меню и бейджа модели
- `main.js` — Оркестратор: инициализация, загрузка вкладок, делегирование событий меню
- `modules/init-interface.js` — Тема, язык, глобальный API
- `modules/status-manager.js` — Статус приложений, бейдж активной модели
- `modules/tab-manager.js` — Переключение вкладок, ленивая загрузка контента
- `modules/tabs-config.js` — Реестр вкладок `APP_TAB_DEFS`, список исключений `TC_EXCLUDES`
- `config/tc_menu_config.json` — Конфигурация кнопок верхнего и бокового меню

## 🧪 Тесты

```bash
pytest tests/test_tc_menu_event_delegation.py -v
```

## 🔗 Ссылки

- [`../../.ai/instructions/standards/DOCUMENTATION.md`](../../.ai/instructions/standards/DOCUMENTATION.md) — Стандарты документирования
- [`../../.ai/instructions/workflows/TDD.md`](../../.ai/instructions/workflows/TDD.md) — TDD workflow
