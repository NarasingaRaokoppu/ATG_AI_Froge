"""FastAPI application entry point."""

"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api import auth as auth_router
from app.api import chat as chat_router
from app.api import messages as messages_router
from app.api import threads as threads_router
from app.api import upload as upload_router
from app.api.routes import research_digest as research_digest_router
from app.api.routes import spreadsheet as spreadsheet_router
from app.api.routes import sql as sql_router
from app.api.v1.routes import images as images_v1_router
from app.api.v1.routes import rag as rag_v1_router
from app.core import settings
from app.db import Base, engine
from app.models import (  # noqa: F401  (register mappers)
    DatabaseConnection,
    Document,
    DocumentChunk,
    GeneratedImage,
    ImageGenerationLog,
    Message,
    RagChatHistory,
    DocumentProcessingLog,
    SpreadsheetQueryHistory,
    SpreadsheetSession,
    SqlQueryHistory,
    Thread,
    User,
)


def _resolve_upload_dir() -> Path:
    configured = Path(settings.UPLOAD_DIR)
    if configured.is_absolute():
        return configured
    backend_root = Path(__file__).resolve().parents[1]
    return (backend_root / configured).resolve()


UPLOAD_DIR_PATH = _resolve_upload_dir()
UPLOAD_DIR_PATH.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Create tables on startup (dev convenience)."""
    UPLOAD_DIR_PATH.mkdir(parents=True, exist_ok=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Dev-time compatibility: add new message attachment columns if absent.
        await conn.execute(
            text(
                "ALTER TABLE messages "
                "ADD COLUMN IF NOT EXISTS attachment_type VARCHAR(32)"
            )
        )
        await conn.execute(
            text(
                "ALTER TABLE messages "
                "ADD COLUMN IF NOT EXISTS attachment_url TEXT"
            )
        )
        await conn.execute(
            text(
                "ALTER TABLE messages "
                "ADD COLUMN IF NOT EXISTS attachment_metadata JSONB"
            )
        )
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_messages_thread_created_at "
                "ON messages (thread_id, created_at)"
            )
        )
    yield


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Multi-user conversational AI platform",
    lifespan=lifespan,
)

# Configure CORS — credentials required for httpOnly cookies
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}


# Routers
app.include_router(auth_router.router, prefix="/api")
app.include_router(threads_router.router, prefix="/api")
app.include_router(messages_router.router, prefix="/api")
app.include_router(chat_router.router, prefix="/api")
app.include_router(upload_router.router, prefix="/api")
app.include_router(spreadsheet_router.router, prefix="/api")
app.include_router(sql_router.router, prefix="/api")
app.include_router(research_digest_router.router, prefix="/api")
app.include_router(images_v1_router.router, prefix="/api")
app.include_router(rag_v1_router.router, prefix="/api")

# Serve uploaded files directly for inline chat rendering.
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR_PATH)), name="uploads")
