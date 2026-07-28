"""Shared UI components for VentureValuator pages."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import time

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import streamlit as st

from app.pipeline_store import pipeline_store
from app.styles import AGENT_STEPS, CHART_COLORS, inject_theme
from core.memory_manager import memory
from core.orchestrator import (
    PipelineCancelledError,
    PipelineStepError,
    run_full_analysis,
)
from tools.auth_status import check_auth_status
from tools.llm_client import use_session_tokens
from tools.pdf_reader import validate_pdf_text
from tools.startup_name import resolve_startup_name


def init_session() -> None:
    defaults = {
        "analysis_result": None,
        "show_results": False,
        "auth_status": None,
        "pipeline_running": False,
        "cancel_requested": False,
        "pipeline_progress": {},
        "pipeline_error": None,
        "last_pdf_path": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def sync_pipeline_from_store() -> None:
    snap = pipeline_store.snapshot()
    st.session_state.pipeline_running = snap["running"]
    st.session_state.cancel_requested = snap["cancel_requested"]
    st.session_state.pipeline_progress = snap["progress"]
    st.session_state.show_results = snap["show_results"]
    st.session_state.pipeline_error = snap["error"]
    if snap["result"] is not None:
        st.session_state.analysis_result = snap["result"]


def setup_page(title: str, subtitle: str) -> None:
    init_session()
    inject_theme()
    sync_pipeline_from_store()
    st.markdown(
        '<div class="vv-logo" style="border-bottom: none; padding: 0 0 1rem 0; margin-bottom: 0;">Venture<span>Valuator</span></div>',
        unsafe_allow_html=True,
    )
    if title:
        st.title(title)
    if subtitle:
        st.markdown(f"<div style='margin-top: -15px; margin-bottom: 25px; color: #799e90; font-size: 0.95rem;'>{subtitle}</div>", unsafe_allow_html=True)


def is_test_mode() -> bool:
    return os.getenv("TEST_MODE", "false").lower() in ("true", "1", "yes")


def get_auth():
    if st.session_state.auth_status is None:
        st.session_state.auth_status = check_auth_status()
    return st.session_state.auth_status, is_test_mode()


def save_uploaded_file(uploaded_file) -> str:
    tmpdir = tempfile.mkdtemp(prefix="vv_upload_")
    out_path = os.path.join(tmpdir, uploaded_file.name)
    with open(out_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return out_path


def pretty_json(obj) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False)


def startup_name_for_result(result: dict) -> str:
    return resolve_startup_name(
        result.get("extracted", {}),
        pdf_path=result.get("pdf_path"),
    )


def run_pipeline_thread(
    pdf_path: str,
    chatgpt_tokens: object | None,
) -> None:
    def on_progress(step, label, phase, error=None):
        pipeline_store.update_progress(step, label, phase, error)

    try:
        with use_session_tokens(chatgpt_tokens):
            result = run_full_analysis(
                pdf_path,
                progress_callback=on_progress,
                cancel_check=pipeline_store.is_cancel_requested,
            )
        pipeline_store.finish_success(result)

    except PipelineCancelledError as e:
        pipeline_store.finish_cancelled(
            f"Analysis stopped before completing **{e.label}**."
        )

    except PipelineStepError as e:
        pipeline_store.finish_error(f"Failed during **{e.label}**: {e}")

    except RuntimeError as e:
        pipeline_store.finish_error(str(e))

    except Exception as e:
        pipeline_store.finish_error(f"Unexpected error: {e}")

def connection_html(auth, test_mode) -> str:
    if test_mode:
        return (
            '<p class="vv-status-line">'
            '<span class="vv-status-dot vv-status-warn"></span>'
            "Demo mode (TEST_MODE)"
            "</p>"
        )
    if auth.authenticated:
        method = "ChatGPT" if auth.method == "keyring" else auth.method or "connected"
        model = f" · {auth.model}" if auth.model else ""
        return (
            '<p class="vv-status-line">'
            '<span class="vv-status-dot vv-status-ok"></span>'
            f"Connected via {method}{model}"
            "</p>"
        )
    return (
        '<p class="vv-status-line">'
        '<span class="vv-status-dot vv-status-off"></span>'
        "Not connected — sign in to run analysis"
        "</p>"
    )


def render_overview_metrics(auth, test_mode) -> None:
    bank = memory.get_memory_bank()
    runs = memory.get_runs()
    last_score = "—"
    if bank:
        score = bank[-1].get("score")
        if score is not None:
            last_score = f"{score:.1f}/10"

    conn_label = "Demo" if test_mode else ("Connected" if auth.authenticated else "Offline")
    conn_class = "accent" if (test_mode or auth.authenticated) else ""

    st.markdown(
        f"""
        <div class="vv-metrics">
            <div class="vv-metric">
                <div class="vv-metric-label">Connection</div>
                <div class="vv-metric-value {conn_class}">{conn_label}</div>
            </div>
            <div class="vv-metric">
                <div class="vv-metric-label">Total analyses</div>
                <div class="vv-metric-value">{len(runs)}</div>
            </div>
            <div class="vv-metric">
                <div class="vv-metric-label">Latest score</div>
                <div class="vv-metric-value accent">{last_score}</div>
            </div>
            <div class="vv-metric">
                <div class="vv-metric-label">Agents</div>
                <div class="vv-metric-value">6</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_stepper(progress: dict) -> None:
    parts = []
    for step_key, step_label in AGENT_STEPS:
        info = progress.get(step_key, {})
        phase = info.get("phase", "pending")
        css = "vv-step"
        if phase == "start":
            css = "vv-step vv-step-active"
        elif phase == "done":
            css = "vv-step vv-step-done"
        elif phase == "error":
            css = "vv-step vv-step-error"
        if st.session_state.cancel_requested and phase == "start":
            css = "vv-step vv-step-cancelled"
        parts.append(f'<div class="{css}">{step_label}</div>')
    st.markdown(f'<div class="vv-stepper">{"".join(parts)}</div>', unsafe_allow_html=True)


def render_radar_chart(dimensions: dict, key: str = None) -> None:
    labels, scores = [], []
    for name, data in dimensions.items():
        if name.startswith("_"):
            continue
        labels.append(name.replace("_", " ").title())
        scores.append(data.get("score", 0))
    if not labels:
        return

    import plotly.graph_objects as go

    colors = CHART_COLORS
    primary = colors["primary"]
    r, g, b = int(primary[1:3], 16), int(primary[3:5], 16), int(primary[5:7], 16)
    fill_color = f"rgba({r},{g},{b},0.18)"

    fig = go.Figure(data=go.Scatterpolar(
        r=scores + [scores[0]],
        theta=labels + [labels[0]],
        fill="toself",
        fillcolor=fill_color,
        line=dict(color=colors["primary"], width=2),
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True, range=[0, 10],
                gridcolor=colors["grid"], linecolor=colors["grid"],
                tickfont=dict(color=colors["text"], size=10),
            ),
            angularaxis=dict(tickfont=dict(color=colors["text"], size=10)),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=colors["text"], size=11),
        showlegend=False,
        margin=dict(l=40, r=40, t=20, b=20),
        height=340,
    )
    st.plotly_chart(fig, width="stretch", key=key)


def render_revenue_chart(financial: dict, key: str = None) -> None:
    scenarios = financial.get("scenarios", {})
    base = scenarios.get("base", {})
    series = base.get("revenue_series", [])
    if not series:
        return

    import plotly.graph_objects as go

    colors = CHART_COLORS
    months = list(range(1, len(series) + 1))
    fig = go.Figure()
    
    # Add a glowing "shadow" trace below the main line
    fig.add_trace(go.Scatter(
        x=months, y=series, mode="lines", name="Glow",
        line=dict(color=colors["primary"], width=8), opacity=0.2, hoverinfo="skip", showlegend=False
    ))
    
    fig.add_trace(go.Scatter(
        x=months, y=series, mode="lines+markers", name="Base",
        line=dict(color=colors["primary"], width=3), 
        marker=dict(size=8, color=colors["primary"], line=dict(color="#ffffff", width=2)),
    ))
    
    for name in ("conservative", "optimistic"):
        alt = scenarios.get(name, {}).get("revenue_series", [])
        if alt:
            fig.add_trace(go.Scatter(
                x=list(range(1, len(alt) + 1)), y=alt, mode="lines",
                name=name.title(),
                line=dict(color=colors["secondary"], dash="dash", width=1.5),
            ))
            
    fig.update_layout(
        title=dict(text="24-month revenue projection", font=dict(size=14, color=colors["text"])),
        xaxis_title="Month", yaxis_title="Revenue ($)", height=320,
        margin=dict(l=48, r=16, t=40, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=11, color=colors["text"])),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=colors["text"], size=12),
        xaxis=dict(gridcolor=colors["grid"], tickfont=dict(color=colors["text"])),
        yaxis=dict(gridcolor=colors["grid"], tickfont=dict(color=colors["text"])),
    )
    st.plotly_chart(fig, width="stretch", key=key)


def render_results(result: dict) -> None:
    memo_out = result.get("memo", {})
    evaluation = memo_out.get("evaluation", {})
    overall = evaluation.get("overall", {})
    extracted = result.get("extracted", {})
    market = result.get("market", {})
    financial = result.get("financial_model", {})
    skeptic = result.get("skeptic", {})
    memo_text = memo_out.get("memo_text", "")
    startup_name = startup_name_for_result(result)
    score = overall.get("score", 0)
    verdict = overall.get("verdict", "—")
    conf = overall.get("confidence", 0)

    st.markdown(
        f"""
        <div class="vv-verdict">
            <div class="vv-verdict-score">{score:.1f}<span style="font-size:1.25rem;font-weight:400;opacity:0.75"> / 10</span></div>
            <div class="vv-verdict-meta">{verdict} · {conf:.0%} confidence</div>
            <div class="vv-verdict-name">{startup_name}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption(f"Completed {result.get('timestamp', '')}")

    ts_key = result.get("timestamp", "").replace(" ", "_").replace(":", "_").replace("-", "_")
    key_suffix = ts_key if ts_key else str(id(result))

    d1, d2, d3 = st.columns(3)
    with d1:
        st.download_button(
            "Download memo",
            memo_text,
            "memo.txt",
            "text/plain",
            width="stretch",
            key=f"btn_dl_memo_{key_suffix}"
        )
    with d2:
        st.download_button(
            "Download JSON",
            pretty_json(result),
            "analysis.json",
            "application/json",
            width="stretch",
            key=f"btn_dl_json_{key_suffix}"
        )
    with d3:
        pptx_path = result.get("deck")
        if pptx_path and os.path.exists(pptx_path):
            with open(pptx_path, "rb") as f:
                st.download_button(
                    "Download pitch deck", f.read(), os.path.basename(pptx_path),
                    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    width="stretch",
                    key=f"btn_dl_deck_{key_suffix}"
                )

    tabs = st.tabs(["Overview", "Market", "Financials", "Skeptic review", "Memo", "Sensitivity Sandbox", "Raw data"])

    with tabs[0]:
        dimensions = evaluation.get("dimensions", {})
        if dimensions:
            c1, c2 = st.columns([1, 1])
            with c1:
                st.markdown("**Score breakdown**")
                render_radar_chart(dimensions, key=f"chart_radar_{key_suffix}")
            with c2:
                for name, data in dimensions.items():
                    if name.startswith("_"):
                        continue
                    label = name.replace("_", " ").title()
                    st.markdown(f"**{label}** · {data.get('weight', 0):.0%}")
                    st.progress(data.get("score", 0) / 10)
                    st.caption(data.get("rationale", ""))

        s_col, r_col = st.columns(2)
        with s_col:
            st.markdown("**Strengths**")
            for s in evaluation.get("strengths", []):
                st.markdown(f"- {s}")
        with r_col:
            st.markdown("**Risks**")
            for r in evaluation.get("risks", []):
                st.markdown(f"- {r}")

        solution = extracted.get("solution", "")
        if isinstance(solution, list):
            solution = " ".join(str(x) for x in solution)
        if solution:
            st.markdown("**Summary**")
            st.markdown(solution[:400])

    with tabs[1]:
        cols = st.columns(4)
        metrics = [
            ("Category", market.get("market_category")),
            ("TAM", market.get("tam")),
            ("SAM", market.get("sam")),
            ("Growth", market.get("market_growth_rate")),
        ]
        for col, (label, val) in zip(cols, metrics):
            if val:
                col.metric(label, val)
        if market.get("summary_insights"):
            st.markdown(market["summary_insights"])
        for t in market.get("key_trends", []):
            st.markdown(f"- {t}")
        sources = market.get("sources") or []
        if sources:
            st.markdown("**Sources**")
            for src in sources[:8]:
                title = src.get("title", "Source")
                url = src.get("url", "")
                if url:
                    st.markdown(f"- [{title}]({url})")
                else:
                    st.markdown(f"- {title}")
                if src.get("snippet"):
                    st.caption(src["snippet"][:160])

    with tabs[2]:
        summary = financial.get("summary", {})
        if summary:
            fcols = st.columns(4)
            fmetrics = [
                ("Monthly revenue", f"${summary['revenue_monthly_start']:,.0f}" if summary.get("revenue_monthly_start") else None),
                ("Gross margin", f"{summary['gross_margin'] * 100:.0f}%" if summary.get("gross_margin") is not None else None),
                ("CAC", f"${summary['cac']:,.0f}" if summary.get("cac") else None),
                ("ARPU", f"${summary['arpu_monthly']:,.0f}" if summary.get("arpu_monthly") else None),
            ]
            for col, (label, val) in zip(fcols, fmetrics):
                if val:
                    col.metric(label, val)
        render_revenue_chart(financial, key=f"chart_revenue_{key_suffix}")
        base = financial.get("scenarios", {}).get("base", {})
        cac_ltv = base.get("cac_ltv", {})
        if cac_ltv:
            u1, u2, u3 = st.columns(3)
            if cac_ltv.get("ltv"):
                u1.metric("LTV", f"${cac_ltv['ltv']:,.0f}")
            if cac_ltv.get("ltv_cac_ratio"):
                u2.metric("LTV/CAC", f"{cac_ltv['ltv_cac_ratio']:.1f}x")
            if base.get("breakeven_month"):
                u3.metric("Breakeven (month)", str(base["breakeven_month"]))

    with tabs[3]:
        if skeptic and not skeptic.get("error"):
            if skeptic.get("skeptic_summary"):
                st.markdown(skeptic["skeptic_summary"])
            if skeptic.get("partner_questions"):
                st.markdown("**Partner questions**")
                for i, q in enumerate(skeptic["partner_questions"], 1):
                    st.markdown(f"{i}. {q}")
            sk1, sk2 = st.columns(2)
            with sk1:
                for label, key in [("Red flags", "red_flags"), ("Claims to verify", "challenged_claims")]:
                    if skeptic.get(key):
                        st.markdown(f"**{label}**")
                        for item in skeptic[key]:
                            st.markdown(f"- {item}")
            with sk2:
                for label, key in [("Missing data", "missing_data"), ("Diligence steps", "diligence_next_steps")]:
                    if skeptic.get(key):
                        st.markdown(f"**{label}**")
                        for item in skeptic[key]:
                            st.markdown(f"- {item}")
        else:
            st.caption("No skeptic review available.")

    with tabs[4]:
        st.text_area("Memo", memo_text, height=460, disabled=True, label_visibility="collapsed", key=f"txt_memo_{key_suffix}")

    with tabs[5]:
        st.subheader("Interactive Valuation Sandbox")
        st.markdown("Adjust key score inputs and financial assumptions to see how they impact the overall opportunity evaluation.")
        
        sandbox_col1, sandbox_col2 = st.columns(2, gap="large")
        
        with sandbox_col1:
            st.markdown("### Score Sensitivity")
            dimensions = evaluation.get("dimensions", {})
            new_scores = {}
            total_weight = 0
            weighted_score = 0
            
            for name, data in dimensions.items():
                if name.startswith("_"):
                    continue
                label = name.replace("_", " ").title()
                weight = data.get("weight", 0)
                orig_score = float(data.get("score", 0))
                
                # Render slider
                new_val = st.slider(
                    f"{label} (Weight: {weight:.0%})",
                    min_value=0.0,
                    max_value=10.0,
                    value=orig_score,
                    step=0.5,
                    key=f"sb_score_{name}_{key_suffix}"
                )
                new_scores[name] = new_val
                weighted_score += new_val * weight
                total_weight += weight
                
            final_weighted = weighted_score / total_weight if total_weight > 0 else 0
            
            # Show verdict comparison
            orig_overall = overall.get("score", 0)
            diff = final_weighted - orig_overall
            diff_text = f" ({diff:+.1f})" if diff != 0 else ""
            
            st.markdown(
                f"""
                <div class="vv-verdict" style="margin-top: 15px; padding: 15px;">
                    <div class="vv-verdict-score">{final_weighted:.1f}<span style="font-size:1rem;font-weight:400;opacity:0.75"> / 10</span></div>
                    <div class="vv-verdict-meta">Adjusted Score {diff_text}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            
        with sandbox_col2:
            st.markdown("### Financial Assumptions")
            base = financial.get("scenarios", {}).get("base", {})
            cac_ltv = base.get("cac_ltv", {})
            
            orig_ltv = float(cac_ltv.get("ltv") or 1000)
            orig_cac = float(cac_ltv.get("cac") or 300)
            
            new_ltv = st.slider("Target LTV ($)", min_value=10.0, max_value=max(10000.0, orig_ltv * 3.0), value=orig_ltv, step=50.0, key=f"sb_ltv_{key_suffix}")
            new_cac = st.slider("Target CAC ($)", min_value=10.0, max_value=max(3000.0, orig_cac * 3.0), value=orig_cac, step=10.0, key=f"sb_cac_{key_suffix}")
            
            new_ratio = new_ltv / new_cac if new_cac > 0 else 0
            
            ratio_status = "Excellent" if new_ratio >= 3.0 else ("Moderate" if new_ratio >= 1.5 else "Risky")
            ratio_color = "#3dd9b0" if new_ratio >= 3.0 else ("#f59e0b" if new_ratio >= 1.5 else "#ef4444")
            
            st.markdown(
                f"""
                <div style="background: rgba(17, 28, 46, 0.6); border: 1px solid #1e2d45; border-radius: 12px; padding: 15px; margin-top: 20px; text-align: center;">
                    <div style="font-size: 0.75rem; text-transform: uppercase; color: #8b9cb3; margin-bottom: 5px;">Adjusted LTV/CAC Ratio</div>
                    <div style="font-size: 2rem; font-weight: 700; color: {ratio_color};">{new_ratio:.1f}x</div>
                    <div style="font-size: 0.85rem; color: #8b9cb3; margin-top: 5px;">Status: <span style="color: {ratio_color}; font-weight: 600;">{ratio_status}</span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with tabs[6]:
        st.json({"extracted": extracted, "market": market, "financial": financial, "skeptic": skeptic})
