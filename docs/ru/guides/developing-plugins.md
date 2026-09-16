# Руководство по разработке плагинов и Plugin Factory

## 🧩 Обзор архитектуры плагинов

Плагины в **AI Breadboard** представляют собой модульные расширения системы, которые:
- Предоставляют интерактивные карточки, кнопки действий (`actions`) и формы настроек (`fields`) в панели администратора Web UI.
- Объявляют инструменты вызова функций (LLM Function Calling) для AI-агентов.
- Могут запускать долгоживущие фоновые процессы и сервисы (демоны, боты, сборщики метрик).
- Поддерживают строгую мультиязычность метаданных (i18n) для бесшовного переключения интерфейса на русский, английский и другие языки.

---

## 📂 Структура директории плагина

Все плагины располагаются в каталоге `plugins/<plugin_name>/`:

```text
plugins/<plugin_name>/
├── __init__.py           # Точка входа, экспортирующая экземпляр/класс plugin
├── plugin.py             # Основная реализация, наследующая BasePlugin
├── README.md             # Англоязычная документация разработчика
└── tests/
    └── test_plugin.py    # Модульные тесты pytest
```

---

## 🏭 Plugin Factory (Генератор плагинов)

Для автоматического создания правильной структуры плагина со всеми шаблонами, типами, мультиязычностью и тестами используется **Plugin Factory**.

### Создание плагина через `manage_tools.py`:
```powershell
# Создание плагина аудита безопасности с двуязычным описанием:
py manage_tools.py plugins create audit_logger `
  --title "Audit Logger" `
  --title-ru "Журнал аудита" `
  --description "Tracks security events, logins, and administrative changes" `
  --description-ru "Отслеживание событий безопасности, авторизаций и изменений настроек" `
  --category "security" `
  --icon "🛡️" `
  --scope "system"
```

### Создание плагина через скрипт `init_plugin.py`:
```powershell
python scripts/dev/init_plugin.py audit_logger `
  --title "Audit Logger" `
  --title-ru "Журнал аудита" `
  --description "Tracks security events, logins, and administrative changes" `
  --description-ru "Отслеживание событий безопасности, авторизаций и изменений настроек" `
  --category "security" `
  --icon "🛡️"
```

### Просмотр установленных плагинов:
```powershell
# Список на русском языке
py manage_tools.py plugins list --lang ru

# Список на английском языке
py manage_tools.py plugins list --lang en
```

---

## 💻 Базовый контракт `BasePlugin`

Каждый плагин наследуется от `BasePlugin` (`plugins/base.py`) и переопределяет необходимые свойства и методы:

```python
# -*- coding: utf-8 -*-
from typing import Any, Dict, List, Optional, AsyncGenerator
from plugins.base import BasePlugin
from src.logger import logger


class AuditLoggerPlugin(BasePlugin):
    """Плагин аудита безопасности для AI Breadboard."""

    name: str = "audit_logger"
    title: str = "Audit Logger"
    title_i18n: Dict[str, str] = {
        "en": "Audit Logger",
        "ru": "Журнал аудита",
    }
    version: str = "1.0.0"
    description: str = "Tracks security events, logins, and administrative changes."
    description_i18n: Dict[str, str] = {
        "en": "Tracks security events, logins, and administrative changes.",
        "ru": "Отслеживание событий безопасности, авторизаций и изменений настроек.",
    }
    icon: str = "🛡️"
    category: str = "security"
    enabled: bool = True
    is_system: bool = True
    scope: str = "system"  # 'system' или 'user'

    def __init__(self, ai_model: Any = None, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(ai_model=ai_model, config=config)
        self.is_running: bool = False

    def get_config_fields(self) -> List[Dict[str, Any]]:
        """Конфигурационные поля для отображения в Web UI."""
        return [
            {
                "name": "retention_days",
                "label": "Retention Period (days)",
                "label_i18n": {"en": "Retention Period (days)", "ru": "Срок хранения (дней)"},
                "type": "number",
                "default": 30,
                "description": "Number of days to preserve audit logs before purging",
            },
            {
                "name": "notify_on_admin_login",
                "label": "Notify on Admin Login",
                "label_i18n": {"en": "Notify on Admin Login", "ru": "Уведомлять о входе админа"},
                "type": "boolean",
                "default": True,
            },
        ]

    def get_actions(self) -> List[Dict[str, Any]]:
        """Интерактивные действия для карточки плагина в админке."""
        return [
            {
                "id": "export_logs",
                "label": "Export Audit Logs",
                "label_i18n": {"en": "Export Audit Logs", "ru": "Экспорт журнала"},
                "icon": "📥",
                "variant": "primary",
                "description": "Download audit trail in JSON format",
            },
            {
                "id": "clear_old",
                "label": "Purge Old Logs",
                "label_i18n": {"en": "Purge Old Logs", "ru": "Очистить старые логи"},
                "icon": "🗑️",
                "variant": "danger",
            },
        ]

    async def execute_action(self, action: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Обработчик нажатия кнопок действий в Web UI."""
        logger.info(f"[{self.name}] Executing action '{action}'")
        if action == "export_logs":
            return {
                "status": "success",
                "message": "Audit logs exported successfully.",
                "data": {"count": 142},
            }
        elif action == "clear_old":
            return {
                "status": "success",
                "message": "Purged 12 outdated log records.",
            }
        return {"status": "error", "message": f"Unknown action: '{action}'"}

    def get_tools(self) -> List[Dict[str, Any]]:
        """Определение инструментов LLM Function Calling."""
        return [
            {
                "name": "audit_logger_query",
                "description": "Query recent security and audit trail logs.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "description": "Max log entries"},
                    },
                },
            }
        ]

    async def handle(self, message: str, **kwargs: Any) -> AsyncGenerator[Dict[str, Any], None]:
        """Потоковая обработка входящих запросов."""
        yield {"status": "complete", "text": f"Audit log acknowledged: {message}"}
```

---

## 🌐 Мультиязычность метаданных (i18n)

Плагины поддерживают мультиязычность через словари `title_i18n` и `description_i18n`.

### Методы разрешения языка:
- `plugin.get_title(lang="ru")` $\to$ Возвращает русский заголовок или выполняет fallback на английский.
- `plugin.get_description(lang="ru")` $\to$ Возвращает русское описание или fallback на английский.
- `plugin.get_manifest(lang="ru")` $\to$ Формирует манифест с локализованными `title` и `description`, а также полными словарями `title_i18n` и `description_i18n`.

---

## 🧪 Тестирование плагинов

Все созданные плагины тестируются стандартным `pytest`:

```powershell
pytest plugins/<plugin_name>/tests/
pytest tests/test_plugin_factory.py
```
