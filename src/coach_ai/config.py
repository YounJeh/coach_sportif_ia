from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = Field(default="development", alias="APP_ENV")
    app_port: int = Field(default=8080, alias="APP_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    llm_provider: str = Field(default="vertex", alias="LLM_PROVIDER")
    planning_model: str = Field(default="gpt-5-nano", alias="PLANNING_MODEL")
    gcp_project_id: str = Field(default="", alias="GCP_PROJECT_ID")
    gcp_location: str = Field(default="europe-west1", alias="GCP_LOCATION")

    db_url: str = Field(default="", alias="DB_URL")
    redis_url: str = Field(default="", alias="REDIS_URL")
    cors_allow_origins: str = Field(default="*", alias="CORS_ALLOW_ORIGINS")

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
