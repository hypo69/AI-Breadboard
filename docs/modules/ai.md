# AI модули

## Google Generative AI

### Класс GoogleGenerativeAI

```python
from core.ai import GoogleGenerativeAI

model = GoogleGenerativeAI(
    api_key_names=["key1", "key2"],
    system_instruction="You are a helpful assistant."
)
```

### Методы

#### chat()

```python
response = await model.chat(
    message="Какой фильм посмотреть?",
    chat_data_folder="",
    system_instruction=None
)
```

**Параметры:**
- `message` — сообщение пользователя
- `chat_data_folder` — папка с историей чата
- `system_instruction` — системная инструкция

**Возвращает:** `str` — ответ модели

#### chat_with_search()

```python
response = await model.chat_with_search(
    message="Найди фильмы про войну",
    top_k=5
)
```

### Конфигурация

```python
model.generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 2048,
}
```

## Embeddings

### Создание embeddings

```python
embedding = model.get_embeddings("текст для embeddings")
```

### Поиск по embeddings

```python
results = model.search_similar(
    query="фильм про войну",
    top_k=5
)
```

## RAG (Retrieval-Augmented Generation)

### Построение индекса

```python
from plugins.media_organizer.media_rag import build_media_rag

rag = build_media_rag(api_key="key_name")
```

### Поиск

```python
results = rag.search("фильм про войну", top_k=5)
```

### Методы RAG

| Метод | Описание |
|-------|----------|
| `add()` | Добавление документов |
| `search()` | Поиск по векторам |
| `count()` | Количество документов |
| `delete()` | Удаление документов |

---

[← Меню](../index.md) | [Plugins →](../dev/plugins.md)