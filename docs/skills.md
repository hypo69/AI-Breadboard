# Руководство по Skills в Gemini CLI

## 📋 Введение
Навыки (Skills) в Gemini CLI — это модульные пакеты, расширяющие возможности ассистента за счет специализированного экспертного знания, рабочих процессов и инструментов автоматизации для проекта `ai-assistant`.

## 🛠️ Существующие навыки

В проекте установлены и активны следующие навыки:

| Название навыка | Назначение | Основные команды |
| :--- | :--- | :--- |
| **`media-manager`** | Организация медиатеки, аудит, классификация | `python run_media_organizer.py`, `python audit_media.py` |
| **`torrent-controller`**| Управление qBittorrent, синхронизация, проверка | `python assign_torrents_ids.py`, `python update_torrent_state.py` |
| **`db-inspector`** | Работа с SQLite БД, анализ данных, отладка | `python get_schema.py`, `python check_db.py`, `python inspect_user_rags.py` |
| **`storage-tool`** | Аудит дисков, мониторинг размеров | `python audit_disk.py`, `python update_media_sizes.py`, `python view_storage.py` |

Каждый навык содержит файл `SKILL.md` с подробным описанием логики и быстрым стартом.

## 📝 Инструкция по созданию новых навыков

Для создания новых навыков используется встроенный в Gemini CLI инструмент `skill-creator`.

### 1. Подготовка
Убедитесь, что у вас установлен `node` и доступ к системным инструментам `skill-creator`.

### 2. Процесс создания
1.  **Инициализация:**
    Выполните команду для создания структуры:
    ```bash
    node <path-to-skill-creator>/scripts/init_skill.cjs <skill-name> --path ./skills/<skill-name>
    ```
2.  **Редактирование:**
    - Отредактируйте `SKILL.md`: заполните YAML frontmatter (`name`, `description`) и Markdown-инструкции.
    - Добавьте необходимые скрипты в папку `scripts/` (обязательно протестируйте их работоспособность).
    - Разместите справочные материалы в `references/`.
    - Добавьте шаблоны в `assets/`.
3.  **Валидация и упаковка:**
    Упакуйте навык в файл `.skill`:
    ```bash
    node <path-to-skill-creator>/scripts/package_skill.cjs ./skills/<skill-name> ./dist
    ```
    *Примечание: Если возникнут ошибки при автоматической упаковке, можно упаковать папку вручную через `Compress-Archive` в PowerShell.*

### 3. Установка
После получения `.skill` файла установите его:
```bash
gemini skills install ./dist/<skill-name>.skill --scope workspace
/skills reload
```

## 🏗️ Принципы проектирования
- **Минимализм:** Включайте только то, что действительно нужно для работы (избегайте лишней документации).
- **Связность:** Навык должен решать одну четко определенную задачу или группу связанных задач.
- **Интерактивность:** ИИ должен понимать, *когда* применять навык, основываясь на описании в YAML.

## 🌐 Универсальный реестр навыков

Для совместного использования навыков разными моделями и агентами применяется `core.skills.SkillRegistry`.
Он поддерживает каталоги `.gemini/skills`, `.agents/skills`, `.github/skills` и `skills`, поэтому исходный `SKILL.md` не нужно дублировать для каждого провайдера.

### Единый CLI

```powershell
python manage_tools.py skills list
python manage_tools.py skills search медиатека
python manage_tools.py skills show media-manager
python manage_tools.py skills export media-manager
python manage_tools.py skills export media-manager --without-instructions
```

`show` возвращает инструкции для добавления в системный промпт. `export` возвращает переносимый JSON-контракт, который можно передать внешнему агенту или преобразовать в формат конкретного SDK.

### Машинный контракт

В папке навыка можно разместить необязательный `skill.json`:

```json
{
    "name": "media-manager",
    "description": "Управление медиатекой",
    "providers": ["gemini", "ollama", "foundry"],
    "capabilities": ["filesystem", "database"]
}
```

`SKILL.md` остаётся человекочитаемым источником инструкций, а `skill.json` описывает метаданные для маршрутизации. Реестр ничего не запускает автоматически: выполнение скриптов должно быть отдельным явно разрешённым шагом агента.
