# Архитектура ИИ-интеграции в DataResearchEngine

В `DataResearchEngine` реализована возможность использования LLM-модели для глубокой интерпретации статистических данных (диагностика аномалий). Данная функциональность **уже активна** и интегрирована в архитектуру приложения.

## Текущая архитектура

### 1. Передача `chat_model` через AppState
Приложение использует паттерн инъекции зависимостей через `AppState` (FastAPI).

- Роутер `apps/research_and_statistic/router.py` принимает `state: "AppState"` при инициализации.
- При вызове эндпоинта `POST /apps/research-statistic/run-research`, `DataResearchEngine` инициализируется с передачей `state.chat_model`:

```python
# apps/research_and_statistic/router.py
engine = DataResearchEngine(user_id=0, chat_model=state.chat_model)
```

### 2. Регистрация роутера
Регистрация приложения в `src/app/__init__.py` корректно передает `state` для обеспечения доступа к ИИ-сервисам:

```python
# src/app/__init__.py
from apps.research_and_statistic.router import init_router as init_research_app_router
app.include_router(init_research_app_router(state))
```

### 3. ИИ-интерпретация в `diagnose()`
После инициализации с `chat_model`, метод `run_full_research` автоматически вызывает унаследованный метод `diagnose()`. 
- `DiagnosticEngine` использует `chat_model` для формирования исполнительного резюме (`executive assessment`) и рекомендаций при обнаружении аномалий эвристиками.

## Настройка
Функционал готов к работе. Убедитесь, что конфигурация ИИ (`config.json` / `.env`) корректно настроена для выбранного провайдера, так как `DataResearchEngine` использует `chat_model.ask(prompt)` для анализа данных при наличии обнаруженных аномалий.
