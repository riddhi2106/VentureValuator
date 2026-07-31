"""Dashboard — upload and run pitch deck analysis."""

import os
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import threading
import time

import streamlit as st

from app.components import (
    get_auth,
    render_results,
    render_stepper,
    run_pipeline_thread,
    save_uploaded_file,
    setup_page,
    sync_pipeline_from_store,
)
from app.pipeline_store import pipeline_store
from app.styles import AGENT_STEPS
from tools.pdf_reader import validate_pdf_text

setup_page(
    "Dashboard",
    "Upload a pitch deck to run extraction, market research, financial modeling, and investor scoring.",
)

st.markdown(
    """
    <div style="padding: 0.5rem 0; margin-bottom: 1.5rem;">
        <p style="margin: 0; color: #799e90; font-size: 0.95rem; line-height: 1.6;">
            Evaluate and stress-test startup opportunities using a team of specialized AI agents. 
            Upload a pitch deck PDF, and the platform will automatically run research on the market, 
            generate a financial forecast, perform skeptic risk assessment, and output a detailed investment memo.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

auth, test_mode = get_auth()

if st.session_state.pipeline_error:
    st.error(st.session_state.pipeline_error)

st.markdown('<div class="vv-card"><div class="vv-card-title">New analysis</div>', unsafe_allow_html=True)

upload_col, guide_col = st.columns([3, 2], gap="large")

with upload_col:
    uploaded = st.file_uploader(
        "Pitch deck PDF",
        type=["pdf"],
        label_visibility="collapsed",
        disabled=st.session_state.pipeline_running,
    )

    btn_run, btn_stop = st.columns(2)
    can_auth = test_mode or auth.authenticated
    run_disabled = uploaded is None or not can_auth or st.session_state.pipeline_running

    with btn_run:
        run_clicked = st.button("Run analysis", type="primary", disabled=run_disabled, width="stretch")
    with btn_stop:
        stop_clicked = st.button("Stop", type="secondary", disabled=not st.session_state.pipeline_running, width="stretch")

    if uploaded and not can_auth:
        st.caption("Sign in to ChatGPT before running. See connection status in sidebar.")

    if stop_clicked and st.session_state.pipeline_running:
        pipeline_store.request_cancel()
        st.session_state.cancel_requested = True

    if run_clicked and uploaded and can_auth and not st.session_state.pipeline_running:
        pdf_path = save_uploaded_file(uploaded)
        ok, pdf_err = validate_pdf_text(pdf_path)
        if not ok:
            st.error(pdf_err)
        else:
            pipeline_store.begin()
            st.session_state.pipeline_running = True
            st.session_state.pipeline_progress = {}
            st.session_state.pipeline_error = None
            st.session_state.cancel_requested = False
            st.session_state.show_results = False
            chatgpt_tokens = st.session_state.get("chatgpt_tokens")
            threading.Thread(
                target=run_pipeline_thread,
                args=(pdf_path, chatgpt_tokens),
                daemon=True,
            ).start()
            st.rerun()

with guide_col:
    with st.expander("Pipeline Details", expanded=True):
        st.markdown(
            """
            <div style="font-size: 0.88rem; color: #799e90; line-height: 1.75;">
                <p style="margin: 0 0 10px 0;">Our multi-agent pipeline triggers:</p>
                <div style="margin-bottom: 8px;"><b>1. Extract data</b></div>
                <div style="margin-bottom: 8px;"><b>2. Market research</b></div>
                <div style="margin-bottom: 8px;"><b>3. Financial model</b></div>
                <div style="margin-bottom: 8px;"><b>4. Skeptic review</b></div>
                <div style="margin-bottom: 8px;"><b>5. Memo & Deck</b></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("</div>", unsafe_allow_html=True)

sync_pipeline_from_store()

if st.session_state.pipeline_running:
    st.markdown('<div class="vv-card"><div class="vv-card-title">Pipeline progress</div>', unsafe_allow_html=True)
    if st.session_state.cancel_requested:
        st.caption("Stop requested — finishing current step, then halting.")
    render_stepper(st.session_state.pipeline_progress)
    progress = st.session_state.pipeline_progress
    completed = sum(1 for s, _ in AGENT_STEPS if progress.get(s, {}).get("phase") == "done")
    st.progress(completed / len(AGENT_STEPS), text=f"{completed} of {len(AGENT_STEPS)} steps complete")
    for step_key, _ in AGENT_STEPS:
        info = progress.get(step_key, {})
        if info.get("phase") == "start":
            st.caption(f"Running: {info.get('label', step_key)}")
            break
    st.markdown("</div>", unsafe_allow_html=True)
    time.sleep(1.2)
    st.rerun()

elif st.session_state.show_results and st.session_state.analysis_result:
    st.markdown('<div class="vv-card"><div class="vv-card-title">Results</div>', unsafe_allow_html=True)
    render_results(st.session_state.analysis_result)
    st.markdown("</div>", unsafe_allow_html=True)

else:
    st.markdown(
        """
        <div class="vv-card vv-empty">
            <p><strong>No analysis running.</strong></p>
            <p>Upload a pitch deck PDF above. Six agents will extract data, research the market,
            model finances, stress-test the pitch, score the opportunity, and generate a memo and deck.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)
st.page_link("pages/history.py", label="View full analysis history", icon="📋", width="stretch")
