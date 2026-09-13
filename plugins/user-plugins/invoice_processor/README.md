# 🧾 Invoice Processor Plugin

Modular plugin for AI Breadboard that automatically extracts structured invoice data from PDFs, scanned documents, and images using multi-backend OCR and AI vision models, and synchronizes the results directly into Google Sheets and local CSV backups.

---

## 🚀 Features

- **Multi-Format Ingestion**: Supports `.pdf`, `.png`, `.jpg`, `.jpeg`, `.bmp`, `.webp`, `.tiff`.
- **Hybrid OCR & Multimodal Intelligence**: Uses cascading text extraction (native PDF text -> Tesseract OCR -> Gemini Multimodal Vision).
- **Structured Field Extraction**:
  - Invoice Number
  - Invoice & Due Dates
  - Vendor / Company Name & VAT / Tax ID
  - Customer Name
  - Total & Tax Amounts
  - Currency
  - Line Items Summary & Notes
- **Direct Google Sheets Sync**: Appends extracted rows to the configured Google Spreadsheet.
- **Local Fallback**: Automatically saves an appended CSV backup to `data/invoices_processed/invoices_summary.csv`.

---

## ⚙️ Configuration (`config.json`)

```json
{
  "spreadsheet_id": "YOUR_GOOGLE_SPREADSHEET_ID",
  "sheet_name": "Invoices",
  "enable_local_backup": true,
  "backup_dir": "data/invoices_processed",
  "default_currency": "USD",
  "auto_create_header": true
}
```

---

## 🛠️ Actions & Tools

### Admin Actions
1. `process_folder`: Scan directory, extract all invoices, and sync to Google Sheets.
2. `process_file`: Extract details from a single invoice file.

### Function Tools
- `process_invoices_folder(folder_path, spreadsheet_id, sheet_name)`: Tool callable by LLM chat agents.