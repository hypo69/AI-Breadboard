# 📋 How to Prepare Documents for PixelRAG Index Generation

This guide explains how to prepare your documents for indexing in Google Colab using the `PixelRAG_Hybrid_Index_Generator.ipynb` notebook.

---

## 📁 Directory Structure

Create a folder structure like this on your computer, then ZIP it:

```
my_documents/
│
├── PDFs/
│   ├── manual.pdf
│   ├── documentation.pdf
│   └── report.pdf
│
├── markdown_files/
│   ├── README.md
│   ├── guide.md
│   └── notes.md
│
├── images/
│   ├── screenshot1.png
│   ├── screenshot2.jpg
│   ├── diagram.png
│   └── workflow.gif
│
├── code/
│   ├── example.py
│   ├── helper.js
│   └── config.json
│
└── urls.txt (optional)
```

---

## 📝 File Format Support

### Text Files ✅
- **Formats:** `.txt`, `.md`, `.markdown`, `.rst`, `.log`, `.json`, `.csv`, `.tsv`
- **Code:** `.py`, `.js`, `.ts`, `.html`, `.css`, `.sh`, `.sql`, `.xml`
- **Support:** Full text extraction and chunking

**Example:**
```
└── docs/
    ├── getting_started.md
    ├── api_reference.md
    ├── config.json
    └── CHANGELOG.txt
```

### PDF Files ✅
- **Format:** `.pdf`
- **Text Extraction:** Yes (for Text RAG)
- **Page Tiles:** Yes (for Pixel RAG) — creates images of each page
- **Note:** Scanned PDFs without OCR may produce empty text

**Example:**
```
└── pdfs/
    ├── user_manual.pdf       # 50 pages → 50 tiles + text
    ├── technical_spec.pdf
    └── training_guide.pdf
```

### Image Files ✅
- **Formats:** `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.bmp`
- **Processing:** Indexed directly as tiles
- **Recommended:** Screenshots, diagrams, UI mockups

**Example:**
```
└── images/
    ├── dashboard_screenshot.png
    ├── architecture_diagram.jpg
    └── ui_components/
        ├── button.png
        ├── input_field.png
        └── modal_dialog.png
```

### URLs (Optional) ✅
- **File:** `urls.txt` (one URL per line)
- **Currently:** Listed but not processed in v1
- **Future:** Web scraping + screenshot capture

**Example (`urls.txt`):**
```
https://example.com/docs
https://api.example.com/reference
https://blog.example.com/tutorials
```

---

## 🎯 Recommended Document Collection

For best results, include:

1. **Documentation** (40%)
   - User guides
   - API documentation
   - Architecture docs
   - Tutorials

2. **Code** (20%)
   - Example scripts
   - Configuration files
   - Code snippets

3. **Visual Content** (30%)
   - Screenshots
   - Diagrams
   - UI mockups
   - Flowcharts

4. **Other** (10%)
   - Release notes
   - FAQs
   - Quick reference cards

---

## 📦 Creating the ZIP File

### On Windows (PowerShell)
```powershell
# Navigate to parent directory
cd C:\Users\YourName\Documents

# Create ZIP
Compress-Archive -Path my_documents -DestinationPath documents.zip

# Verify
Get-ChildItem documents.zip | Select Length, Name
```

### On macOS/Linux
```bash
# Navigate to parent directory
cd ~/Documents

# Create ZIP
zip -r documents.zip my_documents

# Verify
ls -lh documents.zip
```

### Using 7-Zip (Windows)
1. Right-click `my_documents` folder
2. Select **7-Zip → Add to archive**
3. Save as `documents.zip`

---

## 📤 Upload to Google Drive

1. Go to [Google Drive](https://drive.google.com)
2. Create a new folder called `RAG_Documents`
3. Upload `documents.zip` to this folder
4. **Right-click → Share** and set to "Editor" access for the notebook runner (if needed)

---

## 🔍 Size Recommendations

| Document Count | Total Size | Processing Time | Cost (Colab) |
|---|---|---|---|
| 10-20 files | < 50 MB | 5-10 min | Free (GPU) |
| 20-50 files | 50-200 MB | 15-30 min | Free (GPU) |
| 50-100 files | 200-500 MB | 30-60 min | Free (GPU) |
| 100+ files | 500+ MB | 1+ hour | May need Pro |

**Tip:** If ZIP > 500 MB, consider:
- Creating multiple ZIP files and running notebook separately for each
- Removing images > 2 MB
- Splitting large PDFs into separate files

---

## ⚠️ Document Quality Tips

### PDFs
- ✅ Use **searchable/OCR'd PDFs** for text extraction
- ✅ PDFs with **embedded text** (not scanned images)
- ❌ Avoid corrupt or password-protected PDFs
- 💡 Use QPDF to remove password: `qpdf --decrypt input.pdf output.pdf`

### Images
- ✅ **High contrast** images (better for visual search)
- ✅ **Screenshots with UI elements** (buttons, fields, menus)
- ✅ **Diagrams with clear labels**
- ❌ Avoid tiny images < 100x100px
- ❌ Avoid very large images > 10 MB (auto-resized anyway)

### Text Files
- ✅ **Well-structured content** with headings and paragraphs
- ✅ **Plain UTF-8 encoding** (avoid binary formats)
- ✅ **Consistent formatting** (helps chunking)
- ❌ Avoid extremely large single files > 10 MB

---

## 🧪 Example: Preparing Your First Index

**Scenario:** You want to index your Python project documentation

### Step 1: Organize Files
```bash
mkdir my_docs
cd my_docs

# Copy documentation
cp -r ../my_project/docs .
cp ../my_project/README.md .
cp ../my_project/CONTRIBUTING.md .

# Copy selected code examples
mkdir code_examples
cp ../my_project/examples/*.py code_examples/

# Add some screenshots
mkdir screenshots
# (Add your UI screenshots here)

cd ..
```

### Step 2: Create ZIP
```bash
zip -r rag_documents.zip my_docs
ls -lh rag_documents.zip  # Should be ~50-100 MB
```

### Step 3: Upload to Drive
- Go to Google Drive
- Create folder `RAG_Documents`
- Upload `rag_documents.zip`

### Step 4: Configure Notebook
In Cell 0 of `PixelRAG_Hybrid_Index_Generator.ipynb`:
```python
DOCUMENTS_ZIP_PATH = "/content/drive/MyDrive/RAG_Documents/rag_documents.zip"
```

### Step 5: Run!
- Click the play button
- Wait for completion
- Download the resulting `rag_indices_*.zip`

---

## 🚀 Advanced: Multi-Source Collection

If you want to build a comprehensive index from multiple projects:

```
all_documentation/
├── project_a/
│   ├── docs/
│   └── README.md
├── project_b/
│   ├── api_docs/
│   └── tutorials/
├── external_docs/
│   └── third_party_references/
└── screenshots/
    ├── ui_guides/
    └── system_architecture/
```

ZIP and upload to Colab as usual.

---

## 📊 What Gets Generated?

After running the notebook, you'll get:

**Text RAG Index:**
- 2,500+ text chunks (depends on document size)
- FAISS index with semantic embeddings
- TF-IDF vectors for fast similarity search
- Metadata (file names, page numbers, timestamps)

**Pixel RAG Index:**
- All PDF pages as PNG tiles
- All images resized and optimized
- Visual embeddings for each tile
- Separate FAISS index for image search

**Total Output Size:** 200-500 MB (ZIP), depending on input

---

## ✅ Checklist Before Running Notebook

- [ ] Documents collected and organized
- [ ] ZIP file created successfully
- [ ] ZIP file uploaded to Google Drive
- [ ] `DOCUMENTS_ZIP_PATH` updated in notebook Cell 0
- [ ] Colab GPU enabled (recommended)
- [ ] GEMINI_API_KEY set in Colab Secrets (if needed)
- [ ] Sufficient Google Drive storage (200+ MB)

---

## 🆘 Troubleshooting

### Q: My ZIP file is too large (> 500 MB)
**A:** Split into multiple ZIPs and run notebook separately for each

### Q: Some PDFs have no text extracted
**A:** These are scanned PDFs. Use OCR tool to extract text first (e.g., Tesseract)

### Q: Images are rotated incorrectly
**A:** Notebook auto-rotates using EXIF. If still wrong, pre-rotate images before ZIPping

### Q: Out of memory during processing
**A:** Reduce `TEXT_CHUNK_SIZE` from 500 to 256 in Cell 0

### Q: Very slow processing
**A:** Enable GPU runtime in Colab for 5-10x speedup

---

## 💡 Tips for Best Results

1. **Mix content types** — Text + PDFs + images work better together
2. **Include context** — Add README files explaining document purpose
3. **Use clear naming** — `user_guide.pdf` is better than `document_1.pdf`
4. **Update regularly** — Re-generate indices when new documentation is added
5. **Keep originals** — Store original documents separately from indices

---

## 📝 Example Collections to Try

### Documentation Project
```
├── API reference (10 MB)
├── User guides (20 MB)
├── Architecture diagrams (5 MB)
├── Code examples (3 MB)
└── Screenshots (5 MB)
Total: ~43 MB
```

### Software Manual
```
├── User manual PDF (50 MB)
├── System requirements (1 MB)
├── Installation guide (2 MB)
└── Troubleshooting (1 MB)
Total: ~54 MB
```

### Knowledge Base
```
├── FAQ documents (5 MB)
├── Tutorial videos (screenshots) (10 MB)
├── Configuration files (1 MB)
├── Setup guides (3 MB)
└── Reference materials (8 MB)
Total: ~27 MB
```

---

**Ready to build your RAG indices? Create your ZIP and follow the [PixelRAG_Hybrid_Index_Generator.ipynb](./PixelRAG_Hybrid_Index_Generator.ipynb) notebook!**
