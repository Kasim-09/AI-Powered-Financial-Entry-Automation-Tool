from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from src.financial_entry_automation.pdf_extractor import extract_transactions_pdfplumber
from src.financial_entry_automation.validation import validate_dataframe, summarize_issues
from src.financial_entry_automation.exporter import dataframe_to_csv_bytes

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(
    page_title="Financial Entry Automation",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# Minimal CSS polish (no extra deps)
# -----------------------------
st.markdown(
    """
<style>
/* tighter overall spacing */
.block-container { padding-top: 1.2rem; padding-bottom: 2.5rem; }

/* nicer metric cards */
[data-testid="stMetric"] {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.10);
  padding: 14px 16px;
  border-radius: 16px;
}

/* section headers */
.section-title {
  font-size: 1.1rem;
  font-weight: 700;
  margin: 0.25rem 0 0.5rem 0;
}

/* subtle cards */
.card {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.10);
  border-radius: 18px;
  padding: 14px 16px;
}

/* make dataframes feel like cards */
[data-testid="stDataFrame"] {
  border-radius: 18px;
  overflow: hidden;
  border: 1px solid rgba(255,255,255,0.10);
}

/* buttons a bit rounder */
.stDownloadButton button, .stButton button {
  border-radius: 14px !important;
  padding: 0.6rem 0.9rem !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# -----------------------------
# Header
# -----------------------------
left_title, right_title = st.columns([3, 1], vertical_alignment="center")
with left_title:
    st.title("💳 AI-Powered Financial Entry Automation")
    st.caption("Upload a bank statement PDF → extract transactions → validate/clean → download a strict CSV.")
with right_title:
    st.markdown(
        """
<div class="card" style="margin-top:30px">
  <div style="font-weight:700;">Output columns</div>
  <div style="opacity:0.9; font-size:0.9rem; margin-top:8px;">
    Serial No, Transaction Date, Value Date, Description, Cheque Number, Debit, Credit, Balance
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

st.divider()

# -----------------------------
# Sidebar controls
# -----------------------------
with st.sidebar:
    st.header("📄 Input")
    uploaded = st.file_uploader("Upload bank statement PDF", type=["pdf"])
    st.markdown("---")
    st.subheader("⚙️ Options")
    show_raw = st.toggle("Show raw extracted rows", value=False)
    show_debug = st.toggle("Show debug details", value=False)
    st.markdown("---")
    st.caption("Tip: If extraction looks off, try another PDF export or scanned-version text layer.")

if uploaded is None:
    st.info("Upload a PDF from the sidebar to begin.")
    st.stop()

# -----------------------------
# Processing
# -----------------------------
status = st.status("Step 1/3 — Extracting transactions from PDF…", expanded=True)

with tempfile.TemporaryDirectory() as td:
    pdf_path = Path(td) / uploaded.name
    pdf_path.write_bytes(uploaded.getbuffer())

    try:
        df_raw, extraction_issues = extract_transactions_pdfplumber(str(pdf_path))
    except Exception as e:
        status.update(label="Extraction failed.", state="error")
        st.error(f"Extraction failed: {e}")
        st.stop()

    if df_raw.empty:
        status.update(label="No transactions extracted.", state="error")
        st.error("No transactions extracted from the PDF.")
        if extraction_issues:
            st.subheader("Extraction issues")
            st.dataframe(pd.DataFrame([i.__dict__ for i in extraction_issues]), use_container_width=True, hide_index=True)
        st.stop()

    status.update(label="Step 2/3 — Validating and cleaning…", state="running")

    df_clean, validation_issues = validate_dataframe(df_raw)
    issues = extraction_issues + validation_issues
    summary = summarize_issues(issues)

    if summary["errors"] > 0:
        status.update(label="Step 3/3 — Review required (errors found).", state="error")
    elif summary["warnings"] > 0:
        status.update(label="Step 3/3 — Ready to export (warnings found).", state="complete")
    else:
        status.update(label="Step 3/3 — Ready to export (no issues).", state="complete")

# -----------------------------
# Dashboard row
# -----------------------------
m1, m2, m3, m4 = st.columns([1.1, 1, 1, 1.2])
m1.metric("Rows extracted", int(df_raw.shape[0]))
m2.metric("Warnings", int(summary["warnings"]))
m3.metric("Errors", int(summary["errors"]))
m4.metric("Rows ready to export", int(df_clean.shape[0]) if summary["errors"] == 0 else 0)

# Helpful banner
if summary["errors"] > 0:
    st.error("Errors found. Review flagged rows before exporting.")
elif summary["warnings"] > 0:
    st.warning("Warnings found. You can still export, but review is recommended.")
else:
    st.success("All checks passed. You can export safely.")

# -----------------------------
# Main content: tabs
# -----------------------------
tab_preview, tab_issues, tab_export = st.tabs(["📊 Preview", "🛡️ Validation", "⬇️ Export"])

with tab_preview:
    st.markdown('<div class="section-title">Cleaned data preview</div>', unsafe_allow_html=True)
    st.dataframe(df_clean, use_container_width=True, hide_index=True)

    if show_raw:
        with st.expander("Show raw extracted rows (before validation)", expanded=False):
            st.dataframe(df_raw, use_container_width=True, hide_index=True)

with tab_issues:
    st.markdown('<div class="section-title">Warnings / errors</div>', unsafe_allow_html=True)
    if not issues:
        st.success("No validation issues to show.")
    else:
        issue_df = pd.DataFrame(
            [{"Serial No": i.serial_no, "Level": i.level, "Message": i.message} for i in issues]
        )

        # Order: errors first, then warnings; by serial
        level_order = {"error": 0, "warning": 1}
        issue_df["__level_order"] = issue_df["Level"].map(level_order).fillna(99).astype(int)
        issue_df["__serial_sort"] = issue_df["Serial No"].fillna(10**9).astype(int)
        issue_df = issue_df.sort_values(["__level_order", "__serial_sort"]).drop(
            columns=["__level_order", "__serial_sort"]
        )

        err_ct = int((issue_df["Level"] == "error").sum())
        warn_ct = int((issue_df["Level"] == "warning").sum())
        c1, c2 = st.columns(2)
        c1.metric("Errors", err_ct)
        c2.metric("Warnings", warn_ct)

        st.dataframe(issue_df, use_container_width=True, hide_index=True)

        if show_debug:
            with st.expander("Debug details (raw issue payload)", expanded=False):
                st.json([i.__dict__ for i in issues])

with tab_export:
    st.markdown('<div class="section-title">Download CSV</div>', unsafe_allow_html=True)

    st.markdown(
        """
<div class="card" style="margin-bottom: 10px;">
  <div style="font-weight:700;">CSV rules</div>
  <ul style="margin-top:8px; margin-bottom:0;">
    <li>Header: Serial No,Transaction Date,Value Date,Description,Cheque Number,Debit,Credit,Balance</li>
    <li>No surrounding quotes; comma-safe descriptions enforced</li>
    <li>One transaction per row; no empty rows</li>
  </ul>
</div>
""",
        unsafe_allow_html=True,
    )

    if summary["errors"] > 0:
        st.warning("Export is disabled because errors were found. Fix the errors (or adjust parsing rules) and try again.")
    else:
        csv_bytes, filename = dataframe_to_csv_bytes(df_clean)
        st.download_button(
            label="⬇️ Download clean CSV",
            data=csv_bytes,
            file_name=filename,
            mime="text/csv",
            use_container_width=False,
        )
        st.caption("If your downstream system is strict, keep descriptions comma-free and ensure numeric fields are valid.")