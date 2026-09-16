# Wikipedia Research & Model Comparison Laboratory (`apps/wikipedia_research`)

**Статус:** ✅ Active  
**Языковой стандарт:** Русский (документация и комментарии) / PEP 8 (Python)  
**Автор:** hypo69  
**Пакет:** `apps.wikipedia_research`  
**API Префикс:** `/api/v1/wikipedia-research`  
**Порт по умолчанию (standalone):** `8110`

---

## 📋 Описание проекта

**Wikipedia Research & Model Laboratory** — это исследовательское микроприложение и демонстрационный бенчмарк-сценарий для платформы **AI-Breadboard**.

Приложение решает две фундаментальные задачи:
1. **Experiment A (Wikipedia Language Comparison)**: Сравнительный анализ того, как одна и та же тема (событие, концепт, исторический факт) освещается в разных языковых разделах Википедии (English, Русский, עברית, Deutsch, Français, Español, Українська, العربية и др.).
2. **Experiment B (Multi-Model AI Comparison)**: Сравнительный бенчмарк того, как различные AI-модели (`Gemini`, `Microsoft Foundry`, `Ollama`, `ONNX DirectML`, `OpenAI`) интерпретируют и оценивают один и тот же текст Википедии.

---

## 🏛️ Архитектура

```text
                    Wikipedia (MediaWiki API / REST)
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │    Wikipedia Collector    │
                    │   (Статьи, Языки, Views)  │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │      Text Normalizer      │
                    │ (Очистка HTML, Wikitext)  │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │ AI-BreadBoard ModelRouter │
                    └─────────────┬─────────────┘
                                  │
                ┌─────────────────┼─────────────────┐
                ▼                 ▼                 ▼
          Google Gemini   Microsoft Foundry    Ollama / ONNX
                │                 │                 │
                └─────────────────┼─────────────────┘
                                  ▼
                    ┌───────────────────────────┐
                    │   Multidimensional AI     │
                    │     Analysis Engine       │
                    │ (Sentiment, Framing, etc) │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │    Research Comparator    │
                    │ (Language A / Models B)   │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │ Statistics / Charts / TUI │
                    │      Reports / WebGUI     │
                    └───────────────────────────┘
```

---

## 🔍 Измерения и аспекты анализа

- **Sentiment (Тональность):** шкала от `-1.0` (резко негативная) до `+1.0` (позитивная).
- **Subjectivity (Субъективность):** от `0.0` (строго нейтральная фактология) до `1.0` (эмоционально-оценочная подача).
- **Criticism (Уровень критики):** удельный вес критических оценок и обвинений (`0.0` .. `1.0`).
- **Praise (Уровень похвалы):** удельный вес апологетических и одобрительных оценок (`0.0` .. `1.0`).
- **Uncertainty (Неопределенность):** частота использования слов вероятности и сомнения (`0.0` .. `1.0`).
- **Controversial Claims (Спорные утверждения):** фиксация и подсчет поляризующих тезисов.
- **Framing Tone (Фрейминг):** определение доминирующей смысловой рамки (`neutral_factual`, `critical`, `defensive`, `cautious`, `legalistic`).

---

## 🚀 Запуск и использование

### 1. Интерактивный терминальный режим (TUI)
```powershell
python -m apps.wikipedia_research
```

### 2. Запуск конкретного эксперимента через CLI
```powershell
# Эксперимент A (Сравнение языков)
python -m apps.wikipedia_research --mode experiment_a --topic "Israel–Gaza war" --languages en ru he de fr

# Эксперимент B (Сравнение моделей)
python -m apps.wikipedia_research --mode experiment_b --topic "Quantum computing" --models gemini foundry ollama --json
```

### 3. Запуск отдельного API сервера
```powershell
python -m apps.wikipedia_research --mode server --port 8110
```

---

## 🌐 FastAPI REST API

| Метод | Эндпоинт | Описание |
|---|---|---|
| `GET` | `/api/v1/wikipedia-research/health` | Проверка здоровья сервиса |
| `GET` | `/api/v1/wikipedia-research/languages` | Список поддерживаемых языковых разделов |
| `GET` | `/api/v1/wikipedia-research/models` | Доступные модели AI-Breadboard |
| `GET` | `/api/v1/wikipedia-research/search` | Поиск статей по теме |
| `POST` | `/api/v1/wikipedia-research/experiment/languages` | Запуск Эксперимента A (языки) |
| `POST` | `/api/v1/wikipedia-research/experiment/models` | Запуск Эксперимента B (модели) |
| `GET` | `/api/v1/wikipedia-research/history` | История проведенных экспериментов |
