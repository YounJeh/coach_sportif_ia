from __future__ import annotations

from datetime import date

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from coach_ai.config import get_settings
from coach_ai.graph import run_planning
from coach_ai.state import GoalInput

settings = get_settings()
app = FastAPI(
    title="Coach Sportif IA",
    version="0.1.0",
    description="LangGraph orchestration service for adaptive training plans",
)

origins = [o.strip() for o in settings.cors_allow_origins.split(",") if o.strip()]
if not origins:
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GoalRequest(BaseModel):
    user_id: str = Field(..., examples=["athlete_123"])
    objective: str = Field(..., examples=["Courir un semi-marathon"])
    deadline: date
    available_slots: list[str] = Field(default_factory=list)
    off_days: list[str] = Field(default_factory=list)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.app_env}


@app.post("/v1/plan")
def generate_plan(payload: GoalRequest) -> dict:
    result = run_planning(
        GoalInput(
            user_id=payload.user_id,
            objective=payload.objective,
            deadline=payload.deadline,
            available_slots=payload.available_slots,
            off_days=payload.off_days,
        )
    )

    if isinstance(result, dict):
        plan = result.get("plan", {})
        briefing = result.get("briefing", {})
        safety = result.get("safety", {})
        quality_score = result.get("quality_score", 0.0)
        decision_log = result.get("decision_log", [])
    else:
        plan = result.plan
        briefing = result.briefing
        safety = result.safety
        quality_score = result.quality_score
        decision_log = result.decision_log

    return {
        "plan": plan,
        "briefing": briefing,
        "safety": safety,
        "quality_score": quality_score,
        "decision_log": decision_log,
    }
