# Руководство по разработке плагинов

> **Раздел:** Разработка плагинов  
> **Язык:** Русский  

---

## 🛠️ Создание плагина с помощью Plugin Factory

В проекте **AI Breadboard** предусмотрен генератор плагинов (**Plugin Factory**), который создает правильную файловую структуру, базовый класс, конфигурацию, тесты и англоязычный `README.md`.

### Вариант 1: Через CLI-менеджер `manage_tools.py`

```powershell
py manage_tools.py plugins create security_scanner `
  --title "Security Scanner" `
  --title-ru "Сканер безопасности" `
  --description "Scans project files for leaked API keys and vulnerabilities" `
  --description-ru "Сканирует файлы проекта на утечки ключей API и уязвимости" `
  --category "security" `
  --icon "🔍" `
  --scope "system"
```

### Вариант 2: Через скрипт `scripts/dev/init_plugin.py`

```powershell
python scripts/dev/init_plugin.py security_scanner `
  --title "Security Scanner" `
  --title-ru "Сканер безопасности" `
  --description "Scans project files for leaked API keys and vulnerabilities" `
  --description-ru "Сканирует файлы проекта на утечки ключей API и уязвимости" `
  --category "security" `
  --icon "🔍"
```

---

## 📂 Структура директории плагина

После генерации плагин располагается в `plugins/<plugin_name>/`:

```text
plugins/security_scanner/
├── __init__.py           # Экспорт класса и точки входа
├── plugin.py             # Основная реализация (наследует BasePlugin)
├── config.json           # Начальные параметры плагина
├── README.md             # Англоязычная документация разработчика
└── tests/
    └── test_plugin.py    # Модульные тесты pytest
```

---

## 💻 Пошаговый пример реализации плагина

### 1. Файл точки входа: `plugins/security_scanner/__init__.py`

```python
# -*- coding: utf-8 -*-
from .plugin import SecurityScannerPlugin

plugin = SecurityScannerPlugin()

__all__ = ["SecurityScannerPlugin", "plugin"]
```

### 2. Файл логики: `plugins/security_scanner/plugin.py`

```python
# -*- coding: utf-8 -*-
from typing import Any, Dict, List, Optional, AsyncGenerator
from pathlib import Path

from plugins.base import BasePlugin
from src.logger import logger


class SecurityScannerPlugin(BasePlugin):
    """Плагин для проверки безопасности и обнаружения утечек секретов."""

    name: str = "security_scanner"
    title: str = "Security Scanner"
    title_i18n: Dict[str, str] = {
        "en": "Security Scanner",
        "ru": "Сканер безопасности",
    }
    version: str = "1.0.0"
    description: str = "Scans project files for leaked API keys and vulnerabilities."
    description_i18n: Dict[str, str] = {
        "en": "Scans project files for leaked API keys and vulnerabilities.",
        "ru": "Сканирует файлы проекта на утечки ключей API и уязвимости.",
    }
    icon: str = "🔍"
    category: str = "security"
    enabled: bool = True
    is_system: bool = True
    scope: str = "system"

    def __init__(self, ai_model: Any = None, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(ai_model=ai_model, config=config)
        self.is_running: bool = False

    def get_config_fields(self) -> List[Dict[str, Any]]:
        """Поля формы настроек плагина в Web UI."""
        return [
            {
                "name": "scan_hidden_dirs",
                "label": "Scan Hidden Directories",
                "label_i18n": {"en": "Scan Hidden Directories", "ru": "Сканировать скрытые папки"},
                "type": "boolean",
                "default": False,
                "description": "Включать ли папки, начинающиеся с точки (.git, .env)",
            },
            {
                "name": "max_file_size_mb",
                "label": "Max File Size (MB)",
                "label_i18n": {"en": "Max File Size (MB)", "ru": "Максимальный размер файла (МБ)"},
                "type": "number",
                "default": 5,
            },
        ]

    def get_actions(self) -> List[Dict[str, Any]]:
        """Кнопки действий на карточке плагина."""
        return [
            {
                "id": "run_quick_scan",
                "label": "Quick Scan",
                "label_i18n": {"en": "Quick Scan", "ru": "Быстрое сканирование"},
                "icon": "⚡",
                "variant": "primary",
                "description": "Проверить корневую директорию на наличие открытых .env и токенов",
            },
            {
                "id": "clear_reports",
                "label": "Clear Reports",
                "label_i18n": {"en": "Clear Reports", "ru": "Очистить отчеты"},
                "icon": "🗑️",
                "variant": "danger",
            },
        ]

    async def execute_action(self, action_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Обработка клика по кнопке действия."""
        logger.info(f"[{self.name}] Executing action '{action_id}'")
        if action_id == "run_quick_scan":
            # Имитация проверки
            return {
                "status": "success",
                "message": "Сканирование завершено: критических уязвимостей не найдено.",
                "data": {"scanned_files": 48, "warnings": 0},
            }
        elif action_id == "clear_reports":
            return {"status": "success", "message": "История сканирований очищена."}
        return {"status": "error", "message": f"Неизвестное действие: '{action_id}'"}

    def get_tools(self) -> List[Dict[str, Any]]:
        """Декларация Function Calling инструментов для AI-моделей."""
        return [
            {
                "name": "scan_for_secrets",
                "description": "Сканирует указанный путь на наличие незашифрованных API-ключей и паролей.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory_path": {"type": "string", "description": "Абсолютный путь к каталогу"},
                    },
                    "required": ["directory_path"],
                },
            }
        ]

    async def handle(self, message: str, **kwargs: Any) -> AsyncGenerator[Dict[str, Any], None]:
        """Потоковый обработчик запросов."""
        yield {"status": "progress", "text": f"Запуск сканирования для запроса: {message}\n"}
        yield {"status": "complete", "text": "Сканирование выполнено успешно."}
```

---

## 🧪 Тестирование плагина

Создайте тест в `plugins/security_scanner/tests/test_plugin.py`:

```python
# -*- coding: utf-8 -*-
import pytest
from plugins.security_scanner.plugin import SecurityScannerPlugin


@pytest.mark.asyncio
async def test_plugin_metadata():
    plugin = SecurityScannerPlugin()
    assert plugin.name == "security_scanner"
    assert plugin.get_title("ru") == "Сканер безопасности"
    assert plugin.get_title("en") == "Security Scanner"
    assert len(plugin.get_config_fields()) >= 2
    assert len(plugin.get_actions()) >= 2


@pytest.mark.asyncio
async def test_plugin_actions():
    plugin = SecurityScannerPlugin()
    res = await plugin.execute_action("run_quick_scan")
    assert res["status"] == "success"
    
    unknown = await plugin.execute_action("non_existent")
    assert unknown["status"] == "error"
```

Запуск тестов:
```powershell
pytest plugins/security_scanner/tests/
```

---

## 📋 Стандарты и правила оформления

1. **Строгий лимит строк:** Файлы плагинов не должны превышать 500 строк функционального кода. При необходимости разбивайте логику на вспомогательные модули (`client.py`, `scanner.py`, `utils.py`).
2. **Логирование:** Используйте только централизованный логгер `from src.logger import logger` (прямые вызовы `print()` запрещены).
3. **Безопасность:** Не храните секреты и ключи в коде плагина или `config.json`. Все учетные данные загружаются из `.env`.
4. **Языковой стандарт:** Код, имена переменных, docstrings и `README.md` в папке плагина оформляются строго на английском языке. Пользовательские строки интерфейса оформляются через словари `*_i18n`.
