from pydantic import BaseModel
from typing import List, Literal, Optional


class ChatRequest(BaseModel):
    session_id: str
    user_input: str
    constraint: str = "Aucune"


class Segment(BaseModel):
    type: Literal["text", "sound", "pause"]
    content: Optional[str] = None
    sound_tag: Optional[str] = None
    sound_file: Optional[str] = None
    tts_audio: Optional[str] = None
    duration: Optional[float] = None


class DirectorInfo(BaseModel):
    scam_type: str
    stage: str
    stage_description: str
    objective_used: str


class ChatResponse(BaseModel):
    session_id: str
    segments: List[Segment]
    raw_text: str
    director_info: Optional[DirectorInfo] = None


class SessionResponse(BaseModel):
    session_id: str


class SessionInfoResponse(BaseModel):
    session_id: str
    turn_count: int
    active: bool
    scam_type: Optional[str] = None
    current_stage: Optional[str] = None
    current_objective: Optional[str] = None
