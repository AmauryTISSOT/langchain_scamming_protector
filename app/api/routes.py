from fastapi import APIRouter, HTTPException, Request
from app.api.models import (
    ChatRequest, ChatResponse, Segment,
    SessionResponse, SessionInfoResponse,
)

router = APIRouter(prefix="/api")


def _get_session_manager(request: Request):
    return request.app.state.session_manager


@router.post("/sessions", response_model=SessionResponse)
async def create_session(request: Request):
    sm = _get_session_manager(request)
    session_id = sm.create_session()
    return SessionResponse(session_id=session_id)


@router.get("/sessions/{session_id}", response_model=SessionInfoResponse)
async def get_session(session_id: str, request: Request):
    sm = _get_session_manager(request)
    if not sm.exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionInfoResponse(
        session_id=session_id,
        turn_count=sm.get_turn_count(session_id),
        active=True,
    )


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, request: Request):
    sm = _get_session_manager(request)
    if not sm.delete(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return {"detail": "Session deleted"}


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, request: Request):
    sm = _get_session_manager(request)
    agent = sm.get(body.session_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Session not found")

    segments_data, clean_text = agent.respond_web(
        user_input=body.user_input,
        objective=body.objective,
        constraint=body.constraint,
    )
    sm.increment_turn(body.session_id)

    segments = [Segment(**s) for s in segments_data]

    return ChatResponse(
        session_id=body.session_id,
        segments=segments,
        raw_text=clean_text,
    )
