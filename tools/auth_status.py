import os
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


def _check_keyring() -> AuthStatus:
    try:
        from login_with_chatgpt import ChatGPTAccount

        account = ChatGPTAccount()
        status = account.status()
        if not status.authenticated:
            return AuthStatus(authenticated=False, error="Not signed in to ChatGPT")

        model_ids = account.list_models()
        default_model = os.getenv("CHATGPT_MODEL", "gpt-5.6-sol")
        model = default_model if default_model in model_ids else (model_ids[0] if model_ids else default_model)
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

    keyring_status = _check_keyring()
    if keyring_status.authenticated:
        return keyring_status

    proxy_status = _check_proxy()
    if proxy_status.authenticated:
        return proxy_status

    return AuthStatus(
        authenticated=False,
        error=(
            "Not signed in to ChatGPT. Run in your terminal:\n"
            "  uvx login-with-chatgpt login\n\n"
            "Or start the local proxy:\n"
            "  npx openai-oauth --detach"
        ),
    )
