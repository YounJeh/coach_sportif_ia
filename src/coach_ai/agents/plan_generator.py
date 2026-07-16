from __future__ import annotations

import json
import logging
from datetime import date

from coach_ai.llm import get_model
from coach_ai.models import GoalInput, TrainingPlan

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
Tu es un agent planificateur sportif minimaliste.

Tu dois produire un planning de exactement 2 seances individualisees et executables.
""".strip()

def generate_training_plan(
    goal: GoalInput,
) -> TrainingPlan:
    model = get_model().with_structured_output(
        TrainingPlan,
        method="json_schema",
        strict=True,
    )

    payload = {
        "today": date.today().isoformat(),
        "goal": goal.model_dump(mode="json"),
    }

    logger.info(f"payload for training plan generation: {json.dumps(payload, ensure_ascii=False, default=str)}")

    result = model.invoke(
        [
            ("system", SYSTEM_PROMPT),
            (
                "user",
                "Genere un planning sportif de 2 seances." + "\n\n" + json.dumps(payload, ensure_ascii=False, default=str),
            ),
        ]
    )

    if isinstance(result, TrainingPlan):
        return result

    return TrainingPlan.model_validate(result)
