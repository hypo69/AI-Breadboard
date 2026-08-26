# Стратегия тестирования

## Обзор

Проект ai-assistant - это комплексное приложение с несколькими слоями:
1. Frontend Layer (HTML/CSS/JS)
2. Backend Layer (FastAPI + Python)
3. AI Layer (Google Gemini)
4. Media Layer (SQLite + TMDB API)
5. Plugin Layer (8 плагинов)
6. Storage Layer (SQLite + JSON)

## Подход к тестированию

### 1. Unit Testing (40%)

Тестируем отдельные модули изолированно с помощью моков.

**Цели:**
- Проверка логики отдельных функций
- Проверка обработки крайних случаев
- Быстрая обратная связь

**Модули:**
- `core/ai/` - AI модели и RAG
- `core/fastapi/` - роутеры и хендлеры
- `core/logger/` - логирование
- `core/tts/` - синтез речи
- `core/user_manager/` - управление пользователями
- `plugins/` - плагины

**Пример:**
```python
# tests/test_ai.py
def test_google_generative_ai_chat(mock_ai_model):
    mock_ai_model.chat.return_value = "Test response"
    result = await mock_ai_model.chat("Test question")
    assert result == "Test response"
```

### 2. Integration Testing (30%)

Тестируем взаимодействие между компонентами.

**Цели:**
- Проверка интеграции между модулями
- Проверка взаимодействия с внешними API
- Проверка работы с базой данных

**Сценарии:**
- API endpoints (GET/POST/PUT/DELETE)
- База данных (CRUD операции)
- Внешние API (TMDB, Gemini)
- Плагины (загрузка и обработка)

**Пример:**
```python
# tests/test_integration_api.py
def test_post_chat():
    response = client.post('/api/chat', json={'message': 'Hello'})
    assert response.status_code == 200
```

### 3. API Testing (20%)

Тестируем все API endpoints.

**Цели:**
- Проверка корректности ответов
- Проверка кодов статусов
- Проверка валидации входных данных
- Проверка обработки ошибок

**Тестируемые endpoints:**
- `/api/chat` - чат с AI
- `/api/media/*` - управление медиатекой
- `/api/torrents/*` - управление торрентами
- `/api/control/*` - управление плеером
- `/api/auth/*` - аутентификация
- `/api/tts/*` - синтез речи

### 4. Smoke Testing (10%)

Быстрые тесты перед деплоем.

**Цели:**
- Проверка базовой работоспособности
- Проверка запуска сервера
- Проверка основных endpoints

## Приоритеты тестирования

| Приоритет | Модуль | Тип | Частота |
|-----------|--------|-----|---------|
| P0 | Authentication | Integration | Каждый PR |
| P0 | API Core | Integration | Каждый PR |
| P1 | AI Models | Unit | Каждый PR |
| P1 | Media Scanner | Integration | Каждый PR |
| P2 | Plugins | Integration | Каждый PR |
| P2 | TTS | Unit | Каждый PR |
| P3 | Logger | Unit | Еженедельно |

## Критерии готовности к релизу

- [ ] 100% тестов проходит на CI
- [ ] Покрытие кода > 80%
- [ ] Критические баги (P0, P1) закрыты
- [ ] Документация актуальна
- [ ] Smoke тесты пройдены

---

[← QA README](index.md) | [Тест-кейсы →](test-cases.md)
