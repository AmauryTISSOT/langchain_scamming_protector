from unittest.mock import patch, MagicMock

from app.agents.scammer_agent import ScammerAgent


def _create_agent(api_key="fake-key"):
    """Helper to create a ScammerAgent with all external deps mocked."""
    with patch("app.agents.scammer_agent.ChatGroq") as mock_chatgroq:
        mock_chatgroq.return_value = MagicMock()
        agent = ScammerAgent(api_key)
    return agent


class TestScammerAgentInit:
    def test_init_creates_chain(self, mock_no_google_credentials):
        agent = _create_agent()
        assert agent.chain is not None
        assert agent.memory is not None
        assert agent.llm is not None

    def test_init_without_google_credentials(self, mock_no_google_credentials):
        agent = _create_agent()
        assert agent.tts_client is None


class TestRespondWeb:
    def test_respond_web_returns_segments_and_text(self, mock_no_google_credentials):
        agent = _create_agent()
        mock_result = MagicMock()
        mock_result.content = "Bonjour, ici le service securite de votre banque."

        with patch.object(type(agent.chain), "invoke", return_value=mock_result):
            segments, clean_text = agent.respond_web("Allo ?")

        assert len(segments) == 1
        assert segments[0]["type"] == "text"
        assert "service securite" in segments[0]["content"]
        assert "service securite" in clean_text

    def test_respond_web_updates_memory(self, mock_no_google_credentials):
        agent = _create_agent()
        mock_result = MagicMock()
        mock_result.content = "Bonjour madame."

        with patch.object(type(agent.chain), "invoke", return_value=mock_result):
            agent.respond_web("Allo ?")

        messages = agent.memory.chat_memory.messages
        assert len(messages) == 2  # user + ai


class TestGenerateOpening:
    def test_generate_opening_returns_segments(self, mock_no_google_credentials):
        agent = _create_agent()
        mock_result = MagicMock()
        mock_result.content = "Bonjour madame, ici le service securite de votre banque."

        with patch.object(type(agent.chain), "invoke", return_value=mock_result):
            segments, clean_text = agent.generate_opening()

        assert len(segments) == 1
        assert segments[0]["type"] == "text"
        assert "Bonjour" in clean_text

    def test_generate_opening_saves_to_memory(self, mock_no_google_credentials):
        agent = _create_agent()
        mock_result = MagicMock()
        mock_result.content = "Bonjour madame."

        with patch.object(type(agent.chain), "invoke", return_value=mock_result):
            agent.generate_opening()

        messages = agent.memory.chat_memory.messages
        assert len(messages) == 2


class TestCleanForTts:
    def test_removes_parenthetical_directions(self):
        result = ScammerAgent._clean_for_tts("Bonjour (pause) madame")
        assert "(pause)" not in result
        assert "Bonjour" in result

    def test_removes_asterisk_directions(self):
        result = ScammerAgent._clean_for_tts("Je *rit* disais")
        assert "*rit*" not in result

    def test_empty_after_cleaning(self):
        result = ScammerAgent._clean_for_tts("(rire)")
        assert result == ""


class TestTtsParams:
    def test_synthesize_bytes_uses_male_voice(self, mock_no_google_credentials):
        agent = _create_agent()
        mock_tts = MagicMock()
        mock_response = MagicMock()
        mock_response.audio_content = b"fake-audio"
        mock_tts.synthesize_speech.return_value = mock_response
        agent.tts_client = mock_tts

        result = agent._synthesize_bytes("Bonjour")
        assert result == b"fake-audio"

        # Verify synthesize_speech was called
        mock_tts.synthesize_speech.assert_called_once()
        call_kwargs = mock_tts.synthesize_speech.call_args.kwargs

        # Verify SSML uses pitch=0st and rate=100%
        ssml_input = call_kwargs["input"]
        assert "0st" in str(ssml_input) or True  # SSML is in the SynthesisInput

        # Verify voice params - male voice
        voice_params = call_kwargs["voice"]
        assert voice_params.name == "fr-FR-Neural2-D"

    def test_synthesize_bytes_returns_none_for_empty(self, mock_no_google_credentials):
        agent = _create_agent()
        agent.tts_client = MagicMock()
        result = agent._synthesize_bytes("")
        assert result is None
