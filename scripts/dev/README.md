# Модуль `scripts/dev` — Утилиты разработки и тестирования

## Назначение
Набор утилит для локальной разработки, тестирования, аудита стандартов и кодогенерации:

| Скрипт | Назначение | Использование |
|---|---|---|
| [`run_tests.py`](run_tests.py) | Запуск набора тестов через Pytest с поддержкой маркеров и отчета о покрытии. | `python scripts/dev/run_tests.py` |
| [`generate_coverage_report.py`](generate_coverage_report.py) | Генерация HTML и консольных отчетов о покрытии кода тестами. | `python scripts/dev/generate_coverage_report.py` |
| [`analyze_dependencies.py`](analyze_dependencies.py) | Аудит импортов модулей и сопоставление с `requirements.txt`. | `python scripts/dev/analyze_dependencies.py` |
| [`scan_headers.py`](scan_headers.py) | Валидация шапок файлов (`FILE_HEADERS.md`) на соответствие стандартам проекта. | `python scripts/dev/scan_headers.py` |
| [`export_pdf.py`](export_pdf.py) | Экспорт кодовой базы и документации проекта в сводные PDF-книги (`code.pdf`, `docs.pdf`). | `python -m scripts.dev.export_pdf` |
| [`init_skill.py`](init_skill.py) | Генератор каркаса нового агентурного навыка (`.skills/<name>/SKILL.md`). | `python scripts/dev/init_skill.py --name <name>` |
| [`package_skill.py`](package_skill.py) | Упаковка и валидация манифеста агентурного навыка. | `python scripts/dev/package_skill.py <name>` |
| [`init_plugin.py`](init_plugin.py) | Генератор каркаса нового плагина системы (`plugins/<name>/`). | `python scripts/dev/init_plugin.py --name <name>` |
| [`bot_runner.py`](bot_runner.py) | Автономный запуск Telegram-бота в отдельном процессе. | `python scripts/dev/bot_runner.py` |
| [`update_docs.py`](update_docs.py) | Проверка наличия docstrings в измененных Git-файлах. | `python scripts/dev/update_docs.py` |
| [`update_scripts_documentation.py`](update_scripts_documentation.py) | Автоматическая генерация и обновление документации по скриптам проекта. | `python scripts/dev/update_scripts_documentation.py` |
