---
name: gdrive-organizer
description: Scans Google Drive, analyzes folder hierarchy and file disorganization, detects clutter and duplicates, and proposes or executes structured reorganization improvements.
description_i18n:
  en: Scans Google Drive, analyzes folder hierarchy and file disorganization, detects clutter and duplicates, and proposes or executes structured reorganization improvements.
  ru: Сканирует Google Диск, анализирует логику и беспорядок в структуре папок, находит дубликаты и неструктурированные файлы, предлагает и выполняет план наведения порядка.
---

# 🗂️ Google Drive Intelligent Auditor & Organizer Skill

Intelligent assistant skill for scanning Google Drive, auditing storage hierarchy, detecting clutter (loose root files, messy versions, empty folders, duplicate candidates), and generating actionable, safe restructuring proposals.

---

## 🎯 Use Cases

1. **Storage Health Audit**:
   - Calculate Drive Organization Health Score (0–100%).
   - Detect files dumped directly into root, duplicate copies, copy-of name clutter, and abandoned empty directories.
2. **Restructuring Plan Generation**:
   - Categorize files logically based on semantic keywords, MIME types, and date stamps.
   - Produce clear Markdown comparison tables and JSON migration plans.
3. **Safe Execution**:
   - Dry-run simulation before moving any files.
   - Non-destructive directory creation and file moving with audit logging.

---

## 🚀 CLI Commands

### 1. Audit Drive Structure & Print Report:
```powershell
python skills/gdrive-organizer/scripts/main.py audit
python skills/gdrive-organizer/scripts/main.py audit --report-out reports/drive_health.md
```

### 2. Generate Reorganization Plan:
```powershell
python skills/gdrive-organizer/scripts/main.py propose --out plan.json --report-out plan_preview.md
```

### 3. Dry-run Preview of Plan:
```powershell
python skills/gdrive-organizer/scripts/main.py apply --plan plan.json --dry-run
```

### 4. Execute Restructuring Plan:
```powershell
python skills/gdrive-organizer/scripts/main.py apply --plan plan.json --log-out execution_log.json
```

---

## 🔐 Authentication

Uses Google Workspace credentials discovered automatically by `google_auth.py`:
- `src/secrets/credentials.json` or `credentials.json` (OAuth 2.0)
- `src/secrets/service_account.json` or `service_account.json` (Service Account)
- Environment variable `GOOGLE_APPLICATION_CREDENTIALS`
