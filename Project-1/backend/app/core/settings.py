"""Configuration settings loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # App
    APP_NAME: str = "amzur-ai-chat"
    ENVIRONMENT: str = "development"
    SECRET_KEY: str
    JWT_EXPIRE_MINUTES: int = 480

    # Database
    DATABASE_URL: str

    # Amzur LiteLLM Proxy
    LITELLM_PROXY_URL: str
    LITELLM_API_KEY: str
    LLM_MODEL: str = "gemini/gemini-2.5-flash"
    LITELLM_EMBEDDING_MODEL: str = "text-embedding-3-large"
    IMAGE_GEN_MODEL: str = "gemini/imagen-4.0-fast-generate-001"
    LITELLM_USER_ID: str | None = None

    # Google OAuth
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/google/callback"

    # ChromaDB
    CHROMA_PERSIST_DIR: str = "./chroma_db"

    # Google Sheets
    GOOGLE_SERVICE_ACCOUNT_JSON: str | None = None

    # File uploads
    MAX_UPLOAD_MB: int = 20
    UPLOAD_DIR: str = "./uploads"

    class Config:
        """Pydantic config."""

        env_file = (".env", "../.env")
        case_sensitive = True


# Global settings instance
settings = Settings()
