from __future__ import annotations

from typing import Any, NotRequired, Required, TypedDict

from coach_ai.models import AthleteProfile, GoalInput, TrainingPlan


class CoachState(TypedDict):
    goal: Required[GoalInput]
    decision_log: Required[list[dict[str, Any]]]
    athlete_profile: NotRequired[AthleteProfile]
    plan: NotRequired[TrainingPlan]
