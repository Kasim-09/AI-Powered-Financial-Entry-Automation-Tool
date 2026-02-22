from __future__ import annotations

import re
from typing import List, Dict, Tuple, Optional

import pdfplumber
import pandas as pd

from .utils import ValidationIssue, get_logger
from .cleaning import normalize_date, clean_amount, clean_cheque_number, clean_description

logger = get_logger()

# Fallback parsing patterns
SRNO_LINE = re.compile(r"^\s*(\d{1,4})\s+(\d{2}[-/]\d{2}[-/]\d{4})\s+(?:(\d{2}[-/]\d{2}[-/]\d{4})\s+)?(.*)$")
AMOUNT_TOKEN = re.compile(r"^[\d,]+(?:\.\d{2})?$|^-$")

EXPECTED_COLS = ["Serial No","Transaction Date","Value Date","Description","Cheque Number","Debit","Credit","Balance"]

def _looks_like_header_row(row: List[str]) -> bool:
    joined = " ".join((c or "").lower() for c in row)
    return ("sr.no" in joined) or ("transaction" in joined) or ("value" in joined) or ("description" in joined)

def _normalize_table_row(row: List[str]) -> Optional[Dict[str, str]]:
    """
    Normalize a pdfplumber table row to the expected schema.

    Expected table layout (8 columns):
    Sr.No | Transaction Date | Value Date | Description | Cheque Number | Debit | Credit | Balance
    """
    if not row:
        return None
    cells = [(c or "").replace("\n", " ").strip() for c in row]
    if _looks_like_header_row(cells):
        return None
    if len(cells) < 6:
        return None

    # If 8+ columns, map from ends and merge the middle into Description.
    if len(cells) >= 8:
        sr = cells[0]
        txn_date = cells[1]
        val_date = cells[2]
        debit = cells[-3]
        credit = cells[-2]
        balance = cells[-1]
        cheque = cells[-4]
        desc_parts = cells[3:-4]
        desc = " ".join([p for p in desc_parts if p])
    else:
        # best-effort for 6-7 column extractions
        sr = cells[0]
        txn_date = cells[1]
        val_date = cells[2] if len(cells) > 2 else ""
        debit = cells[-3] if len(cells) >= 6 else ""
        credit = cells[-2] if len(cells) >= 6 else ""
        balance = cells[-1] if len(cells) >= 6 else ""
        mid = cells[3:-3]
        desc = " ".join([p for p in mid if p])
        cheque = ""

    if clean_description(desc).lower() == "opening balance":
        return None

    return {
        "Serial No": sr,
        "Transaction Date": txn_date,
        "Value Date": val_date,
        "Description": desc,
        "Cheque Number": cheque,
        "Debit": debit,
        "Credit": credit,
        "Balance": balance,
    }

def extract_transactions_pdfplumber(pdf_path: str) -> Tuple[pd.DataFrame, List[ValidationIssue]]:
    """
    Extract transaction rows from a bank statement PDF using pdfplumber table extraction.
    Returns (dataframe, issues). Falls back to regex parsing if tables are not found.
    """
    issues: List[ValidationIssue] = []
    rows: List[Dict[str, str]] = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_idx, page in enumerate(pdf.pages, start=1):
                before_rows = len(rows)
                tables = page.extract_tables(
                    table_settings={
                        "vertical_strategy": "lines",
                        "horizontal_strategy": "lines",
                        "intersection_tolerance": 5,
                        "snap_tolerance": 3,
                        "join_tolerance": 3,
                        "edge_min_length": 20,
                        "min_words_vertical": 1,
                        "min_words_horizontal": 1,
}
                )

                if not tables:
                    page_text = page.extract_text() or ""
                    fallback_rows, fallback_issues = _extract_from_text(page_text)
                    rows.extend(fallback_rows)
                    issues.extend([
                        ValidationIssue(serial_no=i.serial_no, level=i.level,
                                        message=f"(page {page_idx}) {i.message}", context=i.context)
                        for i in fallback_issues
                    ])
                    continue

                for t in tables:
                    for r in t:
                        item = _normalize_table_row(r)
                        if item:
                            item["_page"] = str(page_idx)
                            rows.append(item)

                # If table extraction produced nothing usable, fall back to text parsing for this page.
                if len(rows) == before_rows:
                    page_text = page.extract_text() or ""
                    fallback_rows, fallback_issues = _extract_from_text(page_text)
                    rows.extend(fallback_rows)
                    issues.extend([
                        ValidationIssue(serial_no=i.serial_no, level=i.level,
                                        message=f"(page {page_idx}) {i.message}", context=i.context)
                        for i in fallback_issues
                    ])

    except Exception as e:
        logger.exception("Failed to open/parse PDF")
        issues.append(ValidationIssue(serial_no=None, level="error",
                                      message=f"Failed to open or parse PDF: {e}"))
        return pd.DataFrame(columns=EXPECTED_COLS), issues

    if not rows:
        issues.append(ValidationIssue(serial_no=None, level="error",
                                      message="No transaction rows were extracted from the PDF."))
        return pd.DataFrame(columns=EXPECTED_COLS), issues

    df = pd.DataFrame(rows)
    df = _clean_and_standardize(df, issues)
    return df, issues

def _extract_from_text(text: str) -> Tuple[List[Dict[str, str]], List[ValidationIssue]]:
    """
    Fallback parser that reconstructs rows from PDF text.

    This PDF's text extraction often yields a pattern where the *description line(s)*
    appear immediately BEFORE the line that starts with the Sr.No + dates + amounts.
    We handle that by buffering "orphan" description lines and attaching them to the
    next detected transaction line.
    """
    issues: List[ValidationIssue] = []
    rows: List[Dict[str, str]] = []

    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    current: Optional[Dict[str, str]] = None
    prebuffer: List[str] = []

    def is_noise(line: str) -> bool:
        l = line.lower().strip()
        if not l:
            return True
        # Common headers/footers for this statement
        if "account statement from" in l:
            return True
        if l.startswith(("account statement", "page", "this is a computer-generated", "statement is generated")):
            return True
        if "page " in l and " of " in l:
            return True
        if "bob world" in l:
            return True
        # Timestamp footer like '09/11/2025 02:53:00 PM'
        if re.match(r"^\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}\s*(am|pm)$", l):
            return True
        # Hindi header line like '23-08-2025 से 09-11-2025 तक की खाता'
        if "खाता" in l and "से" in l and "तक" in l:
            return True
        # Column header lines (Hindi/English)
        if "sr.no" in l or ("debit" in l and "credit" in l and "balance" in l):
            return True
        if ("चेक" in l and "नामे" in l and "जमा" in l) or ("लेनदेन" in l and "ववरण" in l):
            return True
        return False


    def flush_current():
        nonlocal current
        if current:
            if clean_description(current.get("Description", "")).lower() != "opening balance":
                rows.append(current)
        current = None

    for ln in lines:
        if is_noise(ln) or _looks_like_header_row([ln]):
            continue

        m = SRNO_LINE.match(ln)
        if m:
            flush_current()
            sr, txn_date, val_date, rest = m.groups()
            rest = rest or ""

            # If this line contains Opening Balance, skip it (non-transaction) and clear buffered text.
            if "opening balance" in ln.lower():
                prebuffer = []
                current = None
                continue

            tokens = rest.split()

            # Scan from end for up to 3 trailing amount tokens
            amt_tokens: List[str] = []
            idx = len(tokens) - 1
            while idx >= 0 and len(amt_tokens) < 3:
                tok = tokens[idx]
                if AMOUNT_TOKEN.match(tok):
                    amt_tokens.append(tok)
                    idx -= 1
                else:
                    break
            amt_tokens = list(reversed(amt_tokens))
            desc_tokens = tokens[: idx + 1]

            cheque = ""
            # If a standalone numeric appears at the end of desc_tokens, treat as cheque no.
            if desc_tokens and desc_tokens[-1].isdigit() and len(desc_tokens[-1]) <= 12:
                cheque = desc_tokens[-1]
                desc_tokens = desc_tokens[:-1]

            # Combine any buffered pre-description lines with inline description tokens
            desc_parts = prebuffer + ([" ".join(desc_tokens)] if desc_tokens else [])
            prebuffer = []

            current = {
                "Serial No": sr,
                "Transaction Date": txn_date,
                "Value Date": val_date or "",
                "Description": " ".join([p for p in desc_parts if p]).strip(),
                "Cheque Number": cheque,
                "Debit": "",
                "Credit": "",
                "Balance": "",
            }

            if len(amt_tokens) == 3:
                current["Debit"], current["Credit"], current["Balance"] = amt_tokens
            else:
                issues.append(ValidationIssue(serial_no=int(sr), level="warning",
                                              message="Could not reliably detect trailing Debit/Credit/Balance tokens in fallback text parse."))

        else:
            # Not a row start. Buffer as description for the next row, or append to current row.
            if is_noise(ln):
                continue
            if current is None:
                prebuffer.append(ln)
            else:
                # Continuation after row start
                current["Description"] = (current["Description"] + " " + ln).strip()

    flush_current()
    return rows, issues

def _clean_and_standardize(df: pd.DataFrame, issues: List[ValidationIssue]) -> pd.DataFrame:
    """
    Apply cleaning rules:
    - Dates => DD/MM/YYYY
    - Cheque Number: '-' => empty, remove dashes
    - Amounts: remove commas, '-' => empty for Debit/Credit
    - Description trim
    - Drop malformed rows
    """
    for c in EXPECTED_COLS:
        if c not in df.columns:
            df[c] = ""

    for c in EXPECTED_COLS:
        df[c] = df[c].astype(str).fillna("")

    df["Serial No"] = df["Serial No"].str.strip()
    df["Transaction Date"] = df["Transaction Date"].apply(normalize_date)
    df["Value Date"] = df["Value Date"].apply(normalize_date)
    df["Description"] = df["Description"].apply(clean_description)
    df["Cheque Number"] = df["Cheque Number"].apply(clean_cheque_number)
    df["Debit"] = df["Debit"].apply(lambda x: clean_amount(x, dash_to_empty=True))
    df["Credit"] = df["Credit"].apply(lambda x: clean_amount(x, dash_to_empty=True))
    df["Balance"] = df["Balance"].apply(lambda x: clean_amount(x, dash_to_empty=False))

    bad = df[(df["Serial No"] == "") | (df["Transaction Date"].isna())]
    for _, row in bad.iterrows():
        try:
            sn = int(row["Serial No"]) if row["Serial No"] else None
        except Exception:
            sn = None
        issues.append(ValidationIssue(serial_no=sn, level="warning",
                                      message="Dropping a row due to missing Serial No or invalid Transaction Date.",
                                      context={"row": row.to_dict()}))
    df = df.drop(bad.index).copy()

    df["Serial No"] = df["Serial No"].astype(int)
    df = df[df["Description"].str.lower() != "opening balance"].copy()
    df = df.sort_values("Serial No").drop_duplicates(subset=["Serial No"], keep="first").reset_index(drop=True)

    return df[EXPECTED_COLS]