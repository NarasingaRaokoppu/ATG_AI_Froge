from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    if settings.use_in_memory_repo:
        storage_mode = "in_memory"
    elif settings.supabase_url and settings.supabase_key:
        storage_mode = "supabase"
    elif settings.database_url:
        storage_mode = "postgres"
    else:
        storage_mode = "in_memory"
    return {"status": "ok", "version": settings.app_version, "storage_mode": storage_mode}


app.include_router(router)
