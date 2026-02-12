import re
from unittest.mock import patch, MagicMock

from app.agents.victim_agent import VictimAgent


def _create_agent(api_key="fake-key"):
    """Helper to create a VictimAgent with all external deps mocked."""
    with patch("app.agents.victim_agent.create_openai_functions_agent") as mock_create, \
         patch("app.agents.victim_agent.ChatGroq") as mock_chatgroq, \
         patch("app.agents.victim_agent.AgentExecutor") as mock_executor_cls:
        mock_chatgroq.return_value = MagicMock()
        mock_create.return_value = MagicMock()
        mock_executor_cls.return_value = MagicMock()
        agent = VictimAgent(api_key)
    return agent


class TestVictimAgentInit:
    def test_init_creates_executor(self, mock_no_google_credentials):
        agent = _create_agent()
        assert agent.executor is not None
        assert agent.memory is not None
        assert agent.llm is not None

    def test_init_without_google_credentials(self, mock_no_google_credentials):
        agent = _create_agent()
        assert agent.tts_client is None


class TestTagPattern:
    def test_splits_dog_bark_tag(self):
        pattern = VictimAgent._TAG_PATTERN
        text = "Bonjour, je... [DOG_BARK] Oh Poupoune !"
        parts = pattern.split(text)
        assert "[DOG_BARK]" in parts

    def test_splits_multiple_tags(self):
        pattern = VictimAgent._TAG_PATTERN
        text = "Mon numéro [DOORBELL] attendez [PAUSE] je reviens"
        parts = pattern.split(text)
        assert "[DOORBELL]" in parts
        assert "[PAUSE]" in parts

    def test_splits_coughing_fit(self):
        pattern = VictimAgent._TAG_PATTERN
        text = "Je disais [COUGHING_FIT] pardon"
        parts = pattern.split(text)
        assert "[COUGHING_FIT]" in parts

    def test_no_tags_returns_single_element(self):
        pattern = VictimAgent._TAG_PATTERN
        text = "Bonjour monsieur"
        parts = pattern.split(text)
        assert len(parts) == 1
        assert parts[0] == text


class TestCleanForTts:
    def test_removes_parenthetical_directions(self):
        result = VictimAgent._clean_for_tts("Bonjour (pause) monsieur")
        assert "(pause)" not in result
        assert "Bonjour" in result

    def test_removes_asterisk_directions(self):
        result = VictimAgent._clean_for_tts("Je *tousse* disais")
        assert "*tousse*" not in result

    def test_collapses_multiple_spaces(self):
        result = VictimAgent._clean_for_tts("Bonjour   monsieur")
        assert "  " not in result

    def test_empty_after_cleaning(self):
        result = VictimAgent._clean_for_tts("(rire)")
        assert result == ""


class TestSynthesize:
    def test_builds_correct_ssml(self, mock_no_google_credentials):
        agent = _create_agent()

        # Verify _clean_for_tts works correctly for SSML input
        text = "Bonjour monsieur"
        cleaned = agent._clean_for_tts(text)
        assert cleaned == "Bonjour monsieur"

    def test_synthesize_returns_none_for_empty_text(self):
        """_clean_for_tts returns empty for stage directions only."""
        assert VictimAgent._clean_for_tts("(rire) *tousse*") == ""


class TestRespond:
    @patch("app.agents.victim_agent.play_sound_by_name")
    def test_respond_returns_clean_text(self, mock_play_sound, mock_no_google_credentials):
        agent = _create_agent()
        agent.executor.invoke.return_value = {
            "output": "Bonjour [DOG_BARK] oh Poupoune !"
        }

        result = agent.respond("Hello")
        assert "[DOG_BARK]" not in result
        assert "Bonjour" in result
        assert "Poupoune" in result

    @patch("app.agents.victim_agent.play_sound_by_name")
    def test_respond_calls_play_sound_for_tags(self, mock_play_sound, mock_no_google_credentials):
        agent = _create_agent()
        agent.executor.invoke.return_value = {
            "output": "Attendez [DOORBELL] je reviens [COUGHING_FIT] pardon"
        }

        agent.respond("Hello")
        assert mock_play_sound.call_count == 2

    @patch("app.agents.victim_agent.time")
    @patch("app.agents.victim_agent.play_sound_by_name")
    def test_respond_handles_pause_tag(self, mock_play_sound, mock_time, mock_no_google_credentials):
        agent = _create_agent()
        agent.executor.invoke.return_value = {
            "output": "Je réfléchis [PAUSE] ah oui"
        }

        result = agent.respond("Hello")
        mock_time.sleep.assert_called_with(VictimAgent.PAUSE_DURATION)
        assert "[PAUSE]" not in result
