# tools/setup/ — Инструменты настройки кодовой базы

Скрипты для **анализа и настройки** самой кодовой базы проекта.  
Используются при рефакторинге, анализе зависимостей.

---

## Файлы

| Файл | Назначение | Команда |
|------|------------ |---------|
| `analyze_dependencies.py` | Анализ зависимостей между модулями | `py tools/setup/analyze_dependencies.py` |
| `scan_headers.py` | Сканирование заголовков Python-файлов | `py tools/setup/scan_headers.py` |
| `convert_to_md.py` | Конвертация файлов в Markdown | `py tools/setup/convert_to_md.py` |

---

## Примечание

`header.py` в корне проекта — **не устаревший дубль**.  
Он используется в `main.py` и `manage_tools.py` для определения `__root__`.  
`src/header.py` — аналог для модулей внутри `src/`.
