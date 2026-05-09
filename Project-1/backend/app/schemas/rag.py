"""Pydantic schemas for RAG APIs."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class RagDocumentResponse(BaseModel):
    id: UUID
    user_id: UUID
    thread_id: UUID
    filename: str
    file_size: int
    status: str
    upload_time: datetime
    processing_time: int | None = None
    chunk_count: int
    embedding_model: str

    model_config = {"from_attributes": True}


class RagUploadResponse(BaseModel):
    document: RagDocumentResponse
    message: str


class RagChatRequest(BaseModel):
    thread_id: UUID
    question: str = Field(..., min_length=1, max_length=8000)
    top_k: int | None = Field(default=None, ge=1, le=20)
    document_ids: list[UUID] = Field(default_factory=list)


class RagCitation(BaseModel):
    document_id: UUID
    filename: str
    page_number: int | None = None
    chunk_id: str
    content_preview: str
    score: float


class RagChatResponse(BaseModel):
    answer: str
    confidence: float | None = None
    citations: list[RagCitation] = Field(default_factory=list)
    grounded: bool


class RagDeleteResponse(BaseModel):
    deleted: bool
    document_id: UUID
