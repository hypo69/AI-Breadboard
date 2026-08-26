# Модульные зависимости проекта ai-assistant

В этой директории содержатся разбитые по функциональным модулям списки зависимостей Python для проекта ai-assistant.

## Структура файлов

- `requirements-core.txt` — ядро веб-сервера (FastAPI, Uvicorn, Pydantic, Dotenv, JWT, HTTP-клиенты).
- `requirements-ai.txt` — стек искусственного интеллекта и агентов (LangChain, LangGraph, Google GenAI, FAISS, ChromaDB, Sentence-Transformers, MCP).
- `requirements-media.txt` — работа с мультимедиа, видео, речью и парсингом (yt-dlp, Edge-TTS, gTTS, PyDub, SpeechRecognition, Playwright).
- `requirements-utils.txt` — утилиты для обработки данных, конвертации форматов и документов (Pandas, Pillow, BeautifulSoup4, ReportLab, FPDF2, PDFMiner, Telegram Bot).
- `requirements-test.txt` — зависимости для запуска автоматических тестов (pytest, pytest-asyncio, pytest-cov, freezegun).
- `requirements-docs.txt` — зависимости для генерации документации MkDocs.

## Установка

Все зависимости подключаются в корневой файл `requirements.txt`:
```bash
pip install -r requirements.txt
```

Или по отдельности для конкретных модулей:
```bash
pip install -r req/requirements-core.txt
pip install -r req/requirements-ai.txt
```
