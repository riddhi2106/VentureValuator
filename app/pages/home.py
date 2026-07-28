"""Homepage for VentureValuator."""

import streamlit as st

from app.components import get_auth, render_overview_metrics, setup_page

setup_page("", "")

st.markdown(
    """
    <style>
    /* ── Animated hero canvas ── */
    .vv-hero {
        position: relative;
        overflow: hidden;
        border-radius: 22px;
        border: 1px solid #1e3b33;
        padding: 5rem 2.5rem 4rem;
        text-align: center;
        margin-bottom: 2.5rem;
        background: #0c1b18;
    }

    /* Multi-layer moving gradient orbs */
    .vv-hero::before {
        content: "";
        position: absolute;
        inset: 0;
        background:
            radial-gradient(ellipse 60% 50% at 20% 30%, rgba(61,217,176,0.18) 0%, transparent 60%),
            radial-gradient(ellipse 50% 40% at 80% 70%, rgba(107,159,212,0.14) 0%, transparent 55%),
            radial-gradient(ellipse 40% 60% at 55% 10%, rgba(61,217,176,0.08) 0%, transparent 60%);
        animation: orb-drift 10s ease-in-out infinite alternate;
        z-index: 0;
    }

    /* Floating grid lines */
    .vv-hero::after {
        content: "";
        position: absolute;
        inset: 0;
        background-image:
            linear-gradient(rgba(61,217,176,0.04) 1px, transparent 1px),
            linear-gradient(90deg, rgba(61,217,176,0.04) 1px, transparent 1px);
        background-size: 44px 44px;
        animation: grid-scroll 20s linear infinite;
        z-index: 0;
    }

    @keyframes orb-drift {
        0%   { transform: scale(1) translate(0,0); opacity: 1; }
        50%  { transform: scale(1.08) translate(12px,-8px); opacity: 0.85; }
        100% { transform: scale(1.04) translate(-8px,12px); opacity: 1; }
    }

    @keyframes grid-scroll {
        0%   { background-position: 0 0; }
        100% { background-position: 44px 44px; }
    }

    .vv-hero-content { position: relative; z-index: 1; }

    .vv-hero-badge {
        display: inline-block;
        background: rgba(61,217,176,0.12);
        border: 1px solid rgba(61,217,176,0.3);
        color: #3dd9b0;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        padding: 0.35rem 0.9rem;
        border-radius: 999px;
        margin-bottom: 1.5rem;
        box-shadow: 0 0 12px rgba(61,217,176,0.15);
    }

    .vv-hero h1 {
        font-size: clamp(1.9rem, 4vw, 2.75rem) !important;
        font-weight: 800 !important;
        color: #f8fafc !important;
        line-height: 1.2 !important;
        margin: 0 0 1.1rem !important;
        letter-spacing: -0.03em !important;
        text-shadow: 0 0 30px rgba(61,217,176,0.18);
    }

    .vv-hero h1 span { color: #3dd9b0; }

    .vv-hero p {
        color: #799e90 !important;
        font-size: 1.05rem !important;
        line-height: 1.7 !important;
        max-width: 680px;
        margin: 0 auto !important;
    }

    /* Floating agent orbs row */
    .vv-agents-row {
        display: flex;
        justify-content: center;
        gap: 0.75rem;
        flex-wrap: wrap;
        margin-top: 2.25rem;
    }
    .vv-agent-chip {
        background: rgba(61,217,176,0.08);
        border: 1px solid rgba(61,217,176,0.2);
        color: #3dd9b0;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.3rem 0.8rem;
        border-radius: 999px;
        letter-spacing: 0.04em;
        animation: float-chip 4s ease-in-out infinite;
    }
    .vv-agent-chip:nth-child(2) { animation-delay: 0.5s; }
    .vv-agent-chip:nth-child(3) { animation-delay: 1.0s; }
    .vv-agent-chip:nth-child(4) { animation-delay: 1.5s; }
    .vv-agent-chip:nth-child(5) { animation-delay: 2.0s; }
    .vv-agent-chip:nth-child(6) { animation-delay: 2.5s; }
    .vv-agent-chip:nth-child(7) { animation-delay: 3.0s; }

    @keyframes float-chip {
        0%, 100% { transform: translateY(0); }
        50%       { transform: translateY(-4px); }
    }

    /* Feature cards row */
    .vv-features {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1.25rem;
        margin-bottom: 1.5rem;
    }
    .vv-feature-card {
        background: #162f2a;
        border: 1px solid #1e3b33;
        border-radius: 16px;
        padding: 1.75rem 1.5rem;
        text-align: center;
        transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
    }
    .vv-feature-card:hover {
        transform: translateY(-5px);
        border-color: rgba(61,217,176,0.4);
        box-shadow: 0 12px 24px rgba(0,0,0,0.2), 0 0 20px rgba(61,217,176,0.08);
    }
    .vv-feature-num {
        font-size: 1.6rem;
        font-weight: 800;
        color: #3dd9b0;
        opacity: 0.6;
        line-height: 1;
        margin-bottom: 0.75rem;
    }
    .vv-feature-card h3 {
        font-size: 1rem !important;
        font-weight: 700 !important;
        color: #f8fafc !important;
        margin: 0 0 0.5rem !important;
    }
    .vv-feature-card p {
        color: #799e90 !important;
        font-size: 0.85rem !important;
        line-height: 1.55 !important;
        margin: 0 !important;
    }

    /* How it works */
    .vv-steps {
        display: flex;
        gap: 1rem;
        align-items: flex-start;
        flex-wrap: wrap;
        margin-bottom: 2rem;
    }
    .vv-step-item {
        flex: 1;
        min-width: 160px;
        background: #0c1b18;
        border: 1px solid #1e3b33;
        border-radius: 14px;
        padding: 1.25rem;
        position: relative;
    }
    .vv-step-item::before {
        content: attr(data-n);
        position: absolute;
        top: -10px;
        left: 14px;
        background: #3dd9b0;
        color: #0c1b18;
        font-size: 0.7rem;
        font-weight: 800;
        padding: 2px 8px;
        border-radius: 999px;
        letter-spacing: 0.06em;
    }
    .vv-step-item h4 {
        font-size: 0.88rem !important;
        font-weight: 700 !important;
        color: #f8fafc !important;
        margin: 0.5rem 0 0.3rem !important;
    }
    .vv-step-item p {
        font-size: 0.8rem !important;
        color: #799e90 !important;
        margin: 0 !important;
        line-height: 1.5 !important;
    }
    </style>

    <!-- HERO SECTION -->
    <div class="vv-hero">
        <div class="vv-hero-content">
            <div class="vv-hero-badge">AI Agent Builder Series 2026</div>
            <h1>Evaluate startup opportunities<br>with <span>6 AI agents</span></h1>
            <p>
                Upload a pitch deck and VentureValuator automatically runs market research,
                financial modelling, skeptic review, and generates
                a full investment memo — in under two minutes.
            </p>
            <div class="vv-agents-row">
                <div class="vv-agent-chip">Extract</div>
                <div class="vv-agent-chip">Market</div>
                <div class="vv-agent-chip">Financial</div>
                <div class="vv-agent-chip">Skeptic</div>
                <div class="vv-agent-chip">Memo</div>
                <div class="vv-agent-chip">Deck</div>
            </div>
        </div>
    </div>

    <!-- FEATURE CARDS -->
    <div class="vv-features">
        <div class="vv-feature-card">
            <div class="vv-feature-num">01</div>
            <h3>Data Extraction</h3>
            <p>Automatically parse and structure key metrics and startup info from any pitch deck PDF.</p>
        </div>
        <div class="vv-feature-card">
            <div class="vv-feature-num">02</div>
            <h3>Market Research</h3>
            <p>Real-time web search for TAM, SAM, competitors, and live financial comps via MCP.</p>
        </div>
        <div class="vv-feature-card">
            <div class="vv-feature-num">03</div>
            <h3>Financial Modelling</h3>
            <p>Project 24-month revenue, gross margins, CAC, and LTV with three-scenario forecasting.</p>
        </div>
        <div class="vv-feature-card">
            <div class="vv-feature-num">04</div>
            <h3>Skeptic Review</h3>
            <p>A contrarian VC agent challenges assumptions, flags red flags, and asks hard questions.</p>
        </div>
        <div class="vv-feature-card">
            <div class="vv-feature-num">05</div>
            <h3>Investor Scoring</h3>
            <p>A weighted rubric turns the analysis into a clear score, verdict, and confidence level.</p>
        </div>
        <div class="vv-feature-card">
            <div class="vv-feature-num">06</div>
            <h3>Investor Memo</h3>
            <p>A full investment memo with a 0–10 score, verdict, and confidence — ready to share.</p>
        </div>
    </div>

    <!-- HOW IT WORKS -->
    <div style="margin-bottom:1rem;">
        <div style="font-size:0.78rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#799e90;margin-bottom:1rem;">How it works</div>
        <div class="vv-steps">
            <div class="vv-step-item" data-n="STEP 1">
                <h4>Upload a PDF</h4>
                <p>Go to Dashboard and upload any pitch deck in PDF format.</p>
            </div>
            <div class="vv-step-item" data-n="STEP 2">
                <h4>Agents run</h4>
                <p>6 AI agents execute in sequence — takes about 60–120 seconds.</p>
            </div>
            <div class="vv-step-item" data-n="STEP 3">
                <h4>Review results</h4>
                <p>Explore the score, market report, financial model, and memo in tabbed views.</p>
            </div>
            <div class="vv-step-item" data-n="STEP 4">
                <h4>Download & share</h4>
                <p>Export the memo as text, the full analysis as JSON, or the deck as a PPTX.</p>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

auth, test_mode = get_auth()
render_overview_metrics(auth, test_mode)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Get Started", type="primary", use_container_width=True, key="hero_cta"):
        st.switch_page("pages/dashboard.py")
