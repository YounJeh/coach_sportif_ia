from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass
class GoalInput:
    user_id: str
    objective: str
    deadline: date
    available_slots: list[str]
    off_days: list[str] = field(default_factory=list)


@dataclass
class CoachState:
    goal: GoalInput
    raw_data: dict[str, Any] = field(default_factory=dict)
    quality_score: float = 0.0
    context: dict[str, Any] = field(default_factory=dict)
    plan: dict[str, Any] = field(default_factory=dict)
    safety: dict[str, Any] = field(default_factory=dict)
    briefing: dict[str, str] = field(default_factory=dict)
    decision_log: list[dict[str, Any]] = field(default_factory=list)
