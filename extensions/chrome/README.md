# AI-Breadboard Chrome Extension

A Google Chrome / Chromium extension (Manifest V3) that connects your browser with your AI-Breadboard workspace and AI Assistant.

## Features

- **Context Menu (Right Click / ПКМ):**
  - **"Сохранить страницу" (Save page):** Extracts the readable contents, metadata, or selected text of the active tab and saves it into your personal workspace directory (`/api/user/files/upload`).
  - **"Проанализировать страницу в чате" (Analyze page in chat):** Opens the AI-Breadboard chat interface, pre-fills the page context, and sends a summary prompt (`"Дай краткое содержание"` / localized).
- **Multilingual Support:**
  - Automatic detection based on browser language (`ru`, `en`, `he`).
  - Configurable prompt templates in the extension options.
- **Server Health Check & Quick Popup:**
  - Displays connection status to your local or remote AI-Breadboard server (`http://localhost:8000`).

## Installation

1. Open Google Chrome, Edge, Brave, or any Chromium-based browser.
2. Navigate to `chrome://extensions/` (or `edge://extensions/`).
3. Enable **Developer mode** in the top-right corner.
4. Click **Load unpacked** (Загрузить распакованное расширение).
5. Select this folder: `AI-Breadboard/extensions/chrome`.

## Configuration

1. Click the AI-Breadboard icon in the browser toolbar.
2. Click **⚙️ Settings** (or right click the extension icon and choose *Options*).
3. Set your **Server URL** (default is `http://localhost:8000`).
4. Select your preferred **Prompt Language** or write a custom summary prompt template.
5. Click **Save Settings**.
