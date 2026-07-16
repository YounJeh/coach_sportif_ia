from functools import lru_cache

from langchain_openai import ChatOpenAI

from coach_ai.config import get_settings


def _normalize_openai_model_name(model_name: str) -> str:
    if model_name.startswith("openai:"):
        return model_name.split(":", 1)[1]
    return model_name


@lru_cache(maxsize=1)
def get_model():
    settings = get_settings()
    return ChatOpenAI(
        model=_normalize_openai_model_name(settings.planning_model),
        temperature=0,
    )
