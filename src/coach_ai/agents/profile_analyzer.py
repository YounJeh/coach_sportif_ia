from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from coach_ai.config import get_settings
from coach_ai.llm import get_model
from coach_ai.models import AthleteProfile, GoalInput

logger = logging.getLogger("coach_ai.main")

SYSTEM_PROMPT = """
Tu es un coach sportif expert en planification d'entrainement.

Analyse l'objectif de l'athlete et ses donnees disponibles.

Tu dois :
- identifier la nature reelle de l'objectif ;
- determiner les sports et modalites pertinents ;
- evaluer le niveau probable ;
- identifier les contraintes ;
- estimer une frequence realiste ;
- signaler explicitement toute hypothese ;
- ne jamais inventer de blessure, de performance ou de disponibilite ;
- rester conservateur lorsque les donnees sont insuffisantes.

Tu ne generes pas encore les seances.
""".strip()


async def analyze_athlete(goal: GoalInput, raw_data: dict[str, Any]) -> AthleteProfile:
    model = get_model().with_structured_output(AthleteProfile, method="function_calling")
    settings = get_settings()

    payload = {
        "goal": goal.model_dump(mode="json"),
        "connected_data": raw_data,
    }

    logger.info(
        "analyze_athlete start user_id=%s deadline=%s payload=%s model=%s settings=%s",
        goal.user_id,
        goal.deadline.isoformat(),
        payload,
        model,
        settings,
    )

    return await asyncio.wait_for(
        model.ainvoke(
            [
                ("system", SYSTEM_PROMPT),
                (
                    "user",
                    "Analyse ce profil sportif :\n"
                    + json.dumps(payload, ensure_ascii=False, default=str),
                ),
            ]
        ),
        timeout=settings.llm_timeout_sec,
    )
