from __future__ import annotations

from typing import Any, TypedDict

from coach_ai.models import AthleteProfile, GoalInput, PlanValidation, TrainingPlan


class CoachState(TypedDict, total=False):
    goal: GoalInput
    raw_data: dict[str, Any]
    athlete_profile: AthleteProfile
    plan: TrainingPlan
    validation: PlanValidation
    generation_attempt: int
    max_generation_attempts: int
    safety: dict[str, Any]
    briefing: dict[str, str]
    decision_log: list[dict[str, Any]]
