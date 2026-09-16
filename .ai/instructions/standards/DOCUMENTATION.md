# 📝 Стандарт документирования v1.0

**Статус:** ✅ Production Ready  
**Версия:** 1.0  
**Язык:** Русский (Mandatory)  
**Автор:** hypo69  
**Copyright:** © 2026 hypo69

---

## 📋 Содержание
1. [Общие принципы](#1-общие-принципы)
2. [Docstring формат (`hypo69 docblock`)](#2-docstring-формат-hypo69-docblock)
3. [Структура README.md](#3-структура-readmemd)
4. [Комментирование кода](#4-комментирование-кода)
5. [Заголовки файлов](#5-заголовки-файлов)
6. [Примеры](#6-примеры)

---

## 1. Общие принципы

### 1.1 Документирование = Часть кода
- Документация пишется **одновременно с кодом**, а не после.
- Каждая функция и класс **MUST** содержать docstring перед развёртыванием.
- Docstrings — это **часть кода**, а не опциональный комментарий.

### 1.2 Три уровня документирования

| Уровень | Описание | Где | Когда |
|---------|----------|-----|-------|
| **1. Docstring** | Описание функции/класса, параметры, результаты, примеры | В коде функции | При создании функции |
| **2. Комментарии** | Объяснение логики "почему", а не "что" | В критических местах | При сложной логике |
| **3. README.md** | Описание модуля, архитектура, использование, примеры | В директории модуля | При создании модуля |

### 1.3 Языковой стандарт: Русский язык
**Все docstrings, комментарии, заголовки файлов и документация ДОЛЖНЫ быть на русском языке.**

Исключение: Кириллица **ЗАПРЕЩЕНА** в файлах PHP и JavaScript (только English комментарии там).

---

## 2. Docstring формат (`hypo69 docblock`)

### 2.1 Структура (Обязательный порядок секций)

```text
Краткое описание (1 строка)

Полное описание (опционально, 2-3 предложения)

Args:
    param_name (type): Описание параметра и его назначение.
                       Значение по умолчанию: default_value.

Returns:
    type: Описание возвращаемого значения.

Exceptions:
    ExceptionType: Условия возникновения исключения.

Examples:
    >>> import module
    >>> result = function(param1, param2)
    >>> print(result)
    expected_output
```

**Порядок ОБЯЗАТЕЛЕН и НЕ ДОЛЖЕН изменяться.**

### 2.2 Секция `Args:`

- **MUST** содержать все параметры функции.
- Порядок совпадает с сигнатурой функции.
- Формат: `param_name (type): описание. Значение по умолчанию: default_value.`
- Типы записываются стандартом Python typing: `int`, `str`, `Optional[Dict]`, `List[str]`.

**Пример:**
```python
Args:
    timeout (int): Максимальное время ожидания в секундах.
                   Значение по умолчанию: 30.
    retry_count (Optional[int]): Количество повторных попыток.
                                 Значение по умолчанию: 0.
```

### 2.3 Секция `Returns:`

- Описывает тип и назначение возвращаемого значения.
- Если функция возвращает `False` при ошибке, указать это явно.
- Для методов цепочки (fluent): `Self: Текущий экземпляр класса для цепочки`.

**Примеры:**
```python
Returns:
    bool: True при успешном выполнении, False при ошибке.
    
Returns:
    Dict: Dictionary с ключами 'name', 'age', 'email' или empty {} при ошибке.
    
Returns:
    Self: Текущий экземпляр для цепочки вызовов.
```

### 2.4 Секция `Exceptions:`

- Перечисляет все типы исключений, которые может выбросить функция.
- Описывает условие, при котором выбрасывается exception.
- Опускается, если функция не выбрасывает исключений.

**Пример:**
```python
Exceptions:
    ValueError: Если параметр timeout <= 0.
    ConnectionError: Если не удалось подключиться к серверу за timeout секунд.
    FileNotFoundError: Если указанный путь не существует.
```

### 2.5 Секция `Examples:`

- **MUST** содержать работающий, скопируемый код.
- Минимально 1 пример.
- Использовать `>>>` для кода Python REPL.
- Показать ожидаемый результат без `>>>` перед ним.

**Пример:**
```python
Examples:
    >>> from src.ai import UnifiedChatModel
    >>> model = UnifiedChatModel(model_name='gemini-2.5-flash')
    >>> response = model.chat('Hello world')
    >>> print(len(response) > 0)
    True
```

### 2.6 Docstring функций (Python)

```python
def calculate_file_size(file_path: Optional[str] = '', timeout: Optional[int] = 10) -> int:
    """Вычисление размера файла в байтах.
    
    Функция получает размер файла через систему, обрабатывает ошибки 
    файловой системы и возвращает результат в байтах. При ошибке возвращает 0.
    
    Args:
        file_path (Optional[str]): Абсолютный или относительный путь к файлу.
                                    Значение по умолчанию: ''.
        timeout (Optional[int]): Максимальное время ожидания операции в секундах.
                                Значение по умолчанию: 10.
    
    Returns:
        int: Размер файла в байтах или 0 при ошибке/несуществовании файла.
    
    Exceptions:
        OSError: Если операционная система не позволяет прочитать метаданные файла.
        PermissionError: Если нет прав доступа к файлу.
    
    Examples:
        >>> size = calculate_file_size('/path/to/file.txt')
        >>> print(size > 0)
        True
        
        >>> # Несуществующий файл возвращает 0
        >>> size = calculate_file_size('/nonexistent/file.txt')
        >>> print(size)
        0
    """
    if not file_path:
        return 0
    
    try:
        return Path(file_path).stat().st_size
    except (FileNotFoundError, PermissionError) as ex:
        logger.error(f"Не удалось получить размер файла: {file_path}", exc_info=True)
        return 0
```

### 2.7 Docstring классов

```python
class MediaDatabase:
    """Управление SQLite базой данных медиатеки.
    
    Класс предоставляет единый интерфейс для работы с таблицами `media` и `series_episodes`,
    выполняет миграцию схемы, валидацию данных и резервное копирование.
    
    Attributes:
        db_path (str): Абсолютный путь к файлу БД (по умолчанию: 'media.db').
        connection (sqlite3.Connection): Объект подключения к БД.
    
    Examples:
        >>> db = MediaDatabase(db_path='./data/media.db')
        >>> db.initialize()
        >>> media_list = db.get_all_media()
        >>> print(len(media_list) > 0)
        True
    """
    
    def __init__(self, db_path: Optional[str] = '') -> None:
        """Инициализация объекта базы данных.
        
        Args:
            db_path (Optional[str]): Путь к файлу SQLite базы.
                                     Значение по умолчанию: '' (текущая директория).
        
        Examples:
            >>> db = MediaDatabase(db_path='./media.db')
        """
        self.db_path = db_path or Path.cwd() / 'media.db'
        self.connection = None
```

---

## 3. Структура README.md

### 3.1 Обязательное содержание

**Каждая директория (кроме служебных) MUST содержать README.md с:**

1. **Заголовок** — Название модуля
2. **Назначение** — Что делает модуль, его роль в проекте
3. **Архитектура** — Ключевые компоненты, диаграмма (если нужна)
4. **API** — Основной интерфейс использования
5. **Примеры** — Рабочий код с примерами
6. **Связанные модули** — Ссылки на зависимости
7. **Файловая структура** — Для сложных модулей

### 3.2 Шаблон README.md

```markdown
# Название модуля

**Описание:** Краткое описание функции модуля (15-25 слов).

## Архитектура

Основные компоненты:
- `file1.py` — Class `ClassName`, отвечает за X
- `file2.py` — Function `function_name()`, отвечает за Y

## Использование

### Базовый пример

\`\`\`python
from src.module import ClassName

obj = ClassName(param='value')
result = obj.method()
print(result)
\`\`\`

## Файлы

- `__init__.py` — Экспорт публичного API
- `main.py` — Основная логика
- `utils.py` — Вспомогательные функции

## Ссылки

- [`../../DOCUMENTATION_INDEX.md`](../../DOCUMENTATION_INDEX.md) — Главный индекс
- [`../parent_module/README.md`](../parent_module/README.md) — Родительский модуль
```

### 3.3 Исключения (README.md не нужен)

- `__pycache__/`, `.git/`, `venv/` — служебные директории
- Для простых утилит без сложной архитектуры

---

## 4. Комментирование кода

### 4.1 Философия: "Почему", а не "Что"

Комментарии объясняют **инженерное решение и логические предпосылки**, а не дублируют синтаксис языка.

```python
# ✅ ХОРОШО: Объясняется причина выбора структуры данных
# Использование Set вместо List для обеспечения O(1) поиска уникальных ID
active_connections = set()

# ❌ ПЛОХО: Просто дублирует синтаксис
# Создание множества активных подключений
active_connections = set()
```

### 4.2 Когда комментировать

- **Критические участки логики** — почему выбран этот путь.
- **Нестандартные решения** — почему не использован стандартный подход.
- **Ограничения и предусловия** — что должно быть истинно до выполнения.
- **Сложные алгоритмы** — пошаговое объяснение.

### 4.3 Когда НЕ комментировать

- Очевидный код (переменные имеют ясные имена).
- Синтаксис языка (что делает `for` цикл).
- Повторение docstring информации.

---

## 5. Заголовки файлов

### 5.1 Python (`.py`)

```python
# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Интеграция с локальным сервером Foundry
# =============================================================================
# Description:
#   Организация взаимодействия с API Foundry через HTTP-протокол.
#   Выполнение проверок доступности портов и управление процессами.
#
# Examples:
#   >>> from src.ai.providers.foundry import FoundryConnector
#   >>> connector = FoundryConnector(port=config.port)
#   >>> connector.verify_status()
#
# File: foundry_connector.py
# Project: AI Breadboard
# Module: src.ai.providers.foundry
# Class: FoundryConnector
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================
```

### 5.2 PowerShell (`.ps1`)

```powershell
# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Запуск FastAPI-сервера
# =============================================================================
# Description:
#   Подготовка виртуального окружения, загрузка конфигурации и запуск
#   сервера с проверкой портов и зависимостей.
#
# Examples:
#   .\run.ps1
#   .\launchers\Run-Unicorn.ps1
#
# File: run.ps1
# Project: AI Breadboard
# Module: Runtime
# Function: Start-Service
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================
```

---

## 6. Примеры

### 6.1 Полностью задокументированная функция

```python
def calculate_file_size(file_path: Optional[str] = '', timeout: Optional[int] = 10) -> int:
    """Вычисление размера файла в байтах.
    
    Функция получает размер файла через систему, обрабатывает ошибки 
    файловой системы и возвращает результат в байтах. При ошибке возвращает 0.
    
    Args:
        file_path (Optional[str]): Абсолютный или относительный путь к файлу.
                                    Значение по умолчанию: ''.
        timeout (Optional[int]): Максимальное время ожидания операции в секундах.
                                Значение по умолчанию: 10.
    
    Returns:
        int: Размер файла в байтах или 0 при ошибке/несуществовании файла.
    
    Exceptions:
        OSError: Если операционная система не позволяет прочитать метаданные файла.
        PermissionError: Если нет прав доступа к файлу.
    
    Examples:
        >>> size = calculate_file_size('/path/to/file.txt')
        >>> print(size > 0)
        True
        
        >>> # Несуществующий файл возвращает 0
        >>> size = calculate_file_size('/nonexistent/file.txt')
        >>> print(size)
        0
    """
    # Check входных параметров (Early Return)
    if not file_path:
        return 0
    
    try:
        return Path(file_path).stat().st_size
    except (FileNotFoundError, PermissionError) as ex:
        logger.error(f"Не удалось получить размер файла: {file_path}", exc_info=True)
        return 0
```

### 6.2 Полностью задокументированный класс

```python
class MediaDatabase:
    """Управление SQLite базой данных медиатеки.
    
    Класс предоставляет единый интерфейс для работы с таблицами `media` и `series_episodes`,
    выполняет миграцию схемы, валидацию данных и резервное копирование.
    
    Attributes:
        db_path (str): Абсолютный путь к файлу БД (по умолчанию: 'media.db').
        connection (sqlite3.Connection): Объект подключения к БД.
    
    Examples:
        >>> db = MediaDatabase(db_path='./data/media.db')
        >>> db.initialize()
        >>> media_list = db.get_all_media()
        >>> print(len(media_list) > 0)
        True
    """
    
    def __init__(self, db_path: Optional[str] = '') -> None:
        """Инициализация объекта базы данных.
        
        Args:
            db_path (Optional[str]): Путь к файлу SQLite базы.
                                     Значение по умолчанию: '' (текущая директория).
        
        Examples:
            >>> db = MediaDatabase(db_path='./media.db')
        """
        self.db_path = db_path or Path.cwd() / 'media.db'
        self.connection = None
    
    def initialize(self) -> bool:
        """Инициализация подключения к БД и создание таблиц.
        
        Returns:
            bool: True при успешной инициализации, False при ошибке.
        
        Exceptions:
            sqlite3.Error: При критических ошибках работы с БД.
        
        Examples:
            >>> db = MediaDatabase()
            >>> success = db.initialize()
            >>> print(success)
            True
        """
        # Попытка подключения к БД
        try:
            self.connection = sqlite3.connect(str(self.db_path))
            # Создание таблиц при необходимости
            self._create_tables()
            return True
        except sqlite3.Error as e:
            logger.error(f"Ошибка инициализации БД: {self.db_path}", exc_info=True)
            return False
    
    def _create_tables(self) -> None:
        """Создание требуемых таблиц в БД (если их нет)."""
        pass  # Реализация
```

---

## ✅ Чек-лист перед коммитом

- [ ] Все функции имеют docstrings с 4 секциями (Args, Returns, Exceptions, Examples).
- [ ] Все классы имеют docstrings с Attributes и Examples.
- [ ] Файл имеет корректный заголовок (Process Name, Description, File, Module, Author).
- [ ] Комментарии объясняют "почему", а не "что".
- [ ] README.md создан для новых модулей.
- [ ] Нет примеров с `None` в docstrings.
- [ ] Язык везде русский (кроме PHP и JS файлов).

---

**Последнее обновление:** сентябрь 2026
