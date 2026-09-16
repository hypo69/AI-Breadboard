# 📦 Архивированные файлы инструкций

**Статус:** Архив (больше не используется)  
**Дата архивирования:** сентябрь 2026

---

## ℹ️ Что здесь?

Эта директория содержит **старые, устаревшие файлы инструкций**, которые были консолидированы в новую структуру.

## 📁 Содержимое

### Из `rules/`
- **CODE_RULES.md** → Консолидировано в [`standards/ENGINEERING.md`](../standards/ENGINEERING.md)
- **DOCS_RULES.md** → Консолидировано в [`standards/DOCUMENTATION.md`](../standards/DOCUMENTATION.md) и [`workflows/TDD.md`](../workflows/TDD.md)
- **REUSE_RULES.md** → Консолидировано в [`standards/REUSE.md`](../standards/REUSE.md)

### Из `knowledge/`
- **tdd_standards.md** → Консолидировано в [`workflows/TDD.md`](../workflows/TDD.md)
- **project_overview.md** → Консолидировано в [`reference/ARCHITECTURE.md`](../reference/ARCHITECTURE.md)

---

## 🔄 Миграция инструкций

### ДО (Old Structure)
```
.ai/instructions/
├── rules/
│   ├── CODE_RULES.md           ← 1164 строк, перегруженный
│   ├── DOCS_RULES.md           ← Дублирует 30% от CODE_RULES
│   └── REUSE_RULES.md          ← Отдельный файл
│
└── knowledge/
    ├── tdd_standards.md        ← Конфликтует с DOCS_RULES
    ├── project_overview.md     ← Большой архитектурный файл
    ├── ... (15+ специфичных файлов)
```

### ПОСЛЕ (New Structure)
```
.ai/instructions/
├── README.md                   ← Главный навигатор
│
├── standards/                  ← Фундаментальные стандарты (без дублирования)
│   ├── ENGINEERING.md          ← Разработка: архитектура, код, стиль
│   ├── DOCUMENTATION.md        ← Документирование: docstrings, README.md
│   └── REUSE.md                ← Prior art audit & zero-divergence
│
├── workflows/                  ← Рабочие процессы
│   ├── TDD.md                  ← 6-шаговый TDD протокол
│   └── INTEGRATION.md          ← 6-этапная интеграция приложений
│
├── reference/                  ← Знание о системе
│   ├── ARCHITECTURE.md         ← Система в целом
│   ├── API_REFERENCE.md        ← Все endpoints
│   ├── CHAT_IMPLEMENTATION.md  ← Как работает UnifiedChatModel
│   ├── PLUGIN_SYSTEM.md        ← Архитектура плагинов
│   └── LEGACY_CONTEXT.md       ← Историческое знание
│
└── guides/                     ← Практические руководства
    ├── INSTALLATION.md         ← Установка
    ├── LAUNCHERS.md            ← Запуск сервисов
    ├── CLI_TOOLS.md            ← CLI инструменты
    └── MODEL_SCRIPTS.md        ← Когда AI запускает скрипты
```

---

## 📊 Статистика консолидации

| Файл | Старый размер | Новое местоположение | Сокращение |
|------|---------------|----------------------|-----------|
| CODE_RULES.md | 1164 строк | ENGINEERING.md + DOCUMENTATION.md + INTEGRATION.md | ✅ Распределено |
| DOCS_RULES.md | 580 строк | DOCUMENTATION.md + TDD.md | ✅ Распределено |
| REUSE_RULES.md | 180 строк | REUSE.md | ✅ Полностью |
| tdd_standards.md | 280 строк | TDD.md | ✅ Полностью |
| project_overview.md | 400 строк | ARCHITECTURE.md | ✅ Полностью |

**Итого:** 2604 строк → Прозрачная, модульная структура ✅

---

## 🔗 Быстрая ссылка на новые файлы

### Нужно быстро найти информацию?

| Ищу | Смотри |
|-----|--------|
| Как кодить | [`../standards/ENGINEERING.md`](../standards/ENGINEERING.md) |
| Как документировать | [`../standards/DOCUMENTATION.md`](../standards/DOCUMENTATION.md) |
| Как переиспользовать код | [`../standards/REUSE.md`](../standards/REUSE.md) |
| Как писать тесты | [`../workflows/TDD.md`](../workflows/TDD.md) |
| Как интегрировать приложение | [`../workflows/INTEGRATION.md`](../workflows/INTEGRATION.md) |
| Архитектура системы | [`../reference/ARCHITECTURE.md`](../reference/ARCHITECTURE.md) |

---

## ⚠️ Используются ли старые файлы?

**НЕТ.** Все старые файлы **больше не используются**. Модели и разработчики должны ссылаться только на новые файлы в соответствующих директориях.

Если вы нашли ссылку на старый файл (например, `rules/CODE_RULES.md`), обновите её на ссылку на новый файл.

---

## 📝 Процесс архивирования

1. ✅ **Аудит:** Проведён аудит всех файлов
2. ✅ **Анализ дублирования:** Выявлено перекрытие содержимого
3. ✅ **Проектирование:** Разработана новая структура
4. ✅ **Миграция:** Все содержимое распределено по новым файлам
5. ✅ **Архивирование:** Старые файлы перемещены сюда
6. ✅ **Верификация:** Новая структура полностью функциональна

---

## 🗑️ Удаление?

Старые файлы могут быть **полностью удалены** после периода, когда все ссылки обновлены (рекомендуется: через 1 месяц, сентябрь 2026).

На данный момент они архивированы для справки и сравнения.

---

**Архивировано:** сентябрь 2026  
**Новая структура активна:** Сентябрь 2026  
**Статус:** ✅ Консолидация завершена
