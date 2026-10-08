<!--
=============================================================================
Process Name: AI-Breadboard UI - Architecture Specification
=============================================================================
Description:
  Архитектурный стандарт и спецификация построения веб-интерфейса AI-Breadboard.

Usage Examples:
  Документация и руководство разработчика:
    UI_ARCHITECTURE.md

File: UI_ARCHITECTURE.md
Project: ai-breadboard
Package: windows/api/webgui
Author: hypo69
Copyright: © 2026 hypo69
Updated: 2026-10-08 12:25:00
=============================================================================
-->

# UI Architecture — Стандарт построения веб-интерфейса

## 1. Архитектурный принцип

Каждая страница (`/`, `/tc`, `/su`, `/admin`, `/helpdesk`, `/chat`) — это **оболочка (shell)** с навигацией и набором **вкладок (tabs)**.
Все оболочки используют **единую логику** жизненного цикла и опросников из `js/tab-core.js`.

### 🗺️ Точки входа (Shells) и сценарии запуска

| URL Роут | Файл разметки (Shell) | Скрипт запуска | Конфигурация | Назначение |
|---|---|---|---|---|
| `/admin` | `admin/index.html` | `Run-Dashboard.ps1` | `config/dashboard.json` | Главная панель управления AI Breadboard (администрирование, RAG, модели, ReAct-агенты) |
| `/tc`, `/apps`, `/su` | `apps/index.html` | `Run-TC.ps1` / `su.ps1` | `config/tc_menu_config.json` | Хаб приложений Test Computer и консоль суперпользователя (диагностика, системный стек) |
| `/` | `apps/index.html` (или `user/index.html`) | `Run-UserAssistant.ps1` | `config/dashboard.json` | Пользовательский интерфейс и персональный ассистент (Telegram Mini App) |
| `/helpdesk` | `helpdesk/index.html` | `launchers/helpdesk.ps1` | `config.json` | Рабочее место службы поддержки (тикеты, операторы) |
| `/chat` | `chat/index.html` | `launchers/Run-Chat.ps1` | `config.json` | Автономный диалоговый интерфейс AI со стримингом токенов |

> [!IMPORTANT]
> **Принцип Active-Only & On-Demand Polling**:
> Только открытая **АКТИВНАЯ** вкладка опрашивает API по мере необходимости. При переключении на другую вкладку или скрытии окна браузера (`visibilitychange`) все периодические фоновые опросники (pollers) автоматически приостанавливаются.

---

## 2. Структура файлов и каталогов

```
apps/windows/api/webgui/
├── core/
│   └── tab-registry.js      ← Единый источник правды (SSOT) реестра всех вкладок, иконок, i18n и прав доступа
├── js/
│   ├── tab-core.js          ← ЕДИНСТВЕННЫЙ источник логики вкладок и поллинга (switchTab, registerTabPoller, loadTab, setupTabClicks)
│   ├── i18n.js              ← Интернационализация (i18next)
│   ├── theme-engine.js      ← Движок переключения тем (светлая/тёмная/системная)
│   ├── userSettings.js      ← Персональные настройки пользователя
│   ├── model-tester.js      ← Быстрый пинг и проверка доступности модели ИИ
│   ├── api-cache.js         ← Клиентское кэширование запросов API
│   ├── toast.js             ← Централизованные всплывающие уведомления
│   └── main.js              ← Оркестратор для главной страницы
│
├── ai_modal_dialog/         ← Универсальный компонент модального окна AI-анализатора и WikiLLM
│   ├── index.html           ← Шаблон разметки диалоговых окон
│   ├── main.js              ← Контроллер диалога (AIModalDialog / AITableModal)
│   ├── style.css            ← Стили и визуальные эффекты всплывающего окна
│   └── README.md            ← Документация компонента
│
├── apps/
│   ├── index.html           ← Оболочка для /tc, /apps, /su
│   ├── main.js              ← Оркестратор для /tc (Lazy Load per tab)
│   └── modules/
│       ├── tabs-config.js   ← Локальный реестр путей вкладок /tc
│       ├── status-manager.js← Мониторинг статусов приложений и бейджа модели
│       └── init-interface.js← Инициализация тем, API и языков
│
└── <name>_tab/              ← Каждая вкладка — изолированная папка
    ├── index.html           ← Только HTML-разметка вкладки (без тегов <script>)
    └── main.js              ← Логика вкладки: window.init<Name>Tab() и registerTabPoller()
```

---

## 3. Контракт HTML (одинаков для всех оболочек)

### Кнопка меню
```html
<button type="button" data-tab="tab-xxx">...</button>
```
- Атрибут `data-tab` — единственный способ указать целевую вкладку.
- Работает в любом месте страницы: верхнее меню, боковое меню (Offcanvas), ссылки внутри вкладок.
- **Запрещено** использовать `data-bs-target`, `onclick`, `href` для переключения вкладок.

### Панель вкладки
```html
<div id="tab-xxx" class="tab-pane fade"></div>
```
- ID всегда имеет префикс `tab-{name}`.
- Контейнер: `<div id="mainTabContent" class="tab-content">`.

### Бейдж активного раздела
```html
<span id="active-tab-title-badge">...</span>
```
- Обновляется автоматически при вызове `switchTab`.

### Offcanvas (боковое меню)
```html
<div class="offcanvas" id="appsSideNavOffcanvas">   <!-- /tc, /apps -->
<div class="offcanvas" id="leftSideNavOffcanvas">   <!-- / -->
```
- Закрывается автоматически при `switchTab`.

---

## 4. `tab-core.js` — API управления вкладками и поллингом

```js
import { 
  switchTab, 
  loadTab, 
  setupTabClicks, 
  registerTabPoller, 
  unregisterTabPoller, 
  setTabPollerEnabled, 
  isTabActive 
} from '/html/js/tab-core.js';
```

### 4.1. Переключение и ленивая загрузка
```js
// Переключить вкладку
switchTab('tab-system-inspector');
switchTab('system-inspector');  // префикс tab- добавляется автоматически

// Загрузить HTML+JS вкладки по требованию (Lazy Load)
await loadTab('system-inspector', '/html/system_inspector_tab/index.html?v=20261008_v1', '/html/system_inspector_tab/main.js?v=20261008_v1');

// Повесить обработчик кликов (вызывается один раз при инициализации оболочки)
setupTabClicks();
```

### 4.2. Регистрация периодического опросника (Active-Only Poller)
Вместо небезопасного `setInterval(...)` внутри вкладок строго используется:
```js
// Зарегистрировать периодический опрос для вкладки
window.registerTabPoller('tab-system-inspector', async () => {
  await fetchSensorsData();
}, 3000, { immediate: true });

// Управление тумблером Live-режима (включение/отключение поллера)
window.setTabPollerEnabled('tab-system-inspector_default', isLiveModeActive);

// Проверка активности вкладки
if (window.isTabActive('tab-system-inspector')) {
  // Выполнить действие
}
```

### Автоматическое поведение:
1. При переключении с Вкладки A на Вкладку B:
   - Все опросники Вкладки A **мгновенно останавливаются**.
   - Вызывается хук деактивации `window.deactivate<OldName>Tab?.()` и событие `tab:deactivated`.
   - Вкладка B становится активной, её опросники запускаются и делают свежий запрос данных.
   - Вызывается `window.init<NewName>Tab?.()` / `window.activate<NewName>Tab?.()` и событие `tab:activated`.
2. При сворачивании браузера или переключении на другую вкладку браузера (`document.visibilitychange`):
   - Все фоновые опросники **засыпают**.
   - При возвращении пользователя в окно — активная вкладка немедленно возобновляет работу.

---

## 5. Жизненный цикл вкладки

Каждая вкладка — папка `<name>_tab/` с двумя файлами:

**`index.html`** — только разметка, без `<script>` тегов.

**`main.js`** — экспортирует функции жизненного цикла:
```js
window.initAboutSystemTab = function() {
  bindEvents();
  // Первичная отрисовка данных
  fetchSystemSummary();

  // Регистрация опросника, тикающего ТОЛЬКО пока вкладка на экране
  window.registerTabPoller('tab-about-system', async () => {
    await pollLiveTelemetry();
  }, 3000, { immediate: true });
};

// Опциональный хук очистки при уходе с вкладки
window.deactivateAboutSystemTab = function() {
  cleanupCharts();
};
```

### Соглашение об именовании:
- Папка: `system_inspector_tab/`
- Функции: `window.initSystemInspectorTab()`, `window.deactivateSystemInspectorTab()`
- ID панели: `tab-system-inspector`
- Атрибут кнопки: `data-tab="tab-system-inspector"`

---

## 6. Единый реестр вкладок (`core/tab-registry.js`)

`core/tab-registry.js` выступает единым источником правды (SSOT) для метаданных всех доступных вкладок экосистемы:

```js
import { TAB_DEFINITIONS, TabRegistry } from '/html/core/tab-registry.js';

// Получение метаданных вкладки
const tabDef = TabRegistry.getById('system_inspector');
// Локализованный заголовок
const label = TabRegistry.getLabel(tabDef);
// Фильтрация по роли пользователя и доступности сервисов
const visibleTabs = TabRegistry.getFiltered(appsStatusMap, 'admin');
```

---

## 7. Конфигурация меню (`config/tc_menu_config.json`)

Описывает структуру быстрого верхнего бара и бокового меню Offcanvas для `/tc`:

```json
{
  "menu": {
    "topButtons": [
      { "id": "system_inspector", "tab": "tab-hardware-load-inspector", "icon": "bi-graph-up-arrow", "label": "Ресурсы", "order": 1, "visible": true }
    ],
    "sidebarItems": [
      { "id": "about_system", "tab": "tab-about-system", "icon": "ℹ️", "label": "О Системе", "i18n": "tabs.aboutSystem", "order": 1, "visible": true }
    ]
  }
}
```

---

## 8. Оркестратор страницы (шаблон `main.js`)

```js
import { switchTab, loadTab, setupTabClicks } from '../js/tab-core.js';
import { setupThemeAndLang } from './modules/init-interface.js';

window.switchTab = switchTab;

setupTabClicks();

async function init() {
  // 1. Инициализация темы и локализации
  await setupThemeAndLang();

  // 2. Определение стартовой вкладки из hash или конфигурации
  const initialTab = window.location.hash.replace('#', '') || 'tab-about-system';

  // 3. Переключение на стартовую вкладку с ленивой загрузкой
  await switchTab(initialTab);
}

document.readyState === 'loading'
  ? document.addEventListener('DOMContentLoaded', init)
  : init();
```

---

## 9. Правила разработки UI

| Правило | Обоснование |
|---|---|
| Только `data-tab` для навигации | Единый прозрачный механизм переключения без побочных эффектов. |
| `setupTabClicks()` вызывается один раз | Предотвращение дублирования обработчиков событий в DOM. |
| Поллинг строго через `registerTabPoller` | Исключает утечки ресурсов и фоновую нагрузку на CPU/API. |
| Ленивая загрузка (Lazy Loading) | Мгновенный первый запуск оболочки без загрузки всех 30+ вкладок. |
| Cache-Busting через `?v=YYYYMMDD_vN` | Гарантия получения свежих версий скриптов и стилей клиентом. |
| Запрет `data-bs-target` для переключения вкладок | Bootstrap Tab API отключен в пользу управляемого `tab-core.js`. |
| Локализация через `i18next` | Все пользовательские тексты должны содержать i18n ключи в `locales/`. |

---

## 10. Диагностика и проверка работоспособности

Кнопка навигации и вкладка функционируют корректно, если:
1. У кнопки задан атрибут `data-tab="tab-xxx"`.
2. В DOM присутствует контейнер `<div id="tab-xxx" class="tab-pane">`.
3. Вызвана инициализация `setupTabClicks()`.
4. Глобальная функция `window.switchTab` доступна.

### Проверка в консоли разработчика браузера:
```js
window.switchTab('tab-system-inspector');     // Должно переключить вкладку и активировать поллер
document.getElementById('tab-system-inspector'); // Должен вернуть DOM-контейнер вкладки
document.querySelector('[data-tab="tab-system-inspector"]'); // Должен вернуть кнопку вызова
```
