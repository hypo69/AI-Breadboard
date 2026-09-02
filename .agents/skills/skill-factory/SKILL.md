---
name: skill-factory
description: Инструмент для создания, упаковки и управления жизненным циклом навыков AI Breadboard и Gemini CLI. Используйте для инициализации новых навыков и автоматической сборки существующих в .agents/skills/.
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
├── SKILL.md                 # Обязательно: frontmatter (name, description) + инструкции
├── README.md                # Обязательно: англоязычная документация пакета
├── scripts/                 # (Опционально) Исполняемые утилиты и хелперы
├── references/              # (Опционально) Справочные markdown файлы, гайды, примеры
├── assets/                  # (Опционально) Статические ресурсы, шаблоны
└── dist/                    # Каталог скомпилированного .skill архива (генерируется)
```

---

## 📝 Требования к `SKILL.md`

Каждый `SKILL.md` обязан начинаться с YAML Frontmatter:

```markdown
---
name: my-new-skill
description: Четкое описание роли и триггеров вызова навыка на русском или английском.
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
Автоматически создаёт правильную файловую структуру в `.agents/skills/`:

```bash
# Инициализация навыка
python .agents/skills/skill-factory/scripts/init_skill.py <имя-навыка> --description "Краткое описание"

# Пример:
python .agents/skills/skill-factory/scripts/init_skill.py network-monitor --description "Мониторинг сети и портов"
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
