# Руководство по разработке навыков (Skills)

> **Раздел:** Разработка навыков  
> **Язык:** Русский  

---

## 🏭 Быстрый старт через `skill-factory`

Самый быстрый и надежный способ создать новый навык со всей структурой директорий, манифестом `SKILL.md`, поддержкой i18n и шаблонами тестов — использовать встроенную фабрику навыков **`skill-factory`**.

### Команда инициализации:

```powershell
python .agents/skills/skill-factory/scripts/init_skill.py api-tester `
  --description-en "Tests REST API endpoints, validates HTTP status codes and JSON schemas." `
  --description-ru "Тестирует REST API эндпоинты, проверяет HTTP статус-коды и JSON-схемы."
```

После выполнения команды в `.agents/skills/api-tester/` будет развернута готовая структура файлов.

---

## 📂 Полная структура навыка

```text
.agents/skills/api-tester/
├── SKILL.md                 # Главный манифест (YAML Frontmatter + Markdown инструкции)
├── README.md                # Англоязычное описание для разработчиков
├── scripts/                 # Исполняемые утилиты
│   ├── run_tests.py         # Основной скрипт проверки
│   └── format_report.py     # Форматирование результатов
├── references/              # Справочные материалы (спецификации OpenAPI)
├── resources/               # Шаблоны и конфигурации
├── examples/                # Примеры запросов и ответов
│   └── test_payload.json
└── tests/                   # Модульные тесты скриптов
    └── test_run_tests.py
```

---

## 📝 Спецификация манифеста `SKILL.md`

Манифест `SKILL.md` состоит из блока метаданных (YAML Frontmatter) и структурированного руководства для языковой модели:

```markdown
---
name: api-tester
description: Tests REST API endpoints, validates HTTP status codes and JSON schemas.
description_i18n:
  en: Tests REST API endpoints, validates HTTP status codes and JSON schemas.
  ru: Тестирует REST API эндпоинты, проверяет HTTP статус-коды и JSON-схемы.
version: 1.0.0
category: testing
---

# API Tester Skill

Инструмент для автоматизированной проверки и тестирования HTTP REST API.

## 📋 Возможности
- Проверка доступности эндпоинтов и времени ответа (latency).
- Валидация структуры JSON-ответов по JSON Schema.
- Экспорт сводных отчетов в формате Markdown.

## 🛠️ Рабочий процесс (Workflow)
1. Проверить доступность базового URL сервиса через `scripts/run_tests.py --ping`.
2. Запустить набор тестов по спецификации.
3. При обнаружении ошибок с кодами 4xx/5xx локализовать сбойный запрос.

## ⚙️ Параметры скрипта

| Параметр | Описание | Обязательный |
|---|---|---|
| `--url` | Базовый URL целевого сервиса | Да |
| `--schema` | Путь к JSON Schema для валидации | Нет |
| `--timeout` | Таймаут ожидания ответа в секундах (по умолчанию: 5) | Нет |

## 📝 Чек-лист использования
- [ ] Сервер запущен и отвечает по сети.
- [ ] Ключи авторизации переданы через переменные окружения.
- [ ] Выходной отчет сохранен в артефактах задачи.
```

---

## 🎯 Секрет качественного поля `description`

Поле `description` в YAML Frontmatter — самый важный элемент навыка. Именно по нему оркестратор и модель определяют необходимость активации навыка.

### ✅ Как правильно:
> `description: "Analyzes SQLite database schemas, checks foreign key integrity, and detects missing indexes. Use when user requests database diagnostics or schema review."`
*(Четко указано ЧТО делает инструмент и КОГДА его применять)*.

### ❌ Как неправильно:
> `description: "Database tool"`
*(Слишком абстрактно; модель не поймет конкретные триггеры вызова)*.

---

## 🐍 Разработка вспомогательных скриптов (`scripts/`)

Скрипты навыков должны соответствовать инженерным стандартам проекта:

```python
# -*- coding: utf-8 -*-
"""API testing script for api-tester skill."""

import argparse
import sys
import json
from pathlib import Path
from logger import logger


def run_api_check(base_url: str, timeout: int = 5) -> dict:
    """Executes basic ping check against target URL."""
    logger.info(f"Checking URL: {base_url} (timeout={timeout}s)")
    # Реализация логики
    return {"url": base_url, "status_code": 200, "latency_ms": 42}


def main() -> None:
    parser = argparse.ArgumentParser(description="API Testing Utility")
    parser.add_argument("--url", required=True, help="Target service URL")
    parser.add_argument("--timeout", type=int, default=5, help="Request timeout")
    args = parser.parse_args()

    try:
        result = run_api_check(args.url, args.timeout)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as exc:
        logger.error(f"API check failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

---

## 🧪 Тестирование навыка

Для проверки работоспособности скриптов навыка напишите тесты в директории `tests/`:

```python
# -*- coding: utf-8 -*-
import pytest
from scripts.run_tests import run_api_check


def test_api_check_success():
    res = run_api_check("http://localhost:8000/api/health")
    assert res["status_code"] == 200
```

Запуск тестирования:
```powershell
pytest .agents/skills/api-tester/tests/
```
