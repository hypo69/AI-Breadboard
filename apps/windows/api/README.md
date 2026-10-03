# Внутренний FastAPI-сервис Windows (Internal API & Web GUI)

Модуль реализует внутренний HTTP/REST API и локальный веб-интерфейс (Windows TC Control Center) для подсистемы Windows.

## 📁 Структура

- **`internal_app.py`** — фабрика создания приложения FastAPI (`create_internal_app`), конфигурация middleware и подключение роутеров.
- **`__main__.py`** — точка входа для запуска выделенного Uvicorn-сервера на localhost: `py -m apps.windows.api --port 8001`.
- **`router_capabilities.py`** — роутер атомарных возможностей и действий Windows.
- **`routers/`** — модульные FastAPI-роутеры по панелям интерфейса:
  - `router_tc.py` — интеграция с Total Commander и панелями.
  - `router_about_system.py` — REST API панели «О Системе» (`/api/v1/about-system/*`) на базе `telemetry.db`.
  - `router_diagnostics.py` — эндпоинты запуска диагностик и проверки состояния.
  - `router_admin.py`, `router_control.py`, `router_scenarios.py` и др.
- **`webgui/`** — статические ассеты веб-интерфейса (HTML/CSS/JS).
- **`config.json`** — параметры конфигурации локального сервиса.

> [!NOTE]
> Низкоуровневые CFFI/`ctypes` вызовы нативных библиотек Windows (`kernel32.dll`, `advapi32.dll`, `wevtapi.dll`, `setupapi.dll` и др.) вынесены в модуль телеметрии: [`apps.windows.telemetry.win32_ffi`](../telemetry/win32_ffi/).
