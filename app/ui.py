import streamlit as st
import os
import json
import tempfile
import sys
from datetime import datetime

# Fix import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.orchestrator import run_full_analysis
from core.memory_manager import memory


# ---------------------------
# CONFIG
# ---------------------------
st.set_page_config(page_title="VentureValuator", layout="wide")

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

if "last_pdf_path" not in st.session_state:
    st.session_state.last_pdf_path = None

if "show_results" not in st.session_state:
    st.session_state.show_results = False


# ---------------------------
# HELPERS
# ---------------------------
def save_uploaded_file(uploaded_file):
    tmpdir = tempfile.mkdtemp(prefix="vv_upload_")
    out_path = os.path.join(tmpdir, uploaded_file.name)
    with open(out_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return out_path


def pretty_json(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False)


# ---------------------------
# HEADER
# ---------------------------
st.title("VentureValuator")
st.markdown("Upload a pitch deck PDF and run a full automated analysis.")


# ---------------------------
# SIDEBAR MEMORY VIEW
# ---------------------------
st.sidebar.title("Memory")

if st.sidebar.button("Show previous runs"):
    runs = memory.get_runs()
    if not runs:
        st.sidebar.info("No previous runs yet.")
    else:
        for i, r in enumerate(runs):
            st.sidebar.subheader(f"Run {i+1}")
            st.sidebar.json(r)

if st.sidebar.button("Show summaries"):
    summaries = memory.get_memory_bank()
    if not summaries:
        st.sidebar.info("No summaries saved.")
    else:
        for i, s in enumerate(summaries):
            st.sidebar.subheader("Summary")
            st.sidebar.json(s)


# ---------------------------
# FILE UPLOAD
# ---------------------------
uploaded = st.file_uploader("Upload pitch PDF", type=["pdf"])

run_col, _ = st.columns([1, 3])

if uploaded and run_col.button("▶️ Run analysis", type="primary"):
    pdf_path = save_uploaded_file(uploaded)
    st.session_state.last_pdf_path = pdf_path

    with st.spinner("Running analysis…"):
        result = run_full_analysis(pdf_path)

    st.session_state.analysis_result = result
    st.session_state.show_results = True


# ---------------------------
# DISPLAY RESULTS
# ---------------------------
if st.session_state.show_results and st.session_state.analysis_result:

    result = st.session_state.analysis_result
    ts = result.get("timestamp", "")

    st.success(f"Analysis completed — {ts}")

    # ---------- Extracted Data ----------
    st.subheader("Extracted Data")
    st.json(result.get("extracted", {}))

    # ---------- Market ----------
    st.subheader("Market Analysis")
    st.json(result.get("market", {}))

    # ---------- Financial ----------
    st.subheader("Financial Model")
    fin = result.get("financial_model", {})
    st.write("**Summary:**")
    if fin.get("summary"):
        st.write(fin["summary"])
    st.expander("Full financial JSON").json(fin)

    # ---------- Memo ----------
    st.subheader("Investor Memo")
    memo_out = result.get("memo", {})
    memo_text = memo_out.get("memo_text", "")
    st.text_area("Memo Preview", memo_text, height=300)

    # Download TXT only
    st.download_button(
        label="Download memo.txt",
        data=memo_text,
        file_name="memo.txt",
        mime="text/plain",
        key="download_memo_txt"
    )

    # ---------- Pitch Deck ----------
    st.subheader("Generated Pitch Deck")

    pptx_path = result.get("deck")
    if pptx_path and os.path.exists(pptx_path):
        with open(pptx_path, "rb") as f:
            deck_bytes = f.read()

        st.download_button(
            label="Download pitch deck (.pptx)",
            data=deck_bytes,
            file_name=os.path.basename(pptx_path),
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            key="download_pptx"
        )
    else:
        st.warning("Pitch deck file not found.")

    # Keep screen from resetting
    st.session_state.show_results = True
