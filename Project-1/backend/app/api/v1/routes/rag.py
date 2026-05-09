"""RAG routes for PDF ingestion and retrieval chat."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db import get_db
from app.models import User
from app.schemas.rag import (
    RagChatRequest,
    RagChatResponse,
    RagDeleteResponse,
    RagDocumentResponse,
    RagUploadResponse,
)
from app.services.rag import RagService

router = APIRouter(prefix="/v1/rag", tags=["rag"])


@router.post(
    "/upload",
    response_model=RagUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_rag_pdf(
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    thread_id: Annotated[UUID, Form(...)],
    file: UploadFile = File(...),
) -> RagUploadResponse:
    """Upload a PDF and enqueue background indexing."""
    service = RagService(db)
    document = await service.upload_pdf(
        current_user=current_user,
        thread_id=thread_id,
        file=file,
    )
    background_tasks.add_task(service.process_document, document_id=document.id)

    return RagUploadResponse(
        document=RagDocumentResponse.model_validate(document),
        message="Document uploaded and queued for indexing",
    )


@router.post("/chat", response_model=RagChatResponse)
async def rag_chat(
    payload: RagChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RagChatResponse:
    """Ask a question grounded in indexed thread documents."""
    service = RagService(db)
    return await service.rag_chat(
        current_user=current_user,
        thread_id=payload.thread_id,
        question=payload.question,
        top_k=payload.top_k,
        document_ids=payload.document_ids,
    )


@router.get("/documents", response_model=list[RagDocumentResponse])
async def list_rag_documents(
    thread_id: Annotated[UUID, Query(...)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[RagDocumentResponse]:
    """List PDFs uploaded for a thread."""
    service = RagService(db)
    docs = await service.list_documents(current_user=current_user, thread_id=thread_id)
    return [RagDocumentResponse.model_validate(d) for d in docs]


@router.delete("/documents/{document_id}", response_model=RagDeleteResponse)
async def delete_rag_document(
    document_id: UUID,
    thread_id: Annotated[UUID, Query(...)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RagDeleteResponse:
    """Delete document metadata, file, and vector chunks."""
    service = RagService(db)
    await service.delete_document(
        current_user=current_user,
        thread_id=thread_id,
        document_id=document_id,
    )
    return RagDeleteResponse(deleted=True, document_id=document_id)
