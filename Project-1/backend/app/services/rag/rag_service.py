"""RAG orchestration service for PDF ingestion and grounded chat."""

from __future__ import annotations

import asyncio
import re
import time
import uuid
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm import llm
from app.core import settings
from app.db import AsyncSessionLocal
from app.db.repositories import RagRepository
from app.models import Document, DocumentChunk, User
from app.schemas.rag import RagCitation, RagChatResponse
from app.services import thread_service
from app.services.rag.document_processor import DocumentProcessor
from app.services.rag.vector_store import RagVectorStore

_ALLOWED_EXTENSIONS = {".pdf"}
_ALLOWED_MIME_TYPES = {"application/pdf"}
_GENERIC_ALLOWED_MIME_TYPES = {"application/octet-stream", "binary/octet-stream"}
_SAFE_NAME_RE = re.compile(r"[^a-zA-Z0-9._-]+")


class RagService:
    """Coordinates persistence, vector indexing, and retrieval-based QA."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = RagRepository(db)
        self.processor = DocumentProcessor()
        self.vector_store = RagVectorStore()

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        cleaned = _SAFE_NAME_RE.sub("_", name).strip("._")
        return cleaned or "document.pdf"

    @staticmethod
    def _compress_context(text: str, max_chars: int = 900) -> str:
        compact = re.sub(r"\s+", " ", text).strip()
        if len(compact) <= max_chars:
            return compact
        return compact[:max_chars].rsplit(" ", 1)[0] + "..."

    @staticmethod
    def _rerank_score(question: str, text: str, base_score: float) -> float:
        q_terms = {w for w in re.findall(r"[a-zA-Z0-9]+", question.lower()) if len(w) > 2}
        if not q_terms:
            return base_score
        t_terms = set(re.findall(r"[a-zA-Z0-9]+", text.lower()))
        overlap = len(q_terms & t_terms) / max(len(q_terms), 1)
        return (0.75 * base_score) + (0.25 * overlap)

    @staticmethod
    def _documents_root() -> Path:
        base = Path(settings.UPLOAD_DIR)
        if not base.is_absolute():
            base = (Path(__file__).resolve().parents[3] / base).resolve()
        root = base / "rag"
        root.mkdir(parents=True, exist_ok=True)
        return root

    async def validate_thread_access(self, *, current_user: User, thread_id: UUID) -> None:
        await thread_service.get_thread_for_user(self.db, thread_id, current_user.id)

    async def upload_pdf(
        self,
        *,
        current_user: User,
        thread_id: UUID,
        file: UploadFile,
    ) -> Document:
        await self.validate_thread_access(current_user=current_user, thread_id=thread_id)

        filename = self._sanitize_filename(file.filename or "document.pdf")
        ext = Path(filename).suffix.lower()
        mime = (file.content_type or "application/octet-stream").lower()

        valid_ext = ext in _ALLOWED_EXTENSIONS
        valid_mime = mime in _ALLOWED_MIME_TYPES or (
            valid_ext and mime in _GENERIC_ALLOWED_MIME_TYPES
        )
        if not valid_ext or not valid_mime:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "invalid_pdf",
                    "message": "Only PDF files are allowed.",
                },
            )

        max_bytes = settings.RAG_MAX_UPLOAD_MB * 1024 * 1024
        total = 0
        chunks: list[bytes] = []
        while True:
            buf = await file.read(1024 * 1024)
            if not buf:
                break
            total += len(buf)
            if total > max_bytes:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail={
                        "error": "file_too_large",
                        "message": f"File exceeds {settings.RAG_MAX_UPLOAD_MB} MB limit.",
                    },
                )
            chunks.append(buf)
        await file.close()

        if total == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "empty_file", "message": "Uploaded PDF is empty."},
            )

        doc_id = uuid.uuid4()
        user_dir = self._documents_root() / str(current_user.id) / str(thread_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        storage_path = user_dir / f"{doc_id}.pdf"
        storage_path.write_bytes(b"".join(chunks))

        document = await self.repo.create_document(
            user_id=current_user.id,
            thread_id=thread_id,
            filename=filename,
            storage_path=str(storage_path),
            mime_type=mime,
            file_size=total,
            embedding_model="text-embedding-3-large",
            status="queued",
        )
        await self.repo.add_processing_log(
            document_id=document.id,
            user_id=current_user.id,
            thread_id=thread_id,
            status="queued",
            step="upload",
            message="PDF uploaded and queued for background processing",
        )
        return document

    async def process_document(self, *, document_id: UUID) -> None:
        start = time.perf_counter()
        async with AsyncSessionLocal() as task_db:
            repo = RagRepository(task_db)
            processor = DocumentProcessor()
            vector_store = RagVectorStore()

            document = await task_db.get(Document, document_id)
            if not document:
                return

            try:
                await repo.set_document_status(document=document, status="processing")
                await repo.add_processing_log(
                    document_id=document.id,
                    user_id=document.user_id,
                    thread_id=document.thread_id,
                    status="processing",
                    step="extract",
                    message="Extracting PDF text",
                )

                pdf_path = Path(document.storage_path)
                pages = await asyncio.to_thread(processor.extract_pages, pdf_path)
                if all(not (text or "").strip() for _, text in pages):
                    await repo.add_processing_log(
                        document_id=document.id,
                        user_id=document.user_id,
                        thread_id=document.thread_id,
                        status="warning",
                        step="extract",
                        message="No text detected. OCR pipeline can be plugged in for scanned PDFs.",
                    )

                await repo.add_processing_log(
                    document_id=document.id,
                    user_id=document.user_id,
                    thread_id=document.thread_id,
                    status="processing",
                    step="chunk",
                    message="Chunking extracted text",
                )
                chunks = processor.build_chunks(
                    pages=pages,
                    document_id=str(document.id),
                    filename=document.filename,
                    semantic_chunking=True,
                )
                if not chunks:
                    elapsed_ms = int((time.perf_counter() - start) * 1000)
                    await repo.set_document_status(
                        document=document,
                        status="failed",
                        processing_time_ms=elapsed_ms,
                    )
                    await repo.add_processing_log(
                        document_id=document.id,
                        user_id=document.user_id,
                        thread_id=document.thread_id,
                        status="failed",
                        step="chunk",
                        message="No extractable text chunks found",
                        processing_time_ms=elapsed_ms,
                    )
                    return

                texts = [c.text for c in chunks]
                embeds = await processor.embed_chunks(texts)

                metadatas: list[dict[str, Any]] = []
                ids: list[str] = []
                orm_chunks: list[DocumentChunk] = []
                for c in chunks:
                    metadata = {
                        **c.metadata,
                        "user_id": str(document.user_id),
                        "thread_id": str(document.thread_id),
                        "created_at": repo.now_utc().isoformat(),
                    }
                    ids.append(c.chunk_id)
                    metadatas.append(metadata)
                    orm_chunks.append(
                        DocumentChunk(
                            document_id=document.id,
                            user_id=document.user_id,
                            thread_id=document.thread_id,
                            chunk_id=c.chunk_id,
                            chunk_index=c.chunk_index,
                            page_number=c.page_number,
                            content=c.text,
                            embedding_model=document.embedding_model,
                        )
                    )

                await repo.delete_chunks_for_document(document_id=document.id)
                await repo.add_document_chunks(orm_chunks)
                await asyncio.to_thread(
                    vector_store.upsert_chunks,
                    user_id=document.user_id,
                    thread_id=document.thread_id,
                    ids=ids,
                    embeddings=embeds,
                    documents=texts,
                    metadatas=metadatas,
                )

                elapsed_ms = int((time.perf_counter() - start) * 1000)
                await repo.set_document_status(
                    document=document,
                    status="processed",
                    chunk_count=len(chunks),
                    processing_time_ms=elapsed_ms,
                )
                await repo.add_processing_log(
                    document_id=document.id,
                    user_id=document.user_id,
                    thread_id=document.thread_id,
                    status="processed",
                    step="index",
                    message=f"Indexed {len(chunks)} chunks",
                    processing_time_ms=elapsed_ms,
                )
            except Exception as exc:  # noqa: BLE001
                elapsed_ms = int((time.perf_counter() - start) * 1000)
                await repo.set_document_status(
                    document=document,
                    status="failed",
                    processing_time_ms=elapsed_ms,
                )
                await repo.add_processing_log(
                    document_id=document.id,
                    user_id=document.user_id,
                    thread_id=document.thread_id,
                    status="failed",
                    step="ingestion",
                    message="Document ingestion failed",
                    error_details={"error": str(exc)},
                    processing_time_ms=elapsed_ms,
                )

    async def list_documents(
        self,
        *,
        current_user: User,
        thread_id: UUID,
    ) -> list[Document]:
        await self.validate_thread_access(current_user=current_user, thread_id=thread_id)
        return await self.repo.list_documents_for_thread(
            user_id=current_user.id,
            thread_id=thread_id,
        )

    async def delete_document(
        self,
        *,
        current_user: User,
        thread_id: UUID,
        document_id: UUID,
    ) -> None:
        await self.validate_thread_access(current_user=current_user, thread_id=thread_id)
        document = await self.repo.get_document_for_user(
            document_id=document_id,
            user_id=current_user.id,
            thread_id=thread_id,
        )
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "not_found", "message": "Document not found"},
            )

        await asyncio.to_thread(
            self.vector_store.delete_by_document,
            user_id=current_user.id,
            thread_id=thread_id,
            document_id=document_id,
        )
        try:
            Path(document.storage_path).unlink(missing_ok=True)
        except Exception:
            pass
        await self.repo.delete_document(document)

    async def rag_chat(
        self,
        *,
        current_user: User,
        thread_id: UUID,
        question: str,
        top_k: int | None,
        document_ids: list[UUID],
    ) -> RagChatResponse:
        await self.validate_thread_access(current_user=current_user, thread_id=thread_id)

        available_docs = await self.repo.list_documents_for_thread(
            user_id=current_user.id,
            thread_id=thread_id,
        )
        processed_ids = {d.id for d in available_docs if d.status == "processed"}
        if not processed_ids:
            return RagChatResponse(
                answer="The document does not mention this.",
                confidence=0.0,
                citations=[],
                grounded=False,
            )

        filtered_ids = [doc_id for doc_id in document_ids if doc_id in processed_ids]
        where: dict[str, Any] | None = None
        if filtered_ids:
            where = {"document_id": {"$in": [str(d) for d in filtered_ids]}}

        k = top_k or settings.RAG_TOP_K
        query_embedding = await self.processor.embed_query(question)
        results = await asyncio.to_thread(
            self.vector_store.query,
            user_id=current_user.id,
            thread_id=thread_id,
            embedding=query_embedding,
            top_k=k,
            where=where,
        )

        docs = (results.get("documents") or [[]])[0]
        metadatas = (results.get("metadatas") or [[]])[0]
        distances = (results.get("distances") or [[]])[0]

        citations: list[RagCitation] = []
        scored_rows: list[tuple[float, dict[str, Any], str]] = []

        for idx, doc_text in enumerate(docs):
            metadata = metadatas[idx] if idx < len(metadatas) else {}
            distance = float(distances[idx]) if idx < len(distances) else 1.0
            base_score = 1.0 / (1.0 + max(distance, 0.0))
            final_score = self._rerank_score(question, doc_text, base_score)
            scored_rows.append((final_score, metadata, doc_text))

        scored_rows.sort(key=lambda row: row[0], reverse=True)
        top_rows = scored_rows[:k]

        context_parts: list[str] = []
        confidences: list[float] = []

        for idx, (score, metadata, doc_text) in enumerate(top_rows):
            confidences.append(score)
            compressed = self._compress_context(doc_text)
            preview = compressed[:280] + ("..." if len(compressed) > 280 else "")
            raw_doc_id = metadata.get("document_id") or str(next(iter(processed_ids)))
            citations.append(
                RagCitation(
                    document_id=UUID(str(raw_doc_id)),
                    filename=str(metadata.get("filename", "unknown.pdf")),
                    page_number=metadata.get("page_number"),
                    chunk_id=str(metadata.get("chunk_id", f"chunk-{idx}")),
                    content_preview=preview,
                    score=score,
                )
            )
            context_parts.append(
                f"[Source {idx + 1}] File: {metadata.get('filename', 'unknown.pdf')} | "
                f"Page: {metadata.get('page_number', 'n/a')}\n{compressed}"
            )

        confidence = max(confidences) if confidences else 0.0
        if not context_parts or confidence < settings.RAG_MIN_CONFIDENCE:
            answer = "The document does not mention this."
            grounded = False
        else:
            history_turns = await self.repo.get_recent_chat_turns(
                user_id=current_user.id,
                thread_id=thread_id,
                limit=settings.RAG_HISTORY_TURNS,
            )
            history_text = "\n".join(
                f"Q: {turn.question}\nA: {turn.answer}" for turn in history_turns
            )
            context_text = "\n\n".join(context_parts)
            prompt = (
                "You are an enterprise RAG assistant. Use only provided context. "
                "If context is insufficient, answer exactly: 'The document does not mention this.'\n\n"
                f"Conversation history:\n{history_text or '(none)'}\n\n"
                f"Context:\n{context_text}\n\n"
                f"Question: {question}\n\n"
                "Respond with a concise grounded answer and quote source references in [Source N] form."
            )
            response = await llm.ainvoke(prompt)
            answer = getattr(response, "content", str(response)).strip()
            grounded = answer.lower() != "the document does not mention this."

        citation_payload = [c.model_dump(mode="json") for c in citations]
        await self.repo.add_chat_turn(
            user_id=current_user.id,
            thread_id=thread_id,
            question=question,
            answer=answer,
            sources=citation_payload,
            retrieval_confidence=confidence,
        )

        return RagChatResponse(
            answer=answer,
            confidence=confidence,
            citations=citations,
            grounded=grounded,
        )
