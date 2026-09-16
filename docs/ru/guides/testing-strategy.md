# Руководство по стратегии тестирования

> **Цель:** Овладеть комплексным подходом к тестированию компонентов и систем в AI Breadboard.

---

## 📋 Содержание

1. [Философия тестирования](#философия-тестирования)
2. [Пирамида тестирования](#пирамида-тестирования)
3. [Unit тесты](#unit-тесты)
4. [Интеграционные тесты](#интеграционные-тесты)
5. [Тестирование Skills](#тестирование-skills)
6. [Тестирование Agents](#тестирование-agents)
7. [Property-based тестирование](#property-based-тестирование)
8. [CI/CD интеграция](#cicd-интеграция)
9. [Лучшие практики](#лучшие-практики)

---

## Философия тестирования

### Зачем тестировать?

```
┌─────────────────────────────────────────────┐
│ ТЕСТИРОВАНИЕ - это инвестиция              │
├─────────────────────────────────────────────┤
│                                             │
│ Без тестов:                                │
│ • Много багов в production                │
│ • Дорогой рефакторинг                     │
│ • Низкий темп разработки                  │
│ • Стресс и ночные звонки 📞               │
│                                             │
│ С тестами:                                │
│ • Уверенность в коде ✓                    │
│ • Безопасный рефакторинг                  │
│ • Быстрая разработка                      │
│ • Спокойный сон 😴                        │
│                                             │
└─────────────────────────────────────────────┘
```

### Цель тестирования

**Тесты — это не проверка кода. Тесты — это документация поведения.**

- 📝 Документируют, как использовать код
- 🔒 Защищают от регрессии
- 🧠 Помогают понять дизайн
- 🚀 Ускоряют разработку

---

## Пирамида тестирования

### Уровни тестирования

```
                    ▲
                   ╱ ╲
                  ╱   ╲
                 ╱ E2E ╲         5-10% тестов
                ╱───────╲
               ╱         ╲
              ╱ Integration╲     15-25% тестов
             ╱─────────────╲
            ╱               ╲
           ╱   Unit Tests    ╲   65-80% тестов
          ╱───────────────────╲
         ╱_____________________╲
```

### Соотношение тестов

| Тип | Количество | Скорость | Стоимость |
|-----|-----------|----------|----------|
| **Unit** | 70% | ⚡⚡⚡ Быстро | 💰 Дешево |
| **Integration** | 20% | ⚡⚡ Средне | 💰💰 Среднее |
| **E2E** | 10% | ⚡ Медленно | 💰💰💰 Дорого |

---

## Unit тесты

### Что такое unit тест?

**Unit тест** — тест одного компонента (функции, класса, модуля) в изоляции.

### Структура unit теста

```python
import pytest
from module import calculate_total

class TestCalculateTotal:
    """Тесты для функции calculate_total"""
    
    def test_simple_calculation(self):
        """Базовое вычисление: 2 + 3 = 5"""
        result = calculate_total([2, 3])
        assert result == 5
    
    def test_empty_list(self):
        """Пустой список должен вернуть 0"""
        result = calculate_total([])
        assert result == 0
    
    def test_negative_numbers(self):
        """Отрицательные числа обрабатываются корректно"""
        result = calculate_total([-1, -2, -3])
        assert result == -6
    
    def test_mixed_numbers(self):
        """Смесь положительных и отрицательных"""
        result = calculate_total([10, -5, 3])
        assert result == 8
    
    def test_large_numbers(self):
        """Большие числа"""
        result = calculate_total([1000000, 2000000])
        assert result == 3000000
```

### Правило AAA (Arrange-Act-Assert)

```python
def test_user_creation():
    # ARRANGE - подготовка данных
    user_data = {"name": "Alice", "email": "alice@example.com"}
    
    # ACT - выполнение действия
    user = create_user(user_data)
    
    # ASSERT - проверка результата
    assert user.name == "Alice"
    assert user.email == "alice@example.com"
    assert user.id is not None
```

### Таблица тестовых значений

```python
import pytest

@pytest.mark.parametrize("input_value,expected", [
    ([], 0),                    # пустой список
    ([1], 1),                   # один элемент
    ([1, 2, 3], 6),            # несколько элементов
    ([-1, -2], -3),            # отрицательные
    ([0, 0, 0], 0),            # нули
])
def test_sum_with_various_inputs(input_value, expected):
    """Тест с различными входными значениями"""
    assert calculate_total(input_value) == expected
```

### Примеры edge cases

```python
class TestDataValidation:
    """Тестирование граничных случаев"""
    
    def test_none_input(self):
        """None вызывает исключение"""
        with pytest.raises(TypeError):
            validate(None)
    
    def test_empty_string(self):
        """Пустая строка - валидна"""
        assert validate("") is True
    
    def test_very_long_string(self):
        """Очень длинная строка обрабатывается"""
        long_str = "a" * 10000
        result = validate(long_str)
        assert isinstance(result, bool)
    
    def test_special_characters(self):
        """Спецсимволы обрабатываются корректно"""
        assert validate("!@#$%^&*()") is True
```

---

## Интеграционные тесты

### Что тестировать?

Интеграционные тесты проверяют взаимодействие компонентов:

- 🔌 Модули работают вместе
- 💾 База данных сохраняет данные
- 🌐 API возвращает ожидаемые данные
- 📨 Сообщения доставляются

### Пример интеграционного теста

```python
import pytest
from database import Database
from service import UserService

@pytest.fixture
def db():
    """Создать тестовую БД"""
    database = Database(":memory:")  # SQLite in-memory
    database.init_schema()
    yield database
    database.close()

@pytest.fixture
def service(db):
    """Создать сервис с тестовой БД"""
    return UserService(db)

class TestUserService:
    def test_create_and_retrieve_user(self, service):
        """Создать пользователя и получить его"""
        # Создать
        user_id = service.create_user(
            name="Alice",
            email="alice@example.com"
        )
        
        # Получить
        user = service.get_user(user_id)
        
        # Проверить
        assert user.name == "Alice"
        assert user.email == "alice@example.com"
    
    def test_user_duplication_protection(self, service):
        """Нельзя создать два пользователя с одинаковым email"""
        service.create_user("Alice", "alice@example.com")
        
        with pytest.raises(DuplicateEmailError):
            service.create_user("Bob", "alice@example.com")
    
    def test_user_update(self, service):
        """Обновление пользователя"""
        user_id = service.create_user("Alice", "alice@example.com")
        
        service.update_user(user_id, name="Alice Updated")
        
        user = service.get_user(user_id)
        assert user.name == "Alice Updated"
```

---

## Тестирование Skills

### Структура тестов для Skill'а

```
skill-name/
├── scripts/
│   └── main.py
├── tests/
│   ├── __init__.py
│   ├── test_main.py         # Unit тесты
│   ├── test_integration.py  # Интеграционные
│   └── fixtures/
│       └── sample_data.json # Тестовые данные
└── SKILL.md
```

### Unit тест для Skill'а

```python
# tests/test_main.py
import pytest
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from main import analyze_json, validate_structure

class TestJSONAnalyzer:
    def test_analyze_simple_object(self):
        """Анализировать простой объект"""
        data = {"name": "Alice", "age": 30}
        result = analyze_json(data)
        
        assert result["type"] == "object"
        assert "name" in result["fields"]
        assert "age" in result["fields"]
    
    def test_analyze_nested_structure(self):
        """Анализировать вложенную структуру"""
        data = {
            "user": {
                "name": "Alice",
                "profile": {
                    "bio": "Developer"
                }
            }
        }
        result = analyze_json(data)
        
        assert result["depth"] == 3
    
    def test_validate_invalid_json(self):
        """Невалидный JSON вызывает исключение"""
        with pytest.raises(ValueError):
            validate_structure("{ invalid json }")
```

### Интеграционный тест для Skill'а

```python
# tests/test_integration.py
import json
import subprocess
from pathlib import Path

class TestSkillIntegration:
    def test_skill_end_to_end(self, tmp_path):
        """Полный цикл работы Skill'а"""
        # 1. Создать тестовый файл
        test_file = tmp_path / "test.json"
        test_data = {
            "users": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"}
            ]
        }
        test_file.write_text(json.dumps(test_data))
        
        # 2. Запустить skill
        result = subprocess.run(
            ["python", "scripts/main.py", str(test_file)],
            capture_output=True,
            text=True
        )
        
        # 3. Проверить результат
        assert result.returncode == 0
        output = result.stdout
        assert "users" in output
        assert "array" in output
```

---

## Тестирование Agents

### Unit тестирование компонентов агента

```python
import pytest
from agent import Agent, parse_action

class TestAgentComponents:
    def test_parse_action_basic(self):
        """Парсинг простого действия"""
        text = "Action: search_web(query='python')"
        action, params = parse_action(text)
        
        assert action == "search_web"
        assert params["query"] == "python"
    
    def test_parse_action_with_complex_params(self):
        """Парсинг действия со сложными параметрами"""
        text = """Action: query_db(sql='SELECT * FROM users WHERE age > 18')"""
        action, params = parse_action(text)
        
        assert action == "query_db"
        assert "age > 18" in params["sql"]
```

### Интеграционное тестирование агента

```python
import pytest
from unittest.mock import Mock, patch
from agent import Agent

@pytest.fixture
def mock_model():
    """Mock модели для тестирования"""
    model = Mock()
    model.chat.return_value = "Final Answer: The answer is 42"
    return model

@pytest.fixture
def agent(mock_model):
    """Создать агента с mock моделью"""
    return Agent(model=mock_model)

class TestAgent:
    def test_agent_simple_query(self, agent):
        """Агент обрабатывает простой запрос"""
        result = agent.run("What is 2+2?")
        
        assert "42" in result or "4" in result
        agent.model.chat.assert_called()
    
    def test_agent_with_tools(self, agent):
        """Агент использует инструменты"""
        agent.add_tool("add", lambda a, b: a + b)
        
        # Mock ответ модели с использованием tool
        agent.model.chat.return_value = """
Thought: I need to add 2 and 3
Action: add(2, 3)
Observation: 5
Final Answer: 2 + 3 = 5
"""
        
        result = agent.run("What is 2+3?")
        assert "5" in result
```

---

## Property-based тестирование

### Что такое property-based тестирование?

**Property-based тестирование** — это подход, когда вы определяете свойства, которые должны быть верны для **всех** входных данных, и генератор автоматически создает тестовые случаи.

### Пример с Hypothesis

```python
import pytest
from hypothesis import given, strategies as st

# Стратегии - описывают, какие данные генерировать
positive_integers = st.integers(min_value=1)
lists_of_integers = st.lists(st.integers())

class TestMathProperties:
    @given(st.integers(), st.integers())
    def test_addition_commutative(self, a, b):
        """Сложение коммутативно: a + b = b + a"""
        assert a + b == b + a
    
    @given(lists_of_integers)
    def test_sorted_list_length(self, numbers):
        """Сортированный список имеет ту же длину"""
        assert len(sorted(numbers)) == len(numbers)
    
    @given(lists_of_integers)
    def test_sum_of_empty_list_is_zero(self, numbers):
        """Сумма пустого списка равна 0"""
        if len(numbers) == 0:
            assert sum(numbers) == 0
```

### Стратегии Hypothesis

```python
from hypothesis import strategies as st

# Базовые типы
st.integers()               # Целые числа
st.floats()                 # Дробные числа
st.text()                   # Текст
st.booleans()               # True/False

# Контейнеры
st.lists(st.integers())     # Список целых чисел
st.sets(st.text())          # Множество текста
st.dictionaries(st.text(), st.integers())  # Dict: str -> int

# Комбинация
@given(st.one_of(st.integers(), st.floats()))
def test_numeric_type(value):
    """Тест работает для любого числового типа"""
    assert isinstance(value, (int, float))

# Собственные стратегии
valid_email = st.text().filter(lambda x: "@" in x and "." in x)

@given(valid_email)
def test_email_validation(email):
    """Тест с кастомной стратегией"""
    assert is_valid_email(email)
```

---

## CI/CD интеграция

### GitHub Actions пример

```yaml
# .github/workflows/tests.yml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.8', '3.9', '3.10', '3.11']
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements-dev.txt
    
    - name: Run tests
      run: |
        pytest tests/ --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### Локальное тестирование

```bash
# Установить зависимости
pip install -r requirements-dev.txt

# Запустить все тесты
pytest tests/

# Тесты конкретного файла
pytest tests/test_main.py

# С покрытием кода
pytest tests/ --cov=src

# Конкретный тест
pytest tests/test_main.py::TestClass::test_method

# С подробным выводом
pytest tests/ -v

# С быстрым выходом при первой ошибке
pytest tests/ -x
```

---

## Лучшие практики

### 1. Именование тестов

✅ **Правильно:**
```python
def test_user_creation_with_valid_email():
    """Ясно, что тестируется и какой результат"""
    pass

def test_authentication_fails_with_invalid_password():
    """Описывает условие и ожидаемый результат"""
    pass
```

❌ **Неправильно:**
```python
def test1():
    pass

def test_something():
    pass
```

### 2. Минимальность тестов

✅ **Правильно:**
```python
def test_add_two_numbers():
    result = add(2, 3)
    assert result == 5
```

❌ **Неправильно:**
```python
def test_add():
    # Слишком много в одном тесте
    assert add(2, 3) == 5
    assert add(-1, -2) == -3
    assert add(0, 0) == 0
    assert add(1000, 2000) == 3000
```

### 3. Использование fixtures

✅ **Правильно:**
```python
@pytest.fixture
def sample_user():
    return {"name": "Alice", "email": "alice@example.com"}

def test_user_creation(sample_user):
    user = create_user(sample_user)
    assert user.name == "Alice"
```

❌ **Неправильно:**
```python
def test_user_creation():
    # Дублирование подготовки в каждом тесте
    sample_user = {"name": "Alice", "email": "alice@example.com"}
    user = create_user(sample_user)
    assert user.name == "Alice"
```

### 4. Избегать зависимостей между тестами

✅ **Правильно:**
```python
def test_create_user():
    user = create_user("Alice")
    assert user.id is not None

def test_delete_user():
    user = create_user("Bob")
    result = delete_user(user.id)
    assert result is True
```

❌ **Неправильно:**
```python
user_id = None

def test_create_user():
    global user_id
    user = create_user("Alice")
    user_id = user.id
    assert user_id is not None

def test_delete_user():
    # Зависит от предыдущего теста!
    assert delete_user(user_id) is True
```

### 5. Тестирование ошибок

✅ **Правильно:**
```python
def test_create_user_with_duplicate_email():
    """Проверить, что дублирование email вызывает ошибку"""
    create_user("Alice", "alice@example.com")
    
    with pytest.raises(DuplicateEmailError):
        create_user("Bob", "alice@example.com")
```

❌ **Неправильно:**
```python
def test_create_user_with_duplicate_email():
    # Не проверяет исключение
    create_user("Alice", "alice@example.com")
    result = create_user("Bob", "alice@example.com")
    assert result is None  # Неточно!
```

---

## Контрольный список

### Перед отправкой PR

- [ ] Написаны unit тесты для новых функций
- [ ] Написаны интеграционные тесты для сложной логики
- [ ] Все тесты проходят (`pytest tests/`)
- [ ] Покрытие кода выше 80% (`pytest --cov`)
- [ ] Нет флакирующих тестов (запустить 2 раза подряд)
- [ ] Тесты документированы (есть docstring)
- [ ] Используются fixtures для подготовки данных
- [ ] Нет зависимостей между тестами

---

## 📚 Дополнительные ресурсы

- [Архитектура системы](../ARCHITECTURE.md)
- [Разработка Skills](developing-skills.md)
- [Создание Agents](creating-agents.md)
- [pytest документация](https://docs.pytest.org/)
- [Hypothesis документация](https://hypothesis.readthedocs.io/)
- [Testing Best Practices](https://testingjavascript.com/)

---

**Помните:** Хорошие тесты — это инвестиция, которая окупается в 10 раз! 🎯
