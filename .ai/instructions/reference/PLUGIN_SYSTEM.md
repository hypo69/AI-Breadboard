# 🔌 Система плагинов

**Статус:** ✅ Reference  
**Версия:** 1.0  
**Последнее обновление:** сентябрь 2026

---

## 1. Архитектура плагинов

Плагины — это расширяемые компоненты, которые добавляют функциональность в систему.

### Структура плагина

```python
from src.plugins import BasePlugin

class MyPlugin(BasePlugin):
    """Мой плагин для расширения функциональности."""
    
    def get_manifest(self):
        """Метаинформация о плагине."""
        return {
            'name': 'my_plugin',
            'title': 'My Plugin',
            'version': '1.0.0',
            'description': 'Description of what my plugin does',
            'enabled': True,
            'fields': [
                {'name': 'api_key', 'type': 'password'}
            ]
        }
    
    async def handle(self, message: str, **kwargs):
        """Основная функция обработки."""
        # Обработать сообщение
        result = f"Processed: {message}"
        return result
```

### Регистрация плагина

```python
# В config.json
{
  "plugins": {
    "my_plugin": {
      "enabled": true,
      "config": {
        "api_key": "${MY_PLUGIN_API_KEY}"
      }
    }
  }
}
```

---

## 2. Динамическая загрузка

```python
from src.plugins import PluginLoader

loader = PluginLoader()

# Загрузить все плагины из config.json
plugins = loader.load_from_config()

# Использовать плагин
for plugin in plugins:
    result = await plugin.handle("Hello")
    print(result)
```

---

## 3. Function Calling для плагинов

```python
# Плагин с tool calling поддержкой
class ToolPlugin(BasePlugin):
    def get_tools(self):
        """Инструменты, которые может вызвать AI."""
        return [
            {
                'name': 'fetch_data',
                'description': 'Fetch data from API',
                'parameters': {
                    'url': {'type': 'string', 'description': 'API URL'}
                }
            }
        ]
    
    async def execute_tool(self, tool_name: str, **kwargs):
        """Выполнить инструмент."""
        if tool_name == 'fetch_data':
            return await self._fetch(kwargs['url'])
```

---

## 📚 Смотрите также

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — Общая архитектура
- `src/plugins/` — Исходный код системы плагинов

**Последнее обновление:** сентябрь 2026
