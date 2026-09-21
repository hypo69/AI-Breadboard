# Плагины

## BasePlugin

Базовый класс для всех плагинов. Определяет жизненный цикл, конфигурацию, действия и инструменты для LLM.

::: plugins.base.BasePlugin
    options:
      members:
        - __init__
        - start
        - stop
        - health_check
        - get_config_fields
        - update_config
        - get_actions
        - execute_action
        - get_tools
        - handle
        - get_title
        - get_description
        - get_manifest

---

## Реализации плагинов

Прикладные плагины загружаются динамически из каталогов `plugins/system-plugins`,
`plugins/developer-plugins` и `plugins/user-plugins`. Эти каталоги содержат дефисы
и не являются импортируемыми Python-пакетами, поэтому их API не подключается через
`mkdocstrings` как обычные модули.

Документация конкретных плагинов находится в разделе [каталога плагинов](../plugins/catalog.md).

