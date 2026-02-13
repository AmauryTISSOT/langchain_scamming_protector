from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient


def _make_mock_state():
    """Create a mock SessionState with victim and director."""
    state = MagicMock()
    state.victim = MagicMock()
    state.director = MagicMock()
    state.turn_count = 0
    state.current_objective = "Répondre lentement."
    state.scam_type = "inconnu"
    state.stage = "1"
    state.stage_description = ""
    state.script_hint = "banque"
    # Director returns valid result by default
    state.director.update_objective.return_value = {
        "scam_type": "banque",
        "stage": "1",
        "stage_description": "approche",
        "new_objective": "Poser des questions.",
    }
    # Victim history summary
    state.victim.get_history_summary.return_value = "Aucun historique"
    return state


@pytest.fixture
def client():
    with patch("server.load_config", return_value="fake-key"), \
         patch("server.SessionManager") as MockSM:
        mock_sm = MagicMock()
        MockSM.return_value = mock_sm

        # Setup mock session manager behavior
        states = {}

        def create_session():
            sid = "test-session-123"
            states[sid] = _make_mock_state()
            return sid

        def get_state(sid):
            return states.get(sid)

        def get_victim(sid):
            state = states.get(sid)
            return state.victim if state else None

        def get(sid):
            return get_victim(sid)

        def exists(sid):
            return sid in states

        def delete(sid):
            if sid in states:
                del states[sid]
                return True
            return False

        def get_turn_count(sid):
            state = states.get(sid)
            return state.turn_count if state else 0

        mock_sm.create_session.side_effect = create_session
        mock_sm.get_state.side_effect = get_state
        mock_sm.get_victim.side_effect = get_victim
        mock_sm.get.side_effect = get
        mock_sm.exists.side_effect = exists
        mock_sm.delete.side_effect = delete
        mock_sm.get_turn_count.side_effect = get_turn_count
        mock_sm.increment_turn.side_effect = lambda sid: None

        from server import app
        app.state.session_manager = mock_sm
        yield TestClient(app), states


class TestSessionEndpoints:
    def test_create_session(self, client):
        c, _ = client
        res = c.post("/api/sessions")
        assert res.status_code == 200
        assert "session_id" in res.json()

    def test_get_session(self, client):
        c, _ = client
        c.post("/api/sessions")
        res = c.get("/api/sessions/test-session-123")
        assert res.status_code == 200
        data = res.json()
        assert data["session_id"] == "test-session-123"
        assert data["active"] is True

    def test_get_nonexistent_session(self, client):
        c, _ = client
        res = c.get("/api/sessions/nonexistent")
        assert res.status_code == 404

    def test_delete_session(self, client):
        c, _ = client
        c.post("/api/sessions")
        res = c.delete("/api/sessions/test-session-123")
        assert res.status_code == 200

    def test_delete_nonexistent_session(self, client):
        c, _ = client
        res = c.delete("/api/sessions/nonexistent")
        assert res.status_code == 404


class TestChatEndpoint:
    def test_chat_success(self, client):
        c, states = client
        c.post("/api/sessions")

        state = states["test-session-123"]
        state.victim.respond_web.return_value = (
            [{"type": "text", "content": "Bonjour mon petit"}],
            "Bonjour mon petit",
        )

        res = c.post("/api/chat", json={
            "session_id": "test-session-123",
            "user_input": "Bonjour Jeanne",
        })
        assert res.status_code == 200
        data = res.json()
        assert data["raw_text"] == "Bonjour mon petit"
        assert len(data["segments"]) == 1
        assert data["segments"][0]["type"] == "text"
        # Verify director_info is present
        assert data["director_info"] is not None
        assert data["director_info"]["scam_type"] == "banque"

    def test_chat_nonexistent_session(self, client):
        c, _ = client
        res = c.post("/api/chat", json={
            "session_id": "nonexistent",
            "user_input": "Hello",
        })
        assert res.status_code == 404

    def test_chat_calls_director_before_victim(self, client):
        c, states = client
        c.post("/api/sessions")

        state = states["test-session-123"]
        state.victim.respond_web.return_value = (
            [{"type": "text", "content": "Oui ?"}],
            "Oui ?",
        )

        c.post("/api/chat", json={
            "session_id": "test-session-123",
            "user_input": "Donnez-moi votre code",
        })

        # Director was called
        state.director.update_objective.assert_called_once()
        # Victim was called with director's objective
        state.victim.respond_web.assert_called_once()
        call_kwargs = state.victim.respond_web.call_args
        assert call_kwargs[1]["objective"] == "Poser des questions."
