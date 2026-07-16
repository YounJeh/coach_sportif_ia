from __future__ import annotations

import json
import logging

from coach_ai.llm import get_model
from coach_ai.models import AthleteProfile, GoalInput

logger = logging.getLogger("coach_ai.main")

SYSTEM_PROMPT = """
Tu es un coach sportif expert en planification d'entrainement.

Analyse uniquement la demande de l'athlete.

Tu dois :
- remplir un profil minimal avec:
    objective_summary, primary_sports, current_level, constraints, assumptions ;
- proposer 1 a 2 sports principaux adaptes ;
- rester prudent quand l'information manque ;
- ne jamais inventer des faits de sante.

Tu ne generes pas encore les seances.
""".strip()


def analyze_athlete(goal: GoalInput) -> AthleteProfile:
    model = get_model().with_structured_output(AthleteProfile, method="function_calling")

    payload = {
        "goal": goal.model_dump(mode="json"),
    }

    logger.info(
        "analyze_athlete start user_id=%s deadline=%s payload=%s model=%s settings=%s",
        goal.user_id,
        goal.deadline.isoformat(),
        payload,
        model,
        "timeouts_disabled",
    )

    result = model.invoke(
        [
            ("system", SYSTEM_PROMPT),
            (
                "user",
                "Analyse ce profil sportif :\n"
                + json.dumps(payload, ensure_ascii=False, default=str),
            ),
        ]
    )

    if isinstance(result, AthleteProfile):
        return result

    return AthleteProfile.model_validate(result)
