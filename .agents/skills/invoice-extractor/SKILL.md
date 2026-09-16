---
name: invoice-extractor
description: Extracts structured invoice and receipt metadata from images and PDF documents, and synchronizes the results into Google Sheets.
description_i18n:
  en: Extracts structured invoice and receipt metadata from images and PDF documents, and synchronizes the results into Google Sheets.
  ru: Извлекает структурированные данные из счетов и квитанций (PDF и изображения) с помощью OCR и ИИ, и сохраняет их в Google Таблицы.
---

# 🧾 Invoice Extractor Skill

## 🎯 Purpose / Назначение
Automates the end-to-end ingestion and processing of invoices and receipts from a specified directory. Uses hybrid OCR and multimodal AI to extract financial parameters (invoice number, date, vendor, tax ID, totals, items summary) and writes them into a **Google Sheets** spreadsheet and a local CSV ledger.

---

## 🚀 Execution Protocol / Протокол выполнения

When the user asks to process a folder with invoices or receipts:

1. **Verify Folder Path**:
   Check if the folder path provided by the user exists and contains documents (`.pdf`, `.png`, `.jpg`, `.jpeg`, `.bmp`, `.webp`, `.tiff`).

2. **Execute Processing Script**:
   Run the CLI script providing the folder path and optional Google Spreadsheet ID:
   ```powershell
   python skills/invoice-extractor/scripts/process_invoices.py --folder "C:/path/to/invoices" --spreadsheet-id "<SPREADSHEET_ID>" --sheet-name "Invoices"
   ```

3. **Fallback / Local Operation**:
   If no Google Spreadsheet ID is configured, the skill automatically writes all processed records to `data/invoices_processed/invoices_summary.csv` and outputs the formatted summary in the terminal.

4. **Review & Output**:
   Present the structured table of extracted invoices to the user with status (success, vendor, amounts, currency, line items).

---

## 🛠️ Scripts & Tools

- `scripts/process_invoices.py`: CLI tool for batch processing invoices from a folder.
- `references/invoice_schema.json`: JSON schema definition for structured invoice attributes.

---

## 🔒 Configuration & Credentials

The skill automatically utilizes configured Google Workspace credentials (via `src/secrets/` or environment variables `GOOGLE_APPLICATION_CREDENTIALS` / `GOOGLE_SERVICE_ACCOUNT_JSON`).

