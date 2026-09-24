# Провайдер Gemini CLI (`src/ai/providers/gemini_cli`)

## Обзор

Провайдер `gemini_cli` обеспечивает интеграцию с локальной CLI-утилитой Google Gemini CLI (`gemini`) из Python для платформы **AI-Breadboard**.

Компонент разделен на два уровня:
1. **`GeminiCliProvider`** — низкоуровневый клиент управления процессом CLI, обнаружения исполняемого файла в Windows/Linux, обработки таймаутов, потокового вывода stdout, валидации JSON и запуска агентного режима.
2. **`GeminiCliChatBase`** — высокоуровневый адаптер диалога, реализующий интерфейс `BaseChatProvider` для бесшовной интеграции с `UnifiedChatModel` и Fast-API роутером.

---

## Архитектура

```text
               AI-Breadboard / API Router
                           │
                           ▼
                   UnifiedChatModel
                           │
                           ▼
                  GeminiCliChatBase  (наследует BaseChatProvider)
                           │
                           ▼
                   GeminiCliProvider
          ┌────────────────┼────────────────┬────────────────┐
          ▼                ▼                ▼                ▼
     generate()      generate_json()     stream()        run_agent()
   (обычный запрос) (валидный JSON)   (потоковый)     (контекст проекта)
          │                │                │                │
          └────────────────┴────────┬───────┴────────────────┘
                                    ▼
                           gemini.cmd / gemini
```

---

## 4 режима работы `GeminiCliProvider`

### 1. Обычная текстовая генерация (`generate` / `generate_async`)

```python
from src.ai.providers.gemini_cli import GeminiCliProvider

provider = GeminiCliProvider()

# Синхронный вызов
response = provider.generate("Объясни принцип Fail-Fast в разработке ПО.")
if response.success:
    print(response.text)
else:
    print(f"Ошибка {response.return_code}: {response.stderr}")

# Асинхронный вызов
# response = await provider.generate_async("Привет, Gemini!")
```

### 2. Структурированный JSON-ответ (`generate_json`)

Безопасно извлекает и валидирует JSON даже в случаях, когда модель обрамляет вывод в markdown-блоки ` ```json ... ``` `.

```python
from src.ai.providers.gemini_cli import GeminiCliProvider

provider = GeminiCliProvider()
prompt = "Верни список из 3 популярных языков программирования в формате JSON: [{\"name\": str, \"year\": int}]"

data = provider.generate_json(prompt)
print(data)  # [{'name': 'Python', 'year': 1991}, ...]
```

### 3. Потоковый вывод (`stream` / `stream_async`)

Позволяет выводить токены и строки по мере их генерации процессом CLI в реальном времени.

```python
from src.ai.providers.gemini_cli import GeminiCliProvider

provider = GeminiCliProvider()

# Синхронный стриминг
for chunk in provider.stream("Напиши короткую историю про робота."):
    print(chunk, end="", flush=True)

# Асинхронный стриминг
# async for chunk in provider.stream_async("Напиши стих."):
#     print(chunk, end="", flush=True)
```

### 4. Режим проекта/агента (`run_agent`)

Запускает выполнение задачи в контексте целевого рабочего каталога проекта с доступом к файловой системе и инструментам CLI.

```python
from pathlib import Path
from src.ai.providers.gemini_cli import GeminiCliProvider

provider = GeminiCliProvider()
project_dir = Path(r"C:\Users\onela\AppData\Local\AI-Breadboard")

response = provider.run_agent(
    prompt="Проанализируй структуру проекта и перечисли основные модули в src/ai",
    working_directory=project_dir,
)
print(response.text)
```

---

## Использование через чат-адаптер `GeminiCliChatBase`

```python
from src.ai.providers.gemini_cli import GeminiCliChatBase

chat = GeminiCliChatBase(
    model_id="gemini-3.1-flash-lite",
    system_prompt="Ты эксперт по Python и архитектуре AI.",
)

# Одиночный запрос
answer = await chat.ask("Как настроить DI в Python?")

# Диалог с сохранением истории
reply1 = await chat.chat("Привет, меня зовут Алекс.")
reply2 = await chat.chat("Как меня зовут?")  # Помнит контекст
```

---

## Обнаружение исполняемого файла в Windows

`GeminiCliProvider.find_executable()` автоматически ищет:
1. `gemini.cmd`, `gemini.bat`, `gemini.exe`, `gemini` в системном `PATH`.
2. `%APPDATA%\npm\gemini.cmd`.
3. `%LOCALAPPDATA%\Programs\npm\gemini.cmd`.
4. `~\AppData\Roaming\npm\gemini.cmd`.
