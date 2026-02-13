from fastapi import APIRouter, HTTPException, Request
from app.api.models import (
    ChatRequest, ChatResponse, DirectorInfo, Segment,
    SessionResponse, SessionInfoResponse,
    AutoStartRequest, AutoStartResponse,
    AutoNextRequest, AutoTurnResponse,
    AutoStopRequest, InterventionRequired,
)

router = APIRouter(prefix="/api")


# Constantes de mapping pour les interventions utilisateur
INTERVENTION_CONSTRAINTS = {
    "1": {
        "constraint": "Tu dois maintenant raccrocher le téléphone poliment mais fermement. Dis au revoir et termine la conversation.",
        "terminate": True
    },
    "2": {
        "constraint": "Tu dois maintenant donner un faux numéro de carte bancaire de manière naturelle. Invente un numéro à 16 chiffres et fournis-le lentement comme si tu cherchais ta carte.",
        "terminate": False
    },
    "3": {
        "constraint": "Tu ressens une douleur thoracique soudaine. Tu dois manifester une détresse physique (respiration difficile, douleur), appeler à l'aide, mais reste en ligne.",
        "terminate": False
    },
    "4": {
        "constraint": "Aucune",
        "terminate": False
    }
}


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

    # Appliquer le choix utilisateur si présent
    constraint = "Aucune"
    should_terminate = False

    if body.user_choice and body.user_choice in INTERVENTION_CONSTRAINTS:
        intervention = INTERVENTION_CONSTRAINTS[body.user_choice]
        constraint = intervention["constraint"]
        should_terminate = intervention["terminate"]
        state.pending_intervention = False

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

    # 2. Victim responds with constraint applied
    victim_segments_data, victim_text = state.victim.respond_web(
        user_input=last_scammer_text,
        objective=state.current_objective,
        constraint=constraint,  # APPLICATION DE LA CONTRAINTE
    )
    victim_segments = [Segment(**s) for s in victim_segments_data]

    state.turn_count += 1

    # Si choix 1 (raccroche), terminer immédiatement
    if should_terminate:
        state.is_active = False
        return AutoTurnResponse(
            session_id=body.session_id,
            turn_number=state.turn_count,
            victim_segments=victim_segments,
            victim_text=victim_text,
            scammer_segments=[],
            scammer_text="",
            director_info=DirectorInfo(
                scam_type=state.scam_type,
                stage=state.stage,
                stage_description=state.stage_description,
                objective_used=state.current_objective,
            ),
            is_complete=True,
            intervention_required=None,
        )

    # Vérifier si intervention requise APRÈS la réponse de Jeanne
    intervention_required = None
    if state.turn_count % 2 == 0 and state.turn_count < state.max_turns:
        state.pending_intervention = True
        intervention_required = InterventionRequired(
            message=f"Tour {state.turn_count} : Que fait Jeanne maintenant ?",
            choices=[
                "Jeanne raccroche",
                "Jeanne donne son numéro de carte bancaire",
                "Jeanne fait un arrêt cardiaque",
                "Continuer"
            ],
        )

    is_complete = state.turn_count >= state.max_turns

    # 3. Scammer responds (sauf si intervention pending ou complet)
    scammer_segments = []
    scammer_text = ""
    if not is_complete and not state.pending_intervention:
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
        intervention_required=intervention_required,
    )


@router.post("/auto-conversation/stop")
async def auto_stop(body: AutoStopRequest, request: Request):
    sm = _get_session_manager(request)
    state = sm.get_state(body.session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    state.is_active = False
    return {"detail": "Conversation stopped"}
