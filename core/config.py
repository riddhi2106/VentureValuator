"""Typed application configuration loaded from environment variables and `.env`."""

from functools import lru_cache
from typing import Literal

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings shared by the UI, agents, and external-service adapters.

    Environment variables are case-insensitive and may be supplied by a local
    `.env` file, Streamlit secrets exported as environment variables, Docker, or
    the deployment platform. Secret values use ``SecretStr`` so accidental model
    dumps and logs do not expose credentials.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: Literal["development", "test", "staging", "production"] = "development"
    llm_provider: Literal["chatgpt_oauth", "openai"] = "chatgpt_oauth"
    test_mode: bool = False
    disable_web_search: bool = False

    chatgpt_model: str = "gpt-5.6-sol"
    openai_oauth_proxy_url: str = "http://127.0.0.1:10531/v1"
    chatgpt_token_json: SecretStr | None = None
    openai_api_key: SecretStr | None = None
    tavily_api_key: SecretStr | None = None

    @model_validator(mode="after")
    def prevent_mock_mode_in_deployed_environments(self):
        """Fail fast rather than serving fixed mock analyses in staging/production."""

        if self.app_env in {"staging", "production"} and self.test_mode:
            raise ValueError(f"TEST_MODE must be false when APP_ENV={self.app_env}")
        return self

    def secret_value(self, field_name: str) -> str | None:
        """Return a secret's plaintext value only at the external-service boundary."""

        value = getattr(self, field_name)
        return value.get_secret_value() if value else None


@lru_cache
def get_settings() -> Settings:
    """Return one validated settings object per process."""

    return Settings()
