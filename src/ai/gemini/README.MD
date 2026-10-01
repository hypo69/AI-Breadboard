# 🧠 Интеграция с Google Gemini AI (`src.ai.gemini`)

## 📋 Обзор модуля
Модуль `src.ai.gemini` предоставляет высокоуровневый клиент (`GoogleGenerativeAI`) корпоративного класса для взаимодействия с моделями Google Gemini через официальный `google-genai` SDK.

Модуль реализует отказоустойчивость: автоматическую ротацию пула API-ключей, 24-часовой карантин при исчерпании квот (HTTP 429), динамическое переключение моделей при сбоях (HTTP 404, HTTP 503), гибкое управление инструментами (Tools, Google Search Grounding) и поддержку как ручного агентного цикла, так и нативного механизма Automatic Function Calling (AFC).

---

## 🚀 Ключевые возможности

1. **Управление пулом API-ключей:**
   - Ротация ключей на основе времени последнего использования (`update_last_run`).
   - Автоматическая 24-часовая блокировка ключей с исчерпанным лимитом (`mark_exhausted`).
   - Исключение невалидных и аннулированных ключей (HTTP 401).

2. **Отказоустойчивость и ротация моделей:**
   - Автоматическое переключение на поддерживаемую модель при ошибках 404 (`_switch_model`).
   - Экспоненциальная задержка и автоматическое понижение нагрузки (Downgrade) при недоступности серверов (HTTP 503).
   - Опциональное ожидание сброса квоты (`sleep_on_exhausted`).

3. **Генерация и потоковая передача (Streaming):**
   - Одиночные текстовые запросы без сохранения контекста (`ask`).
   - Полноценные диалоговые сессии с сохранением контекста (`chat`).
   - Асинхронная потоковая генерация токенов в реальном времени (`chat_stream`).
   - Мультимодальные запросы (`describe_image`) и загрузка медиафайлов (`upload_file`).
   - Векторные эмбеддинги текста (`embed`).

4. **Работа с инструментами и вызов функций (Function Calling):**
   - **Google Search Grounding:** подключение актуального поиска Google через параметр `use_google_search=True`.
   - **Ручной агентный цикл (Manual Dispatcher):** выполнение многошаговых сценариев с локальным диспетчером через [`ask_with_tools`](api.py) и [`ask_with_tools_stream`](api.py).
   - **Automatic Function Calling (AFC):** поддержка нативного исполнения Python-функций силами SDK через параметр `automatic_function_calling` в `generation_config`. По умолчанию AFC в прямых запросах отключен (`disable=True`) для предотвращения конфликтов и лишних предупреждений SDK.

---

## 🛠️ Примеры использования

### 1. Одиночный запрос (Stateless)
```python
import asyncio
from src.ai.gemini import GoogleGenerativeAI

async def main():
    ai = GoogleGenerativeAI(system_instruction="Ты старший инженер-исследователь.")
    answer = await ai.ask("Объясни назначение подтягивающего резистора.")
    print(answer)

asyncio.run(main())
```

### 2. Сессия диалога с сохранением контекста
```python
async def chat_session():
    ai = GoogleGenerativeAI(save_history_chat=True)
    r1 = await ai.chat("Посоветуй 3 книги по системной архитектуре.")
    print("AI:", r1)
    r2 = await ai.chat("Какая из них наиболее практическая?")
    print("AI:", r2)
```

### 3. Потоковая генерация токенов (Realtime Streaming)
```python
async def stream_output():
    ai = GoogleGenerativeAI()
    async for chunk in ai.chat_stream("Кратко опиши историю создания микропроцессоров:"):
        print(chunk, end="", flush=True)
```

### 4. Автоматический вызов функций (Automatic Function Calling / AFC)
```python
def get_device_status(device_id: str) -> str:
    """Возвращает текущий статус устройства по его идентификатору.
    
    Args:
        device_id: Идентификатор устройства (например, 'sensor_1').
    """
    return f"Устройство {device_id} активно, температура: 42°C"

async def afc_example():
    ai = GoogleGenerativeAI()
    response = await ai.ask(
        q="Проверь статус датчика sensor_1",
        generation_config={
            "tools": [get_device_status],
            "automatic_function_calling": {
                "disable": False,
                "maximum_remote_calls": 5,
            },
        },
    )
    print(response)
```

---

## 📁 Структура файлов пакета

- `core.py` — Базовый клиент (`GoogleGenerativeAICore`), управление ключами, клиентом `genai.Client` и ротацией моделей.
- `config.py` — Миксин конфигурации (`GoogleGenerativeAIConfigMixin`), построение `GenerateContentConfig`, нормализация текста и параметры AFC.
- `api.py` — Главный агрегирующий класс `GoogleGenerativeAI`, объединяющий методы `ask`, `chat`, `chat_stream`, `ask_with_tools`.
- `api_single.py` — Методы одиночных текстовых запросов (`ask`).
- `api_chat.py` — Методы диалогового чата и стриминга (`chat`, `chat_stream`).
- `history.py` — Управление историей диалогов и восстановление сессий.
- `images.py` — Мультимодальные запросы и обработка изображений.
- `embeddings.py` — Генерация векторных представлений текста.
- `errors.py` — Обработка сетевых ошибок, квот и переключения ключей/моделей.
