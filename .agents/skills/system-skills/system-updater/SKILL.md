---
name: system-updater
description: Update checker, backup creator, and safe updater for AI Breadboard to latest version with automated database migrations.
description_i18n:
  en: Update checker, backup creator, and safe updater for AI Breadboard to latest version with automated database migrations.
  ru: Проверка наличия обновлений, создание резервных копий, скачивание и безопасное обновление AI Breadboard до последней версии с автоматическим наездом миграций БД.
---

# 🔄 System Updater Skill

Навык для проверки версий, создания резервных копий, скачивания и безопасного обновления кодовой базы AI Breadboard до последней стабильной версии с автоматическим наездом миграций баз данных SQLite.

---

## 🎯 Назначение и триггеры

Используйте этот навык, когда:
- Пользователь просит обновить проект или систему до последней версии ("обновись", "проверь обновления", "подтяни свежий код").
- Необходимо проверить актуальность текущей версии и коммитов по сравнению с удаленным репозиторием (GitHub).
- Требуется накатить миграции базы данных после изменения структуры таблиц или после `git pull`.
- Требуется создать снимок состояния проекта (backup) перед критическими изменениями.

---

## 🚀 Протокол выполнения (Шаги)

### Шаг 1 — Проверка версии и обновлений
Выполните проверку доступности новых тегов или коммитов в удаленном репозитории:
```bash
python .agents/skills/system-updater/scripts/update.py --check
```
Или через единый CLI:
```bash
python manage_tools.py db status
```

### Шаг 2 — Создание резервной копии и накат обновления
Если обновления доступны и пользователь запросил обновление:
```bash
python .agents/skills/system-updater/scripts/update.py --apply --branch main
```

Процесс обновления автоматически выполняет:
1. Создание резервной копии основных файлов (`config.json`, `.env`, `src/`, `requirements.txt`).
2. `git fetch origin` и `git merge origin/<branch>`.
3. Автоматический запуск менеджера миграций БД (`MigrationManager.apply_all_pending()`).
4. В случае сбоя слияния или миграций — автоматический откат из бэкапа.

### Шаг 3 — Проверка и применение миграций баз данных
Для проверки и отдельного наката миграций схем БД SQLite:
```bash
# Проверка статуса миграций
py manage_tools.py db status

# Накат всех ожидающих миграций
py manage_tools.py db migrate

# Создание новой миграции
py manage_tools.py db create <db_name> <migration_name>
```

---

## 🛠️ Скрипты и команды

- `scripts/update.py --check`: Проверка наличия новой версии в Git.
- `scripts/update.py --apply`: Полный цикл обновления с созданием бэкапа и миграциями.
- `scripts/update.py --status-db`: Проверка статуса миграций SQLite.
- `manage_tools.py db migrate`: Применение всех ожидающих миграций БД.
- `manage_tools.py db status`: Просмотр примененных и ожидающих миграций.
