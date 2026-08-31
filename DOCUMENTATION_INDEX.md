# Индекс документации AI Breadboard — Портирование на Linux/macOS

Полный индекс всей документации по портированию AI Breadboard на кроссплатформенное решение.

## 🚀 Начните отсюда

### Для новых пользователей

1. **[QUICK_START.md](./QUICK_START.md)** ⭐ **НАЧНИТЕ ОТСЮДА**
   - Быстрая установка на все платформы
   - Основные команды
   - Простые Examples
   - Время: 5-10 минут

### Для опытных разработчиков

1. **[PORTING_SUMMARY.md](./PORTING_SUMMARY.md)** — Итоги портирования
   - Что было портировано
   - Статистика
   - Преимущества подхода
   - Время: 10-15 минут

2. **[ARCHITECTURE.md](./ARCHITECTURE.md)** — Архитектура решения
   - Как все работает
   - Слои архитектуры
   - Examples кода
   - Время: 20-30 минут

## 📖 Основная документация

### Установка и первый запуск

| Документ | Когда использовать | Длина |
|----------|-------------------|-------|
| [QUICK_START.md](./QUICK_START.md) | Первый раз | 5 мин |
| [INSTALL_LINUX.md](./INSTALL_LINUX.md) | Установка на Linux | 15 мин |
| [CONFIG.md](./CONFIG.md) | Конфигурирование | 20 мин |
| [MIGRATION_TO_LINUX.md](./MIGRATION_TO_LINUX.md) | Миграция со старых скриптов | 15 мин |

### Техническая документация

| Документ | Тема | Целевая аудитория |
|----------|------|-------------------|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Архитектура системы | Разработчики |
| [PORTING_SUMMARY.md](./PORTING_SUMMARY.md) | Обзор портирования | Все |
| [VERIFICATION_CHECKLIST.md](./VERIFICATION_CHECKLIST.md) | Check компонентов | QA / DevOps |
| [DOCUMENTATION_INDEX.md](./DOCUMENTATION_INDEX.md) | Этот документ | Все |

### Документация модулей

| Документ | Module | Содержит |
|----------|--------|----------|
| [scripts/cli/README.md](./scripts/cli/README.md) | scripts/cli/ | API модулей |
| [scripts/cli/INSTALLER_README.md](./scripts/cli/INSTALLER_README.md) | installer.py | Варианты установки |
| [.mcp/README.md](./.mcp/README.md) | MCP серверы | Configuration MCP |
| [systemd/README.md](./systemd/README.md) | systemd сервисы | Автозапуск на Linux |

## 🔍 По типам задач

### Я хочу установить проект

**Выберите вашу ОС:**
- Windows → [QUICK_START.md](./QUICK_START.md) (раздел Windows)
- Linux → [INSTALL_LINUX.md](./INSTALL_LINUX.md)
- macOS → [INSTALL_LINUX.md](./INSTALL_LINUX.md) (используются bash скрипты как на Linux)

### Я хочу запустить сервер

1. [QUICK_START.md](./QUICK_START.md) — основные команды
2. [CONFIG.md](./CONFIG.md) — конфигурирование
3. Запустить: `./run` или `run.cmd`

### Я хочу перейти со старых PowerShell скриптов

1. Читать: [MIGRATION_TO_LINUX.md](./MIGRATION_TO_LINUX.md)
2. Следовать инструкциям миграции
3. Проверить: [VERIFICATION_CHECKLIST.md](./VERIFICATION_CHECKLIST.md)

### Я хочу настроить конфигурацию

1. Читать: [CONFIG.md](./CONFIG.md)
2. Создать `.env` файл
3. Использовать `assist config` команды

### Я хочу понять архитектуру

1. Читать: [ARCHITECTURE.md](./ARCHITECTURE.md)
2. Смотреть Examples в [scripts/cli/README.md](./scripts/cli/README.md)
3. Смотреть код в `scripts/cli/`

### Я хочу проверить что всё работает

1. Следовать: [VERIFICATION_CHECKLIST.md](./VERIFICATION_CHECKLIST.md)
2. Запустить тесты: `assist test`
3. Проверить логи: `assist logs 100`

### Я хочу настроить systemd сервисы (Linux)

1. Читать: [systemd/README.md](./systemd/README.md)
2. Запустить: `cd systemd && bash install.sh`
3. Управлять: `systemctl --user start/stop/status ai-breadboard-*`

### Я хочу расширить/изменить код

1. Понять архитектуру: [ARCHITECTURE.md](./ARCHITECTURE.md)
2. Посмотреть API: [scripts/cli/README.md](./scripts/cli/README.md)
3. Добавить код в `scripts/cli/`
4. Протестировать на всех ОС

## 📚 Структура документации

### Документы уровня проекта (корень)

```
README.md                      # Основное описание проекта
QUICK_START.md                 # Быстрый старт ⭐
INSTALL_LINUX.md               # Установка на Linux
CONFIG.md                      # Configuration
MIGRATION_TO_LINUX.md          # Миграция со старых скриптов
ARCHITECTURE.md                # Архитектура решения
PORTING_SUMMARY.md             # Итоги портирования
VERIFICATION_CHECKLIST.md      # Чек-лист верификации
DOCUMENTATION_INDEX.md         # Этот документ
```

### Документы модулей

```
scripts/cli/
  ├── README.md               # API и использование
  ├── INSTALLER_README.md     # Документация установщика
  ├── paths.py                # Управление путями
  ├── config.py               # Управление конфигурацией
  ├── utils.py                # Утилиты
  ├── assist.py               # Главный CLI
  └── installer.py            # Установщик

systemd/
  ├── README.md               # Документация systemd
  ├── install.sh              # Установщик сервисов
  ├── *.service               # systemd service файлы
  └── [тексты сервисов]

.mcp/
  ├── README.md               # Документация MCP
  ├── config_helper.py        # Вспомогательный Module
  └── example_mcp_server.py   # Пример MCP сервера

launchers/
  ├── run.py                  # Главный лончер
  ├── run_unicorn.py          # Unicorn лончер
  ├── run_light_server.py     # Light режим
  └── run_foundry.py          # Foundry лончер
```

## 🎯 Рекомендованный порядок чтения

### Для установки и запуска

1. ✅ [QUICK_START.md](./QUICK_START.md) (5 мин)
2. ✅ [CONFIG.md](./CONFIG.md) (10 мин) — если нужна Configuration
3. ✅ [INSTALL_LINUX.md](./INSTALL_LINUX.md) (15 мин) — если нужна полная инструкция

### Для разработки

1. ✅ [ARCHITECTURE.md](./ARCHITECTURE.md) (20 мин) — понять структуру
2. ✅ [scripts/cli/README.md](./scripts/cli/README.md) (10 мин) — API модулей
3. ✅ [PORTING_SUMMARY.md](./PORTING_SUMMARY.md) (10 мин) — что было сделано

### Для DevOps/SysAdmin

1. ✅ [INSTALL_LINUX.md](./INSTALL_LINUX.md) (15 мин) — установка на Linux
2. ✅ [systemd/README.md](./systemd/README.md) (10 мин) — настройка автозапуска
3. ✅ [VERIFICATION_CHECKLIST.md](./VERIFICATION_CHECKLIST.md) (10 мин) — check

### Для QA

1. ✅ [VERIFICATION_CHECKLIST.md](./VERIFICATION_CHECKLIST.md) (15 мин) — тестирование
2. ✅ [CONFIG.md](./CONFIG.md) (10 мин) — конфигурирование для тестов
3. ✅ [QUICK_START.md](./QUICK_START.md) (5 мин) — командные инструкции

## 🔗 Быстрые ссылки

### По платформам

| Платформа | Инструкции |
|-----------|-----------|
| Windows | [QUICK_START.md#Windows](./QUICK_START.md) → [Установка](./QUICK_START.md#вариант-a-автоматическая-рекомендуется) → `install.cmd` |
| Linux | [INSTALL_LINUX.md](./INSTALL_LINUX.md) → `bash install.sh` → [systemd](./systemd/README.md) |
| macOS | [QUICK_START.md#Linux/macOS](./QUICK_START.md) → [INSTALL_LINUX.md](./INSTALL_LINUX.md) → `bash install.sh` |

### По компонентам

| Компонент | Документация | Исходный код |
|-----------|-------------|-------------|
| CLI (assist) | [scripts/cli/README.md](./scripts/cli/README.md) | `scripts/cli/assist.py` |
| Лончеры (run) | [QUICK_START.md](./QUICK_START.md) | `launchers/run*.py` |
| Установщик | [scripts/cli/INSTALLER_README.md](./scripts/cli/INSTALLER_README.md) | `scripts/cli/installer.py` |
| Configuration | [CONFIG.md](./CONFIG.md) | `scripts/cli/config.py` |
| Пути | [ARCHITECTURE.md](./ARCHITECTURE.md) | `scripts/cli/paths.py` |
| Утилиты | [ARCHITECTURE.md](./ARCHITECTURE.md) | `scripts/cli/utils.py` |
| systemd | [systemd/README.md](./systemd/README.md) | `systemd/*.service` |
| MCP | [.mcp/README.md](./.mcp/README.md) | `.mcp/config_helper.py` |

### По задачам

| Задача | Документ | Раздел |
|--------|----------|--------|
| Установить на Windows | [QUICK_START.md](./QUICK_START.md) | Windows → Вариант A |
| Установить на Linux | [INSTALL_LINUX.md](./INSTALL_LINUX.md) | Шаг 1-6 |
| Запустить сервер | [QUICK_START.md](./QUICK_START.md) | 🎮 Первый запуск |
| Настроить API ключи | [CONFIG.md](./CONFIG.md) | .env файл |
| Включить автозапуск | [systemd/README.md](./systemd/README.md) | Инсталляция |
| Мигрировать конфиг | [MIGRATION_TO_LINUX.md](./MIGRATION_TO_LINUX.md) | Миграция конфигурации |
| Протестировать | [VERIFICATION_CHECKLIST.md](./VERIFICATION_CHECKLIST.md) | Все разделы |

## 📊 Документация по статистике

### Созданные документы

| Документ | Строк | Категория |
|----------|------|----------|
| QUICK_START.md | 250 | Getting Started |
| INSTALL_LINUX.md | 400 | Installation |
| CONFIG.md | 350 | Configuration |
| MIGRATION_TO_LINUX.md | 300 | Migration |
| ARCHITECTURE.md | 500 | Technical |
| PORTING_SUMMARY.md | 350 | Summary |
| VERIFICATION_CHECKLIST.md | 450 | QA/Testing |
| scripts/cli/README.md | 350 | API Reference |
| scripts/cli/INSTALLER_README.md | 250 | Installation Details |
| systemd/README.md | 300 | Linux Services |
| .mcp/README.md | 300 | MCP Servers |
| DOCUMENTATION_INDEX.md | 400 | This document |

**Итого: 4400+ строк документации**

## ✨ Ключевые особенности документации

✅ **Полнота**
- Охватывает все платформы (Windows, Linux, macOS)
- Охватывает все компоненты (CLI, Launchers, Installer, Services)
- От быстрого старта до глубокой архитектуры

✅ **Доступность**
- Для новичков: [QUICK_START.md](./QUICK_START.md)
- Для опытных: [ARCHITECTURE.md](./ARCHITECTURE.md)
- Для каждого уровня что-то свое

✅ **Практичность**
- Examples кода везде
- Пошаговые инструкции
- Решения проблем

✅ **Актуальность**
- Документирует текущее state
- Синхронизирована с кодом
- Обновляется вместе с проектом

## 🔄 Навигация между документами

### Из QUICK_START.md

- 📖 Полная инструкция → [INSTALL_LINUX.md](./INSTALL_LINUX.md)
- ⚙️ Configuration → [CONFIG.md](./CONFIG.md)
- 🏗️ Архитектура → [ARCHITECTURE.md](./ARCHITECTURE.md)
- 📝 Миграция → [MIGRATION_TO_LINUX.md](./MIGRATION_TO_LINUX.md)
- ✅ Check → [VERIFICATION_CHECKLIST.md](./VERIFICATION_CHECKLIST.md)

### Из ARCHITECTURE.md

- 🚀 Быстрый старт → [QUICK_START.md](./QUICK_START.md)
- 📖 Полная инструкция → [INSTALL_LINUX.md](./INSTALL_LINUX.md)
- 💻 Модули → [scripts/cli/README.md](./scripts/cli/README.md)
- 📊 Статистика → [PORTING_SUMMARY.md](./PORTING_SUMMARY.md)

### Из CONFIG.md

- 🚀 Быстрый старт → [QUICK_START.md](./QUICK_START.md)
- 📚 API модулей → [scripts/cli/README.md](./scripts/cli/README.md)
- 🔄 Миграция конфига → [MIGRATION_TO_LINUX.md](./MIGRATION_TO_LINUX.md)

## 💡 Советы для быстрого поиска

1. **Ищете как установить?**
   → [INSTALL_LINUX.md](./INSTALL_LINUX.md) (для Linux) или [QUICK_START.md](./QUICK_START.md) (для всех)

2. **Ищете как использовать?**
   → [QUICK_START.md](./QUICK_START.md) — раздел "📋 Основные команды"

3. **Ищете как конфигурировать?**
   → [CONFIG.md](./CONFIG.md) — раздел "Configuration"

4. **Ищете как это работает?**
   → [ARCHITECTURE.md](./ARCHITECTURE.md) — раздел "📐 Общая архитектура"

5. **Ищете решение проблемы?**
   → [INSTALL_LINUX.md](./INSTALL_LINUX.md) — раздел "Проблемы и решения"

6. **Ищете что портировано?**
   → [PORTING_SUMMARY.md](./PORTING_SUMMARY.md) — раздел "Результаты"

7. **Ищете как протестировать?**
   → [VERIFICATION_CHECKLIST.md](./VERIFICATION_CHECKLIST.md)

## 🆘 Получить помощь

| Проблема | Где искать | Шаги |
|----------|-----------|------|
| Error установки | [INSTALL_LINUX.md](./INSTALL_LINUX.md) | Раздел "Проблемы и решения" |
| Error запуска | [QUICK_START.md](./QUICK_START.md) | Раздел "🐛 Проблемы и решения" |
| Проблема с конфигом | [CONFIG.md](./CONFIG.md) | Раздел "Examples использования" |
| Проблема с systemd | [systemd/README.md](./systemd/README.md) | Раздел "Проблемы и решения" |
| Проблема с кодом | [ARCHITECTURE.md](./ARCHITECTURE.md) | Раздел "Examples использования архитектуры" |

Если помощь не найдена → [GitHub Issues](https://github.com/hypo69/AI-Breadboard/issues)

---

## 📌 Info о документации

- **Последнее update:** 31 Августа 2026
- **Версия проекта:** 1.0 (Портирование завершено на 98%)
- **Платформы:** Windows, Linux, macOS
- **Язык документации:** Русский + Examples на всех языках
- **Формат:** Markdown

---

**🎉 Вся документация готова к использованию!**

Начните с [QUICK_START.md](./QUICK_START.md) и наслаждайтесь работой с AI Breadboard на любой платформе! 🚀
