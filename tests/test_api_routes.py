from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    with patch("server.load_config", return_value="fake-key"), \
         patch("server.SessionManager") as MockSM:
        mock_sm = MagicMock()
        MockSM.return_value = mock_sm

        # Setup mock session manager behavior
        sessions = {}

        def create_session():
            sid = "test-session-123"
            agent = MagicMock()
            sessions[sid] = agent
            return sid

        def get(sid):
            return sessions.get(sid)

        def exists(sid):
            return sid in sessions

        def delete(sid):
            if sid in sessions:
                del sessions[sid]
                return True
            return False

        def get_turn_count(sid):
            return 0

        mock_sm.create_session.side_effect = create_session
        mock_sm.get.side_effect = get
        mock_sm.exists.side_effect = exists
        mock_sm.delete.side_effect = delete
        mock_sm.get_turn_count.side_effect = get_turn_count

        from server import app
        app.state.session_manager = mock_sm
        yield TestClient(app)


class TestSessionEndpoints:
    def test_create_session(self, client):
        res = client.post("/api/sessions")
        assert res.status_code == 200
        assert "session_id" in res.json()

    def test_get_session(self, client):
        client.post("/api/sessions")
        res = client.get("/api/sessions/test-session-123")
        assert res.status_code == 200
        data = res.json()
        assert data["session_id"] == "test-session-123"
        assert data["active"] is True

    def test_get_nonexistent_session(self, client):
        res = client.get("/api/sessions/nonexistent")
        assert res.status_code == 404

    def test_delete_session(self, client):
        client.post("/api/sessions")
        res = client.delete("/api/sessions/test-session-123")
        assert res.status_code == 200

    def test_delete_nonexistent_session(self, client):
        res = client.delete("/api/sessions/nonexistent")
        assert res.status_code == 404


class TestChatEndpoint:
    def test_chat_success(self, client):
        client.post("/api/sessions")
        # Mock the agent's respond_web
        agent = client.app.state.session_manager.get("test-session-123")
        agent.respond_web.return_value = (
            [{"type": "text", "content": "Bonjour mon petit"}],
            "Bonjour mon petit",
        )

        res = client.post("/api/chat", json={
            "session_id": "test-session-123",
            "user_input": "Bonjour Jeanne",
        })
        assert res.status_code == 200
        data = res.json()
        assert data["raw_text"] == "Bonjour mon petit"
        assert len(data["segments"]) == 1
        assert data["segments"][0]["type"] == "text"

    def test_chat_nonexistent_session(self, client):
        res = client.post("/api/chat", json={
            "session_id": "nonexistent",
            "user_input": "Hello",
        })
        assert res.status_code == 404
