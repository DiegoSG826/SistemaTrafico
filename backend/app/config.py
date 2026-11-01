from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "sqlite:///./data/cuauhtemoc.db"
    admin_email: str = "admin@example.test"
    admin_password: str = ""
    app_db_password: str = ""
    jwt_secret: str = ""
    ml_service_url: str = "http://127.0.0.1:8001"
    model_dir: Path = Path("ml_model/artifacts")
    sim_speed: float = Field(default=10, gt=0, le=100)
    sim_seed: int = 20261031


def settings() -> Settings:
    return Settings()
