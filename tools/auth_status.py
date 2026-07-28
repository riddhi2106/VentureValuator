import os
import time
from dataclasses import dataclass
from typing import Optional

import httpx


@dataclass
class AuthStatus:
    authenticated: bool
    method: Optional[str] = None
    model: Optional[str] = None
    error: Optional[str] = None


def _is_test_mode() -> bool:
    return os.getenv("TEST_MODE", "false").lower() in ("true", "1", "yes")


def _tokens_look_usable(tokens: object) -> bool:
    """Validate freshly exchanged session tokens without making a network call."""
    access_token = getattr(tokens, "access_token", None)
    refresh_token = getattr(tokens, "refresh_token", None)
    expires_at = getattr(tokens, "expires_at", None)
    if not access_token:
        return False
    if refresh_token:
        return True
    return expires_at is None or expires_at > time.time() + 60


def _check_session_tokens() -> Optional[AuthStatus]:
    try:
        import streamlit as st
        if "chatgpt_tokens" in st.session_state and st.session_state.chatgpt_tokens:
            from login_with_chatgpt import ChatGPTAccount
            from login_with_chatgpt.auth.store import MemoryTokenStore

            tokens = st.session_state.chatgpt_tokens
            if not _tokens_look_usable(tokens):
                return None

            store = MemoryTokenStore()
            store.save("default", tokens)
            account = ChatGPTAccount(store=store)
            default_model = os.getenv("CHATGPT_MODEL", "gpt-5.6-sol")

            # Account status is local-only in current login-with-chatgpt versions,
            # but a library/version-specific parsing failure should not discard
            # tokens that were just successfully exchanged by this session.
            try:
                status = account.status()
                if not status.authenticated:
                    return None
            except Exception as status_error:
                print(f"[auth_status] Account status probe failed: {status_error}")

            return AuthStatus(
                authenticated=True,
                method="session",
                model=default_model,
            )
    except Exception as e:
        print(f"[auth_status] Session auth check failed: {e}")
    return None


def _check_keyring() -> AuthStatus:
    try:
        from login_with_chatgpt import ChatGPTAccount

        account = ChatGPTAccount()
        status = account.status()
        if not status.authenticated:
            return AuthStatus(authenticated=False, error="Not signed in to ChatGPT")

        default_model = os.getenv("CHATGPT_MODEL", "gpt-5.6-sol")
        try:
            model_ids = account.list_models()
            model = default_model if default_model in model_ids else (model_ids[0] if model_ids else default_model)
        except Exception:
            model = default_model
        return AuthStatus(authenticated=True, method="keyring", model=model)
    except Exception as e:
        return AuthStatus(authenticated=False, error=str(e))


def _check_proxy() -> AuthStatus:
    proxy_url = os.getenv("OPENAI_OAUTH_PROXY_URL", "http://127.0.0.1:10531/v1").rstrip("/")
    try:
        resp = httpx.get(f"{proxy_url}/models", timeout=3.0)
        resp.raise_for_status()
        data = resp.json()
        model_ids = [m.get("id") for m in data.get("data", []) if m.get("id")]
        default_model = os.getenv("CHATGPT_MODEL", "gpt-5.6-sol")
        model = default_model if default_model in model_ids else (model_ids[0] if model_ids else default_model)
        return AuthStatus(authenticated=True, method="proxy", model=model)
    except Exception as e:
        return AuthStatus(authenticated=False, error=str(e))


def check_auth_status() -> AuthStatus:
    if _is_test_mode():
        return AuthStatus(authenticated=True, method="test", model="mock")

    # 1. Check session-specific login first (web users)
    session_status = _check_session_tokens()
    if session_status and session_status.authenticated:
        return session_status

    # 2. Check local keyring (CLI)
    keyring_status = _check_keyring()
    if keyring_status.authenticated:
        return keyring_status

    # 3. Check local proxy
    proxy_status = _check_proxy()
    if proxy_status.authenticated:
        return proxy_status

    return AuthStatus(
        authenticated=False,
        error="Not signed in to ChatGPT. Please go to the connection page to connect your account.",
    )
