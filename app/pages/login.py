"""Connection Settings for VentureValuator."""

import os
import time

import streamlit as st
from login_with_chatgpt._config import ProtocolConfig
from login_with_chatgpt.auth.device import poll_device_code, request_device_code
from login_with_chatgpt.auth.oauth import exchange_authorization_code

from app.components import connection_html, get_auth, setup_page
from tools.auth_status import AuthStatus

setup_page("Login / Connection", "Manage your ChatGPT connection for running analyses.")

auth, test_mode = get_auth()

st.subheader("Connection Status")
st.markdown(connection_html(auth, test_mode), unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ----------------- AUTHENTICATED STATE -----------------
if auth.authenticated:
    st.success(f"Successfully connected to ChatGPT! (Method: {auth.method})")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("Refresh status", key="btn_refresh_status", use_container_width=True):
            st.session_state.auth_status = None
            st.rerun()
            
    with col2:
        if auth.method == "session":
            if st.button("Disconnect session / Sign Out", key="btn_disconnect", type="primary", use_container_width=True):
                # Clear session state
                if "chatgpt_tokens" in st.session_state:
                    del st.session_state.chatgpt_tokens
                if "device_code_auth" in st.session_state:
                    del st.session_state.device_code_auth
                st.session_state.auth_status = None
                st.success("Successfully disconnected!")
                time.sleep(1.0)
                st.rerun()
        else:
            st.info("Local deployment connection. To sign out, use the terminal: `login-with-chatgpt logout`.")

# ----------------- UNAUTHENTICATED STATE (Web Users) -----------------
else:
    st.subheader("Sign in with ChatGPT")
    st.write(
        "To run startup analyses, sign in with your own ChatGPT account. "
        "No passwords or API keys are stored on the server — your session tokens stay in your browser window."
    )
    
    # Check if a login flow is already active
    if "device_code_auth" not in st.session_state:
        # Show "Start Login" button
        if st.button("Connect ChatGPT Account", type="primary", key="btn_start_oauth"):
            with st.spinner("Requesting pairing code from OpenAI..."):
                try:
                    config = ProtocolConfig()
                    code_info = request_device_code(config)
                    st.session_state.device_code_auth = code_info
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to initiate login: {e}")
    else:
        # Active device login flow
        code_info = st.session_state.device_code_auth
        
        # Check if the code has expired
        if time.time() > code_info.expires_at:
            st.warning("Pairing code has expired. Please request a new one.")
            if st.button("Generate New Code", key="btn_regen_code"):
                del st.session_state.device_code_auth
                st.rerun()
        else:
            # Render Pairing Code UI
            st.info("Pairing code generated! Follow the instructions below:")
            
            # Big beautiful pairing code layout
            st.markdown(
                f"""
                <div style="background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 2rem; text-align: center; margin: 1.5rem 0;">
                    <div style="font-size: 0.85rem; text-transform: uppercase; color: #799e90; letter-spacing: 0.05em; margin-bottom: 0.5rem;">Pairing Code</div>
                    <div style="font-size: 3rem; font-weight: 700; letter-spacing: 0.1em; color: #3dd9b0; font-family: monospace;">{code_info.user_code}</div>
                    <div style="margin-top: 1.5rem;">
                        <a href="{code_info.verification_url}" target="_blank" style="background: #3dd9b0; color: #0d1527; font-weight: 600; padding: 0.75rem 1.5rem; border-radius: 8px; text-decoration: none; display: inline-block;">
                            Authorize on ChatGPT
                        </a>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            st.markdown(
                f"""
                1. Click the **Authorize on ChatGPT** button above (or open [chatgpt.com/device](https://chatgpt.com/device) in your browser).
                2. If prompted, log into your ChatGPT account.
                3. Enter the pairing code: **`{code_info.user_code}`** and approve the session request.
                4. Once approved, return here and click **Check Connection Status** below.
                """
            )
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Check Connection Status", type="primary", key="btn_check_connection", use_container_width=True):
                    with st.spinner("Checking approval status..."):
                        try:
                            config = ProtocolConfig()
                            authorization = poll_device_code(config, code_info)
                            if authorization is not None:
                                tokens = exchange_authorization_code(
                                    config,
                                    code=authorization.authorization_code,
                                    code_verifier=authorization.code_verifier,
                                    redirect_uri=config.device_redirect_uri
                                )
                                # Save tokens in user session state!
                                st.session_state.chatgpt_tokens = tokens
                                # Clean up active auth info
                                del st.session_state.device_code_auth
                                st.session_state.auth_status = AuthStatus(
                                    authenticated=True,
                                    method="session",
                                    model=os.getenv("CHATGPT_MODEL", "gpt-5.6-sol"),
                                )
                                st.success("Connected successfully!")
                                time.sleep(1.0)
                                st.rerun()
                            else:
                                st.error("Waiting for approval on ChatGPT. Please enter the code first!")
                        except Exception as e:
                            st.error(f"Error checking login status: {e}")
            with c2:
                if st.button("Cancel Sign-In", key="btn_cancel_oauth", use_container_width=True):
                    del st.session_state.device_code_auth
                    st.rerun()

st.divider()
st.caption("Developer tip: Set TEST_MODE=true in your environment configuration to bypass logins completely and use mock responses.")
