import uuid
from typing import Dict, Optional
from app.agents.victim_agent import VictimAgent


class SessionManager:
    def __init__(self, api_key: str):
        self._sessions: Dict[str, VictimAgent] = {}
        self._turn_counts: Dict[str, int] = {}
        self._api_key = api_key

    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = VictimAgent(self._api_key)
        self._turn_counts[session_id] = 0
        return session_id

    def get(self, session_id: str) -> Optional[VictimAgent]:
        return self._sessions.get(session_id)

    def increment_turn(self, session_id: str) -> None:
        if session_id in self._turn_counts:
            self._turn_counts[session_id] += 1

    def get_turn_count(self, session_id: str) -> int:
        return self._turn_counts.get(session_id, 0)

    def delete(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            del self._turn_counts[session_id]
            return True
        return False

    def exists(self, session_id: str) -> bool:
        return session_id in self._sessions
