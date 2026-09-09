---
name: skill-factory
description: Tool for creating, packaging, and managing the lifecycle of AI Breadboard and Gemini CLI skills. Use for initializing new skills and automated builds in .agents/skills/.
description_i18n:
  en: Tool for creating, packaging, and managing the lifecycle of AI Breadboard and Gemini CLI skills. Use for initializing new skills and automated builds in .agents/skills/.
  ru: Инструмент для создания, упаковки и управления жизненным циклом навыков AI Breadboard и Gemini CLI. Используйте для инициализации новых навыков и автоматической сборки существующих в .agents/skills/.
---

# 🏭 Skill Factory

Этот навык управляет жизненным циклом навыков для AI Breadboard, Gemini CLI и Antigravity.

---

## 📂 Стандарт размещения навыков

Все навыки проекта **MUST** располагаться исключительно в директории:
```text
.agents/skills/<skill-name>/
```

### 📁 Обязательная структура любого навыка:
```text
.agents/skills/<skill-name>/
├── SKILL.md                 # Обязательно: frontmatter (name, description, description_i18n) + инструкции
├── README.md                # Обязательно: англоязычная документация пакета
├── scripts/                 # (Опционально) Исполняемые утилиты и хелперы
├── references/              # (Опционально) Справочные markdown файлы, гайды, примеры
├── assets/                  # (Опционально) Статические ресурсы, шаблоны
└── dist/                    # Каталог скомпилированного .skill архива (генерируется)
```

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
  es: Descripción clara del rol y disparadores del skill en español.
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
Автоматически создаёт правильную файловую структуру в `.agents/skills/` с поддержкой i18n:

```bash
# Инициализация навыка с двуязычным описанием:
python .agents/skills/skill-factory/scripts/init_skill.py network-monitor --description-en "Network and port monitoring toolkit" --description-ru "Мониторинг сети и портов"

# Или с общим описанием (автоматически определит язык):
python .agents/skills/skill-factory/scripts/init_skill.py network-monitor --description "Network and port monitoring toolkit"
```

### 2. Упаковка навыка (`pack.py`)
Собирает директорию навыка в архив `.skill` внутри папки `dist/`:

```bash
# По имени навыка:
python .agents/skills/skill-factory/scripts/pack.py <имя-навыка>

# Или по пути к директории:
python .agents/skills/skill-factory/scripts/pack.py .agents/skills/<имя-навыка>
```

---

## ⚙️ Правила и ограничения

1. **Никаких устаревших путей:** Запрещено использовать `.gemini/skills/` — все навыки размещаются строго в `.agents/skills/`.
2. **Динамические пути в скриптах:** Все скрипты навыка должны вычислять пути относительно `Path(__file__).resolve()`.
3. **Англоязычный код:** Любой код, тесты и docstrings внутри `scripts/` пишутся строго на английском языке в соответствии с `CODE_RULES.md`.
