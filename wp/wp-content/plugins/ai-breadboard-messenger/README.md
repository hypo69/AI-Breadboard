# AI Breadboard Messenger WordPress Plugin

The `ai-breadboard-messenger` plugin bridges your WordPress site with the AI Breadboard Real-Time Messenger and WebRTC Meeting Room backend.

---

## 🚀 Installation & Setup

1. The plugin is located in `wp-content/plugins/ai-breadboard-messenger`.
2. Go to **WordPress Admin > Plugins** and click **Activate**.
3. Navigate to **AI Messenger** in the WordPress admin menu:
   - Enter your **Backend Server URL** (e.g. `http://localhost:8000` or `https://your-domain.com`).
   - Enter your **Sync Secret Key** (matching `MESSENGER_SYNC_SECRET` on the backend).
   - Click **Save Changes**.

---

## 💡 Features

- **Automatic User Sync:** WordPress users, avatars, and display names are automatically mirrored to the Messenger backend on login, registration, and profile edits.
- **Single Sign-On (SSO):** Logged-in WordPress users are securely auto-authenticated via signed HMAC/JWT tokens without requiring separate logins.
- **Floating Messenger Widget:** Public or member-only floating chat bubble automatically rendered on your WordPress site.
- **Embeddable Shortcode:** Embed full-screen or embedded messenger rooms on any page or post using:
  ```
  [breadboard_messenger]
  ```
- **WebRTC Conferencing:** Direct support for audio/video meeting rooms with screen sharing inside the WordPress portal.
