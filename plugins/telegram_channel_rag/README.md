# Telegram Channel RAG & Fast Search Plugin (`telegram_channel_rag`)

## Description
Modular AI Breadboard plugin that collects messages from a Telegram group/channel (e.g. `canozrimb` / `https://t.me/canozrimb`), builds a vector and semantic TF-IDF RAG index, and performs fast relevance search returning exact permalinks (`https://t.me/canozrimb/<message_id>`) for direct viewing.

---

## Features
- **Public Channel Web Preview Ingestion**: Fetches message history directly from public Telegram channel previews (`https://t.me/s/canozrimb`) without requiring API keys.
- **Offline JSON Export Parser**: Reads Telegram Desktop `result.json` export files for instant private or public group indexing.
- **Direct Message Permalinks**: Every search result includes `url` pointing directly to the specific Telegram message.
- **Multilingual Tokenizer**: Supports Russian, English, punctuation, and code tokens.
- **LLM Function Calling**: Exposes `search_telegram_channel` tool to AI models.
- **Web UI Admin Actions**: Trigger indexing, status inspection, and interactive search queries.

---

## Configuration (`config.json`)
```json
{
  "target_channel": "canozrimb",
  "max_messages": 5000,
  "index_name": "canozrimb",
  "storage_dir": "data/telegram_rag",
  "similarity_top_k": 5
}
```

---

## Admin Actions
| Action ID | Name | Description |
|-----------|------|-------------|
| `fetch_and_index` | Fetch & Rebuild RAG Index | Scrapes channel preview and indexes messages |
| `import_export_file` | Import Exported JSON | Indexes a local `result.json` Telegram export |
| `search` | Search Channel Messages | Performs instant semantic retrieval |
| `get_index_status` | Get Index Status | Reports message count, vocabulary size, and storage path |

---

## Author
hypo69 © 2026
