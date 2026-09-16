# `webinterface/remote_mic` — Voice & Media Remote Control Interface

## Purpose
Mobile-optimized voice and media remote control interface designed for hands-free voice interaction, direct audio recording transcription, and multimodal media uploads to the AI assistant from smartphones and tablets.

---

## Features
- **Large Central Microphone Button:** Touch-optimized, animated pulse/ripple recording trigger with Telegram WebApp haptic feedback.
- **Audio & Media Upload Actions:**
  - Dedicated **Audio File Upload** button with native mobile picker for `.mp3`, `.wav`, `.m4a`, `.ogg`, `.flac`, `.webm` voice notes and recordings.
  - Automatic invocation of `/api/audio/diarize` for speaker diarization, executive summaries, key thesis extraction, and action items.
  - Dedicated **Media & File Attachment** button for photos, video clips, and documents with preview rendering.
- **Speech-to-Text Recognition:** Multi-language support (RU, EN, HE) with Web Speech API.
- **AI Streaming Integration:** Streams conversational responses directly from `/api/chat`.
- **Text-to-Speech (TTS) Voiceover:** Real-time audio playback using backend `/api/tts/synthesize` or browser SpeechSynthesis.
- **Telegram WebApp & Standalone PWA:** Fully responsive mobile layout with automatic dark/light theme switching and authentication integration.

---

## Files
- `index.html`: Standalone single-page voice and media remote application.
- `README.md`: Component documentation.
