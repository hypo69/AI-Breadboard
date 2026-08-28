# Modular Dependencies (`req/`)

This directory contains modular Python dependency requirement files partitioned by subsystem for `ai-breadboard` / `AI Breadboard`.

---

## File Structure

- **`requirements-core.txt`** — Core web server (FastAPI, Uvicorn, Pydantic, Dotenv, JWT, aiohttp, httpx).
- **`requirements-ai.txt`** — AI stack and agent orchestration (LangChain, LangGraph, Google GenAI, FAISS, ChromaDB, Sentence-Transformers, MCP).
- **`requirements-media.txt`** — Multimedia processing, audio streaming, and voice synthesis (yt-dlp, Edge-TTS, gTTS, PyDub, SpeechRecognition, Playwright).
- **`requirements-utils.txt`** — Data processing, format conversion, and document parsing (Pandas, Pillow, BeautifulSoup4, ReportLab, FPDF2, PDFMiner, python-telegram-bot).
- **`requirements-test.txt`** — Automated testing framework (pytest, pytest-asyncio, pytest-cov, freezegun).
- **`requirements-docs.txt`** — Documentation generation stack (MkDocs, Material theme).

---

## Installation

Install all dependencies via root `requirements.txt`:
```bash
pip install -r requirements.txt
```

Or install specific profiles individually:
```bash
pip install -r req/requirements-core.txt
pip install -r req/requirements-ai.txt
```
