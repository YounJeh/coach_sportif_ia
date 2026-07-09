from __future__ import annotations

from datetime import date, timedelta

from langgraph.graph import END, StateGraph

from coach_ai.connectors import get_connectors
from coach_ai.state import CoachState, GoalInput


def intake_node(state: CoachState) -> CoachState:
    state.decision_log.append(
        {
            "agent": "intake",
            "message": "Objective captured",
            "objective": state.goal.objective,
            "deadline": state.goal.deadline.isoformat(),
        }
    )
    return state


def sync_node(state: CoachState) -> CoachState:
    connectors = get_connectors()
    user_id = state.goal.user_id

    state.raw_data = {
        "strava": connectors["strava"].fetch_activity_range(user_id),
        "calendar": connectors["calendar"].fetch_calendar(user_id),
    }
    state.decision_log.append({"agent": "sync", "message": "Data synced"})
    return state


def quality_node(state: CoachState) -> CoachState:
    source_count = len(state.raw_data)
    freshness_bonus = 0.2 if source_count >= 2 else 0.0
    state.quality_score = min(1.0, 0.5 + freshness_bonus)
    state.decision_log.append(
        {
            "agent": "quality",
            "message": "Quality scored",
            "quality_score": state.quality_score,
        }
    )
    return state


def context_node(state: CoachState) -> CoachState:
    activities = []
    for source in ["strava"]:
        activities.extend(state.raw_data.get(source, {}).get("activities", []))

    avg_rpe = 0.0
    if activities:
        avg_rpe = sum(a.get("rpe", 0) for a in activities) / len(activities)

    state.context = {
        "avg_rpe": round(avg_rpe, 2),
        "objective": state.goal.objective,
        "days_to_deadline": max((state.goal.deadline - date.today()).days, 0),
    }
    state.decision_log.append({"agent": "context", "message": "Context built"})
    return state


def _infer_modality(objective: str) -> str:
    goal = objective.lower()
    if any(token in goal for token in ["course", "run", "marathon", "semi", "5k", "10k"]):
        return "running"
    if any(token in goal for token in ["muscu", "musculation", "force", "strength", "bench", "squat"]):
        return "strength"
    if any(token in goal for token in ["fitness", "hiit", "cardio", "condition"]):
        return "fitness"
    return "fitness"


def _build_session_title(modality: str, index: int) -> str:
    if modality == "running":
        return f"Running session {index}"
    if modality == "strength":
        return f"Strength session {index}"
    if modality == "fitness":
        return f"Fitness session {index}"
    return f"Recovery session {index}"


def _build_plan_data(modality: str, slot: str, index: int) -> dict:
    if modality == "running":
        workout_type = "easy" if index % 3 else "interval"
        return {
            "slot_hint": slot,
            "workout_type": workout_type,
            "alternative_short_min": 20,
        }
    if modality == "strength":
        return {
            "slot_hint": slot,
            "focus": "full_body" if index % 2 else "upper_body",
            "template": [
                {"exercise": "Squat", "sets": 3, "reps": 8},
                {"exercise": "Push-up", "sets": 3, "reps": 12},
                {"exercise": "Row", "sets": 3, "reps": 10},
            ],
            "alternative_short_min": 25,
        }
    if modality == "fitness":
        return {
            "slot_hint": slot,
            "format": "circuit",
            "work_rest": "40/20",
            "rounds": 6,
            "alternative_short_min": 15,
        }
    return {"slot_hint": slot, "alternative_short_min": 15}


def planning_node(state: CoachState) -> CoachState:
    base_duration = 45
    if state.context.get("avg_rpe", 0) >= 7:
        base_duration = 35

    modality = _infer_modality(state.goal.objective)
    slots = state.goal.available_slots[:7]
    sessions = []
    for idx, slot in enumerate(slots, start=1):
        session_date = date.today() + timedelta(days=idx - 1)
        sessions.append(
            {
                "user_id": state.goal.user_id,
                "goal_id": None,
                "session_date": session_date.isoformat(),
                "modality": modality,
                "title": _build_session_title(modality, idx),
                "target_duration_min": base_duration,
                "target_intensity_rpe": 6.0,
                "status": "planned",
                "plan_data": _build_plan_data(modality, slot, idx),
                "result_data": {},
                "notes": None,
            }
        )

    state.plan = {
        "objective": state.goal.objective,
        "deadline": state.goal.deadline.isoformat(),
        "quality_score": state.quality_score,
        "sessions": sessions,
    }
    state.decision_log.append({"agent": "planning", "message": "Plan generated"})
    return state


def safety_node(state: CoachState) -> CoachState:
    conservative_mode = state.quality_score < 0.6
    state.safety = {
        "conservative_mode": conservative_mode,
        "health_disclaimer": (
            "Recommandations non medicales. En cas de douleur persistante, consultez un professionnel de sante."
        ),
    }

    if conservative_mode:
        for session in state.plan.get("sessions", []):
            session["target_duration_min"] = min(session["target_duration_min"], 30)

    state.decision_log.append(
        {
            "agent": "safety",
            "message": "Safety policy applied",
            "conservative_mode": conservative_mode,
        }
    )
    return state


def briefing_node(state: CoachState) -> CoachState:
    sessions = state.plan.get("sessions", [])
    today = sessions[0] if sessions else {}
    state.briefing = {
        "coach": (
            f"Plan genere avec score confiance {state.quality_score:.2f}. "
            f"Mode conservateur: {state.safety.get('conservative_mode', False)}."
        ),
        "athlete": (
            f"Aujourd'hui: {today.get('title', 'Session recovery')} pendant "
            f"{today.get('target_duration_min', 20)} min. "
            "Option courte disponible si agenda charge."
        ),
    }
    state.decision_log.append({"agent": "briefing", "message": "Briefings generated"})
    return state


def build_graph():
    graph = StateGraph(CoachState)
    graph.add_node("intake", intake_node)
    graph.add_node("sync", sync_node)
    graph.add_node("quality", quality_node)
    graph.add_node("context", context_node)
    graph.add_node("planning", planning_node)
    graph.add_node("safety", safety_node)
    graph.add_node("briefing", briefing_node)

    graph.set_entry_point("intake")
    graph.add_edge("intake", "sync")
    graph.add_edge("sync", "quality")
    graph.add_edge("quality", "context")
    graph.add_edge("context", "planning")
    graph.add_edge("planning", "safety")
    graph.add_edge("safety", "briefing")
    graph.add_edge("briefing", END)

    return graph.compile()


def run_planning(goal: GoalInput) -> CoachState:
    app = build_graph()
    initial_state = CoachState(goal)
    return app.invoke(initial_state)
