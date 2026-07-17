from __future__ import annotations

import json
import logging
from datetime import date

from coach_ai.llm import parse_to_format
from coach_ai.models import GoalInput, TrainingPlan

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
Tu es un agent planificateur sportif minimaliste.

Tu dois produire un planning de exactement 2 seances individualisees et executables.
""".strip()

def generate_training_plan(
    goal: GoalInput,
) -> TrainingPlan:
    payload = {
        "today": date.today().isoformat(),
        "goal": goal.model_dump(mode="json"),
    }

    logger.info(f"payload for training plan generation: {json.dumps(payload, ensure_ascii=False, default=str)}")

    return parse_to_format(
        input_text="Genere un planning sportif de 2 seances." + "\n\n" + json.dumps(payload, ensure_ascii=False, default=str),
        output_structure=TrainingPlan,
        system_prompt=SYSTEM_PROMPT,
        reasoning={"effort": "minimal"},
    )
