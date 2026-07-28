"""Analysis history — browse all past pitch deck runs."""

import os
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import streamlit as st

from app.components import (
    pretty_json,
    render_results,
    setup_page,
    startup_name_for_result,
)
from core.memory_manager import memory


setup_page(
    "Analysis history",
    "Browse every pitch deck you've analyzed — scores, verdicts, and full reports.",
)

runs = list(reversed(memory.get_runs()))

if not runs:
    st.markdown(
        """
        <div class="vv-card vv-empty">
            <p><strong>No analyses yet.</strong></p>
            <p>Run your first pitch deck from the Dashboard. Results will appear here automatically.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.page_link("pages/dashboard.py", label="Go to Dashboard", icon=":material/dashboard:", width="stretch")
else:
    st.markdown('<div class="vv-card"><div class="vv-card-title">Startup Comparison Sandbox</div>', unsafe_allow_html=True)
    options = []
    run_map = {}
    for i, run in enumerate(runs):
        data = run.get("data", {})
        name = startup_name_for_result(data)
        score = data.get("memo", {}).get("evaluation", {}).get("overall", {}).get("score")
        score_str = f"{score:.1f}/10" if score is not None else "No score"
        date_short = run.get("timestamp", "")[:10]
        label = f"{name} ({score_str} — {date_short})"
        options.append(label)
        run_map[label] = run

    selected_labels = st.multiselect(
        "Select up to 3 startups to compare side-by-side:",
        options=options,
        max_selections=3,
        placeholder="Choose startups to compare...",
    )
    
    if selected_labels:
        cols = st.columns(len(selected_labels))
        for col, label in zip(cols, selected_labels):
            run = run_map[label]
            data = run.get("data", {})
            memo = data.get("memo", {})
            evaluation = memo.get("evaluation", {})
            overall = evaluation.get("overall", {})
            market = data.get("market", {})
            financial = data.get("financial_model", {})
            base = financial.get("scenarios", {}).get("base", {})
            cac_ltv = base.get("cac_ltv", {})
            
            name = startup_name_for_result(data)
            score = overall.get("score", 0)
            verdict = overall.get("verdict", "—")
            category = market.get("market_category", "—")
            tam = market.get("tam", "—")
            ltv = cac_ltv.get("ltv")
            cac = cac_ltv.get("cac")
            ltv_cac = cac_ltv.get("ltv_cac_ratio")
            
            with col:
                ltv_val = f"${ltv:,.0f}" if isinstance(ltv, (int, float)) else str(ltv)
                cac_val = f"${cac:,.0f}" if isinstance(cac, (int, float)) else str(cac)
                ltv_cac_val = f"{ltv_cac:.1f}x" if isinstance(ltv_cac, (int, float)) else "—"
                st.markdown(
                    f"""
                    <div style="background: rgba(17, 28, 46, 0.8); border: 2px solid #3dd9b0; border-radius: 16px; padding: 20px; text-align: center; margin-bottom: 20px;">
                        <h3 style="margin: 0 0 5px 0; color: #f8fafc; font-size: 1.2rem;">{name}</h3>
                        <div style="font-size: 2.25rem; font-weight: 700; color: #3dd9b0; margin: 10px 0;">{score:.1f}</div>
                        <div style="font-size: 0.9rem; font-weight: 600; color: #8b9cb3; text-transform: uppercase; margin-bottom: 15px;">{verdict}</div>
                        <hr style="border-color: #1e2d45; margin: 15px 0;" />
                        <div style="text-align: left; font-size: 0.85rem; color: #8b9cb3; line-height: 1.8;">
                            <p style="margin: 4px 0;"><b>Category:</b> {category}</p>
                            <p style="margin: 4px 0;"><b>TAM:</b> {tam}</p>
                            <p style="margin: 4px 0;"><b>LTV:</b> {ltv_val}</p>
                            <p style="margin: 4px 0;"><b>CAC:</b> {cac_val}</p>
                            <p style="margin: 4px 0;"><b>LTV/CAC:</b> {ltv_cac_val}</p>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="vv-card"><div class="vv-card-title">All analyses</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="vv-table-row vv-table-head">
            <div>Startup</div>
            <div>Score</div>
            <div>Verdict</div>
            <div>Category</div>
            <div>Date</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for i, run in enumerate(runs):
        data = run.get("data", {})
        ts = run.get("timestamp", data.get("timestamp", ""))
        extracted = data.get("extracted", {})
        memo = data.get("memo", {})
        evaluation = memo.get("evaluation", {})
        overall = evaluation.get("overall", {})
        market = data.get("market", {})

        name = startup_name_for_result(data)
        score = overall.get("score")
        verdict = overall.get("verdict", "—")
        category = market.get("market_category", "—")
        date_short = ts[:10] if ts else "—"

        score_html = f'<span class="vv-score-pill">{score:.1f}</span>' if score is not None else "—"
        verdict_html = f'<span class="vv-verdict-pill">{verdict}</span>' if verdict != "—" else "—"

        st.markdown(
            f"""
            <div class="vv-table-row">
                <div><div class="vv-table-name">{name}</div></div>
                <div>{score_html}</div>
                <div>{verdict_html}</div>
                <div class="vv-table-meta">{category}</div>
                <div class="vv-table-meta">{date_short}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander(f"View report — {name}"):
            render_results(data)
            st.download_button(
                "Download JSON",
                pretty_json(data),
                file_name=f"analysis_{date_short}_{name.replace(' ', '_')}.json",
                mime="application/json",
                key=f"dl_json_{i}",
            )

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.page_link("pages/dashboard.py", label="Back to Dashboard", icon=":material/dashboard:", width="stretch")
