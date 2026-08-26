# Версионирование Python-модулей (`core.utils.versioning`)

## Назначение

Модуль `core/utils/versioning.py` предоставляет утилиты разбора, сравнения и выбора версий по стандарту [SemVer 2.0](https://semver.org/). Используется в `main.py` и других компонентах для выбора актуального тега при обновлениях.

## Публичный API

| Функция | Сигнатура | Описание |
|---|---|---|
| `parse_semver` | `(v: str) -> Tuple` | Разбор строки в кортеж `(major, minor, patch, prerelease[])`. Возвращает `()` при невалидной строке. |
| `compare_versions` | `(a: str, b: str) -> int` | Сравнение двух версий: `-1`, `0`, `1`. |
| `choose_best_tag` | `(tags, allow_prerelease, debug) -> str` | Выбор наибольшей версии из списка. Возвращает `''` при пустом списке. |

## Правила использования

- Функции **не возвращают `None`** — при отсутствии результата возвращается пустое значение типа (`()` или `''`).
- `debug=True` в `choose_best_tag` выводит информацию через `core.logger.logger`, **не через `print()`**.
- Пре-релизный тег (`1.2.3-alpha`) считается **меньше** стабильного (`1.2.3`) согласно SemVer §11.

## Примеры

```python
from core.utils.versioning import compare_versions, choose_best_tag

# Сравнение версий
compare_versions('1.2.3', '1.2.4')   # -1
compare_versions('v1.10.0', '1.9.9') # 1
compare_versions('1.2.3-alpha', '1.2.3')  # -1  (пре-релиз < стабильный)

# Выбор лучшего тега (только стабильные)
choose_best_tag(['v1.0.0', 'v1.1.0-alpha', 'v1.0.1'])
# → 'v1.0.1'

# Выбор лучшего тега (включая пре-релизы)
choose_best_tag(['v1.0.0', 'v1.1.0-alpha', 'v1.0.1'], allow_prerelease=True)
# → 'v1.1.0-alpha'
```

## Расположение

```
core/utils/versioning.py   ← основной модуль
tests/test_versioning.py   ← тесты (4 сценария, 100% pass)
```

## Связанные документы

- `.ai/instructions/knowledge/codex/js_versioning.md` — версионирование JS/CSS файлов (кэш-бастинг)
- `.ai/instructions/rules/CODE_RULES.md` — инженерный стандарт проекта
