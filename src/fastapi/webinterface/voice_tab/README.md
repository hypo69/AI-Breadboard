# Voice Tab Web Interface

## Overview
Provides a dedicated web interface for microphone audio recording, audio file ingestion, Google Gemini multimodal speech processing, speaker diarization, executive meeting summaries, and one-click saving to the RAG knowledge base.

## Features
- **Live Microphone Recording**: Uses HTML5 `MediaRecorder` with visual waveform indicator, real-time timer, and cancel/stop controls.
- **Audio File Upload**: Supports Drag & Drop and file picker for `.mp3`, `.wav`, `.ogg`, `.m4a`, `.webm`, `.aac`.
- **Gemini Multimodal Analysis**: Turn-by-turn transcription with speaker separation (`Собеседник 1`, `Собеседник 2`), timestamps, key discussion points, and action items.
- **RAG Integration**: Direct export to `data/rag_documents/` with automatic re-indexing.
