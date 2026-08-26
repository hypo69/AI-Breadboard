# QA Engineer Documentation

## Введение

Это руководство для QA инженеров, работающих над проектом **ai-assistant** - AI-ассистентом с медиаплеером, Telegram Mini App, пультом дистанционного управления и голосовым вводом.

## Структура документации

| Документ | Описание |
|----------|----------|
| [README](index.md) | Общая информация для QA инженеров |
| [Стратегия тестирования](testing-strategy.md) | Подход к тестированию проекта |
| [Тест-кейсы](test-cases.md) | Подробные тест-кейсы по модулям |
| [API тестирование](api-testing.md) | Руководство по тестированию API |
| [Интеграционное тестирование](integration-testing.md) | Интеграционные сценарии |
| [Чеклист QA](qa-checklist.md) | Контрольный список для проверок |
| [Инструменты QA](qa-tools.md) | Список используемых инструментов |

## Быстрый старт

### Установка зависимостей

```bash
pip install -r requirements.txt
pip install -r requirements-test.txt
```

### Запуск тестов

```bash
# Все тесты
pytest

# С покрытием
pytest --cov=src --cov=plugins --cov-report=html:htmlcov

# Конкретный файл
pytest tests/test_ai.py

# Конкретный тест
pytest tests/test_ai.py::TestGoogleGenerativeAI::test_chat_with_mock
```

### Просмотр отчетов

```bash
# Открыть HTML отчет о покрытии
start htmlcov/index.html
```

## Типы тестов

| Тип | Описание | Доля |
|-----|----------|------|
| Unit | Модульное тестирование | 40% |
| Integration | Интеграционное тестирование | 30% |
| API | Тестирование API endpoints | 20% |
| Smoke | Быстрое тестирование | 10% |

## CI/CD

Тесты автоматически запускаются при каждом push и pull request.

**GitHub Actions workflow:** `.github/workflows/test.yml`

## Контакты

- **Project Lead**: hypo69
- **QA Lead**: [Ваше имя]
- **Slack**: #ai-assistant-qa

---

[← Назад к документации](../index.md)