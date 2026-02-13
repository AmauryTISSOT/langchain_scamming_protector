from unittest.mock import patch, MagicMock
from app.api.session_manager import SessionManager


def _create_session_manager():
    with patch("app.api.session_manager.VictimAgent") as MockAgent:
        MockAgent.return_value = MagicMock()
        sm = SessionManager("fake-key")
        return sm, MockAgent


class TestCreateSession:
    def test_returns_uuid_string(self):
        sm, _ = _create_session_manager()
        session_id = sm.create_session()
        assert isinstance(session_id, str)
        assert len(session_id) == 36  # UUID format

    def test_session_exists_after_creation(self):
        sm, _ = _create_session_manager()
        session_id = sm.create_session()
        assert sm.exists(session_id)

    def test_get_returns_agent(self):
        sm, _ = _create_session_manager()
        session_id = sm.create_session()
        agent = sm.get(session_id)
        assert agent is not None


class TestDeleteSession:
    def test_delete_existing_session(self):
        sm, _ = _create_session_manager()
        session_id = sm.create_session()
        assert sm.delete(session_id) is True
        assert not sm.exists(session_id)

    def test_delete_nonexistent_session(self):
        sm, _ = _create_session_manager()
        assert sm.delete("nonexistent") is False


class TestTurnCount:
    def test_initial_turn_count_is_zero(self):
        sm, _ = _create_session_manager()
        session_id = sm.create_session()
        assert sm.get_turn_count(session_id) == 0

    def test_increment_turn(self):
        sm, _ = _create_session_manager()
        session_id = sm.create_session()
        sm.increment_turn(session_id)
        sm.increment_turn(session_id)
        assert sm.get_turn_count(session_id) == 2

    def test_get_turn_count_nonexistent(self):
        sm, _ = _create_session_manager()
        assert sm.get_turn_count("nonexistent") == 0
