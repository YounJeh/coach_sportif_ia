from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class GoalInput(BaseModel):
    user_id: str
    objective: str
    deadline: date

    available_slots: list[str] = Field(default_factory=list)
    off_days: list[str] = Field(default_factory=list)
    sessions_per_week: int | None = Field(default=None, ge=1, le=14)
    max_session_duration_min: int | None = Field(default=None, ge=10, le=300)


class PlannedSession(BaseModel):
    session_date: date
    title: str
    sport: str
    objective: str
    duration_min: int = Field(ge=5, le=360)
    intensity: Literal["easy", "moderate", "hard"]
    notes: str | None = None


class TrainingPlan(BaseModel):
    objective: str
    strategy: str
    sessions: list[PlannedSession] = Field(min_length=2, max_length=2)
    assumptions: list[str] = Field(default_factory=list)
