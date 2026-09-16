# 🛠️ CLI инструменты и manage_tools.py

**Статус:** ✅ Reference  
**Версия:** 1.0  
**Язык:** Python  
**Последнее обновление:** сентябрь 2026

---

## 1. Использование manage_tools.py

### Основная команда

```bash
python manage_tools.py --help
```

### Группы инструментов

| Группа | Команда | Описание |
|--------|---------|---------|
| **Config** | `--config` | Управление конфигурацией |
| **Tests** | `--test` | Запуск тестов |
| **Build** | `--build` | Построение проекта |
| **Deploy** | `--deploy` | Развёртывание |
| **Docs** | `--docs` | Генерация документации |

---

## 2. Примеры команд

### Конфигурация

```bash
# Валидировать config.json
python manage_tools.py --config validate

# Обновить config от .env
python manage_tools.py --config sync-env

# Создать backup
python manage_tools.py --config backup
```

### Тестирование

```bash
# Запустить все тесты
python manage_tools.py --test all

# Запустить тесты с coverage
python manage_tools.py --test coverage

# Запустить специфичный модуль
python manage_tools.py --test src/ai
```

### Документация

```bash
# Сгенерировать документацию
python manage_tools.py --docs generate

# Обновить индексы
python manage_tools.py --docs update-index
```

---

## 3. Создание собственного инструмента

### Структура инструмента

```python
# tools/my_tool.py

class MyTool:
    """Описание моего инструмента."""
    
    @staticmethod
    def execute(args):
        """Выполнить инструмент.
        
        Args:
            args: Аргументы командной строки
        """
        print(f"Executing MyTool with args: {args}")
        return 0
```

### Регистрация инструмента

```python
# tools/__init__.py

from .my_tool import MyTool

TOOLS = {
    'my-tool': MyTool
}
```

### Использование

```bash
python manage_tools.py --my-tool --arg1 value1 --arg2 value2
```

---

## 4. Автоматизация с AI моделями

Модели могут автоматически запускать инструменты при определённых условиях.

Смотрите [`guides/MODEL_SCRIPTS.md`](MODEL_SCRIPTS.md) для полного руководства.

---

## 📚 Дополнительно

- [`guides/INSTALLATION.md`](INSTALLATION.md) — Установка проекта
- [`guides/MODEL_SCRIPTS.md`](MODEL_SCRIPTS.md) — Когда модели запускают скрипты

**Последнее обновление:** сентябрь 2026
