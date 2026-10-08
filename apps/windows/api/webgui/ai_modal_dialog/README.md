<!--
=============================================================================
Process Name: Windows WebGUI - AI Modal Dialog Component Documentation
=============================================================================
Description:
  Документация универсального компонента всплывающего окна ИИ-анализатора (ai_modal_dialog).

File: README.md
Project: ai-breadboard
Package: apps.windows.api.webgui.ai_modal_dialog
Author: hypo69
Copyright: © 2026 hypo69
Updated: 2026-10-08 12:25:00
=============================================================================
-->

# Универсальное модальное окно с ИИ-анализатором (`ai_modal_dialog`)

Модуль `ai_modal_dialog` предоставляет универсальный компонент всплывающего окна для инспекции строк таблиц, аналитики сущностей Windows (процессы, службы, задачи, софт, драйверы, реестр) с интеграцией базы знаний WikiLLM и вызовом внешнего LLM-анализатора.

---

## 📁 Структура директории

```
ai_modal_dialog/
├── index.html       ← Базовая HTML-разметка диалоговых окон
├── main.js          ← Контроллер диалогового окна, кэширование WikiLLM, вызовы API
├── style.css        ← Стили и анимации всплывающего окна
└── README.md        ← Настоящая документация компонента
```

---

## 🚀 Подключение и интеграция

### Подключение в HTML
```html
<link rel="stylesheet" href="/html/ai_modal_dialog/style.css?v=20261008_v1">
<script src="/html/ai_modal_dialog/main.js?v=20261008_v1"></script>
```

---

## 💻 API JavaScript

Компонент экспортирует глобальные объекты:
- `window.AIModalDialog` (основной)
- `window.AITableModal` (для обратной совместимости)

### Вызов всплывающего окна: `window.AIModalDialog.show(options)`

```js
window.AIModalDialog.show({
  title: 'svchost.exe',
  subtitle: 'PID: 1042',
  icon: '⚙️',
  tableType: 'process',
  badges: [
    { text: 'System', class: 'badge bg-primary' },
    { text: 'Active', class: 'badge bg-success' }
  ],
  metadata: [
    { label: 'Исполняемый путь', value: 'C:\\Windows\\System32\\svchost.exe', isCode: true },
    { label: 'Память', value: '45.2 MB' },
    { label: 'CPU', value: '0.4%' }
  ],
  rawTitle: 'Командная строка запуска',
  rawContent: 'C:\\Windows\\System32\\svchost.exe -k netsvcs -p -s Schedule',
  autoRun: false, // Автоматический запуск генерации AI (по умолчанию false - сначала проверка WikiLLM)
  actions: [
    {
      label: 'Завершить процесс',
      icon: 'bi-x-circle',
      class: 'btn-outline-danger',
      onClick: (opts) => { console.log('Kill', opts); }
    }
  ]
});
```

### Редактор промптов: `window.AIModalDialog.openPromptEditor(tableType)`

Открывает встроенный редактор шаблонов системных инструкций и промптов для указанного типа сущности (`process`, `service`, `software`, `task`, `network`, `registry`, `user`, `website`, `generic`).
