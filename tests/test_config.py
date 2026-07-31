import pytest
from pydantic import ValidationError

from core.config import Settings, get_settings


def test_settings_load_typed_environment_values_and_mask_secrets(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("TEST_MODE", "yes")
    monkeypatch.setenv("DISABLE_WEB_SEARCH", "1")
    monkeypatch.setenv("CHATGPT_MODEL", "gpt-test")
    monkeypatch.setenv("TAVILY_API_KEY", "private-key")

    settings = get_settings()

    assert settings.app_env == "test"
    assert settings.test_mode is True
    assert settings.disable_web_search is True
    assert settings.chatgpt_model == "gpt-test"
    assert settings.secret_value("tavily_api_key") == "private-key"
    assert "private-key" not in repr(settings)


def test_settings_reject_invalid_environment_name():
    with pytest.raises(ValidationError):
        Settings(app_env="preview")


def test_deployed_environments_reject_mock_mode():
    with pytest.raises(ValidationError, match="TEST_MODE must be false"):
        Settings(app_env="production", test_mode=True)


def test_settings_cache_returns_single_process_instance():
    assert get_settings() is get_settings()
