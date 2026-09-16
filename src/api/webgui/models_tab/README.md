# `webinterface/models_tab` — AI Model Switcher & Parameter Tuning

## Purpose
Primary dashboard tab for selecting active AI models, tuning hyperparameters (temperature, top_p, top_k, max tokens), and viewing API key health.

---

## Capabilities
- **Provider Switching**: Select among Google Gemini, Microsoft AI Foundry, ONNX DirectML, Hugging Face, AGY, and Ollama.
- **Parameter Sliders**: Real-time adjustment of sampling parameters.
- **Model Warm-Up & Health**: Trigger cache actualization and view response latencies.

---

## Files
- `index.html`: Model selection controls and parameter sliders.
- `main.js`: Communication with `/api/keys` and `/api/chat` model listing.
