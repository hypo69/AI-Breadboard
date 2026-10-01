# `webinterface/rc` — Remote Control Gateway Interface

## Purpose
Mobile-friendly remote control interface allowing secondary devices (smartphones, tablets) to control media playback on the main player screen via WebSockets.

---

## Features
- Play/Pause, seek forward/backward, and volume adjustment.
- Track selection and episode switching.
- Low-latency bidirectional WebSocket synchronization over `/ws/control`.

---

## Files
- `index.html`: Touch-optimized remote control keypad.
- `main.js`: WebSocket client sending real-time control events.
