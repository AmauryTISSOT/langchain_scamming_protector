from fastapi import APIRouter, HTTPException, Request
from app.api.models import (
    ChatRequest, ChatResponse, DirectorInfo, Segment,
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
    state = sm.get_state(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionInfoResponse(
        session_id=session_id,
        turn_count=state.turn_count,
        active=True,
        scam_type=state.scam_type,
        current_stage=state.stage,
        current_objective=state.current_objective,
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
    state = sm.get_state(body.session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    # 1. Get history summary from victim's memory
    history_summary = state.victim.get_history_summary(max_turns=5)

    # 2. Director analyzes and generates new objective
    director_result = state.director.update_objective(
        last_scammer=body.user_input,
        history_summary=history_summary,
        script_hint=state.script_hint,
    )

    # 3. Update session state
    state.scam_type = director_result.get("scam_type", "autre")
    state.stage = director_result.get("stage", "1")
    state.stage_description = director_result.get("stage_description", "")
    state.current_objective = director_result.get("new_objective", state.current_objective)

    # 4. Victim responds with Director's objective
    segments_data, clean_text = state.victim.respond_web(
        user_input=body.user_input,
        objective=state.current_objective,
        constraint=body.constraint,
    )
    sm.increment_turn(body.session_id)

    segments = [Segment(**s) for s in segments_data]

    director_info = DirectorInfo(
        scam_type=state.scam_type,
        stage=state.stage,
        stage_description=state.stage_description,
        objective_used=state.current_objective,
    )

    return ChatResponse(
        session_id=body.session_id,
        segments=segments,
        raw_text=clean_text,
        director_info=director_info,
    )
