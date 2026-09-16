# AI Responder for WordPress (davidka.net)

Automated, context-aware AI comment responder plugin for WordPress connected seamlessly to the central **AI-Breadboard** (`https://kino.davidka.net`).

---

## 🎯 Key Features

* 🤖 **Dedicated Bot User Support:** Automatically assigns generated replies to a dedicated WordPress user account (e.g., `AI Assistant` or `Davidka Bot`) with its custom avatar, display name, and bio.
* 🛡️ **Recursion & Loop Prevention:** Automatically ignores comments published by the bot user itself and skips already-processed comment threads.
* 🌐 **Centralized AI-Breadboard Gateway:** Dispatches requests directly to `https://kino.davidka.net/api/chat/comment-responder` (or local fallback), supporting seamless routing across Google Gemini, Microsoft Foundry Local, Ollama, ONNX, and OpenAI-compatible models.
* 🧠 **Deep Context Awareness:** Gathers the blog post title, full text/excerpt, and comment ancestor chain (parent comments) to produce coherent, relevant replies.
* ⏱️ **Asynchronous Non-Blocking Execution:** Uses WordPress background cron scheduling (`wp_schedule_single_event`) with configurable delay (e.g. 10-30s) so visitor page loading is never blocked by LLM response time.
* 🔍 **Admin Dashboard & Live Logs:** Includes interactive connectivity testing, model switching, moderation settings, and real-time log viewer.

---

## 🏗️ Architecture & Data Flow

```
[Visitor on davidka.net]
          │ (posts a comment)
          ▼
[WordPress Hook: comment_post]
          │
  (Validations: bot_user_id check, spam filter, min length, approval status)
          │
          ▼
[Scheduled Async Event (WP-Cron)]
          │ (POST JSON payload)
          ▼
[AI-Breadboard: https://kino.davidka.net/api/chat/comment-responder]
          │ (Multi-model routing, prompt instructions, RAG context)
          ▼
[WordPress: wp_insert_comment]
          │ (Inserts reply linked to parent comment with bot user_id)
          ▼
[Published Reply on davidka.net]
```

---

## ⚙️ Configuration Options

| Option | Description | Default |
|---|---|---|
| `enabled` | Enable or disable auto-replies | `true` |
| `api_url` | AI-Breadboard endpoint URL | `https://kino.davidka.net/api/chat/comment-responder` |
| `api_key` | Optional bearer token/secret | `""` |
| `model` | Target AI model identifier | `gemini-2.5-flash` |
| `provider` | AI provider (`gemini`, `foundry`, `ollama`, `openai`, etc.) | `gemini` |
| `bot_user_id` | Dedicated WordPress user ID for the AI bot | `0` |
| `auto_approve` | Automatically publish reply comments without moderation | `true` |
| `reply_delay` | Delay in seconds before triggering async reply generation | `10` |
| `min_comment_length` | Minimum characters in user comment to trigger reply | `5` |
| `max_thread_depth` | Maximum ancestor comments collected for context | `5` |
| `system_instruction` | Custom system prompt / persona for the AI assistant | Pre-configured English prompt |

---

## 📜 Setup Instructions

See [INSTALL.md](INSTALL.md) for detailed step-by-step setup and dedicated user configuration.
