# `core.tts` Module — Text-to-Speech (TTS) Engines

## Purpose
The `core.tts` package provides a standardized, multi-engine interface for synthesized speech generation and streaming audio playback.

---

## Supported Engines

| File | Engine | Characteristics |
|---|---|---|
| `edge.py` | Microsoft Edge TTS | High-quality cloud neural speech synthesis with multi-language and voice pitch/rate tuning. |
| `gtts.py` | Google Translate TTS | Lightweight cloud fallback engine. |
| `silero.py` | Silero TTS | Local neural TTS model for completely offline, low-latency synthesis. |

---

## Integration Scheme

```python
from core.tts.edge import EdgeTTS

tts = EdgeTTS()
audio_bytes = await tts.synthesize(text="Playback starting now.", voice="en-US-GuyNeural")
```
