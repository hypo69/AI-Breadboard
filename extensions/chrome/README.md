# AI-Breadboard Chrome Extension

A Google Chrome / Chromium extension (Manifest V3) that connects your browser with your AI-Breadboard workspace and AI Assistant.

## Features

- **Popup Window Chat Integration:**
  - **"Проанализировать страницу в чате" (Analyze page in chat):** Opens the AI-Breadboard chat interface in a dedicated **popup window** on your configured server domain, automatically passing the page context and running a summary prompt (`"Дай краткое содержание"` / multilingual).
- **Workspace Page Archival:**
  - **"Сохранить страницу" (Save page):** Extracts readable page content/selection and saves it to your personal workspace directory via `/api/user/files/upload`.
- **Google OAuth Authentication:**
  - Sign in with Google directly from the extension popup window.
- **Zero-Hardcode Configuration:**
  - Dynamic loading from `config.json` (`serverUrl`, `userDomain`, `chatWindow` dimensions).
  - Configurable in the extension Options page.

## Installation

1. Open Google Chrome, Edge, Brave, or any Chromium-based browser.
2. Navigate to `chrome://extensions/`.
3. Enable **Developer mode** in the top-right corner.
4. Click **Load unpacked** (Загрузить распакованное расширение).
5. Select this folder: `AI-Breadboard/extensions/chrome`.

## Configuration

1. Click the AI-Breadboard icon in the browser toolbar.
2. Click **⚙️ Settings** (or right click the extension icon and choose *Options*).
3. The Server URL defaults to the configured value in `config.json` (e.g. `https://kino.davidka.net`).
4. Select your preferred **Prompt Language** or write a custom summary prompt template.
5. Click **Save Settings**.
