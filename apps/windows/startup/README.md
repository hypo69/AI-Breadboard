# 🚀 Windows Startup & Persistence Auditor

**Windows Startup & Persistence Auditor** — автономное приложение и модуль экосистемы **AI Breadboard** для всестороннего обнаружения, глубокого аудита безопасности и оптимизации всех механизмов автозапуска и персистентности в операционной системе Windows.

---

## 📋 Оглавление
- [Возможности](#-возможности)
- [Контролируемые точки автозапуска](#-контролируемые-точки-автозапуска)
- [Архитектура приложения](#-архитектура-приложения)
- [Правила аудита и оценка рисков](#-правила-аудита-и-оценка-рисков)
- [Использование (CLI и TUI)](#-использование-cli-и-tui)
- [FastAPI REST API](#-fastapi-rest-api)
- [Конфигурация](#-конфигурация)

---

## ✨ Возможности

- **Полное сканирование всех веток реестра**: `Run`, `RunOnce`, `RunOnceEx`, `Policies\Explorer\Run`, а также 32-битные ветки подсистемы `WOW6432Node` в `HKLM` и `HKCU`.
- **Анализ файловой системы**: Сканирование пользовательской (`%APPDATA%`) и общесистемной (`%PROGRAMDATA%`) папок автозагрузки, автоматическое разрешение ярлыков `.lnk` и скриптов.
- **Статусы включения/отключения**: Прямая интеграция с реестром `StartupApproved` Windows Task Manager для определения фактического состояния автозапуска элементов.
- **Аудит системных механизмов**: Проверка параметров `Winlogon` (`Shell`, `Userinit`, `AppInit_DLLs`).
- **Обнаружение отладочных перехватов (IFEO)**: Поиск внедрений отладчиков через `Image File Execution Options` (debugger hijacking).
- **Аудит задач планировщика**: Анализ триггеров запуска (`Logon`, `Boot`, `Startup`) и поиск скрытых/закодированных команд PowerShell (`-enc`, `-w hidden`).
- **Аудит автозапускаемых служб**: Обнаружение сторонних служб с типом старта `Auto` и `Delayed-Auto`.
- **Анализ целостности**: Автоматическое выявление «мёртвых» (битых) записей автозагрузки с отсутствующими файлами на диске.
- **Расчет индекса чистоты (Health Score)**: Числовая оценка (0-100) безопасности и оптимизированности автозапуска.
- **Экспорт отчетов**: Сохранение результатов аудита в форматах JSON и CSV.

---

## 🔍 Контролируемые точки автозапуска

| Тип локации | Расположение в системе | Описание |
|---|---|---|
| **Реестр Run (User)** | `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` | Автозапуск при входе текущего пользователя |
| **Реестр Run (System)** | `HKLM\Software\Microsoft\Windows\CurrentVersion\Run` | Общесистемный автозапуск для всех пользователей |
| **Реестр WOW6432Node** | `HKLM\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run` | Автозапуск 32-битных приложений на x64 Windows |
| **Реестр RunOnce** | `HKCU`/`HKLM` `...\CurrentVersion\RunOnce` | Однократный старт программы при перезагрузке |
| **Политики Explorer** | `HKCU`/`HKLM` `...\Policies\Explorer\Run` | Административные политики автозапуска |
| **Папка Startup (User)** | `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup` | Ярлыки и скрипты в профиле пользователя |
| **Папка Startup (Common)** | `%ProgramData%\Microsoft\Windows\Start Menu\Programs\Startup` | Ярлыки и скрипты для всех пользователей |
| **Winlogon** | `HKLM\Software\Microsoft\Windows NT\CurrentVersion\Winlogon` | Системные оболочки (`Shell`, `Userinit`, `Taskman`) |
| **IFEO Debuggers** | `HKLM\Software\Microsoft\Windows NT\CurrentVersion\Image File Execution Options` | Отладочные перехваты запуска исполняемых файлов |
| **Планировщик задач** | Windows Task Scheduler (`schtasks`) | Задачи с триггерами при входе или старте системы |
| **Службы Windows** | `Services.msc` (`Win32_Service`) | Службы с автоматическим типом запуска |

---

## 🏛️ Архитектура приложения

```
apps/windows_startup_auditor/
├── __init__.py                # Экспорт фабрики роутера и движка
├── __main__.py                # CLI точка входа и standalone сервер
├── config.json                # Конфигурация приложения (порт 8112)
├── README.md                  # Документация приложения
├── router.py                  # FastAPI REST и WebSocket эндпоинты
├── tui.py                     # Rich Terminal Dashboard
├── core/
│   ├── __init__.py
│   ├── models.py              # Pydantic модели данных и DTO
│   ├── scanner.py             # Сканер всех точек автозапуска Windows
│   ├── auditor.py             # Движок классификации, аудита и скоринга
│   └── manager.py             # Управление состоянием (StartupApproved) и экспорт
└── tests/
    ├── __init__.py
    ├── test_models.py
    ├── test_scanner.py
    ├── test_auditor.py
    └── test_router.py
```

---

## 🛡️ Правила аудита и оценка рисков

1. **`CRITICAL` (Критический риск)**:
   - Обнаружен отладочный перехватчик `IFEO Debugger`.
   - Командная строка содержит флаги обфускации или скрытого запуска (`-encodedcommand`, `-enc`, `-windowstyle hidden`, `bypass`).
2. **`SUSPICIOUS` (Подозрительный)**:
   - Запуск бинарных файлов или скриптов из временных каталогов (`%TEMP%`, `C:\Users\Public`, `C:\Windows\Temp`).
   - Прямой автозапуск скриптовых интерпретаторов (`mshta.exe`, `wscript.exe`, `cscript.exe`, `regsvr32.exe`).
3. **`WARNING` (Предупреждение)**:
   - Битая ссылка автозагрузки (исполняемый файл удален или путь не существует на диске).
4. **`NOTICE` (Информационный)**:
   - Стороннее пользовательское приложение или фоновый модуль обновления (фоновый апдейтер).
5. **`CLEAN` (Безопасный)**:
   - Доверенный системный компонент Windows или подписанный драйвер оборудования (Intel, NVIDIA, Realtek, AMD).

---

## 💻 Использование (CLI и TUI)

### Интерактивный дашборд (TUI на базе Rich)
```powershell
python -m apps.windows.startup --audit
```

### Вывод отчета в формате JSON
```powershell
python -m apps.windows.startup --json
```

### Выгрузка отчета в файл CSV
```powershell
python -m apps.windows.startup --export startup_audit.csv
```

### Запуск автономного FastAPI сервера
```powershell
python -m apps.windows.startup --mode server --port 8112
```

---

## 🌐 FastAPI REST API

Эндпоинты доступны по префиксу `/api/v1/startup-auditor`:

| Метод | Эндпоинт | Описание |
|---|---|---|
| `GET` | `/status` | Статус готовности сервиса |
| `GET` | `/locations` | Список контролируемых точек автозапуска |
| `GET` | `/audit` | Запуск полного аудита и получение полного отчета |
| `GET` | `/summary` | Краткая сводка, счетчики и Health Score |
| `GET` | `/entries` | Список элементов автозапуска с параметрами фильтрации |
| `POST` | `/toggle` | Включение/отключение элемента автозагрузки (`StartupApproved`) |
| `GET` | `/export?format=json` | Экспорт отчета в формате JSON или CSV |
| `WS` | `/stream` | WebSocket поток обновлений аудита |

---

## ⚙️ Конфигурация

Файл `config.json`:
```json
{
  "app_name": "windows_startup_auditor",
  "display_name": "Windows Startup Auditor",
  "description": "Комплексный аудит всех точек автозапуска и персистентности Windows",
  "version": "1.0.0",
  "enabled": true,
  "tab": "tab-startup-auditor",
  "server": {
    "host": "127.0.0.1",
    "port": 8112,
    "use_ssl": false,
    "workers": 1
  }
}
```

---

## 📜 Лицензия

© 2026 hypo69. Все права защищены.
