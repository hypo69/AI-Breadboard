# 🧠 Модуль `core.rag` — Универсальная подсистема RAG

## 📋 Описание
Модуль `core.rag` реализует чистую, доменно-независимую архитектуру **«RAG-First»** для обработки запросов пользователя.

---

## 🔄 Пайплайн обработки запросов (RAG-First)

```
Запрос пользователя ──► RAGEngine.evaluate() ──► Поиск по базе знаний (RAG)
                                │
       ┌────────────────────────┴────────────────────────┐
       ▼                                                 ▼
[Найден точный ответ (Score >= threshold)]    [Нет прямого ответа]
       │                                                 │
       ▼                                                 ▼
Прямой возврат ответа (Direct RAG)            Вызов LLM (с RAG-контекстом)
(Мгновенный ответ без вызова модели)                     │
                                                         ▼
                                              Автосохранение нового ответа в RAG
```

---

## 📂 Структура модуля

| Файл | Назначение |
|---|---|
| `__init__.py` | Публичный интерфейс подсистемы, синглтон `get_rag_engine()`. |
| `models.py` | Датаклассы и перечисления (`RAGDecisionType`, `RAGRouteDecision`, `RAGSearchResult`). |
| `engine.py` | Класс `RAGEngine`: координация поиска по базе знаний, проверка порога уверенности и подготовка RAG-контекста. |
| `rules_rag.py` | Семантический поиск по модульным промптам (`prompts/`) для динамической сборки системных промптов LLM. |
| `user_rag.py` | Семантический поиск по сохраненным ответам и профилю предпочтений пользователя. |

---

## ⚙️ Использование в коде

### 1. Оценка и маршрутизация запроса через `RAGEngine`:
```python
from core.rag import get_rag_engine

engine = get_rag_engine()
decision = await engine.evaluate(
    query="Как настроить проект?",
    user_identifier="user_123",
    api_key=api_key
)

if decision.is_direct:
    # Мгновенный возврат найденного ответа клиенту
    print(decision.direct_text)
else:
    # Запрос к LLM с инжектированным контекстом decision.context_text
    pass
```

### 2. Динамическая сборка системного промпта через `RulesRAG`:
```python
from core.rag import RulesRAG

rules_rag = RulesRAG()
relevant_rules = rules_rag.search("правила для диктора", top_k=3)
```
