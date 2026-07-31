import pytest

from core.config import get_settings


@pytest.fixture(autouse=True)
def reset_settings_cache():
    """Ensure environment changes made by one test cannot leak into another."""

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
