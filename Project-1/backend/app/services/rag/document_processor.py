"""PDF ingestion pipeline: extract text, split chunks, embed, index."""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from app.ai.llm import embeddings
from app.core import settings


@dataclass
class ProcessedChunk:
    chunk_id: str
    chunk_index: int
    page_number: int | None
    text: str
    metadata: dict


class DocumentProcessor:
    """Converts PDF bytes into embedded chunks ready for vector storage."""

    def __init__(self) -> None:
        self.recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.RAG_CHUNK_SIZE,
            chunk_overlap=settings.RAG_CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        self.semantic_like_splitter = RecursiveCharacterTextSplitter(
            chunk_size=max(800, int(settings.RAG_CHUNK_SIZE * 0.8)),
            chunk_overlap=max(120, int(settings.RAG_CHUNK_OVERLAP * 0.8)),
            separators=["\n\n## ", "\n\n", "\n- ", "\n", ". ", " ", ""],
        )

    @staticmethod
    def sanitize_text(text: str) -> str:
        text = text.replace("\x00", " ")
        text = re.sub(r"\s+", " ", text).strip()
        # Strip common prompt injection wrappers from extracted text.
        text = text.replace("<system>", "").replace("</system>", "")
        return text

    @staticmethod
    def extract_pages(pdf_path: Path) -> list[tuple[int, str]]:
        reader = PdfReader(str(pdf_path))
        pages: list[tuple[int, str]] = []
        for page_idx, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            pages.append((page_idx, text))
        return pages

    def build_chunks(
        self,
        *,
        pages: list[tuple[int, str]],
        document_id: str,
        filename: str,
        semantic_chunking: bool,
    ) -> list[ProcessedChunk]:
        chunks: list[ProcessedChunk] = []
        splitter = self.semantic_like_splitter if semantic_chunking else self.recursive_splitter

        for page_number, page_text in pages:
            cleaned = self.sanitize_text(page_text)
            if not cleaned:
                continue
            split_texts = splitter.split_text(cleaned)
            for split_idx, chunk_text in enumerate(split_texts):
                chunk_id = f"{document_id}:{page_number}:{split_idx}:{uuid4().hex[:8]}"
                chunks.append(
                    ProcessedChunk(
                        chunk_id=chunk_id,
                        chunk_index=len(chunks),
                        page_number=page_number,
                        text=chunk_text,
                        metadata={
                            "document_id": document_id,
                            "filename": filename,
                            "page_number": page_number,
                            "chunk_id": chunk_id,
                        },
                    )
                )
        return chunks

    async def embed_chunks(self, chunk_texts: list[str]) -> list[list[float]]:
        return await asyncio.to_thread(embeddings.embed_documents, chunk_texts)

    async def embed_query(self, text: str) -> list[float]:
        return await asyncio.to_thread(embeddings.embed_query, text)
