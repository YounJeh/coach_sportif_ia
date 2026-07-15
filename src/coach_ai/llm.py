from functools import lru_cache

from langchain.chat_models import init_chat_model

from coach_ai.config import get_settings


@lru_cache(maxsize=1)
def get_model():
    settings = get_settings()
    return init_chat_model(settings.planning_model, temperature=0.2)
