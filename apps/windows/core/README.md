# Модуль аудита ПО (Software Audit Engine)

Этот модуль реализует **гибридный движок аудита (Hybrid Audit Engine)**, предназначенный для инвентаризации и анализа установленного программного обеспечения в среде Windows.

## Архитектура
Движок объединяет данные из нескольких источников для получения полной картины:

1.  **Инвентаризация (Registry):**
    *   Сканирование веток `HKLM` и `HKCU` по путям `...\Uninstall` для получения списка установленных программ.
2.  **Поведенческий анализ (OS Artifacts):**
    *   **UserAssist:** Анализ истории запусков GUI-приложений через реестр (декодирование ROT13).
    *   **Prefetch:** Сканирование файлов `.pf` для определения точного времени последних запусков приложений.

## Компоненты
- `SoftwareAuditEngine`: Главный класс для генерации отчетов (`generate_audit_report`).
- `SoftwareCategorizer`: Классификатор приложений по категориям (Браузеры, Разработка, Игры и т.д.).
- `PrefetchScanner` / `UserAssistParser`: Парсеры артефактов активности ОС.

## Использование
```python
from apps.windows.core.software_audit import SoftwareAuditEngine

engine = SoftwareAuditEngine()
report = engine.generate_audit_report()
print(f"Всего приложений: {report.total_apps}")
```
