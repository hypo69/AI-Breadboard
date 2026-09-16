# 🤖 Когда AI модели запускают скрипты

**Статус:** ✅ Reference  
**Версия:** 1.0  
**Последнее обновление:** сентябрь 2026

---

## 1. Принцип работы

AI модели могут автоматически запускать скрипты и инструменты при определённых условиях.

### Когда это разрешено

✅ **РАЗРЕШЕНО запускать скрипты:**
- Обработка и трансформация данных
- Запуск тестов
- Генерация документации
- Вызов внешних API
- Системные диагностические команды

### Когда это ЗАПРЕЩЕНО

❌ **ЗАПРЕЩЕНО запускать скрипты:**
- Модификация конфигурации продакшена без подтверждения пользователя
- Удаление важных файлов (особенно `.env`, `config.json`)
- Система-wide изменения (изменение PATH, установка глобальных пакетов)
- Доступ к чувствительным данным без явного разрешения

---

## 2. Конфигурация автоматического запуска

### В `.env`

```env
# Разрешить AI моделям автоматически запускать скрипты
AI_AUTO_SCRIPTS_ENABLED=true

# Максимальное время выполнения скрипта (секунды)
AI_SCRIPT_TIMEOUT=30

# Разрешённые скрипты (через запятую)
AI_ALLOWED_SCRIPTS=tests,docs,build,lint
```

### В `config.json`

```json
{
  "ai_scripts": {
    "auto_execute": true,
    "timeout": 30,
    "allowed": ["tests", "docs", "build", "lint"],
    "blocked": ["delete", "modify_config", "deploy"]
  }
}
```

---

## 3. Примеры использования

### Запуск тестов

```python
# Модель автоматически запускает тесты после изменения кода
if code_changed:
    result = model.run_script('pytest tests/ -v')
    if result.returncode != 0:
        model.suggest_fixes(result.stderr)
```

### Генерация документации

```python
# После добавления новой функции, модель генерирует README
def new_feature():
    # ... реализация ...
    pass

model.run_script('python manage_tools.py --docs generate')
```

### Валидация

```python
# Перед коммитом, модель проверяет лinting и type hints
model.run_script('pylint src/')
model.run_script('mypy src/')
```

---

## 4. Контроль выполнения

### Требовать подтверждение

```python
# Модель просит подтверждение перед запуском опасного скрипта
if script in dangerous_scripts:
    await model.request_user_confirmation(
        f"Модель хочет запустить: {script}. Разрешить?"
    )
```

### Логирование

```python
# Все запуски логируются
logger.info(f"AI script executed: {script}")
logger.debug(f"Output: {result.stdout}")
```

---

## 5. Безопасность

### Песочница (Sandbox)

```python
# Запуск в изолированной среде
result = run_script_in_sandbox(
    script='python test.py',
    timeout=30,
    allow_network=False,
    allowed_directories=['/project/tests']
)
```

### Проверка разрешений

```python
# Проверить, разрешён ли скрипт перед выполнением
if script in config['ai_scripts']['blocked']:
    raise PermissionError(f"Script {script} is blocked")

if script not in config['ai_scripts']['allowed']:
    await request_user_permission(script)
```

---

## 📚 Дополнительно

- [`guides/CLI_TOOLS.md`](CLI_TOOLS.md) — Доступные CLI инструменты
- [`standards/ENGINEERING.md`](../standards/ENGINEERING.md) — Стандарты разработки

**Последнее обновление:** сентябрь 2026
