# Employee Offboarding Monitor Skill

## Overview
The `employee-offboarding-monitor` skill monitors incoming HR documents (dismissal/termination orders), extracts employee metadata using Large Language Models, audits associated user footprints across enterprise storages, and generates actionable administrative security alerts for data cleanup and account decommissioning.

## Localization (i18n)
- **English (`en`)**: Monitors HR incoming documents for employee termination orders, extracts employee details via LLM, and triggers administrator security alerts for data cleanup and account decommissioning.
- **Russian (`ru`)**: Отслеживает кадровые документы на предмет приказов об увольнении, извлекает метаданные через LLM и формирует алерты администратору для удаления данных и блокировки учетных записей.

## Architecture & Workflow

```
[HR Document (PDF/DOCX/Scan)]
             │
             ▼
   [scripts/parse_order.py] ─── (Text Ingestion)
             │
             ▼
  [scripts/classify_order.py] ── (AI Entity & Dismissal Extraction)
             │
             ▼
  [scripts/check_resources.py] ─ (Account & Storage Footprint Audit)
             │
             ▼
    [scripts/send_alert.py] ──── (Admin Notification & Human-in-the-Loop)
```

## Available Scripts

### 1. `scripts/parse_order.py`
Extracts text from various file formats (`.pdf`, `.docx`, `.txt`, `.rtf`).
```bash
python .agents/skills/employee-offboarding-monitor/scripts/parse_order.py --file "C:/HR/Orders/Order_142.docx"
```

### 2. `scripts/classify_order.py`
Analyzes document text against dismissal order criteria and outputs structured JSON metadata.
```bash
python .agents/skills/employee-offboarding-monitor/scripts/classify_order.py --text "Приказ № 142-К..."
```

### 3. `scripts/check_resources.py`
Identifies active accounts, user home directories, and email storage mapped to the employee.
```bash
python .agents/skills/employee-offboarding-monitor/scripts/check_resources.py --employee-name "Иванов Иван Иванович"
```

### 4. `scripts/send_alert.py`
Dispatches an alert to system administrators with interactive options (quarantine, schedule deletion, dismiss).
```bash
python .agents/skills/employee-offboarding-monitor/scripts/send_alert.py --data order_payload.json
```

## Security & Compliance
- **Human-in-the-Loop:** Permanent data deletion is never executed autonomously; it mandates administrative approval.
- **Grace Period Support:** Recommends quarantine and cold backup before final sanitization.

## Related Modules
- [`../../DOCUMENTATION.md`](../../DOCUMENTATION.md) — Documentation index
- [`.ai/instructions/rules/DOCS_RULES.md`](../../.ai/instructions/rules/DOCS_RULES.md) — Documentation standards

