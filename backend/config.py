from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT_DIR / "frontend"
LANDING_DIR = ROOT_DIR / "scrollcraft" / "builds" / "terminal-descent"
CASES_DIR = BACKEND_DIR / "scenarios" / "cases"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env", extra="ignore")

    app_name: str = "LLM Attack Lab"
    app_version: str = "0.1.0"
    api_prefix: str = "/api"
    run_timeout_seconds: int = 120
    allow_code_edit: bool = True


settings = Settings()
