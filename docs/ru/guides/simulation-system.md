# Руководство по системе имитации (Simulation System)

> **Цель:** Изучить архитектуру, принципы работы и интеграцию подсистемы генерации фиктивных данных (`src/ai/simulation/`) с клиентским RAG и дефолтной LLM-моделью платформы.

---

## 📋 Содержание

1. [Концепция и назначение](#концепция-и-назначение)
2. [Архитектура подсистемы](#архитектура-подсистемы)
3. [Ключевые компоненты](#ключевые-компоненты)
4. [Интеграция с Client RAG](#интеграция-с-client-rag)
5. [Обогащение через дефолтную LLM-модель](#обогащение-через-дефолтную-llm-модель)
6. [Создание собственного генератора](#создание-собственного-генератора)
7. [Примеры использования и программный API](#примеры-использования-и-программный-api)
8. [Тестирование и валидация](#тестирование-и-валидация)

---

## Концепция и назначение

В реальных бизнес-сценариях (тестирование клиентских чатов, демонстрации, обучение агентов, моделирование документооборота) возникает потребность в **генерации правдоподобных фиктивных ответов** на вопросы пользователей (например, *«Найди договор с Иваном Петровым»*, *«Покажи счет по аренде»*).

Главная проблема обычной генерации — **потеря контекста при повторных вопросах**. Если пользователь спустя время спросит: *«Какой номер договора был у Петрова?»* или *«Какая там сумма?»*, система без сквозной памяти может выдать противоречивые данные.

### Решение в AI Breadboard:
1. **Синтетический генератор** формирует детерминированные реквизиты (номера, суммы, даты, стороны).
2. **Дефолтная модель** (Gemini / Foundry / Ollama) обогащает ответ экспертными комментариями и советами для менеджера.
3. **Client RAG** немедленно индексирует сгенерированную пару (запрос + ответ) в изолированное векторное хранилище конкретного `user_id`.
4. **Повторные запросы** автоматически извлекают факты из клиентского RAG, обеспечивая 100% консистентность диалога.

---

## Архитектура подсистемы

```mermaid
flowchart TD
    subgraph 1. Первичный запрос
        Q1["Пользователь: 'Найди договор с Иваном Петровым'"]
    end

    subgraph 2. Модуль симуляции (src/ai/simulation)
        Engine["SimulationEngine"]
        Router["Выбор генератора (can_handle)"]
        ContractGen["ContractSimulationGenerator"]
        GenericGen["GenericSimulationGenerator"]
        Enricher["LLM Enricher (llm_enricher.py)"]
        LLM["Дефолтная модель (UnifiedChat / Gemini / Ollama)"]
    end

    subgraph 3. Хранилище Client RAG
        UserRAG[("Персональный RAG пользователя: user_rags/user_rag_<id>.db")]
    end

    Q1 --> Engine
    Engine --> Router
    Router -->|Договоры / Соглашения| ContractGen
    Router -->|Прочие сущности| GenericGen
    ContractGen -->|Каркас реквизитов| Enricher
    Enricher <-->|Обогащение и советы| LLM
    Enricher -->|Итоговый Markdown| Engine
    Engine -->|index_user_query| UserRAG
    Engine --> Resp1["Возврат фиктивного ответа пользователю"]

    subgraph 4. Повторные и уточняющие вопросы
        Q2["Пользователь: 'Какой номер договора у Петрова?'"]
        Q2 --> Search["search_user_history / search_user_context"]
        Search --> UserRAG
        UserRAG --> FoundDoc["Извлеченный контекст сгенерированного договора"]
        FoundDoc --> FinalAns["Консистентный ответ на базе RAG"]
    end
```

---

## Ключевые компоненты

Подсистема расположена в пакете [`src/ai/simulation/`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/src/ai/simulation/):

| Модуль | Описание |
|---|---|
| [`models.py`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/src/ai/simulation/models.py) | Pydantic и Dataclass модели: `SimulationRequest`, `SimulationResult`, `EntityType`. |
| [`base_generator.py`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/src/ai/simulation/base_generator.py) | Абстрактный интерфейс `BaseSimulationGenerator` (`entity_type`, `can_handle`, `generate`). |
| [`generators/contract_generator.py`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/src/ai/simulation/generators/contract_generator.py) | Генератор договоров: извлечение имени/контрагента, генерация номеров, сумм, дат и условий. |
| [`generators/generic_generator.py`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/src/ai/simulation/generators/generic_generator.py) | Универсальный генератор-fallback для любых кастомных сущностей. |
| [`llm_enricher.py`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/src/ai/simulation/llm_enricher.py) | Адаптер подключения дефолтных языковых моделей для обогащения ответов. |
| [`engine.py`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/src/ai/simulation/engine.py) | Главный координатор `SimulationEngine`: маршрутизация, вызов генераторов, LLM и сохранение в RAG. |

---

## Интеграция с Client RAG

Каждый сгенерированный документ автоматически сохраняется в изолированную клиентскую базу данных пользователя (`src/ai/gemini/user_query_rag.py` / `src/rag/user_rag.py`):

```python
# Автоматическая индексация в движке симуляции
await asyncio.to_thread(
    index_user_query,
    user_id=request.user_id,
    api_key=request.api_key,
    query=request.query,
    response=result.generated_text,
)
```

### Преимущества клиентской изоляции:
- Данные пользователя `user_1` никогда не пересекаются с `user_2`.
- Вся цепочка обсуждений и сгенерированных документов доступна для семантического поиска (`search_user_context`).
- При переполнении лимита старые записи автоматически ротируются (`_prune_if_needed`).

---

## Обогащение через дефолтную LLM-модель

Для придания ответам максимальной реалистичности к симуляции подключается дефолтная модель (`UnifiedChatModel`, `Gemini`, `Ollama`, `Foundry`):

### Алгоритм обогащения:
1. **Генератор** рассчитывает ключевые параметры (номер, дату, предмет, сумму, статус).
2. **Адаптер обогащения** (`llm_enricher.py`) передает структурированные данные в LLM со специальным системным промптом эксперта агентства.
3. **Модель** дополняет документ:
   - Краткой предысторией сделки.
   - Юридическими и коммерческими оговорками.
   - Блоком *«💡 Примечания и рекомендации для менеджера»*.
4. В случае недоступности LLM срабатывает **Graceful Fallback** — возвращается чистый базовый шаблон.

---

## Создание собственного генератора

Чтобы добавить новый тип сущности (например, **Счета на оплату / Invoices**), создайте класс, наследующий `BaseSimulationGenerator`:

```python
from src.ai.simulation import BaseSimulationGenerator, SimulationRequest, SimulationResult

class InvoiceSimulationGenerator(BaseSimulationGenerator):
    @property
    def entity_type(self) -> str:
        return "invoice"

    def can_handle(self, request: SimulationRequest) -> bool:
        query = request.query.lower()
        return any(kw in query for kw in ("счет", "invoice", "инвойс", "оплата"))

    async def generate(self, request: SimulationRequest) -> SimulationResult:
        inv_num = f"INV-2026/08-{request.user_id[:4]}"
        text = (
            f"### 💳 Счет на оплату № {inv_num}\n\n"
            f"- **Назначение:** Агентское вознаграждение за сопровождение сделки\n"
            f"- **Сумма к оплате:** 450 000 руб.\n"
            f"- **Срок оплаты:** до 25.09.2026\n"
            f"- **Статус:** Ожидает оплаты\n"
        )
        return SimulationResult(
            entity_type="invoice",
            title=f"Счет {inv_num}",
            generated_text=text,
            structured_data={"invoice_number": inv_num, "amount": 450000},
        )
```

### Регистрация в движке:
```python
from src.ai.simulation import get_simulation_engine

engine = get_simulation_engine()
engine.register_generator(InvoiceSimulationGenerator(), prepend=True)
```

---

## Примеры использования и программный API

### 1. Быстрый вызов симуляции с авто-индексацией:

```python
import asyncio
from src.ai.simulation import get_simulation_engine, SimulationRequest

async def run():
    engine = get_simulation_engine()
    
    # Запрос пользователя
    request = SimulationRequest(
        query="Найди договор аренды квартиры с Иваном Петровым",
        user_id="client_789",
        api_key="...",  # Gemini API key для векторизации в RAG
    )
    
    result = await engine.simulate(request, auto_index=True, enrich_with_llm=True)
    print("Результат:", result.generated_text)
    print("Сохранено в RAG:", result.is_indexed)

if __name__ == "__main__":
    asyncio.run(run())
```

### 2. Подключение дефолтной модели платформы:

```python
from src.ai.orchestration.unified_chat import UnifiedChatModel
from src.ai.simulation import get_simulation_engine

engine = get_simulation_engine()
# Подключаем активную модель приложения
engine.llm_model = default_chat_model
```

---

## Тестирование и валидация

Пакет полностью покрыт юнит-тестами в [`tests/test_simulation.py`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/tests/test_simulation.py).

Запуск тестов:
```powershell
pytest tests/test_simulation.py -v
```

Тестовый набор проверяет:
- Корректность извлечения имен и названий компаний (`extract_counterparty`).
- Детерминированность генерации номеров и сумм при одинаковом `user_id` и `counterparty`.
- Маршрутизацию и авто-индексацию в Client RAG.
- Обогащение через LLM и поведение при сбоях (Fallback).
