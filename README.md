# 💳 AI-Powered Financial Entry Automation Tool

## Overview

The **AI-Powered Financial Entry Automation Tool** is a Streamlit-based  
application that extracts transaction data from bank statement PDFs and  
converts it into a clean, validated CSV file ready for financial  
processing.

The tool is designed to reduce manual data entry, improve accuracy, and  
standardize transaction data for downstream accounting or automation  
systems.

---

## 🎯 Target Audience

This tool is intended for:

- Internal finance teams  
- Accounting and operations staff  
- Business users who process bank statements regularly  
- Technical teams supporting finance automation  

No programming knowledge is required for normal use.

---

## 🚀 Key Features

### 📄 PDF Transaction Extraction

**What it does**  
Extracts transaction rows from a bank statement PDF.

**Business benefit**

- Eliminates manual copy-paste work  
- Speeds up reconciliation workflows  
- Reduces human error  

**Prerequisites**

- PDF must contain selectable text (not scanned)  
- Statement should follow supported layout  

---

### 🧹 Automated Data Cleaning

**Cleaning rules**

- Removes commas from numeric fields  
- Converts "-" to empty cells where required  
- Trims description whitespace  
- Normalizes date format to DD/MM/YYYY  
- Removes dashes from cheque numbers  

---

### ✅ Built-in Data Validation

**Validation checks**

- Column alignment verification  
- Numeric format validation  
- Missing value detection  
- Debit/Credit consistency check  
- Balance presence validation  

---

### 📊 Interactive Preview Dashboard

Users can:

- Preview cleaned transactions  
- View warnings and errors  
- Inspect raw extracted data (optional)  

---

### ⬇️ Strict CSV Export

**Output schema**


**Export guarantees**

- No surrounding quotes  
- One transaction per row  
- No empty rows  
- Numeric fields normalized  

---

## 🏦 Supported Bank Formats

### ✅ Fully Supported

Optimized for **Bank of Baroda** statements with:

- Standard column order  
- Multi-line description handling  
- BOB-style number formatting  
- Header/footer filtering  

---

### ⚠️ Partially Supported

May work with similar banks if:

- Same column order  
- Text-based PDF  
- Similar date formats  
- Detectable table grid  

Accuracy is not guaranteed.

---

## ❌ Known Limitations

### Scanned or Image PDFs

Not supported. OCR is not implemented.

### Different Column Structures

Layouts that differ from BOB may misalign.

### Very Different Bank Layouts

Examples that may fail:

- HDFC  
- ICICI  
- SBI  

### Multi-Account Statements

May introduce noise rows.

### Description Line Break Issues ⚠️

In some statements, the transaction description spans multiple lines.  
Due to PDF text extraction behavior, the tool may occasionally:

- Merge two transaction descriptions, or  
- Incompletely capture multi-line descriptions  

**Workaround:**  
Review the Preview tab and manually verify descriptions for critical entries.

---

## 🖥️ System Requirements

- Python 3.9+  
- 4 GB RAM recommended  
- Modern web browser  

---

## ⚙️ Installation

```bash
git clone <your-repo-url>
cd AI-Powered-Financial-Entry-Automation-Tool
pip install -r requirements.txt
streamlit run app.py

