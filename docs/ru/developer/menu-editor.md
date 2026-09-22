# Редактор меню

## Обзор

Редактор меню — это инструмент для настройки расположения элементов навигации в веб-интерфейсе `/tc` (Test Computer). Он позволяет:

- Изменять порядок элементов в верхнем и боковом меню
- Включать/отключать элементы меню
- Сохранять конфигурацию в файл `menu-config.json`

## Архитектура

### Файлы

| Файл | Описание |
|------|----------|
| `menu-config.json` | Внешний файл конфигурации меню |
| `apps/index.html` | HTML-шаблон с редактором меню |
| `apps/main.js` | Основной JS-модуль |
| `apps/modules/status-manager.js` | Управление состоянием приложений |
| `apps/modules/tabs-config.js` | Реестр определений вкладок |
| `css/components.css` | Стили для редактора меню |

### Структура конфигурации

```json
{
  "version": "1.0",
  "menu": {
    "topButtons": [
      {
        "id": "system_inspector",
        "label": "Потребление ресурсов",
        "icon": "bi-graph-up-arrow",
        "tab": "tab-system-inspector",
        "order": 1,
        "visible": true
      }
    ],
    "sidebarItems": [
      {
        "id": "about_system",
        "label": "О Системе",
        "icon": "bi-grid-fill",
        "tab": "tab-about-system",
        "order": 1,
        "visible": true
      }
    ]
  },
  "settings": {
    "showTopButtons": true,
    "showSidebar": true,
    "defaultTab": "tab-about-system",
    "enableAnimations": true
  }
}
```

### Поля конфигурации

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| `id` | string | Да | Уникальный идентификатор (должен совпадать с `id` в `tabs-config.js`) |
| `label` | string | Да | Отображаемое имя элемента |
| `icon` | string | Да | Иконка Bootstrap Icons (например, `bi-gear-fill`) |
| `tab` | string | Да | ID вкладки (например, `tab-system-inspector`) |
| `order` | number | Нет | Порядок отображения (по возрастанию) |
| `visible` | boolean | Нет | Показывать/скрывать элемент |

## Использование

### Открытие редактора

1. Откройте веб-интерфейс `/tc`
2. Нажмите кнопку **МЕНЮ** слева
3. Внизу бокового меню нажмите **Редактор меню**

### Изменение порядка

1. В модальном окне перетащите элементы мышью
2. Элементы сортируются по полю `order` в конфигурации

### Включение/отключение элементов

1. Нажмите чекбокс **Показать** рядом с элементом
2. Отключенные элементы не отображаются в меню и не запускаются

### Сохранение

1. Нажмите кнопку **Сохранить**
2. Конфигурация сохраняется в `menu-config.json`
3. Страница перезагружается

## Разработка

### Добавление нового элемента меню

1. **Добавьте определение вкладки** в `apps/modules/tabs-config.js`:

```javascript
{ id: 'new_feature', tab: 'new-feature', tabId: 'tab-new-feature', html: '/html/new_feature_tab/index.html', js: '/html/new_feature_tab/main.js' }
```

2. **Добавьте элемент в `menu-config.json`**:

```json
{
  "id": "new_feature",
  "label": "Новая функция",
  "icon": "bi-star-fill",
  "tab": "tab-new-feature",
  "order": 5,
  "visible": true
}
```

3. **Создайте HTML и JS файлы** для вкладки:
   - `html/new_feature_tab/index.html`
   - `html/new_feature_tab/main.js`

### Drag-and-Drop реализация

Редактор использует нативный HTML5 Drag and Drop API:

```javascript
// Drag start
element.addEventListener('dragstart', (e) => {
  element.classList.add('dragging');
  e.dataTransfer.setData('text/plain', JSON.stringify({
    id: item.id,
    type: type,
    order: item.order
  }));
});

// Drop zone
container.addEventListener('dragover', (e) => {
  e.preventDefault();
  const afterElement = getDragAfterElement(container, e.clientY);
  const draggable = container.querySelector('.dragging');
  if (draggable) {
    container.insertBefore(draggable, afterElement);
  }
});
```

### Фильтрация disabled приложений

При генерации меню проверяется статус приложений:

```javascript
const appInfo = appsMap[item.id] || Object.values(appsMap).find(a => a.tab === item.tab);
if (appInfo && appInfo.enabled === false) return; // Пропустить отключенные
```

## Структура проекта

```
AI-Breadboard/
├── menu-config.json              # Конфигурация меню
├── src/
│   └── api/
│       └── webgui/
│           ├── apps/
│           │   ├── index.html    # HTML-шаблон
│           │   ├── main.js       # Основной JS
│           │   └── modules/
│           │       ├── status-manager.js
│           │       └── tabs-config.js
│           └── css/
│               └── components.css # Стили редактора
└── docs/
    └── ru/
        └── developer/
            └── menu-editor.md    # Документация
```

## Тестирование

### Ручное тестирование

1. **Проверка отображения**:
   - Откройте `/tc`
   - Убедитесь, что элементы отображаются в правильном порядке
   - Проверьте, что отключенные элементы не видны

2. **Drag-and-Drop**:
   - Откройте редактор меню
   - Перетащите элементы
   - Сохраните и проверьте новый порядок

3. **Включение/отключение**:
   - Отключите элемент через чекбокс
   - Сохраните
   - Убедитесь, что элемент исчез из меню

### Автоматизированное тестирование

Создайте тестовый файл `tests/test_menu_editor.py`:

```python
import pytest
import json
from pathlib import Path

def test_menu_config_structure():
    """Проверка структуры menu-config.json"""
    config_path = Path("menu-config.json")
    assert config_path.exists(), "menu-config.json не найден"
    
    with open(config_path) as f:
        config = json.load(f)
    
    assert "menu" in config, "Отсутствует секция menu"
    assert "topButtons" in config["menu"], "Отсутствует topButtons"
    assert "sidebarItems" in config["menu"], "Отсутствует sidebarItems"
    
    # Проверка обязательных полей
    for item in config["menu"]["topButtons"]:
        assert "id" in item, "Отсутствует id в topButtons"
        assert "label" in item, "Отсутствует label в topButtons"
        assert "icon" in item, "Отсутствует icon в topButtons"
        assert "tab" in item, "Отсутствует tab в topButtons"

def test_tabs_config_consistency():
    """Проверка согласованности tabs-config.js"""
    # Проверка, что все id из menu-config.json есть в tabs-config.js
    pass  # Реализовать проверку
```

## Устранение неполадок

### Элементы не отображаются

1. Проверьте, что `visible: true` в конфигурации
2. Убедитесь, что приложение включено в `config_tc.json`
3. Проверьте консоль браузера на ошибки

### Drag-and-drop не работает

1. Убедитесь, что элементы имеют класс `menu-editor-item`
2. Проверьте, что установлен атрибут `draggable="true"`
3. Проверьте обработчики событий `dragstart` и `dragover`

### Изменения не сохраняются

1. Проверьте права доступа к `menu-config.json`
2. Убедитесь, что сервер запущен
3. Проверьте консоль на ошибки при сохранении

## См. также

- [Архитектура приложений](architecture.md)
- [Разработка плагинов](plugins.md)
- [Каталог приложений](../apps/catalog.md)
