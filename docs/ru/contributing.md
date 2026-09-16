# Правила контрибуции в AI-Breadboard

Спасибо за интерес к разработке AI-Breadboard! Этот документ содержит правила и рекомендации для контрибьюторов.

## Содержание

- [Начало работы](#начало-работы)
- [Процесс Pull Request](#процесс-pull-request)
- [Требования к коду](#требования-к-коду)
- [Требования к docstrings](#требования-к-docstrings)
- [Требования к commit messages](#требования-к-commit-messages)
- [Примеры структуры документации](#примеры-структуры-документации)
- [Локальное тестирование](#локальное-тестирование)
- [Примеры хороших docstrings](#примеры-хороших-docstrings)
- [Стиль кодирования](#стиль-кодирования)

## Начало работы

1. **Форкните репозиторий** - создайте свой fork проекта на GitHub
2. **Клонируйте fork** - скопируйте код себе локально:
   ```bash
   git clone https://github.com/YOUR_USERNAME/breadboard.git
   cd breadboard
   ```

3. **Создайте виртуальное окружение**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # На Windows: venv\Scripts\activate
   ```

4. **Установите зависимости**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-test.txt
   pip install -r requirements-docs.txt
   ```

5. **Создайте ветку** для вашего изменения:
   ```bash
   git checkout -b feature/my-new-feature
   ```

## Процесс Pull Request

### 1. Подготовка PR

Перед отправкой pull request убедитесь:

- [ ] Ваша ветка создана от свежего `main` или `develop`
- [ ] Код соответствует [требованиям стиля](#стиль-кодирования)
- [ ] Все тесты проходят локально
- [ ] Документация обновлена (если необходимо)
- [ ] Коммиты имеют понятные сообщения

### 2. Отправка PR

1. Отправьте вашу ветку в fork:
   ```bash
   git push origin feature/my-new-feature
   ```

2. Перейдите на GitHub и создайте Pull Request
3. Заполните шаблон PR:
   - Описание изменений
   - Связанные issues (если есть)
   - Инструкции по тестированию
   - Скриншоты/видео (если применимо)

### 3. Процесс review

- Минимум 1 approver требуется для merge
- CI/CD pipeline должен пройти успешно
- При комментариях - внесите исправления и отправьте обновление
- Используйте "Resolve conversation" только после исправления

### 4. Merge PR

После получения approvals:
- Ваша ветка будет merged в `main`
- Ветка будет удалена с GitHub
- Изменения будут задеплоены в продакшн

## Требования к коду

### Язык Python

- **Версия**: Python 3.8+
- **PEP 8**: Следуйте стандартам PEP 8
- **Type hints**: Используйте type hints для всех параметров и возвращаемых значений
- **Линтинг**: Код должен проходить проверку через `pylint`, `flake8`

### Примеры требований

**Правильно:**
```python
def calculate_average(numbers: List[float]) -> float:
    """Вычисляет среднее арифметическое списка чисел.
    
    Args:
        numbers: Список чисел
        
    Returns:
        Среднее арифметическое
        
    Raises:
        ValueError: Если список пуст
    """
    if not numbers:
        raise ValueError("Список не может быть пуст")
    return sum(numbers) / len(numbers)
```

**Неправильно:**
```python
def calc_avg(nums):
    # Функция для вычисления среднего
    if len(nums) == 0:
        return 0
    return sum(nums) / len(nums)
```

### Структура проекта

- `src/` - исходный код
- `tests/` - тесты
- `docs/` - документация
- `scripts/` - служебные скрипты
- `integrations/` - интеграции с внешними сервисами

## Требования к docstrings

Используйте **Google-style docstrings** для всех модулей, классов и функций.

### Формат для функций

```python
def create_skill(name: str, description: str, tags: List[str]) -> Skill:
    """Создает новый skill.
    
    Функция инициализирует skill с указанными параметрами и проводит
    базовую валидацию.
    
    Args:
        name: Имя skill (уникально в системе)
        description: Описание функциональности skill
        tags: Список тегов для категоризации
        
    Returns:
        Объект Skill с заполненными полями
        
    Raises:
        ValueError: Если name содержит недопустимые символы
        ValueError: Если description пуст
        
    Examples:
        >>> skill = create_skill("translator", "Переводит текст", ["ai", "nlp"])
        >>> skill.name
        'translator'
        >>> len(skill.tags)
        2
    """
    if not name or not re.match(r'^[a-z_][a-z0-9_]*$', name):
        raise ValueError(f"Недопустимое имя skill: {name}")
    if not description:
        raise ValueError("Описание skill не может быть пусто")
    
    return Skill(name=name, description=description, tags=tags)
```

### Формат для классов

```python
class SkillExecutor:
    """Исполнитель tasks для skills.
    
    Управляет выполнением tasks в контексте определённого skill.
    Обеспечивает изоляцию, логирование и управление состоянием
    выполнения.
    
    Attributes:
        skill: Skill, который исполняется
        timeout: Таймаут выполнения в секундах
        max_retries: Максимум попыток переexecution
        
    Examples:
        >>> executor = SkillExecutor(skill, timeout=30)
        >>> result = executor.execute(task)
    """
    
    def __init__(self, skill: Skill, timeout: int = 300, max_retries: int = 3):
        """Инициализирует SkillExecutor.
        
        Args:
            skill: Skill для выполнения
            timeout: Таймаут в секундах
            max_retries: Максимум переtriedов
        """
        self.skill = skill
        self.timeout = timeout
        self.max_retries = max_retries
```

### Требования к docstrings

- **Обязательные разделы**: `Args`, `Returns`, `Raises` (если применимо)
- **Examples**: Добавляйте примеры использования
- **Русский язык**: Всё должно быть на русском
- **Актуальность**: Docstring должен соответствовать реальной реализации
- **Линия символов**: Максимум 79 символов на строку

## Требования к commit messages

### Формат

```
<тип>(<область>): <описание>

<тело>

<footers>
```

### Типы

- `feat` - новая функция
- `fix` - исправление ошибки
- `docs` - обновление документации
- `style` - изменение стиля кода (форматирование)
- `refactor` - рефакторинг кода
- `perf` - улучшение производительности
- `test` - добавление/изменение тестов
- `chore` - технические изменения (обновление зависимостей и т.д.)

### Области

- `api` - API документация
- `docs` - файлы документации
- `core` - ядро (core)
- `skills` - skills
- `agents` - agents
- `ci` - CI/CD pipeline
- `tests` - тесты

### Примеры

**Хорошо:**
```
feat(skills): добавить поддержку асинхронного выполнения skills

- Реализован класс AsyncSkillExecutor
- Добавлены методы для обработки Promise-подобных операций
- Тесты покрывают основные сценарии

Fixes #123
```

```
fix(core): исправить race condition в cache layer

Заменена примитивная синхронизация на threading.RLock для
предотвращения одновременного доступа к кэшу.

Closes #456
```

```
docs(contributing): обновить требования к docstrings

Добавлены примеры для Google-style docstrings и требования
к type hints.
```

### Правила

- Первая строка - короче 50 символов
- Используйте imperative mood ("добавить", а не "добавил")
- Не заканчивайте точкой
- Разделяйте логические части пустой строкой
- Ссылайтесь на issues: `Fixes #123`, `Closes #456`

## Примеры структуры документации

### Добавление страницы в manual/

Раздел `manual/` содержит справочную документацию и пошаговые инструкции.

**Структура файла:**
```markdown
# Название компонента

## Описание

Краткое описание функциональности.

## Основные возможности

- Возможность 1
- Возможность 2

## Использование

### Пример 1

```python
# Ваш код здесь
```

## Связанные разделы

- [Руководство пользователя](./manual/index.md)
```

**Файловая структура:**
```
docs/ru/manual/
├── component-name.md
├── another-component.md
└── README.md
```

### Добавление страницы в guides/

Раздел `guides/` содержит практические руководства и примеры использования.

**Структура файла:**
```markdown
# Как сделать X

## Введение

Зачем нужно это делать и в каких случаях.

## Предварительные условия

- Требование 1
- Требование 2

## Пошагово

1. Первый шаг

```python
code_example()
```

2. Второй шаг

## Полный пример

```python
# Полный рабочий пример
```

## Что дальше

- Следующий шаг 1
- Следующий шаг 2

## Частые вопросы

**Q: Вопрос?**
A: Ответ.
```

**Файловая структура:**
```
docs/ru/guides/
├── getting-started.md
├── advanced-usage.md
└── README.md
```

### Обновление архитектуры

Документ `ARCHITECTURE.md` описывает структуру проекта на высоком уровне.

**Что обновлять:**
1. При добавлении нового модуля - добавить раздел в архитектуру
2. При изменении взаимодействия компонентов - обновить диаграммы
3. При добавлении интеграции - документировать взаимодействие

**Формат:**
```markdown
## Название компонента

### Описание

Что делает компонент и как он интегрирован.

### Интерфейсы

- `Interface1`: Описание
- `Interface2`: Описание

### Зависимости

- `dependency1`
- `dependency2`

### Диаграмма

```
[Компонент A] --> [Компонент B]
     |
     v
[Компонент C]
```
```

### Общие требования к документации

1. **Язык**: Русский или английский (консистентно в одном документе)
2. **Стиль**: Ясный, лаконичный, без лишних подробностей
3. **Примеры**: Все примеры должны быть рабочими и актуальными
4. **Ссылки**: Используйте относительные ссылки на другие документы
5. **Форматирование**: Следуйте стандартам Markdown

## Локальное тестирование

### Установка тестовых зависимостей

```bash
pip install -r requirements-test.txt
```

### Запуск всех тестов

```bash
pytest
```

### Запуск конкретного теста

```bash
pytest tests/test_skill.py::test_create_skill
```

### Запуск тестов с покрытием

```bash
pytest --cov=src --cov-report=html
```

### Запуск с verbose

```bash
pytest -v
```

### Запуск property-based тестов

```bash
pytest --hypothesis-show-statistics
```

### Сборка документации

Для локальной сборки документации используйте:

```bash
make docs-build
```

Или вручную:

```bash
cd docs/ru
sphinx-build -b html . _build
```

После успешной сборки откройте `docs/ru/_build/index.html` в браузере.

### Валидация документации

Перед отправкой PR проверьте документацию:

```bash
make docs-validate
```

Эта команда проверяет:
- Синтаксис Markdown
- Корректность ссылок
- Наличие обязательных разделов
- Форматирование примеров кода

### Просмотр изменений локально

Для просмотра изменений в реальном времени используйте:

```bash
make docs-serve
```

Сервер будет доступен по адресу `http://localhost:8000`

При сохранении файлов документация автоматически пересобирается.

### Проверка качества кода

```bash
# Линтинг
pylint src/
flake8 src/

# Type checking
mypy src/

# Форматирование (только проверка)
black --check src/

# Форматирование (применить исправления)
black src/

# Все вместе
make lint
```

## Примеры хороших docstrings

### Пример 1: Простая функция с параметрами

```python
def get_user_by_email(email: str) -> Optional[User]:
    """Получает пользователя по электронной почте.
    
    Ищет пользователя в базе данных по точному совпадению 
    электронной почты. Поиск нечувствителен к регистру.
    
    Args:
        email: Email адрес пользователя для поиска
        
    Returns:
        Объект User если пользователь найден, иначе None
        
    Raises:
        ValueError: Если email имеет неправильный формат
        DatabaseError: Если произошла ошибка при обращении к БД
        
    Examples:
        >>> user = get_user_by_email("john@example.com")
        >>> user.name
        'John Doe'
        >>> 
        >>> not_found = get_user_by_email("unknown@example.com")
        >>> not_found is None
        True
    """
    if '@' not in email:
        raise ValueError(f"Неправильный формат email: {email}")
    # Остальной код...
```

### Пример 2: Функция с множественными returns

```python
def validate_and_parse(data: str) -> Tuple[bool, Dict[str, Any]]:
    """Валидирует и парсит JSON строку.
    
    Проверяет корректность JSON и преобразует его в словарь.
    Если валидация не пройдена, возвращает False и пустой словарь.
    
    Args:
        data: JSON строка для парсинга
        
    Returns:
        Кортеж (успешно, результат):
        - успешно (bool): True если парсинг прошёл успешно
        - результат (dict): Распарсенные данные или пусто {} при ошибке
        
    Examples:
        >>> success, data = validate_and_parse('{"key": "value"}')
        >>> success
        True
        >>> data["key"]
        'value'
        >>>
        >>> success, data = validate_and_parse('invalid json')
        >>> success
        False
        >>> data
        {}
    """
    # Остальной код...
```

### Пример 3: Сложный класс с методами

```python
class DocumentProcessor:
    """Процессор для обработки документов.
    
    Класс обеспечивает полный цикл обработки документов: загрузку,
    валидацию, преобразование и сохранение. Поддерживает асинхронное
    выполнение операций и обработку ошибок.
    
    Attributes:
        config: Конфигурация процессора
        output_format: Формат выходных данных (json, xml, csv)
        max_retries: Максимальное количество попыток обработки
        
    Examples:
        >>> processor = DocumentProcessor(config, output_format="json")
        >>> result = processor.process("document.pdf")
        >>> result.success
        True
        >>> result.data
        {...}
    """
    
    def __init__(self, config: Config, output_format: str = "json"):
        """Инициализирует DocumentProcessor.
        
        Args:
            config: Объект конфигурации
            output_format: Формат результата (json, xml, csv)
            
        Raises:
            ValueError: Если output_format не поддерживается
        """
        self.config = config
        self.output_format = output_format
        self.max_retries = 3
        
    def process(self, file_path: str) -> ProcessResult:
        """Обрабатывает документ.
        
        Args:
            file_path: Путь к файлу документа
            
        Returns:
            ProcessResult: Результат обработки с данными и статусом
            
        Raises:
            FileNotFoundError: Если файл не найден
            ProcessingError: Если обработка не удалась после всех попыток
            
        Examples:
            >>> result = processor.process("data/document.pdf")
            >>> if result.success:
            ...     print(result.data)
        """
        # Остальной код...
        pass
```

### Пример 4: Класс с асинхронными методами

```python
class AsyncDataFetcher:
    """Асинхронный загрузчик данных.
    
    Загружает данные из множественных источников параллельно
    с кэшированием результатов и обработкой таймаутов.
    
    Examples:
        >>> async def main():
        ...     fetcher = AsyncDataFetcher()
        ...     data = await fetcher.fetch_all(["url1", "url2"])
        ...     return data
    """
    
    async def fetch(self, url: str, timeout: int = 30) -> str:
        """Загружает данные по URL асинхронно.
        
        Загружает данные, кэширует результат и возвращает содержимое.
        При повторном обращении возвращает данные из кэша.
        
        Args:
            url: URL для загрузки
            timeout: Таймаут в секундах
            
        Returns:
            Содержимое ответа в виде строки
            
        Raises:
            TimeoutError: Если превышен таймаут
            ConnectionError: Если не удалось подключиться
            
        Examples:
            >>> data = await fetcher.fetch("https://api.example.com/data")
            >>> len(data) > 0
            True
        """
        # Остальной код...
        pass
```

### Рекомендации по написанию docstrings

1. **Начните с краткого описания** - одна строка, что делает функция
2. **Добавьте подробное описание** - объясните how и why, если не очевидно
3. **Документируйте все параметры** - даже необязательные
4. **Укажите тип возвращаемого значения** - даже если используется Type hints
5. **Перечислите все исключения** - включая условия, при которых они возникают
6. **Приведите примеры** - рабочие примеры использования, особенно для сложных функций
7. **Обновляйте при изменениях** - docstring должен быть актуальным с кодом
8. **Не повторяйте Type hints** - используйте Type hints в функции, не в docstring
9. **Будьте ясны и лаконичны** - избегайте лишних деталей
10. **Проверьте примеры** - примеры в docstring должны быть рабочими

## Стиль кодирования

### Конвенции названий

- **Модули**: `snake_case` (e.g., `skill_executor.py`)
- **Классы**: `PascalCase` (e.g., `SkillExecutor`)
- **Функции/методы**: `snake_case` (e.g., `execute_task()`)
- **Константы**: `UPPER_SNAKE_CASE` (e.g., `MAX_TIMEOUT`)
- **Приватные методы**: `_snake_case` (e.g., `_validate_input()`)

### Импорты

Порядок импортов:
1. Стандартная библиотека
2. Сторонние пакеты
3. Локальные импорты

```python
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional

import numpy as np
from pydantic import BaseModel

from src.core import Config
from src.skills import Skill
```

### Максимальная длина строки

- **Код**: 100 символов
- **Docstrings и комментарии**: 79 символов
- **URLs и длинные строки**: исключение

### Использование черт

```python
# Хорошо
user = User.objects.filter(active=True).first()

# Плохо
users = User.objects.all()
active_user = None
for user in users:
    if user.active:
        active_user = user
        break
```

## Дополнительные ресурсы

- [PEP 8 Style Guide](https://www.python.org/dev/peps/pep-0008/)
- [PEP 257 Docstring Conventions](https://www.python.org/dev/peps/pep-0257/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [AI-Breadboard Documentation](./index.md)

## Связь с командой

- **Issues**: Используйте GitHub Issues для отчётов об ошибках и предложений
- **Discussions**: Обсуждайте идеи в GitHub Discussions
- **Email**: Свяжитесь с командой через info@breadboard.ai

---

**Спасибо за вашу контрибуцию в развитие AI-Breadboard!** 🙏
