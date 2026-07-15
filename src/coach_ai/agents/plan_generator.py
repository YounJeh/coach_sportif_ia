from __future__ import annotations

import asyncio
import json
from datetime import date
from typing import Any

from coach_ai.config import get_settings
from coach_ai.llm import get_model
from coach_ai.models import AthleteProfile, GoalInput, TrainingPlan

SYSTEM_PROMPT = """
Tu es un planificateur sportif multidisciplinaire.

Tu dois produire un programme individualise et executable.

Principes obligatoires :
- respecter les disponibilites et les jours exclus ;
- adapter le programme au niveau et a l'historique ;
- creer une progression coherente ;
- repartir charge, recuperation et seances cles ;
- ne pas ajouter de seance sur un jour indisponible ;
- decrire precisement chaque bloc d'une seance ;
- proposer des adaptations courtes ou faciles ;
- ne pas presenter de conseil medical ;
- exprimer les hypotheses dans le champ assumptions ;
- utiliser les sports les plus adaptes a l'objectif, sans etre limite
  a une liste predefinie.

Le programme doit etre exploitable directement par une application.
""".strip()


async def generate_training_plan(
    goal: GoalInput,
    athlete_profile: AthleteProfile,
    raw_data: dict[str, Any],
    previous_plan: TrainingPlan | None = None,
    validation_errors: list[dict[str, Any]] | None = None,
) -> TrainingPlan:
    model = get_model().with_structured_output(TrainingPlan, method="function_calling")
    settings = get_settings()

    payload = {
        "today": date.today().isoformat(),
        "goal": goal.model_dump(mode="json"),
        "athlete_profile": athlete_profile.model_dump(mode="json"),
        "connected_data": raw_data,
        "previous_plan": previous_plan.model_dump(mode="json") if previous_plan else None,
        "validation_errors": validation_errors or [],
    }

    instruction = (
        "Genere le programme sportif."
        if previous_plan is None
        else "Corrige entierement le programme en tenant compte des erreurs."
    )

    return await asyncio.wait_for(
        model.ainvoke(
            [
                ("system", SYSTEM_PROMPT),
                (
                    "user",
                    f"{instruction}\n\n" + json.dumps(payload, ensure_ascii=False, default=str),
                ),
            ]
        ),
        timeout=settings.llm_timeout_sec,
    )
