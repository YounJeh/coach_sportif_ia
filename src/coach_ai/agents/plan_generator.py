from __future__ import annotations

import asyncio
import json
import logging
from datetime import date

from coach_ai.llm import get_model
from coach_ai.models import AthleteProfile, GoalInput, TrainingPlan

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
Tu es un agent planificateur sportif minimaliste.

Tu dois produire un planning de exactement 2 seances individualisees et executables.

Principes obligatoires :
- produire exactement 2 objets dans sessions, ni plus ni moins ;
- respecter les disponibilites et les jours exclus ;
- adapter les seances au niveau et aux contraintes ;
- pour chaque seance fournir: session_date, title, sport, objective, duration_min, intensity, notes ;
- ne pas presenter de conseil medical ;
- expliciter les hypotheses dans assumptions.
""".strip()


async def generate_training_plan(
    goal: GoalInput,
    athlete_profile: AthleteProfile,
) -> TrainingPlan:
    model = get_model().with_structured_output(TrainingPlan, method="function_calling")

    payload = {
        "today": date.today().isoformat(),
        "goal": goal.model_dump(mode="json"),
        "athlete_profile": athlete_profile.model_dump(mode="json"),
    }

    logger.info(f"payload for training plan generation: {json.dumps(payload, ensure_ascii=False, default=str)}")

    result = await asyncio.wait_for(
        model.ainvoke(
            [
                ("system", SYSTEM_PROMPT),
                (
                    "user",
                    "Genere un planning sportif de 2 seances." + "\n\n" + json.dumps(payload, ensure_ascii=False, default=str),
                ),
            ]
        ),
        timeout=300,
    )

    if isinstance(result, TrainingPlan):
        return result

    return TrainingPlan.model_validate(result)
