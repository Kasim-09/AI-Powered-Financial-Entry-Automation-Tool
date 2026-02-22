from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st
import pandas as pd

from src.financial_entry_automation.pdf_extractor import extract_transactions_pdfplumber
from src.financial_entry_automation.validation import validate_dataframe, summarize_issues
from src.financial_entry_automation.exporter import dataframe_to_csv_bytes

st.set_page_config(page_title="AI-Powered Financial Entry Automation Tool", layout="wide")

st.title("AI-Powered Financial Entry Automation Tool")
st.caption("Upload a bank statement PDF → extract transactions → validate/clean → download a strict CSV.")

uploaded = st.file_uploader("Upload bank statement PDF", type=["pdf"])

left, right = st.columns([2, 1], gap="large")

if uploaded is None:
    st.info("Upload a PDF to begin.")
    st.stop()

with tempfile.TemporaryDirectory() as td:
    pdf_path = Path(td) / uploaded.name
    pdf_path.write_bytes(uploaded.getbuffer())

    with st.spinner("Extracting transactions from PDF..."):
        df_raw, extraction_issues = extract_transactions_pdfplumber(str(pdf_path))

    if df_raw.empty:
        st.error("No transactions extracted.")
        if extraction_issues:
            st.subheader("Extraction issues")
            st.dataframe(pd.DataFrame([i.__dict__ for i in extraction_issues]), use_container_width=True)
        st.stop()

    with st.spinner("Cleaning & validating extracted data..."):
        df_clean, validation_issues = validate_dataframe(df_raw)

    issues = extraction_issues + validation_issues
    summary = summarize_issues(issues)

    with right:
        st.subheader("Data quality summary")
        st.metric("Rows extracted", int(df_raw.shape[0]))
        st.metric("Warnings", int(summary["warnings"]))
        st.metric("Errors", int(summary["errors"]))

        if summary["errors"] > 0:
            st.error("Errors found. Review flagged rows before exporting.")
        elif summary["warnings"] > 0:
            st.warning("Warnings found. Review flagged rows.")
        else:
            st.success("No issues found.")

    with left:
        st.subheader("Preview (cleaned)")
        st.dataframe(df_clean, use_container_width=True, hide_index=True)

        if issues:
            st.subheader("Validation warnings / errors")
            issue_df = pd.DataFrame([{
                "Serial No": i.serial_no,
                "Level": i.level,
                "Message": i.message
            } for i in issues]).sort_values(["Level","Serial No"], ascending=[False, True])
            st.dataframe(issue_df, use_container_width=True, hide_index=True)

    if summary["errors"] == 0:
        csv_bytes, filename = dataframe_to_csv_bytes(df_clean)
        st.download_button(
            label="Download clean CSV",
            data=csv_bytes,
            file_name=filename,
            mime="text/csv"
        )
    else:
        st.warning("Fix the errors above (or adjust parsing rules) before exporting.")
