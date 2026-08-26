# Google Gemini интеграция

## API ключи

### Получение ключа

1. Перейдите в [Google AI Studio](https://aistudio.google.com/)
2. Создайте API ключ
3. Сохраните ключ в `.env` файл

### Настройка

```env
GEMINI_API_KEY_NAMES=key1,key2
```

## Использование

### 1. Chat API

```python
from core.ai import GoogleGenerativeAI

model = GoogleGenerativeAI(
    api_key_names=["key1"],
    system_instruction="You are a helpful assistant."
)

response = await model.chat("Какой фильм посмотреть?")
```

### 2. Embeddings

```python
embedding = model.get_embeddings("текст")
```

### 3. RAG

```python
from plugins.media_organizer.media_rag import get_media_rag

rag = get_media_rag(api_key="key1")
results = rag.search("фильм про войну", top_k=5)
```

## Конфигурация

### generation_config

```python
model.generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 2048,
}
```

### safety_settings

```python
model.safety_settings = {
    "HARM_CATEGORY_HATE_SPEECH": "BLOCK_MEDIUM_AND_ABOVE",
    "HARM_CATEGORY_HARASSMENT": "BLOCK_MEDIUM_AND_ABOVE"
}
```

---

[← MCP](mcp.md) | [Telegram Mini App →](tgmini.md)