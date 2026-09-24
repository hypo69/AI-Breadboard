# Уровень оркестрации (`src/ai/orchestration`)

## Обзор
**Уровень оркестрации (Orchestration Layer)** обеспечивает унифицированную маршрутизацию, классификацию и отслеживание здоровья моделей, определение аппаратного ускорения и диспетчеризацию возможностей AI-провайдеров между локальными и облачными бэкендами.

---

## Основные компоненты

```
                    ┌─────────────────────────┐
                    │       AIRouter          │
                    └───────────┬─────────────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
┌──────────────────┐  ┌───────────────────┐  ┌───────────────────┐
│ DiscoveryEngine  │  │CapabilityRegistry │  │  ModelErrorHub    │
│ (Hardware & Port)│  │ (Chat/Vision/OCR) │  │(Классификатор &   │
└──────────────────┘  └───────────────────┘  │  Health Registry) │
                                             └───────────────────┘
```

1. **[`hardware.py`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/src/ai/orchestration/hardware.py)**: Диагностика CPU, GPU (CUDA, DirectML), NPU, RAM/VRAM и аппаратного ускорения Windows Copilot+.
2. **[`discovery.py`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/src/ai/orchestration/discovery.py)**: Сканирование локальных демонов (Foundry Local на `54837`, Ollama на `11434`), компонентов Windows AI и ключей доступа.
3. **[`capability_registry.py`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/src/ai/orchestration/capability_registry.py)**: Стандартизация возможностей моделей (`chat`, `vision`, `ocr`, `embedding`, `code`, `image_generation`).
4. **[`model_error_hub.py`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/src/ai/orchestration/model_error_hub.py)**: Централизованный хаб классификации (`SERVICE_UNAVAILABLE`, `RATE_LIMIT`, `AUTH_ERROR`, `NOT_FOUND`, `CONTEXT_OVERFLOW`, `SAFETY_BLOCK`, `CONNECTION_ERROR`), регистрации инцидентов, расчета здоровья моделей и оповещения слушателей.
5. **[`model_pool_state.py`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/src/ai/orchestration/model_pool_state.py)**: Реестр состояния пулов моделей, отслеживание 503/429 и автоматический failover.
6. **[`policy.py`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/src/ai/orchestration/policy.py)**: Применение политик приватности (`strict` vs `standard`) и локализации исполнения (`local_only`, `prefer_local`, `cloud_only`).
7. **[`router.py`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/src/ai/orchestration/router.py)**: Разрешение запросов `AIRequest` на доступные исполнительные бэкенды.
8. **[`unified_chat.py`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/src/ai/orchestration/unified_chat.py)**: Высокоуровневый фасад чата для маршрутизаторов FastAPI и CLI-агентов.

---

## Пример использования централизованного хаба ошибок
```python
from src.ai.orchestration import (
    record_model_error,
    get_model_errors,
    get_model_health_summary,
    ModelErrorCategory,
)

# Фиксация сбоя
event = record_model_error(
    provider="gemini",
    model_name="gemini-3.1-flash-lite-preview",
    error="503 UNAVAILABLE: High demand",
    status_code=503,
    attempt=1,
    max_attempts=5,
    action_taken="retry",
    retry_delay_seconds=2.0,
)

# Запрос недавних ошибок и сводки
errors = get_model_errors(provider="gemini", limit=10)
health = get_model_health_summary()
```
