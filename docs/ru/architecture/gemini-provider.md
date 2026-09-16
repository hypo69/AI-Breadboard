# Архитектура и интеграция Google Gemini

Документация по архитектуре интеграции с Google Generative AI (Gemini), механизмам мониторинга отправляемых запросов (payload), управлению веб-поиском и многоуровневой обработке лимитов (Rate Limits & Quota).

---

## 1. Обзор модуля `src.ai.gemini`

Интеграция с Google Gemini реализована на базе официального SDK `google-genai` (v1+) и разделена на модульные миксины:

- **`GoogleGenerativeAICore`** (`core.py`) — инициализация клиента `genai.Client`, пул API-ключей, управление состоянием и базовые параметры.
- **`GoogleGenerativeAIConfigMixin`** (`config.py`) — сборка `types.GenerateContentConfig`, форматирование инструкций (Chat / TTS), управление инструментами (tools) и логирование структуры payload.
- **`GoogleGenerativeAIHistoryMixin`** (`history.py`) — восстановление, подготовка и очистка истории сообщений диалога.
- **`GoogleGenerativeAIErrorMixin`** (`errors.py`) — централизованная обработка исключений API, классификация ошибок 401/404/429/503, ротация ключей и экспоненциальный backoff.
- **`GoogleGenerativeAI`** (`api.py`) — публичные методы `ask`, `chat`, `chat_stream`, `ask_with_tools`, `ask_with_tools_stream`.

---

## 2. Мониторинг и наблюдаемость исходящих запросов (Payload Tracking)

Для предотвращения скрытого переполнения контекста модели и точного отслеживания того, **что именно отправляется в API Gemini**, в `GoogleGenerativeAIConfigMixin._log_request_details` внедрено структурированное логирование.

### Состав логируемых параметров:
- **`method`** — вызываемый метод (`ask`, `chat`, `chat_stream`, `ask_with_tools`).
- **`model`** — используемый идентификатор модели Gemini.
- **`prompt_len` & `prompt preview`** — точный размер текста запроса пользователя в символах и превью начала текста.
- **`history_turns` & `history_chars`** — количество сообщений диалога в контексте и их суммарный размер в символах.
- **`sys_prompt_len` & `preview`** — размер и начало системной инструкции (включая служебные блоки форматирования `[CHAT]... [VOICE]...`).
- **`tools`** — список активных инструментов (например, `google_search`, `custom_functions` или `none`).
- **`gen_config`** — переопределенные параметры генерации (`temperature`, `top_p`, `top_k` и т.д.).

### Пример записи в системном логе:
```text
INFO - Gemini Outgoing [chat_stream] -> Model: "gemini-2.5-flash" | Prompt (45 chars): 'Какая погода сегодня?' | History: 4 msgs (~850 chars) | SysInstruction (320 chars): 'CRITICAL: You must format...' | Tools: none | GenConfig: {}
```

---

## 3. Конфигурация инструментов и веб-поиска (Grounding)

### Проблема Search Grounding по умолчанию:
Ранее инструмент `types.Tool(google_search=types.GoogleSearch())` автоматически добавлялся во все запросы. Это вызывало:
1. Предупреждение SDK: `Direct use of automatic function calling (AFC) in AsyncModels.generate_content_stream is not recommended`.
2. Ошибку `429 RESOURCE_EXHAUSTED` с `quota_limit_value: '0'` на бесплатных тарифах Google Cloud и в неподдерживаемых регионах, где квота на Google Search Grounding равна нулю.

### Решение: Опциональное включение (`use_google_search`):
- В `src/ai/gemini/config.py` инструмент поиска подключается **только при явном включении**:
  - Через параметр `use_google_search=True` в `generation_config`.
  - Либо через свойство `ai.use_google_search = True` на экземпляре клиента.
- Если инструменты не требуются, секция `tools` не передается в `GenerateContentConfig`, что исключает AFC и снижает задержку ответа.

---

## 4. Обработка квот и Rate Limits (Ошибка 429)

Google API возвращает код `429 RESOURCE_EXHAUSTED` в двух принципиально разных ситуациях:

| Тип ошибки | Сигнатура в ответе API | Поведение системы |
|---|---|---|
| **Минутный лимит (Rate Limit / Burst)** | `ApiRequestsPerMinute`, `1/min`, `RATE_LIMIT_EXCEEDED` | Экспоненциальная пауза (`min(base_wait * 2^attempt, 60)` секунд) и повтор запроса. **API-ключ НЕ блокируется**. |
| **Суточный лимит (Daily Quota)** | `RequestsPerDay`, `perday`, `daily_quota` | Ключ помечается как исчерпанный (`mark_exhausted`) на 24 часа. Система переключается на следующий ключ из пула (`_switch_api_key`). |

### Алгоритм в `_handle_api_error`:
```python
if '429' in ex_str or 'RESOURCE_EXHAUSTED' in ex_str:
    is_per_minute = any(k in ex_str.lower() for k in [
        '1/min', 'perminute', 'per_minute', 'requestsperminute',
        'apirequestsperminute', 'rate_limit_exceeded'
    ])
    is_daily = not is_per_minute and any(k in ex_str.lower() for k in [
        'perday', 'per_day', 'requestsperday', 'daily_quota'
    ])

    if is_daily:
        self._mark_key_exhausted(self.api_key)
        if self._switch_api_key():
            return True
        return self._switch_model()

    # Минутный лимит: задержка и повторная попытка без суточной блокировки ключа
    wait_time = min(base_wait * (2 ** min(attempt, 3)), 60)
    await asyncio.sleep(wait_time)
    return True
```

---

## 5. Пул ключей и ротация (`src.secrets.api_key_state`)

Ключи Gemini загружаются из `.env` и сохраняются в `src/secrets/gemini_keys.json`:
- Поддерживается настройка нескольких ключей (`GEMINI_API_KEY_1`, `GEMINI_API_KEY_2`, ...).
- При получении подтвержденного суточного лимита ключ временно переводится в статус `exhausted`.
- По истечении 24 часов ключ автоматически возвращается в пул доступных ключей.
