# `src/skills` — Реестр навыков

## Что это за модуль?

`src/skills` — центральное хранилище **навыков (skills)**, которые используются в AI‑Breadboard. Каждый навык представляет собой набор инструкций, описанных в файле `SKILL.md`, и может быть динамически загружен агентами, приложениями и другими компонентами системы.

## Зачем он нужен?

- **Повторное использование**: навыки инкапсулируют типичные действия (работа с API, генерация кода, обработка текста и т.д.) и могут использоваться в разных частях проекта без дублирования кода.
- **Модульность**: каждый навык изолирован в собственном подкаталоге, имеет собственные метаданные и инструкции.
- **Автоматическое обнаружение**: `SkillRegistry` сканирует каталоги, ищет `SKILL.md` и регистрирует навыки, делая их доступными через единый API.

## Как настроить?

1. **Создайте навык** – в подкаталоге `src/skills` разместите директорию с файлом `SKILL.md` (шаблон находится в `.skills/`).
2. **Определите пути поиска** – файл `src/skills/config.json` задаёт, где искать навыки:

```json
{
  "search_paths": ["./src/skills"],
  "include": [],
  "exclude": []
}
```

- `search_paths` – список каталогов, сканируемых регистратором.
- `include` / `exclude` – явные списки включаемых и исключаемых имен навыков (по желанию).

3. **Регистрация** – при запуске приложения `SkillRegistry(project_root=__root__)` автоматически подхватит конфигурацию:

```python
from src.skills.registry import SkillRegistry
registry = SkillRegistry()
skills = registry.discover()
```

4. **Дополнительная настройка** – при необходимости добавьте новые директории или ограничения, отредактировав `config.json` и перезапустив процесс, использующий `SkillRegistry`.

## Полезные команды

- Показать доступные навыки:

```powershell
py manage_tools.py skills list
```

- Обновить конфигурацию – отредактируйте `src/skills/config.json` и перезапустите процесс.

---

> **Важно**: Все новые навыки должны соответствовать формату `hypo69 docblock` – комментарии и docstrings пишутся на русском, имена функций/классов остаются на английском.

## Overview
The `core.skills` package provides a unified registry for discovering, inspecting, and managing skills across AI models, agents, and IDE tools.

---

## How It Works

1. `SkillRegistry` automatically scans skill directories in:
   - `.gemini/skills/`
   - `skills/`
   - `.github/skills/`
   - `skills/`
2. Each valid skill folder must contain a `SKILL.md` file with YAML frontmatter.
3. An optional `skill.json` file defines the machine contract: providers, capabilities, parameters, and tool interfaces.
4. The registry loads skill metadata and instructions into memory safely. Execution of skill scripts remains an explicit, isolated operation.

---

## Module Files

- `registry.py`: `SkillDefinition` data model, discovery engine, search filters, and JSON serialization.
- `__init__.py`: Public package exports and singleton accessors.

---

## Usage

```python
from core.skills import get_skill_registry

registry = get_skill_registry()
all_skills = registry.list_skills()

# Find skill by capability or name
skill = registry.get_skill("file-saver")
if skill:
    print(f"Loaded skill: {skill.name} - {skill.description}")
```
