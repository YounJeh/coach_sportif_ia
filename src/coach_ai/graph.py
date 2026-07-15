from __future__ import annotations

import logging

from langgraph.graph import END, START, StateGraph

from coach_ai.agents.plan_generator import generate_training_plan
from coach_ai.agents.profile_analyzer import analyze_athlete
from coach_ai.connectors import get_connectors
from coach_ai.models import GoalInput
from coach_ai.services.plan_validator import validate_plan
from coach_ai.state import CoachState

logger = logging.getLogger(__name__)


async def sync_node(state: CoachState) -> dict:
    goal = state["goal"]
    logger.info("node sync start user_id=%s", goal.user_id)
    connectors = get_connectors()

    raw_data = {}

    if "strava" in connectors:
        raw_data["strava"] = await connectors["strava"].fetch_activity_range(goal.user_id)

    if "calendar" in connectors:
        raw_data["calendar"] = await connectors["calendar"].fetch_calendar(goal.user_id)

    logger.info("node sync done user_id=%s sources=%s", goal.user_id, list(raw_data))

    return {
        "raw_data": raw_data,
        "decision_log": [
            *state.get("decision_log", []),
            {
                "agent": "sync",
                "message": "Connected data retrieved",
                "sources": list(raw_data),
            },
        ],
    }


async def profile_node(state: CoachState) -> dict:
    logger.info("node profile start user_id=%s", state["goal"].user_id)
    profile = await analyze_athlete(
        goal=state["goal"],
        raw_data=state.get("raw_data", {}),
    )

    logger.info(
        "node profile done user_id=%s primary_sports=%s missing_info=%d",
        state["goal"].user_id,
        profile.primary_sports,
        len(profile.missing_information),
    )

    return {
        "athlete_profile": profile,
        "decision_log": [
            *state.get("decision_log", []),
            {
                "agent": "profile_analyzer",
                "message": "Athlete profile analyzed",
                "sports": profile.primary_sports,
            },
        ],
    }


async def planning_node(state: CoachState) -> dict:
    logger.info(
        "node planning start user_id=%s previous_attempt=%d",
        state["goal"].user_id,
        state.get("generation_attempt", 0),
    )
    previous_plan = state.get("plan")
    previous_validation = state.get("validation")

    errors = None
    if previous_validation:
        errors = [issue.model_dump(mode="json") for issue in previous_validation.issues]

    plan = await generate_training_plan(
        goal=state["goal"],
        athlete_profile=state["athlete_profile"],
        raw_data=state.get("raw_data", {}),
        previous_plan=previous_plan,
        validation_errors=errors,
    )

    attempt = state.get("generation_attempt", 0) + 1
    logger.info(
        "node planning done user_id=%s attempt=%d sessions=%d",
        state["goal"].user_id,
        attempt,
        len(plan.sessions),
    )

    return {
        "plan": plan,
        "generation_attempt": attempt,
        "decision_log": [
            *state.get("decision_log", []),
            {
                "agent": "planner",
                "message": "Training plan generated",
                "attempt": attempt,
                "session_count": len(plan.sessions),
            },
        ],
    }


def validation_node(state: CoachState) -> dict:
    logger.info("node validation start user_id=%s", state["goal"].user_id)
    validation = validate_plan(
        goal=state["goal"],
        plan=state["plan"],
    )
    error_count = sum(issue.severity == "error" for issue in validation.issues)
    logger.info(
        "node validation done user_id=%s valid=%s issues=%d errors=%d",
        state["goal"].user_id,
        validation.valid,
        len(validation.issues),
        error_count,
    )

    return {
        "validation": validation,
        "decision_log": [
            *state.get("decision_log", []),
            {
                "agent": "validator",
                "message": "Plan validated",
                "valid": validation.valid,
                "issues": len(validation.issues),
            },
        ],
    }


def route_after_validation(state: CoachState) -> str:
    validation = state["validation"]

    if validation.valid:
        logger.info("route validation->briefing user_id=%s", state["goal"].user_id)
        return "briefing"

    if state.get("generation_attempt", 0) >= state.get("max_generation_attempts", 3):
        logger.info("route validation->fallback user_id=%s", state["goal"].user_id)
        return "fallback"

    logger.info("route validation->planning user_id=%s", state["goal"].user_id)
    return "planning"


def fallback_node(state: CoachState) -> dict:
    logger.warning(
        "node fallback reached user_id=%s attempts=%d",
        state["goal"].user_id,
        state.get("generation_attempt", 0),
    )
    return {
        "safety": {
            "status": "manual_review_required",
            "message": (
                "Le programme n'a pas pu satisfaire toutes les regles "
                "apres plusieurs tentatives."
            ),
        },
        "decision_log": [
            *state.get("decision_log", []),
            {
                "agent": "fallback",
                "message": "Manual review required after retries",
            },
        ],
    }


async def briefing_node(state: CoachState) -> dict:
    logger.info("node briefing start user_id=%s", state["goal"].user_id)
    plan = state["plan"]
    first_session = plan.sessions[0] if plan.sessions else None

    athlete_message = (
        "Ton programme a ete cree."
        if first_session is None
        else (
            f"Ta premiere seance est '{first_session.title}', "
            f"prevue le {first_session.session_date.isoformat()} "
            f"pour environ {first_session.duration_min} minutes."
        )
    )

    return {
        "briefing": {
            "athlete": athlete_message,
            "coach": f"{len(plan.sessions)} seances generees. Strategie: {plan.strategy}",
        },
        "safety": {
            "status": "validated",
            "disclaimer": "Ces recommandations ne remplacent pas un avis medical.",
        },
    }


def build_graph():
    builder = StateGraph(CoachState)

    builder.add_node("sync", sync_node)
    builder.add_node("profile", profile_node)
    builder.add_node("planning", planning_node)
    builder.add_node("validation", validation_node)
    builder.add_node("fallback", fallback_node)
    builder.add_node("briefing", briefing_node)

    builder.add_edge(START, "sync")
    builder.add_edge("sync", "profile")
    builder.add_edge("profile", "planning")
    builder.add_edge("planning", "validation")

    builder.add_conditional_edges(
        "validation",
        route_after_validation,
        {
            "planning": "planning",
            "briefing": "briefing",
            "fallback": "fallback",
        },
    )

    builder.add_edge("briefing", END)
    builder.add_edge("fallback", END)

    return builder.compile()


graph = build_graph()


async def run_planning(goal: GoalInput) -> CoachState:
    logger.info("run_planning start user_id=%s", goal.user_id)
    initial_state: CoachState = {
        "goal": goal,
        "raw_data": {},
        "generation_attempt": 0,
        "max_generation_attempts": 3,
        "decision_log": [],
    }

    result = await graph.ainvoke(initial_state)
    logger.info(
        "run_planning done user_id=%s final_valid=%s",
        goal.user_id,
        result.get("validation").valid if result.get("validation") else None,
    )
    return result
