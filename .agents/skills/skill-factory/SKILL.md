---
name: skill-factory
description: Tool and guide for creating, packaging, and managing the lifecycle of AI Breadboard and Gemini CLI skills. Use for initializing new skills, guidelines for creating effective skills, and automated builds in skills/.
description_i18n:
  en: Tool and guide for creating, packaging, and managing the lifecycle of AI Breadboard and Gemini CLI skills. Use for initializing new skills, guidelines for creating effective skills, and automated builds in skills/.
  ru: Инструмент и руководство по созданию, упаковке и управлению жизненным циклом навыков AI Breadboard и Gemini CLI. Используйте для инициализации новых навыков, создания эффективных манифестов и автоматической сборки в skills/.
---

# 🏭 Skill Factory & Creator

Этот навык управляет жизненным циклом навыков для AI Breadboard, Gemini CLI и Antigravity, а также содержит полное руководство по проектированию и созданию эффективных навыков.

---

## 📂 Стандарт размещения навыков

Все навыки проекта **MUST** располагаться исключительно в директории:
```text
skills/<skill-name>/
```

### 📁 Обязательная структура любого навыка:
```text
skills/<skill-name>/
├── SKILL.md                 # Обязательно: frontmatter (name, description, description_i18n) + инструкции
├── README.md                # Обязательно: англоязычная документация пакета
├── scripts/                 # (Опционально) Исполняемые утилиты и хелперы
├── references/              # (Опционально) Справочные markdown файлы, гайды, примеры
├── assets/                  # (Опционально) Статические ресурсы, шаблоны
└── dist/                    # Каталог скомпилированного .skill архива (генерируется)
```

---

## 💡 Руководство по созданию эффективных навыков (Best Practices)

При разработке нового навыка руководствуйтесь следующими принципами:
1. **Четкие триггеры и описание:** Поле `description` и блок `description_i18n` должны однозначно описывать, когда и для каких задач следует активировать навык.
2. **Прогрессивное раскрытие контекста:** Помещайте основные инструкции в `SKILL.md`, а детальные справочники, большие примеры и документацию — в поддиректорию `references/`.
3. **Автономность скриптов:** Любые вспомогательные скрипты в `scripts/` должны использовать относительные пути от `Path(__file__).resolve()` и быть полностью самодостаточными.
4. **Строгая типизация и качество кода:** Пишите код на Python строго по стандартам проекта (PEP 8, docstrings на русском языке для кода общего назначения или на английском для скриптов инфраструктуры навыков).

---

## 📝 Требования к `SKILL.md` и Мультиязычности (i18n)

Каждый `SKILL.md` обязан начинаться с YAML Frontmatter, содержащего каноническое описание на английском языке (`description`) и блок локализаций (`description_i18n`):

```markdown
---
name: my-new-skill
description: Clear English description of skill role and activation triggers.
description_i18n:
  en: Clear English description of skill role and activation triggers.
  ru: Четкое описание роли и триггеров вызова навыка на русском языке.
---

# Название навыка

## 🎯 Назначение
...

## 🚀 Протокол выполнения (Шаги)
...

## 🛠️ Скрипты и команды
...
```

---

## 🛠️ Доступные утилиты

### 1. Инициализация нового навыка (`init_skill.py`)
Автоматически создаёт правильную файловую структуру в `skills/` с поддержкой i18n:

```bash
# Инициализация навыка с двуязычным описанием:
python skills/skill-factory/scripts/init_skill.py network-monitor --description-en "Network and port monitoring toolkit" --description-ru "Мониторинг сети и портов"

# Или с общим описанием (автоматически определит язык):
python skills/skill-factory/scripts/init_skill.py network-monitor --description "Network and port monitoring toolkit"
```

### 2. Упаковка навыка (`pack.py`)
Собирает директорию навыка в архив `.skill` внутри папки `dist/`:

```bash
# По имени навыка:
python skills/skill-factory/scripts/pack.py <имя-навыка>

# Или по пути к директории:
python skills/skill-factory/scripts/pack.py skills/<имя-навыка>
```

---

## ⚙️ Правила и ограничения

1. **Никаких устаревших путей:** Запрещено использовать `.gemini/skills/` — все навыки размещаются строго в `skills/`.
2. **Динамические пути в скриптах:** Все скрипты навыка должны вычислять пути относительно `Path(__file__).resolve()`.
3. **Англоязычный код:** Любой код, тесты и docstrings внутри `scripts/` пишутся строго в соответствии с стандартами проекта.
