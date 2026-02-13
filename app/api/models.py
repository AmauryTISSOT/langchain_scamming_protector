from pydantic import BaseModel
from typing import List, Literal, Optional


class ChatRequest(BaseModel):
    session_id: str
    user_input: str
    objective: str = "Embrouiller l'arnaqueur et ne donner aucune information personnelle."
    constraint: str = "Aucune"


class Segment(BaseModel):
    type: Literal["text", "sound", "pause"]
    content: Optional[str] = None
    sound_tag: Optional[str] = None
    sound_file: Optional[str] = None
    tts_audio: Optional[str] = None
    duration: Optional[float] = None


class ChatResponse(BaseModel):
    session_id: str
    segments: List[Segment]
    raw_text: str


class SessionResponse(BaseModel):
    session_id: str


class SessionInfoResponse(BaseModel):
    session_id: str
    turn_count: int
    active: bool
