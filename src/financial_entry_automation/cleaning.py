from __future__ import annotations

import re
from typing import Optional
from datetime import datetime

DATE_IN = re.compile(r"^\s*(\d{2})[-/](\d{2})[-/](\d{4})\s*$")
NUMERIC_OK = re.compile(r"^\d+(\.\d+)?$")

def normalize_date(date_str: str) -> Optional[str]:
    """Normalize a date into DD/MM/YYYY (accepts DD-MM-YYYY or DD/MM/YYYY)."""
    if date_str is None:
        return None
    m = DATE_IN.match(str(date_str))
    if not m:
        return None
    dd, mm, yyyy = m.groups()
    try:
        dt = datetime(int(yyyy), int(mm), int(dd))
    except ValueError:
        return None
    return dt.strftime("%d/%m/%Y")

def clean_cheque_number(chq: str) -> str:
    """Remove dashes; convert '-' or missing to empty."""
    if chq is None:
        return ""
    s = str(chq).strip()
    if s == "-" or s == "":
        return ""
    return s.replace("-", "").strip()

def clean_amount(val: str, dash_to_empty: bool = True) -> str:
    """Remove commas; convert '-' to empty (for Debit/Credit)."""
    if val is None:
        return ""
    s = str(val).strip()
    if dash_to_empty and s == "-":
        return ""
    return s.replace(",", "").strip()

def clean_description(desc: str) -> str:
    """Trim leading/trailing whitespace; preserve internal spacing."""
    if desc is None:
        return ""
    return str(desc).strip()

def validate_numeric(val: str) -> bool:
    """True if empty or matches digits + optional decimal."""
    if val is None or val == "":
        return True
    return bool(NUMERIC_OK.match(str(val)))
