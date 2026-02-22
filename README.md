# AI-Powered Financial Entry Automation Tool

Streamlit app that extracts transaction rows from a bank statement PDF and converts them into a clean, validated CSV.

## Quickstart

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Notes
- Uses `pdfplumber` to extract tables. If table extraction is imperfect, it falls back to a robust text/regex parser.
- Produces a strict CSV header:

`Serial No,Transaction Date,Value Date,Description,Cheque Number,Debit,Credit,Balance`

- Adds data-quality warnings and flags suspicious rows before export.
