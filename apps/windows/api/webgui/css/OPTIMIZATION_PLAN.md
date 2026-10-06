# План оптимизации CSS - AI-Breadboard WebGUI

## Текущая проблема

В веб-интерфейсе наблюдается **серьезное дублирование стилей** между разными вкладками:

### Дублирующиеся паттерны:

#### 1. Карточки (Cards)
- `about_system_tab`: `.about-sys-card`, `.about-sys-panel`
- `admin_tab`: `.card` (Bootstrap)
- `components.css`: `.ui-kpi-card`, `.ui-panel`

**Все имеют идентичные свойства:**
```css
background: var(--surface-1);
border: 1px solid var(--border-color);
border-radius: 8px;
box-shadow: var(--shadow-sm);
```

#### 2. Таблицы спецификаций
- `.about-sys-spec-table`
- `.ui-spec-table`
- `.sysctl-spec-table`
- `.def-spec-table`
- `.winadmin-spec-table`

**Все используют одинаковую структуру:**
```css
border-collapse: separate;
border-spacing: 0;
font-size: 0.82rem;
```

#### 3. Бейджи статусов
- `.about-sys-badge-ok`, `.about-sys-badge-warn`
- `.diag-badge-critical`, `.diag-badge-warning`, `.diag-badge-normal`
- `.ui-badge-success`, `.ui-badge-danger`, `.ui-badge-warning`, `.ui-badge-info`

**Все имеют идентичную структуру:**
```css
font-size: 0.72rem;
padding: 2px 6px;
border-radius: 4px;
font-weight: 600;
```

#### 4. Хедеры панелей
- `.about-sys-panel-header`
- `.ui-panel-header`
- `.diag-panel-header`

**Все используют:**
```css
background: var(--surface-2);
border-bottom: 1px solid var(--border-color);
padding: 0.5rem 0.9rem;
font-weight: 600;
```

---

## Решение: Унификация через CSS-наследование

### Шаг 1: Создать глобальные утилитарные классы

В `components.css` добавить:

```css
/* Универсальная карточка */
.card-unified {
  background: var(--surface-1);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.card-unified:hover {
  border-color: var(--nav-active);
  box-shadow: var(--shadow-md);
}

/* Универсальный хедер панели */
.panel-header-unified {
  background: var(--surface-2);
  border-bottom: 1px solid var(--border-color);
  padding: 0.5rem 0.9rem;
  font-weight: 600;
  font-size: 0.85rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.5rem;
}

/* Универсальная таблица спецификаций */
.spec-table-unified {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  font-size: 0.82rem;
}

.spec-table-unified th {
  padding: 8px 16px;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  border-bottom: 1px solid var(--border-subtle);
  background: transparent;
}

.spec-table-unified td {
  padding: 9px 14px;
  border-bottom: 1px solid var(--border-subtle);
  vertical-align: middle;
  line-height: 1.45;
  color: var(--text-color);
}

/* Универсальный бейдж статуса */
.status-badge-unified {
  font-size: 0.72rem;
  font-weight: 600;
  padding: 0.2rem 0.55rem;
  border-radius: var(--radius-xs);
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  line-height: 1.2;
}

.status-badge-success {
  background: var(--status-success-bg);
  color: var(--status-success-text);
  border: 1px solid var(--status-success-border);
}

.status-badge-danger {
  background: var(--status-danger-bg);
  color: var(--status-danger-text);
  border: 1px solid var(--status-danger-border);
}

.status-badge-warning {
  background: var(--status-warning-bg);
  color: var(--status-warning-text);
  border: 1px solid var(--status-warning-border);
}

.status-badge-info {
  background: var(--status-info-bg);
  color: var(--status-info-text);
  border: 1px solid var(--status-info-border);
}
```

### Шаг 2: Обновить HTML-файлы

#### В `about_system_tab/index.html`:

**Было:**
```html
<div class="about-sys-card">
  <div class="about-sys-label">...</div>
  <div class="about-sys-value">...</div>
  <div class="about-sys-sub">...</div>
</div>
```

**Стало:**
```html
<div class="card-unified ui-kpi-card">
  <div class="ui-kpi-label">...</div>
  <div class="ui-kpi-value">...</div>
  <div class="ui-kpi-sub">...</div>
</div>
```

**Таблицы:**
```html
<!-- Было -->
<table class="about-sys-spec-table">...</table>

<!-- Стало -->
<table class="spec-table-unified">...</table>
```

**Бейджи:**
```html
<!-- Было -->
<span class="about-sys-badge-ok">OK</span>
<span class="diag-badge-warning">Warning</span>

<!-- Стало -->
<span class="status-badge-unified status-badge-success">OK</span>
<span class="status-badge-unified status-badge-warning">Warning</span>
```

### Шаг 3: Удалить дублирующиеся классы из CSS

Из `components.css` удалить:
- `.about-sys-card`, `.about-sys-label`, `.about-sys-value`, `.about-sys-sub`
- `.about-sys-panel`, `.about-sys-panel-header`
- `.about-sys-spec-table`, `.about-sys-spec-key`, `.about-sys-spec-val`
- `.diag-badge-critical`, `.diag-badge-warning`, `.diag-badge-normal`
- `.diag-panel`, `.diag-panel-header`

### Шаг 4: Обновить темы

В `variables.css` убедиться, что все каскадные переменные работают:

```css
/* Уже есть - проверить, что работает */
.ui-kpi-card.is-success { --kpi-border: var(--status-success-border); }
.ui-kpi-card.is-danger { --kpi-border: var(--status-danger-border); }
.ui-kpi-card.is-warning { --kpi-border: var(--status-warning-border); }
.ui-kpi-card.is-info { --kpi-border: var(--status-info-border); }
```

---

## Ожидаемый результат

### Уменьшение кода:
- **CSS-файлы**: ~30-40% уменьшение строк
- **HTML-файлы**: ~20-30% уменьшение строк (за счет упрощения классов)
- **Обслуживание**: один источник правды для каждого паттерна

### Преимущества:
1. **Единый источник правды** - изменение стиля карточки в одном месте
2. **Легче поддерживать** - меньше дублирующегося кода
3. **Быстрее загрузка** - меньше CSS-кода
4. **Консистентность** - все карточки выглядят одинаково
5. **Гибкость** - легко создавать новые вариации через модификаторы

### Совместимость:
- Все существующие вкладки продолжат работать
- Можно постепенно мигрировать (не все сразу)
- Bootstrap-классы остаются для базовых компонентов

---

## Порядок реализации

1. ✅ Создать план оптимизации (этот файл)
2. 🔄 Добавить глобальные утилитарные классы в `components.css`
3. 🔄 Обновить `about_system_tab/index.html` на новые классы
4. 🔄 Обновить `admin_tab/index.html` на новые классы
5. 🔄 Обновить другие вкладки (по мере необходимости)
6. 🔄 Удалить старые дублирующиеся классы из `components.css`
7. ✅ Протестировать все темы (light, brick, dark, terminal)

---

## Примечания

- Не удалять классы, пока все HTML-файлы не обновлены
- Использовать CSS-переменные для всех кастомизируемых параметров
- Добавить комментарии в CSS для объяснения назначения классов
- Обновить документацию при изменении API классов
