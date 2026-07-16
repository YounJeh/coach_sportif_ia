from __future__ import annotations

import logging
from typing import cast

from langgraph.graph import END, START, StateGraph

from coach_ai.agents.plan_generator import generate_training_plan
from coach_ai.agents.profile_analyzer import analyze_athlete
from coach_ai.models import GoalInput
from coach_ai.state import CoachState

logger = logging.getLogger(__name__)


def profile_node(state: CoachState) -> dict:
    logger.info("node profile start user_id=%s", state["goal"].user_id)
    profile = analyze_athlete(goal=state["goal"])

    logger.info(
        "node profile done user_id=%s primary_sports=%s profile=%s",
        state["goal"].user_id,
        profile.primary_sports,
        profile,
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


def planning_node(state: CoachState) -> dict:
    logger.info("node planning start user_id=%s", state["goal"].user_id)
    if "athlete_profile" not in state:
        raise ValueError("athlete_profile missing from state")

    plan = generate_training_plan(
        goal=state["goal"],
        athlete_profile=state["athlete_profile"],
    )
    logger.info(
        "node planning done user_id=%s sessions=%d",
        state["goal"].user_id,
        len(plan.sessions),
    )

    return {
        "plan": plan,
        "decision_log": [
            *state.get("decision_log", []),
            {
                "agent": "planner",
                "message": "Training plan generated",
                "session_count": len(plan.sessions),
            },
        ],
    }


def build_graph():
    builder = StateGraph(CoachState)

    builder.add_node("profile", profile_node)
    builder.add_node("planning", planning_node)

    builder.add_edge(START, "profile")
    builder.add_edge("profile", "planning")
    builder.add_edge("planning", END)

    return builder.compile()


graph = build_graph()


def run_planning(goal: GoalInput) -> CoachState:
    logger.info("run_planning start user_id=%s", goal.user_id)
    initial_state: CoachState = {
        "goal": goal,
        "decision_log": [],
    }

    result = cast(CoachState, graph.invoke(initial_state))
    if "plan" not in result:
        raise ValueError("plan missing from final state")

    logger.info("run_planning done user_id=%s sessions=%d", goal.user_id, len(result["plan"].sessions))
    return result
