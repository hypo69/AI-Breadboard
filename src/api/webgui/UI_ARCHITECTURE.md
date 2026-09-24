# UI Architecture — Стандарт построения веб-интерфейса

## Принцип

Каждая страница (`/`, `/tc`, `/su`, `/admin`, `/helpdesk`, `/chat`) — это **оболочка (shell)** с навигацией и набором **вкладок (tabs)**.
Все оболочки используют **одну и ту же логику** из `js/tab-core.js`.

### 🗺️ Точки входа (Shells) и сценарии запуска

| URL Роут | Файл разметки (Shell) | Скрипт запуска | Конфигурация | Назначение |
|---|---|---|---|---|
| `/admin` | `src/api/webgui/admin/index.html` | `Run-Dashboard.ps1` | `config/dashboard.json` | Главная панель управления AI Breadboard (администрирование, RAG, агенты) |
| `/tc` | `src/api/webgui/apps/index.html` | `Run-TC.ps1` | `config/tc.json` | Хаб приложений Test Computer (диагностика, системный стек) |
| `/su` | `src/api/webgui/apps/index.html` | `su.ps1` | `su.json` | Хаб приложений для суперпользователя (SU Console) |
| `/helpdesk` | `src/api/webgui/helpdesk/index.html` | `launchers/helpdesk.ps1` | `config.json` | Рабочее место службы поддержки (тикеты, операторы) |
| `/` | `src/api/webgui/user/index.html` | `Run-UserAssistant.ps1` | `config/dashboard.json` | Пользовательский интерфейс и персональный ассистент |
| `/chat` | `src/api/webgui/chat/index.html` | `launchers/Run-Chat.ps1` | `config.json` | Автономный диалоговый интерфейс AI |

> [!IMPORTANT]
> **Принцип Active-Only & On-Demand Polling**:
> Только открытая **АКТИВНАЯ** вкладка опрашивает API по мере необходимости. При переключении на другую вкладку или скрытии окна браузера (`visibilitychange`) все периодические фоновые опросники (pollers) автоматически приостанавливаются.

---

## Структура файлов

```
webgui/
  js/
    tab-core.js        ← ЕДИНСТВЕННЫЙ источник логики вкладок и поллинга (switchTab, registerTabPoller, loadTab, setupTabClicks)
    i18n.js            ← переводы
    theme.js           ← тема
    userSettings.js    ← настройки пользователя
    main.js            ← оркестратор для / (run.ps1)

  apps/
    index.html         ← оболочка для /tc (tc.ps1)
    main.js            ← оркестратор для /tc (Lazy Load per tab)
    modules/
      tabs-config.js   ← реестр вкладок /tc (id → html/js пути)
      status-manager.js
      init-interface.js

  <name>_tab/          ← каждая вкладка — изолированная папка
    index.html
    main.js            ← экспортирует window.init<Name>Tab() и регистрирует опросники через registerTabPoller
```

---

## Контракт HTML (одинаков для всех оболочек)

### Кнопка меню
```html
<button type="button" data-tab="tab-xxx">...</button>
```
- Атрибут `data-tab` — единственный способ указать целевую вкладку
- Работает в любом месте страницы: верхнее меню, боковое меню, внутри вкладок
- НЕ используем `data-bs-target`, `onclick`, `href` для переключения вкладок

### Панель вкладки
```html
<div id="tab-xxx" class="tab-pane fade"></div>
```
- id всегда `tab-{name}`
- Контейнер: `<div id="mainTabContent" class="tab-content">`

### Бейдж активного раздела
```html
<span id="active-tab-title-badge">...</span>
```
- Обновляется автоматически при `switchTab`

### Offcanvas (боковое меню)
```html
<div class="offcanvas" id="leftSideNavOffcanvas">   <!-- / -->
<div class="offcanvas" id="appsSideNavOffcanvas">   <!-- /tc -->
```
- Закрывается автоматически при `switchTab`

---

## tab-core.js — API управления вкладками и поллингом

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

### 1. Переключение и ленивая загрузка
```js
// Переключить вкладку
switchTab('tab-chat');
switchTab('chat');  // префикс tab- добавляется автоматически

// Загрузить HTML+JS вкладки по требованию (Lazy Load)
await loadTab('chat', '/html/chat/index.html', '/html/chat/main.js');

// Повесить обработчик кликов (вызвать один раз при инициализации оболочки)
setupTabClicks();
```

### 2. Регистрация периодического опросника (Active-Only Poller)
Вместо небезопасного `setInterval(...)` внутри вкладок используется:
```js
// Зарегистрировать периодический опрос для вкладки
window.registerTabPoller('tab-system-inspector', async () => {
  await fetchSensorsData();
}, 3000, { immediate: true });

// Управление тумблером Live-режима
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

## Жизненный цикл вкладки

Каждая вкладка — папка `<name>_tab/` с двумя файлами:

**index.html** — только разметка, без `<script>` тегов

**main.js** — экспортирует функции жизненного цикла:
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
```

Соглашение об именовании:
- папка: `system_inspector_tab/`
- функции: `window.initSystemInspectorTab()`, опционально `window.deactivateSystemInspectorTab()`
- id панели: `tab-system-inspector`
- data-tab: `tab-system-inspector`

---

## Конфиг меню (только для /tc)

`config/tc_menu_config.json` — описывает какие кнопки показывать сверху и слева:

```json
{
  "menu": {
    "topButtons": [
      { "id": "system_inspector", "tab": "tab-system-inspector", "icon": "bi-graph-up-arrow", "label": "Ресурсы", "order": 1, "visible": true }
    ],
    "sidebarItems": [
      { "id": "about_system", "tab": "tab-about-system", "icon": "ℹ️", "label": "О Системе", "i18n": "tabs.aboutSystem", "order": 1, "visible": true }
    ]
  }
}
```

---

## Оркестратор страницы (шаблон)

```js
// main.js любой страницы
import { switchTab, loadTab, setupTabClicks } from '../js/tab-core.js';

window.switchTab = switchTab;

setupTabClicks();

async function init() {
  // 1. тема, язык
  // 2. lazy-загрузка активной вкладки
  // 3. switchTab(hash || 'tab-first')
}

document.readyState === 'loading'
  ? document.addEventListener('DOMContentLoaded', init)
  : init();
```

---

## Правила

| Правило | Почему |
|---|---|
| Только `data-tab` для навигации | Один механизм — нет путаницы |
| `setupTabClicks()` вызывается один раз | Нет дублирующих обработчиков |
| Поллинг строго через `registerTabPoller` | Опрос API идет только пока вкладка активна и окно видимо |
| Lazy-load по клику | Минимальное время старта и отсутствие фоновой нагрузки |
| Пути к вкладкам — в `tabs-config.js`, не генерируются | Нет 404 из-за несовпадения имён папок |
| Нет `data-bs-target` для переключения вкладок | Bootstrap tab API не используем, управляем сами |

---

## Тест работоспособности кнопки

Кнопка работает если:
1. У неё есть `data-tab="tab-xxx"`
2. В DOM есть `<div id="tab-xxx" class="tab-pane">`
3. `setupTabClicks()` был вызван
4. `window.switchTab` установлен

Проверка в консоли:
```js
window.switchTab('tab-xxx')  // должно переключить вкладку
document.getElementById('tab-xxx')  // должен вернуть элемент
document.querySelector('[data-tab="tab-xxx"]')  // должен вернуть кнопку
```
