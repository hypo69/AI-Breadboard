# 💬 UnifiedChatModel: Реализация чата

**Статус:** ✅ Reference  
**Версия:** 2.0  
**Последнее обновление:** сентябрь 2026

---

## 📋 Содержание
1. [Архитектура UnifiedChatModel](#1-архитектура-unifiedchatmodel)
2. [Переключение провайдеров](#2-переключение-провайдеров)
3. [RAG интеграция](#3-rag-интеграция)
4. [Потоковые ответы](#4-потоковые-ответы)

---

## 1. Архитектура UnifiedChatModel

### Обзор

`UnifiedChatModel` — это единый интерфейс ко всем AI провайдерам. Скрывает различия между API-шками разных провайдеров под одинаковым интерфейсом.

### Структура

```python
from src.ai import UnifiedChatModel

# Создание модели
model = UnifiedChatModel(
    provider='gemini',              # Выбор провайдера
    model_name='gemini-2.5-flash',  # Название модели
    temperature=0.7                 # Параметры модели
)

# Простой запрос
response = model.chat('Hello, world!')
print(response)

# С параметрами
response = model.chat(
    message='Tell me a story',
    max_tokens=500,
    system_instruction='You are a storyteller'
)
```

### Поддерживаемые параметры

| Параметр | Тип | Значение по умолчанию | Описание |
|----------|-----|----------------------|---------|
| `provider` | str | 'gemini' | Провайдер: gemini, foundry, ollama, openai, и т.д. |
| `model_name` | str | 'gemini-2.5-flash' | Название модели |
| `temperature` | float | 0.7 | Креативность ответа (0-1) |
| `max_tokens` | int | 2000 | Максимальное количество токенов |
| `top_p` | float | 0.95 | Nucleus sampling parameter |
| `system_instruction` | str | '' | Системный prompt |

---

## 2. Переключение провайдеров

### Автоматическое переключение

```python
from src.ai import UnifiedChatModel

# Попытаться использовать Gemini, если не доступен - fallback на Ollama
model = UnifiedChatModel(
    provider='gemini',
    fallback_provider='ollama'
)

response = model.chat('Hello')
```

### Явное переключение

```python
model = UnifiedChatModel(provider='gemini')

# Переключиться на другого провайдера
model.switch_provider('foundry')

# Или создать новый экземпляр
model_ollama = UnifiedChatModel(provider='ollama')
```

### Динамический выбор

```python
# Выбирать провайдера в зависимости от условий
def choose_provider(task_type: str) -> str:
    if task_type == 'vision':
        return 'gemini'  # Gemini поддерживает vision
    elif task_type == 'local':
        return 'ollama'  # Локальный провайдер
    else:
        return 'openai'  # Fallback

provider = choose_provider('vision')
model = UnifiedChatModel(provider=provider)
```

---

## 3. RAG интеграция

### С RAG контекстом

```python
from src.ai import UnifiedChatModel
from src.rag import RAGRetriever

# Инициализировать RAG
rag = RAGRetriever()

# Создать модель с RAG
model = UnifiedChatModel(provider='gemini')

# Получить контекст из RAG
context = rag.search('Как установить систему?', limit=3)

# Добавить контекст в запрос
message = f"""
Контекст из базы знаний:
{context}

Вопрос: Как установить систему?
"""

response = model.chat(message)
```

### RAG в system instruction

```python
context = rag.search(query)

model = UnifiedChatModel(
    provider='gemini',
    system_instruction=f"""
    Ты помощник. Используй следующий контекст для ответов:
    
    {context}
    """
)

response = model.chat('Мой вопрос')
```

---

## 4. Потоковые ответы

### Server-Sent Events (SSE)

```python
from src.ai import UnifiedChatModel

model = UnifiedChatModel(provider='gemini')

# Потоковый ответ
for chunk in model.stream_chat('Tell me a long story'):
    print(chunk, end='', flush=True)
```

### WebSocket Stream

```python
# В FastAPI роутере
from fastapi import WebSocket

@router.websocket("/api/chat/ws")
async def websocket_chat_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    model = UnifiedChatModel(provider='gemini')
    
    while True:
        message = await websocket.receive_text()
        
        # Потоковый ответ
        for chunk in model.stream_chat(message):
            await websocket.send_text(chunk)
```

### Асинхронный потоковый ответ

```python
import asyncio
from src.ai import UnifiedChatModel

model = UnifiedChatModel(provider='gemini')

async def stream_response(message: str):
    """Асинхронный потоковый ответ."""
    async for chunk in model.async_stream_chat(message):
        print(chunk, end='', flush=True)
        await asyncio.sleep(0.01)  # Небольшая задержка

await stream_response('Hello, world!')
```

---

## 📚 Смотрите также

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — Общая архитектура
- [`standards/ENGINEERING.md`](../standards/ENGINEERING.md) — Стандарты разработки
- `src/ai/unified_chat_model.py` — Исходный код

**Последнее обновление:** сентябрь 2026
