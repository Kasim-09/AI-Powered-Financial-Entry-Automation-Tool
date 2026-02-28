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

🔗 **Live Demo:**  
👉 https://ai-powered-financial-entry-automation-tool-jxzmwjrowlc4g5ftuzm.streamlit.app/

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
---

## 🔐 Encrypted PDF Support (NEW FEATURE)

### What it does

The application now automatically detects and processes **password-protected (encrypted) bank statement PDFs**.

If a user uploads an encrypted PDF, the system:

1. Detects encryption automatically  
2. Attempts to unlock the PDF  
3. Prompts for a password only if required  
4. Removes encryption securely in memory  
5. Continues processing normally  

This ensures encrypted PDFs no longer cause the application to fail.

---

### 💡 How It Works

- The system checks whether the uploaded PDF is encrypted  
- If encrypted:
  - It first attempts to open using a blank password  
  - If unsuccessful, the user is prompted to enter the correct password  
- Once unlocked, the tool creates a temporary unencrypted version  
- All existing extraction, cleaning, validation, and export steps run unchanged  

No external tools or APIs are used — the feature is implemented using Python-native PDF libraries.

---

### 🖥️ User Experience

When an encrypted PDF is uploaded:

- A 🔒 Encrypted PDF detected message appears  
- A secure password input field is displayed (only if needed)  
- Status updates show the decryption process  
- Processing continues automatically after successful unlock  

For unencrypted PDFs, there is **no change** in workflow.

---

### 🔒 Security & Privacy

- Passwords are not stored  
- Decryption occurs temporarily during processing  
- No external services are used  
- Files remain within the Streamlit application environment  

---

### ⚠️ Edge Case Handling

The system gracefully handles:

- Incorrect passwords  
- Unsupported encryption types  
- PDFs that cannot be decrypted  

Clear error messages are shown without crashing the application.

---

### 📌 Business Impact

- Eliminates failures when users upload protected bank statements  
- Reduces manual intervention  
- Improves reliability of the automation workflow  
- Expands compatibility with real-world banking PDFs  

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

