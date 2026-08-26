# 🚀 Руководство по запуску скриптов для AI моделей

**Цель:** Обеспечить четкий и однозначный запуск скриптов для внутренних инструментов моделями AI

## 📌 Основные принципы

1. **Единая точка входа:** Все скрипты запускаются через `manage_tools.py`
2. **Автоматизация:** Модели ДОЛЖНЫ автоматически запускать скрипты после соответствующих операций
3. **Ясность:** Четкие инструкции и примеры для каждой категории операций
4. **Безопасность:** Правильные параметры и обработка ошибок

## 🎯 Обязательные сценарии автоматического запуска

### Сценарий 1: Файловые операции (переименование, перенос, удаление)
**Когда:** После изменения файловой структуры медиатеки
**Что запускать:**
```bash
# ОБЯЗАТЕЛЬНО
py manage_tools.py db sizes                 # Обновление размеров в БД
py manage_tools.py torrents path            # Синхронизация путей торрентов

# РЕКОМЕНДУЕТСЯ
py manage_tools.py audit media --path "E:"  # Проверка целостности
```

### Сценарий 2: Работа с торрентами
**Когда:** После добавления или изменения торрентов
**Что запускать:**
```bash
# ОБЯЗАТЕЛЬНО
py manage_tools.py torrents assign          # Сопоставление категорий
py manage_tools.py torrents ids --disk "ДИСК 1"  # Привязка торрентов

# ДОПОЛНИТЕЛЬНО
py manage_tools.py torrents state           # Проверка состояния торрентов
```

### Сценарий 3: Изменение структуры БД
**Когда:** После модификации схемы базы данных
**Что запускать:**
```bash
# ОБЯЗАТЕЛЬНО
py manage_tools.py db update                # Миграция схемы БД

# ДЛЯ ПРОВЕРКИ
py manage_tools.py check db                 # Проверка структуры БД
py manage_tools.py check data               # Проверка данных
```

### Сценарий 4: Диагностика проблем
**Когда:** При возникновении проблем с медиатекой
**Что запускать:**
```bash
# БАЗОВАЯ ДИАГНОСТИКА
py manage_tools.py check media_type         # Статистика типов медиа
py manage_tools.py check db                 # Проверка структуры БД

# УГЛУБЛЕННАЯ ПРОВЕРКА
py manage_tools.py audit disk "ДИСК 1"      # Аудит диска
py manage_tools.py audit media              # Аудит медиафайлов
```

## 🔧 Краткий справочник команд `manage_tools.py`

### Команды для медиатеки
```bash
# Сканирование и обновление
py manage_tools.py media scan --disk "диск 2" --path "E:"
py manage_tools.py media complete --disk "ДИСК 1"

# Аудит и проверка
py manage_tools.py media scan --audit --path "E:" "L:" "S:"
```

### Команды для торрентов
```bash
# Сопоставление и управление
py manage_tools.py torrents assign
py manage_tools.py torrents ids --disk "ДИСК 1"
py manage_tools.py torrents path
py manage_tools.py torrents state
py manage_tools.py torrents clear
```

### Команды для БД
```bash
# Обслуживание
py manage_tools.py db update
py manage_tools.py db sizes E: L:
py manage_tools.py db fill --disk "ДИСК 1"

# Диагностика
py manage_tools.py check db
py manage_tools.py check data
py manage_tools.py check media_type
```

## 📋 Примеры комплексного использования

### Пример 1: Полная обработка нового диска
```bash
# 1. Сканирование диска
py manage_tools.py media scan --disk "диск 3" --path "S:"

# 2. Привязка торрентов
py manage_tools.py torrents ids --disk "ДИСК 3"

# 3. Обновление размеров
py manage_tools.py db sizes S:

# 4. Проверка целостности
py manage_tools.py audit disk "ДИСК 3"
```

### Пример 2: Исправление проблем с путями
```bash
# 1. Проверка текущего состояния
py manage_tools.py check media_type
py manage_tools.py check data

# 2. Синхронизация путей
py manage_tools.py torrents path

# 3. Обновление размеров
py manage_tools.py db sizes

# 4. Аудит после исправлений
py manage_tools.py audit media
```

### Пример 3: Ежедневное обслуживание
```bash
# 1. Проверка типов медиа
py manage_tools.py check media_type

# 2. Обновление размеров
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

### Правило 2: Указывай правильные параметры
❌ НЕПРАВИЛЬНО: `py manage_tools.py audit disk`
✅ ПРАВИЛЬНО: `py manage_tools.py audit disk "ДИСК 1"`

### Правило 3: Проверяй результат
После запуска скрипта всегда проверяй:
1. Код возврата (0 = успех)
2. Вывод в консоли
3. Изменения в системе

### Правило 4: Документируй запуски
В своих ответах указывай:
```text
✅ Запущено: py manage_tools.py db sizes
📊 Результат: Обновлены размеры для 124 файлов
```

## 🎓 Интеграция с системными инструкциями

Эти инструкции интегрированы в:
1. `system_instruction.md` (чат) - раздел "Автоматический запуск скриптов"
2. `media_organizer/system_instruction.md` - раздел "Интеграция со скриптами управления"
3. `scripts_tools.md` - раздел 8 "Рекомендации по автоматическому запуску для ИИ-ассистентов"

## 🔍 Быстрая справка

### Как узнать доступные команды?
```bash
py manage_tools.py --help                    # Основная справка
py manage_tools.py media --help              # Справка по медиа
py manage_tools.py torrents --help           # Справка по торрентам
```

### Где найти полную документацию?
- `.ai_instructions/knowledge/scripts_tools.md` - полный справочник
- `.ai_instructions/prompts/chat/system_instruction.md` - инструкция для чата
- `manage_tools.py --help` - встроенная справка

---

**Статус:** Актуально  
**Дата обновления:** 25 июля 2026  
**Для моделей AI:** Используй это руководство для четкого и однозначного запуска скриптов!
