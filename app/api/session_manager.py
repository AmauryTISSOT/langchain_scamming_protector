import uuid
from dataclasses import dataclass, field
from typing import Dict, Optional
from app.agents.victim_agent import VictimAgent
from app.agents.director_agent import DirectorAgent


@dataclass
class SessionState:
    victim: VictimAgent
    director: DirectorAgent
    turn_count: int = 0
    current_objective: str = "Répondre lentement et gagner du temps."
    scam_type: str = "inconnu"
    stage: str = "1"
    stage_description: str = ""
    script_hint: str = "banque"


class SessionManager:
    def __init__(self, api_key: str):
        self._sessions: Dict[str, SessionState] = {}
        self._api_key = api_key

    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = SessionState(
            victim=VictimAgent(self._api_key),
            director=DirectorAgent(self._api_key),
        )
        return session_id

    def get_state(self, session_id: str) -> Optional[SessionState]:
        return self._sessions.get(session_id)

    def get_victim(self, session_id: str) -> Optional[VictimAgent]:
        state = self._sessions.get(session_id)
        return state.victim if state else None

    # Keep backward compat
    def get(self, session_id: str) -> Optional[VictimAgent]:
        return self.get_victim(session_id)

    def increment_turn(self, session_id: str) -> None:
        state = self._sessions.get(session_id)
        if state:
            state.turn_count += 1

    def get_turn_count(self, session_id: str) -> int:
        state = self._sessions.get(session_id)
        return state.turn_count if state else 0

    def delete(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def exists(self, session_id: str) -> bool:
        return session_id in self._sessions
