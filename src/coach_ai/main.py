from __future__ import annotations

from datetime import date
import logging
import os
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from coach_ai.config import get_settings
from coach_ai.graph import run_planning
from coach_ai.models import GoalInput

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    stream=sys.stdout,
    force=True,
)

logger = logging.getLogger(__name__)

settings = get_settings()
app = FastAPI(
    title="Coach Sportif IA",
    version="0.2.0",
    description="Agentic adaptive training planning service",
)

origins = [origin.strip() for origin in settings.cors_allow_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=origins != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class GoalRequest(BaseModel):
    user_id: str
    objective: str
    deadline: date

    available_slots: list[str] = Field(default_factory=list)
    off_days: list[str] = Field(default_factory=list)

    preferred_sports: list[str] = Field(default_factory=list)
    disliked_sports: list[str] = Field(default_factory=list)
    equipment: list[str] = Field(default_factory=list)

    experience_level: str = "unknown"
    injuries_or_limitations: list[str] = Field(default_factory=list)

    sessions_per_week: int | None = None
    max_session_duration_min: int | None = None


@app.get("/health")
def health() -> dict[str, str]:
    logger.info("health requested")
    return {"status": "ok", "env": settings.app_env}


@app.post("/v1/plan")
def generate_plan(payload: GoalRequest) -> dict:
    logger.info(
        "plan request received user_id=%s deadline=%s slots=%d",
        payload.user_id,
        payload.deadline.isoformat(),
        len(payload.available_slots),
    )

    try:
        result = run_planning(GoalInput.model_validate(payload.model_dump()))

        plan = result["plan"] if "plan" in result else None
        decision_log = result["decision_log"]

        logger.info(
            "plan request completed user_id=%s plan_generated=%s sessions=%d decision_log=%d",
            payload.user_id,
            bool(plan),
            len(plan.sessions) if plan else 0,
            len(decision_log),
        )

        return {
            "plan": plan.model_dump(mode="json") if plan else None,
            "decision_log": decision_log,
        }
    except Exception:
        logger.exception("plan request failed user_id=%s", payload.user_id)
        raise
