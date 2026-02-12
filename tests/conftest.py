import sys
from unittest.mock import MagicMock

# Mock pygame BEFORE any app module is imported (module-level code in
# sound_tools.py does `import pygame; pygame.mixer.init()` at import time).
_mock_pygame = MagicMock()
_mock_pygame.mixer.get_init.return_value = True
_mock_pygame.mixer.music.get_busy.return_value = False
sys.modules.setdefault("pygame", _mock_pygame)

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def mock_pygame():
    """Provide the mocked pygame.mixer to tests and reset between tests."""
    _mock_pygame.mixer.reset_mock()
    _mock_pygame.mixer.get_init.return_value = True
    _mock_pygame.mixer.music.get_busy.return_value = False
    return _mock_pygame.mixer


@pytest.fixture
def mock_groq_api_key(monkeypatch):
    """Set a fake GROQ_API_KEY."""
    monkeypatch.setenv("GROQ_API_KEY", "fake-groq-key-for-testing")
    return "fake-groq-key-for-testing"


@pytest.fixture
def mock_no_google_credentials(monkeypatch):
    """Ensure no Google credentials are set."""
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    monkeypatch.delenv("GOOGLE_CREDENTIALS", raising=False)
