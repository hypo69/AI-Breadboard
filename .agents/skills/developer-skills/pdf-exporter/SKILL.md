---
name: pdf-exporter
description: Toolkit for exporting project source code and documentation into formatted PDF books (code.pdf and docs.pdf).
description_i18n:
  en: Toolkit for exporting project source code and documentation into formatted PDF books (code.pdf and docs.pdf).
  ru: Набор инструментов для пакетного экспорта исходного кода и документации проекта в форматированные PDF книги (code.pdf и docs.pdf).
  es: Herramientas para exportar el codigo fuente y la documentacion del proyecto a libros PDF formateados (code.pdf y docs.pdf).
  he: ערכת כלים לייצוא קוד מקור ותיעוד הפרויקט לספרי PDF מעוצבים (code.pdf ו-docs.pdf).
---

# PDF Exporter Skill

Навык пакетного экспорта всей актуальной кодовой базы и документации проекта в единые PDF-книги: **docs.pdf** и **code.pdf**.

---

## Назначение и триггеры активации

Используйте этот навык в следующих сценариях:
1. **Экспорт документации проекта в PDF:** объединить все Markdown / RST / TXT документы репозитория в единый файл docs.pdf.
2. **Экспорт исходного кода в PDF:** сохранить всю кодовую базу с нумерацией строк и структурой каталогов в code.pdf.
3. **Пакетная сборка для оффлайн-анализа или ревью:** подготовка PDF-книг проекта для печати, аудита или архивирования.
4. **Запуск через CLI:** вызовы команды py manage_tools.py docs pdf.

---

## Команды CLI

### 1. Полная сборка документации и кода:
`powershell
py manage_tools.py docs pdf
`

### 2. Сборка только документации:
`powershell
py manage_tools.py docs pdf --target docs --output-dir pdf_exports
`

### 3. Сборка только исходного кода:
`powershell
py manage_tools.py docs pdf --target code --output-dir pdf_exports
`

---

## Программный вызов (Python API)

`python
from pathlib import Path
from src.utils.pdf import PDFUtils

# Экспорт документации
PDFUtils.build_docs_pdf(
    root_dir=Path('.'),
    output_file=Path('pdf_exports/docs.pdf'),
    doc_patterns=['*.md', '*.rst', '*.txt']
)

# Экспорт исходного кода
PDFUtils.build_code_pdf(
    root_dir=Path('.'),
    output_file=Path('pdf_exports/code.pdf'),
    code_patterns=['*.py', '*.ps1', '*.sh', '*.json', '*.yaml', '*.yml', '*.sql']
)
`
