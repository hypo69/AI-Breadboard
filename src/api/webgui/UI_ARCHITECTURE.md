# UI Architecture — Стандарт построения веб-интерфейса

## Принцип

Каждая страница (`/`, `/tc`, `/admin`, ...) — это **оболочка (shell)** с навигацией и набором **вкладок (tabs)**.
Все оболочки используют **одну и ту же логику** из `js/tab-core.js`.

---

## Структура файлов

```
webgui/
  js/
    tab-core.js        ← ЕДИНСТВЕННЫЙ источник логики вкладок (switchTab, loadTab, setupTabClicks)
    i18n.js            ← переводы
    theme.js           ← тема
    userSettings.js    ← настройки пользователя
    main.js            ← оркестратор для / (run.ps1)

  apps/
    index.html         ← оболочка для /tc (tc.ps1)
    main.js            ← оркестратор для /tc
    modules/
      tabs-config.js   ← реестр вкладок /tc (id → html/js пути)
      status-manager.js
      init-interface.js

  <name>_tab/          ← каждая вкладка — изолированная папка
    index.html
    main.js            ← экспортирует window.init<Name>Tab()
```

**Артефакты (не используются, можно удалить):**
- `js/tab-loader.js` — заменён `loadTab` в `tab-core.js`
- `js/tab-switch-optimizer.js` — не используется
- `js/tab-debounce-auto-patch.js` — не используется
- `js/tab-state-persistence.js` — не используется
- `apps/modules/tab-manager.js` — заменён `tab-core.js`

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
- Обновляется автоматически при switchTab

### Offcanvas (боковое меню)
```html
<div class="offcanvas" id="leftSideNavOffcanvas">   <!-- / -->
<div class="offcanvas" id="appsSideNavOffcanvas">   <!-- /tc -->
```
- Закрывается автоматически при switchTab

---

## tab-core.js — API

```js
import { switchTab, loadTab, setupTabClicks } from '/html/js/tab-core.js';

// Переключить вкладку
switchTab('tab-chat');
switchTab('chat');  // префикс tab- добавляется автоматически

// Загрузить HTML+JS вкладки
await loadTab('chat', '/html/chat/index.html', '/html/chat/main.js');

// Повесить обработчик кликов (вызвать один раз при инициализации)
setupTabClicks();
```

### Что делает switchTab:
1. Снимает `active` со всех `[data-tab]` на странице, ставит на нужную
2. Показывает нужный `.tab-pane`, скрывает остальные
3. Обновляет `#active-tab-title-badge`
4. Закрывает offcanvas
5. Обновляет `location.hash`
6. Вызывает `window.init<Name>Tab()` если функция существует

### Что делает setupTabClicks:
- Один `document.addEventListener('click', ...)` на всю страницу
- Ловит клики на `button[data-tab]` и `a[data-tab]`
- Вызывает `switchTab`

---

## Жизненный цикл вкладки

Каждая вкладка — папка `<name>_tab/` с двумя файлами:

**index.html** — только разметка, без `<script>` тегов

**main.js** — экспортирует одну функцию:
```js
window.initChatTab = function() {
  // инициализация при первом показе вкладки
  // вызывается автоматически из switchTab
};
```

Соглашение об именовании:
- папка: `system_inspector_tab/`
- функция: `window.initSystemInspectorTab()`
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

Для `/` (run.ps1) меню статическое — прописано в `index.html`.

---

## Оркестратор страницы (шаблон)

```js
// main.js любой страницы
import { switchTab, loadTab, setupTabClicks } from '../js/tab-core.js';

window.switchTab = switchTab;  // для вызова из вкладок

setupTabClicks();  // один раз — все кнопки с data-tab работают

async function init() {
  // 1. тема, язык
  // 2. загрузить вкладки (все сразу или lazy)
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
| Пути к вкладкам — в `tabs-config.js`, не генерируются | Нет 404 из-за несовпадения имён папок |
| `window.init<Name>Tab()` — единственный lifecycle hook | Предсказуемо, не нужны отдельные события |
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
