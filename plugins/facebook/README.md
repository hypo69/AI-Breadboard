# Facebook Publisher Plugin

**Plugin Name:** `facebook`  
**Title:** Facebook Publisher  
**Category:** `communication` / `social_media`  
**Author:** hypo69  
**Version:** 1.0.0  

---

## 📋 Overview

The **Facebook Publisher** plugin integrates the **Facebook Graph API** into AI Breadboard. It enables automated and AI-driven publishing of text updates, articles with link previews, and photos with captions directly to Facebook Pages or user feeds.

---

## ✨ Features

- **Multi-Type Publishing:** Supports standard text posts, links with rich previews, and image/photo uploads via URL or file upload.
- **LLM Function Calling Tools:** Exposes `post_to_facebook`, `get_facebook_page_info`, and `get_facebook_accounts` tools to AI models.
- **Admin UI Actions:** Directly test token validity, fetch page stats, and publish test posts from the AI Breadboard Admin interface.
- **Dynamic Configuration:** Supports settings via `config.json`, environment variables (`FACEBOOK_PAGE_ACCESS_TOKEN`, `FACEBOOK_PAGE_ID`), or web UI runtime updates.
- **Fail-Fast & Observability:** Detailed Facebook Graph API error extraction and structured logging via `src.logger.logger`.

---

## 🔑 Setup & Requirements

### 1. Required Permissions
To publish content to Facebook Pages, your Facebook Access Token requires the following permissions in the Meta Developer Console:
- `pages_manage_posts`
- `pages_read_engagement`
- `pages_show_list` (optional, for listing accounts)

### 2. Configuration Options

You can configure the plugin via environment variables in `.env` or in the web UI:

```env
FACEBOOK_PAGE_ACCESS_TOKEN=EAA...
FACEBOOK_PAGE_ID=123456789012345
```

Or via `config.json`:

```json
{
  "page_id": "123456789012345",
  "page_access_token": "EAA...",
  "user_access_token": "",
  "api_version": "v19.0",
  "default_target": "page"
}
```

---

## 🛠️ AI Function Tools

### `post_to_facebook`
Publish a post to Facebook.
- **Parameters:**
  - `message` (*string, required*): The text body of the post or photo caption.
  - `link` (*string, optional*): Web URL to attach as a rich preview card.
  - `photo_url` (*string, optional*): Public URL of an image to post.
  - `page_id` (*string, optional*): Override target Facebook Page ID.

### `get_facebook_page_info`
Retrieve metadata, follower counts, and status for a target page.
- **Parameters:**
  - `page_id` (*string, optional*): Page ID to query (defaults to configured page).

### `get_facebook_accounts`
List all Facebook pages accessible with the user access token.

---

## ⚙️ Admin Actions

| Action ID | Label | Description |
|---|---|---|
| `test_connection` | Test Connection | Validates token and verifies connectivity to the Graph API. |
| `publish_post` | Publish Post | Publishes a post with parameters `{message, link, photo_url, page_id}`. |
| `get_page_info` | Get Page Info | Retrieves metadata and follower counts for the target page. |

---

## 🧪 Usage Example

```python
from plugins.facebook import plugin

# Initialize plugin
fb = plugin(config={
    "page_id": "1234567890",
    "page_access_token": "YOUR_TOKEN_HERE"
})

# Test connection
result = await fb.execute_action("test_connection")
print(result)

# Publish a post
publish_result = await fb.execute_action("publish_post", {
    "message": "Hello from AI Breadboard!",
    "link": "https://github.com/hypo69/AI-Breadboard"
})
print(publish_result)
```
