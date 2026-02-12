import os
import sys
import json
import importlib
from unittest.mock import patch, MagicMock


class TestMainApiKeyValidation:
    def test_missing_groq_key_raises_valueerror(self, monkeypatch):
        """main.py raises ValueError when GROQ_API_KEY is not set."""
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
        monkeypatch.delenv("GOOGLE_CREDENTIALS", raising=False)

        sys.modules.pop("main", None)

        # Mock load_dotenv so .env file doesn't set GROQ_API_KEY
        with patch("dotenv.load_dotenv", return_value=None), \
             patch("app.agents.victim_agent.VictimAgent"):
            try:
                import main
                importlib.reload(main)
                assert False, "Should have raised ValueError"
            except ValueError as e:
                assert "GROQ_API_KEY" in str(e)
            finally:
                sys.modules.pop("main", None)


class TestGoogleCredentialsParsing:
    def test_google_credentials_json_parsed(self, monkeypatch):
        """GOOGLE_CREDENTIALS JSON string is parsed and written to a temp file."""
        monkeypatch.setenv("GROQ_API_KEY", "fake-key")
        monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)

        fake_creds = json.dumps({"type": "service_account", "project_id": "test"})
        monkeypatch.setenv("GOOGLE_CREDENTIALS", fake_creds)

        sys.modules.pop("main", None)

        mock_victim_instance = MagicMock()
        with patch("app.agents.victim_agent.VictimAgent", return_value=mock_victim_instance):
            with patch("builtins.input", side_effect=EOFError):
                try:
                    import main
                    importlib.reload(main)
                except (EOFError, SystemExit):
                    pass
                finally:
                    sys.modules.pop("main", None)

        creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if creds_path and os.path.exists(creds_path):
            with open(creds_path) as f:
                data = json.load(f)
            assert data["type"] == "service_account"
            os.unlink(creds_path)
