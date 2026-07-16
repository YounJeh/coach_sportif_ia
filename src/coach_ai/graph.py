from __future__ import annotations

import logging
from typing import cast

from langgraph.graph import END, START, StateGraph

from coach_ai.agents.plan_generator import generate_training_plan
from coach_ai.models import GoalInput
from coach_ai.state import CoachState

logger = logging.getLogger(__name__)


def planning_node(state: CoachState) -> dict:
    logger.info("node planning start user_id=%s", state["goal"].user_id)

    plan = generate_training_plan(
        goal=state["goal"],
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

    builder.add_node("planning", planning_node)

    builder.add_edge(START, "planning")
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
