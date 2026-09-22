# Централизованная конфигурация

Эта папка содержит конфигурационные файлы для всех приложений платформы AI-Breadboard.

## Назначение

Каждое приложение имеет свой набор конфигурационных файлов, которые управляют его поведением, интерфейсом и настройками. Все конфиги централизованно хранятся здесь для:

- **Легкого поиска** — все конфиги в одном месте
- **Управления версиями** — проще отслеживать изменения
- **Избежания конфликтов** — уникальные имена для каждого приложения
- **Упрощенной поддержки** — понятная структура

## Структура именования

```
{application_name}_{config_type}.json
```

**Примеры:**
- `tc_menu_config.json` — меню для Test Computer
- `admin_settings_config.json` — настройки для Admin Panel
- `chat_theme_config.json` — темы для Chat

## Доступ из кода

Конфиги доступны по пути:

```
/html/config/{config_name}.json
```

**Пример:**
```javascript
const res = await fetch('/html/config/tc_menu_config.json');
const config = await res.json();
```

## Типы конфигов

| Тип | Назначение | Примеры |
|-----|-----------|---------|
| `menu_config.json` | Настройка элементов меню | `tc_menu_config.json` |
| `settings_config.json` | Общие настройки приложения | `admin_settings_config.json` |
| `theme_config.json` | Настройки темы и стилей | `chat_theme_config.json` |
| `api_config.json` | Настройки API endpoints | `rag_api_config.json` |
| `feature_config.json` | Включение/отключение фич | `feature_flags_config.json` |

## Добавление нового конфига

1. Создайте файл в этой папке с правильным именем
2. Добавьте конфигурацию в нужном формате (JSON)
3. Обновите код приложения для загрузки конфига по пути `/html/config/{name}.json`
4. Добавьте документацию в `docs/ru/architecture/centralized-config.md`

## Связанная документация

- [Централизованная система конфигурации](../../docs/ru/architecture/centralized-config.md) — полная документация
- [Архитектура системы](../../docs/ru/architecture/index.md) — обзор архитектуры
