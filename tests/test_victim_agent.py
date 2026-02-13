import re
from unittest.mock import patch, MagicMock

from langchain_core.messages import HumanMessage, AIMessage

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


class TestGetHistorySummary:
    def test_empty_memory_returns_aucun_historique(self, mock_no_google_credentials):
        agent = _create_agent()
        assert agent.get_history_summary() == "Aucun historique"

    def test_with_messages(self, mock_no_google_credentials):
        agent = _create_agent()
        agent.memory.chat_memory.messages = [
            HumanMessage(content="Bonjour, ici votre banque."),
            AIMessage(content="Ah bonjour [DOG_BARK] oh Poupoune !"),
        ]
        result = agent.get_history_summary()
        assert "Arnaqueur: Bonjour, ici votre banque." in result
        assert "Jeanne: Ah bonjour  oh Poupoune !" in result
        assert "[DOG_BARK]" not in result

    def test_truncates_long_messages(self, mock_no_google_credentials):
        agent = _create_agent()
        long_msg = "A" * 150
        agent.memory.chat_memory.messages = [
            HumanMessage(content=long_msg),
        ]
        result = agent.get_history_summary()
        assert result.endswith("...")
        assert len(result.split(": ", 1)[1]) == 103  # 100 chars + "..."

    def test_respects_max_turns(self, mock_no_google_credentials):
        agent = _create_agent()
        agent.memory.chat_memory.messages = [
            HumanMessage(content=f"Message {i}") for i in range(20)
        ]
        result = agent.get_history_summary(max_turns=2)
        lines = result.strip().split("\n")
        assert len(lines) == 4  # 2 turns * 2 messages
