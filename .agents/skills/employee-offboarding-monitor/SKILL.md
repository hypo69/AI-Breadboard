---
name: employee-offboarding-monitor
description: Monitors HR incoming documents for employee termination orders, extracts employee details via LLM, and triggers administrator security alerts for data cleanup and account decommissioning.
description_i18n:
  en: Monitors HR incoming documents for employee termination orders, extracts employee details via LLM, and triggers administrator security alerts for data cleanup and account decommissioning.
  ru: Отслеживает кадровые документы на предмет приказов об увольнении, извлекает метаданные через LLM и формирует алерты администратору для удаления данных и блокировки учетных записей.
---

# 🛡️ Employee Offboarding Monitor Skill

## 🎯 Purpose / Назначение
Monitors and analyzes HR documentation to detect employee dismissal/termination orders. When a valid termination order is detected, the skill extracts the employee profile, identifies associated enterprise accounts and data repositories, and generates an actionable alert for system administrators to perform offboarding and data decommissioning.

---

## 🚀 Execution Protocol / Протокол выполнения

1. **Document Ingestion & Text Extraction (`scripts/parse_order.py`)**:
   - Inspect files in the specified directory or file path (`.pdf`, `.docx`, `.txt`, `.rtf`, scanned images).
   - Extract raw text content cleanly.

2. **AI Classification & Entity Extraction (`scripts/classify_order.py`)**:
   - Prompt the LLM using the structured schema in `references/prompt_templates.md`.
   - Classify if document is an official dismissal/termination order.
   - Extract structured JSON:
     - `employee_name`: Full Name
     - `employee_id` / `personnel_number`: Tab number (if present)
     - `dismissal_date`: Effective termination date
     - `order_number`: Order registration number
     - `department` & `position`: Job title and department
     - `reason`: Legal or organizational basis

3. **Account & Resource Audit (`scripts/check_resources.py`)**:
   - Scan configured resources or storage directories for matched user footprint:
     - User home folders / shared drives
     - Mailboxes and cloud shares
     - Active sessions or credentials

4. **Administrator Alert Dispatch (`scripts/send_alert.py`)**:
   - Format alert with severity `HIGH/CRITICAL`.
   - Present Human-in-the-Loop decision options:
     - `[Schedule Deletion & Archive]`
     - `[Disable & Quarantine Now]`
     - `[Dismiss (False Positive)]`
   - Dispatch via configured webhook, Telegram bot, or console alert.

---

## 🛠️ Scripts & Tools

- `scripts/parse_order.py`: Extracts raw text from HR order files.
- `scripts/classify_order.py`: Analyzes text against termination order criteria and outputs structured JSON.
- `scripts/check_resources.py`: Identifies user directories and storage spaces associated with employee name/login.
- `scripts/send_alert.py`: Sends notification to administrator channels.

---

## 🔒 Safety & Compliance Guarantees

> [!CAUTION]
> **Human-in-the-Loop Mandatory:** The skill MUST NOT permanently delete data automatically without explicit administrator confirmation. It creates an actionable alert with quarantine recommendations.
