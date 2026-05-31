from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Project14 Personalization API"
    app_version: str = "1.0.0"
    environment: str = "dev"
    use_in_memory_repo: bool = True

    supabase_url: str = ""
    supabase_key: str = ""
    database_url: str = ""

    # The MVP keeps pricing suggestions within safe limits.
    max_discount_pct: int = 20

    model_config = SettingsConfigDict(env_file=str(BASE_DIR / ".env"), env_file_encoding="utf-8")


settings = Settings()
