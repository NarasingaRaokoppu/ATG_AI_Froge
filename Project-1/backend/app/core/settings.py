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
    IMAGE_GEN_MAX_RETRIES: int = 2
    IMAGE_GEN_RATE_LIMIT_PER_MINUTE: int = 10
    IMAGE_GEN_PROMPT_MAX_LENGTH: int = 2000
    LITELLM_USER_ID: str | None = None

    # Google OAuth
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/google/callback"

    # ChromaDB
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    RAG_COLLECTION_PREFIX: str = "rag"
    RAG_MAX_UPLOAD_MB: int = 50
    RAG_CHUNK_SIZE: int = 1200
    RAG_CHUNK_OVERLAP: int = 150
    RAG_TOP_K: int = 6
    RAG_MIN_CONFIDENCE: float = 0.18
    RAG_HISTORY_TURNS: int = 5

    # Google Sheets
    GOOGLE_SERVICE_ACCOUNT_JSON: str | None = None

    # File uploads
    MAX_UPLOAD_MB: int = 20
    UPLOAD_DIR: str = "./uploads"
    # Base URL at which the backend is publicly reachable (used to build
    # absolute attachment URLs sent to the LLM vision API)
    PUBLIC_BASE_URL: str = "http://localhost:8000"

    class Config:
        """Pydantic config."""

        env_file = (".env", "../.env")
        case_sensitive = True


# Global settings instance
settings = Settings()
