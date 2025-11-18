# 📄 BD Tickers – Automated Financial Statement Scanner

**Automatically detect, extract, and generate high-resolution searchable PDFs of P&L (Income Statement) pages from Bangladeshi listed companies’ financials.**

This repository provides an advanced PDF parsing and OCR automation pipeline capable of handling **all types of financial statements**—including:

✔ Scanned PDFs
✔ Low-quality images
✔ Machine-readable PDFs
✔ Annual & quarterly financial statements
✔ Consolidated or standalone reports

The system identifies the **main or consolidated Profit & Loss (Income Statement)** page from any financial report and exports it as a **high-resolution, fully searchable PDF**.

---

## 🚀 Key Features

### 🔍 Accurate P&L Page Detection

* Detects the correct P&L (Income Statement) page using:

  * Header keyword scoring
  * Financial term scoring
  * OCR fallbacks for low-text pages

### 🤖 Hybrid OCR + Text Extraction

* Uses **PyMuPDF** for fast text extraction.
* Falls back to **Tesseract OCR** for:

  * Image-only scanned PDFs
  * Rotated pages
  * Half-page OCR to optimize speed

### ✨ Smart Rotation Handling

* Automatically detects orientation using Tesseract OSD.
* Normalizes rotated or sideways pages.

### 📤 High-Resolution Output

* Extracted P&L page is rendered at **300 DPI**.
* Saved as a **searchable PDF** using OCR overlay.

### 🧠 Highly Scalable

* Chunked scanning for large PDFs (200–500+ pages).
* Multi-stage pipeline for accuracy + speed balance.

---

## 🛠️ Technologies Used

* **Python 3.10+**
* **PyMuPDF (fitz)** → PDF parsing, rendering
* **Tesseract OCR / pytesseract** → OCR for scanned pages
* **Pillow** → Image handling
* **Regex** → Keyword-based scoring

---

## 📁 Folder Structure

```
BD_ticker-s_financial_automation/
│
├── functions.py          # Main logic: scanning, OCR, extraction
├── samples/              # Example financial statements
└── README.md             # Documentation
```

---

## 📌 How It Works

### **Stage A – Header Word Scoring**

* Each page is scanned for header words like:

  ```
  Statement of Profit or Loss
  Comprehensive Income
  Consolidated Account
  ```
* Top-K likely candidate pages are selected.

### **Stage B – Deep Term Scoring**

* For the Top-K pages, the system checks for keywords such as:

  ```
  revenue, cost of goods sold, gross profit, eps,
  operating expenses, ebit, depreciation, tax, net profit
  ```
* OCR is applied only when needed.

### **Final Selection**

* The page with the **highest financial-term score** is chosen as the P&L statement.

### **PDF Export**

* The best page is converted to an image → OCR → searchable PDF.

---

## 📦 Installation

### 1. Clone the repository

```bash
git clone https://github.com/Mehedi24434/BD_ticker-s_financial_automation.git
cd BD_ticker-s_financial_automation
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Tesseract

* **Windows:**
  Download from [https://github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki)
* **Linux (Ubuntu):**

  ```bash
  sudo apt install tesseract-ocr
  ```
* **Mac:**

  ```bash
  brew install tesseract
  ```

---

## 🧪 Example Usage

```python
import functions as f

pdf_file = "./samples/sample13.pdf"
output_pdf = "pnl_page_searchable.pdf"

f.save_best_pnl_page_as_searchable_pdf(
    pdf_file, 
    output_pdf, 
    rotation_option=False, 
    dpi=300
)
```

### ✔ Example Output (from sample13.pdf)

```
Top pages by header score:
  Page 2 → 10
  Page 1 → 6
  Page 3 → 5
  ...
Term scores among header Top-K:
  Page 2 → 18
  Page 1 → 3
  Page 3 → 3
  ...

Most likely P&L page: Page 2
P&L page saved as high-quality searchable PDF: pnl_page_searchable.pdf
```

---

## 📘 API Overview

### **find_best_pnl_page_chunked(pdf_path, ...)**

Finds the most probable P&L page using header scoring + OCR scoring.

### **save_best_pnl_page_as_searchable_pdf(pdf_path, output_path, ...)**

Extracts & saves the high-quality searchable income statement page.

---

## 📈 Why This Project Exists

Bangladeshi companies publish financials in inconsistent formats:

* Scanned images
* Watermarked PDFs
* Rotated pages
* Tables broken across columns
* Mixed English/Bengali

This project provides a **robust, production-ready** tool for analysts and automation pipelines to **quickly locate and extract the P&L section** without manual searching.

---

## 🔮 Future Improvements

* Add extraction for:

  * Balance Sheet
  * Cash Flow Statement
  * Notes
* Add deep learning tables detection (LayoutLM / DocTr)
* Add CLI and REST API versions
* Add parallel processing mode for bulk PDF scanning

---

## 🤝 Contributing

Pull requests are welcome!
For major changes, please open an issue first to discuss what you would like to improve.

---

## 📜 License

MIT License – free to use and modify.


