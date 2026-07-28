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

# Password protection gate
def check_password() -> bool:
    """Returns True if the user had the correct password, False otherwise."""
    # Look for password in secrets (Streamlit Cloud) or env vars
    target_password = st.secrets.get("ACCESS_PASSWORD") or os.getenv("ACCESS_PASSWORD")
    
    # If no password is configured, bypass the gate (default to open)
    if not target_password:
        return True

    if "password_authenticated" not in st.session_state:
        st.session_state.password_authenticated = False

    if st.session_state.password_authenticated:
        return True

    # Show password form
    st.markdown(
        '<div class="vv-logo" style="border-bottom: none; padding: 2rem 0; text-align: center;">Venture<span>Valuator</span></div>',
        unsafe_allow_html=True,
    )
    st.subheader("Private Access Required")
    st.write("Please enter the password to access this application.")
    
    with st.form("password_gate"):
        password_input = st.text_input("Password", type="password")
        submit = st.form_submit_button("Access App")
        if submit:
            if password_input == target_password:
                st.session_state.password_authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password")
                
    return False

if check_password():
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
