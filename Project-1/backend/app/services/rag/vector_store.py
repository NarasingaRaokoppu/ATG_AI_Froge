"""Chroma vector store adapter for thread-scoped collections."""

from __future__ import annotations

import re
from pathlib import Path
from uuid import UUID

import chromadb

from app.core import settings

_SAFE_NAME_RE = re.compile(r"[^a-zA-Z0-9_-]+")


class RagVectorStore:
    """Wrapper around ChromaDB with per-thread collection strategy."""

    def __init__(self) -> None:
        persist_dir = Path(settings.CHROMA_PERSIST_DIR)
        persist_dir.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(persist_dir))

    def _collection_name(self, *, user_id: UUID, thread_id: UUID) -> str:
        raw = f"{settings.RAG_COLLECTION_PREFIX}_u_{user_id}_t_{thread_id}"
        return _SAFE_NAME_RE.sub("_", raw)[:180]

    def upsert_chunks(
        self,
        *,
        user_id: UUID,
        thread_id: UUID,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict],
    ) -> None:
        collection = self.client.get_or_create_collection(
            name=self._collection_name(user_id=user_id, thread_id=thread_id),
            metadata={"hnsw:space": "cosine"},
        )
        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def query(
        self,
        *,
        user_id: UUID,
        thread_id: UUID,
        embedding: list[float],
        top_k: int,
        where: dict | None = None,
    ) -> dict:
        collection = self.client.get_or_create_collection(
            name=self._collection_name(user_id=user_id, thread_id=thread_id),
            metadata={"hnsw:space": "cosine"},
        )
        return collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

    def delete_by_document(
        self,
        *,
        user_id: UUID,
        thread_id: UUID,
        document_id: UUID,
    ) -> None:
        collection = self.client.get_or_create_collection(
            name=self._collection_name(user_id=user_id, thread_id=thread_id),
            metadata={"hnsw:space": "cosine"},
        )
        collection.delete(where={"document_id": str(document_id)})
