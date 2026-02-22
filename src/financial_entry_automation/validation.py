from __future__ import annotations

from typing import List, Tuple, Dict, Any
import pandas as pd

from .utils import ValidationIssue
from .cleaning import validate_numeric

def validate_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[ValidationIssue]]:
    """
    Validation checks:
    - Column presence and order
    - Serial numbers int-like + sequential warning
    - Numeric fields valid
    - Balance present
    - Debit/Credit mutual-exclusion warning
    - Commas in Description warning + replacement (CSV has no quoting)
    """
    issues: List[ValidationIssue] = []

    expected_cols = ["Serial No","Transaction Date","Value Date","Description","Cheque Number","Debit","Credit","Balance"]
    missing = [c for c in expected_cols if c not in df.columns]
    if missing:
        issues.append(ValidationIssue(serial_no=None, level="error", message=f"Missing required columns: {missing}"))
        return df, issues

    df = df[expected_cols].copy()

    try:
        ser = df["Serial No"].astype(int)
        df["Serial No"] = ser
        expected = list(range(int(ser.min()), int(ser.max()) + 1))
        if ser.tolist() != expected:
            issues.append(ValidationIssue(serial_no=None, level="warning",
                                          message="Serial numbers are not perfectly sequential. This may indicate missing/duplicate rows.",
                                          context={"min": int(ser.min()), "max": int(ser.max())}))
    except Exception as e:
        issues.append(ValidationIssue(serial_no=None, level="error", message=f"Serial No column is not numeric: {e}"))
        return df, issues

    for _, row in df.iterrows():
        sn = int(row["Serial No"])
        for col in ["Debit","Credit","Balance"]:
            if not validate_numeric(row[col]):
                issues.append(ValidationIssue(serial_no=sn, level="error",
                                              message=f"Invalid numeric format in {col}: {row[col]}"))

        if row["Balance"] in (None, ""):
            issues.append(ValidationIssue(serial_no=sn, level="error", message="Missing Balance value"))

        d, c = (row["Debit"] or ""), (row["Credit"] or "")
        if (d == "" and c == "") or (d != "" and c != ""):
            issues.append(ValidationIssue(serial_no=sn, level="warning",
                                          message="Expected exactly one of Debit/Credit to be filled for a transaction."))

        if "," in (row["Description"] or ""):
            issues.append(ValidationIssue(serial_no=sn, level="warning",
                                          message="Description contains a comma. CSV output is configured to avoid quotes; comma was replaced with a space."))
            df.loc[df["Serial No"] == sn, "Description"] = (row["Description"] or "").replace(",", " ")

        if not row["Transaction Date"]:
            issues.append(ValidationIssue(serial_no=sn, level="error", message="Missing Transaction Date"))
        if not row["Value Date"]:
            issues.append(ValidationIssue(serial_no=sn, level="warning", message="Missing Value Date"))

    return df, issues

def summarize_issues(issues: List[ValidationIssue]) -> Dict[str, Any]:
    return {
        "total": len(issues),
        "errors": sum(1 for i in issues if i.level == "error"),
        "warnings": sum(1 for i in issues if i.level == "warning"),
    }
