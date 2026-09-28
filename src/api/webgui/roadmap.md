# ROADMAP: Рефакторинг, оптимизация и модернизация WebGUI (AI Breadboard / Mediteka)

> **Статус документа**: Проект архитектурного развития  
> **Целевая кодовая база**: Frontend WebGUI (`/html/admin`, `/html/apps`, `/html/js`, контроллеры вкладок `/html/*_tab`)  
> **Версия архитектуры**: 3.2-Refactored  

---

## 1. Введение и цели рефакторинга

Текущий веб-интерфейс **AI Breadboard (Mediteka WebGUI)** представляет собой многофункциональную клиентскую панель управления, обеспечивающую работу более 30 подсистем (от AI-ассистентов, RAG и агентов до системной телеметрии, аудита безопасности Defender, управления Cloudflared и дисковыми накопителями).

Несмотря на высокую функциональность и наличие продвинутых оптимизаций (L1/L2 кеширование, ленивая загрузка, контроль активности поллеров), в процессе эволюции кодовой базы образовался существенный **технический долг**:
- Наличие дублирующих слоев инициализации (`main.js`, `main-refactored.js`, `lazy-init-patch.js`, `optimization-init.js`);
- Обезьяний патчинг (`Monkey Patching`) ключевых функций навигации во время события `window.load`;
- Загрязнение глобальной области `window` множественными локальными функциями и состояниями;
- Нарушение принципа единого источника правды (SSOT) при объявлении реестра вкладок;
- Использование ручного `innerHTML` рендеринга и несистемных таймеров `setInterval`.

### Главные цели рефакторинга:
1. **Архитектурная чистота**: Переход к единой, предсказуемой и модульной архитектуре на базе ES-модулей с жестким контрактом жизненного цикла вкладок (`TabController`).
2. **Ликвидация Monkey Patching**: Полное удаление `lazy-init-patch.js` и встраивание нативной ленивой загрузки в главный оркестратор `main-refactored.js`.
3. **Единый источник правды (SSOT)**: Объединение разрозненных конфигураций вкладок в единый модуль `tab-registry.js`.
4. **Изоляция состояния и шина событий**: Замена глобальных переменных на `window` на реактивную шину событий (`CoreEventBus`) и локализованное состояние.
5. **Гарантия производительности и безопасности**: Устранение утечек памяти (таймеры, события), безопасный DOM-рендеринг, выдерживание времени переключения вкладок **< 100 мс**.

---

## 2. Комплексный аудит проблем и технический долг (Technical Debt Matrix)

| № | Область | Описание проблемы | Локализация в коде | Уровень риска |
|---|---|---|---|---|
| **1** | **Инициализация** | **Monkey Patching переключения вкладок**: `lazy-init-patch.js` дожидается загрузки `main.js` и перезаписывает `window.switchTab` обертками из `optimization-init.js` и `tab-switch-optimizer.js`. Это усложняет стек вызовов и создает гонку условий (Race Condition). | `lazy-init-patch.js:31-56` | 🔴 **Критический** |
| **2** | **Архитектура (SSOT)** | **Дублирование реестров вкладок**: Определения вкладок, их HTML/JS путей и привязанных `appId` продублированы минимум в 4 местах. Изменение одной вкладки требует правок во всех файлах. | `tabs-config.js`, `main.js`, `lazy-init-patch.js:59-109`, `main-refactored.js` | 🔴 **Критический** |
| **3** | **Глобальный контекст** | **Загрязнение `window`**: Экспорт функций инициализации (`window.initAboutSystemTab`, `window.initAgentsTab`), переменных состояния (`_state`, `window.appsStatusMap`) и API-методов непосредственно в глобальную область. | Почти все файлы `/html/*_tab/main.js` | 🟡 **Высокий** |
| **4** | **Ресурсы и таймеры** | **Фолбэки на `setInterval` в обход центрального полинга**: В отдельных вкладках при отсутствии `registerTabPoller` запускаются прямые `setInterval`. При переключении вкладок или ошибках они не очищаются, выбывая из-под контроля `visibilitychange`. | `about_system_tab/main.js:231`, `autolog_tab/main.js:831`, `hardware_monitor/main.js:46` | 🟡 **Высокий** |
| **5** | **UI и Безопасность** | **Ручная конкатенация HTML-строк**: Генерация динамических интерфейсов через `container.innerHTML = items.map(...)`. Повышает риск XSS-уязвимостей при отсутствии/пропуске `escapeHtml` и снижает производительность DOM. | `about_system_tab/main.js:1084-1133`, `defender_tab/main.js:76-86` | 🟡 **Высокий** |
| **6** | **Сетевой слой** | **Дублирование методов `apiFetch`**: В разных вкладках реализованы локальные обертки `apiFetch` / `_fetchJson` с собственной логикой обработки HTTP-ошибок вместо использования единого `cachedApiFetch`. | `about_system_tab/main.js:111`, `agents_tab/main.js:53`, `forensics_tab/main.js:37` | 🟢 **Средний** |

---

## 3. Целевая архитектура системы (Target Architecture)

```
┌────────────────────────────────────────────────────────────────────────┐
│                        MAIN ORCHESTRATOR                               │
│                   (src/admin/main-refactored.js)                       │
└──────┬─────────────────────────┬───────────────────────────────┬───────┘
       │                         │                               │
       ▼                         ▼                               ▼
┌──────────────┐      ┌─────────────────────┐       ┌────────────────────┐
│ Tab Registry │      │   Tab Lifecycle     │       │   Core Event Bus   │
│   (SSOT)     │      │      Manager        │       │   (EventTarget)    │
└──────┬───────┘      └──────────┬──────────┘       └─────────┬──────────┘
       │                         │                            │
       └──────────────────┬──────┴────────────────────────────┘
                          │
                          ▼
             ┌─────────────────────────┐
             │   BaseTabController     │
             │ (mount, unmount, poll)  │
             └────────────┬────────────┘
                          │
       ┌──────────────────┼──────────────────┐
       ▼                  ▼                  ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  About System│   │  AutoLog Tab │   │  Agents Tab  │
│  Controller  │   │  Controller  │   │  Controller  │
└──────────────┘   └──────────────┘   └──────────────┘
```

### Ключевые компоненты целевой архитектурной модели:
1. **`TabRegistry` (Single Source of Truth)**:
   - Единый JavaScript-модуль, хранящий полный список вкладок, метаданные (`id`, `label`, `icon`), пути к ресурсам (`htmlUrl`, `jsUrl`), права доступа и роли сценариев (`tc`, `admin`, `su`).
2. **`TabLifecycleManager`**:
   - Единственная точка переключения вкладок. Реализует немедленную визуальную реакцию UI (**Zero-Delay UI**) и передает управление соответствующему контроллеру.
3. **`BaseTabController` (Абстрактный контроллер вкладки)**:
   - Стандартизированный интерфейс для контроллеров всех вкладок. Гарантирует наличие методов `mount()`, `unmount()`, `onActivate()`, `onDeactivate()` и автоматизирует регистрацию поллеров.
4. **`CoreEventBus`**:
   - Шина событий на базе стандартного `EventTarget` для асинхронного межмодульного взаимодействия (например, смена языка, изменение статуса ИИ-модели, события кеша) без загрязнения `window`.
5. **`ApiGateway & CacheManager`**:
   - Единая точка отправки HTTP-запросов, объединяющая `APIFetcher`, `browserCache` (IndexedDB/Memory) и `RequestManager` (Debounce/Throttle/Batching).

---

## 4. Пошаговый план реализации (Phased Execution Plan)

```
[Фаза 1: Консолидация & SSOT] ➔ [Фаза 2: Lifecycle & Polling] ➔ [Фаза 3: State & Event Bus] ➔ [Фаза 4: UI & Cache] ➔ [Фаза 5: QA & CI/CD]
```

---

### Фаза 1: Консолидация архитектуры инициализации и единый реестр (SSOT)
**Цель**: Устранить monkey patching, удалить устаревший `lazy-init-patch.js` и свести все реестры вкладок к единому источнику правды.

#### Задачи:
1. **Создание модуля `tab-registry.js`**:
   - Объединить конфигурации из `tabs-config.js`, `lazy-init-patch.js` и `main.js`.
   - Внедрить методы получения списка вкладок с фильтрацией по активному профилю (`/api/apps/status`).
2. **Интеграция ленивой загрузки в `main-refactored.js`**:
   - Перенести инициализацию `LazyTabLoader` непосредственно в главный оркестратор.
   - Реализовать единый вызов `switchTab`, убрав цепочки оберток из `lazy-init-patch.js`.
3. **Удаление технического долга**:
   - Полностью выпилить файл `lazy-init-patch.js`.
   - Очистить монолитный `main.js` от дублирующих загрузчиков `loadTabContent`.

#### Критерии приемки Фазы 1:
- [ ] Файл `lazy-init-patch.js` удален из проекта.
- [ ] Переключение вкладок работает без ошибок в консоли.
- [ ] Реестр вкладок задан ровно в одном месте (`tab-registry.js`).

---

### Фаза 2: Стандартизация жизненного цикла вкладок и Polling Engine
**Цель**: Внедрить жесткий контракт для контроллеров вкладок и полностью исключить неуправляемые таймеры `setInterval`.

#### Задачи:
1. **Разработка базового класса `BaseTabController`**:
   - Создать единый базовый класс в `src/core/base-tab-controller.js`.
   - Автоматизировать привязку/отвязку обработчиков событий и регистрацию поллеров API.
2. **Рефакторинг ключевых контроллеров**:
   - Перевести тяжелые контроллеры (`about_system_tab`, `autolog_tab`, `agents_tab`, `defender_tab`) на наследование от `BaseTabController`.
3. **Строгий аудит таймеров**:
   - Заменить все прямые вызовы `setInterval` в контроллерах на вызовы `this.registerPoller(...)`.
   - Проверить, что при переключении вкладки все фоновые опросы засыпают за 0 миллисекунд.

#### Критерии приемки Фазы 2:
- [ ] В коде контроллеров вкладок отсутствуют прямые вызовы `setInterval`.
- [ ] При свертывании окна браузера (`document.hidden`) количество фоновых HTTP-запросов падает до нуля.
- [ ] Контроллеры корректно освобождают ресурсы при `unmount()`.

---

### Фаза 3: Изоляция состояния, Event Bus и чистка `window`
**Цель**: Избавить глобальный контекст `window` от несистемных переменных и внедрить событийно-ориентированное взаимодействие.

#### Задачи:
1. **Реализация `CoreEventBus`**:
   - Создать легкий класс `CoreEventBus` (в `src/core/event-bus.js`).
   - Перевести системные уведомления (`languageChanged`, `themeChanged`, `modelChanged`, `cacheInvalidated`) на Event Bus.
2. **Инкапсуляция глобальных функций**:
   - Убрать регистрацию контроллеров вкладок в `window` (`window.initXTab = ...`). Контроллеры экспортируются как ES-модули.
   - Сформировать единственный строго документированный глобальный пространство имен `window.WebGUI` только для публичного внешнего API.
3. **Централизация вызовов API**:
   - Заменить локальные функции `apiFetch` / `_fetchJson` во всех вкладках на единый экспорт `cachedApiFetch` из `api-cache.js`.

#### Критерии приемки Фазы 3:
- [ ] В `window` отсутствует более 80% ранее экспортируемых служебных функций.
- [ ] Межмодульное взаимодействие происходит строго через `CoreEventBus`.

---

### Фаза 4: Оптимизация кеширования, DOM-рендеринга и безопасность
**Цель**: Повысить безопасность рендеринга, снизить нагрузку на CPU/DOM и унифицировать кеширование.

#### Задачи:
1. **Безопасная шаблонизация UI**:
   - Внедрить использование HTML `<template>` элементов или безопасного хелпера `html` (с автоматическим экранированием по умолчанию).
   - Заменить прямую конкатенацию строк при сборке сложных карточек (AI Диагностика, дерево AIDA64, таблицы Defender).
2. **Унификация кеширования**:
   - Перевести все вкладки на декларирование кеш-стратегий в `api-cache.js` (`STATIC`, `SEMI_STATIC`, `DYNAMIC`, `REALTIME`).
   - Настроить автоматическую инвалидацию кешей при мутирующих запросах (`POST`/`PUT`/`DELETE`).

#### Критерии приемки Фазы 4:
- [ ] Динамический рендеринг устойчив к XSS-инъекциям.
- [ ] Повторное открытие вкладок происходит мгновенно из DOM-кеша или IndexedDB без повторного сетевого скачка.

---

### Фаза 5: Тестирование, профилирование и документация
**Цель**: Подтвердить стабильность, измерить прирост производительности и актуализировать документацию.

#### Задачи:
1. **Автоматизированное тестирование**:
   - Расширить `optimization-test-suite.js` для проверки ленивой загрузки, чистки таймеров и эффективности кеша.
2. **Профилирование памяти и CPU**:
   - Провести тесты на утечки памяти (Memory Leaks) в Chrome DevTools при 100 последовательных переключениях вкладок.
3. **Обновление документации**:
   - Обновить архитектурное руководство `UI_ARCHITECTURE.md` и составить гайд для разработчиков по созданию новых вкладок.

---

## 5. Детальные примеры кода и целевых интерфейсов

### 5.1. Единый реестр вкладок (`src/core/tab-registry.js`)

```javascript
/**
 * TabRegistry - Единый источник правды (SSOT) для всех вкладок WebGUI
 */
export const TAB_DEFINITIONS = [
  {
    id: 'about-system',
    appId: 'about_system',
    label: 'О системе',
    icon: 'bi-info-circle',
    htmlUrl: '/html/about_system_tab/index.html',
    jsUrl: '/html/about_system_tab/main.js',
    category: 'system',
    roles: ['admin', 'tc', 'su']
  },
  {
    id: 'agents',
    appId: 'ai_agents',
    label: 'Агенты ИИ',
    icon: 'bi-robot',
    htmlUrl: '/html/agents_tab/index.html',
    jsUrl: '/html/agents_tab/main.js',
    category: 'ai',
    roles: ['admin', 'tc']
  },
  {
    id: 'autolog',
    appId: 'autolog_manager',
    label: 'Автолог и Телеметрия',
    icon: 'bi-journal-code',
    htmlUrl: '/html/autolog_tab/index.html',
    jsUrl: '/html/autolog_tab/main.js',
    category: 'telemetry',
    roles: ['tc', 'su']
  }
];

export class TabRegistry {
  static getAll() {
    return TAB_DEFINITIONS;
  }

  static getById(tabId) {
    const cleanId = tabId.replace(/^tab-/, '');
    return TAB_DEFINITIONS.find(t => t.id === cleanId || t.appId === cleanId);
  }

  static getFiltered(appsStatusMap = null, targetRole = 'admin') {
    return TAB_DEFINITIONS.filter(tab => {
      if (!tab.roles.includes(targetRole)) return false;
      if (tab.appId && appsStatusMap && appsStatusMap[tab.appId]) {
        return appsStatusMap[tab.appId].enabled !== false;
      }
      return true;
    });
  }
}
```

---

### 5.2. Абстрактный базовый контроллер вкладки (`src/core/base-tab-controller.js`)

```javascript
import { registerTabPoller, unregisterAllTabPollers } from './tab-core.js';
import { cachedApiFetch } from './api-cache.js';

export class BaseTabController {
  constructor(tabId) {
    this.tabId = tabId.startsWith('tab-') ? tabId : `tab-${tabId}`;
    this.container = null;
    this.eventCleanups = [];
    this.isMounted = false;
  }

  /**
   * Вызывается при первичной подгрузке DOM вкладки
   */
  async mount(container) {
    this.container = container;
    this.isMounted = true;
    this.bindEvents();
    await this.onInit();
  }

  /**
   * Вызывается при уничтожении/выгрузке вкладки
   */
  unmount() {
    this.eventCleanups.forEach(cleanup => cleanup());
    this.eventCleanups = [];
    unregisterAllTabPollers(this.tabId);
    this.isMounted = false;
  }

  /**
   * Вызывается при каждом переключении на данную вкладку
   */
  onActivate() {}

  /**
   * Вызывается при переключении на другую вкладку
   */
  onDeactivate() {}

  /**
   * Переопределяемый метод инициализации
   */
  async onInit() {}

  /**
   * Переопределяемый метод привязки событий
   */
  bindEvents() {}

  /**
   * Безопасная регистрация обработчика событий с автоочисткой
   */
  addEventListener(element, event, handler) {
    if (!element) return;
    element.addEventListener(event, handler);
    this.eventCleanups.push(() => element.removeEventListener(event, handler));
  }

  /**
   * Безопасная регистрация поллера API
   */
  registerPoller(pollFn, intervalMs = 3000, options = {}) {
    return registerTabPoller(this.tabId, pollFn, intervalMs, options);
  }

  /**
   * Упрощенный API запрос
   */
  async fetch(url, options = {}, cacheOptions = {}) {
    return cachedApiFetch(url, options, cacheOptions);
  }
}
```

---

### 5.3. Пример рефакторинга контроллера (`about_system_tab/main.js`)

```javascript
import { BaseTabController } from '../core/base-tab-controller.js';

export class AboutSystemTabController extends BaseTabController {
  constructor() {
    super('about-system');
    this.isLiveActive = true;
  }

  async onInit() {
    await this.refreshAllData();
    
    // Регистрируем централизованный поллер телеметрии
    this.registerPoller(() => this.pollLiveTelemetry(), 3000, {
      pollerId: 'about_system_telemetry',
      immediate: false
    });
  }

  bindEvents() {
    const btnRefresh = this.container.querySelector('#btn-about-sys-refresh');
    this.addEventListener(btnRefresh, 'click', async () => {
      await this.refreshAllData(true);
    });

    const btnClearCache = this.container.querySelector('#btn-about-sys-clear-cache');
    this.addEventListener(btnClearCache, 'click', async () => {
      await this.clearTabCache();
      await this.refreshAllData(true);
    });
  }

  async pollLiveTelemetry() {
    if (!this.isLiveActive) return;
    await Promise.allSettled([
      this.fetchSystemSummary(true),
      this.fetchHardwareSensors(true)
    ]);
  }

  async fetchSystemSummary(isLightPoll = false) {
    const data = await this.fetch(
      '/api/v1/system/summary?process_limit=25',
      {},
      { strategy: isLightPoll ? 'stale-while-revalidate' : 'network-first', ttl: 5000 }
    );
    if (data) {
      this.renderSummary(data);
    }
  }

  renderSummary(data) {
    // Безопасное обновление DOM без ручной конкатенации HTML
    const hostEl = this.container.querySelector('#about-host-name');
    if (hostEl) hostEl.textContent = data.hostname || '--';
  }
}
```

---

## 6. Стратегия миграции и управление рисками

### Стратегия миграции (Pattern: Strangler Fig)
Для предотвращения дестабилизации системы миграция осуществляется по принципу **Strangler Fig (Удушающий плющ)**:
1. Создаются новые ядровые модули (`TabRegistry`, `BaseTabController`, `CoreEventBus`).
2. Оркестратор `main-refactored.js` переводится на новый `TabRegistry` с сохранением обратной совместимости для старых контроллеров.
3. Поочередно (по 2–3 вкладки за итерацию) контроллеры рефакторятся и переводятся на класс `BaseTabController`.
4. После перевода 100% вкладок удаляются легаси-адаптеры и файл `lazy-init-patch.js`.

### Чек-лист проверки качества контроллера вкладки (Quality Gate):
- [ ] Контроллер экспортирует класс, наследуемый от `BaseTabController`.
- [ ] Отсутствуют прямые обращения к `window.initXTab` и глобальные переменные вне класса.
- [ ] Отсутствуют прямые вызовы `setInterval` и `setTimeout` для опрашивания бэкенда.
- [ ] Все вызовы API выполнены через `this.fetch()` с явным указанием стратегии кеширования.
- [ ] Все подписки на DOM-события зарегистрированы через `this.addEventListener()`.
- [ ] Время активации вкладки при повторном клике составляет **менее 50 мс**.

---

## 7. График реализации и распределение этапов

```
Неделя 1-2: [Фаза 1] Консолидация реестров (TabRegistry) и отказ от lazy-init-patch.js
Неделя 3-4: [Фаза 2] Реализация BaseTabController, рефакторинг системных вкладок
Неделя 5-6: [Фаза 3] Внедрение CoreEventBus, чистка window и стандартизация API
Неделя 7-8: [Фаза 4] Безопасная шаблонизация UI и оптимизация IndexedDB кеша
Неделя 9-10: [Фаза 5] Нагрузочное тестирование, проверка утечек памяти и финализация UI_ARCHITECTURE.md
```
