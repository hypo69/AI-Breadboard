# GEMINI.md — Инструкция WebGUI и Руководство по интеграции `ai_modal_dialog`

## 📋 Общие сведения модуля `apps/windows/api/webgui`

Данная директория содержит фронтенд веб-интерфейса AI Breadboard (оболочки `/`, `/apps`, `/tc`, `/admin`, изолированные модули вкладок `*_tab/`, системные скрипты `js/` и универсальное модальное окно AI-анализатора `ai_modal_dialog/`).

> [!IMPORTANT]
> **Языковой стандарт**: Все комментарии к коду, docstrings и документация ведутся строго на **русском языке**.
> [!IMPORTANT]
> **Темы оформления**: Запрещено жестко зашивать цвета фона и текста (`bg-black`, `bg-dark`, `text-light`, `#12151a` и т.д.). Стили обязаны использовать CSS-переменные (`var(--surface-1)`, `var(--surface-2)`, `var(--text-color)`, `var(--border-color)`).
> [!IMPORTANT]
> **Фиксация даты изменения**: При любом редактировании файлов обязательно обновлять заголовок: `Updated: YYYY-MM-DD HH:MM:SS`.

---

## 🛠️ Инструкция: Как встроить модальное окно `ai_modal_dialog` в любую таблицу

Модуль `ai_modal_dialog` предоставляет универсальное всплывающее окно для контекстного AI-анализа строк таблиц, инспекции параметров сущностей Windows (процессы, службы, установленный софт, задачи планировщика, сетевые соединения, ключи реестра, пользователи, диски) и проверки по базе знаний WikiLLM (L1 Exact Cache).

---

### Шаг 1. Подключение модуля в Shell (HTML)

В файле оболочки страницы (`apps/index.html`, `admin/index.html`, `index.html`) должны быть подключены стили и скрипт:

```html
<!-- Стили и контроллер Universal AI Modal Dialog -->
<link rel="stylesheet" href="/html/ai_modal_dialog/style.css?v=20261008_v1">
<script src="/html/ai_modal_dialog/main.js?v=20261008_v1"></script>
```

> [!NOTE]
> Контроллер автоматически гарантирует создание элементов диалоговых окон `#universal-ai-table-modal` и `#universal-ai-prompt-editor-modal` в DOM. Ручное копирование разметки модалки во вкладки **не требуется**.

---

### Шаг 2. Разметка таблицы (`index.html` вкладки)

Создайте стандартную таблицу Bootstrap. Строкам таблицы рекомендуется задать класс или атрибут для интерактивного указателя мыши:

```html
<div class="table-responsive">
  <table class="table table-hover align-middle mb-0">
    <thead>
      <tr>
        <th>Имя процесса</th>
        <th>PID</th>
        <th>Состояние</th>
        <th>Память (RAM)</th>
        <th class="text-end">Действия</th>
      </tr>
    </thead>
    <tbody id="my-table-body">
      <!-- Строки генерируются динамически через JS -->
    </tbody>
  </table>
</div>
```

---

### Шаг 3. Привязка вызова `AIModalDialog.show()` в JavaScript (`main.js` вкладки)

При рендеринге строк таблицы повесьте обработчик клика на элемент `<tr>`:

```javascript
/**
 * Отрисовка строк таблицы с привязкой универсального AI-модального окна.
 * @param {Array<Object>} items Список элементов данных
 */
function renderTableRows(items) {
  const tbody = document.getElementById('my-table-body');
  if (!tbody) return;

  tbody.innerHTML = items.map(item => `
    <tr class="interactive-table-row" data-id="${item.id}" style="cursor: pointer;">
      <td>
        <div class="fw-semibold text-body">${escapeHtml(item.name)}</div>
        <div class="small text-muted font-monospace">${escapeHtml(item.executable_path || '')}</div>
      </td>
      <td><span class="badge bg-body-secondary text-body font-monospace">${item.pid}</span></td>
      <td><span class="badge ${item.status === 'Running' ? 'bg-success' : 'bg-secondary'}">${item.status}</span></td>
      <td class="font-monospace">${item.memory_mb} MB</td>
      <td class="text-end no-modal-trigger">
        <button type="button" class="btn btn-sm btn-outline-danger btn-kill" data-id="${item.id}">
          <i class="bi bi-x-circle"></i>
        </button>
      </td>
    </tr>
  `).join('');

  // Навешивание обработчиков клика по строкам
  tbody.querySelectorAll('.interactive-table-row').forEach(row => {
    row.addEventListener('click', (event) => {
      // 1. Игнорируем клики по внутренним кнопкам действий, чекбоксам и ссылкам
      if (event.target.closest('button, a, input, select, .no-modal-trigger')) {
        return;
      }

      const itemId = row.getAttribute('data-id');
      const item = items.find(x => String(x.id) === String(itemId));
      if (!item) return;

      // 2. Вызов универсального AI модального окна
      openItemAiModal(item);
    });
  });
}
```

---

### Шаг 4. Конфигурация параметров `window.AIModalDialog.show(options)`

```javascript
/**
 * Открытие карточки записи с AI-анализом и проверкой WikiLLM.
 * @param {Object} item Объект строки таблицы
 */
function openItemAiModal(item) {
  const modal = window.AIModalDialog || window.AITableModal;
  if (!modal) {
    console.warn('[TableModule] AIModalDialog модуль не найден в глобальной области window');
    return;
  }

  modal.show({
    // 1. Основной заголовок и подзаголовок
    title: item.name,
    subtitle: `PID: ${item.pid} | Архитектура: AMD64`,
    icon: '⚙️', // Эмодзи или текстовая иконка сущности

    // 2. Тип таблицы (для выбора системного промпта в редакторе промптов)
    // Доступные типы: 'process' | 'service' | 'software' | 'task' | 'network' | 'registry' | 'user' | 'website' | 'rag_doc' | 'disk' | 'startup' | 'generic'
    tableType: 'process',

    // 3. Статусные бейджи в шапке модалки
    badges: [
      { text: item.status, class: item.status === 'Running' ? 'badge bg-success' : 'badge bg-secondary' },
      { text: item.priority || 'Normal', class: 'badge border text-secondary' }
    ],

    // 4. Сетка метаданных (отображается в 2 колонки)
    metadata: [
      { label: 'Исполняемый путь', value: item.executable_path, isCode: true },
      { label: 'Командная строка', value: item.command_line, isCode: true, fullWidth: true },
      { label: 'Память (RAM)', value: `${item.memory_mb} MB` },
      { label: 'Использование CPU', value: `${item.cpu_percent}%` },
      { label: 'Пользователь / SID', value: item.username || 'SYSTEM' }
    ],

    // 5. Исходные данные / код (скрыт по умолчанию; отображается только при непустом значении)
    rawTitle: 'Дамп процесса / Контекст дескрипторов',
    rawContent: item.raw_dump || '',

    // 6. Флаг немедленного запуска AI-генерации (по умолчанию false: сначала быстрый L1 кэш WikiLLM)
    autoRun: false,

    // 7. Дополнительные действия в футере окна (опционально)
    actions: [
      {
        label: 'Перезапустить',
        icon: 'bi-arrow-repeat',
        class: 'btn-outline-warning',
        onClick: (opts) => {
          console.log('Restart action:', opts.title);
        }
      },
      {
        label: 'Завершить процесс',
        icon: 'bi-trash',
        class: 'btn-outline-danger',
        onClick: (opts) => {
          if (confirm(`Завершить процесс «${opts.title}»?`)) {
            terminateProcess(item.pid);
          }
        }
      }
    ]
  });
}
```

---

## 📋 Таблица поддерживаемых типов таблиц (`tableType`)

| `tableType` | Описание сущности | Переменные в шаблоне промпта |
|---|---|---|
| `process` | Процессы Windows, дескрипторы, потоки | `{title}`, `{subtitle}`, `{metadata}`, `{raw_data}` |
| `service` | Системные службы Windows (Win32 Service) | `{title}`, `{subtitle}`, `{metadata}`, `{raw_data}` |
| `software` | Установленное программное обеспечение, версии, вендоры | `{title}`, `{subtitle}`, `{metadata}`, `{raw_data}` |
| `task` | Задачи планировщика Windows Task Scheduler | `{title}`, `{subtitle}`, `{metadata}`, `{raw_data}` |
| `network` | Сетевые сокеты, активные соединения, порты, IP | `{title}`, `{subtitle}`, `{metadata}`, `{raw_data}` |
| `registry` | Ключи и значения реестра Windows | `{title}`, `{subtitle}`, `{metadata}`, `{raw_data}` |
| `user` | Локальные учетные записи пользователей и группы | `{title}`, `{subtitle}`, `{metadata}`, `{raw_data}` |
| `website` | Метрики мониторинга веб-ресурсов и URL | `{title}`, `{subtitle}`, `{metadata}`, `{raw_data}` |
| `rag_doc` | Документы базы знаний и чанков RAG | `{title}`, `{subtitle}`, `{metadata}`, `{raw_data}` |
| `disk` | Физические диски, разделы и тома | `{title}`, `{subtitle}`, `{metadata}`, `{raw_data}` |
| `startup` | Программы и модули автозагрузки | `{title}`, `{subtitle}`, `{metadata}`, `{raw_data}` |
| `generic` | Универсальный базовый шаблон | `{title}`, `{subtitle}`, `{metadata}`, `{raw_data}` |

---

## ⚡ Особенности работы диалогового окна:
1. **L1 Exact Cache WikiLLM**: При открытии окна сначала проверяется наличие верифицированного описания в локальной базе знаний WikiLLM без траты токенов LLM.
2. **Web Grounding**: При клике на «Запросить AI-анализ» отправляется запрос на бэкенд с автоматическим поиском актуальной информации в интернете.
3. **Сохранение в WikiLLM**: После получения результата пользователь может нажать «Одобрить и сохранить в WikiLLM», чтобы знание навсегда закешировалось для всех последующих вызовов.
4. **Редактор промптов**: Кнопка «Промпт» в заголовке карточки позволяет администратору настроить системный промпт конкретного типа сущности прямо из интерфейса.
5. **Адаптивность тем**: Контейнеры и текст автоматически принимают палитру активной темы (Light/NightView, Brick, Dark, Terminal).
