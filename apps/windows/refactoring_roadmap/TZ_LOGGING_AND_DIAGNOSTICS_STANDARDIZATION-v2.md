# Техническое задание: Стандартизация сквозного логирования, дублирования ошибок и оптимизации производительности `logger.py` (v2)

## 1. Назначение и ключевые требования

Настоящее техническое задание определяет архитектурный стандарт интеграции системы логирования, обработки ошибок и оптимизации производительности подсистемы `Logger` во всех модулях платформы **AI-Breadboard Windows Diagnostic & Administration Center**.

### Ключевые требования
1. **100% Покрытие кодовой базы (100% Codebase Coverage)**: Запрещается прямое использование встроенного модуля `logging.getLogger()` без единого интерфейса или частичное отсутствие логирования. Все модули без исключения ведут запись через переменную `logger`.
2. **Унифицированный защитный импорт с ленивой загрузкой (Universal Fallback Import Pattern)**: Каждый модуль платформы обязан содержать единую паттерн-конструкцию с гарантированным переключением на стандартный логгер при отсутствии или сбое импорта `logger.py`. Модуль `logging` подгружается лениво (lazy import) только в аварийной ветке `except ImportError`.
3. **Принудительное дублирование трейсбеков в консоль**: Все сбои в эндпоинтах `FastAPI`, middleware и критических процессах должны логироваться с полным трейсбеком (`exc_info=True`) и дублироваться в системную консоль.
4. **Высокопроизводительная инспекция стека**: Определение вызывающего контекста в `_get_caller_info()` переводится с `inspect.stack()` на микросекундный C-API вызов `sys._getframe()`.

---

## 2. Стандарт импорта и шаблон защищенного фолбэка (Universal Import Guard)

Во всех существующих и вновь создаваемых Python-файлах платформы (включая автономные службы Windows, CLI-скрипты, REST-роутеры и фоновые коллекторы) логирование инициализируется **строго по следующему оптимизированному шаблону с ленивым импортом `logging`**:

```python
import sys

# Унифицированный паттерн гарантированного импорта логгера
try:
    from logger import logger
except ImportError:
    # Фолбэк на стандартный логгер при автономном запуске без модуля logger.py (Lazy Import)
    import logging
    logger = logging.getLogger("AITelemetryFallback")
    if not logger.handlers:
        _handler = logging.StreamHandler(sys.stderr)
        _formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] - %(message)s"
        )
        _handler.setFormatter(_formatter)
        logger.addHandler(_handler)
        logger.setLevel(logging.DEBUG)
```

### Преимущества данного шаблона
* **Ленивая загрузка (Lazy Import)**: В 99% случаев успешного импорта `from logger import logger` модуль `logging` не загружается в область видимости файла, снижая накладные расходы на инициализацию.
* **Изоляция заменяемости**: Стандартный модуль `logging` подгружается только в качестве аварийного резерва.
* **Чистота глобального пространства имен**: В файлах не создается лишних импортов верхнего уровня, если все операции выполняются через абстракцию `logger`.

### Правила применения
* Переменная логгера **всегда должна именоваться `logger`**.
* Категорически запрещается переопределять `logger = logging.getLogger(...)` поверх импортированного синглтона.
* Все вызовы вывода информации в коде осуществляются только через методы глобального экземпляра: `logger.debug()`, `logger.info()`, `logger.warning()`, `logger.error()`, `logger.critical()`.

---

## 3. Правила обработки ошибок и дублирования трейсбеков в REST API и консоль

### 3.1 Обработка сбоев в эндпоинтах FastAPI
Во всех обработчиках REST API (`apps/windows/api/routers/` и роутерах функциональных модулей) перехват исключений включает обязательную запись полного трейсбека с принудительным дублированием вывода в консоль:

```python
@router.get("/api/v1/system/status")
async def get_system_status():
    try:
        # Исполнение системного вызова
        return await fetch_telemetry_snapshot()
    except Exception as e:
        # 1. Запись с трейсбеком в файл и централизованный обработчик
        logger.error(f"[REST API Error] GET /api/v1/system/status failed: {e}", exc_info=True)
        
        # 2. Гарантированный дублирующий вывод ошибки в системный поток stderr
        sys.stderr.write(f"\n[CRITICAL REST EXCEPTION] {request.url.path}: {str(e)}\n")
        sys.stderr.flush()
        
        raise HTTPException(status_code=500, detail=str(e))
```

### 3.2 Настройка `PrettyConsoleFormatter`
Класс `PrettyConsoleFormatter` в `logger.py` модернизируется для автоматической подсветки и форматирования трассировок стека исключений в консоли:

* При наличии `exc_info` форматировщик отрисовывает блок трассировки ярким красным цветом (`colorama.Fore.RED`) с графическим разделителем `------------------- TRACEBACK -------------------`.

---

## 4. Оптимизация производительности: замена `inspect.stack()` на `sys._getframe()`

Для устранения задержек в высокочастотных циклах телеметрии (250 мс тики, ETW-пайплайн) метод `_get_caller_info()` в `logger.py` переписывается с использованием высокоскоростного C-API вызова `sys._getframe()`:

### Было (Задержка ~1.2 - 1.8 мс на один вызов лога):
```python
def _get_caller_info(self):
    stack = inspect.stack()
    # Медленное считывание всего стека вызовов и дисковых исходников
    for frame_info in stack[2:]:
        filename = frame_info.filename
        if not filename.endswith("logger.py"):
            return filename, frame_info.lineno, frame_info.function
    return "unknown", 0, "unknown"
```

### Стало (Задержка <0.015 мс на один вызов лога):
```python
def _get_caller_info(self):
    try:
        # Прямой проход по кадрам стека в памяти без дисковых I/O операций
        frame = sys._getframe(2)
        while frame:
            filename = frame.f_code.co_filename
            if not filename.endswith("logger.py"):
                return filename, frame.f_lineno, frame.f_code.co_name
            frame = frame.f_back
    except Exception:
        pass
    return "unknown", 0, "unknown"
```

---

## 5. Автоматический сброс критических ошибок в `telemetry.db`

Для создания единого системного журнала сбоев в `Logger` добавляется специализированный обработчик `SQLiteTelemetryLogHandler`:

### 5.1 Схема таблицы `system_error_logs` в SQLite
```sql
CREATE TABLE IF NOT EXISTS system_error_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    level TEXT NOT NULL,                  -- 'ERROR', 'CRITICAL'
    module_name TEXT NOT NULL,
    filename TEXT NOT NULL,
    line_number INTEGER NOT NULL,
    message TEXT NOT NULL,
    traceback_text TEXT,
    is_resolved INTEGER NOT NULL DEFAULT 0
);
```

### 5.2 Поведение хэндлера
* Перехватывает только записи с уровнем `level >= logging.ERROR`.
* Производит асинхронный сброс в `telemetry.db` через встроенный кольцевой буфер, исключая блокировку главного потока.

---

## 6. Расширение правил динамической маршрутизации (`_route_to_module_logger`)

В методе `_route_to_module_logger` расширяется карта автоматического распределения сообщений по изолированным файлам логов:

| Модуль / Подсистема | Паттерн пути / Файла | Целевой лог-файл |
| :--- | :--- | :--- |
| **FastAPI Server** | `fast_api.py`, `routers/` | `logs/fastapi.log` |
| **Gemini AI / LLM** | `gemini`, `wikillm` | `logs/gemini.log` |
| **Playwright Web** | `playwright`, `browser` | `logs/playwright.log` |
| **Media Downloader**| `yt_dlp` | `logs/yt_dlp.log` |
| **Focus Policy** | `focus_policy`, `focus_executor` | `logs/focus.log` |
| **VSS Versioning** | `vss_versioning`, `backup_manager` | `logs/vss.log` |
| **Personalization** | `personalization` | `logs/personalization.log` |
| **PID Telemetry** | `pid_telemetry`, `process_collector`| `logs/pid_telemetry.log` |
| **Ядро Телеметрии** | `telemetry/`, `sqlite.py` | `logs/telemetry.log` |

---

## 7. Ротация логов и автосжатие (`CompressingHandler` & `log_analyzer.py`)

1. **Сжатие повторов (`CompressingHandler`)**:
   * Все дисковые файлы логов управляются через `CompressingHandler` (`maxBytes=10MB`, `backupCount=5`).
   * Повторяющиеся записи объединяются в буфере и записываются в виде `[Nx] <message>`, предотвращая переполнение дискового пространства.

2. **ИИ-анализ логов (`log_analyzer_loop`)**:
   * При достижении размера любого лог-файла 10 МБ фоновая служба считывает фрагмент аномалий, отправляет запрос в Gemini для генерации резюме, обновляет `master_journal.md` и очищает основной файл.

---

## 8. Регламент приемки и критерии качества

1. **Static Analysis Check**: Запуск `ast`-сканера по всем файлам проекта для подтверждения наличия шаблона с ленивым импортом `import logging` внутри `except ImportError:` в 100% Python-модулей.
2. **Benchmark Test**: Тестирование `_get_caller_info()` должно подтвердить ускорение логирования (время исполнения не более 0.02 мс за вызов).
3. **Traceback Console Verification**: Вызов ошибки в REST-эндпоинте должен корректно логировать трейсбек в лог-файл и форматированно дублировать его ярким цветом в консоль.
