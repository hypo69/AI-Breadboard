# Скрипты документации

Этот раздел содержит скрипты для автоматизации процесса генерации, валидации и управления документацией проекта AI-Breadboard.

## Содержание

- `generate_api.py` - Генератор API-документации из Python docstrings
- `test_generate_api.py` - Unit-тесты для генератора API
- `validate_structure.py` - Валидатор структуры документации
- `check_links.py` - Проверяет ссылки в документации
- `test_check_links.py` - Unit-тесты для проверки ссылок

## Быстрый старт

### Генерация API-документации

```bash
python scripts/docs/generate_api.py
```

Этот скрипт:
1. Парсит Python docstrings в Google-формате
2. Извлекает информацию о функциях и классах
3. Генерирует Markdown файлы в `docs/ru/api/`
4. Создаёт индекс API

**Модули для генерации:**
- `src.skills` - Навыки системы
- `src.ai` - Компоненты AI
- `src.ai.agents` - Агенты
- `src.utils` - Утилиты

### Запуск тестов

```bash
python scripts/docs/test_generate_api.py
python scripts/docs/test_check_links.py
```

Запускает unit-тесты для компонентов:
- **test_generate_api.py** - тесты генератора API
  - DocstringParser - парсинг docstrings
  - MarkdownGenerator - генерация Markdown
  - APIDocumentationGenerator - управление генерацией

- **test_check_links.py** - тесты проверки ссылок (38+ тестов)
  - Извлечение ссылок из Markdown
  - Валидация внутренних ссылок
  - Обработка якорей и внешних ссылок
  - Разрешение относительных путей
  - Отчёты об ошибках

## Описание скриптов

### generate_api.py

**Назначение:** Автоматическая генерация API-документации из docstrings

**Классы:**

#### DocstringParser
Парсер для извлечения информации из Python docstrings в Google-формате.

Методы:
- `parse_function()` - Парсит функцию и извлекает информацию
- `parse_class()` - Парсит класс и его методы
- `parse_google_docstring()` - Парсит docstring в Google-формате

**Поддерживаемые разделы docstring:**
- Summary (первая строка)
- Description (подробное описание)
- Args: (параметры функции)
- Returns: (возвращаемое значение)
- Raises: (исключения)
- Examples: (примеры кода)

#### MarkdownGenerator
Генератор Markdown из распарсенной информации.

Методы:
- `generate_header()` - Создаёт Markdown заголовок
- `generate_code_block()` - Создаёт блок кода
- `generate_function_docs()` - Генерирует документацию функции
- `generate_class_docs()` - Генерирует документацию класса

#### APIDocumentationGenerator
Главный генератор, координирующий весь процесс.

Методы:
- `generate()` - Генерирует документацию для набора модулей
- `generate_module_docs()` - Генерирует документацию одного модуля
- `generate_api_index()` - Создаёт индексный файл API
- `process_python_file()` - Обрабатывает Python файл
- `print_summary()` - Выводит сводку по генерации

**Использование:**

```python
from generate_api import APIDocumentationGenerator
from pathlib import Path

# Инициализируем генератор
src_root = Path('src')
docs_root = Path('docs')
generator = APIDocumentationGenerator(src_root, docs_root)

# Генерируем документацию
modules = [
    'src.skills',
    'src.ai',
    'src.ai.agents',
    'src.utils',
]
generator.generate(modules)

# Выводим сводку
generator.print_summary()
```

### validate_structure.py

**Назначение:** Валидация структуры документации

**Функции:**
- Проверка наличия обязательных файлов
- Валидация синтаксиса Markdown
- Проверка обязательных разделов

### check_links.py

**Назначение:** Проверка ссылок в документации

**Класс LinkChecker:**

Методы:
- `collect_all_files()` - Собирает все доступные .md файлы в директории docs/ru/
- `extract_links(content)` - Извлекает ссылки из Markdown контента
- `resolve_relative_path(link, source_file)` - Разрешает относительные пути с учётом положения исходного файла
- `validate_internal_link(link, source_file)` - Проверяет валидность внутренней ссылки
- `check_file(md_file)` - Проверяет ссылки в одном Markdown файле
- `check_all()` - Проверяет все Markdown файлы в документации

**Проверяет:**
- Внутренние ссылки (../manual/file.md) - проверяет существование целевого файла
- Якоря (#якорь) - пропускает (считаются валидными)
- Внешние ссылки (http://, https://) - пропускает (не требуют проверки)
- Относительные пути с ../ и ./

**Использование:**

```bash
# Проверить ссылки в документации
python scripts/docs/check_links.py

# Вывод: отчёт об ошибках ссылок с exit code 0 (успех) или 1 (ошибки найдены)
```

**Результаты:**
- Exit code 0 - все ссылки корректны
- Exit code 1 - найдены ошибки в ссылках
- Вывод содержит полный список ошибок с указанием файла и неверной ссылки

**Примеры ошибок:**
```
❌ Неверная ссылка в manual/guide.md: 'missing.md' (целевой файл не найден: missing.md)
❌ Неверная ссылка в api/index.md: '../../nonexistent.md' (целевой файл не найден: nonexistent.md)
```

## Требования

Все скрипты используют только стандартную библиотеку Python:
- `ast` - парсинг Python кода
- `pathlib` - работа с путями
- `re` - регулярные выражения
- `typing` - type hints
- `unittest` - фреймворк для тестирования

**Python версия:** 3.10+

**Зависимости для тестирования:** pytest (опционально)
```bash
pip install pytest
python -m pytest scripts/docs/test_check_links.py -v
```

или использовать встроенный unittest:
```bash
python scripts/docs/test_check_links.py
```

## Структура выходных файлов

```
docs/ru/api/
├── index.md          # Индекс API с ссылками на все модули
├── skills.md         # API для src.skills
├── ai.md             # API для src.ai
├── agents.md         # API для src.ai.agents
└── utils.md          # API для src.utils
```

## Формат Google-style Docstring

Скрипты ожидают docstrings в следующем формате:

```python
def example_function(param1: str, param2: int) -> bool:
    """
    Краткое описание функции.
    
    Подробное описание функции, которое может быть
    многострочным и содержать дополнительную информацию.
    
    Args:
        param1: Описание первого параметра
        param2: Описание второго параметра
        
    Returns:
        Описание возвращаемого значения
        
    Raises:
        ValueError: Когда возникает эта ошибка
        TypeError: Когда возникает эта ошибка
        
    Examples:
        >>> result = example_function('test', 42)
        >>> print(result)
        True
    """
    # Реализация функции
    pass
```

## Результаты генерации

Каждый модуль генерирует Markdown файл со следующей структурой:

```markdown
# Модуль `src.skills`

Описание модуля из его docstring.

## Классы

### `ClassName(BaseClass)`

Описание класса.

**Атрибуты:**
- `attribute1`
- `attribute2`

### Методы

#### `method_name(param1, param2)`

Описание метода.

**Параметры:**

| Параметр | Описание |
|----------|---------|
| `param1` | Описание |
| `param2` | Описание |

**Возвращает:**

Описание возвращаемого значения.

## Функции

### `function_name(param1, param2)`

Описание функции.
```

## Интеграция с CI/CD

Скрипт рекомендуется запускать в составе GitHub Actions workflow перед сборкой документации:

```yaml
- name: Генерация API-документации
  run: python scripts/docs/generate_api.py

- name: Валидация документации
  run: python scripts/docs/validate_structure.py
  
- name: Проверка ссылок
  run: python scripts/docs/check_links.py
```

## Обработка ошибок

Скрипты выводят информативные сообщения об ошибках:

```
❌ Ошибка: директория исходного кода не найдена
✗ Ошибка при генерации документации для модуля: модуль_имя
⚠️  Предупреждение: Не удалось найти docstring
✓ Успешно сгенерирована документация для модуля: модуль_имя
```

## Примеры использования

### Пример 1: Генерация для одного модуля

```python
from generate_api import APIDocumentationGenerator
from pathlib import Path

gen = APIDocumentationGenerator(Path('src'), Path('docs'))
gen.generate(['src.skills'])
```

### Пример 2: Обработка файла напрямую

```python
from generate_api import APIDocumentationGenerator
from pathlib import Path

gen = APIDocumentationGenerator(Path('src'), Path('docs'))
result = gen.process_python_file(Path('src/skills/__init__.py'))
print(f"Найдено классов: {len(result['classes'])}")
print(f"Найдено функций: {len(result['functions'])}")
```

### Пример 3: Парсинг docstring

```python
from generate_api import DocstringParser

docstring = """
Функция для обработки данных.

Args:
    data: Входные данные
    
Returns:
    Обработанные данные
"""

result = DocstringParser.parse_google_docstring(docstring)
print(result['summary'])  # Функция для обработки данных
print(result['args'])     # {'data': 'Входные данные'}
```

## Возможные проблемы и решения

### Проблема: Модуль не найден

**Решение:** Убедитесь что модуль содержит `__init__.py` файл в корне.

### Проблема: Docstring не парсится

**Решение:** Проверьте что docstring используют Google-style формат и правильные отступы.

### Проблема: Выходные файлы пусты

**Решение:** Проверьте что в модулях присутствуют классы и функции с docstrings.

## Разработка

Для разработки новых функций используйте unit-тесты:

```bash
python scripts/docs/test_generate_api.py -v
```

## Лицензия

Эти скрипты являются частью проекта AI-Breadboard и используют ту же лицензию.

---

**Последнее обновление:** 2026-09-06
**Язык документации:** Русский
