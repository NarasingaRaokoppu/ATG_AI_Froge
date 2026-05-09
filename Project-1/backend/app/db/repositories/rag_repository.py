"""Repository operations for RAG document and chat persistence."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Document, DocumentChunk, DocumentProcessingLog, RagChatHistory


class RagRepository:
    """Encapsulates SQL operations for the RAG domain."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_document(
        self,
        *,
        user_id: UUID,
        thread_id: UUID,
        filename: str,
        storage_path: str,
        mime_type: str,
        file_size: int,
        embedding_model: str,
        status: str = "queued",
    ) -> Document:
        document = Document(
            user_id=user_id,
            thread_id=thread_id,
            filename=filename,
            storage_path=storage_path,
            mime_type=mime_type,
            file_size=file_size,
            embedding_model=embedding_model,
            status=status,
        )
        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)
        return document

    async def get_document_for_user(
        self,
        *,
        document_id: UUID,
        user_id: UUID,
        thread_id: UUID | None = None,
    ) -> Document | None:
        stmt = select(Document).where(
            Document.id == document_id,
            Document.user_id == user_id,
        )
        if thread_id is not None:
            stmt = stmt.where(Document.thread_id == thread_id)
        return await self.db.scalar(stmt)

    async def list_documents_for_thread(
        self,
        *,
        user_id: UUID,
        thread_id: UUID,
    ) -> list[Document]:
        result = await self.db.scalars(
            select(Document)
            .where(Document.user_id == user_id, Document.thread_id == thread_id)
            .order_by(Document.upload_time.desc())
        )
        return list(result)

    async def set_document_status(
        self,
        *,
        document: Document,
        status: str,
        chunk_count: int | None = None,
        processing_time_ms: int | None = None,
    ) -> Document:
        document.status = status
        if chunk_count is not None:
            document.chunk_count = chunk_count
        if processing_time_ms is not None:
            document.processing_time = processing_time_ms
        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)
        return document

    async def add_document_chunks(self, chunks: list[DocumentChunk]) -> None:
        self.db.add_all(chunks)
        await self.db.commit()

    async def delete_document(self, document: Document) -> None:
        await self.db.delete(document)
        await self.db.commit()

    async def delete_chunks_for_document(self, *, document_id: UUID) -> None:
        await self.db.execute(
            delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
        )
        await self.db.commit()

    async def add_processing_log(
        self,
        *,
        user_id: UUID,
        thread_id: UUID,
        status: str,
        step: str,
        message: str | None = None,
        document_id: UUID | None = None,
        error_details: dict | None = None,
        processing_time_ms: int | None = None,
    ) -> DocumentProcessingLog:
        log = DocumentProcessingLog(
            document_id=document_id,
            user_id=user_id,
            thread_id=thread_id,
            status=status,
            step=step,
            message=message,
            error_details=error_details,
            processing_time_ms=processing_time_ms,
        )
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log

    async def add_chat_turn(
        self,
        *,
        user_id: UUID,
        thread_id: UUID,
        question: str,
        answer: str,
        sources: list[dict],
        retrieval_confidence: float | None,
    ) -> RagChatHistory:
        turn = RagChatHistory(
            user_id=user_id,
            thread_id=thread_id,
            question=question,
            answer=answer,
            sources=sources,
            retrieval_confidence=retrieval_confidence,
        )
        self.db.add(turn)
        await self.db.commit()
        await self.db.refresh(turn)
        return turn

    async def get_recent_chat_turns(
        self,
        *,
        user_id: UUID,
        thread_id: UUID,
        limit: int,
    ) -> list[RagChatHistory]:
        result = await self.db.scalars(
            select(RagChatHistory)
            .where(
                RagChatHistory.user_id == user_id,
                RagChatHistory.thread_id == thread_id,
            )
            .order_by(RagChatHistory.created_at.desc())
            .limit(limit)
        )
        turns = list(result)
        turns.reverse()
        return turns

    @staticmethod
    def now_utc() -> datetime:
        return datetime.now(timezone.utc)
