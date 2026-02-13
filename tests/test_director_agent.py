import json
from unittest.mock import patch, MagicMock

from app.agents.director_agent import DirectorAgent, DEFAULT_RESULT


def _create_director(api_key="fake-key"):
    """Helper to create a DirectorAgent with ChatGroq mocked."""
    with patch("app.agents.director_agent.ChatGroq") as mock_chatgroq:
        mock_chatgroq.return_value = MagicMock()
        director = DirectorAgent(api_key)
    return director


class TestParseResponse:
    def test_parses_valid_json(self):
        content = json.dumps({
            "scam_type": "banque",
            "stage": "2",
            "stage_description": "vérification identité",
            "new_objective": "Faire semblant de chercher ses papiers."
        })
        result = DirectorAgent._parse_response(content)
        assert result["scam_type"] == "banque"
        assert result["stage"] == "2"
        assert result["stage_description"] == "vérification identité"
        assert result["new_objective"] == "Faire semblant de chercher ses papiers."

    def test_handles_json_with_extra_text(self):
        content = 'Voici mon analyse:\n{"scam_type": "colis", "stage": "1", "stage_description": "notification", "new_objective": "Demander ce que contient le colis."}\nFin.'
        result = DirectorAgent._parse_response(content)
        assert result["scam_type"] == "colis"
        assert result["new_objective"] == "Demander ce que contient le colis."

    def test_fallback_on_invalid_json(self):
        content = "Je ne sais pas trop quoi dire ici..."
        result = DirectorAgent._parse_response(content)
        assert result == DEFAULT_RESULT

    def test_fallback_on_missing_required_keys(self):
        content = json.dumps({"stage": "2", "stage_description": "test"})
        result = DirectorAgent._parse_response(content)
        assert result == DEFAULT_RESULT

    def test_adds_stage_description_if_missing(self):
        content = json.dumps({
            "scam_type": "support_technique",
            "stage": "3",
            "new_objective": "Décrire un écran imaginaire."
        })
        result = DirectorAgent._parse_response(content)
        assert result["scam_type"] == "support_technique"
        assert result["stage_description"] == "Stade 3"

    def test_adds_stage_if_missing(self):
        content = json.dumps({
            "scam_type": "banque",
            "new_objective": "Gagner du temps."
        })
        result = DirectorAgent._parse_response(content)
        assert result["stage"] == "1"
        assert "stage_description" in result


class TestUpdateObjective:
    def test_returns_parsed_dict(self):
        director = _create_director()
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "scam_type": "banque",
            "stage": "1",
            "stage_description": "approche",
            "new_objective": "Poser des questions."
        })
        director.chain = MagicMock()
        director.chain.invoke.return_value = mock_response

        result = director.update_objective("Bonjour, ici votre banque.")
        assert result["scam_type"] == "banque"
        assert result["new_objective"] == "Poser des questions."

    def test_returns_default_on_exception(self):
        director = _create_director()
        director.chain = MagicMock()
        director.chain.invoke.side_effect = Exception("API error")

        result = director.update_objective("test")
        assert result == DEFAULT_RESULT
