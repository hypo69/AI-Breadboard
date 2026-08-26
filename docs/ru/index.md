# 🧭 AI Breadboard — Русскоязычная документация проекта прототипирования моделей

> **Интерактивный стенд и «макетная плата» для исследования, тестирования, сравнения и калибровки языковых моделей искусственного интеллекта.**

---

## 💡 О проекте

**AI Breadboard** переносит концепцию радиоэлектронной макетной платы в программную инженерию искусственного интеллекта. Модели ИИ выступают в роли сменных микросхем, сигнальная шина `UnifiedChatModel` обеспечивает мгновенную коммутацию, а контрольные точки (RAG-индекс, логи, SSE-потоки) дают полную наблюдаемость за всеми этапами работы нейросетей.

```mermaid
graph LR
    User["Пользователь / Приложение"] --> Router["Шина маршрутизации (UnifiedChatModel)"]
    
    subgraph "Сменные чипы (Модели)"
        Router <--> Gemini["Google Gemini SDK / CLI"]
        Router <--> Foundry["Microsoft AI Foundry"]
        Router <--> ONNX["ONNX DirectML / CPU / CUDA"]
        Router <--> HF["Hugging Face Transformers"]
        Router <--> AGY["Antigravity AGY"]
        Router <--> Ollama["Ollama Local"]
        Router <--> OpenAI["OpenAI / DeepSeek"]
    end
    
    subgraph "Модули памяти и инструментов"
        Router <--> RAG["Векторная память (FAISS + SQLite)"]
        Router <--> MCP["Шина инструментов (FastMCP)"]
        Router <--> Skills["Реестр навыков (SkillRegistry)"]
    end
```

---

## 📚 Разделы русскоязычной документации

### 1. 📘 [Учебная книга по архитектуре и прототипированию моделей](book/index.md)
Фундаментальное практическое руководство из 8 глав по работе со стендом:
- **[Глава 1. Архитектура макетной платы и среда](book/ch01_philosophy.md)** — Философия стенда, шины сигналов, сокеты в `config.json`, изоляция секретов `.env`.
- **[Глава 2. Оркестратор моделей и отказоустойчивость](book/ch02_orchestration.md)** — `model_manager.py`, `unified_chat.py`, балансировка квот, circuit breaker.
- **[Глава 3. Локальный инференс (HF и DirectML)](book/ch03_local_inference.md)** — Запуск моделей в памяти процесса, квантование, аппаратное ускорение DirectML на любых GPU.
- **[Глава 4. Архитектура RAG и векторный поиск](book/ch04_rag_architecture.md)** — Модули оперативной памяти, косинусная близость, индекс FAISS, гибридный поиск.
- **[Глава 5. Оптимизация, экспорт и Fine-Tuning](book/ch05_optimization_finetuning.md)** — Оптимизатор Microsoft Olive, экспорт GGUF -> ONNX, дообучение LoRA/QLoRA.
- **[Глава 6. ReAct-агенты, MCP и мультимодальность](book/ch06_agents_and_mcp.md)** — Цикл Thought-Action-Observation, FastMCP-серверы, голосовой конвейер.
- **[Глава 7. Создание и управление навыками (Skills)](book/ch07_skills_management.md)** — Манифесты `SKILL.md`, фабрика навыков `skill-factory`.
- **[Глава 8. Практикум: 10 лабораторных работ](book/ch08_laboratory_practicum.md)** — Пошаговые лабораторные работы для закрепления навыков.

---

### 2. ⚙️ [Техническая документация модулей и исходного кода](code/index.md)
Подробное описание архитектуры, API и исходного кода всех подсистем проекта:
- 🤖 **[Ядро системы (`core/`)](code/core/README.md)**:
  - [`core.ai`](code/core/ai/README.md) — Мультимодельный оркестратор, адаптеры провайдеров.
  - [`core.ai.gemini`](code/core/ai/gemini/README.MD) — Google Gemini SDK, ротация ключей, отказоустойчивость.
  - [`core.rag`](code/core/rag/README.md) — Подсистема RAG-First, `RAGEngine`, `RulesRAG`, `UserRAG`.
  - [`core.fastapi`](code/core/fastapi/README.md) — API-роутеры, WebSocket и SSE стриминг.
  - [`core.secrets`](code/core/secrets/README.md) — Менеджер API-ключей и отслеживание квот.
  - [`core.skills`](code/core/skills/README.md) — Универсальный реестр навыков.
  - [`core.tts`](code/core/tts/README.md) — Движки синтеза речи (Edge-TTS, gTTS, Silero).
  - [`core.logger`](code/core/logger/README.MD) — Подсистема структурированного логирования.
  - [`core.clients`](code/core/clients/README.md) — Клиенты внешних сервисов (Foundry, Ollama).
  - [`core.user_manager`](code/core/user_manager/README.md) — Профили пользователей и сессии.
  - [`core.utils`](code/core/utils/README.md) — Утилиты и конверторы данных.
- 🖥️ **[Веб-интерфейс (`webinterface/`)](code/webinterface/README.md)**:
  - [Чат с ИИ](code/webinterface/chat/README.md), [Панель моделей](code/webinterface/models_tab/README.md), [ReAct-агенты](code/webinterface/agents_tab/README.md), [RAG-поиск](code/webinterface/search_tab/README.md), [Плеер](code/webinterface/cosmicplayer/README.md), [Пульт ДУ](code/webinterface/rc/README.md), [Админка](code/webinterface/admin/README.md).
- 🔌 **[Серверы Model Context Protocol (`.mcp/`)](code/.mcp/README.md)**:
  - FastMCP серверы для внешних агентов (Claude Desktop, Cursor, Antigravity, VS Code).
- 🧠 **[Инструкции и промпты ИИ (`.ai/`)](code/.ai/instructions/README.md)**:
  - Единый центр инструкций, правила `CODE_RULES.md`, база знаний `codex/` и системные промпты `prompts/`.
- 🛠️ **[Инструменты разработчика и тесты (`scripts/`, `tests/`)](code/scripts/README.md)**:
  - Скрипты разработки (`scripts/dev/`), сопровождения (`scripts/maintenance/`), автоматические тесты (`tests/`).
- 📦 **[Установка и окружение (`install/`, `req/`)](code/install/README.md)**:
  - Модульный установщик, генерация SSL-сертификатов, профили зависимостей Python.

---

## ⚡ Быстрый старт со стендом

### Запуск через PowerShell-лончер (Windows):
```powershell
./run.ps1
```
Лончер автоматически:
1. Проверяет и освобождает рабочий порт (`3000`).
2. При необходимости запускает демон Microsoft AI Foundry.
3. Стартует FastAPI сервер с поддержкой SSL и автоперезагрузкой.

### Доступ к интерфейсам:
- 🏠 **Основной дашборд:** `http://localhost:3000/`
- 📄 **Интерактивная документация Swagger:** `http://localhost:3000/docs`
- 📱 **Мобильный пользовательский портал:** `http://localhost:3000/user`
- 🛠️ **Панель администратора:** `http://localhost:3000/admin`
