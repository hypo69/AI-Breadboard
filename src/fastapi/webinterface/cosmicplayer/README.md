# `webinterface/cosmicplayer` — Video Player Component

## Purpose
Modern HTML5 media player designed for streaming video files directly from local storage and media servers.

---

## Key Features
- Native H.264 / MP4 / WebM video streaming via HTTP range requests (`/api/media-admin/stream`).
- Automatic sequential playback for multi-episode series.
- Local storage persistence for playback position, volume, and subtitle preferences.
- WebSocket synchronization with the Remote Control (`webinterface/rc`) gateway.

---

## Files
- `index.html`: Player UI and control overlay.
- `main.js`: Video event handling, buffer management, and sync listener.
- `style.css`: Custom player controls and fullscreen styling.
