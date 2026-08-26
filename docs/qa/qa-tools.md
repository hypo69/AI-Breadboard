# Инструменты QA

## Тестирование

### 1. pytest

**Основной фреймворк для тестирования.**

```bash
# Установка
pip install pytest pytest-asyncio pytest-cov

# Запуск всех тестов
pytest

# С покрытием
pytest --cov=src --cov=plugins --cov-report=html:htmlcov

# Конкретный файл
pytest tests/test_ai.py

# Конкретный класс
pytest tests/test_ai.py::TestGoogleGenerativeAI

# С фильтрацией по маркерам
pytest -m unit
pytest -m integration
pytest -m slow
```

**Команды pytest.ini:**
```ini
[pytest]
asyncio_mode = auto
asyncio_default_fixture_loop_scope = session
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --cov=src --cov=plugins --cov-report=term-missing --cov-report=html:htmlcov --cov-report=xml:coverage.xml --cov-config=.coveragerc --strict-markers
markers =
    unit: unit tests
    integration: integration tests
    slow: slow running tests
    database: database tests
    api: API endpoint tests
```

### 2. httpx

**Для асинхронного HTTP тестирования.**

```bash
pip install httpx

# Пример использования
import httpx

async with httpx.AsyncClient() as client:
    response = await client.get('http://localhost:3000/api/media/files')
    print(response.json())
```

### 3. coverage

**Для измерения покрытия кода тестами.**

```bash
pip install coverage

# Запуск с покрытием
coverage run -m pytest
coverage report -m
coverage html
```

## API Тестирование

### 1. curl

**Утилита командной строки для HTTP запросов.**

```bash
# GET запрос
curl http://localhost:3000/api/media/files

# POST запрос
curl -X POST http://localhost:3000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
```

### 2. httpie

**Более удобная альтернатива curl.**

```bash
pip install httpie

# GET запрос
http GET http://localhost:3000/api/media/files

# POST запрос с JSON
http POST http://localhost:3000/api/chat \
  message="Hello" \
  history:='[]'
```

### 3. Postman

**Графический интерфейс для тестирования API.**

**Коллекция:** `tests/postman_collection.json`

**Основные коллекции:**
- Chat API
- Media API
- Torrent API
- Auth API
- TTS API

## Отладка

### 1. Логирование

```python
from core.logger import logger

logger.info("Information message")
logger.error("Error message")
logger.warning("Warning message")
logger.debug("Debug message")
```

### 2. Отладка тестов

```bash
# Запуск с pdb
pytest --pdb tests/test_ai.py

# Остановка на первом ошибке
pytest -x tests/test_ai.py

# Отладочный вывод
pytest -vv tests/test_ai.py
```

## Валидация

### 1. JSON Schema

**Валидация структуры JSON ответов.**

```python
from jsonschema import validate, ValidationError

schema = {
    "type": "object",
    "properties": {
        "status": {"type": "string"},
        "text": {"type": "string"}
    },
    "required": ["status", "text"]
}

validate(instance=response.json(), schema=schema)
```

### 2. Pydantic

**Валидация моделей данных.**

```python
from pydantic import BaseModel

class ChatResponse(BaseModel):
    status: str
    text: str

response = ChatResponse(**response_data)
```

## CI/CD

### 1. GitHub Actions

**Автоматическое тестирование при push и pull request.**

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      - name: Run tests
        run: pytest --cov=src --cov=plugins --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: coverage.xml
```

### 2. Local Testing

```bash
# Установка зависимостей
pip install -r requirements.txt
pip install -r requirements-test.txt

# Запуск тестов
python run_tests.py --verbose

# С покрытием
python run_tests.py --coverage

# Открыть отчет
python run_tests.py --open-coverage
```

## Производительность

### 1. profiler

**Профилирование кода.**

```bash
pip install pytest-benchmark

# Запуск с бенчмарками
pytest --benchmark-enable tests/test_ai.py
```

### 2. memory profiler

**Проверка утечек памяти.**

```bash
pip install memory-profiler

# Запуск с profiling
pytest --memory-profile tests/test_ai.py
```

## Визуализация

### 1. HTML отчет о покрытии

```bash
pytest --cov=src --cov=plugins --cov-report=html:htmlcov
# Открыть htmlcov/index.html
```

### 2. Тест дашборд

**Пример:**

| Тест | Статус | Время |
|------|--------|-------|
| test_chat_with_mock | ✅ | 0.05s |
| test_verify_jwt_token | ✅ | 0.12s |
| test_get_media_files | ✅ | 0.08s |
| test_torrents_list | ⚠️ | 2.34s |
| test_rag_vector_search | ❌ | 0.01s |

---

[← Интеграционное тестирование](integration-testing.md)