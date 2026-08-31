# 🚀 Руководство по запуску скриптов для AI моделей

**Цель:** Обеспечить четкий и однозначный запуск скриптов для внутренних инструментов моделями AI

## 📌 Основные принципы

1. **Единая точка входа:** Все скрипты запускаются через `manage_tools.py`
2. **Автоматизация:** Модели ДОЛЖНЫ автоматически запускать скрипты после соответствующих операций
3. **Ясность:** Четкие инструкции и Examples для каждой категории операций
4. **Безопасность:** Правильные Parameters и обработка ошибок

## 🔗 Основная справка

Полный справочник команд, синтаксис и Examples находятся в документе [`scripts_tools.md`](scripts_tools.md):
- **§ 0** — Универсальный CLI `manage_tools.py`
- **§ 1-7** — Все команды и их описание
- **§ 8** — Рекомендации по автоматическому запуску (то, что вы читаете)

**На этой странице мы сосредоточимся на сценариях и best practices для AI моделей.**

---

## 🎯 Обязательные сценарии автоматического запуска

### Сценарий 1: Файловые операции (переименование, перенос, удаление)
**Когда:** После изменения файловой структуры медиатеки
**Что запускать:**
```powershell
# ОБЯЗАТЕЛЬНО
py manage_tools.py db sizes                 # Update размеров в БД
py manage_tools.py torrents path            # Синхронизация путей торрентов

# РЕКОМЕНДУЕТСЯ
py manage_tools.py audit media --path "E:"  # Check целостности
```

### Сценарий 2: Работа с торрентами
**Когда:** После добавления или изменения торрентов
**Что запускать:**
```powershell
# ОБЯЗАТЕЛЬНО
py manage_tools.py torrents assign          # Сопоставление категорий
py manage_tools.py torrents ids --disk "ДИСК 1"  # Привязка торрентов

# ДОПОЛНИТЕЛЬНО
py manage_tools.py torrents state           # Check состояния торрентов
```

### Сценарий 3: Изменение структуры БД
**Когда:** После модификации схемы базы данных
**Что запускать:**
```powershell
# ОБЯЗАТЕЛЬНО
py manage_tools.py db update                # Миграция схемы БД

# ДЛЯ ПРОВЕРКИ
py manage_tools.py check db                 # Check структуры БД
py manage_tools.py check data               # Check данных
```

### Сценарий 4: Диагностика проблем
**Когда:** При возникновении проблем с медиатекой
**Что запускать:**
```powershell
# БАЗОВАЯ ДИАГНОСТИКА
py manage_tools.py check media_type         # Статистика типов медиа
py manage_tools.py check db                 # Check структуры БД

# УГЛУБЛЕННАЯ ПРОВЕРКА
py manage_tools.py audit disk "ДИСК 1"      # Аудит диска
py manage_tools.py audit media              # Аудит медиафайлов
```

---

## 🧠 Когда AI модель должна автоматически запускать скрипты

### ✅ ДОЛЖНА запустить (MUST)
- После любого переименования, перемещения или удаления медиафайлов: `py manage_tools.py db sizes`
- После изменения пути хранения торрентов: `py manage_tools.py torrents path`
- После модификации схемы БД в коде: `py manage_tools.py db update`

### ✅ РЕКОМЕНДУЕТСЯ запустить (SHOULD)
- После добавления новых торрентов: `py manage_tools.py torrents assign`
- После привязки медиатеки к торрентам: `py manage_tools.py torrents ids`
- При решении проблем: `py manage_tools.py check data`

### ❌ НЕ ДОЛЖНА запускать без явного указания пользователя
- Команды с флагом `--yes` (автоматические действия требуют подтверждения)
- Командыс флагом `--auto-fix` (исправления требуют явного согласия)
- `torrents orchestrator` (комплексная операция)

---

## 📝 Best Practices для AI моделей

### 1. Контекст перед скриптом
Перед запуском скрипта сообщите пользователю, что вы делаете:
```
Я вижу, что вы изменили структуру медиатеки. 
Сейчас я обновлю размеры файлов в БД командой:
py manage_tools.py db sizes
```

### 2. Цепочка скриптов
Если требуется несколько команд, выполняйте их последовательно:
```powershell
# Сначала: update размеров
py manage_tools.py db sizes E: L:

# Потом: синхронизация путей
py manage_tools.py torrents path

# Наконец: check целостности (если нужна)
py manage_tools.py audit media --path "E:"
```

### 3. Check результата
После каждого скрипта проверьте вывод и убедитесь, что операция прошла successfully:
```powershell
# Выполнить команду
py manage_tools.py db sizes

# Проверить результат
py manage_tools.py check data
```

### 4. Обработка ошибок
Если скрипт завершился с ошибкой, выведите лог и предложите решение:
```
❌ Error при выполнении: py manage_tools.py db sizes
Сообщение: Database locked
Решение: Убедитесь, что БД не открыта в другом процессе или закройте все приложения, работающие с media.db
```

---

## 🔗 Дополнительные ссылки

- **Полный справочник:** [`scripts_tools.md`](scripts_tools.md)
- **Стандарты кода:** [`../../rules/CODE_RULES.md`](../../rules/CODE_RULES.md)
- **Configuration проекта:** [`INSTALLATION_GUIDE.md`](INSTALLATION_GUIDE.md) § 4

---

**Status:** ✅ Актуальна на август 2026  
**Версия:** 2.0  
**Последнее update:** 2026-08-24
```bash
# 1. Сканирование диска
py manage_tools.py media scan --disk "диск 3" --path "S:"

# 2. Привязка торрентов
py manage_tools.py torrents ids --disk "ДИСК 3"

# 3. Update размеров
py manage_tools.py db sizes S:

# 4. Check целостности
py manage_tools.py audit disk "ДИСК 3"
```

### Пример 2: Исправление проблем с путями
```bash
# 1. Check текущего состояния
py manage_tools.py check media_type
py manage_tools.py check data

# 2. Синхронизация путей
py manage_tools.py torrents path

# 3. Update размеров
py manage_tools.py db sizes

# 4. Аудит после исправлений
py manage_tools.py audit media
```

### Пример 3: Ежедневное обслуживание
```bash
# 1. Check типов медиа
py manage_tools.py check media_type

# 2. Update размеров
py manage_tools.py db sizes

# 3. Синхронизация торрентов
py manage_tools.py torrents assign
py manage_tools.py torrents path

# 4. Быстрый аудит
py manage_tools.py audit media
```

## ⚠️ Важные правила

### Правило 1: Всегда используй `manage_tools.py`
❌ НЕПРАВИЛЬНО: `python update_db.py`
✅ ПРАВИЛЬНО: `py manage_tools.py db update`

### Правило 2: Указывай правильные Parameters
❌ НЕПРАВИЛЬНО: `py manage_tools.py audit disk`
✅ ПРАВИЛЬНО: `py manage_tools.py audit disk "ДИСК 1"`

### Правило 3: Проверяй результат
После запуска скрипта всегда проверяй:
1. Код возврата (0 = success)
2. Вывод в консоли
3. Изменения в системе

### Правило 4: Документируй запуски
В своих ответах указывай:
```text
✅ Запущено: py manage_tools.py db sizes
📊 Результат: Обновлены размеры для 124 файлов
```

## 🎓 Integration с системными инструкциями

Эти инструкции интегрированы в:
1. `system_instruction.md` (чат) - раздел "Автоматический запуск скриптов"
2. `media_organizer/system_instruction.md` - раздел "Integration со скриптами управления"
3. `scripts_tools.md` - раздел 8 "Рекомендации по автоматическому запуску для ИИ-ассистентов"

## 🔍 Быстрая справка

### Как узнать доступные команды?
```bash
py manage_tools.py --help                    # Основная справка
py manage_tools.py media --help              # Справка по медиа
py manage_tools.py torrents --help           # Справка по торрентам
```

### Где найти полную документацию?
- `.ai_instructions/knowledge/scripts_tools.md` — полный справочник скриптов
- `.ai_instructions/knowledge/LAUNCHER_GUIDE.md` — правила лончеров (Run-*.ps1)
- `manage_tools.py --help` — встроенная справка CLI

---

## 🗂️ Инструменты ИИ (tools/ai/)

Скрипты для работы агентов с RAG-индексами и кодовой базой.  
Путь от корня проекта `C:\ai-assistant`:

```bash
# Пересборка RAG-индекса кода (после изменений в core/)
py tools/ai/rebuild_dev_rag.py

# Пересборка RAG медиатеки
py tools/ai/rebuild_rag.py

# Поиск по кодовой базе
py tools/ai/search_code.py --query "MediaDatabase"

# Update документации
py tools/ai/update_docs.py

# Validation RAG-файлов
py tools/ai/validate_rag_files.py

# Упаковка навыка
py tools/ai/package_skill.py <skill_name>
```

## 🚀 Запуск лончеров агентами ИИ

```powershell
# Все лончеры — в корне C:\ai-assistant\
& "C:\ai-assistant\run.ps1"                         # Запуск всего
& "C:\ai-assistant\Run-Unicorn.ps1"                 # Только FastAPI
& "C:\ai-assistant\Run-Foundry.ps1" -Action start   # Foundry AI
& "C:\ai-assistant\Run-Foundry.ps1" -Action stop
& "C:\ai-assistant\Run-Foundry.ps1" -Action status

# Проверить что FastAPI запущен
Invoke-WebRequest -Uri "https://localhost:3000/health" -SkipCertificateCheck
```

---

**Status:** Актуально  
**Дата обновления:** 24 августа 2026  
**Для моделей AI:** Используй это руководство для чёткого и однозначного запуска скриптов!
