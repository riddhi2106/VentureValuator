"""Connection Settings for VentureValuator."""

import streamlit as st

from app.components import connection_html, get_auth, setup_page

setup_page("Login / Connection", "Manage your ChatGPT connection for running analyses.")

auth, test_mode = get_auth()

# Render connection status using native styling instead of broken HTML divs
st.subheader("Status")
st.markdown(connection_html(auth, test_mode), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

col1, _ = st.columns([1, 3])
with col1:
    if st.button("Refresh connection", type="primary", key="login_refresh_conn", use_container_width=True):
        st.session_state.auth_status = None
        st.rerun()

st.divider()

if not test_mode and not auth.authenticated:
    st.subheader("Sign-in Instructions")
    st.markdown(
        """
        1. Open your terminal in the project directory.
        2. Run the command: `login-with-chatgpt login`
        3. Return to this page and click **Refresh connection**.
        
        **Fallback method:** `npx openai-oauth --detach`
        """
    )
else:
    st.success("You are successfully authenticated and ready to run analyses!")
