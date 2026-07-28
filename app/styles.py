"""LSDx-inspired dark navy dashboard theme."""

NAVY_BG = "#102420"
NAVY_SIDEBAR = "#0c1b18"
NAVY_CARD = "#162f2a"
NAVY_CARD_ALT = "#122a26"
NAVY_BORDER = "#1e3b33"
WHITE = "#f8fafc"
MUTED = "#799e90"
ACCENT = "#3dd9b0"
ACCENT_DIM = "rgba(61, 217, 176, 0.15)"
ACCENT_PURPLE = "#a78bfa"

AGENT_STEPS = [
    ("extraction", "Extract"),
    ("market", "Market"),
    ("financial", "Financial"),
    ("impact", "Impact"),
    ("skeptic", "Skeptic"),
    ("memo", "Memo"),
    ("deck", "Deck"),
]

CHART_COLORS = {
    "primary": ACCENT,
    "secondary": "#6b9fd4",
    "grid": NAVY_BORDER,
    "text": WHITE,
}

THEME_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

#MainMenu, footer, header {{ visibility: hidden; }}

.stApp {{
    background: radial-gradient(ellipse 80% 50% at 20% 0%, rgba(61,217,176,0.07), transparent 55%),
                radial-gradient(ellipse 60% 40% at 90% 10%, rgba(107,159,212,0.06), transparent 50%),
                {NAVY_BG};
    color: {WHITE};
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}}

.stApp, .stApp p, .stApp li, .stApp span, .stApp label,
.stMarkdown, .stMarkdown p, [data-testid="stMarkdownContainer"] {{
    color: {WHITE};
}}

.block-container {{
    padding: 1.5rem 2.5rem 3rem 2.5rem;
    max-width: 1200px;
}}

/* Sidebar */
[data-testid="stSidebar"] {{
    background: {NAVY_SIDEBAR} !important;
    border-right: 1px solid {NAVY_BORDER};
    box-shadow: 2px 0 10px rgba(0, 0, 0, 0.2);
}}

[data-testid="stSidebar"] > div:first-child {{
    padding-top: 1.5rem;
}}

[data-testid="stSidebarNav"] {{
    padding-top: 0.5rem;
}}

[data-testid="stSidebarNav"] ul {{
    gap: 0.35rem;
}}

[data-testid="stSidebarNav"] a {{
    background: transparent !important;
    color: {MUTED} !important;
    font-weight: 500 !important;
    font-size: 0.95rem !important;
    border-radius: 12px !important;
    padding: 0.65rem 0.85rem !important;
    transition: all 0.2s ease;
}}

[data-testid="stSidebarNav"] a:hover {{
    background: {NAVY_CARD} !important;
    color: {WHITE} !important;
    transform: translateX(2px);
}}

[data-testid="stSidebarNav"] a[aria-current="page"] {{
    background: {NAVY_CARD} !important;
    color: {WHITE} !important;
    border: 1px solid {NAVY_BORDER};
    box-shadow: inset 2px 0 0 {ACCENT};
}}

[data-testid="stSidebarCollapseButton"] {{
    color: {MUTED} !important;
}}

.vv-logo {{
    font-size: 1.35rem;
    font-weight: 700;
    color: {WHITE};
    letter-spacing: -0.02em;
    padding: 0 0.85rem 1.25rem 0.85rem;
    border-bottom: 1px solid {NAVY_BORDER};
    margin-bottom: 0.5rem;
}}

.vv-logo span {{
    color: {ACCENT};
}}

.vv-sidebar-foot {{
    font-size: 0.78rem;
    color: {MUTED};
    padding: 1rem 0.85rem;
    border-top: 1px solid {NAVY_BORDER};
    margin-top: 1rem;
    line-height: 1.5;
}}

/* Page header */
.vv-page-header {{
    margin-bottom: 1.75rem;
}}

.vv-page-header h1 {{
    font-size: 1.85rem !important;
    font-weight: 700 !important;
    color: {WHITE} !important;
    margin: 0 0 0.35rem 0 !important;
    letter-spacing: -0.03em;
}}

.vv-page-header p {{
    color: {MUTED} !important;
    font-size: 1rem !important;
    margin: 0 !important;
    line-height: 1.5 !important;
}}

/* Cards */
.vv-card {{
    background: {NAVY_CARD};
    border: 1px solid {NAVY_BORDER};
    border-radius: 16px;
    padding: 1.5rem 1.75rem;
    margin-bottom: 1rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}}

.vv-card:hover {{
    box-shadow: 0 8px 12px rgba(0, 0, 0, 0.15), 0 0 10px rgba(61, 217, 176, 0.05);
}}

.vv-card-title {{
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: {MUTED};
    margin-bottom: 1rem;
}}

.vv-card h3 {{
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    color: {WHITE} !important;
    margin: 0 0 0.75rem 0 !important;
}}

/* Metric tiles */
.vv-metrics {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 1rem;
    margin-bottom: 1.5rem;
}}

.vv-metric {{
    background: {NAVY_CARD};
    border: 1px solid {NAVY_BORDER};
    border-radius: 14px;
    padding: 1.25rem 1.5rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    transition: all 0.2s ease;
}}

.vv-metric:hover {{
    transform: translateY(-2px);
    box-shadow: 0 6px 12px rgba(0,0,0,0.15), 0 0 8px {ACCENT_DIM};
    border-color: rgba(61, 217, 176, 0.3);
}}

.vv-metric-label {{
    font-size: 0.78rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: {MUTED};
    margin-bottom: 0.45rem;
}}

.vv-metric-value {{
    font-size: 1.6rem;
    font-weight: 700;
    color: {WHITE};
    line-height: 1.2;
}}

.vv-metric-value.accent {{
    color: {ACCENT};
    text-shadow: 0 0 10px {ACCENT_DIM};
}}

/* Verdict hero */
.vv-verdict {{
    background: linear-gradient(135deg, {NAVY_CARD} 0%, {NAVY_CARD_ALT} 100%);
    border: 1px solid {NAVY_BORDER};
    border-radius: 18px;
    padding: 2.25rem;
    text-align: center;
    margin: 1.25rem 0;
    box-shadow: 0 10px 20px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.05);
}}

.vv-verdict-score {{
    font-size: 3.75rem;
    font-weight: 700;
    color: {ACCENT};
    line-height: 1;
    text-shadow: 0 0 15px rgba(61, 217, 176, 0.3);
}}

.vv-verdict-meta {{
    font-size: 1.15rem;
    color: {WHITE};
    margin-top: 0.5rem;
    font-weight: 500;
}}

.vv-verdict-name {{
    font-size: 0.85rem;
    color: {MUTED};
    margin-top: 0.6rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}}

/* Stepper */
@keyframes pulse-border {{
    0% {{ box-shadow: 0 0 0 0 rgba(61, 217, 176, 0.4); }}
    70% {{ box-shadow: 0 0 0 6px rgba(61, 217, 176, 0); }}
    100% {{ box-shadow: 0 0 0 0 rgba(61, 217, 176, 0); }}
}}

.vv-stepper {{
    display: flex;
    flex-wrap: wrap;
    gap: 0.55rem;
    margin: 0.75rem 0;
}}

.vv-step {{
    flex: 1;
    min-width: 80px;
    text-align: center;
    padding: 0.6rem 0.35rem;
    border-radius: 12px;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    border: 1px solid {NAVY_BORDER};
    background: {NAVY_CARD_ALT};
    color: {MUTED};
    transition: all 0.3s ease;
}}

.vv-step-active {{
    border-color: {ACCENT};
    color: {ACCENT};
    background: {ACCENT_DIM};
    animation: pulse-border 2s infinite;
}}

.vv-step-done {{
    border-color: {ACCENT};
    background: {ACCENT};
    color: {NAVY_BG};
}}

.vv-step-error, .vv-step-cancelled {{
    border-style: dashed;
    color: {MUTED};
}}

/* Status */
.vv-status-line {{
    font-size: 0.95rem;
    color: {WHITE};
    line-height: 1.5;
    margin: 0;
}}

.vv-status-dot {{
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 0.5rem;
    vertical-align: middle;
    box-shadow: 0 0 5px currentColor;
}}

.vv-status-ok {{ background: {ACCENT}; color: {ACCENT}; }}
.vv-status-warn {{ background: #fbbf24; color: #fbbf24; }}
.vv-status-off {{ background: #475569; color: #475569; }}

/* History table rows */
.vv-table-row {{
    display: grid;
    grid-template-columns: 2fr 0.8fr 1fr 1.2fr 0.6fr;
    gap: 1rem;
    align-items: center;
    padding: 1rem 0;
    border-bottom: 1px solid {NAVY_BORDER};
    font-size: 0.95rem;
    transition: background 0.2s ease;
}}
.vv-table-row:hover {{
    background: rgba(255,255,255,0.02);
    border-radius: 8px;
    padding-left: 0.5rem;
    margin-left: -0.5rem;
    width: calc(100% + 1rem);
}}

.vv-table-row:last-child {{ border-bottom: none; }}

.vv-table-head {{
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: {MUTED};
    padding-bottom: 0.75rem;
    border-bottom: 1px solid {NAVY_BORDER};
}}

.vv-table-name {{
    font-weight: 600;
    color: {WHITE};
}}

.vv-table-meta {{
    color: {MUTED};
    font-size: 0.85rem;
}}

.vv-score-pill {{
    display: inline-block;
    background: {ACCENT_DIM};
    color: {ACCENT};
    font-weight: 700;
    font-size: 0.88rem;
    padding: 0.25rem 0.65rem;
    border-radius: 999px;
    box-shadow: 0 2px 4px rgba(61, 217, 176, 0.1);
}}

.vv-verdict-pill {{
    display: inline-block;
    background: rgba(167,139,250,0.15);
    color: {ACCENT_PURPLE};
    font-weight: 600;
    font-size: 0.8rem;
    padding: 0.25rem 0.65rem;
    border-radius: 999px;
    box-shadow: 0 2px 4px rgba(167,139,250,0.1);
}}

/* Roadmap */
.vv-roadmap-item {{
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    padding: 1rem 0;
    border-bottom: 1px solid {NAVY_BORDER};
}}

.vv-roadmap-item:last-child {{ border-bottom: none; }}

.vv-roadmap-badge {{
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    padding: 0.25rem 0.55rem;
    border-radius: 6px;
    background: {NAVY_CARD_ALT};
    color: {MUTED};
    border: 1px solid {NAVY_BORDER};
    white-space: nowrap;
}}

.vv-roadmap-title {{
    font-weight: 600;
    color: {WHITE};
    font-size: 0.95rem;
}}

.vv-roadmap-desc {{
    color: {MUTED};
    font-size: 0.88rem;
    margin-top: 0.25rem;
    line-height: 1.5;
}}

.vv-empty {{
    text-align: center;
    padding: 3rem 2rem;
    color: {MUTED};
    font-size: 1rem;
    line-height: 1.6;
    background: {NAVY_CARD_ALT};
    border-style: dashed;
}}

/* Streamlit widgets */
[data-testid="stMetricLabel"] {{
    color: {MUTED} !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}

[data-testid="stMetricValue"] {{
    color: {WHITE} !important;
    font-size: 1.6rem !important;
    font-weight: 700 !important;
}}

.stCaption, small {{
    color: {MUTED} !important;
}}

.stTabs [data-baseweb="tab-list"] {{
    border-bottom: 1px solid {NAVY_BORDER};
    gap: 0.5rem;
}}

.stTabs [data-baseweb="tab"] {{
    color: {MUTED} !important;
    font-weight: 600;
    font-size: 0.9rem;
    background: transparent !important;
    transition: color 0.2s ease;
}}

.stTabs [aria-selected="true"] {{
    color: {ACCENT} !important;
    border-bottom-color: {ACCENT} !important;
}}

.stTextArea textarea {{
    background: {NAVY_CARD_ALT} !important;
    color: {WHITE} !important;
    border: 1px solid {NAVY_BORDER} !important;
    border-radius: 12px !important;
    font-size: 0.95rem !important;
    line-height: 1.6 !important;
}}

[data-testid="stFileUploader"] {{
    background: {NAVY_CARD_ALT};
    border: 1px dashed {NAVY_BORDER};
    border-radius: 16px;
    padding: 1.5rem;
    transition: all 0.2s ease;
}}
[data-testid="stFileUploader"]:hover {{
    border-color: rgba(61, 217, 176, 0.4);
    background: {NAVY_CARD};
}}

[data-testid="stFileUploader"] section {{
    color: {MUTED} !important;
}}

.stButton > button[kind="primary"] {{
    background: linear-gradient(135deg, #4ef5ca 0%, {ACCENT} 100%) !important;
    color: {NAVY_BG} !important;
    border: none !important;
    font-weight: 700 !important;
    border-radius: 12px !important;
    padding: 0.65rem 1.5rem !important;
    box-shadow: 0 4px 10px rgba(61, 217, 176, 0.25) !important;
    transition: all 0.2s ease;
}}

.stButton > button[kind="secondary"] {{
    background: transparent !important;
    color: {WHITE} !important;
    border: 1px solid {NAVY_BORDER} !important;
    font-weight: 600 !important;
    border-radius: 12px !important;
    padding: 0.65rem 1.5rem !important;
    transition: all 0.2s ease;
}}

.stButton > button:hover {{
    opacity: 0.95;
    transform: translateY(-1px);
    box-shadow: 0 6px 14px rgba(61, 217, 176, 0.3) !important;
}}
.stButton > button[kind="secondary"]:hover {{
    background: {NAVY_CARD_ALT} !important;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important;
}}

.stProgress > div > div > div {{
    background: linear-gradient(90deg, {ACCENT}, #4ef5ca) !important;
    box-shadow: 0 0 10px rgba(61, 217, 176, 0.5);
}}

.stProgress > div > div {{
    background: {NAVY_BORDER} !important;
    border-radius: 8px;
    overflow: hidden;
}}

div[data-testid="stExpander"] {{
    background: {NAVY_CARD_ALT};
    border: 1px solid {NAVY_BORDER};
    border-radius: 14px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}}

.stDownloadButton > button {{
    background: {NAVY_CARD_ALT} !important;
    color: {WHITE} !important;
    border: 1px solid {NAVY_BORDER} !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease;
}}
.stDownloadButton > button:hover {{
    background: {NAVY_CARD} !important;
    border-color: rgba(255,255,255,0.15) !important;
}}

.stMarkdown a {{
    color: {ACCENT} !important;
    font-weight: 500;
    text-decoration: none;
    border-bottom: 1px dotted {ACCENT};
}}
.stMarkdown a:hover {{
    color: #4ef5ca !important;
    border-bottom-style: solid;
}}

[data-testid="stAlert"] {{
    border-radius: 12px;
    background: {NAVY_CARD} !important;
    border: 1px solid {NAVY_BORDER} !important;
}}

hr {{
    border-color: {NAVY_BORDER} !important;
    margin: 2rem 0 !important;
}}
</style>
"""


def inject_theme() -> None:
    import streamlit as st
    st.markdown(THEME_CSS, unsafe_allow_html=True)
