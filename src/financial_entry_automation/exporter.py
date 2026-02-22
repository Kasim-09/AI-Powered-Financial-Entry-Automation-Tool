from __future__ import annotations

import csv
import io
from typing import Tuple
import pandas as pd

EXPECTED_HEADER = ["Serial No","Transaction Date","Value Date","Description","Cheque Number","Debit","Credit","Balance"]

def dataframe_to_csv_bytes(df: pd.DataFrame) -> Tuple[bytes, str]:
    """
    Export to a strict CSV format:
    - Comma-separated
    - No surrounding quotes
    - No empty rows
    NOTE: Because quoting is disabled, commas inside fields must be removed upstream.
    """
    out = io.StringIO()
    writer = csv.writer(out, delimiter=",", quoting=csv.QUOTE_NONE, escapechar="\\", lineterminator="\n")
    writer.writerow(EXPECTED_HEADER)
    for _, row in df.iterrows():
        writer.writerow([row.get(c, "") for c in EXPECTED_HEADER])
    return out.getvalue().encode("utf-8"), "transactions_clean.csv"
