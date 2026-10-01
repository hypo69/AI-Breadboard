# 🗝️ Windows Registry Viewer & Editor Application

## 📋 Описание
**Windows Registry Viewer & Editor** — автономное микроприложение экосистемы AI-Breadboard для безопасного просмотра, интерактивного аудита, навигации, полнотекстового поиска и **безопасного редактирования параметров и подразделов системного реестра Windows** (`HKLM`, `HKCU`, `HKCR`, `HKU`, `HKCC`) с **обязательным предварительным созданием резервных копий (снимков)** перед сохранением любых изменений и поддержкой отката.

Приложение может запускаться как в консольном TUI/CLI режиме, так и в виде отдельного FastAPI микросервиса или встроенного модуля в AI-Breadboard Web UI.

---

## ✨ Основные возможности
- **Инструменты редактора реестра:** Создание и изменение параметров (`REG_SZ`, `REG_DWORD`, `REG_QWORD`, `REG_MULTI_SZ`, `REG_BINARY`, `REG_EXPAND_SZ`), создание и удаление подразделов.
- **Обязательное автоматическое резервное копирование:** Перед любым изменением или удалением данных создается снимок ветки в форматах JSON и нативном `.reg` в каталоге `data/registry_backups/`.
- **Точки восстановления и откат (Rollback):** Возможность мгновенно восстановить состояние ветки реестра из любой сохраненной точки восстановления через REST API или Web UI.
- **Поддержка всех корневых разделов:** `HKEY_LOCAL_MACHINE`, `HKEY_CURRENT_USER`, `HKEY_CLASSES_ROOT`, `HKEY_USERS`, `HKEY_CURRENT_CONFIG` и их коротких псевдонимов (`HKLM`, `HKCU`, `HKCR`, `HKU`, `HKCC`).
- **Быстрые системные закладки:** Мгновенный переход к автозагрузке (Run/RunOnce), списку установленных программ (x64/x86 Uninstall), системным службам (Services), переменным среды (Environment) и групповым политикам.
- **Полнотекстовый рекурсивный поиск:** Поиск по именам ключей, названиям параметров и их значениям с контролем глубины обхода.
- **Интерактивный Web UI & TUI:** Веб-панель с модальными окнами редактирования, кнопками быстрого создания параметров, удаления и списком бэкапов, а также консольный интерфейс Rich.
- **Гибкий экспорт:** Выгрузка параметров в форматы JSON и CSV.
- **Автономный REST API сервер:** Встроенный веб-сервис на базе FastAPI и Uvicorn.
- **Кроссплатформенный Fallback (Mock):** Автоматическая генерация демонстрационных данных при запуске на не-Windows системах или в изолированных тестовых средах.

---

## 🚀 Быстрый старт и запуск

### 1. Консольный режим (CLI / TUI)

```powershell
# Просмотр списка системных закладок
python -m apps.windows.registry --bookmarks

# Быстрый переход к разделу автозагрузки
python -m apps.windows.registry --bookmark startup_run

# Просмотр конкретного раздела реестра
python -m apps.windows.registry --view "HKLM\SOFTWARE\Microsoft\Windows"

# Поиск по поддереву реестра
python -m apps.windows.registry --search "Windows" --hive HKLM --max-results 20

# Экспорт в файл JSON или CSV
python -m apps.windows.registry --bookmark services --export services.json
python -m apps.windows.registry --bookmark installed_apps_x64 --export apps.csv
```

### 2. Запуск автономного REST API сервера

```powershell
python -m apps.windows.registry --mode server --port 8114
```

Интерактивная документация Swagger/OpenAPI будет доступна по адресу:  
`http://127.0.0.1:8114/docs`

---

## 📡 REST API Эндпоинты

| Метод | Эндпоинт | Описание |
|---|---|---|
| `GET` | `/api/registry/bookmarks` | Список быстрых системных закладок |
| `GET` | `/api/registry/key` | Получение подразделов и параметров ключа (`hive`, `path`) |
| `GET` | `/api/registry/search` | Полнотекстовый поиск (`query`, `hive`, `path`, `max_results`) |
| `GET` | `/api/registry/export` | Экспорт ключа в формате JSON или CSV (`format=json\|csv`) |
| `POST` | `/api/registry/value` | Создание или изменение параметра с автобэкапом |
| `DELETE` | `/api/registry/value` | Удаление параметра с автобэкапом |
| `POST` | `/api/registry/key` | Создание нового подраздела реестра |
| `DELETE` | `/api/registry/key` | Удаление подраздела реестра с автобэкапом |
| `GET` | `/api/registry/backups` | Список точек восстановления и истории бэкапов |
| `POST` | `/api/registry/restore` | Откат состояния раздела из снимка бэкапа |

---

## 📂 Структура приложения

```
apps/registry_viewer/
├── __init__.py          # Экспорт ключевых модулей, моделей и функций
├── __main__.py          # Точка входа CLI / Standalone Server
├── backup.py            # Менеджер резервного копирования и отката (снимки .reg / .json)
├── config.json          # Конфигурационный файл приложения
├── models.py            # Pydantic модели (DTO запросов, ответов, бэкапов)
├── viewer.py            # Ядро RegistryViewer (чтение/запись winreg, поиск, бэкапы)
├── tui.py               # Rich TUI интерфейс отображения
├── router.py            # FastAPI роутер эндпоинтов просмотра и редактирования
└── README.md            # Документация приложения
```

---

## 🧪 Тестирование

Запуск тестов приложения:
```powershell
pytest tests/test_app_registry_viewer.py tests/test_router_registry_viewer.py -v
```

