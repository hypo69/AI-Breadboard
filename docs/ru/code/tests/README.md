# Тесты ai-assistant

## Структура

```
tests/
├── __init__.py           # Инициализация
├── conftest.py           # Общие фикстуры
├── data/                 # Тестовые данные
│   └── __init__.py
├── test_ai.py            # Тесты AI модуля
├── test_fastapi.py       # Тесты FastAPI роутеров
├── test_tts.py           # Тесты TTS модуля
├── test_user_manager.py  # Тесты user_manager
├── test_logger.py        # Тесты логирования
├── test_plugins.py       # Тесты плагинов
├── test_integration_api.py  # Интеграционные API тесты
└── test_environment.py   # Тесты окружения и конфигурации
```

## Установка зависимостей

```bash
# Установка основных зависимостей
pip install -r requirements.txt

# Установка тестовых зависимостей
pip install -r requirements-test.txt
```

## Запуск тестов

### Все тесты
```bash
pytest
```

### Конкретный файл
```bash
pytest tests/test_ai.py
pytest tests/test_fastapi.py
```

### Конкретный класс/метод
```bash
pytest tests/test_ai.py::TestGoogleGenerativeAI
pytest tests/test_ai.py::TestGoogleGenerativeAI::test_chat_with_mock
```

### С покрытием
```bash
pytest --cov=src --cov=plugins --cov-report=term-missing
```

### С фильтрацией
```bash
# Только unit тесты
pytest -m unit

# Только интеграционные
pytest -m integration

# Без медленных тестов
pytest -m "not slow"
```

## CI/CD

Для GitHub Actions добавьте в `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      - name: Run tests
        run: |
          pytest --cov=src --cov=plugins --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: coverage.xml
```

## Используемые фикстуры

- `mock_ai_model` - мок для AI модели
- `mock_db` - мок для MediaDatabase
- `mock_qbt_client` - мок для qBittorrentClient
- `temp_db_path` - временная база данных
- `sample_media_records` - примеры медиа записей
- `sample_torrents` - примеры торрентов
- `setup_env` - автозапуск настройки переменных
