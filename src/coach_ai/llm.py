from functools import lru_cache
from typing import Any, TypeVar

from openai import OpenAI
from pydantic import BaseModel

from coach_ai.config import get_settings

T = TypeVar("T", bound=BaseModel)


def _normalize_openai_model_name(model_name: str) -> str:
    if model_name.startswith("openai:"):
        return model_name.split(":", 1)[1]
    return model_name


@lru_cache(maxsize=1)
def get_openai_client() -> OpenAI:
    return OpenAI()


def parse_to_format(
    input_text: str,
    output_structure: type[T],
    system_prompt: str,
    **llm_params: Any,
) -> T:
    """Genere et valide une reponse structuree avec Pydantic."""
    settings = get_settings()

    response = get_openai_client().responses.parse(
        model=_normalize_openai_model_name(settings.planning_model),
        instructions=system_prompt,
        input=input_text,
        text_format=output_structure,
        **llm_params,
    )

    if response.output_parsed is None:
        raise ValueError("OpenAI n'a pas retourne de contenu structure valide.")

    return response.output_parsed
