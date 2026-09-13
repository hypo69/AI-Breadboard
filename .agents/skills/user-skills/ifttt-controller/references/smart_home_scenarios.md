# Smart Home Scenarios & Implementation Guide

This reference documents the primary smart home architectures and scenarios using AI Breadboard and the IFTTT controller.

---

## 🏠 Scenarios

### 1. Context-Aware Ambiance & Comfort
- **Trigger:** Voice or Chat command (*"I'm starting a movie"*, *"I'm going to sleep"*, *"Deep focus time"*).
- **AI Processing:** Agent extracts intent, determines appropriate color temperature / brightness and climate settings.
- **Action:** Triggers IFTTT event `movie_mode` or `scene_relax` with `value1="living_room"`, `value2="warm_dim"`.

### 2. Intelligent Doorbell & Security Anomaly Detection
- **Trigger:** Inbound webhook from IFTTT Doorbell / Camera applet to `POST /api/ifttt/webhook/doorbell_pressed`.
- **AI Processing:** Assistant fetches camera snapshot, runs Vision LLM (e.g. Gemini 2.5 Flash / ONNX), determines whether it's a delivery driver, guest, or false trigger.
- **Action:** Dispatches descriptive alert to Telegram / Messenger and plays doorbell chime.

### 3. Voice & Chat Multi-Command Dispatcher
- **Trigger:** Multi-intent instruction (*"Turn off all kitchen lights, start the robot vacuum in the hallway, and cool bedroom to 21°C"*).
- **AI Processing:** LangChain ReAct agent decomposes the sentence into discrete tool calls:
  1. `ifttt_trigger_event(event_name="kitchen_lights_off")`
  2. `ifttt_trigger_event(event_name="vacuum_start", value1="hallway")`
  3. `ifttt_trigger_event(event_name="ac_set_temp", value1="bedroom", value2="21")`

### 4. Morning Routine & Household Sync
- **Trigger:** Alarm trigger or user prompt (*"Good morning"*).
- **AI Processing:** Fetches weather forecast, calendar events via Google Workspace skill, and personalized news digest via news-reader skill.
- **Action:** Starts smart kettle / coffee machine via IFTTT (`coffee_maker_on`) and synthesizes speech via Edge TTS / Silero.
