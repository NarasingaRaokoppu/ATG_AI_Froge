"""FastAPI application entry point."""

"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth as auth_router
from app.api import chat as chat_router
from app.api import messages as messages_router
from app.api import threads as threads_router
from app.core import settings
from app.db import Base, engine
from app.models import Message, Thread, User  # noqa: F401  (register mappers)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Create tables on startup (dev convenience)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
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
