from fastapi import APIRouter, HTTPException, Request
from app.api.models import (
    ChatRequest, ChatResponse, DirectorInfo, Segment,
    SessionResponse, SessionInfoResponse,
    AutoStartRequest, AutoStartResponse,
    AutoNextRequest, AutoTurnResponse,
    AutoStopRequest,
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


@router.post("/auto-conversation/start", response_model=AutoStartResponse)
async def auto_start(body: AutoStartRequest, request: Request):
    sm = _get_session_manager(request)
    state = sm.get_state(body.session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    state.is_active = True
    state.turn_count = 0

    # Scammer generates opening message
    scammer_segments_data, scammer_text = state.scammer.generate_opening()
    scammer_segments = [Segment(**s) for s in scammer_segments_data]

    return AutoStartResponse(
        session_id=body.session_id,
        scammer_segments=scammer_segments,
        scammer_text=scammer_text,
    )


@router.post("/auto-conversation/next", response_model=AutoTurnResponse)
async def auto_next(body: AutoNextRequest, request: Request):
    sm = _get_session_manager(request)
    state = sm.get_state(body.session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    if not state.is_active:
        raise HTTPException(status_code=400, detail="Conversation not active")

    if state.turn_count >= state.max_turns:
        raise HTTPException(status_code=400, detail="Max turns reached")

    # Get last scammer message from scammer memory
    scammer_messages = state.scammer.memory.chat_memory.messages
    last_scammer_text = scammer_messages[-1].content if scammer_messages else ""

    # 1. Director analyzes last scammer message
    history_summary = state.victim.get_history_summary(max_turns=5)
    director_result = state.director.update_objective(
        last_scammer=last_scammer_text,
        history_summary=history_summary,
        script_hint=state.script_hint,
    )

    state.scam_type = director_result.get("scam_type", "autre")
    state.stage = director_result.get("stage", "1")
    state.stage_description = director_result.get("stage_description", "")
    state.current_objective = director_result.get("new_objective", state.current_objective)

    # 2. Victim responds to scammer
    victim_segments_data, victim_text = state.victim.respond_web(
        user_input=last_scammer_text,
        objective=state.current_objective,
    )
    victim_segments = [Segment(**s) for s in victim_segments_data]

    state.turn_count += 1
    is_complete = state.turn_count >= state.max_turns

    # 3. Scammer responds (unless complete)
    scammer_segments = []
    scammer_text = ""
    if not is_complete:
        scammer_segments_data, scammer_text = state.scammer.respond_web(victim_text)
        scammer_segments = [Segment(**s) for s in scammer_segments_data]

    director_info = DirectorInfo(
        scam_type=state.scam_type,
        stage=state.stage,
        stage_description=state.stage_description,
        objective_used=state.current_objective,
    )

    if is_complete:
        state.is_active = False

    return AutoTurnResponse(
        session_id=body.session_id,
        turn_number=state.turn_count,
        victim_segments=victim_segments,
        victim_text=victim_text,
        scammer_segments=scammer_segments,
        scammer_text=scammer_text,
        director_info=director_info,
        is_complete=is_complete,
    )


@router.post("/auto-conversation/stop")
async def auto_stop(body: AutoStopRequest, request: Request):
    sm = _get_session_manager(request)
    state = sm.get_state(body.session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    state.is_active = False
    return {"detail": "Conversation stopped"}
