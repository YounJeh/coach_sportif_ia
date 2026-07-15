from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class GoalInput(BaseModel):
    user_id: str
    objective: str
    deadline: date
    available_slots: list[str] = Field(default_factory=list)
    off_days: list[str] = Field(default_factory=list)

    preferred_sports: list[str] = Field(default_factory=list)
    disliked_sports: list[str] = Field(default_factory=list)
    equipment: list[str] = Field(default_factory=list)

    experience_level: Literal[
        "beginner",
        "intermediate",
        "advanced",
        "unknown",
    ] = "unknown"

    injuries_or_limitations: list[str] = Field(default_factory=list)
    sessions_per_week: int | None = Field(default=None, ge=1, le=14)
    max_session_duration_min: int | None = Field(default=None, ge=10, le=300)


class AthleteProfile(BaseModel):
    objective_summary: str
    objective_type: str
    primary_sports: list[str]
    secondary_sports: list[str] = Field(default_factory=list)

    current_level: str
    estimated_sessions_per_week: int
    constraints: list[str] = Field(default_factory=list)
    equipment: list[str] = Field(default_factory=list)

    average_recent_rpe: float | None = None
    recent_training_load: str = "unknown"
    recovery_status: str = "unknown"

    planning_horizon_days: int
    assumptions: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)

    @field_validator("assumptions", "missing_information", mode="before")
    @classmethod
    def normalize_list_like_fields(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            normalized = value.replace("\n", ",").replace(";", ",")
            return [part.strip() for part in normalized.split(",") if part.strip()]
        return [str(value).strip()]


class ExerciseBlock(BaseModel):
    name: str
    category: str
    duration_min: int | None = None
    sets: int | None = None
    reps: int | None = None
    distance_m: int | None = None
    intensity: str | None = None
    rest_seconds: int | None = None
    instructions: str | None = None


class PlannedSession(BaseModel):
    session_date: date
    title: str
    sport: str
    session_type: str

    objective: str
    duration_min: int = Field(ge=5, le=360)
    target_rpe: float = Field(ge=1, le=10)

    warmup: list[ExerciseBlock] = Field(default_factory=list)
    main_work: list[ExerciseBlock] = Field(default_factory=list)
    cooldown: list[ExerciseBlock] = Field(default_factory=list)

    adaptation_short: str | None = None
    adaptation_easy: str | None = None
    coach_notes: str | None = None

    metadata: dict[str, Any] = Field(default_factory=dict)


class TrainingPlan(BaseModel):
    objective: str
    strategy: str
    start_date: date
    end_date: date

    sessions: list[PlannedSession]

    progression_logic: str
    recovery_strategy: str
    assumptions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ValidationIssue(BaseModel):
    code: str
    severity: Literal["warning", "error"]
    message: str
    session_index: int | None = None


class PlanValidation(BaseModel):
    valid: bool
    issues: list[ValidationIssue] = Field(default_factory=list)
