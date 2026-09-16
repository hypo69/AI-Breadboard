# AI Breadboard — Полная документация проекта

> Интерактивный стенд для исследования, тестирования и сравнения языковых моделей ИИ.

Этот раздел содержит **всю русскоязычную документацию** проекта. Разрозненные `.md` файлы из корня проекта собраны здесь по тематическим разделам.

---

## 📁 Структура документации

```
docs/ru/
├── README.md              ← Вы здесь (главный индекс)
├── ARCHITECTURE.md        ← Архитектура кроссплатформенного решения
├── architecture/          ← Обзор архитектуры, компонентов и моделей
├── plugins/               ← Плагины системы (архитектура, создание, каталог)
├── skills/                ← Навыки моделей (Progressive Disclosure, создание, каталог)
├── manual/                ← Руководства пользователя (установка, запуск, конфигурация)
├── guides/                ← Практические гайды и интеграции
├── cook-book/             ← Учебная книга (8 глав)
├── developer/             ← Руководство разработчика (Engineering Standards, TDD)
├── ported.md              ← Детали портирования
└── index.md               ← Обзор проекта и навигация
```

---

## 👨‍💻 Руководство разработчика

- [Руководство разработчика](developer/index.md) — стандарты кода, hypo69 docblock, протокол TDD, добавление провайдеров и эндпоинтов

---

## 🚀 Быстрый старт

- [Установка и требования](manual/installation.md) — установка за 5 минут на Windows и Linux
- [Руководство по запуску (`RUN.md`)](manual/RUN.md) — запуск веб-сервера и сопутствующих служб
- [Справочник конфигурации (`config.json`)](manual/config.md) — `config.json`, `.env`, пути
- [Первые шаги](manual/getting-started.md) — обзор функций и сценариев

---

## 🏗️ Архитектура

- [Архитектура системы](ARCHITECTURE.md) — слои, компоненты, потоки выполнения
- [Обзор архитектуры](architecture/overview.md) — оркестратор провайдеров, шина `UnifiedChatModel`
- [Компоненты системы](architecture/components.md) — адаптеры провайдеров, сервисы, кэширование
- [Провайдер Google Gemini](architecture/gemini-provider.md) — ротация API-ключей, квоты, rate-limits
- [Интеграция с Google Workspace](architecture/google-workspace-integration.md) — OAuth 2.0, Gmail, Drive, Sheets

---

## 📚 Учебная книга

Практическое руководство по работе со стендом AI Breadboard:

| # | Глава |
|---|-------|
| 1 | [Архитектура макетной платы и среда](cook-book/ch01_philosophy.md) |
| 2 | [Оркестратор моделей и отказоустойчивость](cook-book/ch02_orchestration.md) |
| 3 | [Локальный инференс (HF и DirectML)](cook-book/ch03_local_inference.md) |
| 4 | [Архитектура RAG и векторный поиск](cook-book/ch04_rag_architecture.md) |
| 5 | [Оптимизация, экспорт и Fine-Tuning](cook-book/ch05_optimization_finetuning.md) |
| 6 | [ReAct-агенты, MCP и мультимодальность](cook-book/ch06_agents_and_mcp.md) |
| 7 | [Создание и управление навыками](cook-book/ch07_skills_management.md) |
| 8 | [Практикум: 10 лабораторных работ](cook-book/ch08_laboratory_practicum.md) |

---

## 🧩 Плагины и навыки

- [Каталог плагинов (10 плагинов)](plugins/catalog.md) — Telegram, Facebook, RAG Cleaner, Codebase RAG, IFTTT, Invoice Processor, News Feed, etc.
- [Каталог навыков (25 навыков)](skills/catalog.md) — TDD Gen, RAG Search, DB Inspector, Google Workspace, Travel Agent, etc.

---

## 📦 README модулей (на английском)

По стандарту проекта README каждого модуля написан на английском языке:

| Модуль | Описание |
|---|---|
| `src/` | Ядро системы, провайдеры, API, RAG, TTS, плагины и навыки |
| `scripts/cli/` | Кроссплатформенные CLI-утилиты (`assist.py`, `installer.py`) |
| `launchers/` | Скрипты запуска сервисов и демонов (`run.py`, `Run-*.ps1`) |
| `tests/` | Набор юнит- и интеграционных тестов pytest |
| `docs/` | Многоязычная документация проекта |

---

## 🔗 Ссылки

- **GitHub:** https://github.com/hypo69/AI-Breadboard
- **Issues:** https://github.com/hypo69/AI-Breadboard/issues
- **Автор:** hypo69@yandex.com
- **Лицензия:** MIT © 2026 hypo69
