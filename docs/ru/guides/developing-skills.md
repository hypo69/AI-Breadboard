# Руководство по разработке Skills

> **Цель:** Освоить создание собственных Skills для расширения возможностей AI Breadboard.

---

## 📋 Содержание

1. [Введение в Skills](#введение-в-skills)
2. [Архитектура Skills](#архитектура-skills)
3. [Структура директории](#структура-директории)
4. [Пример: Создание собственного Skill](#пример-создание-собственного-skill)
5. [Манифест SKILL.md](#манифест-skillmd)
6. [Лучшие практики](#лучшие-практики)
7. [Тестирование и отладка](#тестирование-и-отладка)

---

## Введение в Skills

### Что такое Skill?

**Skill** (навык) — это модульный компонент, который расширяет возможности AI Breadboard. Это может быть:

- **Инструмент** — специализированный сервис для выполнения конкретной задачи
- **Плагин** — расширение функциональности через интеграцию с внешними API
- **Функция** — набор скриптов для автоматизации процесса
- **Документация** — инструкции для модели о том, как решить задачу

### Проблема, которую решают Skills

Без системы Skills приходилось:
- 🔴 Добавлять весь код в систем-промпт (System Prompt Bloat)
- 🔴 Перегружать контекстное окно статическим текстом
- 🔴 Снижать качество ответов модели ("Lost in the Middle")
- 🔴 Дублировать инструкции в разных агентах

### Решение: Прогрессивное раскрытие

Skills реализуют **Progressive Disclosure**:

```
┌─────────────────────────────────────────┐
│ Постоянный контекст модели             │
├─────────────────────────────────────────┤
│ • Названия всех Skills (метаданные)    │
│ • Краткие описания (1-2 строки)        │
│ • Примеры вызова                       │
│ ~ 2-5 KB текста в каждом запросе      │
└─────────────────────────────────────────┘
            ↓
  Пользователь запрашивает функцию
            ↓
┌─────────────────────────────────────────┐
│ Динамически подгруженный контекст      │
├─────────────────────────────────────────┤
│ • Полный SKILL.md для релевантного     │
│   навыка (~5-20 KB при необходимости)  │
│ • Скрипты и примеры                    │
│ • Чек-листы и инструкции               │
└─────────────────────────────────────────┘
```

**Преимущества:**
- ✅ Минимальный оверхед для стандартных операций
- ✅ Полная поддержка сложного функционала при необходимости
- ✅ Улучшенная точность ответов модели
- ✅ Снижение стоимости API запросов

---

## Архитектура Skills

### Компоненты системы Skills

```
┌─────────────────────────────────────────────┐
│ Менеджер Skills (Manager)                  │
├─────────────────────────────────────────────┤
│ • Сканирование директорий                  │
│ • Парсинг манифестов (SKILL.md)           │
│ • Индексирование метаданных               │
│ • Discovery (поиск по описанию)           │
└────────────────┬────────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
┌───────▼──────┐  ┌──────▼────────┐
│ Skill #1     │  │ Skill #2      │
│              │  │               │
│ SKILL.md     │  │ SKILL.md      │
│ scripts/     │  │ scripts/      │
│ resources/   │  │ resources/    │
└──────────────┘  └───────────────┘
```

### Жизненный цикл Skill'а

```
1. РЕГИСТРАЦИЯ
   └─→ Менеджер сканирует .agents/skills/
   └─→ Парсит SKILL.md в каждой директории
   └─→ Создает индекс (имя, описание, версия)

2. ОБНАРУЖЕНИЕ (Discovery)
   └─→ Пользователь дает задание
   └─→ Менеджер ищет релевантные Skills
   └─→ Сравнивает описание задачи с метаданными

3. АКТИВАЦИЯ
   └─→ Модель получает полный SKILL.md
   └─→ Понимает, как использовать инструмент
   └─→ Готова вызвать скрипты

4. ВЫПОЛНЕНИЕ
   └─→ Скрипты Skill'а выполняются
   └─→ Результаты возвращаются модели
   └─→ Модель обрабатывает результаты

5. КЭШИРОВАНИЕ
   └─→ Использованный Skill кэшируется
   └─→ Следующий запрос быстрее
```

---

## Структура директории

### Стандартная структура Skill'а

```
.agents/skills/my-awesome-skill/
├── SKILL.md                      # Главный манифест (обязателен!)
├── README.md                     # Описание для разработчиков (опционально)
├── scripts/                      # Вспомогательные скрипты
│   ├── main.py                   # Основной Python скрипт
│   ├── helper.py                 # Вспомогательные функции
│   └── utils.sh                  # Bash утилиты для Linux/macOS
├── resources/                    # Ресурсы и конфигурации
│   ├── config.json               # Конфигурация Skill'а
│   ├── templates/                # Шаблоны файлов
│   └── data/                     # Статические данные
├── examples/                     # Примеры использования
│   ├── input_example.json        # Пример входных данных
│   └── output_example.json       # Эталонный результат
└── tests/                        # Тесты (опционально)
    ├── test_main.py              # Unit тесты
    └── test_integration.py       # Интеграционные тесты
```

### Минимальная структура

Для простого Skill'а достаточно:

```
.agents/skills/simple-skill/
├── SKILL.md          # Манифест (ОБЯЗАТЕЛЕН)
└── scripts/
    └── run.py        # Основной скрипт
```

---

## Пример: Создание собственного Skill

### Задача

Создадим Skill для **анализа структуры JSON файлов** — инструмент, который помогает понять структуру неизвестного JSON.

### Шаг 1: Автоматическая генерация через `skill-factory`

Рекомендуемый способ — использовать супернавык `skill-factory` или CLI `manage_tools.py`:

```bash
# Инициализация навыка с двуязычным описанием:
python .agents/skills/skill-factory/scripts/init_skill.py json-analyzer \
  --description-en "Analyzes JSON file structure, schema, statistics, and potential validation issues." \
  --description-ru "Анализирует структуру JSON файлов и выводит схему, статистику и потенциальные проблемы."
```

### Шаг 2: Манифест `SKILL.md` с поддержкой i18n

Манифест `SKILL.md` содержит каноническое английское описание и блок `description_i18n`:

```markdown
---
name: json-analyzer
description: Analyzes JSON file structure, schema, statistics, and potential validation issues.
description_i18n:
  en: Analyzes JSON file structure, schema, statistics, and potential validation issues.
  ru: Анализирует структуру JSON файлов и выводит схему, статистику и потенциальные проблемы.
  es: Analiza la estructura de archivos JSON, su esquema, estadísticas y posibles problemas.
version: 1.0.0
---

# JSON Analyzer Skill

Профессиональный инструмент для анализа JSON файлов.

## 📋 Возможности

- **Анализ структуры** — выводит схему JSON
- **Статистика** — размер, глубина, количество полей
- **Валидация** — проверяет корректность JSON
- **Предложения** — указывает на потенциальные проблемы

## 🚀 Использование

### Базовое использование

```bash
python scripts/main.py input.json
```

### С дополнительными опциями

```bash
python scripts/main.py input.json --detailed --validate --fix-errors
```

## 📊 Примеры

### Входные данные

```json
{
  "users": [
    {
      "id": 1,
      "name": "Alice",
      "email": "alice@example.com",
      "roles": ["admin", "user"]
    }
  ]
}
```

### Вывод анализатора

```
JSON Schema:
{
  "users": [
    {
      "id": "number",
      "name": "string",
      "email": "string",
      "roles": ["string"]
    }
  ]
}

Statistics:
- Total size: 145 bytes
- Depth: 3 levels
- Fields: 5
- Arrays: 1
```

## ⚙️ Параметры скрипта

| Параметр | Описание |
|----------|----------|
| `input` | Путь к JSON файлу |
| `--detailed` | Подробный анализ |
| `--validate` | Проверить корректность |
| `--fix-errors` | Попытаться исправить ошибки |
| `--output` | Путь для сохранения результатов |

## 📝 Чек-лист использования

- [ ] Проверить, что файл существует
- [ ] Убедиться, что файл в валидном JSON формате
- [ ] Выбрать уровень детализации анализа
- [ ] Сохранить результаты если нужно
- [ ] Рассмотреть предложения улучшений

## 🔧 Тестирование

```bash
# Unit тесты
python -m pytest tests/test_main.py

# Интеграционные тесты
python -m pytest tests/test_integration.py

# С покрытием
python -m pytest --cov=scripts tests/
```
```

### Шаг 3: Создание основного скрипта

**Файл:** `scripts/main.py`

```python
#!/usr/bin/env python3
"""JSON Analyzer - анализирует структуру JSON файлов"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def analyze_json_structure(data: Any, max_depth: int = 10) -> Dict[str, Any]:
    """
    Анализирует структуру JSON данных.
    
    Args:
        data: Распарсенные JSON данные
        max_depth: Максимальная глубина для анализа
        
    Returns:
        Словарь с информацией о структуре
    """
    def get_type(obj: Any) -> str:
        if isinstance(obj, bool):
            return "boolean"
        elif isinstance(obj, int):
            return "integer"
        elif isinstance(obj, float):
            return "number"
        elif isinstance(obj, str):
            return "string"
        elif isinstance(obj, list):
            return "array"
        elif isinstance(obj, dict):
            return "object"
        else:
            return "unknown"
    
    def build_schema(obj: Any, depth: int = 0) -> Any:
        if depth > max_depth:
            return "..."
        
        if isinstance(obj, dict):
            return {k: build_schema(v, depth + 1) for k, v in obj.items()}
        elif isinstance(obj, list):
            if obj:
                return [build_schema(obj[0], depth + 1)]
            return []
        else:
            return get_type(obj)
    
    def count_items(obj: Any) -> tuple:
        """Возвращает (объекты, массивы, примитивы, глубина)"""
        if isinstance(obj, dict):
            if not obj:
                return (1, 0, 0, 1)
            objs, arrays, prims, depths = 1, 0, 0, 1
            for v in obj.values():
                o, a, p, d = count_items(v)
                objs += o
                arrays += a
                prims += p
                depths = max(depths, d + 1)
            return (objs, arrays, prims, depths)
        elif isinstance(obj, list):
            if not obj:
                return (0, 1, 0, 1)
            objs, arrays, prims, depths = 0, 1, 0, 1
            for item in obj:
                o, a, p, d = count_items(item)
                objs += o
                arrays += a
                prims += p
                depths = max(depths, d + 1)
            return (objs, arrays, prims, depths)
        else:
            return (0, 0, 1, 1)
    
    schema = build_schema(data)
    objs, arrays, prims, depth = count_items(data)
    
    return {
        "schema": schema,
        "statistics": {
            "objects": objs,
            "arrays": arrays,
            "primitives": prims,
            "max_depth": depth,
        }
    }


def main():
    """Главная функция"""
    if len(sys.argv) < 2:
        print("Использование: python main.py <json_file> [--detailed]")
        sys.exit(1)
    
    json_file = Path(sys.argv[1])
    detailed = "--detailed" in sys.argv
    
    if not json_file.exists():
        print(f"Ошибка: Файл не найден: {json_file}")
        sys.exit(1)
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Ошибка: Невалидный JSON: {e}")
        sys.exit(1)
    
    result = analyze_json_structure(data)
    
    print("=" * 60)
    print("JSON STRUCTURE ANALYSIS")
    print("=" * 60)
    print(f"\nFile: {json_file}")
    print(f"Size: {json_file.stat().st_size} bytes")
    print("\nSchema:")
    print(json.dumps(result["schema"], indent=2, ensure_ascii=False))
    print("\nStatistics:")
    for key, value in result["statistics"].items():
        print(f"  {key}: {value}")
    print("=" * 60)


if __name__ == "__main__":
    main()
```

### Шаг 4: Тестирование Skill'а

**Файл:** `tests/test_main.py`

```python
import pytest
import json
from pathlib import Path
import sys

# Добавить путь к scripts
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from main import analyze_json_structure


def test_analyze_simple_object():
    """Тест анализа простого объекта"""
    data = {"name": "Alice", "age": 30}
    result = analyze_json_structure(data)
    
    assert "schema" in result
    assert "statistics" in result
    assert result["statistics"]["objects"] > 0


def test_analyze_array():
    """Тест анализа массива"""
    data = [1, 2, 3, 4, 5]
    result = analyze_json_structure(data)
    
    assert result["statistics"]["arrays"] > 0


def test_analyze_nested():
    """Тест анализа вложенной структуры"""
    data = {
        "users": [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"}
        ]
    }
    result = analyze_json_structure(data)
    
    assert result["statistics"]["max_depth"] > 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## Манифест SKILL.md

### Обязательные поля

```yaml
---
name: unique-skill-name          # Уникальное имя (lowercase, dashes)
description: "Краткое описание"   # 1-2 строки (будет в метаданных)
---
```

### Рекомендуемые поля

```yaml
---
name: my-skill
description: "Описание для модели"
version: 1.0.0                    # Семантическое версионирование
author: "Your Name"               # Автор Skill'а
category: "tools"                 # Категория: tools, integration, automation
tags:                             # Теги для поиска
  - analysis
  - data
  - validation
requires:                         # Зависимости
  - python: "3.8+"
  - pandas: "1.0+"
---
```

### Структура markdown части

```markdown
# Skill Title

## 📋 Возможности
- Возможность 1
- Возможность 2

## 🚀 Использование
### Базовое использование
...

### С параметрами
...

## 📊 Примеры
### Входные данные
### Вывод

## ⚙️ Параметры
| Параметр | Описание |

## 📝 Чек-лист
- [ ] Пункт 1
- [ ] Пункт 2

## 🔧 Тестирование
```

---

## Лучшие практики

### 1. Дизайн Skill'а

✅ **Правильно:**
- Skill выполняет одну задачу хорошо
- Четкое описание в манифесте
- Независим от других Skills
- Обработка ошибок

❌ **Неправильно:**
- Skill делает все понемногу
- Зависит от других Skills
- Нет обработки ошибок
- Неясное описание

### 2. Структура кода

✅ **Правильно:**
```python
def analyze_data(input_file: str, **options) -> Dict:
    """Документированная функция с типами"""
    if not Path(input_file).exists():
        raise FileNotFoundError(f"Файл не найден: {input_file}")
    
    result = _process(input_file)
    return result
```

❌ **Неправильно:**
```python
def analyze(f, **opt):
    # Нет документации
    # Нет обработки ошибок
    data = open(f).read()
    return process(data)
```

### 3. Форматирование SKILL.md

✅ **Правильно:**
- Четкие заголовки (H2 `##`)
- Примеры в коде-блоках
- Чек-листы для пользователя
- Описание параметров в таблице

❌ **Неправильно:**
- Стена текста без структуры
- Примеры в обычном тексте
- Неполная информация

### 4. Версионирование

Используйте **семантическое версионирование** (SemVer):
- `1.0.0` — основной релиз
- `1.1.0` — добавлена функция (minor)
- `1.0.1` — исправлена ошибка (patch)
- `2.0.0` — несовместимые изменения (major)

### 5. Зависимости

Указывайте в SKILL.md:

```yaml
requires:
  - python: "3.8+"
  - requests: "2.28+"
  - pandas: "1.3+"
```

Не добавляйте зависимости в глобальный `requirements.txt` без согласования.

---

## Тестирование и отладка

### Unit тесты

```python
import pytest
from scripts.main import analyze_json_structure

def test_basic_analysis():
    data = {"key": "value"}
    result = analyze_json_structure(data)
    assert result["statistics"]["objects"] > 0
```

### Интеграционные тесты

```python
from pathlib import Path
import json

def test_analyze_real_file(tmp_path):
    # Создать тестовый файл
    test_file = tmp_path / "test.json"
    test_file.write_text(json.dumps({"test": "data"}))
    
    # Протестировать
    result = analyze_json_structure(test_file)
    assert result is not None
```

### Отладка

**Добавьте логирование:**

```python
import logging

logger = logging.getLogger(__name__)

def analyze_data(file_path):
    logger.debug(f"Analyzing file: {file_path}")
    try:
        result = process(file_path)
        logger.info(f"Analysis complete: {len(result)} items")
        return result
    except Exception as e:
        logger.error(f"Error: {e}")
        raise
```

**Используйте для отладки:**

```bash
# Включить debug логирование
export LOGLEVEL=DEBUG
python scripts/main.py test.json
```

---

## Публикация Skill'а

Когда Skill готов к использованию:

1. ✅ Проверьте документацию SKILL.md
2. ✅ Запустите все тесты
3. ✅ Добавьте примеры использования
4. ✅ Обновите версию в манифесте
5. ✅ Создайте pull request с описанием

---

## 📚 Дополнительные ресурсы

- [Архитектура Skills](../ARCHITECTURE.md)
- [Создание Agents](creating-agents.md)
- [Стратегия тестирования](testing-strategy.md)
- [Учебная книга — Глава 7](../cook-book/ch07_skills_management.md)

---

**Успехов в разработке Skills!** 🚀
