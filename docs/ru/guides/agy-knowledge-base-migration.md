# Руководство по переносу базы знаний и сессий (Brain Storage Migration)

> **Цель:** Перенос накопленной базы знаний, планов реализации, артефактов и сессий из глобального хранилища Antigravity (`~/.gemini/antigravity/brain/`) внутрь проекта для обеспечения полной компьютеронезависимости и переносимости между устройствами.

---

## 📋 Содержание

1. [Проблема привязки к машине](#1-проблема-привязки-к-машине)
2. [Архитектура и структура хранения внутри проекта](#2-архитектура-и-структура-хранения-внутри-проекта)
3. [Пошаговый процесс миграции](#3-пошаговый-процесс-миграции)
4. [Автоматизация переноса с помощью Python](#4-автоматизация-переноса-с-помощью-python)
5. [Как агент считывает знания на новом компьютере](#5-как-агент-считывает-знания-на-новом-компьютере)
6. [Рекомендации по поддержанию независимости](#6-рекомендации-по-поддержанию-независимости)

---

## 1. Проблема привязки к машине

По умолчанию среда **Antigravity** сохраняет промежуточные состояния диалогов и сессионные артефакты в пользовательском каталоге операционной системы:
- **Windows:** `C:\Users\<username>\.gemini\antigravity\brain\<conversation-id>\`
- **Linux / macOS:** `~/.gemini/antigravity/brain/<conversation-id>/`

Внутри каждой папки сессии хранятся:
- `implementation_plan.md` — детальные планы изменений и архитектурные решения.
- `walkthrough.md` — результаты выполнения задач и отчеты о проделанной работе.
- `scratch/` — вспомогательные скрипты и тестовые сниппеты.
- `.system_generated/logs/transcript.jsonl` — полная стенограмма сообщений и рассуждений модели.

**Недостатки хранения в системной папке:**
- ❌ **Нет переносимости:** При клонировании репозитория на другой ПК или смене пользователя (`username`) история и контекст теряются.
- ❌ **Вне контроля версий:** Изменения не попадают в Git.
- ❌ **Изоляция сессий:** Новый запуск агента в другой сессии не видит наработок из предыдущих папок UUID.

---

## 2. Архитектура и структура хранения внутри проекта

Для обеспечения **100% автономности** база знаний и накопленные решения должны быть организованы внутри репозитория:

```text
AI-Breadboard/
├── GEMINI.md                    # Главная точка входа (Master Index правил и базы знаний)
├── AGENTS.md                    # (Опционально) Инструкции и роли агентов
│
├── .agents/                     # Компьютеронезависимые расширения
│   ├── skills/                  # Локальные навыки и скрипты проекта
│   └── rules/                   # Модульные правила
│
├── .ai/                         # Системная база знаний
│   └── instructions/
│       ├── rules/               # CODE_RULES.md, DOCS_RULES.md, REUSE_RULES.md
│       └── knowledge/           # Архитектура, описания системных модулей
│
└── docs/
    └── brain/                   # 🧠 Накопленная история и артефакты проекта
        ├── plans/               # Перенесенные планы (implementation_plan.md)
        ├── walkthroughs/        # Отчеты и результаты внедрения (walkthrough.md)
        └── sessions/            # Ключевые выжимки сессий
```

---

## 3. Пошаговый процесс миграции

### Шаг 1: Создание структуры каталогов
Создайте каталог для хранения проектной памяти:
```powershell
New-Item -ItemType Directory -Force -Path "docs/brain/plans", "docs/brain/walkthroughs", "docs/brain/sessions"
```

### Шаг 2: Извлечение ценных данных
Скопируйте `implementation_plan.md` и `walkthrough.md` из папок `brain/<id>/` в проект, присвоив им информативные имена:
- `docs/brain/plans/2026-09-02-auth-subsystem.md`
- `docs/brain/walkthroughs/2026-09-02-auth-subsystem-walkthrough.md`

### Шаг 3: Фиксация в `GEMINI.md`
Добавьте раздел в `GEMINI.md`, чтобы агент при старте всегда видел ссылки на историю решений:
```markdown
## 🧠 Project Knowledge & Decision History
- **Implementation Plans:** `docs/brain/plans/`
- **Walkthroughs & Reports:** `docs/brain/walkthroughs/`
- **Architecture Knowledge:** `.ai/instructions/knowledge/`
```

---

## 4. Автоматизация переноса с помощью Python

Для автоматического сканирования системного хранилища и переноса артефактов в проект можно использовать следующий скрипт:

```python
"""
Скрипт для экспорта артефактов из системного хранилища Antigravity в проект.
"""
import os
import shutil
from pathlib import Path
from datetime import datetime

USER_HOME = Path.home()
BRAIN_DIR = USER_HOME / ".gemini" / "antigravity" / "brain"
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # AI-Breadboard
TARGET_DIR = PROJECT_ROOT / "docs" / "brain"

def export_brain_artifacts():
    if not BRAIN_DIR.exists():
        print(f"[!] Системная папка {BRAIN_DIR} не найдена.")
        return

    plans_target = TARGET_DIR / "plans"
    walkthroughs_target = TARGET_DIR / "walkthroughs"
    plans_target.mkdir(parents=True, exist_ok=True)
    walkthroughs_target.mkdir(parents=True, exist_ok=True)

    count = 0
    for session_folder in BRAIN_DIR.iterdir():
        if not session_folder.is_dir():
            continue

        session_id = session_folder.name
        mod_time = datetime.fromtimestamp(session_folder.stat().st_mtime).strftime("%Y%m%d_%H%M%S")

        # Копирование implementation_plan.md
        plan_file = session_folder / "implementation_plan.md"
        if plan_file.exists() and plan_file.stat().st_size > 50:
            target_file = plans_target / f"{mod_time}_{session_id[:8]}_plan.md"
            shutil.copy2(plan_file, target_file)
            count += 1

        # Копирование walkthrough.md
        walkthrough_file = session_folder / "walkthrough.md"
        if walkthrough_file.exists() and walkthrough_file.stat().st_size > 50:
            target_file = walkthroughs_target / f"{mod_time}_{session_id[:8]}_walkthrough.md"
            shutil.copy2(walkthrough_file, target_file)
            count += 1

    print(f"[+] Успешно экспортировано {count} артефактов в {TARGET_DIR}")

if __name__ == "__main__":
    export_brain_artifacts()
```

---

## 5. Как агент считывает знания на новом компьютере

После миграции и отправки изменений в Git (`git commit` & `git push`):

1. **Автоматическая загрузка:** При открытии проекта на любом компьютере агент первым делом читает `GEMINI.md`.
2. **Относительные пути:** Поскольку все ссылки ведут на `docs/` и `.ai/instructions/`, агент обращается к локальным файлам репозитория независимо от пути установки (`C:\Users\...`, `D:\Projects\...`, `/home/...`).
3. **Локальные скиллы:** Скиллы из `.agents/skills/` активируются автоматически без необходимости глобальной настройки.

---

## 6. Рекомендации по поддержанию независимости

1. **Используйте команду `/learn`:** Если в процессе работы было найдено важное архитектурное решение, зафиксируйте его в `.ai/instructions/knowledge/` или `docs/`.
2. **Не храните уникальные правила в глобальном `~/.gemini/config`:** Все требования к коду и стилю должны быть в [`.ai/instructions/rules/`](../../../.ai/instructions/rules/).
3. **Включайте документацию в коммиты:** Всегда коммитьте обновленные `docs/` и `.ai/instructions/` вместе с функциональным кодом.
