"""VentureValuator — multi-page Streamlit entry point."""

import os
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import streamlit as st

from app.styles import inject_theme

st.set_page_config(
    page_title="VentureValuator",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_theme()

home_page = st.Page(
    "pages/home.py",
    title="Home",
    icon=":material/home:",
    default=True,
)
dashboard_page = st.Page(
    "pages/dashboard.py",
    title="Dashboard",
    icon=":material/dashboard:",
)
history_page = st.Page(
    "pages/history.py",
    title="Analysis history",
    icon=":material/history:",
)
login_page = st.Page(
    "pages/login.py",
    title="Connection settings",
    icon=":material/settings:",
)

pg = st.navigation([home_page, dashboard_page, history_page, login_page])
pg.run()
