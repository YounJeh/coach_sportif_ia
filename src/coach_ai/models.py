from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class GoalInput(BaseModel):
    user_id: str
    objective: str
    deadline: date

class PlannedSession(BaseModel):
    session_date: date
    title: str
    sport: str
    objective: str
    duration_min: int = Field(ge=5, le=360)
    intensity: Literal["easy", "moderate", "hard"]

class TrainingPlan(BaseModel):
    objective: str
    sessions: list[PlannedSession] = Field(min_length=2, max_length=2)