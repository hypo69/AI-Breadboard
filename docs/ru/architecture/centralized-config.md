# Централизованная система конфигурации

## Обзор

Платформа использует централизованную систему конфигурационных файлов для управления настройками каждого приложения. Это позволяет легко расширять систему новыми приложениями без конфликтов имен и обеспечивает чистую организацию конфигов.

## Структура папки

```
src/api/webgui/config/
├── tc_menu_config.json      # Конфигурация меню для Test Computer
├── admin_menu_config.json   # Конфигурация меню для Admin Panel (планируется)
├── chat_menu_config.json    # Конфигурация меню для Chat (планируется)
└── ...                      # Другие конфиги приложений
```

## Именование конфигов

Каждый конфигурационный файл следует правилу:

```
{application_name}_{config_type}.json
```

**Примеры:**
- `tc_menu_config.json` — меню для Test Computer
- `admin_settings_config.json` — настройки для Admin Panel
- `chat_theme_config.json` — темы для Chat

## Путь к конфигам

Конфиги доступны по пути:

```
/html/config/{config_name}.json
```

**Пример:**
```
/html/config/tc_menu_config.json
```

## Пример конфигурационного файла

```json
{
  "version": "20260920_v1",
  "menu": {
    "topButtons": [
      {
        "id": "system_inspector",
        "label": "Потребление ресурсов",
        "icon": "bi-graph-up-arrow",
        "tab": "tab-system-inspector",
        "order": 1,
        "visible": true,
        "position": "top"
      }
    ],
    "sidebarItems": [
      {
        "id": "about_system",
        "label": "О Системе",
        "icon": "bi-grid-fill",
        "tab": "tab-about-system",
        "order": 1,
        "visible": true,
        "position": "bottom"
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

## Загрузка конфига в JavaScript

```javascript
// Загрузка конфига
const res = await fetch('/html/config/tc_menu_config.json');
const config = await res.json();

// Использование конфига
if (config.menu) {
  const topButtons = config.menu.topButtons || [];
  const sidebarItems = config.menu.sidebarItems || [];
  // ...
}
```

## Принципы проектирования

1. **Централизация** — все конфиги в одной папке для легкого поиска и управления
2. **Изоляция** — каждое приложение имеет свои конфиги с уникальными именами
3. **Простота** — понятная структура именования без сложных правил
4. **Расширяемость** — легко добавить новые конфиги для новых приложений
5. **Версионирование** — каждая конфигурация содержит версию для кэширования

## Миграция старых конфигов

Если у вас есть старые конфиги в корне или в папках приложений:

1. Переместите их в `src/api/webgui/config/`
2. Переименуйте по новому правилу
3. Обновите пути в коде на `/html/config/{new_name}.json`

## Будущие улучшения

- [ ] Система версионирования конфигов с миграциями
- [ ] Валидация конфигов по JSON Schema
- [ ] UI для редактирования конфигов через Admin Panel
- [ ] Поддержка окружений (dev/staging/production)
