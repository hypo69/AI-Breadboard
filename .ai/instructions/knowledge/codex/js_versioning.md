# Правила версионирования JavaScript файлов

## Проблема

При разработке веб-интерфейса возникает проблема кэширования браузером JS и CSS файлов. При локальной разработке и тестировании изменения в файлах могут не отображаться из-за агрессивного кэширования.

## Решение

Все JS и CSS файлы должны включать версионирование через query-параметр `?v=VERSION`.

## Формат версии

```
?v=YYYYMMDD_vN
```

Где:
- `YYYYMMDD` — дата последнего изменения (год, месяц, день)
- `_vN` — номер версии для изменений в течение одного дня

## Examples

```javascript
// Правильно
<script src="/html/js/chatService.js?v=20260807_v1"></script>
<link href="/html/css/main.css?v=20260807_v2" rel="stylesheet">

// Неправильно
<script src="/html/js/chatService.js"></script>
<link href="/html/css/main.css" rel="stylesheet">
```

## Правила обновления

1. **Каждое изменение JS/CSS файла должно сопровождаться обновлением версии**
2. **Версия обновляется в файле main.js при загрузке вкладок**
3. **При изменении HTML файла也需要 обновить версию JS если он подгружает скрипты**
4. **Используйте `Date.now()` для динамического версионирования при разработке**

## Где обновлять

### В `webinterface/admin/main.js`:

```javascript
const cb = Date.now();
await Promise.all([
  loadTabContent('instructions', `/html/instructions_tab/index.html?v=${cb}`, `/html/instructions_tab/main.js?v=${cb}`),
  // ... другие вкладки
]);
```

### В HTML файлах:

```html
<script src="/html/js/i18n.js?v=20260807"></script>
<link href="/html/css/main.css?v=20260807_v1" rel="stylesheet">
```

## Рекомендации

1. **Разработка**: Используйте `Date.now()` для динамической версии
2. **Продакшн**: Используйте фиксированную версию `YYYYMMDD_vN`
3. **Тестирование**: После изменений очистите кэш браузера или нажмите Ctrl+F5
4. **Debug**: Используйте DevTools → Network → "Disable cache" при разработке

## Частые проблемы и решения

### Проблема: Изменения не отображаются

**Причина:** Браузер кэширует файлы

**Решение:**
1. Обновите версию файла
2. Очистите кэш браузера (Ctrl+Shift+Delete)
3. Используйте инкогнито режим
4. Отключите кэш в DevTools (Network → Disable cache)

### Проблема: Вкладка не загружается

**Причина:** Error в JS или caching старой версии

**Решение:**
1. Проверьте консоль браузера на ошибки
2. Обновите версию JS файла
3. Убедитесь что function инициализации экспортирована в `window`

## Логирование для отладки

Добавляйте логирование при инициализации:

```javascript
async function initInstructionsTab() {
  console.log('[InstructionsTab] Initializing...');
  // ... код инициализации
  console.log('[InstructionsTab] Initialized successfully');
}
```

## Ссылки

- [MDN: HTTP caching](https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching)
- [Chrome DevTools: Disable cache](https://developer.chrome.com/docs/devtools/network/#disable-cache)