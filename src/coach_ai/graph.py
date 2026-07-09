from __future__ import annotations

from datetime import date

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
        "garmin": connectors["garmin"].fetch_activity_range(user_id),
        "calendar": connectors["calendar"].fetch_calendar(user_id),
    }
    state.decision_log.append({"agent": "sync", "message": "Data synced"})
    return state


def quality_node(state: CoachState) -> CoachState:
    source_count = len(state.raw_data)
    freshness_bonus = 0.2 if source_count >= 3 else 0.0
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
    for source in ["strava", "garmin"]:
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


def planning_node(state: CoachState) -> CoachState:
    base_duration = 45
    if state.context.get("avg_rpe", 0) >= 7:
        base_duration = 35

    slots = state.goal.available_slots[:7]
    sessions = []
    for idx, slot in enumerate(slots, start=1):
        sessions.append(
            {
                "day": idx,
                "slot": slot,
                "type": "endurance" if idx % 3 else "interval",
                "target_duration_min": base_duration,
                "target_intensity": "moderate",
                "alternative_short_min": 20,
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
            f"Aujourd'hui: {today.get('type', 'recovery')} pendant "
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
    initial_state = CoachState(goal=goal)
    return app.invoke(initial_state)
